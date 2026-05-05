"""
BaseTest — shared helpers that every test class can inherit.

Reduces per-test boilerplate without coupling tests to a rigid fixture chain.
Inherit when two or more of these helpers would otherwise be copy-pasted.

Example:
    from tests.base_test import BaseTest

    class TestMyFeature(BaseTest):
        def test_page_loads(self, authed_page):
            page_obj = MyPage(authed_page)
            self.navigate_and_assert(page_obj)

        def test_something_else(self, authed_page, api_client):
            counts = self.get_api_counts(api_client)
            assert counts["draft"] >= 0
"""
from __future__ import annotations

import allure
import pytest

from utils.logger import get_logger


class BaseTest:
    """Shared test helpers. All methods are stateless — safe across parallel workers."""

    @property
    def log(self):
        return get_logger(self.__class__.__name__)

    # ---------------------------------------------------------------- Page helpers
    def navigate_and_assert(self, page_obj, name: str = "") -> None:
        """Open a page via its canonical URL and assert it reaches loaded state.

        Wraps the two lines that appear in virtually every test method:
            page_obj.open_direct()
            assert page_obj.is_loaded()
        """
        label = name or type(page_obj).__name__
        with allure.step(f"Navigate to {label}"):
            page_obj.open_direct()
        with allure.step(f"Assert {label} is loaded"):
            assert page_obj.is_loaded(), (
                f"{label} did not reach loaded state. URL: {page_obj.page.url}"
            )

    def assert_loaded(self, page_obj, name: str = "") -> None:
        """Assert a page is loaded without navigating (page already open)."""
        label = name or type(page_obj).__name__
        with allure.step(f"Assert {label} is loaded"):
            assert page_obj.is_loaded(), (
                f"{label} did not reach loaded state. URL: {page_obj.page.url}"
            )

    # ---------------------------------------------------------------- API helpers
    def get_api_counts(self, api_client) -> dict:
        """Return statusSummary from the API — used for UI vs API count assertions."""
        with allure.step("Fetch status summary from API"):
            summary = api_client.get_status_summary()
            allure.attach(
                str(summary),
                name="API statusSummary",
                attachment_type=allure.attachment_type.TEXT,
            )
        return summary

    # ---------------------------------------------------------------- Assert helpers
    def assert_counts_match(self, ui_value: int, api_value: int, label: str) -> None:
        """Assert UI count equals API count with a descriptive message."""
        with allure.step(f"Assert {label}: UI={ui_value} == API={api_value}"):
            assert ui_value == api_value, (
                f"{label} mismatch — UI reported {ui_value} but API returned {api_value}"
            )
