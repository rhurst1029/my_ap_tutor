"""
backend/services/takehome_generator.py
Purpose: Generate a take-home Java project for a student based on their assessment report.
         Produces a directory tree with runnable Java files, question READMEs, and a
         Python CLI runner that records answers + timing.
Docs: https://docs.anthropic.com/en/api/messages
Sample input:  generate_takehome("Bella", "session_1", report_data, client)
Sample output: data/students/bella_data/takehome_1/ directory tree
"""
import json
import os
import re
import textwrap
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from loguru import logger

ROOT = Path(__file__).parent.parent.parent

TAKEHOME_PROMPT = """You are an expert AP Computer Science A tutor creating a take-home practice assignment.

Student: {student_name}
Weak/uncertain topics from assessment: {weak_topics}
Performance notes: {performance_notes}

Create exactly 5 take-home questions targeting these weak topics.

Each question must:
1. Be a multiple-choice question about Java code behavior (what does this print, what is the value, etc.)
2. Include a runnable Java code snippet the student can modify and experiment with
3. Have exactly 4 options (A, B, C, D)
4. Have 2-3 follow-up variant questions (labeled A, B, C) that modify the code slightly and test deeper understanding of the same concept
5. Each variant also has exactly 4 options (A, B, C, D) with its own answer key

Return raw JSON only (no markdown fences):
{{
  "questions": [
    {{
      "id": "q1",
      "topic": "<topic_tag>",
      "title": "<short descriptive title>",
      "prompt": "<what does this code print?>",
      "code": "<complete runnable Java snippet — must compile standalone>",
      "options": {{"A": "<option>", "B": "<option>", "C": "<option>", "D": "<option>"}},
      "answer_key": "<A|B|C|D>",
      "explanation": "<why this is the answer>",
      "variants": [
        {{
          "id": "q1a",
          "label": "A",
          "prompt": "<modified question — what changes and why?>",
          "code": "<modified Java code>",
          "options": {{"A": "<option>", "B": "<option>", "C": "<option>", "D": "<option>"}},
          "answer_key": "<A|B|C|D>",
          "explanation": "<why>"
        }}
      ]
    }}
  ]
}}

The Java code must:
- Be a complete snippet that can be wrapped in a main method and compiled
- Use only standard library (no imports beyond java.util.*)
- Be 3-15 lines
- Directly test the weak topic

Make each variant progressively harder — variant A is slight modification, variant C adds an interesting twist.
"""


def _wrap_in_main(code: str, class_name: str) -> str:
    """Wrap a bare code snippet in a public class with a main method."""
    indented = textwrap.indent(code.strip(), '        ')
    return (
        f"public class {class_name} {{\n"
        f"    public static void main(String[] args) {{\n"
        f"{indented}\n"
        f"    }}\n"
        f"}}\n"
    )


def _make_java_file(code: str, class_name: str) -> str:
    """
    If the code already contains a class declaration, replace the class name.
    Otherwise wrap it in a main class.
    """
    if 'public class' in code:
        return re.sub(r'public class \w+', f'public class {class_name}', code)
    return _wrap_in_main(code, class_name)


