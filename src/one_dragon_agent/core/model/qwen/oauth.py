# -*- coding: utf-8 -*-
"""Qwen OAuth 2.0 客户端实现.

本模块提供 Qwen portal 认证的 OAuth 2.0 设备码流程，
包括 PKCE 安全增强和 token 刷新功能。
"""

import asyncio
import hashlib
import time
import uuid
from dataclasses import dataclass
from typing import Callable, Literal, Optional

import httpx

# Qwen OAuth constants
QWEN_OAUTH_BASE_URL = "https://chat.qwen.ai"
QWEN_OAUTH_DEVICE_CODE_ENDPOINT = f"{QWEN_OAUTH_BASE_URL}/api/v1/oauth2/device/code"
QWEN_OAUTH_TOKEN_ENDPOINT = f"{QWEN_OAUTH_BASE_URL}/api/v1/oauth2/token"
QWEN_OAUTH_CLIENT_ID = "f0304373b74a44d2b584a3fb70ca9e56"
QWEN_OAUTH_SCOPE = "openid profile email model.completion"
QWEN_OAUTH_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"


# 异常类定义
class QwenError(Exception):
    """Qwen 相关错误的基础异常类."""

    pass


class QwenOAuthError(QwenError):
    """OAuth 认证流程中抛出的异常."""

    pass


class QwenRefreshTokenInvalidError(QwenError):
    """Refresh token 无效或过期时抛出的异常."""

    pass


class QwenTokenExpiredError(QwenError):
    """Access token 过期时抛出的异常."""

    pass


class QwenTokenNotAvailableError(QwenError):
    """Token 不可用时抛出的异常（例如未完成认证）."""

    pass


@dataclass
class QwenDeviceAuthorization:
    """Qwen 设备授权响应.

    Attributes:
        device_code: 用于轮询的设备码。
        user_code: 用户手动输入的用户码。
        verification_uri: 用户授权的验证 URI。
        verification_uri_complete: 包含用户码的完整验证 URI。
        expires_in: 设备码过期前的秒数。
        interval: 轮询间隔（秒）。

    """

    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str | None
    expires_in: int
    interval: int | None


@dataclass
class QwenOAuthToken:
    """Qwen OAuth token 响应.

    Attributes:
        access_token: 用于 API 调用的访问令牌。
        refresh_token: 用于获取新访问令牌的刷新令牌。
        expires_at: 访问令牌过期的绝对时间戳（毫秒）。
        resource_url: Token 响应中的可选资源 URL。

    """

    access_token: str
    refresh_token: str
    expires_at: int
    resource_url: str | None = None


# 设备 token 轮询结果的内部状态类型
@dataclass
class TokenPending:
    """设备码轮询中的等待状态."""

    status: Literal["pending"]
    slow_down: bool = False


@dataclass
class TokenSuccess:
    """成功状态，包含 token."""

    status: Literal["success"]
    token: QwenOAuthToken


@dataclass
class TokenError:
    """设备码轮询中的错误状态."""

    status: Literal["error"]
    message: str


DeviceTokenResult = TokenPending | TokenSuccess | TokenError


def _to_form_url_encoded(data: dict[str, str]) -> str:
    """Convert dictionary to form URL encoded string.

    Args:
        data: Dictionary of key-value pairs.

    Returns:
        Form URL encoded string.

    """
    return "&".join(f"{key}={value}" for key, value in data.items())


def generate_pkce() -> tuple[str, str]:
    """生成 PKCE code verifier 和 challenge.

    使用 RFC 7636 规范的 SHA256 哈希算法.
    使用 base64url 编码以与 TypeScript 实现保持一致.

    Returns:
        包含 (code_verifier, code_challenge) 的元组.

    """
    import base64
    import secrets

    # 生成 32 字节随机数并编码为 base64url（无填充）
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode().rstrip("=")
    # 使用 SHA256 哈希 verifier 并编码为 base64url（无填充）
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )
    return verifier, challenge


