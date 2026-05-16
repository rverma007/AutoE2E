"""
Central configuration module.

Loads all runtime settings from environment variables (or .env file).
No credentials, URLs, or timeouts are hardcoded in the framework.

Usage:
    from config.config import Config
    url = Config.BASE_URL
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


# Project root (resolved once at import time)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Load the .env file from project root
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def _get_bool(key: str, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_int(key: str, default: int) -> int:
    value = os.environ.get(key)
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _get_str(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


@dataclass(frozen=True)
class _ConfigSchema:
    # Application
    BASE_URL: str
    APP_USERNAME: str
    APP_PASSWORD: str
    ENVIRONMENT: str

    # Browser
    BROWSER: str
    HEADLESS: bool
    SLOW_MO: int
    VIEWPORT_WIDTH: int
    VIEWPORT_HEIGHT: int

    # Timeouts
    DEFAULT_TIMEOUT: int
    NAVIGATION_TIMEOUT: int

    # Artifacts
    RECORD_VIDEO: bool
    RECORD_TRACE: bool
    SCREENSHOT_ON_FAILURE: bool

    # Reporting
    REPORT_TITLE: str

    # Paths (derived)
    PROJECT_ROOT: Path
    REPORTS_DIR: Path
    SCREENSHOTS_DIR: Path
    VIDEOS_DIR: Path
    TRACES_DIR: Path
    DOWNLOADS_DIR: Path

    @property
    def viewport(self) -> dict:
        return {"width": self.VIEWPORT_WIDTH, "height": self.VIEWPORT_HEIGHT}

    def validate(self) -> None:
        """Fail fast if required configuration is missing."""
        missing = []
        if not self.BASE_URL:
            missing.append("BASE_URL")
        if not self.APP_USERNAME:
            missing.append("APP_USERNAME")
        if not self.APP_PASSWORD:
            missing.append("APP_PASSWORD")
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please populate .env (see .env.example)."
            )


def _build_config() -> _ConfigSchema:
    reports_dir = PROJECT_ROOT / "reports"
    screenshots_dir = PROJECT_ROOT / "screenshots"
    videos_dir = PROJECT_ROOT / "videos"
    traces_dir = PROJECT_ROOT / "traces"
    downloads_dir = PROJECT_ROOT / "downloads"

    for d in (reports_dir, screenshots_dir, videos_dir, traces_dir, downloads_dir):
        d.mkdir(parents=True, exist_ok=True)

    cfg = _ConfigSchema(
        BASE_URL=_get_str("BASE_URL").rstrip("/") + "/",
        APP_USERNAME=_get_str("APP_USERNAME"),
        APP_PASSWORD=_get_str("APP_PASSWORD"),
        ENVIRONMENT=_get_str("ENVIRONMENT", "sprint"),
        BROWSER=_get_str("BROWSER", "chromium").lower(),
        HEADLESS=_get_bool("HEADLESS", False),
        SLOW_MO=_get_int("SLOW_MO", 0),
        VIEWPORT_WIDTH=_get_int("VIEWPORT_WIDTH", 1920),
        VIEWPORT_HEIGHT=_get_int("VIEWPORT_HEIGHT", 1080),
        DEFAULT_TIMEOUT=_get_int("DEFAULT_TIMEOUT", 30_000),
        NAVIGATION_TIMEOUT=_get_int("NAVIGATION_TIMEOUT", 60_000),
        RECORD_VIDEO=_get_bool("RECORD_VIDEO", False),
        RECORD_TRACE=_get_bool("RECORD_TRACE", True),
        SCREENSHOT_ON_FAILURE=_get_bool("SCREENSHOT_ON_FAILURE", True),
        REPORT_TITLE=_get_str("REPORT_TITLE", "AutoPythone2e Sanity Report"),
        PROJECT_ROOT=PROJECT_ROOT,
        REPORTS_DIR=reports_dir,
        SCREENSHOTS_DIR=screenshots_dir,
        VIDEOS_DIR=videos_dir,
        TRACES_DIR=traces_dir,
        DOWNLOADS_DIR=downloads_dir,
    )
    cfg.validate()
    return cfg


# Module-level singleton
Config: _ConfigSchema = _build_config()
