"""
Logging utilities for the travel planner system.
"""
import sys

from loguru import logger

from src.config.settings import settings


def setup_logger():
    """Set up the application logger."""
    # Remove default handler
    logger.remove()

    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:"
               "<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )

    # Add file handler for errors
    logger.add(
        "logs/travel_planner.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
               "{name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )

    return logger


# Initialize logger
app_logger = setup_logger()


def get_logger(name: str):
    """Return a logger instance bound with the given name."""
    return app_logger.bind(name=name)
