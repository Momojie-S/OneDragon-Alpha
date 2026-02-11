# -*- coding: utf-8 -*-
"""OAuth 会话管理器测试."""

import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from one_dragon_agent.core.model.qwen.oauth import (
    QwenOAuthClient,
    QwenDeviceAuthorization,
    QwenOAuthToken,
)
from one_dragon_agent.core.model.qwen.oauth_session import (
    OAuthSession,
    OAuthSessionManager,
    get_oauth_session_manager,
    reset_oauth_session_manager,
)


@pytest.fixture
def mock_device_auth():
    """创建模拟的设备授权响应.

    Returns:
        QwenDeviceAuthorization 对象
    """
    return QwenDeviceAuthorization(
        device_code="test-device-code-123",
        user_code="ABCD-1234",
        verification_uri="https://qwen.ai/verify",
        verification_uri_complete="https://qwen.ai/verify?code=ABCD-1234",
        expires_in=900,
        interval=5,
    )


@pytest.fixture
def mock_oauth_client():
    """创建模拟的 OAuth 客户端.

    Returns:
        模拟的 QwenOAuthClient
    """
    client = MagicMock(spec=QwenOAuthClient)
    return client


@pytest.fixture
def sample_token():
    """创建示例 OAuth token.

    Returns:
        QwenOAuthToken 对象
    """
    return QwenOAuthToken(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expires_at=int(time.time() * 1000) + 3600 * 1000,  # 1 小时后过期
        resource_url="https://portal.qwen.ai",
    )


@pytest.mark.timeout(10)
class TestOAuthSession:
    """OAuth 会话数据类测试."""

    def test_init(self) -> None:
        """测试初始化."""
        session = OAuthSession(
            session_id="test-session-id",
            device_code="device-123",
            code_verifier="verifier-abc",
            code_challenge="challenge-xyz",
            user_code="ABCD-1234",
            verification_uri="https://qwen.ai/verify",
            verification_uri_complete="https://qwen.ai/verify?code=ABCD-1234",
            expires_at=int(time.time() * 1000) + 900000,
            interval=5,
        )

        assert session.session_id == "test-session-id"
        assert session.status == "pending"
        assert session.token is None
        assert session.error is None
        assert session.poll_count == 0

    def test_is_expired_false(self) -> None:
        """测试未过期的会话."""
        session = OAuthSession(
            session_id="test",
            device_code="device",
            code_verifier="verifier",
            code_challenge="challenge",
            user_code="ABCD",
            verification_uri="https://qwen.ai",
            verification_uri_complete=None,
            expires_at=int(time.time() * 1000) + 10000,  # 10 秒后过期
            interval=5,
        )

        assert not session.is_expired()

    def test_is_expired_true(self) -> None:
        """测试已过期的会话."""
        session = OAuthSession(
            session_id="test",
            device_code="device",
            code_verifier="verifier",
            code_challenge="challenge",
            user_code="ABCD",
            verification_uri="https://qwen.ai",
            verification_uri_complete=None,
            expires_at=int(time.time() * 1000) - 1000,  # 1 秒前已过期
            interval=5,
        )

        assert session.is_expired()

    def test_can_poll_first_time(self) -> None:
        """测试首次轮询."""
        session = OAuthSession(
            session_id="test",
            device_code="device",
            code_verifier="verifier",
            code_challenge="challenge",
            user_code="ABCD",
            verification_uri="https://qwen.ai",
            verification_uri_complete=None,
            expires_at=int(time.time() * 1000) + 900000,
            interval=5,
            last_poll_at=None,
        )

        assert session.can_poll()

    def test_can_poll_after_interval(self) -> None:
        """测试间隔后可以轮询."""
        session = OAuthSession(
            session_id="test",
            device_code="device",
            code_verifier="verifier",
            code_challenge="challenge",
            user_code="ABCD",
            verification_uri="https://qwen.ai",
            verification_uri_complete=None,
            expires_at=int(time.time() * 1000) + 900000,
            interval=5,
            last_poll_at=datetime.now() - timedelta(seconds=2),
        )

        assert session.can_poll(min_interval_ms=1000)


