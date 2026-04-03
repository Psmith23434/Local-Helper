"""GitHub integration — read files from a connected repository."""

from config import GITHUB_TOKEN

try:
    from github import Github, GithubException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False


def get_repo_file(repo_full_name: str, file_path: str, branch: str = "main") -> str:
    """Fetch a single file from a GitHub repository.

    Args:
        repo_full_name: e.g. 'Psmith23434/Local-Helper'
        file_path:      path inside the repo, e.g. 'src/main.py'
        branch:         branch name, defaults to 'main'

    Returns:
        File content as string, or error message.
    """
    if not GITHUB_AVAILABLE:
        return "[PyGithub not installed]"
    if not GITHUB_TOKEN:
        return "[GitHub token not set in config.py]"
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(repo_full_name)
        file_content = repo.get_contents(file_path, ref=branch)
        return file_content.decoded_content.decode("utf-8")
    except Exception as e:
        return f"[GitHub error: {e}]"


def list_repo_files(repo_full_name: str, path: str = "", branch: str = "main") -> list[str]:
    """List files in a GitHub repository directory.

    Returns:
        List of file paths, or empty list on error.
    """
    if not GITHUB_AVAILABLE or not GITHUB_TOKEN:
        return []
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(repo_full_name)
        contents = repo.get_contents(path, ref=branch)
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
    """Build context string from multiple GitHub repo files."""
    if not repo_full_name or not file_paths:
        return ""
    parts = []
    for fp in file_paths:
        content = get_repo_file(repo_full_name, fp, branch)
        parts.append(f"### GitHub: {repo_full_name}/{fp}\n```\n{content}\n```")
    return "\n\n".join(parts)
