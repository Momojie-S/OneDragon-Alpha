# -*- coding: utf-8 -*-
"""Tests for generate_pkce function."""

import base64
import hashlib

import pytest

from one_dragon_agent.core.agent.qwen.oauth import generate_pkce


class TestGeneratePkce:
    """Test cases for the generate_pkce function."""

    @pytest.mark.asyncio
    async def test_generate_pkce_returns_tuple(self) -> None:
        """Test that generate_pkce returns a tuple of two strings."""
        verifier, challenge = generate_pkce()

        assert isinstance(verifier, str)
        assert isinstance(challenge, str)

    @pytest.mark.asyncio
    async def test_verifier_is_base64url_encoded(self) -> None:
        """Test that the verifier is base64url encoded without padding."""
        verifier, _ = generate_pkce()

        # Should be base64url (no padding, URL-safe characters)
        assert "=" not in verifier
        assert "+" not in verifier
        assert "/" not in verifier

        # Should be decodable
        try:
            base64.urlsafe_b64encode(
                base64.urlsafe_b64decode(verifier + "==")
            ).decode().rstrip("=")
        except Exception as e:
            pytest.fail(f"Failed to decode verifier: {e}")

    @pytest.mark.asyncio
    async def test_challenge_is_base64url_encoded(self) -> None:
        """Test that the challenge is base64url encoded without padding."""
        _, challenge = generate_pkce()

        # Should be base64url (no padding, URL-safe characters)
        assert "=" not in challenge
        assert "+" not in challenge
        assert "/" not in challenge

    @pytest.mark.asyncio
    async def test_challenge_is_sha256_of_verifier(self) -> None:
        """Test that challenge is SHA256 hash of verifier."""
        verifier, challenge = generate_pkce()

        # Compute expected challenge
        expected_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode().rstrip("=")

        assert challenge == expected_challenge

    @pytest.mark.asyncio
    async def test_verifier_length_is_reasonable(self) -> None:
        """Test that verifier has reasonable length."""
        verifier, _ = generate_pkce()

        # 32 bytes encoded as base64url = ~43 characters
        assert len(verifier) >= 40
        assert len(verifier) <= 50

    @pytest.mark.asyncio
    async def test_challenge_length_is_reasonable(self) -> None:
        """Test that challenge has reasonable length."""
        _, challenge = generate_pkce()

        # SHA256 hash (32 bytes) encoded as base64url = ~43 characters
        assert len(challenge) >= 40
        assert len(challenge) <= 50

    @pytest.mark.asyncio
    async def test_generate_pkce_produces_unique_values(self) -> None:
        """Test that generate_pkce produces unique values each call."""
        verifier1, challenge1 = generate_pkce()
        verifier2, challenge2 = generate_pkce()

        # Different calls should produce different values
        assert verifier1 != verifier2
        assert challenge1 != challenge2
