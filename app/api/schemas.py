"""Pydantic schemas for the public API contract."""

import logging
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.config.settings import settings

logger = logging.getLogger(__name__)

class MessageRequest(BaseModel):
    """Request payload for the POST /messages endpoint."""

    message: str = Field(..., description="User message to be answered using KB context.")
    session_id: Optional[str] = Field(None, description="Optional session identifier.")

    @field_validator("message")
    def validate_message(cls, value: str) -> str:
        """Validate and normalize incoming user message."""
        logger.debug("Validating incoming message payload.")
        normalized = value.strip()
        if not normalized:
            logger.warning("Rejected empty message after normalization.")
            raise ValueError("Message cannot be empty.")
        if len(normalized) > settings.max_message_chars:
            logger.warning("Rejected message exceeding MAX_MESSAGE_CHARS=%s.", settings.max_message_chars)
            raise ValueError(f"Message cannot exceed {settings.max_message_chars} characters.")
        return normalized

class SourceItem(BaseModel):
    """A single source section used to build the answer."""

    section: str = Field(..., description="Section from which the information was retrieved.")


class MessageResponse(BaseModel):
    """Response payload for the POST /messages endpoint."""

    answer: str = Field(..., description="Generated answer.")
    sources: List[SourceItem] = Field(..., description="Sections used to produce the answer.")