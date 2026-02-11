# -*- coding: utf-8 -*-
"""MySQL Token 持久化模块.

本模块提供 Qwen OAuth token 的 MySQL 持久化功能，
将 token 存储到 model_configs 表的 OAuth 字段中。
"""

from datetime import datetime

from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from one_dragon_agent.core.model.repository import model_configs_table
from one_dragon_agent.core.model.qwen.oauth import QwenOAuthToken
from one_dragon_agent.core.system.log import get_logger

logger = get_logger(__name__)


class MySQLTokenPersistence:
    """MySQL Token 持久化类.

    将 OAuth token 存储到 model_configs 表中，与配置关联。
    每个配置可以拥有独立的 OAuth token。

    Attributes:
        _session: SQLAlchemy 异步会话

    Examples:
        >>> async with get_session() as session:
        ...     persistence = MySQLTokenPersistence(session)
        ...     await persistence.save_token(123, token)
    """

    def __init__(self, session: AsyncSession) -> None:
        """初始化 MySQL Token 持久化.

        Args:
            session: SQLAlchemy 异步会话

        """
        self._session = session

    async def save_token(
        self,
        config_id: int,
        token: QwenOAuthToken,
    ) -> None:
        """保存 OAuth token 到数据库.

        将 token 信息存储到指定配置的 OAuth 字段中。
        如果该配置已有 token，则覆盖。

        Args:
            config_id: 模型配置 ID
            token: 要保存的 QwenOAuthToken

        Raises:
            ValueError: 如果配置不存在

        """
        table = model_configs_table

        # 构建 token 数据
        token_data = {
            "oauth_access_token": token.access_token,
            "oauth_token_type": "Bearer",
            "oauth_refresh_token": token.refresh_token,
            "oauth_expires_at": token.expires_at,
            "oauth_scope": "openid profile email model.completion",
            "oauth_metadata": None,
        }

        # 如果有 resource_url，存入 metadata
        if token.resource_url:
            import json

            token_data["oauth_metadata"] = json.dumps(
                {"resource_url": token.resource_url}
            )

        stmt = (
            update(table)
            .where(table.c.id == config_id)
            .values(**token_data)
        )

        result = await self._session.execute(stmt)
        await self._session.commit()

        if result.rowcount == 0:
            msg = f"配置 ID {config_id} 不存在"
            raise ValueError(msg)

        logger.info(
            f"Token 已保存到配置 {config_id}，"
            f"过期时间: {datetime.fromtimestamp(token.expires_at / 1000)}"
        )

    async def load_token(self, config_id: int) -> QwenOAuthToken | None:
        """从数据库加载 OAuth token.

        Args:
            config_id: 模型配置 ID

        Returns:
            QwenOAuthToken 如果存在且有效，否则返回 None

        """
        table = model_configs_table

        stmt = table.select().where(table.c.id == config_id)
        result = await self._session.execute(stmt)
        row = result.fetchone()

        if not row:
            logger.warning(f"配置 ID {config_id} 不存在")
            return None

        # 检查是否有 OAuth token
        if not row.oauth_access_token or not row.oauth_refresh_token:
            logger.info(f"配置 {config_id} 没有 OAuth token")
            return None

        # 解析 metadata（如果存在）
        import json

        resource_url = None
        if row.oauth_metadata:
            try:
                metadata = (
                    json.loads(row.oauth_metadata)
                    if isinstance(row.oauth_metadata, str)
                    else row.oauth_metadata
                )
                resource_url = metadata.get("resource_url")
            except (json.JSONDecodeError, TypeError):
                pass

        token = QwenOAuthToken(
            access_token=row.oauth_access_token,
            refresh_token=row.oauth_refresh_token,
            expires_at=row.oauth_expires_at,
            resource_url=resource_url,
        )

        logger.info(f"从配置 {config_id} 加载 Token")
        return token

    async def delete_token(self, config_id: int) -> bool:
        """删除配置的 OAuth token.

        将 OAuth 相关字段设置为 NULL。

        Args:
            config_id: 模型配置 ID

        Returns:
            是否删除成功

        """
        table = model_configs_table

        stmt = (
            update(table)
            .where(table.c.id == config_id)
            .values(
                oauth_access_token=None,
                oauth_token_type=None,
                oauth_refresh_token=None,
                oauth_expires_at=None,
                oauth_scope=None,
                oauth_metadata=None,
            )
        )

        result = await self._session.execute(stmt)
        await self._session.commit()

        if result.rowcount == 0:
            logger.warning(f"配置 ID {config_id} 不存在")
            return False

        logger.info(f"配置 {config_id} 的 OAuth token 已清除")
        return True

    async def update_token(
        self,
        config_id: int,
        token: QwenOAuthToken,
    ) -> None:
        """更新 OAuth token（refresh 后使用）.

        Args:
            config_id: 模型配置 ID
            token: 新的 QwenOAuthToken

        Raises:
            ValueError: 如果配置不存在

        """
        await self.save_token(config_id, token)

    async def has_token(self, config_id: int) -> bool:
        """检查配置是否有有效的 OAuth token.

        Args:
            config_id: 模型配置 ID

        Returns:
            是否有 token

        """
        table = model_configs_table

        stmt = table.select().where(table.c.id == config_id)
        result = await self._session.execute(stmt)
        row = result.fetchone()

        if not row:
            return False

        return bool(row.oauth_access_token and row.oauth_refresh_token)
