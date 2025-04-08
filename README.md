# 🤖 AI-Powered Code Review Tool

> Let your code shine with intelligent, automated reviews! ✨

A powerful code review tool that brings the magic of AI to your pull requests, leveraging OpenAI's language models through MCP (Model Context Protocol) Server integration with GitHub Actions pipelines.

## ⭐ Key Features

🧠 **AI-Powered Reviews**
- Intelligent code analysis using OpenAI's GPT models
- Context-aware suggestions
- Best practices recommendations

🔄 **Seamless Integration**
- Works automatically with GitHub Actions
- Real-time PR comments
- Easy setup and configuration

🎯 **Smart Analysis**
- Diff-based code review
- Security vulnerability checks
- Code style recommendations
- Performance insights

🛠️ **Developer Friendly**
- Extensible MCP Server architecture
- Customizable review rules
- Local development support

## 🚀 Quick Start

### 1. Clone & Setup

```bash
# Clone the repository
git clone <your-repo-url>

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Linux/Mac
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_api_key_here
```

## 🔗 GitHub Actions Integration

1. 🔐 Add your OpenAI API key as a repository secret
   - Repository Settings > Secrets > Actions
   - Create new secret: `OPENAI_API_KEY`

2. ✨ That's it! The magic happens automatically:
   - Runs on every pull request
   - Posts review comments directly to PR
   - Helps improve code quality

## 💻 Local Development

Run the MCP server locally for testing:

```bash
python -m src.mcp_server
```

## 🤝 Contributing

We love contributions! Here's how you can help:

1. 🍴 Fork the repository
2. 🌿 Create your feature branch
3. ✨ Make your changes
4. 📝 Write clear commit messages
5. 🚀 Submit a pull request

## 📄 License

MIT License - Feel free to use and modify! 🎉

## 🙏 Acknowledgments

Special thanks to:
- OpenAI for their amazing LLM models
- The amazing open-source community
- All our contributors

---
Made with ❤️ by [@marlonsouza](https://github.com/marlonsouza)