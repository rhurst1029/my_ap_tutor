"""
scripts/generate_session6_takehome.py  (v2)
Purpose: Generate Bella's Session 6 take-home assignment — 15 FRQ-style questions
         targeting her weak areas. v2 improvements over v1:
         - Starter Java files contain a COMPLETE working implementation
           (students modify it per the variant's instructions — no phantom
           "copy your earlier solution" references)
         - Each test case declares method_type: "value_return" | "void_print"
           so the frontend test runner knows exactly how to invoke it
         - Reference-style examples from Session 5 hand-crafted Java files
           are injected into the prompt as style exemplars

Docs:    https://docs.anthropic.com/en/api/messages
Run:     source backend/venv/bin/activate && python scripts/generate_session6_takehome.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

from dotenv import load_dotenv
import anthropic

ROOT = Path(__file__).parent.parent
load_dotenv(ROOT / "backend" / ".env")

OUTPUT_DIR = ROOT / "data" / "students" / "bella_data" / "take_home_session_6"
REFERENCE_DIR = OUTPUT_DIR / "_reference"
MODEL = "claude-sonnet-4-6"

# ── Question plan (15 questions) ─────────────────────────────────────────────
QUESTIONS_PLAN: List[Dict] = [
    {"id": "Q1", "title": "Print a Multiplication Table",
     "topics": ["nested_loops", "loops"], "priority": "CRITICAL", "difficulty": "easy",
     "concept": "Print i*j for i=1..n, j=1..n with newline after inner loop — the canonical nested loop exercise",
     "method_signature": "public static void printTable(int n)",
     "base_behavior": "Prints an n×n multiplication table where row i contains i*1, i*2, ..., i*n separated by spaces, with a newline after each row."},

    {"id": "Q2", "title": "Count Nested Loop Iterations",
     "topics": ["nested_loops", "loops"], "priority": "CRITICAL", "difficulty": "medium",
     "concept": "Total inner-body runs when j's upper bound is i (sum 1+2+...+n, not n*n) — Bella's Session 4 Q6 error",
     "method_signature": "public static int countIterations(int n)",
     "base_behavior": "Returns the total number of times the inner loop body runs when the outer loop is i=1..n and the inner loop is j=1..i. For n=4, returns 10 (= 1+2+3+4), NOT 16."},

    {"id": "Q3", "title": "Print a Right Triangle of Stars",
     "topics": ["nested_loops", "loops"], "priority": "CRITICAL", "difficulty": "easy",
     "concept": "Inner loop variable resets each outer iteration — print i stars on row i",
     "method_signature": "public static void printTriangle(int n)",
     "base_behavior": "Prints n rows where row i has exactly i stars (no trailing space), each row followed by a newline. For n=3: '*\\n**\\n***\\n'."},

    {"id": "Q4", "title": "Sum Upper Triangle",
     "topics": ["nested_loops", "loops", "arrays"], "priority": "CRITICAL", "difficulty": "medium",
     "concept": "Nested loop accumulator where bounds depend on each other — sum i*j for j >= i",
     "method_signature": "public static int sumUpperTriangle(int n)",
     "base_behavior": "Returns the sum of i*j for all (i,j) with 1 <= i <= j <= n. For n=3: (1*1)+(1*2)+(1*3)+(2*2)+(2*3)+(3*3) = 1+2+3+4+6+9 = 25."},

    {"id": "Q5", "title": "Count Values Above Threshold",
     "topics": ["arrays", "index_vs_value"], "priority": "HIGH", "difficulty": "easy",
     "concept": "arr[i] > threshold vs i > threshold — Bella's classic index-vs-value bug",
     "method_signature": "public static int countAbove(int[] arr, int threshold)",
     "base_behavior": "Returns the number of elements in arr that are strictly greater than threshold. Uses arr[i] > threshold inside the loop, NOT i > threshold."},

    {"id": "Q6", "title": "Collect Positions of Even Values",
     "topics": ["arrays", "arraylist", "index_vs_value"], "priority": "HIGH", "difficulty": "medium",
     "concept": "Distinguish i (position) from arr[i] (value) — use arr[i] to test, use i to collect",
     "method_signature": "public static ArrayList<Integer> evenPositions(int[] arr)",
     "base_behavior": "Returns an ArrayList containing the INDICES (not values) where arr[i] is even. For {1,6,3,8,2}: returns [1,3,4]."},

    {"id": "Q7", "title": "Find Max Value Index",
     "topics": ["arrays", "index_vs_value"], "priority": "HIGH", "difficulty": "medium",
     "concept": "Track and return the INDEX of the max — reinforces i vs arr[i] distinction",
     "method_signature": "public static int maxIndex(int[] arr)",
     "base_behavior": "Returns the INDEX of the largest value in arr. If arr = {3,8,5,10,2}, returns 3 (the position of 10), NOT 10 (the value)."},

    {"id": "Q8", "title": "Build Squares ArrayList",
     "topics": ["arraylist", "loops"], "priority": "MEDIUM", "difficulty": "easy",
     "concept": "Declare ArrayList<Integer>, use .add() in a loop, return it — the canonical ArrayList workflow",
     "method_signature": "public static ArrayList<Integer> squares(int n)",
     "base_behavior": "Returns an ArrayList of the first n squares: [1, 4, 9, 16, ..., n*n]. Demonstrates declaration, .add(), and returning an ArrayList."},

    {"id": "Q9", "title": "Filter ArrayList by Length",
     "topics": ["arraylist", "loops", "strings"], "priority": "MEDIUM", "difficulty": "medium",
     "concept": "Traverse an ArrayList with .get(i) and .size(), build a filtered ArrayList — standard AP CSA operation",
     "method_signature": "public static ArrayList<String> longWords(ArrayList<String> words, int minLen)",
     "base_behavior": "Returns a new ArrayList containing only the strings from words whose length is >= minLen. Does not modify the input."},

    {"id": "Q10", "title": "Method Return Type Matching",
     "topics": ["methods", "return_types", "arraylist"], "priority": "MEDIUM", "difficulty": "medium",
     "concept": "Method signature must match the type of value returned — reinforces the Session 4 compiler-error moment",
     "method_signature": "public static ArrayList<Integer> doubled(int[] arr)",
     "base_behavior": "Returns an ArrayList where each element is 2× the corresponding element of arr. The return type in the signature must match the actual return value type."},

    {"id": "Q11", "title": "Check All Positive",
     "topics": ["methods", "parameters", "loops"], "priority": "MEDIUM", "difficulty": "medium",
     "concept": "Method with multiple parameters returning boolean — early return pattern",
     "method_signature": "public static boolean allPositive(int[] arr)",
     "base_behavior": "Returns true if every element of arr is strictly positive, false otherwise. An empty array returns true (vacuously)."},

    {"id": "Q12", "title": "Student Class Design",
     "topics": ["classes_and_objects", "constructors", "getters"], "priority": "MEDIUM", "difficulty": "medium",
     "concept": "Private fields + constructor (no return type keyword!) + getters",
     "method_signature": "// (Student class — constructor + getName + getGrade)",
     "base_behavior": "A complete Student class with private String name and private int grade fields, a constructor that sets both, and getName() and getGrade() methods. No return type on the constructor."},

    {"id": "Q13", "title": "Copy Constructor",
     "topics": ["classes_and_objects", "constructors"], "priority": "MEDIUM", "difficulty": "medium",
     "concept": "A second constructor that accepts another object and copies its fields",
     "method_signature": "// (Book class with two constructors)",
     "base_behavior": "A Book class with private String title and private String author, a primary constructor taking both, AND a copy constructor Book(Book other) that copies the fields from another Book."},

    {"id": "Q14", "title": "Find Second Smallest",
     "topics": ["arrays", "comparison_direction"], "priority": "LOW", "difficulty": "medium",
     "concept": "Two-pass find: first the minimum, then the smallest value greater than it — flipping < and > intentionally",
     "method_signature": "public static int secondSmallest(int[] arr)",
     "base_behavior": "Returns the second-smallest distinct value in arr. For {5,3,8,1,9}: returns 3. For {4,1,7,2,9}: returns 2. Assumes arr has at least 2 distinct values."},

    {"id": "Q15", "title": "Row Sums of 2D Array",
     "topics": ["2d_arrays", "nested_loops", "arraylist"], "priority": "HIGH", "difficulty": "hard",
     "concept": "Traverse a 2D int[][] with nested loops, return ArrayList<Integer> of row sums — integrates all weak areas",
     "method_signature": "public static ArrayList<Integer> rowSums(int[][] grid)",
     "base_behavior": "Returns an ArrayList where the i-th element is the sum of row i in grid. For {{1,2,3},{4,5,6}}: returns [6, 15]."},
]

assert len(QUESTIONS_PLAN) == 15


# ── Prompt ────────────────────────────────────────────────────────────────────
QUESTION_PROMPT = """You are writing a Java practice question for an AP Computer Science A student named Bella.

