import os
from git import Repo
from typing import List, Dict
from ..code_reviewer import CodeReviewer, debug_log

class LLMReviewer:
    def __init__(self):
        self.code_reviewer = CodeReviewer()
        self.repo = None

    def initialize_repo(self, repo_path: str):
        """Initialize the git repository for review."""
        debug_log(f"Initializing repository at {repo_path}")
        self.repo = Repo(repo_path)

    def get_changed_files(self) -> List[str]:
        """Get list of changed files in the repository."""
        if not self.repo:
            debug_log("Error: Repository not initialized")
            return []

        try:
            # Get base and head SHAs from environment
            base_sha = os.getenv('PR_BASE_SHA')
            head_sha = os.getenv('PR_HEAD_SHA')

            debug_log(f"Getting changes between {base_sha} and {head_sha}")
            
            if not base_sha or not head_sha:
                debug_log("Warning: PR_BASE_SHA or PR_HEAD_SHA not set")
                return []

            # Get the diff between base and head
            diff_index = self.repo.commit(head_sha).diff(base_sha)
            
            # Return list of changed file paths
            changed_files = [diff.a_path for diff in diff_index]
            debug_log(f"Found {len(changed_files)} changed files")
            return changed_files

        except Exception as e:
            debug_log(f"Error getting changed files: {str(e)}")
            return []

    async def process_changes(self, files: List[str]) -> List[Dict[str, str]]:
        """Process each changed file and generate reviews."""
        if not self.repo:
            debug_log("Error: Repository not initialized")
            return []

        reviews = []
        base_sha = os.getenv('PR_BASE_SHA')
        head_sha = os.getenv('PR_HEAD_SHA')

        for file_path in files:
            try:
                debug_log(f"Processing file: {file_path}")
                
                # Get current content
                head_content = self.repo.git.show(f"{head_sha}:{file_path}")
                
                # Get diff
                try:
                    diff = self.repo.git.diff(base_sha, head_sha, "--", file_path)
                except:
                    diff = ""
                    debug_log(f"Could not get diff for {file_path}")

                # Generate review
                debug_log(f"Generating review for {file_path}")
                review = await self.code_reviewer.review(head_content, diff, file_path)
                
                # Only add the review if there's actual content
                if review.strip():
                    reviews.append({
                        "file_path": file_path,
                        "review": review
                    })
                debug_log(f"Completed review for {file_path}")

            except Exception as e:
                debug_log(f"Error processing {file_path}: {str(e)}")
                reviews.append({
                    "file_path": file_path,
                    "review": f"⚠️ Error reviewing file: {str(e)}"
                })

        return reviews