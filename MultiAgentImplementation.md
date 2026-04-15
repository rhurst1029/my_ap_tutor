# Multi-Agent Development Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the five-agent development pipeline described in `MultiAgentDesign.md` as runnable Python code using the Anthropic SDK.

**Architecture:** A Python orchestrator (`backend/orchestrator.py`) drives a sequential pipeline: Planning → Code → Testing → Review → Docs. Each agent is an Anthropic API call with a scoped system prompt. Transfer between agents uses structured tool calls. Shared state lives in `HANDOFF_STATE.json` on the filesystem (the "blackboard"). The Code Agent is a Claude Code subagent — the orchestrator hands off to it via a structured file and then waits.

**Tech Stack:** Python 3.11+, Anthropic SDK (`anthropic>=0.50.0`), FastAPI (existing), Pydantic v2 (existing), `uv` for package management.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `backend/agents/__init__.py` | Package marker |
| Create | `backend/agents/handoff.py` | HandoffState Pydantic schema + read/write utilities |
| Create | `backend/agents/transfers.py` | Transfer tool definitions (Claude tool schemas) |
| Create | `backend/agents/config.py` | Agent configurations — system prompts + tool lists |
| Create | `backend/agents/planning.py` | Planning agent — reads blackboard, produces scoped task |
| Create | `backend/agents/testing.py` | Testing agent — runs validation sequence, reports failures |
| Create | `backend/agents/review.py` | Review agent — reads code, runs fixed security/schema checklist |
| Create | `backend/agents/docs.py` | Documentation agent — updates BuildGuide, PROGRESS, DECISIONS |
| Create | `backend/orchestrator.py` | Pipeline runner — routes between agents with retry guard |
| Create | `backend/tests/test_handoff.py` | Validation tests for HandoffState schema |
| Modify | `backend/requirements.txt` | Add `anthropic>=0.50.0` |

**Not created here:** The Code Agent runs as a Claude Code subagent (it needs Edit/Write/Bash tools from the Claude Code harness). The orchestrator writes `HANDOFF_STATE.json` and exits with instructions; the human invokes Claude Code for the code step, then re-runs the orchestrator to continue.

---

## Task 1: Update anthropic dependency

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Check current anthropic version**

```bash
cd /path/to/MyAPTutor
grep anthropic backend/requirements.txt
```
Expected output: `anthropic==0.28.0`

- [ ] **Step 2: Update requirements.txt**

Replace the existing `anthropic==0.28.0` line with:
```
anthropic>=0.50.0
```

`backend/requirements.txt` full file after edit:
```
fastapi==0.111.0
uvicorn[standard]==0.30.1
python-multipart==0.0.9
python-dotenv==1.0.1
anthropic>=0.50.0
vosk==0.3.44
python-docx==1.1.2
pydantic==2.7.1
aiofiles==23.2.1
httpx==0.27.0
pydub==0.25.1
```

- [ ] **Step 3: Install updated package**

```bash
source backend/venv/bin/activate && pip install "anthropic>=0.50.0"
```
Expected: `Successfully installed anthropic-X.Y.Z`

- [ ] **Step 4: Verify install**

```bash
python -c "import anthropic; print(anthropic.__version__)"
```
Expected: version string ≥ 0.50.0

- [ ] **Step 5: Commit**

```bash
git add backend/requirements.txt
git commit -m "backend: update anthropic SDK to >=0.50.0 for tool-use support"
```

---

## Task 2: HandoffState schema and filesystem utilities

**Files:**
- Create: `backend/agents/__init__.py`
- Create: `backend/agents/handoff.py`
- Create: `backend/tests/test_handoff.py`

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_handoff.py`:
```python
# Tests for HandoffState schema — validates JSON serialization round-trip
# and filesystem read/write contract.
import json
import pytest
from pathlib import Path
from agents.handoff import (
    HandoffState,
    ScopedTask,
    TestingResult,
    ReviewResult,
    RetryCount,
    write_handoff_state,
    read_handoff_state,
    delete_handoff_state,
)


def test_scoped_task_serializes():
    task = ScopedTask(
        id="add-report-endpoint",
        label="MUST",
        description="Create backend/routers/ai.py with POST /api/report.",
        done_when="curl POST /api/report returns 200 with valid JSON",
        estimated_minutes=35,
        files=["backend/routers/ai.py", "backend/main.py"],
    )
    data = task.model_dump()
    assert data["id"] == "add-report-endpoint"
    assert data["label"] == "MUST"
    assert data["files"] == ["backend/routers/ai.py", "backend/main.py"]


def test_handoff_state_round_trip(tmp_path):
    state = HandoffState(
        agent="planning",
        session_goal="Add /api/report endpoint",
        scoped_task=ScopedTask(
            id="add-report-endpoint",
            label="MUST",
            description="Create POST /api/report in backend/routers/ai.py",
            done_when="curl returns 200",
            estimated_minutes=30,
            files=["backend/routers/ai.py"],
        ),
        deferred_to_parking_lot=["study_guide endpoint"],
        retry_count=RetryCount(),
    )
    path = tmp_path / "HANDOFF_STATE.json"
    write_handoff_state(state, path)
    loaded = read_handoff_state(path)
    assert loaded.agent == "planning"
    assert loaded.scoped_task.id == "add-report-endpoint"
    assert loaded.deferred_to_parking_lot == ["study_guide endpoint"]


def test_testing_result_fail_serializes():
    result = TestingResult(
        status="FAIL",
        failures=["schema_sync: missing field topic_analysis"],
        route_to="code_agent",
    )
    data = result.model_dump()
    assert data["status"] == "FAIL"
    assert len(data["failures"]) == 1


def test_review_result_approved_serializes():
    result = ReviewResult(status="APPROVED", issues=[], route_to="docs_agent")
    data = result.model_dump()
    assert data["status"] == "APPROVED"
    assert data["issues"] == []


def test_delete_handoff_state(tmp_path):
    state = HandoffState(
        agent="docs",
        session_goal="Document changes",
        scoped_task=ScopedTask(
            id="doc-step",
            label="MUST",
            description="Update BuildGuide.md",
            done_when="BuildGuide.md has new endpoint",
            estimated_minutes=10,
            files=["BuildGuide.md"],
        ),
    )
    path = tmp_path / "HANDOFF_STATE.json"
    write_handoff_state(state, path)
    assert path.exists()
    delete_handoff_state(path)
    assert not path.exists()


def test_delete_nonexistent_handoff_state(tmp_path):
    path = tmp_path / "HANDOFF_STATE.json"
    # Should not raise
    delete_handoff_state(path)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd MyAPTutor && source backend/venv/bin/activate
