# -*- coding: utf-8 -*-
"""Qwen chat model implementation for AgentScope.

This module provides QwenChatModel which integrates Qwen's OAuth authentication
with AgentScope's OpenAIChatModel.
"""

from typing import Any

from agentscope.model import OpenAIChatModel

from one_dragon_agent.core.agent.qwen.oauth import QwenError
from one_dragon_agent.core.agent.qwen.token_manager import QwenTokenManager

# Export exceptions for convenience
__all__ = [
    "QwenChatModel",
    "QwenError",
]


class QwenChatModel(OpenAIChatModel):
    """Qwen chat model with automatic OAuth token management.

    This class inherits from AgentScope's OpenAIChatModel and automatically
    handles Qwen OAuth authentication and token refresh.

    Example:
        >>> model = QwenChatModel(model_name="coder-model")
        >>> response = model("Hello, Qwen!")

    """

    def __init__(
        self,
        model_name: str = "coder-model",
        client_id: str | None = None,
        token_path: str | None = None,
    ) -> None:
        """Initialize QwenChatModel.

        Args:
            model_name: Qwen model name (e.g., "coder-model", "vision-model").
            client_id: OAuth client ID (uses default if not provided).
            token_path: Path to store token file (uses default if not provided).

        """
        # Get token manager singleton
        self._token_manager = QwenTokenManager.get_instance(client_id, token_path)
        self._model_name = model_name
        self._full_model_id = self._get_full_model_id(model_name)
        self._token_initialized = False

        # Initialize parent with a placeholder token
        # The actual token will be loaded when needed
        super().__init__(
            model_name=self._full_model_id,
            api_key="qwen-oauth-placeholder",  # Placeholder
            client_args={"base_url": "https://portal.qwen.ai/v1"},
        )

    def _get_full_model_id(self, model_name: str) -> str:
        """Get full model ID with prefix.

        Args:
            model_name: Short model name.

        Returns:
            Full model ID (e.g., "qwen-portal/coder-model").

        """
        if model_name.startswith("qwen-portal/"):
            return model_name
        return f"qwen-portal/{model_name}"

    def _ensure_token(self) -> None:
        """Ensure token is loaded and update client if needed.

        This method should be called before any API usage.
        """
        if not self._token_initialized:
            import asyncio

            # Get token synchronously
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create new loop in thread to get token
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run, self._token_manager.get_access_token()
                        )
                        token = future.result(timeout=30)
                else:
                    token = asyncio.run(self._token_manager.get_access_token())
            except Exception as e:
                from one_dragon_agent.core.agent.qwen.oauth import (
                    QwenTokenNotAvailableError,
                )

                raise QwenTokenNotAvailableError(
                    f"Failed to get Qwen access token: {e}"
                )

            # Update the API key in the parent class
            self.api_key = token

            # Recreate the OpenAI client with new token
            self._setup_client()

            self._token_initialized = True

    def _setup_client(self) -> None:
        """Set up OpenAI client with current API key."""
        import openai

        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://portal.qwen.ai/v1",
        )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Call the model with Qwen token.

        Args:
            *args: Positional arguments to pass to parent.
            **kwargs: Keyword arguments to pass to parent.

        Returns:
            Model response.

        """
        self._ensure_token()
        return super().__call__(*args, **kwargs)
