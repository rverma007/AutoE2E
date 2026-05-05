"""LetterConsolidationPage — consolidate letter types."""
from __future__ import annotations

from pages.base_page import BasePage


class LetterConsolidationPage(BasePage):
    PATH = "letter-consolidation"

    @property
    def _page_heading(self):
        return self.page.locator(
            "h1, h2, h3", has_text="Letter Consolidation"
        ).first

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        return self.PATH in self.page.url

    def open_direct(self) -> "LetterConsolidationPage":
        self.navigate()
        return self
