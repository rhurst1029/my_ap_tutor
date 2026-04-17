# CLAUDE.md — MyAPTutor (AP CSA Adaptive Learning Platform)

> **Inherits from:** `../CLAUDE.md` (ADHD-Aware Development Partner Protocol)
> Read the parent file first. All behavioral rules, session phases, creative interventions,
> and shorthand commands defined there are in effect here. This file adds only what is
> project-specific.

> **For task implementation details:** see [BuildGuide.md](./docs/BuildGuide.md)

---

## Project Overview

An iterative AP CSA learning management tool for a private tutoring practice.
Core loop: **Gauge → Teach → Re-assess**. Each cycle tests the student, identifies weak
topics via time-per-question signals and Claude AI analysis, runs a targeted study module,
then generates an adaptive test for the next iteration.

**Stack:** React + TypeScript (Vite) · Python FastAPI · Vosk (local STT) · Claude API

**Phases:**
- Phase 1 (complete): Core test flow — name entry, timed Q&A, session save, completion screen
- Phase 2: Java visualizer (Monaco + step-through traces) + Vosk audio capture
- Phase 3: Claude AI layer — reports, study guides, streaming chat
- Phase 4: Full iteration loop — adaptive test generation, history-aware welcome

---

## Architecture Rules

- All student data lives under `data/students/{name}_data/` — never committed, always gitignored
- Student names are normalised to title case (`bella` → `Bella`) at the API boundary in `backend/routers/sessions.py`
- Session directories are only created on `/start`; the ghost-session guard in `_cleanup_orphan()` must be preserved
- The test JSON schema (`data/tests/*.json`) is the source of truth for question structure
- Backend routes follow the prefix pattern in `backend/main.py`; new routers must be registered there
- Phase-gated code (audio, visualizer, AI) lives in separate routers/components; imported only when that phase is active

---

## What to Protect

Never modify or suggest modifying:

- `data/students/` — runtime student data, never touched by automation
- `backend/.env` — secrets file, never read or written by any automated workflow
- `data/tests/ap_csa_test_1.json` — canonical test; changes require explicit human instruction
- `_cleanup_orphan()` and `normalize_name()` in `sessions.py` — fix real production bugs

---

## Documentation Rules

- **`CLAUDE.md`** (this file) — update when project structure, phases, or conventions change
- **`docs/BuildGuide.md`** — update when endpoints, components, schemas, or dependencies are added
- **`docs/MultiAgentDesign.md`** — design doc for the five-agent development pipeline (Planning, Code, Testing, Review, Docs); update when agent roles, tools, or handoff protocols change
- **`README.md`** (once created) — quickstart only; architecture lives in docs/BuildGuide.md
- No JSDoc/docstrings on code that wasn't changed; comments only where logic is non-obvious

---

## Commit Style

- Imperative mood, present tense: "Add completion screen" not "Added completion screen"
- Scope prefix when helpful: `frontend:`, `backend:`, `data:`, `scripts:`
- Breaking changes noted in the body
- No "WIP" commits to main

---

## Development Priority

1. Working code
2. Validation (with real data — see `.claude/rules/testing-validation.md`)
3. Readability
4. Static analysis (after code works)

---

## Running the App

```bash
# Backend
source backend/venv/bin/activate
uvicorn backend.main:app --reload

# Frontend (separate terminal)
cd frontend && npm run dev
```

Frontend: http://localhost:5173 · Backend: http://localhost:8000 · API docs: http://localhost:8000/docs
