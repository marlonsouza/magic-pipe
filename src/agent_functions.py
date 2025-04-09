from typing import Dict, Any
from openai_agents import AgentFunction

review_code = AgentFunction(
    name="review_code",
    description="Review code changes and provide constructive feedback",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file being reviewed"
            },
            "content": {
                "type": "string",
                "description": "Current content of the file"
            },
            "changes": {
                "type": "string",
                "description": "Summary of changes (additions/deletions)"
            },
            "diff": {
                "type": "string",
                "description": "Git diff of the changes"
            }
        },
        "required": ["file_path", "content"]
    }
)

get_file_changes = AgentFunction(
    name="get_file_changes",
    description="Get information about changes in a file",
    parameters={
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file"
            }
        },
        "required": ["file_path"]
    }
)

format_review = AgentFunction(
    name="format_review",
    description="Format a code review into a friendly, markdown-formatted comment",
    parameters={
        "type": "object",
        "properties": {
            "reviews": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "review": {"type": "string"}
                    }
                },
                "description": "List of file reviews"
            }
        },
        "required": ["reviews"]
    }
)