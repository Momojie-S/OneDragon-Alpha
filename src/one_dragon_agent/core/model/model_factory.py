# -*- coding: utf-8 -*-
"""模型工厂类，用于根据配置创建模型实例."""

import time
from typing import Any

from one_dragon_agent.core.model.models import ModelConfigInternal
from one_dragon_agent.core.model.qwen.qwen_chat_model import QwenChatModel
from one_dragon_agent.core.system.log import get_logger

logger = get_logger(__name__)


# Token 缓存，避免每次创建模型都刷新
_token_cache: dict[int, dict] = {}
_TOKEN_REFRESH_BUFFER = 5 * 60 * 1000  # 5 分钟缓冲期（毫秒）


class ModelFactory:
    """模型工厂类.

    根据模型配置创建对应的 AgentScope 模型实例。
    支持 OpenAI 和 Qwen 两种提供商。

    对于 Qwen provider，支持从数据库配置读取 OAuth token 并自动刷新。
    """

    @staticmethod
    def create_model(config: ModelConfigInternal, model_id: str):
        """根据配置创建模型实例.

        Args:
            config: 模型配置对象(包含 api_key)
            model_id: 要使用的模型 ID（必须是 config.models 中的一个）

        Returns:
            AgentScope 模型实例（OpenAIChatModel 或 QwenChatModel）

        Raises:
            ValueError: 如果配置无效或模型 ID 不存在

        """
        # 验证模型 ID 是否在配置中
        model_ids = [m.model_id for m in config.models]
        if model_id not in model_ids:
            msg = f"模型 ID '{model_id}' 不在配置 '{config.name}' 的模型列表中: {model_ids}"
            raise ValueError(msg)

        # 根据 provider 创建对应的模型
        if config.provider == "openai":
            return ModelFactory._create_openai_model(config, model_id)
        elif config.provider == "qwen":
            return ModelFactory._create_qwen_model(config, model_id)
        else:
            msg = f"不支持的 provider: {config.provider}"
            raise ValueError(msg)

    @staticmethod
    def _create_openai_model(config: ModelConfigInternal, model_id: str):
        """创建 OpenAI 兼容的模型实例.

        Args:
            config: 模型配置对象
            model_id: 要使用的模型 ID

        Returns:
            OpenAIChatModel 实例

        """
        from agentscope.model import OpenAIChatModel

        logger.info(f"创建 OpenAI 模型: {model_id}, base_url: {config.base_url}")

        return OpenAIChatModel(
            model_name=model_id,
            api_key=config.api_key,
            client_kwargs={"base_url": config.base_url},
        )

    @staticmethod
    def _create_qwen_model(config: ModelConfigInternal, model_id: str):
        """创建 Qwen 模型实例.

        使用数据库配置中的 OAuth token，并在 token 接近过期时自动刷新。

        Args:
            config: 模型配置对象（需包含 OAuth 字段）
            model_id: 要使用的模型 ID

        Returns:
            QwenChatModelWithConfig 实例

        Raises:
            ValueError: 如果配置没有 OAuth token

        """
        logger.info(f"创建 Qwen 模型: {model_id}")

        # 检查配置是否有 OAuth token
        if not hasattr(config, "oauth_access_token") or not config.oauth_access_token:
            msg = (
                f"配置 '{config.name}' 没有有效的 OAuth token，"
                "请先完成 Qwen OAuth 认证"
            )
            raise ValueError(msg)

        # 获取或刷新 token
        token_data = ModelFactory._get_or_refresh_token(config)

        # 创建带配置的 Qwen 模型
        return QwenChatModelWithConfig(
            model_name=model_id,
            access_token=token_data["access_token"],
            config_id=config.id,
        )

    @staticmethod
    def _get_or_refresh_token(config: ModelConfigInternal) -> dict:
        """获取或刷新 OAuth token.

        Args:
            config: 模型配置对象（需包含 OAuth 字段）

        Returns:
            包含 access_token 的字典（明文）

        Raises:
            ValueError: 如果 token 无效或无法刷新

        """
        from one_dragon_agent.core.model.qwen.token_encryption import (
            get_token_encryption,
        )

        config_id = config.id
        now_ms = int(time.time() * 1000)
        encryption = get_token_encryption()

        # 检查缓存
        if config_id in _token_cache:
            cached = _token_cache[config_id]
            expires_at = cached.get("expires_at", 0)
            if expires_at > now_ms + _TOKEN_REFRESH_BUFFER:
                # Token 仍然有效（有 5 分钟缓冲）
                logger.debug(f"使用缓存的 token (配置 {config_id})")
                return cached

        # Token 需要刷新或不在缓存中
        expires_at = getattr(config, "oauth_expires_at", 0)

        if expires_at < now_ms + _TOKEN_REFRESH_BUFFER:
            # Token 接近过期，需要刷新
            logger.info(f"配置 {config_id} 的 token 接近过期，尝试刷新")
            token_data = ModelFactory._refresh_qwen_token(config)
        else:
            # Token 仍然有效，解密后返回
            token_data = {
                "access_token": encryption.decrypt(config.oauth_access_token),
                "refresh_token": encryption.decrypt(config.oauth_refresh_token),
                "expires_at": expires_at,
            }

        # 更新缓存
        _token_cache[config_id] = token_data

        return token_data

    @staticmethod
    def _refresh_qwen_token(config: ModelConfigInternal) -> dict:
        """刷新 Qwen OAuth token.

        Args:
            config: 模型配置对象（需包含 OAuth 字段）

        Returns:
            包含新 token 的字典（明文）

        Raises:
            ValueError: 如果刷新失败

        """
        from one_dragon_agent.core.model.qwen.oauth import (
            QwenOAuthClient,
            QwenRefreshTokenInvalidError,
        )
        from one_dragon_agent.core.model.qwen.token_encryption import (
            get_token_encryption,
        )

        encryption = get_token_encryption()
        refresh_token_encrypted = getattr(config, "oauth_refresh_token", None)
        if not refresh_token_encrypted:
            msg = f"配置 {config.id} 没有 refresh_token，无法刷新"
            raise ValueError(msg)

        # 解密 refresh_token
        try:
            refresh_token = encryption.decrypt(refresh_token_encrypted)
        except Exception as e:
            logger.error(f"解密 refresh_token 失败: {e}")
            msg = f"配置 '{config.name}' 的 OAuth 授权已过期，请重新完成认证流程"
            raise ValueError(msg) from e

        try:
            client = QwenOAuthClient()
            new_token = client.refresh_token(refresh_token)

            # 同步更新数据库
            import asyncio

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop is not None:
                # 在已有事件循环中执行
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        ModelFactory._update_token_in_db(config.id, new_token),
                    )
                    future.result(timeout=30)
            else:
                # 创建新的事件循环
                asyncio.run(ModelFactory._update_token_in_db(config.id, new_token))

            logger.info(f"配置 {config.id} 的 token 刷新成功")

            return {
                "access_token": new_token.access_token,
                "refresh_token": new_token.refresh_token,
                "expires_at": new_token.expires_at,
            }

        except QwenRefreshTokenInvalidError as e:
            logger.error(f"配置 {config.id} 的 refresh_token 无效: {e}")
            msg = (
                f"配置 '{config.name}' 的 OAuth 授权已过期，"
                "请重新完成认证流程"
            )
            raise ValueError(msg) from e
        except Exception as e:
            logger.exception(f"刷新 token 失败: {e}")
            msg = f"刷新 token 失败: {str(e)}"
            raise ValueError(msg) from e

    @staticmethod
    async def _update_token_in_db(config_id: int, token) -> None:
        """更新数据库中的 token.

        Args:
            config_id: 配置 ID
            token: 新的 QwenOAuthToken

        """
        from one_dragon_agent.core.model.repository import ModelConfigRepository
        from one_dragon_alpha.services.mysql import MySQLConnectionService
        import json

        mysql_service = MySQLConnectionService()
        async with await mysql_service.get_session() as session:
            repository = ModelConfigRepository(session)

            token_data = {
                "access_token": token.access_token,
                "token_type": "Bearer",
                "refresh_token": token.refresh_token,
                "expires_at": token.expires_at,
                "scope": "openid profile email model.completion",
                "metadata": None,
            }

            if token.resource_url:
                token_data["metadata"] = json.dumps(
                    {"resource_url": token.resource_url}
                )

            await repository.update_oauth_token(config_id, token_data)

    @staticmethod
    def clear_token_cache(config_id: int | None = None) -> None:
        """清除 token 缓存.

        Args:
            config_id: 配置 ID，如果为 None 则清除所有缓存

        """
        if config_id is None:
            _token_cache.clear()
            logger.info("已清除所有 token 缓存")
        elif config_id in _token_cache:
            del _token_cache[config_id]
            logger.info(f"已清除配置 {config_id} 的 token 缓存")


