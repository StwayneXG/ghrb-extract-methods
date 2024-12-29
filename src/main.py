import json
import os
from git_utils import get_full_file_diff, save_diff_to_file

# Paths
METADATA_PATH = "data/metadata.json"
CONFIG_PATH = "data/config.json"

def load_metadata(path):
    """Load metadata JSON."""
    with open(path, 'r') as file:
        return json.load(file)

def main():
    # Load metadata and config
    metadata = load_metadata(METADATA_PATH)
    config = load_metadata(CONFIG_PATH)
    
    for project_key, project_data in metadata.items():
        project_id = project_key.rsplit("-", 1)[0]
        repo_info = config.get(project_id)
        if not repo_info:
            print(f"Config not found for project {project_id}. Skipping...")
            continue
        
        # Get repo details
        repo_path = repo_info['repo_path']
        test_prefix = repo_info["test_prefix"]
        buggy_commit = project_data["buggy_commit"]
        fixed_commit = project_data["merge_commit"]
        
        # Get diff
        try:
            full_diff = get_full_file_diff(repo_path, buggy_commit, fixed_commit, test_prefix)

            # Save diff to individual file
            output_dir = 'output/full_diffs'
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{project_key}_java_diff.txt")
            save_diff_to_file(full_diff, output_file)

            print(f"Full file content unified .java diff saved for {project_key} at {output_file}")
        except Exception as e:
            print(f"Error processing {project_key}: {e}")
        break

if __name__ == "__main__":
    main()