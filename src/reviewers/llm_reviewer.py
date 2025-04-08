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
        diff_index = self.repo.index.diff(None)
        
        for diff_item in diff_index:
            file_path = diff_item.a_path
            diff = diff_item.diff.decode('utf-8')
            with open(os.path.join(self.repo.working_dir, file_path), 'r') as f:
                content = f.read()
                
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