## Bella's profile
- STRUGGLES with nested loops: she thinks the inner variable carries over between outer iterations (it resets), and she multiplies outer×inner counts instead of summing (4×4=16 when the correct answer is 1+2+3+4=10).
- STRUGGLES with index vs. value: she writes `if (i > threshold)` instead of `if (arr[i] > threshold)`.
- MASTERED comparison direction (< for findMin, > for findMax) — 100% accuracy, <7s per question. Can be used as a confidence builder.
- MASTERED constructor syntax: knows constructors have NO return type (not even void).
- LEARNED that return types must match what the method actually returns.
- NEW to her: ArrayList<T> declaration, .add(), .size(), .get(i).

## Style exemplar (a hand-crafted Session 5 question for reference)

```java
{exemplar_code}
```

Notice: a complete, runnable file with a working implementation. The docstring explains background, the question has clear answer options, and an answer key at the bottom traces the execution. THAT is the quality level you're aiming for.

## Your task — generate this question

- ID: {id}
- Title: {title}
- Topics: {topics}
- Priority: {priority}
- Difficulty: {difficulty}
- Concept being probed: {concept}
- Required method signature for the STARTER: {method_signature}
- What the starter code must DO when run as-is: {base_behavior}

## Output format — return ONLY this JSON (no markdown fences, no prose before/after)

