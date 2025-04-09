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
        # Get detailed mode from environment variable (default to false)
        detailed_reviews = os.getenv('DETAILED_REVIEWS', 'false').lower() == 'true'
        
        sections = [
            "# 🎉 Revisão de Código\n",
            f"Analisei {len(reviews)} arquivo(s) neste PR. Aqui está o resumo das principais observações:\n"
        ]

        # Add summary of key findings
        summary_points = []
        
        # Process each file and collect key points
        for review in reviews:
            file_name = review['filename'].split('/')[-1]  # Get just the filename without path
            
            if detailed_reviews:
                # Add full detailed review for each file
                sections.extend([
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
            sections.append("## 📝 Resumo por Arquivo\n")
            for point in summary_points:
                sections.append(f"- {point}\n")
        
        # Extract specific recommendations from reviews
        key_recommendations = []
        for review in reviews:
            file_path = review['filename']
            review_text = review['review']
            
            # Skip empty reviews
            if not review_text.strip():
                continue
                
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
        
        sections.append("## 💡 Principais Recomendações\n")
        
        if key_recommendations:
            for rec in key_recommendations[:5]:  # Limit to top 5 recommendations
                sections.append(f"- {rec}\n")
        else:
            sections.extend([
                "- Mantenha a consistência nos padrões de código\n",
                "- Adicione testes para novas funcionalidades\n",
                "- Verifique tratamento de erros e casos extremos\n",
                "- Documente interfaces públicas e APIs importantes\n"
            ])
        
        sections.extend([
            "\n---\n",
            "✨ *Análise gerada automaticamente. Para revisão detalhada de um arquivo específico, mencione-o nos comentários.* ✨"
        ])

        return "\n".join(sections)