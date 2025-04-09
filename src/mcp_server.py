import asyncio
import sys
from typing import Dict, Any, List, Optional
import json
import os
from .code_reviewer import CodeReviewer

class MCPMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self):
        return {"role": self.role, "content": self.content}

class CodeReviewMCPServer:
    def __init__(self):
        self.code_reviewer = CodeReviewer()

    def _create_review_prompt(self, file_content: str, diff: str, file_path: str = "") -> str:
        file_type = os.path.splitext(file_path)[1] if file_path else "unknown"
        
        base_prompt = f"""Please review the following {'changes to the ' + file_path if file_path else 'code'}:

File type: {file_type}

"""
        if diff:
            base_prompt += f"""Changes:
```
{diff}
```

Full file context:
```
{file_content}
```
"""
        else:
            base_prompt += f"""Full content:
```
{file_content}
```
"""

        base_prompt += """
Please provide:
1. A concise summary of the changes/code
2. Potential issues, bugs, or security concerns
3. Suggestions for improvement
4. Best practices applicable to this code
"""

        return base_prompt

    async def handle_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Extract file content and diff from context
            context = request.get('context', {})
            file_content = context.get('file_content', '')
            diff = context.get('diff', '')
            file_path = context.get('file_path', '')
            
            # Create a review prompt specific to the file type
            prompt = self._create_review_prompt(file_content, diff, file_path)
            
            # Get the code review
            review_result = await self.code_reviewer.review(file_content, diff, prompt)
            
            # Create response message
            message = MCPMessage(role="assistant", content=review_result)
            
            # Return completion response
            return {
                "messages": [message.to_dict()]
            }
            
        except Exception as e:
            # Handle errors properly
            error_message = MCPMessage(
                role="assistant",
                content=f"⚠️ Error performing code review: {str(e)}"
            )
            return {"messages": [error_message.to_dict()]}

    async def _read_request(self) -> str:
        request_str = ""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    return ""
                request_str += line
                if line.strip() == "":
                    return request_str.strip()
            except Exception as e:
                print(f"Error reading request: {str(e)}", file=sys.stderr)
                return ""

    async def _write_response(self, response: Dict[str, Any]):
        try:
            response_str = json.dumps(response)
            print(response_str)
            print("")  # Empty line to signal end of response
            sys.stdout.flush()
        except Exception as e:
            print(f"Error writing response: {str(e)}", file=sys.stderr)

    async def run(self):
        """Run the MCP server"""
        try:
            while True:
                request_str = await self._read_request()
                if not request_str:
                    continue

                try:
                    request = json.loads(request_str)
                    if request.get('type') == 'completion':
                        response = await self.handle_completion(request)
                        await self._write_response(response)
                    else:
                        await self._write_response({"error": "Unsupported request type"})
                except json.JSONDecodeError as e:
                    await self._write_response({"error": f"Invalid JSON request: {str(e)}"})
                except Exception as e:
                    await self._write_response({"error": f"Error processing request: {str(e)}"})

        except Exception as e:
            print(f"Server error: {str(e)}", file=sys.stderr)
            raise

if __name__ == "__main__":
    server = CodeReviewMCPServer()
    asyncio.run(server.run())