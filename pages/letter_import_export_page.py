"""LetterImportExportPage — import/export letter type configurations."""
from __future__ import annotations

import re

from pages.base_page import BasePage


class LetterImportExportPage(BasePage):
    PATH = "import-export"

    @property
    def _page_heading(self):
        return self.page.locator("h1, h2, h3", has_text="Import").first

    @property
    def _alt_heading(self):
        return self.page.locator("h1, h2, h3", has_text="Export").first

    # "Export Letter Type (N)" — active only when rows are selected
    @property
    def export_button(self):
        return self.page.locator(
            "button:has-text('Export Letter Type'), "
            "button:has-text('Export All'), "
            "button:has-text('Export ZIP'), "
            "button:has-text('Export'), "
            "button:has-text('Download'), "
            "[data-testid='export-btn'], "
            "[data-testid*='export' i]"
        ).first

    @property
    def first_row_checkbox(self):
        return self.page.locator(
            "table tbody tr:first-child input[type='checkbox'], "
            "table tbody tr:first-child [role='checkbox']"
        ).first

    @property
    def import_zip_input(self):
        return self.page.locator("input[type='file']").first

    @property
    def import_confirm_button(self):
        return self.page.locator(
            "button:has-text('Import Letter Type'), "
            "button:has-text('Import'), "
            "button[type='submit']:has-text('Import')"
        ).first

    # ---------------------------------------------------------------- Actions

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        if self.is_visible(self._alt_heading, timeout=2_000):
            return True
        return self.PATH in self.page.url or "import" in self.page.url

    def open_direct(self) -> "LetterImportExportPage":
        self.navigate()
        return self

    def select_first_row(self) -> bool:
        """Click the checkbox on the first letter type row to enable Export."""
        cb = self.first_row_checkbox
        if not self.is_visible(cb, timeout=10_000):
            return False
        cb.click()
        self.page.wait_for_timeout(500)
        return True

    def is_export_button_visible(self, timeout: int = 8_000) -> bool:
        return self.is_visible(self.export_button, timeout=timeout)

    def click_export(self) -> None:
        """Click the Export Letter Type button."""
        self.safe_click(self.export_button, "Export Letter Type")

    def is_export_complete(self, timeout: int = 30_000) -> bool:
        """Wait for the 'Export Complete' success panel to appear."""
        try:
            self.page.wait_for_selector(
                "text=Export Complete",
                state="visible", timeout=timeout
            )
            return True
        except Exception:
            return False

    def get_export_file_path(self) -> str:
        """Extract the server-side file path from the export success notification."""
        # Try locating the path text directly
        for sel in [
            "text=/\\/mnt\\/netapp/",
            "text=/manual_imports/",
            "[class*='path']",
            "[class*='notification'] p",
        ]:
            try:
                loc = self.page.locator(sel).first
                if self.is_visible(loc, timeout=3_000):
                    return self.text_of(loc).strip()
            except Exception:
                pass
        # Fallback: scan full page text for the path
        try:
            body = self.page.evaluate("() => document.body.innerText") or ""
            m = re.search(r"/mnt/netapp[^\s\n]+", body)
            if m:
                return m.group(0)
        except Exception:
            pass
        return ""

    def upload_zip(self, file_path: str) -> None:
        self.import_zip_input.set_input_files(file_path)
        self.wait_for_idle()

    def click_import(self) -> None:
        self.safe_click(self.import_confirm_button, "Import")
        self.wait_for_idle()
