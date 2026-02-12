# -*- coding: utf-8 -*-
"""通用模型配置 API 路由."""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from one_dragon_agent.core.model.models import (
    ModelConfigCreate,
    ModelConfigResponse,
    ModelConfigUpdate,
    PaginatedModelConfigResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
from one_dragon_agent.core.model.repository import model_configs_table
from one_dragon_agent.core.model.service import ModelConfigService
from one_dragon_agent.core.system.log import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/models/configs", tags=["模型配置"])


async def get_db_session() -> AsyncSession:
    """获取数据库会话依赖.

    Yields:
        AsyncSession: 数据库会话

    Raises:
        HTTPException: 如果无法获取数据库会话
    """
    from one_dragon_alpha.services.mysql import MySQLConnectionService

    try:
        # 获取 MySQL 连接服务实例
        mysql_service = MySQLConnectionService()
        async with await mysql_service.get_session() as session:
            yield session
    except Exception as e:
        logger.error(f"无法获取数据库会话: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法连接到数据库",
        ) from e


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "",
    response_model=ModelConfigResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建模型配置",
)
async def create_config(
    config: ModelConfigCreate,
    session: SessionDep,
) -> ModelConfigResponse:
    """创建新的模型配置.

    Args:
        config: 创建请求模型
        session: 数据库会话

    Returns:
        创建的配置

    Raises:
        HTTPException: 如果创建失败
    """
    try:
        service = ModelConfigService(session)
        return await service.create_model_config(config)
    except ValueError as e:
        logger.error(f"创建配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("创建配置时发生未知错误")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误",
        ) from e


@router.get(
    "",
    response_model=PaginatedModelConfigResponse,
    summary="获取模型配置列表",
)
async def list_configs(
    page: Annotated[int, Query(ge=1, description="页码")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="每页记录数")] = 20,
    is_active: Annotated[
        bool | None, Query(description="是否启用（可选过滤条件）")
    ] = None,
    provider: Annotated[str | None, Query(description="提供商（可选过滤条件）")] = None,
    session: SessionDep = None,
) -> PaginatedModelConfigResponse:
    """获取模型配置列表（支持分页和过滤）.

    Args:
        page: 页码（从 1 开始）
        page_size: 每页记录数（最大 100）
        is_active: 是否启用（可选过滤条件）
        provider: 提供商（可选过滤条件）
        session: 数据库会话

    Returns:
        分页响应

    Raises:
        HTTPException: 如果查询失败
    """
    try:
        service = ModelConfigService(session)
        return await service.list_model_configs(
            page=page,
            page_size=page_size,
            is_active=is_active,
            provider=provider,
        )
    except ValueError as e:
        logger.error(f"查询配置列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("查询配置列表时发生未知错误")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误",
        ) from e


@router.delete(
    "/cleanup-test-data",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="清理测试数据（仅测试环境）",
    include_in_schema=False,  # 不在 OpenAPI 文档中显示
)
async def cleanup_test_data(
    session: SessionDep,
    x_test_token: Annotated[str, Header(...)],
    request: Request,
) -> None:
    """清理测试期间创建的数据.

    此接口仅用于测试环境，用于清理测试创建的配置数据。
    通过请求头 x-test-token 验证测试权限。

    清理规则：
    - 删除名称以 'test_' 或 'E2E' 开头的配置
    - 删除名称包含 'E2E Test' 的配置

    Args:
        session: 数据库会话
        x_test_token: 测试令牌（必须与环境变量 TEST_TOKEN 匹配）
        request: FastAPI Request 对象，用于获取客户端信息

    Raises:
        HTTPException: 401 如果测试令牌无效
    """
    # 验证测试令牌
    expected_token = os.getenv("TEST_TOKEN", "test-token-123")
    if x_test_token != expected_token:
        client_host = request.client.host if request.client else "unknown"
        logger.warning(f"无效的测试令牌，来自: {client_host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的测试令牌",
        )

    try:
        # 使用 ORM 表达式 API 构建删除条件（避免 SQL 注入）
        delete_conditions = or_(
            model_configs_table.c.name.like("test_%"),
            model_configs_table.c.name.like("E2E%"),
            model_configs_table.c.name.like("%E2E Test%"),
        )

        # 执行删除
        delete_stmt = delete(model_configs_table).where(delete_conditions)
        result = await session.execute(delete_stmt)
        deleted_count = result.rowcount
        await session.commit()

        logger.info(f"已清理 {deleted_count} 条测试数据")

    except Exception as e:
        await session.rollback()
        logger.exception(f"清理测试数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理失败: {str(e)}",
        ) from e


@router.get(
    "/{config_id}",
    response_model=ModelConfigResponse,
    summary="获取单个模型配置",
)
async def get_config(
    config_id: int,
    session: SessionDep,
) -> ModelConfigResponse:
    """获取单个模型配置.

    Args:
        config_id: 配置 ID
        session: 数据库会话

    Returns:
        配置对象

    Raises:
        HTTPException: 如果配置不存在
    """
    try:
        service = ModelConfigService(session)
        return await service.get_model_config(config_id)
    except ValueError as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("获取配置时发生未知错误")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误",
        ) from e


