import asyncio
import os
from src.reviewers.llm_reviewer import LLMReviewer
from git import Repo

async def main():
    # Initialize the reviewer
    reviewer = LLMReviewer()
    
    # Get the repository path from GitHub Actions workspace
    repo_path = os.getenv('GITHUB_WORKSPACE', '.')
    reviewer.initialize_repo(repo_path)
    
    # Get changed files
    changes = reviewer.get_changed_files()
    
    # Process changes and generate reviews
    reviews = await reviewer.process_changes(changes)
    
    # Print reviews in a format suitable for GitHub Actions
    for review in reviews:
        print(f"\n## Code Review for {review['file_path']}\n")
        print(review['review'])
        print("\n---\n")

if __name__ == "__main__":
    asyncio.run(main())