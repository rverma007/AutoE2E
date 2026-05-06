"""
Pytest fixtures for the AutoPythone2e framework.

Key performance design:
 - browser        : session-scoped  (launched once per worker)
 - auth_state     : session-scoped  (one login per worker, cookies saved to disk)
 - authed_context : session-scoped  (one browser context per worker — avoids
                                     recreating context + loading storage_state
                                     for every single test)
 - authed_page    : function-scoped (fresh page per test, shares the context)
 - context/page   : function-scoped (anonymous, for login / env tests)

Trace recording uses start_chunk/stop_chunk so per-test traces still work
even though the context is shared across tests.
"""
from __future__ import annotations

import os
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Generator

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
from pages.audit_logger_page import AuditLoggerPage
from pages.component_library_page import ComponentLibraryPage
from pages.letter_control_center_page import LetterControlCenterPage
from pages.letter_consolidation_page import LetterConsolidationPage
from pages.recon_report_page import ReconReportPage
from pages.settings_page import SettingsPage
from utils.logger import get_logger


log = get_logger(__name__)

_STORAGE_STATE: Path = Config.REPORTS_DIR / f".auth_state_{_WORKER_ID}.json"


# ---------------------------------------------------------------------------
# Playwright / Browser  (session)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Generator[Browser, None, None]:
    browser_type = getattr(playwright_instance, Config.BROWSER)
    log.info(
        f"Launching {Config.BROWSER} "
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
    """Log in once, save cookies to disk.  Retries up to 3 times."""
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
# Anonymous context + page  (function-scoped, for login/env tests)
# ---------------------------------------------------------------------------
def _new_context(browser: Browser, *, with_storage: Path | None = None) -> BrowserContext:
    args: Dict = {"viewport": Config.viewport}
    if Config.RECORD_VIDEO:
        args["record_video_dir"] = str(Config.VIDEOS_DIR)
    if with_storage is not None and with_storage.exists():
        args["storage_state"] = str(with_storage)
    return browser.new_context(**args)


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
# Using session scope is the single biggest speed improvement:
#   • browser context creation     : ~1–2 s  saved per test
#   • storage_state loading        : ~1 s    saved per test
#   • tracing.start()              : ~0.5 s  saved per test
# With 13 authed tests that is ~30–45 s reclaimed per run.
#
# Trace isolation is preserved via start_chunk / stop_chunk so each test
# still gets its own trace file even though the context is shared.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def authed_context(browser: Browser, auth_state: Path) -> Generator[BrowserContext, None, None]:
    ctx = _new_context(browser, with_storage=auth_state)
    if Config.RECORD_TRACE:
        # start() once; individual tests call start_chunk/stop_chunk below.
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
    # Start a new trace chunk so this test gets its own trace file
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

    # Stop the trace chunk — keep only on failure
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

    try:
        p.close()
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# Page Object fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def login_page(page: Page) -> LoginPage:
    return LoginPage(page)


@pytest.fixture()
def letter_type_page(authed_page: Page) -> LetterTypePage:
    return LetterTypePage(authed_page)


@pytest.fixture()
def audit_logger_page(authed_page: Page) -> AuditLoggerPage:
    return AuditLoggerPage(authed_page)


@pytest.fixture()
def component_library_page(authed_page: Page) -> ComponentLibraryPage:
    return ComponentLibraryPage(authed_page)


@pytest.fixture()
def letter_control_center_page(authed_page: Page) -> LetterControlCenterPage:
    return LetterControlCenterPage(authed_page)


@pytest.fixture()
def letter_consolidation_page(authed_page: Page) -> LetterConsolidationPage:
    return LetterConsolidationPage(authed_page)


@pytest.fixture()
def recon_report_page(authed_page: Page) -> ReconReportPage:
    return ReconReportPage(authed_page)


@pytest.fixture()
def settings_page(authed_page: Page) -> SettingsPage:
    return SettingsPage(authed_page)


@pytest.fixture(scope="session")
def xml_file(tmp_path_factory) -> str:
    """Minimal valid XML for letter generation, created once per session."""
    fixtures_dir = tmp_path_factory.mktemp("fixtures")
    xml_path = fixtures_dir / "sample_member.xml"
    xml_path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<MemberData>\n"
        "  <Member>\n"
        "    <MemberId>TEST001</MemberId>\n"
        "    <FirstName>John</FirstName>\n"
        "    <LastName>Doe</LastName>\n"
        "    <DateOfBirth>1980-01-15</DateOfBirth>\n"
        "    <Plan>Gold</Plan>\n"
        "    <EffectiveDate>2026-01-01</EffectiveDate>\n"
        "  </Member>\n"
        "</MemberData>\n",
        encoding="utf-8",
    )
    log.info(f"Sample XML created -> {xml_path}")
    return str(xml_path)


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


def pytest_configure(config):
    config.addinivalue_line("markers", "sanity: quick smoke / sanity checks")
    config.addinivalue_line("markers", "regression: full regression suite")
    config.addinivalue_line("markers", "slow: long-running tests")
    htmlpath = config.getoption("htmlpath", default=None)
    if htmlpath:
        config._metadata = getattr(config, "_metadata", {}) or {}
        config._metadata["Environment"] = Config.ENVIRONMENT
        config._metadata["Base URL"] = Config.BASE_URL
        config._metadata["Browser"] = Config.BROWSER
        config._metadata["Headless"] = str(Config.HEADLESS)


def pytest_html_report_title(report):
    report.title = Config.REPORT_TITLE
