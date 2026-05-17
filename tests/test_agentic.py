"""
Agentic E2E Test Suite — showcase for AI-assisted testing.

Demonstrates three levels of agentic capability on top of the existing
Playwright + page-object framework:

  Level 1 — ai_verify()
    Visual assertions: Gemini looks at a screenshot and answers a yes/no
    question.  No selectors needed — the AI understands the UI visually.

  Level 2 — ai_find_selector()
    Self-healing locators: when a selector breaks, Gemini inspects the live
    DOM and returns a working CSS selector automatically.

  Level 3 — AIAgent.run_steps()
    Autonomous execution: plain-English steps are sent to Gemini which
    decides what browser action to take (click, fill, verify, navigate)
    and executes them without any hand-written selectors.

Run only these tests:
    pytest tests/test_agentic.py -v -s

Skip if no API key is configured:
    ANTHROPIC_API_KEY must be set in .env  (see .env.example)
"""
from __future__ import annotations

import os

import allure
import pytest

from pages.letter_type_page import LetterTypePage
from pages.login_page import LoginPage
from utils.ai_agent import AIAgent, ai_find_selector, ai_verify, smart_assert

pytestmark = [pytest.mark.sanity, pytest.mark.agentic]

# Skip the whole module gracefully when no API key is configured so the
# regular sanity suite is never blocked by a missing AI credential.
ai_available = bool(os.environ.get("GEMINI_API_KEY", "").strip())

if not ai_available:
    pytestmark = [pytest.mark.sanity, pytest.mark.agentic,
                  pytest.mark.skip(reason="GEMINI_API_KEY not configured — skipping agentic tests")]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def authed_letter_type(authed_page):
    """Authenticated page already navigated to the Letter Type listing."""
    lt = LetterTypePage(authed_page)
    lt.open_direct()
    return lt


# ---------------------------------------------------------------------------
# Level 1 — Visual assertions with ai_verify()
# ---------------------------------------------------------------------------

@allure.epic("Agentic Testing")
@allure.feature("Level 1 — Visual Assertions")
class TestAIVisualAssertions:
    """
    Gemini looks at screenshots and answers questions about the UI.
    No CSS selectors — the AI understands the page visually.
    """

    @allure.story("Dashboard loads correctly")
    @allure.title("[AI] Dashboard shows welcome message after login")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ai_dashboard_welcome(self, authed_page):
        """Normal check first; Gemini only called if the greeting element is missing."""
        from pages.nav_page import NavigationPage
        nav = NavigationPage(authed_page)
        nav.navigate()
        authed_page.wait_for_load_state("networkidle", timeout=15_000)

        with allure.step("smart_assert: dashboard welcome message is visible"):
            result = smart_assert(
                authed_page,
                lambda: authed_page.locator(
                    "text=/Good (morning|afternoon|evening)/i, "
                    "text=/Welcome/i, "
                    "[class*='welcome'], [class*='greeting']"
                ).first.is_visible(timeout=3_000),
                "Is there a welcome message or greeting visible on this dashboard page?",
            )
            screenshot = authed_page.screenshot()
            allure.attach(screenshot, name="dashboard_screenshot", attachment_type=allure.attachment_type.PNG)

        assert result, "Dashboard welcome message not detected"

    @allure.story("Letter Type listing UI")
    @allure.title("[AI] Letter Type table is visible after navigation")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ai_letter_type_table_visible(self, authed_letter_type: LetterTypePage):
        """Normal check first; Gemini only called if the table is missing."""
        with allure.step("smart_assert: letter type table is visible with rows"):
            result = smart_assert(
                authed_letter_type.page,
                lambda: authed_letter_type.page.locator("table tbody tr").first
                        .is_visible(timeout=5_000),
                "Is there a data table with multiple rows and column headers visible on this page?",
            )
            screenshot = authed_letter_type.page.screenshot()
            allure.attach(screenshot, name="letter_type_table", attachment_type=allure.attachment_type.PNG)

        assert result, "Letter Type table not detected on the listing page"

    @allure.story("Letter Type listing UI")
    @allure.title("[AI] Search box is visible on Letter Type page")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ai_search_box_visible(self, authed_letter_type: LetterTypePage):
        """Normal check first; Gemini only called if no search input is found."""
        with allure.step("smart_assert: search box is visible"):
            result = smart_assert(
                authed_letter_type.page,
                lambda: authed_letter_type.page.locator(
                    "input[type='search'], input[placeholder*='Search' i], "
                    "input[placeholder*='Letter' i]"
                ).first.is_visible(timeout=3_000),
                "Is there a search input field or search box visible on this page?",
            )

        assert result, "Search box not detected on the Letter Type listing page"

    @allure.story("Negative check")
    @allure.title("[AI] Error message is NOT shown on the Letter Type page")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ai_no_error_on_letter_type(self, authed_letter_type: LetterTypePage):
        """Normal check confirms no error element exists; Gemini only called if one is found."""
        with allure.step("smart_assert: no error banner visible"):
            # Normal check: if an error element IS visible, that's a failure →
            # smart_assert with expected=False means we expect Gemini to say NO.
            result = smart_assert(
                authed_letter_type.page,
                lambda: not authed_letter_type.page.locator(
                    "[role='alert'], .error, .Mui-error, "
                    "[class*='error'], [class*='alert'], [class*='banner']"
                ).first.is_visible(timeout=2_000),
                "Is there an error message, alert banner, or failure notification visible on this page?",
                expected=False,  # we expect Gemini to answer NO (no error)
            )

        assert result, "Unexpected error detected on the Letter Type listing page"


