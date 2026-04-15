"""
backend/services/quiz_report_generator.py
Purpose: Generate a post-quiz report (assessment + take-home + quiz analysis) and
         the next iteration's mock AP assessment test JSON.
Called as a BackgroundTask after a quiz session saves.
Docs: https://docs.anthropic.com/en/api/messages
Sample input:  generate_quiz_report_and_next_assessment("Bella", "session_2")
Sample output: data/students/bella_data/quiz_report_2.json
               data/tests/generated/bella_data_assessment_3.json
"""
import json, os, re
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Tuple
from loguru import logger
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / "backend" / ".env")
GENERATED_DIR = ROOT / "data" / "tests" / "generated"
REFERENCE_BANK_PATH = ROOT / "data" / "ap_csa_reference_bank.md"

QUIZ_REPORT_PROMPT = """You are an expert AP Computer Science A tutor writing a comprehensive progress report.

Student: {student_name}

--- ORIGINAL ASSESSMENT (Session {assessment_iteration}) ---
Score: {assessment_score}%
Weak topics identified: {weak_topics}
Assessment notes: {assessment_notes}

--- TAKE-HOME ASSIGNMENT ---
Topics covered: {takehome_topics}
Take-home responses (if available):
{takehome_responses}

--- QUIZ RESULTS (Session {quiz_iteration}) ---
Score: {quiz_score}% (weighted)
Question-by-question data:
{quiz_questions_json}

Write a JSON report with EXACTLY this structure (raw JSON, no markdown):
{{
  "report_type": "quiz_report",
  "overall_progress": "<2-3 sentence summary of overall progress from assessment to quiz>",
  "assessment_recap": {{
    "score_percent": <int>,
    "key_weaknesses": ["<topic>"],
    "notes": "<brief>"
  }},
  "takehome_analysis": {{
    "topics_covered": ["<topic>"],
    "estimated_impact": "strong" | "moderate" | "minimal",
    "notes": "<how well did the take-home address the weaknesses?>"
  }},
  "quiz_analysis": {{
    "score_percent": <int (weighted)>,
    "improvement_topics": ["<topics that improved>"],
    "still_weak_topics": ["<topics still struggling>"],
    "topic_analysis": [
      {{
        "topic": "<topic>",
        "assessment_confidence": "confident" | "uncertain" | "struggling",
        "quiz_confidence": "confident" | "uncertain" | "struggling",
        "improved": true | false,
        "notes": "<specific observation>"
      }}
    ]
  }},
  "next_session_recommendations": [
    "<specific recommendation 1>",
    "<specific recommendation 2>"
  ],
  "weak_topics_for_next_assessment": ["<topic1>", "<topic2>"]
}}
"""

NEXT_ASSESSMENT_PROMPT = """You are an expert AP Computer Science A exam writer creating a mock AP exam.

Student: {student_name}
Still-weak topics (from quiz report): {weak_topics}
Student history summary: {history_summary}

Reference bank excerpt for context:
---
{reference_bank_excerpt}
---

Create 15 adaptive multiple-choice questions targeting the student's weak topics.

Rules:
1. At least 8 questions must directly target topics in weak_topics
2. Remaining questions cover a mix of other AP CSA topics
3. Include a mix of concept questions and short code-trace questions
4. Every question must have a concise explanation (1-2 sentences)
5. CRITICAL JSON RULES: All string values must be valid JSON. Escape newlines as \\n and quotes as \\". Do NOT use actual newline characters inside string values.

Return ONLY raw JSON (no markdown fences, no text before or after):
{{
  "questions": [
    {{
      "id": "mock_q1",
      "type": "multiple_choice",
      "topic_tags": ["<topic>"],
      "unit": <1-10>,
      "prompt": "<question text — single line, no newlines>",
      "code_block": "<Java snippet with \\n for newlines, or null>",
      "options": {{"A": "<>", "B": "<>", "C": "<>", "D": "<>"}},
      "answer_key": "<A|B|C|D>",
      "explanation": "<1-2 sentence explanation>",
      "guiding_questions": [{{"id": "mock_q1_g1", "text": "<hint>"}}]
    }}
  ]
}}
"""


