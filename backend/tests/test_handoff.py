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
