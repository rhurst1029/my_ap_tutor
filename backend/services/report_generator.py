"""
backend/services/report_generator.py
Purpose: Generate session performance report and practice problems for a student.
Called as a FastAPI BackgroundTask after the /save endpoint completes.
Docs: https://docs.anthropic.com/en/api/messages
Sample input:  generate_report_and_practice("Bella", "session_4")
Sample output: writes report_4.json + practice_4.json to data/students/bella_data/
"""
import json, re, os
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "backend" / ".env")

import anthropic

CLAUDE_MODEL = "claude-opus-4-6"

# ── Prompts (verbatim from scripts/generate_session_report.py) ────────────────

REPORT_PROMPT = """You are an expert AP Computer Science A tutor analyzing a student's test session.

Student: {student_name}
Session: {session_id} (Iteration {iteration})
Test duration: {duration_minutes:.1f} minutes
Score: {correct}/{total} ({score_pct}%)

Here is the complete question-by-question data including time spent per question:
{questions_json}

IMPORTANT: This student got every question correct (100% score). Your analysis must focus on TIME as the primary signal for understanding vs. struggle. A student who takes 14 minutes on a question they got right is still uncertain about that topic.

Analyze the data and return a JSON object with EXACTLY this structure (raw JSON only, no markdown, no code fences):
{{
  "overall_score_percent": <integer>,
  "performance_summary": "<2-3 sentence overall summary noting the perfect score but flagging time-based struggles>",
  "average_time_seconds": <float, average time per question>,
  "topic_analysis": [
    {{
      "topic": "<topic_name>",
      "questions_attempted": <int>,
      "questions_correct": <int>,
      "avg_time_seconds": <float>,
      "confidence_level": "confident" | "uncertain" | "struggling",
      "notes": "<specific observation about this topic based on time and answer pattern>"
    }}
  ],
  "time_analysis": {{
    "fastest_question": {{"id": "<qid>", "topic": "<topic>", "seconds": <int>, "interpretation": "<what this suggests>"}},
    "slowest_question": {{"id": "<qid>", "topic": "<topic>", "seconds": <int>, "interpretation": "<what this suggests>"}},
    "time_distribution_notes": "<overall observation about pacing patterns>"
  }},
  "strengths": ["<strength 1>", "<strength 2>"],
  "weak_topics": ["<topic1>", "<topic2>"],
  "actionable_recommendations": [
    "<specific recommendation 1>",
    "<specific recommendation 2>",
    "<specific recommendation 3>"
  ]
}}

confidence_level rules:
  "confident"  = correct AND time <= 1.5x average
  "uncertain"  = correct but time > 1.5x average, OR answered slowly but correctly
  "struggling" = incorrect, OR time > 2.5x average even if correct

weak_topics should include any topic with confidence_level "uncertain" or "struggling".
"""

