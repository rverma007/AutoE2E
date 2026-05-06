"""LetterImportExportPage — import/export letter type configurations."""
from __future__ import annotations

from pages.base_page import BasePage


class LetterImportExportPage(BasePage):
    PATH = "import-export"

    @property
    def _page_heading(self):
        return self.page.locator(
            "h1, h2, h3",
            has_text="Import"
        ).first

    @property
    def _alt_heading(self):
        return self.page.locator(
            "h1, h2, h3",
            has_text="Export"
        ).first

    @property
    def export_button(self):
        return self.page.locator(
            "button:has-text('Export'), "
            "[data-testid='export-btn']"
        ).first

    @property
    def import_zip_input(self):
        return self.page.locator("input[type='file']").first

    @property
    def import_confirm_button(self):
        return self.page.locator(
            "button:has-text('Import'), "
            "button[type='submit']:has-text('Import')"
        ).first

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        if self.is_visible(self._alt_heading, timeout=2_000):
            return True
        return self.PATH in self.page.url or "import" in self.page.url

    def open_direct(self) -> "LetterImportExportPage":
        self.navigate()
        return self

    def is_export_button_visible(self, timeout: int = 8_000) -> bool:
        return self.is_visible(self.export_button, timeout=timeout)

    def click_export(self):
        """Click Export and return a Playwright Download object, or None."""
        try:
            with self.page.expect_download(timeout=20_000) as dl_info:
                self.safe_click(self.export_button, "Export")
            dl = dl_info.value
            self.log.info(f"Export download: {dl.suggested_filename}")
            return dl
        except Exception as exc:
            self.log.warning(f"Export download not captured: {exc}")
            return None

    def upload_zip(self, file_path: str) -> None:
        self.import_zip_input.set_input_files(file_path)
        self.wait_for_idle()

    def click_import(self) -> None:
        self.safe_click(self.import_confirm_button, "Import")
        self.wait_for_idle()
