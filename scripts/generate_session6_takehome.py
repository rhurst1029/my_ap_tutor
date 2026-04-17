"""
scripts/generate_session6_takehome.py
Purpose: Generate Bella's Session 6 take-home assignment — 15 FRQ-style questions
         targeting her weak areas (nested loops, index vs value) while reinforcing
         mastered topics (comparison direction, constructor syntax).
Docs:    https://docs.anthropic.com/en/api/messages
Run:     source backend/venv/bin/activate && python scripts/generate_session6_takehome.py

Output structure:
  data/students/bella_data/take_home_session_6/
  ├── manifest.json
  ├── Q1/ Q1.java, Q1A.json, Q1B.json
  ├── Q2/ ...
  └── Q15/
"""
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict

from dotenv import load_dotenv
import anthropic

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / "backend" / ".env")

OUTPUT_DIR = ROOT / "data" / "students" / "bella_data" / "take_home_session_6"
MODEL = "claude-sonnet-4-6"

# ── 15-question plan, targeting Bella's weak areas ───────────────────────────
QUESTIONS_PLAN: List[Dict] = [
    # ── NESTED LOOPS (CRITICAL — 33% on Session 5) ─────────────────────────
    {"id": "Q1", "title": "Print a Multiplication Table",
     "topics": ["nested_loops", "loops"], "priority": "CRITICAL", "difficulty": "easy",
     "concept": "Print i*j for i=1..n, j=1..n; newline after inner loop"},
    {"id": "Q2", "title": "Count Nested Loop Iterations",
     "topics": ["nested_loops", "loops"], "priority": "CRITICAL", "difficulty": "medium",
     "concept": "Return the total number of times the inner loop body runs when j's upper bound depends on i"},
    {"id": "Q3", "title": "Print a Right Triangle of Stars",
     "topics": ["nested_loops", "loops"], "priority": "CRITICAL", "difficulty": "easy",
     "concept": "Inner loop variable resets each outer iteration; print i stars on row i"},
    {"id": "Q4", "title": "Sum of Row Products",
     "topics": ["nested_loops", "loops", "arrays"], "priority": "CRITICAL", "difficulty": "medium",
     "concept": "Nested loop accumulator — sum up i*j for all valid (i,j) pairs"},

    # ── INDEX vs VALUE (HIGH — 75% on Session 5 but still a gap) ───────────
    {"id": "Q5", "title": "Count Values Above Threshold",
     "topics": ["arrays", "index_vs_value"], "priority": "HIGH", "difficulty": "easy",
     "concept": "Use arr[i] > threshold NOT i > threshold — the recurring Bella bug"},
    {"id": "Q6", "title": "Find Positions of Even Values",
     "topics": ["arrays", "arraylist", "index_vs_value"], "priority": "HIGH", "difficulty": "medium",
     "concept": "Return an ArrayList of INDICES (i) where arr[i] is even — both i and arr[i] are used"},
    {"id": "Q7", "title": "Trace Through an Array",
     "topics": ["arrays", "index_vs_value"], "priority": "HIGH", "difficulty": "medium",
     "concept": "Given a predetermined array, predict output when only indices are checked vs when values are checked"},

    # ── ARRAYLIST (MEDIUM — new content from Session 4) ────────────────────
    {"id": "Q8", "title": "Build an ArrayList from Scratch",
     "topics": ["arraylist", "loops"], "priority": "MEDIUM", "difficulty": "easy",
     "concept": "Declare ArrayList<Integer>, call .add() in a loop, return it — the ArrayList workflow from Session 4"},
    {"id": "Q9", "title": "Filter ArrayList by Condition",
     "topics": ["arraylist", "loops", "conditionals"], "priority": "MEDIUM", "difficulty": "medium",
     "concept": "Traverse an ArrayList, add only matching elements to a new ArrayList — use .get(i) and .add()"},

    # ── METHODS & RETURN TYPES (MEDIUM — caught her own bug in Session 4) ──
    {"id": "Q10", "title": "Fix the Return Type",
     "topics": ["methods", "return_types"], "priority": "MEDIUM", "difficulty": "medium",
     "concept": "Method returns an ArrayList — declaration must match the return type (not int, not void)"},
    {"id": "Q11", "title": "Method with Multiple Parameters",
     "topics": ["methods", "parameters"], "priority": "MEDIUM", "difficulty": "medium",
     "concept": "Write a method taking two arrays and returning a boolean — practice with signature + multiple params"},

    # ── CLASSES & OBJECTS (MEDIUM — void on constructor bug from Session 4) ─
    {"id": "Q12", "title": "Design a Student Class",
     "topics": ["classes_and_objects", "constructors"], "priority": "MEDIUM", "difficulty": "medium",
     "concept": "Private fields + constructor (no return type!) + getters — full class design"},
    {"id": "Q13", "title": "Copy Constructor",
     "topics": ["classes_and_objects", "constructors"], "priority": "MEDIUM", "difficulty": "medium",
     "concept": "Constructor that takes another object of the same class and copies its fields — reinforces 'no return type'"},

    # ── COMPARISON DIRECTION (LOW — 100% mastered, confidence builder) ─────
    {"id": "Q14", "title": "Find the Second Smallest Element",
     "topics": ["arrays", "comparison_direction"], "priority": "LOW", "difficulty": "medium",
     "concept": "Two-pass find: first the minimum, then the smallest value greater than it — practice flipping < and >"},

    # ── MIXED CONCEPTS ─────────────────────────────────────────────────────
    {"id": "Q15", "title": "2D Array — Sum Each Row",
     "topics": ["2d_arrays", "nested_loops", "arraylist"], "priority": "HIGH", "difficulty": "hard",
     "concept": "Traverse a 2D int[][] with nested loops and return an ArrayList<Integer> of row sums — combines nested loops + index vs value + ArrayList"},
]

