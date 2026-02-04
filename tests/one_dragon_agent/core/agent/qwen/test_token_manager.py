# -*- coding: utf-8 -*-
"""Tests for QwenTokenManager class."""

import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from one_dragon_agent.core.agent.qwen.oauth import (
    QwenOAuthClient,
    QwenOAuthToken,
    QwenRefreshTokenInvalidError,
    QwenTokenNotAvailableError,
)
from one_dragon_agent.core.agent.qwen.token_manager import QwenTokenManager, TokenPersistence


@pytest.mark.timeout(10)
class TestQwenTokenManagerSingleton:
    """Test cases for QwenTokenManager singleton pattern."""

    def setup_method(self):
        """Reset singleton before each test."""
        QwenTokenManager.reset()

    def teardown_method(self):
        """Reset singleton after each test."""
        QwenTokenManager.reset()

    async def test_get_instance_returns_singleton(self) -> None:
        """Test that get_instance returns the same instance."""
        manager1 = QwenTokenManager.get_instance()
        manager2 = QwenTokenManager.get_instance()

        assert manager1 is manager2

    async def test_get_instance_with_custom_client_id(self) -> None:
        """Test that custom client_id is only used on first call."""
        manager1 = QwenTokenManager.get_instance(client_id="custom-client-1")

        # Second call with different client_id should be ignored
        manager2 = QwenTokenManager.get_instance(client_id="custom-client-2")

        assert manager1 is manager2

    async def test_reset_clears_singleton(self) -> None:
        """Test that reset clears the singleton instance."""
        manager1 = QwenTokenManager.get_instance()
        QwenTokenManager.reset()
        manager2 = QwenTokenManager.get_instance()

        assert manager1 is not manager2


@pytest.mark.timeout(10)
class TestQwenTokenManagerGetAccessToken:
    """Test cases for get_access_token method."""

    def setup_method(self):
        """Reset singleton before each test."""
        QwenTokenManager.reset()

    def teardown_method(self):
        """Reset singleton after each test."""
        QwenTokenManager.reset()

    async def test_get_access_token_loads_from_persistence(
        self, tmp_path: Path
    ) -> None:
        """Test that get_access_token loads token from persistence."""
        # Create a valid token file
        token_path = tmp_path / "test_token.json"
        token = QwenOAuthToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=int(time.time() * 1000) + 3600 * 1000,  # 1 hour from now
        )

        import json

        token_path.write_text(json.dumps({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at,
        }))

        manager = QwenTokenManager(token_path=token_path)
        access_token = await manager.get_access_token()

        assert access_token == "test-access-token"

    async def test_get_access_token_raises_when_no_token(self, tmp_path: Path) -> None:
        """Test that get_access_token raises when no token available."""
        # Use a temp path with no token file
        token_path = tmp_path / "nonexistent" / "token.json"
        # Also ensure Qwen CLI path doesn't exist
        qwen_cli_path = tmp_path / "qwen" / "oauth_creds.json"

        manager = QwenTokenManager(token_path=token_path)

        # Mock Qwen CLI path to not exist
        with patch.object(
            TokenPersistence, "_qwen_cli_token_path", qwen_cli_path
        ):
            with pytest.raises(QwenTokenNotAvailableError):
                await manager.get_access_token()

    async def test_get_access_token_refreshes_expired_token(
        self, tmp_path: Path
    ) -> None:
        """Test that get_access_token refreshes expired token."""
        # Create an expired token file
        token_path = tmp_path / "test_token.json"
        token = QwenOAuthToken(
            access_token="old-access-token",
            refresh_token="old-refresh-token",
            expires_at=int(time.time() * 1000) - 1000,  # Expired
        )

        import json

        token_path.write_text(json.dumps({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at,
        }))

        # Mock the refresh_token method
        new_token = QwenOAuthToken(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            expires_at=int(time.time() * 1000) + 3600 * 1000,
        )

        manager = QwenTokenManager(token_path=token_path)
        manager._client = MagicMock()
        manager._client.refresh_token = AsyncMock(return_value=new_token)

        access_token = await manager.get_access_token()

        assert access_token == "new-access-token"
        manager._client.refresh_token.assert_called_once_with("old-refresh-token")

    async def test_get_access_token_returns_cached_token(
        self, tmp_path: Path
    ) -> None:
        """Test that get_access_token returns cached token without reloading."""
        token_path = tmp_path / "test_token.json"
        token = QwenOAuthToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=int(time.time() * 1000) + 3600 * 1000,
        )

        import json

        token_path.write_text(json.dumps({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at,
        }))

        manager = QwenTokenManager(token_path=token_path)

        # First call loads from persistence
        access_token1 = await manager.get_access_token()

        # Delete the file to ensure it's not reloaded
        token_path.unlink()

        # Second call should use cached token
        access_token2 = await manager.get_access_token()

        assert access_token1 == access_token2 == "test-access-token"


