from typing import Dict, List
from git import Repo
import os

class LLMReviewer:
    def __init__(self):
        self.repo = None
        
    def initialize_repo(self, repo_path: str):
        """Initialize the Git repository."""
        self.repo = Repo(repo_path)
        
    def get_changed_files(self) -> List[Dict[str, str]]:
        """Get list of changed files with their diffs."""
        if not self.repo:
            raise ValueError("Repository not initialized")
            
        changes = []
        
        # Get PR specific SHAs if available
        base_sha = os.getenv('PR_BASE_SHA')
        head_sha = os.getenv('PR_HEAD_SHA')
        
        if base_sha and head_sha:
            # We're in a PR context
            diff_index = self.repo.commit(head_sha).diff(base_sha)
        else:
            # Local development context
            diff_index = self.repo.index.diff(None)
            
        for diff_item in diff_index:
            file_path = diff_item.a_path or diff_item.b_path
            
            # Handle the diff content properly
            if isinstance(diff_item.diff, bytes):
                diff = diff_item.diff.decode('utf-8')
            else:
                diff = str(diff_item.diff)
            
            try:
                # Try to read the current content of the file
                with open(os.path.join(self.repo.working_dir, file_path), 'r') as f:
                    content = f.read()
            except (FileNotFoundError, IOError):
                # File might have been deleted in the PR
                content = ""
                
            # Skip if both content and diff are empty
            if not content and not diff:
                continue
                
            changes.append({
                'file_path': file_path,
                'content': content,
                'diff': diff
            })
            
        return changes
        
    async def process_changes(self, changes: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Process each changed file and generate review comments."""
        from ..code_reviewer import CodeReviewer
        
        reviewer = CodeReviewer()
        results = []
        
        for change in changes:
            review = await reviewer.review(
                file_content=change['content'],
                diff=change['diff']
            )
            
            results.append({
                'file_path': change['file_path'],
                'review': review
            })
            
        return results