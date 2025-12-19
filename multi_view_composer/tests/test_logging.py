"""Tests for logging configuration."""

import pytest
import logging
import io

from multi_view_composer import setup_logging, get_logger


class TestSetupLogging:
    def test_returns_logger(self):
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "multi_view_composer"

    def test_sets_level(self):
        logger = setup_logging(level=logging.DEBUG)
        assert logger.level == logging.DEBUG

        logger = setup_logging(level=logging.WARNING)
        assert logger.level == logging.WARNING

    def test_custom_format(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = setup_logging(
            level=logging.INFO,
            format_string="TEST: %(message)s",
            handler=handler
        )
        logger.info("hello")
        output = stream.getvalue()
        assert "TEST: hello" in output

    def test_custom_handler(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        logger = setup_logging(level=logging.INFO, handler=handler)

        logger.info("test message")
        output = stream.getvalue()
        assert "test message" in output

    def test_clears_existing_handlers(self):
        # Add multiple handlers
        logger = setup_logging()
        setup_logging()
        setup_logging()

        # Should only have one handler
        assert len(logger.handlers) == 1


class TestGetLogger:
    def test_returns_package_logger(self):
        logger = get_logger()
        assert logger.name == "multi_view_composer"

    def test_returns_module_logger(self):
        logger = get_logger("generator")
        assert logger.name == "multi_view_composer.generator"

        logger = get_logger("config")
        assert logger.name == "multi_view_composer.config"

    def test_module_loggers_are_children(self):
        parent = get_logger()
        child = get_logger("template_engine")

        assert child.parent == parent
