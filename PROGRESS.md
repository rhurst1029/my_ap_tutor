# PROGRESS.md — MyAPTutor Session Log

> Append only. Never delete entries. Updated at every 45-minute checkpoint and session close-out.
> Format per entry: date/time · what got done · codebase state · next step · energy at close.

---

## Session: 2026-05-12 (session-4-bella — pre-exam tune-up test for Bella)

**What got done:**
- Hand-crafted `data/tests/generated/bella_data_assessment_6.json` (gitignored runtime file) — 10 MCQ + 1 FRQ targeted at the actual gaps surfaced in `bella_data/may_eleventh_report.md` and `bella_data/quiz_report_5.json`. The auto-generated `assessment_6` file from 2026-05-11 covered the quiz_report's still-weak topics (recursion, casting, conditionals, nested_loops) but missed today's session-floor gaps; replaced it with a sharper roster.
- MCQ topic coverage: enhanced for-loop value-vs-index (Q1, Q2 — biggest active gap from today, Q6+Q7 in this morning's session both hit it); `.length` vs `.size()` API confusion (Q3); 2D array indexing + nested traversal count (Q4, Q5 — Bella's self-flagged "horrible to work with" topic); ArrayList add/remove with shifting (Q6 — the other half of her self-flagged ask); triangle nested loop (Q7 — reinforces the `j <= i` rule she named correctly today); casting + int promotion (Q8 — Q7 from quiz_5); short-circuit boolean conditional with hidden div-by-zero trap (Q9 — Q10 from quiz_5); factorial recursion trace with explicit "skip if you can't trace in 30s" reminder (Q10 — recursion is MCQ-only in 2026 per Bella's surfaced format note).
- FRQ Q11: `collectInRange(int[] arr, int low, int high) → ArrayList<Integer>` — sibling of yesterday's `countAboveThreshold` pattern but collects into an ArrayList. Forces ArrayList API + compound-condition + counter+loop fluency in one shot. 6-test harness with embedded check() pattern, edge cases (empty result, low==high, negatives, empty input).
- Verified end-to-end: `Bella` login → adaptive resolver returns `bella_data_assessment_6` → frontend loads "Bella — Pre-Exam Tune-Up (Session 6)" → walked all 11 questions in browser → injected reference solution into Q11 Monaco editor → `Summary: 6/6 tests passed` with verdict "✓ Matches expected" and Submit FRQ enabled. Zero console errors.

**Codebase state:** Working. Backend on :8000 returns `bella_data_assessment_6` for Bella's next-test; frontend on :5173 renders the full test cleanly. JSON file is gitignored runtime data; no tracked-code changes in this session.

**Next step:** Bella logs in for tomorrow morning's pre-exam review. After the AP exam, address parking-lot items: 2D array + ArrayList practice block, take-home generator regressions, strategy-hint UI placement.

**Energy at close:** —

---

## Session: 2026-04-18 (session-4-bella — Take-Home IDE + Session 6 assignment)

**What got done:**
- Built in-browser Take-Home IDE at `/?takehome={student_dir}/{assignment_dir}` — Monaco editor, Run Code, Run Tests, Visualize (UWaterloo Java Visualizer iframe), Info panel, Reset. Consolidated toolbar (Tests/Visualize/Info became toolbar buttons alongside Run Code, panel tabs removed per user feedback).
- New backend route `backend/routers/takehome.py` — `GET /api/takehome/{student_dir}/{assignment}/{rest:path}` serves JSON and Java files from student take-home directories with path-traversal guards (regex-validated `{name}_data` + `take_home_session_{N}` directories).
- Fixed take-home test runner's void-method bug: used to wrap every `method_call` in `System.out.println(...)`, which failed for methods like `printTable(3)` that print internally. Runner now reads explicit `method_type` field from each test case (`"value_return"` or `"void_print"`) and falls back to heuristic (grep `static void <methodName>` in source) when omitted.
- Generated Bella's Session 6 take-home — 15 FRQ questions × 2 mutation variants (30 variants total). `scripts/generate_session6_takehome.py` calls Claude with topic-matched style exemplars from `_reference/`, compile-validates each starter with `javac`, retries once on failure.
- Built standalone Java deliverable — `scripts/combine_variants_into_java.py` fuses each question's base `Q{N}.java` + variant `Q{N}{A,B}.json` into a self-contained runnable `Q{N}{A,B}.java` with embedded test runner (captures stdout per test, rstrip-normalized comparison, PASS/FAIL report with "wrong means" diagnostics). 58 Java files total.
- Playwright student-journey test — `scripts/test_takehome_as_student.mjs` drives the web IDE as Bella, writes solutions via Monaco API, runs tests, captures 10 screenshots + `findings.json`. Passes 7/7 UI checks; found and fixed void-method bug that went from 2/3 → 3/3 on Q1A tests.
- Bella's Session 5 take-home analyzed and reported: 10/13 (77%), nested loops still at 33%. Generated `bella_session5_report.pdf` with tables + example trace tables via reportlab.
- Packaged deliverable as `take_home_session_6.zip` (178 KB) — 58 .java + 31 .json + README.

**Codebase state:** Working. Backend :8000 healthy, frontend :5173 serves take-home UI, all 30 variant Java files compile (10 intentionally require student signature changes — compile error IS the hint).

**Next step:** Optional — build native Java visualizer (JDI-based, research notes in session transcript) to replace the UWaterloo iframe. Also: regenerate Session 5 PDF with the v2 question format if tutoring model changes.

**Energy at close:** —

---

## Session: 2026-04-13 (continued)

**What got done:**
- Restructured CLAUDE.md into lean project-level file + modular `.claude/rules/` directory
- Installed parent ADHD-Aware Development Partner Protocol at `../CLAUDE.md`
- Created 6 path-targeted rules files: `backend-python.md`, `frontend-react.md`, `testing-validation.md`, `schema-sync.md`, `data-safety.md`, `pr-review.md`
- Created session tracking files: PROGRESS.md, TASKS.md, PARKING_LOT.md, DECISIONS.md

**Codebase state:** Working. No functional changes — documentation/tooling only.

**Next step:** Resume Phase 2 feature work per BuildGuide.md, or review TASKS.md for current priority.

**Energy at close:** —

---

## Session: 2026-04-13 (multi-agent design)

**What got done:**
- Designed full five-agent development pipeline (Planning, Code, Testing, Review, Documentation agents)
- Wrote `MultiAgentDesign.md` — architecture diagrams, agent definitions, tool scopes, handoff schemas, orchestrator implementation, and real-world reference citations
- Updated `DECISIONS.md`, `TASKS.md`, `CLAUDE.md` to reflect the design

**Codebase state:** Working. No functional changes — design documentation only.

**Next step:** Implement `orchestrator.py` per `MultiAgentDesign.md` Phase 5 tasks, starting with the `HANDOFF_STATE.json` schema and `transfer_to_X()` handoff functions.

**Energy at close:** —

---

## Session: 2026-04-16 (session-4-bella branch — Bella session 5 + repo cleanup)

**What got done:**
- Wrote `data/tests/generated/bella_data_quiz_5.json` — 5 FRQ (interactive implement-the-method, each with a 5-test verbose harness in `main()`) + 20 MC across AP units 1–10. All 5 FRQ starter templates compile; correct implementations reach `Summary: 5/5 tests passed`.
- Renamed `bella_data/session_5/` → `session_5_takehome/` so iteration logic returns 5 (the take-home artifacts are now isolated from in-app session counting).
- Fixed `_cleanup_orphan()` in `backend/routers/sessions.py` — added numeric-suffix filter so non-iteration directories (like `session_5_takehome`) cannot mask the real orphan when the user abandons a session.
- Added `latest_generated_test_id()` helper + wired both `/api/sessions/start` and `/api/sessions/{name}/next-test` admin branches to return the most recently modified file in `data/tests/generated/`. Admin login now previews whatever quiz was last generated.
- Removed two orphan dirs (`session_5/`, `session_6/`) created by abandoned login attempts before the `_cleanup_orphan` fix landed.
- IDE-style FRQ layout: Monaco editor height now `calc(100vh - 280px)`; added `.test-runner:has(.frq-card)` rule in `App.css` to lift the 760px max-width cap on FRQ pages only.
- Repo cleanup: deleted `.playwright-mcp/`, `frontend/README.md`, `.github/copilot-instructions.md` (stale Copilot config). User had already removed `claude-esp/`, `src/`, `out/`, and the entire `scripts/` directory. Updated `.gitignore` to cover `.playwright-mcp/`, `claude-esp/`, and `testing/node_modules/`. Swept stray `.DS_Store` files outside dependency dirs.

**Codebase state:** Working. Backend live at :8000 returns `bella_data_quiz_5` for both Bella and Admin; `/api/tests/bella_data_quiz_5` HTTP 200. Frontend `tsc --noEmit` exits 0.

**Next step:** Next: have Bella run the full quiz at http://localhost:5173 — verify FRQ verbose harness output renders cleanly in the new IDE-width layout, then commit the working tree.

**Energy at close:** —

---

## Session: 2026-04-14 (session-4-bella branch)

**What got done:**
- Verified Anthropic API credits working (streaming fix was required — sync client drops long Opus connections)
- Fixed `report_generator.py`: switched both Claude calls to `.stream()` + added 300s timeout; was silently failing on practice generation
- Added `scripts/generate_practice.py`: standalone practice generator with streaming, safe to run independently
- Wrote `testing/simulate_student.js`: Playwright script that drives the live frontend (localhost:5173) as a test student; simulated TestStudent 5/10 on ap_csa_assessment; session + report + practice all generated successfully
- Created `data/tests/generated/bella_data_test_4.json`: 10-question manually-curated quiz for Bella's session 4, built from session 4 transcript errors + session 3 report; covers arr[i] vs i, condition direction, return placement, accumulator scoping, nested loops, method return types, private fields, constructors
- Fixed `backend/routers/tests.py`: GET /{test_id} now checks `data/tests/generated/` as fallback so adaptive tests are accessible via the API

**Codebase state:** Working. Backend running. All changes committed except this session's work.

**Next step:** Next: run `git commit` to commit the quiz file, tests.py fix, report_generator.py streaming fix, generate_practice.py, and simulate_student.js. Then Bella logs in and session 4 auto-routes to bella_data_test_4.

**Energy at close:** —
