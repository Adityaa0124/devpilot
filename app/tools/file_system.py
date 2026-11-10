import os
from app.core.logging import get_logger

logger = get_logger("file_system")

WORKSPACE_DIR_NAME = "workspace"
BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".ps1", ".vbs", ".sh"}
BLOCKED_FILENAMES = {".env", ".gitignore", "dockerfile", "docker-compose.yml", "alembic.ini"}


def write_file(filename: str, content: str) -> str:
    """
    Safely writes content to a file inside the designated workspace directory.

    Security Guarantees:
    - Path traversal prevention: ensures resolved target is strictly within workspace/.
    - Absolute path prohibition: prevents accessing arbitrary system paths.
    - Blocks writing to sensitive configuration and executable shell files.
    - Creates necessary parent directories within the workspace boundary.
    """
    if not filename or not filename.strip():
        return "Error: Filename cannot be empty."

    # Disallow absolute paths directly
    if os.path.isabs(filename) or filename.startswith(("\\", "/")):
        logger.warning({"event": "blocked_file_write", "reason": "absolute_path", "filename": filename})
        return "Security Violation: Absolute file paths are prohibited. Specify a relative filename inside workspace."

    clean_filename = filename.strip().replace("\\", "/")
    base_name = os.path.basename(clean_filename).lower()

    if base_name in BLOCKED_FILENAMES:
        logger.warning({"event": "blocked_file_write", "reason": "sensitive_filename", "filename": filename})
        return f"Security Violation: Writing to sensitive configuration file '{base_name}' is blocked."

    ext = os.path.splitext(base_name)[1].lower()
    if ext in BLOCKED_EXTENSIONS:
        logger.warning({"event": "blocked_file_write", "reason": "executable_extension", "filename": filename})
        return f"Security Violation: File extension '{ext}' is prohibited in the workspace."

    workspace_root = os.path.abspath(WORKSPACE_DIR_NAME)
    os.makedirs(workspace_root, exist_ok=True)

    # Resolve destination path
    resolved_target = os.path.abspath(os.path.join(workspace_root, clean_filename))

    # Verify path confinement
    if not (resolved_target == workspace_root or resolved_target.startswith(workspace_root + os.sep)):
        logger.warning({"event": "path_traversal_attempt", "filename": filename, "resolved": resolved_target})
        return "Security Violation: Path traversal detected. Access denied outside the workspace directory."

    parent_dir = os.path.dirname(resolved_target)
    os.makedirs(parent_dir, exist_ok=True)

    try:
        with open(resolved_target, "w", encoding="utf-8") as f:
            f.write(content or "")
        rel_path = os.path.relpath(resolved_target, os.getcwd())
        return f"File successfully written to {rel_path}"
    except Exception as exc:
        logger.error({"event": "file_write_error", "filename": filename, "error": str(exc)})
        return f"Error: Failed to write file: {str(exc)}"