assert len(QUESTIONS_PLAN) == 15, f"Expected 15 questions, got {len(QUESTIONS_PLAN)}"


# ── Prompt per question ──────────────────────────────────────────────────────
QUESTION_PROMPT = """You are writing a Java practice question for an AP Computer Science A student named Bella.

Bella's profile (from Sessions 3-5):
- STRUGGLES with nested loops — she thinks the inner variable carries over between iterations (it doesn't, it resets), and she multiplies inner*outer counts instead of summing (e.g. 4*4=16 when the answer is 1+2+3+4=10)
- STRUGGLES with index vs value — she writes "if (i > threshold)" instead of "if (arr[i] > threshold)"
- MASTERED comparison direction (< for findMin, > for findMax) — 100% accuracy, <7s per question
- MASTERED constructor syntax — knows constructors have no return type (not even void)
- LEARNED that return types must match (caught her own bug from compiler error)
- NEW to her: ArrayList declaration, initialization, .add(), .size()

Question to generate:
ID: {id}
Title: {title}
Topics: {topics}
Priority: {priority}
Difficulty: {difficulty}
Concept: {concept}

Generate a complete Java starter file AND two mutation variants (A, B) as strict JSON.

Return ONLY a single JSON object with EXACTLY this structure (no markdown, no text before/after):

{{
  "java_starter": "public class {id} {{\\n    /**\\n     * Q{id_num}: {title}\\n     * Topic: ...\\n     */\\n    public static ... METHOD_NAME(...) {{\\n        // TODO: implement\\n        return ...;\\n    }}\\n\\n    public static void main(String[] args) {{\\n        System.out.println(METHOD_NAME(...));\\n    }}\\n}}",

  "variant_a": {{
    "id": "{id}A",
    "parent_question": "{id}",
    "mutation_description": "A concrete change the student must make to the base code (1-2 sentences)",
    "concept_tested": "The specific concept this variant probes",
    "difficulty": "easy|medium|hard",
    "topic_tags": ["topic1", "topic2"],
    "starter_modification": "Step-by-step description of what to modify in the starter code",
    "test_cases": [
      {{
        "id": "tc1",
        "description": "Short description of this test case",
        "method_call": "exactMethodName(arguments)",
        "expected_output": "the exact expected stdout (usually a single value or short string)",
        "what_it_tests": "The specific concept this test case verifies",
        "wrong_means": "If the output is wrong, what misconception does that suggest (Bella-specific if applicable)"
      }},
      {{"id": "tc2", "description": "...", "method_call": "...", "expected_output": "...", "what_it_tests": "...", "wrong_means": "..."}},
      {{"id": "tc3", "description": "...", "method_call": "...", "expected_output": "...", "what_it_tests": "...", "wrong_means": "..."}}
    ],
    "summary": {{
      "what_this_tests": "1-2 sentences on what skill this variant is probing",
      "why": "1-2 sentences on why this matters for Bella's progress",
      "concept_background": "2-4 sentences explaining the underlying concept clearly"
    }}
  }},

  "variant_b": {{ ... same structure as variant_a, a DIFFERENT mutation — harder or a different angle ... }}
}}

CRITICAL JSON rules:
- All strings must be valid JSON. Escape newlines as \\n and quotes as \\".
- Do NOT use literal newlines inside Java code strings — use \\n.
- The Java starter code must be a complete, compilable Java file (it can have TODO comments).
- test_cases method_call must be valid Java that can be substituted into main()'s System.out.println(...).
- expected_output is the stdout the test should produce (stripped of trailing whitespace).
- Variant B should be DIFFERENT from Variant A — a different mutation, different angle, or higher difficulty.
"""


