"""
Sanity / smoke tests for the Correspondence application.

Goal: confirm the app is alive and the basic "happy path" works after every
deploy.  Each test is short, independent, and tagged @pytest.mark.sanity so
you can run just the smokes with:

    pytest -m sanity

No selectors, URLs, or credentials are hardcoded here — everything comes
from the page objects and the Config layer.
"""
from __future__ import annotations

import allure
import pytest

from config.config import Config
from pages.letter_type_page import LetterTypePage
from pages.login_page import LoginPage


pytestmark = pytest.mark.sanity


# ---------------------------------------------------------------------------
# 1. Environment / landing
# ---------------------------------------------------------------------------
@allure.epic("Correspondence Application")
@allure.feature("Environment Health")
class TestEnvironment:
    """Pre-login checks that verify the environment is reachable."""

    @allure.story("Base URL Accessibility")
    @allure.title("Base URL loads the login screen")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.description(
        "Navigate to the configured BASE_URL and confirm the login form is "
        "rendered. A failure here means the environment is completely down."
    )
    def test_base_url_is_reachable(self, page, login_page: LoginPage):
        """Loading the base URL should surface the login screen."""
        with allure.step(f"Open base URL: {Config.BASE_URL}"):
            login_page.open()
        with allure.step("Assert login form is visible"):
            assert login_page.is_displayed(), (
                f"Login form not visible at {Config.BASE_URL}. "
                "Is the environment up?"
            )

    @allure.story("Login Page Structure")
    @allure.title("Login page contains all required fields")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Verify that the login page exposes a username field, a password field, "
        "and a submit button. Missing any of these makes login impossible."
    )
    def test_login_page_has_required_fields(self, login_page: LoginPage):
        """Username, password, and a submit control must all be visible."""
        with allure.step("Open the login page"):
            login_page.open()
        with allure.step("Username input is visible"):
            assert login_page.is_visible(login_page.username_input), "username field missing"
        with allure.step("Password input is visible"):
            assert login_page.is_visible(login_page.password_input), "password field missing"
        with allure.step("Submit button is visible"):
            assert login_page.is_visible(login_page.submit_button), "submit button missing"

    @allure.story("Login Page Structure")
    @allure.title("Login page has a non-empty document title")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Check that the browser <title> tag is populated after the page loads. "
        "An empty title indicates the app shell failed to render correctly."
    )
    def test_page_title_is_present(self, login_page: LoginPage):
        """A non-empty <title> means the app shell rendered."""
        with allure.step("Open the login page"):
            login_page.open()
        with allure.step("Assert document title is not empty"):
            assert login_page.title().strip(), "Empty document title"


# ---------------------------------------------------------------------------
# 2. Authentication
# ---------------------------------------------------------------------------
@allure.epic("Correspondence Application")
@allure.feature("Authentication")
class TestAuthentication:
    """Login-centric smoke checks."""

    @allure.story("Valid Login")
    @allure.title("Valid credentials authenticate and redirect to Letter Type listing")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.description(
        "Submit the configured valid credentials and confirm the user lands on "
        "the Letter Type listing page. This is the core happy-path login flow."
    )
    def test_login_with_valid_credentials(self, page, login_page: LoginPage):
        """A valid login should land on an authenticated app page."""
        from urllib.parse import urlparse
        with allure.step("Open the login page"):
            login_page.open()
        with allure.step("Submit valid credentials"):
            login_page.login()  # default creds from Config
        with allure.step("Verify URL is on the app domain (not Keycloak)"):
            app_host = urlparse(Config.BASE_URL).netloc
            current_host = urlparse(page.url).netloc
            allure.attach(
                f"App host  : {app_host}\nCurrent URL: {page.url}",
                name="Post-login URL",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert current_host == app_host, (
                f"After login, browser is still on '{current_host}' not '{app_host}'. "
                f"Full URL: {page.url}"
            )
        with allure.step("Navigate to Letter Type listing and verify it loads"):
            letter_type = LetterTypePage(page)
            letter_type.open_direct()
            assert letter_type.is_loaded(timeout=60_000), (
                f"Letter Type listing did not load after login. URL: {page.url}"
            )

    @allure.story("Invalid Login")
    @allure.title("Invalid credentials do not grant access to authenticated pages")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Attempt login with a deliberately wrong password and verify the user "
        "is NOT redirected to any authenticated page. The app must block or "
        "display an error — silent acceptance of bad credentials is a security failure."
    )
    def test_login_with_invalid_credentials_shows_error_or_blocks(
        self, page, login_page: LoginPage
    ):
        """Wrong password must NOT authenticate the user."""
        with allure.step("Open the login page"):
            login_page.open()
        with allure.step("Submit invalid credentials (non-existent user)"):
            try:
                # Use a non-existent username so the real account is never at
                # risk of Keycloak brute-force lockout.  max_attempts=1 avoids
                # three consecutive failures that could block the real user.
                login_page.login(
                    username="invalid_test_user_xyz@test.invalid",
                    password="__definitely-wrong__",
                    max_attempts=1,
                )
            except Exception:
                # expect_navigation may time out on a bad login; that's fine.
                pass
        with allure.step("Confirm authenticated listing page is NOT loaded"):
            letter_type = LetterTypePage(page)
            assert not letter_type.is_loaded(timeout=5_000), (
                "Landed on authenticated page with bad credentials!"
            )


