"""Domain constants used by the orchestration flow."""

from app.config.settings import settings

FALLBACK_MESSAGE = "Não encontrei informação suficiente na base de conhecimento para responder à sua pergunta. Por favor, tente reformular ou fornecer mais detalhes."
MIN_SECTION_SCORE = settings.min_section_score
MAX_CONTEXT_SECTIONS = settings.max_context_sections