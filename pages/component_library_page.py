"""ComponentLibraryPage — manage reusable letter components."""
from __future__ import annotations

from pages.base_page import BasePage


class ComponentLibraryPage(BasePage):
    PATH = "components"

    @property
    def _page_heading(self):
        return self.page.locator(
            "h1, h2, h3", has_text="Components Management"
        ).first

    @property
    def _subtitle(self):
        return self.page.locator("text=Manage Component").first

    @property
    def placeholder_tab(self):
        return self.page.locator(
            "[role='tab']:has-text('Placeholder'), "
            "button:has-text('Placeholder'), "
            "a:has-text('Placeholder')"
        ).first

    @property
    def insert_tab(self):
        return self.page.locator(
            "[role='tab']:has-text('Insert'), "
            "button:has-text('Insert'), "
            "a:has-text('Insert')"
        ).first

    @property
    def condition_tab(self):
        return self.page.locator(
            "[role='tab']:has-text('Condition'), "
            "button:has-text('Condition'), "
            "a:has-text('Condition')"
        ).first

    @property
    def block_tab(self):
        return self.page.locator(
            "[role='tab']:has-text('Block'), "
            "button:has-text('Block'), "
            "a:has-text('Block')"
        ).first

    @property
    def upload_sample_input(self):
        return self.page.locator("input[type='file']").first

    @property
    def upload_sample_button(self):
        return self.page.locator(
            "button:has-text('Upload Sample'), "
            "button:has-text('User Sample'), "
            "button:has-text('Upload')"
        ).first

    @property
    def _list_rows(self):
        return self.page.locator(
            "table tbody tr, "
            "[role='rowgroup'] [role='row'], "
            "[class*='list-item']"
        )

    def is_loaded(self, timeout: int = 15_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            return True
        if self.is_visible(self._subtitle, timeout=2_000):
            return True
        return self.PATH in self.page.url

    def open_direct(self) -> "ComponentLibraryPage":
        self.navigate()
        return self

    def click_tab(self, tab_locator, label: str) -> bool:
        if self.is_visible(tab_locator, timeout=5_000):
            self.safe_click(tab_locator, label)
            self.wait_for_idle()
            return True
        return False

    def is_list_populated(self, timeout: int = 10_000) -> bool:
        try:
            self._list_rows.first.wait_for(state="visible", timeout=timeout)
            return self._list_rows.count() > 0
        except Exception:  # noqa: BLE001
            return False

    def row_count(self) -> int:
        return self._list_rows.count()

    def upload_sample_file(self, file_path: str) -> bool:
        if self.is_visible(self.upload_sample_button, timeout=5_000):
            self.safe_click(self.upload_sample_button, "Upload Sample")
            self.page.wait_for_timeout(500)
        try:
            self.upload_sample_input.set_input_files(file_path, timeout=10_000)
            self.wait_for_idle()
            return True
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"File upload not available (custom picker): {exc}")
            return False
