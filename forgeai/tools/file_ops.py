from pathlib import Path

from langchain_core.tools import tool

PROJECT_ROOT = Path.cwd().resolve()


def safe_path(path: str) -> Path:
    """Resolve a path and ensure it stays inside the project."""

    target = (PROJECT_ROOT / path).resolve()

    if not target.is_relative_to(PROJECT_ROOT):
        raise ValueError(f"Path {path} is outside the project directory.")
    return target


@tool
def read_file(path: str) -> str:
    """Read and return the content of a file."""

    file_path = safe_path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist.")

    if not file_path.is_file():
        raise ValueError(f"Path {file_path} is not a file.")

    return file_path.read_text(encoding="utf-8")


@tool
def write_file(path: str, content: str) -> str:
    """Create or overwrite a file with the given content."""

    file_path = safe_path(path)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    file_path.write_text(content, encoding="utf-8")

    return f"File {file_path} written successfully."


@tool
def list_directory(path: str = ".") -> str:
    """List files and directories in the given path."""

    directory = safe_path(path)

    if not directory.exists():
        return f"Directory {directory} does not exist."

    if not directory.is_dir():
        return f"Path {directory} is not a directory."

    entries = sorted(directory.iterdir())

    if not entries:
        return f"Directory {directory} is empty."

    result = []

    for entry in entries:
        prefix = "[DIR]" if entry.is_dir() else "[FILE]"
        result.append(f"{prefix[0]} {entry.name}")

    return "\n".join(result)


TOOLS = [
    read_file,
    write_file,
    list_directory,
]
