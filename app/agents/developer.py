import time

from langchain_core.messages import HumanMessage

from app.graph.state import AppState, Message, DeveloperOut
from app.tools.registry import TOOLS
from app.tools.tool_router import execute_tool
from app.core.logging import get_logger
from app.core.config import MAX_CONTEXT_MESSAGES
from app.core.llm import get_chat_llm

logger = get_logger("developer")

llm = get_chat_llm(temperature=0.7)
structured_llm = llm.with_structured_output(DeveloperOut)


def developer_agent(state: AppState) -> AppState:
    task = state.task
    plan = state.plan or []
    discussion = state.discussion[-MAX_CONTEXT_MESSAGES:]
    feedback = state.feedback  # None on first round; set by Reviewer/Security on subsequent rounds

    discussion_text = "\n".join(f"{m.agent}: {m.content}" for m in discussion)
    tools_description = "\n".join(f"{name}: {desc}" for name, desc in TOOLS.items())

    # Build feedback sections for iterations
    feedback_parts = []
    if feedback:
        feedback_parts.append(f"Reviewer Feedback:\n{feedback}")
    if state.security_review and not state.security_review.is_secure:
        findings_txt = "\n".join(
            f"- [{f.severity}] {f.explanation} (Remediation: {f.suggested_remediation})"
            for f in state.security_review.findings
        )
        feedback_parts.append(f"Security Review Findings (MUST FIX):\n{findings_txt}")
    if state.test_results and state.tests_passed is False:
        feedback_parts.append(f"Test Execution Failures (MUST FIX):\n{state.test_results}")

    feedback_section = "\n\n".join(feedback_parts)
    if feedback_section:
        feedback_section = f"""
    FEEDBACK & DEFECTS TO FIX:
    {feedback_section}

    IMPORTANT: Do NOT rewrite everything from scratch. Keep what works and fix ONLY the reported defects.
    """

    previous_code_section = f"""
    Your previous code submission:
    {state.code}
    """ if state.code and feedback_section else ""

    prompt = f"""
    You are a senior Python software engineer.

    Task:
    {task}

    Plan:
    {plan}

    Discussion:
    {discussion_text}
    {previous_code_section}
    {feedback_section}
    Available tools:
    {tools_description}

    Rules:
    - You MUST only use tools from the list above: "run_python_code", "write_file", or "run_shell_command".
    - Use run_python_code ONLY if the code uses standard library modules and can run immediately.
    - Use write_file if the code creates a multi-file project, CLI, server, or uses third-party libraries.
    - Use run_shell_command for system operations.
    - When using write_file, choose a safe descriptive filename (e.g. solution.py, app.py). Never use path traversal (no '../').
    - Do NOT hardcode credentials, secrets, or fake API keys. Use os.getenv('KEY_NAME').
    - Always use safe modern APIs (e.g. OpenAI v1.x: `from openai import OpenAI`).
    - Include executable sample calls/tests with print statements so tool execution outputs verifiable results.

    Return:
    tool: tool name
    code: Python code or shell command
    filename: only if using write_file
    """

    start = time.time()
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    latency_ms = round((time.time() - start) * 1000)

    tool = getattr(response, "tool", None) or "run_python_code"
    code = response.code or ""
    filename = getattr(response, "filename", None)

    if tool not in TOOLS:
        state.execution_result = f"Error: tool '{tool}' does not exist. Available tools: {list(TOOLS.keys())}"
        state.tool_used = None
        logger.info({
            "agent": "developer",
            "decision": "invalid_tool",
            "tool_requested": tool,
            "latency_ms": latency_ms,
        })
        state.current_stage = "developed_with_tool_error"
        return state

    execution_result = execute_tool(
        tool_name=tool,
        response=response,
        filename=filename,
    )

    state.code = code
    state.tool_used = tool
    state.filename = filename
    state.execution_result = execution_result
    state.current_stage = "developed"

    if filename and filename not in state.files_modified:
        state.files_modified.append(filename)

    state.discussion.append(
        Message(
            agent="developer",
            content=f"Tool used: {tool}\nCode length: {len(code)} characters\nOutput:\n{execution_result}",
        )
    )

    logger.info({
        "agent": "developer",
        "tool_used": tool,
        "filename": filename,
        "code_length": len(code),
        "latency_ms": latency_ms,
    })

    return state
