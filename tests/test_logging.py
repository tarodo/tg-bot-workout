from unittest.mock import patch

from src.bot.logging import get_logger, setup_logging


def test_setup_logging():
    """Test logging setup."""
    with patch("structlog.configure") as mock_configure:
        setup_logging()
        mock_configure.assert_called_once()


def test_get_logger():
    """Test logger creation."""
    with patch("structlog.get_logger") as mock_get_logger:
        logger = get_logger("test")
        mock_get_logger.assert_called_once_with("test")
        assert logger == mock_get_logger.return_value
