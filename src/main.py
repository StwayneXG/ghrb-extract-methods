import json
import os
from src.git_utils import get_repo, get_diff_between_commits

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
        repo = get_repo(repo_path)
        
        # Fetch commits
        buggy_commit = project_data["buggy_commit"]
        merge_commit = project_data["merge_commit"]
        
        # Get diff
        try:
            diff = get_diff_between_commits(repo, buggy_commit, merge_commit)
            output_dir = "output/diffs"
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{project_key}_diff.txt")
            
            with open(output_file, 'w') as file:
                file.write('\n'.join(str(patch) for patch in diff))
            print(f"Diff saved for {project_key} at {output_file}")
        except Exception as e:
            print(f"Error processing {project_key}: {e}")

if __name__ == "__main__":
    main()
