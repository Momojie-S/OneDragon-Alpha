# -*- coding: utf-8 -*-
"""Logging module."""

import logging


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Logger instance configured for the module.

    """
    logger = logging.getLogger(name)
    return logger
