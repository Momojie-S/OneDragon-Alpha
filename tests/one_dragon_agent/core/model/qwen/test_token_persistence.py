# -*- coding: utf-8 -*-
"""Tests for TokenPersistence class."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from one_dragon_agent.core.model.qwen.oauth import QwenOAuthToken
from one_dragon_agent.core.model.qwen.token_manager import TokenPersistence


@pytest.mark.timeout(10)
class TestTokenPersistence:
    """Test cases for the TokenPersistence class."""

    async def test_save_token_creates_file(self, tmp_path: Path) -> None:
        """Test that save_token creates a token file."""
        persistence = TokenPersistence(token_path=tmp_path / "test_token.json")

        token = QwenOAuthToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=1234567890000,
            resource_url="portal.qwen.ai",
        )

        await persistence.save_token(token)

        # Verify file exists
        assert persistence._token_path.exists()

    async def test_save_token_content(self, tmp_path: Path) -> None:
        """Test that save_token writes correct content."""
        persistence = TokenPersistence(token_path=tmp_path / "test_token.json")

        token = QwenOAuthToken(
            access_token="test-access-token-abc",
            refresh_token="test-refresh-token-xyz",
            expires_at=1234567890000,
            resource_url="portal.qwen.ai",
        )

        await persistence.save_token(token)

        # Read and verify content
        content = json.loads(persistence._token_path.read_text())
        assert content["access_token"] == "test-access-token-abc"
        assert content["refresh_token"] == "test-refresh-token-xyz"
        assert content["expires_at"] == 1234567890000
        assert content["resource_url"] == "portal.qwen.ai"

    async def test_save_token_without_resource_url(self, tmp_path: Path) -> None:
        """Test that save_token handles missing resource_url."""
        persistence = TokenPersistence(token_path=tmp_path / "test_token.json")

        token = QwenOAuthToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=1234567890000,
            resource_url=None,
        )

        await persistence.save_token(token)

        # Read and verify content
        content = json.loads(persistence._token_path.read_text())
        assert content["resource_url"] is None

    async def test_load_token_success(self, tmp_path: Path) -> None:
        """Test successful token loading."""
        persistence = TokenPersistence(token_path=tmp_path / "test_token.json")

        # First save a token
        token = QwenOAuthToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=1234567890000,
            resource_url="portal.qwen.ai",
        )
        await persistence.save_token(token)

        # Then load it
        loaded_token = await persistence.load_token()

        assert loaded_token is not None
        assert loaded_token.access_token == "test-access-token"
        assert loaded_token.refresh_token == "test-refresh-token"
        assert loaded_token.expires_at == 1234567890000
        assert loaded_token.resource_url == "portal.qwen.ai"

    async def test_load_token_from_qwen_cli_sync(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Test loading token synced from Qwen CLI location."""
        # Create temporary directories
        our_dir = tmp_path / "one_dragon_alpha"
        qwen_dir = tmp_path / "qwen"
        our_dir.mkdir()
        qwen_dir.mkdir()

        # Create token file in Qwen CLI location
        qwen_token_file = qwen_dir / "oauth_creds.json"
        token_data = {
            "access_token": "qwen-cli-token",
            "refresh_token": "qwen-cli-refresh",
            "expires_at": 1234567890000,
            "resource_url": "portal.qwen.ai",
        }
        qwen_token_file.write_text(json.dumps(token_data))

        # Patch the class attributes to use temp directories
        with patch.object(
            TokenPersistence, "_default_token_path", our_dir / "qwen_oauth_creds.json"
        ), patch.object(TokenPersistence, "_qwen_cli_token_path", qwen_token_file):
            persistence = TokenPersistence()
            loaded_token = await persistence.load_token()

            # Token should be loaded from Qwen CLI location
            assert loaded_token is not None
            assert loaded_token.access_token == "qwen-cli-token"

            # Token should be synced to our location
            assert persistence._token_path.exists()
            synced_content = json.loads(persistence._token_path.read_text())
            assert synced_content["access_token"] == "qwen-cli-token"

    async def test_load_token_file_not_exists(self, tmp_path: Path) -> None:
        """Test loading when token file doesn't exist and Qwen CLI location doesn't exist."""
        # Use a temp directory that doesn't have Qwen CLI token
        persistence = TokenPersistence(token_path=tmp_path / "nonexistent.json")

        # Mock the Qwen CLI token path to not exist
        with patch.object(
            TokenPersistence, "_qwen_cli_token_path", tmp_path / "nonexistent_qwen" / "oauth_creds.json"
        ):
            loaded_token = await persistence.load_token()

            assert loaded_token is None

    async def test_load_token_invalid_json(self, tmp_path: Path) -> None:
        """Test loading when token file contains invalid JSON."""
        persistence = TokenPersistence(token_path=tmp_path / "invalid.json")

        # Write invalid JSON
        persistence._token_path.write_text("{ invalid json }")

        # Mock the Qwen CLI token path to not exist
        with patch.object(
            TokenPersistence, "_qwen_cli_token_path", tmp_path / "nonexistent_qwen" / "oauth_creds.json"
        ):
            loaded_token = await persistence.load_token()

            assert loaded_token is None

    async def test_load_token_missing_required_fields(self, tmp_path: Path) -> None:
        """Test loading when token file is missing required fields."""
        persistence = TokenPersistence(token_path=tmp_path / "incomplete.json")

        # Write incomplete token data
        incomplete_data = {
            "access_token": "test-token",
            # Missing refresh_token and expires_at
        }
        persistence._token_path.write_text(json.dumps(incomplete_data))

        # Mock the Qwen CLI token path to not exist
        with patch.object(
            TokenPersistence, "_qwen_cli_token_path", tmp_path / "nonexistent_qwen" / "oauth_creds.json"
        ):
            # Should return None when fields are missing (caught by try/except)
            loaded_token = await persistence.load_token()
            assert loaded_token is None

    async def test_delete_token(self, tmp_path: Path) -> None:
        """Test deleting token file."""
        persistence = TokenPersistence(token_path=tmp_path / "test_token.json")

        # First create a token
        token = QwenOAuthToken(
            access_token="test-token",
            refresh_token="test-refresh",
            expires_at=1234567890000,
        )
        await persistence.save_token(token)

        # Verify file exists
        assert persistence._token_path.exists()

        # Delete token
        await persistence.delete_token()

        # Verify file is deleted
        assert not persistence._token_path.exists()

    async def test_delete_token_when_not_exists(self, tmp_path: Path) -> None:
        """Test deleting token when file doesn't exist (should not raise error)."""
        persistence = TokenPersistence(token_path=tmp_path / "nonexistent.json")

        # Should not raise an error
        await persistence.delete_token()

        assert True  # If we got here, no error was raised

    async def test_save_token_creates_parent_directory(
        self, tmp_path: Path
    ) -> None:
        """Test that save_token creates parent directory if it doesn't exist."""
        # Use a path with non-existent parent directory
        token_path = tmp_path / "subdir" / "test_token.json"
        persistence = TokenPersistence(token_path=token_path)

        token = QwenOAuthToken(
            access_token="test-token",
            refresh_token="test-refresh",
            expires_at=1234567890000,
        )

        await persistence.save_token(token)

        # Verify parent directory was created
        assert persistence._token_path.parent.exists()
        assert persistence._token_path.exists()
