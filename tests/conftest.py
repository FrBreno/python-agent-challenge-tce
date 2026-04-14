"""Test configuration and shared fixtures."""

from __future__ import annotations

import os
import sys
import pytest
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure settings can be instantiated during module imports.
os.environ.setdefault("KB_URL", "https://example.com/knowledge-base.md")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")
os.environ.setdefault("LLM_API_KEY", "test-api-key")
os.environ.setdefault("LLM_BASE_URL", "https://api.openai.com/v1")

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Build a FastAPI test client for endpoint-level tests."""
    from app.main import app

    with TestClient(app) as test_client:
        yield test_client
