# -*- coding: utf-8 -*-
"""Qwen model integration for AgentScope.

This module provides Qwen chat model with OAuth 2.0 device code authentication
and automatic token refresh.
"""

from one_dragon_agent.core.agent.qwen.qwen_chat_model import QwenChatModel
from one_dragon_agent.core.agent.qwen.oauth import (
    QwenError,
    QwenOAuthClient,
    QwenDeviceAuthorization,
    QwenOAuthError,
    QwenOAuthToken,
    QwenRefreshTokenInvalidError,
    QwenTokenExpiredError,
    QwenTokenNotAvailableError,
    generate_pkce,
    login_qwen_oauth,
)
from one_dragon_agent.core.agent.qwen.token_manager import (
    QwenTokenManager,
    TokenPersistence,
)

__all__ = [
    # Models
    "QwenChatModel",
    # Token Manager
    "QwenTokenManager",
    "TokenPersistence",
    # OAuth Client
    "QwenOAuthClient",
    "generate_pkce",
    "login_qwen_oauth",
    # Data Types
    "QwenOAuthToken",
    "QwenDeviceAuthorization",
    # Exceptions
    "QwenError",
    "QwenOAuthError",
    "QwenRefreshTokenInvalidError",
    "QwenTokenExpiredError",
    "QwenTokenNotAvailableError",
]
