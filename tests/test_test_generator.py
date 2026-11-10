from unittest.mock import patch
from app.agents.test_generator import test_generator_agent as run_test_generator
from app.graph.state import AppState, TestGenerationOut


def test_test_generator_runs_and_passes():
    """Test generator should create and run tests successfully for valid code."""
    state = AppState(
        task="Write a function to calculate square of a number",
        code="def square(n):\n    return n * n",
    )

    mock_response = TestGenerationOut(
        test_code="from solution import square\n\ndef test_square():\n    assert square(3) == 9\n    assert square(-2) == 4\n",
        test_file="test_solution.py",
        test_description="Verifies square of positive and negative numbers",
    )

    with patch("app.agents.test_generator.structured_test_llm") as mock_llm, \
         patch("app.agents.test_generator._execute_pytest_suite", return_value=(True, "2 passed in 0.05s")):
        mock_llm.invoke.return_value = mock_response
        result = run_test_generator(state)

    assert result.tests_passed is True
    assert "2 passed" in result.test_results
    assert result.current_stage == "tested"
    assert "✅ Automated Tests" in result.discussion[-1].content


def test_test_generator_captures_failure():
    """Test generator should record failure output when tests fail."""
    state = AppState(
        task="Write a function to add two numbers",
        code="def add(a, b):\n    return a - b",  # Buggy implementation
    )

    mock_response = TestGenerationOut(
        test_code="from solution import add\n\ndef test_add():\n    assert add(2, 3) == 5\n",
        test_file="test_solution.py",
        test_description="Verifies addition function",
    )

    with patch("app.agents.test_generator.structured_test_llm") as mock_llm, \
         patch("app.agents.test_generator._execute_pytest_suite", return_value=(False, "FAILED test_solution.py::test_add - assert -1 == 5")):
        mock_llm.invoke.return_value = mock_response
        result = run_test_generator(state)

    assert result.tests_passed is False
    assert "FAILED" in result.test_results
    assert "❌ Automated Tests" in result.discussion[-1].content
