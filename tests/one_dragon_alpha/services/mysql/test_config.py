# -*- coding: utf-8 -*-
"""Tests for MySQLConfig class."""

import pytest

from one_dragon_alpha.services.mysql.config import MySQLConfig


class TestMySQLConfig:
    """Test cases for MySQLConfig class."""

    def test_create_config_with_valid_parameters(self) -> None:
        """Test creating a config object with valid parameters."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        assert config.host == "localhost"
        assert config.port == 3306
        assert config.user == "test_user"
        assert config.password == "test_password"
        assert config.database == "test_db"
        assert config.pool_size == 5  # default value
        assert config.max_overflow == 10  # default value
        assert config.pool_recycle == 3600  # default value
        assert config.echo is False  # default value

    def test_create_config_with_custom_pool_settings(self) -> None:
        """Test creating a config object with custom pool settings."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
            echo=True,
        )

        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_recycle == 1800
        assert config.echo is True

    def test_to_connection_url(self) -> None:
        """Test converting config to connection URL."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        url = config.to_connection_url()
        # Should use aiomysql for async support
        assert "mysql+aiomysql://test_user:test_password@localhost:3306/test_db" == url

    def test_validate_with_valid_config(self) -> None:
        """Test validation with valid configuration."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        # Should not raise any exception
        config.validate()

    def test_validate_with_empty_host(self) -> None:
        """Test validation with empty host."""
        config = MySQLConfig(
            host="",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with pytest.raises(ValueError, match="Database host cannot be empty"):
            config.validate()

    def test_validate_with_invalid_port(self) -> None:
        """Test validation with invalid port number."""
        config = MySQLConfig(
            host="localhost",
            port=0,
            user="test_user",
            password="test_password",
            database="test_db",
        )

        with pytest.raises(ValueError, match="Invalid port number"):
            config.validate()

    def test_validate_with_empty_user(self) -> None:
        """Test validation with empty user."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="",
            password="test_password",
            database="test_db",
        )

        with pytest.raises(ValueError, match="Database user cannot be empty"):
            config.validate()

    def test_validate_with_empty_password(self) -> None:
        """Test validation with empty password."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="",
            database="test_db",
        )

        with pytest.raises(ValueError, match="Database password cannot be empty"):
            config.validate()

    def test_validate_with_empty_database(self) -> None:
        """Test validation with empty database name."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="",
        )

        with pytest.raises(ValueError, match="Database name cannot be empty"):
            config.validate()

    def test_validate_with_invalid_pool_size(self) -> None:
        """Test validation with invalid pool size."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
            pool_size=0,
        )

        with pytest.raises(ValueError, match="Invalid pool_size"):
            config.validate()

    def test_validate_with_negative_max_overflow(self) -> None:
        """Test validation with negative max_overflow."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
            max_overflow=-1,
        )

        with pytest.raises(ValueError, match="Invalid max_overflow"):
            config.validate()

    def test_validate_with_negative_pool_recycle(self) -> None:
        """Test validation with negative pool_recycle."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="test_password",
            database="test_db",
            pool_recycle=-1,
        )

        with pytest.raises(ValueError, match="Invalid pool_recycle"):
            config.validate()


