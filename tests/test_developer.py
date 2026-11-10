from unittest.mock import patch

from app.agents.developer import developer_agent
from app.graph.state import AppState, DeveloperOut


def _make_state(**kwargs) -> AppState:
    defaults = dict(
        task="Write a function that adds two numbers",
        plan=["Define the function", "Return a + b"],
    )
    defaults.update(kwargs)
    return AppState(**defaults)


def test_developer_generates_code_with_run_python_code():
    """Developer should use run_python_code for stdlib-only tasks."""
    state = _make_state()

    mock_response = DeveloperOut(
        code="def add(a, b):\n    return a + b\nprint(add(1, 2))",
        tool="run_python_code",
        filename=None,
    )

    with patch("app.agents.developer.structured_llm") as mock_llm, \
         patch("app.agents.developer.execute_tool", return_value="3\n") as mock_tool:
        mock_llm.invoke.return_value = mock_response
        result = developer_agent(state)

    mock_tool.assert_called_once_with(
        tool_name="run_python_code",
        response=mock_response,
        filename=None,
    )
    assert result.code == "def add(a, b):\n    return a + b\nprint(add(1, 2))"
    assert result.tool_used == "run_python_code"
    assert result.execution_result == "3\n"


def test_developer_generates_code_with_write_file():
    """Developer should use write_file for tasks that require third-party libraries."""
    state = _make_state(task="Build a chatbot using OpenAI")

    mock_response = DeveloperOut(
        code="from openai import OpenAI\nclient = OpenAI()\n...",
        tool="write_file",
        filename="chatbot.py",
    )

    with patch("app.agents.developer.structured_llm") as mock_llm, \
         patch("app.agents.developer.execute_tool", return_value="File written to workspace/chatbot.py") as mock_tool:
        mock_llm.invoke.return_value = mock_response
        result = developer_agent(state)

    mock_tool.assert_called_once_with(
        tool_name="write_file",
        response=mock_response,
        filename="chatbot.py",
    )
    assert result.tool_used == "write_file"
    assert result.execution_result == "File written to workspace/chatbot.py"


def test_developer_rejects_invalid_tool():
    """Developer should record an error and set tool_used=None if LLM returns an unknown tool."""
    state = _make_state()

    mock_response = DeveloperOut(
        code="print('hello')",
        tool="nonexistent_tool",
        filename=None,
    )

    with patch("app.agents.developer.structured_llm") as mock_llm, \
         patch("app.agents.developer.execute_tool") as mock_tool:
        mock_llm.invoke.return_value = mock_response
        result = developer_agent(state)

    mock_tool.assert_not_called()
    assert result.tool_used is None
    assert "does not exist" in result.execution_result


def test_developer_does_not_increment_round():
    """Developer must never increment state.round — only the Reviewer does that."""
    state = _make_state(round=2)

    mock_response = DeveloperOut(
        code="def add(a, b): return a + b",
        tool="run_python_code",
        filename=None,
    )

    with patch("app.agents.developer.structured_llm") as mock_llm, \
         patch("app.agents.developer.execute_tool", return_value=""):
        mock_llm.invoke.return_value = mock_response
        result = developer_agent(state)

    assert result.round == 2


def test_developer_adds_message_to_discussion():
    """Developer should always append one message to the shared discussion."""
    state = _make_state()

    mock_response = DeveloperOut(
        code="def add(a, b): return a + b",
        tool="run_python_code",
        filename=None,
    )

    with patch("app.agents.developer.structured_llm") as mock_llm, \
         patch("app.agents.developer.execute_tool", return_value=""):
        mock_llm.invoke.return_value = mock_response
        result = developer_agent(state)

    assert len(result.discussion) == 1
    assert result.discussion[0].agent == "developer"
    assert "Code length" in result.discussion[0].content


def test_developer_includes_feedback_in_revision():
    """When feedback is present, the previous code must be included in state for revision."""
    state = _make_state(
        code="def add(a, b): return a - b",  # buggy previous code
        feedback="You are subtracting instead of adding. Fix the operator.",
    )

    mock_response = DeveloperOut(
        code="def add(a, b): return a + b",
        tool="run_python_code",
        filename=None,
    )

    with patch("app.agents.developer.structured_llm") as mock_llm, \
         patch("app.agents.developer.execute_tool", return_value="3"):
        mock_llm.invoke.return_value = mock_response
        result = developer_agent(state)

    # Verify the LLM was called with a prompt that contains both the feedback and the previous code
    prompt_sent = mock_llm.invoke.call_args[0][0][0].content
    assert "subtracting instead of adding" in prompt_sent
    assert "def add(a, b): return a - b" in prompt_sent
    assert result.code == "def add(a, b): return a + b"
