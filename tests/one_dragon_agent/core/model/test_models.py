# -*- coding: utf-8 -*-
"""通用模型配置数据模型单元测试."""

import pytest

from one_dragon_agent.core.model.models import (
    ModelInfo,
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
    TestConnectionRequest,
)


class TestModelInfo:
    """ModelInfo 模型测试类."""

    def test_create_model_info_success(self) -> None:
        """测试成功创建模型信息.

        Given: 有效的模型信息数据
        When: 创建 ModelInfo 对象
        Then: 对象创建成功，字段值正确
        """
        # Given
        model_data = {
            "model_id": "deepseek-chat",
            "support_vision": True,
            "support_thinking": False,
        }

        # When
        model = ModelInfo(**model_data)

        # Then
        assert model.model_id == "deepseek-chat"
        assert model.support_vision is True
        assert model.support_thinking is False

    def test_create_model_info_default_values(self) -> None:
        """测试创建模型信息时使用默认值.

        Given: 仅提供 model_id
        When: 创建 ModelInfo 对象
        Then: support_vision 和 support_thinking 默认为 False
        """
        # Given & When
        model = ModelInfo(model_id="gpt-4")

        # Then
        assert model.model_id == "gpt-4"
        assert model.support_vision is False
        assert model.support_thinking is False


class TestModelConfigCreate:
    """ModelConfigCreate 模型测试类."""

    def test_create_openai_config_success(self) -> None:
        """测试成功创建 OpenAI 配置.

        Given: 有效的 OpenAI 配置数据
        When: 创建 ModelConfigCreate 对象
        Then: 对象创建成功
        """
        # Given
        config_data = {
            "name": "DeepSeek 官方",
            "provider": "openai",
            "base_url": "https://api.deepseek.com",
            "api_key": "sk-test123",
            "models": [
                {
                    "model_id": "deepseek-chat",
                    "support_vision": True,
                    "support_thinking": False,
                }
            ],
            "is_active": True,
        }

        # When
        config = ModelConfigCreate(**config_data)

        # Then
        assert config.name == "DeepSeek 官方"
        assert config.provider == "openai"
        assert config.base_url == "https://api.deepseek.com"
        assert len(config.models) == 1

    def test_create_qwen_config_with_empty_base_url_success(self) -> None:
        """测试创建 Qwen 配置时 base_url 为空字符串.

        Given: Qwen provider 且 base_url 为空
        When: 创建 ModelConfigCreate 对象
        Then: 对象创建成功
        """
        # Given
        config_data = {
            "name": "Qwen 测试配置",
            "provider": "qwen",
            "base_url": "",  # Qwen 不需要 base_url
            "api_key": "",  # Qwen 不需要 api_key
            "models": [{"model_id": "qwen-max"}],
        }

        # When
        config = ModelConfigCreate(**config_data)

        # Then
        assert config.provider == "qwen"
        assert config.base_url == ""

    def test_create_qwen_config_with_base_url_fails(self) -> None:
        """测试创建 Qwen 配置时设置了 base_url 验证失败.

        Given: Qwen provider 但 base_url 非空
        When: 创建 ModelConfigCreate 对象
        Then: 抛出 ValueError 异常
        """
        # Given
        config_data = {
            "name": "Qwen 测试配置",
            "provider": "qwen",
            "base_url": "https://api.example.com",  # Qwen 不应该设置 base_url
            "api_key": "",
            "models": [{"model_id": "qwen-max"}],
        }

        # When & Then
        with pytest.raises(ValueError, match="Qwen provider 不需要设置 baseUrl"):
            ModelConfigCreate(**config_data)

    def test_create_openai_config_with_empty_base_url_success(self) -> None:
        """测试创建 OpenAI 配置时 base_url 为空字符串.

        Given: OpenAI provider 且 base_url 为空字符串（允许）
        When: 创建 ModelConfigCreate 对象
        Then: 对象创建成功
        """
        # Given
        config_data = {
            "name": "OpenAI 测试配置",
            "provider": "openai",
            "base_url": "",  # 允许空字符串
            "api_key": "sk-test",
            "models": [{"model_id": "gpt-4"}],
        }

        # When
        config = ModelConfigCreate(**config_data)

        # Then
        assert config.provider == "openai"
        assert config.base_url == ""

    def test_create_config_name_empty_fails(self) -> None:
        """测试配置名称为空时验证失败.

        Given: 配置名称为空字符串
        When: 创建 ModelConfigCreate 对象
        Then: 抛出 ValueError 异常
        """
        # Given
        config_data = {
            "name": "  ",
            "provider": "openai",
            "base_url": "https://api.deepseek.com",
            "api_key": "sk-test123",
            "models": [{"model_id": "deepseek-chat"}],
        }

        # When & Then
        with pytest.raises(ValueError, match="配置名称不能为空"):
            ModelConfigCreate(**config_data)

    def test_create_config_base_url_invalid_fails(self) -> None:
        """测试 baseUrl 格式无效时验证失败.

        Given: baseUrl 不以 http:// 或 https:// 开头
        When: 创建 ModelConfigCreate 对象
        Then: 抛出 ValueError 异常
        """
        # Given
        config_data = {
            "name": "Test Config",
            "provider": "openai",
            "base_url": "invalid-url",
            "api_key": "sk-test123",
            "models": [{"model_id": "deepseek-chat"}],
        }

        # When & Then
        with pytest.raises(ValueError, match="baseUrl 必须以 http:// 或 https:// 开头"):
            ModelConfigCreate(**config_data)

    def test_create_config_models_empty_fails(self) -> None:
        """测试模型列表为空时验证失败.

        Given: models 为空数组
        When: 创建 ModelConfigCreate 对象
        Then: 抛出 ValueError 异常
        """
        # Given
        config_data = {
            "name": "Test Config",
            "provider": "openai",
            "base_url": "https://api.deepseek.com",
            "api_key": "sk-test123",
            "models": [],
        }

        # When & Then
        with pytest.raises(ValueError):  # Pydantic 会先于自定义验证器触发
            ModelConfigCreate(**config_data)