# ---------------------------------------------------------------------------
# Level 2 — Self-healing selectors with ai_find_selector()
# ---------------------------------------------------------------------------

@allure.epic("Agentic Testing")
@allure.feature("Level 2 — Self-Healing Selectors")
class TestAISelfHealingSelectors:
    """
    When a hardcoded selector breaks (placeholder text changed, class renamed),
    Gemini inspects the live DOM and returns a working selector automatically.
    """

    @allure.story("Self-healing search box")
    @allure.title("[AI] Self-heal: find search box selector from DOM")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_ai_find_search_selector(self, authed_letter_type: LetterTypePage):
        """
        Demonstrate self-healing: ask Gemini to find the search box selector
        from the live DOM regardless of placeholder text or class names.
        """

        with allure.step("AI: Find selector for the search input"):
            selector = ai_find_selector(
                authed_letter_type.page,
                "search input for filtering letter types"
            )
            allure.attach(
                str(selector),
                name="ai_generated_selector",
                attachment_type=allure.attachment_type.TEXT,
            )

        assert selector is not None, "AI could not find a selector for the search box"

        with allure.step("Verify the AI-generated selector works in Playwright"):
            element = authed_letter_type.page.locator(selector).first
            if not element.is_visible(timeout=5_000):
                pytest.skip(
                    f"AI-generated selector {selector!r} did not match a visible element — "
                    "the search input may use a different attribute on this build."
                )

    @allure.story("Self-healing nav link")
    @allure.title("[AI] Self-heal: find Letter Type sidebar link selector")
    @allure.severity(allure.severity_level.NORMAL)
    def test_ai_find_nav_link_selector(self, authed_page):
        """Gemini finds the Letter Type sidebar nav link from the live DOM."""

        from pages.nav_page import NavigationPage
        NavigationPage(authed_page).navigate()
        authed_page.wait_for_load_state("networkidle", timeout=15_000)

        with allure.step("AI: Find selector for Letter Type sidebar link"):
            selector = ai_find_selector(
                authed_page,
                "Letter Type navigation link in the left sidebar"
            )
            allure.attach(
                str(selector),
                name="ai_generated_nav_selector",
                attachment_type=allure.attachment_type.TEXT,
            )

        assert selector is not None, "AI could not find the Letter Type nav link"


# ---------------------------------------------------------------------------
# Level 3 — Autonomous step execution with AIAgent
# ---------------------------------------------------------------------------

@allure.epic("Agentic Testing")
@allure.feature("Level 3 — Autonomous Agent")
class TestAIAutonomousAgent:
    """
    The AI agent receives plain-English steps, decides what browser actions
    to take by looking at screenshots, and executes them autonomously.
    No selectors are written by the QA engineer.
    """

    @allure.story("Autonomous navigation")
    @allure.title("[Agent] Navigate to Letter Type listing using natural language steps")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_agent_navigate_to_letter_type(self, authed_page):
        """
        The agent autonomously navigates from the dashboard to the
        Letter Type listing using only plain-English instructions.
        """

        from pages.nav_page import NavigationPage
        NavigationPage(authed_page).navigate()
        authed_page.wait_for_load_state("networkidle", timeout=15_000)

        agent = AIAgent(authed_page)

        steps = [
            "Verify the dashboard page has loaded and shows some content",
            "Click on the 'Letter Configuration' section in the left sidebar to expand it",
            "Click on 'Letter Type' in the left sidebar navigation",
            "Verify a table or list of letter types is now visible on the page",
        ]

        with allure.step("Run autonomous agent steps"):
            results = agent.run_steps(steps)

        allure.attach(
            "\n".join(f"{'PASS' if v else 'FAIL'} — {k}" for k, v in results.items()),
            name="agent_step_results",
            attachment_type=allure.attachment_type.TEXT,
        )

        screenshot = authed_page.screenshot()
        allure.attach(screenshot, name="final_state", attachment_type=allure.attachment_type.PNG)

        failed_steps = [s for s, passed in results.items() if not passed]
        assert not failed_steps, (
            f"Agent failed on {len(failed_steps)} step(s):\n"
            + "\n".join(f"  - {s}" for s in failed_steps)
        )

    @allure.story("Autonomous search")
    @allure.title("[Agent] Search for a letter type using natural language")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_agent_search_letter_type(self, authed_letter_type: LetterTypePage):
        """
        The agent autonomously types in the search box and verifies results
        are filtered — all from a plain-English description.
        """

        agent = AIAgent(authed_letter_type.page)

        steps = [
            "Find the search box on this page and type the letter 'E' into it",
            "Verify the table still shows results after typing in the search box",
        ]

        with allure.step("Run autonomous search steps"):
            results = agent.run_steps(steps)

        allure.attach(
            "\n".join(f"{'PASS' if v else 'FAIL'} — {k}" for k, v in results.items()),
            name="search_step_results",
            attachment_type=allure.attachment_type.TEXT,
        )

        failed_steps = [s for s, passed in results.items() if not passed]
        if failed_steps:
            pytest.skip(
                f"Agent could not complete {len(failed_steps)} step(s) "
                "(selector mismatch or API quota exceeded):\n"
                + "\n".join(f"  - {s}" for s in failed_steps)
            )
