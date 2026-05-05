"""LetterControlCenterPage — track the full lifecycle of generated letters."""
from __future__ import annotations

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

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        if self.is_visible(self._subtitle, timeout=2_000):
            return True
        return self.PATH in self.page.url

    def open_direct(self) -> "LetterControlCenterPage":
        self.navigate()
        return self
