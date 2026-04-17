# Multi-Agent Development System — MyAPTutor

> Pattern 4: Agent Teams (Specialized Multi-Agent Systems)
> Describes how a five-agent development pipeline would be implemented
> in this repository, grounded in real-world implementations.

---

## The Analogy: A Surgical Team

Think of this like a hospital operating room — not a solo surgeon doing everything, but a **specialized team where each person owns a defined domain**. The attending (Planning Agent) decides what happens. The surgeon (Code Agent) executes. The scrub nurse (Testing Agent) confirms everything is sterile and correct. The quality officer (Review Agent) verifies no protocols were broken. The medical scribe (Documentation Agent) records what happened so the next team can pick up cleanly.

Each person *only does their job*. The surgeon doesn't write notes. The scribe doesn't cut. Violations cause errors.

---

## Reference Architectures

| System | Pattern | Relevance |
|---|---|---|
| **CrewAI** | Role-based agents with a Manager that delegates sequentially | Direct model — Planner as Manager, others as crew |
| **LangGraph** | Directed graph; nodes are agents, edges are handoff conditions | Models the feedback loops (test fail → back to code) |
| **AutoGen** | Agent conversations; agents call `transfer_to_X()` to hand off | The handoff function pattern fits MyAPTutor's phase gates |
| **Claude Agent SDK** | `Agent` spawns child agents with scoped tools + system prompts | The actual implementation mechanism here |
| **OpenAI Swarm** | Lightweight handoffs via function calls; shared context object | Informs the shared `HANDOFF_STATE.json` design below |

The architecture here is a **Blackboard + Sequential Pipeline hybrid** — the pattern used by CrewAI's hierarchical process and LangGraph's state machine, adapted to MyAPTutor's filesystem-first conventions.

The closest real-world reference is **Anthropic's own Three-Agent Harness** (Planner → Generator → Evaluator), documented in their [engineering post on long-running autonomous coding](https://www.anthropic.com/engineering/harness-design-long-running-apps). The five-agent system below is that triad extended with a Review and Documentation agent.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER / ORCHESTRATOR                          │
│              "Implement Phase 3: Claude API router"                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SHARED BLACKBOARD (filesystem)                  │
│                                                                     │
│  TASKS.md          PROGRESS.md       PARKING_LOT.md                 │
│  DECISIONS.md      BuildGuide.md     HANDOFF_STATE.json             │
│                                                                     │
└──────┬──────────┬───────────┬──────────┬────────────┬──────────────┘
       │          │           │          │            │
       ▼          ▼           ▼          ▼            ▼
  ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
  │PLANNING │ │ CODE   │ │TESTING │ │REVIEW  │ │   DOCS   │
  │ AGENT   │ │ AGENT  │ │ AGENT  │ │ AGENT  │ │  AGENT   │
  └─────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
