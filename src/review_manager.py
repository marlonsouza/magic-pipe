import os
import json
import asyncio
from typing import List, Dict, Optional
import aiohttp
from .reviewers.llm_reviewer import LLMReviewer

class ReviewManager:
    def __init__(self):
        self.reviewer = LLMReviewer()
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('GITHUB_REPOSITORY', '').split('/')[0]
        self.repo_name = os.getenv('GITHUB_REPOSITORY', '').split('/')[-1]
        self.pr_number = os.getenv('PR_NUMBER')

    async def post_review_comment(self, content: str) -> bool:
        """Post a review comment on the PR using GitHub API."""
        if not all([self.github_token, self.repo_owner, self.repo_name, self.pr_number]):
            print("Missing required GitHub environment variables")
            return False

        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{self.pr_number}/comments"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"body": content}, headers=headers) as response:
                return response.status == 201

    def format_review_report(self, reviews: List[Dict[str, str]], total_files: int) -> str:
        """Format the review results into a markdown report."""
        report = [
            "# 🎉 Code Review Mágico\n",
            "## ✨ Visão Geral\n",
            f"Olá! Eu analisei {total_files} arquivo(s) neste PR e tenho alguns feedbacks construtivos para compartilhar!\n",
            "## 📝 Análise dos Arquivos\n"
        ]

        for review in reviews:
            report.extend([
                f"### 🔍 `{review['file_path']}`\n",
                f"{review['review']}\n",
                "---\n"
            ])

        report.extend([
            "## ℹ️ Informações Adicionais\n",
            "> 🤖 **Sobre esta Análise**\n",
            "> - Esta revisão foi gerada automaticamente usando análise de IA\n",
            "> - Cada arquivo foi analisado considerando:\n",
            ">   - ✨ Qualidade e boas práticas de código\n",
            ">   - 🛡️ Potenciais bugs e questões de segurança\n",
            ">   - 📚 Documentação e manutenibilidade\n",
            ">   - 🎯 Considerações específicas da linguagem\n\n",
            "> 💡 **Dúvidas ou Sugestões?**\n",
            "> - Precisa de esclarecimentos? Comente abaixo!\n",
            "> - Quer um foco específico? Me avise na resposta\n",
            "> - Continuarei monitorando este PR para atualizações\n\n",
            "---\n",
            "✨ *Gerado com ❤️ pelo seu assistente de código favorito* 🤖✨"
        ])

        return "\n".join(report)

    async def process_review(self, repo_path: str) -> bool:
        """Process the code review and post results."""
        try:
            # Initialize the repository
            self.reviewer.initialize_repo(repo_path)

            # Get changed files
            changed_files = self.reviewer.get_changed_files()
            if not changed_files:
                print("No files to review")
                return True

            # Process changes
            reviews = await self.reviewer.process_changes(changed_files)
            
            # Format and post review
            report = self.format_review_report(reviews, len(changed_files))
            success = await self.post_review_comment(report)
            
            return success

        except Exception as e:
            print(f"Error during review process: {str(e)}")
            return False