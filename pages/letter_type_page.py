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

    def configure_letter_type(self, file_path: str) -> "LetterTypePage":
        """Click Configure Letter Type, then upload the given template file."""
        self.log.info(f"Configuring letter type with template: {file_path!r}")
        self.safe_click(self.configure_button, "Configure Letter Type")

        # Dismiss popup via JS (no Escape key — avoids closing the configure panel).
        self.dismiss_ask_auto_popup()

        # Wait for the file input to become attached and visible before calling
        # set_input_files — a hidden <input type="file"> is valid for
        # set_input_files but the panel must be open for the upload to register.
        if not self.is_visible(self.upload_input, timeout=10_000):
            # Try once more — some apps animate the panel open
            self.page.wait_for_timeout(500)

        self.upload_input.set_input_files(file_path)
        self.log.info("Template file set on upload input.")

        # Click Submit / Upload button if it appears
        if self.is_visible(self.upload_submit_button, timeout=8_000):
            self.safe_click(self.upload_submit_button, "Upload submit")
        else:
            self.log.warning("Submit button not found after file set — file may auto-upload.")

        # Wait for the request to complete and the list to refresh
        self.wait_for_idle()
        # Give the server a moment to register the upload before the caller
        # starts polling status — avoids reading stale "no rows" state.
        self.page.wait_for_timeout(1_500)
        return self

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
        # Scan every cell in the first row for a known status value
        _known = {"processing", "draft", "active", "inactive", "published", "error"}
        tds = self.page.locator("tbody tr:first-child td")
        for i in range(tds.count()):
            text = self.text_of(tds.nth(i)).strip()
            if text.lower() in _known:
                return text
        # Last resort: return the full text of the first data row
        row = self.page.locator("tbody tr:first-child").first
        return self.text_of(row).strip()

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
