"""Domain constants used by orchestration."""

from app.config.settings import settings

FALLBACK_MESSAGE = "Não encontrei informação suficiente na base para responder essa pergunta."
MIN_SECTION_SCORE = settings.min_section_score
MAX_CONTEXT_SECTIONS = settings.max_context_sections
SOURCE_SECTION_LEVELS = (2,)