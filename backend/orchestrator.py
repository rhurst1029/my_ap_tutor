#!/usr/bin/env python3
# Purpose: Multi-agent development pipeline orchestrator.
# Runs: Planning → [Code — human/Claude Code step] → Testing → Review → Docs
#
# Design reference: MultiAgentDesign.md § "Orchestrator Implementation"
# Claude multi-agent patterns: https://www.anthropic.com/research/building-effective-agents
#
# Sample usage:
#   PYTHONPATH=backend python backend/orchestrator.py "Add /api/report endpoint"
#   PYTHONPATH=backend python backend/orchestrator.py --resume
#
# Expected output: Pipeline runs to completion; HANDOFF_STATE.json deleted at end.
import argparse
import sys
from pathlib import Path

import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent))
from config import ANTHROPIC_API_KEY
from agents.handoff import read_handoff_state
from agents.planning import run_planning_agent
from agents.testing import run_testing_agent
from agents.review import run_review_agent
from agents.docs import run_docs_agent

BASE_DIR     = Path(__file__).parent.parent  # MyAPTutor/
HANDOFF_PATH = BASE_DIR / "HANDOFF_STATE.json"
MAX_RETRIES  = 3


def _print_banner(agent: str) -> None:
    width = 60
    print("\n" + "=" * width)
    print(f"  AGENT: {agent.upper()}")
    print("=" * width)


def _print_code_agent_instructions(state) -> None:
    """Print human-readable instructions for the Code Agent step."""
    print("\n" + "=" * 60)
    print("  CODE AGENT STEP — Human / Claude Code Required")
    print("=" * 60)
    print(f"\nTask ID:     {state.scoped_task.id}")
    print(f"Description: {state.scoped_task.description}")
    print(f"Done when:   {state.scoped_task.done_when}")
    if state.scoped_task.files:
        print(f"Files:       {', '.join(state.scoped_task.files)}")
    print(f"\nHANDOFF_STATE.json: {HANDOFF_PATH}")
    print("\nNext steps:")
    print("  1. Implement the task above in Claude Code")
    print("  2. When done, re-run:")
    print(f"     PYTHONPATH=backend python backend/orchestrator.py --resume")
    print()


def run_pipeline(session_goal: str) -> None:
    """Start a new pipeline session from the Planning Agent."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    _print_banner("planning")
    state = run_planning_agent(session_goal, HANDOFF_PATH, client=client)
    logger.success(f"Planning complete: task_id={state.scoped_task.id}")

    # Pipeline pauses here — Code Agent is a human step
    _print_banner("code — awaiting human")
    _print_code_agent_instructions(state)
    sys.exit(0)


def resume_pipeline() -> None:
    """Resume pipeline after Code Agent (human) step. Runs Testing → Review → Docs."""
    if not HANDOFF_PATH.exists():
        print(f"\nError: {HANDOFF_PATH} not found.")
        print("Run without --resume to start a new session.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    state = read_handoff_state(HANDOFF_PATH)
    logger.info(f"Resuming pipeline: task_id={state.scoped_task.id}")

    # ── Testing loop (max MAX_RETRIES) ────────────────────────────────────────
    while True:
        _print_banner("testing")
        state = run_testing_agent(state, HANDOFF_PATH, client=client)

        if state.testing.status == "PASS":
            logger.success("Testing passed")
            break

        retries = state.retry_count.code_to_test
        if retries >= MAX_RETRIES:
            print(f"\n❌ Max retries ({MAX_RETRIES}) reached at Testing. Escalating to user.")
            print("Failures:")
            for f in state.testing.failures:
                print(f"  - {f}")
            print(f"\nHANDOFF_STATE.json preserved at: {HANDOFF_PATH}")
            sys.exit(1)

        state.retry_count.code_to_test += 1
        print(f"\n⚠️  Testing FAILED (attempt {state.retry_count.code_to_test}/{MAX_RETRIES}).")
        print("Failures:")
        for f in state.testing.failures:
            print(f"  - {f}")
        _print_code_agent_instructions(state)
        sys.exit(0)  # Pause for human fix; resume again with --resume

    # ── Review loop (max MAX_RETRIES) ─────────────────────────────────────────
    while True:
        _print_banner("review")
        state = run_review_agent(state, HANDOFF_PATH, client=client)

        if state.review.status == "APPROVED":
            logger.success("Review approved")
            break

        retries = state.retry_count.code_to_review
        if retries >= MAX_RETRIES:
            print(f"\n❌ Max retries ({MAX_RETRIES}) reached at Review. Escalating to user.")
            print("Issues:")
            for i in state.review.issues:
                print(f"  - {i}")
            print(f"\nHANDOFF_STATE.json preserved at: {HANDOFF_PATH}")
            sys.exit(1)

        state.retry_count.code_to_review += 1
        print(f"\n⚠️  Review ISSUES (attempt {state.retry_count.code_to_review}/{MAX_RETRIES}).")
        print("Issues:")
        for i in state.review.issues:
            print(f"  - {i}")
        _print_code_agent_instructions(state)
        sys.exit(0)

    # ── Documentation Agent ────────────────────────────────────────────────────
    _print_banner("docs")
    state = run_docs_agent(state, HANDOFF_PATH, client=client)

    print("\n" + "=" * 60)
    print("  SESSION COMPLETE")
    print("=" * 60)
    print(f"\nTask '{state.scoped_task.id}' completed and documented.")
    print("HANDOFF_STATE.json deleted — session is closed.\n")


# ── __main__ ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MyAPTutor multi-agent development pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Start new session:
    PYTHONPATH=backend python backend/orchestrator.py "Add /api/report endpoint"

  Resume after Code Agent completes:
    PYTHONPATH=backend python backend/orchestrator.py --resume
        """,
    )
    parser.add_argument(
        "goal",
        nargs="?",
        help="Session goal (required for new sessions, omit with --resume)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume pipeline after Code Agent step",
    )
    args = parser.parse_args()

    if args.resume and args.goal:
        parser.error("Cannot use --resume with a session goal — pick one.")
    elif args.resume:
        resume_pipeline()
    elif args.goal:
        run_pipeline(args.goal)
    else:
        parser.print_help()
        sys.exit(1)
