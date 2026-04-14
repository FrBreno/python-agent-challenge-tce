"""OpenAI provider client implementation."""

import logging
from typing import Any, Dict, List

from ..base import LLMClientError
from ..system_prompt import build_openai_messages
from .base_http_client import BaseHTTPLLMClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseHTTPLLMClient):
    """OpenAI API client implementation."""

    provider_name = "openai"

    def __init__(self, model: str, api_key: str, base_url: str = "", timeout_seconds: float = 30.0) -> None:
        resolved_base_url = base_url.rstrip("/") if base_url else "https://api.openai.com/v1"
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=resolved_base_url,
            timeout_seconds=timeout_seconds,
        )
        logger.debug(
            "OpenAIClient initialized with model=%s base_url=%s timeout_seconds=%s",
            model,
            resolved_base_url,
            timeout_seconds,
        )

    async def generate_answer(self, message: str, context_sections: List[Dict[str, Any]]) -> str:
        """Generate an answer using OpenAI API."""
        self._require_api_key()

        messages = build_openai_messages(message=message, context_sections=context_sections)
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.2,
        }

        data = await self._post_json(url=url, payload=payload, headers=headers)
        choices = data.get("choices", [])
        if not choices:
            raise LLMClientError("OpenAI returned no choices.")

        text = str(choices[0].get("message", {}).get("content", "")).strip()
        if not text:
            raise LLMClientError("OpenAI returned blank text.")

        return text