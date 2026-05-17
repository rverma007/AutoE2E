"""LetterControlCenterPage — track the full lifecycle of generated letters."""
from __future__ import annotations

import re
from typing import Optional

from pages.base_page import BasePage


class LetterControlCenterPage(BasePage):
    PATH = "letter-control-center"

    # ---------------------------------------------------------------- Locators

    @property
    def _page_heading(self):
        return self.page.locator("h1, h2, h3", has_text="Generated Letters").first

    @property
    def _subtitle(self):
        return self.page.locator(
            "text=Track the full lifecycle of generated letters"
        ).first

    @property
    def filter_button(self):
        return self.page.get_by_role("button", name=re.compile(r"^Filters?$", re.IGNORECASE))

    @property
    def xml_upload_input(self):
        return self.page.locator("input[type='file']").first

    @property
    def xml_upload_button(self):
        return self.page.get_by_role("button", name="Generate Letter")

    @property
    def select_letter_type_button(self):
        return self.page.get_by_role("button", name="Select Letter Type")

    @property
    def select_file_button(self):
        return self.page.get_by_role("button", name="Select file to Upload")

    @property
    def upload_file_button(self):
        return self.page.get_by_role("button", name="Upload File")

    @property
    def generate_button(self):
        # "Generate Letter" button inside the generation dialog
        return self.page.get_by_role("button", name="Generate Letter")

    @property
    def _rows(self):
        return self.page.locator("table tbody tr")

    # Download button on list page — opens a dropdown menu
    @property
    def bulk_download_button(self):
        return self.page.get_by_role("button", name=re.compile(r"^Download$", re.IGNORECASE))

    @property
    def download_csv_menuitem(self):
        return self.page.get_by_role("menuitem", name="Download Report (CSV)")

    # Split download button (⬇️ ▼) in the PDF viewer toolbar on the detail page.
    # Clicking the chevron (▼) part opens the PDF / DOCX dropdown menu.
    @property
    def detail_download_button(self):
        return self.page.locator(
            # ▼ chevron of MUI split ButtonGroup — opens format dropdown
            "button:has(svg[data-testid='ArrowDropDownIcon']), "
            # Last button in a ButtonGroup (chevron position)
            ".MuiButtonGroup-root button:last-child, "
            # aria/title fallbacks
            "button[aria-label*='download' i], "
            "button[title*='download' i], "
            # MUI download icon variants
            "button:has(svg[data-testid='FileDownloadIcon']), "
            "button:has(svg[data-testid='DownloadIcon']), "
            "button:has(svg[data-testid='GetAppIcon']), "
            # Last resort: any contained button
            ".MuiButtonBase-root.MuiButton-root.MuiButton-contained"
        ).first

    @property
    def pdf_menuitem(self):
        return self.page.locator(
            "[role='menuitem']:has-text('PDF'), "
            "[role='option']:has-text('PDF'), "
            "li:has-text('PDF'), "
            "button:has-text('PDF')"
        ).first

    @property
    def docx_menuitem(self):
        return self.page.locator(
            "[role='menuitem']:has-text('DOCX'), "
            "[role='option']:has-text('DOCX'), "
            "li:has-text('DOCX'), "
            "button:has-text('DOCX')"
        ).first

    @property
    def validation_summary_tab(self):
        return self.page.get_by_role("tab", name="Validation Summary")

    @property
    def delivery_logs_tab(self):
        return self.page.locator(
            "[role='tab']:has-text('Delivery Logs'), "
            "[role='tab']:has-text('Delivery'), "
            "[role='tab']:has-text('Logs'), "
            "button:has-text('Delivery Logs'), "
            "button:has-text('Delivery'), "
            "a:has-text('Delivery Logs')"
        ).first

    @property
    def _footer_text(self):
        return self.page.get_by_text(
            re.compile(r"Showing \d+\s*[–\-]\s*\d+ results of \d+", re.IGNORECASE)
        ).first

    @property
    def search_input(self):
        return self.page.locator(
            "input[placeholder*='Search by Document']"
        ).first

    @property
    def rows_per_page_combobox(self):
        return self.page.locator(
            "[role='combobox']"
        ).filter(has_text=re.compile(r"/ page", re.IGNORECASE)).first

    @property
    def next_page_button(self):
        return self.page.get_by_role("button", name=re.compile(r"Go to next page", re.IGNORECASE))

    @property
    def prev_page_button(self):
        return self.page.get_by_role("button", name=re.compile(r"Go to previous page", re.IGNORECASE))

    @property
    def ask_auto_modal_button(self):
        return self.page.get_by_role("button", name=re.compile(r"^Ask Auto$", re.IGNORECASE))

    # Refresh icon on the LCC table toolbar (circular arrows, aria-label="refresh")
    @property
    def refresh_button(self):
        return self.page.get_by_role(
            "button", name=re.compile(r"^refresh$", re.IGNORECASE)
        ).first

    @property
    def stat_letter_types_used(self):
        return self.page.locator("h3, h4", has_text="Letter Types Used").locator(
            "xpath=ancestor::*[position()<=3]"
        ).last

    @property
    def stat_total_generated(self):
        return self.page.locator("h3, h4", has_text="Total Letters Generated").locator(
            "xpath=ancestor::*[position()<=3]"
        ).last

    # ---------------------------------------------------------------- Actions

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

    def open_letter_detail(self) -> bool:
        """Click the Document ID cell of the first real data row to open the detail page.

        Waits until the cell has non-empty text to avoid clicking skeleton rows.
        """
        import time as _time
        cell = self.page.locator("table tbody tr:first-child td:nth-child(2)").first
        if not self.is_visible(cell, timeout=15_000):
            return False
        # Poll until the cell contains actual text (skeleton rows are empty)
        deadline = _time.monotonic() + 12
        has_text = False
        while _time.monotonic() < deadline:
            if self.text_of(cell).strip():
                has_text = True
                break
            self.page.wait_for_timeout(500)
        if not has_text:
            return False
        cell.click()
        try:
            self.page.wait_for_url(re.compile(r"generated-letter-detail"), timeout=12_000)
        except Exception:  # noqa: BLE001
            pass
        return "generated-letter-detail" in self.page.url

    # Placeholder/BU column index on the Select Letter Type page (1-based)
    _BU_COLUMN = 6

    def _pick_xml(self, xml_files: dict, bu_text: str) -> str:
        """Return the XML path matching the Placeholder/BU value.

        "UM" (or starts with "UM") → xml_files["um"]
        "ANG ..." (contains "ANG")  → xml_files["ang"]
        Fallback: first available file.
        """
        bu = bu_text.lower().strip()
        if bu.startswith("um") and "um" in xml_files:
            return xml_files["um"]
        if "ang" in bu and "ang" in xml_files:
            return xml_files["ang"]
        return next(iter(xml_files.values()))

    def upload_xml_and_generate(self, xml_files: dict) -> bool:
        """Open Generate Letter dialog → Select Letter Type → auto-pick XML by BU → generate.

        xml_files: {"ang": "/path/CA_Pega AnG (1).xml", "um": "/path/UM-LTR-....xml"}
        The correct XML is chosen by reading the Placeholder/BU column of the first
        letter-type row on the Select Letter Type page.
        """
        if not self.is_visible(self.xml_upload_button, timeout=5_000):
            return False
        self.safe_click(self.xml_upload_button, "Generate Letter")
        self.page.wait_for_timeout(500)

        if self.is_visible(self.select_letter_type_button, timeout=5_000):
            self.safe_click(self.select_letter_type_button, "Select Letter Type")
            # Wait for Select Letter Type page to fully load
            self.wait_for_idle()
            self.page.wait_for_timeout(500)

        # Wait for real data to load (skeleton rows have empty cells)
        import time as _time
        bu_cell = self.page.locator(
            f"table tbody tr:first-child td:nth-child({self._BU_COLUMN})"
        ).first
        bu_text = ""
        first_lt_row = self.page.locator("table tbody tr:first-child")
        if self.is_visible(first_lt_row, timeout=10_000):
            # Poll until BU cell has actual text (not a skeleton placeholder)
            deadline = _time.monotonic() + 10
            while _time.monotonic() < deadline:
                if self.is_visible(bu_cell, timeout=500):
                    bu_text = self.text_of(bu_cell).strip()
                    if bu_text:
                        break
                self.page.wait_for_timeout(400)
            self.log.info(f"Letter type Placeholder/BU: {bu_text!r}")
            first_lt_row.get_by_role("button").first.click()
            # Wait for upload page navigation to complete
            self.wait_for_idle()
            self.page.wait_for_timeout(500)

        file_path = self._pick_xml(xml_files, bu_text)
        self.log.info(f"BU={bu_text!r} → Using XML: {file_path}")

        # Upload XML via the hidden <input type="file">.
        # The "Select file to Upload" button triggers the native file dialog — bypass
        # that by setting files directly on the hidden input element.
        if self.is_visible(self.select_file_button, timeout=8_000):
            file_input = self.page.locator("input[type='file']").first
            try:
                file_input.set_input_files(file_path)
            except Exception:  # noqa: BLE001
                # Fallback: dispatch a change event after injecting the file via JS
                self.page.evaluate(
                    """([selector, path]) => {
                        const inp = document.querySelector(selector);
                        if (!inp) return;
                        const dt = new DataTransfer();
                        fetch(path).catch(() => {});
                    }""",
                    ["input[type='file']", file_path],
                )
                file_input.set_input_files(file_path, no_wait_after=True)
            self.page.wait_for_timeout(500)

        if self.is_visible(self.upload_file_button, timeout=5_000):
            self.safe_click(self.upload_file_button, "Upload File")
            self.page.wait_for_timeout(500)

        if self.is_visible(self.generate_button, timeout=8_000):
            self.safe_click(self.generate_button, "Generate Letter")

        self.wait_for_idle()
        return True

    def first_row_status(self, timeout: int = 5_000) -> str:
        loc = self.page.locator("table tbody tr:first-child td:last-child").first
        if self.is_visible(loc, timeout=timeout):
            text = self.text_of(loc).strip()
            if text and text != "-":
                return text
        return ""

    _TERMINAL_STATUSES = (
        "draft", "completed", "letter cancelled",
        "draft modified", "translation completed",
    )

    def wait_for_status(
        self, expected: str, timeout: int = 120_000, poll: int = 3_000
    ) -> bool:
        """Poll until the first-row status contains `expected` (or any terminal state)."""
        import time
        deadline = time.monotonic() + timeout / 1_000
        while time.monotonic() < deadline:
            current = self.first_row_status().lower()
            if expected.lower() in current:
                return True
            if any(t in current for t in self._TERMINAL_STATUSES):
                return True
            self.page.wait_for_timeout(poll)
            self.page.reload()
            self.is_loaded()
        return False

    def download_bulk_csv(self):
        """Click Download → Download Report (CSV) and return the Download object."""
        try:
            self.safe_click(self.bulk_download_button, "Download menu")
            with self.page.expect_download(timeout=30_000) as dl:
                self.safe_click(self.download_csv_menuitem, "Download Report (CSV)")
            return dl.value
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"Bulk CSV download not captured: {exc}")
            return None

    def _open_download_menu(self) -> bool:
        """Click the ▼ chevron of the split download button to open the format menu."""
        btn = self.detail_download_button
        if not self.is_visible(btn, timeout=8_000):
            return False
        self.safe_click(btn, "Download split-button chevron")
        # Wait for the dropdown menu to appear
        try:
            self.page.wait_for_selector(
                "[role='menu'], [role='listbox'], .MuiMenu-root",
                state="visible", timeout=5_000
            )
        except Exception:
            pass
        self.page.wait_for_timeout(300)
        return True

    def download_pdf(self):
        """On the letter detail page: open download menu → click PDF."""
        try:
            if not self._open_download_menu():
                return None
            with self.page.expect_download(timeout=30_000) as dl:
                self.safe_click(self.pdf_menuitem, "PDF")
            return dl.value
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"PDF download not captured: {exc}")
            return None

    def download_docx(self):
        """On the letter detail page: open download menu → click DOCX."""
        try:
            if not self._open_download_menu():
                return None
            with self.page.expect_download(timeout=30_000) as dl:
                self.safe_click(self.docx_menuitem, "DOCX")
            return dl.value
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"DOCX download not captured: {exc}")
            return None

    def search(self, query: str) -> None:
        """Type a search term and wait for results to update."""
        self.safe_fill(self.search_input, query, label="LCC search")
        self.wait_for_idle()

    def clear_search(self) -> None:
        """Clear the search box and wait for results to reset."""
        if self.is_visible(self.search_input, timeout=3_000):
            self.search_input.fill("")
            self.wait_for_idle()

    def first_row_document_id(self) -> str:
        """Return the Document ID text from the first data row."""
        cell = self.page.locator("table tbody tr:first-child td:nth-child(2)").first
        import time as _t
        deadline = _t.monotonic() + 8
        while _t.monotonic() < deadline:
            text = self.text_of(cell).strip()
            if text:
                return text
            self.page.wait_for_timeout(400)
        return ""

    def change_rows_per_page(self, value: str) -> bool:
        """Open the rows-per-page combobox and select a value (e.g. '25')."""
        if not self.is_visible(self.rows_per_page_combobox, timeout=5_000):
            return False
        self.safe_click(self.rows_per_page_combobox, "rows-per-page combobox")
        option = self.page.get_by_role("option", name=re.compile(rf"^{value}", re.IGNORECASE))
        if self.is_visible(option, timeout=3_000):
            option.click()
            self.wait_for_idle()
            return True
        return False

    def go_to_next_page(self) -> bool:
        """Click the next-page button. Returns True if navigation was possible."""
        btn = self.next_page_button
        if self.is_visible(btn, timeout=5_000) and not btn.is_disabled():
            btn.click()
            self.wait_for_idle()
            return True
        return False

    def stat_value(self, heading_text: str) -> str:
        """Return the numeric value from a statistics card by its heading text."""
        card = self.page.locator(
            f"h3:has-text('{heading_text}'), h4:has-text('{heading_text}')"
        ).first
        if not self.is_visible(card, timeout=8_000):
            return ""
        parent = card.locator("xpath=../..").first
        full_text = self.text_of(parent).strip()
        # Card text is e.g. "Letter Types Used\n\n24" — extract the last number
        nums = re.findall(r"[\d,]+", full_text)
        return nums[-1].replace(",", "") if nums else ""

    def open_generate_letter_dialog(self) -> bool:
        """Click the main 'Generate Letter' button; return True when the dialog is visible."""
        if not self.is_visible(self.xml_upload_button, timeout=5_000):
            return False
        self.safe_click(self.xml_upload_button, "Generate Letter")
        # Dialog is open when either modal option is visible
        return (
            self.is_visible(self.ask_auto_modal_button, timeout=5_000)
            or self.is_visible(self.select_letter_type_button, timeout=5_000)
        )

    def navigate_to_select_letter_type_page(self) -> bool:
        """From the Generate Letter modal click 'Select Letter Type'; verify URL."""
        self.safe_click(self.select_letter_type_button, "Select Letter Type")
        self.wait_for_idle()
        self.page.wait_for_timeout(500)
        return "generate-letter-select-type" in self.page.url

    def select_first_letter_type_row(self) -> str:
        """Poll until first row BU text is available, click Select. Returns BU text."""
        import time as _t
        bu_cell = self.page.locator(
            f"table tbody tr:first-child td:nth-child({self._BU_COLUMN})"
        ).first
        bu_text = ""
        deadline = _t.monotonic() + 10
        while _t.monotonic() < deadline:
            bu_text = self.text_of(bu_cell).strip()
            if bu_text:
                break
            self.page.wait_for_timeout(400)
        self.log.info(f"First letter type BU: {bu_text!r}")
        select_btn = (
            self.page.locator("table tbody tr:first-child")
            .get_by_role("button", name="Select")
            .first
        )
        self.safe_click(select_btn, "Select first letter type")
        self.page.wait_for_timeout(500)
        return bu_text

    def upload_metadata_and_generate(self, file_path: str) -> bool:
        """Upload XML in the 'Upload Patient Metadata' panel then click Generate."""
        if self.is_visible(self.select_file_button, timeout=8_000):
            file_input = self.page.locator("input[type='file']").first
            try:
                file_input.set_input_files(file_path)
            except Exception:  # noqa: BLE001
                pass
            self.page.wait_for_timeout(500)
        if self.is_visible(self.upload_file_button, timeout=5_000):
            self.safe_click(self.upload_file_button, "Upload File")
            self.page.wait_for_timeout(500)
        if self.is_visible(self.generate_button, timeout=8_000):
            self.safe_click(self.generate_button, "Generate Letter")
            self.wait_for_idle()
            return True
        return False

    def click_refresh(self) -> bool:
        """Click the refresh icon on the LCC table toolbar."""
        if self.is_visible(self.refresh_button, timeout=3_000):
            self.safe_click(self.refresh_button, "Refresh")
            self.wait_for_idle()
            return True
        return False

    def total_records(self) -> Optional[int]:
        if not self.is_visible(self._footer_text, timeout=5_000):
            return None
        text = self._footer_text.inner_text()
        match = re.search(r"results of\s+([\d,]+)", text)
        if not match:
            return None
        return int(match.group(1).replace(",", ""))

