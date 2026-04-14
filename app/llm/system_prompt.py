"""Centralized system prompt and shared prompt composition helpers."""

from typing import Any, Dict, List


SYSTEM_PROMPT = (
    "Você é um assistente de respostas técnicas para um backend."
    "Regras obrigatórias:"
    "1. Responda somente com base no CONTEXTO fornecido pelo sistema/aplicação."
    "2. Não use conhecimento externo, inferências não sustentadas pelo contexto, nem invente informações."
    "3. Seja objetivo, técnico e claro."

    "Saída esperada:"
    "- Produza apenas a resposta final em texto."
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


def build_user_prompt(message: str, context_sections: List[Dict[str, Any]]) -> str:
    """Compose the user-facing prompt content shared by providers."""
    context_text = build_context_text(context_sections)
    return f"Pergunta:\n{message}\n\nContexto:\n{context_text}"


def build_openai_messages(message: str, context_sections: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Compose OpenAI-compatible chat messages using shared system prompt."""
    user_prompt = build_user_prompt(message=message, context_sections=context_sections)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