def robust_json_parse(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    text = text.strip()
    brace = text.find('{')
    if brace == -1:
        raise ValueError("No opening brace found in response")
    depth = 0
    for i, ch in enumerate(text[brace:], brace):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                text = text[brace:i + 1]
                break
    return json.loads(text)


def generate_question(client: anthropic.Anthropic, spec: Dict) -> dict:
    """Call Claude to generate one question with 2 variants."""
    prompt = QUESTION_PROMPT.format(
        id=spec["id"],
        id_num=spec["id"][1:],
        title=spec["title"],
        topics=", ".join(spec["topics"]),
        priority=spec["priority"],
        difficulty=spec["difficulty"],
        concept=spec["concept"],
    )
    with client.messages.stream(
        model=MODEL, max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        raw = stream.get_final_text()
    return robust_json_parse(raw)


def write_question(spec: Dict, data: dict) -> None:
    """Write Q{N}.java, Q{N}A.json, Q{N}B.json into the question directory."""
    qdir = OUTPUT_DIR / spec["id"]
    qdir.mkdir(parents=True, exist_ok=True)

    # Write Java starter
    (qdir / f"{spec['id']}.java").write_text(data["java_starter"])

    # Write variants with metadata injected
    for letter in ("a", "b"):
        variant = data[f"variant_{letter}"]
        variant["metadata"] = {
            "started_at": None,
            "completed_at": None,
            "total_time_ms": None,
            "run_attempts": [],
            "test_results": [],
        }
        (qdir / f"{spec['id']}{letter.upper()}.json").write_text(
            json.dumps(variant, indent=2)
        )


def build_manifest() -> dict:
    """Construct the manifest listing all questions."""
    return {
        "student": "Bella",
        "session": 6,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": len(QUESTIONS_PLAN),
        "description": "Session 6 take-home: 15 FRQ-style practice problems targeting Bella's weak areas (nested loops, index vs value) and reinforcing new concepts (ArrayList, constructors).",
        "questions": [
            {
                "id": q["id"],
                "title": q["title"],
                "topic_tags": q["topics"],
                "priority": q["priority"],
                "difficulty": q["difficulty"],
                "variants": [f"{q['id']}A", f"{q['id']}B"],
                "directory": q["id"],
            }
            for q in QUESTIONS_PLAN
        ],
    }


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        return 1

    client = anthropic.Anthropic(api_key=api_key, timeout=300.0)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for spec in QUESTIONS_PLAN:
        qdir = OUTPUT_DIR / spec["id"]
        # Skip if already complete (resumable)
        if (qdir / f"{spec['id']}.java").exists() and \
           (qdir / f"{spec['id']}A.json").exists() and \
           (qdir / f"{spec['id']}B.json").exists():
            print(f"  [{spec['id']}] already exists — skipping")
            continue

        print(f"  [{spec['id']}] generating... ({spec['title']})")
        try:
            data = generate_question(client, spec)
            write_question(spec, data)
            print(f"  [{spec['id']}] ✓ saved")
        except Exception as e:
            print(f"  [{spec['id']}] ✗ FAILED: {e}")
            # Keep going with the next question
            continue

    # Write manifest last
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(build_manifest(), indent=2))
    print(f"\nManifest saved to {manifest_path}")
    print(f"Total questions directory: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
