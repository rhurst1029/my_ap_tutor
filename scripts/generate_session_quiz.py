"""
scripts/generate_session_quiz.py
Purpose: Generate an adaptive follow-up quiz for a student based on their last session
         report and take-home practice set. Quiz gauges improvement on practiced topics
         and adds next-step questions from the report's recommendations.
Docs: https://docs.anthropic.com/en/api/messages
Sample input:  python scripts/generate_session_quiz.py bella 4
Sample output: data/tests/generated/bella_data_test_4.json  (9-question adaptive quiz)
"""
import json, sys, re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from dotenv import load_dotenv
load_dotenv(ROOT / "backend" / ".env")
import os, anthropic
from loguru import logger

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
CLAUDE_MODEL  = "claude-opus-4-6"
GENERATED_DIR = ROOT / "data" / "tests" / "generated"

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_student_dir(name: str) -> Path:
    safe = re.sub(r'[^\w]', '_', name.lower().strip())
    return ROOT / "data" / "students" / f"{safe}_data"


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    return json.loads(text.strip())


# ── Prompt ────────────────────────────────────────────────────────────────────

QUIZ_PROMPT = """You are an expert AP Computer Science A tutor creating a personalized adaptive quiz.

Student: {student_name}
Upcoming session: {session_label}
Target duration: ~45 minutes (9 questions at ~5 minutes each based on historical pace)

## Session {prev_session} Performance Summary
{performance_summary}
Average time per question: {avg_time}s

## Topics by Confidence
STRUGGLING (highest priority — include hardest problems):
{struggling_topics}

UNCERTAIN (medium priority — moderate challenge):
{uncertain_topics}

CONFIDENT (low priority — include 1-2 warmup questions only):
{confident_topics}

## What She Practiced at Home (take-home problems from session {prev_session}):
{practice_summary}

## Recommendations from last session report:
{recommendations}

---

Generate a 9-question adaptive quiz with this exact structure:
- 3-4 questions gauging improvement on PRACTICED topics — these must be harder or novel
  variants of the take-home problems (e.g., if she practiced findMin, ask findSecondMax or
  traversal with a conditional accumulator; if she practiced BankAccount, ask about a class
  with multiple interacting methods)
- 3 questions targeting STRUGGLING/UNCERTAIN topics not covered in the take-home practice
  (push depth — e.g., sorting a parallel array, nested loop over a 2D array, class
  inheritance or multi-object interaction)
- 2 warmup questions on CONFIDENT topics at the START of the quiz to build momentum

Each question must be "code_trace" (read code, predict output) or "multiple_choice"
(conceptual reasoning). No FRQ. Order questions: warmup first, then practice-gauging,
then depth questions last.

Return a JSON object with EXACTLY this structure (raw JSON only, no markdown, no code fences):
{{
  "test_id": "{test_file_stem}",
  "title": "AP CSA \u2014 {student_name} Session {session_num} Adaptive Quiz",
  "generated_for": "{student_name}",
  "generated_at": "{now}",
  "questions": [
    {{
      "id": "q1",
      "type": "code_trace",
      "topic_tags": ["<topic>"],
      "unit": <AP CSA unit number 1-10>,
      "prompt": "<question text>",
      "code_block": "<Java snippet, or null>",
      "options": {{"A": "<text>", "B": "<text>", "C": "<text>", "D": "<text>"}},
      "answer_key": "A",
      "explanation": "<why correct, 1-2 sentences>",
      "guiding_questions": [
        {{"id": "q1_g1", "text": "<scaffolding question>"}},
        {{"id": "q1_g2", "text": "<scaffolding question>"}},
        {{"id": "q1_g3", "text": "<scaffolding question>"}}
      ]
    }}
  ]
}}

AP CSA unit reference: 1=Primitive Types, 2=Using Objects, 3=Boolean Expressions & If,
4=Iteration, 5=Writing Classes, 6=Array, 7=ArrayList, 8=2D Array,
9=Inheritance, 10=Recursion

CONSTRAINTS (violations will break the frontend):
- "options" must be an object {{A: str, B: str, C: str, D: str}} — NOT an array
- Field name is "prompt" (not "text")
- "code_block" must be present as either a string or null — never omitted
- "answer_key" must exactly match one of the four option keys (A, B, C, or D)
- Every question must have exactly 3 guiding_questions
- 9 questions total
"""