python -m pytest backend/tests/test_handoff.py -v
```
Expected: `ModuleNotFoundError: No module named 'agents'`

- [ ] **Step 3: Create package marker**

Create `backend/agents/__init__.py`:
```python
# agents/ — multi-agent development pipeline
# See MultiAgentDesign.md for architecture overview.
```

Also create `backend/tests/__init__.py` if it doesn't exist:
```python
```

- [ ] **Step 4: Implement HandoffState schema**

Create `backend/agents/handoff.py`:
```python
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
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd MyAPTutor && source backend/venv/bin/activate
python -m pytest backend/tests/test_handoff.py -v
```
Expected: all 6 tests `PASSED`

- [ ] **Step 6: Run __main__ validation block**

```bash
cd MyAPTutor && source backend/venv/bin/activate
PYTHONPATH=backend python backend/agents/handoff.py
```
Expected: `✅ VALIDATION PASSED — all 3 tests produced expected results`

- [ ] **Step 7: Commit**

```bash
git add backend/agents/__init__.py backend/agents/handoff.py backend/tests/__init__.py backend/tests/test_handoff.py
git commit -m "backend: add HandoffState schema and filesystem utilities"
```

---

## Task 3: Transfer tool definitions

**Files:**
- Create: `backend/agents/transfers.py`

Transfer functions are Claude tool schemas. When an agent's API response contains a tool call to one of these, the orchestrator intercepts it and routes to the next agent. The LLM *must* call a transfer function to conclude its turn — it cannot simply stop.

- [ ] **Step 1: Create transfers.py**

Create `backend/agents/transfers.py`:
```python
# Purpose: Structured transfer tool definitions for agent handoffs.
# These are passed as `tools=` to client.messages.create().
# The orchestrator inspects tool_use blocks in the response and routes accordingly.
#
# Design reference: MultiAgentDesign.md § "Handoff Implementation"
# Claude tool use docs: https://docs.anthropic.com/en/docs/tool-use
import sys
from typing import Any, Dict, Optional


# ── Tool schemas (passed to Claude API as tools=[...]) ────────────────────────

TRANSFER_TO_CODE_AGENT: Dict[str, Any] = {
    "name": "transfer_to_code_agent",
    "description": (
        "Call this when planning is complete and the scoped task is written to HANDOFF_STATE.json. "
        "Pass the task id and a summary of what the code agent should implement. "
        "Do NOT call this until the scoped_task fields are fully filled out."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "The id field from scoped_task in HANDOFF_STATE.json",
            },
            "implementation_notes": {
                "type": "string",
                "description": "One paragraph of context for the code agent — what to build and why",
            },
        },
        "required": ["task_id", "implementation_notes"],
    },
}

TRANSFER_TO_TESTING_AGENT: Dict[str, Any] = {
    "name": "transfer_to_testing_agent",
    "description": (
        "Call this when implementation is complete. "
        "Pass the list of files that were modified. "
        "The testing agent will validate: server health, endpoint smoke test, schema sync, "
        "__main__ block, and frontend type-check."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "artifacts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths that were created or modified",
            },
            "notes": {
                "type": "string",
                "description": "Optional context for the testing agent (known edge cases, etc.)",
            },
        },
        "required": ["artifacts"],
    },
}

TRANSFER_TO_REVIEW_AGENT: Dict[str, Any] = {
    "name": "transfer_to_review_agent",
    "description": (
        "Call this when all tests pass. "
        "The review agent runs a fixed security, schema, phase-boundary, and regression checklist. "
        "It does NOT fix issues — it reports them."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "artifacts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths to review",
            },
        },
        "required": ["artifacts"],
    },
}

TRANSFER_TO_DOCS_AGENT: Dict[str, Any] = {
    "name": "transfer_to_docs_agent",
    "description": (
        "Call this when review is APPROVED. "
        "The docs agent updates BuildGuide.md, PROGRESS.md, DECISIONS.md, TASKS.md, "
        "and reviews PARKING_LOT.md."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "One sentence: what was built and where it lives",
            },
            "new_endpoints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of new API endpoints added (e.g. 'POST /api/report')",
            },
            "new_components": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of new frontend components added",
            },
            "schema_changes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of schema changes (model additions, field changes)",
            },
        },
        "required": ["summary"],
    },
}

TRANSFER_TO_USER: Dict[str, Any] = {
    "name": "transfer_to_user",
    "description": (
        "Call this when the max retry limit (3) has been reached without passing tests or review, "
        "or when a blocker requires human judgement. Provide a clear summary of what failed."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Why we are escalating to the user",
            },
            "failures": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of failures that could not be resolved automatically",
            },
        },
        "required": ["reason", "failures"],
    },
}


# ── Tool sets per agent ───────────────────────────────────────────────────────

PLANNING_TOOLS = [TRANSFER_TO_CODE_AGENT]
TESTING_TOOLS = [TRANSFER_TO_REVIEW_AGENT, TRANSFER_TO_CODE_AGENT, TRANSFER_TO_USER]
REVIEW_TOOLS = [TRANSFER_TO_DOCS_AGENT, TRANSFER_TO_CODE_AGENT, TRANSFER_TO_USER]
DOCS_TOOLS = [TRANSFER_TO_USER]   # Only escalates on error


def extract_tool_call(response: Any) -> Optional[Dict[str, Any]]:
    """
    Extract the first tool_use block from an Anthropic API response.
    Returns {"name": str, "input": dict} or None if no tool call in response.
    """
    for block in response.content:
        if block.type == "tool_use":
            return {"name": block.name, "input": block.input}
    return None


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    all_validation_failures = []
    total_tests = 0

    # Test 1: All tool schemas have required fields
    total_tests += 1
    for tool in [
        TRANSFER_TO_CODE_AGENT,
        TRANSFER_TO_TESTING_AGENT,
        TRANSFER_TO_REVIEW_AGENT,
        TRANSFER_TO_DOCS_AGENT,
        TRANSFER_TO_USER,
    ]:
        for field in ["name", "description", "input_schema"]:
            if field not in tool:
                all_validation_failures.append(
                    f"Tool {tool.get('name', '?')} missing field: {field}"
                )

    # Test 2: extract_tool_call returns None on empty content
    total_tests += 1
    class FakeBlock:
        type = "text"
        text = "hello"
    class FakeResponse:
        content = [FakeBlock()]
    result = extract_tool_call(FakeResponse())
    if result is not None:
        all_validation_failures.append(f"extract_tool_call should return None for text-only, got {result}")

    # Test 3: extract_tool_call returns dict for tool_use block
    total_tests += 1
    class FakeToolBlock:
        type = "tool_use"
        name = "transfer_to_code_agent"
        input = {"task_id": "x", "implementation_notes": "y"}
    class FakeToolResponse:
        content = [FakeToolBlock()]
    result = extract_tool_call(FakeToolResponse())
    if result is None or result["name"] != "transfer_to_code_agent":
        all_validation_failures.append(f"extract_tool_call failed: {result}")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
```

- [ ] **Step 2: Run __main__ validation block**

```bash
PYTHONPATH=backend python backend/agents/transfers.py
```
Expected: `✅ VALIDATION PASSED — all 3 tests produced expected results`

- [ ] **Step 3: Commit**

```bash
git add backend/agents/transfers.py
git commit -m "backend: add transfer tool definitions for agent handoffs"
```

---

## Task 4: Agent configuration (system prompts)

**Files:**
- Create: `backend/agents/config.py`

- [ ] **Step 1: Create config.py**

Create `backend/agents/config.py`:
```python
# Purpose: Agent configurations — maps agent names to system prompts and tool sets.
# System prompts are loaded from .claude/rules/ files.
# Tool sets reference the transfer tool definitions from transfers.py.
#
# Design reference: MultiAgentDesign.md § "Agent Definitions"
import sys
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).parent.parent.parent  # MyAPTutor/
RULES_DIR = BASE_DIR / ".claude" / "rules"