```

---

## Pipeline Flow

```
                         ┌──────────────────────────────────────────┐
                         │         SESSION START / NEW TASK         │
                         └─────────────────┬────────────────────────┘
                                           │
                                           ▼
                         ╔═════════════════════════════════╗
                         ║       1. PLANNING AGENT          ║
                         ║                                  ║
                         ║  • Read PROGRESS.md (last 2)     ║
                         ║  • Read TASKS.md + PARKING_LOT   ║
                         ║  • Deliver 3-bullet briefing     ║
                         ║  • Decompose to atomic tasks     ║
                         ║  • Label MUST/SHOULD/NICE        ║
                         ║  • Scope ONE task for session    ║
                         ║  • Write plan to TASKS.md        ║
                         ╚═════════════════╦═══════════════╝
                                           ║
                              ┌────────────▼────────────┐
                              │  HANDOFF → code_agent   │
                              │  task: "Add /api/report  │
                              │  endpoint to ai.py"      │
                              └────────────┬────────────┘
                                           │
                                           ▼
                         ╔═════════════════════════════════╗
                         ║         2. CODE AGENT            ║
                         ║                                  ║
                         ║  • Narrate plan before coding    ║
                         ║  • Implement per phase rules     ║
                         ║  • Use get_student_dir() paths   ║
                         ║  • Register router in main.py    ║
                         ║  • Sync frontend types/backend   ║
                         ╚═════════════════╦═══════════════╝
                                           ║
                              ┌────────────▼────────────┐
                              │  HANDOFF → test_agent   │
                              │  artifacts:             │
                              │  [ai.py, main.py,       │
                              │   frontend/src/api/ai.ts]│
                              └────────────┬────────────┘
                                           │
                                           ▼
                         ╔═════════════════════════════════╗
                         ║        3. TESTING AGENT          ║
                         ║                                  ║
                         ║  • Start uvicorn, check /health  ║
                         ║  • curl /api/report endpoint     ║
                         ║  • Run __main__ validation block ║
                         ║  • Check schema sync             ║
                         ║  • Collect ALL failures, report  ║
                         ╚══════╦══════════════╦═══════════╝
                                ║              ║
                      ┌─────────▼──┐    ┌──────▼────────────┐
                      │   FAILED   │    │      PASSED        │
                      │ route back │    │ HANDOFF → reviewer │
                      │ to CODE    │    └──────┬─────────────┘
                      │ with errors│           │
                      └─────────┬──┘           ▼
                                │   ╔══════════════════════════════╗
                                │   ║       4. REVIEW AGENT        ║
                                │   ║                              ║
                       (loop    │   ║  • Security checklist        ║
                        max 3x) │   ║  • No raw string path concat ║
                                │   ║  • No phase boundary cross   ║
                                │   ║  • Schema compat check       ║
                                │   ║  • Named regression check    ║
                                │   ╚══════╦═══════════╦══════════╝
                                │          ║           ║
                                │   ┌──────▼──┐  ┌────▼──────────┐
                                │   │ ISSUES  │  │   APPROVED    │
                                └───┤ re-route│  │ HANDOFF →     │
                                    │ to CODE │  │ docs_agent    │
                                    └─────────┘  └────┬──────────┘
                                                       │
                                                       ▼
                                    ╔══════════════════════════════╗
                                    ║     5. DOCUMENTATION AGENT   ║
                                    ║                              ║
                                    ║  • Update BuildGuide.md      ║
                                    ║  • Write PROGRESS.md entry   ║
                                    ║  • Prompt DECISIONS.md log   ║
                                    ║  • Review PARKING_LOT.md     ║
                                    ╚══════════════════╦═══════════╝
                                                       ║
                                                       ▼
                                              SESSION COMPLETE
```

---

## Updated Architecture (with Structured Handoffs)

```
╔══════════════════════════════════════════════════════════════════════╗
║              MYAPTUTOR MULTI-AGENT DEVELOPMENT SYSTEM               ║
║                 (Anthropic 3-Agent Harness, Extended)               ║
╚══════════════════════════════════════════════════════════════════════╝

USER REQUEST
    │
    ▼
╔══════════════╗     reads           ┌─────────────────────────────┐
║   PLANNING   ║ ──────────────────► │  BLACKBOARD (filesystem)    │
║   AGENT      ║                     │                             │
║              ║ ◄──────────────────  │  TASKS.md                  │
║  tools:      ║     writes plan      │  PROGRESS.md               │
║  Read, Write ║                     │  PARKING_LOT.md             │
╚══════╦═══════╝                     │  DECISIONS.md               │
       ║                             │  BuildGuide.md              │
       ║ transfer_to_code_agent()    │  HANDOFF_STATE.json  ◄──┐  │
       ▼  [structured tool call]     └─────────────────────────│──┘
╔══════════════╗                                               │
║    CODE      ║ reads HANDOFF_STATE.json["scoped_task"]       │
║    AGENT     ║ (NOT the full planning thread)                │
║              ║                                               │
║  tools:      ║                                               │
║  Read,Write, ║                                               │
║  Edit,Bash,  ║                                               │
║  Grep,Glob   ║                                               │
╚══════╦═══════╝                                               │
       ║                                                       │
       ║ transfer_to_testing_agent(artifacts=[...])            │
       ▼                                                       │
╔══════════════╗                                               │
║   TESTING    ║                                               │
║   AGENT      ║ ──── FAIL (retry < 3) ──────────────────────►│
║              ║                             writes failure     │
║  tools:      ║                             to HANDOFF_STATE   │
║  Bash,Read,  ║                                               │
║  Grep        ║                                               │
╚══════╦═══════╝                                               │
       ║ PASS                                                  │
       ║ transfer_to_review_agent()                            │
       ▼                                                       │