# ── Core logic ────────────────────────────────────────────────────────────────

def build_quiz(student_name: str, iteration: int) -> tuple[dict, str]:
    student_dir = get_student_dir(student_name)
    prev = iteration - 1
    report_path   = student_dir / f"report_{prev}.json"
    practice_path = student_dir / f"practice_{prev}.json"

    if not report_path.exists():
        raise FileNotFoundError(f"report_{prev}.json not found in {student_dir}")
    if not practice_path.exists():
        raise FileNotFoundError(f"practice_{prev}.json not found in {student_dir}")

    report   = json.loads(report_path.read_text())
    practice = json.loads(practice_path.read_text())

    struggling = [t for t in report["topic_analysis"] if t["confidence_level"] == "struggling"]
    uncertain  = [t for t in report["topic_analysis"] if t["confidence_level"] == "uncertain"]
    confident  = [t for t in report["topic_analysis"] if t["confidence_level"] == "confident"]

    practice_summary = "\n".join(
        f"- [{p['topic']}] {p['title']} ({p['difficulty']}): {p['task'][:140]}..."
        for p in practice["problems"]
    )

    test_file_stem = f"{student_dir.name}_test_{iteration}"

    prompt = QUIZ_PROMPT.format(
        student_name=student_name.capitalize(),
        session_label=f"Session {iteration}",
        session_num=iteration,
        prev_session=prev,
        performance_summary=report["performance_summary"],
        avg_time=int(report["average_time_seconds"]),
        struggling_topics=json.dumps(
            [{"topic": t["topic"], "avg_time_seconds": t["avg_time_seconds"], "notes": t["notes"]}
             for t in struggling], indent=2),
        uncertain_topics=json.dumps(
            [{"topic": t["topic"], "avg_time_seconds": t["avg_time_seconds"], "notes": t["notes"]}
             for t in uncertain], indent=2),
        confident_topics=json.dumps([t["topic"] for t in confident]),
        practice_summary=practice_summary,
        recommendations="\n".join(f"- {r}" for r in report["actionable_recommendations"]),
        test_file_stem=test_file_stem,
        now=datetime.now(timezone.utc).isoformat(),
    )

    logger.info(f"Calling Claude to generate quiz for {student_name} session {iteration}...")
    msg = client.messages.create(
        model=CLAUDE_MODEL, max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )
    quiz = _parse_json(msg.content[0].text)
    logger.info(f"Generated {len(quiz.get('questions', []))} questions")
    return quiz, test_file_stem


def validate_quiz(quiz: dict) -> None:
    """Raise ValueError if the quiz fails any frontend schema constraint."""
    questions = quiz.get("questions", [])
    if not questions:
        raise ValueError("No questions in quiz")
    for q in questions:
        qid = q.get("id", "?")
        assert "prompt" in q,                      f"{qid}: missing 'prompt'"
        assert isinstance(q.get("options"), dict), f"{qid}: options must be a dict"
        assert q.get("answer_key") in q["options"], f"{qid}: answer_key not in options"
        assert q.get("code_block", "MISSING") != "MISSING", f"{qid}: code_block must be present (string or null)"
        gqs = q.get("guiding_questions", [])
        assert len(gqs) == 3,                      f"{qid}: need exactly 3 guiding_questions, got {len(gqs)}"
    logger.info("Quiz schema validation passed")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    student_name = sys.argv[1] if len(sys.argv) > 1 else "bella"
    iteration    = int(sys.argv[2]) if len(sys.argv) > 2 else 4

    quiz, stem = build_quiz(student_name, iteration)
    validate_quiz(quiz)

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = GENERATED_DIR / f"{stem}.json"
    out_path.write_text(json.dumps(quiz, indent=2))
    logger.info(f"Quiz saved -> {out_path}")
    logger.info(f"test_id:    {quiz['test_id']}")
    logger.info(f"title:      {quiz.get('title')}")
    logger.info(f"Questions:  {len(quiz['questions'])}")
    for i, q in enumerate(quiz["questions"], 1):
        logger.info(f"  q{i}: [{q['type']:15s}] {str(q['topic_tags']):30s} — {q['prompt'][:65]}...")


if __name__ == "__main__":
    main()
