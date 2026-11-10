import os
import shlex
import subprocess
from app.core.config import EXECUTION_TIMEOUT_SECONDS, ALLOW_SHELL_EXECUTION
from app.tools.code_executor import get_sanitized_env
from app.core.logging import get_logger

logger = get_logger("shell_executor")

# Permitted command binaries
ALLOWED_COMMANDS = {
    "python",
    "pip",
    "pytest",
    "git",
    "echo",
    "cat",
    "dir",
    "ls",
    "mkdir",
    "type",
}

# Blocked high-risk command strings
BLOCKED_PATTERNS = [
    "rm -rf",
    "del /",
    "rmdir /s",
    "format",
    "shutdown",
    "mkfs",
    "curl",
    "wget",
    "netcat",
    "nc ",
    "> /dev/",
    "dd if=",
    ":(){ :|:& };:",
]


def run_shell_command(command: str, timeout: int = EXECUTION_TIMEOUT_SECONDS) -> str:
    """
    Safely executes an authorized shell command with:
    - Command authorization & pattern checking.
    - Path isolation to workspace directory.
    - Credential stripping from environment.
    - Enforced execution timeout.
    """
    # Check for explicitly blocked destructive patterns first
    if command:
        cmd_lower = command.strip().lower()
        for pattern in BLOCKED_PATTERNS:
            if pattern in cmd_lower:
                logger.warning({"event": "blocked_command_pattern", "pattern": pattern, "command": command})
                return f"Security Policy Violation: Command contains prohibited pattern '{pattern}'. Execution blocked."

    if not ALLOW_SHELL_EXECUTION:
        return "Security Policy Violation: Shell command execution is disabled by system policy (ALLOW_SHELL_EXECUTION=false)."

    if not command or not command.strip():
        return "Error: No shell command provided."

    # Parse command tokens safely
    try:
        tokens = shlex.split(command, posix=os.name != "nt")
    except Exception as exc:
        return f"Error: Command could not be parsed safely: {str(exc)}"

    if not tokens:
        return "Error: Empty command string."

    base_cmd = os.path.basename(tokens[0]).lower().replace(".exe", "")
    if base_cmd not in ALLOWED_COMMANDS:
        return f"Security Policy Violation: Command binary '{base_cmd}' is not in the allowed list: {sorted(list(ALLOWED_COMMANDS))}"

    workspace_dir = os.path.abspath("workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    safe_env = get_sanitized_env()

    try:
        result = subprocess.run(
            tokens,
            cwd=workspace_dir,
            env=safe_env,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""

        if result.returncode == 0:
            return stdout or stderr or "[Command executed successfully with no output]"

        error_details = []
        if stdout:
            error_details.append(f"STDOUT:\n{stdout}")
        if stderr:
            error_details.append(f"STDERR:\n{stderr}")
        return f"Command Failed (Exit Code {result.returncode}):\n" + "\n".join(error_details)

    except subprocess.TimeoutExpired:
        logger.warning({"event": "shell_command_timeout", "timeout_sec": timeout, "command": command})
        return f"Execution Error: Shell command timed out after {timeout} seconds."
    except Exception as exc:
        logger.error({"event": "shell_command_exception", "error": str(exc), "command": command})
        return f"Execution Error: Failed to execute command '{tokens[0]}': {str(exc)}"
