"""
Pytest fixtures for the AutoPythone2e framework.

Scalability design:
 - browser            : session-scoped  (launched once per worker)
 - auth_state         : session-scoped  (one login per worker, cookies saved to disk)
 - authed_context     : session-scoped  (one browser context per worker — fastest path)
 - authed_page        : function-scoped (fresh page per test; clears non-auth
                                         localStorage on teardown to prevent state leak)
 - isolated_authed_page: function-scoped (fresh context per test — full DOM/storage
                                         isolation; ~2s slower, use for tests that
                                         mutate context-level state)
 - api_client         : session-scoped  (authenticated HTTP client for data setup)
 - context / page     : function-scoped (anonymous, for login / env tests)

Parallelism:
 - Set PYTEST_WORKERS=N (or pass -n N) to run N parallel workers.
 - conftest applies --dist loadfile automatically when PYTEST_WORKERS is set.
 - Explicit CLI -n always wins over PYTEST_WORKERS.

Cross-browser:
 - Set BROWSER=firefox in .env, or pass --browser-override firefox at CLI.
"""
from __future__ import annotations

import json
import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator, Optional

_WORKER_ID = os.environ.get("PYTEST_XDIST_WORKER", "master")

import pytest
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from config.config import Config
from pages.login_page import LoginPage
from pages.letter_type_page import LetterTypePage
from utils.logger import get_logger


log = get_logger(__name__)

_STORAGE_STATE: Path = Config.REPORTS_DIR / f".auth_state_{_WORKER_ID}.json"


# ---------------------------------------------------------------------------
# pytest CLI options
# ---------------------------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--browser-override",
        default=None,
        metavar="BROWSER",
        help="Override the BROWSER env var at runtime: chromium | firefox | webkit",
    )


# ---------------------------------------------------------------------------
# pytest_configure — apply env-driven settings before tests start
# ---------------------------------------------------------------------------
def pytest_configure(config):
    # ── Browser override ──────────────────────────────────────────────────
    # Must set os.environ BEFORE the browser fixture reads it.
    try:
        browser_override = config.getoption("--browser-override", default=None)
        if browser_override:
            os.environ["BROWSER"] = browser_override.lower()
            log.info(f"Browser overridden via CLI: {browser_override}")
    except (ValueError, AttributeError):
        pass

    # ── Parallel workers via PYTEST_WORKERS env var ───────────────────────
    # Only applied when -n was NOT already passed on the CLI.
    workers_env = os.environ.get("PYTEST_WORKERS", "").strip()
    if workers_env:
        try:
            current = getattr(config.option, "numprocesses", None)
            if current is None:
                val = int(workers_env) if workers_env.isdigit() else workers_env
                config.option.numprocesses = val
                # Apply loadfile distribution so all tests in a file run on
                # the same worker — prevents cross-worker ordering interference.
                if getattr(config.option, "dist", "no") in ("no", None):
                    config.option.dist = "loadfile"
                log.info(f"Parallel workers set from PYTEST_WORKERS={workers_env}")
        except (AttributeError, ValueError):
            pass

    # ── Markers & HTML metadata ───────────────────────────────────────────
    config.addinivalue_line("markers", "sanity: quick smoke / sanity checks")
    config.addinivalue_line("markers", "regression: full regression suite")
    config.addinivalue_line("markers", "slow: long-running tests (upload polling, etc.)")
    htmlpath = config.getoption("htmlpath", default=None)
    if htmlpath:
        config._metadata = getattr(config, "_metadata", {}) or {}
        config._metadata["Environment"] = Config.ENVIRONMENT
        config._metadata["Base URL"]    = Config.BASE_URL
        config._metadata["Browser"]     = os.environ.get("BROWSER", Config.BROWSER)
        config._metadata["Headless"]    = str(Config.HEADLESS)
        config._metadata["Workers"]     = os.environ.get("PYTEST_WORKERS", "1")


def pytest_html_report_title(report):
    report.title = Config.REPORT_TITLE


