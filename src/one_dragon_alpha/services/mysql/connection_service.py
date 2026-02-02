# -*- coding: utf-8 -*-
"""MySQL connection service module."""

from __future__ import annotations

import asyncio
from typing import Self

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import SQLAlchemyError

from one_dragon_alpha.core.system.log import get_logger
from one_dragon_alpha.services.mysql.config import MySQLConfig
from one_dragon_alpha.services.mysql.health import HealthStatus

logger = get_logger(__name__)


class MySQLConnectionService:
    """MySQL connection service management class.

    This class encapsulates SQLAlchemy async engine and session management,
    providing a unified database connection interface.

    Attributes:
        _engine: SQLAlchemy async engine instance.
        _config: Database connection configuration.
        _is_closed: Whether the service has been closed.
        _session_factory: Async session factory for creating sessions.
        _lock: Async lock for thread-safe close operation.
    """

    def __init__(self, config: MySQLConfig | None = None) -> None:
        """Initialize MySQL connection service.

        Args:
            config: Database configuration, if None will load from environment variables.

        Raises:
            ValueError: If configuration is invalid.
            SQLAlchemyError: If connection fails.
        """
        if config is None:
            config = MySQLConfig.from_env()

        config.validate()
        self._config = config
        self._is_closed = False
        self._lock = asyncio.Lock()

        try:
            self._engine = self._create_engine()
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )
            logger.info(
                f"MySQL connection service initialized: "
                f"{config.host}:{config.port}/{config.database}"
            )
        except SQLAlchemyError:
            logger.exception("Failed to initialize MySQL connection service")
            raise

    def _create_engine(self) -> AsyncEngine:
        """Create SQLAlchemy async engine with configuration.

        Returns:
            AsyncEngine: Configured async engine instance.
        """
        connection_url = self._config.to_connection_url()

        return create_async_engine(
            connection_url,
            pool_size=self._config.pool_size,
            max_overflow=self._config.max_overflow,
            pool_recycle=self._config.pool_recycle,
            pool_pre_ping=True,  # Verify connections before using
            echo=self._config.echo,
        )

    async def get_session(self) -> AsyncSession:
        """Get database session.

        Returns:
            AsyncSession: SQLAlchemy async session object.

        Raises:
            RuntimeError: If service has been closed.
        """
        if self._is_closed:
            msg = "Cannot get session: service has been closed"
            raise RuntimeError(msg)

        return self._session_factory()

    def get_engine(self) -> AsyncEngine:
        """Get underlying engine.

        Returns:
            AsyncEngine: SQLAlchemy async engine object.

        Raises:
            RuntimeError: If service has been closed.
        """
        if self._is_closed:
            msg = "Cannot get engine: service has been closed"
            raise RuntimeError(msg)

        return self._engine

    async def close(self) -> None:
        """Close all connections and release resources.

        This method is idempotent, multiple calls will not produce errors.
        """
        async with self._lock:
            if self._is_closed:
                return

            try:
                self._is_closed = True
                await self._engine.dispose()
                logger.info("MySQL connection service closed")
            except SQLAlchemyError:
                self._is_closed = False
                logger.exception("Error closing MySQL connection service")
                raise

    async def health_check(self) -> HealthStatus:
        """Check database connection health status.

        Returns:
            HealthStatus: Health status object with connection details.
        """
        try:
            if self._is_closed:
                return HealthStatus(
                    is_healthy=False,
                    message="Service has been closed",
                    error="Service closed",
                )

            conn = await self._engine.connect()
            try:
                await conn.execute(text("SELECT 1"))
            finally:
                await conn.close()

            pool = self._engine.pool
            return HealthStatus(
                is_healthy=True,
                message="Database connection is healthy",
                pool_size=pool.size(),
                pool_overflow=pool.overflow(),
                checked_out=pool.checkedout(),
            )
        except SQLAlchemyError:
            logger.exception("Health check failed")
            return HealthStatus(
                is_healthy=False,
                message="Database connection is unhealthy",
                error="Database connection failed",
            )

    async def __aenter__(self) -> Self:
        """Async context manager entry.

        Returns:
            Self: The service instance.
        """
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit.

        Args:
            *args: Exception info if any.
        """
        await self.close()