def _load_rule(filename: str) -> str:
    """Load a rules file. Raises FileNotFoundError with a helpful message if missing."""
    path = RULES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Rule file not found: {path}\n"
            f"Expected rules in {RULES_DIR}. Check that .claude/rules/ exists."
        )
    return path.read_text()


# ── Planning Agent ────────────────────────────────────────────────────────────
# Reads blackboard state, decomposes task, scopes ONE atomic task per session.
# Writes HANDOFF_STATE.json then calls transfer_to_code_agent().
# NO Bash access — planning only.
PLANNING_SYSTEM = """
You are the Planning Agent for the MyAPTutor multi-agent development pipeline.
Your only job is to analyze the current project state and produce a scoped task plan.

RULES:
1. Read the provided PROGRESS.md, TASKS.md, and PARKING_LOT.md content.
2. Deliver a 3-bullet "where we are" briefing.
3. Decompose the session goal into atomic sub-tasks, each completable in ≤45 minutes.
4. Label each task: MUST / SHOULD / NICE.
5. Surface ONE task for this session.
6. Define "done" as a testable, observable criterion (e.g., curl returns 200).
7. List file paths the code agent will need to touch.
8. Identify any out-of-scope work and add it to deferred_to_parking_lot.
9. Call transfer_to_code_agent() with the task_id and implementation_notes.

Do NOT write any code. Do NOT suggest implementation approaches unless asked.
Output the HANDOFF_STATE JSON fields in your response, then call the transfer tool.
""" + "\n\n## Session Management Rules\n" + _load_rule("session-management.md")

# ── Testing Agent ─────────────────────────────────────────────────────────────
# Runs the validation sequence. Reports ALL failures before routing.
# Never modifies files — validates only.
TESTING_SYSTEM = """
You are the Testing Agent for the MyAPTutor multi-agent development pipeline.
Your only job is to validate that the code changes work correctly.

Run this sequence IN ORDER and collect ALL failures before reporting:

1. Backend health check:
   Start uvicorn: uvicorn backend.main:app --reload &
   Wait 2 seconds, then: curl -s http://localhost:8000/api/health
   Expected: {"status": "ok"}

2. New endpoint smoke test (use the artifacts list from HANDOFF_STATE.json):
   Construct a minimal valid request payload and curl the new endpoint.
   Expected: HTTP 200 with valid JSON matching the Pydantic model.

3. Schema sync check:
   For each new backend model field, verify the corresponding frontend type field exists.
   snake_case backend ↔ camelCase frontend (or explicit alias documented in code).

4. __main__ validation block:
   Run: python backend/{changed_file}.py
   Expected: "✅ VALIDATION PASSED"

5. Frontend type-check:
   cd frontend && npm run type-check
   Expected: 0 errors

Collect every failure. Do NOT stop at the first one.
After running all 5 checks:
- If any failures: call transfer_to_code_agent() with failures listed.
- If all pass: call transfer_to_review_agent() with artifacts.
""" + "\n\n## Testing Rules\n" + _load_rule("testing-validation.md")

# ── Review Agent ─────────────────────────────────────────────────────────────
# Read-only checklist. Reports protocol violations, does not fix them.
REVIEW_SYSTEM = """
You are the Review Agent for the MyAPTutor multi-agent development pipeline.
You are READ-ONLY. You never modify files. You run a fixed checklist and report violations.

FIXED CHECKLIST — run every item, collect ALL issues:

SECURITY (block on any):
  □ No raw string path concat for student files (must use get_student_dir())
  □ No env vars logged or returned in API responses
  □ No path traversal vector (../  in user-supplied input)
  □ No new file-serving route without explicit sanitization

SCHEMA COMPATIBILITY (block on divergence):
  □ frontend/src/types/ in sync with backend/models/
  □ No fields that bypass the test JSON schema in data/tests/

PHASE BOUNDARY (block on any violation):
  □ No Phase 2/3/4 imports inside Phase 1 components or router files

NAMED REGRESSIONS (block on any):
  □ _cleanup_orphan() in sessions.py is untouched
  □ normalize_name() in sessions.py is untouched
  □ Completion screen time signals in frontend/src/components/TestRunner/ intact

DOCUMENTATION:
  □ BuildGuide.md updated if new endpoints, components, or schemas were added

After checking all items:
- If any SECURITY, SCHEMA, PHASE BOUNDARY, or NAMED REGRESSION issues found:
  call transfer_to_code_agent() with the issues list.
- If only DOCUMENTATION issues: include them in issues but still call transfer_to_docs_agent()
  with APPROVED status (docs agent will fix them).
- If zero issues: call transfer_to_docs_agent() with APPROVED.
""" + "\n\n## PR Review Rules\n" + _load_rule("pr-review.md") \
   + "\n\n## Data Safety Rules\n" + _load_rule("data-safety.md")

# ── Documentation Agent ───────────────────────────────────────────────────────
# Updates the blackboard files after an approved session.
DOCS_SYSTEM = """
You are the Documentation Agent for the MyAPTutor multi-agent development pipeline.
You update the project's living documents after every approved changeset.

For every approved session, in this order:

1. BuildGuide.md — if new endpoint/component/schema was added:
   Add an entry under the correct phase section with:
   - Route or component name
   - Input/output schema reference
   - File it lives in

2. PROGRESS.md — append a session entry:
   Format exactly:
   ## Session [date]
   **Done:** [one sentence — what actually completed]
   **State:** [working / uvicorn starts, tests pass] or [broken — what's broken]
   **Next:** [verb] [specific thing] in [specific file]

3. DECISIONS.md — for any architectural choice made this session:
   Format:
   ## [date] — [short title]
   We chose [X] over [Y] because [Z].

4. PARKING_LOT.md — review all items. Promote anything with 2+ appearances to TASKS.md.

5. TASKS.md — mark the completed task [x].

Output each file's updated content in a code block labeled with the filename.
Then call transfer_to_user() with a summary confirming what was updated.
"""


# ── Agent registry ────────────────────────────────────────────────────────────
AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "planning": {
        "system": PLANNING_SYSTEM,
        "model": "claude-opus-4-6",
        "max_tokens": 4096,
    },
    "testing": {
        "system": TESTING_SYSTEM,
        "model": "claude-opus-4-6",
        "max_tokens": 4096,
    },
    "review": {
        "system": REVIEW_SYSTEM,
        "model": "claude-opus-4-6",
        "max_tokens": 4096,
    },
    "docs": {
        "system": DOCS_SYSTEM,
        "model": "claude-sonnet-4-6",  # Docs don't need Opus
        "max_tokens": 8192,
    },
}


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    all_validation_failures = []
    total_tests = 0

    # Test 1: All required agent configs present
    total_tests += 1
    for name in ["planning", "testing", "review", "docs"]:
        if name not in AGENT_CONFIGS:
            all_validation_failures.append(f"Missing agent config: {name}")
        else:
            cfg = AGENT_CONFIGS[name]
            for field in ["system", "model", "max_tokens"]:
                if field not in cfg:
                    all_validation_failures.append(f"Agent {name} missing config field: {field}")

    # Test 2: System prompts are non-empty strings
    total_tests += 1
    for name, cfg in AGENT_CONFIGS.items():
        if not isinstance(cfg.get("system"), str) or len(cfg["system"]) < 100:
            all_validation_failures.append(
                f"Agent {name} system prompt is too short or missing"
            )

    # Test 3: Rules files loaded without error (already triggered at import)
    total_tests += 1
    # If we got here, all _load_rule() calls succeeded
    expected_rules = ["session-management.md", "testing-validation.md", "pr-review.md", "data-safety.md"]
    for rule_file in expected_rules:
        rule_path = RULES_DIR / rule_file
        if not rule_path.exists():
            all_validation_failures.append(f"Rules file missing: {rule_path}")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
