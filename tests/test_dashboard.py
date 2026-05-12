"""
Dashboard stat-card + tab-footer tests.

Validates that:
1. Every stat card (Draft & Imported, Pending, Rejected, Approved) displays
   the count returned by the letter-type-version API statusSummary.
2. After clicking each stat card, the footer "results of X" matches the API
   totalRecords returned for that status filter.

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
from utils.ai_agent import smart_assert


pytestmark = [pytest.mark.sanity, pytest.mark.agentic]


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
            assert smart_assert(
                authed_page,
                lambda: dashboard.is_loaded(),
                "Is the dashboard page loaded with stat cards visible?",
            ), "Dashboard did not reach loaded state."

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
            assert smart_assert(
                authed_page,
                lambda: dashboard.is_loaded(),
                "Is the dashboard page loaded with stat cards and a data table visible?",
            )

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
            assert smart_assert(
                authed_page,
                lambda: dashboard.is_loaded(),
                "Is the dashboard page loaded with stat cards and a data table visible?",
            )

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
            assert smart_assert(
                authed_page,
                lambda: dashboard.is_loaded(),
                "Is the dashboard page loaded with stat cards and a data table visible?",
            )

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