def _load_takehome_responses(student_dir: Path, iteration: int) -> Tuple[List, str]:
    """Load take-home responses file if it exists. Returns (topics, summary_text)."""
    takehome_dir = student_dir / f"takehome_{iteration}"
    responses_file = takehome_dir / "questions_and_responses.txt"
    if not responses_file.exists():
        return [], "Take-home responses not submitted."
    data = json.loads(responses_file.read_text())
    responses = data.get("responses", [])
    summary = json.dumps(responses, indent=2)[:2000]  # cap at 2000 chars
    topics = list({r.get("topic", "") for r in responses if r.get("topic")})
    return topics, summary


def _load_assessment_report(student_dir: Path, assessment_iteration: int) -> dict:
    report_path = student_dir / f"report_{assessment_iteration}.json"
    if not report_path.exists():
        return {}
    return json.loads(report_path.read_text())


def _extract_reference_sections(topics: List[str]) -> str:
    if not REFERENCE_BANK_PATH.exists():
        return ""
    content = REFERENCE_BANK_PATH.read_text()
    excerpts = []
    for topic in topics[:3]:  # limit to 3 topics to keep prompt size reasonable
        escaped = re.escape(topic.replace('_', ' '))
        pattern = re.compile(
            r'(#{1,3}\s+.*?' + escaped + r'.*?\n)(.*?)(?=\n#{1,3}\s|\Z)',
            re.IGNORECASE | re.DOTALL
        )
        for heading, body in pattern.findall(content):
            excerpts.append(f"{heading}{body[:600].strip()}")
    return "\n\n---\n\n".join(excerpts) if excerpts else ""


