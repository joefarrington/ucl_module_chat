import os
from pathlib import Path

from git import Repo


def get_abs_path_using_repo_root(path: str | Path) -> Path:
    """Takes path relative to the repo root and returns the absolute path."""

    # Initialize the repo (this will automatically find the root if
    # you're in a subdirectory)
    repo = Repo(os.getcwd(), search_parent_directories=True)

    # Get the root directory
    repo_root = repo.git.rev_parse("--show-toplevel")
    abs_path = Path(repo_root) / path
    return abs_path
