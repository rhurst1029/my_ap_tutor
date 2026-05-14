# PROGRESS.md — MyAPTutor Session Log

> Append only. Never delete entries. Updated at every 45-minute checkpoint and session close-out.
> Format per entry: date/time · what got done · codebase state · next step · energy at close.

---

## Session: 2026-05-14 (session-4-bella — guided practice UI flow)

**What got done:**
- Built a tutor-facing **guided practice** flow that turns the 2-hour day-before-exam session plan into a timed, stage-by-stage UI walkthrough. Earlier this session I researched test-prep literature and wrote `data/students/bella_data/may_fourteenth_session_plan.md` (the 2-hour plan) + `data/references/test_day_prep_research.md` (+ PDFs of both via a reportlab `md_to_pdf.py` script); this feature implements that plan in the app.
- New files (all tracked):
  - `frontend/src/components/GuidedPractice/guidedPlan.ts` — `GUIDED_PLAN`, 7 typed `GuidedStage` objects encoding the plan (re-anchor, warm-up retrieval, interleaved FRQ rehearsal, break, strategy rehearsal, psychological tools, close-out). Stage kinds: `instruction`, `warmup`, `frq`, `break`, `writing`.
  - `frontend/src/components/GuidedPractice/GuidedPractice.tsx` — stage-walker component: per-stage countdown timer (auto-start, Pause/Resume/Reset, clamps at 0 without auto-advancing — tutor controls pace), progress bar + stage dots, Prev/Next nav with "Finish" on the last stage, per-stage checklist with persistent tick-state, expressive-writing textarea on the writing stage.
  - The FRQ rehearsal stage embeds the existing `TestRunner` inline on `bella_data_quiz_8` (user chose inline embed over a link-out hand-off). The runner is mounted once the FRQ stage is first reached and then kept alive via a `display` toggle, so navigating away and back does NOT restart its backend session.
- Wired `?guided=1` URL param into `App.tsx` (mirrors the existing `?test=` / `?takehome=` pattern) — added the `'guided'` screen state and render branch. Plan is Bella-specific for v1, so the route hardcodes `studentName='Bella'`.
- Added `.guided-*` styles to `App.css` using the existing CSS custom properties (dark theme, no new CSS deps).
- Updated `docs/BuildGuide.md` with a "Guided Practice" section (route, plan-data schema, component behavior).

**Codebase state:** Working. `tsc --noEmit` exits 0. Browser-verified end-to-end via Playwright: walked all 7 stages, confirmed checklist toggling, the embedded FRQ TestRunner loading quiz_8 (Monaco mounted, Question 1 of 4), the writing textarea, Finish button on the last stage, and — critically — that the TestRunner persists across stage navigation (mount-marker survived a round-trip) and the writing text persists too. Zero console errors.

**Next step:** If guided practice should support students beyond Bella, lift the hardcoded plan into a backend-served JSON keyed by student (mirrors how `?test=` resolves). Not needed for tomorrow's session.

**Energy at close:** —

---

## Session: 2026-05-13 (session-4-bella — fix FRQ prompt formatting)

**What got done:**
- User reported the FRQ prompt text rendered as "one giant paragraph" and was intimidating. Root cause: `QuestionCard.tsx` line 156 dumps `question.prompt` (which now contains many `\n`, bullets, headings) into a single `<p>` whose default `white-space: normal` collapses all whitespace.
- Fix part 1 (tracked): added `white-space: pre-wrap;` to `.question-prompt` in `frontend/src/App.css`. One-line change. Newlines, indentation, and blank-line breaks now render. Verified via Playwright `getComputedStyle` — `whiteSpace = "pre-wrap"`. Visual line count for the Q1 FRQ prompt jumped from ~1 paragraph to ~38 visual lines with proper structure (headers framed by `===` dividers, numbered tips on separate lines, bullets on separate lines).
- Fix part 2 (gitignored data): the new prompts contained `**bold**` markdown and inline ` `code` ` backticks left over from the strategy-guide layering. Without a markdown renderer those produce visible asterisks and backticks. Stripped both via in-place Python regex pass on `bella_data_quiz_8.json` — 0 asterisks and 0 backticks remain in the prompt text.

**Codebase state:** Working. Frontend `App.css` updated; backend unchanged; quiz_8 JSON cleaned in place (still gitignored). Backend continues to serve quiz_8 as Bella's next-test. Visual smoke test passed (screenshot showed proper sectioning of the GENERAL FRQ STRATEGY block, the numbered checklist, the Rules bullets, and the per-FRQ Strategy Reminders).

