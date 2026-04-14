"""Shared HTTP client behavior for LLM providers."""

import logging
from typing import Any, Dict, Optional

import httpx

from ..base import BaseLLMClient, LLMClientError


class BaseHTTPLLMClient(BaseLLMClient):
    """Common utilities for HTTP-based LLM providers."""

    provider_name = "llm"

    def __init__(self, model: str, api_key: str, base_url: str, timeout_seconds: float = 30.0) -> None:
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.logger = logging.getLogger(self.__class__.__module__)

    def _require_api_key(self) -> None:
        """Validate that an API key is configured for provider usage."""
        if not self.api_key:
            self.logger.error("%s API key is not configured.", self.provider_name.upper())
            raise LLMClientError("LLM provider API key is missing.")

    async def _post_json(
        self,
        url: str,
        payload: Dict[str, Any],
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Execute POST request and return decoded JSON with normalized error handling."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers, params=params)
        except httpx.TimeoutException as exc:
            self.logger.error("%s timeout.", self.provider_name.upper(), exc_info=True)
            raise LLMClientError(f"{self.provider_name.capitalize()} request timeout.") from exc
        except httpx.RequestError as exc:
            self.logger.error("%s request failure.", self.provider_name.upper(), exc_info=True)
            raise LLMClientError(f"{self.provider_name.capitalize()} request failed.") from exc

        if response.status_code >= 400:
            self.logger.warning(
                "%s returned status=%s body=%s",
                self.provider_name.upper(),
                response.status_code,
                response.text[:500],
            )
            raise LLMClientError(f"{self.provider_name.capitalize()} returned status {response.status_code}.")

        try:
            return response.json()
        except ValueError as exc:
            self.logger.error("%s returned invalid JSON response.", self.provider_name.upper(), exc_info=True)
            raise LLMClientError(f"{self.provider_name.capitalize()} returned invalid JSON.") from exc
