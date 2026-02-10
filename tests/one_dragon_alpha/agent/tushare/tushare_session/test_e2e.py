# -*- coding: utf-8 -*-
"""TushareSession 端到端测试.

这些测试使用真实的数据库和真实的 AI 模型 API 调用，
验证 TushareSession 类的完整功能。
"""

import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from one_dragon_agent.core.model.models import (
    ModelConfigCreate,
    ModelInfo,
)
from one_dragon_agent.core.model.service import ModelConfigService
from one_dragon_agent.core.system.log import get_logger
from one_dragon_alpha.agent.tushare.tushare_session import TushareSession
from agentscope.memory import InMemoryMemory

logger = get_logger(__name__)


# ============================================================================
# 测试配置
# ============================================================================

TEST_DB_HOST = os.getenv("MYSQL_HOST", "localhost")
TEST_DB_PORT = os.getenv("MYSQL_PORT", "21001")
TEST_DB_USER = os.getenv("MYSQL_USER", "root")
TEST_DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
TEST_DB_DATABASE = os.getenv("MYSQL_DATABASE", "one_dragon_alpha")
DATABASE_URL = f"mysql+aiomysql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_DATABASE}"


# ============================================================================
# Fixtures
# ============================================================================


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话.

    每个测试函数使用独立的数据库会话，确保测试之间互不影响.

    Yields:
        AsyncSession: 测试用的数据库会话
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_configs(db_session: AsyncSession):
    """获取测试用的模型配置.

    使用数据库中已有的真实配置（ModelScope-Free），确保可以调用真实 API。

    Args:
        db_session: 数据库会话

    Yields:
        tuple: (config1, config2, service, cleanup_configs) 测试配置、服务实例和清理函数
    """
    service = ModelConfigService(db_session)
    import uuid

    # 使用数据库中已有的 ModelScope-Free 配置（ID=1）
    config1 = await service.get_model_config_internal(1)

    # 创建第二个测试配置（使用 config1 的 API Key，避免配置多套凭据）
    unique_suffix2 = uuid.uuid4().hex[:8]
    config2_response = await service.create_model_config(
        ModelConfigCreate(
            name=f"test_e2e_config_2_{unique_suffix2}",
            provider="openai",
            base_url=config1.base_url,
            api_key=config1.api_key,
            models=[
                ModelInfo(
                    model_id="ZhipuAI/GLM-4.7-Flash",
                    support_vision=False,
                    support_thinking=False,
                ),
            ],
        )
    )

    # 获取完整的内部配置（包含 api_key）
    config2_internal = await service.get_model_config_internal(config2_response.id)

    # 记录需要清理的配置 ID（只清理 config2，config1 是真实数据不清理）
    created_config_ids = [config2_response.id]

    # 定义清理函数
    async def cleanup_configs():
        """清理测试创建的配置."""
        cleanup_errors = []
        for config_id in created_config_ids:
            try:
                await service.delete_model_config(config_id)
                logger.info(f"已清理测试配置: ID {config_id}")
            except Exception as e:
                error_msg = f"清理配置 {config_id} 失败: {e}"
                logger.error(error_msg)
                cleanup_errors.append(error_msg)

        # 如果有清理失败，抛出异常让测试失败
        if cleanup_errors:
            raise AssertionError(f"测试数据清理失败: {'; '.join(cleanup_errors)}")

    yield config1, config2_internal, service, cleanup_configs

    # 清理测试配置
    await cleanup_configs()