def generate_quiz_report_and_next_assessment(
    student_name: str, session_id: str
) -> None:
    """
    Generate post-quiz report and next mock AP assessment.
    Safe as a FastAPI BackgroundTask — logs errors, never raises.
    """
    logger.info(f"Starting quiz report generation for {student_name}/{session_id}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not set — skipping quiz report")
        return

    try:
        import anthropic
        from config import STUDENTS_DIR

        safe = re.sub(r'[^\w]', '_', student_name.lower().strip())
        student_dir = STUDENTS_DIR / f"{safe}_data"
        session_dir = student_dir / session_id
        quiz_iteration = int(session_id.split("_")[1])
        assessment_iteration = quiz_iteration - 1  # assessment was the previous session

        responses = json.loads((session_dir / "responses.json").read_text())
        metadata = json.loads((session_dir / "metadata.json").read_text())

        # Load the quiz test file
        test_id = metadata["test_id"]
        test_path = GENERATED_DIR / f"{test_id}.json"
        if not test_path.exists():
            test_path = ROOT / "data" / "tests" / f"{test_id}.json"
        test = json.loads(test_path.read_text())

        # Build quiz question summaries
        summaries = []
        for r in responses["responses"]:
            q = next((q for q in test["questions"] if q["id"] == r["question_id"]), None)
            if q:
                summaries.append({
                    "question_id": q["id"],
                    "topic_tags": q["topic_tags"],
                    "prompt": q.get("prompt", ""),
                    "selected_answer": r.get("selected_answer"),
                    "correct_answer": q["answer_key"],
                    "is_correct": r["is_correct"],
                    "attempt_number": r.get("attempt_number", 1),
                    "score_weight": r.get("score_weight", 1.0 if r["is_correct"] else 0.0),
                    "time_spent_seconds": r["time_spent_seconds"],
                })

        total = len(summaries)
        weighted_score = sum(s["score_weight"] for s in summaries)
        quiz_score_pct = round((weighted_score / total) * 100) if total else 0

        # Load assessment report and take-home data
        assessment_report = _load_assessment_report(student_dir, assessment_iteration)
        takehome_topics, takehome_responses_text = _load_takehome_responses(
            student_dir, assessment_iteration
        )

        client = anthropic.Anthropic(api_key=api_key, timeout=300.0)

        # ── Quiz report ───────────────────────────────────────────────────────
        report_prompt = QUIZ_REPORT_PROMPT.format(
            student_name=student_name.capitalize(),
            assessment_iteration=assessment_iteration,
            assessment_score=assessment_report.get("overall_score_percent", "?"),
            weak_topics=", ".join(assessment_report.get("weak_topics", [])),
            assessment_notes=assessment_report.get("performance_summary", ""),
            quiz_iteration=quiz_iteration,
            quiz_score=quiz_score_pct,
            quiz_questions_json=json.dumps(summaries, indent=2),
            takehome_topics=", ".join(takehome_topics) if takehome_topics else "unknown",
            takehome_responses=takehome_responses_text,
        )

        with client.messages.stream(
            model="claude-opus-4-6", max_tokens=4096,
            messages=[{"role": "user", "content": report_prompt}],
        ) as stream:
            raw = stream.get_final_text().strip()

        if raw.startswith("```"):
            raw = re.sub(r'^```[a-z]*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
        raw = raw.strip()
        brace_start = raw.find('{')
        if brace_start != -1:
            depth = 0
            for i, ch in enumerate(raw[brace_start:], brace_start):
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        raw = raw[brace_start:i + 1]
                        break
        quiz_report = json.loads(raw)
        quiz_report["report_id"] = f"quiz_report_{quiz_iteration}"
        quiz_report["student_name"] = student_name.capitalize()
        quiz_report["session_id"] = session_id
        quiz_report["iteration"] = quiz_iteration
        quiz_report["generated_at"] = datetime.now(timezone.utc).isoformat()

        report_path = student_dir / f"quiz_report_{quiz_iteration}.json"
        report_path.write_text(json.dumps(quiz_report, indent=2))
        logger.info(f"Quiz report saved -> {report_path}")

        # ── Next assessment ───────────────────────────────────────────────────
        still_weak = quiz_report.get("weak_topics_for_next_assessment", [])
        reference_excerpt = _extract_reference_sections(still_weak)
        improvement_topics = quiz_report.get("quiz_analysis", {}).get("improvement_topics", [])
        history_summary = (
            f"Assessment score: {assessment_report.get('overall_score_percent', '?')}%. "
            f"Quiz score: {quiz_score_pct}%. "
            f"Improvement: {improvement_topics}."
        )

        next_iteration = quiz_iteration + 1
        assessment_prompt = NEXT_ASSESSMENT_PROMPT.format(
            student_name=student_name.capitalize(),
            weak_topics=", ".join(still_weak),
            history_summary=history_summary,
            reference_bank_excerpt=reference_excerpt,
        )

        with client.messages.stream(
            model="claude-opus-4-6", max_tokens=8192,
            messages=[{"role": "user", "content": assessment_prompt}],
        ) as stream:
            raw2 = stream.get_final_text().strip()

        if raw2.startswith("```"):
            raw2 = re.sub(r'^```[a-z]*\n?', '', raw2)
            raw2 = re.sub(r'\n?```$', '', raw2)
        raw2 = raw2.strip()
        brace_start2 = raw2.find('{')
        if brace_start2 != -1:
            depth2 = 0
            for i2, ch2 in enumerate(raw2[brace_start2:], brace_start2):
                if ch2 == '{':
                    depth2 += 1
                elif ch2 == '}':
                    depth2 -= 1
                    if depth2 == 0:
                        raw2 = raw2[brace_start2:i2 + 1]
                        break
        assessment_data = json.loads(raw2)

        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        assessment_id = f"{student_dir.name}_assessment_{next_iteration}"
        next_assessment = {
            "test_id": assessment_id,
            "title": f"{student_name.capitalize()} — Mock AP Exam (Session {next_iteration})",
            "session_type": "assessment",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "questions": assessment_data["questions"],
        }
        assessment_path = GENERATED_DIR / f"{assessment_id}.json"
        assessment_path.write_text(json.dumps(next_assessment, indent=2))
        logger.info(f"Next assessment saved -> {assessment_path}")

    except Exception as e:
        logger.error(f"Quiz report generation failed for {student_name}/{session_id}: {e}")


if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "bella"
    sid = sys.argv[2] if len(sys.argv) > 2 else "session_2"
    generate_quiz_report_and_next_assessment(name, sid)
