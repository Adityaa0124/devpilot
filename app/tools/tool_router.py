from app.tools.code_executor import run_python_code
from app.tools.file_system import write_file
from app.tools.shell_executor import run_shell_command


def execute_tool(tool_name, response, filename: str = None):
    """Dispatches to the correct tool based on tool_name."""
    if tool_name == "run_python_code":
        return run_python_code(response.code)

    if tool_name == "write_file":
        return write_file(filename, response.code)

    if tool_name == "run_shell_command":
        return run_shell_command(response.code)

    return f"Error: tool '{tool_name}' does not exist. Available tools: run_python_code, write_file, run_shell_command."