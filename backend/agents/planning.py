# Purpose: Planning Agent — reads blackboard files, decomposes session goal,
# produces a scoped atomic task in HANDOFF_STATE.json.
# Called at session start. Writes the task for the Code Agent.
#
# Design reference: MultiAgentDesign.md § "1. Planning Agent"
# Anthropic messages API: https://docs.anthropic.com/en/api/messages
#
# Sample usage:
#   state = run_planning_agent("Add /api/report endpoint", Path("HANDOFF_STATE.json"))
#   # Writes HANDOFF_STATE.json with agent="planning", scoped_task populated
#
# Expected output: HandoffState written to disk; returns HandoffState object.
import sys
from pathlib import Path
from typing import Optional

import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY
from agents.handoff import HandoffState, ScopedTask, RetryCount, write_handoff_state
from agents.transfers import PLANNING_TOOLS, extract_tool_call
from agents.config import AGENT_CONFIGS

BASE_DIR = Path(__file__).parent.parent.parent  # MyAPTutor/


def _read_blackboard() -> str:
    """Read PROGRESS.md, TASKS.md, PARKING_LOT.md and return as formatted context block."""
    files = {
        "PROGRESS.md":    BASE_DIR / "PROGRESS.md",
        "TASKS.md":       BASE_DIR / "TASKS.md",
        "PARKING_LOT.md": BASE_DIR / "PARKING_LOT.md",
    }
    parts = []
    for name, path in files.items():
        content = path.read_text() if path.exists() else "(file does not exist yet)"
        parts.append(f"=== {name} ===\n{content}")
    logger.debug(f"Blackboard read: {[n for n, p in files.items() if p.exists()]} exist")
    return "\n\n".join(parts)


def run_planning_agent(
    session_goal: str,
    handoff_path: Path,
    client: Optional[anthropic.Anthropic] = None,
) -> HandoffState:
    """
    Run the Planning Agent for one session.

    Calls Claude with the Planning system prompt + blackboard context.
    Expects Claude to call transfer_to_code_agent() to conclude.
    Writes HANDOFF_STATE.json and returns the HandoffState.

    Args:
        session_goal: User-provided description of what to build this session.
        handoff_path: Where to write HANDOFF_STATE.json.
        client: Optional pre-constructed Anthropic client (for testing).

    Returns:
        HandoffState with agent="planning" and scoped_task populated.

    Raises:
        ValueError: If Claude does not call the transfer tool.
        anthropic.APIError: On API failure.
    """
    if client is None:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    cfg = AGENT_CONFIGS["planning"]
    blackboard = _read_blackboard()

    user_message = (
        f"Session goal: {session_goal}\n\n"
        f"Current blackboard state:\n{blackboard}\n\n"
        "Analyze the above, produce a briefing and scoped task plan, "
        "then call transfer_to_code_agent() with the task_id and implementation_notes."
    )

    logger.info(f"Planning Agent: calling Claude API (model={cfg['model']})")
    response = client.messages.create(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        system=cfg["system"],
        tools=PLANNING_TOOLS,
        messages=[{"role": "user", "content": user_message}],
    )
    logger.info(f"Planning Agent: stop_reason={response.stop_reason}")

    # Print Claude's narrative for the user to read
    for block in response.content:
        if hasattr(block, "text"):
            print(block.text)

    tool_call = extract_tool_call(response)
    if tool_call is None or tool_call["name"] != "transfer_to_code_agent":
        raise ValueError(
            f"Planning Agent did not call transfer_to_code_agent(). "
            f"stop_reason={response.stop_reason}. "
            "Check the system prompt instructs the agent to call the transfer tool."
        )

    inp = tool_call["input"]
    scoped_task = ScopedTask(
        id=inp["task_id"],
        label="MUST",
        description=inp["implementation_notes"],
        done_when="Defined by Planning Agent — see implementation_notes above",
        estimated_minutes=45,
        files=[],
    )
    state = HandoffState(
        agent="planning",
        session_goal=session_goal,
        scoped_task=scoped_task,
        retry_count=RetryCount(),
    )
    write_handoff_state(state, handoff_path)
    logger.success(f"Planning Agent: wrote {handoff_path}")
    return state


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile

    all_validation_failures = []
    total_tests = 0

    # Test 1: _read_blackboard() returns a non-empty string without crashing
    total_tests += 1
    result = _read_blackboard()
    if not isinstance(result, str) or len(result) < 10:
        all_validation_failures.append(f"_read_blackboard() returned unexpected: {result!r}")
    if "=== TASKS.md ===" not in result and "=== PROGRESS.md ===" not in result:
        all_validation_failures.append("_read_blackboard() missing expected section headers")

    # Test 2: HandoffState can be written and read back
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "HANDOFF_STATE.json"
        state = HandoffState(
            agent="planning",
            session_goal="test goal",
            scoped_task=ScopedTask(
                id="test-id",
                label="MUST",
                description="test desc",
                done_when="test done when",
                estimated_minutes=10,
                files=[],
            ),
        )
        write_handoff_state(state, path)
        if not path.exists():
            all_validation_failures.append("write_handoff_state did not create file")

    # Test 3: PLANNING_TOOLS contains transfer_to_code_agent
    total_tests += 1
    if not any(t["name"] == "transfer_to_code_agent" for t in PLANNING_TOOLS):
        all_validation_failures.append("PLANNING_TOOLS missing transfer_to_code_agent")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
