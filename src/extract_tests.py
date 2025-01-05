import json
import subprocess as sp
import javalang
import pandas as pd
import os

metadata = json.load(open("data/metadata.json"))
config = json.load(open("data/config.json"))
test_data = json.load(open("data/test_data.json"))

def git_checkout(repo_path, commit_hash, version='buggy'):
    cp = sp.run(['git', 'checkout', commit_hash],
                cwd=repo_path, capture_output=True)
    assert cp.returncode == 0, f"checkout for {version} commit was not successful: {cp.stderr.decode()}"
    out = sp.run(['git', 'rev-parse', 'HEAD'],
                 cwd=repo_path, capture_output=True)
    assert commit_hash in out.stdout.decode(
    ), f"checkout for {version} commit {commit_hash} was not successful: current commit is {out.stdout.decode()}"

def git_reset(repo_dir_path):
    sp.run(['git', 'reset', '--hard', 'HEAD'],
           cwd=repo_dir_path, stdout=sp.DEVNULL, stderr=sp.DEVNULL)


def git_clean(repo_dir_path):
    sp.run(['git', 'clean', '-df'],
           cwd=repo_dir_path, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

def get_testfile_tree(test_file):
    with open(test_file, 'r') as file:
        tree = javalang.parse.parse(file.read())
    return tree


def _find_method_body(start_position, content: str) -> str:
    lines = content.split('\n')
    current_line = start_position[0] - 1
    current_column = start_position[1] - 1
    brace_count = 0
    in_string = False
    in_char = False
    in_block_comment = False
    escape_next = False
    method_lines = []

    while current_line < len(lines):
        line = lines[current_line]
        i = current_column if current_line == start_position[0] - 1 else 0
        in_line_comment = False

        while i < len(line):
            char = line[i]

            if escape_next:
                escape_next = False
            elif char == '\\':
                escape_next = True
            elif in_string:
                if char == '"':
                    in_string = False
            elif in_char:
                if char == "'":
                    in_char = False
            elif in_line_comment:
                pass
            elif in_block_comment:
                if char == '*' and i + 1 < len(line) and line[i + 1] == '/':
                    in_block_comment = False
                    i += 1
            else:
                if char == '"':
                    in_string = True
                elif char == "'":
                    in_char = True
                elif char == '/' and i + 1 < len(line):
                    if line[i + 1] == '/':
                        in_line_comment = True
                        i += 1
                    elif line[i + 1] == '*':
                        in_block_comment = True
                        i += 1
                elif char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        method_lines.append(line[:i + 1])
                        return '\n'.join(method_lines)

            i += 1

        method_lines.append(line)
        current_line += 1
        current_column = 0

    return '\n'.join(method_lines)

def get_test_methods(tree, test_method_name):
    for path, node in tree.filter(javalang.tree.MethodDeclaration):
        if node.name == test_method_name:
            return node

def main():
    os.makedirs("ground_truth_testcases", exist_ok=True)
    for project_key, project_data in metadata.items():
        project = project_key.rsplit("-", 1)[0]
        
        repo_info = config.get(project)
        repo_path = repo_info["repo_path"]

        test_prefix = repo_info["test_prefix"]

        git_reset(repo_path)
        git_clean(repo_path)

        git_checkout(repo_path, project_data["merge_commit"], 'buggy')

        valid_tests = test_data[project_key]

        if len(valid_tests) == 0:
            print("\n\n\n")
            print(f"No valid tests for {project_key}")
            print("\n\n\n")
            continue
        
        df = pd.DataFrame(columns=["Project", "Bug Number", "Package Name", "Testcase Name", "Method Implementation"])
        for test_class, tests in valid_tests.items():
            test_file = repo_path + test_prefix + test_class.replace('.', '/') + '.java'
            tree = get_testfile_tree(test_file)

            for test in tests:
                if '(' in test:
                    test = test.split('(')[0]
                elif '.' in test:
                    test = test.split('.')[-1]
                test_method = get_test_methods(tree, test)
                if test_method is None:
                    # print(f"{project_key}: {test_class}.{test} not found")
                    raise Exception(f"{project_key}: {test_class}.{test} not found")
                test_method_body = _find_method_body(test_method.position, open(test_file).read())
                # Create a new DataFrame for the new row
                new_row_df = pd.DataFrame([{
                    "Project": project,
                    "Bug Number": project_key.rsplit("-", 1)[1],
                    "Package Name": test_class,
                    "Testcase Name": test,
                    "Method Implementation": test_method_body
                }])

                # Concatenate the new row with the existing DataFrame
                df = pd.concat([df, new_row_df], ignore_index=True)

        df.to_csv(f"ground_truth_testcases/{project_key}.csv", index=False)

if __name__ == "__main__":
    main()

