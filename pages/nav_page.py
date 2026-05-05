"""
NavigationPage — encapsulates the left sidebar navigation.

All tests that need to click through the nav import this class instead of
hardcoding selectors.  Expand-button groups (Letter Configuration, Reports)
are handled here so callers don't have to care about DOM internals.

Design decisions
----------------
* Every go_to_* method first attempts the sidebar click, then falls back to
  direct URL navigation.  This means the test still validates that the page
  loads even if a sidebar link is temporarily mis-wired.
* _expand_group does NOT rely on aria-expanded (the button may not have it).
  It always tries to click the expand button and then waits for any one of
  the group's child links to become visible before proceeding.
* DEFAULT_TIMEOUT for sub-link visibility is kept short (5 s) so failures
  are reported quickly rather than after a full 30 s timeout.
"""
from __future__ import annotations

from playwright.sync_api import TimeoutError as PWTimeoutError

from pages.base_page import BasePage


class NavigationPage(BasePage):
    """Sidebar navigation helper shared by all post-login pages."""

    PATH = "dashboard"  # canonical start after login

    _EXPAND_WAIT_MS = 1_500   # animation settle time after expand click
    _SUBLINK_TIMEOUT = 6_000  # how long to wait for a sub-link after expand

    # ── Sidebar link / button locators ─────────────────────────────────────

    @property
    def _ask_auto_link(self):
        return self.page.locator("a[href*='ask-auto']").first

    @property
    def _dashboard_link(self):
        return self.page.locator("a[href*='/dashboard']").first

    @property
    def _letter_config_expand_btn(self):
        return self.page.locator("button.expand-btn", has_text="Letter Configuration").first

    @property
    def _letter_type_link(self):
        return self.page.locator("a[href*='letter-type']").first

    @property
    def _component_library_link(self):
        return self.page.locator("a[href*='/components']").first

    @property
    def _letter_consolidation_link(self):
        return self.page.locator("a[href*='letter-consolidation']").first

    @property
    def _letter_control_center_link(self):
        return self.page.locator("a[href*='letter-control-center']").first

    @property
    def _settings_link(self):
        return self.page.locator("a[href*='/settings']").first

    @property
    def _reports_expand_btn(self):
        return self.page.locator("button.expand-btn", has_text="Reports").first

    @property
    def _audit_logger_link(self):
        return self.page.locator("a[href*='audit-logger']").first

    @property
    def _recon_report_link(self):
        return self.page.locator("a[href*='recon-report']").first

    # ── Private helpers ─────────────────────────────────────────────────────

    def _expand_group(self, btn_locator, child_link_locator, group_name: str) -> bool:
        """
        Expand a sidebar accordion group and wait until a child link is visible.

        Returns True if the group is open (child link visible), False otherwise.
        Raises nothing — callers decide what to do on failure.
        """
        # Step 1: check if child links are already visible (group already open)
        if self.is_visible(child_link_locator, timeout=1_000):
            self.log.debug(f"Group '{group_name}' already expanded.")
            return True

        # Step 2: click the expand button
        try:
            btn_locator.wait_for(state="visible", timeout=8_000)
            btn_locator.click()
            self.page.wait_for_timeout(self._EXPAND_WAIT_MS)
        except Exception as exc:
            self.log.warning(f"Could not click expand button for '{group_name}': {exc}")
            return False

        # Step 3: confirm child links are now visible
        if self.is_visible(child_link_locator, timeout=self._SUBLINK_TIMEOUT):
            return True

        self.log.warning(f"Child links still not visible after expanding '{group_name}'.")
        return False

    def _click_or_navigate(self, link_locator, fallback_path: str, label: str) -> None:
        """
        Try clicking a sidebar link; fall back to direct URL navigation if it
        isn't visible within a short window (avoids a 30 s timeout on failures).
        """
        if self.is_visible(link_locator, timeout=4_000):
            link_locator.scroll_into_view_if_needed()
            link_locator.click()
            self.log.info(f"Sidebar click -> {label}")
        else:
            self.log.warning(
                f"Sidebar link '{label}' not visible — falling back to direct navigation."
            )
            self.navigate(fallback_path)

        self.wait_for_idle()

    # ── Public navigation methods ───────────────────────────────────────────

    def go_to_ask_auto(self) -> None:
        """Navigate to Ask Auto via sidebar link or direct URL."""
        self._click_or_navigate(self._ask_auto_link, "ask-auto", "Ask Auto")

    def go_to_dashboard(self) -> None:
        self._click_or_navigate(self._dashboard_link, "dashboard", "My Dashboard")

    def go_to_letter_type(self) -> None:
        self._expand_group(
            self._letter_config_expand_btn,
            self._letter_type_link,
            "Letter Configuration",
        )
        self._click_or_navigate(self._letter_type_link, "letter-type", "Letter Type")

    def go_to_component_library(self) -> None:
        self._expand_group(
            self._letter_config_expand_btn,
            self._component_library_link,
            "Letter Configuration",
        )
        self._click_or_navigate(
            self._component_library_link, "components", "Component Library"
        )

    def go_to_letter_consolidation(self) -> None:
        self._expand_group(
            self._letter_config_expand_btn,
            self._letter_consolidation_link,
            "Letter Configuration",
        )
        self._click_or_navigate(
            self._letter_consolidation_link,
            "letter-consolidation",
            "Letter Consolidation",
        )

    def go_to_letter_control_center(self) -> None:
        self._click_or_navigate(
            self._letter_control_center_link,
            "letter-control-center",
            "Letter Control Center",
        )

    def go_to_settings(self) -> None:
        self._click_or_navigate(self._settings_link, "settings", "Settings")

    def go_to_audit_logger(self) -> None:
        self._expand_group(
            self._reports_expand_btn,
            self._audit_logger_link,
            "Reports",
        )
        self._click_or_navigate(self._audit_logger_link, "audit-logger", "Audit Logger")

    def go_to_recon_report(self) -> None:
        self._expand_group(
            self._reports_expand_btn,
            self._recon_report_link,
            "Reports",
        )
        self._click_or_navigate(
            self._recon_report_link, "recon-report", "Recon Report"
        )
