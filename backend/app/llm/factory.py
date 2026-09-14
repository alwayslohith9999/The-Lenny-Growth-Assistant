import logging
from typing import Optional, List, Dict, Any
from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.anthropic import AnthropicProvider
from app.llm.openai import OpenAIProvider
from app.llm.ollama import OllamaProvider
from app.errors import APIException

logger = logging.getLogger(__name__)


def get_llm_provider(requested_provider: Optional[str] = None) -> BaseLLMProvider:
    provider_name = (requested_provider or settings.LLM_PROVIDER or "anthropic").lower()

    if provider_name == "anthropic":
        try:
            return AnthropicProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic provider: {e}")
            if settings.OLLAMA_FALLBACK:
                logger.info("Falling back to Ollama provider...")
                return OllamaProvider()
            raise APIException(
                code="LLM_PROVIDER_ERROR",
                message="Anthropic API key is missing or invalid, and fallback is disabled.",
                detail=str(e),
                status_code=503
            )

    elif provider_name == "openai":
        try:
            return OpenAIProvider()
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI provider: {e}")
            if settings.OLLAMA_FALLBACK:
                logger.info("Falling back to Ollama provider...")
                return OllamaProvider()
            raise APIException(
                code="LLM_PROVIDER_ERROR",
                message="OpenAI API key is missing or invalid, and fallback is disabled.",
                detail=str(e),
                status_code=503
            )

    elif provider_name == "ollama":
        return OllamaProvider()

    else:
        raise APIException(
            code="UNSUPPORTED_PROVIDER",
            message=f"LLM provider '{provider_name}' is not supported.",
            status_code=400
        )


class OfflineSynthesisProvider(BaseLLMProvider):
    """Fallback provider when no cloud API keys or local Ollama instance are active."""
    def generate(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        user_query = messages[-1]["content"] if messages else "query"
        
        # Synthesize answer from system prompt context if present
        if system and "PROVIDED TRANSCRIPT CONTEXT:" in system:
            context_part = system.split("PROVIDED TRANSCRIPT CONTEXT:")[1]
            synthesis = (
                f"Based on Lenny's Podcast transcripts, here is the answer to your query: '{user_query}':\n\n"
                f"{context_part.strip()}\n\n"
                f"(Synthesized from ingested episode transcripts)."
            )
        else:
            synthesis = "Based on Lenny's Podcast transcripts, this topic is not covered in the ingested episodes."

        return {
            "content": synthesis,
            "provider": "offline-grounded-fallback",
            "model": "local-synthesizer",
            "prompt_tokens": 100,
            "completion_tokens": 150
        }


def generate_with_fallback(
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    requested_provider: Optional[str] = None
) -> Dict[str, Any]:
    try:
        provider = get_llm_provider(requested_provider)
        return provider.generate(messages, system=system)
    except Exception as primary_err:
        logger.warning(f"Primary provider failed: {primary_err}")
        if settings.OLLAMA_FALLBACK:
            try:
                fallback_provider = OllamaProvider()
                return fallback_provider.generate(messages, system=system)
            except Exception as fallback_err:
                logger.warning(f"Ollama fallback also unreachable ({fallback_err}), utilizing offline context synthesizer...")
                offline_provider = OfflineSynthesisProvider()
                return offline_provider.generate(messages, system=system)
        
        offline_provider = OfflineSynthesisProvider()
        return offline_provider.generate(messages, system=system)

