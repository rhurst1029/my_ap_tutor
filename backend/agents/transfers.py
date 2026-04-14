# Purpose: Structured transfer tool definitions for agent handoffs.
# These are passed as `tools=` to client.messages.create().
# The orchestrator inspects tool_use blocks in the response and routes accordingly.
#
# Anthropic tool use docs: https://docs.anthropic.com/en/docs/tool-use
# Claude tool schema reference: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
#
# Sample input (extract_tool_call):
#   response = client.messages.create(tools=PLANNING_TOOLS, ...)
#   call = extract_tool_call(response)
#   # call == {"name": "transfer_to_code_agent", "input": {"task_id": "x", ...}}
#
# Expected output: dict with "name" and "input" keys, or None if no tool call.
import sys
from typing import Any, Dict, Optional
from loguru import logger


# ── Tool schemas (passed to Claude API as tools=[...]) ────────────────────────

TRANSFER_TO_CODE_AGENT: Dict[str, Any] = {
    "name": "transfer_to_code_agent",
    "description": (
        "Call this when planning is complete and the scoped task is written to HANDOFF_STATE.json. "
        "Pass the task id and a summary of what the code agent should implement. "
        "Do NOT call this until the scoped_task fields are fully filled out."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "The id field from scoped_task in HANDOFF_STATE.json",
            },
            "implementation_notes": {
                "type": "string",
                "description": "One paragraph of context for the code agent — what to build and why",
            },
        },
        "required": ["task_id", "implementation_notes"],
    },
}

TRANSFER_TO_TESTING_AGENT: Dict[str, Any] = {
    "name": "transfer_to_testing_agent",
    "description": (
        "Call this when implementation is complete. "
        "Pass the list of files that were modified. "
        "The testing agent will validate: server health, endpoint smoke test, schema sync, "
        "__main__ block, and frontend type-check."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "artifacts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths that were created or modified",
            },
            "notes": {
                "type": "string",
                "description": "Optional context for the testing agent (known edge cases, etc.)",
            },
        },
        "required": ["artifacts"],
    },
}

TRANSFER_TO_REVIEW_AGENT: Dict[str, Any] = {
    "name": "transfer_to_review_agent",
    "description": (
        "Call this when all tests pass. "
        "The review agent runs a fixed security, schema, phase-boundary, and regression checklist. "
        "It does NOT fix issues — it reports them."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "artifacts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of file paths to review",
            },
        },
        "required": ["artifacts"],
    },
}

TRANSFER_TO_DOCS_AGENT: Dict[str, Any] = {
    "name": "transfer_to_docs_agent",
    "description": (
        "Call this when review is APPROVED. "
        "The docs agent updates BuildGuide.md, PROGRESS.md, DECISIONS.md, TASKS.md, "
        "and reviews PARKING_LOT.md."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "One sentence: what was built and where it lives",
            },
            "new_endpoints": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of new API endpoints added (e.g. 'POST /api/report')",
            },
            "new_components": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of new frontend components added",
            },
            "schema_changes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of schema changes (model additions, field changes)",
            },
        },
        "required": ["summary"],
    },
}

TRANSFER_TO_USER: Dict[str, Any] = {
    "name": "transfer_to_user",
    "description": (
        "Call this when the max retry limit (3) has been reached without passing tests or review, "
        "or when a blocker requires human judgement. Provide a clear summary of what failed."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": "Why we are escalating to the user",
            },
            "failures": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of failures that could not be resolved automatically",
            },
        },
        "required": ["reason", "failures"],
    },
}


# ── Tool sets per agent ───────────────────────────────────────────────────────

PLANNING_TOOLS = [TRANSFER_TO_CODE_AGENT]
TESTING_TOOLS = [TRANSFER_TO_REVIEW_AGENT, TRANSFER_TO_CODE_AGENT, TRANSFER_TO_USER]
REVIEW_TOOLS = [TRANSFER_TO_DOCS_AGENT, TRANSFER_TO_CODE_AGENT, TRANSFER_TO_USER]
DOCS_TOOLS = [TRANSFER_TO_USER]   # Only escalates on error


def extract_tool_call(response: Any) -> Optional[Dict[str, Any]]:
    """
    Extract the first tool_use block from an Anthropic API response.
    Returns {"name": str, "input": dict} or None if no tool call in response.
    """
    for block in response.content:
        if block.type == "tool_use":
            logger.debug(f"Tool call extracted: {block.name}")
            return {"name": block.name, "input": block.input}
    logger.debug("No tool_use block found in response")
    return None


# ── __main__ validation ───────────────────────────────────────────────────────
if __name__ == "__main__":
    all_validation_failures = []
    total_tests = 0

    # Test 1: All tool schemas have required fields
    total_tests += 1
    for tool in [
        TRANSFER_TO_CODE_AGENT,
        TRANSFER_TO_TESTING_AGENT,
        TRANSFER_TO_REVIEW_AGENT,
        TRANSFER_TO_DOCS_AGENT,
        TRANSFER_TO_USER,
    ]:
        for field in ["name", "description", "input_schema"]:
            if field not in tool:
                all_validation_failures.append(
                    f"Tool {tool.get('name', '?')} missing field: {field}"
                )

    # Test 2: extract_tool_call returns None on text-only response
    total_tests += 1
    class FakeBlock:
        type = "text"
        text = "hello"
    class FakeResponse:
        content = [FakeBlock()]
    result = extract_tool_call(FakeResponse())
    if result is not None:
        all_validation_failures.append(f"extract_tool_call should return None for text-only, got {result}")

    # Test 3: extract_tool_call returns dict for tool_use block
    total_tests += 1
    class FakeToolBlock:
        type = "tool_use"
        name = "transfer_to_code_agent"
        input = {"task_id": "x", "implementation_notes": "y"}
    class FakeToolResponse:
        content = [FakeToolBlock()]
    result = extract_tool_call(FakeToolResponse())
    if result is None or result["name"] != "transfer_to_code_agent":
        all_validation_failures.append(f"extract_tool_call failed: {result}")

    # Test 4: PLANNING_TOOLS contains only TRANSFER_TO_CODE_AGENT
    total_tests += 1
    if len(PLANNING_TOOLS) != 1 or PLANNING_TOOLS[0]["name"] != "transfer_to_code_agent":
        all_validation_failures.append(f"PLANNING_TOOLS wrong: {[t['name'] for t in PLANNING_TOOLS]}")

    if all_validation_failures:
        print(f"❌ VALIDATION FAILED — {len(all_validation_failures)} of {total_tests} tests failed:")
        for f in all_validation_failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED — all {total_tests} tests produced expected results")
        sys.exit(0)
