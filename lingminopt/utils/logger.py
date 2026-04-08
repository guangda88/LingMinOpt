"""
Logging utilities
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    file_level: Optional[int] = None,
    format_string: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """
    Setup a logger with console and optional rotating file output.

    Args:
        name: Logger name
        level: Console logging level (default: INFO)
        log_file: Optional file path for log output
        file_level: File logging level (default: DEBUG if log_file set, else ignored)
        format_string: Custom format string (optional)
        max_bytes: Maximum log file size before rotation (default: 10MB)
        backup_count: Number of rotated log files to keep (default: 5)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(min(level, file_level or level))

    if not logger.handlers:
        logger.propagate = False

    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        effective_file_level = file_level if file_level is not None else logging.DEBUG
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(effective_file_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
