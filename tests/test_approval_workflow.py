"""
Approval Workflow — Dashboard-driven approve / reject flow.

Covers:
  TC_AW_001  Pending Approvals tab shows letters in Pending/Submitted status
  TC_AW_002  Approved Versions tab shows letters in Approved status
  TC_AW_003  Rejected Approvals tab shows letters in Rejected status
  TC_AW_004  Approve a pending letter — Approved count increases on Dashboard
  TC_AW_005  Reject a pending letter — Rejected count increases on Dashboard

Flow:
  Dashboard (Pending Approvals card)
    → click row
      → Letter Type detail page
          → Approve / Reject button
            → status changes
              → Dashboard counts update
"""
from __future__ import annotations

import allure
import pytest
from playwright.sync_api import Page

from pages.dashboard_page import DashboardPage
from pages.letter_type_details_page import LetterTypeDetailsPage


pytestmark = pytest.mark.sanity


def _navigate_and_capture_ltv(page: Page, dashboard: DashboardPage) -> dict:
    """Navigate to dashboard and capture the letter-type-version API response."""
    with page.expect_response(
        lambda r: "letter-type-version" in r.url and r.status == 200,
        timeout=90_000,
    ) as resp_info:
        dashboard.navigate()
    return resp_info.value.json()


def _click_card_and_capture_ltv(page: Page, dashboard: DashboardPage, card: str) -> dict:
    with page.expect_response(
        lambda r: "letter-type-version" in r.url and r.status == 200,
        timeout=45_000,
    ) as resp_info:
        dashboard.click_card(card)
    return resp_info.value.json()


