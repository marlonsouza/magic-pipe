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
        """Format the review results into a concise markdown report."""
        # Get detailed mode from environment variable (default to false)
        detailed_reviews = os.getenv('DETAILED_REVIEWS', 'false').lower() == 'true'
        
        report = [
            "# 🎉 Code Review\n",
            f"Analisei {total_files} arquivo(s) neste PR. Aqui está o resumo das principais observações:\n"
        ]

        # Add summary of key findings
        summary_points = []
        
        # Process each file and collect key points
        for review in reviews:
            file_name = review['file_path'].split('/')[-1]  # Get just the filename without path
            
            if detailed_reviews:
                # Add full detailed review for each file
                report.extend([
                    f"## 🔍 `{file_name}`\n",
                    f"{review['review']}\n",
                    "---\n"
                ])
            else:
                # Extract the first paragraph or sentence from each review as a summary
                review_text = review['review']
                first_para = review_text.split('\n\n')[0] if '\n\n' in review_text else review_text
                
                # If still too long, take just the first sentence
                if len(first_para) > 200:
                    first_sentence = first_para.split('. ')[0]
                    summary_points.append(f"**`{file_name}`**: {first_sentence}.")
                else:
                    summary_points.append(f"**`{file_name}`**: {first_para}")
        
        # If using summary mode, add the points to the report
        if not detailed_reviews:
            report.append("## 📝 Resumo por Arquivo\n")
            for point in summary_points:
                report.append(f"- {point}\n")
        
        report.extend([
            "## 💡 Principais Recomendações\n",
            "- Mantenha a consistência dos padrões de código usados no projeto\n",
            "- Considere adicionar testes para as novas funcionalidades\n",
            "- Documente interfaces públicas e APIs\n",
            "- Verifique tratamento de erros e casos extremos\n",
            "\n---\n",
            "✨ *Análise gerada automaticamente. Para revisão detalhada de um arquivo específico, mencione-o nos comentários.* ✨"
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