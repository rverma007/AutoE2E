"""
BasePage — common primitives every page object inherits.

Encapsulates Playwright interactions so individual page objects stay small,
declarative, and focused on domain-level intent.
"""
from __future__ import annotations

from typing import Optional

from playwright.sync_api import Locator, Page, TimeoutError as PWTimeoutError

from config.config import Config
from utils.logger import get_logger

_SUPPRESS_POPUP_SCRIPT = """
(function () {
    var MARKER = '__askAutoSuppressed';
    if (window[MARKER]) return;
    window[MARKER] = true;

    function hide(node) {
        if (!node || node.nodeType !== 1) return;
        var targets = [];
        if (node.getAttribute && node.getAttribute('role') === 'dialog') {
            targets.push(node);
        }
        if (node.querySelectorAll) {
            node.querySelectorAll('[role="dialog"]').forEach(function (d) {
                targets.push(d);
            });
        }
        targets.forEach(function (d) {
            if (d.textContent && d.textContent.includes('What can I help with')) {
                d.style.cssText += ';display:none!important;pointer-events:none!important;';
                d.setAttribute('aria-hidden', 'true');
            }
        });
    }

    var obs = new MutationObserver(function (mutations) {
        mutations.forEach(function (m) {
            if (m.type === 'childList') {
                m.addedNodes.forEach(hide);
            } else if (m.type === 'attributes' && m.target) {
                hide(m.target);
            }
        });
    });
    obs.observe(document.documentElement, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['class', 'style', 'aria-hidden', 'hidden']
    });

    setInterval(function () {
        document.querySelectorAll('[role="dialog"]').forEach(function (d) {
            if (d.textContent && d.textContent.includes('What can I help with')
                    && d.style.display !== 'none') {
                d.style.cssText += ';display:none!important;pointer-events:none!important;';
                d.setAttribute('aria-hidden', 'true');
            }
        });
    }, 400);
})();
"""


