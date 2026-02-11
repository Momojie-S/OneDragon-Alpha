# -*- coding: utf-8 -*-
"""ModelFactory 单元测试."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from agentscope.model import OpenAIChatModel

from one_dragon_agent.core.model.model_factory import ModelFactory, QwenChatModelWithConfig
from one_dragon_agent.core.model.models import ModelConfigInternal, ModelInfo


@pytest.fixture
def openai_config():
    """创建 OpenAI 配置."""
    return ModelConfigInternal(
        id=1,
        name="OpenAI Config",
        provider="openai",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
        is_active=True,
        models=[
            ModelInfo(model_id="gpt-4", support_vision=False, support_thinking=False),
            ModelInfo(model_id="gpt-4-vision", support_vision=True, support_thinking=False),
        ],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def qwen_config():
    """创建 Qwen 配置."""
    import time
    # 创建一个未来的过期时间（24小时后）
    expires_at = int(time.time() * 1000) + (24 * 60 * 60 * 1000)

    return ModelConfigInternal(
        id=2,
        name="Qwen Config",
        provider="qwen",
        base_url="",
        api_key="",
        is_active=True,
        models=[
            ModelInfo(model_id="qwen-max", support_vision=False, support_thinking=True),
        ],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        # OAuth 相关字段
        oauth_access_token="encrypted_test_token",
        oauth_token_type="Bearer",
        oauth_refresh_token="encrypted_refresh_token",
        oauth_expires_at=expires_at,
        oauth_scope="openid profile email model.completion",
        oauth_metadata=None,
    )


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_create_openai_model(openai_config):
    """测试创建 OpenAI 模型."""
    model = ModelFactory.create_model(openai_config, "gpt-4")

    assert isinstance(model, OpenAIChatModel)
    assert model.model_name == "gpt-4"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
@patch("one_dragon_agent.core.model.qwen.token_encryption.get_token_encryption")
async def test_create_qwen_model(mock_get_encryption, qwen_config):
    """测试创建 Qwen 模型."""
    # Mock token encryption
    mock_encryption = Mock()
    mock_encryption.decrypt.return_value = "test_access_token"
    mock_get_encryption.return_value = mock_encryption

    model = ModelFactory.create_model(qwen_config, "qwen-max")

    assert isinstance(model, QwenChatModelWithConfig)
    assert model._model_name == "qwen-max"
    assert model._access_token == "test_access_token"
    assert model._config_id == 2


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_model_id_not_in_config_raises_error(openai_config):
    """测试模型 ID 不在配置中抛出 ValueError."""
    with pytest.raises(ValueError, match="模型 ID 'invalid-model' 不在配置"):
        ModelFactory.create_model(openai_config, "invalid-model")
