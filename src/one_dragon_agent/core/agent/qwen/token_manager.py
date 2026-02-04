# -*- coding: utf-8 -*-
"""Qwen OAuth token 管理模块.

本模块提供 Qwen OAuth 认证的 token 持久化和自动刷新功能。
"""

import asyncio
import json
import time
from pathlib import Path

from one_dragon_agent.core.system.log import get_logger

from one_dragon_agent.core.agent.qwen.oauth import (
    QwenOAuthClient,
    QwenOAuthToken,
    QwenRefreshTokenInvalidError,
    QwenTokenNotAvailableError,
)

logger = get_logger(__name__)


class TokenPersistence:
    """Token 持久化到文件系统.

    本类处理 token 存储逻辑，包括：
    1. 主存储位置：~/.one_dragon_alpha/qwen_oauth_creds.json
    2. 从以下位置同步：~/.qwen/oauth_creds.json（Qwen CLI 位置）
    3. 如果 token 存在于 Qwen CLI 位置但不存在于我们的位置，自动同步.
    """

    _default_token_path = Path.home() / ".one_dragon_alpha" / "qwen_oauth_creds.json"
    _qwen_cli_token_path = Path.home() / ".qwen" / "oauth_creds.json"

    def __init__(self, token_path: str | Path | None = None) -> None:
        """初始化 token 持久化.

        Args:
            token_path: 存储 token 文件的路径。若未提供则使用默认路径。

        """
        self._token_path = Path(token_path) if token_path else self._default_token_path

    async def save_token(self, token: QwenOAuthToken) -> None:
        """保存 token 到文件.

        Args:
            token: 要保存的 QwenOAuthToken。

        """
        self._token_path.parent.mkdir(parents=True, exist_ok=True)

        token_data = {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at,
            "resource_url": token.resource_url,
        }

        self._token_path.write_text(
            json.dumps(token_data, indent=2),
            encoding="utf-8",
        )

        # 设置文件权限为 0600（仅所有者可读写）
        try:
            self._token_path.chmod(0o600)
        except OSError as e:
            logger.warning(f"Failed to set token file permissions: {e}")

        logger.info(f"Token saved to {self._token_path}")

    async def load_token(self) -> QwenOAuthToken | None:
        """从文件加载 token.

        加载策略（按顺序）：
        1. 尝试我们的默认位置：~/.one_dragon_alpha/qwen_oauth_creds.json
        2. 如果未找到，尝试从 Qwen CLI 同步：~/.qwen/oauth_creds.json
        3. 如果仍未找到，返回 None（调用者应触发新登录）

        Returns:
            如果找到且有效则返回 QwenOAuthToken，否则返回 None。

        """
        # 步骤 1：首先尝试从我们的位置加载
        if self._token_path.exists():
            try:
                text = self._token_path.read_text(encoding="utf-8")
                data = json.loads(text)

                token = QwenOAuthToken(
                    access_token=data["access_token"],
                    refresh_token=data["refresh_token"],
                    expires_at=data["expires_at"],
                    resource_url=data.get("resource_url"),
                )
                logger.info(f"Token loaded from our location: {self._token_path}")
                return token
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to load token from our location: {e}")

        # 步骤 2：我们的位置未找到，尝试从 Qwen CLI 同步
        if self._qwen_cli_token_path.exists():
            try:
                text = self._qwen_cli_token_path.read_text(encoding="utf-8")
                data = json.loads(text)

                token = QwenOAuthToken(
                    access_token=data["access_token"],
                    refresh_token=data["refresh_token"],
                    expires_at=data["expires_at"],
                    resource_url=data.get("resource_url"),
                )

                # Sync to our location
                await self.save_token(token)
                logger.info(
                    f"Token synced from Qwen CLI ({self._qwen_cli_token_path}) "
                    f"to our location ({self._token_path})"
                )
                return token

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Failed to sync token from Qwen CLI: {e}")

        # Step 3: No token found anywhere, return None
        logger.info("No token found in our location or Qwen CLI location")
        return None

    async def delete_token(self) -> None:
        """Delete token file."""
        if self._token_path.exists():
            self._token_path.unlink()


