import time

from langchain_core.messages import HumanMessage

from app.graph.state import AppState, Message, ReviewerOut
from app.core.logging import get_logger
from app.core.config import MAX_CONTEXT_MESSAGES
from app.core.llm import get_chat_llm

logger = get_logger("reviewer")

llm = get_chat_llm(temperature=0.3)
structured_llm = llm.with_structured_output(ReviewerOut)


def reviewer_agent(state: AppState) -> AppState:
    task = state.task
    code = state.code or ""
    execution_result = state.execution_result or "No execution result available."
    tool_used = state.tool_used
    filename = state.filename
    discussion = state.discussion[-MAX_CONTEXT_MESSAGES:]

    discussion_text = "\n".join(f"{m.agent}: {m.content}" for m in discussion)

    # Different review criteria depending on how code was delivered.
    if tool_used == "write_file":
        evaluation_instructions = f"""
    The developer saved the code to a file ({filename}) because it requires third-party libraries
    or user interaction and cannot be executed in a sandbox.
    The execution result "{execution_result}" is just confirmation that the file was written — it is NOT an error.

    Your job:
    - Review the code STATICALLY (as a code review, not based on runtime output).
    - Check if the code is logically correct and addresses all requirements of the task.
    - If during review it becomes clear that the task is missing critical information,
      set needs_clarification=true and write a clarification_question.
    - APPROVE (approved=true) if the code correctly implements the core functionality of the task, even if minor improvements could be made. Style issues, optional enhancements, and non-critical suggestions should be mentioned in feedback but must NOT block approval.
    - REJECT (approved=false) ONLY for these blocking reasons:
        1. Deprecated or removed APIs that will crash at runtime (e.g. openai.ChatCompletion.create — removed in openai>=1.0.0).
        2. A required core feature is completely missing and makes the task fail (e.g. a chatbot task with a specified persona but no system message at all).
        3. A clear logical bug that breaks the main functionality.
    - Do NOT reject for: lacking runtime output, requiring pip install, requiring env vars or API keys, minor code style issues, or non-critical enhancements.
    - Correct openai syntax (openai>=1.0.0):
          from openai import OpenAI
          client = OpenAI()
          response = client.chat.completions.create(...)
        """
    else:
        evaluation_instructions = f"""
    Execution result (stdout/stderr from running the code):
    {execution_result}

    Your job:
    - Analyze whether the code correctly solves the task.
    - Check the execution result for errors, exceptions, or unexpected output.
    - If during review it becomes clear that the task is missing critical information,
      set needs_clarification=true and write a clarification_question.
    - If the code runs correctly and solves the task, set approved=true and explain why it's good.
    - If there are errors or the task is not solved, set approved=false with specific instructions to fix.
        """

    prompt = f"""
    You are a senior code reviewer.

    Task:
    {task}

    Code written by the developer:
    {code}

    {evaluation_instructions}

    Discussion so far:
    {discussion_text}

    Be objective. Focus on correctness and whether the task is actually solved.
    """

    start = time.time()
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    latency_ms = round((time.time() - start) * 1000)

    state.approved = response.approved
    state.feedback = response.feedback
    state.needs_clarification = response.needs_clarification
    state.clarification_question = response.clarification_question
    state.current_stage = "reviewed"
    state.final_status = "approved" if response.approved else ("clarification_needed" if response.needs_clarification else "rejected")

    state.discussion.append(Message(agent="reviewer", content=response.feedback))
    state.round += 1

    logger.info({
        "agent": "reviewer",
        "round": state.round,
        "approved": response.approved,
        "needs_clarification": response.needs_clarification,
        "tool_used": tool_used,
        "latency_ms": latency_ms,
    })

    return state
