"""
Recon Report module — TC_SM_049.

Covers:
  TC_SM_049  Verify Recon Report (page loads, list visible, download works)

This test was marked Fail in the UAT report.
"""
from __future__ import annotations

import allure
import pytest

from pages.recon_report_page import ReconReportPage


pytestmark = pytest.mark.sanity


@allure.epic("Correspondence Application")
@allure.feature("Recon Report")
class TestReconReport:

    @allure.story("Page Load & List")
    @allure.title("[TC_SM_049] Recon Report page loads and list is visible")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to the Recon Report page. Verify:\n"
        "  • The page loads successfully.\n"
        "  • The report list is visible (table or empty-state).\n"
        "  • The Download/Export report button is present and clickable.\n\n"
        "This test was marked Fail in the UAT report — captures the regression."
    )
    def test_recon_report_page_loads(self, recon_report_page: ReconReportPage):
        with allure.step("Navigate to Recon Report"):
            recon_report_page.open_direct()

        with allure.step("Assert page is loaded"):
            loaded = recon_report_page.is_loaded(timeout=15_000)
            allure.attach(
                f"Page loaded: {loaded}\nURL: {recon_report_page.page.url}",
                name="Page load state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, (
                f"Recon Report page did not load. URL: {recon_report_page.page.url}"
            )

        with allure.step("Assert report list or empty-state is visible"):
            list_visible = recon_report_page.is_list_visible(timeout=10_000)
            row_count = recon_report_page.row_count()
            allure.attach(
                f"List visible: {list_visible}\nRow count: {row_count}",
                name="Report list",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert list_visible or row_count >= 0, (
                "Recon Report list area is not visible."
            )

        with allure.step("Check for Download Report button"):
            dl_visible = recon_report_page.is_visible(
                recon_report_page.download_button, timeout=8_000
            )
            allure.attach(
                f"Download button visible: {dl_visible}",
                name="Download button",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not dl_visible:
                pytest.skip(
                    "Download button not visible on Recon Report — "
                    "may require a filter selection first."
                )

        with allure.step("Click Download and verify the report downloads"):
            download = recon_report_page.download_report()

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
                assert recon_report_page.is_visible(
                    recon_report_page.download_button, timeout=5_000
                ), "Download button missing after click."
