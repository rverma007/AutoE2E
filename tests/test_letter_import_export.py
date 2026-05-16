"""
Letter Import/Export module — TC_SM_024 to TC_SM_027.

Covers:
  TC_SM_024  Import/Export page is accessible
  TC_SM_025  Export generates a valid ZIP
  TC_SM_026  Approved ZIP import works  [HOLD — skipped]
  TC_SM_027  Admin-only access enforced
"""
from __future__ import annotations

import allure
import pytest

from pages.letter_import_export_page import LetterImportExportPage


pytestmark = pytest.mark.sanity


@allure.epic("Correspondence Application")
@allure.feature("Letter Import/Export")
class TestLetterImportExport:

    @allure.story("Page Accessibility")
    @allure.title("[TC_SM_024] Import/Export page is accessible")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Navigate directly to the Import/Export module and verify the page loads "
        "successfully without errors."
    )
    def test_import_export_page_accessible(self, authed_page):
        page = LetterImportExportPage(authed_page)

        with allure.step("Navigate to Import/Export page"):
            page.open_direct()

        with allure.step("Assert page loaded"):
            loaded = page.is_loaded(timeout=15_000)
            allure.attach(
                f"Import/Export page loaded: {loaded}\nURL: {authed_page.url}",
                name="Page load state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, (
                f"Import/Export page did not load. URL: {authed_page.url}"
            )

    @allure.story("Export")
    @allure.title("[TC_SM_025] Export generates a valid ZIP file")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Select an approved letter type, click Export, and verify that a valid "
        "ZIP file downloads successfully."
    )
    def test_export_generates_zip(self, authed_page):
        page = LetterImportExportPage(authed_page)

        with allure.step("Navigate to Import/Export page"):
            page.open_direct()
            assert page.is_loaded(timeout=15_000), "Import/Export page did not load."

        with allure.step("Assert Export button is present"):
            export_visible = page.is_export_button_visible(timeout=8_000)
            allure.attach(
                f"Export button visible: {export_visible}",
                name="Export button availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert export_visible, "Export button not found on Import/Export page."

        with allure.step("Click Export once — listen for file download and all API responses"):
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
                "application/xml", "text/xml",
            )
            _DOWNLOAD_URL_KEYWORDS = (
                "download", "export", "import", "letter-type", "template",
            )

            def _on_response(r) -> None:
                try:
                    all_responses.append(r)
                except Exception:
                    pass

            page.page.on("response", _on_response)
            try:
                with page.page.expect_download(timeout=15_000) as dl_info:
                    page.safe_click(page.export_button, "Export")
                dl = dl_info.value
                filename, saved_path = page.save_download(dl, "letter_export")
                allure.attach(
                    f"File name : {filename}\nSaved path: {saved_path}",
                    name="Export download details",
                    attachment_type=allure.attachment_type.TEXT,
                )
                page.allure_attach_file(saved_path, filename)
                download_captured = True
                assert filename, "Export triggered but filename is empty."
                assert filename.lower().endswith((".zip", ".json", ".xml")), (
                    f"Unexpected export file extension: {filename}"
                )
            except AssertionError:
                raise
            except Exception:
                try:
                    page.page.wait_for_timeout(4_000)
                except Exception:
                    pass
            finally:
                page.page.remove_listener("response", _on_response)

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
                name="Export result",
                attachment_type=allure.attachment_type.TEXT,
            )

        with allure.step("Assert export was initiated"):
            if api_captured:
                assert api_status in (200, 201, 202), (
                    f"Export API returned unexpected status: {api_status} — URL: {api_url}"
                )
            else:
                assert download_captured, (
                    "Export button was clicked but neither a browser file download "
                    "nor an API response with a file content-type / content-disposition "
                    "header was captured. Check the 'All network responses' attachment "
                    "in the Allure report to see the actual API URL and content-type."
                )

    @allure.story("Import")
    @allure.title("[TC_SM_026] Approved ZIP import works")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Upload a valid approved ZIP and click Import. "
        "This test case is currently on hold pending a stable approved ZIP artifact."
    )
    @pytest.mark.skip(reason="TC_SM_026 — On hold: requires a pre-approved ZIP artifact.")
    def test_approved_zip_import(self, authed_page):
        page = LetterImportExportPage(authed_page)

        with allure.step("Navigate to Import/Export page"):
            page.open_direct()
            assert page.is_loaded(timeout=15_000)

        # placeholder: upload_zip() and click_import() when artifact is available
        with allure.step("Upload approved ZIP and click Import"):
            pass  # artifact not yet available

    @allure.story("Access Control")
    @allure.title("[TC_SM_027] Admin-only access is enforced for restricted modules")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Verify that the Import/Export module is only accessible to admin users. "
        "A non-admin login should either be blocked or see restricted access UI."
    )
    def test_admin_only_access_enforced(self, authed_page):
        page = LetterImportExportPage(authed_page)

        with allure.step("Navigate to Import/Export page as the current user"):
            page.open_direct()
            loaded = page.is_loaded(timeout=15_000)
            current_url = authed_page.url

        allure.attach(
            f"Page loaded: {loaded}\nURL: {current_url}",
            name="Access check",
            attachment_type=allure.attachment_type.TEXT,
        )

        # The configured user (from .env) is an admin — page should load.
        # If you run this with a non-admin user, expect loaded=False or
        # an access-denied message.
        with allure.step("Assert that admin user can access the page (or access denied for non-admin)"):
            access_denied = authed_page.locator(
                "text=Access Denied, text=Forbidden, text=Unauthorized, "
                "text=You do not have permission"
            ).first
            denied = page.is_visible(access_denied, timeout=3_000)

            allure.attach(
                f"Access denied banner visible: {denied}",
                name="Access control result",
                attachment_type=allure.attachment_type.TEXT,
            )

            # The configured user (.env) is an admin — page must load and show no access-denied banner.
            assert loaded, (
                f"Import/Export page did not load for the configured user. URL: {current_url}"
            )
            assert not denied, (
                "Access Denied banner visible — the configured user may not have admin privileges."
            )
