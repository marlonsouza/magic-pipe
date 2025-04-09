import os
import asyncio
import sys
from typing import Optional, Dict, Any
from openai import AsyncOpenAI, AuthenticationError, NotFoundError, RateLimitError, APIConnectionError
from dotenv import load_dotenv

load_dotenv()

# Debug mode controlled by environment variable, off by default
DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'

def debug_log(message: str):
    if DEBUG_MODE:
        print(f"DEBUG: {message}", file=sys.stderr)

class CodeReviewer:
    def __init__(self):
        debug_log("Initializing CodeReviewer...")
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            debug_log("ERROR: OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        debug_log(f"Using model: {self.model}")
        
    async def analyze_file(self, file_info: Dict[str, Any]) -> str:
        """Analyze a file's content and changes."""
        try:
            # Prepare function call arguments
            args = {
                "type": "completion",
                "context": {
                    "file_path": file_info['filename'],
                    "status": file_info['status'],
                    "changes": f"+{file_info['additions']} -{file_info['deletions']}",
                    "diff": file_info.get('patch', '')
                }
            }
            
            # Let the agent handle the review through function calls
            return args
                
        except Exception as e:
            return f"⚠️ Error analyzing file: {str(e)}"
        
    def format_review(self, filename: str, review_content: str) -> Dict[str, str]:
        """Format a review for a single file."""
        return {
            'filename': filename,
            'review': review_content
        }
        
    async def review(self, file_content: str, diff: str, file_path: str = "", custom_prompt: Optional[str] = None) -> str:
        retry_count = 0
        last_error = None
        
        while retry_count < self.max_retries:
            try:
                debug_log(f"Review attempt {retry_count + 1}/{self.max_retries}")
                prompt = custom_prompt if custom_prompt else self._build_review_prompt(file_content, diff, file_path)
                
                debug_log("Sending request to OpenAI API...")
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": """Você é um assistente especialista em revisão de código, agindo como um tech lead sênior.

Ao revisar o código:
- Seja direto e objetivo
- Foque nos problemas mais críticos e em melhorias importantes
- Inclua números de linha específicos ao mencionar problemas ou sugestões
- Mantenha o feedback conciso e acionável
- Use sempre a língua portuguesa para seus comentários

Seu objetivo é fornecer feedback técnico objetivo como um engenheiro sênior, não ser um crítico ou elogiar sem necessidade."""},
                        {"role": "user", "content": prompt + "\n\nIMPORTANTE: Responda SEMPRE em português."}
                    ],
                    temperature=0.5,  # Lower temperature for more consistent output
                    max_tokens=2000,
                    timeout=120  # 2 minute timeout
                )
                
                debug_log("Successfully received response from OpenAI")
                content = response.choices[0].message.content
                
                # If the response is about no issues found (in English or Portuguese), return an empty string
                if (content.strip() == "No issues found." or 
                    content.strip() == "No issues found" or
                    content.strip() == "Nenhum problema encontrado." or
                    content.strip() == "Nenhum problema encontrado" or
                    content.strip() == "Sem problemas encontrados"):
                    return ""
                
                return content
                
            except AuthenticationError as e:
                debug_log(f"Authentication error: {str(e)}")
                return "⚠️ Erro: Chave de API OpenAI inválida. Por favor, verifique sua variável de ambiente OPENAI_API_KEY."
            except NotFoundError as e:
                debug_log(f"Model not found error: {str(e)}")
                return f"⚠️ Erro: O modelo '{self.model}' não está disponível. Por favor, tente usar 'gpt-4' ou verifique seu acesso à conta OpenAI."
            except RateLimitError as e:
                debug_log(f"Rate limit error: {str(e)}")
                return "⚠️ Erro: Cota da API OpenAI excedida. Por favor, verifique seus detalhes de faturamento em https://platform.openai.com/account/billing"
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
        return f"⚠️ Erro ao realizar revisão de código após {self.max_retries} tentativas: {str(last_error)}"
        
    def _build_review_prompt(self, file_content: str, diff: str, file_path: str) -> str:
        debug_log("Building review prompt...")
        concise_mode = not os.getenv('DETAILED_REVIEWS', 'false').lower() == 'true'
        
        if concise_mode:
            debug_log("Using concise review prompt")
            if diff:
                return f"""Revise as seguintes alterações de código como um desenvolvedor sênior experiente. Foque apenas nos problemas principais.

Arquivo: {file_path}

Alterações:
```
{diff}
```

Contexto do arquivo:
```
{file_content}
```

Forneça uma revisão MUITO CONCISA (máximo de 1-2 parágrafos) que um desenvolvedor sênior faria.
Quando encontrar um problema ou tiver uma recomendação, inclua o(s) número(s) específico(s) da(s) linha(s) a que se aplica.

Foque APENAS em:
1. Os problemas mais críticos de qualidade ou segurança (se houver)
2. Uma sugestão principal de melhoria
3. Destaque quaisquer boas práticas que você veja

Se nenhum problema for encontrado e não houver recomendações específicas, responda apenas com "Nenhum problema encontrado."

Seja breve, direto e objetivo como se você fosse um tech lead ocupado. Evite explicações longas.
"""
            else:
                return f"""Revise o seguinte código como um desenvolvedor sênior experiente. Foque apenas nos problemas principais.

Arquivo: {file_path}

```
{file_content}
```

Forneça uma revisão MUITO CONCISA (máximo de 1-2 parágrafos) que um desenvolvedor sênior faria.
Quando encontrar um problema ou tiver uma recomendação, inclua o(s) número(s) específico(s) da(s) linha(s) a que se aplica.

Foque APENAS em:
1. Os problemas mais críticos de qualidade ou segurança (se houver)
2. Uma sugestão principal de melhoria
3. Destaque quaisquer boas práticas que você veja

Se nenhum problema for encontrado e não houver recomendações específicas, responda apenas com "Nenhum problema encontrado."

Seja breve, direto e objetivo como se você fosse um tech lead ocupado. Evite explicações longas.
"""
        else:
            debug_log("Using detailed review prompt")
            if diff:
                debug_log("Including diff in prompt")
                return f"""Por favor, revise as seguintes alterações de código:

Arquivo: {file_path}

Alterações:
```
{diff}
```

Contexto completo do arquivo:
```
{file_content}
```

Por favor, forneça:
1. Um resumo conciso das alterações
2. Potenciais problemas, bugs ou preocupações de segurança (com números de linha)
3. Sugestões de melhoria (com números de linha específicos onde aplicável)
4. Boas práticas que deveriam ser aplicadas

Se não houver problemas encontrados, responda com "Nenhum problema encontrado."
"""
            else:
                debug_log("No diff provided, reviewing full content")
                return f"""Por favor, revise o seguinte código:

Arquivo: {file_path}

```
{file_content}
```

Por favor, forneça:
1. Uma avaliação concisa da qualidade do código
2. Potenciais problemas, bugs ou preocupações de segurança (com números de linha)
3. Sugestões de melhoria (com números de linha específicos onde aplicável)
4. Boas práticas que deveriam ser aplicadas

Se não houver problemas encontrados, responda com "Nenhum problema encontrado."
"""