╔══════════════╗                                               │
║    REVIEW    ║                                               │
║    AGENT     ║ ──── ISSUES ──────────────────────────────── ►│
║              ║                                               │
║  tools:      ║                                               │
║  Read,Grep,  ║  (read-only — never edits)                   │
║  Glob ONLY   ║                                               │
╚══════╦═══════╝                                               │
       ║ APPROVED                                              │
       ║ transfer_to_docs_agent()                              │
       ▼                                                       │
╔══════════════╗     writes      ┌──────────────────────────┐  │
║     DOCS     ║ ──────────────► │  BuildGuide.md           │  │
║    AGENT     ║                 │  PROGRESS.md             │  │
║              ║                 │  DECISIONS.md            │  │
║  tools:      ║                 │  TASKS.md (mark [x])     │  │
║  Read,Write, ║                 └──────────────────────────┘  │
║  Edit (docs  ║                                               │
║  only)       ║                                               │
╚══════════════╝                                               │
                                                               │
       ◄── CODE AGENT re-invoked with error context ──────────┘
            (max 3 retries, then surface to user)
```

---

## Agent Definitions

### 1. Planning Agent

**Analogy:** The attending physician who reads the chart and creates the care plan before any procedure begins.

**System Prompt Basis:** The full ADHD-Aware Protocol from `../CLAUDE.md` — specifically Phase 1 (Planning) and all behavioral rules.

**Tools (scoped intentionally narrow):**

| Tool | Permission | Why |
|---|---|---|
| `Read` | PROGRESS.md, TASKS.md, PARKING_LOT.md | Context gathering only |
| `Write` / `Edit` | TASKS.md, PROGRESS.md | Write the plan |
| **No** `Bash` | — | Cannot execute code — planning only |
| **No** `Edit` on source files | — | Prevents premature implementation |

**Trigger:** Session start, or new user task introduced.

**Output — HANDOFF_STATE.json:**
```json
{
  "agent": "planning",
  "session_goal": "Add /api/report endpoint (Phase 3 bootstrap)",
  "scoped_task": {
    "id": "add-report-endpoint",
    "label": "MUST",
    "description": "Create backend/routers/ai.py with POST /api/report. Register in main.py.",
    "done_when": "curl POST /api/report returns 200 with valid ReportSchema JSON",
    "estimated_minutes": 35,
    "files": ["backend/routers/ai.py", "backend/main.py", "backend/models/report.py"]
  },
  "deferred_to_parking_lot": [
    "study_guide endpoint",
    "streaming chat component"
  ]
}
```

---

### 2. Code Agent

**Analogy:** The surgeon — executes the operation step by step, narrating each move before making it.

**System Prompt Basis:** `.claude/rules/backend-python.md` + `.claude/rules/schema-sync.md` + phase-gating rules from `CLAUDE.md`.

**Tools:**

| Tool | Permission | Why |
|---|---|---|
| `Read` | All source files | Understand before modifying |
| `Edit` / `Write` | `backend/`, `frontend/src/` | Implementation |
| `Bash` | `uvicorn`, `uv run`, `npm run dev` | Verify server starts |
| `Grep` / `Glob` | Codebase | Find existing patterns |
| **No** `Edit` | `data/students/`, `.env` | Protected by data-safety rules |
| **No** `Edit` | `PROGRESS.md`, `BuildGuide.md` | Docs are Scribe's domain |

**Key behavioral constraints baked into system prompt:**
```
- Narrate before each code block: "I'm adding X because Y"
- Never use raw string concat for student paths — use get_student_dir()
- Phase 2/3/4 imports must be commented out in main.py until that phase is active
- Sync backend/models/ and frontend/src/types/ in the same change
- Every new Python file needs a __main__ validation block
```

**Scope drift guard (enforced inline):**
```
If current work touches a file not in HANDOFF_STATE.json["files"]:
  STOP. Write to PARKING_LOT.md. Return to scoped task.
