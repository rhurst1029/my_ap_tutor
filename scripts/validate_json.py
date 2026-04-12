"""
Validates ap_csa_test_1.json against the BuildGuide schema.
Usage: python scripts/validate_json.py [path_to_json]
"""
import json, sys
from pathlib import Path

VALID_TYPES = {"multiple_choice", "free_response", "code_trace"}
VALID_TOPICS = {
    "variables_and_types", "operators", "conditionals", "loops",
    "arrays", "2d_arrays", "methods", "parameter_passing", "strings",
    "classes_and_objects", "inheritance", "polymorphism", "recursion",
    "arraylist", "searching_sorting", "interfaces"
}

errors = []

def err(msg):
    errors.append(msg)
    print(f"  ERROR: {msg}")

def warn(msg):
    print(f"  WARN:  {msg}")

def validate_test(data: dict):
    # Top-level fields
    for field in ["$schema", "test_id", "title", "created_at", "source", "questions"]:
        if field not in data:
            err(f"Missing top-level field: {field}")

    questions = data.get("questions", [])
    if not questions:
        err("No questions found")
        return

    ids_seen = set()
    for i, q in enumerate(questions):
        prefix = f"q[{i}] id={q.get('id', '?')}"

        # Required fields
        for field in ["id", "type", "topic_tags", "difficulty", "text", "options",
                      "answer_key", "explanation", "guiding_questions", "execution_trace"]:
            if field not in q:
                err(f"{prefix}: Missing field '{field}'")

        # ID uniqueness
        qid = q.get("id")
        if qid in ids_seen:
            err(f"{prefix}: Duplicate id '{qid}'")
        ids_seen.add(qid)

        # Type validation
        qtype = q.get("type")
        if qtype not in VALID_TYPES:
            err(f"{prefix}: Invalid type '{qtype}', must be one of {VALID_TYPES}")

        # Topic tags
        tags = q.get("topic_tags", [])
        if not tags:
            warn(f"{prefix}: Empty topic_tags")
        for tag in tags:
            if tag not in VALID_TOPICS:
                warn(f"{prefix}: Unknown topic tag '{tag}'")

        # Answer key
        answer = q.get("answer_key", "")
        if qtype in {"multiple_choice", "code_trace"} and answer not in {"A", "B", "C", "D"}:
            err(f"{prefix}: answer_key '{answer}' must be A/B/C/D for {qtype}")

        # Options for MC/code_trace
        opts = q.get("options", [])
        if qtype in {"multiple_choice", "code_trace"} and len(opts) != 4:
            err(f"{prefix}: Expected 4 options for {qtype}, got {len(opts)}")

        # code_block for code_trace
        if qtype == "code_trace" and not q.get("code_block"):
            warn(f"{prefix}: code_trace question has no code_block")

        # Guiding questions
        for j, gq in enumerate(q.get("guiding_questions", [])):
            gprefix = f"{prefix} gq[{j}]"
            for field in ["id", "text", "intent"]:
                if field not in gq:
                    err(f"{gprefix}: Missing field '{field}'")

    print(f"\n  Validated {len(questions)} questions. IDs: {sorted(ids_seen)}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/tests/ap_csa_test_1.json"
    path = Path(path)

    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    print(f"Validating {path}...")
    data = json.loads(path.read_text())
    validate_test(data)

    if errors:
        print(f"\nFAILED with {len(errors)} error(s).")
        sys.exit(1)
    else:
        print("\nPASSED — JSON schema is valid.")
