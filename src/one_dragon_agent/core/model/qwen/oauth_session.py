# -*- coding: utf-8 -*-
"""OAuth 会话管理模块.

本模块管理 OAuth 2.0 设备码流程的会话状态，
使用内存存储（适合单机部署）。
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Literal

from one_dragon_agent.core.model.qwen.oauth import (
    QwenOAuthClient,
    QwenOAuthToken,
    QwenDeviceAuthorization,
    generate_pkce,
)
from one_dragon_agent.core.system.log import get_logger

logger = get_logger(__name__)


@dataclass
class OAuthSession:
    """OAuth 会话数据.

    Attributes:
        session_id: 会话 ID
        device_code: 设备码
        code_verifier: PKCE code verifier
        code_challenge: PKCE code challenge
        user_code: 用户码
        verification_uri: 验证链接
        verification_uri_complete: 完整验证链接
        expires_at: 过期时间戳（毫秒）
        interval: 轮询间隔（秒）
        created_at: 创建时间
        status: 会话状态
        token: 认证成功后的 token
        error: 错误信息
        last_poll_at: 最后轮询时间
        poll_count: 轮询次数
    """

    session_id: str
    device_code: str
    code_verifier: str
    code_challenge: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str | None
    expires_at: int
    interval: int | None
    created_at: datetime = field(default_factory=datetime.now)
    status: Literal["pending", "success", "error", "expired"] = "pending"
    token: QwenOAuthToken | None = None
    error: str | None = None
    last_poll_at: datetime | None = None
    poll_count: int = 0

    def is_expired(self) -> bool:
        """检查会话是否已过期.

        Returns:
            是否过期
        """
        return time.time() * 1000 > self.expires_at

    def can_poll(self, min_interval_ms: int = 1000) -> bool:
        """检查是否可以进行轮询.

        Args:
            min_interval_ms: 最小轮询间隔（毫秒）

        Returns:
            是否可以轮询
        """
        if self.last_poll_at is None:
            return True

        elapsed_ms = (datetime.now() - self.last_poll_at).total_seconds() * 1000
        return elapsed_ms >= min_interval_ms


class OAuthSessionManager:
    """OAuth 会话管理器.

    使用内存存储管理 OAuth 设备码流程会话。
    使用 asyncio.Lock 保证线程安全。

    Attributes:
        _sessions: 会话字典 {session_id: OAuthSession}
        _device_to_session: 设备码到会话 ID 的映射
        _lock: 异步锁
        _session_timeout: 会话超时时间（秒）
        _cleanup_interval: 清理间隔（秒）

    """

    def __init__(
        self,
        session_timeout: int = 900,  # 15 分钟
        cleanup_interval: int = 300,  # 5 分钟
    ) -> None:
        """初始化会话管理器.

        Args:
            session_timeout: 会话超时时间（秒），默认 900 秒（15 分钟）
            cleanup_interval: 清理间隔（秒），默认 300 秒（5 分钟）

        """
        self._sessions: dict[str, OAuthSession] = {}
        self._device_to_session: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._session_timeout = session_timeout
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: asyncio.Task | None = None

    async def create_session(
        self, client: QwenOAuthClient
    ) -> OAuthSession:
        """创建新的 OAuth 会话.

        Args:
            client: Qwen OAuth 客户端

        Returns:
            新创建的会话

        """
        # 生成 PKCE
        verifier, challenge = generate_pkce()

        # 获取设备码
        device_auth = await client.get_device_code(challenge)

        # 创建会话
        session_id = str(uuid.uuid4())

        session = OAuthSession(
            session_id=session_id,
            device_code=device_auth.device_code,
            code_verifier=verifier,
            code_challenge=challenge,
            user_code=device_auth.user_code,
            verification_uri=device_auth.verification_uri,
            verification_uri_complete=device_auth.verification_uri_complete,
            expires_at=int(time.time() * 1000) + device_auth.expires_in * 1000,
            interval=device_auth.interval,
        )

        async with self._lock:
            self._sessions[session_id] = session
            self._device_to_session[device_auth.device_code] = session_id

        logger.info(
            f"创建 OAuth 会话 {session_id}，"
            f"用户码: {session.user_code}"
        )

        # 启动清理任务
        self._start_cleanup_task()

        return session

    async def get_session(self, session_id: str) -> OAuthSession | None:
        """获取会话.

        Args:
            session_id: 会话 ID

        Returns:
            会话对象，如果不存在则返回 None

        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session and session.is_expired():
                session.status = "expired"
            return session

    async def get_session_by_device_code(
        self, device_code: str
    ) -> OAuthSession | None:
        """通过设备码获取会话.

        Args:
            device_code: 设备码

        Returns:
            会话对象，如果不存在则返回 None

        """
        async with self._lock:
            session_id = self._device_to_session.get(device_code)
            if not session_id:
                return None

            session = self._sessions.get(session_id)
            if session and session.is_expired():
                session.status = "expired"
            return session

    async def update_session_poll(self, session_id: str) -> None:
        """更新会话轮询信息.

        Args:
            session_id: 会话 ID

        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.last_poll_at = datetime.now()
                session.poll_count += 1

    async def mark_session_success(
        self, session_id: str, token: QwenOAuthToken
    ) -> None:
        """标记会话为成功.

        Args:
            session_id: 会话 ID
            token: OAuth token

        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.status = "success"
                session.token = token
                logger.info(f"会话 {session_id} 认证成功")

    async def mark_session_error(self, session_id: str, error: str) -> None:
        """标记会话为错误.

        Args:
            session_id: 会话 ID
            error: 错误信息

        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.status = "error"
                session.error = error
                logger.warning(f"会话 {session_id} 认证失败: {error}")

    async def mark_session_slow_down(self, session_id: str) -> None:
        """标记会话需要降低轮询频率.

        Args:
            session_id: 会话 ID

        """
        async with self._lock:
            session = self._sessions.get(session_id)
            if session and session.interval:
                # 增加轮询间隔
                session.interval = min(int(session.interval * 1.5), 10)
                logger.info(f"会话 {session_id} 轮询间隔调整为 {session.interval} 秒")

    def _start_cleanup_task(self) -> None:
        """启动清理任务."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        """定期清理过期会话."""
        while True:
            await asyncio.sleep(self._cleanup_interval)

            async with self._lock:
                now = time.time() * 1000
                expired_sessions = []

                for session_id, session in self._sessions.items():
                    # 清理超过过期时间 5 分钟的会话
                    if session.expires_at + 5 * 60 * 1000 < now:
                        expired_sessions.append(session_id)
                    # 清理已完成或出错的会话（超过 1 小时）
                    elif (
                        session.status in ("success", "error")
                        and (datetime.now() - session.created_at).total_seconds() > 3600
                    ):
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    session = self._sessions.pop(session_id, None)
                    if session:
                        self._device_to_session.pop(session.device_code, None)
                        logger.info(f"清理过期会话 {session_id}")

                # 如果没有会话了，停止清理任务
                if not self._sessions:
                    break

    async def shutdown(self) -> None:
        """关闭会话管理器."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            self._sessions.clear()
            self._device_to_session.clear()

        logger.info("OAuth 会话管理器已关闭")


# 全局会话管理器实例
_session_manager: OAuthSessionManager | None = None


def get_oauth_session_manager() -> OAuthSessionManager:
    """获取全局 OAuth 会话管理器实例.

    Returns:
        OAuthSessionManager 实例

    """
    global _session_manager
    if _session_manager is None:
        _session_manager = OAuthSessionManager()
    return _session_manager


def reset_oauth_session_manager() -> None:
    """重置全局会话管理器（用于测试）."""
    global _session_manager
    _session_manager = None
