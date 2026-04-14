"""In-memory session state with TTL and short history window."""

import asyncio
import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class SessionTurn:
    """A single conversational turn stored per session."""
    user_message: str
    assistant_answer: str
    created_at: float # seconds since epoch


@dataclass
class SessionState:
    """Container for session turns and expiration metadata."""
    turns: list[SessionTurn] = field(default_factory=list)
    expires_at: float = 0.0 # seconds since epoch


class SessionMemory:
    """Keeps short isolated conversation history for each session_id."""

    def __init__(self, ttl_seconds: int = 1800, max_turns: int = 3) -> None:
        self.ttl_seconds = max(1, int(ttl_seconds))
        self.max_turns = max(1, int(max_turns))
        self._sessions: dict[str, SessionState] = {}
        self._lock = asyncio.Lock()

    def _now(self) -> float:
        return time.time()

    def _purge_expired_unlocked(self, now: float) -> None:
        expired = [session_id for session_id, state in self._sessions.items() if state.expires_at <= now]
        for session_id in expired:
            self._sessions.pop(session_id, None)
        if expired:
            logger.debug("Purged %s expired session(s).", len(expired))

    async def get_turns(self, session_id: str) -> list[SessionTurn]:
        """Return current turns for a session while refreshing its TTL."""
        now = self._now()
        async with self._lock:
            self._purge_expired_unlocked(now)
            state = self._sessions.get(session_id)
            if state is None:
                return []
            state.expires_at = now + self.ttl_seconds
            return list(state.turns)

    async def append_turn(self, session_id: str, user_message: str, assistant_answer: str) -> None:
        """Store a new turn and enforce short memory window and TTL."""
        now = self._now()
        async with self._lock:
            self._purge_expired_unlocked(now)
            state = self._sessions.get(session_id)
            if state is None:
                state = SessionState()
                self._sessions[session_id] = state

            state.turns.append(
                SessionTurn(
                    user_message=user_message,
                    assistant_answer=assistant_answer,
                    created_at=now,
                )
            )
            if len(state.turns) > self.max_turns:
                state.turns = state.turns[-self.max_turns :]
            state.expires_at = now + self.ttl_seconds