# ---------------------------------------------------------------------------
# Playwright / Browser  (session)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Generator[Browser, None, None]:
    # Read BROWSER from env directly so --browser-override CLI flag takes effect
    # without requiring a Config reload (Config is a frozen singleton).
    browser_name = os.environ.get("BROWSER", "chromium").lower()
    browser_type = getattr(playwright_instance, browser_name)
    log.info(
        f"Launching {browser_name} "
        f"(headless={Config.HEADLESS}, slow_mo={Config.SLOW_MO})"
    )
    b = browser_type.launch(headless=Config.HEADLESS, slow_mo=Config.SLOW_MO)
    yield b
    b.close()


# ---------------------------------------------------------------------------
# Auth state  (session — one login per worker)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=False)
def auth_state(browser: Browser) -> Path:
    """Log in once, save cookies+localStorage to disk. Retries up to 3 times."""
    if _STORAGE_STATE.exists():
        try:
            _STORAGE_STATE.unlink()
        except Exception:  # noqa: BLE001
            pass

    last_exc: Exception | None = None
    for attempt in range(1, 4):
        ctx = browser.new_context(viewport=Config.viewport)
        pg = ctx.new_page()
        try:
            lp = LoginPage(pg)
            lp.open()
            lp.login()

            lt = LetterTypePage(pg)
            if not lt.is_loaded(timeout=20_000):
                lt.open_direct()
            if lt.is_loaded(timeout=20_000):
                ctx.storage_state(path=str(_STORAGE_STATE))
                log.info(f"Auth state saved -> {_STORAGE_STATE}")
                return _STORAGE_STATE

            log.warning(f"Auth attempt {attempt}/3: letter-type page did not load.")
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            log.warning(f"Auth attempt {attempt}/3 failed: {exc}")
        finally:
            ctx.close()

    raise RuntimeError(
        f"Could not establish auth session after 3 attempts. "
        f"Last error: {last_exc}"
    )


# ---------------------------------------------------------------------------
# Context factory
# ---------------------------------------------------------------------------
def _new_context(browser: Browser, *, with_storage: Optional[Path] = None) -> BrowserContext:
    args: Dict = {"viewport": Config.viewport}
    if Config.RECORD_VIDEO:
        args["record_video_dir"] = str(Config.VIDEOS_DIR)
    if with_storage is not None and with_storage.exists():
        args["storage_state"] = str(with_storage)
    return browser.new_context(**args)


# ---------------------------------------------------------------------------
# Anonymous context + page  (function-scoped, for login/env tests)
# ---------------------------------------------------------------------------
@pytest.fixture()
def context(browser: Browser, request) -> Generator[BrowserContext, None, None]:
    ctx = _new_context(browser)
    if Config.RECORD_TRACE:
        ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield ctx
    _finalize_context(ctx, request, trace_prefix="anon")


@pytest.fixture()
def page(context: BrowserContext) -> Generator[Page, None, None]:
    p = context.new_page()
    yield p


# ---------------------------------------------------------------------------
# Authenticated context  (SESSION-scoped — created once per worker)
#
# Why session scope?
#   • browser context creation     : ~1–2 s saved per test
#   • storage_state loading        : ~1 s   saved per test
#   • tracing.start()              : ~0.5 s saved per test
# With 13+ authed tests that is 30–45 s reclaimed per run.
#
# State isolation between tests is preserved by:
#   1. A fresh Page (tab) per test via authed_page (function-scoped).
#   2. authed_page teardown clears non-auth localStorage keys so one test's
#      stored filter/pagination state cannot pollute the next test.
#   3. Per-test trace chunks via start_chunk/stop_chunk.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def authed_context(browser: Browser, auth_state: Path) -> Generator[BrowserContext, None, None]:
    ctx = _new_context(browser, with_storage=auth_state)
    if Config.RECORD_TRACE:
        ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    yield ctx
    if Config.RECORD_TRACE:
        try:
            ctx.tracing.stop()
        except Exception:  # noqa: BLE001
            pass
    ctx.close()


