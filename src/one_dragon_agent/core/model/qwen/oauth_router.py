# -*- coding: utf-8 -*-
"""Qwen OAuth API 路由."""

import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from one_dragon_agent.core.model.qwen.oauth_models import (
    DeviceCodeResponse,
    OAuthStatusResponse,
    OAuthTokenInfo,
)
from one_dragon_agent.core.model.qwen.oauth_session import (
    OAuthSession,
    get_oauth_session_manager,
    reset_oauth_session_manager,
)
from one_dragon_agent.core.model.qwen.oauth import QwenOAuthClient
from one_dragon_agent.core.system.log import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/qwen/oauth", tags=["Qwen OAuth"])


# 设备码请求频率限制（简单的内存计数）
_rate_limit_store: dict[str, list[int]] = {}
_RATE_LIMIT_WINDOW = 60  # 秒
_RATE_LIMIT_MAX_REQUESTS = 10  # 每分钟最大请求数


def _check_rate_limit(client_identifier: str) -> bool:
    """检查请求频率限制.

    Args:
        client_identifier: 客户端标识（IP 地址）

    Returns:
        是否允许请求

    """
    now = int(time.time())

    if client_identifier not in _rate_limit_store:
        _rate_limit_store[client_identifier] = []

    # 清理过期的请求记录
    _rate_limit_store[client_identifier] = [
        ts
        for ts in _rate_limit_store[client_identifier]
        if ts > now - _RATE_LIMIT_WINDOW
    ]

    # 检查是否超过限制
    if len(_rate_limit_store[client_identifier]) >= _RATE_LIMIT_MAX_REQUESTS:
        return False

    # 记录本次请求
    _rate_limit_store[client_identifier].append(now)
    return True


@router.post(
    "/device-code",
    response_model=DeviceCodeResponse,
    status_code=status.HTTP_200_OK,
    summary="获取 Qwen OAuth 设备码",
)
async def get_device_code(
    request_client_ip: Annotated[str, Query(include_in_schema=False)] = "unknown",
) -> DeviceCodeResponse:
    """获取 Qwen OAuth 设备码.

    启动 OAuth 2.0 设备码流程，返回设备码和用户授权信息。

    Returns:
        设备码响应，包含会话 ID、设备码、用户码等信息

    Raises:
        HTTPException: 429 如果请求频率过高
        HTTPException: 500 如果获取设备码失败

    """
    # 频率限制检查
    if not _check_rate_limit(request_client_ip):
        logger.warning(f"客户端 {request_client_ip} 请求频率过高")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求频率过高，请稍后再试",
            headers={"Retry-After": str(_RATE_LIMIT_WINDOW)},
        )

    try:
        # 获取会话管理器
        session_manager = get_oauth_session_manager()

        # 创建 OAuth 客户端
        client = QwenOAuthClient()

        # 创建会话并获取设备码
        session = await session_manager.create_session(client)

        return DeviceCodeResponse(
            session_id=session.session_id,
            device_code=session.device_code,
            user_code=session.user_code,
            verification_uri=session.verification_uri,
            verification_uri_complete=session.verification_uri_complete,
            expires_in=int((session.expires_at - time.time() * 1000) / 1000),
            interval=session.interval,
        )

    except Exception as e:
        logger.exception(f"获取设备码失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取设备码失败: {str(e)}",
        ) from e


@router.get(
    "/status",
    response_model=OAuthStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="轮询 Qwen OAuth 认证状态",
)
async def get_oauth_status(
    device_code: Annotated[str, Query(..., description="设备码")],
) -> OAuthStatusResponse:
    """轮询 Qwen OAuth 认证状态.

    通过设备码查询 OAuth 认证的当前状态。

    Args:
        device_code: 设备码

    Returns:
        OAuth 状态响应

    Raises:
        HTTPException: 408 如果认证超时
        HTTPException: 404 如果设备码无效
        HTTPException: 425 如果轮询频率过高（需要降低频率）

    """
    try:
        session_manager = get_oauth_session_manager()

        # 获取会话
        session = await session_manager.get_session_by_device_code(device_code)

        if not session:
            logger.warning(f"无效的设备码: {device_code[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="设备码无效",
            )

        # 检查会话是否过期
        if session.is_expired():
            await session_manager.mark_session_error(session.session_id, "认证超时")
            raise HTTPException(
                status_code=status.HTTP_408_REQUEST_TIMEOUT,
                detail="认证超时",
            )

        # 检查是否可以轮询（最小间隔 1 秒）
        if not session.can_poll(min_interval_ms=1000):
            # 返回 pending 但建议降低频率
            return OAuthStatusResponse(
                status="pending",
                retry_after=2000,
            )

        # 更新轮询信息
        await session_manager.update_session_poll(session.session_id)

        # 检查状态
        if session.status == "success":
            # 认证成功
            token_info = OAuthTokenInfo(
                access_token=session.token.access_token,
                refresh_token=session.token.refresh_token,
                expires_at=session.token.expires_at,
                resource_url=session.token.resource_url,
            )
            return OAuthStatusResponse(status="success", token=token_info)

        if session.status == "error":
            # 认证失败
            return OAuthStatusResponse(
                status="error",
                error=session.error or "认证失败",
            )

        # 仍然在等待认证，轮询 Qwen 服务器
        client = QwenOAuthClient()
        result = await client.poll_device_token(
            device_code, session.code_verifier
        )

        if result.status == "success":
            # 认证成功，保存 token
            await session_manager.mark_session_success(
                session.session_id, result.token
            )
            token_info = OAuthTokenInfo(
                access_token=result.token.access_token,
                refresh_token=result.token.refresh_token,
                expires_at=result.token.expires_at,
                resource_url=result.token.resource_url,
            )
            return OAuthStatusResponse(status="success", token=token_info)

        if result.status == "error":
            # 认证失败
            await session_manager.mark_session_error(
                session.session_id, result.message
            )
            return OAuthStatusResponse(
                status="error",
                error=result.message,
            )

        # pending 状态
        retry_after = None
        if result.slow_down:
            await session_manager.mark_session_slow_down(session.session_id)
            retry_after = (session.interval or 5) * 1000

        return OAuthStatusResponse(
            status="pending",
            retry_after=retry_after,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取 OAuth 状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取认证状态失败: {str(e)}",
        ) from e


@router.post(
    "/shutdown",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="关闭 OAuth 会话管理器（仅用于服务关闭）",
    include_in_schema=False,
)
async def shutdown_oauth_manager() -> None:
    """关闭 OAuth 会话管理器.

    仅用于服务关闭时清理资源。
    """
    session_manager = get_oauth_session_manager()
    await session_manager.shutdown()
    reset_oauth_session_manager()
