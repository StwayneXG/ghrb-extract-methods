import subprocess
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
    Generate a unified diff for .java files between two commits.
    :param repo_path: Path to the Git repository.
    :param old_commit: SHA of the old commit (buggy commit).
    :param new_commit: SHA of the new commit (fixed commit).
    :param test_prefix: Prefix path to identify test files.
    :return: String containing the unified diff.
    """
    # Get the diff with complete file content for .java files
    args = [
        'diff', '--no-prefix', f'{old_commit}..{new_commit}', '-U99999',
        '--', '*.java'
    ]
    diff_output = run_git_command(repo_path, args)
    
    # Filter out test files
    filtered_diff = []
    in_hunk = False
    for line in diff_output.splitlines():
        if line.startswith('--- ') or line.startswith('+++ '):
            # Check if the file is a test file
            file_path = line[4:]  # Skip '--- ' or '+++ '
            if test_prefix in file_path:
                in_hunk = False
            else:
                in_hunk = True
                filtered_diff.append(line)
        elif in_hunk:
            filtered_diff.append(line)
    
    return '\n'.join(filtered_diff)

def save_diff_to_file(diff_content, output_file):
    """
    Save the unified diff to a file.
    :param diff_content: The content of the diff.
    :param output_file: Path to save the diff.
    """
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(diff_content)
