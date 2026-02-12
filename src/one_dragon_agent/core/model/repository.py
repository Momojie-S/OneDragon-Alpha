# -*- coding: utf-8 -*-
"""通用模型配置数据库仓库."""

import json
from datetime import datetime

from sqlalchemy import (
    Table,
    MetaData,
    select,
    update,
    delete,
    func,
    Column,
    BigInteger,
    String,
    Text,
    Boolean,
    DateTime,
    Index,
    JSON,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from one_dragon_agent.core.model.models import (
    ModelConfigCreate,
    ModelConfigUpdate,
    ModelConfigResponse,
    ModelConfigInternal,
)
from one_dragon_agent.core.system.log import get_logger

logger = get_logger(__name__)

# 定义表元数据
metadata = MetaData()

# 定义 model_configs 表结构
model_configs_table = Table(
    "model_configs",
    metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("name", String(255), unique=True, nullable=False),
    Column("provider", String(50), nullable=False),
    Column("base_url", Text, nullable=False),
    Column("api_key", Text, nullable=False),
    Column("models", JSON, nullable=False),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime, default=datetime.now),
    Column("updated_at", DateTime, default=datetime.now, onupdate=datetime.now),
    # OAuth 相关字段（003 迁移添加）
    Column("oauth_access_token", Text, nullable=True),
    Column("oauth_token_type", String(50), nullable=True),
    Column("oauth_refresh_token", Text, nullable=True),
    Column("oauth_expires_at", BigInteger, nullable=True),
    Column("oauth_scope", String(500), nullable=True),
    Column("oauth_metadata", JSON, nullable=True),
    Index("idx_name", "name"),
    Index("idx_provider", "provider"),
    Index("idx_is_active", "is_active"),
    Index("idx_oauth_expires_at", "oauth_expires_at"),
)


