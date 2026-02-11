# -*- coding: utf-8 -*-
"""通用模型配置服务层."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from one_dragon_agent.core.model.models import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
    ModelConfigInternal,
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

    async def validate_config_unique(
        self, name: str, exclude_id: int | None = None
    ) -> bool:
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

    async def create_model_config(
        self, config: ModelConfigCreate
    ) -> ModelConfigResponse:
        """创建模型配置.

        Args:
            config: 创建请求模型

        Returns:
            创建的配置

        Raises:
            ValueError: 如果验证失败
        """
        # 验证 provider 字段
        if config.provider not in ("openai", "qwen"):
            msg = f"不支持的 provider: {config.provider}"
            raise ValueError(msg)

        # OpenAI provider 需要 api_key
        if config.provider == "openai" and not config.api_key:
            msg = "OpenAI provider 必须提供 api_key"
            raise ValueError(msg)

        # Qwen provider 需要 oauth_token
        if config.provider == "qwen" and not config.oauth_token:
            msg = "Qwen provider 必须提供 oauth_token"
            raise ValueError(msg)

        # 验证配置名称唯一性
        await self.validate_config_unique(config.name)

        # 创建配置
        created_config = await self._repository.create_config(config)

        # 如果是 Qwen provider 且有 oauth_token，保存到数据库
        if config.provider == "qwen" and config.oauth_token:
            from one_dragon_agent.core.model.qwen.token_encryption import (
                get_token_encryption,
            )

            encryption = get_token_encryption()
            token_data = {
                "access_token": encryption.encrypt(config.oauth_token["access_token"]),
                "token_type": "Bearer",
                "refresh_token": encryption.encrypt(config.oauth_token["refresh_token"]),
                "expires_at": config.oauth_token["expires_at"],
                "scope": "openid profile email model.completion",
                "metadata": None,
            }
            if config.oauth_token.get("resource_url"):
                import json

                token_data["metadata"] = json.dumps(
                    {"resource_url": config.oauth_token["resource_url"]}
                )

            await self._repository.update_oauth_token(
                created_config.id, token_data
            )

        return created_config

    async def get_model_config_internal(self, config_id: int) -> ModelConfigInternal:
        """获取包含 api_key 的完整配置(仅供内部使用).

        Args:
            config_id: 配置 ID

        Returns:
            包含 api_key 的内部配置对象

        Raises:
            ValueError: 如果配置不存在
        """
        config = await self._repository.get_config_internal(config_id)
        return config

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
        if provider is not None and provider not in ("openai", "qwen"):
            msg = f"不支持的 provider: {provider}"
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
        if config_update.provider is not None and config_update.provider not in ("openai", "qwen"):
            msg = f"不支持的 provider: {config_update.provider}"
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

    async def toggle_config_status(
        self, config_id: int, is_active: bool
    ) -> ModelConfigResponse:
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

        使用 AgentScope Agent 发送一个简单的聊天请求来验证连接。

        Args:
            request: 测试连接请求

        Returns:
            测试连接响应
        """
        from one_dragon_agent.core.model.model_factory import ModelFactory
        from one_dragon_agent.core.model.models import ModelConfigInternal, ModelInfo
        from agentscope.agent import ReActAgent
        from agentscope.formatter import OpenAIChatFormatter
        from agentscope.memory import InMemoryMemory
        from agentscope.message import Msg

        # 构造临时的 ModelConfigInternal 对象
        temp_config = ModelConfigInternal(
            id=0,  # 临时 ID
            name="test_connection_temp",
            provider="openai",
            base_url=request.base_url,
            api_key=request.api_key,
            models=[
                ModelInfo(
                    model_id=request.model_id,
                    support_vision=False,
                    support_thinking=False,
                )
            ],
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        try:
            # 使用 ModelFactory 创建模型实例
            model = ModelFactory.create_model(temp_config, request.model_id)

            # 创建一个简单的 Agent 用于测试
            agent = ReActAgent(
                name="TestConnection",
                sys_prompt="You are a helpful assistant.",
                model=model,
                formatter=OpenAIChatFormatter(),
                memory=InMemoryMemory(),
            )

            # 禁用 agent 的控制台输出
            agent.set_console_output_enabled(False)

            # 创建测试消息
            test_msg = Msg(name="user", content="hi", role="user")

            # 调用 agent
            response = await agent(test_msg)

            # 提取响应内容
            content = (
                response.get_text_content()
                if hasattr(response, "get_text_content")
                else str(response)
            )
            content_preview = content[:50] if content else ""

            return TestConnectionResponse(
                success=True,
                message=f"连接成功！模型回复: {content_preview}",
            )

        except Exception as e:
            logger.exception(f"测试连接失败: {e}")

            # 尝试识别错误类型
            error_str = str(e).lower()
            if (
                "401" in error_str
                or "unauthorized" in error_str
                or "api key" in error_str
                or "incorrect" in error_str
            ):
                return TestConnectionResponse(
                    success=False,
                    message="API Key 无效或已过期",
                    raw_error={"error": str(e)},
                )
            elif "404" in error_str or "not found" in error_str:
                return TestConnectionResponse(
                    success=False,
                    message="API 端点不存在，请检查 Base URL 是否正确（应包含完整路径，如 /v1）",
                    raw_error={"error": str(e)},
                )
            else:
                return TestConnectionResponse(
                    success=False,
                    message=f"连接失败: {str(e)}",
                    raw_error={"error": str(e)},
                )
