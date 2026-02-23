"""Logging configuration for multi-view composer."""

import logging
import sys
from typing import Optional

# Package logger
_PACKAGE_NAME = "multi_view_composer"


def setup_logging(
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    handler: Optional[logging.Handler] = None,
) -> logging.Logger:
    """
    Configure logging for the multi_view_composer package.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        format_string: Custom format string. If None, uses default format.
        handler: Custom handler. If None, uses StreamHandler to stderr.

    Returns:
        The configured package logger.

    Example:
        from multi_view_composer import setup_logging
        import logging

        # Basic setup
        setup_logging(level=logging.DEBUG)

        # Custom format
        setup_logging(
            level=logging.INFO,
            format_string="%(asctime)s - %(name)s - %(message)s"
        )

        # File logging
        file_handler = logging.FileHandler("composer.log")
        setup_logging(level=logging.DEBUG, handler=file_handler)
    """
    logger = logging.getLogger(_PACKAGE_NAME)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create handler
    if handler is None:
        handler = logging.StreamHandler(sys.stderr)

    handler.setLevel(level)

    # Create formatter
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger for a module within the package.

    Args:
        name: Module name (e.g., "generator", "template_engine").
              If None, returns the package root logger.

    Returns:
        Logger instance.

    Example:
        from multi_view_composer.logging_config import get_logger

        logger = get_logger("generator")
        logger.info("Processing camera image")
    """
    if name is None:
        return logging.getLogger(_PACKAGE_NAME)
    return logging.getLogger(f"{_PACKAGE_NAME}.{name}")
