from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseSkill(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def run(self, input_text: str, context_chunks: List[Dict[str, Any]], provider_name: str = None) -> Dict[str, Any]:
        """
        Executes the skill against context chunks.
        Returns:
            {
                "content": str (Markdown output),
                "artifact": {"type": "markdown"|"html", "title": str, "content": str},
                "citations": List[Dict]
            }
        """
        pass
