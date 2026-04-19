#!/usr/bin/env python3
"""
Production logging helpers for deployment utilities.
"""

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Any


LOG_DIRS = [
    Path("logs"),
    Path("logs/daily"),
    Path("logs/errors"),
    Path("logs/trades"),
    Path("logs/system"),
]


def ensure_log_directories():
    """Create the log directory structure expected by deployment scripts."""
    for directory in LOG_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def setup_production_logging() -> logging.Logger:
    """Configure a shared project logger for production helpers."""
    ensure_log_directories()

    logger = logging.getLogger("trading")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = RotatingFileHandler(
        "logs/system/trading.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger


def log_system_metrics(metrics: Dict[str, Any]):
    """Persist system metrics in both log and jsonl form for monitoring."""
    logger = setup_production_logging()
    logger.info("System metrics: %s", metrics)

    ensure_log_directories()
    with Path("logs/system/metrics.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(metrics, default=str) + "\n")
