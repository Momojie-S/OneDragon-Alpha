"""Global context management for OneDragon Alpha server."""

from typing import Optional

from one_dragon_alpha.server.ws_manager import WebSocketConnectionManager
from one_dragon_alpha.session.session_service import SessionService


class OneDragonAlphaContext:
    """Global context for OneDragon Alpha application."""
    
    _instance: Optional['OneDragonAlphaContext'] = None
    
    def __init__(self):
        """Initialize the context with required services."""
        self.session_service = SessionService()
        self.chat_ws_manager = WebSocketConnectionManager()
    
    @classmethod
    def get_instance(cls) -> 'OneDragonAlphaContext':
        """Get the global context instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def initialize(cls) -> 'OneDragonAlphaContext':
        """Initialize the global context."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset the global context."""
        cls._instance = None