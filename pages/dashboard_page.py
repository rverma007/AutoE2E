"""
DashboardPage — My Dashboard post-login landing page.

Stat cards (Draft & Imported, Pending, Rejected, Approved) and their
interaction with the letter-type-version API are encapsulated here.
"""
from __future__ import annotations

import re
from typing import Dict, Optional

from playwright.sync_api import Page

from pages.base_page import BasePage


class DashboardPage(BasePage):
    PATH = "dashboard"

    # Primary selectors: Tailwind color classes pinpoint each stat card count.
    # Fallback selectors added because class names change across UI releases.
    _COUNT_SELECTORS: Dict[str, list] = {
        "draft_imported": [
            "p.text-\\[28px\\].text-tx-primary",
            "[class*='stat'][class*='draft'] [class*='count'], "
            "[class*='card']:nth-child(1) [class*='count'], "
            "[class*='card']:nth-child(1) p[class*='text-']",
        ],
        "pending": [
            "p.text-\\[28px\\].text-tx-pending",
            "[class*='stat'][class*='pending'] [class*='count'], "
            "[class*='card']:nth-child(2) [class*='count'], "
            "[class*='card']:nth-child(2) p[class*='text-']",
        ],
        "rejected": [
            "p.text-\\[28px\\].text-tx-error",
            "[class*='stat'][class*='reject'] [class*='count'], "
            "[class*='card']:nth-child(3) [class*='count'], "
            "[class*='card']:nth-child(3) p[class*='text-']",
        ],
        "approved": [
            "p.text-\\[28px\\].text-tx-success",
            "[class*='stat'][class*='approv'] [class*='count'], "
            "[class*='card']:nth-child(4) [class*='count'], "
            "[class*='card']:nth-child(4) p[class*='text-']",
        ],
    }

    _CARD_LABELS: Dict[str, str] = {
        "draft_imported": "Draft & Imported Versions",
        "pending":        "Pending Approvals",
        "rejected":       "Rejected Approvals",
        "approved":       "Approved Versions",
    }

    # ── Locators ─────────────────────────────────────────────────────────────

    @property
    def _welcome_text(self):
        # Try both "LettersHub" and "LetterHub" spellings; also accept any h1/h2
        # that appears after the dashboard API response arrives.
        return self.page.locator(
            "text=Welcome to LettersHub!, "
            "text=Welcome to LetterHub!, "
            "text=Welcome, "
            "h1, h2"
        ).first

    @property
    def _footer_text(self):
        return self.page.locator("text=/Showing.*results of/").first

    # ── Load check ───────────────────────────────────────────────────────────

    def is_loaded(self, timeout: int = 20_000) -> bool:
        # Fast path: welcome banner
        if self.is_visible(self._welcome_text, timeout=timeout):
            return True
        # Fallback: at least verify we're on the dashboard route
        return "dashboard" in self.page.url

    def open_direct(self) -> "DashboardPage":
        self.navigate()
        self.dismiss_ask_auto_popup()
        return self

    # ── Stat card helpers ─────────────────────────────────────────────────────

    def get_card_count(self, card: str) -> int:
        """
        Read the numeric count shown on a stat card.
        `card` must be one of: draft_imported | pending | rejected | approved.

        Tries the primary Tailwind selector then falls back to positional
        selectors so the test survives minor CSS refactors.
        """
        selectors = self._COUNT_SELECTORS[card]
        for sel in selectors:
            try:
                loc = self.page.locator(sel).first
                loc.wait_for(state="visible", timeout=10_000)
                raw = loc.inner_text().strip().replace(",", "")
                if raw.isdigit():
                    return int(raw)
            except Exception:  # noqa: BLE001
                continue
        raise RuntimeError(
            f"Could not read stat card count for '{card}' with any known selector."
        )

    def click_card(self, card: str) -> None:
        """Click a stat card to switch the detail table to that status filter."""
        self.dismiss_ask_auto_popup()
        label = self._CARD_LABELS[card]
        self.page.get_by_text(label, exact=True).first.click()
        self.wait_for_idle()

    # ── Footer ────────────────────────────────────────────────────────────────

    def get_footer_count(self, default: int = 0) -> int:
        """
        Parse the total from the footer: "Showing 1 – 10 results of 86" → 86.

        Returns `default` (0) when the footer is absent — which happens when
        the filtered result set is empty or fits on one page without pagination.
        Never raises so callers can compare counts without try/except.
        """
        if not self.is_visible(self._footer_text, timeout=8_000):
            return default
        try:
            text = self._footer_text.inner_text()
            match = re.search(r"results of\s+([\d,]+)", text)
            if not match:
                return default
            return int(match.group(1).replace(",", ""))
        except Exception:  # noqa: BLE001
            return default

    # ── API intercept helper ──────────────────────────────────────────────────

    def capture_status_summary(self) -> Dict[str, int]:
        """
        Navigate to the dashboard while intercepting the letter-type-version
        API response that contains the full statusSummary.
        """
        with self.page.expect_response(
            lambda r: "letter-type-version" in r.url and r.status == 200,
            timeout=60_000,
        ) as resp_info:
            self.navigate()
        body = resp_info.value.json()
        self.dismiss_ask_auto_popup()
        return body.get("statusSummary", {})
