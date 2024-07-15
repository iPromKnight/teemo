"""Logging utils"""

import sys
from loguru import logger
from src.settings.manager import settings_manager
from rich.console import Console


def setup_logger(level):
    # Default log levels
    logger.level("INFO", icon="📰")
    logger.level("DEBUG", icon="🤖")
    logger.level("WARNING", icon="⚠️ ")
    logger.level("CRITICAL", icon="")
    logger.level("SUCCESS", icon="✔️ ")

    # Log format to match the old log format, but with color
    log_format = (
        "<fg #818589>{time:YY-MM-DD} {time:HH:mm:ss}</fg #818589> | "
        "<level>{level.icon}</level> <level>{level: <9}</level> | "
        "<fg #990066>{module}</fg #990066>.<fg #990066>{function}</fg #990066> - <level>{message}</level>"
    )

    logger.configure(handlers=[
        {
            "sink": sys.stderr,
            "level": "DEBUG",
            "format": log_format,
            "backtrace": False,
            "diagnose": False,
            "enqueue": True,
        },
        {
            "sink": sys.stdout,
            "level": level, 
            "format": log_format,
            "backtrace": False,
            "diagnose": False,
            "enqueue": True,
        }
    ])


console = Console()
log_level = "DEBUG" if settings_manager.settings.debug else "INFO"
setup_logger(log_level)