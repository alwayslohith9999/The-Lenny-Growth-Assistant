import httpx
import logging
from typing import List, Dict, Any, Optional
from app.llm.base import BaseLLMProvider
from app.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = (host or settings.OLLAMA_HOST).rstrip('/')
        self.model = model or settings.LLM_MODEL or "llama3.2"

    def generate(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        formatted_messages = []
        if system:
            formatted_messages.append({"role": "system", "content": system})
        formatted_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.host}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                content_text = data.get("message", {}).get("content", "")
                
                return {
                    "content": content_text,
                    "provider": "ollama",
                    "model": self.model,
                    "prompt_tokens": data.get("prompt_eval_count"),
                    "completion_tokens": data.get("eval_count")
                }
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise e