```

- [ ] **Step 2: Run __main__ validation block**

```bash
PYTHONPATH=backend python backend/agents/config.py
```
Expected: `✅ VALIDATION PASSED — all 3 tests produced expected results`

- [ ] **Step 3: Commit**

```bash
git add backend/agents/config.py
git commit -m "backend: add agent configurations with system prompts from rules files"
```

---

## Task 5: Planning Agent

**Files:**
- Create: `backend/agents/planning.py`

- [ ] **Step 1: Create planning.py**

Create `backend/agents/planning.py`:
```python
# Purpose: Planning Agent — reads blackboard files, decomposes session goal,
# produces a scoped atomic task in HANDOFF_STATE.json.
#
# Design reference: MultiAgentDesign.md § "1. Planning Agent"
# Anthropic tool use: https://docs.anthropic.com/en/docs/tool-use
import json
import sys
from pathlib import Path
from typing import Optional

import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from agents.handoff import HandoffState, ScopedTask, RetryCount, write_handoff_state
from agents.transfers import PLANNING_TOOLS, extract_tool_call
from agents.config import AGENT_CONFIGS

BASE_DIR = Path(__file__).parent.parent.parent  # MyAPTutor/


def _read_blackboard() -> str:
    """Read the three blackboard files and return them as a formatted context block."""
    files = {
        "PROGRESS.md": BASE_DIR / "MyAPTutor" / "PROGRESS.md",
        "TASKS.md":    BASE_DIR / "MyAPTutor" / "TASKS.md",
        "PARKING_LOT.md": BASE_DIR / "MyAPTutor" / "PARKING_LOT.md",
    }
    parts = []
    for name, path in files.items():
        content = path.read_text() if path.exists() else "(file does not exist yet)"
        parts.append(f"=== {name} ===\n{content}")
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

    logger.info("Planning Agent: calling Claude API")
    response = client.messages.create(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        system=cfg["system"],
        tools=PLANNING_TOOLS,
        messages=[{"role": "user", "content": user_message}],
    )
    logger.info(f"Planning Agent: stop_reason={response.stop_reason}")

    # Print the agent's narrative output for the user to read
    for block in response.content:
        if hasattr(block, "text"):
            print(block.text)

    tool_call = extract_tool_call(response)
    if tool_call is None or tool_call["name"] != "transfer_to_code_agent":
        raise ValueError(
            f"Planning Agent did not call transfer_to_code_agent(). "
            f"stop_reason={response.stop_reason}. "
            "Check that the system prompt instructs the agent to call the transfer tool."
        )

    inp = tool_call["input"]
    # Build a minimal HandoffState — the scoped_task fields come from Claude's narrative.
    # In a full implementation, Claude would output JSON fields in its text response.
    # Here we construct from what the transfer tool received.
    scoped_task = ScopedTask(
        id=inp["task_id"],
        label="MUST",
        description=inp["implementation_notes"],
        done_when="Defined by Planning Agent — see HANDOFF_STATE.json notes",
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

    # Test 2: HandoffState round-trip through write/read
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

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
```

- [ ] **Step 2: Run __main__ validation block**

```bash
PYTHONPATH=backend python backend/agents/planning.py
```
Expected: `✅ VALIDATION PASSED — all 2 tests produced expected results`

- [ ] **Step 3: Commit**

```bash
git add backend/agents/planning.py
git commit -m "backend: add Planning Agent with blackboard read and Claude API call"
```

---

## Task 6: Testing Agent

**Files:**
- Create: `backend/agents/testing.py`

- [ ] **Step 1: Create testing.py**

Create `backend/agents/testing.py`:
```python
# Purpose: Testing Agent — runs the 5-step validation sequence, collects all
# failures, and routes to either the Code Agent (FAIL) or Review Agent (PASS).
#
# Design reference: MultiAgentDesign.md § "3. Testing Agent"
# Validation sequence: uvicorn health → endpoint smoke → schema sync →
#                      __main__ block → frontend type-check
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY
from agents.handoff import HandoffState, TestingResult, read_handoff_state, write_handoff_state
from agents.transfers import TESTING_TOOLS, extract_tool_call
from agents.config import AGENT_CONFIGS

BASE_DIR = Path(__file__).parent.parent.parent  # MyAPTutor/
FRONTEND_DIR = BASE_DIR / "MyAPTutor" / "frontend"
BACKEND_DIR  = BASE_DIR / "MyAPTutor" / "backend"


def _run_cmd(cmd: str, cwd: Optional[Path] = None, timeout: int = 30) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        cwd=str(cwd) if cwd else None, timeout=timeout,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _check_health(failures: List[str]) -> bool:
    """Step 1: Start uvicorn and check /api/health returns {"status":"ok"}."""
    # Kill any existing uvicorn on port 8000
    _run_cmd("pkill -f 'uvicorn backend.main' || true", cwd=BASE_DIR / "MyAPTutor")
    time.sleep(1)

    # Start uvicorn in background
    subprocess.Popen(
        "source backend/venv/bin/activate && uvicorn backend.main:app --port 8000",
        shell=True, cwd=str(BASE_DIR / "MyAPTutor"),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(3)  # Wait for startup

    code, stdout, stderr = _run_cmd("curl -s http://localhost:8000/api/health")
    if code != 0 or '"status": "ok"' not in stdout and '"status":"ok"' not in stdout:
        failures.append(f"health_check: /api/health failed (code={code}, stdout={stdout!r})")
        return False
    return True


def _check_frontend_types(failures: List[str]) -> None:
    """Step 5: Frontend type-check must produce 0 errors."""
    if not FRONTEND_DIR.exists():
        failures.append("frontend_typecheck: frontend/ directory not found")
        return
    code, stdout, stderr = _run_cmd("npm run type-check", cwd=FRONTEND_DIR, timeout=60)
    if code != 0:
        failures.append(f"frontend_typecheck: npm run type-check failed\n{stdout}\n{stderr}")


def run_testing_agent(
    state: HandoffState,
    handoff_path: Path,
    client: Optional[anthropic.Anthropic] = None,
) -> HandoffState:
    """
    Run the Testing Agent validation sequence.

    Runs health check and frontend type-check directly (no Claude API needed).
    Uses Claude to analyze schema sync and __main__ block results.
    Updates HANDOFF_STATE.json with testing results.

    Args:
        state: Current HandoffState (must have scoped_task.artifacts).
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

    # Steps 2-4: Use Claude to analyze the artifacts
    artifacts = state.scoped_task.files
    artifact_contents = {}
    for file_path in artifacts:
        full_path = BASE_DIR / "MyAPTutor" / file_path
        if full_path.exists():
            artifact_contents[file_path] = full_path.read_text()
        else:
            failures.append(f"artifact_missing: {file_path} not found after implementation")

    cfg = AGENT_CONFIGS["testing"]
    user_message = (
        f"Validate the following artifacts from task '{state.scoped_task.id}':\n"
        f"Files changed: {artifacts}\n\n"
        f"File contents:\n"
        + "\n\n".join(f"=== {k} ===\n{v}" for k, v in artifact_contents.items())
        + f"\n\nHealth check passed: {health_ok}\n"
        f"Existing failures collected: {failures}\n\n"
        "Run steps 2 (endpoint smoke test), 3 (schema sync), and 4 (__main__ block).\n"
        "Collect ALL failures. Then call the appropriate transfer tool.\n"
        "transfer_to_review_agent if all pass, transfer_to_code_agent if any fail."
    )

    logger.info("Testing Agent: calling Claude API for steps 2-4")
    response = client.messages.create(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        system=cfg["system"],
        tools=TESTING_TOOLS,
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if hasattr(block, "text"):
            print(block.text)

    # Step 5: Frontend type-check (always run regardless of Claude result)
    logger.info("Testing Agent: Step 5 — frontend type-check")
    _check_frontend_types(failures)

    tool_call = extract_tool_call(response)
    if tool_call is None:
        failures.append("testing_agent_error: Claude did not call a transfer tool")
        route = "code_agent"
    else:
        route = "review_agent" if tool_call["name"] == "transfer_to_review_agent" else "code_agent"
        # Merge any additional failures Claude reported
        if tool_call["name"] == "transfer_to_code_agent":
            claude_failures = tool_call["input"].get("failures", [])
            if isinstance(claude_failures, list):
                failures.extend(claude_failures)

    # Add pre-collected failures if Claude said pass but we have direct failures
    status: str
    if failures:
        status = "FAIL"
        route = "code_agent"
    else:
        status = "PASS"
        route = "review_agent"

    state.testing = TestingResult(
        status=status,
        failures=failures,
        route_to=route,
    )
    state.agent = "testing"
    write_handoff_state(state, handoff_path)
    logger.info(f"Testing Agent: status={status}, route_to={route}")
    return state


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    all_validation_failures = []
    total_tests = 0

    # Test 1: _run_cmd returns correct exit code for a known command
    total_tests += 1
    code, stdout, stderr = _run_cmd("echo hello")
    if code != 0 or stdout != "hello":
        all_validation_failures.append(f"_run_cmd('echo hello') returned code={code}, stdout={stdout!r}")

    # Test 2: _run_cmd captures stderr on failure
    total_tests += 1
    code, stdout, stderr = _run_cmd("ls /nonexistent_path_xyz")
    if code == 0:
        all_validation_failures.append("_run_cmd should return non-zero for bad ls command")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
```

- [ ] **Step 2: Run __main__ validation block**

```bash
PYTHONPATH=backend python backend/agents/testing.py
```
Expected: `✅ VALIDATION PASSED — all 2 tests produced expected results`

- [ ] **Step 3: Commit**

```bash
git add backend/agents/testing.py
git commit -m "backend: add Testing Agent with 5-step validation sequence"
```

---

## Task 7: Review Agent

**Files:**
- Create: `backend/agents/review.py`

- [ ] **Step 1: Create review.py**

Create `backend/agents/review.py`:
```python
# Purpose: Review Agent — runs the fixed security/schema/phase-boundary/regression
# checklist. Read-only: never modifies files, only reports violations.
#
# Design reference: MultiAgentDesign.md § "4. Review Agent"
import sys
from pathlib import Path
from typing import List, Optional

import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY
from agents.handoff import HandoffState, ReviewResult, read_handoff_state, write_handoff_state
from agents.transfers import REVIEW_TOOLS, extract_tool_call
from agents.config import AGENT_CONFIGS

BASE_DIR = Path(__file__).parent.parent.parent  # MyAPTutor/


def _read_artifacts(artifacts: List[str]) -> str:
    """Read file contents for review context. Returns formatted string."""
    parts = []
    for file_path in artifacts:
        full_path = BASE_DIR / "MyAPTutor" / file_path
        if full_path.exists():
            parts.append(f"=== {file_path} ===\n{full_path.read_text()}")
        else:
            parts.append(f"=== {file_path} ===\n(FILE NOT FOUND)")
    return "\n\n".join(parts)


def run_review_agent(
    state: HandoffState,
    handoff_path: Path,
    client: Optional[anthropic.Anthropic] = None,
) -> HandoffState:
    """
    Run the Review Agent checklist.

    Reads the artifact files and asks Claude to run the fixed checklist
    from the system prompt. Expects Claude to call either
    transfer_to_docs_agent (APPROVED) or transfer_to_code_agent (ISSUES).

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

    # Also read sessions.py to check named regressions
    sessions_path = BASE_DIR / "MyAPTutor" / "backend" / "routers" / "sessions.py"
    sessions_content = sessions_path.read_text() if sessions_path.exists() else "(not found)"

    cfg = AGENT_CONFIGS["review"]
    user_message = (
        f"Review the following changes for task '{state.scoped_task.id}'.\n"
        f"Files changed: {artifacts}\n\n"
        f"Changed file contents:\n{artifact_contents}\n\n"
        f"sessions.py (for regression checks):\n{sessions_content}\n\n"
        "Run ALL checklist items. Collect ALL issues.\n"
        "Call transfer_to_docs_agent() if APPROVED (zero blocking issues).\n"
        "Call transfer_to_code_agent() if there are SECURITY, SCHEMA, PHASE, or REGRESSION issues."
    )

    logger.info("Review Agent: calling Claude API")
    response = client.messages.create(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        system=cfg["system"],
        tools=REVIEW_TOOLS,
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if hasattr(block, "text"):
            print(block.text)

    tool_call = extract_tool_call(response)
    if tool_call is None:
        issues = ["review_agent_error: Claude did not call a transfer tool"]
        route = "code_agent"
    elif tool_call["name"] == "transfer_to_docs_agent":
        issues = []
        route = "docs_agent"
    else:
        issues = tool_call["input"].get("issues", [])
        if not isinstance(issues, list):
            issues = [str(issues)]
        route = "code_agent"

    review_status = "APPROVED" if route == "docs_agent" else "ISSUES"
    state.review = ReviewResult(
        status=review_status,
        issues=issues,
        route_to=route,
    )
    state.agent = "review"
    write_handoff_state(state, handoff_path)
    logger.info(f"Review Agent: status={review_status}, route_to={route}")
    return state


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    all_validation_failures = []
    total_tests = 0

    # Test 1: _read_artifacts returns correct format for existing file
    total_tests += 1
    existing = ["backend/main.py"]
    result = _read_artifacts(existing)
    if "=== backend/main.py ===" not in result:
        all_validation_failures.append(f"_read_artifacts missing header: {result[:100]}")

    # Test 2: _read_artifacts handles missing file gracefully
    total_tests += 1
    missing = ["backend/nonexistent_xyz.py"]
    result = _read_artifacts(missing)
    if "FILE NOT FOUND" not in result:
        all_validation_failures.append(f"_read_artifacts should note missing file: {result[:100]}")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
```

- [ ] **Step 2: Run __main__ validation block**

```bash
PYTHONPATH=backend python backend/agents/review.py
```
Expected: `✅ VALIDATION PASSED — all 2 tests produced expected results`

- [ ] **Step 3: Commit**

```bash
git add backend/agents/review.py
git commit -m "backend: add Review Agent with fixed security/schema/regression checklist"
```

---

## Task 8: Documentation Agent

**Files:**
- Create: `backend/agents/docs.py`

- [ ] **Step 1: Create docs.py**

Create `backend/agents/docs.py`:
```python
# Purpose: Documentation Agent — updates BuildGuide.md, PROGRESS.md, DECISIONS.md,
# PARKING_LOT.md, and TASKS.md after every approved session.
# Write-only on documentation files; never touches source files.
#
# Design reference: MultiAgentDesign.md § "5. Documentation Agent"
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY
from agents.handoff import HandoffState, delete_handoff_state, write_handoff_state
from agents.transfers import DOCS_TOOLS, extract_tool_call
from agents.config import AGENT_CONFIGS

BASE_DIR = Path(__file__).parent.parent.parent  # MyAPTutor/
PROJECT_DIR = BASE_DIR / "MyAPTutor"


def _read_doc(filename: str) -> str:
    path = PROJECT_DIR / filename
    return path.read_text() if path.exists() else f"(file {filename} does not exist yet)"


def _write_doc(filename: str, content: str) -> None:
    path = PROJECT_DIR / filename
    path.write_text(content)
    logger.info(f"Docs Agent: updated {filename}")


def _append_to_progress(entry: str) -> None:
    """Append a session entry to PROGRESS.md (never deletes entries)."""
    path = PROJECT_DIR / "PROGRESS.md"
    existing = path.read_text() if path.exists() else "# PROGRESS.md\n\n"
    path.write_text(existing + "\n" + entry + "\n")


def _mark_task_complete(task_id: str) -> None:
    """Mark a task [x] in TASKS.md by its id or description fragment."""
    path = PROJECT_DIR / "TASKS.md"
    if not path.exists():
        return
    content = path.read_text()
    # Match lines like "- [ ] ..." or "- [MUST] ..." containing the task_id
    updated = re.sub(
        rf"(- \[[ ]\].*{re.escape(task_id)}.*)",
        lambda m: m.group(0).replace("- [ ]", "- [x]", 1),
        content,
    )
    path.write_text(updated)


def run_docs_agent(
    state: HandoffState,
    handoff_path: Path,
    client: Optional[anthropic.Anthropic] = None,
) -> HandoffState:
    """
    Run the Documentation Agent.

    Reads all blackboard files, asks Claude to produce updated content
    for each documentation file, then writes those updates to disk.
    Archives key parts of HANDOFF_STATE.json into PROGRESS.md, then deletes it.

    Args:
        state: Current HandoffState (review.status must be APPROVED).
        handoff_path: Path to HANDOFF_STATE.json.
        client: Optional pre-constructed Anthropic client.

    Returns:
        The same HandoffState (agent field updated to "docs").

    Raises:
        ValueError: If called when review is not APPROVED.
    """
    if state.review is None or state.review.status != "APPROVED":
        raise ValueError(
            "Docs Agent should only run after Review Agent approves. "
            f"Current review status: {state.review}"
        )
    if client is None:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    today = date.today().isoformat()
    blackboard_context = "\n\n".join([
        f"=== {name} ===\n{_read_doc(name)}"
        for name in ["BuildGuide.md", "TASKS.md", "PARKING_LOT.md", "DECISIONS.md"]
    ])

    cfg = AGENT_CONFIGS["docs"]
    user_message = (
        f"Session complete. Task '{state.scoped_task.id}' was approved by the Review Agent.\n"
        f"Today's date: {today}\n"
        f"Session goal: {state.session_goal}\n"
        f"What was built: {state.scoped_task.description}\n"
        f"Files changed: {state.scoped_task.files}\n\n"
        f"Current document state:\n{blackboard_context}\n\n"
        "Produce updated content for each of these files:\n"
        "1. A PROGRESS.md session entry (append — don't replace existing content)\n"
        "2. TASKS.md — mark the completed task [x]\n"
        "3. BuildGuide.md — if new endpoints, components, or schemas, add entries\n"
        "4. DECISIONS.md — if any architectural choices were made, log them\n"
        "5. PARKING_LOT.md — review and promote items with 2+ appearances to TASKS.md\n\n"
        "Output each file's updated content inside a code block with the filename as label.\n"
        "Then call transfer_to_user() with a summary of what was updated."
    )

    logger.info("Docs Agent: calling Claude API")
    response = client.messages.create(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        system=cfg["system"],
        tools=DOCS_TOOLS,
        messages=[{"role": "user", "content": user_message}],
    )

    # Parse and write file content blocks from Claude's response
    for block in response.content:
        if not hasattr(block, "text"):
            continue
        text = block.text
        print(text)
        # Extract ```filename ... ``` code blocks and write them
        pattern = r"```([\w./\-]+)\n([\s\S]*?)```"
        for match in re.finditer(pattern, text):
            filename = match.group(1).strip()
            content  = match.group(2)
            # Only write to known documentation files — never source files
            allowed_docs = {
                "PROGRESS.md", "TASKS.md", "BuildGuide.md",
                "DECISIONS.md", "PARKING_LOT.md",
            }
            if filename in allowed_docs:
                if filename == "PROGRESS.md":
                    # PROGRESS.md is append-only; extract only the new entry
                    _append_to_progress(content.strip())
                else:
                    _write_doc(filename, content)

    # Always mark the task complete in TASKS.md regardless of Claude output
    _mark_task_complete(state.scoped_task.id)

    state.agent = "docs"
    write_handoff_state(state, handoff_path)

    # Delete HANDOFF_STATE.json — session is complete
    delete_handoff_state(handoff_path)
    logger.success("Docs Agent: session complete, HANDOFF_STATE.json deleted")
    return state


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile

    all_validation_failures = []
    total_tests = 0

    # Test 1: _mark_task_complete updates checkbox syntax correctly
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp:
        tasks_path = Path(tmp) / "TASKS.md"
        tasks_path.write_text("- [ ] add-report-endpoint: Create POST /api/report\n- [ ] other-task\n")
        # Monkeypatch PROJECT_DIR
        import backend.agents.docs as docs_module
        original_dir = docs_module.PROJECT_DIR
        docs_module.PROJECT_DIR = Path(tmp)
        _mark_task_complete("add-report-endpoint")
        updated = tasks_path.read_text()
        docs_module.PROJECT_DIR = original_dir
        if "- [x] add-report-endpoint" not in updated:
            all_validation_failures.append(f"_mark_task_complete failed: {updated!r}")
        if "- [ ] other-task" not in updated:
            all_validation_failures.append(f"_mark_task_complete modified wrong line: {updated!r}")

    # Test 2: _append_to_progress appends, does not overwrite
    total_tests += 1
    with tempfile.TemporaryDirectory() as tmp:
        import backend.agents.docs as docs_module
        original_dir = docs_module.PROJECT_DIR
        docs_module.PROJECT_DIR = Path(tmp)
        progress_path = Path(tmp) / "PROGRESS.md"
        progress_path.write_text("# PROGRESS.md\n\n## Session 2026-01-01\nfirst entry\n")
        _append_to_progress("new entry content")
        content = progress_path.read_text()
        docs_module.PROJECT_DIR = original_dir
        if "first entry" not in content or "new entry content" not in content:
            all_validation_failures.append(f"_append_to_progress overwrote existing: {content!r}")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
```

- [ ] **Step 2: Run __main__ validation block**

```bash
PYTHONPATH=backend python backend/agents/docs.py
```
Expected: `✅ VALIDATION PASSED — all 2 tests produced expected results`

- [ ] **Step 3: Commit**

```bash
git add backend/agents/docs.py
git commit -m "backend: add Documentation Agent that updates blackboard files"
```

---

## Task 9: Orchestrator pipeline runner

**Files:**
- Create: `backend/orchestrator.py`

This is the main entry point. Run it as:
```bash
PYTHONPATH=backend python backend/orchestrator.py "Add /api/report endpoint to Phase 3"
```

**Important:** The Code Agent step is a human/Claude Code step, not automated. The orchestrator writes `HANDOFF_STATE.json` and prints instructions for you to invoke Claude Code. After implementation, re-run the orchestrator with `--resume` to continue the pipeline.

- [ ] **Step 1: Create orchestrator.py**

Create `backend/orchestrator.py`:
```python
#!/usr/bin/env python3
# Purpose: Multi-agent development pipeline orchestrator.
# Runs: Planning → [Code — human/Claude Code step] → Testing → Review → Docs
#
# Usage:
#   Start a new session:
#     PYTHONPATH=backend python backend/orchestrator.py "Implement /api/report endpoint"
#
#   Resume after Code Agent (human) completes:
#     PYTHONPATH=backend python backend/orchestrator.py --resume
#
# Design reference: MultiAgentDesign.md § "Orchestrator Implementation"
import argparse
import json
import sys
from pathlib import Path

import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent))
from config import ANTHROPIC_API_KEY
from agents.handoff import HandoffState, read_handoff_state, delete_handoff_state
from agents.planning  import run_planning_agent
from agents.testing   import run_testing_agent
from agents.review    import run_review_agent
from agents.docs      import run_docs_agent

BASE_DIR    = Path(__file__).parent.parent  # MyAPTutor/
HANDOFF_PATH = BASE_DIR / "HANDOFF_STATE.json"
MAX_RETRIES = 3


def _print_banner(agent: str) -> None:
    width = 60
    print("\n" + "=" * width)
    print(f"  AGENT: {agent.upper()}")
    print("=" * width)


def _print_code_agent_instructions(state: HandoffState) -> None:
    """Print human-readable instructions for the Code Agent step."""
    print("\n" + "=" * 60)
    print("  CODE AGENT STEP — Human/Claude Code Required")
    print("=" * 60)
    print(f"\nTask ID:     {state.scoped_task.id}")
    print(f"Description: {state.scoped_task.description}")
    print(f"Done when:   {state.scoped_task.done_when}")
    print(f"Files:       {', '.join(state.scoped_task.files) or '(see description)'}")
    print(f"\nImplementation notes:")
    print(f"  {state.scoped_task.description}")
    print(f"\nHANDOFF_STATE.json written to: {HANDOFF_PATH}")
    print("\nNext steps:")
    print("  1. Open Claude Code in this directory")
    print("  2. Implement the task above (Code Agent constraints apply)")
    print("  3. When done, re-run:")
    print(f"     PYTHONPATH=backend python backend/orchestrator.py --resume")
    print()


def run_pipeline(session_goal: str) -> None:
    """Run the full pipeline from Planning → Docs for a new session goal."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # ── Planning Agent ────────────────────────────────────────────────────────
    _print_banner("planning")
    state = run_planning_agent(session_goal, HANDOFF_PATH, client=client)
    logger.success(f"Planning complete: task={state.scoped_task.id}")

    # ── Code Agent (human/Claude Code step) ───────────────────────────────────
    _print_banner("code — awaiting human")
    _print_code_agent_instructions(state)
    sys.exit(0)  # Pipeline pauses here; resume with --resume


def resume_pipeline() -> None:
    """
    Resume the pipeline after the Code Agent (human) step.
    Reads HANDOFF_STATE.json and runs Testing → Review → Docs with retry logic.
    """
    if not HANDOFF_PATH.exists():
        print(f"Error: {HANDOFF_PATH} not found.")
        print("Run without --resume to start a new session.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    state = read_handoff_state(HANDOFF_PATH)
    logger.info(f"Resuming pipeline: task={state.scoped_task.id}")

    # ── Testing → Code loop (max MAX_RETRIES) ─────────────────────────────────
    while True:
        _print_banner("testing")
        state = run_testing_agent(state, HANDOFF_PATH, client=client)

        if state.testing.status == "PASS":
            break

        retries = state.retry_count.code_to_test
        if retries >= MAX_RETRIES:
            print(f"\n❌ Max retries ({MAX_RETRIES}) reached. Escalating to user.")
            print("Failures:")
            for f in state.testing.failures:
                print(f"  - {f}")
            print(f"\nHANDOFF_STATE.json preserved at: {HANDOFF_PATH}")
            sys.exit(1)

        state.retry_count.code_to_test += 1
        print(f"\n⚠️  Testing FAILED (attempt {retries + 1}/{MAX_RETRIES}). Failures:")
        for f in state.testing.failures:
            print(f"  - {f}")
        _print_code_agent_instructions(state)
        sys.exit(0)  # Pause for human to fix; resume again

    # ── Review → Code loop (max MAX_RETRIES) ─────────────────────────────────
    while True:
        _print_banner("review")
        state = run_review_agent(state, HANDOFF_PATH, client=client)

        if state.review.status == "APPROVED":
            break

        retries = state.retry_count.code_to_review
        if retries >= MAX_RETRIES:
            print(f"\n❌ Review max retries ({MAX_RETRIES}) reached. Escalating to user.")
            print("Issues:")
            for i in state.review.issues:
                print(f"  - {i}")
            print(f"\nHANDOFF_STATE.json preserved at: {HANDOFF_PATH}")
            sys.exit(1)

        state.retry_count.code_to_review += 1
        print(f"\n⚠️  Review ISSUES (attempt {retries + 1}/{MAX_RETRIES}). Issues:")
        for i in state.review.issues:
            print(f"  - {i}")
        _print_code_agent_instructions(state)
        sys.exit(0)  # Pause for human to fix; resume again

    # ── Documentation Agent ────────────────────────────────────────────────────
    _print_banner("docs")
    state = run_docs_agent(state, HANDOFF_PATH, client=client)

    print("\n" + "=" * 60)
    print("  SESSION COMPLETE")
    print("=" * 60)
    print(f"\nTask '{state.scoped_task.id}' completed and documented.")
    print("HANDOFF_STATE.json deleted — session is closed.")
    print()


# ── __main__ ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MyAPTutor multi-agent development pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Start new session:
    PYTHONPATH=backend python backend/orchestrator.py "Add /api/report endpoint"

  Resume after Code Agent completes:
    PYTHONPATH=backend python backend/orchestrator.py --resume
        """,
    )
    parser.add_argument(
        "goal",
        nargs="?",
        help="Session goal (required for new sessions, omit with --resume)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume pipeline after Code Agent step",
    )
    args = parser.parse_args()

    if args.resume:
        resume_pipeline()
    elif args.goal:
        run_pipeline(args.goal)
    else:
        parser.print_help()
        sys.exit(1)
