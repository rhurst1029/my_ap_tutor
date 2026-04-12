"""
Generate a performance report and practice questions for a student's session.
Usage: python scripts/generate_session_report.py bella session_3
"""
import json, sys, re
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv
load_dotenv(ROOT / "backend" / ".env")

import os, anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
CLAUDE_MODEL = "claude-opus-4-6"

def get_student_dir(name: str) -> Path:
    safe = re.sub(r'[^\w]', '_', name.lower().strip())
    return ROOT / "data" / "students" / f"{safe}_data"

def load_session(student_name: str, session_id: str):
    d = get_student_dir(student_name) / session_id
    responses = json.loads((d / "responses.json").read_text())
    metadata  = json.loads((d / "metadata.json").read_text())
    return responses, metadata

def load_test(test_id: str):
    return json.loads((ROOT / "data" / "tests" / f"{test_id}.json").read_text())

def _parse_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    return json.loads(text.strip())

def build_question_summary(responses: dict, test: dict) -> list[dict]:
    summaries = []
    for r in responses["responses"]:
        q = next(q for q in test["questions"] if q["id"] == r["question_id"])
        summaries.append({
            "question_id": q["id"],
            "topic_tags": q["topic_tags"],
            "difficulty": q["difficulty"],
            "question_text": q["text"],
            "code_block": q.get("code_block"),
            "selected_answer": r.get("selected_answer"),
            "correct_answer": q["answer_key"],
            "is_correct": r["is_correct"],
            "time_spent_seconds": r["time_spent_seconds"],
            "explanation": q.get("explanation", "")
        })
    return summaries


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

Focus problems on the topics where Bella showed the most hesitation (longest time).
Make the problems concrete and practical — real AP CSA style, not abstract.
"""

def main():
    student_name = sys.argv[1] if len(sys.argv) > 1 else "bella"
    session_id   = sys.argv[2] if len(sys.argv) > 2 else "session_3"

    print(f"Loading session data for {student_name} / {session_id}...")
    responses, metadata = load_session(student_name, session_id)
    test = load_test(metadata["test_id"])
    summaries = build_question_summary(responses, test)

    total    = len(summaries)
    correct  = sum(1 for s in summaries if s["is_correct"])
    duration = (
        datetime.fromisoformat(metadata["completed_at"]) -
        datetime.fromisoformat(metadata["timestamp"])
    ).total_seconds() / 60

    print(f"Score: {correct}/{total} | Duration: {duration:.1f} min")
    print("Generating report with Claude...")

    report_prompt = REPORT_PROMPT.format(
        student_name=student_name.capitalize(),
        session_id=session_id,
        iteration=metadata["iteration"],
        duration_minutes=duration,
        correct=correct,
        total=total,
        score_pct=round(correct / total * 100),
        questions_json=json.dumps(summaries, indent=2)
    )

    msg = client.messages.create(
        model=CLAUDE_MODEL, max_tokens=4096,
        messages=[{"role": "user", "content": report_prompt}]
    )
    report = _parse_json(msg.content[0].text)
    report["report_id"]   = f"report_{metadata['iteration']}"
    report["student_name"] = student_name.capitalize()
    report["session_id"]   = session_id
    report["iteration"]    = metadata["iteration"]
    report["generated_at"] = datetime.now(timezone.utc).isoformat()

    student_dir = get_student_dir(student_name)
    report_path = student_dir / f"report_{metadata['iteration']}.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(f"Report saved -> {report_path}")

    weak_topics = report.get("weak_topics", [])
    print(f"Weak topics identified: {weak_topics}")

    # Build performance notes for practice prompt
    uncertain = [
        t for t in report.get("topic_analysis", [])
        if t["confidence_level"] in ("uncertain", "struggling")
    ]
    perf_notes = "; ".join(
        f"{t['topic']}: {t['notes']}" for t in uncertain
    ) or "Student answered all correctly but showed hesitation on several topics."

    print("Generating practice problems with Claude...")
    practice_prompt = PRACTICE_PROMPT.format(
        student_name=student_name.capitalize(),
        student_name_lower=student_name.lower(),
        session_id=session_id,
        weak_topics=", ".join(weak_topics),
        weak_topics_json=json.dumps(weak_topics),
        performance_notes=perf_notes,
        now=datetime.now(timezone.utc).isoformat()
    )

    msg2 = client.messages.create(
        model=CLAUDE_MODEL, max_tokens=8192,
        messages=[{"role": "user", "content": practice_prompt}]
    )
    practice = _parse_json(msg2.content[0].text)

    practice_path = student_dir / f"practice_{metadata['iteration']}.json"
    practice_path.write_text(json.dumps(practice, indent=2))
    print(f"Practice problems saved -> {practice_path}")

    # Print human-readable summary
    print("\n" + "="*60)
    print(f"REPORT SUMMARY — {student_name.capitalize()} / {session_id}")
    print("="*60)
    print(f"Score: {report['overall_score_percent']}%")
    print(f"Summary: {report['performance_summary']}")
    print(f"\nAverage time per question: {report['average_time_seconds']:.0f}s")
    print(f"Slowest: {report['time_analysis']['slowest_question']['id']} "
          f"({report['time_analysis']['slowest_question']['topic']}) — "
          f"{report['time_analysis']['slowest_question']['seconds']}s")
    print(f"\nWeak topics: {', '.join(weak_topics) if weak_topics else 'None'}")
    print("\nTopic breakdown:")
    for t in report.get("topic_analysis", []):
        icon = "✓" if t["confidence_level"] == "confident" else ("~" if t["confidence_level"] == "uncertain" else "✗")
        print(f"  {icon} {t['topic']:30s} avg {t['avg_time_seconds']:.0f}s  [{t['confidence_level']}]")
    print("\nRecommendations:")
    for i, r in enumerate(report.get("actionable_recommendations", []), 1):
        print(f"  {i}. {r}")
    print(f"\nPractice problems generated: {len(practice.get('problems', []))}")
    for p in practice.get("problems", []):
        print(f"  - [{p['topic']}] {p['title']} ({p['difficulty']})")
    print("="*60)

if __name__ == "__main__":
    main()
