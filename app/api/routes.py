"""API routes for user message handling."""

import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas import MessageRequest, MessageResponse
from app.config.settings import settings
from app.core.orchestrator import Orchestrator
from app.core.session_memory import SessionMemory
from app.llm.factory import build_llm_client
from app.tools.kb_tool import KnowledgeBaseTool

router = APIRouter()
logger = logging.getLogger(__name__)

_kb_tool = KnowledgeBaseTool(kb_url=settings.kb_url, timeout_seconds=settings.kb_timeout_seconds)
_llm_client = build_llm_client()
_session_memory = SessionMemory(
    ttl_seconds=settings.session_ttl_seconds,
    max_turns=settings.session_max_turns,
)
_orchestrator = Orchestrator(
    kb_tool=_kb_tool,
    llm_client=_llm_client,
    session_memory=_session_memory,
)


@router.post("/messages", response_model=MessageResponse)
async def handle_message(request: MessageRequest) -> MessageResponse:
    logger.info("Received POST /messages request.")
    logger.debug("Request metadata: session_id_present=%s", bool(request.session_id))
    try:
        response = await _orchestrator.handle_message(
            message=request.message,
            session_id=request.session_id,
        )
        logger.info("POST /messages completed successfully with %s source(s).", len(response.sources))
        return response
    except ValueError as exc:
        logger.warning("Validation/business error while handling message: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Unexpected error while handling message: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from exc