"""LLM abstraction contracts."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, TypedDict


class LLMClientError(Exception):
    """Custom exception for LLM integration errors."""


class ChatMessage(TypedDict):
    """Provider-agnostic chat turn representation."""
    role: Literal["user", "assistant"]
    content: str


class BaseLLMClient(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def generate_answer(
        self,
        message: str,
        context_sections: List[Dict[str, Any]],
        session_history: List[ChatMessage] | None = None,
    ) -> str:
        """Generate an answer from user message, retrieved context, and optional structured history."""
        raise NotImplementedError("LLMClient must implement generate_answer method.")