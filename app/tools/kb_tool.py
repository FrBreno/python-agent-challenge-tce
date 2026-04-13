"""Knowledge base tool responsible for HTTP fetch, markdown parsing, and relevance ranking."""

import logging
import re
import unicodedata
from typing import Any, Dict, List, TypedDict

import httpx

logger = logging.getLogger(__name__)


class KBToolError(Exception):
    """Controlled error raised when KB retrieval cannot be completed safely."""


class KBSection(TypedDict):
    """Typed representation of a ranked KB section used as retrieval context."""

    section: str
    content: str
    level: int
    order: int
    score: int


class KBSearchResult(TypedDict):
    """Typed output for structured context retrieval."""

    context: List[KBSection]
    sources: List[str]


class KnowledgeBaseTool:
    """Provides KB retrieval and lightweight relevance search."""

    def __init__(self, kb_url: str, timeout_seconds: float = 10.0) -> None:
        self.kb_url = kb_url
        self.timeout_seconds = timeout_seconds
        logger.debug(
            "KnowledgeBaseTool initialized with kb_url=%s timeout_seconds=%s",
            kb_url,
            timeout_seconds,
        )

    def _normalize(self, text: str) -> str:
        """Normalize text for robust phrase matching."""
        normalized = unicodedata.normalize("NFKD", text.lower())
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", ascii_text).strip()

    def _tokenize(self, text: str) -> set[str]:
        """Normalize and tokenize text for lexical matching."""
        normalized = self._normalize(text)
        tokens = re.findall(r"[a-z0-9]{3,}", normalized)
        return set(tokens)

    def _score_section(self, message_tokens: set[str], normalized_message: str, section_title: str, section_content: str) -> int:
        """Compute section relevance score while preserving current ranking rules."""
        normalized_title = self._normalize(section_title)
        title_tokens = self._tokenize(section_title)
        content_tokens = self._tokenize(section_content)

        title_hints = len(message_tokens.intersection(title_tokens))
        content_hints = len(message_tokens.intersection(content_tokens))
        exact_title_match = normalized_title in normalized_message

        # Strict relevance gate:
        # - accept if title matches at least one token, or
        # - accept if the full normalized title is present in the message.
        if title_hints == 0 and not exact_title_match:
            return 0

        return (title_hints * 100) + (50 if exact_title_match else 0) + (content_hints * 2)

    async def fetch_markdown(self) -> str:
        """Fetch markdown content from the configured KB URL with strict validation."""
        logger.info("Fetching KB markdown from URL.")
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self.kb_url)
        except httpx.TimeoutException as exc:
            logger.error("KB fetch timeout for url=%s", self.kb_url, exc_info=True)
            raise KBToolError("KB request timeout") from exc
        except httpx.RequestError as exc:
            logger.error("KB request failed for url=%s", self.kb_url, exc_info=True)
            raise KBToolError("KB request failed") from exc

        if response.status_code != 200:
            logger.warning(
                "KB fetch returned unexpected status_code=%s",
                response.status_code,
            )
            raise KBToolError(f"KB returned status {response.status_code}")

        if not response.content:
            logger.warning("KB fetch returned empty response body.")
            raise KBToolError("KB returned empty body")

        try:
            markdown = response.content.decode("utf-8")
        except UnicodeDecodeError as exc:
            logger.error("KB response body could not be decoded as UTF-8.", exc_info=True)
            raise KBToolError("KB response decode failed") from exc

        if not markdown.strip():
            logger.warning("KB decoded body is blank after whitespace normalization.")
            raise KBToolError("KB body is blank")

        logger.info("KB markdown fetched with status=%s and bytes=%s", response.status_code, len(markdown))
        return markdown

    def parse_markdown(self, markdown: str) -> List[Dict[str, Any]]:
        """
        Parse markdown content into level-2 sections (##) with associated content.

        Level-2 headings are treated as the main retrieval units.
        Subheadings remain part of the current section content.
        """
        logger.debug("Starting markdown parsing.")
        lines = markdown.splitlines()
        sections: List[Dict[str, Any]] = []

        current_section: str | None = None
        current_order = -1
        current_content_buffer: List[str] = []

        for raw_line in lines:
            line = raw_line.rstrip()
            header_match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line.strip())

            if header_match:
                heading_level = len(header_match.group(1))
                heading_text = header_match.group(2).strip()

                if heading_level == 2:
                    if current_section is not None:
                        content = "\n".join(current_content_buffer).strip()
                        if content:
                            sections.append(
                                {
                                    "section": current_section.strip(),
                                    "content": content,
                                    "level": 2,
                                    "order": current_order,
                                }
                            )

                    current_order += 1
                    current_section = heading_text
                    current_content_buffer = []
                    continue

                if current_section is not None:
                    current_content_buffer.append(line)
                continue

            if current_section is not None:
                current_content_buffer.append(line)

        if current_section is not None:
            content = "\n".join(current_content_buffer).strip()
            if content:
                sections.append(
                    {
                        "section": current_section.strip(),
                        "content": content,
                        "level": 2,
                        "order": current_order,
                    }
                )

        parsed_sections = [s for s in sections if str(s.get("content", "")).strip()]
        if not parsed_sections:
            logger.warning("Markdown parsing produced no non-empty sections.")
        else:
            logger.info("Markdown parsing produced %s section(s).", len(parsed_sections))
        return parsed_sections

    def select_relevant_sections(
        self,
        message: str,
        sections: List[Dict[str, Any]],
        max_sections: int = 3,
    ) -> List[KBSection]:
        """
        Rank sections by lexical overlap, prioritizing title matches heavily.

        A section is only considered relevant if:
        - it has at least one title token overlap, or
        - the normalized section title appears inside the normalized message.

        This prevents broad content-only false positives.
        """
        logger.debug("Selecting relevant sections with max_sections=%s.", max_sections)
        message_tokens = self._tokenize(message)
        normalized_message = self._normalize(message)

        if not message_tokens:
            logger.warning("Message tokenization produced no tokens; no context will be returned.")
            return []

        ranked: List[KBSection] = []

        for item in sections:
            if int(item.get("level", 0)) != 2:
                continue

            section_title = str(item.get("section", "")).strip()
            section_content = str(item.get("content", "")).strip()

            if not section_title or not section_content:
                continue

            score = self._score_section(
                message_tokens=message_tokens,
                normalized_message=normalized_message,
                section_title=section_title,
                section_content=section_content,
            )
            if score <= 0:
                continue

            ranked.append(
                {
                    "section": section_title,
                    "content": section_content,
                    "level": int(item.get("level", 2)),
                    "order": int(item.get("order", 0)),
                    "score": score,
                }
            )

        ranked.sort(key=lambda x: (-x["score"], x["order"]))
        selected = ranked[:max_sections]

        logger.info(
            "Selected %s relevant section(s) from %s total section(s).",
            len(selected),
            len(sections),
        )
        if not selected:
            logger.warning("No relevant section matched the provided message.")
        return selected

    async def search(self, message: str, max_sections: int = 3) -> KBSearchResult:
        """
        Retrieve structured context sections relevant to a user message.

        This method performs retrieval only. It does not generate final answers.
        """
        logger.info("Starting KB search for incoming message.")
        markdown = await self.fetch_markdown()
        sections = self.parse_markdown(markdown)
        ranked_context = self.select_relevant_sections(
            message=message,
            sections=sections,
            max_sections=max_sections,
        )
        sources = [item["section"] for item in ranked_context]

        logger.info("KB search completed with %s context section(s).", len(ranked_context))
        return {
            "context": ranked_context,
            "sources": sources,
        }