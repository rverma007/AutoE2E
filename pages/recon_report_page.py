"""ReconReportPage — template migration reconciliation report."""
from __future__ import annotations

from pages.base_page import BasePage


class ReconReportPage(BasePage):
    PATH = "recon-report"

    @property
    def _page_heading(self):
        return self.page.locator(
            "h1, h2, h3", has_text="Recon Report"
        ).first

    @property
    def _subtitle(self):
        return self.page.locator(
            "text=Recon Report that records all template migration"
        ).first

    @property
    def _table_rows(self):
        return self.page.locator("table tbody tr")

    @property
    def download_button(self):
        return self.page.locator(
            "button:has-text('Report'), "
            "button:has-text('Download'), "
            "button:has-text('Export'), "
            "button[aria-label*='download' i]"
        ).first

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        if self.is_visible(self._subtitle, timeout=2_000):
            return True
        return self.PATH in self.page.url

    def open_direct(self) -> "ReconReportPage":
        self.navigate()
        return self

    def row_count(self) -> int:
        return self._table_rows.count()

    def is_list_visible(self, timeout: int = 10_000) -> bool:
        table = self.page.locator("table").first
        empty = self.page.locator(
            "text=No records, text=No data, text=No results"
        ).first
        return (
            self.is_visible(table, timeout=timeout)
            or self.is_visible(empty, timeout=2_000)
        )

    def download_report(self):
        try:
            with self.page.expect_download(timeout=20_000) as dl:
                self.safe_click(self.download_button, "Download Recon Report")
            return dl.value
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"Recon report download not captured: {exc}")
            return None