def _write_runner(takehome_dir: Path, questions: list) -> None:
    """Write runner.py — the CLI that walks the student through all questions."""
    question_list_json = json.dumps([
        {
            "id": q["id"],
            "folder": f"question{i+1}",
            "main_java": f"Question{i+1}.java",
            "variants": [
                {"label": v["label"], "java": f"Question{i+1}{v['label']}.java"}
                for v in q.get("variants", [])
            ],
        }
        for i, q in enumerate(questions)
    ], indent=2)

    runner_code = (
        '#!/usr/bin/env python3\n'
        '"""\n'
        'Take-Home Assignment Runner\n'
        'Usage: python runner.py\n'
        '\n'
        'Walks through each question, compiles + runs the Java file, then prompts\n'
        'for your multiple-choice answer. Saves all responses and timing to\n'
        'questions_and_responses.txt.\n'
        '\n'
        'You can edit the .java files between runs — the runner recompiles each time.\n'
        '"""\n'
        'import subprocess, time, pathlib, json, datetime, sys\n'
        '\n'
        'BASE = pathlib.Path(__file__).parent\n'
        'RESPONSES_FILE = BASE / "questions_and_responses.txt"\n'
        f'QUESTIONS = {question_list_json}\n'
        '\n'
        '\n'
        'def compile_and_run(java_path: pathlib.Path) -> str:\n'
        '    """Compile and run a Java file. Returns combined stdout+stderr."""\n'
        '    result = subprocess.run(\n'
        '        ["javac", str(java_path)],\n'
        '        capture_output=True, text=True, cwd=java_path.parent\n'
        '    )\n'
        '    if result.returncode != 0:\n'
        '        return f"COMPILE ERROR:\\n{result.stderr}"\n'
        '    class_name = java_path.stem\n'
        '    result = subprocess.run(\n'
        '        ["java", class_name],\n'
        '        capture_output=True, text=True, cwd=java_path.parent\n'
        '    )\n'
        '    output = result.stdout\n'
        '    if result.stderr:\n'
        '        output += f"\\nSTDERR: {result.stderr}"\n'
        '    return output\n'
        '\n'
        '\n'
        'def ask_question(q_id: str, readme_path: pathlib.Path, java_path: pathlib.Path) -> dict:\n'
        '    sep = "=" * 60\n'
        '    print(f"\\n{sep}")\n'
        '    print(f"  {q_id.upper()}")\n'
        '    print(sep)\n'
        '    print(readme_path.read_text())\n'
        '    print("\\n--- Running the Java code ---")\n'
        '    print(compile_and_run(java_path))\n'
        '    print("\\nYou can edit the .java file in another editor and press R to re-run.")\n'
        '\n'
        '    start = time.time()\n'
        '    while True:\n'
        '        answer = input("\\nYour answer (A/B/C/D) or R to re-run: ").strip().upper()\n'
        '        if answer == "R":\n'
        '            print("\\n--- Re-running ---")\n'
        '            print(compile_and_run(java_path))\n'
        '        elif answer in ("A", "B", "C", "D"):\n'
        '            elapsed = round(time.time() - start)\n'
        '            return {"question_id": q_id, "answer": answer, "time_seconds": elapsed}\n'
        '        else:\n'
        '            print("Please enter A, B, C, D, or R.")\n'
        '\n'
        '\n'
        'def main():\n'
        '    print("\\nAP CSA Take-Home Assignment")\n'
        '    print("Answers will be saved to questions_and_responses.txt\\n")\n'
        '\n'
        '    all_responses = []\n'
        '    session_start = datetime.datetime.now().isoformat()\n'
        '\n'
        '    for q in QUESTIONS:\n'
        '        folder = BASE / q["folder"]\n'
        '\n'
        '        # Main question\n'
        '        readme = folder / "README.md"\n'
        '        java = folder / q["main_java"]\n'
        '        if readme.exists() and java.exists():\n'
        '            r = ask_question(q["id"], readme, java)\n'
        '            all_responses.append(r)\n'
        '\n'
        '        # Variants\n'
        '        for v in q.get("variants", []):\n'
        '            v_label = v["label"]\n'
        '            q_id = q["id"]\n'
        '            readme_v = folder / f"README_{v_label}.md"\n'
        '            java_v = folder / v["java"]\n'
        '            if readme_v.exists() and java_v.exists():\n'
        '                r = ask_question(f"{q_id}{v_label.lower()}", readme_v, java_v)\n'
        '                all_responses.append(r)\n'
        '\n'
        '    output = {\n'
        '        "session_start": session_start,\n'
        '        "completed_at": datetime.datetime.now().isoformat(),\n'
        '        "responses": all_responses,\n'
        '    }\n'
        '    RESPONSES_FILE.write_text(json.dumps(output, indent=2))\n'
        '    print(f"\\n\\u2713 Responses saved to {RESPONSES_FILE}")\n'
        '    print("\\nAll done! Bring this file to your next session.")\n'
        '\n'
        '\n'
        'if __name__ == "__main__":\n'
        '    main()\n'
    )
    (takehome_dir / "runner.py").write_text(runner_code)


