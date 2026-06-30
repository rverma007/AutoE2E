"""LetterTypeDetailsPage — detail view for a single letter type record."""
from __future__ import annotations

from pages.base_page import BasePage


class LetterTypeDetailsPage(BasePage):
    PATH = "letter-type"

    # Text of the last success/snackbar toast captured after approve/reject.
    last_toast: str = ""

    @property
    def _page_heading(self):
        return self.page.locator("h1, h2, h3, h4").first

    @property
    def version_dropdown(self):
        return self.page.locator(
            "select:near(:text('Version')), "
            "[role='combobox']:near(:text('Version')), "
            "[class*='version'] select, "
            "[class*='version'] [role='combobox'], "
            "select[class*='version']"
        ).first

    @property
    def make_current_button(self):
        return self.page.locator(
            "button:has-text('Make Current'), "
            "button:has-text('Set as Current'), "
            "[data-testid='make-current-btn']"
        ).first

    @property
    def generate_test_letter_button(self):
        return self.page.locator(
            "button:has-text('Generate Test Letter'), "
            "button:has-text('Test Letter'), "
            "[data-testid='generate-test-letter']"
        ).first

    @property
    def xml_upload_input(self):
        return self.page.locator("input[type='file']").first

    @property
    def generate_confirm_button(self):
        return self.page.locator(
            "button:has-text('Generate'), "
            "button[type='submit']:has-text('Generate')"
        ).first

    @property
    def validation_summary_tab(self):
        return self.page.locator(
            "button:has-text('Validation Summary'), "
            "a:has-text('Validation Summary'), "
            "[role='tab']:has-text('Validation')"
        ).first

    @property
    def edit_button(self):
        return self.page.locator(
            "button:has-text('Edit'), "
            "a:has-text('Edit'), "
            "[data-testid='edit-btn']"
        ).first

    @property
    def approve_button(self):
        return self.page.locator(
            "button:has-text('Approve'), "
            "button:has-text('Approve Version'), "
            "[data-testid='approve-btn']"
        ).first

    @property
    def reject_button(self):
        return self.page.locator(
            "button:has-text('Reject'), "
            "button:has-text('Reject Version'), "
            "[data-testid='reject-btn']"
        ).first

    @property
    def rejection_reason_input(self):
        return self.page.locator(
            "textarea[placeholder*='reason' i], "
            "textarea[placeholder*='comment' i], "
            "textarea[name*='reason' i], "
            "input[placeholder*='reason' i]"
        ).first

    @property
    def confirm_approve_button(self):
        # The 'Yes' button on the "Approval Confirmation" dialog. Scoped to the
        # dialog so we never match an unrelated button; .last picks the most
        # recently opened modal.
        return self.page.locator(
            "[role='dialog'] button:has-text('Yes'), "
            "[role='dialog'] button:has-text('Confirm'), "
            "button:has-text('Confirm Approval')"
        ).last

    @property
    def confirm_reject_button(self):
        # The "Leave Feedback" dialog confirms a rejection with a 'Submit'
        # button (not 'Confirm'). Scope to the dialog and take the last match.
        return self.page.locator(
            "[role='dialog'] button:has-text('Submit'), "
            "[role='dialog'] button:has-text('Confirm'), "
            "button:has-text('Confirm Rejection'), "
            "button:has-text('Submit Rejection')"
        ).last

    @property
    def status_badge(self):
        return self.page.locator(
            "[class*='status'], [class*='badge'], [class*='chip'], [class*='tag']"
        ).first

    def is_loaded(self, timeout: int = 20_000) -> bool:
        if self.is_visible(self._page_heading, timeout=timeout):
            # Confirm we're on a detail page (URL has more than just /letter-type)
            url = self.page.url
            return "letter-type" in url
        return False

    def click_first_row(self, letter_type_page) -> "LetterTypeDetailsPage":
        """Click the first data row in the letter type list to open its details."""
        rows = letter_type_page.rows
        if rows.count() > 0:
            rows.first.click()
            self.wait_for_idle()
        return self

    def is_version_dropdown_visible(self, timeout: int = 10_000) -> bool:
        # The version selector may appear as a native select, combobox, or
        # a clickable badge/button showing the current version number.
        candidates = [
            "select",
            "[role='combobox']",
            "[class*='version'] select",
            "[class*='version'] [role='combobox']",
            "button:has-text('Version'), span:has-text('v1'), span:has-text('Version')",
        ]
        for sel in candidates:
            loc = self.page.locator(sel).first
            if self.is_visible(loc, timeout=2_000):
                return True
        return False

    def click_make_current(self) -> None:
        self.safe_click(self.make_current_button, "Make Current")
        self.wait_for_idle()

    def open_generate_test_letter(self) -> bool:
        if self.is_visible(self.generate_test_letter_button, timeout=8_000):
            self.safe_click(self.generate_test_letter_button, "Generate Test Letter")
            self.wait_for_idle()
            return True
        return False

    def upload_xml_and_generate(self, xml_path: str) -> bool:
        try:
            self.xml_upload_input.set_input_files(xml_path, timeout=10_000)
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"XML file input not available (custom picker): {exc}")
            return False
        self.wait_for_idle()
        if self.is_visible(self.generate_confirm_button, timeout=8_000):
            self.safe_click(self.generate_confirm_button, "Generate confirm")
        self.wait_for_idle()
        return True

    def is_validation_summary_visible(self, timeout: int = 10_000) -> bool:
        return self.is_visible(self.validation_summary_tab, timeout=timeout)

    def click_validation_summary(self) -> None:
        self.safe_click(self.validation_summary_tab, "Validation Summary")
        self.wait_for_idle()

    def click_edit(self) -> bool:
        if self.is_visible(self.edit_button, timeout=8_000):
            self.safe_click(self.edit_button, "Edit")
            self.wait_for_idle()
            return True
        return False

    def has_backend_error(self) -> bool:
        """Return True when the detail page shows a server-side validation/pydantic error."""
        err_loc = self.page.locator(
            "text=/unexpected error/i, "
            "text=/validation error/i, "
            "text=/pydantic/i, "
            "text=/Field required/i"
        ).first
        return self.is_visible(err_loc, timeout=3_000)

    _KNOWN_STATUSES = (
        "submitted for approval", "pending approval", "approved", "rejected",
        "submitted", "draft", "processing", "pipeline error", "published",
        "archived", "under review", "placeholder mismatch",
    )

    def current_status(self) -> str:
        """Return the letter's status text from the detail panel.

        The detail panel shows a "Status" label followed by a status chip.
        Earlier this method grabbed the first ``[class*='chip']`` element, which
        matched a placeholder chip (e.g. ``{MergeDateTime}``) instead of the
        status. We now:
          1. Read the element right after the "Status" label.
          2. Fall back to any chip/badge whose text is a known status keyword.
        Placeholder chips (containing ``{`` / ``}``) are always ignored.
        Returns '' when no status is found (e.g. the page navigated away).
        """
        # 1. Element immediately following the "Status" label
        try:
            loc = self.page.locator(
                "xpath=//*[normalize-space(.)='Status']/following::*[1]"
            ).first
            if self.is_visible(loc, timeout=2_000):
                text = self.text_of(loc).strip()
                if text and "{" not in text and text.lower() != "status":
                    return text
        except Exception:
            pass

        # 2. Any chip/badge/tag whose text matches a known status keyword
        for sel in ("[class*='status']", "[class*='badge']", "[class*='chip']", "[class*='tag']"):
            locs = self.page.locator(sel)
            try:
                n = min(locs.count(), 20)
            except Exception:
                n = 0
            for i in range(n):
                try:
                    t = self.text_of(locs.nth(i)).strip()
                except Exception:
                    continue
                if not t or "{" in t:
                    continue
                if any(k in t.lower() for k in self._KNOWN_STATUSES):
                    return t
        return ""

    def _read_toast(self, timeout: int = 8_000) -> str:
        """Poll briefly for a snackbar/toast and return its text (or '')."""
        import time as _t
        deadline = _t.monotonic() + timeout / 1_000
        while _t.monotonic() < deadline:
            try:
                txt = self.page.evaluate(
                    """() => {
                        const sels = ['.MuiSnackbar-root','[class*="snackbar" i]',
                            '[class*="toast" i]','[class*="notification" i]',
                            'div[role="alert"]','div[role="status"]'];
                        for (const s of sels) {
                            for (const el of document.querySelectorAll(s)) {
                                const st = getComputedStyle(el);
                                if (st.display==='none' || st.visibility==='hidden') continue;
                                if (!el.offsetWidth && !el.offsetHeight) continue;
                                const t = (el.innerText||'').trim();
                                if (t.length > 5 && !/\\.docx$/i.test(t)) return t;
                            }
                        }
                        return null;
                    }"""
                )
                if txt:
                    self.log.info(f"Toast captured: {txt!r}")
                    return txt
            except Exception:
                pass
            self.page.wait_for_timeout(250)
        return ""

    def click_approve(self) -> bool:
        """Click Approve, then confirm 'Yes' on the Approval Confirmation dialog.

        Returns True if the Approve button was found and clicked. The app shows
        a two-step flow: Approve → "Are you sure…" dialog → Yes.
        """
        if not self.is_visible(self.approve_button, timeout=8_000):
            return False
        self.last_toast = ""
        self.safe_click(self.approve_button, "Approve")
        self.wait_for_idle()
        # Approval Confirmation dialog -> click Yes to commit
        if self.is_visible(self.confirm_approve_button, timeout=6_000):
            self.safe_click(self.confirm_approve_button, "Confirm Approval (Yes)")
            # Capture the success toast immediately — it fades within seconds
            self.last_toast = self._read_toast(timeout=8_000)
            self.wait_for_idle()
        return True

    def click_reject(self, reason: str = "Automated test rejection") -> bool:
        """Click Reject, fill the feedback reason, then Submit the dialog.

        Two-step flow: Reject → "Leave Feedback" dialog (reason textarea) →
        Submit. Returns True if the Reject button was found and clicked.
        """
        if not self.is_visible(self.reject_button, timeout=8_000):
            return False
        self.last_toast = ""
        self.safe_click(self.reject_button, "Reject")
        self.wait_for_idle()
        if self.is_visible(self.rejection_reason_input, timeout=5_000):
            self.safe_fill(self.rejection_reason_input, reason, label="rejection reason")
        if self.is_visible(self.confirm_reject_button, timeout=5_000):
            self.safe_click(self.confirm_reject_button, "Submit Rejection")
            # Capture the success toast immediately — it fades within seconds
            self.last_toast = self._read_toast(timeout=8_000)
            self.wait_for_idle()
        return True
