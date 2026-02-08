# -*- coding: utf-8 -*-
"""通用模型配置服务层."""

import asyncio
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from one_dragon_agent.core.model.models import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
    TestConnectionRequest,
    TestConnectionResponse,
    PaginatedModelConfigResponse,
)
from one_dragon_agent.core.model.repository import ModelConfigRepository
from one_dragon_agent.core.system.log import get_logger

logger = get_logger(__name__)


class ModelConfigService:
    """模型配置服务类.

    负责处理模型配置的业务逻辑。

    Attributes:
        session: SQLAlchemy 异步会话
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化服务.

        Args:
            session: SQLAlchemy 异步会话
        """
        self._session = session
        self._repository = ModelConfigRepository(session)

    async def validate_config_unique(self, name: str, exclude_id: int | None = None) -> bool:
        """验证配置名称唯一性.

        Args:
            name: 配置名称
            exclude_id: 排除的配置 ID（用于更新时）

        Returns:
            是否唯一

        Raises:
            ValueError: 如果配置名称已存在
        """
        # 这里通过尝试创建/更新来让数据库层验证唯一性
        # 业务层只做额外的验证逻辑
        return True

    async def validate_base_url(self, base_url: str) -> bool:
        """验证 baseUrl 格式.

        Args:
            base_url: baseUrl

        Returns:
            是否有效
        """
        base_url = base_url.strip()
        return base_url.startswith(("http://", "https://"))

    async def create_model_config(self, config: ModelConfigCreate) -> ModelConfigResponse:
        """创建模型配置.

        Args:
            config: 创建请求模型

        Returns:
            创建的配置

        Raises:
            ValueError: 如果验证失败
        """
        # 验证 provider 字段
        if config.provider != "openai":
            msg = f"当前仅支持 provider='openai'，收到: {config.provider}"
            raise ValueError(msg)

        # 验证配置名称唯一性
        await self.validate_config_unique(config.name)

        return await self._repository.create_config(config)

    async def get_model_config(self, config_id: int) -> ModelConfigResponse:
        """获取单个配置.

        Args:
            config_id: 配置 ID

        Returns:
            配置对象

        Raises:
            ValueError: 如果配置不存在
        """
        config = await self._repository.get_config_by_id(config_id)
        if not config:
            msg = f"配置 ID {config_id} 不存在"
            raise ValueError(msg)
        return config

    async def list_model_configs(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        provider: str | None = None,
    ) -> PaginatedModelConfigResponse:
        """获取配置列表.

        Args:
            page: 页码（从 1 开始）
            page_size: 每页记录数（最大 100）
            is_active: 是否启用（可选过滤条件）
            provider: 提供商（可选过滤条件）

        Returns:
            分页响应
        """
        # 验证 provider 字段
        if provider is not None and provider != "openai":
            msg = f"当前仅支持 provider='openai'，收到: {provider}"
            raise ValueError(msg)

        # 限制 page_size 最大值
        page_size = min(page_size, 100)

        configs, total = await self._repository.get_configs(
            page=page,
            page_size=page_size,
            is_active=is_active,
            provider=provider,
        )

        return PaginatedModelConfigResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=configs,
        )

    async def update_model_config(
        self, config_id: int, config_update: ModelConfigUpdate
    ) -> ModelConfigResponse:
        """更新模型配置.

        Args:
            config_id: 配置 ID
            config_update: 更新请求模型

        Returns:
            更新后的配置

        Raises:
            ValueError: 如果验证失败或配置不存在
        """
        # 验证 provider 字段
        if config_update.provider is not None and config_update.provider != "openai":
            msg = f"当前仅支持 provider='openai'，收到: {config_update.provider}"
            raise ValueError(msg)

        return await self._repository.update_config(config_id, config_update)

    async def delete_model_config(self, config_id: int) -> bool:
        """删除模型配置.

        Args:
            config_id: 配置 ID

        Returns:
            是否删除成功

        Raises:
            ValueError: 如果配置不存在
        """
        return await self._repository.delete_config(config_id)

    async def toggle_config_status(self, config_id: int, is_active: bool) -> ModelConfigResponse:
        """切换配置启用状态.

        Args:
            config_id: 配置 ID
            is_active: 是否启用

        Returns:
            更新后的配置

        Raises:
            ValueError: 如果配置不存在
        """
        return await self._repository.toggle_config_status(config_id, is_active)

    @staticmethod
    async def test_connection(request: TestConnectionRequest) -> TestConnectionResponse:
        """测试 API 连接.

        通过发送一个简单的聊天请求来验证连接（会消耗少量 token）。

        Args:
            request: 测试连接请求

        Returns:
            测试连接响应
        """
        base_url = request.base_url.rstrip("/")
        api_key = request.api_key
        model_id = request.model_id

        # 使用 chat completions 端点测试连接
        url = f"{base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # 发送一个简单的测试消息
        payload = {
            "model": model_id,  # 使用用户配置的模型
            "messages": [
                {"role": "user", "content": "hi"}
            ],
            "max_tokens": 5,  # 限制返回 token 数量
            "temperature": 0,
        }

        try:
            # 设置 15 秒超时
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 200:
                    # 解析响应
                    try:
                        data = response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return TestConnectionResponse(
                            success=True,
                            message=f"连接成功！模型回复: {content[:50]}",
                        )
                    except Exception:
                        return TestConnectionResponse(
                            success=True,
                            message="连接成功！",
                        )

                elif response.status_code == 401:
                    return TestConnectionResponse(
                        success=False,
                        message="API Key 无效或已过期",
                        raw_error={"status_code": 401},
                    )
                elif response.status_code == 404:
                    return TestConnectionResponse(
                        success=False,
                        message="API 端点不存在，请检查 Base URL 是否正确",
                        raw_error={"status_code": 404},
                    )
                else:
                    # 尝试解析错误信息
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", response.text)
                    except Exception:
                        error_msg = response.text or f"HTTP {response.status_code}"

                    return TestConnectionResponse(
                        success=False,
                        message=error_msg,
                        raw_error={"status_code": response.status_code, "body": response.text},
                    )

        except asyncio.TimeoutError:
            logger.error(f"测试连接超时: {base_url}")
            return TestConnectionResponse(
                success=False,
                message="连接超时，请检查 baseUrl 是否正确",
                raw_error={"error": "timeout"},
            )
        except httpx.ConnectError as e:
            logger.error(f"测试连接失败: {e}")
            return TestConnectionResponse(
                success=False,
                message=f"无法连接到服务器: {str(e)}",
                raw_error={"error": str(e)},
            )
        except Exception as e:
            logger.exception(f"测试连接异常: {e}")
            return TestConnectionResponse(
                success=False,
                message=f"连接失败: {str(e)}",
                raw_error={"error": str(e)},
            )
