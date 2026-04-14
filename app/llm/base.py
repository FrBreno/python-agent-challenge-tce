"""LLM abstraction contracts."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMClientError(Exception):
    """Custom exception for LLM integration errors."""


class BaseLLMClient(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate_answer(self, message: str, context_sections: List[Dict[str, Any]]) -> str:
        """Generate an answer from user message and retrieved context."""
        raise NotImplementedError("LLMClient must implement generate_answer method.")