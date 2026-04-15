from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
from config import TESTS_DIR

router = APIRouter()

@router.get("/")
async def list_tests():
    return [
        {"test_id": json.loads(f.read_text())["test_id"],
         "title":   json.loads(f.read_text())["title"]}
        for f in TESTS_DIR.glob("*.json")
    ]

@router.get("/{test_id}")
async def get_test(test_id: str):
    path = TESTS_DIR / f"{test_id}.json"
    if not path.exists():
        path = TESTS_DIR / "generated" / f"{test_id}.json"
    if not path.exists():
        raise HTTPException(404, "Test not found")
    return json.loads(path.read_text())

class AnswerCheckRequest(BaseModel):
    answer: str

@router.post("/{test_id}/check/{question_id}")
async def check_answer(test_id: str, question_id: str, body: AnswerCheckRequest):
    path = TESTS_DIR / f"{test_id}.json"
    if not path.exists():
        raise HTTPException(404, "Test not found")
    data = json.loads(path.read_text())
    q = next((q for q in data["questions"] if q["id"] == question_id), None)
    if not q:
        raise HTTPException(404, "Question not found")
    return {"is_correct": body.answer == q["answer_key"], "correct_answer": q["answer_key"]}
