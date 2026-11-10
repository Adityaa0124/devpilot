from unittest.mock import patch

from app.agents.reviewer import reviewer_agent
from app.graph.state import AppState, ReviewerOut


def _make_state(**kwargs) -> AppState:
    defaults = dict(
        task="Write a function that adds two numbers",
        code="def add(a, b):\n    return a + b\nprint(add(1, 2))",
        execution_result="3",
        tool_used="run_python_code",
        round=0,
    )
    defaults.update(kwargs)
    return AppState(**defaults)


def test_reviewer_approves_correct_code():
    """Reviewer should set approved=True and increment round."""
    state = _make_state()

    mock_response = ReviewerOut(
        approved=True,
        feedback="Code is correct and produces the expected output.",
        needs_clarification=False,
        clarification_question=None,
    )

    with patch("app.agents.reviewer.structured_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = reviewer_agent(state)

    assert result.approved is True
    assert result.feedback == "Code is correct and produces the expected output."
    assert result.needs_clarification is False
    # Reviewer is the only agent that increments round
    assert result.round == 1
    assert len(result.discussion) == 1
    assert result.discussion[0].agent == "reviewer"


def test_reviewer_rejects_with_feedback():
    """Reviewer should set approved=False and provide actionable feedback."""
    state = _make_state(
        code="def add(a, b):\n    return a - b",
        execution_result="-1",
    )

    mock_response = ReviewerOut(
        approved=False,
        feedback="The function subtracts instead of adding. Change '-' to '+'.",
        needs_clarification=False,
        clarification_question=None,
    )

    with patch("app.agents.reviewer.structured_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = reviewer_agent(state)

    assert result.approved is False
    assert "subtracts" in result.feedback
    assert result.round == 1


def test_reviewer_static_review_for_write_file():
    """Reviewer should approve write_file tasks based on code quality, not runtime output."""
    state = _make_state(
        code="import openai\n# chatbot code...",
        execution_result="File written to workspace/chatbot.py",
        tool_used="write_file",
        filename="chatbot.py",
    )

    mock_response = ReviewerOut(
        approved=True,
        feedback="Code is logically correct and implements all chatbot requirements.",
        needs_clarification=False,
        clarification_question=None,
    )

    with patch("app.agents.reviewer.structured_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = reviewer_agent(state)

    assert result.approved is True
    assert result.round == 1


def test_reviewer_requests_clarification():
    """Reviewer should set needs_clarification=True when task is underspecified."""
    state = _make_state()

    mock_response = ReviewerOut(
        approved=False,
        feedback="Cannot evaluate — the task is missing required context.",
        needs_clarification=True,
        clarification_question="What should the function do when the inputs are not numbers?",
    )

    with patch("app.agents.reviewer.structured_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = reviewer_agent(state)

    assert result.needs_clarification is True
    assert result.clarification_question == "What should the function do when the inputs are not numbers?"
    # round still increments — the cycle did complete
    assert result.round == 1


def test_reviewer_increments_round_each_cycle():
    """round counter increases once per reviewer call, regardless of the decision."""
    state = _make_state(round=2)

    mock_response = ReviewerOut(
        approved=False,
        feedback="Still broken.",
        needs_clarification=False,
        clarification_question=None,
    )

    with patch("app.agents.reviewer.structured_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_response
        result = reviewer_agent(state)

    assert result.round == 3
