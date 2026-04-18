"""
scripts/combine_variants_into_java.py
Purpose: For each question in take_home_session_6, fuse Q{N}.java's starter
         code with Q{N}A.json / Q{N}B.json into Q{N}A.java / Q{N}B.java —
         self-contained, runnable files with an embedded test runner.

Each generated Q{N}<A|B>.java:
  - Renames the class from Q{N} to Q{N}A (or Q{N}B)
  - Replaces the top docstring with the variant's mutation + task + concept
  - Keeps the starter method body as the thing the student modifies
  - Replaces main() with a test runner that runs every test case from the
    variant JSON, captures stdout, and prints PASS/FAIL vs expected

Usage: source backend/venv/bin/activate && python scripts/combine_variants_into_java.py
"""
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional

ROOT = Path(__file__).parent.parent
BASE_DIR = ROOT / "data" / "students" / "bella_data" / "take_home_session_6"


def read_manifest() -> dict:
    return json.loads((BASE_DIR / "manifest.json").read_text())


def strip_leading_docstring(java: str) -> str:
    """Remove the top /** ... */ block so we can insert our own."""
    return re.sub(r'^\s*/\*\*[\s\S]*?\*/\s*', '', java, count=1)


def strip_trailing_comment(java: str) -> str:
    """Remove the trailing /* ... */ block (often the answer key)."""
    # Find the last `}` (class close) and drop anything after it that is a /* ... */
    last_close = java.rfind('}')
    if last_close == -1:
        return java
    tail = java[last_close + 1:]
    if '/*' in tail:
        return java[:last_close + 1]
    return java