class QwenChatModelWithConfig:
    """使用配置中的 OAuth token 的 Qwen 模型.

    这个类包装了 OpenAIChatModel，使用从数据库配置获取的 OAuth token。

    Attributes:
        _model_name: 模型名称
        _access_token: OAuth 访问令牌
        _config_id: 配置 ID
        _client: OpenAI 客户端

    """

    def __init__(
        self, model_name: str, access_token: str, config_id: int
    ) -> None:
        """初始化 QwenChatModelWithConfig.

        Args:
            model_name: 模型名称
            access_token: OAuth 访问令牌
            config_id: 配置 ID

        """
        self._model_name = model_name
        self._access_token = access_token
        self._config_id = config_id
        self._client = None
        self._setup_client()

    def _setup_client(self) -> None:
        """设置 OpenAI 客户端."""
        import openai

        self._client = openai.AsyncOpenAI(
            api_key=self._access_token,
            base_url="https://portal.qwen.ai/v1",
        )

    async def _call_api(self, messages: list[dict], **kwargs: Any) -> Any:
        """调用 Qwen API.

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Returns:
            API 响应

        """
        response = await self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            **kwargs,
        )
        return response

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """同步调用接口.

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            模型响应

        """
        import asyncio

        return asyncio.run(self._call_api(*args, **kwargs))
