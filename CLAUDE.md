# CLAUDE.md — AP CSA Adaptive Learning Platform

This file defines how Claude should behave when working on this project,
whether in a local Claude Code session, a PR review, or a GitHub Actions workflow.

---

## Project Overview

An iterative AP Computer Science A learning management tool built for a private tutoring practice.
The core loop: **Gauge → Teach → Re-assess**. Each iteration tests the student, identifies weak
topics using time-per-question signals and Claude AI analysis, guides them through a targeted study
module, then generates an adaptive test for the next iteration.

**Stack:** React + TypeScript (Vite) frontend · Python FastAPI backend · Vosk (local STT) ·
Claude API for reports, study guides, adaptive test generation, and Q&A chat.

**Phases:**
- Phase 1 (complete): Core test flow — name entry, timed Q&A, session save, completion screen
- Phase 2: Java visualizer (Monaco + step-through traces) + Vosk audio capture
- Phase 3: Claude AI layer — reports, study guides, streaming chat
- Phase 4: Full iteration loop — adaptive test generation, history-aware welcome

---

## Code Style

- **TypeScript:** strict mode, no `any`, explicit return types on all exported functions
- **React:** functional components only, hooks for state, no class components
- **Python:** type hints on all function signatures, Pydantic models for all request/response shapes
- **Naming:** camelCase for TS/JS, snake_case for Python, kebab-case for CSS classes
- **CSS:** single `App.css` for global styles using CSS custom properties (`:root` variables); no CSS modules or Tailwind
- **No inline styles** except one-off layout overrides that don't belong in a shared class

---

## Architecture Rules

- All student data lives under `data/students/{name}_data/` — never committed, always gitignored
- Student names are normalised to title case (`bella` → `Bella`) at the API boundary in `backend/routers/sessions.py`
- Session directories are only created on `/start`; the ghost-session guard in `_cleanup_orphan()` must be preserved
- The test JSON schema (`data/tests/*.json`) is the source of truth for question structure — do not add fields to components that bypass it
- Backend routes follow the prefix pattern in `backend/main.py`; new routers must be registered there
- Phase-gated code (audio, visualizer, AI) lives in separate routers/components and is imported only when that phase is active

---

## Documentation Rules

When updating docs, follow these conventions:

- **`CLAUDE.md`** — update when project structure, conventions, or phase status changes
- **`BuildGuide.md`** — update when new endpoints, components, schemas, or dependencies are added; keep the phase checklists current
- **`README.md`** (once created) — keep to quickstart only: prerequisites, setup commands, how to run; no architecture details (those live in BuildGuide.md)
- Do not add JSDoc/docstrings to code that wasn't changed
- Code comments only where logic is non-obvious

---

## What to Protect

Never modify or suggest modifying:

- `data/students/` — runtime student data, never touched by automation
- `backend/.env` — secrets file, never read or written by any automated workflow
- `data/tests/ap_csa_test_1.json` — the canonical test; changes require explicit human instruction
- The `_cleanup_orphan` and `normalize_name` logic in `sessions.py` — these fix real bugs observed in production use

---

## PR Review Guidelines

When reviewing a pull request:

1. **Security first** — flag any path that could expose `data/students/`, leak env vars, or allow path traversal in file-serving routes
2. **Schema compatibility** — check that frontend types (`src/types/`) stay in sync with Pydantic models (`backend/models/`)
3. **Phase boundary** — flag imports of Phase 2/3/4 code into Phase 1 components
4. **Student data handling** — any new endpoint that reads/writes student files must use `get_student_dir()` for path construction, never raw string concatenation
5. **No regressions on** — ghost session fix, name normalization, guiding question text responses, completion screen time signals

---

## Commit Style

- Imperative mood, present tense: "Add completion screen" not "Added completion screen"
- Scope prefix when helpful: `frontend:`, `backend:`, `data:`, `scripts:`
- Breaking changes noted in the body
- No "WIP" commits to main

---

## Running the App

```bash
# Backend
source backend/venv/bin/activate
uvicorn backend.main:app --reload

# Frontend (separate terminal)
cd frontend && npm run dev
```

Frontend: http://localhost:5173  
Backend: http://localhost:8000  
API docs: http://localhost:8000/docs
