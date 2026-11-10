import os
import sys
import time
import tempfile
import subprocess
from langchain_core.messages import HumanMessage

from app.graph.state import AppState, Message, TestGenerationOut
from app.core.config import EXECUTION_TIMEOUT_SECONDS
from app.core.logging import get_logger
from app.core.llm import get_chat_llm
from app.tools.code_executor import get_sanitized_env

logger = get_logger("test_generator")

llm = get_chat_llm(temperature=0.2)
structured_test_llm = llm.with_structured_output(TestGenerationOut)


def _execute_pytest_suite(solution_code: str, test_code: str, timeout: int = EXECUTION_TIMEOUT_SECONDS) -> tuple[bool, str]:
    """
    Executes generated unit tests against the solution inside an isolated temporary directory.
    Returns (tests_passed, output_log).
    """
    safe_env = get_sanitized_env()

    with tempfile.TemporaryDirectory(prefix="devpilot_test_") as temp_dir:
        solution_file = os.path.join(temp_dir, "solution.py")
        test_file = os.path.join(temp_dir, "test_solution.py")

        with open(solution_file, "w", encoding="utf-8") as f:
            f.write(solution_code)

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        try:
            # Run pytest directly in subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                cwd=temp_dir,
                env=safe_env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            stdout = result.stdout or ""
            stderr = result.stderr or ""
            output = (stdout + "\n" + stderr).strip()

            passed = (result.returncode == 0)
            return passed, output

        except subprocess.TimeoutExpired:
            return False, f"Test execution timed out after {timeout} seconds."
        except Exception as exc:
            return False, f"Test execution error: {str(exc)}"


def test_generator_agent(state: AppState) -> AppState:
    """
    Automated Test Generation Agent.
    Generates unit tests for the current code solution and executes them in an isolated test runner.
    """
    task = state.task
    code = state.code or ""

    if not code.strip():
        state.test_results = "No code provided to test."
        state.tests_passed = False
        return state

    prompt = f"""
You are a Principal Test Automation Engineer.

Task:
{task}

Implementation Code:
```python
{code}
```

Your Mission:
Write a comprehensive suite of `pytest` unit tests for the implementation above.

Requirements:
1. Include tests for standard / happy-path cases.
2. Include tests for edge cases (empty inputs, zero, boundary values, type mismatches).
3. If the code defines functions, import them from `solution` (e.g. `from solution import ...`).
4. Keep the test file self-contained, clean, and executable via pytest.
"""

    start_time = time.time()
    response = structured_test_llm.invoke([HumanMessage(content=prompt)])
    latency_ms = round((time.time() - start_time) * 1000)

    test_code = response.test_code
    state.test_code = test_code
    state.test_file = response.test_file

    # Execute tests in isolated runner
    tests_passed, test_output = _execute_pytest_suite(code, test_code)

    state.tests_passed = tests_passed
    state.test_results = test_output
    state.current_stage = "tested"

    verdict_emoji = "✅" if tests_passed else "❌"
    msg_content = (
        f"{verdict_emoji} Automated Tests ({'PASSED' if tests_passed else 'FAILED'})\n"
        f"Summary: {response.test_description}\n"
        f"Output:\n{test_output}"
    )
    state.discussion.append(Message(agent="test_generator", content=msg_content))

    logger.info({
        "agent": "test_generator",
        "tests_passed": tests_passed,
        "latency_ms": latency_ms,
    })

    return state

