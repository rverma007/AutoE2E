"""AskAutoPage — AI assistant page for letter template queries."""
from __future__ import annotations

from pages.base_page import BasePage


class AskAutoPage(BasePage):
    PATH = "ask-auto"

    @property
    def _page_heading(self):
        return self.page.locator("h1, h2", has_text="Ask Auto").first

    @property
    def _subtitle(self):
        # Try both the exact phrase and a partial match in case the copy changes
        return self.page.locator(
            "text=Your AI assistant for letter template queries, "
            "text=AI assistant, "
            "[class*='subtitle'], [class*='description']"
        ).first

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        if self.is_visible(self._subtitle, timeout=2_000):
            return True
        # URL-based fallback: at least confirm we landed on the right route
        return self.PATH in self.page.url

    def open_direct(self) -> "AskAutoPage":
        self.navigate()
        return self
