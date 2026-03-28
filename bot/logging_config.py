"""
Logging configuration for the trading bot.
Sets up structured logging to both console and file.
"""

import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(log_dir: str = "logs", log_file: str = "trading_bot.log") -> logging.Logger:
    """
    Configure and return the root logger with file and console handlers.

    Args:
        log_dir: Directory where log files will be stored.
        log_file: Name of the log file.

    Returns:
        Configured logger instance.
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # --- File handler (DEBUG and above) ---
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # --- Console handler (INFO and above) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Module-level logger for internal use
logger = setup_logging()