class QwenOAuthClient:
    """Qwen OAuth 2.0 设备码流程认证客户端."""

    def __init__(self, client_id: str | None = None) -> None:
        """初始化 Qwen OAuth 客户端.

        Args:
            client_id: OAuth 客户端 ID。若未提供则使用默认的 Qwen 客户端 ID。

        """
        self._client_id = client_id or QWEN_OAUTH_CLIENT_ID

    async def get_device_code(self, code_challenge: str) -> QwenDeviceAuthorization:
        """向 Qwen OAuth 服务器请求设备码.

        Args:
            code_challenge: 从 code_verifier 生成的 PKCE code challenge。

        Returns:
            包含 device_code、user_code 和 verification_uri 的 QwenDeviceAuthorization.

        Raises:
            QwenOAuthError: If the request fails or returns incomplete response.

        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                QWEN_OAUTH_DEVICE_CODE_ENDPOINT,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "x-request-id": str(uuid.uuid4()),
                },
                content=_to_form_url_encoded(
                    {
                        "client_id": self._client_id,
                        "scope": QWEN_OAUTH_SCOPE,
                        "code_challenge": code_challenge,
                        "code_challenge_method": "S256",
                    }
                ),
            )

        if not response.is_success:
            text = response.text
            raise QwenOAuthError(
                f"Qwen device authorization failed ({response.status_code}): {text or response.text}"
            )

        payload = response.json()
        if (
            not payload.get("device_code")
            or not payload.get("user_code")
            or not payload.get("verification_uri")
            or not payload.get("expires_in")
        ):
            error = payload.get("error", "Missing required fields in response")
            raise QwenOAuthError(
                f"Qwen device authorization returned incomplete payload: {error}"
            )

        return QwenDeviceAuthorization(
            device_code=payload["device_code"],
            user_code=payload["user_code"],
            verification_uri=payload["verification_uri"],
            verification_uri_complete=payload.get("verification_uri_complete"),
            expires_in=payload["expires_in"],
            interval=payload.get("interval"),
        )

    async def poll_device_token(
        self,
        device_code: str,
        code_verifier: str,
    ) -> DeviceTokenResult:
        """Poll Qwen OAuth server for token authorization.

        Args:
            device_code: Device code from get_device_code() response.
            code_verifier: PKCE code verifier generated with code_challenge.

        Returns:
            DeviceTokenResult indicating success, pending, or error state.

        """
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                QWEN_OAUTH_TOKEN_ENDPOINT,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                content=_to_form_url_encoded(
                    {
                        "grant_type": QWEN_OAUTH_GRANT_TYPE,
                        "client_id": self._client_id,
                        "device_code": device_code,
                        "code_verifier": code_verifier,
                    }
                ),
            )

        if not response.is_success:
            try:
                payload = response.json()
            except Exception:
                text = response.text
                return TokenError(status="error", message=text or response.text)

            error = payload.get("error")
            if error == "authorization_pending":
                return TokenPending(status="pending", slow_down=False)
            if error == "slow_down":
                return TokenPending(status="pending", slow_down=True)

            return TokenError(
                status="error",
                message=payload.get("error_description") or error or response.text,
            )

        token_payload = response.json()
        if (
            not token_payload.get("access_token")
            or not token_payload.get("refresh_token")
            or not token_payload.get("expires_in")
        ):
            return TokenError(status="error", message="Incomplete token payload")

        return TokenSuccess(
            status="success",
            token=QwenOAuthToken(
                access_token=token_payload["access_token"],
                refresh_token=token_payload["refresh_token"],
                expires_at=int(time.time() * 1000) + token_payload["expires_in"] * 1000,
                resource_url=token_payload.get("resource_url"),
            ),
        )

    async def refresh_token(self, refresh_token: str) -> QwenOAuthToken:
        """Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token from previous authentication.

        Returns:
            QwenOAuthToken with new access_token and expires_at.

        Raises:
            QwenRefreshTokenInvalidError: If refresh_token is invalid or expired.
            QwenOAuthError: If the refresh request fails.

        """
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            response = await client.post(
                QWEN_OAUTH_TOKEN_ENDPOINT,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                content=_to_form_url_encoded(
                    {
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self._client_id,
                    }
                ),
            )

        if response.status_code == 400:
            raise QwenRefreshTokenInvalidError(
                "Qwen OAuth refresh token expired or invalid. Please re-authenticate."
            )

        if not response.is_success:
            text = response.text
            raise QwenOAuthError(f"Qwen OAuth refresh failed: {text or response.text}")

        payload = response.json()
        if not payload.get("access_token") or not payload.get("expires_in"):
            raise QwenOAuthError("Qwen OAuth refresh response missing access token")

        return QwenOAuthToken(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token") or refresh_token,
            expires_at=int(time.time() * 1000) + payload["expires_in"] * 1000,
        )


async def login_qwen_oauth(
    client: Optional[QwenOAuthClient] = None,
    open_url: Optional[Callable] = None,
    note: Optional[Callable] = None,
    progress: Optional[object] = None,
) -> QwenOAuthToken:
    """Execute complete Qwen OAuth device code flow.

    Args:
        client: QwenOAuthClient instance. If None, creates default instance.
        open_url: Async callable to open verification URL in browser.
            If None, prints URL to console.
        note: Async callable to display notes to user.
            If None, uses print statement.
        progress: Progress object with update() and stop() methods.
            If None, no progress tracking.

    Returns:
        QwenOAuthToken upon successful authentication.

    Raises:
        QwenOAuthError: If OAuth flow fails or times out.

    """
    # Set up defaults if not provided
    if client is None:
        client = QwenOAuthClient()

    if open_url is None:
        async def _default_open_url(url: str) -> None:
            print(f"\n请打开以下链接进行认证:\n{url}\n")

        open_url = _default_open_url

    if note is None:
        async def _default_note(message: str, title: str) -> None:
            print(f"\n{title}\n{'=' * len(title)}\n{message}\n")

        note = _default_note

    if progress is None:
        class _DefaultProgress:
            """默认进度跟踪器."""

            def update(self, message: str) -> None:
                """更新进度消息."""
                print(f"  {message}")

            def stop(self, message: str) -> None:
                """停止进度跟踪."""
                print(f"  {message}")

        progress = _DefaultProgress()

    verifier, challenge = generate_pkce()
    device = await client.get_device_code(challenge)
    verification_url = device.verification_uri_complete or device.verification_uri

    await note(
        f"Open {verification_url} to approve access.\n"
        f"If prompted, enter the code {device.user_code}.",
        "Qwen OAuth",
    )

    try:
        await open_url(verification_url)
    except Exception:
        # Fall back to manual copy/paste if browser open fails
        pass

    start_time = time.time()
    poll_interval_ms = device.interval * 1000 if device.interval else 2000
    timeout_sec = device.expires_in

    while time.time() - start_time < timeout_sec:
        progress.update("Waiting for Qwen OAuth approval…")
        result = await client.poll_device_token(device.device_code, verifier)

        if result.status == "success":
            progress.stop("Qwen OAuth complete")
            return result.token

        if result.status == "error":
            progress.stop("Qwen OAuth failed")
            raise QwenOAuthError(f"Qwen OAuth failed: {result.message}")

        if result.status == "pending" and result.slow_down:
            poll_interval_ms = min(int(poll_interval_ms * 1.5), 10000)

        # Wait for poll_interval_ms before next poll
        await asyncio.sleep(poll_interval_ms / 1000)

    progress.stop("Qwen OAuth timed out")
    raise QwenOAuthError("Qwen OAuth timed out waiting for authorization.")
