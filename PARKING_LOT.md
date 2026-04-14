# PARKING_LOT.md — MyAPTutor

> Ideas, bugs, tangents, and future work. Capture everything here so nothing derails the current task.
> Items get reviewed at session close-out and promoted to TASKS.md or DECISIONS.md when relevant.

---

## Ideas

<!-- Drop anything here mid-session with `parking lot it` -->

---

## Bugs / Issues Noticed

<!-- Things spotted but not in scope for the current task -->

---

## Questions / Decisions Deferred

<!-- Architectural questions to resolve in a future session -->

---

## Multi-Agent Pipeline — Follow-up items
- [ ] Add `done_when` and `files` parameters to `transfer_to_code_agent` tool schema so ScopedTask is fully populated from Claude's response (`backend/agents/transfers.py`)
- [ ] Add `logger.add("app.log", rotation="10 MB")` to `orchestrator.py` per backend-python.md logging rule