{{
  "java_starter": "<COMPLETE, COMPILABLE Java file. The method must be FULLY IMPLEMENTED (working, not TODO). Include a main() that demonstrates it with one example call. Use \\n for newlines and \\\" for quotes inside the string. The class name must exactly match the question id ({id}).>",

  "variant_a": {{
    "id": "{id}A",
    "parent_question": "{id}",
    "mutation_description": "1–2 sentences describing a CONCRETE change the student must make to the starter. Must be self-contained — do not say 'your earlier solution'.",
    "concept_tested": "The specific misconception this variant probes",
    "difficulty": "easy|medium|hard",
    "topic_tags": ["topic1", "topic2"],
    "starter_modification": "Step-by-step edits. Reference line numbers or code snippets from the starter. Example: 'Change line 8 from `if (arr[i] > threshold)` to `if (arr[i] >= threshold)` to make it inclusive.'",
    "test_cases": [
      {{
        "id": "tc1",
        "description": "Short test-case description",
        "method_call": "methodName(args)",
        "method_type": "value_return" or "void_print",
        "expected_output": "exact stdout (stripped of trailing whitespace)",
        "what_it_tests": "The specific concept this verifies",
        "wrong_means": "What misconception wrong output would reveal (Bella-specific if applicable)"
      }},
      {{"id": "tc2", ...}},
      {{"id": "tc3", ...}}
    ],
    "summary": {{
      "what_this_tests": "1–2 sentences on the skill being probed",
      "why": "1–2 sentences on why this matters for Bella specifically",
      "concept_background": "2–4 sentences explaining the underlying concept — this is what the Info panel shows"
    }}
  }},

  "variant_b": {{ ... same shape, but a DIFFERENT mutation — harder or a different angle ... }}
}}

## Rules

1. `java_starter` must be a COMPLETE, CORRECT implementation that compiles and produces the base_behavior. Students modify it for each variant — they need a working base to experiment on.
2. `method_type` is MANDATORY in every test case. Use `value_return` if the method returns a value we should print with System.out.println(...). Use `void_print` if the method prints internally and the test call is just `method(...);`.
3. For classes (Q12, Q13), `method_call` can be like `new Student("Bella", 95).getName()` or `new Book(new Book("X","Y")).toString()` — exact Java expression, method_type determines whether println-wrapping is needed.
4. ALL strings must be valid JSON: escape newlines as \\n and quotes as \\\". Do NOT use literal newlines in any string value.
5. Variant B must probe a DIFFERENT angle than Variant A. Examples of good variant pairs:
   - A: "Change the method to only print values less than threshold" ; B: "Change the loop bound so it stops at the first zero"
   - A: "Make the loop exclusive (start at 1 not 0)" ; B: "Return the positions of ODD values instead of even"
