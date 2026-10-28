import logging
import os

from app.core.config import settings
from app.core.error_logging import setup_logger as setup_error_logger


def is_lambda_environment() -> bool:
    """Check if running in AWS Lambda environment."""
    return os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None


def setup_logging() -> None:
    """Setup application logging configuration using the existing error logging system."""

    # Use the existing error logging system which already handles Lambda environments
    error_logger = setup_error_logger()

    # Setup root logger to use the same configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Add the same handler that the error logger uses
    for handler in error_logger.handlers:
        root_logger.addHandler(handler)

    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.INFO)
    logging.getLogger("langgraph").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