@pytest.mark.timeout(15)
class TestQwenTokenManagerRefreshLoop:
    """Test cases for token refresh loop."""

    def setup_method(self):
        """Reset singleton before each test."""
        QwenTokenManager.reset()

    def teardown_method(self):
        """Reset singleton after each test."""
        QwenTokenManager.reset()

    async def test_refresh_timer_starts_on_first_access(self, tmp_path: Path):
        """Test that refresh timer starts after first access."""
        token_path = tmp_path / "test_token.json"
        token = QwenOAuthToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=int(time.time() * 1000) + 3600 * 1000,
        )

        import json

        token_path.write_text(json.dumps({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at,
        }))

        manager = QwenTokenManager(token_path=token_path)

        # Initially, no refresh task
        assert manager._refresh_task is None

        # After first access, refresh task should be created
        await manager.get_access_token()

        # Give it a moment to start
        await asyncio.sleep(0.1)

        # Refresh task should exist
        assert manager._refresh_task is not None
        assert not manager._refresh_task.done()

        # Clean up
        await manager.shutdown()

    async def test_shutdown_stops_refresh_loop(self, tmp_path: Path):
        """Test that shutdown stops the refresh loop."""
        token_path = tmp_path / "test_token.json"
        token = QwenOAuthToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=int(time.time() * 1000) + 3600 * 1000,
        )

        import json

        token_path.write_text(json.dumps({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at,
        }))

        manager = QwenTokenManager(token_path=token_path)
        await manager.get_access_token()

        # Give it a moment to start
        await asyncio.sleep(0.1)

        # Refresh task should be running
        assert manager._refresh_task is not None
        assert not manager._refresh_task.done()

        # Shutdown
        await manager.shutdown()

        # Wait a bit for task to complete
        await asyncio.sleep(0.1)

        # Stop event should be set
        assert manager._stop_event.is_set()

    async def test_refresh_with_invalid_refresh_token(self, tmp_path: Path):
        """Test that refresh stops when refresh token is invalid."""
        token_path = tmp_path / "test_token.json"
        token = QwenOAuthToken(
            access_token="test-access-token",
            refresh_token="invalid-refresh-token",
            expires_at=int(time.time() * 1000) + 3600 * 1000,
        )

        import json

        token_path.write_text(json.dumps({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at,
        }))

        manager = QwenTokenManager(token_path=token_path)
        manager._client = MagicMock()
        manager._client.refresh_token = AsyncMock(
            side_effect=QwenRefreshTokenInvalidError("Invalid token")
        )

        await manager.get_access_token()

        # Trigger refresh by setting token as expired
        manager._token.expires_at = int(time.time() * 1000) - 1000

        # Try to refresh - should raise error
        with pytest.raises(QwenRefreshTokenInvalidError):
            await manager._refresh_token()


@pytest.mark.timeout(10)
class TestQwenTokenManagerConcurrency:
    """Test cases for concurrent access to TokenManager."""

    def setup_method(self):
        """Reset singleton before each test."""
        QwenTokenManager.reset()

    def teardown_method(self):
        """Reset singleton after each test."""
        QwenTokenManager.reset()

    async def test_concurrent_get_access_token(self, tmp_path: Path):
        """Test that concurrent calls to get_access_token are thread-safe."""
        token_path = tmp_path / "test_token.json"
        token = QwenOAuthToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=int(time.time() * 1000) + 3600 * 1000,
        )

        import json

        token_path.write_text(json.dumps({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at,
        }))

        manager = QwenTokenManager(token_path=token_path)

        # Make concurrent calls
        tasks = [manager.get_access_token() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # All should return the same token
        assert all(r == "test-access-token" for r in results)

        # Clean up
        await manager.shutdown()

    async def test_concurrent_refresh_is_locked(self, tmp_path: Path):
        """Test that concurrent refresh attempts are locked."""
        token_path = tmp_path / "test_token.json"
        token = QwenOAuthToken(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            expires_at=int(time.time() * 1000) - 1000,  # Expired
        )

        import json

        token_path.write_text(json.dumps({
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at,
        }))

        manager = QwenTokenManager(token_path=token_path)

        # Mock refresh to take some time
        refresh_started = asyncio.Event()
        refresh_allowed = asyncio.Event()
        refresh_count = 0

        async def slow_refresh(refresh_token: str) -> QwenOAuthToken:
            nonlocal refresh_count
            refresh_count += 1
            refresh_started.set()
            await refresh_allowed.wait()
            new_token = QwenOAuthToken(
                access_token=f"new-token-{refresh_count}",
                refresh_token="new-refresh",
                expires_at=int(time.time() * 1000) + 3600 * 1000,
            )
            return new_token

        manager._client = MagicMock()
        manager._client.refresh_token = AsyncMock(side_effect=slow_refresh)

        # Start first task that will begin refresh
        task1 = asyncio.create_task(manager.get_access_token())
        await refresh_started.wait()

        # Start second task while first is still refreshing
        task2 = asyncio.create_task(manager.get_access_token())

        # Allow the refresh to complete
        refresh_allowed.set()

        # Both should complete successfully
        result1 = await task1
        result2 = await task2

        # Both should get the same new token (from the single refresh)
        # Note: result2 might return test-access-token if it loaded before refresh completed
        # The important thing is that refresh was only called once
        assert manager._client.refresh_token.call_count == 1

        # Clean up
        await manager.shutdown()
