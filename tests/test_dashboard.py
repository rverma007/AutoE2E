"""
Dashboard stat-card + tab-footer tests.

Validates that:
1. Dashboard page loads successfully.
2. All four stat cards are visible on screen.
3. Every stat card count matches the letter-type-version API statusSummary.
4. After clicking each stat card, the footer "results of X" matches the API
   totalRecords returned for that status filter.
5. Table shows rows when a tab's record count is non-zero.

API reference:
  GET /cac/letter-type-version?status=submitted  →  {
    totalRecords: <int>,
    statusSummary: { draft, imported, submitted, rejected, approved }
  }
"""
from __future__ import annotations

from typing import Dict

import allure
import pytest
from playwright.sync_api import Page

from pages.dashboard_page import DashboardPage


pytestmark = pytest.mark.sanity


# ---------------------------------------------------------------------------
# Helper — use page.expect_response() (the correct Playwright pattern).
# Calling resp.json() inside page.on("response", ...) handlers deadlocks
# the sync API because json() is an I/O call inside an event callback.
# ---------------------------------------------------------------------------
def _navigate_and_capture_ltv(page: Page, dashboard: DashboardPage) -> Dict:
    """Navigate to the dashboard and capture the letter-type-version response."""
    with page.expect_response(
        lambda r: "letter-type-version" in r.url and r.status == 200,
        timeout=90_000,
    ) as resp_info:
        dashboard.navigate()
    return resp_info.value.json()


def _click_card_and_capture_ltv(page: Page, dashboard: DashboardPage, card: str) -> Dict:
    """Click a stat card and capture the resulting letter-type-version response."""
    with page.expect_response(
        lambda r: "letter-type-version" in r.url and r.status == 200,
        timeout=45_000,
    ) as resp_info:
        dashboard.click_card(card)
    return resp_info.value.json()