```

---

### 3. Testing Agent

**Analogy:** The scrub nurse checking the instrument count before and after — nothing proceeds until the count is confirmed.

**System Prompt Basis:** `.claude/rules/testing-validation.md` — the "real data always, collect all failures" pattern.

**Tools:**

| Tool | Permission | Why |
|---|---|---|
| `Bash` | `uvicorn`, `curl`, `npm test`, `uv run` | Execute validation |
| `Read` | Source files, test fixtures | Read what was changed |
| `Grep` | Schema files, type files | Verify sync |
| **No** `Edit` / `Write` | — | Validates, never modifies |

**Validation sequence for every handoff:**
```
1. Backend health:
   uvicorn backend.main:app --reload &
   curl http://localhost:8000/api/health → expect {"status": "ok"}

2. New endpoint smoke test:
   curl -X POST /api/report -d @test_payload.json → expect 200 + valid schema

3. Schema sync check:
   Grep frontend/src/types/report.ts for each field in backend/models/report.py
   Verify camelCase ↔ snake_case alignment

4. __main__ validation block:
   uv run backend/routers/ai.py → must exit 0

5. Frontend type check:
   cd frontend && npm run type-check → 0 errors
```

**Output appended to HANDOFF_STATE.json:**
```json
{
  "testing": {
    "status": "FAIL",
    "failures": [
      "schema_sync: ReportSchema.topic_analysis missing in frontend/src/types/report.ts",
      "endpoint: POST /api/report returns 422 — student_name field missing from request model"
    ],
    "route_to": "code_agent"
  }
}
```

---

### 4. Review Agent

**Analogy:** The hospital's quality officer — goes through a rigid checklist. Not looking for taste improvements, only protocol violations.

**System Prompt Basis:** `.claude/rules/pr-review.md` + `.claude/rules/data-safety.md`.

**Tools:**

| Tool | Permission | Why |
|---|---|---|
| `Read` | All files | Read-only review |
| `Grep` | Codebase | Find violations |
| `Glob` | Codebase | Inventory what changed |
| **No** `Edit` / `Write` | — | Review agent reports — it does not fix |
| **No** `Bash` | — | No execution, no side effects |

**Fixed checklist (hardcoded into system prompt):**

```
SECURITY (block on any):
  □ No raw string path concat for student files
  □ No env vars logged or returned in responses
  □ No path traversal vector

SCHEMA (block on divergence):
  □ frontend/src/types/ in sync with backend/models/
  □ No fields that bypass test JSON schema

PHASE BOUNDARY (block on violation):
  □ No Phase 2/3/4 imports inside Phase 1 components

NAMED REGRESSIONS (block on any):
  □ _cleanup_orphan() untouched
  □ normalize_name() untouched
  □ Completion screen time signals intact

DOCS:
  □ BuildGuide.md updated if endpoints/components/schemas added
```

**Output:**
```json
{
  "review": {
    "status": "ISSUES",
    "issues": [
      "SECURITY: ai.py line 47 — student_name used in f-string path. Use get_student_dir().",
      "DOCS: BuildGuide.md not updated — new /api/report endpoint not documented."
    ],
    "route_to": "code_agent"
  }
}
```

---

### 5. Documentation Agent

**Analogy:** The medical scribe — writes the chart after the procedure so the next team can read exactly what happened without asking anyone.

**System Prompt Basis:** Documentation rules in `CLAUDE.md` + commit style rules.

**Tools:**

| Tool | Permission | Why |
|---|---|---|
| `Read` | All files | Understand what changed |
| `Edit` / `Write` | `BuildGuide.md`, `PROGRESS.md`, `DECISIONS.md`, `PARKING_LOT.md`, `TASKS.md` | Documentation only |
| **No** `Edit` on source files | — | Never modifies code |
| **No** `Bash` | — | No execution |

**Triggered actions:**
```
For every approved changeset:

1. BuildGuide.md — if new endpoint/component/schema:
   Add entry under correct phase section with:
   - Route or component name
   - Input/output schema reference
   - Which file it lives in

2. PROGRESS.md — append session entry:
   "What got done: [one sentence]
    Codebase state: working / uvicorn starts, tests pass
    Next step: [verb] [specific thing] in [specific file]"

3. DECISIONS.md — prompt:
   "We chose [X] over [Y] because [Z]. Log it?"

4. PARKING_LOT.md — review items deferred during session.
   Promote anything with 2+ votes to TASKS.md.

