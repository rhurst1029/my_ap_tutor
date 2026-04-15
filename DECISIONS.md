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

**Multi-agent development pipeline design (see `MultiAgentDesign.md`)**
- Alternatives considered: single-agent sessions (current), CrewAI framework, LangGraph state graph
- Why this design: Sequential Pipeline + Blackboard hybrid maps directly onto the existing filesystem-first conventions (`TASKS.md`, `PROGRESS.md`, `HANDOFF_STATE.json`). The `.claude/rules/` files already function as scoped system prompts for each agent role — no new infrastructure required. Anthropic's own Three-Agent Harness (Planner → Generator → Evaluator) is the closest real-world reference and validates the approach.
- Why not a framework: CrewAI and LangGraph add dependencies and abstraction layers that would outweigh the benefit for a solo-developer workflow. The Claude Agent SDK is sufficient.
- Key constraint: Each agent receives only `HANDOFF_STATE.json["scoped_task"]`, not the full prior thread — prevents context explosion (15x token multiplication documented in multi-agent research).
- Not yet implemented — design only. Implementation tracked in `TASKS.md`.
- Date: 2026-04-13

---