class ModelConfigORM:
    """模型配置 ORM 模型（使用 SQLAlchemy Core）.

    这是一个辅助类，用于处理数据库记录的序列化和反序列化。
    实际的表结构定义在迁移脚本中。
    """

    TABLE_NAME = "model_configs"

    @staticmethod
    def dict_to_orm(row: dict) -> dict:
        """将数据库记录转换为响应模型.

        Args:
            row: 数据库记录

        Returns:
            响应模型字典
        """
        # 解析 JSON 字段
        models_data = (
            json.loads(row["models"])
            if isinstance(row["models"], str)
            else row["models"]
        )

        return {
            "id": row["id"],
            "name": row["name"],
            "provider": row["provider"],
            "base_url": row["base_url"],
            "models": models_data,
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def create_to_dict(config: ModelConfigCreate) -> dict:
        """将创建请求转换为数据库记录.

        Args:
            config: 创建请求模型

        Returns:
            数据库记录字典
        """
        return {
            "name": config.name,
            "provider": config.provider,
            "base_url": config.base_url,
            "api_key": config.api_key,
            "models": [m.model_dump() for m in config.models],
            "is_active": config.is_active,
        }


class ModelConfigRepository:
    """模型配置仓库类.

    负责处理模型配置的数据库操作。

    Attributes:
        session: SQLAlchemy 异步会话
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化仓库.

        Args:
            session: SQLAlchemy 异步会话
        """
        self._session = session

    async def create_config(self, config: ModelConfigCreate) -> ModelConfigResponse:
        """创建模型配置.

        Args:
            config: 创建请求模型

        Returns:
            创建的配置

        Raises:
            ValueError: 如果配置名称已存在
        """
        table = model_configs_table
        data = ModelConfigORM.create_to_dict(config)
        data["created_at"] = datetime.now()
        data["updated_at"] = datetime.now()

        try:
            # 使用 SQLAlchemy Core 插入数据
            from sqlalchemy import insert

            stmt = insert(table).values(**data)

            result = await self._session.execute(stmt)
            await self._session.commit()

            # 获取插入的 ID
            config_id = result.lastrowid

            # 查询并返回完整的配置
            return await self._get_by_id_internal(config_id)

        except IntegrityError as e:
            await self._session.rollback()
            logger.error(f"创建配置失败: {e}")
            if "name" in str(e):
                msg = f"配置名称 '{config.name}' 已存在"
                raise ValueError(msg) from e
            raise

    async def get_config_by_id(self, config_id: int) -> ModelConfigResponse | None:
        """根据 ID 查询配置.

        Args:
            config_id: 配置 ID

        Returns:
            配置对象，如果不存在则返回 None
        """
        try:
            return await self._get_by_id_internal(config_id)
        except ValueError:
            return None

    async def _get_by_id_internal(self, config_id: int) -> ModelConfigResponse:
        """根据 ID 查询配置（内部方法）。

        Args:
            config_id: 配置 ID

        Returns:
            配置对象

        Raises:
            ValueError: 如果配置不存在
        """
        table = model_configs_table

        stmt = select(table).where(table.c.id == config_id)
        result = await self._session.execute(stmt)
        row = result.fetchone()

        if not row:
            msg = f"配置 ID {config_id} 不存在"
            raise ValueError(msg)

        # 将 SQLAlchemy Row 对象转换为字典
        row_dict = dict(row._mapping)
        config_data = ModelConfigORM.dict_to_orm(row_dict)
        return ModelConfigResponse(**config_data)

    async def get_config_internal(self, config_id: int) -> ModelConfigInternal:
        """根据 ID 查询配置(包含 api_key 和 OAuth 字段,仅供内部使用).

        Args:
            config_id: 配置 ID

        Returns:
            包含 api_key 和 OAuth 字段的内部配置对象

        Raises:
            ValueError: 如果配置不存在
        """
        table = model_configs_table

        stmt = select(table).where(table.c.id == config_id)
        result = await self._session.execute(stmt)
        row = result.fetchone()

        if not row:
            msg = f"配置 ID {config_id} 不存在"
            raise ValueError(msg)

        # 将 SQLAlchemy Row 对象转换为字典
        row_dict = dict(row._mapping)

        # 解析 JSON 字段
        models_data = (
            json.loads(row_dict["models"])
            if isinstance(row_dict["models"], str)
            else row_dict["models"]
        )

        # 解析 OAuth metadata（如果存在）
        oauth_metadata = None
        if row_dict.get("oauth_metadata"):
            try:
                oauth_metadata = (
                    json.loads(row_dict["oauth_metadata"])
                    if isinstance(row_dict["oauth_metadata"], str)
                    else row_dict["oauth_metadata"]
                )
            except (json.JSONDecodeError, TypeError):
                pass

        # 构建 ModelConfigInternal 所需的字典(包含 api_key 和 OAuth 字段)
        config_data = {
            "id": row_dict["id"],
            "name": row_dict["name"],
            "provider": row_dict["provider"],
            "base_url": row_dict["base_url"],
            "api_key": row_dict["api_key"],  # 包含 api_key
            "models": models_data,
            "is_active": bool(row_dict["is_active"]),
            "created_at": row_dict["created_at"],
            "updated_at": row_dict["updated_at"],
            # OAuth 字段
            "oauth_access_token": row_dict.get("oauth_access_token"),
            "oauth_token_type": row_dict.get("oauth_token_type"),
            "oauth_refresh_token": row_dict.get("oauth_refresh_token"),
            "oauth_expires_at": row_dict.get("oauth_expires_at"),
            "oauth_scope": row_dict.get("oauth_scope"),
            "oauth_metadata": oauth_metadata,
        }

        return ModelConfigInternal(**config_data)

    async def get_config_with_oauth(self, config_id: int) -> dict:
        """根据 ID 查询配置(包含 api_key 和 OAuth 字段).

        用于获取包含完整 OAuth token 信息的配置。

        Args:
            config_id: 配置 ID

        Returns:
            包含 api_key 和 OAuth 字段的配置字典

        Raises:
            ValueError: 如果配置不存在
        """
        table = model_configs_table

        stmt = select(table).where(table.c.id == config_id)
        result = await self._session.execute(stmt)
        row = result.fetchone()

        if not row:
            msg = f"配置 ID {config_id} 不存在"
            raise ValueError(msg)

        # 将 SQLAlchemy Row 对象转换为字典
        row_dict = dict(row._mapping)

        # 解析 JSON 字段
        models_data = (
            json.loads(row_dict["models"])
            if isinstance(row_dict["models"], str)
            else row_dict["models"]
        )

        # 解析 OAuth metadata
        oauth_metadata = None
        if row_dict.get("oauth_metadata"):
            try:
                oauth_metadata = (
                    json.loads(row_dict["oauth_metadata"])
                    if isinstance(row_dict["oauth_metadata"], str)
                    else row_dict["oauth_metadata"]
                )
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "id": row_dict["id"],
            "name": row_dict["name"],
            "provider": row_dict["provider"],
            "base_url": row_dict["base_url"],
            "api_key": row_dict["api_key"],
            "models": models_data,
            "is_active": bool(row_dict["is_active"]),
            "created_at": row_dict["created_at"],
            "updated_at": row_dict["updated_at"],
            # OAuth 字段
            "oauth_access_token": row_dict.get("oauth_access_token"),
            "oauth_token_type": row_dict.get("oauth_token_type"),
            "oauth_refresh_token": row_dict.get("oauth_refresh_token"),
            "oauth_expires_at": row_dict.get("oauth_expires_at"),
            "oauth_scope": row_dict.get("oauth_scope"),
            "oauth_metadata": oauth_metadata,
        }

    async def update_oauth_token(
        self, config_id: int, token_data: dict
    ) -> None:
        """更新配置的 OAuth token.

        Args:
            config_id: 配置 ID
            token_data: OAuth token 数据字典

        Raises:
            ValueError: 如果配置不存在
        """
        table = model_configs_table

        stmt = (
            update(table)
            .where(table.c.id == config_id)
            .values(
                oauth_access_token=token_data.get("access_token"),
                oauth_token_type=token_data.get("token_type", "Bearer"),
                oauth_refresh_token=token_data.get("refresh_token"),
                oauth_expires_at=token_data.get("expires_at"),
                oauth_scope=token_data.get("scope"),
                oauth_metadata=token_data.get("metadata"),
                updated_at=datetime.now(),
            )
        )

        result = await self._session.execute(stmt)
        await self._session.commit()

        if result.rowcount == 0:
            msg = f"配置 ID {config_id} 不存在"
            raise ValueError(msg)

        logger.info(f"配置 {config_id} 的 OAuth token 已更新")

    async def get_configs(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        provider: str | None = None,
    ) -> tuple[list[ModelConfigResponse], int]:
        """分页查询配置列表.

        Args:
            page: 页码（从 1 开始）
            page_size: 每页记录数
            is_active: 是否启用（可选过滤条件）
            provider: 提供商（可选过滤条件）

        Returns:
            (配置列表, 总记录数)
        """
        table = model_configs_table

        # 构建查询条件
        conditions = []
        if is_active is not None:
            conditions.append(table.c.is_active == is_active)
        if provider is not None:
            conditions.append(table.c.provider == provider)

        # 查询总数
        count_stmt = select(func.count()).select_from(table)
        if conditions:
            count_stmt = count_stmt.where(*conditions)

        total_result = await self._session.execute(count_stmt)
        total = total_result.scalar() or 0

        # 查询分页数据
        offset = (page - 1) * page_size
        select_stmt = (
            select(table)
            .where(*conditions)
            .order_by(table.c.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )

        result = await self._session.execute(select_stmt)
        rows = result.fetchall()

        # 转换为响应模型
        configs = []
        for row in rows:
            row_dict = dict(row._mapping)
            config_data = ModelConfigORM.dict_to_orm(row_dict)
            configs.append(ModelConfigResponse(**config_data))

        return configs, total

    async def update_config(
        self, config_id: int, config_update: ModelConfigUpdate
    ) -> ModelConfigResponse:
        """更新模型配置.

        Args:
            config_id: 配置 ID
            config_update: 更新请求模型

        Returns:
            更新后的配置

        Raises:
            ValueError: 如果配置不存在或名称冲突
        """
        table = model_configs_table

        # 构建更新数据
        update_data = {}
        if config_update.name is not None:
            update_data["name"] = config_update.name
        if config_update.provider is not None:
            update_data["provider"] = config_update.provider
        if config_update.base_url is not None:
            update_data["base_url"] = config_update.base_url
        if config_update.api_key is not None:
            update_data["api_key"] = config_update.api_key
        if config_update.models is not None:
            update_data["models"] = [m.model_dump() for m in config_update.models]
        if config_update.is_active is not None:
            update_data["is_active"] = config_update.is_active

        if not update_data:
            # 没有要更新的字段
            return await self._get_by_id_internal(config_id)

        update_data["updated_at"] = datetime.now()

        try:
            stmt = update(table).where(table.c.id == config_id).values(**update_data)

            # 将乐观锁检查移到 WHERE 条件中，使其成为原子操作
            if config_update.updated_at is not None:
                stmt = stmt.where(table.c.updated_at == config_update.updated_at)

            result = await self._session.execute(stmt)
            await self._session.commit()

            if result.rowcount == 0:
                # 需要区分是记录不存在还是乐观锁冲突
                if config_update.updated_at is not None:
                    # 先检查记录是否存在
                    exists = await self.get_config_by_id(config_id)
                    if exists is None:
                        msg = f"配置 ID {config_id} 不存在"
                        raise ValueError(msg)
                    # 记录存在但 updated_at 不匹配，说明已被其他用户修改
                    msg = "配置已被其他用户修改，请刷新。"
                    raise ValueError(msg)
                # 没有 updated_at 的情况，说明记录不存在
                msg = f"配置 ID {config_id} 不存在"
                raise ValueError(msg)

            return await self._get_by_id_internal(config_id)

        except IntegrityError as e:
            await self._session.rollback()
            logger.error(f"更新配置失败: {e}")
            if "name" in str(e):
                msg = "配置名称已存在"
                raise ValueError(msg) from e
            raise

    async def delete_config(self, config_id: int) -> bool:
        """删除模型配置.

        Args:
            config_id: 配置 ID

        Returns:
            是否删除成功

        Raises:
            ValueError: 如果配置不存在
        """
        table = model_configs_table

        stmt = delete(table).where(table.c.id == config_id)
        result = await self._session.execute(stmt)
        await self._session.commit()

        if result.rowcount == 0:
            msg = f"配置 ID {config_id} 不存在"
            raise ValueError(msg)

        return True

    async def cleanup_test_data(self, prefix: str = "test_e2e_") -> int:
        """清理所有指定前缀的测试数据.

        Args:
            prefix: 测试数据前缀（默认 "test_e2e_"）

        Returns:
            删除的记录数
        """
        table = model_configs_table

        # 使用 LIKE 查询匹配前缀
        stmt = delete(table).where(table.c.name.like(f"{prefix}%"))

        result = await self._session.execute(stmt)
        deleted_count = result.rowcount
        await self._session.commit()

        logger.info(f"已删除 {deleted_count} 条测试数据（前缀: {prefix}）")
        return deleted_count

    async def get_test_data_stats(self, prefix: str = "test_e2e_") -> dict:
        """获取测试数据统计信息.

        Args:
            prefix: 测试数据前缀（默认 "test_e2e_"）

        Returns:
            统计信息字典
        """
        table = model_configs_table

        # 查询测试数据总数
        count_stmt = select(func.count()).select_from(table).where(
            table.c.name.like(f"{prefix}%")
        )
        total_result = await self._session.execute(count_stmt)
        total_count = total_result.scalar() or 0

        # 查询最新和最老的测试数据
        time_stmt = (
            select(table.c.created_at)
            .where(table.c.name.like(f"{prefix}%"))
            .order_by(table.c.created_at.desc())
        )
        time_result = await self._session.execute(time_stmt)
        all_times = time_result.scalars().all()

        newest_at = all_times[0] if all_times else None
        oldest_at = all_times[-1] if all_times else None

        # 查询所有唯一前缀
        prefix_stmt = (
            select(func.substr(table.c.name, 1, len(prefix)))
            .where(table.c.name.like(f"{prefix}%"))
            .distinct()
        )
        prefix_result = await self._session.execute(prefix_stmt)
        prefixes = prefix_result.scalars().all()

        return {
            "test_data_count": total_count,
            "test_data_prefixes": list(prefixes),
            "oldest_test_data": oldest_at,
            "newest_test_data": newest_at,
        }

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
        table = model_configs_table

        stmt = (
            update(table)
            .where(table.c.id == config_id)
            .values(is_active=is_active, updated_at=datetime.now())
        )

        result = await self._session.execute(stmt)
        await self._session.commit()

        if result.rowcount == 0:
            msg = f"配置 ID {config_id} 不存在"
            raise ValueError(msg)

        return await self._get_by_id_internal(config_id)
