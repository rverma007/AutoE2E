"""LetterControlCenterPage — track the full lifecycle of generated letters."""
from __future__ import annotations

import re
from typing import Optional

from pages.base_page import BasePage


class LetterControlCenterPage(BasePage):
    PATH = "letter-control-center"

    @property
    def _page_heading(self):
        return self.page.locator(
            "h1, h2, h3", has_text="Generated Letters"
        ).first

    @property
    def _subtitle(self):
        return self.page.locator(
            "text=Track the full lifecycle of generated letters"
        ).first

    @property
    def filter_button(self):
        return self.page.locator(
            "button[aria-label*='filter' i], "
            "[data-testid='filter-btn'], "
            "button:has-text('Filter')"
        ).first

    @property
    def xml_upload_input(self):
        return self.page.locator("input[type='file']").first

    @property
    def xml_upload_button(self):
        return self.page.locator(
            "button:has-text('Upload XML'), "
            "button:has-text('Generate Letter'), "
            "button:has-text('Upload'), "
            "[data-testid='xml-upload-btn']"
        ).first

    @property
    def generate_button(self):
        return self.page.locator(
            "button:has-text('Generate'), "
            "[data-testid='generate-btn']"
        ).first

    @property
    def _rows(self):
        return self.page.locator("table tbody tr")

    @property
    def pdf_download_button(self):
        return self.page.locator(
            "button[aria-label*='PDF' i], "
            "button:has-text('PDF'), "
            "[data-testid='pdf-download']"
        ).first

    @property
    def docx_download_button(self):
        return self.page.locator(
            "button[aria-label*='DOCX' i], "
            "button:has-text('DOCX'), "
            "[data-testid='docx-download']"
        ).first

    @property
    def bulk_download_button(self):
        return self.page.locator(
            "button:has-text('Bulk Download'), "
            "button[aria-label*='bulk' i], "
            "[data-testid='bulk-download']"
        ).first

    @property
    def validation_summary_link(self):
        return self.page.locator(
            "button:has-text('Validation Summary'), "
            "a:has-text('Validation Summary'), "
            "[role='tab']:has-text('Validation')"
        ).first

    @property
    def _footer_text(self):
        return self.page.locator("text=/Showing.*results of/").first

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        if self.is_visible(self._subtitle, timeout=2_000):
            return True
        return self.PATH in self.page.url

    def open_direct(self) -> "LetterControlCenterPage":
        self.navigate()
        return self

    def row_count(self) -> int:
        return self._rows.count()

    def is_filters_section_visible(self, timeout: int = 10_000) -> bool:
        return self.is_visible(self.filter_button, timeout=timeout)

    def upload_xml_and_generate(self, file_path: str) -> None:
        if self.is_visible(self.xml_upload_button, timeout=5_000):
            self.safe_click(self.xml_upload_button, "Upload XML button")
            self.page.wait_for_timeout(500)
        self.xml_upload_input.set_input_files(file_path)
        self.wait_for_idle()
        if self.is_visible(self.generate_button, timeout=8_000):
            self.safe_click(self.generate_button, "Generate")
        self.wait_for_idle()

    def first_row_status(self, timeout: int = 5_000) -> str:
        candidates = [
            "table tbody tr:first-child [class*='status']",
            "table tbody tr:first-child [class*='badge']",
            "table tbody tr:first-child [class*='chip']",
            "table tbody tr:first-child td:nth-child(3)",
            "table tbody tr:first-child td:last-child",
        ]
        for sel in candidates:
            loc = self.page.locator(sel).first
            if self.is_visible(loc, timeout=timeout):
                text = self.text_of(loc).strip()
                if text:
                    return text
        return ""

    def wait_for_status(
        self, expected: str, timeout: int = 120_000, poll: int = 3_000
    ) -> bool:
        import time
        deadline = time.monotonic() + timeout / 1_000
        while time.monotonic() < deadline:
            if self.first_row_status().lower() == expected.lower():
                return True
            self.page.wait_for_timeout(poll)
            self.page.reload()
            self.is_loaded()
        return False

    def download_pdf(self):
        try:
            with self.page.expect_download(timeout=20_000) as dl:
                self.safe_click(self.pdf_download_button, "PDF download")
            return dl.value
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"PDF download not captured: {exc}")
            return None

    def download_docx(self):
        try:
            with self.page.expect_download(timeout=20_000) as dl:
                self.safe_click(self.docx_download_button, "DOCX download")
            return dl.value
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"DOCX download not captured: {exc}")
            return None

    def total_records(self) -> Optional[int]:
        if not self.is_visible(self._footer_text, timeout=5_000):
            return None
        text = self._footer_text.inner_text()
        match = re.search(r"results of\s+([\d,]+)", text)
        if not match:
            return None
        return int(match.group(1).replace(",", ""))
