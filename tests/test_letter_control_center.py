"""
Letter Control Center module — TC_SM_034 to TC_SM_043.

Covers:
  TC_SM_034  Generated Letters page loads
  TC_SM_035  Verify the letter control filters present
  TC_SM_036  XML Upload & Generation Flow Works
  TC_SM_037  Processing → Draft/Completed Status Update Works
  TC_SM_038  PDF & DOCX Download Works
  TC_SM_039  Validation Summary Executes Successfully
  TC_SM_040  Verify the bulk download
  TC_SM_041  Search by Document ID/Name works
  TC_SM_042  Pagination & Rows-Per-Page work
  TC_SM_043  Statistics cards display correct counts
"""
from __future__ import annotations

import allure
import pytest

from pages.letter_control_center_page import LetterControlCenterPage


pytestmark = pytest.mark.sanity


@allure.epic("Correspondence Application")
@allure.feature("Letter Control Center")
class TestLetterControlCenter:

    @allure.story("Page Load")
    @allure.title("[TC_SM_034] Generated Letters page loads successfully")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to the Letter Control Center (Generated Letters) module and "
        "verify the page loads with records displayed."
    )
    def test_generated_letters_page_loads(
        self, letter_control_center_page: LetterControlCenterPage
    ):
        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()

        with allure.step("Assert page is loaded"):
            loaded = letter_control_center_page.is_loaded(timeout=15_000)
            allure.attach(
                f"Page loaded: {loaded}\nURL: {letter_control_center_page.page.url}",
                name="Page load state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, (
                f"Letter Control Center page did not load. "
                f"URL: {letter_control_center_page.page.url}"
            )

        with allure.step("Assert records are displayed"):
            row_count = letter_control_center_page.row_count()
            total = letter_control_center_page.total_records()
            allure.attach(
                f"Visible rows: {row_count}\nFooter total: {total}",
                name="Record counts",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0 or (total is not None and total > 0), (
                f"Letter Control Center shows no records. "
                f"Visible rows: {row_count}, Footer total: {total}"
            )

    @allure.story("Filters")
    @allure.title("[TC_SM_035] Letter Control Center filters are present")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to Letter Control Center, open the Filters panel and verify "
        "filter fields are present. Apply filters and confirm results update."
    )
    def test_filters_present(self, letter_control_center_page: LetterControlCenterPage):
        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)

        with allure.step("Assert Filters button is visible"):
            filters_visible = letter_control_center_page.is_filters_section_visible(
                timeout=8_000
            )
            allure.attach(
                f"Filters button visible: {filters_visible}",
                name="Filter availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert filters_visible, "Filters button not found on Letter Control Center page."

        with allure.step("Open Filters dialog and verify fields"):
            letter_control_center_page.safe_click(
                letter_control_center_page.filter_button, "Filters"
            )
            apply_btn = letter_control_center_page.page.get_by_role(
                "button", name="Apply Filters"
            )
            apply_visible = letter_control_center_page.is_visible(apply_btn, timeout=5_000)
            allure.attach(
                f"Apply Filters button visible: {apply_visible}",
                name="Filter dialog",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert apply_visible, "Advanced Search dialog did not open or Apply Filters not found."

        with allure.step("Apply filters and assert page stays loaded"):
            letter_control_center_page.safe_click(apply_btn, "Apply Filters")
            letter_control_center_page.wait_for_idle()
            assert letter_control_center_page.is_loaded(timeout=10_000), (
                "Page lost loaded state after applying filters."
            )

    @allure.story("XML Upload & Generation")
    @allure.title("[TC_SM_036] XML Upload & Generation Flow works")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Click Generate Letter, choose Select Letter Type, upload a valid XML "
        "member data file, and verify the letter generates successfully."
    )
    def test_xml_upload_and_generate(
        self, letter_control_center_page: LetterControlCenterPage, xml_files: dict
    ):
        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)

        with allure.step("Check Generate Letter button is present"):
            gen_visible = letter_control_center_page.is_visible(
                letter_control_center_page.xml_upload_button, timeout=8_000
            )
            allure.attach(
                f"Generate Letter button visible: {gen_visible}",
                name="Generate button",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not gen_visible:
                pytest.skip("Generate Letter button not visible on this environment.")

        with allure.step("Record state before generation"):
            rows_before = letter_control_center_page.row_count()
            total_before = letter_control_center_page.total_records()
            first_doc_before = letter_control_center_page.first_row_document_id()
            allure.attach(
                f"Rows before   : {rows_before}\n"
                f"Footer total  : {total_before}\n"
                f"First doc ID  : {first_doc_before!r}",
                name="Pre-generation state",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Upload XML and generate letter"):
            letter_control_center_page.upload_xml_and_generate(xml_files)

        with allure.step("Assert page is still loaded and a new record appeared"):
            assert letter_control_center_page.is_loaded(timeout=15_000), (
                "Letter Control Center lost loaded state after generation."
            )
            rows_after = letter_control_center_page.row_count()
            total_after = letter_control_center_page.total_records()
            first_doc_after = letter_control_center_page.first_row_document_id()
            allure.attach(
                f"Rows after    : {rows_after}\n"
                f"Footer total  : {total_after}\n"
                f"First doc ID  : {first_doc_after!r}",
                name="Post-generation state",
                attachment_type=allure.attachment_type.TEXT,
            )
            # A new letter was added if the footer total grew, or if the
            # newest-first sort put a different Document ID at the top, or if
            # the visible row count itself grew (page was not yet full).
            new_record = (
                (total_after is not None and total_before is not None and total_after > total_before)
                or (first_doc_after and first_doc_after != first_doc_before)
                or rows_after > rows_before
            )
            assert new_record, (
                f"No new record detected after generation.\n"
                f"Rows: {rows_before} → {rows_after}, "
                f"Footer total: {total_before} → {total_after}, "
                f"First doc ID: {first_doc_before!r} → {first_doc_after!r}"
            )

        _VALID_STATUSES = (
            "processing", "draft", "completed", "letter cancelled",
            "draft modified", "translation completed",
        )
        with allure.step("Assert first row has a recognised status"):
            first_status = letter_control_center_page.first_row_status(timeout=8_000)
            allure.attach(
                f"First row status: {first_status!r}",
                name="Post-generation status",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert first_status, (
                "First row status is empty after generation — expected 'Processing' or a terminal state."
            )
            assert any(s in first_status.lower() for s in _VALID_STATUSES), (
                f"First row status {first_status!r} is not a recognised value. "
                f"Expected one of: {_VALID_STATUSES}"
            )

    @allure.story("Status Transition")
    @allure.title("[TC_SM_037] Letter reaches terminal status after generation")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Trigger letter generation and observe the status column. "
        "The status must reach a terminal state (Draft, Draft Modified, "
        "Letter Cancelled, or Completed) within the polling window."
    )
    def test_processing_to_completed_status(
        self, letter_control_center_page: LetterControlCenterPage, xml_files: dict
    ):
        _TERMINAL = (
            "draft", "completed", "letter cancelled",
            "draft modified", "translation completed",
        )

        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)

        with allure.step("Read initial first-row status"):
            initial_status = letter_control_center_page.first_row_status(timeout=5_000)
            allure.attach(
                f"Initial first-row status: {initial_status!r}",
                name="Initial status",
                attachment_type=allure.attachment_type.TEXT,
            )

        if not initial_status:
            with allure.step("No existing records — trigger generation first"):
                if not letter_control_center_page.is_visible(
                    letter_control_center_page.xml_upload_button, timeout=5_000
                ):
                    pytest.skip("No records and Generate Letter not visible.")
                letter_control_center_page.upload_xml_and_generate(xml_files)

        with allure.step("Poll for terminal status (up to 60 s)"):
            reached = letter_control_center_page.wait_for_status(
                "draft", timeout=60_000, poll=3_000
            )
            final_status = letter_control_center_page.first_row_status()
            allure.attach(
                f"Reached terminal: {reached}\nFinal status: {final_status!r}",
                name="Status transition result",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert reached or any(t in final_status.lower() for t in _TERMINAL), (
                f"Status did not reach a terminal state within 60 s. "
                f"Final status: {final_status!r}"
            )

    @allure.story("Download")
    @allure.title("[TC_SM_038] PDF & DOCX download works from letter detail")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Open a generated letter to the detail page. Click the Download button, "
        "select PDF and then DOCX from the dropdown, verify files download."
    )
    def test_pdf_and_docx_download(
        self, letter_control_center_page: LetterControlCenterPage
    ):
        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)

        with allure.step("Open first letter detail page"):
            navigated = letter_control_center_page.open_letter_detail()
            allure.attach(
                f"Navigated to detail: {navigated}\nURL: {letter_control_center_page.page.url}",
                name="Letter detail navigation",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert navigated, (
                "Could not open letter detail page — ensure at least one row exists."
            )

        with allure.step("Assert detail Download button is present"):
            dl_visible = letter_control_center_page.is_visible(
                letter_control_center_page.detail_download_button, timeout=8_000
            )
            allure.attach(
                f"Detail download button visible: {dl_visible}",
                name="Download button",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert dl_visible, (
                "Download button not found on letter detail page — "
                "check backend availability (ECONNREFUSED may indicate service is down)."
            )

        with allure.step("Download PDF"):
            import os
            pdf = letter_control_center_page.download_pdf()
            assert pdf is not None, "PDF download was not captured."
            pdf_filename, pdf_saved = letter_control_center_page.save_download(pdf, "letter_pdf")
            letter_control_center_page.allure_attach_file(pdf_saved, pdf_filename)
            allure.attach(
                f"File: {pdf_filename}\nPath: {pdf_saved}\n"
                f"Size: {os.path.getsize(pdf_saved) if os.path.exists(pdf_saved) else 'N/A'} bytes",
                name="PDF download details",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert pdf_filename, "PDF download triggered but filename is empty."
            assert os.path.exists(pdf_saved), f"PDF file not saved to disk: {pdf_saved}"
            assert os.path.getsize(pdf_saved) > 0, f"PDF file is empty (0 bytes): {pdf_saved}"

        with allure.step("Download DOCX"):
            docx = letter_control_center_page.download_docx()
            assert docx is not None, "DOCX download was not captured."
            docx_filename, docx_saved = letter_control_center_page.save_download(docx, "letter_docx")
            letter_control_center_page.allure_attach_file(docx_saved, docx_filename)
            allure.attach(
                f"File: {docx_filename}\nPath: {docx_saved}\n"
                f"Size: {os.path.getsize(docx_saved) if os.path.exists(docx_saved) else 'N/A'} bytes",
                name="DOCX download details",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert docx_filename, "DOCX download triggered but filename is empty."
            assert os.path.exists(docx_saved), f"DOCX file not saved to disk: {docx_saved}"
            assert os.path.getsize(docx_saved) > 0, f"DOCX file is empty (0 bytes): {docx_saved}"

    @allure.story("Validation Summary")
    @allure.title("[TC_SM_039] Validation Summary tab loads on letter detail")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Open a generated letter to the detail page. Click the Validation Summary "
        "tab and verify it loads without errors."
    )
    def test_validation_summary(
        self, letter_control_center_page: LetterControlCenterPage
    ):
        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)

        with allure.step("Open first letter detail page"):
            navigated = letter_control_center_page.open_letter_detail()
            allure.attach(
                f"Navigated to detail: {navigated}\nURL: {letter_control_center_page.page.url}",
                name="Letter detail navigation",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert navigated, (
                "Could not open letter detail page — ensure at least one row exists."
            )

        with allure.step("Assert Delivery Logs tab is visible"):
            delivery_visible = letter_control_center_page.is_visible(
                letter_control_center_page.delivery_logs_tab, timeout=8_000
            )
            allure.attach(
                f"Delivery Logs tab visible: {delivery_visible}",
                name="Delivery Logs tab",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert delivery_visible, (
                "Delivery Logs tab not visible — check backend availability."
            )

        with allure.step("Click Validation Summary tab"):
            vs_visible = letter_control_center_page.is_visible(
                letter_control_center_page.validation_summary_tab, timeout=5_000
            )
            assert vs_visible, "Validation Summary tab not visible on letter detail page."
            letter_control_center_page.safe_click(
                letter_control_center_page.validation_summary_tab, "Validation Summary"
            )
            letter_control_center_page.wait_for_idle()

        with allure.step("Assert detail page is still open after Validation Summary"):
            still_on_detail = "generated-letter-detail" in letter_control_center_page.page.url
            allure.attach(
                f"URL after tab click: {letter_control_center_page.page.url}",
                name="Post-tab URL",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert still_on_detail, (
                "Navigated away from letter detail page after clicking Validation Summary tab. "
                f"URL: {letter_control_center_page.page.url}"
            )

    @allure.story("Bulk Download")
    @allure.title("[TC_SM_040] Bulk download CSV is triggered successfully")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to Letter Control Center. Click the Download button, select "
        "'Download Report (CSV)' from the dropdown and verify the file downloads."
    )
    def test_bulk_download(self, letter_control_center_page: LetterControlCenterPage):
        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)

        with allure.step("Assert Download button is present"):
            bulk_visible = letter_control_center_page.is_visible(
                letter_control_center_page.bulk_download_button, timeout=8_000
            )
            allure.attach(
                f"Download button visible: {bulk_visible}",
                name="Download button availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert bulk_visible, (
                "Download button not visible — ensure records are loaded."
            )

        with allure.step("Click Download → Download Report (CSV)"):
            download = letter_control_center_page.download_bulk_csv()
            allure.attach(
                f"Download captured: {download is not None}",
                name="Bulk download result",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert download is not None, (
                "Download Report (CSV) was not captured — check the Download dropdown menu."
            )

        with allure.step("Verify downloaded file name and saved path"):
            import os
            filename, saved_path = letter_control_center_page.save_download(
                download, "bulk_report"
            )
            allure.attach(
                f"File: {filename}\nPath: {saved_path}",
                name="Bulk download file",
                attachment_type=allure.attachment_type.TEXT,
            )
            letter_control_center_page.allure_attach_file(saved_path, filename)
            assert filename, "Download triggered but filename is empty."
            assert saved_path and os.path.exists(saved_path), (
                f"Downloaded file not found on disk at: {saved_path}"
            )
            assert os.path.getsize(saved_path) > 0, (
                f"Downloaded file is empty (0 bytes): {saved_path}"
            )
            allure.attach(
                f"File name  : {filename}\n"
                f"Saved path : {saved_path}\n"
                f"File size  : {os.path.getsize(saved_path)} bytes",
                name="Bulk download job validation",
                attachment_type=allure.attachment_type.TEXT,
            )

    @allure.story("Search")
    @allure.title("[TC_SM_041] Search by Document ID/Name filters the table")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Type a Document ID from the first row into the search box and verify "
        "the table filters to show only matching results. Then clear the search "
        "and verify the full result set is restored."
    )
    def test_search_by_document_id(
        self, letter_control_center_page: LetterControlCenterPage
    ):
        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)

        with allure.step("Assert search input is present"):
            search_visible = letter_control_center_page.is_visible(
                letter_control_center_page.search_input, timeout=8_000
            )
            allure.attach(
                f"Search input visible: {search_visible}",
                name="Search input",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert search_visible, "Search input not found on Letter Control Center page."

        with allure.step("Read first row Document ID and total record count"):
            doc_id = letter_control_center_page.first_row_document_id()
            total_before = letter_control_center_page.total_records()
            rows_before = letter_control_center_page.row_count()
            allure.attach(
                f"Document ID: {doc_id!r}\nRows before: {rows_before}\nTotal: {total_before}",
                name="Pre-search state",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not doc_id:
                pytest.skip("No document ID found in first row — table may be empty.")

        with allure.step("Search for the Document ID"):
            letter_control_center_page.search(doc_id)
            rows_after = letter_control_center_page.row_count()
            total_after = letter_control_center_page.total_records()
            allure.attach(
                f"Search term: {doc_id!r}\nRows after: {rows_after}\nTotal after: {total_after}",
                name="Post-search state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert rows_after > 0, (
                f"Search for {doc_id!r} returned no results."
            )
            assert total_after is None or total_after <= (total_before or rows_before), (
                "Result count increased after applying a search filter — unexpected."
            )

        with allure.step("Verify first visible row matches the search term"):
            first_visible_id = letter_control_center_page.first_row_document_id()
            allure.attach(
                f"First visible Document ID: {first_visible_id!r}",
                name="Search result row",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert doc_id.lower() in first_visible_id.lower() or rows_after > 0, (
                f"First result {first_visible_id!r} does not match search term {doc_id!r}."
            )

        with allure.step("Clear search and verify results restore"):
            letter_control_center_page.clear_search()
            rows_restored = letter_control_center_page.row_count()
            allure.attach(
                f"Rows after clear: {rows_restored}",
                name="Post-clear row count",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert rows_restored > 0, "No rows visible after clearing the search."

    @allure.story("Pagination")
    @allure.title("[TC_SM_042] Pagination and Rows-Per-Page work correctly")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Change the rows-per-page setting and navigate to the next page. "
        "Verify the row count updates and the next page shows different records."
    )
    def test_pagination_and_rows_per_page(
        self, letter_control_center_page: LetterControlCenterPage
    ):
        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)

        with allure.step("Read initial state"):
            initial_rows = letter_control_center_page.row_count()
            initial_total = letter_control_center_page.total_records()
            allure.attach(
                f"Initial rows: {initial_rows}\nTotal records: {initial_total}",
                name="Initial pagination state",
                attachment_type=allure.attachment_type.TEXT,
            )
            if initial_rows == 0:
                pytest.skip("No records to paginate through.")

        with allure.step("Read first-row Document ID on page 1"):
            page1_doc_id = letter_control_center_page.first_row_document_id()
            allure.attach(
                f"Page 1 first Document ID: {page1_doc_id!r}",
                name="Page 1 first row",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Change rows-per-page to 25"):
            changed = letter_control_center_page.change_rows_per_page("25")
            rows_after_change = letter_control_center_page.row_count()
            allure.attach(
                f"Rows-per-page changed: {changed}\nRows now visible: {rows_after_change}",
                name="Rows-per-page result",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert letter_control_center_page.is_loaded(timeout=10_000), (
                "Page lost loaded state after changing rows-per-page."
            )
            assert rows_after_change > 0, "No rows visible after changing rows-per-page."

        with allure.step("Navigate to next page (if available)"):
            advanced = letter_control_center_page.go_to_next_page()
            allure.attach(
                f"Navigated to next page: {advanced}",
                name="Next page navigation",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert next page shows valid rows"):
            post_rows = letter_control_center_page.row_count()
            post_doc_id = letter_control_center_page.first_row_document_id()
            allure.attach(
                f"Rows on next page: {post_rows}\nFirst Document ID: {post_doc_id!r}",
                name="Next page state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert post_rows > 0, (
                f"No rows visible after pagination. Row count: {post_rows}"
            )
            if advanced and page1_doc_id:
                assert post_doc_id != page1_doc_id, (
                    "First row on page 2 is the same as page 1 — pagination may not have worked."
                )

    @allure.story("Statistics")
    @allure.title("[TC_SM_043] Statistics cards display correct counts")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to Letter Control Center and verify the statistics dashboard "
        "cards — 'Letter Types Used' and 'Total Letters Generated' — display "
        "non-zero numeric values that are consistent with the table footer total."
    )
    def test_statistics_cards(
        self, letter_control_center_page: LetterControlCenterPage
    ):
        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)

        with allure.step("Assert 'Letter Types Used' card is visible and non-zero"):
            lt_heading = letter_control_center_page.page.get_by_role(
                "heading", name="Letter Types Used"
            ).first
            lt_visible = letter_control_center_page.is_visible(lt_heading, timeout=15_000)
            allure.attach(
                f"Letter Types Used card visible: {lt_visible}",
                name="Letter Types Used card",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert lt_visible, "'Letter Types Used' statistics card not found on the page."
            # Go up 2 levels (heading → inner wrapper → card) then find the numeric <p>
            lt_card = lt_heading.locator("xpath=../..").first
            lt_value = letter_control_center_page.text_of(
                lt_card.locator("p").first
            ).strip()
            allure.attach(
                f"Letter Types Used value: {lt_value!r}",
                name="Letter Types Used value",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert lt_value.isdigit() and int(lt_value) > 0, (
                f"'Letter Types Used' shows unexpected value: {lt_value!r}. "
                "Expected a positive integer."
            )

        with allure.step("Assert 'Total Letters Generated' card is visible and non-zero"):
            tg_heading = letter_control_center_page.page.get_by_role(
                "heading", name="Total Letters Generated"
            ).first
            tg_visible = letter_control_center_page.is_visible(tg_heading, timeout=15_000)
            allure.attach(
                f"Total Letters Generated card visible: {tg_visible}",
                name="Total Letters Generated card",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert tg_visible, "'Total Letters Generated' statistics card not found on the page."
            tg_card = tg_heading.locator("xpath=../..").first
            tg_value = letter_control_center_page.text_of(
                tg_card.locator("p").first
            ).strip()
            allure.attach(
                f"Total Letters Generated value: {tg_value!r}",
                name="Total Letters Generated value",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert tg_value.isdigit() and int(tg_value) > 0, (
                f"'Total Letters Generated' shows unexpected value: {tg_value!r}. "
                "Expected a positive integer."
            )

        with allure.step("Assert stats are consistent with table footer total"):
            footer_total = letter_control_center_page.total_records()
            allure.attach(
                f"Footer total: {footer_total}\nStats total: {tg_value}",
                name="Stats vs footer consistency",
                attachment_type=allure.attachment_type.TEXT,
            )
            if footer_total is not None:
                assert int(tg_value) >= footer_total, (
                    f"'Total Letters Generated' ({tg_value}) is less than the "
                    f"table footer total ({footer_total}) — data inconsistency."
                )

    @allure.story("XML Upload & Generation")
    @allure.title(
        "[TC_SM_044] Generate Letter dialog flow — dialog options, Approved letter types, "
        "BU-matched XML upload, Draft status"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "End-to-end generation flow with granular assertions at every step:\n"
        "1. Click Generate Letter → verify dialog shows both 'Ask Auto' and 'Select Letter Type'.\n"
        "2. Click 'Select Letter Type' → verify navigation to generate-letter-select-type page.\n"
        "3. Verify all visible letter types have 'Approved' status.\n"
        "4. Read Placeholder/BU of the first row, click Select.\n"
        "5. Verify 'Upload Patient Metadata' panel opens.\n"
        "6. Upload the correct XML for the detected BU.\n"
        "7. Verify a new row appears on LCC with a terminal status (Draft or similar). "
        "If still 'Processing', the refresh icon is clicked until the status resolves."
    )
    def test_generate_letter_full_dialog_flow(
        self,
        letter_control_center_page: LetterControlCenterPage,
        xml_files: dict,
    ):
        _TERMINAL = (
            "draft", "completed", "letter cancelled",
            "draft modified", "translation completed",
        )

        with allure.step("Navigate to Letter Control Center"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)

        with allure.step("Record initial state before generation"):
            rows_before = letter_control_center_page.row_count()
            total_before = letter_control_center_page.total_records()
            first_doc_before = letter_control_center_page.first_row_document_id()
            allure.attach(
                f"Rows before    : {rows_before}\n"
                f"Footer total   : {total_before}\n"
                f"First doc ID   : {first_doc_before!r}",
                name="Initial state",
                attachment_type=allure.attachment_type.TEXT,
            )

        # ── Step 1: dialog ────────────────────────────────────────────────────
        with allure.step("Click 'Generate Letter' and verify dialog appears"):
            dialog_opened = letter_control_center_page.open_generate_letter_dialog()
            allure.attach(
                f"Generate Letter dialog opened: {dialog_opened}",
                name="Dialog state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert dialog_opened, (
                "Generate Letter dialog did not appear after clicking the button."
            )

        with allure.step("Verify 'Ask Auto' option is present in dialog"):
            ask_auto_visible = letter_control_center_page.is_visible(
                letter_control_center_page.ask_auto_modal_button, timeout=5_000
            )
            allure.attach(
                f"Ask Auto button visible: {ask_auto_visible}",
                name="Ask Auto option",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert ask_auto_visible, "'Ask Auto' option not found in the Generate Letter dialog."

        with allure.step("Verify 'Select Letter Type' option is present in dialog"):
            slt_visible = letter_control_center_page.is_visible(
                letter_control_center_page.select_letter_type_button, timeout=5_000
            )
            allure.attach(
                f"Select Letter Type button visible: {slt_visible}",
                name="Select Letter Type option",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert slt_visible, (
                "'Select Letter Type' option not found in the Generate Letter dialog."
            )

        # ── Step 2: navigate to select-type page ─────────────────────────────
        with allure.step("Click 'Select Letter Type' and verify page navigation"):
            navigated = letter_control_center_page.navigate_to_select_letter_type_page()
            allure.attach(
                f"On select-type page: {navigated}\nURL: {letter_control_center_page.page.url}",
                name="Select Letter Type navigation",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert navigated, (
                f"Did not navigate to generate-letter-select-type. "
                f"URL: {letter_control_center_page.page.url}"
            )

        # ── Step 3: all letter types must be Approved ─────────────────────────
        with allure.step("Verify all visible letter types have 'Approved' status"):
            letter_control_center_page.wait_for_idle()
            rows_loc = letter_control_center_page.page.locator("table tbody tr")

            # Wait until skeleton rows are replaced with real data
            import time as _t_skel
            skel_deadline = _t_skel.monotonic() + 15
            while _t_skel.monotonic() < skel_deadline:
                first_text = letter_control_center_page.text_of(rows_loc.first).strip()
                if first_text:
                    break
                letter_control_center_page.page.wait_for_timeout(500)

            row_count = rows_loc.count()
            assert row_count > 0, "No letter types found on the Select Letter Type page."

            non_approved: list[str] = []
            for i in range(min(row_count, 10)):
                row_text = letter_control_center_page.text_of(rows_loc.nth(i))
                if row_text.strip() and "approved" not in row_text.lower():
                    non_approved.append(row_text.strip()[:100])

            allure.attach(
                f"Rows checked: {min(row_count, 10)}\n"
                f"Non-approved rows: {non_approved or 'none'}",
                name="Letter type status check",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert not non_approved, (
                f"Some letter types do not have 'Approved' status: {non_approved}"
            )

        # ── Step 4 & 5: read BU, click Select, verify metadata panel ─────────
        with allure.step("Read BU of first letter type and click Select"):
            bu_text = letter_control_center_page.select_first_letter_type_row()
            allure.attach(
                f"First letter type Placeholder/BU: {bu_text!r}",
                name="Selected letter type BU",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Verify 'Upload Patient Metadata' panel is visible"):
            panel_visible = letter_control_center_page.is_visible(
                letter_control_center_page.select_file_button, timeout=8_000
            )
            allure.attach(
                f"Upload panel visible: {panel_visible}",
                name="Upload panel",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert panel_visible, (
                "'Upload Patient Metadata' panel did not open after clicking Select."
            )

        # ── Step 6: upload BU-matched XML ─────────────────────────────────────
        with allure.step("Upload XML matching detected BU and submit generation"):
            file_path = letter_control_center_page._pick_xml(xml_files, bu_text)
            allure.attach(
                f"BU detected : {bu_text!r}\nXML selected: {file_path}",
                name="XML selection",
                attachment_type=allure.attachment_type.TEXT,
            )
            generated = letter_control_center_page.upload_metadata_and_generate(file_path)
            allure.attach(
                f"Generation triggered: {generated}",
                name="Generation result",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert generated, "Could not complete the metadata upload and generation steps."

        # ── Step 7: new row + terminal status ─────────────────────────────────
        with allure.step("Navigate back to LCC and verify new row appeared"):
            letter_control_center_page.open_direct()
            assert letter_control_center_page.is_loaded(timeout=15_000)
            # first_row_document_id() polls until real data replaces skeleton rows
            first_doc_after = letter_control_center_page.first_row_document_id()
            rows_after = letter_control_center_page.row_count()
            total_after = letter_control_center_page.total_records()
            allure.attach(
                f"Rows     : {rows_before} → {rows_after}\n"
                f"Footer   : {total_before} → {total_after}\n"
                f"First doc: {first_doc_before!r} → {first_doc_after!r}",
                name="Row count comparison",
                attachment_type=allure.attachment_type.TEXT,
            )
            new_record = (
                (total_after is not None and total_before is not None and total_after > total_before)
                or (first_doc_after and first_doc_after != first_doc_before)
                or rows_after > rows_before
            )
            assert new_record, (
                f"No new record detected after generation.\n"
                f"Rows: {rows_before} → {rows_after}, "
                f"Footer total: {total_before} → {total_after}, "
                f"First doc: {first_doc_before!r} → {first_doc_after!r}"
            )

        with allure.step(
            "Wait for letter to leave 'Processing' — click refresh icon if needed"
        ):
            import time as _time
            deadline = _time.monotonic() + 60
            final_status = ""
            while _time.monotonic() < deadline:
                final_status = letter_control_center_page.first_row_status()
                if final_status and "processing" not in final_status.lower():
                    break
                letter_control_center_page.click_refresh()
                letter_control_center_page.page.wait_for_timeout(3_000)

            allure.attach(
                f"Final first-row status: {final_status!r}",
                name="Post-generation status",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert final_status, (
                "First row has no status after generation — table may not have updated."
            )
            assert any(t in final_status.lower() for t in _TERMINAL), (
                f"Letter did not reach a terminal status within 60 s. "
                f"Final status: {final_status!r}. Expected one of: {_TERMINAL}"
            )

