# Purpose: Documentation Agent — updates BuildGuide.md, PROGRESS.md, DECISIONS.md,
# PARKING_LOT.md, and TASKS.md after every approved session.
# Write-only on documentation files; never touches source files or data/.
#
# Design reference: MultiAgentDesign.md § "5. Documentation Agent"
# Anthropic messages API: https://docs.anthropic.com/en/api/messages
#
# Sample usage:
#   state = run_docs_agent(state, Path("HANDOFF_STATE.json"))
#   # Documentation files updated; HANDOFF_STATE.json deleted
#
# Expected output: BlackBoard docs updated; HANDOFF_STATE.json deleted at session end.
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import anthropic
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ANTHROPIC_API_KEY
from agents.handoff import HandoffState, delete_handoff_state, write_handoff_state
from agents.transfers import DOCS_TOOLS, extract_tool_call
from agents.config import AGENT_CONFIGS

BASE_DIR = Path(__file__).parent.parent.parent  # MyAPTutor/
PROJECT_DIR = BASE_DIR  # PROGRESS.md, TASKS.md, etc. live in MyAPTutor/

# Documentation files the Docs Agent is allowed to write
ALLOWED_DOCS = frozenset({
    "PROGRESS.md", "TASKS.md", "BuildGuide.md",
    "DECISIONS.md", "PARKING_LOT.md",
})


def _read_doc(filename: str) -> str:
    path = PROJECT_DIR / filename
    if path.exists():
        return path.read_text()
    logger.debug(f"{filename} does not exist yet — will be created if needed")
    return f"(file {filename} does not exist yet)"


def _write_doc(filename: str, content: str) -> None:
    """Write a documentation file. Only allowed files accepted."""
    if filename not in ALLOWED_DOCS:
        logger.warning(f"Docs Agent: refused to write to non-doc file: {filename}")
        return
    path = PROJECT_DIR / filename
    path.write_text(content)
    logger.info(f"Docs Agent: updated {filename}")


def _append_to_progress(entry: str) -> None:
    """Append a session entry to PROGRESS.md (never overwrites existing content)."""
    path = PROJECT_DIR / "PROGRESS.md"
    existing = path.read_text() if path.exists() else "# PROGRESS.md\n\n"
    path.write_text(existing.rstrip() + "\n\n" + entry.strip() + "\n")
    logger.info("Docs Agent: appended to PROGRESS.md")


def _mark_task_complete(task_id: str) -> None:
    """Mark a task [x] in TASKS.md by finding lines containing the task_id."""
    path = PROJECT_DIR / "TASKS.md"
    if not path.exists():
        logger.debug("TASKS.md not found — skipping task completion mark")
        return
    content = path.read_text()
    updated = re.sub(
        rf"(- \[ \].*{re.escape(task_id)}.*)",
        lambda m: m.group(0).replace("- [ ]", "- [x]", 1),
        content,
    )
    if updated != content:
        path.write_text(updated)
        logger.info(f"Docs Agent: marked task complete: {task_id}")
    else:
        logger.debug(f"Docs Agent: no matching task found for: {task_id}")


