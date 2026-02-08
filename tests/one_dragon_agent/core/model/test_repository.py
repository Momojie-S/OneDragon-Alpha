# -*- coding: utf-8 -*-
"""通用模型配置 Repository 层单元测试."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncSession

from one_dragon_agent.core.model.models import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
    ModelInfo,
)
from one_dragon_agent.core.model.repository import (
    ModelConfigRepository,
    ModelConfigORM,
)


@pytest.fixture
def mock_session() -> AsyncMock:
    """创建模拟的数据库会话.

    Returns:
        模拟的 AsyncSession
    """
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def sample_config_create() -> ModelConfigCreate:
    """创建示例配置创建请求.

    Returns:
        ModelConfigCreate 对象
    """
    return ModelConfigCreate(
        name="Test Config",
        provider="openai",
        base_url="https://api.openai.com",
        api_key="sk-test123",
        models=[
            ModelInfo(
                model_id="gpt-4",
                support_vision=True,
                support_thinking=False,
            )
        ],
        is_active=True,
    )


@pytest.fixture
def sample_config_response() -> ModelConfigResponse:
    """创建示例配置响应.

    Returns:
        ModelConfigResponse 对象
    """
    return ModelConfigResponse(
        id=1,
        name="Test Config",
        provider="openai",
        base_url="https://api.openai.com",
        models=[
            ModelInfo(
                model_id="gpt-4",
                support_vision=True,
                support_thinking=False,
            )
        ],
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestModelConfigORM:
    """ModelConfigORM 工具类测试."""

    def test_dict_to_orm_success(self) -> None:
        """测试将数据库记录转换为响应模型.

        Given: 数据库记录字典
        When: 调用 dict_to_orm
        Then: 返回正确的响应模型字典
        """
        # Given
        row = {
            "id": 1,
            "name": "Test Config",
            "provider": "openai",
            "base_url": "https://api.openai.com",
            "api_key": "sk-test123",
            "models": json.dumps([{"model_id": "gpt-4", "support_vision": True, "support_thinking": False}]),
            "is_active": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # When
        result = ModelConfigORM.dict_to_orm(row)

        # Then
        assert result["id"] == 1
        assert result["name"] == "Test Config"
        assert result["provider"] == "openai"
        assert len(result["models"]) == 1
        assert result["models"][0]["model_id"] == "gpt-4"
        assert "api_key" not in result  # 确保不包含 api_key

    def test_create_to_dict_success(self, sample_config_create: ModelConfigCreate) -> None:
        """测试将创建请求转换为数据库记录.

        Given: ModelConfigCreate 对象
        When: 调用 create_to_dict
        Then: 返回正确的数据库记录字典
        """
        # When
        result = ModelConfigORM.create_to_dict(sample_config_create)

        # Then
        assert result["name"] == "Test Config"
        assert result["provider"] == "openai"
        assert result["base_url"] == "https://api.openai.com"
        assert result["api_key"] == "sk-test123"
        assert "models" in result
        assert isinstance(result["models"], list)  # SQLAlchemy JSON 列接收 Python 列表
        assert len(result["models"]) == 1
        assert result["models"][0]["model_id"] == "gpt-4"


class TestModelConfigRepository:
    """ModelConfigRepository 仓库类测试."""

    @pytest.mark.asyncio
    async def test_create_config_success(
        self, mock_session: AsyncMock, sample_config_create: ModelConfigCreate
    ) -> None:
        """测试成功创建配置.

        Given: 有效的配置创建请求
        When: 调用 create_config
        Then: 返回创建的配置
        """
        # Given
        mock_result = MagicMock()
        mock_result.lastrowid = 1
        mock_session.execute.return_value = mock_result

        # 模拟 _get_by_id_internal 返回数据
        sample_response = ModelConfigResponse(
            id=1,
            name=sample_config_create.name,
            provider=sample_config_create.provider,
            base_url=sample_config_create.base_url,
            models=sample_config_create.models,
            is_active=sample_config_create.is_active,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # When
        repository = ModelConfigRepository(mock_session)
        with patch.object(repository, "_get_by_id_internal", return_value=sample_response):
            result = await repository.create_config(sample_config_create)

        # Then
        assert result.id == 1
        assert result.name == "Test Config"
        mock_session.execute.assert_called()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_config_by_id_success(
        self, mock_session: AsyncMock, sample_config_response: ModelConfigResponse
    ) -> None:
        """测试根据 ID 成功查询配置.

        Given: 配置 ID
        When: 调用 get_config_by_id
        Then: 返回配置对象
        """
        # Given
        config_id = 1

        # When
        repository = ModelConfigRepository(mock_session)
        with patch.object(repository, "_get_by_id_internal", return_value=sample_config_response):
            result = await repository.get_config_by_id(config_id)

        # Then
        assert result is not None
        assert result.id == 1
        assert result.name == "Test Config"

    @pytest.mark.asyncio
    async def test_get_config_by_id_not_found(self, mock_session: AsyncMock) -> None:
        """测试查询不存在的配置.

        Given: 不存在的配置 ID
        When: 调用 get_config_by_id
        Then: 返回 None
        """
        # Given
        config_id = 999

        # When
        repository = ModelConfigRepository(mock_session)
        with patch.object(repository, "_get_by_id_internal", side_effect=ValueError("Not found")):
            result = await repository.get_config_by_id(config_id)

        # Then
        assert result is None

    @pytest.mark.asyncio
    async def test_get_configs_pagination(
        self, mock_session: AsyncMock, sample_config_response: ModelConfigResponse
    ) -> None:
        """测试分页查询配置列表.

        Given: 分页参数
        When: 调用 get_configs
        Then: 返回分页结果
        """
        # Given
        page = 1
        page_size = 20

        # 模拟 count 查询返回
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 5
        mock_count_result.scalars.return_value.first.return_value = 5

        # 模拟数据查询返回
        mock_data_result = MagicMock()
        mock_data_result.fetchall.return_value = [
            MagicMock(
                _mapping=sample_config_response.model_dump()
            ) for _ in range(5)
        ]

        # 设置 execute 返回不同的结果
        mock_session.execute.return_value = mock_count_result
        call_count = [0]

        async def mock_execute(stmt):
            call_count[0] += 1
            if call_count[0] == 1:  # 第一次调用是 count
                return mock_count_result
            else:  # 第二次调用是数据查询
                return mock_data_result

        mock_session.execute = mock_execute

        # When
        repository = ModelConfigRepository(mock_session)
        configs, total = await repository.get_configs(page=page, page_size=page_size)

        # Then
        assert len(configs) == 5
        assert total == 5

    @pytest.mark.asyncio
    async def test_delete_config_success(self, mock_session: AsyncMock) -> None:
        """测试成功删除配置.

        Given: 配置 ID
        When: 调用 delete_config
        Then: 返回 True
        """
        # Given
        config_id = 1
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # When
        repository = ModelConfigRepository(mock_session)
        result = await repository.delete_config(config_id)

        # Then
        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_config_not_found(self, mock_session: AsyncMock) -> None:
        """测试删除不存在的配置.

        Given: 不存在的配置 ID
        When: 调用 delete_config
        Then: 抛出 ValueError
        """
        # Given
        config_id = 999
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        # When & Then
        repository = ModelConfigRepository(mock_session)
        with pytest.raises(ValueError, match="配置 ID 999 不存在"):
            await repository.delete_config(config_id)