6. Keep test cases CONCISE — 3 per variant, covering edge cases the mutation could break.
"""


def robust_json_parse(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```[a-z]*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    text = text.strip()
    brace = text.find('{')
    if brace == -1:
        raise ValueError("No opening brace in response")
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


def pick_exemplar(topics: List[str]) -> str:
    """Return a reference Java file whose topic matches the question."""
    if not REFERENCE_DIR.exists():
        return "// (no reference exemplar available)"
    mapping = {
        "nested_loops": "Block2_Q2c_NestedLoop_TotalCount.java",
        "index_vs_value": "Block1_Q1a_IndexVsValue.java",
        "comparison_direction": "Block3_Q3b_FindMin_BackwardsOperator.java",
        "constructors": "Block4_Q4c_Constructor_SetsFields.java",
        "classes_and_objects": "Block4_Q4c_Constructor_SetsFields.java",
    }
    for topic in topics:
        if topic in mapping:
            path = REFERENCE_DIR / mapping[topic]
            if path.exists():
                return path.read_text()
    # Default fallback
    fallback = REFERENCE_DIR / "Block1_Q1a_IndexVsValue.java"
    return fallback.read_text() if fallback.exists() else "// no exemplar"


def validate_java_compiles(source_code: str) -> Optional[str]:
    """Try compiling the Java source. Returns None on success, or the error."""
    m = re.search(r'public\s+class\s+(\w+)', source_code)
    if not m:
        return "no public class found"
    class_name = m.group(1)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"{class_name}.java"
        src.write_text(source_code)
        try:
            result = subprocess.run(
                ["javac", str(src)], capture_output=True, text=True, timeout=10, cwd=tmp,
            )
            if result.returncode != 0:
                return result.stderr.replace(tmp + "/", "").strip()
        except Exception as e:
            return str(e)
    return None


def generate_question(client: anthropic.Anthropic, spec: Dict) -> dict:
    """Generate one question with 2 variants. Retries once if Java doesn't compile."""
    exemplar = pick_exemplar(spec["topics"])
    prompt = QUESTION_PROMPT.format(
        id=spec["id"],
        title=spec["title"],
        topics=", ".join(spec["topics"]),
        priority=spec["priority"],
        difficulty=spec["difficulty"],
        concept=spec["concept"],
        method_signature=spec["method_signature"],
        base_behavior=spec["base_behavior"],
        exemplar_code=exemplar,
    )

    for attempt in range(2):
        with client.messages.stream(
            model=MODEL, max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            raw = stream.get_final_text()
        data = robust_json_parse(raw)

        error = validate_java_compiles(data["java_starter"])
        if error is None:
            return data
        print(f"    [attempt {attempt + 1}] Java did NOT compile: {error[:150]}")
        # On retry, append the compile error to the prompt
        prompt = prompt + f"\n\nYour previous response's java_starter did NOT compile. Error:\n{error}\n\nFix it and return the JSON again."

    # If still broken after retry, return anyway — the error will show up in Run Code
    return data


def write_question(spec: Dict, data: dict) -> None:
    qdir = OUTPUT_DIR / spec["id"]
    qdir.mkdir(parents=True, exist_ok=True)
    (qdir / f"{spec['id']}.java").write_text(data["java_starter"])

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
    return {
        "student": "Bella",
        "session": 6,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": len(QUESTIONS_PLAN),
        "description": "Session 6 take-home (v2): 15 FRQ questions with working starter code and explicit method_type annotations. Targets Bella's weak areas (nested loops, index vs. value) and reinforces new concepts (ArrayList, constructors).",
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

    # Clear previous v1 questions but preserve _reference and _student_journey_report
    print(f"Clearing previous questions in {OUTPUT_DIR}")
    for q in QUESTIONS_PLAN:
        qdir = OUTPUT_DIR / q["id"]
        if qdir.exists():
            shutil.rmtree(qdir)
    mf = OUTPUT_DIR / "manifest.json"
    if mf.exists():
        mf.unlink()

    client = anthropic.Anthropic(api_key=api_key, timeout=300.0)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for spec in QUESTIONS_PLAN:
        print(f"  [{spec['id']}] generating... ({spec['title']})")
        try:
            data = generate_question(client, spec)
            write_question(spec, data)
            print(f"  [{spec['id']}] ✓ saved")
        except Exception as e:
            print(f"  [{spec['id']}] ✗ FAILED: {e}")
            continue

    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(build_manifest(), indent=2))
    print(f"\nManifest: {manifest_path}")
    print(f"Output: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
