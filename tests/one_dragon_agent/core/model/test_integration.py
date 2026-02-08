# -*- coding: utf-8 -*-
"""通用模型配置集成测试（使用真实数据库）.

这些测试使用真实的数据库连接，验证完整的数据流。
运行时使用 pytest -m "not integration" 跳过集成测试。

每个测试都会自动清理数据，确保可以重复运行。
"""

import asyncio
import os
from datetime import datetime
from typing import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from one_dragon_agent.core.model.models import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelInfo,
)
from one_dragon_agent.core.model.repository import ModelConfigRepository
from one_dragon_agent.core.model.service import ModelConfigService


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

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话."""
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


# ============================================================================
# 辅助函数
# ============================================================================

def generate_unique_name(prefix: str = "测试") -> str:
    """生成唯一的配置名称."""
    return f"{prefix}_{uuid4().hex[:8]}"


async def cleanup_test_configs(session: AsyncSession, *config_ids: int) -> None:
    """清理测试创建的配置.

    Args:
        session: 数据库会话
        *config_ids: 要删除的配置 ID 列表
    """
    repository = ModelConfigRepository(session)
    for config_id in config_ids:
        try:
            await repository.delete_config(config_id)
        except Exception:
            pass  # 忽略清理时的错误


# ============================================================================
# 集成测试
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_get_config(db_session: AsyncSession) -> None:
    """测试创建和查询配置（关键场景1）."""
    repository = ModelConfigRepository(db_session)

    config_create = ModelConfigCreate(
        name=generate_unique_name("创建测试"),
        provider="openai",
        base_url="https://api.openai.com",
        api_key="sk-test-123",
        models=[ModelInfo(model_id="gpt-4", support_vision=True, support_thinking=False)],
        is_active=True,
    )

    # 创建配置
    created = await repository.create_config(config_create)
    assert created.id > 0
    assert created.name == config_create.name

    # 查询配置
    fetched = await repository.get_config_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id

    # 清理
    await cleanup_test_configs(db_session, created.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_config(db_session: AsyncSession) -> None:
    """测试更新配置（关键场景2）."""
    repository = ModelConfigRepository(db_session)

    config_create = ModelConfigCreate(
        name=generate_unique_name("更新测试"),
        provider="openai",
        base_url="https://api.openai.com",
        api_key="sk-test",
        models=[ModelInfo(model_id="gpt-4", support_vision=False, support_thinking=False)],
        is_active=True,
    )

    created = await repository.create_config(config_create)
    original_updated_at = created.updated_at

    await asyncio.sleep(0.1)  # 确保 updated_at 会变化

    update_data = ModelConfigUpdate(
        name="已更新",
        is_active=False,
        updated_at=original_updated_at,
    )
    updated = await repository.update_config(created.id, update_data)

    assert updated.name == "已更新"
    assert updated.is_active is False

    # 清理
    await cleanup_test_configs(db_session, created.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pagination(db_session: AsyncSession) -> None:
    """测试分页查询（关键场景3）."""
    repository = ModelConfigRepository(db_session)
    created_ids = []

    # 创建5个配置
    for i in range(5):
        config = ModelConfigCreate(
            name=generate_unique_name(f"分页{i}"),
            provider="openai",
            base_url=f"https://api{i}.test.com",
            api_key=f"sk-{i}",
            models=[ModelInfo(model_id=f"model-{i}", support_vision=False, support_thinking=False)],
            is_active=True,
        )
        created = await repository.create_config(config)
        created_ids.append(created.id)

    # 测试第一页
    configs, total = await repository.get_configs(page=1, page_size=3)
    assert total >= 5
    assert len(configs) == 3

    # 测试第二页
    configs_page2, _ = await repository.get_configs(page=2, page_size=3)
    assert len(configs_page2) >= 2

    # 清理
    await cleanup_test_configs(db_session, *created_ids)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_by_status(db_session: AsyncSession) -> None:
    """测试按启用状态过滤（关键场景4）."""
    repository = ModelConfigRepository(db_session)

    # 创建启用的配置
    config_active = ModelConfigCreate(
        name=generate_unique_name("启用配置"),
        provider="openai",
        base_url="https://api.test.com",
        api_key="sk-active",
        models=[ModelInfo(model_id="gpt-4", support_vision=False, support_thinking=False)],
        is_active=True,
    )
    created_active = await repository.create_config(config_active)

    # 创建禁用的配置
    config_inactive = ModelConfigCreate(
        name=generate_unique_name("禁用配置"),
        provider="openai",
        base_url="https://api.test.com",
        api_key="sk-inactive",
        models=[ModelInfo(model_id="gpt-4", support_vision=False, support_thinking=False)],
        is_active=False,
    )
    created_inactive = await repository.create_config(config_inactive)

    # 测试过滤启用的配置
    active_configs, _ = await repository.get_configs(is_active=True)
    assert any(c.id == created_active.id for c in active_configs)

    # 测试过滤禁用的配置
    inactive_configs, _ = await repository.get_configs(is_active=False)
    assert any(c.id == created_inactive.id for c in inactive_configs)

    # 清理
    await cleanup_test_configs(db_session, created_active.id, created_inactive.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_config(db_session: AsyncSession) -> None:
    """测试删除配置（关键场景5）."""
    repository = ModelConfigRepository(db_session)

    config_create = ModelConfigCreate(
        name=generate_unique_name("删除测试"),
        provider="openai",
        base_url="https://api.test.com",
        api_key="sk-delete",
        models=[ModelInfo(model_id="gpt-4", support_vision=False, support_thinking=False)],
        is_active=True,
    )

    created = await repository.create_config(config_create)
    config_id = created.id

    # 删除配置
    await repository.delete_config(config_id)

    # 验证已删除
    fetched = await repository.get_config_by_id(config_id)
    assert fetched is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_unique_name_constraint(db_session: AsyncSession) -> None:
    """测试配置名称唯一性约束（关键场景6）."""
    repository = ModelConfigRepository(db_session)

    config_name = generate_unique_name("唯一性测试")
    config_create = ModelConfigCreate(
        name=config_name,
        provider="openai",
        base_url="https://api.test.com",
        api_key="sk-unique",
        models=[ModelInfo(model_id="gpt-4", support_vision=False, support_thinking=False)],
        is_active=True,
    )

    # 创建第一个配置
    await repository.create_config(config_create)

    # 尝试创建同名配置，应该失败
    with pytest.raises(ValueError, match="已存在"):
        await repository.create_config(config_create)

    # 清理
    configs, _ = await repository.get_configs()
    for config in configs:
        if config.name == config_name:
            await repository.delete_config(config.id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_crud_workflow(db_session: AsyncSession) -> None:
    """测试完整的 CRUD 工作流（关键场景7 - 端到端）."""
    service = ModelConfigService(db_session)

    # Create
    config_create = ModelConfigCreate(
        name=generate_unique_name("CRUD测试"),
        provider="openai",
        base_url="https://api.test.com",
        api_key="sk-crud",
        models=[ModelInfo(model_id="gpt-4", support_vision=False, support_thinking=False)],
        is_active=True,
    )
    created = await service.create_model_config(config_create)
    config_id = created.id

    # Read
    fetched = await service.get_model_config(config_id)
    assert fetched.id == config_id

    # Update
    await asyncio.sleep(0.1)
    update_data = ModelConfigUpdate(name="已更新", updated_at=fetched.updated_at)
    updated = await service.update_model_config(config_id, update_data)
    assert updated.name == "已更新"

    # Delete
    deleted = await service.delete_model_config(config_id)
    assert deleted is True

    # Verify deleted
    with pytest.raises(ValueError, match="不存在"):
        await service.get_model_config(config_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_optimistic_lock(db_session: AsyncSession) -> None:
    """测试乐观锁冲突（关键场景8）."""
    service = ModelConfigService(db_session)

    config_create = ModelConfigCreate(
        name=generate_unique_name("乐观锁测试"),
        provider="openai",
        base_url="https://api.test.com",
        api_key="sk-lock",
        models=[ModelInfo(model_id="gpt-4", support_vision=False, support_thinking=False)],
        is_active=True,
    )
    created = await service.create_model_config(config_create)
    config_id = created.id
    original_updated_at = created.updated_at

    # 用户A更新成功
    await asyncio.sleep(0.1)
    update_a = ModelConfigUpdate(name=generate_unique_name("用户A"), updated_at=original_updated_at)
    await service.update_model_config(config_id, update_a)

    # 用户B使用旧的 updated_at 尝试更新，应该失败
    # 注意：这里使用不同的名称避免触发唯一性约束
    update_b = ModelConfigUpdate(name=generate_unique_name("用户B"), updated_at=original_updated_at)
    with pytest.raises(ValueError, match="已被其他用户修改"):
        await service.update_model_config(config_id, update_b)

    # 清理
    await service.delete_model_config(config_id)


# ============================================================================
# 测试执行说明
# ============================================================================

"""
运行所有测试（包括集成测试）:
    uv run --env-file .env pytest tests/one_dragon_agent/core/model/ -v

只运行单元测试（跳过集成测试）:
    uv run --env-file .env pytest tests/one_dragon_agent/core/model/ -v -m "not integration"

只运行集成测试:
    uv run --env-file .env pytest tests/one_dragon_agent/core/model/ -v -m "integration"

查看集成测试覆盖率:
    uv run --env-file .env pytest tests/one_dragon_agent/core/model/test_integration.py -v --cov=src/one_dragon_agent/core/model
"""
