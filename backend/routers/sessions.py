import re, json, shutil
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pathlib import Path
from datetime import datetime, timezone
from config import STUDENTS_DIR, TESTS_DIR
from models.session import SessionStartRequest, SessionSaveRequest
from services.report_generator import generate_report_and_practice

router = APIRouter()

ADMIN_NAME        = "Admin"
ASSESSMENT_TEST   = "ap_csa_assessment"   # standard first test for all students
GENERATED_DIR     = TESTS_DIR / "generated"


def is_admin(name: str) -> bool:
    return normalize_name(name) == ADMIN_NAME

def normalize_name(name: str) -> str:
    return name.strip().title()

def get_student_dir(name: str) -> Path:
    safe = re.sub(r'[^\w]', '_', normalize_name(name).lower())
    return STUDENTS_DIR / f"{safe}_data"

QUIZ_PREFIX       = "quiz"
ASSESSMENT_PREFIX = "assessment"

def resolve_test_id(student_dir: Path, iteration: int) -> tuple:
    """
    Returns (test_id, session_type).
    Session 1 is always the standard assessment.
    Subsequent sessions check for a generated quiz first, then a generated assessment.
    """
    if iteration == 1:
        return (ASSESSMENT_TEST, "assessment")
    # Quiz check: quiz files are named {student_dir.name}_quiz_{iteration}.json
    quiz_path = GENERATED_DIR / f"{student_dir.name}_{QUIZ_PREFIX}_{iteration}.json"
    if quiz_path.exists():
        return (quiz_path.stem, "quiz")
    # Assessment check: generated assessments named {student_dir.name}_assessment_{iteration}.json
    assessment_path = GENERATED_DIR / f"{student_dir.name}_{ASSESSMENT_PREFIX}_{iteration}.json"
    if assessment_path.exists():
        return (assessment_path.stem, "assessment")
    return (ASSESSMENT_TEST, "assessment")

def next_iteration(student_dir: Path) -> int:
    """Use highest existing session number + 1 to handle abandoned sessions correctly."""
    dirs = [d for d in student_dir.glob("session_*") if d.is_dir()]
    if not dirs:
        return 1
    nums = [int(d.name.split("_")[1]) for d in dirs
            if len(d.name.split("_")) == 2 and d.name.split("_")[1].isdigit()]
    return max(nums) + 1 if nums else 1

def _cleanup_orphan(student_dir: Path) -> None:
    """Delete the last session directory if it has no responses (browser refresh ghost)."""
    dirs = sorted(student_dir.glob("session_*"), key=lambda d: d.name)
    if not dirs:
        return
    last = dirs[-1]
    if not (last / "responses.json").exists():
        meta_path = last / "metadata.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            if not meta.get("completed"):
                shutil.rmtree(last)


@router.post("/start")
async def start_session(req: SessionStartRequest):
    normalized_name = normalize_name(req.student_name)
    if is_admin(normalized_name):
        return {"session_id": "admin_preview", "iteration": 0, "test_id": ASSESSMENT_TEST}
    student_dir = get_student_dir(normalized_name)
    if student_dir.exists():
        _cleanup_orphan(student_dir)
    iteration  = next_iteration(student_dir)
    test_id, session_type = resolve_test_id(student_dir, iteration)
    session_id = f"session_{iteration}"
    session_dir = student_dir / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "audio").mkdir(exist_ok=True)
    metadata = {
        "session_id":       session_id,
        "student_name":     normalized_name,
        "test_id":          test_id,
        "iteration":        iteration,
        "session_type":     session_type,
        "phase":            "assessment",
        "timestamp":        datetime.now(timezone.utc).isoformat(),
        "total_questions":  req.total_questions,
        "completed":        False,
        "study_completed":  False,
    }
    (session_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return {"session_id": session_id, "iteration": iteration, "test_id": test_id, "session_type": session_type}


@router.post("/{student_name}/{session_id}/save")
async def save_responses(
    student_name: str,
    session_id: str,
    req: SessionSaveRequest,
    background_tasks: BackgroundTasks,
):
    if is_admin(student_name):
        return {"status": "saved"}
    session_dir = get_student_dir(student_name) / session_id
    if not session_dir.exists():
        raise HTTPException(404, "Session not found")
    (session_dir / "responses.json").write_text(json.dumps(req.dict(), indent=2))
    meta_path = session_dir / "metadata.json"
    meta = json.loads(meta_path.read_text())
    meta["completed"]    = True
    meta["completed_at"] = datetime.now(timezone.utc).isoformat()
    meta["phase"]        = "report_ready"
    meta_path.write_text(json.dumps(meta, indent=2))

    session_type = meta.get("session_type", "assessment")
    if session_type == "assessment":
        background_tasks.add_task(generate_report_and_practice, student_name, session_id)
    else:
        from services.quiz_report_generator import generate_quiz_report_and_next_assessment
        background_tasks.add_task(generate_quiz_report_and_next_assessment, student_name, session_id)
    return {"status": "saved"}


@router.patch("/{student_name}/{session_id}/phase")
async def advance_phase(student_name: str, session_id: str, body: dict):
    """Advance iteration phase: report_ready → practice_ready → quiz_ready → complete."""
    if is_admin(student_name):
        return {"status": "updated"}
    meta_path = get_student_dir(student_name) / session_id / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(404, "Session not found")
    meta = json.loads(meta_path.read_text())
    meta["phase"] = body.get("phase", meta["phase"])
    meta_path.write_text(json.dumps(meta, indent=2))
    return {"status": "updated", "phase": meta["phase"]}


@router.patch("/{student_name}/{session_id}/mark-study-complete")
async def mark_study_complete(student_name: str, session_id: str):
    if is_admin(student_name):
        return {"status": "updated"}
    meta_path = get_student_dir(student_name) / session_id / "metadata.json"
    if not meta_path.exists():
        raise HTTPException(404, "Session not found")
    meta = json.loads(meta_path.read_text())
    meta["study_completed"] = True
    meta["phase"]           = "complete"
    meta_path.write_text(json.dumps(meta, indent=2))
    return {"status": "updated"}


@router.get("/{student_name}/next-test")
async def get_next_test(student_name: str):
    """Return the test_id and iteration for this student's next session without creating it."""
    normalized = normalize_name(student_name)
    if is_admin(normalized):
        return {"test_id": ASSESSMENT_TEST, "iteration": 0, "session_type": "assessment"}
    student_dir = get_student_dir(normalized)
    if student_dir.exists():
        _cleanup_orphan(student_dir)
    iteration = next_iteration(student_dir)
    test_id, session_type = resolve_test_id(student_dir, iteration)
    return {"test_id": test_id, "iteration": iteration, "session_type": session_type}


@router.get("/{student_name}/history")
async def get_history(student_name: str):
    if is_admin(student_name):
        return {"sessions": [], "reports": []}
    student_dir = get_student_dir(student_name)
    if not student_dir.exists():
        return {"sessions": [], "reports": []}
    sessions = [json.loads((d / "metadata.json").read_text())
                for d in sorted(student_dir.glob("session_*"))
                if (d / "metadata.json").exists()]
    reports  = [json.loads(p.read_text()) for p in sorted(student_dir.glob("report_*.json"))]
    return {"sessions": sessions, "reports": reports}
