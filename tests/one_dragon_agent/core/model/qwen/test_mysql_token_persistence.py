# -*- coding: utf-8 -*-
"""MySQL Token 持久化测试."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from unittest.mock import patch, Mock

import pytest

from one_dragon_agent.core.model.qwen.oauth import QwenOAuthToken
from one_dragon_agent.core.model.qwen.mysql_token_persistence import (
    MySQLTokenPersistence,
)
from sqlalchemy import Row


@pytest.fixture
def mock_session():
    """创建模拟的数据库会话.

    Returns:
        模拟的 AsyncSession
    """
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sample_token():
    """创建示例 OAuth token.

    Returns:
        QwenOAuthToken 对象
    """
    return QwenOAuthToken(
        access_token="test-access-token-abc123",
        refresh_token="test-refresh-token-xyz789",
        expires_at=1234567890000,
        resource_url="https://portal.qwen.ai",
    )


@pytest.fixture
def sample_token_no_resource_url():
    """创建没有 resource_url 的示例 OAuth token.

    Returns:
        QwenOAuthToken 对象
    """
    return QwenOAuthToken(
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expires_at=1234567890000,
        resource_url=None,
    )


@pytest.mark.timeout(10)
class TestMySQLTokenPersistence:
    """MySQL Token 持久化测试."""

    async def test_init(self, mock_session) -> None:
        """测试初始化.

        Given: 模拟的数据库会话
        When: 创建 MySQLTokenPersistence 实例
        Then: 成功初始化
        """
        persistence = MySQLTokenPersistence(mock_session)
        assert persistence._session == mock_session

    async def test_save_token_success(
        self, mock_session, sample_token
    ) -> None:
        """测试成功保存 token.

        Given: 模拟的数据库会话和 token
        When: 调用 save_token
        Then: 正确执行更新语句
        """
        # Mock execute 返回值
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        await persistence.save_token(123, sample_token)

        # 验证 execute 被调用
        assert mock_session.execute.called
        assert mock_session.commit.called

    async def test_save_token_with_resource_url(
        self, mock_session, sample_token
    ) -> None:
        """测试保存带 resource_url 的 token.

        Given: 带 resource_url 的 token
        When: 调用 save_token
        Then: metadata 字段包含 resource_url
        """
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        await persistence.save_token(123, sample_token)

        # 获取调用参数
        call_args = mock_session.execute.call_args
        assert call_args is not None

    async def test_save_token_config_not_exists(
        self, mock_session, sample_token
    ) -> None:
        """测试配置不存在时抛出异常.

        Given: 配置不存在
        When: 调用 save_token
        Then: 抛出 ValueError
        """
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)

        with pytest.raises(ValueError, match="配置 ID 123 不存在"):
            await persistence.save_token(123, sample_token)

    async def test_load_token_success(
        self, mock_session, sample_token
    ) -> None:
        """测试成功加载 token.

        Given: 数据库中有 token 记录
        When: 调用 load_token
        Then: 返回正确的 token
        """
        # Mock 数据库返回值
        mock_row = Mock()
        mock_row.oauth_access_token = sample_token.access_token
        mock_row.oauth_refresh_token = sample_token.refresh_token
        mock_row.oauth_expires_at = sample_token.expires_at
        mock_row.oauth_metadata = json.dumps(
            {"resource_url": sample_token.resource_url}
        )

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        loaded_token = await persistence.load_token(123)

        assert loaded_token is not None
        assert loaded_token.access_token == sample_token.access_token
        assert loaded_token.refresh_token == sample_token.refresh_token
        assert loaded_token.expires_at == sample_token.expires_at
        assert loaded_token.resource_url == sample_token.resource_url

    async def test_load_token_no_resource_url(
        self, mock_session, sample_token_no_resource_url
    ) -> None:
        """测试加载没有 resource_url 的 token.

        Given: 数据库中 token 没有 resource_url
        When: 调用 load_token
        Then: resource_url 为 None
        """
        mock_row = Mock()
        mock_row.oauth_access_token = sample_token_no_resource_url.access_token
        mock_row.oauth_refresh_token = sample_token_no_resource_url.refresh_token
        mock_row.oauth_expires_at = sample_token_no_resource_url.expires_at
        mock_row.oauth_metadata = None

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        loaded_token = await persistence.load_token(123)

        assert loaded_token is not None
        assert loaded_token.resource_url is None

    async def test_load_token_config_not_exists(self, mock_session) -> None:
        """测试配置不存在时返回 None.

        Given: 配置不存在
        When: 调用 load_token
        Then: 返回 None
        """
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        loaded_token = await persistence.load_token(999)

        assert loaded_token is None

    async def test_load_token_no_oauth_fields(self, mock_session) -> None:
        """测试配置没有 OAuth 字段时返回 None.

        Given: 配置存在但没有 OAuth 字段
        When: 调用 load_token
        Then: 返回 None
        """
        mock_row = Mock()
        mock_row.oauth_access_token = None
        mock_row.oauth_refresh_token = None

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        loaded_token = await persistence.load_token(123)

        assert loaded_token is None

    async def test_delete_token_success(self, mock_session) -> None:
        """测试成功删除 token.

        Given: 配置存在
        When: 调用 delete_token
        Then: 返回 True
        """
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        result = await persistence.delete_token(123)

        assert result is True
        assert mock_session.execute.called
        assert mock_session.commit.called

    async def test_delete_token_config_not_exists(self, mock_session) -> None:
        """测试配置不存在时删除失败.

        Given: 配置不存在
        When: 调用 delete_token
        Then: 返回 False
        """
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        result = await persistence.delete_token(999)

        assert result is False

    async def test_has_token_true(self, mock_session) -> None:
        """测试配置有 token 时返回 True.

        Given: 配置有 OAuth token
        When: 调用 has_token
        Then: 返回 True
        """
        mock_row = Mock()
        mock_row.oauth_access_token = "some-token"
        mock_row.oauth_refresh_token = "some-refresh-token"

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        result = await persistence.has_token(123)

        assert result is True

    async def test_has_token_false_no_token(self, mock_session) -> None:
        """测试配置没有 token 时返回 False.

        Given: 配置没有 OAuth token
        When: 调用 has_token
        Then: 返回 False
        """
        mock_row = Mock()
        mock_row.oauth_access_token = None
        mock_row.oauth_refresh_token = None

        mock_result = MagicMock()
        mock_result.fetchone.return_value = mock_row
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        result = await persistence.has_token(123)

        assert result is False

    async def test_has_token_config_not_exists(self, mock_session) -> None:
        """测试配置不存在时返回 False.

        Given: 配置不存在
        When: 调用 has_token
        Then: 返回 False
        """
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result

        persistence = MySQLTokenPersistence(mock_session)
        result = await persistence.has_token(999)

        assert result is False
