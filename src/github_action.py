import asyncio
import os
import sys
from .review_manager import ReviewManager

async def main():
    try:
        # Initialize the review manager
        manager = ReviewManager()
        
        # Get the repository path from GitHub Actions workspace
        repo_path = os.getenv('GITHUB_WORKSPACE', '.')
        print(f"Using repository path: {repo_path}", file=sys.stderr)
        
        # Process review and post comments
        success = await manager.process_review(repo_path)
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"⚠️ Error during code review: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())