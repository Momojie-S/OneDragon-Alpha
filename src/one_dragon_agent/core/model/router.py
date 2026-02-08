# -*- coding: utf-8 -*-
"""通用模型配置 API 路由."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from one_dragon_agent.core.model.models import (
    ModelConfigCreate,
    ModelConfigResponse,
    ModelConfigUpdate,
    PaginatedModelConfigResponse,
    TestConnectionRequest,
    TestConnectionResponse,
)
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
    provider: Annotated[
        str | None, Query(description="提供商（可选过滤条件）")
    ] = None,
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
