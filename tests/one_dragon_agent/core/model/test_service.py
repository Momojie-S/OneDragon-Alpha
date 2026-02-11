# -*- coding: utf-8 -*-
"""通用模型配置 Service 层单元测试（简化版本）.

由于测试文件格式问题，这是一个简化版本。
建议使用真实的数据库集成测试来验证功能。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from one_dragon_agent.core.model.models import (
    ModelConfigCreate,
    ModelConfigResponse,
    ModelInfo,
    PaginatedModelConfigResponse,
)
from one_dragon_agent.core.model.service import ModelConfigService


@pytest.fixture
def mock_session() -> AsyncMock:
    """创建模拟的数据库会话."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_config_create() -> ModelConfigCreate:
    """创建示例配置创建请求."""
    return ModelConfigCreate(
        name="Test Config",
        provider="openai",
        base_url="https://api.openai.com",
        api_key="sk-test123",
        models=[ModelInfo(model_id="gpt-4", support_vision=True, support_thinking=False)],
    )


@pytest.mark.asyncio
async def test_create_model_config_success(mock_session: AsyncMock, sample_config_create: ModelConfigCreate) -> None:
    """测试成功创建配置."""
    service = ModelConfigService(mock_session)
    mock_repository = AsyncMock()
    mock_repository.create_config.return_value = ModelConfigResponse(
        id=1,
        name=sample_config_create.name,
        provider=sample_config_create.provider,
        base_url=sample_config_create.base_url,
        models=sample_config_create.models,
        is_active=True,
        created_at=MagicMock(),
        updated_at=MagicMock(),
    )

    with patch.object(service, "_repository", mock_repository):
        result = await service.create_model_config(sample_config_create)

    assert result.name == "Test Config"


@pytest.mark.asyncio
async def test_list_model_configs_success(mock_session: AsyncMock) -> None:
    """测试成功获取配置列表."""
    service = ModelConfigService(mock_session)
    mock_repository = AsyncMock()
    mock_repository.get_configs.return_value = ([], 0)

    with patch.object(service, "_repository", mock_repository):
        result = await service.list_model_configs(page=1, page_size=20)

    assert isinstance(result, PaginatedModelConfigResponse)
    assert result.total == 0


@pytest.mark.asyncio
async def test_test_connection_success() -> None:
    """测试成功连接."""
    from one_dragon_agent.core.model.models import TestConnectionRequest

    request = TestConnectionRequest(
        base_url="https://api.openai.com",
        api_key="sk-test",
        model_id="gpt-3.5-turbo"
    )

    # 模拟服务实例
    mock_session = AsyncMock(spec=AsyncSession)
    service = ModelConfigService(mock_session)

    # 创建模拟的响应消息
    mock_response_msg = MagicMock()
    mock_response_msg.get_text_content.return_value = "Hello! How can I help you today?"

    # Mock ModelFactory.create_model 返回模拟模型
    mock_model = MagicMock()

    # Mock ReActAgent
    mock_agent = AsyncMock()
    mock_agent.return_value = mock_response_msg
    mock_agent.set_console_output_enabled = MagicMock()

    # 使用多个 patch 来模拟不同的组件
    # 注意：需要 patch 在导入时的位置
    with patch("one_dragon_agent.core.model.model_factory.ModelFactory.create_model", return_value=mock_model), \
         patch("agentscope.agent.ReActAgent", return_value=mock_agent):

        result = await service.test_connection(request)

    assert result.success is True
    assert "连接成功" in result.message
    assert "Hello! How can I help you today?" in result.message