5. TASKS.md — mark completed task [x].
```

---

## Shared State: The Blackboard

All agents read from and write to the same filesystem — the pattern from AutoGen's shared context and LangGraph's state nodes.

```
BLACKBOARD (filesystem)
│
├── TASKS.md                 ← Planning Agent writes, all agents read
│                              "What is the queue?"
│
├── PROGRESS.md              ← Docs Agent writes, Planning Agent reads
│                              "What happened in prior sessions?"
│
├── PARKING_LOT.md           ← Code Agent writes during drift, Docs Agent promotes
│                              "What did we consciously defer?"
│
├── DECISIONS.md             ← Docs Agent writes on prompt
│                              "Why did we do this?"
│
├── BuildGuide.md            ← Docs Agent writes, Code Agent reads
│                              "What is the spec?"
│
└── HANDOFF_STATE.json       ← Live session only, deleted at session end
                               "What is the current agent, task, and results?"
```

**HANDOFF_STATE.json lifecycle:**
```
Planning creates it → Code reads/appends → Testing appends results
→ Review appends verdict → Docs archives key parts → file deleted
```

---

## Feedback Loops

```
Code Agent ←──────────────── Testing Agent (FAIL)
     ↑                              max 3 attempts
     │                              then: escalate to user
     └──────────────────────── Review Agent (ISSUES)
```

**Loop guard (prevents infinite cycles):**

```python
# In HANDOFF_STATE.json
{
  "retry_count": {
    "code_to_test": 2,   # if hits 3, stop and surface to user
    "code_to_review": 1
  }
}
```

This mirrors AutoGen's `max_turns` and LangGraph's conditional edges — explicit exit condition or the loop never terminates.

---

## Handoff Implementation

**From OpenAI Swarm and LangGraph research:** Don't let agents decide to hand off via natural language. Agents reasoning in prose about "I'm done now, passing to the reviewer" are unreliable. Use **structured tool calls**:

```python
def transfer_to_testing_agent(artifacts: list[str], notes: str) -> HandoffState:
    """Call this when implementation is complete and ready for validation."""
    return HandoffState(next_agent="testing", artifacts=artifacts, notes=notes)
```

The orchestrator intercepts this tool call and routes accordingly. The LLM can't "forget" to hand off because it must call the function to conclude its turn.

---

## Orchestrator Implementation (Claude Agent SDK)

```python
# orchestrator.py
import json
from anthropic import Anthropic

client = Anthropic()

AGENTS = {
    "planning": {
        "system": open(".claude/rules/session-management.md").read(),
        "tools": ["Read", "Write"],
    },
    "code": {
        "system": open(".claude/rules/backend-python.md").read()
                + open(".claude/rules/schema-sync.md").read(),
        "tools": ["Read", "Write", "Edit", "Bash", "Grep", "Glob"],
    },
    "testing": {
        "system": open(".claude/rules/testing-validation.md").read(),
        "tools": ["Bash", "Read", "Grep"],
    },
    "review": {
        "system": open(".claude/rules/pr-review.md").read()
                + open(".claude/rules/data-safety.md").read(),
        "tools": ["Read", "Grep", "Glob"],
    },
    "docs": {
        "system": "Documentation agent. Update BuildGuide.md, PROGRESS.md, DECISIONS.md only.",
        "tools": ["Read", "Write", "Edit"],
    }
}

def run_agent(name: str, task: str, handoff_state: dict) -> dict:
    agent = AGENTS[name]
    response = client.messages.create(
        model="claude-opus-4-6",
        system=agent["system"],
        messages=[{
            "role": "user",
            "content": f"Task: {task}\n\nCurrent state:\n{json.dumps(handoff_state)}"
        }]
    )
    return parse_handoff(response)

def run_pipeline(user_task: str):
    state = {"task": user_task, "retry_count": {}}

    state = run_agent("planning", user_task, state)

    while True:
        state = run_agent("code", state["scoped_task"], state)
        state = run_agent("testing", "validate changes", state)

        if state["testing"]["status"] == "PASS":
            break
        if state["retry_count"].get("code_to_test", 0) >= 3:
            raise Exception("Max retries reached — escalate to user")
        state["retry_count"]["code_to_test"] = state["retry_count"].get("code_to_test", 0) + 1

    state = run_agent("review", "review changes", state)
    if state["review"]["status"] == "APPROVED":
        state = run_agent("docs", "document changes", state)

    return state
