import time
from typing import Dict, Any, List

from langchain_core.messages import HumanMessage

from app.graph.state import AppState, Message, SubagentOut, CandidateSolution
from app.tools.registry import TOOLS
from app.tools.tool_router import execute_tool
from app.core.logging import get_logger
from app.core.llm import get_chat_llm

logger = get_logger("blind_subagents")

llm = get_chat_llm(temperature=0.7)
structured_subagent_llm = llm.with_structured_output(SubagentOut)

# Configuration for diverse, blind independent subagents
SUBAGENTS_CONFIG = [
    {
        "id": "subagent_pragmatic",
        "name": "Pragmatic Pythonist",
        "label": "Candidate A",
        "role_description": "Clean, idiomatic, standard-library-first approach. Focuses on clarity, simplicity, maintainability, and direct solution without over-engineering.",
        "guidelines": """
- Prioritize standard library modules and idiomatic Python.
- Write clean, straightforward functions with descriptive naming and clear docstrings.
- Ensure the solution directly addresses the user request with minimal moving parts.
- Include executable verification calls with print statements to verify output immediately.
""",
    },
    {
        "id": "subagent_defensive",
        "name": "Defensive Systems Engineer",
        "label": "Candidate B",
        "role_description": "Defensive programming and resilience. Focuses on comprehensive input validation, boundary and edge-case handling, explicit exception recovery, and graceful degradation.",
        "guidelines": """
- Treat all inputs as untrusted: validate types, ranges, empty collections, and nulls.
- Use explicit try-except blocks catching specific exceptions, never bare except.
- Handle edge cases: empty strings/lists, negative numbers, extreme values, missing keys.
- Include smoke tests/assertions verifying both valid inputs and error recovery.
""",
    },
    {
        "id": "subagent_performance",
        "name": "Algorithmic Specialist",
        "label": "Candidate C",
        "role_description": "Performance, computational complexity, and resource optimization. Focuses on optimal data structures, low memory footprint, and avoiding redundant operations.",
        "guidelines": """
- Optimize for optimal asymptotic time and space complexity (O(1), O(log N), O(N)).
- Utilize optimal data structures (e.g. dicts/sets for O(1) lookups, collections.deque, collections.defaultdict, itertools, bisect).
- Avoid unnecessary memory allocations, repeated linear scans, or redundant conversions.
- Include execution profiling or performance verification demonstrating efficiency.
""",
    },
]


def execute_blind_subagent(
    task: str,
    plan: List[str] | None,
    config: Dict[str, Any],
) -> CandidateSolution:
    """
    Executes a single subagent in complete isolation ('blind' to other subagents).
    The subagent does NOT receive the discussion, thoughts, or code of any other subagent.
    """
    subagent_id = config["id"]
    subagent_name = config["name"]
    candidate_label = config["label"]
    role_description = config["role_description"]
    guidelines = config["guidelines"]

    tools_description = "\n".join(f"{name}: {desc}" for name, desc in TOOLS.items())
    plan_section = f"\nTask Implementation Steps to follow:\n" + "\n".join(f"- {s}" for s in plan) if plan else ""

    prompt = f"""
You are {subagent_name}, an expert developer with the following perspective:
{role_description}

Specific Subagent Guidelines:
{guidelines}

Task:
{task}
{plan_section}

Available execution tools:
{tools_description}

Rules:
- You are developing your candidate solution independently in isolation.
- Only select tools from the available tools list: "run_python_code", "write_file", or "run_shell_command".
- Use run_python_code if the solution relies on Python's standard library and can run immediately.
- Use write_file if the solution requires third-party dependencies or creates a multi-file project/server/CLI.
- Use run_shell_command if the task requires system or shell execution.
- Modern API syntax only: for openai>=1.0.0, use `from openai import OpenAI` and `client.chat.completions.create(...)`.
- Include verification/print output at the end so the tool execution yields tangible stdout evidence.

Return:
strategy: A 1-2 sentence explanation of your approach.
tool: tool name
code: Python code or shell command
filename: only if using write_file
"""

    start_time = time.time()
    response = structured_subagent_llm.invoke([HumanMessage(content=prompt)])
    latency_ms = round((time.time() - start_time) * 1000)

    tool = getattr(response, "tool", "run_python_code") or "run_python_code"
    code = response.code or ""
    filename = getattr(response, "filename", None)
    strategy = getattr(response, "strategy", f"Solution from {subagent_name}")

    # Tool validation and execution
    if tool not in TOOLS:
        execution_result = f"Error: Tool '{tool}' is not available. Available: {list(TOOLS.keys())}"
        execution_success = False
    else:
        try:
            execution_result = execute_tool(
                tool_name=tool,
                response=response,
                filename=filename,
            )
            has_error = (
                "Traceback (most recent call last)" in (execution_result or "")
                or "Error:" in (execution_result or "")
                or "Exception:" in (execution_result or "")
            )
            execution_success = not has_error
        except Exception as exc:
            execution_result = f"Tool execution failed: {str(exc)}"
            execution_success = False

    logger.info({
        "subagent_id": subagent_id,
        "candidate_label": candidate_label,
        "tool": tool,
        "execution_success": execution_success,
        "latency_ms": latency_ms,
    })

    return CandidateSolution(
        subagent_id=subagent_id,
        subagent_name=subagent_name,
        candidate_label=candidate_label,
        strategy=strategy,
        code=code,
        tool_used=tool,
        filename=filename,
        execution_result=execution_result,
        execution_success=execution_success,
    )


def blind_subagents_node(state: AppState) -> AppState:
    """
    Executes all configured blind independent subagents in isolation.
    Each subagent generates and runs its candidate solution without knowledge of other subagents.
    Populates `state.candidates` with the candidate solutions.
    """
    candidates: List[CandidateSolution] = []

    for config in SUBAGENTS_CONFIG:
        candidate = execute_blind_subagent(
            task=state.task,
            plan=state.plan,
            config=config,
        )
        candidates.append(candidate)
        state.discussion.append(
            Message(
                agent=config["id"],
                content=f"[{config['label']} - {config['name']}]\nStrategy: {candidate.strategy}\nTool: {candidate.tool_used}\nExecution output:\n{candidate.execution_result or 'None'}",
            )
        )

    state.candidates = candidates
    state.current_stage = "subagents_completed"

    if candidates:
        first = candidates[0]
        state.code = first.code
        state.tool_used = first.tool_used
        state.filename = first.filename
        state.execution_result = first.execution_result

    return state


def subagent_pragmatic_node(state: AppState) -> AppState:
    candidate = execute_blind_subagent(state.task, state.plan, SUBAGENTS_CONFIG[0])
    state.candidates.append(candidate)
    state.discussion.append(
        Message(agent="subagent_pragmatic", content=f"[Candidate A] {candidate.strategy}\nOutput: {candidate.execution_result}")
    )
    return state


def subagent_defensive_node(state: AppState) -> AppState:
    candidate = execute_blind_subagent(state.task, state.plan, SUBAGENTS_CONFIG[1])
    state.candidates.append(candidate)
    state.discussion.append(
        Message(agent="subagent_defensive", content=f"[Candidate B] {candidate.strategy}\nOutput: {candidate.execution_result}")
    )
    return state


def subagent_performance_node(state: AppState) -> AppState:
    candidate = execute_blind_subagent(state.task, state.plan, SUBAGENTS_CONFIG[2])
    state.candidates.append(candidate)
    state.discussion.append(
        Message(agent="subagent_performance", content=f"[Candidate C] {candidate.strategy}\nOutput: {candidate.execution_result}")
    )
    return state
