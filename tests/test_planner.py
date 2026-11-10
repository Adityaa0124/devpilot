from unittest.mock import patch

from app.agents.planner import planner_agent
from app.graph.state import AppState, PlannerOut


def test_planner_generates_plan():
    """Planner should populate state.plan when the task is clear."""
    state = AppState(task="Write a function that adds two numbers")

    mock_response = PlannerOut(
        steps=["Define the add function", "Return a + b", "Print the result"],
        needs_clarification=False,
        clarification_question=None,
    )

    with patch("app.agents.planner.structured_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = planner_agent(state)

    assert result.plan == ["Define the add function", "Return a + b", "Print the result"]
    assert result.needs_clarification is False
    assert result.clarification_question is None
    # Planner should have added one message to the discussion
    assert len(result.discussion) == 1
    assert result.discussion[0].agent == "planner"
    # round must NOT be incremented by the planner
    assert result.round == 0


def test_planner_requests_clarification_on_vague_task():
    """Planner should set needs_clarification=True and NOT generate a plan."""
    state = AppState(task="Build something")

    mock_response = PlannerOut(
        steps=[],
        needs_clarification=True,
        clarification_question="What exactly should be built? Please describe the expected inputs and outputs.",
    )

    with patch("app.agents.planner.structured_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = planner_agent(state)

    assert result.needs_clarification is True
    assert result.clarification_question == (
        "What exactly should be built? Please describe the expected inputs and outputs."
    )
    # No plan must be set when clarification is needed
    assert result.plan is None
    assert result.round == 0
