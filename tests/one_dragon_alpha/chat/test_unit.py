# -*- coding: utf-8 -*-
"""ChatSession 单元测试.

这些测试使用 Mock 来验证 ChatSession 的模型切换逻辑，
不涉及真实的数据库连接或 AI 模型 API 调用。
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from agentscope.agent import ReActAgent
from agentscope.memory import InMemoryMemory
from agentscope.model import OpenAIChatModel

from one_dragon_agent.core.model.models import ModelConfigInternal, ModelInfo
from one_dragon_alpha.chat.chat_session import ChatSession


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
    config.created_at = datetime.now()
    config.updated_at = datetime.now()
    return config


@pytest.fixture
def mock_config_2():
    """创建第二个模型配置 Mock."""
    config = Mock(spec=ModelConfigInternal)
    config.id = 2
    config.name = "Test Config 2"
    config.provider = "openai"
    config.base_url = "https://api.openai.com/v2"
    config.api_key = "test-key-2"
    config.is_active = True
    config.models = [
        ModelInfo(model_id="gpt-3.5-turbo", support_vision=False, support_thinking=False),
    ]
    config.created_at = datetime.now()
    config.updated_at = datetime.now()
    return config


@pytest.fixture
def tushare_session():
    """创建 ChatSession 实例."""
    # 设置临时 WORKSPACE_DIR
    old_workspace = os.environ.get("WORKSPACE_DIR")
    os.environ["WORKSPACE_DIR"] = "/tmp/test_workspace"
    os.makedirs("/tmp/test_workspace", exist_ok=True)

    memory = InMemoryMemory()
    session_id = "test_session_001"
    session = ChatSession(session_id=session_id, memory=memory)

    yield session

    # 清理
    if old_workspace:
        os.environ["WORKSPACE_DIR"] = old_workspace
    else:
        os.environ.pop("WORKSPACE_DIR", None)


# ============================================================================
# 测试用例
# ============================================================================


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_first_chat_request_creates_agent(tushare_session, mock_config):
    """测试首次聊天请求创建 Agent."""
    # 首次调用时，_current_model_config_id 应该是 None
    assert tushare_session._current_model_config_id is None
    assert tushare_session._current_model_id is None
    # __init__ 中创建了占位 Agent，通过 agent 属性访问
    assert tushare_session.agent is not None


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_same_model_config_and_id_reuses_agent(tushare_session, mock_config):
    """测试相同的 model_config_id 和 model_id 复用 Agent."""
    # 第一次设置模型
    tushare_session.set_model(mock_config, "gpt-4")
    first_agent = tushare_session.agent
    first_agent_id = id(first_agent)

    # 第二次使用相同的配置和模型 ID
    tushare_session.set_model(mock_config, "gpt-4")
    second_agent = tushare_session.agent
    second_agent_id = id(second_agent)

    # Agent 应该被复用（对象 ID 相同）
    assert first_agent_id == second_agent_id
    assert tushare_session._current_model_config_id == 1
    assert tushare_session._current_model_id == "gpt-4"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_different_model_config_id_rebuilds_agent(tushare_session, mock_config, mock_config_2):
    """测试 model_config_id 不同时重建 Agent."""
    # 第一次设置模型（config 1）
    tushare_session.set_model(mock_config, "gpt-4")
    first_agent = tushare_session.agent
    first_agent_id = id(first_agent)

    # 第二次使用不同的配置（config 2）
    tushare_session.set_model(mock_config_2, "gpt-3.5-turbo")
    second_agent = tushare_session.agent
    second_agent_id = id(second_agent)

    # Agent 应该被重建（对象 ID 不同）
    assert first_agent_id != second_agent_id
    assert tushare_session._current_model_config_id == 2
    assert tushare_session._current_model_id == "gpt-3.5-turbo"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_different_model_id_rebuilds_agent(tushare_session, mock_config):
    """测试 model_id 不同时重建 Agent（配置相同）."""
    # 第一次设置模型（gpt-4）
    tushare_session.set_model(mock_config, "gpt-4")
    first_agent = tushare_session.agent
    first_agent_id = id(first_agent)

    # 第二次使用相同的配置但不同的模型 ID（gpt-4-turbo）
    tushare_session.set_model(mock_config, "gpt-4-turbo")
    second_agent = tushare_session.agent
    second_agent_id = id(second_agent)

    # Agent 应该被重建（对象 ID 不同）
    assert first_agent_id != second_agent_id
    assert tushare_session._current_model_config_id == 1
    assert tushare_session._current_model_id == "gpt-4-turbo"


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_analyse_agent_uses_same_config_and_model(tushare_session, mock_config):
    """测试分析 Agent 使用与主 Agent 相同的配置和模型."""
    # 设置 TUSHARE_API_TOKEN 环境变量
    os.environ["TUSHARE_API_TOKEN"] = "test_token"

    # 设置主 Agent
    tushare_session.set_model(mock_config, "gpt-4")
    main_agent_model = tushare_session.agent.model

    # 创建一个真实的分析 Agent（不是 Mock）
    analyse_agent = await tushare_session._get_analyse_by_code_agent(1)

    # 验证分析 Agent 使用与主 Agent 相同的模型
    assert analyse_agent.model == main_agent_model

    # 清理
    os.environ.pop("TUSHARE_API_TOKEN", None)


@pytest.mark.asyncio
@pytest.mark.timeout(10)
async def test_switching_model_clears_analyse_agent_cache(tushare_session, mock_config):
    """测试切换模型时清空分析 Agent 缓存."""
    # 设置模型
    tushare_session.set_model(mock_config, "gpt-4")

    # 手动添加一个分析 Agent 到缓存
    mock_analyse_agent = Mock(spec=ReActAgent)
    tushare_session._analyse_by_code_map[1] = mock_analyse_agent
    assert 1 in tushare_session._analyse_by_code_map

    # 切换到不同的模型
    tushare_session.set_model(mock_config, "gpt-4-turbo")

    # 验证分析 Agent 缓存被清空
    assert len(tushare_session._analyse_by_code_map) == 0
