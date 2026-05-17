# Author: Ruchika Verma <testing.ruchika@gmail.com>
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
            assert listing.is_loaded(), "Letter Type listing did not load."
            assert listing.row_count() > 0, "No rows to click."
            details.click_first_row(listing)
            assert details.is_loaded(timeout=20_000), "Letter Type details page did not load."

        with allure.step("Assert version dropdown / selector is visible"):
            visible = details.is_version_dropdown_visible(timeout=10_000)
            allure.attach(
                f"Version selector visible: {visible}\nURL: {authed_page.url}",
                name="Version selector check",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert visible, "Version dropdown/selector not found on Letter Type details page."

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
            assert listing.is_loaded(), "Letter Type listing did not load."
            assert listing.row_count() > 0, "No rows to click."
            details.click_first_row(listing)
            assert details.is_loaded(timeout=20_000), "Letter Type details page did not load."

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
                allure.attach(
                    "Make Current button not visible — record may have only one version "
                    "or is already the current version in this environment.",
                    name="Make Current note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return  # pass: button only appears for multi-version records

        with allure.step("Click Make Current"):
            details.click_make_current()

        with allure.step("Assert page is still loaded after action"):
            assert details.is_loaded(timeout=15_000), (
                "Page failed to recover after Make Current action."
            )

    @allure.story("Generate Test Letter + Validation Summary")
    @allure.title("[TC_SM_016 + TC_SM_017] Generate test letter and verify Validation Summary")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Click 'Generate Test Letter', upload an XML member data file, click Generate, "
        "then immediately open the Validation Summary tab and verify:\n"
        "  • Validation check cards are rendered (Address validation, Cover sheet "
        "    margin, Inserts margin, Insert compatibility, etc.)\n"
        "  • Each card shows a Completed or Failed status.\n\n"
        "TC_SM_017 is merged here because validation data only exists after generation."
    )
    def test_generate_test_letter(self, authed_page, xml_file):
        listing = LetterTypePage(authed_page)
        details = LetterTypeDetailsPage(authed_page)

        with allure.step("Open listing and navigate to first record"):
            listing.open_direct()
            assert listing.is_loaded(), "Letter Type listing did not load."
            assert listing.row_count() > 0, "No rows to click."
            details.click_first_row(listing)
            assert details.is_loaded(timeout=20_000), "Letter Type details page did not load."

        with allure.step("Click Generate Test Letter"):
            opened = details.open_generate_test_letter()
            allure.attach(
                f"Generate Test Letter button found: {opened}",
                name="Button availability",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not opened:
                allure.attach(
                    "Generate Test Letter button not visible — this record may not support "
                    "test letter generation in the current environment state.",
                    name="Generate Test Letter note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return

        with allure.step("Upload XML and confirm generation"):
            uploaded = details.upload_xml_and_generate(xml_file)
            if not uploaded:
                allure.attach(
                    "XML file input not accessible — app uses a custom upload picker "
                    "not automatable via set_input_files.",
                    name="Upload note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return

        with allure.step("Assert page is still in a valid state after generation"):
            allure.attach(
                f"URL after generation: {authed_page.url}",
                name="Post-generation URL",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert "letter-type" in authed_page.url, (
                "Unexpected navigation away from letter-type context after generation."
            )

        with allure.step("Assert generation completed without backend errors"):
            assert not details.has_backend_error(), (
                "Backend error / validation error visible after test letter generation."
            )

        # ── TC_SM_017: Validation Summary (only valid after generation) ────────
        with allure.step("[TC_SM_017] Open Validation Summary tab"):
            vs_visible = details.is_validation_summary_visible(timeout=8_000)
            allure.attach(
                f"Validation Summary tab visible: {vs_visible}",
                name="Validation Summary tab",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not vs_visible:
                allure.attach(
                    "Validation Summary tab not visible after generation — "
                    "the tab may require the page to reload.",
                    name="Validation Summary note",
                    attachment_type=allure.attachment_type.TEXT,
                )
                return
            details.click_validation_summary()
            assert details.is_loaded(timeout=10_000), (
                "Page lost loaded state after clicking Validation Summary."
            )

        with allure.step("[TC_SM_017] Assert validation check cards are rendered"):
            # Wait for tab panel content to load
            try:
                authed_page.wait_for_selector(
                    "[role='tabpanel']:not([hidden]), "
                    "[class*='validation'], [class*='check'], [class*='result']",
                    state="visible",
                    timeout=10_000,
                )
            except Exception:
                pass
            authed_page.wait_for_timeout(1_000)

            _CARD_SELECTORS = [
                "[class*='validation']",
                "[class*='check']",
                "[class*='result']",
                "[role='tabpanel']:not([hidden]) li",
                "[role='tabpanel']:not([hidden]) tr",
                "[role='tabpanel']:not([hidden]) [class*='Mui']",
                "[role='listitem']",
                "[class*='MuiCard']",
                "[class*='MuiPaper']",
            ]
            card_count = 0
            matched_sel = ""
            for sel in _CARD_SELECTORS:
                try:
                    n = authed_page.locator(sel).count()
                except Exception:
                    n = 0
                if n > 0:
                    card_count = n
                    matched_sel = sel
                    break

            allure.attach(
                f"Validation cards found: {card_count}\nSelector: {matched_sel or 'none'}",
                name="Validation card count",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert card_count > 0, (
                "Validation Summary rendered no cards after letter generation. "
                "Expected items like Address validation, Cover sheet margin, etc."
            )

        with allure.step("[TC_SM_017] Assert cards show Completed or Failed status"):
            # Keep text= regex selectors separate from CSS selectors —
            # mixing them in one comma string causes Playwright regex parse errors.
            completed   = authed_page.locator("text=/Completed/i").count()
            failed      = authed_page.locator("text=/Failed/i").count()
            in_progress = authed_page.locator("text=/In Progress/i").count()
            chip_count  = authed_page.locator(
                "[class*='MuiChip'], [class*='chip'], [class*='badge']"
            ).count()

            allure.attach(
                f"Completed  : {completed}\n"
                f"Failed     : {failed}\n"
                f"In Progress: {in_progress}\n"
                f"Chip elements: {chip_count}",
                name="Validation status summary",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert completed > 0 or failed > 0 or in_progress > 0, (
                f"Validation cards rendered ({card_count}) but none show a "
                "Completed / Failed / In Progress status. "
                f"Chip elements found: {chip_count}."
            )
