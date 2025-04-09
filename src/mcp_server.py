import asyncio
import json
import os
import sys
from typing import Dict, Any, List, Optional
from git import Repo
from openai_agents import MCPServer, MCPMessage, MCPRequest, MCPFunction
from .code_reviewer import CodeReviewer, debug_log

class CodeReviewMCPServer(MCPServer):
    def __init__(self):
        super().__init__()
        self.code_reviewer = CodeReviewer()
        self.repo = None
        
        # Register available functions
        self.register_functions([
            MCPFunction(
                name="review_code",
                description="Review code changes in a pull request or repository",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file to review"},
                        "diff": {"type": "string", "description": "Git diff of the changes"},
                        "content": {"type": "string", "description": "Current content of the file"}
                    },
                    "required": ["file_path", "content"]
                }
            ),
            MCPFunction(
                name="get_file_content",
                description="Get the content of a file from the repository",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file"},
                        "ref": {"type": "string", "description": "Git reference (commit, branch, etc)"}
                    },
                    "required": ["file_path"]
                }
            ),
            MCPFunction(
                name="get_file_diff",
                description="Get the diff of a file between two commits",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Path to the file"},
                        "base_ref": {"type": "string", "description": "Base commit reference"},
                        "head_ref": {"type": "string", "description": "Head commit reference"}
                    },
                    "required": ["file_path", "base_ref", "head_ref"]
                }
            )
        ])
        debug_log("MCP Server initialized with functions")

    def initialize_repo(self, repo_path: str):
        """Initialize git repository."""
        debug_log(f"Initializing repository at {repo_path}")
        self.repo = Repo(repo_path)

    async def handle_completion(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle completion requests."""
        try:
            function_name = request.function_call.name
            params = request.function_call.arguments
            debug_log(f"Handling function call: {function_name}")

            if function_name == "review_code":
                debug_log(f"Reviewing code for file: {params['file_path']}")
                review_result = await self.code_reviewer.review(
                    file_content=params["content"],
                    diff=params.get("diff", ""),
                    custom_prompt=None
                )
                return MCPMessage(role="assistant", content=review_result).to_dict()
            
            elif function_name == "get_file_content":
                if not self.repo:
                    debug_log("Error: Repository not initialized")
                    return MCPMessage(
                        role="assistant",
                        content="Error: Repository not initialized"
                    ).to_dict()
                    
                ref = params.get("ref", "HEAD")
                debug_log(f"Getting file content: {params['file_path']} at {ref}")
                content = self.repo.git.show(f"{ref}:{params['file_path']}")
                return MCPMessage(role="assistant", content=content).to_dict()
            
            elif function_name == "get_file_diff":
                if not self.repo:
                    debug_log("Error: Repository not initialized")
                    return MCPMessage(
                        role="assistant",
                        content="Error: Repository not initialized"
                    ).to_dict()
                    
                debug_log(f"Getting diff for {params['file_path']} between {params['base_ref']} and {params['head_ref']}")
                diff = self.repo.git.diff(
                    params["base_ref"],
                    params["head_ref"],
                    "--",
                    params["file_path"]
                )
                return MCPMessage(role="assistant", content=diff).to_dict()
            
            else:
                debug_log(f"Function {function_name} not implemented")
                return MCPMessage(
                    role="assistant",
                    content=f"Function {function_name} not implemented"
                ).to_dict()

        except Exception as e:
            debug_log(f"Error processing request: {str(e)}")
            return MCPMessage(
                role="assistant",
                content=f"Error processing request: {str(e)}"
            ).to_dict()

    async def start(self):
        """Start the MCP server."""
        debug_log("Starting MCP server")
        while True:
            try:
                debug_log("Waiting for request...")
                request = await self.read_request()
                if not request:
                    debug_log("Empty request received, continuing")
                    continue

                debug_log("Processing request")
                response = await self.handle_completion(request)
                debug_log("Sending response")
                await self.write_response(response)

            except Exception as e:
                debug_log(f"Server error: {str(e)}")
                error_response = MCPMessage(
                    role="assistant",
                    content=f"Server error: {str(e)}"
                ).to_dict()
                await self.write_response(error_response)

async def run_mcp_server():
    """Run the MCP server with proper error handling."""
    try:
        debug_log("Initializing CodeReviewMCPServer")
        server = CodeReviewMCPServer()
        
        repo_path = os.getenv('GITHUB_WORKSPACE', '.')
        debug_log(f"Using repository path: {repo_path}")
        
        server.initialize_repo(repo_path)
        debug_log("Repository initialized, starting server")
        
        await server.start()
    except Exception as e:
        debug_log(f"Fatal error in MCP server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_mcp_server())