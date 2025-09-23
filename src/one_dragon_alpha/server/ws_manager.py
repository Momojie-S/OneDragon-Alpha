from typing import Dict

from fastapi import WebSocket


# Connection manager for tracking active WebSocket sessions
class WebSocketConnectionManager:
    """Manager for tracking WebSocket connections per session."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    def add_connection(self, session_id: str, websocket: WebSocket) -> None:
        """Add a WebSocket connection for a session."""
        self.active_connections[session_id] = websocket

    def remove_connection(self, session_id: str) -> None:
        """Remove a WebSocket connection for a session."""
        self.active_connections.pop(session_id, None)

    def get_connection(self, session_id: str) -> WebSocket | None:
        """Get WebSocket connection for a session."""
        return self.active_connections.get(session_id)