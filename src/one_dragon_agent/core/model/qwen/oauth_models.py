# -*- coding: utf-8 -*-
"""OAuth API 数据模型."""

from typing import Literal

from pydantic import BaseModel, Field


# ========== Request Models ==========


class DeviceCodeRequest(BaseModel):
    """获取设备码请求模型.

    空请求体，不需要额外参数。
    """

    pass


# ========== Response Models ==========


class DeviceCodeResponse(BaseModel):
    """设备码响应模型.

    Attributes:
        session_id: 会话 ID，用于后续状态轮询
        device_code: 设备码（用于服务端轮询）
        user_code: 用户码（8位用户码，格式如 "ABCD-1234"）
        verification_uri: 验证链接
        verification_uri_complete: 包含用户码的完整验证链接
        expires_in: 过期时间（秒）
        interval: 轮询间隔（秒）
    """

    session_id: str = Field(..., description="会话 ID")
    device_code: str = Field(..., description="设备码")
    user_code: str = Field(..., description="用户码")
    verification_uri: str = Field(..., description="验证链接")
    verification_uri_complete: str | None = Field(
        None, description="完整验证链接（包含用户码）"
    )
    expires_in: int = Field(..., description="过期时间（秒）")
    interval: int | None = Field(None, description="轮询间隔（秒）")


class OAuthTokenInfo(BaseModel):
    """OAuth Token 信息模型.

    Attributes:
        access_token: 访问令牌
        refresh_token: 刷新令牌
        expires_at: 过期时间戳（毫秒）
        resource_url: 资源 URL（可选）
    """

    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    expires_at: int = Field(..., description="过期时间戳（毫秒）")
    resource_url: str | None = Field(None, description="资源 URL")


class OAuthStatusResponse(BaseModel):
    """OAuth 状态响应模型.

    Attributes:
        status: 状态（pending/success/error）
        token: token 信息（仅 status=success 时）
        error: 错误信息（仅 status=error 时）
        retry_after: 建议重试间隔（毫秒）
    """

    status: Literal["pending", "success", "error"] = Field(
        ..., description="认证状态"
    )
    token: OAuthTokenInfo | None = Field(None, description="Token 信息")
    error: str | None = Field(None, description="错误信息")
    retry_after: int | None = Field(None, description="建议重试间隔（毫秒）")