**Next step:** If a future test wants real markdown (bold, code spans, headings), add `react-markdown` and replace `<p className="question-prompt">{...}</p>` with `<ReactMarkdown>{...}</ReactMarkdown>`. Not needed today — the pre-wrap + strip combo is enough.

**Energy at close:** —

---

## Session: 2026-05-13 (session-4-bella — AP25-style FRQ drill + strategy guide, session 8)

**What got done:**
- Bella completed yesterday's practice exam in the browser (session_7) — auto-generated `bella_data/quiz_report_7.json` shows 100% accuracy with q10 `hasEnoughPaint` (2D array FRQ) consuming **432 seconds** — by far the longest. Weak signals identified for next session: `2d_arrays`, `free_response_coding`, `nested_loops`, plus a recommendation to "introduce FRQ-style problems from past AP exams".
- Created `data/tests/generated/bella_data_quiz_8.json` (gitignored) — a 4-FRQ AP25-style drill that mirrors the structure and subjects of the actual 2025 AP CSA FRQ paper (extracted via pypdf from `https://apcentral.collegeboard.org/media/pdf/ap25-frq-computer-science-a.pdf`):
  - q1 `PetFeeder.feedPets` — methods + helper-class delegation + min logic (mirrors AP25 #1 DogWalker.walkDogs)
  - q2 `EmailHandle` — full class with constructor + 2 string-manipulation methods (mirrors AP25 #2 SignedText)
  - q3 `PracticeBracket.buildPairings` — ArrayList + two-pointer paired traversal (mirrors AP25 #3 Round.buildMatches)
  - q4 `PuzzleGrid.clearPair(row, col)` — **2D array search + mutation** (mirrors AP25 #4 SumOrSameGame.clearPair) — the targeted drill for Bella's 432s slowness signal
- Built via Python generator script `/tmp/gen_quiz_8.py` (compile-verifies each starter and reference solution before emitting JSON). Verified offline: q1 starter 0/5 → ref 5/5; q2 starter 1/7 → ref 7/7; q3 starter 0/5 → ref 5/5; q4 starter 2/6 → ref 6/6.
- **Layered FRQ strategy guidance into every prompt** from the new reference transcript at `data/references/how_to_answer_frqs_transcript.txt` (John's APCSA FRQ tutorial):
  - Top-level GENERAL FRQ STRATEGY block on every FRQ (return-type check, hand-trace examples, USE provided helpers, declare anything for partial credit)
  - Per-FRQ Strategy Reminders sections specific to that FRQ type:
    - FRQ-1-style: helper-method usage gets full credit, min-of-two pattern, side-effect verification
    - FRQ-2-style: #1 mistake = forgetting the constructor, indexOf returns -1, substring inclusive/exclusive trap
    - FRQ-3-style: build-a-new-list recipe, REMOVE in reverse, two-pointer with strict `<`, adjacent-pair pattern needs i=1 start
    - FRQ-4-style: one-column = no nested loops, one-row = no nested loops, find-min/max never returns early (but find-first-match does), cache target before mutation
  - Added 1-2 strategy-derived guiding_questions per FRQ (4 of them now reference the guide directly)
- Title bumped to "Bella — AP25-Style FRQ Drill + Strategy Guide (Session 8)" so the change is visible at the top of the test.

**Codebase state:** Working. Backend on :8000 returns `bella_data_quiz_8` for Bella's next-test (iteration 8). Frontend renders the 4 FRQs with strategy text intact. JSON file is gitignored (41 KB on disk, 36 KB served).

**Next step:** Bella runs the AP25-style FRQ drill at her next session — focus on q4 fluency drill for the 2D-array gap. After: keep cycling AP-past-FRQ-style content per the report's recommendation.

**Energy at close:** —

---

## Session: 2026-05-12 (session-4-bella — practice exam for Bella, session 7, post-AP-exam)

**What got done:**
- Replaced `data/tests/generated/bella_data_quiz_7.json` (gitignored) — was a 5-FRQ pure drill earlier this session; now a mixed-format **practice exam** (8 MCQ + 2 FRQ) synthesized from three inputs: today's session transcript (`bella_data/may_twelth.txt`), the auto-generated `bella_data/practice_6.json` problem bank, and the timing/weak-signals in `bella_data/report_6.json`. The drill version was never run by Bella (today's session happened in person, not in the IDE) so overwriting was safe.
- MCQ coverage maps to today's actual session content + lingering gaps:
  - Q1 Fibonacci recursion trace (today's recursion topic)
  - Q2 Merge step from merge sort (today's merge sort walkthrough — sidesteps the recursion mastery hurdle by drilling the in-place merge)
  - Q3 ArrayList `.set` vs `.add(i,v)` vs `.replace` (Bella's open question from today's transcript — the answer is `.set`)
  - Q4 Enhanced for-loop value-vs-index (persistent gap from May 11 report — kept in rotation)
  - Q5 Compound-conditional range check (mirrors practice_6 problem 1)
  - Q6 2D array surface-area accumulation (today's paint problem topic)
  - Q7 Parallel ArrayLists with GPA filter (mirrors practice_6 problem 5)
  - Q8 Remove-during-iteration skip-bug (mirrors practice_6 problem 4 — known AP CSA pitfall)
- FRQs target the slowness signal in report_6 (565s on the lone FRQ vs ~56s avg on MCQs):
  - Q9 `squareValuesInPlace(ArrayList<Integer>) → void` — the problem they DIDN'T finish today, plus operationally answers the open `.set` question. Forces in-place mutation pattern.
  - Q10 `hasEnoughPaint(int[][] surfaces, int gallons) → boolean` — exactly today's paint problem, integrating 2D arrays + accumulator + boundary `>=` comparison.
- Verified all FRQs offline (javac+java):
    q9 starter 1/5 → ref 5/5
    q10 starter 2/6 → ref 6/6
- Verified end-to-end in browser via Playwright: name=Bella → adaptive resolver picks `bella_data_quiz_7` → "Quiz — Bella — Practice Exam (Session 7)" renders Question 1 of 10 → walked all 8 MCQs and got every answer-key correct on first try → landed on Q9 with Monaco mounted → Run on unmodified Q9 starter → "Summary: 1/5 tests passed" (matches offline baseline exactly). Zero console errors throughout.

**Codebase state:** Working. Backend on :8000 returns `bella_data_quiz_7` (now the practice exam). Frontend renders the 10 mixed questions cleanly. JSON file is gitignored; only PROGRESS.md is tracked here.

**Next step:** Bella runs the practice exam at her next session. After: address parking-lot items (2D array + ArrayList drill block, take-home generator regressions, strategy-hint UI placement).

**Energy at close:** —

---

## Session: 2026-05-12 (session-4-bella — FRQ-only drill quiz for Bella, session 7)

**What got done:**
- Hand-crafted `data/tests/generated/bella_data_quiz_7.json` (gitignored) — 5 FRQ-only quiz targeted at the slowdown signal in `bella_data/report_6.json`. The report shows 100% accuracy but a 565s spike on the lone FRQ (vs. ~56s avg on MCQs); weak signals were "methods (writing from scratch)", "arraylist (constructing)", and "conditionals (compound conditions in code-writing)". Replaced the auto-generated mixed quiz_7 (8 questions: 3 code_trace + 2 MC + 2 FRQ + 1 trace) with a pure FRQ drill.
- FRQ ladder by difficulty:
  - q1 `countInRange(int[], int, int) → int` — counter + compound condition warm-up (target <2 min).
  - q2 `buildSquares(int n) → ArrayList<Integer>` — ArrayList construction from scratch (target <3 min).
  - q3 `findFirstDuplicate(int[]) → int` — nested loop with `j < i` (triangle pattern) + early-return + sentinel (target <4 min).
  - q4 `largestEvenInGrid(int[][]) → int` — 2D nested loops + compound conditional + max tracker + sentinel (target <5 min).
  - q5 `mostFrequent(ArrayList<String>) → String` — full integration: ArrayList input + nested loop + .equals() + tracker variable + tie-break-via-strict-> + empty-list guard (target <6 min).
- Each FRQ has 5–6 tests covering edge cases (empty input, single element, all-tied, sentinel-return paths). Each starter compiles cleanly with a safe-default return that produces an honest non-zero baseline pass count (Bella sees what's already passing before she writes a line).
- Verified all 5 offline via javac+java:
    q1 starter 2/6 → ref 6/6
    q2 starter 1/5 → ref 5/5
    q3 starter 3/5 → ref 5/5
    q4 starter 2/5 → ref 5/5
    q5 starter 1/5 → ref 5/5
- Verified in browser: name=Bella → adaptive resolver picks `bella_data_quiz_7` (iteration 7, session_type=quiz) → "Quiz — Bella — FRQ Drill (Session 7)" renders Question 1 of 5 with Monaco editor → Run on the unmodified starter → "Summary: 2/6 tests passed" (matches offline baseline). Zero console errors.

**Codebase state:** Working. Backend on :8000 returns `bella_data_quiz_7` (with priority over the parallel auto-generated `assessment_7`); frontend renders the 5 FRQs cleanly. JSON file is gitignored; only PROGRESS.md is tracked.

**Next step:** Bella runs the quiz post-AP-exam (FRQ fluency drill, not exam-prep). After: address parking-lot items.

**Energy at close:** —

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
