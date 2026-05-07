"""
Agentic E2E Testing — Live Demo Script
=======================================
Run this file directly to showcase all 3 levels of AI-assisted testing
to your manager.  No pytest knowledge needed — just:

    python demo_agentic.py

What the demo does
------------------
  Level 1  Visual Assertions  — Claude looks at a screenshot and answers
                                questions about the UI (no selectors needed)
  Level 2  Self-Healing       — Claude finds a broken selector automatically
                                from the live DOM
  Level 3  Autonomous Agent   — Claude reads plain-English steps and drives
                                the browser on its own

Prerequisites
-------------
  pip install -r requirements.txt
  GEMINI_API_KEY=your-key   set in your .env file (free at aistudio.google.com)
"""
from __future__ import annotations

import os
import sys
import time
import textwrap
from pathlib import Path

# ── Load .env before anything else ──────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from playwright.sync_api import sync_playwright

from config.config import Config
from pages.login_page import LoginPage
from pages.letter_type_page import LetterTypePage
from pages.nav_page import NavigationPage
from utils.ai_agent import AIAgent, ai_find_selector, ai_verify


# ── Terminal helpers ─────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
DIM    = "\033[2m"


def banner(text: str) -> None:
    width = 70
    print()
    print(CYAN + "═" * width + RESET)
    print(CYAN + BOLD + f"  {text}" + RESET)
    print(CYAN + "═" * width + RESET)


def section(title: str) -> None:
    print()
    print(BOLD + WHITE + f"▶  {title}" + RESET)
    print(DIM + "─" * 60 + RESET)


def result(label: str, passed: bool, detail: str = "") -> None:
    icon  = GREEN + "✔  PASS" + RESET if passed else RED + "✘  FAIL" + RESET
    print(f"  {icon}  {label}")
    if detail:
        print(DIM + f"         {detail}" + RESET)


def info(msg: str) -> None:
    print(YELLOW + f"  ℹ  {msg}" + RESET)


def skip(msg: str) -> None:
    print(YELLOW + f"  ⚠  SKIP — {msg}" + RESET)


def wait_for_key(msg: str = "Press ENTER to continue...") -> None:
    input(DIM + f"\n  {msg}" + RESET)


# ── Check prerequisites ──────────────────────────────────────────────────────

def check_prerequisites() -> bool:
    banner("Agentic E2E Testing — Demo by Autonomize QA")

    print(f"\n  {BOLD}Framework:{RESET}  Playwright + Python + Claude AI")
    print(f"  {BOLD}App URL:{RESET}    {Config.BASE_URL}")
    print(f"  {BOLD}User:{RESET}       {Config.APP_USERNAME}")

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        masked = api_key[:8] + "..." + api_key[-4:]
        print(f"  {BOLD}API Key:{RESET}    {GREEN}{masked} (set){RESET}")
        ai_on = True
    else:
        print(f"  {BOLD}API Key:{RESET}    {RED}NOT SET — AI levels will be skipped{RESET}")
        print(f"\n  {DIM}Add GEMINI_API_KEY to your .env to enable AI features.{RESET}")
        ai_on = False

    print()
    return ai_on


# ── Demo sections ────────────────────────────────────────────────────────────

def demo_level_1(page, ai_on: bool) -> None:
    banner("LEVEL 1 — Visual Assertions with ai_verify()")
    print(textwrap.dedent("""
      How it works:
        Claude takes a screenshot of the browser, looks at it like a human,
        and answers a yes/no question.  No CSS selectors needed.

      Why it matters:
        UI text changes, class renames, DOM restructuring — none of that
        breaks an AI assertion because Claude understands the *meaning*
        of what it sees, not the raw HTML.
    """))

    if not ai_on:
        skip("GEMINI_API_KEY not set")
        return

    wait_for_key("Ready to run Level 1 — press ENTER")

    checks = [
        ("Dashboard welcome message is visible",
         "Is there a welcome message or greeting visible on this page?",
         True),
        ("LettersHub logo or branding is present",
         "Is there a product logo or application name visible in the top-left area?",
         True),
        ("No error alert on the dashboard",
         "Is there an error message, alert banner, or failure notification visible?",
         False),
    ]

    section("Visual checks on the Dashboard page")
    for label, question, expected in checks:
        t0 = time.time()
        answer = ai_verify(page, question)
        elapsed = time.time() - t0
        passed = (answer == expected)
        result(label, passed, f"Claude answered {'YES' if answer else 'NO'} in {elapsed:.1f}s")

    # Navigate to Letter Type listing for more checks
    nav = NavigationPage(page)
    nav.go_to_letter_type()
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        pass

    section("Visual checks on Letter Type listing page")
    listing_checks = [
        ("Letter Type table is visible with rows",
         "Is there a data table with multiple rows of data visible on this page?",
         True),
        ("Search box is present",
         "Is there a search input or search box visible on this page?",
         True),
        ("No loading spinner — page is fully loaded",
         "Is there a loading spinner, skeleton screen, or 'loading' indicator still visible?",
         False),
    ]
    for label, question, expected in listing_checks:
        t0 = time.time()
        answer = ai_verify(page, question)
        elapsed = time.time() - t0
        passed = (answer == expected)
        result(label, passed, f"Claude answered {'YES' if answer else 'NO'} in {elapsed:.1f}s")


