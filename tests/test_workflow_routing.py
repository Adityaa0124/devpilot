from app.graph.state import AppState, SecurityReviewOut, SecurityFinding
from app.graph.workflow import (
    after_planner,
    after_security_review,
    after_test_generator,
    after_reviewer,
)


def test_after_planner_clarification():
    """Should route to 'end' when planner requests clarification."""
    state = AppState(task="vague", needs_clarification=True)
    assert after_planner(state) == "end"
    assert state.final_status == "clarification_needed"


def test_after_planner_proceeds_to_developer():
    """Should route to developer when task is clear."""
    state = AppState(task="clear task", needs_clarification=False)
    assert after_planner(state) == "developer"


def test_after_security_review_failure_retries():
    """Security failure with retries remaining must route back to developer."""
    state = AppState(
        task="run command",
        round=0,
        max_rounds=3,
        security_review=SecurityReviewOut(
            is_secure=False,
            findings=[SecurityFinding(
                severity="HIGH",
                file_name="solution.py",
                line_or_location="1",
                explanation="Insecure subprocess",
                suggested_remediation="Sanitize input",
            )],
            summary="Failed",
        )
    )
    next_node = after_security_review(state)
    assert next_node == "developer"
    assert state.round == 1


def test_after_security_review_failure_max_rounds_terminates():
    """Security failure when max_rounds reached must safely terminate at end."""
    state = AppState(
        task="run command",
        round=3,
        max_rounds=3,
        security_review=SecurityReviewOut(is_secure=False, findings=[], summary="Failed"),
    )
    next_node = after_security_review(state)
    assert next_node == "end"
    assert state.final_status == "failed"


def test_after_test_generator_success_proceeds():
    """Passed tests should proceed to reviewer."""
    state = AppState(task="some task", tests_passed=True)
    assert after_test_generator(state) == "reviewer"


def test_after_test_generator_failure_retries():
    """Failed tests should route back to developer if rounds remain."""
    state = AppState(task="some task", tests_passed=False, round=0, max_rounds=3)
    assert after_test_generator(state) == "developer"
    assert state.round == 1


def test_after_reviewer_approves_completes():
    """Reviewer approval should route to end with final_status='completed'."""
    state = AppState(task="some task", approved=True)
    assert after_reviewer(state) == "end"
    assert state.final_status == "completed"


def test_after_reviewer_rejection_retries_or_fails():
    """Reviewer rejection should retry until max_rounds, then terminate safely."""
    state_retry = AppState(task="task", approved=False, round=1, max_rounds=3)
    assert after_reviewer(state_retry) == "developer"

    state_max = AppState(task="task", approved=False, round=3, max_rounds=3)
    assert after_reviewer(state_max) == "end"
    assert state_max.final_status == "failed"

