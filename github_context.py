"""GitHub integration — read files and commit changes to a connected repository."""

from config import GITHUB_TOKEN

try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


def _get_repo(repo_full_name: str):
    if not GITHUB_AVAILABLE:
        raise RuntimeError("PyGithub not installed. Run: pip install PyGithub")
    if not GITHUB_TOKEN:
        raise RuntimeError("GitHub token not set in config.py")
    return Github(GITHUB_TOKEN).get_repo(repo_full_name)


def get_repo_file(repo_full_name: str, file_path: str, branch: str = "main") -> str:
    """Fetch a single file's content from a GitHub repository."""
    try:
        repo = _get_repo(repo_full_name)
        return repo.get_contents(file_path, ref=branch).decoded_content.decode("utf-8")
    except Exception as e:
        return f"[GitHub error: {e}]"


def list_repo_files(repo_full_name: str, path: str = "", branch: str = "main") -> list[str]:
    """List all file paths in a repository directory (recursive)."""
    if not GITHUB_AVAILABLE or not GITHUB_TOKEN:
        return []
    try:
        repo = _get_repo(repo_full_name)
        contents = list(repo.get_contents(path, ref=branch))
        files = []
        while contents:
            item = contents.pop(0)
            if item.type == "dir":
                contents.extend(repo.get_contents(item.path, ref=branch))
            else:
                files.append(item.path)
        return files
    except Exception:
        return []


def build_github_context(repo_full_name: str, file_paths: list[str], branch: str = "main") -> str:
    """Build a context string from multiple GitHub repo files (for AI injection)."""
    if not repo_full_name or not file_paths:
        return ""
    parts = []
    for fp in file_paths:
        content = get_repo_file(repo_full_name, fp, branch)
        parts.append(f"### GitHub: {repo_full_name}/{fp}\n```\n{content}\n```")
    return "\n\n".join(parts)


def commit_file(
    repo_full_name: str,
    file_path: str,
    content: str,
    commit_message: str = "Update via Local Helper",
    branch: str = "main",
) -> str:
    """Create or update a file in the repository and commit it.

    Args:
        repo_full_name:  e.g. 'Psmith23434/Local-Helper'
        file_path:       path inside the repo, e.g. 'src/utils.py'
        content:         new file content as string
        commit_message:  git commit message
        branch:          target branch (default 'main')

    Returns:
        Commit SHA string on success.

    Raises:
        RuntimeError on failure.
    """
    try:
        repo = _get_repo(repo_full_name)
        # Check if file already exists (update) or is new (create)
        try:
            existing = repo.get_contents(file_path, ref=branch)
            result = repo.update_file(
                path=file_path,
                message=commit_message,
                content=content,
                sha=existing.sha,
                branch=branch,
            )
        except Exception:
            result = repo.create_file(
                path=file_path,
                message=commit_message,
                content=content,
                branch=branch,
            )
        return result["commit"].sha
    except Exception as e:
        raise RuntimeError(f"GitHub commit failed: {e}") from e
