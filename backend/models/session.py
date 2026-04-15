from pydantic import BaseModel
from typing import Optional, Literal

# ── Iteration phase ───────────────────────────────────────────────────────────
IterationPhase = Literal[
    "assessment",     # taking the test
    "report_ready",   # test complete, report generated
    "practice_ready", # practice questions generated (Phase 3)
    "quiz_ready",     # practice quiz generated (Phase 3)
    "complete",       # full iteration done
]

# ── Session start ─────────────────────────────────────────────────────────────
class SessionStartRequest(BaseModel):
    student_name: str
    test_id: str
    total_questions: int

# ── Guiding question response (MC questions) ──────────────────────────────────
class GuidingQuestionResponse(BaseModel):
    guiding_question_id: str
    text_response: Optional[str] = None
    audio_file: Optional[str] = None
    transcript: Optional[str] = None
    transcript_confidence: Optional[float] = None

# ── FRQ run attempt ───────────────────────────────────────────────────────────
class FRQRunAttempt(BaseModel):
    attempt_number: int
    code_snapshot: str
    stdout: str
    stderr: str
    compile_errors: list[str] = []
    passed: bool
    timestamp: str

# ── FRQ part response (rich behavioral metadata) ──────────────────────────────
class FRQPartResponse(BaseModel):
    part: str                                   # "a", "b", "c"
    final_code: str
    passed: bool
    total_runs: int
    total_time_seconds: int
    time_to_first_keystroke_seconds: int
    run_attempts: list[FRQRunAttempt] = []
    compile_errors_encountered: list[str] = []  # all unique errors seen
    line_time_map: dict[str, int] = {}           # line number → seconds
    line_edit_counts: dict[str, int] = {}        # line number → edit count
    struggled_lines: list[int] = []              # lines with high time or edit count

# ── MC question response ──────────────────────────────────────────────────────
class QuestionResponse(BaseModel):
    question_id: str
    question_type: Literal["multiple_choice", "code_trace", "frq"] = "multiple_choice"
    selected_answer: Optional[str] = None        # MC / code_trace
    frq_parts: list[FRQPartResponse] = []        # FRQ only
    is_correct: bool
    time_spent_seconds: int
    guiding_question_responses: list[GuidingQuestionResponse] = []

# ── Full session save payload ─────────────────────────────────────────────────
class SessionSaveRequest(BaseModel):
    session_id: str
    student_name: str
    test_id: str
    iteration: int
    started_at: str
    completed_at: str
    responses: list[QuestionResponse]