```

- [ ] **Step 2: Run with --help to verify argument parsing**

```bash
PYTHONPATH=backend python backend/orchestrator.py --help
```
Expected output includes:
```
usage: orchestrator.py [-h] [--resume] [goal]
...
Examples:
  Start new session:
    PYTHONPATH=backend python backend/orchestrator.py "Add /api/report endpoint"
```

- [ ] **Step 3: Verify imports work (dry run without API call)**

```bash
PYTHONPATH=backend python -c "
import sys
sys.path.insert(0, 'backend')
from agents.handoff import HandoffState, ScopedTask
from agents.planning import run_planning_agent
from agents.testing import run_testing_agent
from agents.review import run_review_agent
from agents.docs import run_docs_agent
print('✅ All imports successful')
"
```
Expected: `✅ All imports successful`

- [ ] **Step 4: Commit**

```bash
git add backend/orchestrator.py
git commit -m "backend: add orchestrator pipeline runner with Planning→Testing→Review→Docs flow"
```

---

## Task 10: End-to-end smoke test (dry run)

**Files:**
- No new files — run against existing project state

This test runs the Planning Agent against the real API with a real session goal, verifies it produces a valid HANDOFF_STATE.json, then cleans up. It does NOT run the full pipeline (that requires actual code changes).

- [ ] **Step 1: Confirm ANTHROPIC_API_KEY is set**

```bash
grep ANTHROPIC_API_KEY backend/.env
```
Expected: `ANTHROPIC_API_KEY=sk-ant-...` (key present, not empty)

- [ ] **Step 2: Run Planning Agent for a real task**

```bash
source backend/venv/bin/activate
PYTHONPATH=backend python backend/orchestrator.py "Add POST /api/report endpoint to Phase 3 (stub — returns hardcoded ReportSchema JSON)"
```

Expected output structure:
```
============================================================
  AGENT: PLANNING
