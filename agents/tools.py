import pathlib
import subprocess

from langchain_core.tools import tool

PROJECT_ROOT = pathlib.Path.cwd() / "generated_project"
PROJECT_ROOT.mkdir(parents=True, exist_ok=True)

# =========================
# SAFE PATH
# =========================

def safe_path_for_project(path: str) -> pathlib.Path:
    p = (PROJECT_ROOT / path).resolve()

    try:
        p.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        raise ValueError("Attempt to access outside project root")

    return p

# =========================
# WRITE FILE
# =========================

@tool
def write_file(path: str, content: str) -> str:
    """
    Write content to a file. Creates the file if it does not exist.
    Always pass path and content as plain strings.
    """
    p = safe_path_for_project(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with open(p, "w", encoding="utf-8") as f:
        f.write(content.strip())

    return f"WROTE: {p}"

# =========================
# EDIT FILE
# =========================

@tool
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """
    Replace old_text with new_text inside an existing file.
    Always pass path, old_text, and new_text as plain strings.
    """
    p = safe_path_for_project(path)

    if not p.exists():
        return f"ERROR: File does not exist: {path}"

    content = p.read_text(encoding="utf-8")

    if old_text not in content:
        return "ERROR: old_text not found in file"

    updated = content.replace(old_text, new_text, 1)
    p.write_text(updated, encoding="utf-8")

    return f"UPDATED: {p}"

# =========================
# READ FILE
# =========================

@tool
def read_file(path: str) -> str:
    """
    Read and return the content of a file.
    Always pass path as a plain string.
    """
    p = safe_path_for_project(path)

    if not p.exists():
        return ""

    with open(p, "r", encoding="utf-8") as f:
        return f.read()

# =========================
# LIST FILES
# =========================

@tool
def list_file(directory: str = ".") -> str:
    """
    List all files in the project directory.
    Always pass directory as a plain string.
    """
    p = safe_path_for_project(directory)

    if not p.is_dir():
        return "Directory not found"

    files = [
        str(f.relative_to(PROJECT_ROOT))
        for f in p.glob("**/*")
        if f.is_file()
    ]

    return "\n".join(files) if files else "No files found."

# =========================
# CURRENT DIRECTORY
# =========================

@tool
def get_current_directory() -> str:
    """
    Return the absolute path to the project root directory.
    """
    return str(PROJECT_ROOT)

# =========================
# RUN COMMAND
# =========================

@tool
def run_cmd(
    cmd: str,
    cwd: str = None,
    timeout: int = 120,
) -> str:
    """
    Execute a shell command and return the output.

    cmd MUST be a plain string.
    CORRECT: run_cmd(cmd="ls -la")
    WRONG:   run_cmd(cmd=["ls", "-la"])

    Args:
        cmd: Plain shell command string. Never pass a list or array.
        cwd: Optional subdirectory within the project root to run from.
        timeout: Max seconds to wait before timing out (default 120).
    """
    if isinstance(cmd, list):
        cmd = " ".join(cmd)

    cwd_dir = safe_path_for_project(cwd) if cwd else PROJECT_ROOT

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(cwd_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = [f"Exit code: {result.returncode}"]

        if result.stdout.strip():
            output.append(f"\nSTDOUT:\n{result.stdout}")

        if result.stderr.strip():
            output.append(f"\nSTDERR:\n{result.stderr}")

        return "\n".join(output)

    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout} seconds"