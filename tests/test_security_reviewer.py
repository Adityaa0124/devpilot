from unittest.mock import patch
from app.agents.security_reviewer import security_reviewer_agent
from app.graph.state import AppState, SecurityReviewOut, SecurityFinding


def _make_state(**kwargs) -> AppState:
    defaults = dict(
        task="Write a script to backup database files",
        code="import os\nos.system('rm -rf /tmp/backup')",
        tool_used="run_python_code",
    )
    defaults.update(kwargs)
    return AppState(**defaults)


def test_security_reviewer_flags_high_severity():
    """Security reviewer must mark is_secure=False and record findings for dangerous code."""
    state = _make_state()

    mock_review = SecurityReviewOut(
        is_secure=False,
        findings=[
            SecurityFinding(
                severity="CRITICAL",
                file_name="solution.py",
                line_or_location="Line 2",
                explanation="Dangerous os.system command with arbitrary destructive deletion",
                suggested_remediation="Use shutil.rmtree with validated directory path and error handling",
            )
        ],
        summary="Critical command execution vulnerability detected.",
    )

    with patch("app.agents.security_reviewer.structured_security_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_review
        result = security_reviewer_agent(state)

    assert result.security_review.is_secure is False
    assert len(result.security_review.findings) == 1
    assert result.security_review.findings[0].severity == "CRITICAL"
    assert "BLOCKED" in result.discussion[-1].content
    assert result.current_stage == "security_reviewed"


def test_security_reviewer_approves_safe_code():
    """Security reviewer should pass code without security flaws."""
    state = _make_state(code="def add(a, b):\n    return a + b\nprint(add(2, 3))")

    mock_review = SecurityReviewOut(
        is_secure=True,
        findings=[],
        summary="No security vulnerabilities identified in pure arithmetic function.",
    )

    with patch("app.agents.security_reviewer.structured_security_llm") as mock_llm:
        mock_llm.invoke.return_value = mock_review
        result = security_reviewer_agent(state)

    assert result.security_review.is_secure is True
    assert len(result.security_review.findings) == 0
    assert "PASSED" in result.discussion[-1].content

