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

# ---------------------------------------------------------------------------
# Browser-level Ask Auto popup suppressor
# ---------------------------------------------------------------------------
# Injected into every page before first navigation.  Uses a MutationObserver
# to hide the popup the instant it appears in the DOM, and a setInterval
# fallback for popups that become visible via CSS class changes rather than
# new DOM nodes.  Neither mechanism uses the Escape key, so other open
# panels/drawers (Configure, Filter) are never accidentally closed.
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

    // Watch for new nodes and attribute changes that reveal the popup
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

    // Interval safety net: catch any popup that slips through
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

    #: Subclasses may override to set a canonical URL path, e.g. "/login".
    PATH: str = ""

    def __init__(self, page: Page) -> None:
        self.page: Page = page
        self.log = get_logger(self.__class__.__name__)
        self.page.set_default_timeout(Config.DEFAULT_TIMEOUT)
        self.page.set_default_navigation_timeout(Config.NAVIGATION_TIMEOUT)
        # Inject the popup suppressor before any navigation so it runs on
        # every page load for the lifetime of this Page object.
        try:
            self.page.add_init_script(_SUPPRESS_POPUP_SCRIPT)
        except Exception:  # noqa: BLE001
            pass  # page may already be closed / detached in edge-case fixtures

    # ------------------------------------------------------------------ URLs
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

    # ----------------------------------------------------------------- Waits
    def wait_for_idle(self, timeout: Optional[int] = None) -> None:
        try:
            self.page.wait_for_load_state(
                "load", timeout=timeout or Config.NAVIGATION_TIMEOUT
            )
        except PWTimeoutError:
            self.log.debug("load state not reached — continuing.")

    def wait_for_visible(
        self, locator: Locator, timeout: Optional[int] = None
    ) -> Locator:
        locator.wait_for(state="visible", timeout=timeout or Config.DEFAULT_TIMEOUT)
        return locator

    # --------------------------------------------------------- Safe primitives
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
        # Use wait_for so the timeout parameter is actually honoured
        # (locator.is_visible() is an instant check with no retry).
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return True
        except PWTimeoutError:
            return False
        except Exception:  # noqa: BLE001
            return False

    def text_of(self, locator: Locator) -> str:
        try:
            text = (locator.inner_text() or "").strip()
            if not text:
                text = (locator.text_content() or "").strip()
            return text
        except Exception:  # noqa: BLE001
            return ""

    # ------------------------------------------------------- Modal / Overlay
    def dismiss_ask_auto_popup(self, timeout: int = 3_000) -> bool:
        """Hide the Ask Auto popup if it is still visible.

        The init-script suppressor handles most cases automatically.  This
        method is a fallback for popups that appear between the suppressor's
        400 ms polling intervals.

        Uses JavaScript to hide the element — never Escape — so other open
        panels (Configure drawer, Filter panel) are not accidentally closed.
        """
        try:
            hidden = self.page.evaluate("""
                () => {
                    var found = false;
                    document.querySelectorAll('[role="dialog"]').forEach(function(d) {
                        if (d.textContent && d.textContent.includes('What can I help with')) {
                            d.style.cssText += ';display:none!important;pointer-events:none!important;';
                            d.setAttribute('aria-hidden', 'true');
                            found = true;
                        }
                    });
                    return found;
                }
            """)
            if hidden:
                self.log.info("Ask Auto popup hidden via JavaScript.")
            return bool(hidden)
        except Exception:  # noqa: BLE001
            return False

    # ----------------------------------------------------------------- Asserts
    def current_url(self) -> str:
        return self.page.url

    def title(self) -> str:
        return self.page.title()
