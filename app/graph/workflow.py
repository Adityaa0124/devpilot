from langgraph.graph import StateGraph, END
from app.graph.state import AppState
from app.agents.planner import planner_agent
from app.agents.developer import developer_agent
from app.agents.security_reviewer import security_reviewer_agent
from app.agents.test_generator import test_generator_agent
from app.agents.reviewer import reviewer_agent
from app.agents.blind_subagents import blind_subagents_node
from app.agents.evaluator import evaluator_agent
from app.core.config import MAX_ROUNDS


def after_planner(state: AppState) -> str:
    """Conditional edge after planning."""
    if state.needs_clarification:
        state.final_status = "clarification_needed"
        return "end"
    return "developer"


def after_security_review(state: AppState) -> str:
    """
    Conditional edge after security review.
    If high-risk security flaws are detected, route back to developer to remediate (within MAX_ROUNDS).
    """
    if state.security_review and not state.security_review.is_secure:
        if state.round < state.max_rounds:
            state.round += 1
            return "developer"
        state.final_status = "failed"
        return "end"
    return "test_generator"


def after_test_generator(state: AppState) -> str:
    """
    Conditional edge after automated testing.
    If unit tests failed and retries remain, loop back to developer.
    """
    if state.tests_passed is False:
        if state.round < state.max_rounds:
            state.round += 1
            return "developer"
        # If max rounds exceeded, proceed to reviewer for final verdict
        return "reviewer"
    return "reviewer"


def after_reviewer(state: AppState) -> str:
    """
    Conditional edge after final code review.
    """
    if state.needs_clarification:
        state.final_status = "clarification_needed"
        return "end"
    if state.approved:
        state.final_status = "completed"
        return "end"
    if state.round >= state.max_rounds:
        state.final_status = "failed"
        return "end"
    return "developer"


def build_graph():
    """
    Compiles the full DevPilot Multi-Agent Architecture with:
    - Planning & Ambiguity Detection
    - Implementation & Tool Selection
    - Dedicated Security Audit
    - Automated Unit Test Generation & Sandboxed Execution
    - Final Review & Iterative Healing Loop
    """
    workflow = StateGraph(AppState)

    workflow.add_node("planner", planner_agent)
    workflow.add_node("developer", developer_agent)
    workflow.add_node("security_reviewer", security_reviewer_agent)
    workflow.add_node("test_generator", test_generator_agent)
    workflow.add_node("reviewer", reviewer_agent)

    workflow.set_entry_point("planner")

    workflow.add_conditional_edges(
        "planner",
        after_planner,
        {"developer": "developer", "end": END},
    )

    workflow.add_edge("developer", "security_reviewer")

    workflow.add_conditional_edges(
        "security_reviewer",
        after_security_review,
        {"developer": "developer", "test_generator": "test_generator", "end": END},
    )

    workflow.add_conditional_edges(
        "test_generator",
        after_test_generator,
        {"developer": "developer", "reviewer": "reviewer"},
    )

    workflow.add_conditional_edges(
        "reviewer",
        after_reviewer,
        {"developer": "developer", "end": END},
    )

    return workflow.compile()


def build_blind_evaluator_graph():
    """
    Compiles the Blind Independent Subagents + Evaluator Graph.
    Used for multi-candidate comparative generation and judging.
    """
    workflow = StateGraph(AppState)

    def after_blind_planner(state: AppState) -> str:
        if state.needs_clarification:
            return "end"
        return "blind_subagents"

    def after_evaluator(state: AppState) -> str:
        if state.needs_clarification or state.approved or state.round >= state.max_rounds:
            return "end"
        return "blind_subagents"

    workflow.add_node("planner", planner_agent)
    workflow.add_node("blind_subagents", blind_subagents_node)
    workflow.add_node("evaluator", evaluator_agent)

    workflow.set_entry_point("planner")

    workflow.add_conditional_edges(
        "planner",
        after_blind_planner,
        {"blind_subagents": "blind_subagents", "end": END},
    )

    workflow.add_edge("blind_subagents", "evaluator")

    workflow.add_conditional_edges(
        "evaluator",
        after_evaluator,
        {"blind_subagents": "blind_subagents", "end": END},
    )

    return workflow.compile()
