"""
Navigation smoke test — validates every sidebar page in a single test run.

Covers:
  - My Dashboard
  - Ask Auto
  - Letter Configuration group: Letter Type, Component Library, Letter Consolidation
  - Letter Control Center
  - Settings
  - Reports group: Audit Logger, Recon Report

Each nav item is reached by clicking through the sidebar (POM-driven), not by
pasting URLs directly, so the test also validates that every link in the
sidebar is wired up and resolves to the correct page.
"""
from __future__ import annotations

import allure
import pytest

from pages.ask_auto_page import AskAutoPage
from pages.audit_logger_page import AuditLoggerPage
from pages.component_library_page import ComponentLibraryPage
from pages.dashboard_page import DashboardPage
from pages.letter_consolidation_page import LetterConsolidationPage
from pages.letter_control_center_page import LetterControlCenterPage
from pages.letter_type_page import LetterTypePage
from pages.nav_page import NavigationPage
from pages.recon_report_page import ReconReportPage
from pages.settings_page import SettingsPage
from utils.ai_agent import smart_assert


pytestmark = [pytest.mark.sanity, pytest.mark.agentic]

# Timeout passed to every is_loaded() call.  Pages load data via async API
# calls after the browser "load" event fires — 20 s gives enough headroom
# for slow sprint environments without making the test feel stuck.
_PAGE_LOAD_TIMEOUT = 10_000


@allure.epic("Correspondence Application")
@allure.feature("Sidebar Navigation")
class TestNavigation:
    """End-to-end navigation walk-through using the sidebar POM."""

    @allure.story("Full Navigation Walk-through")
    @allure.title("All sidebar navigation pages load correctly")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Clicks every item in the left sidebar (expanding the 'Letter Configuration' "
        "and 'Reports' groups as needed) and asserts that the correct page loads "
        "for each entry.  A failure pinpoints exactly which nav link is broken.\n\n"
        "Pages validated:\n"
        "  1. My Dashboard\n"
        "  2. Ask Auto\n"
        "  3. Letter Configuration › Letter Type\n"
        "  4. Letter Configuration › Component Library\n"
        "  5. Letter Configuration › Letter Consolidation\n"
        "  6. Letter Control Center\n"
        "  7. Settings\n"
        "  8. Reports › Audit Logger\n"
        "  9. Reports › Recon Report"
    )
    def test_all_nav_pages_load(self, authed_page):
        """Click through every sidebar link and assert each page renders."""
        nav = NavigationPage(authed_page)

        # ── Start on Dashboard so the sidebar is visible ─────────────────
        with allure.step("Open application — land on Dashboard"):
            nav.navigate()
            dashboard = DashboardPage(authed_page)
            loaded = smart_assert(
                authed_page,
                lambda: dashboard.is_loaded(timeout=30_000),
                "Is the dashboard page loaded with stat cards visible?",
            )
            allure.attach(
                f"Dashboard loaded: {loaded}  URL: {authed_page.url}",
                name="Dashboard initial load",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert loaded, "Dashboard did not load after initial navigation."

        # ── 1. My Dashboard ───────────────────────────────────────────────
        with allure.step("Navigate to: My Dashboard"):
            nav.go_to_dashboard()
            assert smart_assert(
                authed_page,
                lambda: DashboardPage(authed_page).is_loaded(timeout=_PAGE_LOAD_TIMEOUT),
                "Is the dashboard page loaded with stat cards visible?",
            ), f"My Dashboard did not load. URL: {authed_page.url}"

        # ── 2. Ask Auto ───────────────────────────────────────────────────
        with allure.step("Navigate to: Ask Auto"):
            nav.go_to_ask_auto()
            assert smart_assert(
                authed_page,
                lambda: AskAutoPage(authed_page).is_loaded(timeout=_PAGE_LOAD_TIMEOUT),
                "Is the Ask Auto AI assistant page loaded with a chat or query interface visible?",
            ), f"Ask Auto page did not load. URL: {authed_page.url}"

        # ── 3. Letter Configuration › Letter Type ─────────────────────────
        with allure.step("Expand 'Letter Configuration' and navigate to: Letter Type"):
            nav.go_to_letter_type()
            assert smart_assert(
                authed_page,
                lambda: LetterTypePage(authed_page).is_loaded(timeout=_PAGE_LOAD_TIMEOUT),
                "Is the Letter Type listing page loaded with a search box and data table visible?",
            ), f"Letter Type page did not load. URL: {authed_page.url}"

        # ── 4. Letter Configuration › Component Library ───────────────────
        with allure.step("Navigate to: Component Library"):
            nav.go_to_component_library()
            assert smart_assert(
                authed_page,
                lambda: ComponentLibraryPage(authed_page).is_loaded(timeout=_PAGE_LOAD_TIMEOUT),
                "Is the Component Library page loaded with tabs and a list of components visible?",
            ), f"Component Library page did not load. URL: {authed_page.url}"

        # ── 5. Letter Configuration › Letter Consolidation ────────────────
        with allure.step("Navigate to: Letter Consolidation"):
            nav.go_to_letter_consolidation()
            assert smart_assert(
                authed_page,
                lambda: LetterConsolidationPage(authed_page).is_loaded(timeout=_PAGE_LOAD_TIMEOUT),
                "Is the Letter Consolidation page loaded with groups or a list of letters visible?",
            ), f"Letter Consolidation page did not load. URL: {authed_page.url}"

        # ── 6. Letter Control Center ──────────────────────────────────────
        with allure.step("Navigate to: Letter Control Center"):
            nav.go_to_letter_control_center()
            assert smart_assert(
                authed_page,
                lambda: LetterControlCenterPage(authed_page).is_loaded(timeout=_PAGE_LOAD_TIMEOUT),
                "Is the Letter Control Center page loaded with a list of generated letters visible?",
            ), f"Letter Control Center page did not load. URL: {authed_page.url}"

        # ── 7. Settings ───────────────────────────────────────────────────
        with allure.step("Navigate to: Settings"):
            nav.go_to_settings()
            assert smart_assert(
                authed_page,
                lambda: SettingsPage(authed_page).is_loaded(timeout=_PAGE_LOAD_TIMEOUT),
                "Is the Settings page loaded with configuration tabs visible?",
            ), f"Settings page did not load. URL: {authed_page.url}"

        # ── 8. Reports › Audit Logger ─────────────────────────────────────
        with allure.step("Expand 'Reports' and navigate to: Audit Logger"):
            nav.go_to_audit_logger()
            assert smart_assert(
                authed_page,
                lambda: AuditLoggerPage(authed_page).is_loaded(timeout=_PAGE_LOAD_TIMEOUT),
                "Is the Audit Logger page loaded with a table of audit entries visible?",
            ), f"Audit Logger page did not load. URL: {authed_page.url}"

        # ── 9. Reports › Recon Report ─────────────────────────────────────
        with allure.step("Navigate to: Recon Report"):
            nav.go_to_recon_report()
            assert smart_assert(
                authed_page,
                lambda: ReconReportPage(authed_page).is_loaded(timeout=_PAGE_LOAD_TIMEOUT),
                "Is the Recon Report page loaded with a list or table of reports visible?",
            ), f"Recon Report page did not load. URL: {authed_page.url}"
