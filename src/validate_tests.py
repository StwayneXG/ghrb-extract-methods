import json
import subprocess as sp
import os
import re

metadata = json.load(open("data/metadata.json"))
config = json.load(open("data/config.json"))

properties_to_replace = {
    'jackson-core': {
        r'<javac.src.version>\s*1.6\s*</javac.src.version>': '',
        r'<javac.target.version>\s*1.6\s*</javac.target.version>': '',
        r'<maven.compiler.source>\s*1.6\s*</maven.compiler.source>': '<maven.compiler.source>11</maven.compiler.source>',
        r'<maven.compiler.target>\s*1.6\s*</maven.compiler.target>': '<maven.compiler.target>11</maven.compiler.target>',
    },
    'jackson-databind': {
        r'<version>\s*2.13.0-rc1-SNAPSHOT\s*</version>': '<version>2.14.0</version>',
        r'<source>\s*14\s*</source>': '<source>17</source>',
        r'<release>\s*14\s*</release>': '<release>17</release>',
        r'<id>\s*java17\+\s*</id>': '<id>java17+</id>',
        r'<jdk>\s*\[17\,\)\s*</jdk>': '<jdk>[17,)</jdk>'
    }
}

def fix_build_env(repo_dir_path):
    if 'jackson-core' in repo_dir_path or 'jackson-databind' in repo_dir_path:
        pom_file = os.path.join(repo_dir_path, 'pom.xml')

        with open(pom_file, 'r') as f:
            content = f.read()

        if 'jackson-core' in repo_dir_path:
            replace_map = properties_to_replace['jackson-core']
        elif 'jackson-databind' in repo_dir_path:
            replace_map = properties_to_replace['jackson-databind']

        for unsupported_property in replace_map:
            content = re.sub(
                unsupported_property, replace_map[unsupported_property], content)

        with open(pom_file, 'w') as f:
            f.write(content)

def verify_in_buggy_version(buggy_commit, test_patch_dir, repo_path, test_prefix):
    sp.run(['git', 'reset', '--hard', 'HEAD'],
           cwd=repo_path, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    sp.run(['git', 'clean', '-df'],
           cwd=repo_path, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

    # checkout to the buggy version and apply patch to the buggy version
    sp.run(['git', 'checkout', buggy_commit], cwd=repo_path,
           stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    sp.run(['git', 'apply', test_patch_dir], cwd=repo_path,
           stdout=sp.DEVNULL, stderr=sp.DEVNULL)

    p = sp.run(['git', 'status'], cwd=repo_path,
               stdout=sp.PIPE, stderr=sp.PIPE)

    changed_test_files = [p.strip().split()[-1] for p in p.stdout.decode(
        'utf-8').split('\n') if p.strip().endswith('.java')]

    fix_build_env(repo_path)

    changed_test_id = list(map(lambda x: x.split(
        test_prefix)[-1].split('.')[0].replace('/', '.'), changed_test_files))

    valid_tests = {}
    for test_id in changed_test_id:
        print(f"Running test: {test_id}")
        test_process = sp.run(['mvn', 'clean', 'test', '-Denforcer.skip=true',
                              f'-Dtest={test_id}', '-DfailIfNoTests=false'], capture_output=True, cwd=repo_path)

        captured_stdout = test_process.stdout.decode()
        test_output = captured_stdout.split('T E S T S')[-1].strip()

        print(test_output)
        
        tests = []
        for line in test_output.split('\n'):
            if 'ERROR' in line and 'Time elapsed' in line and line.endswith('!'):
                tests.append(line.split(' ')[1])
        
        if 'There are test failures' in captured_stdout:
            valid_tests[test_id] = tests

        # print(f"Tests in {test_id}:")
        # for test in tests:
        #     print(test)

    return valid_tests


def verify_in_fixed_version(fixed_commit, target_test_classes, repo_path, test_prefix):
    sp.run(['git', 'reset', '--hard', 'HEAD'],
           cwd=repo_path, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
    sp.run(['git', 'clean', '-df'],
           cwd=repo_path, stdout=sp.DEVNULL, stderr=sp.DEVNULL)

    sp.run(['git', 'checkout', fixed_commit], cwd=repo_path)

    fix_build_env(repo_path)

    valid_tests = []
    for test_id in target_test_classes.keys():
        test_process = sp.run(['mvn', 'clean', 'test', '-Denforcer.skip=true',
                              f'-Dtest={test_id}', '-DfailIfNoTests=false'], capture_output=True, cwd=repo_path)
        captured_stdout = test_process.stdout.decode()

        if 'BUILD SUCCESS' in captured_stdout:
            valid_tests.append(test_id)

    return valid_tests


def verify_bug(bug_id, buggy_commit, fixed_commit):
    project = bug_id.rsplit('-', 1)[0]

    repo_path = config[project]['repo_path']
    src_dir = config[project]['src_dir']
    test_prefix = config[project]['test_prefix']

    test_patch_dir = os.path.abspath(os.path.join(
        'test_diff', f'{bug_id}.diff'))

    valid_tests = verify_in_buggy_version(
        buggy_commit, test_patch_dir, repo_path, test_prefix)

    success_tests = verify_in_fixed_version(
        fixed_commit, valid_tests, repo_path, test_prefix)
    
    print(f"Valid tests for {bug_id}: {len(valid_tests)}")
    print(valid_tests)
    print(f"Success tests for {bug_id}: {len(success_tests)}")
    print(success_tests)
    return valid_tests, success_tests

# No valid tests for Hakky54_sslcontext-kickstart-167
# No valid tests for Hakky54_sslcontext-kickstart-197
# No valid tests for FasterXML_jackson-databind-3195
# No valid tests for FasterXML_jackson-databind-3418

def main():
    test_data = {}
    for bug_id, bug_data in metadata.items():
        if not bug_id in ['FasterXML_jackson-databind-3418']:
            continue
        print(f"Verifying {bug_id}...")
        valid_tests, success_tests = verify_bug(bug_id, bug_data['buggy_commit'], bug_data['merge_commit'])
        
        tests = {k: v for k, v in valid_tests.items() if k in success_tests}
        test_data[bug_id] = tests

    # with open('data/test_data.json', 'w') as f:
    #     json.dump(test_data, f, indent=4)


if __name__ == "__main__":
    main()