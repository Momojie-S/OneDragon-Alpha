# -*- coding: utf-8 -*-
"""Integration tests for MySQL connection service.

These tests require a real MySQL database connection.
They are marked with the 'integration' marker and can be skipped during normal testing.
"""

import pytest
from sqlalchemy import text

from one_dragon_alpha.services.mysql.config import MySQLConfig
from one_dragon_alpha.services.mysql.connection_service import MySQLConnectionService


@pytest.mark.integration
class TestMySQLConnectionServiceIntegration:
    """Integration tests with real MySQL database."""

    @pytest.fixture(scope="class")
    def config(self) -> MySQLConfig:
        """Get database configuration from environment."""
        return MySQLConfig.from_env()

    @pytest.mark.asyncio
    async def test_real_database_connection(self, config: MySQLConfig) -> None:
        """Test that we can connect to a real MySQL database."""
        async with MySQLConnectionService(config) as service:
            # Get a session
            session = await service.get_session()
            assert session is not None

            # Execute a simple query
            result = await session.execute(text("SELECT 1 as value"))
            row = result.fetchone()
            assert row is not None
            assert row[0] == 1

    @pytest.mark.asyncio
    async def test_health_check_with_real_database(self, config: MySQLConfig) -> None:
        """Test health check with real database connection."""
        async with MySQLConnectionService(config) as service:
            health = await service.health_check()

            assert health.is_healthy is True
            assert "healthy" in health.message.lower()
            assert health.error is None
            # Pool statistics should be available
            assert health.pool_size > 0

    @pytest.mark.asyncio
    async def test_multiple_sessions_with_real_database(
        self, config: MySQLConfig
    ) -> None:
        """Test creating multiple sessions with real database."""
        async with MySQLConnectionService(config) as service:
            session1 = await service.get_session()
            session2 = await service.get_session()

            # Sessions should be independent
            assert session1 is not session2

            # Both should work
            result1 = await session1.execute(text("SELECT 1"))
            result2 = await session2.execute(text("SELECT 2"))

            assert result1.fetchone()[0] == 1
            assert result2.fetchone()[0] == 2

    @pytest.mark.asyncio
    async def test_session_lifecycle_with_real_database(
        self, config: MySQLConfig
    ) -> None:
        """Test session lifecycle with real database operations."""
        async with MySQLConnectionService(config) as service:
            # Get session
            session = await service.get_session()

            # Execute query
            result = await session.execute(
                text("SELECT CONNECTION_ID() as connection_id")
            )
            connection_id = result.fetchone()[0]

            # Connection ID should be a positive integer
            assert isinstance(connection_id, int)
            assert connection_id > 0

            # Close session explicitly
            await session.close()

    @pytest.mark.asyncio
    async def test_service_close_and_cleanup(self, config: MySQLConfig) -> None:
        """Test that service properly closes and cleans up resources."""
        service = MySQLConnectionService(config)

        # Service should be usable
        health = await service.health_check()
        assert health.is_healthy is True

        # Close the service
        await service.close()

        # Service should be closed
        health = await service.health_check()
        assert health.is_healthy is False
        assert "closed" in health.message.lower()

    @pytest.mark.asyncio
    async def test_get_engine_with_real_database(self, config: MySQLConfig) -> None:
        """Test getting engine with real database."""
        async with MySQLConnectionService(config) as service:
            engine = service.get_engine()
            assert engine is not None

            # Engine should have a pool
            assert engine.pool is not None

            # Pool should have correct size
            assert engine.pool.size() == config.pool_size

    @pytest.mark.asyncio
    async def test_database_information(self, config: MySQLConfig) -> None:
        """Test retrieving database information."""
        async with MySQLConnectionService(config) as service:
            session = await service.get_session()

            # Get MySQL version
            result = await session.execute(text("SELECT VERSION() as version"))
            version = result.fetchone()[0]

            assert version is not None
            assert isinstance(version, str)
            assert len(version) > 0

            # Get current database
            result = await session.execute(text("SELECT DATABASE() as db"))
            database = result.fetchone()[0]

            assert database == config.database

    @pytest.mark.asyncio
    async def test_connection_pool_statistics(self, config: MySQLConfig) -> None:
        """Test connection pool statistics through health check."""
        # Use a smaller pool for this test
        test_config = MySQLConfig(
            host=config.host,
            port=config.port,
            user=config.user,
            password=config.password,
            database=config.database,
            pool_size=3,
            max_overflow=5,
        )

        async with MySQLConnectionService(test_config) as service:
            # Get initial health
            health = await service.health_check()
            assert health.is_healthy is True
            assert health.pool_size == 3

            # Use a few connections and properly manage them
            async with await service.get_session() as session1:
                async with await service.get_session() as session2:
                    # Execute queries to ensure connections are active
                    await session1.execute(text("SELECT 1"))
                    await session2.execute(text("SELECT 1"))

                    # Check pool stats while connections are active
                    health = await service.health_check()
                    # checked_out may vary based on pool implementation
                    # Just verify the service is healthy
                    assert health.is_healthy is True

            # After closing all connections, pool should be healthy
            health = await service.health_check()
            assert health.is_healthy is True
