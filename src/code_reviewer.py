import os
from typing import Optional
from openai import AsyncOpenAI, AuthenticationError, NotFoundError, RateLimitError, APIConnectionError
from dotenv import load_dotenv

load_dotenv()

class CodeReviewer:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        
    async def review(self, file_content: str, diff: str, custom_prompt: Optional[str] = None) -> str:
        try:
            prompt = custom_prompt if custom_prompt else self._build_review_prompt(file_content, diff)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful code review assistant. Provide clear, constructive feedback focusing on code quality, best practices, potential bugs, and security issues."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000,
                timeout=120  # 2 minute timeout
            )
            
            return response.choices[0].message.content
        except AuthenticationError:
            return "⚠️ Error: Invalid OpenAI API key. Please check your OPENAI_API_KEY environment variable."
        except NotFoundError:
            return f"⚠️ Error: The model '{self.model}' is not available. Please try using 'gpt-3.5-turbo' or check your OpenAI account access."
        except RateLimitError:
            return "⚠️ Error: OpenAI API quota exceeded. Please check your billing details at https://platform.openai.com/account/billing"
        except APIConnectionError:
            return "⚠️ Error: Could not connect to OpenAI API. Please check your internet connection and try again."
        except Exception as e:
            return f"⚠️ Error performing code review: {str(e)}"
        
    def _build_review_prompt(self, file_content: str, diff: str) -> str:
        if diff:
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