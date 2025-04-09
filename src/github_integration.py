import os
import aiohttp
from typing import List, Dict, Any

class GitHubIntegration:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('GITHUB_REPOSITORY', '').split('/')[0]
        self.repo_name = os.getenv('GITHUB_REPOSITORY', '').split('/')[-1]
        self.pr_number = os.getenv('PR_NUMBER')
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    @property
    def is_configured(self) -> bool:
        """Check if all required GitHub environment variables are set."""
        return all([
            self.github_token,
            self.repo_owner,
            self.repo_name,
            self.pr_number
        ])

    async def post_review_comment(self, content: str) -> bool:
        """Post a review comment on the PR."""
        if not self.is_configured:
            print("Missing required GitHub environment variables")
            return False

        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/issues/{self.pr_number}/comments"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"body": content}, headers=self.headers) as response:
                return response.status == 201

    async def get_pr_files(self) -> List[Dict[str, Any]]:
        """Get list of files changed in the PR."""
        if not self.is_configured:
            return []

        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls/{self.pr_number}/files"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
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

    def format_review(self, reviews: List[Dict[str, Any]]) -> str:
        """Format the review results into a markdown comment."""
        sections = [
            "# 🎉 Code Review Mágico\n",
            "## ✨ Análise do Código\n",
            f"Olá! Analisei {len(reviews)} arquivo(s) e tenho alguns feedbacks construtivos para compartilhar!\n"
        ]

        for review in reviews:
            sections.extend([
                f"\n### 📝 `{review['filename']}`\n",
                f"{review['review']}\n",
                "---\n"
            ])

        sections.extend([
            "\n## ℹ️ Informações Adicionais\n",
            "> 🤖 **Sobre esta Análise**\n",
            "> - Esta revisão foi gerada usando IA com foco em ajudar você\n",
            "> - Analisei cada arquivo considerando:\n",
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

        return "\n".join(sections)