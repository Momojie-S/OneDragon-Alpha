# -*- coding: utf-8 -*-
"""MySQL configuration module."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Self
from urllib.parse import quote_plus


@dataclass
class MySQLConfig:
    """MySQL database configuration.

    Attributes:
        host: Database host address.
        port: Database port number.
        user: Database username.
        password: Database password.
        database: Database name.
        pool_size: Connection pool size (number of persistent connections).
        max_overflow: Maximum overflow connections beyond pool_size.
        pool_recycle: Connection recycle time in seconds.
        echo: Whether to log SQL statements.
    """

    host: str
    port: int
    user: str
    password: str
    database: str
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 3600
    echo: bool = False

    @classmethod
    def from_env(cls) -> Self:
        """Create configuration from environment variables.

        Reads the following environment variables:
        - MYSQL_HOST: Database host (default: localhost)
        - MYSQL_PORT: Database port (default: 3306)
        - MYSQL_USER: Database username (required)
        - MYSQL_PASSWORD: Database password (required)
        - MYSQL_DATABASE: Database name (required)
        - MYSQL_POOL_SIZE: Connection pool size (default: 5)
        - MYSQL_MAX_OVERFLOW: Max overflow connections (default: 10)
        - MYSQL_POOL_RECYCLE: Recycle time in seconds (default: 3600)
        - MYSQL_ECHO: Enable SQL logging (default: false)

        Returns:
            MySQLConfig: Configuration object with values from environment.

        Raises:
            ValueError: If required environment variables are missing or invalid.
        """
        try:
            host = os.getenv("MYSQL_HOST", "localhost")
            port = int(os.getenv("MYSQL_PORT", "3306"))
            user = os.getenv("MYSQL_USER")
            password = os.getenv("MYSQL_PASSWORD")
            database = os.getenv("MYSQL_DATABASE")
            pool_size = int(os.getenv("MYSQL_POOL_SIZE", "5"))
            max_overflow = int(os.getenv("MYSQL_MAX_OVERFLOW", "10"))
            pool_recycle = int(os.getenv("MYSQL_POOL_RECYCLE", "3600"))
            echo = os.getenv("MYSQL_ECHO", "false").lower() == "true"
        except ValueError as e:
            msg = f"Invalid numeric value in environment variable: {e}"
            raise ValueError(msg) from e

        if not user:
            msg = "MYSQL_USER environment variable is required"
            raise ValueError(msg)
        if not password:
            msg = "MYSQL_PASSWORD environment variable is required"
            raise ValueError(msg)
        if not database:
            msg = "MYSQL_DATABASE environment variable is required"
            raise ValueError(msg)

        config = cls(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            echo=echo,
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Validate configuration parameters.

        Raises:
            ValueError: If any configuration parameter is invalid.
        """
        if not self.host:
            msg = "Database host cannot be empty"
            raise ValueError(msg)
        if self.port < 1 or self.port > 65535:
            msg = f"Invalid port number: {self.port}"
            raise ValueError(msg)
        if not self.user:
            msg = "Database user cannot be empty"
            raise ValueError(msg)
        if not self.password:
            msg = "Database password cannot be empty"
            raise ValueError(msg)
        if not self.database:
            msg = "Database name cannot be empty"
            raise ValueError(msg)
        if self.pool_size < 1:
            msg = f"Invalid pool_size: {self.pool_size}"
            raise ValueError(msg)
        if self.max_overflow < 0:
            msg = f"Invalid max_overflow: {self.max_overflow}"
            raise ValueError(msg)
        if self.pool_recycle < 0:
            msg = f"Invalid pool_recycle: {self.pool_recycle}"
            raise ValueError(msg)

    def to_connection_url(self) -> str:
        """Convert configuration to SQLAlchemy connection URL.

        Returns:
            str: MySQL connection URL for SQLAlchemy.
        """
        # URL-encode password to handle special characters like @, :, /
        encoded_password = quote_plus(self.password)
        # Use aiomysql driver for async support
        return (
            f"mysql+aiomysql://{self.user}:{encoded_password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
