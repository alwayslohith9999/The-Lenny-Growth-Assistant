import httpx
import logging
from typing import List, Dict, Any, Optional
from app.llm.base import BaseLLMProvider
from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """LLM provider implementation for OpenAI chat completion APIs."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL or "gpt-4o"
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured.")

    def generate(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        formatted_messages = []
        if system:
            formatted_messages.append({"role": "system", "content": system})
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": 4096
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                content_text = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                return {
                    "content": content_text,
                    "provider": "openai",
                    "model": self.model,
                    "prompt_tokens": usage.get("prompt_tokens"),
                    "completion_tokens": usage.get("completion_tokens")
                }
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise e
