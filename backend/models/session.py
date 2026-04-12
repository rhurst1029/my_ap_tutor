from pydantic import BaseModel
from typing import Optional

class SessionStartRequest(BaseModel):
    student_name: str
    test_id: str
    total_questions: int

class GuidingQuestionResponse(BaseModel):
    guiding_question_id: str
    text_response: Optional[str] = None
    audio_file: Optional[str] = None
    transcript: Optional[str] = None
    transcript_confidence: Optional[float] = None

class QuestionResponse(BaseModel):
    question_id: str
    selected_answer: Optional[str] = None
    free_response_text: Optional[str] = None
    is_correct: bool
    time_spent_seconds: int
    guiding_question_responses: list[GuidingQuestionResponse] = []

class SessionSaveRequest(BaseModel):
    session_id: str
    student_name: str
    test_id: str
    iteration: int
    started_at: str
    completed_at: str
    responses: list[QuestionResponse]
