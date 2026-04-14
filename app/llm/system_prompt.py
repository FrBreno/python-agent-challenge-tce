"""Centralized system prompt and shared prompt composition helpers."""

from __future__ import annotations
from typing import Any, Dict, List

from .base import ChatMessage


SYSTEM_PROMPT = (
    "Você é um assistente técnico para um backend de IA.\n"
    "Regras obrigatórias:\n"
    "1. Responda somente com base no CONTEXTO fornecido pela aplicação.\n"
    "2. Não use conhecimento externo, inferências não sustentadas pelo contexto, nem invente informações.\n"
    "3. Seja objetivo, técnico e claro.\n"
    "\n"
    "Formato da resposta:\n"
    "- Produza apenas a resposta final em texto.\n"
    "- Não use Markdown decorativo excessivo."
)


def build_context_text(context_sections: List[Dict[str, Any]]) -> str:
    """Build a normalized context block from retrieved KB sections."""
    blocks: List[str] = []
    for section in context_sections:
        title = str(section.get("section", "")).strip()
        content = str(section.get("content", "")).strip()
        blocks.append(f"Section: {title}\nContent:\n{content}")
    return "\n\n---\n\n".join(blocks).strip()


def build_user_prompt(
    message: str,
    context_sections: List[Dict[str, Any]],
) -> str:
    """Compose the current user turn with retrieved KB context."""
    context_text = build_context_text(context_sections)
    parts: List[str] = []
    parts.append(f"Pergunta atual:\n{message}")

    if context_text:
        parts.append(f"Contexto recuperado da base de conhecimento:\n{context_text}")

    return "\n\n".join(parts).strip()


def build_openai_messages(
    message: str,
    context_sections: List[Dict[str, Any]],
    session_history: List[ChatMessage] | None = None,
) -> List[Dict[str, str]]:
    """Compose OpenAI-compatible chat messages using shared system prompt."""
    messages: List[Dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    for turn in session_history or []:
        role = str(turn.get("role", "")).strip().lower()
        content = str(turn.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    user_prompt = build_user_prompt(
        message=message,
        context_sections=context_sections,
    )
    messages.append({"role": "user", "content": user_prompt})
    return messages


def build_gemini_contents(
    message: str,
    context_sections: List[Dict[str, Any]],
    session_history: List[ChatMessage] | None = None,
) -> List[Dict[str, Any]]:
    """
    Compose Gemini-compatible contents.

    Gemini receives the system instruction separately, so this function returns only
    the conversation contents (history + current turn).
    """
    contents: List[Dict[str, Any]] = []

    for turn in session_history or []:
        role = str(turn.get("role", "")).strip().lower()
        content = str(turn.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue

        gemini_role = "user" if role == "user" else "model"

        contents.append(
            {
                "role": gemini_role,
                "parts": [{"text": content}],
            }
        )

    user_prompt = build_user_prompt(
        message=message,
        context_sections=context_sections,
    )
    contents.append(
        {
            "role": "user",
            "parts": [{"text": user_prompt}],
        }
    )
    return contents