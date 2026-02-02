# -*- coding: utf-8 -*-
"""Health check status module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class HealthStatus:
    """Database connection health status.

    Attributes:
        is_healthy: Whether the database connection is healthy.
        message: Status message describing the health check result.
        error: Error details if health check failed, None otherwise.
        pool_size: Current connection pool size.
        pool_overflow: Current overflow connection count.
        checked_out: Number of connections currently checked out.
    """

    is_healthy: bool
    message: str
    error: str | None = None
    pool_size: int = 0
    pool_overflow: int = 0
    checked_out: int = 0
