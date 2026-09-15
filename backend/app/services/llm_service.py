"""LLM Service orchestrator.

Coordinates prompt assembly, model execution timing, and telemetry measurement.
"""
import time
import logging
from typing import List, Dict, Any, Optional
from app.llm.factory import generate_with_fallback

logger = logging.getLogger(__name__)


class LLMService:
    """Service wrapper providing latency measurement and telemetry tracking for LLM requests."""

    @staticmethod
    def generate(
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        requested_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Executes generation through tiered fallback while measuring true round-trip wall-clock latency."""
        start_time = time.perf_counter()
        try:
            result = generate_with_fallback(
                messages=messages,
                system=system,
                requested_provider=requested_provider
            )
        finally:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        result["latency_ms"] = max(1, elapsed_ms)
        logger.info(
            f"LLM generation finished in {elapsed_ms}ms "
            f"using provider='{result.get('provider')}' model='{result.get('model')}' fallback={result.get('is_fallback')}"
        )
        return result