def _write_question_folder(takehome_dir: Path, q: dict, question_num: int) -> None:
    folder = takehome_dir / f"question{question_num}"
    folder.mkdir(parents=True, exist_ok=True)

    options_text = "\n".join(f"  {k}) {v}" for k, v in q["options"].items())
    readme = (
        f"# Question {question_num}: {q['title']}\n\n"
        f"{q['prompt']}\n\n"
        f"**Options:**\n{options_text}\n\n"
        f"---\n"
        f"*Edit Question{question_num}.java and run `python ../runner.py` to experiment.*\n"
    )
    (folder / "README.md").write_text(readme)

    java_code = _make_java_file(q["code"], f"Question{question_num}")
    (folder / f"Question{question_num}.java").write_text(java_code)

    for v in q.get("variants", []):
        label = v["label"]
        opts_text = "\n".join(f"  {k}) {vv}" for k, vv in v["options"].items())
        readme_v = (
            f"# Question {question_num}{label}: {q['title']} — Variant {label}\n\n"
            f"{v['prompt']}\n\n"
            f"**Options:**\n{opts_text}\n\n"
            f"---\n"
            f"*Edit Question{question_num}{label}.java and run `python ../runner.py` to experiment.*\n"
        )
        (folder / f"README_{label}.md").write_text(readme_v)
        java_v = _make_java_file(v["code"], f"Question{question_num}{label}")
        (folder / f"Question{question_num}{label}.java").write_text(java_v)


def generate_takehome(
    student_name: str, session_id: str, report: dict, client
) -> Optional[Path]:
    """
    Generate take-home Java project directory from assessment report.
    Returns the path to the generated takehome directory, or None on failure.
    Safe to call as a FastAPI BackgroundTask — logs errors, never raises.
    """
    try:
        from config import STUDENTS_DIR

        safe = re.sub(r'[^\w]', '_', student_name.lower().strip())
        student_dir = STUDENTS_DIR / f"{safe}_data"
        iteration = int(session_id.split("_")[1])
        takehome_dir = student_dir / f"takehome_{iteration}"
        takehome_dir.mkdir(parents=True, exist_ok=True)

        weak_topics = report.get("weak_topics", [])
        uncertain = [t for t in report.get("topic_analysis", [])
                     if t["confidence_level"] in ("uncertain", "struggling")]
        performance_notes = (
            "; ".join(f"{t['topic']}: {t['notes']}" for t in uncertain)
            or "Student showed hesitation on several topics."
        )

        prompt = TAKEHOME_PROMPT.format(
            student_name=student_name.capitalize(),
            weak_topics=", ".join(weak_topics),
            performance_notes=performance_notes,
        )

        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            raw = stream.get_final_text().strip()

        if raw.startswith("```"):
            raw = re.sub(r'^```[a-z]*\n?', '', raw)
            raw = re.sub(r'\n?```$', '', raw)
        data = json.loads(raw.strip())
        questions = data["questions"]

        overview = (
            f"# AP CSA Take-Home Assignment\n\n"
            f"Student: {student_name.capitalize()}\n"
            f"Session: {session_id}\n"
            f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n"
            f"## Topics\n{', '.join(weak_topics)}\n\n"
            f"## How to use\n"
            f"1. Run `python runner.py` to start the assignment\n"
            f"2. Edit the `.java` files in each question folder to experiment\n"
            f"3. The runner will re-compile and re-run when you press R\n"
            f"4. Your answers are saved to `questions_and_responses.txt`\n"
        )
        (takehome_dir / "README.md").write_text(overview)

        for i, q in enumerate(questions):
            _write_question_folder(takehome_dir, q, i + 1)

        _write_runner(takehome_dir, questions)

        logger.info(f"Take-home generated -> {takehome_dir}")
        return takehome_dir

    except Exception as e:
        logger.error(f"Take-home generation failed for {student_name}/{session_id}: {e}")
        return None


if __name__ == "__main__":
    import sys
    import anthropic
    from dotenv import load_dotenv

    load_dotenv(ROOT / "backend" / ".env")
    name = sys.argv[1] if len(sys.argv) > 1 else "bella"
    sid = sys.argv[2] if len(sys.argv) > 2 else "session_1"
    safe = re.sub(r'[^\w]', '_', name.lower())
    report_path = ROOT / "data" / "students" / f"{safe}_data" / f"report_{sid.split('_')[1]}.json"
    if not report_path.exists():
        print(f"No report found at {report_path}")
        sys.exit(1)
    report_data = json.loads(report_path.read_text())
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set")
        sys.exit(1)
    c = anthropic.Anthropic(api_key=api_key, timeout=300.0)
    result = generate_takehome(name, sid, report_data, c)
    print(f"Generated: {result}")
