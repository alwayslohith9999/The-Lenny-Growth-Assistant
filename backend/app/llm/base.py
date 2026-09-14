from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], system: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate response from LLM provider.
        Returns:
            {
                "content": str,
                "provider": str,
                "model": str,
                "prompt_tokens": Optional[int],
                "completion_tokens": Optional[int]
            }
        """
        pass
