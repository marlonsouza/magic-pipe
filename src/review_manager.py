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
            "# 🎉 Revisão de Código\n",
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
        
        # Extract specific recommendations from reviews
        key_recommendations = []
        for review in reviews:
            file_path = review['file_path']
            review_text = review['review']
            
            # Split by lines to find recommendations
            lines = review_text.split('\n')
            for line in lines:
                # Look for lines that mention line numbers and contain suggestions
                if ('linha' in line.lower() or 'line' in line.lower() or 
                    any(str(i) in line for i in range(1, 1000)) and  # Has numbers 1-999
                    ('sugiro' in line.lower() or 'recomendo' in line.lower() or 
                     'considere' in line.lower() or 'deveria' in line.lower() or
                     'poderia' in line.lower() or 'melhor' in line.lower() or
                     'issue' in line.lower() or 'problema' in line.lower() or
                     'should' in line.lower() or 'could' in line.lower() or
                     'consider' in line.lower() or 'recommend' in line.lower())):
                    # Format: filename:recommendation
                    file_name = file_path.split('/')[-1]  # Just the filename without path
                    key_recommendations.append(f"**{file_name}**: {line.strip()}")
        
        report.append("## 💡 Principais Recomendações\n")
        
        if key_recommendations:
            for rec in key_recommendations[:5]:  # Limit to top 5 recommendations
                report.append(f"- {rec}\n")
        else:
            report.extend([
                "- Mantenha a consistência dos padrões de código no projeto\n",
                "- Considere adicionar testes para novas funcionalidades\n",
                "- Verifique tratamento de erros e casos extremos\n",
                "- Documente interfaces públicas e APIs importantes\n"
            ])
        
        report.extend([
            "\n---\n",
            "✨ *Análise gerada automaticamente. Para revisão detalhada de um arquivo específico, mencione-o nos comentários.* ✨"
        ])

        return "\n".join(report)

    async def process_review(self, repo_path: str) -> dict:
        """Process the code review and post results.
        
        Returns a dictionary with:
            - success: Boolean indicating if the operation succeeded
            - review_text: The formatted review text (if generated)
        """
        try:
            # Initialize the repository
            self.reviewer.initialize_repo(repo_path)

            # Get changed files
            changed_files = self.reviewer.get_changed_files()
            if not changed_files:
                return {
                    "success": True,
                    "review_text": "# 🎉 Revisão de Código\n\nNenhum arquivo para revisar neste PR."
                }

            # Process changes
            reviews = await self.reviewer.process_changes(changed_files)
            
            # Format review
            report = self.format_review_report(reviews, len(changed_files))
            
            # Post review (if GITHUB_TOKEN is set)
            success = True
            if self.github_token:
                success = await self.post_review_comment(report)
            
            return {
                "success": success,
                "review_text": report
            }

        except Exception as e:
            error_msg = f"Error during review process: {str(e)}"
            print(error_msg)
            return {
                "success": False,
                "review_text": f"# ⚠️ Erro na Revisão\n\nOcorreu um erro durante o processo de revisão: {error_msg}"
            }