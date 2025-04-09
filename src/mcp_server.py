import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from git import Repo
from agents.mcp import MCPServer, MCPMessage, MCPRequest, MCPFunction
from .code_reviewer import CodeReviewer

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

    def initialize_repo(self, repo_path: str):
        """Initialize git repository."""
        self.repo = Repo(repo_path)

    async def handle_completion(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle completion requests."""
        try:
            function_name = request.function_call.name
            params = request.function_call.arguments

            if function_name == "review_code":
                review_result = await self.code_reviewer.review(
                    file_content=params["content"],
                    diff=params.get("diff", ""),
                    custom_prompt=None
                )
                return MCPMessage(role="assistant", content=review_result).to_dict()
            
            elif function_name == "get_file_content":
                if not self.repo:
                    return MCPMessage(
                        role="assistant",
                        content="Error: Repository not initialized"
                    ).to_dict()
                    
                ref = params.get("ref", "HEAD")
                content = self.repo.git.show(f"{ref}:{params['file_path']}")
                return MCPMessage(role="assistant", content=content).to_dict()
            
            elif function_name == "get_file_diff":
                if not self.repo:
                    return MCPMessage(
                        role="assistant",
                        content="Error: Repository not initialized"
                    ).to_dict()
                    
                diff = self.repo.git.diff(
                    params["base_ref"],
                    params["head_ref"],
                    "--",
                    params["file_path"]
                )
                return MCPMessage(role="assistant", content=diff).to_dict()
            
            else:
                return MCPMessage(
                    role="assistant",
                    content=f"Function {function_name} not implemented"
                ).to_dict()

        except Exception as e:
            return MCPMessage(
                role="assistant",
                content=f"Error processing request: {str(e)}"
            ).to_dict()

    async def start(self):
        """Start the MCP server."""
        while True:
            try:
                request = await self.read_request()
                if not request:
                    continue

                response = await self.handle_completion(request)
                await self.write_response(response)

            except Exception as e:
                error_response = MCPMessage(
                    role="assistant",
                    content=f"Server error: {str(e)}"
                ).to_dict()
                await self.write_response(error_response)

if __name__ == "__main__":
    server = CodeReviewMCPServer()
    asyncio.run(server.start())