def demo_level_2(page, ai_on: bool) -> None:
    banner("LEVEL 2 — Self-Healing Selectors with ai_find_selector()")
    print(textwrap.dedent("""
      How it works:
        When a CSS selector breaks (e.g. placeholder text changed, class renamed),
        ai_find_selector() sends the live DOM + screenshot to Claude which returns
        a working selector automatically — no human intervention.

      Why it matters:
        Selector maintenance is the #1 cost of E2E test suites.
        Self-healing means broken selectors fix themselves.
    """))

    if not ai_on:
        skip("GEMINI_API_KEY not set")
        return

    wait_for_key("Ready to run Level 2 — press ENTER")

    section("Demonstrate self-healing: find the search box")

    info("Simulating a broken hardcoded selector...")
    broken_selector = "input[placeholder='THIS SELECTOR IS BROKEN']"
    element = page.locator(broken_selector).first
    try:
        is_vis = element.is_visible(timeout=1_000)
    except Exception:
        is_vis = False
    result("Broken selector finds nothing (as expected)", not is_vis,
           f"selector: {broken_selector}")

    info("Asking Claude to find the real selector from the live DOM...")
    t0 = time.time()
    selector = ai_find_selector(page, "search input for filtering letter types")
    elapsed = time.time() - t0

    if selector:
        info(f"Claude returned selector in {elapsed:.1f}s: {selector!r}")
        try:
            healed = page.locator(selector).first
            visible = healed.is_visible(timeout=3_000)
            result("Self-healed selector finds the element", visible,
                   f"selector: {selector}")
        except Exception as exc:
            result("Self-healed selector validation", False, str(exc))
    else:
        result("AI returned a selector", False, "Claude returned None")

    section("Find the Letter Type sidebar nav link")
    t0 = time.time()
    nav_selector = ai_find_selector(page, "Letter Type navigation link in the left sidebar")
    elapsed = time.time() - t0
    if nav_selector:
        info(f"Claude returned: {nav_selector!r} in {elapsed:.1f}s")
        result("Sidebar nav selector found", True, nav_selector)
    else:
        result("Sidebar nav selector found", False)


def demo_level_3(page, ai_on: bool) -> None:
    banner("LEVEL 3 — Autonomous Agent with AIAgent.run_steps()")
    print(textwrap.dedent("""
      How it works:
        You write plain-English test steps — the same way you'd describe
        them to a junior tester.  The AI agent reads each step, looks at a
        screenshot, decides what browser action to take, and executes it.

      Why it matters:
        - Non-technical stakeholders (BAs, PMs) can contribute test cases
        - Tests survive major UI redesigns
        - Exploratory testing without writing a single selector
    """))

    if not ai_on:
        skip("GEMINI_API_KEY not set")
        return

    wait_for_key("Ready to run Level 3 — press ENTER")

    # Navigate back to dashboard for a clean starting point
    nav = NavigationPage(page)
    nav.navigate()
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        pass

    steps = [
        "Confirm the dashboard page has loaded and is showing some statistics or content",
        "Click on 'Letter Configuration' in the left sidebar to expand the menu",
        "Click on 'Letter Type' in the left sidebar navigation",
        "Verify that a table with letter type records is now visible on the page",
        "Confirm there is no error message or alert visible on the page",
    ]

    section("Plain-English steps (written as if explaining to a person)")
    for i, step in enumerate(steps, 1):
        print(f"  {DIM}{i}. {step}{RESET}")

    print()
    info("Handing steps to the AI agent now...")
    agent = AIAgent(page)

    section("Agent executing steps autonomously")
    results = {}
    for i, step in enumerate(steps, 1):
        print(f"\n  {CYAN}Step {i}/{len(steps)}{RESET}: {step}")
        info("Agent is looking at the screen and deciding what to do...")
        t0 = time.time()
        passed = agent._execute_step(step)
        elapsed = time.time() - t0
        results[step] = passed
        result(f"Step {i} complete", passed, f"{elapsed:.1f}s")

    section("Agent summary")
    passed_count = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  {BOLD}Result: {passed_count}/{total} steps passed{RESET}")
    overall = passed_count == total
    result("All agent steps passed", overall)


def demo_summary(ai_on: bool) -> None:
    banner("Demo Complete — Summary")
    print(textwrap.dedent(f"""
      What was demonstrated
      ─────────────────────
      Level 1  ai_verify()         Visual assertions — no selectors, uses screenshots
      Level 2  ai_find_selector()  Self-healing — broken selectors fixed by AI
      Level 3  AIAgent             Autonomous execution from plain English steps

      Existing framework
      ──────────────────
      • Playwright + Python page objects (unchanged)
      • Pytest + Allure reporting (unchanged)
      • All existing sanity tests still run normally

      The AI layer sits ON TOP — nothing was replaced, only enhanced.

      Next steps
      ──────────
      1. Add GEMINI_API_KEY to CI/CD environment
      2. Wrap flaky selectors with ai_find_selector() as fallback
      3. Write new test cases in plain English using AIAgent.run_steps()

      Run the agentic test suite anytime:
        pytest -m agentic -v -s
    """))


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    ai_on = check_prerequisites()
    wait_for_key("Press ENTER to launch browser and begin demo...")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(viewport=Config.viewport)
        page = context.new_page()

        # ── Login ────────────────────────────────────────────────────────────
        banner("Setup — Logging in to the application")
        info("Opening login page...")
        login = LoginPage(page)
        login.open()
        info(f"Logging in as {Config.APP_USERNAME}...")
        login.login()
        info(f"Logged in. Current URL: {page.url}")

        # Wait for dashboard to settle
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass

        # Dismiss Ask Auto popup
        from pages.base_page import BasePage
        BasePage(page).dismiss_ask_auto_popup()

        # ── Run the three demo levels ─────────────────────────────────────────
        try:
            demo_level_1(page, ai_on)
            demo_level_2(page, ai_on)
            demo_level_3(page, ai_on)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}  Demo interrupted by user.{RESET}")
        finally:
            demo_summary(ai_on)
            wait_for_key("Press ENTER to close the browser...")
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
