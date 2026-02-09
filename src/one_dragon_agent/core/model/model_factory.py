# -*- coding: utf-8 -*-
"""模型工厂类，用于根据配置创建模型实例."""

from one_dragon_agent.core.model.models import ModelConfigInternal
from one_dragon_agent.core.model.qwen.qwen_chat_model import QwenChatModel
from one_dragon_agent.core.system.log import get_logger

logger = get_logger(__name__)


class ModelFactory:
    """模型工厂类.

    根据模型配置创建对应的 AgentScope 模型实例。
    支持 OpenAI 和 Qwen 两种提供商。
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
            client_args={"base_url": config.base_url},
        )

    @staticmethod
    def _create_qwen_model(config: ModelConfigInternal, model_id: str):
        """创建 Qwen 模型实例.

        Args:
            config: 模型配置对象
            model_id: 要使用的模型 ID

        Returns:
            QwenChatModel 实例

        """
        logger.info(f"创建 Qwen 模型: {model_id}")

        # Qwen 模型使用 OAuth 认证，不需要 api_key
        # 注意：Qwen 的 model_id 需要符合其命名规范
        return QwenChatModel(model_name=model_id)
