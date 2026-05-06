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
            "h1, h2, h3, h4", has_text="Global Configuration"
        ).first

    @property
    def _bu_config_heading(self):
        return self.page.locator(
            "h1, h2, h3, h4", has_text="Business Unit"
        ).first

    @property
    def global_config_tab(self):
        return self.page.locator(
            "[role='tab']:has-text('Global'), "
            "button:has-text('Global Configuration'), "
            "a:has-text('Global')"
        ).first

    @property
    def bu_config_tab(self):
        return self.page.locator(
            "[role='tab']:has-text('Business Unit'), "
            "button:has-text('Business Unit'), "
            "a:has-text('Business Unit')"
        ).first

    @property
    def save_settings_button(self):
        return self.page.locator(
            "button:has-text('Save Settings'), "
            "button:has-text('Save'), "
            "button[type='submit']"
        ).first

    @property
    def bu_select_dropdown(self):
        return self.page.locator(
            "select[class*='business'], "
            "[data-testid='bu-select'], "
            "select, [role='combobox']"
        ).first

    @property
    def _success_toast(self):
        return self.page.locator(
            "[class*='toast'], [class*='snackbar'], "
            "[role='alert']:has-text('success'), "
            "text=saved successfully, text=Settings saved"
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

    def is_global_config_visible(self, timeout: int = 10_000) -> bool:
        if self.is_visible(self._global_config_heading, timeout=timeout):
            return True
        return self.is_visible(self.global_config_tab, timeout=2_000)

    def is_bu_config_visible(self, timeout: int = 10_000) -> bool:
        if self.is_visible(self._bu_config_heading, timeout=timeout):
            return True
        return self.is_visible(self.bu_config_tab, timeout=2_000)

    def is_save_button_visible(self, timeout: int = 5_000) -> bool:
        return self.is_visible(self.save_settings_button, timeout=timeout)

    def click_save_settings(self) -> bool:
        """Click Save Settings and return True if a success signal is observed."""
        self.safe_click(self.save_settings_button, "Save Settings")
        self.wait_for_idle()
        return self.is_visible(self._success_toast, timeout=5_000)

    def click_global_config_tab(self) -> None:
        if self.is_visible(self.global_config_tab, timeout=5_000):
            self.safe_click(self.global_config_tab, "Global Config tab")
            self.wait_for_idle()

    def click_bu_config_tab(self) -> None:
        if self.is_visible(self.bu_config_tab, timeout=5_000):
            self.safe_click(self.bu_config_tab, "Business Unit Config tab")
            self.wait_for_idle()
