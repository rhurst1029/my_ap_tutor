# Purpose: Testing Agent — runs the 5-step validation sequence, collects all
# failures, and routes to Review Agent (PASS) or Code Agent (FAIL).
# Never modifies files — validates only.
#
# Design reference: MultiAgentDesign.md § "3. Testing Agent"
# Anthropic tool use: https://docs.anthropic.com/en/docs/tool-use
#
# Sample usage:
#   state = run_testing_agent(state, Path("HANDOFF_STATE.json"))
#   # Updates state.testing with status="PASS" or "FAIL"
#
# Expected output: HandoffState with testing field populated; HANDOFF_STATE.json updated.
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY
from agents.handoff import HandoffState, TestingResult, write_handoff_state
from agents.transfers import TESTING_TOOLS, extract_tool_call
from agents.config import AGENT_CONFIGS

BASE_DIR = Path(__file__).parent.parent.parent  # MyAPTutor/
FRONTEND_DIR = BASE_DIR / "frontend"


def _run_cmd(cmd: str, cwd: Optional[Path] = None, timeout: int = 30) -> tuple[int, str, str]:
    """Run a shell command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        cwd=str(cwd) if cwd else None, timeout=timeout,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _check_health(failures: List[str]) -> bool:
    """Step 1: Check /api/health returns {"status":"ok"}. Starts uvicorn if needed."""
    # Kill any existing uvicorn on port 8000 first
    _run_cmd("pkill -f 'uvicorn backend.main' || true", cwd=BASE_DIR)
    time.sleep(1)

    # Start uvicorn in background
    subprocess.Popen(
        [str(BASE_DIR / "backend" / "venv" / "bin" / "uvicorn"), "backend.main:app", "--port", "8000"],
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={**__import__("os").environ, "PYTHONPATH": str(BASE_DIR / "backend")},
    )
    time.sleep(3)  # Wait for startup

    code, stdout, stderr = _run_cmd("curl -s http://localhost:8000/api/health")
    ok = code == 0 and ("ok" in stdout)
    if not ok:
        failures.append(f"health_check: /api/health failed (code={code}, stdout={stdout!r})")
        logger.warning(f"Health check failed: {stdout!r}")
    else:
        logger.info("Health check passed")
    return ok


def _check_frontend_types(failures: List[str]) -> None:
    """Step 5: Frontend type-check must produce 0 errors."""
    if not FRONTEND_DIR.exists():
        logger.warning(f"Frontend directory not found at {FRONTEND_DIR} — skipping type-check")
        return
    code, stdout, stderr = _run_cmd("npm run type-check", cwd=FRONTEND_DIR, timeout=60)
    if code != 0:
        failures.append(f"frontend_typecheck: npm run type-check failed\n{stdout}\n{stderr}")
        logger.warning("Frontend type-check failed")
    else:
        logger.info("Frontend type-check passed")


def _read_artifacts(artifacts: List[str]) -> dict:
    """Read file contents for the artifacts list. Returns {path: content} dict."""
    contents = {}
    for file_path in artifacts:
        full_path = BASE_DIR / file_path
        if full_path.exists():
            contents[file_path] = full_path.read_text()
        else:
            contents[file_path] = "(FILE NOT FOUND)"
    return contents


def run_testing_agent(
    state: HandoffState,
    handoff_path: Path,
    client: Optional[anthropic.Anthropic] = None,
) -> HandoffState:
    """
    Run the Testing Agent validation sequence.

    Steps 1 (health) and 5 (frontend type-check) run directly.
    Steps 2-4 (smoke test, schema sync, __main__ block) are analyzed by Claude.

    Args:
        state: Current HandoffState (must have scoped_task.files populated).
        handoff_path: Path to HANDOFF_STATE.json.
        client: Optional pre-constructed Anthropic client.

    Returns:
        Updated HandoffState with testing field populated.
    """
    if client is None:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    failures: List[str] = []

    # Step 1: Backend health
    logger.info("Testing Agent: Step 1 — backend health check")
    health_ok = _check_health(failures)

    # Read artifact contents for Claude's analysis (steps 2-4)
    artifacts = state.scoped_task.files
    artifact_contents = _read_artifacts(artifacts)
    missing = [p for p, c in artifact_contents.items() if c == "(FILE NOT FOUND)"]
    if missing:
        for p in missing:
            failures.append(f"artifact_missing: {p} not found after implementation")
        logger.warning(f"Missing artifacts: {missing}")

    cfg = AGENT_CONFIGS["testing"]
    artifact_text = "\n\n".join(
        f"=== {k} ===\n{v}" for k, v in artifact_contents.items()
    )
    user_message = (
        f"Validate task '{state.scoped_task.id}'.\n"
        f"Files changed: {artifacts}\n\n"
        f"File contents:\n{artifact_text}\n\n"
        f"Health check (Step 1) passed: {health_ok}\n"
        f"Pre-collected failures: {failures}\n\n"
        "Run Steps 2 (endpoint smoke test), 3 (schema sync), and 4 (__main__ block).\n"
        "Collect ALL failures. Then call the appropriate transfer tool:\n"
        "- transfer_to_review_agent if all pass\n"
        "- transfer_to_code_agent if any fail (include all failures)"
    )

    logger.info("Testing Agent: calling Claude for steps 2-4")
    response = client.messages.create(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        system=cfg["system"],
        tools=TESTING_TOOLS,
        messages=[{"role": "user", "content": user_message}],
    )
    logger.info(f"Testing Agent: stop_reason={response.stop_reason}")

    for block in response.content:
        if hasattr(block, "text"):
            print(block.text)

    # Step 5: Frontend type-check (always runs)
    logger.info("Testing Agent: Step 5 — frontend type-check")
    _check_frontend_types(failures)

    tool_call = extract_tool_call(response)
    if tool_call is None:
        failures.append("testing_agent_error: Claude did not call a transfer tool")
        route = "code_agent"
        logger.error("Testing Agent: no tool call in response")
    else:
        if tool_call["name"] == "transfer_to_code_agent":
            claude_failures = tool_call["input"].get("failures", [])
            if isinstance(claude_failures, list):
                failures.extend(claude_failures)
            route = "code_agent"
        else:
            route = "review_agent"

    # Direct failures (health, missing artifacts, frontend) override Claude's pass verdict
    if failures:
        status = "FAIL"
        route = "code_agent"
    else:
        status = "PASS"
        route = "review_agent"

    state.testing = TestingResult(status=status, failures=failures, route_to=route)
    state.agent = "testing"
    write_handoff_state(state, handoff_path)
    logger.info(f"Testing Agent: status={status}, route_to={route}, failures={len(failures)}")
    return state


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    all_validation_failures = []
    total_tests = 0

    # Test 1: _run_cmd returns correct exit code and stdout
    total_tests += 1
    code, stdout, stderr = _run_cmd("echo hello")
    if code != 0 or stdout != "hello":
        all_validation_failures.append(f"_run_cmd('echo hello'): code={code}, stdout={stdout!r}")

    # Test 2: _run_cmd captures non-zero exit
    total_tests += 1
    code, stdout, stderr = _run_cmd("ls /nonexistent_path_xyz_abc")
    if code == 0:
        all_validation_failures.append("_run_cmd should return non-zero for failed ls")

    # Test 3: _read_artifacts handles existing file
    total_tests += 1
    result = _read_artifacts(["backend/main.py"])
    if "backend/main.py" not in result:
        all_validation_failures.append("_read_artifacts missing expected key")
    elif "(FILE NOT FOUND)" in result["backend/main.py"]:
        all_validation_failures.append("_read_artifacts: backend/main.py should exist")

    # Test 4: _read_artifacts handles missing file gracefully
    total_tests += 1
    result = _read_artifacts(["backend/nonexistent_xyz_abc.py"])
    if result.get("backend/nonexistent_xyz_abc.py") != "(FILE NOT FOUND)":
        all_validation_failures.append("_read_artifacts should return FILE NOT FOUND for missing")

    # Test 5: TESTING_TOOLS contains both transfer tools
    total_tests += 1
    tool_names = {t["name"] for t in TESTING_TOOLS}
    for expected in ["transfer_to_review_agent", "transfer_to_code_agent"]:
        if expected not in tool_names:
            all_validation_failures.append(f"TESTING_TOOLS missing: {expected}")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