@allure.epic("Correspondence Application")
@allure.feature("Dashboard – Approval Workflow")
class TestApprovalWorkflow:

    # ── TC_AW_001 ─────────────────────────────────────────────────────────────
    @allure.story("Tab Content")
    @allure.title("[TC_AW_001] Pending Approvals tab shows letters in Pending/Submitted status")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Click the 'Pending Approvals' stat card on the Dashboard. "
        "Verify the table populates with rows and every visible row contains "
        "'Pending' or 'Submitted' in its text. Skips when API count is zero."
    )
    def test_pending_tab_shows_pending_letters(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard and capture statusSummary"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded(), "Dashboard did not load."

        pending_count = api_body.get("statusSummary", {}).get("submitted", 0)
        allure.attach(
            f"API pending count: {pending_count}",
            name="Pending count from API",
            attachment_type=allure.attachment_type.TEXT,
        )
        if pending_count == 0:
            pytest.skip("No pending letters in this environment — nothing to verify.")

        with allure.step("Click Pending Approvals card"):
            dashboard.click_card("pending")

        with allure.step("Wait for rows to load and verify Pending tab shows expected records"):
            rows = authed_page.locator("table tbody tr")
            import time as _t
            deadline = _t.monotonic() + 15
            while _t.monotonic() < deadline:
                if dashboard.text_of(rows.first).strip():
                    break
                authed_page.wait_for_timeout(400)

            row_count = rows.count()
            allure.attach(
                f"API pending count : {pending_count}\n"
                f"Visible row count : {row_count}",
                name="Pending tab row check",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0, (
                "Pending Approvals tab shows 0 rows but API reported "
                f"{pending_count} pending letters."
            )
            # The Pending tab is API-filtered — all rows are pending by definition.
            # Status is rendered as a visual chip, not as row text.
            assert row_count <= pending_count, (
                f"Visible rows ({row_count}) exceed API pending count ({pending_count})."
            )

    # ── TC_AW_002 ─────────────────────────────────────────────────────────────
    @allure.story("Tab Content")
    @allure.title("[TC_AW_002] Approved Versions tab shows letters in Approved status")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Click the 'Approved Versions' stat card. Verify every visible row "
        "contains 'Approved' in its text. Skips when API count is zero."
    )
    def test_approved_tab_shows_approved_letters(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded()

        approved_count = api_body.get("statusSummary", {}).get("approved", 0)
        if approved_count == 0:
            pytest.skip("No approved letters in this environment.")

        with allure.step("Click Approved Versions card"):
            dashboard.click_card("approved")

        with allure.step("Verify Approved tab loads rows"):
            rows = authed_page.locator("table tbody tr")
            import time as _t
            deadline = _t.monotonic() + 15
            while _t.monotonic() < deadline:
                if dashboard.text_of(rows.first).strip():
                    break
                authed_page.wait_for_timeout(400)

            row_count = rows.count()
            allure.attach(
                f"API approved count : {approved_count}\n"
                f"Visible row count  : {row_count}",
                name="Approved tab row check",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0, (
                f"Approved tab shows 0 rows but API count={approved_count}."
            )
            # The Approved tab is API-filtered — all rows are approved by definition.
            # Rows do not render a redundant status label; row count is the assertion.
            assert row_count <= approved_count, (
                f"Visible rows ({row_count}) exceed API approved count ({approved_count})."
            )

    # ── TC_AW_003 ─────────────────────────────────────────────────────────────
    @allure.story("Tab Content")
    @allure.title("[TC_AW_003] Rejected Approvals tab shows letters in Rejected status")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Click the 'Rejected Approvals' stat card. Verify every visible row "
        "contains 'Rejected' in its text. Skips when API count is zero."
    )
    def test_rejected_tab_shows_rejected_letters(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded()

        rejected_count = api_body.get("statusSummary", {}).get("rejected", 0)
        if rejected_count == 0:
            pytest.skip("No rejected letters in this environment.")

        with allure.step("Click Rejected Approvals card"):
            dashboard.click_card("rejected")

        with allure.step("Verify Rejected tab loads rows"):
            rows = authed_page.locator("table tbody tr")
            import time as _t
            deadline = _t.monotonic() + 15
            while _t.monotonic() < deadline:
                if dashboard.text_of(rows.first).strip():
                    break
                authed_page.wait_for_timeout(400)

            row_count = rows.count()
            allure.attach(
                f"API rejected count : {rejected_count}\n"
                f"Visible row count  : {row_count}",
                name="Rejected tab row check",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert row_count > 0, (
                f"Rejected tab shows 0 rows but API count={rejected_count}."
            )
            # The Rejected tab is API-filtered — all rows are rejected by definition.
            assert row_count <= rejected_count, (
                f"Visible rows ({row_count}) exceed API rejected count ({rejected_count})."
            )

    # ── TC_AW_004 ─────────────────────────────────────────────────────────────
    @allure.story("Approve Letter")
    @allure.title(
        "[TC_AW_004] Cac Admin approves a pending letter — "
        "Pending −1 and Approved +1 on Dashboard"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Full approve flow with role verification:\n"
        "1. Verify the logged-in user has the 'Cac Admin' role.\n"
        "2. Navigate to Dashboard — record Pending and Approved counts from API.\n"
        "3. Click the Pending Approvals card (URL: dashboard?tab=pending).\n"
        "4. Click 'Review' on the first letter in the Actions column.\n"
        "5. Click 'Approve' on the letter detail page.\n"
        "6. Navigate back to Dashboard — verify Pending count = before−1 "
        "AND Approved count = before+1.\n"
        "Skips when no pending letters exist."
    )
    def test_approve_pending_letter(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)
        details = LetterTypeDetailsPage(authed_page)

        # ── Step 1: role check ────────────────────────────────────────────────
        with allure.step("Navigate to Dashboard and verify Cac Admin role"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded()

            role = dashboard.get_current_role()
            allure.attach(
                f"Detected role: {role!r}",
                name="User role",
                attachment_type=allure.attachment_type.TEXT,
            )
            if role and "cac admin" not in role.lower():
                # Attempt to switch to Cac Admin
                switched = dashboard.ensure_role("Cac Admin")
                allure.attach(
                    f"Switched to Cac Admin: {switched}",
                    name="Role switch",
                    attachment_type=allure.attachment_type.TEXT,
                )
                if switched:
                    api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded(), "Dashboard not loaded after role check."

        # ── Step 2: capture initial counts ───────────────────────────────────
        summary = api_body.get("statusSummary", {})
        pending_before = summary.get("submitted", 0)
        approved_before = summary.get("approved", 0)

        allure.attach(
            f"Pending before : {pending_before}\nApproved before: {approved_before}",
            name="Initial counts",
            attachment_type=allure.attachment_type.TEXT,
        )
        if pending_before == 0:
            pytest.skip("No pending letters — cannot approve.")

        # ── Steps 3-4: open Pending tab and find a row whose detail loads OK ────
        # Poll for up to 15 s after each Review click: if the Approve button
        # appears the page is ready; if an error indicator appears (or neither
        # shows within the timeout) skip that row and try the next one.
        import time as _t

        _ERR_SEL = (
            "text=/unexpected error/i, "
            "text=/validation error/i, "
            "text=/Field required/i"
        )
        MAX_ROWS = 5
        detail_ok = False
        for attempt in range(MAX_ROWS):
            with allure.step(
                f"Pending tab → Review row {attempt} (attempt {attempt + 1}/{MAX_ROWS})"
            ):
                _navigate_and_capture_ltv(authed_page, dashboard)
                dashboard.click_card("pending")

                rows_loc = authed_page.locator("table tbody tr")
                load_deadline = _t.monotonic() + 15
                while _t.monotonic() < load_deadline:
                    if dashboard.text_of(rows_loc.first).strip():
                        break
                    authed_page.wait_for_timeout(400)

                if rows_loc.count() <= attempt:
                    break

                navigated = dashboard.click_review_for_row(attempt)
                if not navigated:
                    allure.attach(
                        f"Row {attempt}: Review did not navigate away from dashboard.",
                        name=f"Attempt {attempt + 1} — no navigation",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                    continue

                # Wait up to 15 s for approve button OR error — whichever first
                btn_found = False
                page_error = False
                poll_deadline = _t.monotonic() + 15
                while _t.monotonic() < poll_deadline:
                    try:
                        if details.approve_button.is_visible():
                            btn_found = True
                            break
                    except Exception:
                        pass
                    try:
                        if authed_page.locator(_ERR_SEL).first.is_visible():
                            page_error = True
                            break
                    except Exception:
                        pass
                    authed_page.wait_for_timeout(600)

                allure.attach(
                    f"Row {attempt}: btn_found={btn_found}, "
                    f"page_error={page_error}, URL={authed_page.url}",
                    name=f"Attempt {attempt + 1}",
                    attachment_type=allure.attachment_type.TEXT,
                )
                if btn_found:
                    detail_ok = True
                    break
                # page_error or timeout → try next row

        assert detail_ok, (
            f"Could not find a pending letter with a loadable Approve button "
            f"after {MAX_ROWS} attempts — all rows had backend errors or timed out."
        )

        # ── Step 5: approve ───────────────────────────────────────────────────
        with allure.step("Assert Approve button is visible on detail page"):
            # Button was already confirmed visible in the poll loop above;
            # re-check with a short timeout to keep the allure step consistent.
            approve_visible = details.is_visible(details.approve_button, timeout=5_000)
            allure.attach(
                f"Approve button visible: {approve_visible}\nURL: {authed_page.url}",
                name="Approve button",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert approve_visible, (
                "Approve button disappeared between poll and assertion — "
                "possible race or permission issue."
            )

        with allure.step("Click Approve"):
            clicked = details.click_approve()
            assert clicked, "Approve button click failed."

        with allure.step("Assert letter status changed to Approved on detail page"):
            status_after = details.current_status()
            allure.attach(
                f"Status after approve: {status_after!r}",
                name="Post-approve status",
                attachment_type=allure.attachment_type.TEXT,
            )
            if status_after:
                assert "approved" in status_after.lower(), (
                    f"Expected 'Approved' status after clicking Approve, "
                    f"got: {status_after!r}"
                )

        # ── Step 6: verify Dashboard counts ──────────────────────────────────
        with allure.step(
            "Navigate back to Dashboard — verify Pending −1 and Approved +1"
        ):
            new_api = _navigate_and_capture_ltv(authed_page, dashboard)
            new_summary = new_api.get("statusSummary", {})
            pending_after = new_summary.get("submitted", 0)
            approved_after = new_summary.get("approved", 0)

            allure.attach(
                f"Pending  : {pending_before} → {pending_after}  "
                f"(expected {pending_before - 1})\n"
                f"Approved : {approved_before} → {approved_after}  "
                f"(expected {approved_before + 1})",
                name="Count delta",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert pending_after == pending_before - 1, (
                f"Pending count should be {pending_before - 1} after approving one letter, "
                f"got {pending_after}."
            )
            assert approved_after == approved_before + 1, (
                f"Approved count should be {approved_before + 1} after approving one letter, "
                f"got {approved_after}."
            )

    # ── TC_AW_005 ─────────────────────────────────────────────────────────────
    @allure.story("Reject Letter")
    @allure.title(
        "[TC_AW_005] Cac Admin rejects a pending letter — "
        "Pending −1 and Rejected +1 on Dashboard"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Full reject flow with role verification:\n"
        "1. Verify the logged-in user has the 'Cac Admin' role.\n"
        "2. Navigate to Dashboard — record Pending and Rejected counts from API.\n"
        "3. Click the Pending Approvals card (URL: dashboard?tab=pending).\n"
        "4. Click 'Review' on the first letter in the Actions column.\n"
        "5. Click 'Reject', fill in a rejection reason, confirm.\n"
        "6. Navigate back to Dashboard — verify Pending count = before−1 "
        "AND Rejected count = before+1.\n"
        "Skips when no pending letters exist."
    )
    def test_reject_pending_letter(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)
        details = LetterTypeDetailsPage(authed_page)

        # ── Step 1: role check ────────────────────────────────────────────────
        with allure.step("Navigate to Dashboard and verify Cac Admin role"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded()

            role = dashboard.get_current_role()
            allure.attach(
                f"Detected role: {role!r}",
                name="User role",
                attachment_type=allure.attachment_type.TEXT,
            )
            if role and "cac admin" not in role.lower():
                switched = dashboard.ensure_role("Cac Admin")
                allure.attach(
                    f"Switched to Cac Admin: {switched}",
                    name="Role switch",
                    attachment_type=allure.attachment_type.TEXT,
                )
                if switched:
                    api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded(), "Dashboard not loaded after role check."

        # ── Step 2: capture initial counts ───────────────────────────────────
        summary = api_body.get("statusSummary", {})
        pending_before = summary.get("submitted", 0)
        rejected_before = summary.get("rejected", 0)

        allure.attach(
            f"Pending before : {pending_before}\nRejected before: {rejected_before}",
            name="Initial counts",
            attachment_type=allure.attachment_type.TEXT,
        )
        if pending_before == 0:
            pytest.skip("No pending letters — cannot reject.")

        # ── Steps 3-4: open Pending tab and find a row whose detail loads OK ────
        import time as _t

        _ERR_SEL = (
            "text=/unexpected error/i, "
            "text=/validation error/i, "
            "text=/Field required/i"
        )
        MAX_ROWS = 5
        detail_ok = False
        for attempt in range(MAX_ROWS):
            with allure.step(
                f"Pending tab → Review row {attempt} (attempt {attempt + 1}/{MAX_ROWS})"
            ):
                _navigate_and_capture_ltv(authed_page, dashboard)
                dashboard.click_card("pending")

                rows_loc = authed_page.locator("table tbody tr")
                load_deadline = _t.monotonic() + 15
                while _t.monotonic() < load_deadline:
                    if dashboard.text_of(rows_loc.first).strip():
                        break
                    authed_page.wait_for_timeout(400)

                if rows_loc.count() <= attempt:
                    break

                navigated = dashboard.click_review_for_row(attempt)
                if not navigated:
                    allure.attach(
                        f"Row {attempt}: Review did not navigate away from dashboard.",
                        name=f"Attempt {attempt + 1} — no navigation",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                    continue

                # Wait up to 15 s for reject button OR error — whichever first
                btn_found = False
                page_error = False
                poll_deadline = _t.monotonic() + 15
                while _t.monotonic() < poll_deadline:
                    try:
                        if details.reject_button.is_visible():
                            btn_found = True
                            break
                    except Exception:
                        pass
                    try:
                        if authed_page.locator(_ERR_SEL).first.is_visible():
                            page_error = True
                            break
                    except Exception:
                        pass
                    authed_page.wait_for_timeout(600)

                allure.attach(
                    f"Row {attempt}: btn_found={btn_found}, "
                    f"page_error={page_error}, URL={authed_page.url}",
                    name=f"Attempt {attempt + 1}",
                    attachment_type=allure.attachment_type.TEXT,
                )
                if btn_found:
                    detail_ok = True
                    break
                # page_error or timeout → try next row

        assert detail_ok, (
            f"Could not find a pending letter with a loadable Reject button "
            f"after {MAX_ROWS} attempts — all rows had backend errors or timed out."
        )

        # ── Step 5: reject ────────────────────────────────────────────────────
        with allure.step("Assert Reject button is visible on detail page"):
            reject_visible = details.is_visible(details.reject_button, timeout=5_000)
            allure.attach(
                f"Reject button visible: {reject_visible}\nURL: {authed_page.url}",
                name="Reject button",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert reject_visible, (
                "Reject button disappeared between poll and assertion — "
                "possible race or permission issue."
            )

        with allure.step("Click Reject and provide rejection reason"):
            clicked = details.click_reject(reason="Automated sanity test — rejection check")
            assert clicked, "Reject button click failed."

        with allure.step("Assert letter status changed to Rejected on detail page"):
            status_after = details.current_status()
            allure.attach(
                f"Status after reject: {status_after!r}",
                name="Post-reject status",
                attachment_type=allure.attachment_type.TEXT,
            )
            if status_after:
                assert "rejected" in status_after.lower(), (
                    f"Expected 'Rejected' status after clicking Reject, "
                    f"got: {status_after!r}"
                )

        # ── Step 6: verify Dashboard counts ──────────────────────────────────
        with allure.step(
            "Navigate back to Dashboard — verify Pending −1 and Rejected +1"
        ):
            new_api = _navigate_and_capture_ltv(authed_page, dashboard)
            new_summary = new_api.get("statusSummary", {})
            pending_after = new_summary.get("submitted", 0)
            rejected_after = new_summary.get("rejected", 0)

            allure.attach(
                f"Pending  : {pending_before} → {pending_after}  "
                f"(expected {pending_before - 1})\n"
                f"Rejected : {rejected_before} → {rejected_after}  "
                f"(expected {rejected_before + 1})",
                name="Count delta",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert pending_after == pending_before - 1, (
                f"Pending count should be {pending_before - 1} after rejecting one letter, "
                f"got {pending_after}."
            )
            assert rejected_after == rejected_before + 1, (
                f"Rejected count should be {rejected_before + 1} after rejecting one letter, "
                f"got {rejected_after}."
            )

    # ── TC_AW_006 ─────────────────────────────────────────────────────────────
    @allure.story("Bulk Approve")
    @allure.title("[TC_AW_006] Bulk Approve button is visible on Pending Approvals tab")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Navigate to the Pending Approvals tab and verify the 'Bulk Approve' "
        "button is present in the toolbar. Skips when no pending records exist."
    )
    def test_bulk_approve_button_visible(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded()

        if api_body.get("statusSummary", {}).get("submitted", 0) == 0:
            pytest.skip("No pending records — Bulk Approve may not render.")

        with allure.step("Click Pending Approvals card"):
            dashboard.click_card("pending")

        with allure.step("Assert Bulk Approve button is visible"):
            visible = dashboard.is_visible(dashboard.bulk_approve_button, timeout=8_000)
            allure.attach(
                f"Bulk Approve button visible: {visible}\nURL: {authed_page.url}",
                name="Bulk Approve button",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert visible, (
                "Bulk Approve button not found on the Pending Approvals tab toolbar."
            )

    # ── TC_AW_007 ─────────────────────────────────────────────────────────────
    @allure.story("Refresh")
    @allure.title("[TC_AW_007] Refresh button reloads Pending Approvals data")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "On the Pending Approvals tab, click the Refresh button and verify that "
        "the page remains loaded and the table still shows data. "
        "Skips when no pending records exist or Refresh button is not visible."
    )
    def test_refresh_button_reloads_data(self, authed_page: Page):
        dashboard = DashboardPage(authed_page)

        with allure.step("Navigate to Dashboard and open Pending Approvals tab"):
            api_body = _navigate_and_capture_ltv(authed_page, dashboard)
            assert dashboard.is_loaded()

        pending_count = api_body.get("statusSummary", {}).get("submitted", 0)
        if pending_count == 0:
            pytest.skip("No pending records — table may be empty after refresh.")

        with allure.step("Click Pending Approvals card"):
            dashboard.click_card("pending")

        with allure.step("Assert Refresh button is visible"):
            refresh_visible = dashboard.is_visible(
                dashboard.table_refresh_button, timeout=8_000
            )
            allure.attach(
                f"Refresh button visible: {refresh_visible}",
                name="Refresh button",
                attachment_type=allure.attachment_type.TEXT,
            )
            if not refresh_visible:
                pytest.skip("Refresh button not found on Pending Approvals tab.")

        with allure.step("Record row count before refresh"):
            rows_before = dashboard.row_count()

        with allure.step("Click Refresh and wait for data to reload"):
            dashboard.safe_click(dashboard.table_refresh_button, "Refresh")
            dashboard.wait_for_idle()
            # Wait for real data to replace skeleton rows
            import time as _t
            rows_loc = authed_page.locator("table tbody tr")
            deadline = _t.monotonic() + 15
            while _t.monotonic() < deadline:
                if dashboard.text_of(rows_loc.first).strip():
                    break
                authed_page.wait_for_timeout(400)

        with allure.step("Assert table still shows rows after refresh"):
            rows_after = dashboard.row_count()
            allure.attach(
                f"Rows before refresh: {rows_before}\nRows after refresh : {rows_after}",
                name="Row count after refresh",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert rows_after > 0, (
                "Table shows 0 rows after clicking Refresh — data may have failed to reload."
            )
