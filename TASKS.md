# TASKS.md — MyAPTutor

> Current task list with priorities. Updated each session.
> Labels: [MUST] = blocking · [SHOULD] = high value · [NICE] = when bandwidth allows
> All tasks must be completable in ≤45 minutes. If not, break it down first.

---

## Active

<!-- Add current session tasks here -->

---

## Backlog

### Phase 2
- [SHOULD] Set up Monaco editor component for Java visualizer
- [SHOULD] Integrate Vosk STT for audio capture
- [SHOULD] Wire audio capture to question flow in TestRunner

### Phase 3
- [SHOULD] Add Claude API router to backend
- [SHOULD] Build session report generation prompt
- [SHOULD] Build study guide generation prompt
- [SHOULD] Implement streaming chat component

### Phase 4
- [NICE] Adaptive test generation based on session history
- [NICE] History-aware welcome screen

### Phase 5 — Multi-Agent Development Pipeline
> Design: `MultiAgentDesign.md` | Implementation: `MultiAgentImplementation.md`
- [x] Build `orchestrator.py` — sequential pipeline runner with retry guard (max 3 loops)
- [x] Implement `transfer_to_X()` handoff tool functions per agent role
- [x] Define `HANDOFF_STATE.json` schema and lifecycle (create → append → delete)
- [x] Wire Planning Agent system prompt from `.claude/rules/session-management.md`
- [x] Wire Review Agent system prompt from `.claude/rules/pr-review.md` + `data-safety.md`
- [x] Wire Testing Agent validation sequence (uvicorn → curl → schema check → type-check)

---

## Completed

- [x] Phase 1: Core test flow (name entry, timed Q&A, session save, completion screen)
- [x] Restructure CLAUDE.md into modular rules directory
