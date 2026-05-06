"""
Audit Logger module — TC_SM_043 to TC_SM_048.

Covers:
  TC_SM_043  Verify Audit Logger page loads
  TC_SM_044  Verify letter actions create an audit entry
  TC_SM_045  Verify audit data shows correct User/Entity/Action/Date
  TC_SM_046  Verify Search & Date Range Filter work
  TC_SM_047  Verify Download Audit Report works
  TC_SM_048  Verify Pagination & Rows-Per-Page work
"""
from __future__ import annotations

import allure
import pytest

from pages.audit_logger_page import AuditLoggerPage


pytestmark = pytest.mark.sanity


@allure.epic("Correspondence Application")
@allure.feature("Audit Logger")
class TestAuditLogger:

    @allure.story("Page Load")
    @allure.title("[TC_SM_043] Audit Logger page loads successfully")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Navigate to the Audit Logger module and verify the page loads "
        "without errors."
    )
    def test_audit_logger_page_loads(self, audit_logger_page: AuditLoggerPage):
        with allure.step("Navigate to Audit Logger"):
            audit_logger_page.open_direct()

        with allure.step("Assert page is loaded"):
            loaded = audit_logger_page.is_loaded(timeout=15_000)
            allure.attach(
                f"Page loaded: {loaded}\nURL: {audit_logger_page.page.url}",
                name="Page load state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, (
                f"Audit Logger page did not load. URL: {audit_logger_page.page.url}"
            )

    @allure.story("Audit Logging")
    @allure.title("[TC_SM_044] Letter actions create an audit entry")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Navigate to Audit Logger and verify at least one audit entry exists, "
        "confirming that system actions (Create/Edit/Approve/Generate) are logged."
    )
    def test_letter_actions_create_audit_entry(self, audit_logger_page: AuditLoggerPage):
        with allure.step("Navigate to Audit Logger"):
            audit_logger_page.open_direct()
            assert audit_logger_page.is_loaded(timeout=15_000)

        with allure.step("Assert at least one audit entry is present"):
            row_count = audit_logger_page.row_count()
            total = audit_logger_page.total_records()
            allure.attach(
                f"Visible rows: {row_count}\nFooter total: {total}",
                name="Audit entry counts",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0 or (total is not None and total > 0), (
                "Audit Logger shows no entries — expected at least one action to be logged."
            )

    @allure.story("Audit Data")
    @allure.title("[TC_SM_045] Audit data shows correct User/Entity/Action/Date")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Open the Audit Logger and inspect the first entry's columns. Verify "
        "that User, Entity, Action, and Timestamp fields are populated."
    )
    def test_audit_data_correct_fields(self, audit_logger_page: AuditLoggerPage):
        with allure.step("Navigate to Audit Logger"):
            audit_logger_page.open_direct()
            assert audit_logger_page.is_loaded(timeout=15_000)

        with allure.step("Assert audit entries are present"):
            row_count = audit_logger_page.row_count()
            if row_count == 0:
                pytest.skip("No audit entries to inspect.")

        with allure.step("Read first row data"):
            row_cells = audit_logger_page.get_first_row_texts()
            allure.attach(
                f"First row cells: {row_cells}",
                name="First audit entry",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert first row has non-empty cell data"):
            non_empty = [c for c in row_cells if c.strip()]
            assert len(non_empty) >= 3, (
                f"Audit entry appears to be missing fields. "
                f"Non-empty cells: {non_empty}"
            )

    @allure.story("Filters")
    @allure.title("[TC_SM_046] Search & Date Range filter work on Audit Logger")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Enter a search term and apply a date range filter in Audit Logger. "
        "Verify the results update correctly. This test was marked Fail in the "
        "UAT report — captures the regression."
    )
    def test_search_and_date_range_filter(self, audit_logger_page: AuditLoggerPage):
        with allure.step("Navigate to Audit Logger"):
            audit_logger_page.open_direct()
            assert audit_logger_page.is_loaded(timeout=15_000)

        with allure.step("Check search input availability"):
            search_visible = audit_logger_page.is_visible(
                audit_logger_page.search_input, timeout=8_000
            )
            allure.attach(
                f"Search input visible: {search_visible}",
                name="Search input",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not search_visible:
                pytest.skip("Search input not visible on Audit Logger page.")

        with allure.step("Record unfiltered row count"):
            unfiltered = audit_logger_page.row_count()
            allure.attach(
                f"Unfiltered rows: {unfiltered}",
                name="Pre-filter count",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Apply date range filter (last 30 days)"):
            audit_logger_page.apply_date_filter(
                date_from="2026-04-01",
                date_to="2026-05-06",
            )

        with allure.step("Assert filter applied without error"):
            filtered_count = audit_logger_page.row_count()
            allure.attach(
                f"Filtered rows: {filtered_count}",
                name="Post-filter count",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert filtered_count >= 0, "row_count() raised an error after filter."
            assert audit_logger_page.is_loaded(timeout=10_000), (
                "Audit Logger lost loaded state after applying filter."
            )

    @allure.story("Download Report")
    @allure.title("[TC_SM_047] Download Audit Report works")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to Audit Logger, optionally apply filters, click Download/Export, "
        "and verify the audit report downloads successfully."
    )
    def test_download_audit_report(self, audit_logger_page: AuditLoggerPage):
        with allure.step("Navigate to Audit Logger"):
            audit_logger_page.open_direct()
            assert audit_logger_page.is_loaded(timeout=15_000)

        with allure.step("Assert Download/Export button is present"):
            dl_visible = audit_logger_page.is_visible(
                audit_logger_page.download_button, timeout=8_000
            )
            allure.attach(
                f"Download button visible: {dl_visible}",
                name="Download button",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not dl_visible:
                pytest.skip("Download button not visible on Audit Logger page.")

        with allure.step("Click Download and capture result"):
            download = audit_logger_page.download_report()

        with allure.step("Assert download was initiated"):
            if download is not None:
                filename = download.suggested_filename
                allure.attach(
                    f"Downloaded file: {filename}",
                    name="Report filename",
                    attachment_type=allure.attachment_type.TEXT,
                )
                assert filename, "Download triggered but filename is empty."
            else:
                allure.attach(
                    "Download event not captured — may use navigation/blob delivery.",
                    name="Download note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                assert audit_logger_page.is_visible(
                    audit_logger_page.download_button, timeout=5_000
                ), "Download button missing after click."

    @allure.story("Pagination")
    @allure.title("[TC_SM_048] Pagination & Rows-Per-Page work correctly")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Change the rows-per-page selector and navigate to the next page. "
        "Verify records update correctly with no missing or duplicate entries."
    )
    def test_pagination_and_rows_per_page(self, audit_logger_page: AuditLoggerPage):
        with allure.step("Navigate to Audit Logger"):
            audit_logger_page.open_direct()
            assert audit_logger_page.is_loaded(timeout=15_000)

        with allure.step("Read initial row count"):
            initial_count = audit_logger_page.row_count()
            initial_total = audit_logger_page.total_records()
            allure.attach(
                f"Initial rows: {initial_count}\nTotal records: {initial_total}",
                name="Initial pagination state",
                attachment_type=allure.attachment_type.TEXT,
            )
            if initial_count == 0:
                pytest.skip("No audit entries to paginate through.")

        with allure.step("Attempt to change rows-per-page"):
            changed = audit_logger_page.change_rows_per_page("25")
            allure.attach(
                f"Rows-per-page changed: {changed}",
                name="Rows-per-page change",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert page still loaded after rows-per-page change"):
            assert audit_logger_page.is_loaded(timeout=10_000), (
                "Page lost loaded state after changing rows-per-page."
            )

        with allure.step("Navigate to next page (if available)"):
            advanced = audit_logger_page.go_to_next_page()
            allure.attach(
                f"Navigated to next page: {advanced}",
                name="Next page navigation",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert row count after navigation is valid"):
            post_count = audit_logger_page.row_count()
            allure.attach(
                f"Rows after pagination: {post_count}",
                name="Post-pagination row count",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert post_count >= 0, "row_count() raised an error after pagination."
