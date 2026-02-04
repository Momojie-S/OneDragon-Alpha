# -*- coding: utf-8 -*-
"""Tests for QwenOAuthClient.get_device_code method."""

import base64
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from one_dragon_agent.core.agent.qwen.oauth import (
    QwenDeviceAuthorization,
    QwenOAuthClient,
    QwenOAuthError,
    generate_pkce,
)


@pytest.mark.timeout(10)
class TestGetDeviceCode:
    """Test cases for the get_device_code method."""

    async def test_get_device_code_success(self, mock_challenge: str) -> None:
        """Test successful device code retrieval."""
        mock_response = {
            "device_code": "test-device-code-123",
            "user_code": "ABCD-5678",
            "verification_uri": "https://chat.qwen.ai/authorize",
            "verification_uri_complete": "https://chat.qwen.ai/authorize?user_code=ABCD-5678&client=qwen-code",
            "expires_in": 900,
            "interval": 5,
        }

        with respx.mock:
            request = respx.post(
                "https://chat.qwen.ai/api/v1/oauth2/device/code"
            ).mock(return_value=httpx.Response(200, json=mock_response))

            client = QwenOAuthClient()
            result = await client.get_device_code(mock_challenge)

            assert isinstance(result, QwenDeviceAuthorization)
            assert result.device_code == "test-device-code-123"
            assert result.user_code == "ABCD-5678"
            assert result.verification_uri == "https://chat.qwen.ai/authorize"
            assert result.verification_uri_complete is not None
            assert result.expires_in == 900
            assert result.interval == 5

    async def test_get_device_code_without_verification_uri_complete(
        self, mock_challenge: str
    ) -> None:
        """Test device code retrieval without verification_uri_complete."""
        mock_response = {
            "device_code": "test-device-code-456",
            "user_code": "EFGH-9012",
            "verification_uri": "https://chat.qwen.ai/authorize",
            "expires_in": 900,
        }

        with respx.mock:
            respx.post("https://chat.qwen.ai/api/v1/oauth2/device/code").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            client = QwenOAuthClient()
            result = await client.get_device_code(mock_challenge)

            assert result.verification_uri_complete is None
            assert result.verification_uri == "https://chat.qwen.ai/authorize"

    async def test_get_device_code_http_error(self, mock_challenge: str) -> None:
        """Test device code retrieval with HTTP error."""
        with respx.mock:
            respx.post("https://chat.qwen.ai/api/v1/oauth2/device/code").mock(
                return_value=httpx.Response(400, text="Bad Request")
            )

            client = QwenOAuthClient()

            with pytest.raises(QwenOAuthError) as exc_info:
                await client.get_device_code(mock_challenge)

            assert "Qwen device authorization failed" in str(exc_info.value)

    async def test_get_device_code_missing_required_fields(
        self, mock_challenge: str
    ) -> None:
        """Test device code retrieval with missing required fields."""
        mock_response = {
            "device_code": "test-device-code-789",
            # Missing user_code
            "verification_uri": "https://chat.qwen.ai/authorize",
            "expires_in": 900,
        }

        with respx.mock:
            respx.post("https://chat.qwen.ai/api/v1/oauth2/device/code").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            client = QwenOAuthClient()

            with pytest.raises(QwenOAuthError) as exc_info:
                await client.get_device_code(mock_challenge)

            assert "incomplete payload" in str(exc_info.value)

    async def test_get_device_code_sends_correct_parameters(
        self, mock_challenge: str
    ) -> None:
        """Test that get_device_code sends correct request parameters."""
        mock_response = {
            "device_code": "test-device-code-000",
            "user_code": "TEST-0000",
            "verification_uri": "https://chat.qwen.ai/authorize",
            "expires_in": 900,
        }

        with respx.mock:
            request = respx.post(
                "https://chat.qwen.ai/api/v1/oauth2/device/code"
            ).mock(return_value=httpx.Response(200, json=mock_response))

            client = QwenOAuthClient()
            await client.get_device_code(mock_challenge)

            # Verify request was called
            assert request.call_count == 1

            # Get the request that was made
            received_request = request.calls[0].request

            # Check content type
            assert (
                received_request.headers.get("Content-Type")
                == "application/x-www-form-urlencoded"
            )

            # Check that the body contains required parameters
            body = received_request.content.decode()
            assert "client_id=" in body
            assert "scope=" in body
            assert f"code_challenge={mock_challenge}" in body
            assert "code_challenge_method=S256" in body

    async def test_get_device_code_with_custom_client_id(
        self, mock_challenge: str
    ) -> None:
        """Test device code retrieval with custom client ID."""
        mock_response = {
            "device_code": "test-device-code-custom",
            "user_code": "CUST-1234",
            "verification_uri": "https://chat.qwen.ai/authorize",
            "expires_in": 900,
        }

        with respx.mock:
            respx.post("https://chat.qwen.ai/api/v1/oauth2/device/code").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            custom_client_id = "my-custom-client-id"
            client = QwenOAuthClient(client_id=custom_client_id)
            result = await client.get_device_code(mock_challenge)

            assert result.device_code == "test-device-code-custom"