# ---------------------------------------------------------------------------
# 3. Post-login smoke (uses shared authed session)
# ---------------------------------------------------------------------------
@allure.epic("Correspondence Application")
@allure.feature("Letter Type Listing")
class TestLetterTypeListing:
    """Core post-login surface: the Letter Type listing page."""

    @allure.story("Page Load")
    @allure.title("Letter Type listing page loads successfully")
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.description(
        "Navigate directly to the Letter Type listing and assert the page "
        "reaches a loaded state. Failure blocks every downstream listing test."
    )
    def test_listing_loads(self, letter_type_page: LetterTypePage):
        with allure.step("Open Letter Type listing directly"):
            letter_type_page.open_direct()
        with allure.step("Assert page is in loaded state"):
            assert letter_type_page.is_loaded(), "Letter Type listing did not load."

    @allure.story("Search Functionality")
    @allure.title("Search box accepts and retains typed input")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "Type a query string into the search box and verify the field value "
        "matches what was typed. Ensures the input is interactive and not read-only."
    )
    def test_search_box_accepts_input(self, letter_type_page: LetterTypePage):
        with allure.step("Open Letter Type listing directly"):
            letter_type_page.open_direct()
        with allure.step("Confirm page is loaded before interacting"):
            assert letter_type_page.is_loaded()
        with allure.step("Type 'test' into the search box"):
            letter_type_page.search("test")
        with allure.step("Verify search box retains the typed value"):
            assert letter_type_page.search_box.input_value() == "test"

    @allure.story("Listing Content")
    @allure.title("Listing page shows data rows or a graceful empty state")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "After load, assert the row count resolves without error. "
        "Zero rows (empty state) is acceptable; an unhandled exception or broken "
        "locator is not. This guards against silent rendering failures."
    )
    def test_listing_has_results_or_empty_state(
        self, letter_type_page: LetterTypePage
    ):
        """Either we see rows, or we see a graceful empty state.

        Both are acceptable on a fresh environment; a hard crash is not.
        """
        with allure.step("Open Letter Type listing directly"):
            letter_type_page.open_direct()
        with allure.step("Confirm page is loaded"):
            assert letter_type_page.is_loaded()
        with allure.step("Resolve row count (0 or more is acceptable)"):
            rows = letter_type_page.row_count()
            allure.attach(
                f"Visible rows: {rows}",
                name="Row count",
                attachment_type=allure.attachment_type.TEXT,
            )
            # Both 0 rows (graceful empty state) and N rows are valid outcomes.
            # The meaningful check is that row_count() returns without error and
            # the page remains loaded (asserted in the previous step).
            assert letter_type_page.is_loaded(), (
                "Page lost loaded state after row count check."
            )


# ---------------------------------------------------------------------------
# 4. Session / navigation
# ---------------------------------------------------------------------------
@allure.epic("Correspondence Application")
@allure.feature("Session Persistence")
class TestSessionPersistence:
    """Verify the stored session is honoured across fresh pages."""

    @allure.story("Stored Auth State")
    @allure.title("Stored authentication session bypasses the login form")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "Re-use a previously saved browser auth state and navigate directly to "
        "the Letter Type listing. The app must honour the stored session and skip "
        "the login page entirely. Failure means session persistence is broken."
    )
    def test_authed_session_bypasses_login(self, authed_page):
        """Using stored auth state should go straight past the login form."""
        with allure.step("Open Letter Type listing using stored auth session"):
            letter_type = LetterTypePage(authed_page)
            letter_type.open_direct()
        with allure.step("Assert listing loaded without hitting the login form"):
            assert letter_type.is_loaded(), (
                "Stored session did not bypass login — session persistence broken."
            )