# ============================================================================
# 端到端测试
# ============================================================================


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(60)
async def test_create_session_and_send_chat_request(test_configs):
    """测试场景: 创建 session 并发送聊天请求.

    验证:
    1. 可以成功创建 TushareSession 实例
    2. 可以使用模型配置发送聊天请求
    3. 能够接收到 AI 的响应

    Args:
        test_configs: 测试配置 fixture
    """
    config1, config2, service, _ = test_configs
    session_id = "test_session_e2e_001"
    memory = InMemoryMemory()

    # 创建 TushareSession
    session = TushareSession(
        session_id=session_id,
        memory=memory,
    )

    # 发送聊天请求
    messages = []
    async for message in session.chat(
        user_input="你好",
        model_config_id=config1.id,
        model_id=config1.models[0].model_id,
        config=config1,
    ):
        messages.append(message)
        if message.msg:
            content_preview = (
                str(message.msg.content)[:50] if message.msg.content else ""
            )
            logger.info(f"收到消息: {content_preview}...")

        # 持续接收直到响应完成
        if message.response_completed:
            logger.info("响应已完成")
            break

    # 验证收到了响应
    assert len(messages) > 0, "应该至少收到一条消息"

    # 验证最后一条消息标记响应完成
    assert messages[-1].response_completed is True, "最后一条消息应该标记响应完成"

    # 验证至少有一条消息包含内容
    content_messages = [m for m in messages if m.msg is not None and m.msg.content]
    assert len(content_messages) > 0, "应该至少有一条消息包含内容"

    logger.info(f"测试通过: 收到 {len(messages)} 条消息")
    logger.info(f"AI 响应: {str(content_messages[0].msg.content)[:100]}...")


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(120)
async def test_same_config_reuse_agent(test_configs):
    """测试场景: 相同的 model_config_id 和 model_id 复用 Agent.

    验证:
    1. 第一次聊天请求创建 Agent
    2. 第二次使用相同配置的请求复用 Agent
    3. Agent 对象未被重建

    Args:
        test_configs: 测试配置 fixture
    """
    config1, config2, service, _ = test_configs
    session_id = "test_session_e2e_002"
    memory = InMemoryMemory()

    session = TushareSession(
        session_id=session_id,
        memory=memory,
    )

    # 第一次聊天请求
    agent_id_before = id(session.agent)
    logger.info(f"第一次聊天前 Agent ID: {agent_id_before}")

    async for message in session.chat(
        user_input="你好",
        model_config_id=config1.id,
        model_id=config1.models[0].model_id,
        config=config1,
    ):
        if message.response_completed:
            break

    agent_id_after_first = id(session.agent)
    logger.info(f"第一次聊天后 Agent ID: {agent_id_after_first}")

    # 第二次聊天请求（使用相同的配置）
    async for message in session.chat(
        user_input="再问一个问题",
        model_config_id=config1.id,
        model_id=config1.models[0].model_id,
        config=config1,
    ):
        if message.response_completed:
            break

    agent_id_after_second = id(session.agent)
    logger.info(f"第二次聊天后 Agent ID: {agent_id_after_second}")

    # 验证 Agent 对象未被重建
    assert agent_id_after_first == agent_id_after_second, "相同配置应该复用 Agent"

    logger.info(f"测试通过: Agent 被复用 (ID: {agent_id_after_first})")


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(120)
async def test_different_config_rebuild_agent(test_configs):
    """测试场景: model_config_id 不同时重建 Agent.

    验证:
    1. 第一次聊天请求使用 config1
    2. 第二次聊天请求使用 config2
    3. Agent 对象被重建

    Args:
        test_configs: 测试配置 fixture
    """
    config1, config2, service, _ = test_configs
    session_id = "test_session_e2e_003"
    memory = InMemoryMemory()

    session = TushareSession(
        session_id=session_id,
        memory=memory,
    )

    # 第一次聊天请求使用 config1
    async for message in session.chat(
        user_input="你好",
        model_config_id=config1.id,
        model_id=config1.models[0].model_id,
        config=config1,
    ):
        if message.response_completed:
            break

    agent_id_after_first = id(session.agent)
    model_after_first = session.agent.model
    logger.info(
        f"第一次聊天后 Agent ID: {agent_id_after_first}, Model: {model_after_first}"
    )

    # 第二次聊天请求使用 config2（不同配置）
    async for message in session.chat(
        user_input="换个模型再问一次",
        model_config_id=config2.id,
        model_id=config2.models[0].model_id,
        config=config2,
    ):
        if message.response_completed:
            break

    agent_id_after_second = id(session.agent)
    model_after_second = session.agent.model
    logger.info(
        f"第二次聊天后 Agent ID: {agent_id_after_second}, Model: {model_after_second}"
    )

    # 验证 Agent 对象被重建
    assert agent_id_after_first != agent_id_after_second, "不同配置应该重建 Agent"

    logger.info("测试通过: Agent 被重建")


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(120)
async def test_different_model_id_rebuild_agent(test_configs):
    """测试场景: model_id 不同时重建 Agent（配置相同）.

    验证:
    1. 第一次聊天请求使用 config1 的 model1
    2. 第二次聊天请求使用 config1 的 model2
    3. Agent 对象被重建

    注意: config1 初始包含两个模型，无需更新配置。

    Args:
        test_configs: 测试配置 fixture
    """
    config1, config2, service, _ = test_configs
    session_id = "test_session_e2e_004"
    memory = InMemoryMemory()

    # 保存 config1 的原始 models 以便测试后恢复
    original_config1_models = config1.models.copy()

    # 先更新 config1 添加第二个模型（两个模型使用相同的 API）
    from one_dragon_agent.core.model.models import ModelConfigUpdate

    try:
        await service.update_model_config(
            config1.id,
            ModelConfigUpdate(
                models=[
                    ModelInfo(
                        model_id="moonshotai/Kimi-K2.5",
                        support_vision=False,
                        support_thinking=False,
                    ),
                    ModelInfo(
                        model_id="Qwen/Qwen2.5-72B-Instruct",
                        support_vision=False,
                        support_thinking=False,
                    ),
                ],
            ),
        )

        # 获取更新后的完整内部配置
        updated_config = await service.get_model_config_internal(config1.id)

    session = TushareSession(
        session_id=session_id,
        memory=memory,
    )

    # 第一次聊天请求使用第一个模型
    async for message in session.chat(
        user_input="你好",
        model_config_id=config1.id,
        model_id="moonshotai/Kimi-K2.5",
        config=updated_config,
    ):
        if message.response_completed:
            break

    agent_id_after_first = id(session.agent)
    logger.info(f"第一次聊天后 Agent ID: {agent_id_after_first}")

    # 第二次聊天请求使用第二个模型（同一配置）
    async for message in session.chat(
        user_input="换个模型再问一次",
        model_config_id=config1.id,
        model_id="Qwen/Qwen2.5-72B-Instruct",
        config=updated_config,
    ):
        if message.response_completed:
            break

    agent_id_after_second = id(session.agent)
    logger.info(f"第二次聊天后 Agent ID: {agent_id_after_second}")

    # 验证 Agent 对象被重建
    assert agent_id_after_first != agent_id_after_second, "不同 model_id 应该重建 Agent"

    logger.info("测试通过: Agent 被重建")

    finally:
        # 恢复 config1 的原始 models
        try:
            await service.update_model_config(
                config1.id,
                ModelConfigUpdate(models=original_config1_models),
            )
            logger.info(f"已恢复 config1 (ID={config1.id}) 的原始 models 配置")
        except Exception as e:
            logger.warning(f"恢复 config1 配置失败: {e}")


