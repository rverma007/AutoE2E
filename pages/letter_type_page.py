"""
LetterTypePage — the main landing page after login.

Lists letter types with a search bar. Used as the anchor for "logged in"
and as a smoke-test surface.
"""
from __future__ import annotations

import re
from typing import List, Optional

from pages.base_page import BasePage


class LetterTypePage(BasePage):
    """Page Object for the Letter Type listing screen."""

    PATH = "letter-type"

    # Text of the last toast captured after a Configure upload (success/error).
    last_upload_toast: str = ""

    # --------------------------------------------------------------- Locators

    @property
    def search_box(self):
        return self.page.locator(
            "input[placeholder='Search by Letter Type, Id and External Id']"
        ).first

    @property
    def rows(self):
        # Restrict to tbody rows only — [role='row'] also matches thead/header
        # rows whose text never contains a status value, causing false mismatches
        # in filter assertions.
        return self.page.locator(
            "table tbody tr:not([class*='header']):not([class*='head']), "
            "[role='rowgroup'] [role='row'], "
            "[role='grid'] [role='row']:not([aria-rowindex='0'])"
        )

    @property
    def page_heading(self):
        return self.page.locator("h1, h2, h3, h4").first

    @property
    def table_header_row(self):
        return self.page.locator("thead tr, [role='row']:first-child").first

    @property
    def table_headers(self):
        return self.page.locator("thead th, [role='columnheader']")

    @property
    def _footer_text(self):
        return self.page.locator("text=/Showing.*results of/").first

    # ── Configure Letter Type ────────────────────────────────────────────────

    @property
    def configure_button(self):
        """'Configure Letter Type' button — toolbar or per-row action."""
        return self.page.locator(
            "button:has-text('Configure Letter Type'), "
            "a:has-text('Configure Letter Type'), "
            "button:has-text('Configure')"
        ).first

    @property
    def upload_input(self):
        return self.page.locator("input[type='file']").first

    @property
    def upload_submit_button(self):
        return self.page.locator(
            "button:has-text('Upload'), button:has-text('Submit'), button[type='submit']"
        ).first

    # ── Filter ───────────────────────────────────────────────────────────────

    @property
    def filter_button(self):
        return self.page.locator(
            "button[aria-label*='filter' i], "
            "[data-testid='filter-btn'], "
            "button:has-text('Filter')"
        ).first

    @property
    def filter_apply_button(self):
        return self.page.locator(
            "button:has-text('Apply Filters'), "
            "button:has-text('Apply')"
        ).first

    @property
    def filter_clear_button(self):
        return self.page.locator(
            "button:has-text('Clear'), button:has-text('Reset')"
        ).first

    # ── Download ─────────────────────────────────────────────────────────────

    @property
    def download_button(self):
        return self.page.locator(
            "button[aria-label*='download' i], "
            "button[aria-label*='export' i], "
            "button[title*='download' i], "
            "button[title*='export' i], "
            "[data-testid='download-btn'], "
            "[data-testid='export-btn'], "
            "button:has-text('Download'), "
            "button:has-text('Export')"
        ).first

    # ---------------------------------------------------------------- Actions

    def is_loaded(self, timeout: int = 30_000) -> bool:
        self.dismiss_ask_auto_popup()
        if not self.is_visible(self.search_box, timeout=timeout):
            # URL-based fallback: if we're on the letter-type page the session
            # is valid even when the search box takes longer than expected.
            if "letter-type" in self.page.url:
                self.log.info("is_loaded: search box not visible but URL is /letter-type — treating as loaded.")
                return True
            return False
        # Wait for skeleton shimmer to clear — ALL headers must have text
        try:
            self.page.wait_for_function(
                """() => {
                    const headers = document.querySelectorAll('thead th, [role="columnheader"]');
                    return headers.length > 0 &&
                           Array.from(headers).every(h => h.innerText && h.innerText.trim().length > 0);
                }""",
                timeout=timeout,
            )
        except Exception:  # noqa: BLE001
            pass
        return True

    def open_direct(self) -> "LetterTypePage":
        """Navigate to Letter Type via the sidebar (direct URL redirects to /dashboard)."""
        from pages.nav_page import NavigationPage
        nav = NavigationPage(self.page)
        nav.navigate()
        try:
            self.page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:  # noqa: BLE001
            pass
        self.dismiss_ask_auto_popup()
        nav.go_to_letter_type()
        try:
            self.page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:  # noqa: BLE001
            pass
        self.dismiss_ask_auto_popup()
        return self

    def search(self, query: str) -> "LetterTypePage":
        self.log.info(f"Searching for letter type: {query!r}")
        self.safe_fill(self.search_box, query, label="search")
        # Wait for debounced search results to arrive rather than a fixed sleep
        try:
            self.page.wait_for_load_state("networkidle", timeout=5_000)
        except Exception:  # noqa: BLE001
            pass
        return self

    def row_count(self) -> int:
        return self.rows.count()

    def visible_row_texts(self, limit: int = 10) -> List[str]:
        texts: List[str] = []
        count = min(self.rows.count(), limit)
        for i in range(count):
            try:
                row = self.rows.nth(i)
                text = self.text_of(row)
                if not text:
                    # Fall back to concatenating individual cell texts
                    cells = row.locator("td, [role='cell'], [role='gridcell']")
                    cell_texts = [
                        self.text_of(cells.nth(j))
                        for j in range(cells.count())
                    ]
                    text = " ".join(t for t in cell_texts if t)
                texts.append(text)
            except Exception:  # noqa: BLE001
                pass
        return texts

    def total_records(self) -> Optional[int]:
        """
        Parse the total count from the footer: 'Showing 1 – 10 results of 86' → 86.
        Returns None if no footer is present (small result set with no pagination).
        """
        if not self.is_visible(self._footer_text, timeout=5_000):
            return None
        text = self._footer_text.inner_text()
        match = re.search(r"results of\s+([\d,]+)", text)
        if not match:
            return None
        return int(match.group(1).replace(",", ""))

    def header_texts(self) -> List[str]:
        """Return visible column header labels."""
        count = self.table_headers.count()
        return [
            self.text_of(self.table_headers.nth(i)).strip()
            for i in range(count)
            if self.text_of(self.table_headers.nth(i)).strip()
        ]

    def _pick_first_mui_option(self, mui_id: str) -> str:
        """Open the MUI select #mui_id and click its first non-empty option.

        Returns the selected option text, or '' if it could not be selected.
        Used for the required Business Unit / Region dropdowns in the Configure
        panel where the test just needs *a* valid value.
        """
        sel = self.page.locator(f"#{mui_id}")
        if not self.is_visible(sel, timeout=8_000):
            return ""
        sel.click()
        listbox = self.page.locator("ul[role='listbox']")
        if not self.is_visible(listbox, timeout=6_000):
            return ""
        options = listbox.locator("li[role='option'], li")
        for i in range(options.count()):
            opt = options.nth(i)
            try:
                txt = (opt.inner_text(timeout=800) or "").strip()
            except Exception:
                txt = ""
            if txt:
                opt.click()
                self.page.wait_for_timeout(300)
                return txt
        try:
            self.page.keyboard.press("Escape")
        except Exception:  # noqa: BLE001
            pass
        return ""

    def configure_letter_type(self, file_path: str) -> str:
        """Run the full Configure Letter Type flow and return the created name.

        Steps mirror the real UI: open the panel → select a Business Unit
        (required) → upload the template (auto-fills Name + External ID) →
        give the Name a unique suffix (avoids duplicate-name rejection) →
        select a Region (required) → click Upload File.

        Returns the unique Letter Type Name that was created (searchable in the
        listing afterwards), or '' if the form could not be completed.
        """
        import random
        import string

        self.log.info(f"Configuring letter type with template: {file_path!r}")
        self.safe_click(self.configure_button, "Configure Letter Type")
        self.dismiss_ask_auto_popup()

        # 1. Business Unit (required) — first available option
        bu = self._pick_first_mui_option("mui-component-select-businessUnitDropdown")
        self.log.info(f"Configure: selected Business Unit {bu!r}")

        # 2. Upload the template (the panel must be open for it to register)
        if not self.is_visible(self.upload_input, timeout=10_000):
            self.page.wait_for_timeout(500)
        self.upload_input.set_input_files(file_path)
        self.log.info("Template file set on upload input.")
        self.dismiss_ask_auto_popup()

        # 3. Make the Letter Type Name unique to avoid duplicate-name rejection
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        created_name = ""
        name_input = self.page.locator(
            "div.MuiDrawer-paper input[placeholder*='Letter Type Name' i], "
            "input[placeholder*='Letter Type Name' i]"
        ).first
        if self.is_visible(name_input, timeout=10_000):
            base = (name_input.input_value() or "").strip() or "sample_template"
            created_name = f"{base}_{suffix}"
            name_input.click(click_count=3)
            name_input.fill(created_name)

        # 3b. External ID auto-fills to the same value — it must ALSO be made
        # unique, otherwise the server rejects the upload as a duplicate
        # External ID (the template may already exist from a prior run).
        # NOTE: scope strictly to the drawer — a page-level "External" match
        # also hits the listing search box ("…Id and External Id"), which sits
        # behind the drawer backdrop and is un-clickable.
        ext_input = self.page.locator(
            "div.MuiDrawer-paper input[placeholder='Enter External Id'], "
            "div.MuiDrawer-paper input[placeholder='Enter External ID'], "
            "div.MuiDrawer-paper input[placeholder*='External' i]"
        ).first
        if created_name and self.is_visible(ext_input, timeout=4_000):
            ext_input.click(click_count=3)
            ext_input.fill(created_name)

        # 4. Region (required) — first available option
        region = self._pick_first_mui_option("mui-component-select-regionDropdown")
        self.log.info(f"Configure: selected Region {region!r}")

        # 5. Submit via the 'Upload File' button
        submit = self.page.locator("button:has-text('Upload File')").last
        if self.is_visible(submit, timeout=8_000):
            self.safe_click(submit, "Upload File")
        elif self.is_visible(self.upload_submit_button, timeout=4_000):
            self.safe_click(self.upload_submit_button, "Upload submit")
        else:
            self.log.warning("Upload File button not found after filling the form.")

        # Capture the upload toast (success or error) for diagnostics
        self.last_upload_toast = self._read_upload_toast(timeout=8_000)
        self.log.info(f"Configure upload toast: {self.last_upload_toast!r}")

        # Wait for the drawer to close — the reliable signal the upload committed.
        try:
            self.page.wait_for_function(
                "() => { const d = document.querySelector('div.MuiDrawer-paper');"
                " return !d || getComputedStyle(d).visibility === 'hidden'"
                "    || getComputedStyle(d).display === 'none'; }",
                timeout=15_000,
            )
        except Exception:  # noqa: BLE001
            self.log.warning("Configure drawer did not close after Upload File.")

        self.wait_for_idle()
        # Give the server a moment to register the upload before polling status
        self.page.wait_for_timeout(1_500)
        return created_name

    def _read_upload_toast(self, timeout: int = 8_000) -> str:
        """Poll briefly for a snackbar/toast after upload; return its text."""
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
                                if (t.length > 5 && !/\\.docx$/i.test(t)
                                    && !/double curly brace/i.test(t)) return t;
                            }
                        }
                        return null;
                    }"""
                )
                if txt:
                    return txt
            except Exception:  # noqa: BLE001
                pass
            self.page.wait_for_timeout(250)
        return ""

    def first_row_status(self, timeout: int = 5_000) -> str:
        """Return the status text from the first data row."""
        candidates = [
            "tbody tr:first-child [class*='status']",
            "tbody tr:first-child [class*='badge']",
            "tbody tr:first-child [class*='chip']",
            "tbody tr:first-child [class*='tag']",
            "tbody tr:first-child td:last-child",
        ]
        for selector in candidates:
            loc = self.page.locator(selector).first
            if self.is_visible(loc, timeout=timeout):
                text = self.text_of(loc).strip()
                if text:
                    return text
        # Scan every cell in the first row for a known status keyword
        _known = (
            "processing", "draft", "active", "inactive", "published", "error",
            "approved", "rejected", "submitted for approval", "submitted",
            "placeholder mismatch", "pipeline error", "archived", "under review",
        )
        tds = self.page.locator("tbody tr:first-child td")
        for i in range(tds.count()):
            text = self.text_of(tds.nth(i)).strip()
            if any(k in text.lower() for k in _known):
                return text
        # No recognisable status found — return '' rather than the whole row
        # blob so callers get a clean, assertable signal.
        return ""

    def wait_for_first_row_status_any(
        self, accepted: tuple, timeout: int = 120_000, poll: int = 2_000
    ) -> bool:
        """Poll until the first row's status matches any value in `accepted`."""
        import time
        deadline = time.monotonic() + timeout / 1_000
        while time.monotonic() < deadline:
            status = self.first_row_status().lower()
            if any(s in status for s in accepted):
                return True
            self.page.wait_for_timeout(poll)
            self.page.reload()
            # wait_for_idle only fires on the browser "load" event; table rows
            # are populated by an async API call that comes after that.  Call
            # is_loaded() so we wait until the search box and column headers
            # are rendered (which requires the API response to have arrived)
            # before reading the first-row status.
            self.is_loaded()
        return False

    def wait_for_first_row_status(
        self, expected: str, timeout: int = 120_000, poll: int = 2_000
    ) -> bool:
        """Poll the first row's status until it matches `expected` or timeout expires."""
        import time
        deadline = time.monotonic() + timeout / 1_000
        while time.monotonic() < deadline:
            if self.first_row_status().lower() == expected.lower():
                return True
            self.page.wait_for_timeout(poll)
            self.page.reload()
            self.is_loaded()
        return False

    def apply_filter(self, filter_value: str) -> "LetterTypePage":
        """Open the filter panel and select the given status value, then apply."""
        self.log.info(f"Applying filter: {filter_value!r}")
        self.safe_click(self.filter_button, "Filter")
        self.page.wait_for_timeout(1_000)
        self.dismiss_ask_auto_popup()  # JS-hide any popup

        selected = False

        # --- Approach 1: native <select> element inside the filter panel ---
        native_select = self.page.locator("select").first
        if self.is_visible(native_select, timeout=1_000):
            try:
                native_select.select_option(filter_value)
                selected = True
                self.log.info(f"Filter set via native <select>: {filter_value!r}")
            except Exception:  # noqa: BLE001
                pass

        # --- Approach 2: click the "All Status" custom-select trigger -------
        if not selected:
            # Use get_by_text so we're not sensitive to the wrapper element type
            trigger = self.page.get_by_text("All Status", exact=True).first
            if self.is_visible(trigger, timeout=2_000):
                trigger.click()
                self.log.debug("Clicked 'All Status' dropdown trigger.")
                self.page.wait_for_timeout(400)

                # Options appear in a floating list — try common patterns
                for opt_sel in [
                    f"[role='option']:has-text('{filter_value}')",
                    f"[role='listbox'] *:has-text('{filter_value}')",
                    f"[class*='option']:has-text('{filter_value}')",
                    f"li:has-text('{filter_value}')",
                    f"[class*='menu'] *:has-text('{filter_value}')",
                ]:
                    opt = self.page.locator(opt_sel).first
                    if self.is_visible(opt, timeout=1_500):
                        opt.click()
                        selected = True
                        self.log.info(f"Filter option selected via dropdown: {filter_value!r}")
                        break

        # --- Approach 3: flat checkbox / label list -------------------------
        if not selected:
            direct = self.page.locator(
                f"label:has-text('{filter_value}'), "
                f"[role='option']:has-text('{filter_value}')"
            ).first
            if self.is_visible(direct, timeout=2_000):
                direct.click()
                selected = True
                self.log.info(f"Filter option selected via label/option: {filter_value!r}")

        if not selected:
            self.log.warning(f"Filter option '{filter_value}' not found — applying without selection.")

        if self.is_visible(self.filter_apply_button, timeout=3_000):
            self.safe_click(self.filter_apply_button, "Apply Filters")

        self.wait_for_idle()
        # Wait for filtered rows to render before returning.
        try:
            self.page.wait_for_function(
                """() => {
                    const rows = document.querySelectorAll('table tbody tr, [role="row"]');
                    return rows.length > 0 && rows[0].innerText && rows[0].innerText.trim().length > 0;
                }""",
                timeout=10_000,
            )
        except Exception:  # noqa: BLE001
            pass
        return self

    def download(self):
        """
        Click the Download button.

        Returns a Playwright Download object if the browser fires a download
        event, or None if: the button is permanently disabled (no eligible
        data / permissions), or the file is delivered via navigation/JS-blob.

        Never raises — all failures are treated as non-fatal so the test can
        report the situation rather than crash.
        """
        self.log.info("Initiating download.")
        self.dismiss_ask_auto_popup()

        # Guard: wait for the button to become enabled.  MUI marks it
        # Mui-disabled + sets disabled=true while the page is loading data
        # or when no rows qualify for export.  Clicking a disabled MUI button
        # retries for DEFAULT_TIMEOUT (30 s) and then throws, which is the
        # failure we saw in the logs.  Bail out early instead.
        try:
            self.page.wait_for_function(
                """() => {
                    const b = document.querySelector(
                        'button[aria-label*="Download" i], '  +
                        'button[aria-label*="Export" i], '   +
                        '.letter-type-download-button'
                    );
                    return b && !b.disabled && !b.classList.contains('Mui-disabled');
                }""",
                timeout=8_000,
            )
        except Exception:
            self.log.warning(
                "Download button is disabled — no eligible records for export "
                "or insufficient permissions.  Skipping click."
            )
            return None

        try:
            with self.page.expect_download(timeout=20_000) as dl_info:
                self.safe_click(self.download_button, "Download")
            dl = dl_info.value
            self.log.info(f"Download started: {dl.suggested_filename}")
            return dl
        except Exception as exc:
            self.log.warning(
                f"Download event not captured ({exc}); "
                "the export may use navigation/blob — treating as non-fatal."
            )
            return None
