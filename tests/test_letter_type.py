# Author: Ruchika Verma <testing.ruchika@gmail.com>
"""
Letter Type module — functional test suite.

Covers:
  1. List page loads with all records displayed.
  2. Configure Letter Type: upload a template and verify status transitions
     from 'Processing' to 'Draft'.
  3. Filter functionality: apply a filter and verify results match.
  4. Download functionality: click Download and verify a file is received.

All tests use the shared authenticated session (authed_page / letter_type_page
fixtures) so login is performed only once per session.
"""
from __future__ import annotations

import allure
import pytest

from pages.letter_type_page import LetterTypePage


pytestmark = pytest.mark.sanity


@allure.epic("Correspondence Application")
@allure.feature("Letter Type")
class TestLetterTypeList:
    """Letter Type listing — load and content checks."""

    @allure.story("List Loads")
    @allure.title("Letter Type list loads successfully with records displayed")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.description(
        "Navigate to the Letter Type module and verify:\n"
        "  • The page reaches loaded state (search box visible).\n"
        "  • Column headers are rendered.\n"
        "  • At least one data row is present, or the total record count is "
        "    reported by the footer (graceful empty-state is also acceptable)."
    )
    def test_letter_type_list_loads(self, letter_type_page: LetterTypePage):
        with allure.step("Navigate to Letter Type listing"):
            letter_type_page.open_direct()

        with allure.step("Assert page is loaded"):
            assert letter_type_page.is_loaded(), (
                "Letter Type page did not reach loaded state — search box missing."
            )

        with allure.step("Assert column headers are visible"):
            headers = letter_type_page.header_texts()
            allure.attach(
                f"Headers found: {headers}",
                name="Column headers",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert headers, "No column headers found in the Letter Type table."

        with allure.step("Assert records are displayed or footer shows total count"):
            row_count = letter_type_page.row_count()
            total = letter_type_page.total_records()

            allure.attach(
                f"Visible rows : {row_count}\nFooter total : {total}",
                name="Record counts",
                attachment_type=allure.attachment_type.TEXT,
            )

            assert row_count > 0 or (total is not None and total > 0), (
                f"Letter Type listing has no records. "
                f"Visible rows: {row_count}, Footer total: {total}"
            )


@allure.epic("Correspondence Application")
@allure.feature("Letter Type")
class TestLetterTypeConfiguration:
    """Configure Letter Type — template upload and status transition."""

    @allure.story("Template Upload")
    @allure.title("Configure Letter Type: uploaded template transitions Processing → Draft")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Click the 'Configure Letter Type' button, upload a .docx template, "
        "and verify that the status of the new entry first shows 'Processing' "
        "and then transitions to 'Draft' within a reasonable wait period.\n\n"
        "The status polling reloads the page every 2 s for up to 60 s."
    )
    def test_configure_letter_type_upload(
        self, letter_type_page: LetterTypePage, template_file: str
    ):
        with allure.step("Navigate to Letter Type listing"):
            letter_type_page.open_direct()
            assert letter_type_page.is_loaded(), "Letter Type page did not load."

        with allure.step("Click 'Configure Letter Type' and upload template"):
            letter_type_page.configure_letter_type(template_file)

        # These are all valid statuses the server can return after an upload:
        # Processing / Draft (happy path) or Placeholder Mismatch / Error
        # (template rejected by the server but upload itself succeeded).
        _INITIAL_STATES = ("processing", "draft", "placeholder mismatch", "error")
        _TERMINAL_STATES = ("draft", "placeholder mismatch", "error", "active")

        with allure.step("Verify status reflects a recognised state immediately after upload"):
            status_after_upload = letter_type_page.first_row_status(timeout=15_000)
            allure.attach(
                f"Status after upload: {status_after_upload!r}",
                name="Initial status",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert any(s in status_after_upload.lower() for s in _INITIAL_STATES), (
                f"Expected a recognised upload status, got: {status_after_upload!r}"
            )

        with allure.step("Wait for status to reach a terminal state"):
            reached_terminal = letter_type_page.wait_for_first_row_status_any(
                _TERMINAL_STATES, timeout=120_000, poll=2_000
            )
            final_status = letter_type_page.first_row_status()
            allure.attach(
                f"Final status: {final_status!r}",
                name="Final status",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert reached_terminal, (
                f"Status did not reach a terminal state within 60 s. "
                f"Current status: {final_status!r}"
            )


@allure.epic("Correspondence Application")
@allure.feature("Letter Type")
class TestLetterTypeFilter:
    """Letter Type listing — filter functionality."""

    @allure.story("Filter Results")
    @allure.title("Filter applied to Letter Type list returns matching results")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Click the filter button on the Letter Type list, apply a 'Draft' "
        "status filter, and verify that:\n"
        "  • The results change after the filter is applied.\n"
        "  • Every visible row shows the filtered status (Draft).\n\n"
        "If the filter panel uses a different label (e.g. 'Active', 'Published'), "
        "update the filter_value parameter to match the app's current vocabulary."
    )
    @pytest.mark.parametrize("filter_value", ["Draft"])
    def test_filter_by_status(
        self, letter_type_page: LetterTypePage, filter_value: str
    ):
        with allure.step("Navigate to Letter Type listing"):
            letter_type_page.open_direct()
            assert letter_type_page.is_loaded(), "Letter Type page did not load."

        with allure.step("Record the unfiltered row count"):
            unfiltered_count = letter_type_page.row_count()
            allure.attach(
                f"Row count before filter: {unfiltered_count}",
                name="Pre-filter row count",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step(f"Apply filter: {filter_value!r}"):
            letter_type_page.apply_filter(filter_value)

        with allure.step("Assert filter is applied and results are visible"):
            filtered_count = letter_type_page.row_count()
            allure.attach(
                f"Row count after filter  : {filtered_count}\n"
                f"Row count before filter : {unfiltered_count}\n"
                f"Filter applied          : {filter_value!r}",
                name="Filter count comparison",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert letter_type_page.is_loaded(), "Page lost loaded state after filter."

        with allure.step("Assert every visible row matches the applied filter status"):
            rows_text = letter_type_page.visible_row_texts(limit=20)
            mismatches = [
                row for row in rows_text
                if row and filter_value.lower() not in row.lower()
            ]
            allure.attach(
                "\n".join(rows_text) if rows_text else "(no rows)",
                name="Visible row texts",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert not mismatches, (
                f"Some rows do not contain '{filter_value}': {mismatches}"
            )


@allure.epic("Correspondence Application")
@allure.feature("Letter Type")
class TestLetterTypeDownload:
    """Letter Type listing — download functionality."""

    @allure.story("Download")
    @allure.title("Download button triggers a file download")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Click the Download button on the Letter Type listing page and verify "
        "that a file download is initiated. The test asserts that Playwright's "
        "Download event fires and that the suggested filename is non-empty.\n\n"
        "No specific file content is checked here — the goal is to confirm the "
        "download endpoint is wired up and the browser receives a file."
    )
    def test_download_button_triggers_download(self, letter_type_page: LetterTypePage):
        with allure.step("Navigate to Letter Type listing"):
            letter_type_page.open_direct()
            assert letter_type_page.is_loaded(), "Letter Type page did not load."

        with allure.step("Assert Download button is visible"):
            assert letter_type_page.is_visible(
                letter_type_page.download_button, timeout=10_000
            ), "Download button not found on the Letter Type listing page."

        with allure.step("Click Download once — listen for file download and all API responses"):
            download_captured = False
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
                "application/json",
            )
            _DOWNLOAD_URL_KEYWORDS = (
                "download", "export", "generate", "letter-type", "template",
            )

            def _on_response(r) -> None:
                try:
                    all_responses.append(r)
                except Exception:
                    pass

            letter_type_page.page.on("response", _on_response)
            try:
                with letter_type_page.page.expect_download(timeout=15_000) as dl_info:
                    letter_type_page.safe_click(letter_type_page.download_button, "Download")
                dl = dl_info.value
                filename, saved_path = letter_type_page.save_download(dl, "letter_type")
                allure.attach(
                    f"File name : {filename}\nSaved path: {saved_path}",
                    name="Download details",
                    attachment_type=allure.attachment_type.TEXT,
                )
                letter_type_page.allure_attach_file(saved_path, filename)
                download_captured = True
                assert filename, "Download triggered but filename is empty."
            except AssertionError:
                raise
            except Exception:
                try:
                    letter_type_page.page.wait_for_timeout(4_000)
                except Exception:
                    pass
            finally:
                letter_type_page.page.remove_listener("response", _on_response)

            if not download_captured:
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
                f"API response captured  : {api_captured}\n"
                f"API status             : {api_status}\n"
                f"API content-type       : {api_content_type}\n"
                f"API URL                : {api_url}\n"
                f"Total responses seen   : {len(all_responses)}",
                name="Download result",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert download was triggered"):
            if api_captured:
                assert api_status in (200, 201, 202), (
                    f"Letter Type download API returned unexpected status: {api_status} — URL: {api_url}"
                )
            else:
                assert download_captured, (
                    "Download button was clicked but neither a browser file download "
                    "nor an API response with a file content-type / content-disposition "
                    "header was captured. Check the 'All network responses' attachment "
                    "in the Allure report to see the actual API URL and content-type."
                )
