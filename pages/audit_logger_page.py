"""AuditLoggerPage — track system activities for compliance and troubleshooting."""
from __future__ import annotations

import re
from typing import Optional

from pages.base_page import BasePage


class AuditLoggerPage(BasePage):
    PATH = "audit-logger"

    @property
    def _page_heading(self):
        return self.page.locator("h1, h2, h3", has_text="Audit Logger").first

    @property
    def _subtitle(self):
        return self.page.locator(
            "text=Track, search, and review key system activities"
        ).first

    @property
    def search_input(self):
        return self.page.locator(
            "input[placeholder*='Search' i], "
            "input[type='search'], "
            "[data-testid='audit-search']"
        ).first

    @property
    def date_from_input(self):
        return self.page.locator(
            "input[placeholder*='From' i], "
            "input[type='date']:first-of-type, "
            "[data-testid='date-from']"
        ).first

    @property
    def date_to_input(self):
        return self.page.locator(
            "input[placeholder*='To' i], "
            "input[type='date']:last-of-type, "
            "[data-testid='date-to']"
        ).first

    @property
    def apply_filter_button(self):
        return self.page.locator(
            "button:has-text('Apply'), "
            "button:has-text('Search'), "
            "button[type='submit']"
        ).first

    @property
    def download_button(self):
        return self.page.get_by_role("button", name=re.compile(r"^Report$", re.IGNORECASE))

    @property
    def rows_per_page_select(self):
        return self.page.locator(
            "select[class*='per-page'], "
            "select[class*='rows'], "
            "[data-testid='rows-per-page']"
        ).first

    @property
    def next_page_button(self):
        return self.page.locator(
            "button[aria-label*='next' i], "
            "button:has-text('Next'), "
            "[data-testid='next-page']"
        ).first

    @property
    def _table_rows(self):
        return self.page.locator("table tbody tr")

    @property
    def _footer_text(self):
        return self.page.locator("text=/Showing.*results of/").first

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        if self.is_visible(self._subtitle, timeout=2_000):
            return True
        return self.PATH in self.page.url

    def open_direct(self) -> "AuditLoggerPage":
        self.navigate()
        return self

    def row_count(self) -> int:
        return self._table_rows.count()

    def get_first_row_texts(self) -> list:
        cells = self.page.locator("table tbody tr:first-child td")
        return [self.text_of(cells.nth(i)) for i in range(cells.count())]

    def search(self, query: str) -> None:
        self.safe_fill(self.search_input, query, label="Audit search")
        try:
            self.page.wait_for_load_state("networkidle", timeout=5_000)
        except Exception:  # noqa: BLE001
            pass

    def apply_date_filter(self, date_from: str, date_to: str) -> None:
        if self.is_visible(self.date_from_input, timeout=5_000):
            self.safe_fill(self.date_from_input, date_from, label="date from")
        if self.is_visible(self.date_to_input, timeout=5_000):
            self.safe_fill(self.date_to_input, date_to, label="date to")
        if self.is_visible(self.apply_filter_button, timeout=3_000):
            self.safe_click(self.apply_filter_button, "Apply filter")
        self.wait_for_idle()

    def download_report(self):
        try:
            with self.page.expect_download(timeout=20_000) as dl:
                self.safe_click(self.download_button, "Download report")
            return dl.value
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"Audit report download not captured: {exc}")
            return None

    def total_records(self) -> Optional[int]:
        if not self.is_visible(self._footer_text, timeout=5_000):
            return None
        text = self._footer_text.inner_text()
        match = re.search(r"results of\s+([\d,]+)", text)
        if not match:
            return None
        return int(match.group(1).replace(",", ""))

    def change_rows_per_page(self, value: str) -> bool:
        if self.is_visible(self.rows_per_page_select, timeout=5_000):
            self.rows_per_page_select.select_option(value)
            self.wait_for_idle()
            return True
        return False

    def go_to_next_page(self) -> bool:
        btn = self.next_page_button
        if self.is_visible(btn, timeout=5_000) and not btn.is_disabled():
            btn.click()
            self.wait_for_idle()
            return True
        return False
