# Purpose: HandoffState Pydantic schema and filesystem utilities.
# The HANDOFF_STATE.json file is the live session artifact — created by
# Planning Agent, appended to by Code/Testing/Review agents, archived by
# Docs Agent, then deleted.
#
# Schema reference: MultiAgentDesign.md § "Shared State: The Blackboard"
import json
import sys
from pathlib import Path
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

# ── Task priority label ───────────────────────────────────────────────────────
TaskLabel = Literal["MUST", "SHOULD", "NICE"]

# ── Agent name enum ───────────────────────────────────────────────────────────
AgentName = Literal["planning", "code", "testing", "review", "docs"]


class ScopedTask(BaseModel):
    """The single atomic task scoped for one session."""
    id: str
    label: TaskLabel
    description: str
    done_when: str                     # Observable, testable completion criterion
    estimated_minutes: int
    files: List[str] = Field(default_factory=list)  # Paths the code agent may touch


class RetryCount(BaseModel):
    """Tracks loop iterations to enforce the max-3 retry guard."""
    code_to_test: int = 0
    code_to_review: int = 0


class TestingResult(BaseModel):
    """Output appended by the Testing Agent after validation runs."""
    status: Literal["PASS", "FAIL"]
    failures: List[str] = Field(default_factory=list)
    route_to: Literal["code_agent", "review_agent"]


class ReviewResult(BaseModel):
    """Output appended by the Review Agent after checklist run."""
    status: Literal["APPROVED", "ISSUES"]
    issues: List[str] = Field(default_factory=list)
    route_to: Literal["code_agent", "docs_agent"]


class HandoffState(BaseModel):
    """
    Full session state written to HANDOFF_STATE.json.
    Lifecycle: Planning creates → Code reads → Testing appends →
               Review appends → Docs archives key parts → file deleted.
    """
    agent: AgentName
    session_goal: str
    scoped_task: ScopedTask
    deferred_to_parking_lot: List[str] = Field(default_factory=list)
    retry_count: RetryCount = Field(default_factory=RetryCount)
    testing: Optional[TestingResult] = None
    review: Optional[ReviewResult] = None


# ── Filesystem utilities ──────────────────────────────────────────────────────

def write_handoff_state(state: HandoffState, path: Path) -> None:
    """Write HandoffState to disk as pretty-printed JSON."""
    path.write_text(json.dumps(state.model_dump(), indent=2))


def read_handoff_state(path: Path) -> HandoffState:
    """Read and validate HANDOFF_STATE.json from disk."""
    return HandoffState.model_validate(json.loads(path.read_text()))


def delete_handoff_state(path: Path) -> None:
    """Delete HANDOFF_STATE.json at session end. No-op if file doesn't exist."""
    if path.exists():
        path.unlink()


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile

    all_validation_failures = []
    total_tests = 0

    # Test 1: ScopedTask round-trips through JSON
    total_tests += 1
    task = ScopedTask(
        id="test-task",
        label="MUST",
        description="Test description",
        done_when="curl returns 200",
        estimated_minutes=30,
        files=["backend/routers/ai.py"],
    )
    as_dict = task.model_dump()
    restored = ScopedTask.model_validate(as_dict)
    if restored.id != "test-task" or restored.label != "MUST":
        all_validation_failures.append(f"ScopedTask round-trip failed: {restored}")

    # Test 2: HandoffState write/read round-trip
    total_tests += 1
    state = HandoffState(
        agent="planning",
        session_goal="Test goal",
        scoped_task=task,
        deferred_to_parking_lot=["deferred-thing"],
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "HANDOFF_STATE.json"
        write_handoff_state(state, path)
        loaded = read_handoff_state(path)
        if loaded.session_goal != "Test goal":
            all_validation_failures.append(
                f"HandoffState round-trip failed: goal={loaded.session_goal}"
            )
        delete_handoff_state(path)
        if path.exists():
            all_validation_failures.append("delete_handoff_state did not delete the file")

    # Test 3: RetryCount starts at zero
    total_tests += 1
    rc = RetryCount()
    if rc.code_to_test != 0 or rc.code_to_review != 0:
        all_validation_failures.append(f"RetryCount defaults wrong: {rc}")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
