import os
import aiohttp
from typing import Optional, Dict, Any

class GitHubIntegration:
    def __init__(self):
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

    async def get_pr_files(self) -> list:
        """Get list of files changed in the PR."""
        if not all([self.github_token, self.repo_owner, self.repo_name, self.pr_number]):
            return []

        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls/{self.pr_number}/files"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    files = await response.json()
                    return [
                        {
                            'filename': file['filename'],
                            'status': file['status'],
                            'additions': file['additions'],
                            'deletions': file['deletions'],
                            'changes': file['changes'],
                            'patch': file.get('patch', '')
                        }
                        for file in files
                    ]
                return []

    @staticmethod
    def format_review_comment(reviews: Dict[str, Any]) -> str:
        """Format the review results into a markdown comment."""
        comment = [
            "# 🎉 Code Review Mágico\n",
            "## ✨ Análise do Código\n",
            "Olá! Analisei as alterações e tenho alguns feedbacks construtivos para compartilhar!\n"
        ]

        for file_review in reviews.get('file_reviews', []):
            comment.extend([
                f"\n### 📝 `{file_review['filename']}`\n",
                f"{file_review['review']}\n",
                "---\n"
            ])

        comment.extend([
            "\n## ℹ️ Informações Adicionais\n",
            "> 🤖 **Sobre esta Análise**\n",
            "> - Esta revisão foi gerada automaticamente usando IA\n",
            "> - Cada arquivo foi analisado considerando:\n",
            ">   - ✨ Qualidade e boas práticas\n",
            ">   - 🛡️ Segurança e potenciais bugs\n",
            ">   - 📚 Documentação e manutenibilidade\n",
            ">   - 🎯 Padrões específicos da linguagem\n\n",
            "> 💡 **Dúvidas ou Sugestões?**\n",
            "> - Precisa de esclarecimentos? Comente abaixo!\n",
            "> - Quer um foco específico? Me avise!\n",
            "> - Estou aqui para ajudar! 😊\n\n",
            "---\n",
            "✨ *Gerado com ❤️ pelo seu assistente de código favorito* 🤖✨"
        ])

        return "\n".join(comment)