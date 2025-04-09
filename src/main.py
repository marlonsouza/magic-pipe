import asyncio
import os
import sys
from typing import Optional
from openai_agents import Agent, AgentState, Message, Role
from .github_integration import GitHubIntegration
from .code_reviewer import CodeReviewer

async def run_code_review(reviewer: CodeReviewer, github: GitHubIntegration) -> bool:
    """Run code review using OpenAI agent."""
    try:
        # Initialize agent
        agent = Agent()
        agent_state = AgentState(
            messages=[
                Message(
                    role=Role.SYSTEM,
                    content="""Você é um assistente amigável e especialista em revisão de código. 
Sua missão é revisar o código de forma construtiva e encorajadora.

Ao revisar o código:
- Comece destacando os pontos fortes e boas práticas
- Faça sugestões de forma construtiva e positiva
- Use emojis para tornar o feedback mais amigável
- Sugira melhorias específicas com exemplos
- Mantenha um tom encorajador e colaborativo

Suas análises devem incluir:
1. Pontos positivos do código
2. Sugestões de melhoria
3. Considerações sobre segurança e performance
4. Dicas e melhores práticas

Lembre-se: você está aqui para ser um mentor amigável! 🚀"""
                )
            ]
        )

        # Get files changed in PR
        changed_files = await github.get_pr_files()
        if not changed_files:
            print("No files to review")
            return True

        reviews = []
        for file_info in changed_files:
            # Create review request message
            message = Message(
                role=Role.USER,
                content=f"""Por favor, revise este arquivo:
                - Nome: {file_info['filename']}
                - Status: {file_info['status']}
                - Alterações: +{file_info['additions']} -{file_info['deletions']}
                
                Mudanças:
                {file_info.get('patch', 'Sem diff disponível')}
                
                Foque em:
                1. Boas práticas e padrões de código
                2. Possíveis problemas de segurança ou bugs
                3. Sugestões construtivas de melhoria
                4. Dicas úteis relacionadas ao contexto"""
            )
            
            # Add message to agent state
            agent_state.messages.append(message)
            
            # Run the agent
            completion = await agent.complete(agent_state)
            
            # Store the review
            reviews.append({
                'filename': file_info['filename'],
                'review': completion.message.content
            })
            
            # Reset agent state for next file
            agent_state.messages = agent_state.messages[:-2]

        # Format and post the review
        review_comment = github.format_review_comment({'file_reviews': reviews})
        success = await github.post_review_comment(review_comment)
        
        return success

    except Exception as e:
        print(f"Error during code review: {str(e)}")
        return False

async def main():
    """Main entry point for the code review system."""
    pr_number = os.getenv('PR_NUMBER')
    if not pr_number:
        print("Error: PR_NUMBER environment variable is required")
        return
    
    # Initialize GitHub integration and code reviewer
    github = GitHubIntegration()
    reviewer = CodeReviewer()
    
    # Run the code review process
    success = await run_code_review(reviewer, github)
    
    if not success:
        print("Failed to post review comment")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())