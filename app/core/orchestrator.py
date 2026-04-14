"""Core orchestration flow for message -> KB context -> LLM answer."""

import logging
from typing import Any, Dict, List

from app.api.schemas import MessageResponse, SourceItem
from app.config.settings import settings
from app.core.constants import FALLBACK_MESSAGE, MAX_CONTEXT_SECTIONS, MIN_SECTION_SCORE, SOURCE_SECTION_LEVELS
from app.core.session_memory import SessionMemory, SessionTurn
from app.llm.base import BaseLLMClient, ChatMessage, LLMClientError
from app.tools.kb_tool import KBToolError, KnowledgeBaseTool

logger = logging.getLogger(__name__)


class Orchestrator:
    """Coordinates retrieval, decision, and LLM synthesis."""

    def __init__(
        self,
        kb_tool: KnowledgeBaseTool,
        llm_client: BaseLLMClient,
        session_memory: SessionMemory | None = None,
    ) -> None:
        self.kb_tool = kb_tool
        self.llm_client = llm_client
        self.session_memory = session_memory
        logger.debug("Orchestrator initialized with KnowledgeBaseTool and LLM client.")

    def _fallback_response(self) -> MessageResponse:
        return MessageResponse(answer=FALLBACK_MESSAGE, sources=[])

    def _select_sections_for_response(
        self,
        relevant_sections: List[Dict[str, Any]],
        max_sections: int = MAX_CONTEXT_SECTIONS,
    ) -> List[Dict[str, Any]]:
        if not relevant_sections:
            return []

        used_sections: List[Dict[str, Any]] = []
        seen_sections: set[str] = set()

        for candidate in relevant_sections:
            if len(used_sections) >= max_sections:
                break

            section_name = str(candidate.get("section", "")).strip()
            section_level = int(candidate.get("level", 0))
            if section_level not in SOURCE_SECTION_LEVELS:
                continue

            if not section_name or section_name in seen_sections:
                continue

            seen_sections.add(section_name)
            used_sections.append(candidate)

        return used_sections

    def _build_retrieval_message(self, message: str, history_turns: List[SessionTurn]) -> str:
        """Build retrieval query preserving current question while leveraging short history."""
        if not history_turns:
            return message

        recent_user_messages = [turn.user_message for turn in history_turns[-2:]]
        merged = " ".join([*recent_user_messages, message]).strip()
        return merged[: settings.max_message_chars]

    def _build_session_history(self, history_turns: List[SessionTurn]) -> List[ChatMessage]:
        """Build provider-agnostic structured history turns for LLM input."""
        chat_history: List[ChatMessage] = []
        for turn in history_turns[-2:]:
            user_text = turn.user_message.strip()
            assistant_text = turn.assistant_answer.strip()
            if user_text:
                chat_history.append({"role": "user", "content": user_text})
            if assistant_text:
                chat_history.append({"role": "assistant", "content": assistant_text})
        return chat_history

    async def handle_message(self, message: str, session_id: str | None = None) -> MessageResponse:
        logger.info("Starting message orchestration flow.")
        logger.debug("Flow input: message_length=%s, session_id_present=%s", len(message), bool(session_id))

        history_turns: List[SessionTurn] = []
        if session_id and self.session_memory is not None:
            history_turns = await self.session_memory.get_turns(session_id=session_id)

        retrieval_message = self._build_retrieval_message(
            message=message,
            history_turns=history_turns,
        )
        session_history = self._build_session_history(history_turns=history_turns)

        try:
            search_result = await self.kb_tool.search(
                message=retrieval_message,
                max_sections=MAX_CONTEXT_SECTIONS,
            )
            relevant_sections = search_result["context"]
            logger.info("Context selection produced %s relevant section(s).", len(relevant_sections))
        except KBToolError as exc:
            logger.warning("KB retrieval controlled failure: %s", exc)
            return self._fallback_response()
        except Exception as exc:
            logger.error("Unexpected retrieval error: %s", exc, exc_info=True)
            return self._fallback_response()

        if not relevant_sections:
            logger.warning("No relevant KB context found; returning fallback.")
            return self._fallback_response()

        top_score = int(relevant_sections[0].get("score", 0))
        if top_score < MIN_SECTION_SCORE:
            logger.warning(
                "Top score (%s) below MIN_SECTION_SCORE=%s; returning fallback.",
                top_score,
                MIN_SECTION_SCORE,
            )
            return self._fallback_response()

        used_sections = self._select_sections_for_response(
            relevant_sections=relevant_sections,
            max_sections=MAX_CONTEXT_SECTIONS,
        )
        if not used_sections:
            logger.warning("No valid sections selected for response; returning fallback.")
            return self._fallback_response()

        try:
            answer = await self.llm_client.generate_answer(
                message=message,
                context_sections=used_sections,
                session_history=session_history,
            )
        except LLMClientError as exc:
            logger.warning("LLM controlled failure: %s", exc)
            return self._fallback_response()
        except Exception as exc:
            logger.error("Unexpected LLM error: %s", exc, exc_info=True)
            return self._fallback_response()

        if not answer.strip():
            logger.warning("LLM returned blank answer; returning fallback.")
            return self._fallback_response()

        answer_text = answer.strip()

        if session_id and self.session_memory is not None:
            await self.session_memory.append_turn(
                session_id=session_id,
                user_message=message,
                assistant_answer=answer_text,
            )

        sources = [SourceItem(section=section["section"]) for section in used_sections]
        return MessageResponse(answer=answer_text, sources=sources)