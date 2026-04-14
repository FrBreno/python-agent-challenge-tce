"""Factory for LLM provider clients."""

from app.config.settings import settings
from .base import BaseLLMClient, LLMClientError
from .providers.gemini_client import GeminiClient
from .providers.openai_client import OpenAIClient

def build_llm_client() -> BaseLLMClient:
    """Factory function to build the appropriate LLM client based on configuration."""
    provider = settings.llm_provider.lower()
    model = settings.llm_model
    api_key = settings.llm_api_key
    base_url = settings.llm_base_url
    timeout_seconds = settings.llm_timeout_seconds

    if provider == "openai":
        return OpenAIClient(model=model, api_key=api_key, base_url=base_url, timeout_seconds=timeout_seconds)
    elif provider == "gemini":
        return GeminiClient(model=model, api_key=api_key, base_url=base_url, timeout_seconds=timeout_seconds)
    else:
        raise LLMClientError(f"Unsupported LLM provider: {settings.llm_provider}")