@router.put(
    "/{config_id}",
    response_model=ModelConfigResponse,
    summary="更新模型配置",
)
async def update_config(
    config_id: int,
    config_update: ModelConfigUpdate,
    session: SessionDep,
) -> ModelConfigResponse:
    """更新模型配置.

    Args:
        config_id: 配置 ID
        config_update: 更新请求模型
        session: 数据库会话

    Returns:
        更新后的配置

    Raises:
        HTTPException: 如果更新失败
    """
    try:
        service = ModelConfigService(session)
        return await service.update_model_config(config_id, config_update)
    except ValueError as e:
        logger.error(f"更新配置失败: {e}")
        # 检查是否是乐观锁错误
        if "已被其他用户修改" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("更新配置时发生未知错误")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误",
        ) from e


@router.delete(
    "/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除模型配置",
)
async def delete_config(
    config_id: int,
    session: SessionDep,
) -> None:
    """删除模型配置.

    Args:
        config_id: 配置 ID
        session: 数据库会话

    Raises:
        HTTPException: 如果删除失败
    """
    try:
        service = ModelConfigService(session)
        await service.delete_model_config(config_id)
    except ValueError as e:
        logger.error(f"删除配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("删除配置时发生未知错误")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误",
        ) from e


@router.patch(
    "/{config_id}/status",
    response_model=ModelConfigResponse,
    summary="切换配置启用状态",
)
async def toggle_config_status(
    config_id: int,
    is_active: bool,
    session: SessionDep,
) -> ModelConfigResponse:
    """切换配置启用状态.

    Args:
        config_id: 配置 ID
        is_active: 是否启用
        session: 数据库会话

    Returns:
        更新后的配置

    Raises:
        HTTPException: 如果更新失败
    """
    try:
        service = ModelConfigService(session)
        return await service.toggle_config_status(config_id, is_active)
    except ValueError as e:
        logger.error(f"切换配置状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("切换配置状态时发生未知错误")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误",
        ) from e


@router.post(
    "/test-connection",
    response_model=TestConnectionResponse,
    summary="测试 API 连接",
)
async def test_connection(
    request: TestConnectionRequest,
) -> TestConnectionResponse:
    """测试 API 连接.

    Args:
        request: 测试连接请求

    Returns:
        测试连接响应
    """
    try:
        return await ModelConfigService.test_connection(request)
    except Exception as e:
        logger.exception("测试连接时发生未知错误")
        return TestConnectionResponse(
            success=False,
            message=f"测试失败: {str(e)}",
            raw_error={"error": str(e)},
        )


@router.delete(
    "/cleanup-test-data",
    summary="清理测试数据",
    description="删除所有以 test_e2e_ 开头的测试配置（需要 x-test-token 验证）",
)
async def cleanup_test_data(
    session: SessionDep,
    x_test_token: Annotated[
        str | None, Header(alias="x-test-token", description="测试令牌")
    ] = None,
) -> dict:
    """清理所有测试数据.

    仅删除名称以 'test_e2e_' 开头的配置。
    需要通过 x-test-token 请求头验证。

    Args:
        session: 数据库会话
        x_test_token: 测试令牌

    Returns:
        删除结果

    Raises:
        HTTPException: 如果令牌验证失败
    """
    # 验证测试令牌
    test_token = os.getenv("TEST_TOKEN")
    if not test_token:
        logger.warning("尝试清理测试数据，但 TEST_TOKEN 未配置")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="测试功能在生产环境中被禁用",
        )

    if x_test_token != test_token:
        logger.warning(f"测试令牌验证失败: {x_test_token}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的测试令牌",
        )

    try:
        from one_dragon_agent.core.model.repository import ModelConfigRepository

        repo = ModelConfigRepository(session)
        deleted_count = await repo.cleanup_test_data(prefix="test_e2e_")

        logger.info(f"测试数据清理成功，删除 {deleted_count} 条记录")
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"已删除 {deleted_count} 条测试数据",
        }

    except Exception as e:
        logger.exception(f"清理测试数据时发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理失败: {str(e)}",
        ) from e


@router.get(
    "/test-data-stats",
    summary="获取测试数据统计",
    description="获取测试数据的统计信息（需要 x-test-token 验证）",
)
async def get_test_data_stats(
    session: SessionDep,
    x_test_token: Annotated[
        str | None, Header(alias="x-test-token", description="测试令牌")
    ] = None,
) -> dict:
    """获取测试数据统计信息.

    Args:
        session: 数据库会话
        x_test_token: 测试令牌

    Returns:
        测试数据统计信息

    Raises:
        HTTPException: 如果令牌验证失败
    """
    # 验证测试令牌
    test_token = os.getenv("TEST_TOKEN")
    if not test_token:
        logger.warning("尝试获取测试数据统计，但 TEST_TOKEN 未配置")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="测试功能在生产环境中被禁用",
        )

    if x_test_token != test_token:
        logger.warning(f"测试令牌验证失败: {x_test_token}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的测试令牌",
        )

    try:
        from one_dragon_agent.core.model.repository import ModelConfigRepository

        repo = ModelConfigRepository(session)
        stats = await repo.get_test_data_stats(prefix="test_e2e_")

        return {
            "test_data_count": stats["test_data_count"],
            "test_data_prefixes": stats["test_data_prefixes"],
            "oldest_test_data": stats["oldest_test_data"].isoformat()
            if stats.get("oldest_test_data")
            else None,
            "newest_test_data": stats["newest_test_data"].isoformat()
            if stats.get("newest_test_data")
            else None,
        }

    except Exception as e:
        logger.exception(f"获取测试数据统计时发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计失败: {str(e)}",
        ) from e

