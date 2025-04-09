import asyncio
import os
import sys
from .review_manager import ReviewManager
from .code_reviewer import debug_log

# Import MCP server only when needed to avoid dependency issues
async def run_mcp_server_wrapper():
    from .mcp_server import run_mcp_server
    await run_mcp_server()

async def main():
    try:
        # Check if we're using MCP or traditional mode
        use_mcp = os.getenv('USE_MCP', 'false').lower() == 'true'
        
        if use_mcp:
            debug_log("Starting in MCP server mode")
            await run_mcp_server_wrapper()
        else:
            debug_log("Starting in traditional GitHub action mode")
            # Initialize the review manager
            manager = ReviewManager()
            
            # Get the repository path from GitHub Actions workspace
            repo_path = os.getenv('GITHUB_WORKSPACE', '.')
            debug_log(f"Using repository path: {repo_path}")
            
            # Process review and post comments
            success = await manager.process_review(repo_path)
            
            if not success:
                debug_log("Review process failed")
                sys.exit(1)
            else:
                debug_log("Review process completed successfully")
            
    except Exception as e:
        debug_log(f"⚠️ Error during code review: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())