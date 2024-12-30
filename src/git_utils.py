import subprocess
import json
import os

def run_git_command(repo_path, args):
    """
    Run a git command using subprocess.
    :param repo_path: Path to the Git repository.
    :param args: List of git command arguments.
    :return: Output of the git command.
    """
    result = subprocess.run(
        ['git'] + args,
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Git command failed: {result.stderr}")
    return result.stdout

def get_full_file_diff(repo_path, old_commit, new_commit, test_prefix):
    """
    Generate unified diffs for .java files between two commits, organized by file.
    Exclude unnecessary metadata and only include the changed file content.
    :param repo_path: Path to the Git repository.
    :param old_commit: SHA of the old commit (buggy commit).
    :param new_commit: SHA of the new commit (fixed commit).
    :param test_prefix: Prefix path to identify test files.
    :return: Dictionary containing file contents organized by file name.
    """
    # Run the git diff command
    args = [
        'diff', '--no-prefix', f'{old_commit}..{new_commit}', '-U99999',
        '--', '*.java'
    ]
    diff_output = run_git_command(repo_path, args)
    
    # Parse the diff to group by file
    diffs_by_file = {}
    current_file = None
    current_diff = []

    for line in diff_output.splitlines():
        # Skip metadata lines
        if line.startswith('diff --git') or line.startswith('index') or line.startswith('similarity index') or line.startswith('rename '):
            continue
        if line.startswith('@@'):
            continue  # Skip chunk headers
        
        # Handle file header lines (e.g., `+++ b/...`)
        if line.startswith('+++ ') or line.startswith('--- '):
            # Save the previous file's diff
            if current_file and current_diff:
                diffs_by_file[current_file] = "\n".join(current_diff).strip()
                current_diff = []
            # Extract the file name
            file_path = line[4:]  # Skip '+++ '
            if test_prefix in file_path:
                current_file = None  # Skip test files
            else:
                current_file = os.path.basename(file_path)  # Keep only file name                
        elif current_file:
            current_diff.append(line)
    
    # Save the last file's diff
    if current_file and current_diff:
        diffs_by_file[current_file] = "\n".join(current_diff).strip()
    
    return diffs_by_file


def save_diffs_to_json(diff_dict, output_file):
    """
    Save diffs organized by file into a JSON file.
    :param diff_dict: Dictionary containing diffs organized by file name.
    :param output_file: Path to save the JSON file.
    """
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(diff_dict, file, indent=4)
