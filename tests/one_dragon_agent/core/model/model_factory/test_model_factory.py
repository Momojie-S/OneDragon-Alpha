# -*- coding: utf-8 -*-
"""ModelFactory 单元测试."""

from datetime import datetime
from unittest.mock import Mock

import pytest
from agentscope.model import OpenAIChatModel

from one_dragon_agent.core.model.model_factory import ModelFactory
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
async def test_create_qwen_model(qwen_config):
    """测试创建 Qwen 模型."""
    from one_dragon_agent.core.model.qwen.qwen_chat_model import QwenChatModel

    model = ModelFactory.create_model(qwen_config, "qwen-max")

    assert isinstance(model, QwenChatModel)
    assert model.model_name == "qwen-max"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_model_id_not_in_config_raises_error(openai_config):
    """测试模型 ID 不在配置中抛出 ValueError."""
    with pytest.raises(ValueError, match="模型 ID 'invalid-model' 不在配置"):
        ModelFactory.create_model(openai_config, "invalid-model")
