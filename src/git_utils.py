import os
from git import Repo

def get_repo(repo_path):
    """Initialize the Git repository."""
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Repository path {repo_path} does not exist.")
    return Repo(repo_path)

def get_diff_between_commits(repo, old_commit, new_commit):
    """
    Fetch the diff between two commits.
    :param repo: GitPython repo object.
    :param old_commit: SHA of the old commit (buggy commit).
    :param new_commit: SHA of the new commit (merge commit).
    :return: Diff text.
    """
    old = repo.commit(old_commit)
    new = repo.commit(new_commit)
    diff = new.diff(old, create_patch=True)

    java_diffs = []
    for change in diff:
        if change.a_path.endswith('.java') or change.b_path.endswith('.java'):
            java_diffs.append(change.diff)
    return java_diffs
