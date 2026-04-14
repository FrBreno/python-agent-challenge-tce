"""Gemini provider client implementation."""

import logging
from typing import Any, Dict, List

from ..base import LLMClientError
from ..system_prompt import SYSTEM_PROMPT, build_user_prompt
from .base_http_client import BaseHTTPLLMClient

logger = logging.getLogger(__name__)


class GeminiClient(BaseHTTPLLMClient):
    """Gemini API client implementation."""

    provider_name = "gemini"

    def __init__(self, model: str, api_key: str, base_url: str = "", timeout_seconds: float = 30.0) -> None:
        resolved_base_url = base_url.rstrip("/") if base_url else "https://generativelanguage.googleapis.com/v1beta"
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=resolved_base_url,
            timeout_seconds=timeout_seconds,
        )
        logger.debug(
            "GeminiClient initialized with model=%s base_url=%s timeout_seconds=%s",
            model,
            resolved_base_url,
            timeout_seconds,
        )

    async def generate_answer(self, message: str, context_sections: List[Dict[str, Any]]) -> str:
        """Generate an answer using Gemini API."""
        self._require_api_key()

        user_prompt = build_user_prompt(message=message, context_sections=context_sections)
        url = f"{self.base_url}/models/{self.model}:generateContent"
        params = {"key": self.api_key}
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ]
        }

        data = await self._post_json(url=url, payload=payload, params=params)
        candidates = data.get("candidates", [])
        if not candidates:
            raise LLMClientError("Gemini returned no candidates.")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise LLMClientError("Gemini returned empty content.")

        text = str(parts[0].get("text", "")).strip()
        if not text:
            raise LLMClientError("Gemini returned blank text.")

        return text