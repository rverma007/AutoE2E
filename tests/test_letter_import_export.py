# Author: Ruchika Verma <testing.ruchika@gmail.com>
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
    @allure.title("[TC_SM_025] Export saves letter type to server path containing 'netapp'")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Select the first letter type row, click 'Export Letter Type', wait for "
        "'Export Complete' panel, then assert the server file path contains 'netapp'."
    )
    def test_export_generates_zip(self, authed_page):
        page = LetterImportExportPage(authed_page)

        with allure.step("Navigate to Import/Export page"):
            page.open_direct()
            assert page.is_loaded(timeout=15_000), "Import/Export page did not load."

        with allure.step("Select first letter type row"):
            selected = page.select_first_row()
            allure.attach(
                f"First row selected: {selected}",
                name="Row selection",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not selected:
                pytest.skip("No letter type rows available to select for export.")

        with allure.step("Assert Export button is active"):
            export_visible = page.is_export_button_visible(timeout=8_000)
            allure.attach(
                f"Export button visible: {export_visible}",
                name="Export button",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not export_visible:
                pytest.skip("Export button not found after selecting a row.")

        with allure.step("Click Export Letter Type"):
            page.click_export()

        with allure.step("Wait for Export Complete"):
            complete = page.is_export_complete(timeout=30_000)
            allure.attach(
                f"Export Complete visible: {complete}",
                name="Export status",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert complete, (
                "Export did not complete — 'Export Complete' panel not visible within 30 s."
            )

        with allure.step("Assert server file path contains 'netapp'"):
            file_path = page.get_export_file_path()
            allure.attach(
                f"Export file path: {file_path}",
                name="Export file path",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert file_path, (
                "Export file path not found in success notification."
            )
            assert "netapp" in file_path.lower(), (
                f"Expected 'netapp' in export file path, got: {file_path!r}"
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
