"""SettingsPage — global and business-unit configuration for the Correspondence app."""
from __future__ import annotations

from pages.base_page import BasePage


class SettingsPage(BasePage):
    PATH = "settings"

    # ── Headings ─────────────────────────────────────────────────────────────

    @property
    def _page_heading(self):
        return self.page.locator("h1, h2, h3", has_text="Settings").first

    @property
    def _global_config_heading(self):
        return self.page.locator("h1, h2, h3, h4", has_text="Global Configuration").first

    @property
    def _bu_config_heading(self):
        return self.page.locator("h1, h2, h3, h4", has_text="Business Unit Configuration").first

    # ── Tabs ──────────────────────────────────────────────────────────────────

    @property
    def global_config_tab(self):
        return self.page.locator(
            "[role='tab']:has-text('Global Config'), "
            "button:has-text('Global Config'), "
            "a:has-text('Global Config')"
        ).first

    @property
    def bu_config_tab(self):
        return self.page.locator(
            "[role='tab']:has-text('Business Unit Config'), "
            "button:has-text('Business Unit Config'), "
            "a:has-text('Business Unit Config')"
        ).first

    # ── Global Config elements ────────────────────────────────────────────────

    @property
    def ingestion_model_dropdown(self):
        return self.page.locator(
            "text=Select the Ingestion Model"
        ).locator("xpath=../..").locator("[role='combobox'], select").first

    @property
    def enable_ask_auto_toggle(self):
        return self.page.locator(
            "text=Enable AskAuto"
        ).locator("xpath=..").locator("input[type='checkbox'], [role='switch']").first

    # ── Save button ───────────────────────────────────────────────────────────

    @property
    def save_settings_button(self):
        return self.page.get_by_role("button", name="Save Settings").first

    @property
    def _success_toast(self):
        return self.page.locator(
            "[class*='toast'], [class*='snackbar'], [class*='Snackbar'], "
            "[role='alert'], "
            "text=saved, text=Saved, text=success, text=Success"
        ).first

    # ── BU Config — left panel (BU list) ─────────────────────────────────────

    @property
    def bu_list_items(self):
        """All BU names in the left panel list."""
        return self.page.locator(
            "[class*='list'] li, [class*='List'] li, "
            "[class*='sidebar'] li, [class*='panel'] li, "
            "ul li:has-text('Department'), ul li:has-text('BU'), ul li:has-text('Test'), "
            "ul li:has-text('ANG'), ul li:has-text('PNF')"
        )

    @property
    def first_bu_item(self):
        """First selectable BU in the left panel."""
        return self.page.locator(
            "[class*='list'] li:first-child, "
            "[class*='List'] li:first-child, "
            "ul li:first-child"
        ).first

    # ── BU Config — right panel (detail fields) ───────────────────────────────

    def _toggle_for_label(self, label_text: str):
        """Return the toggle input/switch next to a given label text."""
        return self.page.locator(
            f"text={label_text}"
        ).locator("xpath=..").locator(
            "input[type='checkbox'], [role='switch'], [class*='toggle'], [class*='Toggle']"
        ).first

    @property
    def auto_correct_address_letter_toggle(self):
        return self._toggle_for_label("Auto Correct Address (Letter)")

    @property
    def inserts_margin_toggle(self):
        return self._toggle_for_label("Inserts Margin")

    @property
    def margin_correction_toggle(self):
        return self._toggle_for_label("Margin Correction")

    @property
    def auto_correct_address_letter_type_toggle(self):
        return self._toggle_for_label("Auto Correct Address (LetterType)")

    # ── Load checks ───────────────────────────────────────────────────────────

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        if self.is_visible(self._global_config_heading, timeout=2_000):
            return True
        return self.PATH in self.page.url

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

    def open_direct(self) -> "SettingsPage":
        self.navigate()
        return self

    # ── Actions ───────────────────────────────────────────────────────────────

    def click_global_config_tab(self) -> None:
        if self.is_visible(self.global_config_tab, timeout=5_000):
            self.safe_click(self.global_config_tab, "Global Config tab")
            self.wait_for_idle()

    def click_bu_config_tab(self) -> None:
        if self.is_visible(self.bu_config_tab, timeout=5_000):
            self.safe_click(self.bu_config_tab, "Business Unit Config tab")
            self.wait_for_idle()
            self.page.wait_for_timeout(1_000)

    def click_save_settings(self) -> bool:
        """Click Save Settings and wait for the success toast. Returns True if toast appears."""
        self.safe_click(self.save_settings_button, "Save Settings")
        return self.is_visible(self._success_toast, timeout=8_000)

    def is_toggle_checked(self, toggle_locator) -> bool:
        """Return True if the toggle is currently ON."""
        try:
            el = toggle_locator
            # Try input[type=checkbox] checked property
            checked = el.evaluate("el => el.checked")
            if isinstance(checked, bool):
                return checked
        except Exception:
            pass
        try:
            # MUI Switch: aria-checked on the root span
            return toggle_locator.get_attribute("aria-checked") == "true"
        except Exception:
            return False

    def click_toggle(self, toggle_locator, label: str = "toggle") -> None:
        """Click a toggle switch, using force if needed."""
        try:
            toggle_locator.click(timeout=5_000)
        except Exception:
            toggle_locator.click(force=True, timeout=5_000)
        self.page.wait_for_timeout(500)

    def select_first_bu(self) -> str:
        """Click the first BU in the left panel list. Returns the BU name."""
        item = self.first_bu_item
        if not self.is_visible(item, timeout=5_000):
            return ""
        name = self.text_of(item).strip()
        item.click()
        self.wait_for_idle()
        return name
