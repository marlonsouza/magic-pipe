# Code Review LLM Tool

An automated code review tool that uses LLM (Language Learning Models) integrated with MCP (Model Context Protocol) Server for GitHub Actions pipelines.

## Features

- Automated code review using OpenAI's GPT-4
- Integration with GitHub Actions for pull request reviews
- Support for diff-based code analysis
- MCP Server implementation for extensibility

## Setup

1. Clone the repository
2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## GitHub Actions Integration

1. Add your OpenAI API key as a repository secret named `OPENAI_API_KEY`
2. The workflow will automatically run on pull requests
3. The code review comments will be posted as pull request comments

## Local Development

To run the MCP server locally:

```bash
python -m src.mcp_server
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License