class TestMySQLConfigFromEnv:
    """Test cases for MySQLConfig.from_env class method."""

    def test_from_env_with_all_variables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading config from environment variables with all variables set."""

        env_vars = {
            "MYSQL_HOST": "testhost",
            "MYSQL_PORT": "3307",
            "MYSQL_USER": "env_user",
            "MYSQL_PASSWORD": "env_password",
            "MYSQL_DATABASE": "env_db",
            "MYSQL_POOL_SIZE": "8",
            "MYSQL_MAX_OVERFLOW": "15",
            "MYSQL_POOL_RECYCLE": "7200",
            "MYSQL_ECHO": "true",
        }

        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        config = MySQLConfig.from_env()

        assert config.host == "testhost"
        assert config.port == 3307
        assert config.user == "env_user"
        assert config.password == "env_password"
        assert config.database == "env_db"
        assert config.pool_size == 8
        assert config.max_overflow == 15
        assert config.pool_recycle == 7200
        assert config.echo is True

    def test_from_env_with_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading config with default values for optional variables."""
        # Clear environment variables first to avoid reading from .env
        monkeypatch.delenv("MYSQL_HOST", raising=False)
        monkeypatch.delenv("MYSQL_PORT", raising=False)
        monkeypatch.delenv("MYSQL_POOL_SIZE", raising=False)
        monkeypatch.delenv("MYSQL_MAX_OVERFLOW", raising=False)
        monkeypatch.delenv("MYSQL_POOL_RECYCLE", raising=False)
        monkeypatch.delenv("MYSQL_ECHO", raising=False)

        monkeypatch.setenv("MYSQL_USER", "default_user")
        monkeypatch.setenv("MYSQL_PASSWORD", "default_password")
        monkeypatch.setenv("MYSQL_DATABASE", "default_db")

        config = MySQLConfig.from_env()

        assert config.host == "localhost"  # default
        assert config.port == 3306  # default
        assert config.pool_size == 5  # default
        assert config.max_overflow == 10  # default
        assert config.pool_recycle == 3600  # default
        assert config.echo is False  # default

    def test_from_env_missing_user(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test from_env when MYSQL_USER is missing."""
        monkeypatch.delenv("MYSQL_USER", raising=False)

        with pytest.raises(
            ValueError, match="MYSQL_USER environment variable is required"
        ):
            MySQLConfig.from_env()

    def test_from_env_missing_password(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test from_env when MYSQL_PASSWORD is missing."""
        monkeypatch.setenv("MYSQL_USER", "test_user")
        monkeypatch.delenv("MYSQL_PASSWORD", raising=False)

        with pytest.raises(
            ValueError, match="MYSQL_PASSWORD environment variable is required"
        ):
            MySQLConfig.from_env()

    def test_from_env_missing_database(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test from_env when MYSQL_DATABASE is missing."""
        monkeypatch.setenv("MYSQL_USER", "test_user")
        monkeypatch.setenv("MYSQL_PASSWORD", "test_password")
        monkeypatch.delenv("MYSQL_DATABASE", raising=False)

        with pytest.raises(
            ValueError, match="MYSQL_DATABASE environment variable is required"
        ):
            MySQLConfig.from_env()

    def test_from_env_with_echo_false_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test from_env with MYSQL_ECHO set to 'false' string."""
        monkeypatch.setenv("MYSQL_USER", "test_user")
        monkeypatch.setenv("MYSQL_PASSWORD", "test_password")
        monkeypatch.setenv("MYSQL_DATABASE", "test_db")
        monkeypatch.setenv("MYSQL_ECHO", "false")

        config = MySQLConfig.from_env()
        assert config.echo is False

    def test_from_env_with_echo_true_string(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test from_env with MYSQL_ECHO set to 'true' string."""
        monkeypatch.setenv("MYSQL_USER", "test_user")
        monkeypatch.setenv("MYSQL_PASSWORD", "test_password")
        monkeypatch.setenv("MYSQL_DATABASE", "test_db")
        monkeypatch.setenv("MYSQL_ECHO", "true")

        config = MySQLConfig.from_env()
        assert config.echo is True

    def test_from_env_with_invalid_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test from_env with invalid port value in environment."""
        monkeypatch.setenv("MYSQL_USER", "test_user")
        monkeypatch.setenv("MYSQL_PASSWORD", "test_password")
        monkeypatch.setenv("MYSQL_DATABASE", "test_db")
        monkeypatch.setenv("MYSQL_PORT", "invalid")

        with pytest.raises(ValueError, match="Invalid numeric value"):
            MySQLConfig.from_env()

    def test_from_env_with_invalid_pool_size(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test from_env with invalid pool_size value in environment."""
        monkeypatch.setenv("MYSQL_USER", "test_user")
        monkeypatch.setenv("MYSQL_PASSWORD", "test_password")
        monkeypatch.setenv("MYSQL_DATABASE", "test_db")
        monkeypatch.setenv("MYSQL_POOL_SIZE", "abc")

        with pytest.raises(ValueError, match="Invalid numeric value"):
            MySQLConfig.from_env()

    def test_to_connection_url_with_special_characters(self) -> None:
        """Test URL encoding for password with special characters."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="test_user",
            password="p@ss:w/ord#123",  # Special characters: @, :, /, #
            database="test_db",
        )

        url = config.to_connection_url()
        # Password should be URL-encoded
        assert "p%40ss%3Aw%2Ford%23123" in url
        assert "mysql+aiomysql://test_user:" in url
        assert "@localhost:3306/test_db" in url

    def test_to_connection_url_with_at_sign_in_password(self) -> None:
        """Test URL encoding when password contains @ sign."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="user",
            password="pass@word",  # Contains @ which conflicts with URL format
            database="db",
        )

        url = config.to_connection_url()
        # @ should be encoded as %40
        assert "pass%40word" in url
        # URL should be parseable correctly
        assert url.count("@") == 1  # Only one @ (the separator after password)

    def test_to_connection_url_with_colon_in_password(self) -> None:
        """Test URL encoding when password contains : sign."""
        config = MySQLConfig(
            host="localhost",
            port=3306,
            user="user",
            password="pass:word",  # Contains :
            database="db",
        )

        url = config.to_connection_url()
        # : should be encoded as %3A
        assert "pass%3Aword" in url
