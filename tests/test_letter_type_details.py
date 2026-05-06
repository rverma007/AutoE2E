"""
Letter Type Details module — TC_SM_013 to TC_SM_017.

Covers:
  TC_SM_013  Letter Type Details Page Loads Correctly
  TC_SM_014  Letter type versioning (version dropdown visible)
  TC_SM_015  Letter type version: Make Current
  TC_SM_016  Letter type: Generate test letter (XML upload → generate)
  TC_SM_017  Validation Summary Executes Successfully

All tests navigate from the letter-type listing to a detail record by
clicking the first available data row.
"""
from __future__ import annotations

import allure
import pytest

from pages.letter_type_details_page import LetterTypeDetailsPage
from pages.letter_type_page import LetterTypePage


pytestmark = pytest.mark.sanity


@allure.epic("Correspondence Application")
@allure.feature("Letter Type – Details")
class TestLetterTypeDetails:

    @allure.story("Page Load")
    @allure.title("[TC_SM_013] Letter Type Details page loads correctly")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Navigate to the Letter Type listing, click the first record, and confirm "
        "the detail page loads with visible content."
    )
    def test_details_page_loads(self, authed_page):
        listing = LetterTypePage(authed_page)
        details = LetterTypeDetailsPage(authed_page)

        with allure.step("Open Letter Type listing"):
            listing.open_direct()
            assert listing.is_loaded(), "Letter Type listing did not load."

        with allure.step("Confirm at least one row exists"):
            row_count = listing.row_count()
            allure.attach(
                f"Rows found: {row_count}",
                name="Row count",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0, (
                "No rows in Letter Type listing — cannot navigate to details."
            )

        with allure.step("Click first row to open details"):
            details.click_first_row(listing)

        with allure.step("Assert details page loaded"):
            loaded = details.is_loaded(timeout=20_000)
            allure.attach(
                f"URL after click: {authed_page.url}",
                name="Post-click URL",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, (
                f"Letter Type details page did not load. URL: {authed_page.url}"
            )

    @allure.story("Versioning")
    @allure.title("[TC_SM_014] Letter type versioning dropdown is visible")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Open a letter type detail page and verify that a version selector "
        "(dropdown or badge) is present, indicating versioning is active."
    )
    def test_version_dropdown_visible(self, authed_page):
        listing = LetterTypePage(authed_page)
        details = LetterTypeDetailsPage(authed_page)

        with allure.step("Open listing and navigate to first record"):
            listing.open_direct()
            assert listing.is_loaded()
            assert listing.row_count() > 0, "No rows to click."
            details.click_first_row(listing)
            assert details.is_loaded(timeout=20_000)

        with allure.step("Assert version dropdown / selector is visible"):
            visible = details.is_version_dropdown_visible(timeout=10_000)
            allure.attach(
                f"Version selector visible: {visible}\nURL: {authed_page.url}",
                name="Version selector check",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert visible, (
                "Version dropdown/selector not found on Letter Type details page."
            )

    @allure.story("Make Current")
    @allure.title("[TC_SM_015] Letter type version: Make Current")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Open a letter type with multiple versions and click 'Make Current' on a "
        "non-current version. Verify the action completes without error."
    )
    def test_make_current(self, authed_page):
        listing = LetterTypePage(authed_page)
        details = LetterTypeDetailsPage(authed_page)

        with allure.step("Open listing and navigate to first record"):
            listing.open_direct()
            assert listing.is_loaded()
            assert listing.row_count() > 0, "No rows to click."
            details.click_first_row(listing)
            assert details.is_loaded(timeout=20_000)

        with allure.step("Check Make Current button visibility"):
            make_current_visible = details.is_visible(
                details.make_current_button, timeout=8_000
            )
            allure.attach(
                f"Make Current button visible: {make_current_visible}",
                name="Make Current availability",
                attachment_type=allure.attachment_type.TEXT,
            )

        if not make_current_visible:
            pytest.skip(
                "Make Current button not visible — record may have only one version "
                "or may already be current."
            )

        with allure.step("Click Make Current"):
            details.click_make_current()

        with allure.step("Assert page is still loaded after action"):
            assert details.is_loaded(timeout=15_000), (
                "Page failed to recover after Make Current action."
            )

    @allure.story("Generate Test Letter")
    @allure.title("[TC_SM_016] Letter type: Generate test letter with XML upload")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Click 'Generate Test Letter' on a letter type detail page, upload an XML "
        "member data file, click Generate, and verify the action completes."
    )
    def test_generate_test_letter(self, authed_page, xml_file):
        listing = LetterTypePage(authed_page)
        details = LetterTypeDetailsPage(authed_page)

        with allure.step("Open listing and navigate to first record"):
            listing.open_direct()
            assert listing.is_loaded()
            assert listing.row_count() > 0, "No rows to click."
            details.click_first_row(listing)
            assert details.is_loaded(timeout=20_000)

        with allure.step("Click Generate Test Letter"):
            opened = details.open_generate_test_letter()
            allure.attach(
                f"Generate Test Letter button found: {opened}",
                name="Button availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not opened:
                pytest.skip("Generate Test Letter button not visible on this record.")

        with allure.step("Upload XML and confirm generation"):
            details.upload_xml_and_generate(xml_file)

        with allure.step("Assert page is still in a valid state"):
            allure.attach(
                f"URL after generation: {authed_page.url}",
                name="Post-generation URL",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert "letter-type" in authed_page.url, (
                "Unexpected navigation away from letter-type context after generation."
            )

    @allure.story("Validation Summary")
    @allure.title("[TC_SM_017] Validation Summary executes successfully")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to the letter type detail page and open the Validation Summary "
        "tab/section. Verify it loads without errors."
    )
    def test_validation_summary(self, authed_page):
        listing = LetterTypePage(authed_page)
        details = LetterTypeDetailsPage(authed_page)

        with allure.step("Open listing and navigate to first record"):
            listing.open_direct()
            assert listing.is_loaded()
            assert listing.row_count() > 0, "No rows to click."
            details.click_first_row(listing)
            assert details.is_loaded(timeout=20_000)

        with allure.step("Check Validation Summary tab availability"):
            vs_visible = details.is_validation_summary_visible(timeout=8_000)
            allure.attach(
                f"Validation Summary tab visible: {vs_visible}",
                name="Validation Summary availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not vs_visible:
                pytest.skip(
                    "Validation Summary tab not visible — may require a generated letter."
                )

        with allure.step("Click Validation Summary"):
            details.click_validation_summary()

        with allure.step("Assert page is still loaded after clicking Validation Summary"):
            assert details.is_loaded(timeout=10_000), (
                "Page failed to recover after Validation Summary click."
            )
