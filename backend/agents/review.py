# Purpose: Review Agent — runs the fixed security/schema/phase-boundary/regression
# checklist against changed files. Read-only: never modifies files, only reports.
# Called after Testing Agent passes.
#
# Design reference: MultiAgentDesign.md § "4. Review Agent"
# Anthropic tool use: https://docs.anthropic.com/en/docs/tool-use
#
# Sample usage:
#   state = run_review_agent(state, Path("HANDOFF_STATE.json"))
#   # state.review.status == "APPROVED" or "ISSUES"
#
# Expected output: HandoffState with review field populated; HANDOFF_STATE.json updated.
import sys
from pathlib import Path
from typing import List, Optional

import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY
from agents.handoff import HandoffState, ReviewResult, write_handoff_state
from agents.transfers import REVIEW_TOOLS, extract_tool_call
from agents.config import AGENT_CONFIGS

BASE_DIR = Path(__file__).parent.parent.parent  # MyAPTutor/


def _read_artifacts(artifacts: List[str]) -> str:
    """Read file contents for review context. Returns formatted string."""
    parts = []
    for file_path in artifacts:
        full_path = BASE_DIR / file_path
        if full_path.exists():
            parts.append(f"=== {file_path} ===\n{full_path.read_text()}")
        else:
            parts.append(f"=== {file_path} ===\n(FILE NOT FOUND)")
    logger.debug(f"Read {len(artifacts)} artifacts for review")
    return "\n\n".join(parts)


def run_review_agent(
    state: HandoffState,
    handoff_path: Path,
    client: Optional[anthropic.Anthropic] = None,
) -> HandoffState:
    """
    Run the Review Agent checklist.

    Reads artifact files and sessions.py (for regression checks), then calls
    Claude to run the fixed security/schema/phase-boundary/regression checklist.
    Expects Claude to call transfer_to_docs_agent (APPROVED) or
    transfer_to_code_agent (ISSUES).

    Args:
        state: Current HandoffState (testing.status must be PASS).
        handoff_path: Path to HANDOFF_STATE.json.
        client: Optional pre-constructed Anthropic client.

    Returns:
        Updated HandoffState with review field populated.

    Raises:
        ValueError: If called when testing status is not PASS.
    """
    if state.testing is None or state.testing.status != "PASS":
        raise ValueError(
            "Review Agent should only run after Testing Agent passes. "
            f"Current testing status: {state.testing}"
        )
    if client is None:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    artifacts = state.scoped_task.files
    artifact_contents = _read_artifacts(artifacts)

    # Always include sessions.py for the named regression checks
    sessions_path = BASE_DIR / "backend" / "routers" / "sessions.py"
    sessions_content = sessions_path.read_text() if sessions_path.exists() else "(not found)"

    cfg = AGENT_CONFIGS["review"]
    user_message = (
        f"Review task '{state.scoped_task.id}'.\n"
        f"Files changed: {artifacts}\n\n"
        f"Changed file contents:\n{artifact_contents}\n\n"
        f"sessions.py (for regression checks):\n{sessions_content}\n\n"
        "Run ALL checklist items. Collect ALL issues.\n"
        "Call transfer_to_docs_agent() if APPROVED (zero blocking issues).\n"
        "Call transfer_to_code_agent() if SECURITY, SCHEMA, PHASE, or REGRESSION issues exist."
    )

    logger.info(f"Review Agent: calling Claude API (model={cfg['model']})")
    response = client.messages.create(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        system=cfg["system"],
        tools=REVIEW_TOOLS,
        messages=[{"role": "user", "content": user_message}],
    )
    logger.info(f"Review Agent: stop_reason={response.stop_reason}")

    for block in response.content:
        if hasattr(block, "text"):
            print(block.text)

    tool_call = extract_tool_call(response)
    if tool_call is None:
        issues = ["review_agent_error: Claude did not call a transfer tool"]
        route = "code_agent"
        logger.error("Review Agent: no tool call in response")
    elif tool_call["name"] == "transfer_to_docs_agent":
        issues = []
        route = "docs_agent"
        logger.success("Review Agent: APPROVED")
    else:
        issues = tool_call["input"].get("issues", [])
        if not isinstance(issues, list):
            issues = [str(issues)]
        route = "code_agent"
        logger.warning(f"Review Agent: ISSUES — {len(issues)} found")

    review_status = "APPROVED" if route == "docs_agent" else "ISSUES"
    state.review = ReviewResult(
        status=review_status,
        issues=issues,
        route_to=route,
    )
    state.agent = "review"
    write_handoff_state(state, handoff_path)
    return state


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    from agents.handoff import HandoffState, ScopedTask, TestingResult, RetryCount
    import tempfile

    all_validation_failures = []
    total_tests = 0

    # Test 1: _read_artifacts returns correct format for existing file
    total_tests += 1
    result = _read_artifacts(["backend/main.py"])
    if "=== backend/main.py ===" not in result:
        all_validation_failures.append(f"_read_artifacts missing header: {result[:80]!r}")

    # Test 2: _read_artifacts handles missing file gracefully
    total_tests += 1
    result = _read_artifacts(["backend/nonexistent_xyz_abc.py"])
    if "FILE NOT FOUND" not in result:
        all_validation_failures.append("_read_artifacts should note missing file")

    # Test 3: run_review_agent raises ValueError when testing is not PASS
    total_tests += 1
    bad_state = HandoffState(
        agent="testing",
        session_goal="test",
        scoped_task=ScopedTask(
            id="x", label="MUST", description="d",
            done_when="dw", estimated_minutes=10, files=[],
        ),
        retry_count=RetryCount(),
    )
    try:
        import tempfile
        run_review_agent(bad_state, Path(tempfile.mktemp()))
        all_validation_failures.append("Should have raised ValueError for missing testing result")
    except ValueError:
        pass  # Expected

    # Test 4: REVIEW_TOOLS contains transfer_to_docs_agent and transfer_to_code_agent
    total_tests += 1
    tool_names = {t["name"] for t in REVIEW_TOOLS}
    for expected in ["transfer_to_docs_agent", "transfer_to_code_agent"]:
        if expected not in tool_names:
            all_validation_failures.append(f"REVIEW_TOOLS missing: {expected}")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
