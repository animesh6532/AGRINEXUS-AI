"""
Logging configuration for the AgriNexus-AI backend.
"""

import logging
import sys
from typing import Optional

from .config import settings


def setup_logging() -> logging.Logger:
    """
    Set up application logging configuration.

    Returns:
        logging.Logger: Configured root logger
    """
    # Create logger
    logger = logging.getLogger("agrinexus_market")
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional, for production)
    if not settings.DEBUG:
        try:
            file_handler = logging.FileHandler("market_forecast.log")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception:
            # If we can't create log file, continue with console only
            pass

    return logger


# Initialize logger
logger = setup_logging()