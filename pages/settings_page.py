"""SettingsPage — global configuration for the Correspondence app."""
from __future__ import annotations

from pages.base_page import BasePage


class SettingsPage(BasePage):
    PATH = "settings"

    @property
    def _page_heading(self):
        return self.page.locator("h1, h2, h3", has_text="Settings").first

    @property
    def _global_config_heading(self):
        return self.page.locator(
            "h1, h2, h3", has_text="Global Configuration"
        ).first

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        if self.is_visible(self._global_config_heading, timeout=2_000):
            return True
        return self.PATH in self.page.url

    def open_direct(self) -> "SettingsPage":
        self.navigate()
        return self
