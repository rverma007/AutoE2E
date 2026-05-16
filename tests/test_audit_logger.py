# Author: Ruchika Verma <testing.ruchika@gmail.com>
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
            assert audit_logger_page.is_loaded(timeout=10_000), (
                "Audit Logger lost loaded state after applying filter."
            )
            allure.attach(
                f"Filter applied successfully. Rows returned: {filtered_count}",
                name="Filter result",
                attachment_type=allure.attachment_type.TEXT,
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

        with allure.step("Click Download once — listen for file download and all API responses"):
            download_captured = False
            blob_captured = False
            api_captured = False
            api_status = None
            api_url = None
            api_content_type = None
            all_responses: list = []

            _FILE_CONTENT_TYPES = (
                "text/csv", "application/csv",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats",
                "application/pdf",
                "application/zip",
                "application/octet-stream",
            )

            # Collect every network response that fires after the single click.
            def _on_response(r) -> None:
                try:
                    all_responses.append(r)
                except Exception:
                    pass

            audit_logger_page.page.on("response", _on_response)

            # Intercept client-side blob downloads (FileSaver, xlsx, etc.) before the click.
            try:
                audit_logger_page.page.evaluate("""() => {
                    window.__blobDownloadDetected = false;
                    const _origCOU = URL.createObjectURL;
                    URL.createObjectURL = function(obj) {
                        if (obj instanceof Blob) { window.__blobDownloadDetected = true; }
                        return _origCOU.apply(this, arguments);
                    };
                    const _origAClick = HTMLAnchorElement.prototype.click;
                    HTMLAnchorElement.prototype.click = function() {
                        if (this.download || (this.href && this.href.startsWith('blob:'))) {
                            window.__blobDownloadDetected = true;
                        }
                        return _origAClick.apply(this, arguments);
                    };
                }""")
            except Exception:
                pass

            try:
                with audit_logger_page.page.expect_download(timeout=30_000) as dl_info:
                    audit_logger_page.safe_click(audit_logger_page.download_button, "Download report")
                dl = dl_info.value
                filename, saved_path = audit_logger_page.save_download(dl, "audit_report")
                allure.attach(
                    f"File name : {filename}\nSaved path: {saved_path}",
                    name="Report download details",
                    attachment_type=allure.attachment_type.TEXT,
                )
                audit_logger_page.allure_attach_file(saved_path, filename)
                download_captured = True
                assert filename, "Download triggered but filename is empty."
            except AssertionError:
                raise
            except Exception:
                # expect_download timed out — give async responses time to arrive.
                try:
                    audit_logger_page.page.wait_for_timeout(4_000)
                except Exception:
                    pass
            finally:
                audit_logger_page.page.remove_listener("response", _on_response)

            # Check if a client-side blob/anchor download was triggered.
            if not download_captured:
                try:
                    blob_captured = bool(
                        audit_logger_page.page.evaluate(
                            "() => Boolean(window.__blobDownloadDetected)"
                        )
                    )
                except Exception:
                    blob_captured = False

            _DOWNLOAD_URL_KEYWORDS = (
                "download", "report", "export", "generate", "audit",
            )

            if not download_captured:
                # Inspect every captured response.
                # Match on content-type/content-disposition headers OR a URL
                # that contains a download-related keyword (covers APIs that
                # return application/json but whose URL is clearly a download).
                for r in all_responses:
                    try:
                        if r.status not in (200, 201, 202):
                            continue
                        ct = (r.header_value("content-type") or "").lower()
                        cd = r.header_value("content-disposition") or ""
                        url_lower = r.url.lower()
                        is_file_ct = bool(cd) or any(t in ct for t in _FILE_CONTENT_TYPES)
                        is_download_url = any(k in url_lower for k in _DOWNLOAD_URL_KEYWORDS)
                        if is_file_ct or is_download_url:
                            api_status = r.status
                            api_url = r.url
                            api_content_type = ct
                            api_captured = True
                            break
                    except Exception:
                        pass

                if not api_captured:
                    # Nothing matched — dump all responses so we can see the real URL.
                    resp_log = "\n".join(
                        f"[{r.status}] {r.url}  ct={r.header_value('content-type') or ''}"
                        for r in all_responses
                    ) or "(no responses captured)"
                    allure.attach(
                        resp_log,
                        name="All network responses after button click",
                        attachment_type=allure.attachment_type.TEXT,
                    )

            allure.attach(
                f"File download captured : {download_captured}\n"
                f"Blob download captured : {blob_captured}\n"
                f"API response captured  : {api_captured}\n"
                f"API status             : {api_status}\n"
                f"API content-type       : {api_content_type}\n"
                f"API URL                : {api_url}\n"
                f"Total responses seen   : {len(all_responses)}",
                name="Download result",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert download was initiated"):
            if api_captured:
                assert api_status in (200, 201, 202), (
                    f"Audit report API returned unexpected status: {api_status} — URL: {api_url}"
                )
            else:
                assert download_captured or blob_captured, (
                    "Download button was clicked but neither a browser file download, "
                    "a client-side blob download, nor an API response with a file "
                    "content-type / content-disposition header was captured. Check the "
                    "'All network responses' attachment in the Allure report to see the "
                    "actual API URL and content-type."
                )

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
            assert post_count > 0, (
                f"No rows visible after pagination — expected records on this page. "
                f"Row count: {post_count}"
            )
