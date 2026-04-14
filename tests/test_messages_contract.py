"""Contract tests for POST /messages endpoint."""

from __future__ import annotations

from typing import Any

from app.api.schemas import MessageResponse, SourceItem
from app.core.constants import FALLBACK_MESSAGE

class StubOrchestrator:
    """Deterministic orchestrator stub for endpoint contract tests."""

    async def handle_message(self, message: str, session_id: str | None = None) -> MessageResponse:
        normalized = message.strip().lower()
        if "fora do escopo" in normalized:
            return MessageResponse(answer=FALLBACK_MESSAGE, sources=[])
        return MessageResponse(
            answer="Resposta de teste com contexto.",
            sources=[SourceItem(section="Composição")],
        )


def _assert_contract_shape(body: dict[str, Any]) -> None:
    assert set(body.keys()) == {"answer", "sources"}
    assert isinstance(body["answer"], str)
    assert isinstance(body["sources"], list)
    for source in body["sources"]:
        assert set(source.keys()) == {"section"}
        assert isinstance(source["section"], str)


def test_post_messages_success_contract(client, monkeypatch) -> None:
    import app.api.routes as routes

    monkeypatch.setattr(routes, "_orchestrator", StubOrchestrator())
    response = client.post("/messages", json={"message": "O que é composição?"})

    assert response.status_code == 200
    data = response.json()
    _assert_contract_shape(data)
    assert data["sources"], "sources deve conter ao menos 1 seção em caso de sucesso."


def test_post_messages_fallback_contract(client, monkeypatch) -> None:
    import app.api.routes as routes

    monkeypatch.setattr(routes, "_orchestrator", StubOrchestrator())
    response = client.post("/messages", json={"message": "Pergunta fora do escopo da KB"})

    assert response.status_code == 200
    data = response.json()
    _assert_contract_shape(data)
    assert data["answer"] == FALLBACK_MESSAGE
    assert data["sources"] == []


def test_post_messages_rejects_empty_message(client) -> None:
    response = client.post("/messages", json={"message": "   "})
    # Schema validation is expected to fail for blank messages.
    assert response.status_code == 422
