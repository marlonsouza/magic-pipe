import os
import asyncio
import sys
from typing import Optional
from openai import AsyncOpenAI, AuthenticationError, NotFoundError, RateLimitError, APIConnectionError
from dotenv import load_dotenv

load_dotenv()

def debug_log(message: str):
    print(f"DEBUG: {message}", file=sys.stderr)

class CodeReviewer:
    def __init__(self):
        debug_log("Initializing CodeReviewer...")
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            debug_log("ERROR: OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        debug_log(f"Using model: {self.model}")
        
    async def review(self, file_content: str, diff: str, custom_prompt: Optional[str] = None) -> str:
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                debug_log(f"Review attempt {retry_count + 1}/{self.max_retries}")
                prompt = custom_prompt if custom_prompt else self._build_review_prompt(file_content, diff)
                
                debug_log("Sending request to OpenAI API...")
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": """Você é um assistente amigável e especialista em revisão de código. 
Sua missão é ajudar os desenvolvedores a melhorarem seu código de forma construtiva e encorajadora.

Ao revisar o código:
- Use um tom positivo e amigável
- Comece destacando os pontos fortes
- Faça sugestões de forma construtiva
- Use emojis para tornar o feedback mais acessível
- Mantenha o foco em ajudar o desenvolvedor a crescer

Lembre-se: você está aqui para ser um mentor amigável, não um crítico severo! 🤝"""},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=120  # 2 minute timeout
                )
                
                debug_log("Successfully received response from OpenAI")
                return response.choices[0].message.content
                
            except AuthenticationError as e:
                debug_log(f"Authentication error: {str(e)}")
                return "⚠️ Error: Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable."
            except NotFoundError as e:
                debug_log(f"Model not found error: {str(e)}")
                return f"⚠️ Error: The model '{self.model}' is not available. Please try using 'gpt-3.5-turbo' or check your OpenAI account access."
            except RateLimitError as e:
                debug_log(f"Rate limit error: {str(e)}")
                return "⚠️ Error: OpenAI API quota exceeded. Please check your billing details at https://platform.openai.com/account/billing"
            except APIConnectionError as e:
                debug_log(f"Connection error: {str(e)}")
                last_error = e
                retry_count += 1
                if retry_count < self.max_retries:
                    debug_log(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                continue
            except Exception as e:
                debug_log(f"Unexpected error: {str(e)}")
                last_error = e
                retry_count += 1
                if retry_count < self.max_retries:
                    debug_log(f"Retrying in {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                continue
                
        debug_log(f"All retry attempts failed. Last error: {str(last_error)}")
        return f"⚠️ Error performing code review after {self.max_retries} attempts: {str(last_error)}"
        
    def _build_review_prompt(self, file_content: str, diff: str) -> str:
        debug_log("Building review prompt...")
        if diff:
            debug_log("Including diff in prompt")
            return f"""Please review the following code changes:

Changes:
```
{diff}
```

Full file context:
```
{file_content}
```

Please provide:
1. A concise summary of the changes
2. Potential issues, bugs, or security concerns
3. Suggestions for improvement
4. Best practices that should be applied
"""
        else:
            debug_log("No diff provided, reviewing full content")
            return f"""Please review the following code:

```
{file_content}
```

Please provide:
1. A concise code quality assessment
2. Potential issues, bugs, or security concerns
3. Suggestions for improvement
4. Best practices that should be applied
"""