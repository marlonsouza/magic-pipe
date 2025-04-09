import asyncio
import os
import sys
from typing import Optional, List, Dict, Any
from .github_integration import GitHubIntegration
from .code_reviewer import CodeReviewer, debug_log
from .github_action import main as action_main

async def run_code_review(reviewer: CodeReviewer, github: GitHubIntegration) -> bool:
    """Run code review using OpenAI directly."""
    try:
        debug_log("Starting code review process")
        
        # Get files changed in PR
        debug_log("Fetching changed files from PR")
        changed_files = await github.get_pr_files()
        if not changed_files:
            debug_log("No files to review")
            return True

        debug_log(f"Found {len(changed_files)} files to review")
        
        reviews = []
        for file_info in changed_files:
            debug_log(f"Reviewing file: {file_info['filename']}")
            
            # Get file content and diff
            file_content = f"""
File: {file_info['filename']}
Status: {file_info['status']}
Changes: +{file_info['additions']} -{file_info['deletions']}

Diff:
{file_info.get('patch', 'No diff available')}
"""
            # Generate review
            review_result = await reviewer.review(
                file_content=file_content,
                diff=file_info.get('patch', ''),
                custom_prompt=None
            )
            
            # Store the review
            reviews.append({
                'filename': file_info['filename'],
                'review': review_result
            })
            
            debug_log(f"Completed review for {file_info['filename']}")

        # Format and post the review
        debug_log("Formatting review comment")
        review_comment = github.format_review(reviews)
        debug_log("Posting review comment")
        success = await github.post_review_comment(review_comment)
        
        if success:
            debug_log("Successfully posted review comment")
        else:
            debug_log("Failed to post review comment")
            
        return success

    except Exception as e:
        debug_log(f"Error during code review: {str(e)}")
        return False

async def main():
    """Main entry point for the code review system."""
    # Check for required environment variables
    pr_number = os.getenv('PR_NUMBER')
    if not pr_number:
        debug_log("Error: PR_NUMBER environment variable is required")
        sys.exit(1)
        
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        debug_log("Error: GITHUB_TOKEN environment variable is required")
        sys.exit(1)
        
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        debug_log("Error: OPENAI_API_KEY environment variable is required")
        sys.exit(1)
    
    try:
        # For compatibility with the GitHub Action workflow
        use_action = os.getenv('USE_GITHUB_ACTION', 'false').lower() == 'true'
        
        if use_action:
            debug_log("Using GitHub action entry point")
            await action_main()
        else:
            debug_log("Using direct code review flow")
            # Initialize GitHub integration and code reviewer
            github = GitHubIntegration()
            reviewer = CodeReviewer()
            
            # Run the code review process
            success = await run_code_review(reviewer, github)
            
            if not success:
                debug_log("Failed to post review comment")
                sys.exit(1)
    
    except Exception as e:
        debug_log(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())