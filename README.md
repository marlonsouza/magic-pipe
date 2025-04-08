# 🤖 AI-Powered Code Review Tool

> Let your code shine with intelligent, automated reviews! ✨

A powerful code review tool that brings the magic of AI to your pull requests, leveraging OpenAI's language models through MCP (Model Context Protocol) Server integration with GitHub Actions pipelines.

## 🚀 How to Use in Your Project

### 1. Installation

#### Option A: Using GitHub Actions (Recommended)

1. Create a `.github/workflows` directory in your project if it doesn't exist
2. Create a new file `.github/workflows/code-review.yml` with this content:

```yaml
name: Automated Code Review

on:
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  code-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
          ref: ${{ github.event.pull_request.head.sha }}

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install AI Code Reviewer
        run: |
          python -m pip install --upgrade pip
          pip install git+https://github.com/marlonsouza/pipemagic.git

      - name: Run Code Review
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          PR_BASE_SHA: ${{ github.event.pull_request.base.sha }}
          PR_HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          python -m src.github_action 2>&1 | tee code_review_output.txt

      - name: Comment on PR
        uses: peter-evans/create-or-update-comment@v3
        with:
          issue-number: ${{ github.event.pull_request.number }}
          body-file: code_review_output.txt
```

3. Add your OpenAI API key to your repository secrets:
   - Go to your repository Settings > Secrets > Actions
   - Add a new secret named `OPENAI_API_KEY`
   - Paste your OpenAI API key as the value

#### Option B: Local Installation

1. Install the package:
```bash
pip install git+https://github.com/YOUR_USERNAME/pipemagic.git
```

2. Create a `.env` file in your project root:
```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo  # Optional, defaults to gpt-3.5-turbo
```

### 🎯 Features

🧠 **AI-Powered Reviews**
- Intelligent code analysis using OpenAI's GPT models
- Context-aware suggestions
- Best practices recommendations

🔄 **Seamless Integration**
- Works automatically with GitHub Actions
- Real-time PR comments
- Easy setup and configuration

### 💻 Manual Usage

You can also use the code reviewer manually on any Git repository:

```python
from src.reviewers.llm_reviewer import LLMReviewer
import asyncio

async def review_code():
    reviewer = LLMReviewer()
    reviewer.initialize_repo("/path/to/your/repo")
    
    changes = reviewer.get_changed_files()
    reviews = await reviewer.process_changes(changes)
    
    for review in reviews:
        print(f"\nReview for {review['file_path']}:")
        print(review['review'])

if __name__ == "__main__":
    asyncio.run(review_code())
```

### ⚙️ Configuration Options

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model to use for reviews (default: gpt-3.5-turbo)
- `PR_BASE_SHA`: Base commit SHA for PR comparison (optional)
- `PR_HEAD_SHA`: Head commit SHA for PR comparison (optional)

## 🤝 Contributing

We love contributions! Here's how you can help:

1. 🍴 Fork the repository
2. 🌿 Create your feature branch
3. ✨ Make your changes
4. 📝 Write clear commit messages
5. 🚀 Submit a pull request

## 📄 License

MIT License - Feel free to use and modify! 🎉

---
Made with ❤️ by [@marlonsouza](https://github.com/marlonsouza)