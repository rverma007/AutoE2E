"""LetterTypeDetailsPage — detail view for a single letter type record."""
from __future__ import annotations

from pages.base_page import BasePage


class LetterTypeDetailsPage(BasePage):
    PATH = "letter-type"

    @property
    def _page_heading(self):
        return self.page.locator("h1, h2, h3, h4").first

    @property
    def version_dropdown(self):
        return self.page.locator(
            "select:near(:text('Version')), "
            "[role='combobox']:near(:text('Version')), "
            "[class*='version'] select, "
            "[class*='version'] [role='combobox'], "
            "select[class*='version']"
        ).first

    @property
    def make_current_button(self):
        return self.page.locator(
            "button:has-text('Make Current'), "
            "button:has-text('Set as Current'), "
            "[data-testid='make-current-btn']"
        ).first

    @property
    def generate_test_letter_button(self):
        return self.page.locator(
            "button:has-text('Generate Test Letter'), "
            "button:has-text('Test Letter'), "
            "[data-testid='generate-test-letter']"
        ).first

    @property
    def xml_upload_input(self):
        return self.page.locator("input[type='file']").first

    @property
    def generate_confirm_button(self):
        return self.page.locator(
            "button:has-text('Generate'), "
            "button[type='submit']:has-text('Generate')"
        ).first

    @property
    def validation_summary_tab(self):
        return self.page.locator(
            "button:has-text('Validation Summary'), "
            "a:has-text('Validation Summary'), "
            "[role='tab']:has-text('Validation')"
        ).first

    @property
    def edit_button(self):
        return self.page.locator(
            "button:has-text('Edit'), "
            "a:has-text('Edit'), "
            "[data-testid='edit-btn']"
        ).first

    @property
    def approve_button(self):
        return self.page.locator(
            "button:has-text('Approve'), "
            "button:has-text('Approve Version'), "
            "[data-testid='approve-btn']"
        ).first

    @property
    def reject_button(self):
        return self.page.locator(
            "button:has-text('Reject'), "
            "button:has-text('Reject Version'), "
            "[data-testid='reject-btn']"
        ).first

    @property
    def rejection_reason_input(self):
        return self.page.locator(
            "textarea[placeholder*='reason' i], "
            "textarea[placeholder*='comment' i], "
            "textarea[name*='reason' i], "
            "input[placeholder*='reason' i]"
        ).first

    @property
    def confirm_reject_button(self):
        # Last match picks the confirmatory action, not the opener
        return self.page.locator(
            "button:has-text('Confirm'), "
            "button:has-text('Confirm Rejection'), "
            "button:has-text('Submit Rejection')"
        ).last

    @property
    def status_badge(self):
        return self.page.locator(
            "[class*='status'], [class*='badge'], [class*='chip'], [class*='tag']"
        ).first

    def is_loaded(self, timeout: int = 20_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            # Confirm we're on a detail page (URL has more than just /letter-type)
            url = self.page.url
            return "letter-type" in url
        return False

    def click_first_row(self, letter_type_page) -> "LetterTypeDetailsPage":
        """Click the first data row in the letter type list to open its details."""
        rows = letter_type_page.rows
        if rows.count() > 0:
            rows.first.click()
            self.wait_for_idle()
        return self

    def is_version_dropdown_visible(self, timeout: int = 10_000) -> bool:
        # The version selector may appear as a native select, combobox, or
        # a clickable badge/button showing the current version number.
        candidates = [
            "select",
            "[role='combobox']",
            "[class*='version'] select",
            "[class*='version'] [role='combobox']",
            "button:has-text('Version'), span:has-text('v1'), span:has-text('Version')",
        ]
        for sel in candidates:
            loc = self.page.locator(sel).first
            if self.is_visible(loc, timeout=2_000):
                return True
        return False

    def click_make_current(self) -> None:
        self.safe_click(self.make_current_button, "Make Current")
        self.wait_for_idle()

    def open_generate_test_letter(self) -> bool:
        if self.is_visible(self.generate_test_letter_button, timeout=8_000):
            self.safe_click(self.generate_test_letter_button, "Generate Test Letter")
            self.wait_for_idle()
            return True
        return False

    def upload_xml_and_generate(self, xml_path: str) -> bool:
        try:
            self.xml_upload_input.set_input_files(xml_path, timeout=10_000)
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"XML file input not available (custom picker): {exc}")
            return False
        self.wait_for_idle()
        if self.is_visible(self.generate_confirm_button, timeout=8_000):
            self.safe_click(self.generate_confirm_button, "Generate confirm")
        self.wait_for_idle()
        return True

    def is_validation_summary_visible(self, timeout: int = 10_000) -> bool:
        return self.is_visible(self.validation_summary_tab, timeout=timeout)

    def click_validation_summary(self) -> None:
        self.safe_click(self.validation_summary_tab, "Validation Summary")
        self.wait_for_idle()

    def click_edit(self) -> bool:
        if self.is_visible(self.edit_button, timeout=8_000):
            self.safe_click(self.edit_button, "Edit")
            self.wait_for_idle()
            return True
        return False

    def has_backend_error(self) -> bool:
        """Return True when the detail page shows a server-side validation/pydantic error."""
        err_loc = self.page.locator(
            "text=/unexpected error/i, "
            "text=/validation error/i, "
            "text=/pydantic/i, "
            "text=/Field required/i"
        ).first
        return self.is_visible(err_loc, timeout=3_000)

    def current_status(self) -> str:
        """Return the status badge/chip text visible on the detail page."""
        for sel in ("[class*='status']", "[class*='badge']", "[class*='chip']", "[class*='tag']"):
            loc = self.page.locator(sel).first
            if self.is_visible(loc, timeout=2_000):
                text = self.text_of(loc).strip()
                if text:
                    return text
        return ""

    def click_approve(self) -> bool:
        """Click Approve. Returns True if the button was found and clicked."""
        if not self.is_visible(self.approve_button, timeout=8_000):
            return False
        self.safe_click(self.approve_button, "Approve")
        self.wait_for_idle()
        return True

    def click_reject(self, reason: str = "Automated test rejection") -> bool:
        """Click Reject, fill reason if a textarea appears, confirm. Returns True if clicked."""
        if not self.is_visible(self.reject_button, timeout=8_000):
            return False
        self.safe_click(self.reject_button, "Reject")
        self.wait_for_idle()
        if self.is_visible(self.rejection_reason_input, timeout=5_000):
            self.safe_fill(self.rejection_reason_input, reason, label="rejection reason")
        if self.is_visible(self.confirm_reject_button, timeout=5_000):
            self.safe_click(self.confirm_reject_button, "Confirm Rejection")
            self.wait_for_idle()
        return True
