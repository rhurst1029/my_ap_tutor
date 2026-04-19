# DECISIONS.md — MyAPTutor

> Why key technical choices were made. Prevents "why did I do this?" re-investigation.
> Format: [Decision] → [Alternatives considered] → [Why this choice] → [Date]

---

## Architecture

**Vite + React + TypeScript for frontend**
- Alternatives: Next.js, plain React
- Why: Fast dev server, no SSR overhead needed for local tutoring tool, TypeScript safety for schema sync
- Date: Initial build

**FastAPI for backend**
- Alternatives: Flask, Django
- Why: Async-native, automatic OpenAPI docs at /docs, Pydantic models enforce schema sync with frontend
- Date: Initial build

**Student data in flat files under `data/students/`**
- Alternatives: SQLite, PostgreSQL
- Why: Single-tutor use case, no concurrent writes, zero infrastructure, easy to inspect/backup manually
- Date: Initial build

**`_cleanup_orphan()` ghost session guard**
- Why: Observed in production — browser refresh during `/start` created orphaned session directories that broke re-entry. Guard detects and removes them before creating a new session.
- Date: Post-Phase-1 bugfix

---

## Tooling

**Modular `.claude/rules/` over monolithic CLAUDE.md**
- Why: Path-targeted rules give Claude exactly the right instructions for the files being edited without context noise from unrelated domains. 350-line monolith had all concerns competing at equal priority.
- Date: 2026-04-13

**Repo cleanup pass — removed unreferenced files and stale tooling configs**
- Removed: `claude-esp/` (400 MB external Go monorepo, never integrated), `src/Main.java` + `out/` (Copilot-era Java workspace, no build pipeline), `.github/copilot-instructions.md` (described project as "tiny Java learning workspace" — contradicted current CLAUDE.md), `.playwright-mcp/` (local MCP screenshots), `frontend/README.md` (Vite stub), and the entire `scripts/` directory (one-off generators superseded by `backend/services/`).
- Kept: `convert_docx.py`-style references in `docs/BuildGuide.md` are now stale but harmless; left in place to avoid touching long-form docs in this batch.
- Verified safe via `Explore`-agent grep audit + a second verification pass — every deleted path had zero cross-references in code or active markdown.
- Side fix: `_cleanup_orphan()` numeric-suffix filter (so `session_5_takehome` no longer masks real orphans) and `latest_generated_test_id()` admin route — both committed alongside the cleanup since they fixed the immediate "Bella login lands on wrong test" symptom.
- Date: 2026-04-16

**Take-home assignment format — standalone Java files with embedded test runner**
- Alternatives: in-browser only (web IDE via backend execute endpoint), static HTML MC quiz, Jupyter-style notebook
- Why: Student can work entirely offline in IntelliJ/VS Code without running our backend. Each `Q{N}{A,B}.java` is fully self-contained — embedded docstring explains the task, `main()` is a test runner that captures stdout, compares to expected, and prints PASS/FAIL with "wrong means" diagnostics. Also kept `.json` files so the web IDE (`/?takehome=...`) works when the backend is running.
- Explicit `method_type` field (`"value_return"` | `"void_print"`) on every test case — removed a fragile heuristic that tried to detect void methods from trailing-newline patterns in expected output. Heuristic fallback (grep `static void <methodName>` in code) still present for any variant that omits the field.
- Compile-validation loop in generator — every AI-generated starter goes through `javac` before being written; on failure, Claude gets the error back and retries once.
- Date: 2026-04-18

**Take-home web IDE served via dedicated path-validated backend route**
- Alternatives: Vite public dir + symlink, separate static-file server, embed-all-data in single HTML
- Why chose `/api/takehome/{student_dir}/{assignment}/{rest:path}`: avoids exposing `data/students/` broadly (regex-gates both student_dir and assignment names), lets the same dev setup serve both the web IDE and the zip deliverable, keeps auth trivial (single-tutor model). Rejected paths containing `..` and non-matching directory names.
- Date: 2026-04-18

**Multi-agent development pipeline design (see `MultiAgentDesign.md`)**
- Alternatives considered: single-agent sessions (current), CrewAI framework, LangGraph state graph
- Why this design: Sequential Pipeline + Blackboard hybrid maps directly onto the existing filesystem-first conventions (`TASKS.md`, `PROGRESS.md`, `HANDOFF_STATE.json`). The `.claude/rules/` files already function as scoped system prompts for each agent role — no new infrastructure required. Anthropic's own Three-Agent Harness (Planner → Generator → Evaluator) is the closest real-world reference and validates the approach.
- Why not a framework: CrewAI and LangGraph add dependencies and abstraction layers that would outweigh the benefit for a solo-developer workflow. The Claude Agent SDK is sufficient.
- Key constraint: Each agent receives only `HANDOFF_STATE.json["scoped_task"]`, not the full prior thread — prevents context explosion (15x token multiplication documented in multi-agent research).
- Not yet implemented — design only. Implementation tracked in `TASKS.md`.
- Date: 2026-04-13

---
