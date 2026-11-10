import time

from langchain_core.messages import HumanMessage

from app.graph.state import AppState, Message, PlannerOut
from app.core.logging import get_logger
from app.core.config import MAX_CONTEXT_MESSAGES
from app.core.llm import get_chat_llm

logger = get_logger("planner")

llm = get_chat_llm(temperature=0.7)
structured_llm = llm.with_structured_output(PlannerOut)


def planner_agent(state: AppState) -> AppState:
    task = state.task
    discussion = state.discussion[-MAX_CONTEXT_MESSAGES:]
    discussion_text = "\n".join(f"{m.agent}: {m.content}" for m in discussion)

    prompt = f"""
    You are a senior software architect.

    Task:
    {task}

    Discussion so far:
    {discussion_text}

    Before planning, evaluate if the task has enough information to be implemented:
    - If the task is too vague or missing critical details (e.g., no target URL, no input format, no expected output),
      set needs_clarification=true and write a clarification_question asking the user for what's missing.
    - Otherwise, return the plan as a numbered list with a maximum of 10 steps to implement this task.
    """

    start = time.time()
    response = structured_llm.invoke([HumanMessage(content=prompt)])
    latency_ms = round((time.time() - start) * 1000)

    if response.needs_clarification:
        state.needs_clarification = True
        state.clarification_question = response.clarification_question
        state.current_stage = "clarification_needed"
        state.discussion.append(Message(agent="planner", content=f"Needs clarification: {response.clarification_question}"))
        logger.info({
            "agent": "planner",
            "decision": "needs_clarification",
            "clarification_question": response.clarification_question,
            "latency_ms": latency_ms,
        })
        return state

    plan_txt = "\n".join(response.steps)
    state.discussion.append(Message(agent="planner", content=plan_txt))
    state.plan = response.steps
    state.current_stage = "planned"

    logger.info({
        "agent": "planner",
        "decision": "plan_ready",
        "steps_count": len(response.steps),
        "latency_ms": latency_ms,
    })

    return state
