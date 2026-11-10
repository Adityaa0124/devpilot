from unittest.mock import patch
from app.agents.blind_subagents import (
    execute_blind_subagent,
    blind_subagents_node,
    SUBAGENTS_CONFIG,
)
from app.graph.state import AppState, SubagentOut, CandidateSolution


def _make_state(**kwargs) -> AppState:
    defaults = dict(
        task="Write a Python function to compute Fibonacci numbers",
        plan=["Define fibonacci function", "Return sequence", "Print result"],
    )
    defaults.update(kwargs)
    return AppState(**defaults)


def test_execute_blind_subagent_run_python():
    """Subagent should generate code and run it via tool in isolation."""
    config = SUBAGENTS_CONFIG[0]  # Pragmatic

    mock_response = SubagentOut(
        strategy="Iterative loop with standard list",
        code="def fib(n):\n    a, b = 0, 1\n    res = []\n    for _ in range(n):\n        res.append(a)\n        a, b = b, a + b\n    return res\nprint(fib(5))",
        tool="run_python_code",
        filename=None,
    )

    with patch("app.agents.blind_subagents.structured_subagent_llm") as mock_llm, \
         patch("app.agents.blind_subagents.execute_tool", return_value="[0, 1, 1, 2, 3]\n") as mock_tool:
        mock_llm.invoke.return_value = mock_response
        candidate = execute_blind_subagent("Compute fibonacci", ["Step 1"], config)

    assert candidate.candidate_label == "Candidate A"
    assert candidate.subagent_id == "subagent_pragmatic"
    assert candidate.strategy == "Iterative loop with standard list"
    assert candidate.tool_used == "run_python_code"
    assert candidate.execution_result == "[0, 1, 1, 2, 3]\n"
    assert candidate.execution_success is True


def test_blind_subagents_node_generates_all_candidates():
    """blind_subagents_node should independently execute all configured subagents."""
    state = _make_state()

    mock_responses = [
        SubagentOut(
            strategy="Pragmatic simple solution",
            code="def fib(n): ...",
            tool="run_python_code",
        ),
        SubagentOut(
            strategy="Defensive solution with input validation",
            code="def fib(n): if not isinstance(n, int): raise ValueError() ...",
            tool="run_python_code",
        ),
        SubagentOut(
            strategy="Performance-optimized generator",
            code="def fib(n): ...",
            tool="run_python_code",
        ),
    ]

    with patch("app.agents.blind_subagents.structured_subagent_llm") as mock_llm, \
         patch("app.agents.blind_subagents.execute_tool", return_value="Output OK"):
        mock_llm.invoke.side_effect = mock_responses
        result_state = blind_subagents_node(state)

    assert len(result_state.candidates) == 3
    labels = [c.candidate_label for c in result_state.candidates]
    assert labels == ["Candidate A", "Candidate B", "Candidate C"]

    # Initial code/result should be set
    assert result_state.code is not None
    assert result_state.execution_result == "Output OK"
    # Discussion should contain entries for all 3 subagents
    assert len(result_state.discussion) == 3

