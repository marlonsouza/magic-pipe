import asyncio
import json
import sys
from typing import Dict, Any
from .code_reviewer import CodeReviewer

class MCPServer:
    def __init__(self):
        self.code_reviewer = CodeReviewer()

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        if request.get('type') == 'completion':
            messages = request.get('messages', [])
            context = request.get('context', {})
            file_content = context.get('file_content', '')
            diff = context.get('diff', '')
            
            review_result = await self.code_reviewer.review(file_content, diff)
            
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": review_result
                    }
                }]
            }
        return {"error": "Unsupported request type"}

    async def run(self):
        while True:
            try:
                request_str = await self._read_request()
                if not request_str:
                    continue
                    
                request = json.loads(request_str)
                response = await self.handle_request(request)
                
                await self._write_response(response)
            except Exception as e:
                await self._write_response({"error": str(e)})

    async def _read_request(self) -> str:
        request_str = ""
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                return ""
            request_str += line
            if line.strip() == "":
                return request_str.strip()

    async def _write_response(self, response: Dict[str, Any]):
        response_str = json.dumps(response)
        print(response_str)
        print("")  # Empty line to signal end of response
        sys.stdout.flush()

if __name__ == "__main__":
    server = MCPServer()
    asyncio.run(server.run())