class BasePage:
    """All page objects extend this class."""

    PATH: str = ""

    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.log = get_logger(self.__class__.__name__)
        self.page.set_default_timeout(Config.DEFAULT_TIMEOUT)
        self.page.set_default_navigation_timeout(Config.NAVIGATION_TIMEOUT)
        try:
            self.page.add_init_script(_SUPPRESS_POPUP_SCRIPT)
        except Exception:  # noqa: BLE001
            pass

    @property
    def url(self) -> str:
        base = Config.BASE_URL.rstrip("/")
        path = (self.PATH or "").lstrip("/")
        return f"{base}/{path}" if path else f"{base}/"

    def navigate(self, path: Optional[str] = None) -> None:
        target = self.url if path is None else f"{Config.BASE_URL.rstrip('/')}/{path.lstrip('/')}"
        self.log.info(f"Navigating to: {target}")
        try:
            self.page.goto(
                target,
                wait_until="domcontentloaded",
                timeout=max(Config.NAVIGATION_TIMEOUT, 60_000),
            )
        except PWTimeoutError:
            self.log.debug("domcontentloaded timed out — continuing.")
        self.wait_for_idle()

    def wait_for_idle(self, timeout: Optional[int] = None) -> None:
        try:
            self.page.wait_for_load_state(
                "load", timeout=timeout or Config.NAVIGATION_TIMEOUT
            )
        except PWTimeoutError:
            self.log.debug("load state not reached — continuing.")

    def wait_for_visible(self, locator: Locator, timeout: Optional[int] = None) -> Locator:
        locator.wait_for(state="visible", timeout=timeout or Config.DEFAULT_TIMEOUT)
        return locator

    def safe_click(self, locator: Locator, label: str = "") -> None:
        self.wait_for_visible(locator)
        locator.scroll_into_view_if_needed()
        self.log.debug(f"Click -> {label or locator}")
        locator.click()

    def safe_fill(self, locator: Locator, value: str, label: str = "") -> None:
        self.wait_for_visible(locator)
        self.log.debug(f"Fill '{label or locator}' with len={len(value)}")
        locator.fill(value)

    def is_visible(self, locator: Locator, timeout: int = 2_000) -> bool:
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return True
        except PWTimeoutError:
            return False
        except Exception:  # noqa: BLE001
            return False

    def save_download(self, download, prefix: str = "download") -> tuple[str, str]:
        """Save a Playwright Download to Config.DOWNLOADS_DIR and return (filename, saved_path)."""
        import datetime as _dt
        filename = download.suggested_filename or f"{prefix}.bin"
        ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = Config.DOWNLOADS_DIR / f"{ts}_{filename}"
        download.save_as(str(dest))
        return filename, str(dest)

    @staticmethod
    def allure_attach_file(saved_path: str, filename: str) -> None:
        """Attach a saved download file to the Allure report. Never raises."""
        try:
            import allure as _allure
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            _EXT_MAP = {
                "csv": _allure.attachment_type.CSV,
                "pdf": _allure.attachment_type.PDF,
                "txt": _allure.attachment_type.TEXT,
                "json": _allure.attachment_type.JSON,
                "xml": _allure.attachment_type.XML,
                "html": _allure.attachment_type.HTML,
            }
            att_type = _EXT_MAP.get(ext, _allure.attachment_type.TEXT)
            with open(saved_path, "rb") as fh:
                data = fh.read()
            _allure.attach(data, name=filename, attachment_type=att_type)
        except Exception:  # noqa: BLE001
            pass

    def text_of(self, locator: Locator) -> str:
        try:
            text = (locator.inner_text() or "").strip()
            if not text:
                text = (locator.text_content() or "").strip()
            return text
        except Exception:  # noqa: BLE001
            return ""

    def dismiss_ask_auto_popup(self, timeout: int = 3_000) -> bool:
        try:
            hidden = self.page.evaluate("""
                () => {
                    var PHRASE = 'What can I help with';
                    var found = false;

                    // Pass 1: specific selectors (safe — won't match page containers)
                    var specific = [
                        '[role="dialog"]',
                        '[class*="ask-auto"]',
                        '[class*="chat-popup"]',
                        '[class*="AskAuto"]',
                        '[class*="assistant-popup"]',
                        '[class*="ai-popup"]',
                        '[class*="floating"]'
                    ].join(',');
                    document.querySelectorAll(specific).forEach(function(d) {
                        if (d.textContent && d.textContent.includes(PHRASE)) {
                            d.style.cssText += ';display:none!important;pointer-events:none!important;';
                            d.setAttribute('aria-hidden', 'true');
                            found = true;
                        }
                    });

                    // Pass 2: fallback — find the SMALLEST element containing the phrase.
                    // Skips anything > 70% of the viewport to avoid hiding the whole page.
                    if (!found) {
                        var vpArea = window.innerWidth * window.innerHeight;
                        var best = null;
                        var bestArea = Infinity;
                        document.querySelectorAll('div, section, aside').forEach(function(d) {
                            if (!d.textContent || !d.textContent.includes(PHRASE)) return;
                            var r = d.getBoundingClientRect();
                            var area = r.width * r.height;
                            if (area < vpArea * 0.7 && area < bestArea) {
                                bestArea = area;
                                best = d;
                            }
                        });
                        if (best) {
                            best.style.cssText += ';display:none!important;pointer-events:none!important;';
                            best.setAttribute('aria-hidden', 'true');
                            found = true;
                        }
                    }

                    // CRITICAL: The Ask Auto popup sets aria-hidden="true" on #root,
                    // which blocks all pointer events on the main app. Always restore it.
                    var root = document.getElementById('root');
                    if (root) root.removeAttribute('aria-hidden');
                    // Also restore any other main containers marked aria-hidden by the popup
                    document.querySelectorAll('body > div[aria-hidden="true"]').forEach(function(el) {
                        el.removeAttribute('aria-hidden');
                    });

                    return found;
                }
            """)
            if hidden:
                self.log.info("Ask Auto popup hidden via JavaScript.")
            return bool(hidden)
        except Exception:  # noqa: BLE001
            return False

    def current_url(self) -> str:
        return self.page.url

    def title(self) -> str:
        return self.page.title()
