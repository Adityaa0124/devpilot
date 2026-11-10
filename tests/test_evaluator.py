from unittest.mock import patch
from app.agents.evaluator import evaluator_agent
from app.graph.state import (
    AppState,
    CandidateSolution,
    EvaluatorOut,
    CandidateScore,
)


def _make_state_with_candidates() -> AppState:
    candidates = [
        CandidateSolution(
            subagent_id="subagent_pragmatic",
            subagent_name="Pragmatic Pythonist",
            candidate_label="Candidate A",
            strategy="Clean iterative list accumulator",
            code="def fib(n):\n    a, b = 0, 1\n    res = []\n    for _ in range(n):\n        res.append(a)\n        a, b = b, a + b\n    return res\nprint(fib(5))",
            tool_used="run_python_code",
            execution_result="[0, 1, 1, 2, 3]\n",
            execution_success=True,
        ),
        CandidateSolution(
            subagent_id="subagent_defensive",
            subagent_name="Defensive Systems Engineer",
            candidate_label="Candidate B",
            strategy="Input validation with type and bounds checking",
            code="def fib(n):\n    if not isinstance(n, int) or n < 0:\n        raise ValueError('n must be non-negative int')\n    a, b = 0, 1\n    res = []\n    for _ in range(n):\n        res.append(a)\n        a, b = b, a + b\n    return res\nprint(fib(5))",
            tool_used="run_python_code",
            execution_result="[0, 1, 1, 2, 3]\n",
            execution_success=True,
        ),
        CandidateSolution(
            subagent_id="subagent_performance",
            subagent_name="Algorithmic Specialist",
            candidate_label="Candidate C",
            strategy="Generator with memory efficiency",
            code="def fib_gen(n):\n    a, b = 0, 1\n    for _ in range(n):\n        yield a\n        a, b = b, a + b\nprint(list(fib_gen(5)))",
            tool_used="run_python_code",
            execution_result="[0, 1, 1, 2, 3]\n",
            execution_success=True,
        ),
    ]

    return AppState(
        task="Write a Python function to compute Fibonacci numbers",
        candidates=candidates,
    )


def test_evaluator_scores_and_picks_winner():
    """Evaluator should score each candidate and declare a winning solution."""
    state = _make_state_with_candidates()

    mock_scores = [
        CandidateScore(
            candidate_label="Candidate A",
            correctness_score=9,
            robustness_score=7,
            efficiency_score=8,
            code_quality_score=9,
            total_score=83,
            strengths=["Simple, readable, correct output"],
            weaknesses=["No input validation"],
            verdict="Good baseline solution",
        ),
        CandidateScore(
            candidate_label="Candidate B",
            correctness_score=10,
            robustness_score=10,
            efficiency_score=8,
            code_quality_score=9,
            total_score=93,
            strengths=["Robust input validation", "Explicit exception handling"],
            weaknesses=["Slightly more verbose"],
            verdict="Best production-ready solution",
        ),
        CandidateScore(
            candidate_label="Candidate C",
            correctness_score=9,
            robustness_score=7,
            efficiency_score=10,
            code_quality_score=9,
            total_score=87,
            strengths=["O(1) memory generator", "Fast execution"],
            weaknesses=["Requires list() conversion for direct indexing"],
            verdict="Excellent for streaming",
        ),
    ]

    mock_eval = EvaluatorOut(
        candidate_scores=mock_scores,
        winner_label="Candidate B",
        selection_rationale="Candidate B provides complete input validation while preserving optimal O(N) execution.",
        evaluation_summary="Candidate B scored 93/100, outperforming A (83) and C (87) due to defensive engineering.",
        best_code=state.candidates[1].code,
        best_tool="run_python_code",
        approved=True,
        needs_clarification=False,
    )

    with patch("app.agents.evaluator.structured_evaluator_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_eval
        result = evaluator_agent(state)

    assert result.approved is True
    assert "Candidate B" in result.winner
    assert result.round == 1
    assert result.code == state.candidates[1].code
    assert result.evaluation is not None
    assert len(result.evaluation.candidate_scores) == 3
    assert result.evaluation.winner_label == "Candidate B"
    assert "Winner is Candidate B" in result.discussion[-1].content


def test_evaluator_requests_clarification():
    """Evaluator should flag needs_clarification if task details are missing."""
    state = _make_state_with_candidates()

    mock_eval = EvaluatorOut(
        candidate_scores=[],
        winner_label="None",
        selection_rationale="Task lacks critical requirements",
        evaluation_summary="Missing specification",
        best_code="",
        approved=False,
        needs_clarification=True,
        clarification_question="What should be returned for n <= 0?",
    )

    with patch("app.agents.evaluator.structured_evaluator_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_eval
        result = evaluator_agent(state)

    assert result.needs_clarification is True
    assert result.clarification_question == "What should be returned for n <= 0?"

