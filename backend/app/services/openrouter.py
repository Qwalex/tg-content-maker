import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings


class OpenRouterService:
    @retry(stop=stop_after_attempt(settings.max_openrouter_retries), wait=wait_exponential(multiplier=1, min=1, max=10), reraise=True)
    async def transform_text(self, text: str, language_code: str, system_prompt: str | None, user_prompt: str | None) -> tuple[str, dict]:
        prompt = (
            f"Translate to {language_code}. Keep intent and structure.\n"
            f"SystemPrompt={system_prompt or '-'}\n"
            f"UserPrompt={user_prompt or '-'}\n"
            f"Text={text}"
        )
        payload = {
            "model": settings.openrouter_default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        if not settings.openrouter_api_key:
            return text, payload
        headers = {"Authorization": f"Bearer {settings.openrouter_api_key}"}
        async with httpx.AsyncClient(base_url=settings.openrouter_base_url, timeout=45) as client:
            response = await client.post("/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"], payload
