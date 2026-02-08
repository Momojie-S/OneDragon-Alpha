# -*- coding: utf-8 -*-
"""通用模型配置 API 集成测试."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from one_dragon_agent.core.model.models import (
    ModelConfigCreate,
    ModelConfigResponse,
    ModelInfo,
    PaginatedModelConfigResponse,
)
from one_dragon_agent.core.model.router import get_db_session, router


@pytest.fixture
def mock_session() -> AsyncMock:
    """创建模拟的数据库会话.

    Returns:
        模拟的 AsyncSession
    """
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def test_client(mock_session: AsyncMock) -> TestClient:
    """创建测试客户端.

    Args:
        mock_session: 模拟的数据库会话

    Returns:
        FastAPI 测试客户端
    """
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    # 覆盖依赖注入
    app.dependency_overrides[get_db_session] = lambda: mock_session

    return TestClient(app)


@pytest.fixture
def sample_config_response() -> ModelConfigResponse:
    """创建示例配置响应.

    Returns:
        ModelConfigResponse 对象
    """
    now = datetime.now()
    return ModelConfigResponse(
        id=1,
        name="Test Config",
        provider="openai",
        base_url="https://api.openai.com",
        models=[
            ModelInfo(model_id="gpt-4", support_vision=True, support_thinking=False)
        ],
        is_active=True,
        created_at=now,
        updated_at=now,
    )


class TestModelConfigAPI:
    """模型配置 API 测试类."""

    def test_create_config_success(self, test_client: TestClient, mock_session: AsyncMock) -> None:
        """测试成功创建配置.

        Given: 有效的配置创建请求
        When: POST /api/models/configs
        Then: 返回 201 和创建的配置
        """
        # Given
        request_data = {
            "name": "Test Config",
            "provider": "openai",
            "base_url": "https://api.openai.com",
            "api_key": "sk-test123",
            "models": [
                {
                    "model_id": "gpt-4",
                    "support_vision": True,
                    "support_thinking": False,
                }
            ],
            "is_active": True,
        }

        # 模拟服务层返回
        mock_service = AsyncMock()
        now = datetime.now()
        mock_service.create_model_config.return_value = ModelConfigResponse(
            id=1,
            created_at=now,
            updated_at=now,
            **request_data,
        )

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.post("/api/models/configs", json=request_data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "Test Config"
        assert "api_key" not in data  # 确保不返回 api_key

    def test_create_config_invalid_provider_fails(
        self, test_client: TestClient, mock_session: AsyncMock
    ) -> None:
        """测试创建配置时 provider 无效.

        Given: provider 不是 "openai"
        When: POST /api/models/configs
        Then: 返回 400 错误
        """
        # Given
        request_data = {
            "name": "Test Config",
            "provider": "invalid",
            "base_url": "https://api.openai.com",
            "api_key": "sk-test123",
            "models": [{"model_id": "gpt-4"}],
        }

        # When
        response = test_client.post("/api/models/configs", json=request_data)

        # Then
        # Pydantic 验证失败
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_configs_default_pagination(
        self, test_client: TestClient, mock_session: AsyncMock
    ) -> None:
        """测试获取配置列表（默认分页）.

        Given: 不提供分页参数
        When: GET /api/models/configs
        Then: 返回分页响应（默认值）
        """
        # Given
        mock_service = AsyncMock()
        mock_service.list_model_configs.return_value = PaginatedModelConfigResponse(
            total=0, page=1, page_size=20, items=[]
        )

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.get("/api/models/configs")

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_configs_with_pagination(
        self, test_client: TestClient, mock_session: AsyncMock
    ) -> None:
        """测试获取配置列表（自定义分页）.

        Given: 提供分页参数
        When: GET /api/models/configs?page=2&page_size=10
        Then: 返回分页响应
        """
        # Given
        mock_service = AsyncMock()
        mock_service.list_model_configs.return_value = PaginatedModelConfigResponse(
            total=25, page=2, page_size=10, items=[]
        )

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.get("/api/models/configs?page=2&page_size=10")

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 25
        assert data["page"] == 2
        assert data["page_size"] == 10

    def test_list_configs_page_size_limit(
        self, test_client: TestClient, mock_session: AsyncMock
    ) -> None:
        """测试 page_size 超过限制.

        Given: page_size > 100
        When: GET /api/models/configs?page_size=200
        Then: 返回 422 错误（FastAPI Query 验证）
        """
        # When
        response = test_client.get("/api/models/configs?page_size=200")

        # Then
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_configs_with_filters(
        self, test_client: TestClient, mock_session: AsyncMock
    ) -> None:
        """测试获取配置列表（带过滤）.

        Given: 提供过滤参数
        When: GET /api/models/configs?active=true&provider=openai
        Then: 返回过滤后的结果
        """
        # Given
        mock_service = AsyncMock()
        mock_service.list_model_configs.return_value = PaginatedModelConfigResponse(
            total=5, page=1, page_size=20, items=[]
        )

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.get("/api/models/configs?active=true&provider=openai")

        # Then
        assert response.status_code == status.HTTP_200_OK
        mock_service.list_model_configs.assert_called_once()

    def test_get_config_success(
        self, test_client: TestClient, mock_session: AsyncMock, sample_config_response: ModelConfigResponse
    ) -> None:
        """测试成功获取单个配置.

        Given: 配置 ID
        When: GET /api/models/configs/1
        Then: 返回配置对象
        """
        # Given
        config_id = 1
        mock_service = AsyncMock()
        mock_service.get_model_config.return_value = sample_config_response

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.get(f"/api/models/configs/{config_id}")

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert "api_key" not in data

    def test_get_config_not_found(self, test_client: TestClient, mock_session: AsyncMock) -> None:
        """测试获取不存在的配置.

        Given: 不存在的配置 ID
        When: GET /api/models/configs/999
        Then: 返回 404 错误
        """
        # Given
        config_id = 999
        mock_service = AsyncMock()
        mock_service.get_model_config.side_effect = ValueError("配置 ID 999 不存在")

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.get(f"/api/models/configs/{config_id}")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_config_success(
        self, test_client: TestClient, mock_session: AsyncMock, sample_config_response: ModelConfigResponse
    ) -> None:
        """测试成功更新配置.

        Given: 配置 ID 和更新数据
        When: PUT /api/models/configs/1
        Then: 返回更新后的配置
        """
        # Given
        config_id = 1
        update_data = {"name": "Updated Name"}

        mock_service = AsyncMock()
        mock_service.update_model_config.return_value = sample_config_response

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.put(f"/api/models/configs/{config_id}", json=update_data)

        # Then
        assert response.status_code == status.HTTP_200_OK

    def test_update_config_conflict(
        self, test_client: TestClient, mock_session: AsyncMock
    ) -> None:
        """测试更新配置时乐观锁冲突.

        Given: 配置已被其他用户修改
        When: PUT /api/models/configs/1
        Then: 返回 409 冲突错误
        """
        # Given
        config_id = 1
        update_data = {"name": "Updated Name"}

        mock_service = AsyncMock()
        mock_service.update_model_config.side_effect = ValueError("配置已被其他用户修改")

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.put(f"/api/models/configs/{config_id}", json=update_data)

        # Then
        assert response.status_code == status.HTTP_409_CONFLICT

    def test_delete_config_success(self, test_client: TestClient, mock_session: AsyncMock) -> None:
        """测试成功删除配置.

        Given: 配置 ID
        When: DELETE /api/models/configs/1
        Then: 返回 204
        """
        # Given
        config_id = 1

        mock_service = AsyncMock()
        mock_service.delete_model_config.return_value = True

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.delete(f"/api/models/configs/{config_id}")

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_config_not_found(self, test_client: TestClient, mock_session: AsyncMock) -> None:
        """测试删除不存在的配置.

        Given: 不存在的配置 ID
        When: DELETE /api/models/configs/999
        Then: 返回 404 错误
        """
        # Given
        config_id = 999

        mock_service = AsyncMock()
        mock_service.delete_model_config.side_effect = ValueError("配置 ID 999 不存在")

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.delete(f"/api/models/configs/{config_id}")

        # Then
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_toggle_config_status_success(
        self, test_client: TestClient, mock_session: AsyncMock, sample_config_response: ModelConfigResponse
    ) -> None:
        """测试成功切换配置状态.

        Given: 配置 ID 和新状态
        When: PATCH /api/models/configs/1/status?is_active=false
        Then: 返回更新后的配置
        """
        # Given
        config_id = 1

        mock_service = AsyncMock()
        mock_service.toggle_config_status.return_value = sample_config_response

        with patch("one_dragon_agent.core.model.router.ModelConfigService", return_value=mock_service):
            # When
            response = test_client.patch(f"/api/models/configs/{config_id}/status?is_active=false")

        # Then
        assert response.status_code == status.HTTP_200_OK

    def test_test_connection_success(self, test_client: TestClient) -> None:
        """测试成功测试连接.

        Given: 有效的 API 配置
        When: POST /api/models/configs/test-connection
        Then: 返回成功响应
        """
        # Given
        request_data = {
            "base_url": "https://api.openai.com",
            "api_key": "sk-test123",
            "model_id": "gpt-3.5-turbo",
        }

        # When
        with patch("one_dragon_agent.core.model.router.ModelConfigService.test_connection") as mock_test:
            from one_dragon_agent.core.model.models import TestConnectionResponse
            mock_test.return_value = TestConnectionResponse(
                success=True,
                message="连接成功",
            )

            response = test_client.post("/api/models/configs/test-connection", json=request_data)

        # Then
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