class TestModelConfigUpdate:
    """ModelConfigUpdate 模型测试类."""

    def test_update_config_partial_fields(self) -> None:
        """测试仅更新部分字段.

        Given: 仅提供部分字段
        When: 创建 ModelConfigUpdate 对象
        Then: 仅提供的字段有值，其他字段为 None
        """
        # Given
        update_data = {
            "name": "Updated Name",
            "is_active": False,
        }

        # When
        update = ModelConfigUpdate(**update_data)

        # Then
        assert update.name == "Updated Name"
        assert update.is_active is False
        assert update.provider is None
        assert update.base_url is None

    def test_update_qwen_provider_with_base_url_fails(self) -> None:
        """测试更新 Qwen 配置时设置了 base_url 验证失败.

        Given: provider 为 qwen 且 base_url 非空
        When: 创建 ModelConfigUpdate 对象
        Then: 抛出 ValueError 异常
        """
        # Given
        update_data = {
            "provider": "qwen",
            "base_url": "https://api.example.com",
        }

        # When & Then
        with pytest.raises(ValueError, match="Qwen provider 不需要设置 baseUrl"):
            ModelConfigUpdate(**update_data)

    def test_update_openai_provider_with_invalid_base_url_fails(self) -> None:
        """测试更新 OpenAI 配置时 base_url 格式无效验证失败.

        Given: provider 为 openai 且 base_url 格式无效
        When: 创建 ModelConfigUpdate 对象
        Then: 抛出 ValueError 异常
        """
        # Given
        update_data = {
            "provider": "openai",
            "base_url": "invalid-url",
        }

        # When & Then
        with pytest.raises(ValueError, match="baseUrl 必须以 http:// 或 https:// 开头"):
            ModelConfigUpdate(**update_data)

    def test_update_config_allows_empty_api_key(self) -> None:
        """测试允许 api_key 为空（表示不修改）.

        Given: api_key 显式设置为 None
        When: 创建 ModelConfigUpdate 对象
        Then: api_key 字段为 None
        """
        # Given
        update_data = {"name": "Updated Name", "api_key": None}

        # When
        update = ModelConfigUpdate(**update_data)

        # Then
        assert update.api_key is None


class TestConnectionRequestModel:
    """TestConnectionRequest 模型测试类."""

    def test_connection_request_success(self) -> None:
        """测试成功创建测试连接请求.

        Given: 有效的测试连接数据
        When: 创建 TestConnectionRequest 对象
        Then: 对象创建成功
        """
        # Given
        request_data = {
            "base_url": "https://api.openai.com",
            "api_key": "sk-test123",
        }

        # When
        request = TestConnectionRequest(**request_data)

        # Then
        assert request.base_url == "https://api.openai.com"
        assert request.api_key == "sk-test123"

    def test_connection_request_invalid_url_fails(self) -> None:
        """测试 baseUrl 格式无效时验证失败.

        Given: baseUrl 格式无效
        When: 创建 TestConnectionRequest 对象
        Then: 抛出 ValueError 异常
        """
        # Given
        request_data = {
            "base_url": "not-a-url",
            "api_key": "sk-test123",
        }

        # When & Then
        with pytest.raises(ValueError, match="baseUrl 必须以 http:// 或 https:// 开头"):
            TestConnectionRequest(**request_data)