# ---------------------------------------------------------------------------
# Authenticated page  (function-scoped — fresh page per test)
# ---------------------------------------------------------------------------
@pytest.fixture()
def authed_page(authed_context: BrowserContext, request) -> Generator[Page, None, None]:
    if Config.RECORD_TRACE:
        try:
            authed_context.tracing.start_chunk()
        except Exception:  # noqa: BLE001
            pass

    p = authed_context.new_page()
    yield p

    # ── teardown ────────────────────────────────────────────────────────────
    rep = getattr(request.node, "rep_call", None)
    failed = bool(rep and rep.failed)
    test_name = request.node.name

    # Screenshot on failure
    if Config.SCREENSHOT_ON_FAILURE and failed:
        try:
            shot = Config.SCREENSHOTS_DIR / f"{test_name}_{_timestamp()}_0.png"
            p.screenshot(path=str(shot), full_page=True)
            log.warning(f"Screenshot on failure -> {shot}")
            _attach_artifact(request, shot, "image/png", label="screenshot")
        except Exception as exc:  # noqa: BLE001
            log.warning(f"Could not capture screenshot: {exc}")

    # Trace chunk — keep only on failure
    if Config.RECORD_TRACE:
        trace_path = Config.TRACES_DIR / f"authed_{test_name}_{_timestamp()}.zip"
        try:
            authed_context.tracing.stop_chunk(path=str(trace_path))
            if failed:
                log.warning(f"Trace saved -> {trace_path}")
                _attach_artifact(request, trace_path, "application/zip", label="trace.zip")
            else:
                try:
                    trace_path.unlink()
                except Exception:  # noqa: BLE001
                    pass
        except Exception as exc:  # noqa: BLE001
            log.debug(f"Trace chunk stop failed: {exc}")

    # Clear non-auth localStorage so filter/pagination/modal state from this
    # test cannot pollute the next test sharing this context.
    _clear_app_local_storage(p)

    try:
        p.close()
    except Exception:  # noqa: BLE001
        pass


def _clear_app_local_storage(p: Page) -> None:
    """Remove non-auth localStorage keys to prevent cross-test state pollution.

    Auth tokens (OIDC/Keycloak keys) are preserved so the shared session
    context remains authenticated for the next test.
    """
    try:
        p.evaluate("""
            () => {
                const AUTH_PATTERNS = ['oidc', 'kc-', 'keycloak', 'token', 'auth', 'session'];
                const toRemove = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const k = localStorage.key(i);
                    if (!k) continue;
                    const lower = k.toLowerCase();
                    const isAuth = AUTH_PATTERNS.some(p => lower.includes(p));
                    if (!isAuth) toRemove.push(k);
                }
                toRemove.forEach(k => localStorage.removeItem(k));
            }
        """)
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# Isolated authenticated page  (function-scoped, fresh context per test)
#
# Use this for tests that mutate context-level state (cookies, permissions)
# or when you need guaranteed clean-slate isolation at the cost of ~2s/test.
# ---------------------------------------------------------------------------
@pytest.fixture()
def isolated_authed_page(browser: Browser, auth_state: Path, request) -> Generator[Page, None, None]:
    """Fresh browser context per test — full DOM/storage isolation."""
    ctx = _new_context(browser, with_storage=auth_state)
    if Config.RECORD_TRACE:
        ctx.tracing.start(screenshots=True, snapshots=True, sources=True)
    p = ctx.new_page()
    yield p
    _finalize_context(ctx, request, trace_prefix="isolated")


# ---------------------------------------------------------------------------
# API client  (session-scoped — reuses auth cookies from storage state)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def api_client(auth_state: Path):
    """Authenticated HTTP client for test data setup/teardown.

    Loads cookies from the Playwright storage state so API calls are
    authenticated without needing a separate login flow.
    """
    from utils.api_client import CorrespondenceApiClient
    return CorrespondenceApiClient(Config.BASE_URL, storage_state_path=auth_state)


# ---------------------------------------------------------------------------
# Page Object fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def login_page(page: Page) -> LoginPage:
    return LoginPage(page)


@pytest.fixture()
def letter_type_page(authed_page: Page) -> LetterTypePage:
    return LetterTypePage(authed_page)


