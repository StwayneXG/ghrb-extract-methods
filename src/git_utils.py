import os
from git import Repo
import json

def get_repo(repo_path):
    """Initialize the Git repository."""
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Repository path {repo_path} does not exist.")
    return Repo(repo_path)

def get_full_file_diff(repo, old_commit, new_commit, test_prefix):
    """
    Fetch the full file content in the diff between two commits.
    Excludes test files and non-.java files.
    :param repo: GitPython repo object.
    :param old_commit: SHA of the old commit (buggy commit).
    :param new_commit: SHA of the new commit (fixed commit).
    :param test_prefix: Prefix path to identify test files.
    :return: Dictionary containing file names and their full diffs.
    """
    old = repo.commit(old_commit)
    new = repo.commit(new_commit)
    diff = new.diff(old, create_patch=True, context_lines=99999)  # Large context

    full_diffs = {}
    for change in diff:
        # Filter out non-.java files and test files
        file_path = change.a_path or change.b_path
        if not file_path.endswith('.java'):
            continue
        if is_test_file(file_path, test_prefix):
            continue

        # Decode the diff and store it
        full_diffs[file_path] = change.diff.decode('utf-8')

    return full_diffs

def save_full_diff_to_file(full_diffs, output_file):
    """
    Save the full diffs for each file to individual text files.
    :param full_diffs: Dictionary with file names as keys and diffs as values.
    :param output_dir: Directory to save the output files.
    """

    with open(output_file, 'w', encoding='utf-8') as file:
        for file_name, diff_content in full_diffs.items():
            file.write(f"__FILE__: {file_name}\n\n")
            file.write(diff_content)
            file.write("\n\n")


def is_test_file(file_path, test_prefix):
    """Check if a file path corresponds to a test file."""
    return file_path.startswith(test_prefix)