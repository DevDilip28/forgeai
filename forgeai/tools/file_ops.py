from collections.abc import Iterable
from pathlib import Path
from typing import Annotated

import pathspec
from langchain_core.tools import tool


def _get_gitignore_spec(
    dir_path: Path,
) -> tuple[Path, pathspec.PathSpec | None]:
    root_path = dir_path

    while root_path.parent != root_path:
        if (root_path / ".git").exists() or (root_path / ".gitignore").exists():
            break
        root_path = root_path.parent

    gitignore_path = root_path / ".gitignore"

    if gitignore_path.exists():
        with gitignore_path.open("r", encoding="utf-8") as file:
            spec = pathspec.PathSpec.from_lines(
                "gitwildmatch",
                file.read().splitlines(),
            )
        return root_path, spec

    return root_path, None


def _is_ignored(
    path: Path,
    root_path: Path,
    spec: pathspec.PathSpec | None,
) -> bool:
    if ".git" in path.parts:
        return True

    if spec:
        try:
            relative_path = path.relative_to(root_path)
            relative_string = relative_path.as_posix()

            if path.is_dir():
                relative_string = f"{relative_string}/"

            return spec.match_file(relative_string)
        except ValueError:
            return False

    return False


def _collect_items(
    all_paths: Iterable[Path],
    dir_path: Path,
    root_path: Path,
    spec: pathspec.PathSpec | None,
) -> list[str]:
    items = []

    for path in all_paths:
        if _is_ignored(path, root_path, spec):
            continue

        relative_path = path.relative_to(dir_path)
        relative_string = relative_path.as_posix()

        if path.is_dir():
            items.append(f"{relative_string}/")
        else:
            items.append(relative_string)

    return items


def _format_listing(items: list[str]) -> str:
    if not items:
        return "Directory is empty (or all files are ignored)"

    items.sort()

    max_items = 500
    max_chars = 32768

    result_items = items[:max_items]
    result = "\n".join(result_items)

    if len(items) > max_items or len(result) > max_chars:
        if len(result) > max_chars:
            result = result[:max_chars] + "... (truncated due to length)"

        summary = []

        if len(items) > max_items:
            summary.append(f"{len(items) - max_items} more items")

        return (
            f"{result}\n\n"
            f"... and {', '.join(summary)} "
            f"(output capped to prevent context overflow)"
        )

    return result


@tool
def read_file(
    path: Annotated[str, "Path to the file to read"],
    start_line: Annotated[int | None, "Starting line number (1-indexed)"] = None,
    end_line: Annotated[int | None, "Ending line number (inclusive)"] = None,
) -> str:
    """Read the contents of a file, optionally within a specific line range."""
    try:
        file_path = Path(path)

        if not file_path.exists():
            return f"Error: File '{path}' does not exist"

        if not file_path.is_file():
            return f"Error: '{path}' is not a file"

        with file_path.open("r", encoding="utf-8") as file:
            if start_line is None and end_line is None:
                return file.read()

            lines = file.readlines()
            start = (start_line - 1) if start_line else 0
            end = end_line if end_line else len(lines)

            return "".join(lines[start:end])

    except Exception as error:
        return f"Error reading file: {error!s}"


@tool
def write_file(
    path: Annotated[str, "Path to the file to write"],
    content: Annotated[str, "Content to write to the file"],
    *,
    create_dirs: Annotated[
        bool,
        "Create parent directories if they don't exist",
    ] = True,
) -> str:
    """Write content to a file and optionally create missing parent directories."""

    try:
        file_path = Path(path)

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("w", encoding="utf-8") as file:
            file.write(content)

        return f"Successfully wrote {len(content)} characters to '{path}'"

    except Exception as error:
        return f"Error writing file: {error!s}"


@tool
def list_directory(
    path: Annotated[str, "Directory path"] = ".",
    *,
    recursive: Annotated[bool, "Recursive"] = False,
    include_gitignored: Annotated[bool, "Include ignored"] = False,
) -> str:
    """List files and directories while respecting .gitignore rules by default."""
    try:
        dir_path = Path(path).absolute()

        if not dir_path.exists():
            return f"Error: Directory '{path}' does not exist"

        if not dir_path.is_dir():
            return f"Error: '{path}' is not a directory"

        if not include_gitignored:
            root_path, spec = _get_gitignore_spec(dir_path)
        else:
            root_path, spec = dir_path, None

        all_paths = dir_path.rglob("*") if recursive else dir_path.iterdir()

        items = _collect_items(
            all_paths,
            dir_path,
            root_path,
            spec,
        )

        return _format_listing(items)

    except Exception as error:
        return f"Error listing directory: {error!s}"


file_tools = [
    read_file,
    write_file,
    list_directory,
]

__all__ = [
    "file_tools",
    "list_directory",
    "read_file",
    "write_file",
]
