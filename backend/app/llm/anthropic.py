import httpx
import logging
from typing import List, Dict, Any, Optional
from app.llm.base import BaseLLMProvider
from app.config import settings

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.LLM_MODEL or "claude-3-5-sonnet-20241022"
        if not self.api_key:
            raise ValueError("Anthropic API key is not configured.")

    def generate(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages
        }
        if system:
            payload["system"] = system

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                content_text = ""
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        content_text += block.get("text", "")

                usage = data.get("usage", {})
                return {
                    "content": content_text,
                    "provider": "anthropic",
                    "model": self.model,
                    "prompt_tokens": usage.get("input_tokens"),
                    "completion_tokens": usage.get("output_tokens")
                }
        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise e
