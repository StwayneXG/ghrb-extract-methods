import json
import subprocess as sp

metadata = json.load(open("data/metadata.json"))
config = json.load(open("data/config.json"))

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
    
def main():
    for project_key, project_data in metadata.items():
        project = project_key.rsplit("-", 1)[0]
        
        repo_info = config.get(project)
        repo_path = repo_info["repo_path"]

        test_prefix = repo_info["test_prefix"]

        git_reset(repo_path)
        git_clean(repo_path)

        git_checkout(repo_path, project_data["buggy_commit"], 'buggy')

        valid_tests = project_data["execution_result"]["valid_tests"]
        success_tests = project_data["execution_result"]["success_tests"]

        for test in valid_tests:
            test_process = sp.run(['mvn', 'clean', 'test', '-Denforcer.skip=true',
                                  f'-Dtest={test}', '-DfailIfNoTests=false'], capture_output=True, cwd=repo_path)
            
            captured_stdout = test_process.stdout.decode()
            if 'There are test failures' in captured_stdout:
                print(f"{project_key}: {test} is not a valid test")
            else:
                print(f"{project_key}: {test} is a valid test")

if __name__ == "__main__":
    main()