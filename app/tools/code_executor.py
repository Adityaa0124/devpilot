import os
import sys
import tempfile
import subprocess
from app.core.config import EXECUTION_TIMEOUT_SECONDS
from app.core.logging import get_logger

logger = get_logger("code_executor")

# Sensitive environment variables to strip from child execution
SENSITIVE_ENV_KEYS = {
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "DATABASE_URL",
    "API_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_ACCESS_KEY_ID",
    "GITHUB_TOKEN",
    "SECRET_KEY",
}


def get_sanitized_env() -> dict:
    """Creates a sanitized environment dictionary that protects host credentials."""
    safe_env = {}
    for key, value in os.environ.items():
        if key.upper() in SENSITIVE_ENV_KEYS:
            continue
        if any(secret_term in key.upper() for secret_term in ("KEY", "SECRET", "PASSWORD", "TOKEN")):
            continue
        safe_env[key] = value
    return safe_env


def run_python_code(code: str, timeout: int = EXECUTION_TIMEOUT_SECONDS) -> str:
    """
    Executes Python code safely inside an isolated temporary directory with:
    - Guaranteed cleanup of temporary files (try/finally).
    - Strict execution timeout to prevent DoS / infinite loops.
    - Environment credential sanitization.
    - Captures stdout and stderr safely.
    """
    if not code or not code.strip():
        return "Error: No Python code provided to execute."

    safe_env = get_sanitized_env()

    # Use TemporaryDirectory with context manager for guaranteed disk cleanup
    with tempfile.TemporaryDirectory(prefix="devpilot_sandbox_") as temp_dir:
        script_path = os.path.join(temp_dir, "solution.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        try:
            result = subprocess.run(
                [sys.executable, script_path],
                cwd=temp_dir,
                env=safe_env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            stdout = result.stdout or ""
            stderr = result.stderr or ""

            if result.returncode == 0:
                if stdout:
                    return stdout
                if stderr:
                    return f"[Success with Warnings]\n{stderr}"
                return "[Execution completed successfully with no output]"

            # Non-zero exit code: report error clearly
            error_details = []
            if stdout:
                error_details.append(f"STDOUT:\n{stdout}")
            if stderr:
                error_details.append(f"STDERR / TRACEBACK:\n{stderr}")
            return f"Runtime Error (Exit Code {result.returncode}):\n" + "\n".join(error_details)

        except subprocess.TimeoutExpired:
            logger.warning({"event": "code_execution_timeout", "timeout_sec": timeout})
            return f"Execution Error: Execution timed out after {timeout} seconds. Possible infinite loop or blocking I/O."
        except Exception as exc:
            logger.error({"event": "code_execution_exception", "error": str(exc)})
            return f"Execution Error: Subprocess failed to start: {str(exc)}"
