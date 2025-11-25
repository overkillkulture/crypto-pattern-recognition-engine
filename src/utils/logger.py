"""Logging configuration."""

import sys
from pathlib import Path
from typing import Any, Dict

from loguru import logger


def setup_logger(config: Dict[str, Any]) -> None:
    """
    Configure logging based on config.

    Args:
        config: Logging configuration
    """
    # Remove default handler
    logger.remove()

    # Get logging config
    log_config = config.get("logging", {})
    level = log_config.get("level", "INFO")
    format_type = log_config.get("format", "text")
    outputs = log_config.get("output", ["console"])

    # Define format
    if format_type == "json":
        log_format = (
            "{{"
            '"timestamp": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"message": "{message}", '
            '"module": "{module}", '
            '"function": "{function}", '
            '"line": {line}'
            "}}"
        )
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # Add console handler
    if "console" in outputs:
        logger.add(
            sys.stderr,
            format=log_format,
            level=level,
            colorize=format_type != "json",
        )

    # Add file handler
    if "file" in outputs:
        file_config = log_config.get("file", {})
        log_path = file_config.get("path", "logs/engine.log")
        rotation = file_config.get("rotation", "100 MB")
        retention = file_config.get("retention", "30 days")

        # Create log directory
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_path,
            format=log_format,
            level=level,
            rotation=rotation,
            retention=retention,
            compression="gz",
        )

    logger.info(f"Logger configured: level={level}, outputs={outputs}")
