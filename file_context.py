"""Read local files and inject their content as AI context."""

import os

SUPPORTED_EXTENSIONS = {".txt", ".py", ".md", ".json", ".yaml", ".yml", ".toml", ".csv"}


def read_file(filepath: str) -> str:
    """Read a file and return its content as a string."""
    _, ext = os.path.splitext(filepath)
    if ext not in SUPPORTED_EXTENSIONS:
        return f"[Unsupported file type: {ext}]"
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"[Error reading file: {e}]"


def build_file_context(filepaths: list[str]) -> str:
    """Build a combined context string from a list of file paths."""
    if not filepaths:
        return ""
    parts = []
    for fp in filepaths:
        name = os.path.basename(fp)
        content = read_file(fp)
        parts.append(f"### File: {name}\n```\n{content}\n```")
    return "\n\n".join(parts)
