import json
import subprocess as sp
import javalang

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

def get_test_methods(tree, test_method_name):
    for path, node in tree.filter(javalang.tree.MethodDeclaration):
        if node.name == test_method_name:
            return node
    raise Exception(f"Test method {test_method_name} not found in the test file")


def main():
    for project_key, project_data in metadata.items():
        project = project_key.rsplit("-", 1)[0]
        
        repo_info = config.get(project)
        repo_path = repo_info["repo_path"]

        test_prefix = repo_info["test_prefix"]

        git_reset(repo_path)
        git_clean(repo_path)

        git_checkout(repo_path, project_data["merge_commit"], 'buggy')

        valid_tests = test_data[project_key]

        for test_class, tests in valid_tests.items():
            test_file = repo_path + test_prefix + test_class.replace('.', '/') + '.java'
            tree = get_testfile_tree(test_file)

            for test in tests:
                try:
                    test_method = get_test_methods(tree, test)
                except Exception as e:
                    print(f"Exception: {e}")
                    print(f"{project_key}: {test} not found in {test_file}")
                    continue
                print(f"{project_key}: {test} exists on line {test_method.position[0]}")

if __name__ == "__main__":
    main()

