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


def generate_with_fallback(
    messages: List[Dict[str, str]],
    system: Optional[str] = None,
    requested_provider: Optional[str] = None
) -> Dict[str, Any]:
    provider = get_llm_provider(requested_provider)
    try:
        return provider.generate(messages, system=system)
    except Exception as primary_err:
        logger.error(f"Primary provider execution failed: {primary_err}")
        if settings.OLLAMA_FALLBACK and not isinstance(provider, OllamaProvider):
            logger.info("Attempting execution fallback to Ollama...")
            try:
                fallback_provider = OllamaProvider()
                return fallback_provider.generate(messages, system=system)
            except Exception as fallback_err:
                logger.error(f"Ollama fallback also failed: {fallback_err}")
                raise APIException(
                    code="LLM_FALLBACK_FAILED",
                    message="Both primary LLM provider and Ollama fallback failed.",
                    detail=f"Primary error: {primary_err} | Fallback error: {fallback_err}",
                    status_code=502
                )
        raise APIException(
            code="LLM_GENERATION_FAILED",
            message="LLM generation call failed.",
            detail=str(primary_err),
            status_code=502
        )
