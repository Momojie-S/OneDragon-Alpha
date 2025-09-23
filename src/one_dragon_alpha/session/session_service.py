from typing import Optional

import shortuuid
from agentscope.memory import InMemoryMemory, MemoryBase

from one_dragon_alpha.agent.tushare.tushare_session import TushareSession
from one_dragon_alpha.session.session import Session


class SessionService:
    """Service for managing chat sessions and agents.

    This service provides methods to create, retrieve, and manage
    chat sessions with their corresponding agents.

    Attributes:
        _memory_cache: Dictionary storing session ID to memory mapping.
        _session_cache: Dictionary storing session ID to Session mapping.
    """

    def __init__(self):
        """Initialize the session service."""
        self._memory_cache: dict[str, MemoryBase] = {}
        self._session_cache: dict[str, Session] = {}

    def create_session(self) -> str:
        """Create a new chat session and return the session ID.

        This method generates a unique session ID and initializes
        a new agent for the session.

        Returns:
            The unique session ID for the new session.
        """
        session_id = shortuuid.uuid()

        memory = InMemoryMemory()
        self._memory_cache[session_id] = memory

        session = TushareSession(session_id, memory)
        self._session_cache[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get the session associated with a session ID.

        Args:
            session_id: The session ID to retrieve the session for.

        Returns:
            The session instance if session exists, None otherwise.
        """
        return self._session_cache.get(session_id)