def run_docs_agent(
    state: HandoffState,
    handoff_path: Path,
    client: Optional[anthropic.Anthropic] = None,
) -> HandoffState:
    """
    Run the Documentation Agent.

    Reads blackboard files, asks Claude to produce updated documentation,
    writes those updates to disk (append-only for PROGRESS.md), marks the
    task complete in TASKS.md, then deletes HANDOFF_STATE.json.

    Args:
        state: Current HandoffState (review.status must be APPROVED).
        handoff_path: Path to HANDOFF_STATE.json.
        client: Optional pre-constructed Anthropic client.

    Returns:
        HandoffState with agent="docs".

    Raises:
        ValueError: If called when review is not APPROVED.
    """
    if state.review is None or state.review.status != "APPROVED":
        raise ValueError(
            "Docs Agent should only run after Review Agent approves. "
            f"Current review status: {state.review}"
        )
    if client is None:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    today = date.today().isoformat()
    blackboard_context = "\n\n".join(
        f"=== {name} ===\n{_read_doc(name)}"
        for name in ["BuildGuide.md", "TASKS.md", "PARKING_LOT.md", "DECISIONS.md"]
    )

    cfg = AGENT_CONFIGS["docs"]
    user_message = (
        f"Session complete. Task '{state.scoped_task.id}' was approved by the Review Agent.\n"
        f"Today's date: {today}\n"
        f"Session goal: {state.session_goal}\n"
        f"What was built: {state.scoped_task.description}\n"
        f"Files changed: {state.scoped_task.files}\n\n"
        f"Current document state:\n{blackboard_context}\n\n"
        "Produce updated content for each documentation file that needs updating:\n"
        "1. PROGRESS.md — append only (don't replace). Output just the NEW entry to append.\n"
        "2. TASKS.md — mark the completed task [x] if present\n"
        "3. BuildGuide.md — add entries for new endpoints, components, or schemas if any\n"
        "4. DECISIONS.md — log any architectural choices made this session\n"
        "5. PARKING_LOT.md — review and promote items with 2+ appearances to TASKS.md\n\n"
        "Output each update inside a fenced code block with the filename as the info string:\n"
        "```PROGRESS.md\n[content]\n```\n\n"
        "Only output files that need updating. Then call transfer_to_user() with a summary."
    )

    logger.info("Docs Agent: calling Claude API")
    response = client.messages.create(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        system=cfg["system"],
        tools=DOCS_TOOLS,
        messages=[{"role": "user", "content": user_message}],
    )
    logger.info(f"Docs Agent: stop_reason={response.stop_reason}")

    # Parse and write file content blocks from Claude's text response
    for block in response.content:
        if not hasattr(block, "text"):
            continue
        text = block.text
        print(text)
        # Extract ```FILENAME ... ``` code blocks and write them
        pattern = r"```([\w./\-]+)\n([\s\S]*?)```"
        for match in re.finditer(pattern, text):
            filename = match.group(1).strip()
            content = match.group(2)
            if filename == "PROGRESS.md":
                _append_to_progress(content)
            elif filename in ALLOWED_DOCS:
                _write_doc(filename, content)
            else:
                logger.warning(f"Docs Agent: skipped non-doc file in response: {filename}")

    # Always mark the task complete in TASKS.md
    _mark_task_complete(state.scoped_task.id)

    state.agent = "docs"
    write_handoff_state(state, handoff_path)

    # Delete HANDOFF_STATE.json — session is complete
    delete_handoff_state(handoff_path)
    logger.success("Docs Agent: session complete, HANDOFF_STATE.json deleted")
    return state


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile
    import shutil

    all_validation_failures = []
    total_tests = 0

    # Temporarily redirect PROJECT_DIR to a temp dir for safe testing
    original_project_dir = PROJECT_DIR

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Monkey-patch PROJECT_DIR in the current module's global namespace
        # (functions are defined here in __main__, so patching __main__ globals is correct)
        import agents.docs as docs_module
        import sys as _sys
        _main_module = _sys.modules[__name__]
        _main_module.PROJECT_DIR = tmp_path
        docs_module.PROJECT_DIR = tmp_path

        # Test 1: _append_to_progress appends (does not overwrite)
        total_tests += 1
        progress_path = tmp_path / "PROGRESS.md"
        progress_path.write_text("# PROGRESS.md\n\nfirst entry\n")
        _append_to_progress("new entry content")
        content = progress_path.read_text()
        if "first entry" not in content or "new entry content" not in content:
            all_validation_failures.append(
                f"_append_to_progress overwrote existing content: {content!r}"
            )

        # Test 2: _mark_task_complete updates checkbox syntax
        total_tests += 1
        tasks_path = tmp_path / "TASKS.md"
        tasks_path.write_text("- [ ] add-report-endpoint: Create POST\n- [ ] other-task\n")
        _mark_task_complete("add-report-endpoint")
        updated = tasks_path.read_text()
        if "- [x] add-report-endpoint" not in updated:
            all_validation_failures.append(f"_mark_task_complete failed: {updated!r}")
        if "- [ ] other-task" not in updated:
            all_validation_failures.append(f"_mark_task_complete modified wrong line: {updated!r}")

        # Test 3: _write_doc refuses to write to non-doc files
        total_tests += 1
        _write_doc("backend/main.py", "SHOULD NOT WRITE")
        if (tmp_path / "backend" / "main.py").exists():
            all_validation_failures.append("_write_doc should refuse to write backend/main.py")

        # Test 4: run_docs_agent raises ValueError when review not APPROVED
        total_tests += 1
        from agents.handoff import HandoffState, ScopedTask, RetryCount
        bad_state = HandoffState(
            agent="review",
            session_goal="test",
            scoped_task=ScopedTask(
                id="x", label="MUST", description="d",
                done_when="dw", estimated_minutes=10, files=[],
            ),
            retry_count=RetryCount(),
        )
        try:
            run_docs_agent(bad_state, tmp_path / "HANDOFF_STATE.json")
            all_validation_failures.append("Should have raised ValueError")
        except ValueError:
            pass  # Expected

        _main_module.PROJECT_DIR = original_project_dir
        docs_module.PROJECT_DIR = original_project_dir

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
