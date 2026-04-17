"""
Strip tutor-facing prefixes from guiding question text in the test JSON.
Converts: 'Ask: "What index does..."'  ->  'What index does...'
          'Follow-up if B: "..."'       ->  '...'
          'If A: "..."'                 ->  '...'

Run once: python scripts/clean_guiding_questions.py
"""
import json, re
from pathlib import Path

TESTS_DIR = Path(__file__).parent.parent / "data" / "tests"

PREFIX_PATTERNS = [
    r'^Ask:\s*',
    r'^Follow-up if \w+:\s*',
    r'^If \w+:\s*',
]

def clean_text(text: str) -> str:
    for pattern in PREFIX_PATTERNS:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    # Strip outer quotes left behind
    text = text.strip().strip('"').strip("'").strip()
    return text

def clean_file(path: Path):
    data = json.loads(path.read_text())
    changed = 0
    for question in data.get("questions", []):
        for gq in question.get("guiding_questions", []):
            original = gq["text"]
            cleaned  = clean_text(original)
            if cleaned != original:
                gq["text"] = cleaned
                changed += 1
                print(f"  [{question['id']}] {original[:60]!r}")
                print(f"        -> {cleaned[:60]!r}")
    if changed:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"\n{path.name}: {changed} guiding questions cleaned.\n")
    else:
        print(f"{path.name}: nothing to clean.")

if __name__ == "__main__":
    for f in sorted(TESTS_DIR.glob("*.json")):
        print(f"\n=== {f.name} ===")
        clean_file(f)
