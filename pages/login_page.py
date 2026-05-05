"""
LoginPage — represents the login screen of the correspondence app.

All selectors live here; tests never touch selectors directly.
Login credentials are supplied by the caller (resolved from Config).
"""
from __future__ import annotations

from typing import Optional
from urllib.parse import urlparse

from playwright.sync_api import Page, TimeoutError as PWTimeoutError

from config.config import Config
from pages.base_page import BasePage


def _app_netloc(base: str) -> str:
    """Extract the hostname from BASE_URL, e.g. 'correspondence.sprint.autonomize.dev'."""
    return urlparse(base).netloc


def _is_authenticated_url(url: str, base: str) -> bool:
    """Return True only when the browser is on the app's own domain AND past the root.

    The Keycloak initial auth URL (/protocol/openid-connect/auth?...) does NOT
    contain the word 'login', so keyword-based checks incorrectly treat it as an
    authenticated page.  Checking the hostname is the reliable approach.
    """
    parsed = urlparse(url)
    app_host = _app_netloc(base)
    # Must be on the app domain
    if parsed.netloc != app_host:
        return False
    # Must not be the bare root (which immediately redirects to Keycloak)
    if url.rstrip("/") == base.rstrip("/"):
        return False
    return True


class LoginPage(BasePage):
    """Page Object for the login screen."""

    # No explicit path — app redirects to login when unauthenticated
    PATH = ""

    # -- Locators (defined as properties so they're re-resolved each call) --
    # Mirrors pdftest/basic.py: the Molina Correspondence app uses id=username,
    # id=password, and <input type="submit"> for the primary "Login" button.
    @property
    def username_input(self):
        return self.page.locator("#username").first

    @property
    def password_input(self):
        return self.page.locator("#password").first

    @property
    def submit_button(self):
        # pdftest uses XPath //input[@type='submit'] — keep that exact selector.
        return self.page.locator("xpath=//input[@type='submit']").first

    @property
    def error_message(self):
        return self.page.locator(
            ".alert-error, .error, [role='alert'], .Mui-error, .error-message"
        ).first

    # ---------------------------------------------------------------- Actions
    def open(self) -> "LoginPage":
        self.navigate()
        # Wait for the login form to appear (handles SPA redirect to /login).
        self.is_displayed(timeout=60_000)
        # Second load-state wait: ensures no navigation is still in flight after
        # the form appears (calling page.title() mid-navigation destroys context).
        try:
            self.page.wait_for_load_state("load", timeout=15_000)
        except Exception:  # noqa: BLE001
            pass
        return self

    def is_displayed(self, timeout: int = 30_000) -> bool:
        """True when the username field is on screen.

        Uses Locator.wait_for(state='visible'), which is the canonical
        Playwright way to wait for an element to appear. Playwright's
        Locator.is_visible() is a *snapshot* check — the `timeout` argument
        is advisory and can return False immediately on slow cold-starts,
        which is exactly what was happening on the first test in the suite.
        """
        try:
            self.username_input.wait_for(state="visible", timeout=timeout)
            return True
        except PWTimeoutError:
            return False
        except Exception:  # noqa: BLE001
            return False

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        max_attempts: int = 3,
    ) -> None:
        """Perform a login. Credentials default to those from Config.

        Retries up to `max_attempts` times to handle transient Keycloak
        redirect failures that occur in parallel CI runs.
        """
        username = username if username is not None else Config.APP_USERNAME
        password = password if password is not None else Config.APP_PASSWORD

        base = Config.BASE_URL.rstrip("/")

        def _is_authenticated() -> bool:
            return _is_authenticated_url(self.page.url, base)

        if _is_authenticated():
            self.log.info("Already authenticated — skipping login.")
            return

        submit_selector = "xpath=//input[@type='submit']"

        for attempt in range(1, max_attempts + 1):
            if not self.is_displayed(timeout=60_000):
                self.log.info("Login form not visible — assuming already authenticated.")
                return

            self.log.info(f"Logging in as '{username}' (attempt {attempt}/{max_attempts})")
            self.page.fill("#username", username)
            self.page.fill("#password", password)

            try:
                with self.page.expect_navigation(wait_until="load", timeout=20_000):
                    self.page.click(submit_selector)
            except Exception as exc:  # noqa: BLE001
                self.log.info(f"No hard navigation after submit (likely SPA): {exc}")
                try:
                    self.page.wait_for_load_state("load", timeout=20_000)
                except Exception:  # noqa: BLE001
                    pass

            # Keycloak OAuth redirect can take 30–45 s on slow envs.
            try:
                self.page.wait_for_url(
                    lambda url: _is_authenticated_url(url, base),
                    timeout=45_000,
                )
                self.log.info(f"Auth redirect complete. Current URL: {self.page.url}")

                # The SPA lands on /#state=...&code=... and then exchanges the
                # code for a session token asynchronously.  Navigating away
                # immediately interrupts that exchange and leaves the session
                # un-initialised.  Wait for the hash/query params to clear.
                try:
                    self.page.wait_for_url(
                        lambda url: "code=" not in url and "state=" not in url,
                        timeout=20_000,
                    )
                    self.log.info(f"Session established. Current URL: {self.page.url}")
                except Exception:  # noqa: BLE001
                    # The app may keep the code in the URL — still usable.
                    self.log.info(
                        f"OAuth params still in URL after wait: {self.page.url}"
                    )
                    # Give the SPA time to finish async token exchange.
                    # On slow envs the code exchange can take 10-15 s; navigating
                    # away before it completes breaks the session entirely.
                    self.page.wait_for_timeout(10_000)

                self.log.info("Login submitted.")
                return
            except Exception:  # noqa: BLE001
                self.log.warning(
                    f"URL did not change after login attempt {attempt} "
                    f"(current: {self.page.url})"
                )
                if attempt < max_attempts:
                    self.log.info("Re-navigating to login page for retry…")
                    try:
                        self.navigate()
                    except Exception:  # noqa: BLE001
                        pass

        self.log.info("Login submitted (all attempts exhausted).")

    def get_error_text(self) -> str:
        if self.is_visible(self.error_message, timeout=1_500):
            return self.text_of(self.error_message)
        return ""
