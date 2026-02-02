# -*- coding: utf-8 -*-
"""Tests for MySQLConnectionService class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from one_dragon_alpha.services.mysql.config import MySQLConfig
from one_dragon_alpha.services.mysql.connection_service import MySQLConnectionService


class TestMySQLConnectionServiceInit:
    """Test cases for MySQLConnectionService initialization."""

    @pytest.mark.asyncio
    async def test_init_with_valid_config(self) -> None:
        """Test initialization with valid configuration."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
            echo=False,
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            assert service._config == config
            assert service._is_closed is False

    @pytest.mark.asyncio
    async def test_init_without_config_uses_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test initialization without config uses environment variables."""
        monkeypatch.setenv("MYSQL_USER", "env_user")
        monkeypatch.setenv("MYSQL_PASSWORD", "env_password")
        monkeypatch.setenv("MYSQL_DATABASE", "env_db")

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService()
            assert service._config.user == "env_user"
            assert service._config.database == "env_db"

    @pytest.mark.asyncio
    async def test_init_with_invalid_config_raises_error(self) -> None:
        """Test initialization with invalid config raises ValueError."""
        config = MySQLConfig(
            host="",  # Invalid: empty host
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with pytest.raises(ValueError, match="Database host cannot be empty"):
            MySQLConnectionService(config)

    @pytest.mark.asyncio
    async def test_init_creates_engine_with_correct_parameters(self) -> None:
        """Test that initialization creates engine with correct parameters."""
        config = MySQLConfig(
            host="testhost",
            port=3307,
            user="test_user",
            password="test_password",
            database="test_db",
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ) as mock_engine:
            MySQLConnectionService(config)

            # Verify create_async_engine was called with correct parameters
            call_args = mock_engine.call_args
            assert call_args is not None
            engine_url = call_args[0][0]
            assert "testhost" in engine_url
            assert "test_user" in engine_url
            assert "test_db" in engine_url

            kwargs = call_args[1]
            assert kwargs["pool_size"] == 10
            assert kwargs["max_overflow"] == 20
            assert kwargs["pool_recycle"] == 1800
            assert kwargs["pool_pre_ping"] is True


class TestGetSession:
    """Test cases for get_session method."""

    @pytest.mark.asyncio
    async def test_get_session_returns_async_session(self) -> None:
        """Test that get_session returns an AsyncSession object."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            session = await service.get_session()
            assert session is not None
            # Verify it's an AsyncSession by checking it has async methods
            assert hasattr(session, "execute")

    @pytest.mark.asyncio
    async def test_get_multiple_sessions_are_independent(self) -> None:
        """Test that multiple calls to get_session return independent sessions."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            session1 = await service.get_session()
            session2 = await service.get_session()

            # Sessions should be different objects
            assert session1 is not session2

    @pytest.mark.asyncio
    async def test_get_session_after_close_raises_error(self) -> None:
        """Test that get_session raises RuntimeError after service is closed."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            # Mock the engine's dispose method
            service._engine.dispose = AsyncMock()

            await service.close()

            with pytest.raises(
                RuntimeError, match="Cannot get session: service has been closed"
            ):
                await service.get_session()