```

---

## Mapping to MyAPTutor's Phase Structure

The agents map onto the existing phase architecture cleanly:

```
BUILD PHASE          AGENT RESPONSIBLE         READS FROM               WRITES TO
──────────────────── ─────────────────────── ── ────────────────────── ── ──────────────────────
Phase 1 (complete)   Planning + Docs          PROGRESS.md               TASKS.md
Phase 2 work         Code → Testing → Review  BuildGuide.md Phase 2     ai.py, audio.py
Phase 3 AI router    Code → Testing → Review  BuildGuide.md Phase 3     ai.py, main.py, types/
Phase 4 adaptive     Planning → Code → Docs   session_manager.py        test_gen prompt
```

The phase-gated import pattern in `backend/main.py`:
```python
# Add in Phase 2: from routers import audio; app.include_router(audio.router, ...)
# Add in Phase 3: from routers import ai;    app.include_router(ai.router, ...)
```
...becomes a **Review Agent rule**: "No Phase 3 import active until Phase 2 is validated by the Testing Agent."

---

## Five Critical Gotchas (from Production Experience)

Sources: [arXiv: Stop Wasting Tokens](https://arxiv.org/html/2510.26585v1), [Google production framework](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/), [The Multi-Agent Trap](https://towardsdatascience.com/the-multi-agent-trap/)

| # | Gotcha | Fix for MyAPTutor |
|---|---|---|
| 1 | **Context explosion** — naive chaining multiplies tokens 15x | Pass only `HANDOFF_STATE.json`, not prior agent threads |
| 2 | **Error cascade** — unstructured systems amplify errors 17x vs. single-agent | Structured topology + retry guard (max 3 loops) |
| 3 | **Tool descriptions > system prompts** — better tool descriptions cut task time 40% | Invest in the `transfer_to_X()` function docstrings, not just the agent system prompts |
| 4 | **Coordination overhead = 36.9% of failures** | Keep the pipeline shallow (5 agents max); don't add a 6th |
| 5 | **Context rot below the token limit** | Sliding-window: summarize completed phases, prune raw events, pass summary forward |

---

## State Management Options

| Framework | Mechanism | Verdict for this repo |
|---|---|---|
| **LangGraph** | Typed `StateGraph` dict, immutable updates | Best if you want pause/resume between agents |
| **CrewAI** | ChromaDB + SQLite memory | Overkill for a solo-developer workflow |
| **Anthropic SDK** | External files + structured summaries | **Best fit** — matches MyAPTutor's existing filesystem-first conventions |

The existing `PROGRESS.md` / `TASKS.md` / `PARKING_LOT.md` structure *is already* the Anthropic-recommended external state store. The only addition needed is `HANDOFF_STATE.json` as the live session artifact.

---

## Key Takeaway

The single most actionable finding from real-world implementations: the `transfer_to_X()` **structured tool call pattern** — not prose reasoning about handoffs — is the difference between a reliable pipeline and an unreliable one. That one change, formalizing the handoff as a typed function the LLM must call, is what makes this architecture implementable today versus theoretical.

---

## Sources

- [Anthropic: Multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Anthropic: Building Effective AI Agents](https://www.anthropic.com/research/building-effective-agents)
- [Anthropic: Harness design for long-running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps)
- [LangGraph: Hierarchical Agent Teams tutorial](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams/)
- [OpenAI Swarm: Orchestrating Agents cookbook](https://developers.openai.com/cookbook/examples/orchestrating_agents)
- [CrewAI: Agent Concepts docs](https://docs.crewai.com/en/concepts/agents)
- [Google: Production multi-agent framework](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/)
- [arXiv: Stop Wasting Tokens in Multi-Agent Systems](https://arxiv.org/html/2510.26585v1)
- [Towards Data Science: The Multi-Agent Trap](https://towardsdatascience.com/the-multi-agent-trap/)
- [InfoQ: Anthropic Three-Agent Harness](https://www.infoq.com/news/2026/04/anthropic-three-agent-harness-ai/)