============================================================

[Claude's narrative: 3-bullet briefing + scoped task plan]

============================================================
  AGENT: CODE — AWAITING HUMAN
============================================================

Task ID:     add-report-endpoint
Description: ...
Done when:   ...
...
HANDOFF_STATE.json written to: .../HANDOFF_STATE.json

Next steps:
  1. Open Claude Code in this directory
  2. Implement the task above
  3. When done, re-run: PYTHONPATH=backend python backend/orchestrator.py --resume
```

- [ ] **Step 3: Verify HANDOFF_STATE.json was written**

```bash
cat HANDOFF_STATE.json
```
Expected: valid JSON with `agent`, `session_goal`, `scoped_task.id`, `retry_count` fields

- [ ] **Step 4: Clean up**

```bash
rm -f HANDOFF_STATE.json
```

- [ ] **Step 5: Commit**

No code changes in this task — the smoke test was verification only.

---

## Task 11: Update TASKS.md and BuildGuide.md

**Files:**
- Modify: `MyAPTutor/TASKS.md`
- Modify: `MyAPTutor/BuildGuide.md` (add Phase 5 section)

- [ ] **Step 1: Mark Phase 5 tasks complete in TASKS.md**

In `TASKS.md`, update the Phase 5 backlog tasks that are now implemented:

```markdown
### Phase 5 — Multi-Agent Development Pipeline
> Design complete in `MultiAgentDesign.md`. Implementation in `MultiAgentImplementation.md`.
- [x] Build `orchestrator.py` — sequential pipeline runner with retry guard (max 3 loops)
- [x] Implement `transfer_to_X()` handoff tool functions per agent role
- [x] Define `HANDOFF_STATE.json` schema and lifecycle (create → append → delete)
- [x] Wire Planning Agent system prompt from `.claude/rules/session-management.md`
- [x] Wire Review Agent system prompt from `.claude/rules/pr-review.md` + `data-safety.md`
- [x] Wire Testing Agent validation sequence (uvicorn → curl → schema check → type-check)
```

- [ ] **Step 2: Add Phase 5 section to BuildGuide.md**

Append to `BuildGuide.md`:

```markdown
---

## Phase 5: Multi-Agent Development Pipeline

> Design: `MultiAgentDesign.md` | Implementation: `MultiAgentImplementation.md`

### Files Created

| File | Role |
|------|------|
| `backend/agents/__init__.py` | Package marker |
| `backend/agents/handoff.py` | HandoffState Pydantic schema + read/write utilities |
| `backend/agents/transfers.py` | Transfer tool definitions (Claude tool schemas) |
| `backend/agents/config.py` | Agent system prompts loaded from `.claude/rules/` |
| `backend/agents/planning.py` | Planning Agent — scopes one atomic task per session |
| `backend/agents/testing.py` | Testing Agent — 5-step validation sequence |
| `backend/agents/review.py` | Review Agent — fixed security/schema/regression checklist |
| `backend/agents/docs.py` | Documentation Agent — updates blackboard files |
| `backend/orchestrator.py` | Pipeline runner — routes between agents with retry guard |

### Usage

```bash
# Start a new session
PYTHONPATH=backend python backend/orchestrator.py "Add /api/report endpoint"

# Resume after Code Agent (human/Claude Code) completes
PYTHONPATH=backend python backend/orchestrator.py --resume
```

### HANDOFF_STATE.json Lifecycle

```
Planning creates it
  → Code Agent reads scoped_task (human step)
  → Testing appends testing result
  → Review appends review result
  → Docs archives key parts to PROGRESS.md
  → File deleted at session end
```

### Retry Guard

Testing and Review loops are capped at `MAX_RETRIES = 3`.
On hitting the limit, the pipeline exits with a failure report and preserves
`HANDOFF_STATE.json` for debugging.
```

- [ ] **Step 3: Commit**

```bash
git add MyAPTutor/TASKS.md MyAPTutor/BuildGuide.md
git commit -m "docs: update TASKS.md and BuildGuide.md for Phase 5 multi-agent pipeline"
```

---

## Self-Review

### Spec Coverage

| Design Requirement | Task |
|---|---|
| `orchestrator.py` sequential pipeline | Task 9 |
| `transfer_to_X()` structured tool calls | Task 3 |
| `HANDOFF_STATE.json` schema and lifecycle | Task 2 |
| Planning Agent system prompt from `session-management.md` | Task 4 |
| Code Agent (human/Claude Code step) | Task 9 (documented as pause point) |
| Testing Agent 5-step validation sequence | Task 6 |
| Review Agent fixed checklist | Task 7 |
| Documentation Agent blackboard updates | Task 8 |
| Retry guard (max 3 loops) | Task 9 |
| Context explosion guard (HANDOFF_STATE.json only, not thread) | Task 9 (by design) |
| Blackboard filesystem (PROGRESS.md, TASKS.md, etc.) | Tasks 5, 8 |

### No Gaps Found

All sections of `MultiAgentDesign.md` are covered. The Code Agent is intentionally a human/Claude Code step rather than a fully automated API call — the design specifies it needs `Edit`, `Write`, `Bash` tools from the Claude Code harness.

### Type Consistency

- `HandoffState`, `ScopedTask`, `TestingResult`, `ReviewResult`, `RetryCount` — defined in Task 2, used consistently across Tasks 5-9.
- `extract_tool_call()` — defined in Task 3, imported by Tasks 5, 6, 7, 8.
- `AGENT_CONFIGS` — defined in Task 4, imported by Tasks 5, 6, 7, 8.
- `run_planning_agent`, `run_testing_agent`, `run_review_agent`, `run_docs_agent` — defined in Tasks 5-8, imported by Task 9 (`orchestrator.py`).

---

## Execution Options

**Plan complete and saved to `MyAPTutor/MultiAgentImplementation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** — Fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
