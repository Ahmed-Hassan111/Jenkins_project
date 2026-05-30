"""
logger.py - Centralized logging configuration for Data Quality & ETL Validator.
Sets up file and console handlers with structured formatting.
"""

import logging
import os
from datetime import datetime


def setup_logger(name: str = "etl_validator") -> logging.Logger:
    """
    Configure and return a logger with both file and console handlers.

    Args:
        name: Logger name (default: 'etl_validator')

    Returns:
        Configured logging.Logger instance
    """
    # Ensure the logs directory exists
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_file = os.path.join(logs_dir, "app.log")

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on re-import
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # --- File handler (DEBUG and above) ---
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    # --- Console handler (INFO and above) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info("Logger initialised. Log file: %s", log_file)
    return logger
