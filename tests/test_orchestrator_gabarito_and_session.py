"""Orchestrator tests for reference questions and session behavior."""

from __future__ import annotations

import asyncio
import re
import unicodedata
from typing import Any, Dict, List

from app.core.constants import FALLBACK_MESSAGE
from app.core.orchestrator import Orchestrator
from app.core.session_memory import SessionMemory
from app.llm.base import BaseLLMClient, ChatMessage


class FakeKBTool:
    """KB fake that maps reference questions to deterministic sections."""

    def __init__(self) -> None:
        self._mapping: dict[str, str] = {
            "o que e composicao": "Composição",
            "quando usar heranca": "Herança",
            "qual o papel da orquestracao": "Orquestração",
            "a tool deve responder diretamente ao usuario": "Tool de conhecimento",
            "qual o papel da tool de conhecimento": "Tool de conhecimento",
            "onde colocar regra de negocio": "Endpoint de API",
            "pode resumir": "Composição",
        }

    async def search(self, message: str, max_sections: int = 3) -> Dict[str, Any]:
        normalized = unicodedata.normalize("NFKD", message.lower())
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        for key, section in self._mapping.items():
            if key in normalized:
                return {
                    "context": [
                        {
                            "section": section,
                            "content": f"Conteudo tecnico sobre {section}.",
                            "level": 2,
                            "order": 0,
                            "score": 999,
                        }
                    ],
                    "sources": [section],
                }

        return {"context": [], "sources": []}


class FakeLLMClient(BaseLLMClient):
    """LLM fake that captures structured session history."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    async def generate_answer(
        self,
        message: str,
        context_sections: List[Dict[str, Any]],
        session_history: List[ChatMessage] | None = None,
    ) -> str:
        self.calls.append(
            {
                "message": message,
                "context_sections": context_sections,
                "session_history": session_history or [],
            }
        )
        section = context_sections[0]["section"] if context_sections else "sem contexto"
        return f"Resposta baseada em {section}."


def _run(coro):
    return asyncio.run(coro)


def _build_orchestrator() -> tuple[Orchestrator, FakeLLMClient]:
    llm = FakeLLMClient()
    orchestrator = Orchestrator(
        kb_tool=FakeKBTool(),
        llm_client=llm,
        session_memory=SessionMemory(ttl_seconds=1800, max_turns=5),
    )
    return orchestrator, llm


def test_gabarito_minimo_reference_questions() -> None:
    orchestrator, _ = _build_orchestrator()

    cases = [
        ("O que é composição?", "Composição"),
        ("Quando usar herança?", "Herança"),
        ("Qual o papel da orquestração?", "Orquestração"),
        ("A tool deve responder diretamente ao usuário?", "Tool de conhecimento"),
        ("Qual o papel da Tool de conhecimento?", "Tool de conhecimento"),
        ("Onde colocar regra de negócio, no endpoint ou no fluxo interno?", "Endpoint de API"),
    ]

    for question, expected_section in cases:
        result = _run(orchestrator.handle_message(question))
        assert result.answer
        assert result.sources
        assert result.sources[0].section == expected_section


def test_gabarito_fallback_case() -> None:
    orchestrator, _ = _build_orchestrator()
    result = _run(orchestrator.handle_message("Como agir sem contexto suficiente?"))

    assert result.answer == FALLBACK_MESSAGE
    assert result.sources == []


def test_session_id_reused_keeps_short_history() -> None:
    orchestrator, llm = _build_orchestrator()

    _run(orchestrator.handle_message("O que é composição?", session_id="sessao-123"))
    _run(orchestrator.handle_message("Pode resumir em uma frase?", session_id="sessao-123"))

    assert len(llm.calls) == 2
    assert llm.calls[0]["session_history"] == []
    second_history = llm.calls[1]["session_history"]
    assert len(second_history) == 2
    assert second_history[0]["role"] == "user"
    assert second_history[1]["role"] == "assistant"


def test_session_id_isolation_between_different_sessions() -> None:
    orchestrator, llm = _build_orchestrator()

    _run(orchestrator.handle_message("O que é composição?", session_id="sessao-A"))
    second_result = _run(orchestrator.handle_message("Como agir sem contexto suficiente?", session_id="sessao-B"))

    assert len(llm.calls) == 1
    assert second_result.answer == FALLBACK_MESSAGE
    assert second_result.sources == []


def test_without_session_id_remains_stateless() -> None:
    orchestrator, llm = _build_orchestrator()

    _run(orchestrator.handle_message("O que é composição?"))
    second_result = _run(orchestrator.handle_message("Como agir sem contexto suficiente?"))

    assert len(llm.calls) == 1
    assert llm.calls[0]["session_history"] == []
    assert second_result.answer == FALLBACK_MESSAGE
    assert second_result.sources == []
