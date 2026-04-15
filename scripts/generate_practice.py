"""
scripts/generate_practice.py
Generate practice_N.json for a student session using the report's weak_topics.
Uses a 300s timeout to handle large Opus responses.

Usage:
    python3 scripts/generate_practice.py <student_name> <session_id>
    python3 scripts/generate_practice.py Teststudent session_1
"""
import json, os, re, sys
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / "backend" / ".env")
import anthropic

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
      "starter_code": "<Java skeleton or empty class for them to fill in>",
      "solution": "<complete working Java solution>",
      "solution_explanation": "<line-by-line or concept-by-concept explanation>",
      "follow_up_challenges": [
        "<variation 1 that slightly extends the problem>",
        "<variation 2 that adds a twist>",
        "<variation 3 that combines with another concept>"
      ]
    }}
  ]
}}

Focus problems on the topics where the student showed the most struggle.
Make the problems concrete and practical — real AP CSA style, not abstract.
"""


def _get_student_dir(name: str) -> Path:
    safe = re.sub(r"[^\w]", "_", name.lower().strip())
    return ROOT / "data" / "students" / f"{safe}_data"


def generate_practice(student_name: str, session_id: str) -> None:
    student_dir = _get_student_dir(student_name)
    iteration = int(session_id.split("_")[1])

    report_path = student_dir / f"report_{iteration}.json"
    if not report_path.exists():
        print(f"ERROR: {report_path} not found — run report generation first")
        sys.exit(1)

    report = json.loads(report_path.read_text())
    weak_topics = report.get("weak_topics", [])
    uncertain = [
        t for t in report.get("topic_analysis", [])
        if t["confidence_level"] in ("uncertain", "struggling")
    ]
    perf_notes = (
        "; ".join(f"{t['topic']}: {t['notes']}" for t in uncertain)
        or "Student showed difficulty on several topics."
    )

    print(f"Student: {student_name}")
    print(f"Weak topics: {weak_topics}")
    print("Generating practice problems with claude-opus-4-6 (300s timeout)...")

    prompt = PRACTICE_PROMPT.format(
        student_name=student_name.capitalize(),
        student_name_lower=student_name.lower(),
        session_id=session_id,
        weak_topics=", ".join(weak_topics),
        weak_topics_json=json.dumps(weak_topics),
        performance_notes=perf_notes,
        now=datetime.now(timezone.utc).isoformat(),
    )

    client = anthropic.Anthropic(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        timeout=300.0,
    )

    # Use streaming to avoid server disconnect on long Opus responses
    chunks = []
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            chunks.append(chunk)
            print(".", end="", flush=True)
    print()  # newline after dots

    text = "".join(chunks).strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    practice = json.loads(text.strip())
    practice_path = student_dir / f"practice_{iteration}.json"
    practice_path.write_text(json.dumps(practice, indent=2))

    count = len(practice.get("problems", []))
    print(f"Done. {count} problems saved -> {practice_path}")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "bella"
    sid = sys.argv[2] if len(sys.argv) > 2 else "session_1"
    generate_practice(name, sid)