@pytest.mark.e2e
@pytest.mark.asyncio
@pytest.mark.timeout(120)
async def test_switch_model_clears_analyse_cache(test_configs):
    """测试场景: 切换模型时清空分析 Agent 缓存.

    验证:
    1. 使用 analyse_by_code 工具创建分析 Agent
    2. 切换主模型的配置
    3. 分析 Agent 缓存被清空

    Args:
        test_configs: 测试配置 fixture
    """
    config1, config2, service, _ = test_configs
    session_id = "test_session_e2e_005"
    memory = InMemoryMemory()

    session = TushareSession(
        session_id=session_id,
        memory=memory,
    )

    # 第一次聊天请求（会初始化 _analyse_by_code_map）
    async for message in session.chat(
        user_input="你好",
        model_config_id=config1.id,
        model_id=config1.models[0].model_id,
        config=config1,
    ):
        if message.response_completed:
            break

    # 模拟创建一个分析 Agent
    session._analyse_by_code_map[1] = "fake_analyse_agent"
    logger.info(f"分析 Agent 缓存: {session._analyse_by_code_map}")

    # 切换到不同配置
    async for message in session.chat(
        user_input="换个模型",
        model_config_id=config2.id,
        model_id=config2.models[0].model_id,
        config=config2,
    ):
        if message.response_completed:
            break

    # 验证分析 Agent 缓存被清空
    assert len(session._analyse_by_code_map) == 0, "切换模型时应清空分析 Agent 缓存"

    logger.info("测试通过: 分析 Agent 缓存已清空")
