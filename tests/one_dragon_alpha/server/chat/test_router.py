# -*- coding: utf-8 -*-
"""聊天路由单元测试.

这些测试验证聊天路由的请求验证逻辑，
使用 Mock 来避免真实的数据库连接。
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from one_dragon_alpha.server.chat.router import ChatRequest, router
from one_dragon_agent.core.model.models import ModelConfigInternal, ModelInfo
from one_dragon_agent.core.system.log import get_logger

logger = get_logger(__name__)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_config():
    """创建模型配置 Mock."""
    config = Mock(spec=ModelConfigInternal)
    config.id = 1
    config.name = "Test Config"
    config.provider = "openai"
    config.base_url = "https://api.openai.com/v1"
    config.api_key = "test-key"
    config.is_active = True
    config.models = [
        ModelInfo(model_id="gpt-4", support_vision=False, support_thinking=False),
        ModelInfo(model_id="gpt-4-turbo", support_vision=True, support_thinking=False),
    ]
    return config


@pytest.fixture
def mock_disabled_config():
    """创建已禁用的模型配置 Mock."""
    config = Mock(spec=ModelConfigInternal)
    config.id = 2
    config.name = "Disabled Config"
    config.provider = "openai"
    config.base_url = "https://api.openai.com/v1"
    config.api_key = "test-key"
    config.is_active = False  # 已禁用
    config.models = [
        ModelInfo(model_id="gpt-4", support_vision=False, support_thinking=False),
    ]
    return config


@pytest.fixture
def mock_db_session():
    """创建数据库会话 Mock."""
    session = AsyncMock(spec=AsyncSession)
    return session


# ============================================================================
# ChatRequest 验证测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_chat_request_missing_model_config_id():
    """测试缺少 model_config_id 返回 400 错误."""
    # Pydantic 会自动验证必填字段
    with pytest.raises(Exception):  # Pydantic ValidationError
        ChatRequest(
            session_id="test_session",
            user_input="Hello",
            # model_config_id 缺失
            model_id="gpt-4",
        )


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_chat_request_missing_model_id():
    """测试缺少 model_id 返回 400 错误."""
    # Pydantic 会自动验证必填字段
    with pytest.raises(Exception):  # Pydantic ValidationError
        ChatRequest(
            session_id="test_session",
            user_input="Hello",
            model_config_id=1,
            # model_id 缺失
        )


# ============================================================================
# 配置验证测试
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@patch("one_dragon_agent.core.model.service.ModelConfigService")
async def test_nonexistent_config_id_returns_404(mock_service_class, mock_config, mock_db_session):
    """测试不存在的 config_id 返回 404 错误."""
    # 模拟 ModelConfigService
    mock_service = AsyncMock()
    mock_service.get_model_config_internal.side_effect = ValueError("配置不存在")
    mock_service_class.return_value = mock_service

    # 创建测试客户端
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        response = client.post(
            "/chat/stream",
            json={
                "session_id": "test_session",
                "user_input": "Hello",
                "model_config_id": 999,  # 不存在的配置
                "model_id": "gpt-4",
            },
        )

    # 验证返回 404 错误
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@patch("one_dragon_agent.core.model.service.ModelConfigService")
async def test_disabled_config_id_returns_400(mock_service_class, mock_disabled_config, mock_db_session):
    """测试已禁用的 config_id 返回 400 错误."""
    # 模拟 ModelConfigService
    mock_service = AsyncMock()
    mock_service.get_model_config_internal.return_value = mock_disabled_config
    mock_service_class.return_value = mock_service

    # 创建测试客户端
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        response = client.post(
            "/chat/stream",
            json={
                "session_id": "test_session",
                "user_input": "Hello",
                "model_config_id": 2,  # 已禁用的配置
                "model_id": "gpt-4",
            },
        )

    # 验证返回 400 错误
    assert response.status_code == 400
    assert "已禁用" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@patch("one_dragon_agent.core.model.service.ModelConfigService")
async def test_model_id_not_in_config_returns_400(mock_service_class, mock_config, mock_db_session):
    """测试 model_id 不在配置中返回 400 错误."""
    # 模拟 ModelConfigService
    mock_service = AsyncMock()
    mock_service.get_model_config_internal.return_value = mock_config
    mock_service_class.return_value = mock_service

    # 创建测试客户端
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        response = client.post(
            "/chat/stream",
            json={
                "session_id": "test_session",
                "user_input": "Hello",
                "model_config_id": 1,
                "model_id": "invalid-model",  # 不在配置中的模型
            },
        )

    # 验证返回 400 错误
    assert response.status_code == 400
    assert "不在配置中" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@patch("one_dragon_agent.core.model.service.ModelConfigService")
@patch("one_dragon_alpha.server.chat.router.get_session")
async def test_valid_config_and_model_id_succeeds(
    mock_get_session, mock_service_class, mock_config, mock_db_session
):
    """测试有效的 config_id 和 model_id 成功处理请求."""
    # 模拟 ModelConfigService
    mock_service = AsyncMock()
    mock_service.get_model_config_internal.return_value = mock_config
    mock_service_class.return_value = mock_service

    # 模拟 Session
    mock_session = MagicMock()
    mock_session.chat = AsyncMock()
    async def mock_chat_gen():
        from one_dragon_alpha.session.session_message import SessionMessage
        yield SessionMessage(None, False, True)
    mock_session.chat.return_value = mock_chat_gen()
    mock_get_session.return_value = ("test_session", mock_session)

    # 创建测试客户端
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    with TestClient(app) as client:
        response = client.post(
            "/chat/stream",
            json={
                "session_id": "test_session",
                "user_input": "Hello",
                "model_config_id": 1,
                "model_id": "gpt-4",
            },
        )

    # 验证返回 200（成功）
    # 注意：由于是流式响应，TestClient 可能无法完全模拟
    # 这里我们主要验证没有抛出异常
    assert response.status_code == 200
