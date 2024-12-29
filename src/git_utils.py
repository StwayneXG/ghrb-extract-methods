import os
from git import Repo
import json

def get_repo(repo_path):
    """Initialize the Git repository."""
    if not os.path.exists(repo_path):
        raise FileNotFoundError(f"Repository path {repo_path} does not exist.")
    return Repo(repo_path)

def get_diff_metadata(repo, buggy_commit, fixed_commit, test_prefix):
    """Extract metadata for all changed files in a commit diff."""
    old = repo.commit(buggy_commit)
    new = repo.commit(fixed_commit)
    diff = new.diff(old, create_patch=True)

    changes = []
    for change in diff:
        # Filter out non-.java files and test files
        if not change.a_path.endswith('.java') and not change.b_path.endswith('.java'):
            continue
        if is_test_file(change.a_path or change.b_path, test_prefix):
            continue

        # Parse hunk metadata
        if change.diff:
            diff_lines = change.diff.decode('utf-8').splitlines()
            for line in diff_lines:
                if line.startswith('@@'):
                    # Extract line number metadata
                    parts = line.split(' ')
                    old_meta = parts[1].split(',')
                    new_meta = parts[2].split(',')
                    old_start = int(old_meta[0][1:])
                    old_lines = int(old_meta[1]) if len(old_meta) > 1 else 0
                    new_start = int(new_meta[0][1:])
                    new_lines = int(new_meta[1]) if len(new_meta) > 1 else 0

                    # Store metadata
                    changes.append({
                        "file_name": change.a_path or change.b_path,
                        "commit_details": {
                            "buggy_commit": buggy_commit,
                            "fixed_commit": fixed_commit
                        },
                        "diff_meta_data": {
                            "old_start": old_start,
                            "old_lines": old_lines,
                            "new_start": new_start,
                            "new_lines": new_lines
                        },
                        "hunk_data": [line for line in diff_lines if line.startswith(('+', '-'))]
                    })

    return changes

def save_changes_to_json(changes, output_file):
    """Save changes metadata to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(changes, file, indent=4)
    print(f"Saved diff metadata to {output_file}")

def is_test_file(file_path, test_prefix):
    """Check if a file path corresponds to a test file."""
    return file_path.startswith(test_prefix)