def find_main_block(java: str) -> Optional[tuple]:
    """Return (start_index, end_index) of the entire main() method, including braces."""
    m = re.search(r'public\s+static\s+void\s+main\s*\(\s*String\s*\[\s*\]\s*args?\s*\)\s*\{', java)
    if not m:
        return None
    start = m.start()
    brace_pos = java.index('{', m.end() - 1)
    depth = 0
    for i in range(brace_pos, len(java)):
        ch = java[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return (start, i + 1)
    return None


def java_string_literal(s: str) -> str:
    """Escape a Python string into a valid Java string literal (no surrounding quotes)."""
    return (s.replace('\\', '\\\\')
             .replace('"', '\\"')
             .replace('\n', '\\n')
             .replace('\r', '\\r')
             .replace('\t', '\\t'))


def header_docstring(question_title: str, qid: str, letter: str, variant: dict) -> str:
    """Build the top-of-file docstring from variant metadata."""
    topics = ", ".join(variant.get("topic_tags", []))
    mut = variant.get("mutation_description", "").strip()
    mod = variant.get("starter_modification", "").strip()
    concept = variant.get("concept_tested", "").strip()
    summary = variant.get("summary", {}) or {}
    what = (summary.get("what_this_tests") or "").strip()
    why = (summary.get("why") or "").strip()
    background = (summary.get("concept_background") or "").strip()

    # Indent multi-line strings so they render nicely inside /** */
    def indent(s: str, prefix: str = " *   ") -> str:
        if not s:
            return prefix + "(none)"
        return "\n".join(prefix + line for line in s.splitlines())

    return f"""/**
 * ─────────────────────────────────────────────────────────────────
 * {qid}{letter} — {question_title}  (Variant {letter})
 * ─────────────────────────────────────────────────────────────────
 *
 * TOPICS: {topics}
 * DIFFICULTY: {variant.get("difficulty", "medium")}
 *
 * ─────────────────────────────────────────────────────────────────
 * YOUR TASK (Variant {letter}):
 *
{indent(mut)}
 *
 * STEP-BY-STEP:
 *
{indent(mod)}
 *
 * ─────────────────────────────────────────────────────────────────
 * CONCEPT BEING TESTED:
 *   {concept}
 *
 * WHAT THIS PROBES:
{indent(what)}
 *
 * WHY IT MATTERS:
{indent(why)}
 *
 * BACKGROUND:
{indent(background)}
 *
 * ─────────────────────────────────────────────────────────────────
 * HOW TO USE:
 *   1. Modify the method below to match the task.
 *   2. Compile and run:   javac {qid}{letter}.java && java {qid}{letter}
 *   3. The test runner reports PASS/FAIL for each case with expected
 *      vs. actual output.
 * ─────────────────────────────────────────────────────────────────
 */
"""


def build_test_runner(qid: str, letter: str, variant: dict) -> str:
    """Build the main() + helper methods that run every test case."""
    test_cases: List[Dict] = variant.get("test_cases", [])

    # One small private method per test case so we can pass as a method ref.
    tc_methods_lines = []
    main_calls_lines = []
    for idx, tc in enumerate(test_cases, 1):
        tc_id = tc.get("id", f"tc{idx}")
        method_call = tc.get("method_call", "").strip().rstrip(";")
        method_type = tc.get("method_type", "void_print")
        expected = tc.get("expected_output", "")
        description = tc.get("description", "").strip()
        what = tc.get("what_it_tests", "").strip()
        wrong = tc.get("wrong_means", "").strip()

        # Decide how to invoke
        if method_type == "value_return":
            body = f"System.out.println({method_call});"
        else:
            # void_print: call bare
            body = f"{method_call};"

        method_name = f"__{tc_id}"
        tc_methods_lines.append(f"""    private static void {method_name}() {{
        {body}
    }}""")

        main_calls_lines.append(
            f'        runTest("{java_string_literal(tc_id)}", '
            f'"{java_string_literal(description)}", '
            f'"{java_string_literal(expected)}", '
            f'"{java_string_literal(what)}", '
            f'"{java_string_literal(wrong)}", '
            f'{qid}{letter}::{method_name});'
        )

    tc_methods = "\n\n".join(tc_methods_lines)
    main_calls = "\n".join(main_calls_lines)

    return f"""
    // ═══════════════════════════════════════════════════════════════
    //   TEST RUNNER — do not modify below this line
    // ═══════════════════════════════════════════════════════════════

    public static void main(String[] args) {{
        System.out.println("\\n─────────────────────────────────────────────────");
        System.out.println("  {qid}{letter} Test Runner");
        System.out.println("─────────────────────────────────────────────────\\n");
{main_calls}
        System.out.println();
        System.out.println("─────────────────────────────────────────────────");
        System.out.println("  Results: " + __passes + " passed, " + __fails + " failed");
        System.out.println("─────────────────────────────────────────────────");
    }}

{tc_methods}

    private static int __passes = 0;
    private static int __fails = 0;

    private static void runTest(String id, String desc, String expected,
                                String whatTests, String wrongMeans, Runnable fn) {{
        java.io.ByteArrayOutputStream buf = new java.io.ByteArrayOutputStream();
        java.io.PrintStream original = System.out;
        System.setOut(new java.io.PrintStream(buf));
        String actual;
        Throwable error = null;
        try {{
            fn.run();
            actual = buf.toString();
        }} catch (Throwable t) {{
            actual = buf.toString();
            error = t;
        }} finally {{
            System.setOut(original);
        }}
        // Compare normalized: strip trailing newlines/whitespace on both sides
        String a = actual.replaceAll("\\\\s+$", "");
        String e = expected.replaceAll("\\\\s+$", "");
        boolean passed = (error == null) && a.equals(e);
        System.out.println((passed ? "  \u2713 PASS  " : "  \u2717 FAIL  ") + "[" + id + "] " + desc);
        if (!passed) {{
            System.out.println("         expected : " + escape(expected));
            System.out.println("         actual   : " + escape(actual));
            if (error != null) {{
                System.out.println("         error    : " + error);
            }}
            System.out.println("         wrong means: " + wrongMeans);
        }}
        if (passed) __passes++;
        else __fails++;
    }}

    private static String escape(String s) {{
        return "\\"" + s.replace("\\\\", "\\\\\\\\")
                         .replace("\\"", "\\\\\\"")
                         .replace("\\n", "\\\\n")
                         .replace("\\t", "\\\\t") + "\\"";
    }}
"""


def combine_for_variant(qid: str, letter: str, question_title: str) -> Optional[str]:
    """Build one combined Java file for Q{qid}{letter}. Returns the source text."""
    qdir = BASE_DIR / qid
    java_path = qdir / f"{qid}.java"
    json_path = qdir / f"{qid}{letter}.json"
    if not java_path.exists() or not json_path.exists():
        return None

    starter = java_path.read_text()
    variant = json.loads(json_path.read_text())

    # Remove old top docstring and trailing answer-key comment
    src = strip_leading_docstring(starter)
    src = strip_trailing_comment(src)

    # Rename class Q{N} -> Q{N}A
    src = re.sub(rf'\bclass\s+{re.escape(qid)}\b', f'class {qid}{letter}', src)

    # Replace main() with test runner
    main_span = find_main_block(src)
    if not main_span:
        # If no main found, append before closing brace of class
        last_brace = src.rfind('}')
        new_body = build_test_runner(qid, letter, variant)
        src = src[:last_brace] + new_body + "\n}\n"
    else:
        start, end = main_span
        new_body = build_test_runner(qid, letter, variant)
        src = src[:start] + new_body.lstrip() + src[end:]

    # Inject our new docstring at the top
    docstring = header_docstring(question_title, qid, letter, variant)
    return docstring + src.lstrip()


def main() -> int:
    manifest = read_manifest()
    written = 0
    skipped = 0
    for q in manifest["questions"]:
        qid = q["id"]
        title = q["title"]
        for letter in ("A", "B"):
            combined = combine_for_variant(qid, letter, title)
            if combined is None:
                skipped += 1
                print(f"  [{qid}{letter}] skipped (missing source)")
                continue
            out_path = BASE_DIR / qid / f"{qid}{letter}.java"
            out_path.write_text(combined)
            written += 1
            print(f"  [{qid}{letter}] wrote {out_path.name}")

    print(f"\nDone. Wrote {written} files, skipped {skipped}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
