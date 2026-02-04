# -*- coding: utf-8 -*-
"""Fixtures for Qwen OAuth tests."""

import base64
import hashlib
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_verifier() -> str:
    """Generate a mock code verifier.

    Returns:
        A base64url-encoded verifier string.
    """
    # Use a fixed test value
    return "dGVzdC12ZXJpZmllci0xMjM0NTY3ODkwMTIzNDU2Nzg"


@pytest.fixture
def mock_challenge(mock_verifier: str) -> str:
    """Generate a mock code challenge.

    Args:
        mock_verifier: The mock verifier.

    Returns:
        A base64url-encoded challenge string.
    """
    return base64.urlsafe_b64encode(
        hashlib.sha256(mock_verifier.encode()).digest()
    ).decode().rstrip("=")


@pytest.fixture
def mock_device_code_response() -> dict:
    """Mock device code response from Qwen API.

    Returns:
        A dictionary mimicking the Qwen device code API response.
    """
    return {
        "device_code": "test-device-code-12345678",
        "user_code": "ABCD-1234",
        "verification_uri": "https://chat.qwen.ai/authorize",
        "verification_uri_complete": "https://chat.qwen.ai/authorize?user_code=ABCD-1234&client=qwen-code",
        "expires_in": 900,
        "interval": 5,
    }


@pytest.fixture
def mock_token_response() -> dict:
    """Mock token response from Qwen API.

    Returns:
        A dictionary mimicking the Qwen token API response.
    """

    return {
        "access_token": "test-access-token-abcdef123456",
        "refresh_token": "test-refresh-token-xyz789",
        "expires_in": 7200,
        "resource_url": "portal.qwen.ai",
    }


@pytest.fixture
def mock_oauth_client():
    """Create a mock QwenOAuthClient.

    Returns:
        A MagicMock object with async methods.
    """
    client = MagicMock()
    client.get_device_code = AsyncMock()
    client.poll_device_token = AsyncMock()
    client.refresh_token = AsyncMock()
    return client