class QwenTokenManager:
    """Qwen token manager with auto-refresh capability.

    This class implements singleton pattern and manages token lifecycle,
    including persistence and automatic background refresh.
    """

    _instance: "QwenTokenManager | None" = None

    def __init__(
        self,
        client_id: str | None = None,
        token_path: str | Path | None = None,
    ) -> None:
        """Initialize QwenTokenManager.

        Args:
            client_id: OAuth client ID. Uses default if not provided.
            token_path: Path to store token file. Uses default if not provided.

        """
        self._client = QwenOAuthClient(client_id)
        self._persistence = TokenPersistence(token_path)

        self._token: QwenOAuthToken | None = None
        self._refresh_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(
        cls,
        client_id: str | None = None,
        token_path: str | Path | None = None,
    ) -> "QwenTokenManager":
        """Get global singleton instance of QwenTokenManager.

        Args:
            client_id: OAuth client ID (only used on first call).
            token_path: Path to store token file (only used on first call).

        Returns:
            Global QwenTokenManager instance.

        """
        if cls._instance is None:
            cls._instance = cls(client_id, token_path)
        return cls._instance

    @classmethod
    async def reset_async(cls) -> None:
        """Reset singleton instance asynchronously (for testing).

        This method waits for the background refresh task to complete before clearing.
        """
        if cls._instance:
            # Set stop event and wait for task to complete
            cls._instance._stop_event.set()
            if cls._instance._refresh_task and not cls._instance._refresh_task.done():
                await cls._instance._refresh_task
        cls._instance = None

    @classmethod
    def reset(cls) -> None:
        """Reset singleton instance (for testing).

        Note: This is a synchronous method that only sets the stop event.
        For proper cleanup in tests, use reset_async() instead.
        """
        if cls._instance:
            # Set stop event and clear instance
            cls._instance._stop_event.set()
        cls._instance = None

    async def get_access_token(self) -> str:
        """Get current access token.

        Loads token from persistence or triggers authentication on first call.
        Starts background refresh timer if not already running.

        Returns:
            Current access token.

        """
        if self._token is None:
            # Try loading from persistence first
            self._token = await self._persistence.load_token()

            if self._token is None:
                raise QwenTokenNotAvailableError(
                    "No valid token found. Please authenticate first."
                )

            # Check if token is expired
            if self._token.expires_at < time.time() * 1000:
                # Token expired, try refresh
                await self._refresh_token()
            else:
                # Token valid, start refresh timer
                self._start_refresh_timer()

        return self._token.access_token

    def _start_refresh_timer(self) -> None:
        """Start background refresh timer if not already running."""
        if self._refresh_task is None or self._refresh_task.done():
            self._stop_event.clear()
            self._refresh_task = asyncio.create_task(self._refresh_loop())
            logger.info("Token auto-refresh timer started")

    async def _refresh_loop(self) -> None:
        """Background task loop for automatic token refresh."""
        while not self._stop_event.is_set():
            if self._token is None:
                break

            # Calculate next refresh time (5 minutes before expiration)
            expires_at = self._token.expires_at
            refresh_at = expires_at - 5 * 60 * 1000  # 5 minutes buffer
            now_ms = int(time.time() * 1000)

            if refresh_at > now_ms:
                wait_seconds = (refresh_at - now_ms) / 1000
            else:
                # Already past refresh time, wait 1 minute
                wait_seconds = 60

            try:
                # Wait until refresh time or stop event
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=wait_seconds,
                )
                break  # Stop event set
            except asyncio.TimeoutError:
                pass  # Timeout, proceed with refresh

            # Perform token refresh
            try:
                await self._refresh_token()
                logger.info("Token auto-refresh successful")
            except QwenRefreshTokenInvalidError:
                logger.error("Refresh token invalid, stopping auto-refresh")
                break
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}, retrying in 60 seconds")
                await asyncio.sleep(60)

    async def _refresh_token(self) -> None:
        """Refresh access token using refresh token.

        Raises:
            QwenRefreshTokenInvalidError: If refresh token is invalid.
            QwenOAuthError: If refresh request fails.

        """
        async with self._lock:
            if self._token is None:
                raise QwenTokenNotAvailableError("No token to refresh")

            new_token = await self._client.refresh_token(self._token.refresh_token)
            self._token = new_token
            await self._persistence.save_token(new_token)

    async def shutdown(self) -> None:
        """Shutdown token manager and stop refresh timer."""
        self._stop_event.set()

        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

        logger.info("TokenManager shutdown complete")
