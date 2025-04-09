import asyncio
import os
import sys
from typing import Optional

try:
    from agents import Agent, Runner, trace
    from agents.mcp import MCPServer
except ImportError:
    print("""
Error: Required MCP agent packages not found. 
Please make sure you have the correct agent packages installed.
You might need to install them from a specific source or contact the package maintainer.
    """)
    sys.exit(1)

from .mcp_server import CodeReviewMCPServer
from .github_integration import GitHubIntegration

async def run_code_review(mcp_server: MCPServer, github: GitHubIntegration) -> bool:
    """Run code review using MCP server and agents."""
    repo_path = os.getenv('GITHUB_WORKSPACE', '.')
    
    # Configure the agent with specific instructions for code review
    agent = Agent(
        name="CodeReviewAssistant",
        instructions=f"""Você é um assistente amigável e especialista em revisão de código. 
Sua missão é revisar o código no repositório em {repo_path} de forma construtiva e encorajadora.

Ao revisar o código:
- Comece destacando os pontos fortes e boas práticas já aplicadas
- Faça sugestões de forma construtiva e positiva
- Use emojis para tornar o feedback mais amigável e fácil de ler
- Sugira melhorias específicas com exemplos quando relevante
- Mantenha um tom encorajador e colaborativo

Para cada arquivo:
1. Analise o contexto e as mudanças
2. Identifique padrões e boas práticas
3. Sugira melhorias de forma construtiva
4. Compartilhe conhecimento útil relacionado

Lembre-se: você está aqui para ser um mentor amigável e ajudar o desenvolvedor a crescer! 🚀""",
        mcp_servers=[mcp_server],
    )

    # Get files changed in PR
    changed_files = await github.get_pr_files()
    
    if not changed_files:
        print("No files to review")
        return True

    reviews = []
    for file_info in changed_files:
        message = f"""Por favor, revise este arquivo:
        - Nome: {file_info['filename']}
        - Status: {file_info['status']}
        - Alterações: +{file_info['additions']} -{file_info['deletions']}
        
        Mudanças:
        {file_info.get('patch', 'Sem diff disponível')}
        
        Foque em:
        1. Boas práticas e padrões de código
        2. Possíveis problemas de segurança ou bugs
        3. Sugestões construtivas de melhoria
        4. Dicas úteis relacionadas ao contexto
        """
        
        # Run the agent for each file
        result = await Runner.run(starting_agent=agent, input=message)
        
        reviews.append({
            'filename': file_info['filename'],
            'review': result.final_output
        })

    # Format and post the review
    review_comment = github.format_review_comment({'file_reviews': reviews})
    success = await github.post_review_comment(review_comment)
    
    return success

async def main():
    """Main entry point for the code review system."""
    pr_number = os.getenv('PR_NUMBER')
    if not pr_number:
        print("Error: PR_NUMBER environment variable is required")
        return
    
    # Initialize GitHub integration
    github = GitHubIntegration()
    
    # Initialize our custom MCP server
    server = CodeReviewMCPServer()
    
    # Run the code review process
    with trace(workflow_name="Code Review"):
        success = await run_code_review(server, github)
        
    if not success:
        print("Failed to post review comment")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())