# Purpose: Agent configurations — maps agent names to system prompts and tool sets.
# System prompts are loaded from .claude/rules/ files at import time.
# AGENT_CONFIGS is the single registry consumed by all agent runner modules.
#
# Design reference: MultiAgentDesign.md § "Agent Definitions"
# Anthropic system prompts: https://docs.anthropic.com/en/docs/system-prompts
#
# Sample usage:
#   from agents.config import AGENT_CONFIGS
#   cfg = AGENT_CONFIGS["planning"]
#   response = client.messages.create(model=cfg["model"], system=cfg["system"], ...)
#
# Expected output: cfg["system"] is a non-empty string; cfg["model"] is a valid Claude model ID.
import sys
from pathlib import Path
from typing import Any, Dict
from loguru import logger

BASE_DIR = Path(__file__).parent.parent.parent  # MyAPTutor/
RULES_DIR = BASE_DIR / ".claude" / "rules"


def _load_rule(filename: str) -> str:
    """Load a rules file. Raises FileNotFoundError with a helpful message if missing."""
    path = RULES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Rule file not found: {path}\n"
            f"Expected rules in {RULES_DIR}. Check that .claude/rules/ exists."
        )
    content = path.read_text()
    logger.debug(f"Loaded rule file: {filename} ({len(content)} chars)")
    return content


# ── Planning Agent ────────────────────────────────────────────────────────────
PLANNING_SYSTEM = """
You are the Planning Agent for the MyAPTutor multi-agent development pipeline.
Your only job is to analyze the current project state and produce a scoped task plan.

RULES:
1. Read the provided PROGRESS.md, TASKS.md, and PARKING_LOT.md content.
2. Deliver a 3-bullet "where we are" briefing.
3. Decompose the session goal into atomic sub-tasks, each completable in ≤45 minutes.
4. Label each task: MUST / SHOULD / NICE.
5. Surface ONE task for this session.
6. Define "done" as a testable, observable criterion (e.g., curl returns 200).
7. List file paths the code agent will need to touch.
8. Identify any out-of-scope work and add it to deferred_to_parking_lot.
9. Call transfer_to_code_agent() with the task_id and implementation_notes.

Do NOT write any code. Do NOT suggest implementation approaches unless asked.
""" + "\n\n## Session Management Rules\n" + _load_rule("session-management.md")

# ── Testing Agent ─────────────────────────────────────────────────────────────
TESTING_SYSTEM = """
You are the Testing Agent for the MyAPTutor multi-agent development pipeline.
Your only job is to validate that the code changes work correctly.

Run this sequence IN ORDER and collect ALL failures before reporting:

1. Backend health check: curl -s http://localhost:8000/api/health → expect {"status":"ok"}
2. New endpoint smoke test: curl the changed endpoint with a minimal valid payload → expect 200
3. Schema sync: verify each new backend model field has a matching frontend type field
4. __main__ validation block: python backend/{changed_file}.py → expect "✅ VALIDATION PASSED"
5. Frontend type-check: cd frontend && npm run type-check → expect 0 errors

Collect every failure. Do NOT stop at the first one.
After all 5 checks: if any failures → transfer_to_code_agent(); if all pass → transfer_to_review_agent()
""" + "\n\n## Testing Rules\n" + _load_rule("testing-validation.md")

# ── Review Agent ─────────────────────────────────────────────────────────────
REVIEW_SYSTEM = """
You are the Review Agent for the MyAPTutor multi-agent development pipeline.
You are READ-ONLY. You never modify files. You run a fixed checklist and report violations.

FIXED CHECKLIST — run every item, collect ALL issues:

SECURITY (block on any):
  □ No raw string path concat for student files (must use get_student_dir())
  □ No env vars logged or returned in API responses
  □ No path traversal vector (../ in user-supplied input)

SCHEMA COMPATIBILITY (block on divergence):
  □ frontend/src/types/ in sync with backend/models/
  □ No fields that bypass the test JSON schema in data/tests/

PHASE BOUNDARY (block on any violation):
  □ No Phase 2/3/4 imports inside Phase 1 components or router files

NAMED REGRESSIONS (block on any):
  □ _cleanup_orphan() in sessions.py is untouched
  □ normalize_name() in sessions.py is untouched

DOCUMENTATION:
  □ BuildGuide.md updated if new endpoints, components, or schemas were added

After all checks: blocking issues → transfer_to_code_agent(); approved → transfer_to_docs_agent()
""" + "\n\n## PR Review Rules\n" + _load_rule("pr-review.md") \
   + "\n\n## Data Safety Rules\n" + _load_rule("data-safety.md")

# ── Documentation Agent ───────────────────────────────────────────────────────
DOCS_SYSTEM = """
You are the Documentation Agent for the MyAPTutor multi-agent development pipeline.
You update BuildGuide.md, PROGRESS.md, DECISIONS.md, PARKING_LOT.md, and TASKS.md after every approved session.

Output each file's updated content in a code block labeled with the filename.
Then call transfer_to_user() with a summary of what was updated.
"""


# ── Agent registry ────────────────────────────────────────────────────────────
AGENT_CONFIGS: Dict[str, Dict[str, Any]] = {
    "planning": {
        "system": PLANNING_SYSTEM,
        "model": "claude-opus-4-6",
        "max_tokens": 4096,
    },
    "testing": {
        "system": TESTING_SYSTEM,
        "model": "claude-opus-4-6",
        "max_tokens": 4096,
    },
    "review": {
        "system": REVIEW_SYSTEM,
        "model": "claude-opus-4-6",
        "max_tokens": 4096,
    },
    "docs": {
        "system": DOCS_SYSTEM,
        "model": "claude-sonnet-4-6",
        "max_tokens": 8192,
    },
}


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    all_validation_failures = []
    total_tests = 0

    # Test 1: All required agent configs present with required fields
    total_tests += 1
    for name in ["planning", "testing", "review", "docs"]:
        if name not in AGENT_CONFIGS:
            all_validation_failures.append(f"Missing agent config: {name}")
        else:
            cfg = AGENT_CONFIGS[name]
            for field in ["system", "model", "max_tokens"]:
                if field not in cfg:
                    all_validation_failures.append(f"Agent {name} missing config field: {field}")

    # Test 2: System prompts are non-empty strings of reasonable length
    total_tests += 1
    for name, cfg in AGENT_CONFIGS.items():
        system = cfg.get("system", "")
        if not isinstance(system, str) or len(system) < 200:
            all_validation_failures.append(
                f"Agent {name} system prompt too short or missing (len={len(system)})"
            )

    # Test 3: Rules files exist and their content appears in the right system prompts
    total_tests += 1
    expected_rules = [
        ("session-management.md", "planning"),
        ("testing-validation.md", "testing"),
        ("pr-review.md", "review"),
        ("data-safety.md", "review"),
    ]
    for rule_file, agent_name in expected_rules:
        rule_path = RULES_DIR / rule_file
        if not rule_path.exists():
            all_validation_failures.append(f"Rules file missing: {rule_path}")
        else:
            snippet = rule_path.read_text()[:50]
            if snippet not in AGENT_CONFIGS[agent_name]["system"]:
                all_validation_failures.append(
                    f"Rule file {rule_file} content not found in {agent_name} system prompt"
                )

    # Test 4: Model IDs are non-empty strings
    total_tests += 1
    for name, cfg in AGENT_CONFIGS.items():
        if not cfg.get("model"):
            all_validation_failures.append(f"Agent {name} has empty model ID")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