class TestGetEngine:
    """Test cases for get_engine method."""

    @pytest.mark.asyncio
    async def test_get_engine_returns_engine(self) -> None:
        """Test that get_engine returns the underlying engine."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ) as mock_create:
            mock_engine = MagicMock()
            mock_create.return_value = mock_engine

            service = MySQLConnectionService(config)
            engine = service.get_engine()

            assert engine == mock_engine

    @pytest.mark.asyncio
    async def test_get_engine_returns_same_instance(self) -> None:
        """Test that multiple calls to get_engine return the same engine instance."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            engine1 = service.get_engine()
            engine2 = service.get_engine()

            assert engine1 is engine2

    @pytest.mark.asyncio
    async def test_get_engine_after_close_raises_error(self) -> None:
        """Test that get_engine raises RuntimeError after service is closed."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            service._engine.dispose = AsyncMock()

            await service.close()

            with pytest.raises(
                RuntimeError, match="Cannot get engine: service has been closed"
            ):
                service.get_engine()


class TestClose:
    """Test cases for close method."""

    @pytest.mark.asyncio
    async def test_close_disposes_engine(self) -> None:
        """Test that close disposes the engine."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            service._engine.dispose = AsyncMock()

            await service.close()

            service._engine.dispose.assert_called_once()
            assert service._is_closed is True

    @pytest.mark.asyncio
    async def test_close_is_idempotent(self) -> None:
        """Test that multiple calls to close don't raise errors."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            service._engine.dispose = AsyncMock()

            await service.close()
            await service.close()  # Should not raise
            await service.close()  # Should not raise

            # Dispose should only be called once due to lock
            assert service._engine.dispose.call_count == 1


class TestAsyncContextManager:
    """Test cases for async context manager protocol."""

    @pytest.mark.asyncio
    async def test_async_context_manager_enters_and_exits(self) -> None:
        """Test that async context manager properly enters and exits."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            service._is_closed = False
            service._engine.dispose = AsyncMock()

            async with service:
                assert service._is_closed is False
                session = await service.get_session()
                assert session is not None

            # After exiting context, service should be closed
            assert service._is_closed is True

    @pytest.mark.asyncio
    async def test_async_context_manager_calls_close_on_exit(self) -> None:
        """Test that exiting context calls close method."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            service._engine.dispose = AsyncMock()

            async with service:
                pass

            service._engine.dispose.assert_called_once()


class TestHealthCheck:
    """Test cases for health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_when_connected(self) -> None:
        """Test health_check returns healthy status when database is reachable."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)

            # Mock the engine's connect method and pool
            mock_connection = AsyncMock()
            mock_connection.execute = AsyncMock()
            mock_connection.close = AsyncMock()

            async def mock_connect():
                return mock_connection

            mock_pool = MagicMock()
            mock_pool.size = MagicMock(return_value=5)
            mock_pool.overflow = MagicMock(return_value=0)
            mock_pool.checkedout = MagicMock(return_value=1)

            service._engine.connect = mock_connect
            service._engine.pool = mock_pool

            status = await service.health_check()

            assert status.is_healthy is True
            assert "healthy" in status.message.lower()
            assert status.pool_size == 5

    @pytest.mark.asyncio
    async def test_health_check_returns_unhealthy_when_closed(self) -> None:
        """Test health_check returns unhealthy status when service is closed."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            service._engine.dispose = AsyncMock()
            await service.close()

            status = await service.health_check()

            assert status.is_healthy is False
            assert "closed" in status.message.lower()

    @pytest.mark.asyncio
    async def test_health_check_returns_unhealthy_on_error(self) -> None:
        """Test health_check returns unhealthy status when database is unreachable."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)

            # Mock engine.connect to raise SQLAlchemyError
            async def mock_connect_error():
                raise SQLAlchemyError("Connection failed")

            service._engine.connect = mock_connect_error

            status = await service.health_check()

            assert status.is_healthy is False
            assert "unhealthy" in status.message.lower()
            assert status.error is not None


class TestConcurrency:
    """Test cases for concurrent access and thread safety."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_concurrent_get_session(self) -> None:
        """Test that multiple coroutines can get sessions concurrently."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)

            async def get_session():
                return await service.get_session()

            # Create multiple concurrent tasks
            tasks = [get_session() for _ in range(10)]
            sessions = await __import__("asyncio").gather(*tasks)

            # All sessions should be valid
            assert len(sessions) == 10
            # Sessions should be independent
            assert len(set(id(s) for s in sessions)) == 10

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_concurrent_close_is_thread_safe(self) -> None:
        """Test that concurrent close calls are thread-safe."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with patch(
            "one_dragon_alpha.services.mysql.connection_service.create_async_engine"
        ):
            service = MySQLConnectionService(config)
            service._engine.dispose = AsyncMock()

            async def close_service():
                await service.close()

            # Create multiple concurrent close tasks
            tasks = [close_service() for _ in range(5)]
            await __import__("asyncio").gather(*tasks)

            # Dispose should only be called once due to lock
            assert service._engine.dispose.call_count == 1
            assert service._is_closed is True
