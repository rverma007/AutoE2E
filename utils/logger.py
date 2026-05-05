"""
Structured logger with console + file output.

Usage:
    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("hello")
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from config.config import Config


_LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LOG_FILE: Path = Config.REPORTS_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

_initialized = False


def _init_root() -> None:
    global _initialized
    if _initialized:
        return

    root = logging.getLogger("autopythone2e")
    root.setLevel(logging.DEBUG)
    root.propagate = False

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    root.addHandler(console)

    # File handler
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT, _DATE_FORMAT))
    root.addHandler(file_handler)

    _initialized = True


def get_logger(name: str = "autopythone2e") -> logging.Logger:
    _init_root()
    # Always namespaced under "autopythone2e" so both handlers apply.
    if not name.startswith("autopythone2e"):
        name = f"autopythone2e.{name}"
    return logging.getLogger(name)
