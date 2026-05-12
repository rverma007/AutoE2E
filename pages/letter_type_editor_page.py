"""LetterTypeEditorPage — rich-text editor for letter type templates."""
from __future__ import annotations

from pages.base_page import BasePage


class LetterTypeEditorPage(BasePage):
    PATH = "letter-type"  # reached from a detail page via the Edit button

    @property
    def _editor_container(self):
        return self.page.locator(
            ".ql-editor, "
            ".ProseMirror, "
            ".CodeMirror-scroll, "
            "[class*='editor-container'], "
            "[class*='letter-editor'], "
            "[class*='EditorContainer'], "
            "[class*='RichText'], "
            "[contenteditable='true'], "
            "[role='textbox'], "
            "[data-testid='letter-editor']"
        ).first

    @property
    def reset_button(self):
        return self.page.locator(
            "button:has-text('Reset'), "
            "[data-testid='reset-btn']"
        ).first

    @property
    def diff_view_button(self):
        return self.page.locator(
            "button:has-text('Diff View'), "
            "button:has-text('Diff'), "
            "button:has-text('Compare'), "
            "[data-testid='diff-view-btn']"
        ).first

    @property
    def submit_for_approval_button(self):
        return self.page.locator(
            "button:has-text('Submit for Approval'), "
            "button:has-text('Submit'), "
            "[data-testid='submit-approval-btn']"
        ).first

    @property
    def generate_test_letter_button(self):
        return self.page.locator(
            "button:has-text('Generate Test Letter'), "
            "button:has-text('Test Letter')"
        ).first

    @property
    def letter_preview(self):
        return self.page.locator(
            "[class*='preview'], "
            "[class*='letter-preview'], "
            "[data-testid='letter-preview']"
        ).first

    @property
    def _diff_container(self):
        return self.page.locator(
            "[class*='diff'], "
            "[class*='compare'], "
            "ins, del, "
            "[class*='added'], [class*='removed']"
        ).first

    def is_loaded(self, timeout: int = 20_000) -> bool:
        if self.is_visible(self._editor_container, timeout=timeout):
            return True
        url = self.page.url
        return "edit" in url or "editor" in url or self.PATH in url

    def click_reset(self) -> None:
        self.safe_click(self.reset_button, "Reset")
        self.wait_for_idle()

    def click_diff_view(self) -> None:
        self.safe_click(self.diff_view_button, "Diff View")
        self.wait_for_idle()

    def is_diff_view_visible(self, timeout: int = 10_000) -> bool:
        return self.is_visible(self._diff_container, timeout=timeout)

    def is_preview_visible(self, timeout: int = 10_000) -> bool:
        return self.is_visible(self.letter_preview, timeout=timeout)

    def click_submit_for_approval(self) -> None:
        self.safe_click(self.submit_for_approval_button, "Submit for Approval")
        self.wait_for_idle()

    def is_submit_button_visible(self, timeout: int = 8_000) -> bool:
        return self.is_visible(self.submit_for_approval_button, timeout=timeout)