PRACTICE_PROMPT = """You are an expert AP Computer Science A tutor creating targeted practice problems.

Student: {student_name}
Weak/uncertain topics identified from timing analysis: {weak_topics}
Context: {performance_notes}

Create 5 coding practice problems specifically targeting these weak areas.
These are meant to be WRITTEN/TYPED coding exercises — the student will write actual Java code, not pick multiple choice answers.

For each problem:
- It should be a small, focused coding task (5-20 lines of Java to write)
- Directly targets the weak topic
- Includes a clear task description
- Has a worked solution with line-by-line explanation
- Has 2-3 follow-up challenge variations to deepen understanding

Return a JSON object with EXACTLY this structure (raw JSON only, no markdown, no code fences):
{{
  "practice_set_id": "practice_{student_name_lower}_{session_id}",
  "generated_for": "{student_name}",
  "weak_topics_targeted": {weak_topics_json},
  "generated_at": "{now}",
  "problems": [
    {{
      "id": "p<n>",
      "topic": "<topic_tag>",
      "title": "<short problem title>",
      "difficulty": "easy" | "medium" | "hard",
      "task": "<clear description of what the student must write>",
      "starter_code": "<Java skeleton or empty class for them to fill in, or null if truly open-ended>",
      "solution": "<complete working Java solution>",
      "solution_explanation": "<line-by-line or concept-by-concept explanation of the solution>",
      "follow_up_challenges": [
        "<variation 1 that slightly extends the problem>",
        "<variation 2 that adds a twist>",
        "<variation 3 that combines with another concept>"
      ]
    }}
  ]
}}

Focus problems on the topics where the student showed the most hesitation (longest time).
Make the problems concrete and practical — real AP CSA style, not abstract.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_student_dir(name: str) -> Path:
    safe = re.sub(r'[^\w]', '_', name.lower().strip())
    return ROOT / "data" / "students" / f"{safe}_data"


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    return json.loads(text.strip())


def _build_question_summary(responses: dict, test: dict) -> list:
    summaries = []
    for r in responses["responses"]:
        q = next(q for q in test["questions"] if q["id"] == r["question_id"])
        summaries.append({
            "question_id": q["id"],
            "topic_tags": q["topic_tags"],
            "difficulty": q.get("difficulty", "medium"),
            "question_text": q.get("text") or q.get("prompt", ""),
            "code_block": q.get("code_block"),
            "selected_answer": r.get("selected_answer"),
            "correct_answer": q["answer_key"],
            "is_correct": r["is_correct"],
            "time_spent_seconds": r["time_spent_seconds"],
            "explanation": q.get("explanation", ""),
        })
    return summaries


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_report_and_practice(student_name: str, session_id: str) -> None:
    """
    Generate report_N.json and practice_N.json for a completed session.
    Safe to call as a FastAPI BackgroundTask — never raises, logs errors instead.
    """
    logger.info(f"Starting report generation for {student_name}/{session_id}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set — skipping report generation")
        return

    try:
        student_dir = _get_student_dir(student_name)
        session_dir = student_dir / session_id
        responses = json.loads((session_dir / "responses.json").read_text())
        metadata  = json.loads((session_dir / "metadata.json").read_text())

        # Resolve test file — check tests/ then tests/generated/
        test_path = ROOT / "data" / "tests" / f"{metadata['test_id']}.json"
        if not test_path.exists():
            test_path = ROOT / "data" / "tests" / "generated" / f"{metadata['test_id']}.json"
        test = json.loads(test_path.read_text())
        summaries = _build_question_summary(responses, test)

        total    = len(summaries)
        correct  = sum(1 for s in summaries if s["is_correct"])
        duration = (
            datetime.fromisoformat(metadata["completed_at"]) -
            datetime.fromisoformat(metadata["timestamp"])
        ).total_seconds() / 60

        client = anthropic.Anthropic(api_key=api_key, timeout=300.0)

        # ── Report ────────────────────────────────────────────────────────────
        report_prompt = REPORT_PROMPT.format(
            student_name=student_name.capitalize(),
            session_id=session_id,
            iteration=metadata["iteration"],
            duration_minutes=duration,
            correct=correct,
            total=total,
            score_pct=round(correct / total * 100),
            questions_json=json.dumps(summaries, indent=2),
        )
        with client.messages.stream(
            model=CLAUDE_MODEL, max_tokens=4096,
            messages=[{"role": "user", "content": report_prompt}],
        ) as stream:
            report_text = stream.get_final_text()
        report = _parse_json(report_text)
        report["report_id"]    = f"report_{metadata['iteration']}"
        report["student_name"] = student_name.capitalize()
        report["session_id"]   = session_id
        report["iteration"]    = metadata["iteration"]
        report["generated_at"] = datetime.now(timezone.utc).isoformat()
        report_path = student_dir / f"report_{metadata['iteration']}.json"
        report_path.write_text(json.dumps(report, indent=2))
        logger.info(f"Report saved -> {report_path}")

        # ── Practice problems ─────────────────────────────────────────────────
        weak_topics = report.get("weak_topics", [])
        uncertain = [t for t in report.get("topic_analysis", [])
                     if t["confidence_level"] in ("uncertain", "struggling")]
        perf_notes = "; ".join(f"{t['topic']}: {t['notes']}" for t in uncertain) \
                     or "Student showed hesitation on several topics."

        practice_prompt = PRACTICE_PROMPT.format(
            student_name=student_name.capitalize(),
            student_name_lower=student_name.lower(),
            session_id=session_id,
            weak_topics=", ".join(weak_topics),
            weak_topics_json=json.dumps(weak_topics),
            performance_notes=perf_notes,
            now=datetime.now(timezone.utc).isoformat(),
        )
        with client.messages.stream(
            model=CLAUDE_MODEL, max_tokens=8192,
            messages=[{"role": "user", "content": practice_prompt}],
        ) as stream:
            practice_text = stream.get_final_text()
        practice = _parse_json(practice_text)
        practice_path = student_dir / f"practice_{metadata['iteration']}.json"
        practice_path.write_text(json.dumps(practice, indent=2))
        logger.info(f"Practice saved -> {practice_path}")

    except Exception as e:
        logger.error(f"Report generation failed for {student_name}/{session_id}: {e}")


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "bella"
    sid  = sys.argv[2] if len(sys.argv) > 2 else "session_3"
    generate_report_and_practice(name, sid)
