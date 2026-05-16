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

    def row_count(self) -> int:
        """Return the number of visible data rows in the dashboard table."""
        return self.page.locator("table tbody tr").count()

    def click_first_table_row(self) -> bool:
        """Click the first data row in the dashboard letter-type table.

        Polls until the row has real text (not a skeleton placeholder).
        Returns True if navigation away from /dashboard occurred.
        """
        import time as _t
        row = self.page.locator("table tbody tr:first-child").first
        if not self.is_visible(row, timeout=10_000):
            return False
        deadline = _t.monotonic() + 10
        while _t.monotonic() < deadline:
            if self.text_of(row).strip():
                break
            self.page.wait_for_timeout(400)
        row.click()
        self.wait_for_idle()
        return "dashboard" not in self.page.url

    # ── Pending-tab toolbar elements ─────────────────────────────────────────

    @property
    def pending_search_input(self):
        return self.page.locator(
            "input[placeholder*='Search by Letter Type' i]"
        ).first

    @property
    def bulk_approve_button(self):
        return self.page.get_by_role(
            "button", name=re.compile(r"Bulk Approve", re.IGNORECASE)
        )

    @property
    def table_refresh_button(self):
        return self.page.get_by_role(
            "button", name=re.compile(r"^Refresh$", re.IGNORECASE)
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def welcome_text(self) -> str:
        """Return the welcome / greeting text visible on the dashboard."""
        for sel in ("h1", "h2", "[class*='welcome']", "[class*='greeting']"):
            loc = self.page.locator(sel).first
            if self.is_visible(loc, timeout=2_000):
                text = self.text_of(loc).strip()
                if text:
                    return text
        return ""

    def pending_tab_column_headers(self) -> list:
        """Return non-empty column header texts from the visible table."""
        headers = self.page.locator("table thead th")
        count = headers.count()
        return [
            self.text_of(headers.nth(i)).strip()
            for i in range(count)
            if self.text_of(headers.nth(i)).strip()
        ]

    def search_pending_tab(self, query: str) -> None:
        """Type a query into the pending-tab search box and wait for results."""
        self.safe_fill(self.pending_search_input, query, label="pending tab search")
        self.wait_for_idle()

    def clear_pending_search(self) -> None:
        if self.is_visible(self.pending_search_input, timeout=3_000):
            self.pending_search_input.fill("")
            self.wait_for_idle()

    # ── User menu / role ──────────────────────────────────────────────────────

    @property
    def _user_menu_trigger(self):
        # Top-right "SB Sapna Bhatt ↓" button
        return self.page.locator(
            "[class*='avatar'], "
            "button[class*='user'], "
            "button[aria-label*='account' i], "
            "header button:last-of-type"
        ).last

    def get_current_role(self) -> str:
        """Open the user-profile dropdown and return the active role text.

        The active role is the item shown directly below the user's name
        (underlined / highlighted in the screenshot).  The menu is closed
        afterwards via Escape.
        """
        if not self.is_visible(self._user_menu_trigger, timeout=5_000):
            return ""
        self.safe_click(self._user_menu_trigger, "user menu")
        self.page.wait_for_timeout(400)
        # Try common patterns for the role line inside the dropdown
        for sel in [
            "[role='menu'] p:nth-child(2)",
            "[role='menu'] span:nth-child(2)",
            "[class*='popover'] p:nth-child(2)",
            "[class*='dropdown'] p:nth-child(2)",
            "[class*='menu-item']:first-child + *",
        ]:
            loc = self.page.locator(sel).first
            if self.is_visible(loc, timeout=800):
                text = self.text_of(loc).strip()
                if text:
                    self.page.keyboard.press("Escape")
                    return text
        # Fallback: scan all menu items for known role names
        for role in ("Cac Admin", "Cac Manager", "Cac Approver", "Cac Editor"):
            loc = self.page.get_by_role("menuitem", name=role).first
            if self.is_visible(loc, timeout=500):
                # Cannot distinguish current vs others this way — return empty
                break
        self.page.keyboard.press("Escape")
        return ""

    def ensure_role(self, role_name: str) -> bool:
        """Switch to `role_name` if it is not already active.

        Returns True if the role is active (was already set or successfully switched).
        """
        if not self.is_visible(self._user_menu_trigger, timeout=5_000):
            return False
        self.safe_click(self._user_menu_trigger, "user menu")
        self.page.wait_for_timeout(400)
        role_option = self.page.get_by_text(role_name, exact=True).first
        if not self.is_visible(role_option, timeout=3_000):
            self.page.keyboard.press("Escape")
            return False
        role_option.click()
        self.wait_for_idle()
        return True

    # ── Pending-tab Review button ─────────────────────────────────────────────

    def click_review_first_row(self) -> bool:
        """Click the 'Review' button in the Actions column of the first pending row.

        Waits until the row has real content (not skeleton), then clicks Review.
        Returns True when the browser navigates away from the dashboard.
        """
        import time as _t
        row = self.page.locator("table tbody tr:first-child").first
        if not self.is_visible(row, timeout=10_000):
            return False
        deadline = _t.monotonic() + 12
        while _t.monotonic() < deadline:
            if self.text_of(row).strip():
                break
            self.page.wait_for_timeout(400)
        review_btn = row.get_by_role(
            "button", name=re.compile(r"^Review$", re.IGNORECASE)
        ).first
        if not self.is_visible(review_btn, timeout=5_000):
            # Fallback: link-style Review
            review_btn = row.get_by_text(
                re.compile(r"^Review$", re.IGNORECASE)
            ).first
        if not self.is_visible(review_btn, timeout=3_000):
            return False
        self.safe_click(review_btn, "Review")
        self.wait_for_idle()
        return "dashboard" not in self.page.url

    def click_review_for_row(self, row_index: int) -> bool:
        """Click the 'Review' button on the row at `row_index` (0-based).

        Returns True when the browser navigated away from the dashboard.
        """
        import time as _t
        rows = self.page.locator("table tbody tr")
        if rows.count() <= row_index:
            return False
        row = rows.nth(row_index)
        if not self.is_visible(row, timeout=8_000):
            return False
        deadline = _t.monotonic() + 10
        while _t.monotonic() < deadline:
            if self.text_of(row).strip():
                break
            self.page.wait_for_timeout(400)
        review_btn = row.get_by_role(
            "button", name=re.compile(r"^Review$", re.IGNORECASE)
        ).first
        if not self.is_visible(review_btn, timeout=4_000):
            review_btn = row.get_by_text(re.compile(r"^Review$", re.IGNORECASE)).first
        if not self.is_visible(review_btn, timeout=3_000):
            return False
        self.safe_click(review_btn, f"Review row {row_index}")
        self.wait_for_idle()
        return "dashboard" not in self.page.url

    def all_card_labels_visible(self, timeout: int = 10_000) -> dict[str, bool]:
        """Return {label: visible} for every stat card label."""
        return {
            label: self.is_visible(
                self.page.get_by_text(label, exact=True).first, timeout=timeout
            )
            for label in self._CARD_LABELS.values()
        }

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