@pytest.fixture(scope="session")
def template_file(tmp_path_factory) -> str:
    """Minimal valid .docx created once per session."""
    fixtures_dir = tmp_path_factory.mktemp("fixtures")
    docx_path = fixtures_dir / "sample_template.docx"

    with zipfile.ZipFile(docx_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument'
            '.wordprocessingml.document.main+xml"/>'
            "</Types>",
        )
        zf.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
            ' Target="word/document.xml"/>'
            "</Relationships>",
        )
        zf.writestr(
            "word/_rels/document.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            "</Relationships>",
        )
        zf.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Sample Letter Template</w:t></w:r></w:p></w:body>"
            "</w:document>",
        )

    log.info(f"Sample template created -> {docx_path}")
    return str(docx_path)


# ---------------------------------------------------------------------------
# Anonymous context finalizer  (screenshot + trace + video on failure)
# ---------------------------------------------------------------------------
def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def _finalize_context(ctx: BrowserContext, request, trace_prefix: str) -> None:
    rep = getattr(request.node, "rep_call", None)
    failed = bool(rep and rep.failed)
    test_name = request.node.name
    pages_snapshot = list(ctx.pages)

    try:
        if Config.SCREENSHOT_ON_FAILURE and failed:
            for idx, pg in enumerate(pages_snapshot):
                shot = Config.SCREENSHOTS_DIR / f"{test_name}_{_timestamp()}_{idx}.png"
                try:
                    pg.screenshot(path=str(shot), full_page=True)
                    log.warning(f"Screenshot on failure -> {shot}")
                    _attach_artifact(request, shot, "image/png", label="screenshot")
                except Exception as exc:  # noqa: BLE001
                    log.warning(f"Could not capture screenshot: {exc}")

        if Config.RECORD_TRACE:
            trace_path = Config.TRACES_DIR / f"{trace_prefix}_{test_name}_{_timestamp()}.zip"
            try:
                ctx.tracing.stop(path=str(trace_path))
                if not failed:
                    try:
                        trace_path.unlink()
                    except Exception:  # noqa: BLE001
                        pass
                else:
                    log.warning(f"Trace saved -> {trace_path}")
                    _attach_artifact(request, trace_path, "application/zip", label="trace.zip")
            except Exception as exc:  # noqa: BLE001
                log.debug(f"Trace stop failed: {exc}")
    finally:
        ctx.close()

    if Config.RECORD_VIDEO:
        for idx, pg in enumerate(pages_snapshot):
            try:
                vid = pg.video
                if vid is None:
                    continue
                src = Path(vid.path())
                dst = Config.VIDEOS_DIR / f"{test_name}_{_timestamp()}_{idx}.webm"
                try:
                    src.rename(dst)
                except Exception:  # noqa: BLE001
                    dst = src
                if failed:
                    log.warning(f"Video saved -> {dst}")
                    _attach_artifact(request, dst, "video/webm", label="video.webm")
                else:
                    try:
                        dst.unlink()
                    except Exception:  # noqa: BLE001
                        pass
            except Exception as exc:  # noqa: BLE001
                log.debug(f"Video capture failed: {exc}")


def _attach_artifact(request, path: Path, mime: str, label: str = "") -> None:
    _attach_to_html(request, path, mime)
    _attach_to_allure(path, mime, label=label)


def _attach_to_html(request, path: Path, mime: str) -> None:
    try:
        from pytest_html import extras  # type: ignore
        existing = getattr(request.node, "_html_extras", [])
        rel = os.path.relpath(path, Config.REPORTS_DIR)
        if mime.startswith("image/"):
            existing.append(extras.image(rel))
        else:
            existing.append(extras.url(rel, name=path.name))
        request.node._html_extras = existing
    except Exception:  # noqa: BLE001
        pass


def _attach_to_allure(path: Path, mime: str, label: str = "") -> None:
    try:
        import allure  # type: ignore
        if not path.exists():
            return
        if mime.startswith("image/"):
            at = allure.attachment_type.PNG
        elif mime.startswith("video/"):
            at = allure.attachment_type.WEBM
        else:
            at = None
        name = label or path.name
        if at is not None:
            allure.attach.file(str(path), name=name, attachment_type=at)
        else:
            allure.attach.file(str(path), name=name, extension=path.suffix.lstrip("."))
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# pytest hooks
# ---------------------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
    if rep.when == "call":
        extras = getattr(item, "_html_extras", [])
        if extras:
            rep.extras = extras
