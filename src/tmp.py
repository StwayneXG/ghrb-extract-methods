import json

metadata = json.load(open("data/metadata.json"))

for project_key, project_data in metadata.items():
    valid_tests = project_data["execution_result"]["valid_tests"]
    success_tests = project_data["execution_result"]["success_tests"]

    if len(valid_tests) > 1:
        print(f"{project_key}: {valid_tests} has more than 1 valid test")
    for test in valid_tests:
        if test in success_tests:
            pass
            # print(f"{project_key}: {test} valid and successful")