@pytest.mark.timeout(10)
class TestOAuthSessionManager:
    """OAuth 会话管理器测试."""

    @pytest.fixture
    def manager(self):
        """创建会话管理器实例."""
        # 重置全局实例
        reset_oauth_session_manager()
        return OAuthSessionManager()

    async def test_create_session(
        self, manager, mock_device_auth
    ) -> None:
        """测试创建会话."""
        with patch(
            "one_dragon_agent.core.model.qwen.oauth_session.QwenOAuthClient"
        ) as MockClient:
            mock_client = MagicMock()
            mock_client.get_device_code = AsyncMock(
                return_value=mock_device_auth
            )
            MockClient.return_value = mock_client

            session = await manager.create_session(mock_client)

            assert session.session_id is not None
            assert session.device_code == mock_device_auth.device_code
            assert session.user_code == mock_device_auth.user_code
            assert session.verification_uri == mock_device_auth.verification_uri
            assert session.status == "pending"

    async def test_get_session_by_id(self, manager) -> None:
        """测试通过 ID 获取会话."""
        # 创建一个模拟会话
        session_id = "test-session-id"
        session = OAuthSession(
            session_id=session_id,
            device_code="device",
            code_verifier="verifier",
            code_challenge="challenge",
            user_code="ABCD",
            verification_uri="https://qwen.ai",
            verification_uri_complete=None,
            expires_at=int(time.time() * 1000) + 900000,
            interval=5,
        )

        manager._sessions[session_id] = session

        # 获取会话
        retrieved = await manager.get_session(session_id)
        assert retrieved is not None
        assert retrieved.session_id == session_id

    async def test_get_session_not_found(self, manager) -> None:
        """测试获取不存在的会话."""
        retrieved = await manager.get_session("non-existent")
        assert retrieved is None

    async def test_get_session_by_device_code(self, manager) -> None:
        """测试通过设备码获取会话."""
        session_id = "test-session"
        device_code = "device-code-123"

        session = OAuthSession(
            session_id=session_id,
            device_code=device_code,
            code_verifier="verifier",
            code_challenge="challenge",
            user_code="ABCD",
            verification_uri="https://qwen.ai",
            verification_uri_complete=None,
            expires_at=int(time.time() * 1000) + 900000,
            interval=5,
        )

        manager._sessions[session_id] = session
        manager._device_to_session[device_code] = session_id

        # 通过设备码获取
        retrieved = await manager.get_session_by_device_code(device_code)
        assert retrieved is not None
        assert retrieved.session_id == session_id

    async def test_mark_session_success(
        self, manager, sample_token
    ) -> None:
        """测试标记会话为成功."""
        session_id = "test-session"

        session = OAuthSession(
            session_id=session_id,
            device_code="device",
            code_verifier="verifier",
            code_challenge="challenge",
            user_code="ABCD",
            verification_uri="https://qwen.ai",
            verification_uri_complete=None,
            expires_at=int(time.time() * 1000) + 900000,
            interval=5,
        )

        manager._sessions[session_id] = session

        # 标记为成功
        await manager.mark_session_success(session_id, sample_token)

        assert session.status == "success"
        assert session.token == sample_token

    async def test_mark_session_error(self, manager) -> None:
        """测试标记会话为错误."""
        session_id = "test-session"
        error_msg = "授权被拒绝"

        session = OAuthSession(
            session_id=session_id,
            device_code="device",
            code_verifier="verifier",
            code_challenge="challenge",
            user_code="ABCD",
            verification_uri="https://qwen.ai",
            verification_uri_complete=None,
            expires_at=int(time.time() * 1000) + 900000,
            interval=5,
        )

        manager._sessions[session_id] = session

        # 标记为错误
        await manager.mark_session_error(session_id, error_msg)

        assert session.status == "error"
        assert session.error == error_msg

    async def test_mark_session_slow_down(self, manager) -> None:
        """测试标记降低轮询频率."""
        session_id = "test-session"
        original_interval = 5

        session = OAuthSession(
            session_id=session_id,
            device_code="device",
            code_verifier="verifier",
            code_challenge="challenge",
            user_code="ABCD",
            verification_uri="https://qwen.ai",
            verification_uri_complete=None,
            expires_at=int(time.time() * 1000) + 900000,
            interval=original_interval,
        )

        manager._sessions[session_id] = session

        # 标记降低频率
        await manager.mark_session_slow_down(session_id)

        # interval 应该增加
        assert session.interval > original_interval

    async def test_update_session_poll(self, manager) -> None:
        """测试更新轮询信息."""
        session_id = "test-session"

        session = OAuthSession(
            session_id=session_id,
            device_code="device",
            code_verifier="verifier",
            code_challenge="challenge",
            user_code="ABCD",
            verification_uri="https://qwen.ai",
            verification_uri_complete=None,
            expires_at=int(time.time() * 1000) + 900000,
            interval=5,
            poll_count=0,
        )

        manager._sessions[session_id] = session

        # 更新轮询
        await manager.update_session_poll(session_id)

        assert session.last_poll_at is not None
        assert session.poll_count == 1

        # 再次更新
        await manager.update_session_poll(session_id)
        assert session.poll_count == 2


class TestGlobalSessionManager:
    """全局会话管理器测试."""

    def test_get_singleton(self) -> None:
        """测试获取单例."""
        reset_oauth_session_manager()

        manager1 = get_oauth_session_manager()
        manager2 = get_oauth_session_manager()

        assert manager1 is manager2

    def test_reset_singleton(self) -> None:
        """测试重置单例."""
        reset_oauth_session_manager()

        manager1 = get_oauth_session_manager()
        reset_oauth_session_manager()
        manager2 = get_oauth_session_manager()

        # 重置后应该是新实例
        assert manager1 is not manager2
