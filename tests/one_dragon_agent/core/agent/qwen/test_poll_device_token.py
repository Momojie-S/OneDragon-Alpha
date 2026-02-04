# -*- coding: utf-8 -*-
"""Tests for QwenOAuthClient.poll_device_token method."""

import httpx
import pytest
import respx

from one_dragon_agent.core.agent.qwen.oauth import (
    QwenOAuthClient,
    QwenOAuthError,
    QwenOAuthToken,
)


@pytest.mark.timeout(10)
class TestPollDeviceToken:
    """Test cases for the poll_device_token method."""

    async def test_poll_device_token_success(self) -> None:
        """Test successful token retrieval."""
        import time

        mock_response = {
            "access_token": "test-access-token-123",
            "refresh_token": "test-refresh-token-456",
            "expires_in": 7200,
            "resource_url": "portal.qwen.ai",
        }

        with respx.mock:
            respx.post("https://chat.qwen.ai/api/v1/oauth2/token").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            client = QwenOAuthClient()
            result = await client.poll_device_token(
                device_code="test-device-code",
                code_verifier="test-verifier",
            )

            assert result.status == "success"
            assert result.token.access_token == "test-access-token-123"
            assert result.token.refresh_token == "test-refresh-token-456"
            assert isinstance(result.token.expires_at, int)

    async def test_poll_device_token_pending(self) -> None:
        """Test polling when authorization is pending."""
        mock_response = {
            "error": "authorization_pending",
        }

        with respx.mock:
            respx.post("https://chat.qwen.ai/api/v1/oauth2/token").mock(
                return_value=httpx.Response(400, json=mock_response)
            )

            client = QwenOAuthClient()
            result = await client.poll_device_token(
                device_code="test-device-code",
                code_verifier="test-verifier",
            )

            assert result.status == "pending"
            assert result.slow_down is False

    async def test_poll_device_token_slow_down(self) -> None:
        """Test polling when server requests slow down."""
        mock_response = {
            "error": "slow_down",
        }

        with respx.mock:
            respx.post("https://chat.qwen.ai/api/v1/oauth2/token").mock(
                return_value=httpx.Response(400, json=mock_response)
            )

            client = QwenOAuthClient()
            result = await client.poll_device_token(
                device_code="test-device-code",
                code_verifier="test-verifier",
            )

            assert result.status == "pending"
            assert result.slow_down is True

    async def test_poll_device_token_error(self) -> None:
        """Test polling when authorization fails."""
        mock_response = {
            "error": "access_denied",
            "error_description": "User denied access",
        }

        with respx.mock:
            respx.post("https://chat.qwen.ai/api/v1/oauth2/token").mock(
                return_value=httpx.Response(400, json=mock_response)
            )

            client = QwenOAuthClient()
            result = await client.poll_device_token(
                device_code="test-device-code",
                code_verifier="test-verifier",
            )

            assert result.status == "error"
            assert "User denied access" in result.message

    async def test_poll_device_token_missing_tokens(self) -> None:
        """Test polling when response is missing required tokens."""
        mock_response = {
            "access_token": "test-access-token",
            # Missing refresh_token and expires_in
        }

        with respx.mock:
            respx.post("https://chat.qwen.ai/api/v1/oauth2/token").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            client = QwenOAuthClient()
            result = await client.poll_device_token(
                device_code="test-device-code",
                code_verifier="test-verifier",
            )

            assert result.status == "error"
            assert "Incomplete token payload" in result.message

    async def test_poll_device_token_sends_correct_parameters(self) -> None:
        """Test that poll_device_token sends correct request parameters."""
        mock_response = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 7200,
        }

        with respx.mock:
            request = respx.post("https://chat.qwen.ai/api/v1/oauth2/token").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            client = QwenOAuthClient()
            await client.poll_device_token(
                device_code="test-device-123",
                code_verifier="test-verifier-abc",
            )

            # Verify request was made
            assert request.call_count == 1

            # Check request body contains required parameters
            body = request.calls[0].request.content.decode()
            assert "grant_type=urn:ietf:params:oauth:grant-type:device_code" in body
            assert "device_code=test-device-123" in body
            assert "code_verifier=test-verifier-abc" in body
            assert "client_id=" in body

    async def test_poll_device_token_with_custom_client_id(self) -> None:
        """Test polling with custom client ID."""
        mock_response = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "expires_in": 7200,
        }

        with respx.mock:
            request = respx.post("https://chat.qwen.ai/api/v1/oauth2/token").mock(
                return_value=httpx.Response(200, json=mock_response)
            )

            custom_client_id = "my-custom-client-id"
            client = QwenOAuthClient(client_id=custom_client_id)
            await client.poll_device_token(
                device_code="test-device",
                code_verifier="test-verifier",
            )

            # Check that custom client_id was sent
            body = request.calls[0].request.content.decode()
            assert f"client_id={custom_client_id}" in body

    async def test_poll_device_token_non_json_error_response(self) -> None:
        """Test polling when error response is not JSON."""
        with respx.mock:
            respx.post("https://chat.qwen.ai/api/v1/oauth2/token").mock(
                return_value=httpx.Response(500, text="Internal Server Error")
            )

            client = QwenOAuthClient()
            result = await client.poll_device_token(
                device_code="test-device-code",
                code_verifier="test-verifier",
            )

            assert result.status == "error"
            assert "Internal Server Error" in result.message