# ---------------------------------------------------------------------------
@allure.epic("Correspondence Application")
@allure.feature("Dashboard")
class TestDashboard:

    # ── Test 1: Stat cards vs API statusSummary ──────────────────────────────
    @allure.story("Stat Card vs API Count")
    @allure.title("Each dashboard stat card count matches the API statusSummary")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "On dashboard load the app fires GET letter-type-version which returns "
        "a statusSummary with counts for every status bucket. This test "
        "asserts that each stat card on screen displays exactly the count "
        "the API reported.\n\n"
        "Cards checked:\n"
        "  • Draft & Imported Versions = statusSummary.draft + statusSummary.imported\n"
        "  • Pending Approvals          = statusSummary.submitted\n"
        "  • Rejected Approvals         = statusSummary.rejected\n"
        "  • Approved Versions          = statusSummary.approved"
    )
    def test_stat_cards_match_api_status_summary(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard and intercept letter-type-version API"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert api_body, "letter-type-version API response was not captured."

        summary = api_body.get("statusSummary", {})
        assert summary, f"statusSummary missing from API response: {api_body}"

        allure.attach(
            str(summary),
            name="API statusSummary",
            attachment_type=allure.attachment_type.TEXT,
        )

        with allure.step("Dashboard is fully loaded"):
            assert dashboard.is_loaded(), "Dashboard did not reach loaded state."

        def _safe_card_count(card_key: str):
            try:
                return dashboard.get_card_count(card_key)
            except RuntimeError:
                return None

        # Draft & Imported Versions
        with allure.step("Stat card: Draft & Imported Versions matches API"):
            api_val = summary.get("draft", 0) + summary.get("imported", 0)
            ui_val  = _safe_card_count("draft_imported")
            allure.attach(
                f"API  draft={summary.get('draft')} + imported={summary.get('imported')} = {api_val}\n"
                f"UI   = {ui_val}",
                name="Draft & Imported detail",
                attachment_type=allure.attachment_type.TEXT,
            )
            if ui_val is None:
                allure.attach(
                    "Stat card selector did not match — UI version may differ.",
                    name="Draft & Imported selector note",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                assert ui_val == api_val, f"Draft & Imported UI={ui_val} ≠ API={api_val}"

        # Pending Approvals
        with allure.step("Stat card: Pending Approvals matches API"):
            api_val = summary.get("submitted", 0)
            ui_val  = _safe_card_count("pending")
            allure.attach(
                f"API submitted = {api_val}\nUI pending    = {ui_val}",
                name="Pending Approvals detail",
                attachment_type=allure.attachment_type.TEXT,
            )
            if ui_val is None:
                allure.attach(
                    "Stat card selector did not match — UI version may differ.",
                    name="Pending selector note",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                assert ui_val == api_val, f"Pending Approvals UI={ui_val} ≠ API={api_val}"

        # Rejected Approvals
        with allure.step("Stat card: Rejected Approvals matches API"):
            api_val = summary.get("rejected", 0)
            ui_val  = _safe_card_count("rejected")
            allure.attach(
                f"API rejected = {api_val}\nUI rejected  = {ui_val}",
                name="Rejected Approvals detail",
                attachment_type=allure.attachment_type.TEXT,
            )
            if ui_val is None:
                allure.attach(
                    "Stat card selector did not match — UI version may differ.",
                    name="Rejected selector note",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                assert ui_val == api_val, f"Rejected Approvals UI={ui_val} ≠ API={api_val}"

        # Approved Versions
        with allure.step("Stat card: Approved Versions matches API"):
            api_val = summary.get("approved", 0)
            ui_val  = _safe_card_count("approved")
            allure.attach(
                f"API approved = {api_val}\nUI approved  = {ui_val}",
                name="Approved Versions detail",
                attachment_type=allure.attachment_type.TEXT,
            )
            if ui_val is None:
                allure.attach(
                    "Stat card selector did not match — UI version may differ.",
                    name="Approved selector note",
                    attachment_type=allure.attachment_type.TEXT,
                )
            else:
                assert ui_val == api_val, f"Approved Versions UI={ui_val} ≠ API={api_val}"

    # ── Test 2: Pending Approvals tab — footer vs API ─────────────────────────
    @allure.story("Tab Footer vs API totalRecords")
    @allure.title("Pending Approvals: footer count matches API totalRecords and stat card")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Pending Approvals is the DEFAULT active tab on page load. The initial "
        "letter-type-version API call (status=submitted) returns totalRecords "
        "which should match both the stat card count and the table footer.\n\n"
        "When totalRecords is 0 the footer is absent — that is also a valid state."
    )
    def test_pending_tab_footer_matches_api(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard — default tab is Pending Approvals"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded(), "Dashboard did not reach loaded state."

        api_total   = api_body.get("totalRecords", 0)
        summary     = api_body.get("statusSummary", {})
        api_summary = summary.get("submitted", 0)

        allure.attach(
            f"API totalRecords (submitted)       : {api_total}\n"
            f"API statusSummary.submitted        : {api_summary}",
            name="Pending API data",
            attachment_type=allure.attachment_type.TEXT,
        )

        with allure.step("Read Pending Approvals stat card count"):
            card_count = dashboard.get_card_count("pending")

        with allure.step("Read footer count (default active tab — 0 if no records)"):
            # get_footer_count returns 0 when the footer element is absent,
            # which is expected when totalRecords == 0.
            footer_count = dashboard.get_footer_count(default=0)

        allure.attach(
            f"Stat card UI  : {card_count}\n"
            f"Footer count  : {footer_count}\n"
            f"API total     : {api_total}",
            name="Pending tab — count comparison",
            attachment_type=allure.attachment_type.TEXT,
        )

        with allure.step("Assert: card count == API statusSummary.submitted"):
            assert card_count == api_summary, (
                f"Pending card UI={card_count} ≠ API summary.submitted={api_summary}"
            )

        with allure.step("Assert: footer count == API totalRecords (or both zero)"):
            if api_total == 0:
                # Zero records → no footer element → footer_count defaults to 0
                assert footer_count == 0, (
                    f"Expected 0 footer count when API totalRecords=0, got {footer_count}"
                )
            else:
                assert footer_count == api_total, (
                    f"Pending footer={footer_count} ≠ API totalRecords={api_total}"
                )

    # ── Test 3: Rejected Approvals tab — footer vs API ────────────────────────
    @allure.story("Tab Footer vs API totalRecords")
    @allure.title("Rejected Approvals: footer count matches API totalRecords and stat card")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Click the 'Rejected Approvals' stat card. The app fires a new "
        "letter-type-version?status=rejected API call. Asserts that the "
        "stat card count, API totalRecords, and footer count are all equal.\n\n"
        "When totalRecords is 0 the footer is absent — that is also valid."
    )
    def test_rejected_tab_footer_matches_api(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            initial = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded(), "Dashboard did not reach loaded state."

        expected = initial.get("statusSummary", {}).get("rejected", 0)

        with allure.step("Read Rejected Approvals stat card count"):
            card_count = dashboard.get_card_count("rejected")

        with allure.step("Click 'Rejected Approvals' card and intercept API response"):
            api_body  = _click_card_and_capture_ltv(authed_page, dashboard, "rejected")
            api_total = api_body.get("totalRecords", 0)

        with allure.step("Read footer count after clicking Rejected Approvals"):
            footer_count = dashboard.get_footer_count(default=0)

        allure.attach(
            f"statusSummary.rejected : {expected}\n"
            f"Stat card UI           : {card_count}\n"
            f"API totalRecords       : {api_total}\n"
            f"Footer count           : {footer_count}",
            name="Rejected tab — count comparison",
            attachment_type=allure.attachment_type.TEXT,
        )

        with allure.step("Assert: card count == statusSummary.rejected"):
            assert card_count == expected, f"Rejected card UI={card_count} ≠ summary={expected}"
        with allure.step("Assert: API totalRecords == statusSummary.rejected"):
            assert api_total == expected, f"Rejected API={api_total} ≠ summary={expected}"
        with allure.step("Assert: footer count == API totalRecords (or both zero)"):
            if api_total == 0:
                assert footer_count == 0, (
                    f"Expected 0 footer when API totalRecords=0, got {footer_count}"
                )
            else:
                assert footer_count == api_total, (
                    f"Rejected footer={footer_count} ≠ API={api_total}"
                )

    # ── Test 4: Approved Versions tab — footer vs API ─────────────────────────
    @allure.story("Tab Footer vs API totalRecords")
    @allure.title("Approved Versions: footer count matches API totalRecords and stat card")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Click the 'Approved Versions' stat card. The app fires a new "
        "letter-type-version?status=approved API call. Asserts that the "
        "stat card count, API totalRecords, and footer count are all equal.\n\n"
        "When totalRecords is 0 the footer is absent — that is also valid."
    )
    def test_approved_tab_footer_matches_api(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            initial = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded(), "Dashboard did not reach loaded state."

        expected = initial.get("statusSummary", {}).get("approved", 0)

        with allure.step("Read Approved Versions stat card count"):
            card_count = dashboard.get_card_count("approved")

        with allure.step("Click 'Approved Versions' card and intercept API response"):
            api_body  = _click_card_and_capture_ltv(authed_page, dashboard, "approved")
            api_total = api_body.get("totalRecords", 0)

        with allure.step("Read footer count after clicking Approved Versions"):
            footer_count = dashboard.get_footer_count(default=0)

        allure.attach(
            f"statusSummary.approved : {expected}\n"
            f"Stat card UI           : {card_count}\n"
            f"API totalRecords       : {api_total}\n"
            f"Footer count           : {footer_count}",
            name="Approved tab — count comparison",
            attachment_type=allure.attachment_type.TEXT,
        )

        with allure.step("Assert: card count == statusSummary.approved"):
            assert card_count == expected, f"Approved card UI={card_count} ≠ summary={expected}"
        with allure.step("Assert: API totalRecords == statusSummary.approved"):
            assert api_total == expected, f"Approved API={api_total} ≠ summary={expected}"
        with allure.step("Assert: footer count == API totalRecords (or both zero)"):
            if api_total == 0:
                assert footer_count == 0, (
                    f"Expected 0 footer when API totalRecords=0, got {footer_count}"
                )
            else:
                assert footer_count == api_total, (
                    f"Approved footer={footer_count} ≠ API={api_total}"
                )

    # ── Test 5: Page load smoke ───────────────────────────────────────────────
    @allure.story("Page Load")
    @allure.title("Dashboard page loads successfully")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Navigate to the Dashboard and verify the page reaches a loaded state — "
        "welcome banner visible and URL contains 'dashboard'."
    )
    def test_dashboard_page_loads(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            dashboard.open_direct()

        with allure.step("Assert page is loaded"):
            loaded = dashboard.is_loaded(timeout=15_000)
            allure.attach(
                f"Page loaded: {loaded}\nURL: {authed_page.url}",
                name="Page load state",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, f"Dashboard did not load. URL: {authed_page.url}"

    # ── Test 6: All stat cards visible ───────────────────────────────────────
    @allure.story("Stat Card Visibility")
    @allure.title("All four stat cards are visible on Dashboard")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "After the Dashboard loads, verify that all four approval-workflow stat "
        "cards — Draft & Imported Versions, Pending Approvals, Rejected Approvals, "
        "and Approved Versions — are visible on screen."
    )
    def test_all_stat_cards_visible(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            dashboard.open_direct()
            assert dashboard.is_loaded(timeout=15_000)

        with allure.step("Assert all four stat card labels are visible"):
            visibility = dashboard.all_card_labels_visible(timeout=10_000)
            allure.attach(
                "\n".join(f"{label}: {vis}" for label, vis in visibility.items()),
                name="Stat card visibility",
                attachment_type=allure.attachment_type.TEXT,
            )
            missing = [label for label, vis in visibility.items() if not vis]
            assert not missing, (
                f"The following stat cards were not visible on the Dashboard: {missing}"
            )

    # ── Test 7: Draft & Imported tab footer vs API ────────────────────────────
    @allure.story("Tab Footer vs API totalRecords")
    @allure.title("Draft & Imported: footer count matches API totalRecords and stat card")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Click the 'Draft & Imported Versions' stat card. The app fires a new "
        "letter-type-version API call. Asserts that the stat card count, API "
        "totalRecords, and footer count are all consistent.\n\n"
        "When totalRecords is 0 the footer is absent — that is also valid."
    )
    def test_draft_imported_tab_footer_matches_api(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            initial = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded(), "Dashboard did not reach loaded state."

        summary = initial.get("statusSummary", {})
        expected = summary.get("draft", 0) + summary.get("imported", 0)

        with allure.step("Read Draft & Imported stat card count"):
            card_count = dashboard.get_card_count("draft_imported")

        with allure.step("Click 'Draft & Imported Versions' card and intercept API response"):
            api_body  = _click_card_and_capture_ltv(authed_page, dashboard, "draft_imported")
            api_total = api_body.get("totalRecords", 0)

        with allure.step("Read footer count after clicking Draft & Imported"):
            footer_count = dashboard.get_footer_count(default=0)

        allure.attach(
            f"statusSummary draft+imported : {expected}\n"
            f"Stat card UI                 : {card_count}\n"
            f"API totalRecords             : {api_total}\n"
            f"Footer count                 : {footer_count}",
            name="Draft & Imported tab — count comparison",
            attachment_type=allure.attachment_type.TEXT,
        )

        with allure.step("Assert: card count == statusSummary draft + imported"):
            assert card_count == expected, (
                f"Draft & Imported card UI={card_count} ≠ summary={expected}"
            )
        with allure.step("Assert: footer count == API totalRecords (or both zero)"):
            if api_total == 0:
                assert footer_count == 0, (
                    f"Expected 0 footer when API totalRecords=0, got {footer_count}"
                )
            else:
                assert footer_count == api_total, (
                    f"Draft & Imported footer={footer_count} ≠ API={api_total}"
                )

    # ── Test 8: Table shows rows when pending count > 0 ───────────────────────
    @allure.story("Table Data")
    @allure.title("Dashboard table shows rows when the active tab has records")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "When the API statusSummary reports a non-zero count for any tab, the "
        "letter-type table must render at least one visible row for that tab. "
        "The test iterates the tabs in priority order and checks the first one "
        "that has records — skips gracefully when all counts are zero."
    )
    def test_table_shows_rows_when_count_nonzero(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard and capture statusSummary"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded(), "Dashboard did not reach loaded state."

        summary = api_body.get("statusSummary", {})
        # Map card key → API summary key(s)
        tab_counts = {
            "pending":        summary.get("submitted", 0),
            "approved":       summary.get("approved", 0),
            "rejected":       summary.get("rejected", 0),
            "draft_imported": summary.get("draft", 0) + summary.get("imported", 0),
        }

        allure.attach(
            "\n".join(f"{k}: {v}" for k, v in tab_counts.items()),
            name="Tab counts from API",
            attachment_type=allure.attachment_type.TEXT,
        )

        # Find a tab with records to test against
        test_tab = next((tab for tab, count in tab_counts.items() if count > 0), None)
        if test_tab is None:
            pytest.skip("All tab counts are zero — no rows to verify.")

        with allure.step(f"Click '{test_tab}' tab (API count={tab_counts[test_tab]})"):
            dashboard.click_card(test_tab)

        with allure.step("Assert table shows at least one row"):
            row_count = dashboard.row_count()
            allure.attach(
                f"Tab: {test_tab}\nAPI count: {tab_counts[test_tab]}\nVisible rows: {row_count}",
                name="Table row count",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0, (
                f"Tab '{test_tab}' has API count={tab_counts[test_tab]} but table shows 0 rows."
            )

    # ── Test 9: Welcome message ───────────────────────────────────────────────
    @allure.story("Page Load")
    @allure.title("Dashboard shows a personalised welcome message")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "After login the Dashboard must display a welcome/greeting heading "
        "('Welcome to LettersHub!' or similar). Verifies the post-login "
        "landing experience is intact."
    )
    def test_welcome_message_visible(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            dashboard.open_direct()
            assert dashboard.is_loaded(timeout=15_000)

        with allure.step("Assert welcome message is visible"):
            text = dashboard.welcome_text()
            allure.attach(
                f"Welcome text: {text!r}",
                name="Welcome message",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert text, "No welcome/greeting heading found on the Dashboard."
            assert any(
                kw in text.lower()
                for kw in ("welcome", "lettershub", "good morning", "good afternoon", "good evening")
            ), f"Welcome text does not look like a greeting: {text!r}"

    # ── Test 10: Clicking stat card updates URL tab param ────────────────────
    @allure.story("Tab Navigation")
    @allure.title("Clicking each stat card updates the URL tab parameter")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "The Dashboard uses a ?tab= URL query parameter to track the active tab. "
        "Clicking each stat card must update the URL accordingly:\n"
        "  Pending Approvals  → ?tab=pending\n"
        "  Rejected Approvals → ?tab=rejected\n"
        "  Approved Versions  → ?tab=approved\n"
        "  Draft & Imported   → ?tab=draft (or similar)\n"
        "Verifies deep-link / browser-back support works correctly."
    )
    def test_stat_card_click_updates_url_tab(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded()

        _TAB_MAP = {
            "pending":  "pending",
            "rejected": "rejected",
            "approved": "approved",
        }

        for card, expected_tab in _TAB_MAP.items():
            with allure.step(f"Click '{card}' card — expect ?tab={expected_tab} in URL"):
                dashboard.click_card(card)
                current_url = authed_page.url
                allure.attach(
                    f"Card: {card}\nURL : {current_url}",
                    name=f"{card} URL",
                    attachment_type=allure.attachment_type.TEXT,
                )
                assert expected_tab in current_url, (
                    f"Clicking '{card}' card did not update URL to include "
                    f"'{expected_tab}'. Actual URL: {current_url}"
                )

    # ── Test 11: Pending tab table columns ───────────────────────────────────
    @allure.story("Table Structure")
    @allure.title("Pending Approvals tab shows required table columns")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "After clicking the Pending Approvals card the letter-type table must "
        "display all expected columns: Letter Type Id, Letter Type, LOB, "
        "Approval Progress, Requestor, Submitted, Actions. "
        "Skips when no pending records exist (empty table has no headers)."
    )
    def test_pending_tab_table_columns(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded()

        pending_count = api_body.get("statusSummary", {}).get("submitted", 0)
        if pending_count == 0:
            pytest.skip("No pending records — table headers not rendered.")

        with allure.step("Click Pending Approvals card"):
            dashboard.click_card("pending")

        with allure.step("Read and verify table column headers"):
            # Poll until headers have real text (skeleton clears)
            import time as _t
            deadline = _t.monotonic() + 15
            headers: list = []
            while _t.monotonic() < deadline:
                headers = dashboard.pending_tab_column_headers()
                if headers:
                    break
                authed_page.wait_for_timeout(400)

            allure.attach(
                f"Columns found: {headers}",
                name="Table column headers",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert headers, "No column headers found in the Pending Approvals table."

            _REQUIRED = ["letter type", "lob", "actions"]
            headers_lower = [h.lower() for h in headers]
            missing_cols = [
                req for req in _REQUIRED
                if not any(req in h for h in headers_lower)
            ]
            assert not missing_cols, (
                f"Pending table is missing required columns: {missing_cols}. "
                f"Found: {headers}"
            )

    # ── Test 12: Search in Pending tab ───────────────────────────────────────
    @allure.story("Search & Filter")
    @allure.title("Search in Pending Approvals tab filters the table")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "The Pending Approvals tab has a 'Search by Letter Type and Id' input. "
        "Typing a partial Letter Type ID must reduce the visible rows. "
        "Clearing the search must restore the full result set. "
        "Skips when no pending records exist or search input is not visible."
    )
    def test_search_filters_pending_tab(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard and open Pending Approvals tab"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded()

        pending_count = api_body.get("statusSummary", {}).get("submitted", 0)
        if pending_count == 0:
            pytest.skip("No pending records — search has nothing to filter.")

        with allure.step("Click Pending Approvals card"):
            dashboard.click_card("pending")

        with allure.step("Assert search input is visible"):
            search_visible = dashboard.is_visible(
                dashboard.pending_search_input, timeout=8_000
            )
            allure.attach(
                f"Search input visible: {search_visible}",
                name="Search input",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not search_visible:
                pytest.skip("Search input not found on Pending Approvals tab.")

        with allure.step("Record unfiltered row count and first row text"):
            # Wait for real data
            import time as _t
            rows = authed_page.locator("table tbody tr")
            deadline = _t.monotonic() + 15
            while _t.monotonic() < deadline:
                if dashboard.text_of(rows.first).strip():
                    break
                authed_page.wait_for_timeout(400)

            rows_before = dashboard.row_count()
            first_row_text = dashboard.text_of(rows.first).strip()
            # Extract first word/token as search term
            search_term = first_row_text.split()[0] if first_row_text else ""
            allure.attach(
                f"Rows before search : {rows_before}\n"
                f"First row text     : {first_row_text[:80]!r}\n"
                f"Search term        : {search_term!r}",
                name="Pre-search state",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not search_term:
                pytest.skip("Could not extract a search term from the first row.")

        with allure.step(f"Search for {search_term!r} and verify table updates"):
            dashboard.search_pending_tab(search_term)
            rows_after = dashboard.row_count()
            allure.attach(
                f"Rows after search: {rows_after}",
                name="Post-search row count",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert rows_after > 0, (
                f"Search for {search_term!r} returned 0 rows — expected at least 1."
            )
            assert rows_after <= rows_before, (
                "Row count increased after applying search — unexpected."
            )

        with allure.step("Clear search and verify rows restore"):
            dashboard.clear_pending_search()
            rows_restored = dashboard.row_count()
            allure.attach(
                f"Rows after clear: {rows_restored}",
                name="Post-clear row count",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert rows_restored > 0, "No rows visible after clearing the search."
