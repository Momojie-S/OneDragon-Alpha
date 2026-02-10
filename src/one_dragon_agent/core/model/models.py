# -*- coding: utf-8 -*-
"""通用模型配置数据模型."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ModelInfo(BaseModel):
    """模型信息.

    Attributes:
        model_id: 模型 ID
        support_vision: 是否支持视觉能力
        support_thinking: 是否支持思考能力
    """

    model_id: str = Field(..., description="模型 ID")
    support_vision: bool = Field(default=False, description="是否支持视觉能力")
    support_thinking: bool = Field(default=False, description="是否支持思考能力")


class ModelConfigBase(BaseModel):
    """模型配置基础模型.

    Attributes:
        name: 配置名称
        provider: 模型提供商（支持 openai 和 qwen）
        base_url: API baseUrl（qwen 不需要）
        models: 模型列表
        is_active: 是否启用
    """

    name: str = Field(..., min_length=1, max_length=255, description="配置名称")
    provider: Literal["openai", "qwen"] = Field(
        ..., description="模型提供商（支持 openai 和 qwen）"
    )
    base_url: str = Field(default="", description="API baseUrl（qwen 不需要）")
    models: list[ModelInfo] = Field(..., min_length=1, description="模型列表")
    is_active: bool = Field(default=True, description="是否启用")

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        """验证配置名称不为空.

        Args:
            v: 配置名称

        Returns:
            验证后的配置名称

        Raises:
            ValueError: 如果配置名称为空
        """
        if not v or not v.strip():
            raise ValueError("配置名称不能为空")
        return v.strip()

    @field_validator("base_url")
    @classmethod
    def base_url_must_be_valid(cls, v: str) -> str:
        """验证 baseUrl 格式.

        Args:
            v: baseUrl

        Returns:
            验证后的 baseUrl

        Raises:
            ValueError: 如果 baseUrl 格式无效
        """
        v = v.strip()
        # 允许空字符串（用于 qwen provider）
        if not v:
            return v
        if not v.startswith(("http://", "https://")):
            raise ValueError("baseUrl 必须以 http:// 或 https:// 开头")
        return v

    @field_validator("models")
    @classmethod
    def models_must_not_be_empty(cls, v: list[ModelInfo]) -> list[ModelInfo]:
        """验证模型列表不为空.

        Args:
            v: 模型列表

        Returns:
            验证后的模型列表

        Raises:
            ValueError: 如果模型列表为空
        """
        if not v:
            raise ValueError("至少需要添加一个模型")
        return v


class ModelConfigCreate(ModelConfigBase):
    """创建模型配置请求模型.

    Attributes:
        api_key: API 密钥
    """

    api_key: str = Field(..., min_length=1, description="API 密钥")

    @field_validator("api_key")
    @classmethod
    def api_key_must_not_be_empty(cls, v: str) -> str:
        """验证 API key 不为空.

        Args:
            v: API key

        Returns:
            验证后的 API key

        Raises:
            ValueError: 如果 API key 为空
        """
        if not v or not v.strip():
            raise ValueError("API key 不能为空")
        return v.strip()


class ModelConfigUpdate(BaseModel):
    """更新模型配置请求模型.

    Attributes:
        name: 配置名称（可选）
        provider: 模型提供商（可选）
        base_url: API baseUrl（可选）
        api_key: API 密钥（可选，为空则不修改）
        models: 模型列表（可选）
        is_active: 是否启用（可选）
    """

    name: str | None = Field(None, min_length=1, max_length=255, description="配置名称")
    provider: Literal["openai", "qwen"] | None = Field(None, description="模型提供商")
    base_url: str | None = Field(None, description="API baseUrl")
    api_key: str | None = Field(None, description="API 密钥（为空则不修改）")
    models: list[ModelInfo] | None = Field(None, min_length=1, description="模型列表")
    is_active: bool | None = Field(None, description="是否启用")
    updated_at: datetime | None = Field(None, description="更新时间（用于乐观锁）")

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str | None) -> str | None:
        """验证配置名称不为空.

        Args:
            v: 配置名称

        Returns:
            验证后的配置名称

        Raises:
            ValueError: 如果配置名称为空
        """
        if v is not None:
            if not v.strip():
                raise ValueError("配置名称不能为空")
            return v.strip()
        return v

    @field_validator("base_url")
    @classmethod
    def base_url_must_be_valid(cls, v: str | None) -> str | None:
        """验证 baseUrl 格式.

        Args:
            v: baseUrl

        Returns:
            验证后的 baseUrl

        Raises:
            ValueError: 如果 baseUrl 格式无效
        """
        if v is not None:
            v = v.strip()
            if not v.startswith(("http://", "https://")):
                raise ValueError("baseUrl 必须以 http:// 或 https:// 开头")
            return v
        return v

    @field_validator("api_key")
    @classmethod
    def api_key_empty_to_none(cls, v: str | None) -> str | None:
        """将空字符串转换为 None.

        Args:
            v: API 密钥

        Returns:
            验证后的 API 密钥
        """
        if v is not None:
            v = v.strip()
            return v or None
        return v


class ModelConfigResponse(ModelConfigBase):
    """模型配置响应模型（不包含 api_key）.

    Attributes:
        id: 配置 ID
        created_at: 创建时间
        updated_at: 更新时间
    """

    id: int = Field(..., description="配置 ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class ModelConfigInternal(ModelConfigBase):
    """模型配置内部响应模型（包含 api_key）.

    此模型仅用于内部服务间调用，不应直接返回给前端。

    Attributes:
        id: 配置 ID
        api_key: API 密钥
        created_at: 创建时间
        updated_at: 更新时间
    """

    id: int = Field(..., description="配置 ID")
    api_key: str = Field(..., description="API 密钥")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class PaginatedModelConfigResponse(BaseModel):
    """分页模型配置响应模型.

    Attributes:
        total: 总记录数
        page: 当前页码
        page_size: 每页记录数
        items: 模型配置列表
    """

    total: int = Field(..., ge=0, description="总记录数")
    page: int = Field(..., ge=1, description="当前页码")
    page_size: int = Field(..., ge=1, le=100, description="每页记录数")
    items: list[ModelConfigResponse] = Field(
        default_factory=list, description="模型配置列表"
    )


class TestConnectionRequest(BaseModel):
    """测试连接请求模型.

    Attributes:
        base_url: API baseUrl
        api_key: API 密钥
        model_id: 模型 ID（可选，如果不提供则使用默认值）
    """

    base_url: str = Field(..., min_length=1, description="API baseUrl")
    api_key: str = Field(..., min_length=1, description="API 密钥")
    model_id: str = Field(default="gpt-3.5-turbo", description="模型 ID")

    @field_validator("base_url")
    @classmethod
    def base_url_must_be_valid(cls, v: str) -> str:
        """验证 baseUrl 格式.

        Args:
            v: baseUrl

        Returns:
            验证后的 baseUrl

        Raises:
            ValueError: 如果 baseUrl 格式无效
        """
        v = v.strip()
        # 允许空字符串（用于 qwen provider）
        if not v:
            return v
        if not v.startswith(("http://", "https://")):
            raise ValueError("baseUrl 必须以 http:// 或 https:// 开头")
        return v


class TestConnectionResponse(BaseModel):
    """测试连接响应模型.

    Attributes:
        success: 是否成功
        message: 响应消息
        raw_error: 原始错误信息（失败时）
    """

    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    raw_error: dict | None = Field(None, description="原始错误信息（失败时）")
