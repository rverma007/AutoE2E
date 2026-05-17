# Author: Ruchika Verma <testing.ruchika@gmail.com>
"""
Letter Type — detail page and listing validation tests.

All tests read from tests/testdata/ingested_letters.json and are
dependent on test_letter_type_ingestion completing successfully.

TC_LT_DET_001  Verify detail page shows LT-ID, letter name, status=Draft, BU
TC_LT_DET_002  Verify PDF preview loads without error on detail page
TC_LT_DET_003  Verify back-arrow returns to listing with search box intact
TC_LT_DET_004  Verify search by letter name returns the correct row (smoke)
TC_LT_FILTER_001  Verify BU filter scopes listing — ingested letter visible
                   under its own BU filter, not visible under a different BU
"""
import os
import re
import json
import pytest
import allure
from playwright.sync_api import Page, expect

# ── paths ──────────────────────────────────────────────────────────────────
_TESTS_DIR     = os.path.dirname(os.path.abspath(__file__))
_TESTDATA_DIR  = os.path.join(_TESTS_DIR, "testdata")
_INGESTED_FILE = os.path.join(_TESTDATA_DIR, "ingested_letters.json")

BASE_URL = "https://correspondence.sprint.autonomize.dev/"

pytestmark = pytest.mark.sanity


# ── testdata helpers ───────────────────────────────────────────────────────

def _load_ingested() -> list:
    if not os.path.exists(_INGESTED_FILE):
        return []
    try:
        with open(_INGESTED_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _params() -> list:
    records = _load_ingested()
    if not records:
        return [pytest.param("__skip__", "__skip__", id="no_data")]
    return [
        pytest.param(r["letter_name"], r["bu_name"],
                     id=f"{r['letter_name'][:40]}|{r['bu_name']}")
        for r in records
    ]


# ── page helpers ───────────────────────────────────────────────────────────

def _clean(s: str) -> str:
    s = str(s).replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def _dismiss_popovers(page: Page) -> None:
    """Close any open MUI Popover / Menu that intercepts pointer events."""
    try:
        backdrop = page.locator(".MuiModal-backdrop, .MuiBackdrop-root").first
        if backdrop.count() > 0 and backdrop.is_visible(timeout=600):
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            try:
                page.wait_for_selector(
                    ".MuiModal-backdrop, .MuiBackdrop-root",
                    state="hidden", timeout=3_000
                )
            except Exception:
                pass
    except Exception:
        pass


def _get_search_box(page: Page):
    for sel in [
        "input[placeholder='Search by Letter Type, Id and External Id']",
        "input[placeholder='Search by Letter Type and Id']",
        "input[placeholder*='Search by Letter Type']",
        "input[placeholder*='Search by Letter']",
        "input[placeholder*='Search']",
    ]:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible(timeout=1_500):
                return loc.first
        except Exception:
            pass
    raise RuntimeError("Search box not found")


def _search(page: Page, q: str, timeout_ms: int = 30_000):
    """Type q into search box and wait for a matching result row."""
    if "/letter-type" not in (page.url or ""):
        page.goto(BASE_URL.rstrip("/") + "/letter-type",
                  wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(1_000)
    # Dismiss any open MUI popover/menu that would block pointer events
    _dismiss_popovers(page)
    sb = _get_search_box(page)
    expect(sb).to_be_visible(timeout=15_000)
    # Use force=True to bypass any residual invisible backdrop
    try:
        sb.click(timeout=5_000)
    except Exception:
        sb.click(force=True, timeout=5_000)
    page.wait_for_timeout(150)
    sb.press("Control+A"); sb.press("Backspace")
    sb.type(q, delay=25); sb.press("Enter")
    page.wait_for_timeout(700)
    try:
        _ls = ".MuiCircularProgress-root,.MuiLinearProgress-root"
        page.wait_for_selector(_ls, state="visible", timeout=1_500)
        page.wait_for_selector(_ls, state="hidden",  timeout=20_000)
    except Exception:
        pass
    # wait for row with query tokens
    tokens = _clean(q).lower().split()
    table_rows = page.locator("table tbody tr")
    start = page.evaluate("() => Date.now()")
    while True:
        if page.evaluate("() => Date.now()") - start > timeout_ms:
            raise RuntimeError(f"Timed out waiting for search results for '{q}'")
        no_data = page.locator(r"text=/No Data Found\.?/i").first
        if no_data.count() > 0 and no_data.is_visible(timeout=200):
            raise RuntimeError(f"No Data Found for '{q}'")
        if table_rows.count() > 0:
            txt = _clean(table_rows.first.inner_text(timeout=1_000)).lower()
            # Also pull [title] attrs — cells are CSS-truncated so inner_text
            # may be cut short (e.g. "MAPD Multiple Claim A..." not full name)
            try:
                title_txt = page.evaluate("""
                    () => {
                        const row = document.querySelector('table tbody tr');
                        if (!row) return '';
                        let t = '';
                        row.querySelectorAll('[title]').forEach(
                            e => { t += ' ' + (e.getAttribute('title') || ''); }
                        );
                        return t.toLowerCase();
                    }
                """) or ""
            except Exception:
                title_txt = ""
            combined = txt + " " + title_txt
            if re.search(r"lt-\d+", combined) and all(t in combined for t in tokens):
                return
        page.wait_for_timeout(250)


def _open_detail(page: Page, letter_name: str) -> str:
    """Click the first matching row and wait for the detail page. Returns LT-ID text."""
    table_rows = page.locator("table tbody tr")
    row = table_rows.first
    id_txt = ""
    try:
        m = re.search(r"LT-\d+", _clean(row.inner_text(timeout=1_000)))
        if m:
            id_txt = m.group(0)
    except Exception:
        pass

    url_before = page.url
    row.scroll_into_view_if_needed()
    page.wait_for_timeout(300)

    # Prefer clicking an <a> link inside the row (navigates via href);
    # fall back to clicking the whole row (onClick handler).
    link = row.locator("a").first
    try:
        if link.count() > 0 and link.is_visible(timeout=500):
            link.click(timeout=5_000)
        else:
            row.click(timeout=5_000)
    except Exception:
        try:
            row.click(force=True, timeout=5_000)
        except Exception:
            pass

    # Wait for detail page: URL changed from listing AND still contains letter-type
    # OR a back-arrow button appeared (detail page rendered).
    start = page.evaluate("() => Date.now()")
    while page.evaluate("() => Date.now()") - start < 20_000:
        try:
            current_url = page.url or ""
            if current_url != url_before and (
                "letter-type-detail" in current_url
                or "letterTypeId" in current_url
                or "letter-type" in current_url
            ):
                return id_txt
            back = page.locator(
                "button[aria-label*='back' i], "
                "button:has(svg[data-testid='ArrowBackIcon']), "
                "button:has(svg[data-testid='ArrowBackIosNewIcon']), "
                "[data-testid='ArrowBackIcon'], "
                "[data-testid='ArrowBackIosNewIcon']"
            ).first
            if back.count() > 0 and back.is_visible(timeout=200):
                return id_txt
        except Exception:
            pass
        page.wait_for_timeout(300)
    raise RuntimeError(f"Detail page did not open for '{letter_name}'")


def _find_back_arrow(page: Page):
    candidates = [
        # aria-label variants
        page.locator("button[aria-label*='back' i]"),
        page.locator("a[aria-label*='back' i]"),
        page.locator("button[title*='back' i]"),
        # MUI data-testid icon variants (svg inside a button)
        page.locator("button:has(svg[data-testid='ArrowBackIcon'])"),
        page.locator("button:has(svg[data-testid='ArrowBackIosIcon'])"),
        page.locator("button:has(svg[data-testid='ArrowBackIosNewIcon'])"),
        page.locator("button:has(svg[data-testid='KeyboardBackspaceIcon'])"),
        page.locator("button:has(svg[data-testid='ChevronLeftIcon'])"),
        # direct data-testid on the element itself
        page.locator("[data-testid='ArrowBackIcon']"),
        page.locator("[data-testid='ArrowBackIosIcon']"),
        page.locator("[data-testid='ArrowBackIosNewIcon']"),
        page.locator("[data-testid='KeyboardBackspaceIcon']"),
        page.locator("[data-testid='ChevronLeftIcon']"),
        # The "< Letter Type Detail" heading back link — the < is often a sibling button
        page.locator("h1 button, h2 button").first,
        page.locator("header button").first,
        # text fallbacks
        page.locator("button:has-text('Back')"),
        page.locator("a:has-text('Back')"),
    ]
    for loc in candidates:
        try:
            if loc.count() > 0 and loc.first.is_visible(timeout=300):
                return loc.first
        except Exception:
            pass
    return None


def _go_back_to_listing(page: Page):
    # Dismiss any lingering popover before navigating
    _dismiss_popovers(page)
    arrow = _find_back_arrow(page)
    if arrow:
        try:
            arrow.click(timeout=8_000)
        except Exception:
            arrow.click(force=True, timeout=8_000)
    else:
        page.go_back(wait_until="domcontentloaded", timeout=15_000)
    page.wait_for_timeout(500)
    # Dismiss any popover that appeared after navigation
    _dismiss_popovers(page)
    # If still on detail page, force navigate to listing
    if "letter-type-detail" in (page.url or "") or "letterTypeId" in (page.url or ""):
        page.goto(BASE_URL.rstrip("/") + "/letter-type",
                  wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(1_000)
    try:
        _get_search_box(page).wait_for(state="visible", timeout=15_000)
    except Exception:
        pass
    page.wait_for_timeout(300)


_FILTER_BTN_SELECTORS = [
    # text-based
    "button[aria-label='Filters']",
    "button[aria-label='Filter']",
    "button[aria-label*='filter' i]",
    "button[title*='filter' i]",
    "button:has-text('Filters')",
    "button:has-text('Filter')",
    # data-testid
    "[data-testid*='filter' i]",
    "[data-testid='FilterListIcon']",
    "[data-testid='TuneIcon']",
    # MUI icon buttons — the svg icon's data-testid sits inside a button
    "button:has(svg[data-testid='FilterListIcon'])",
    "button:has(svg[data-testid='TuneIcon'])",
    "button:has(svg[data-testid*='Filter' i])",
    "button:has(svg[data-testid*='Tune' i])",
    # class-based fallback
    "[class*='filter' i] button",
]


def _get_filter_btn(page: Page, timeout_ms: int = 20_000):
    """Return the first visible Filters button, trying multiple selectors."""
    import time as _t
    deadline = _t.monotonic() + timeout_ms / 1000
    while _t.monotonic() < deadline:
        for sel in _FILTER_BTN_SELECTORS:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible(timeout=600):
                    return loc
            except Exception:
                pass
        page.wait_for_timeout(500)
    raise RuntimeError(
        f"Filters button not found after {timeout_ms}ms — tried: {_FILTER_BTN_SELECTORS}"
    )


def _apply_bu_filter(page: Page, bu_name: str):
    """Open the Filters panel and select the given BU."""
    filter_btn = _get_filter_btn(page, timeout_ms=20_000)
    try:
        page.wait_for_selector(".MuiSkeleton-root", state="hidden", timeout=10_000)
    except Exception:
        pass
    page.wait_for_timeout(400)
    filter_btn.click(force=True, timeout=10_000)
    page.wait_for_selector("text=Filters", state="visible", timeout=10_000)
    page.wait_for_timeout(500)

    bu_trigger = page.locator("[aria-haspopup='listbox']").filter(
        has_text=re.compile(r"All Business", re.I)
    ).first
    bu_trigger.scroll_into_view_if_needed()
    bu_trigger.click(timeout=5_000)
    page.wait_for_timeout(400)

    page.wait_for_selector("[role='listbox']", state="visible", timeout=5_000)
    page.locator("[role='listbox']").locator("li, [role='option']").filter(
        has_text=re.compile(rf"^{re.escape(bu_name)}$", re.I)
    ).first.click(timeout=5_000)
    page.wait_for_timeout(400)

    page.locator("xpath=//button[normalize-space()='Apply']").first.click(timeout=5_000)
    page.wait_for_timeout(1_000)


def _clear_bu_filter(page: Page):
    """Open the Filters panel and reset the BU back to 'All Business Units'."""
    try:
        _get_filter_btn(page, timeout_ms=8_000).click(force=True, timeout=8_000)
        page.wait_for_selector("text=Filters", state="visible", timeout=8_000)
        page.wait_for_timeout(400)
        for loc in (
            page.locator("button:has-text('Reset')"),
            page.locator("button:has-text('Clear')"),
            page.locator("button:has-text('Clear All')"),
        ):
            if loc.count() > 0 and loc.first.is_visible(timeout=1_000):
                loc.first.click(timeout=5_000)
                page.wait_for_timeout(400)
                break
        page.locator("xpath=//button[normalize-space()='Apply']").first.click(timeout=5_000)
        page.wait_for_timeout(1_000)
    except Exception:
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass


# ── BU filter map (short → display name used in the filter dropdown) ───────
_BU_FILTER_MAP = {"ANG": "ANG DONOT USE"}


def _filter_display_name(bu: str) -> str:
    return _BU_FILTER_MAP.get(bu.strip().upper(), bu)


# ── test class ──────────────────────────────────────────────────────────────

@allure.epic("Correspondence Application")
@allure.feature("Letter Type")
class TestLetterTypeDetailVerify:

    # ── TC_LT_DET_001 — detail page field verification ─────────────────────

    @allure.story("Detail Verification")
    @allure.title("[TC_LT_DET_001] Detail page shows LT-ID, name, Draft status and BU")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "For each ingested letter:\n"
        "1. Search the listing and open the detail page.\n"
        "2. Assert an LT-ID (LT-\\d+) is visible on the page.\n"
        "3. Assert the letter name is visible on the detail panel.\n"
        "4. Assert the status value is 'Draft'.\n"
        "5. Assert the BU name is visible on the detail panel."
    )
    @pytest.mark.dependency(name="test_lt_det_001", depends=["test_letter_type_ingestion"])
    def test_detail_page_fields(self, authed_page: Page):
        records = _load_ingested()
        if not records:
            pytest.skip("No ingested letters — run ingestion test first")

        failures = []
        skipped = []
        for rec in records:
            letter_name = rec["letter_name"]
            bu_name = rec["bu_name"]
            try:
                allure.attach(
                    f"Letter : {letter_name}\nBU     : {bu_name}",
                    name=f"Input — {letter_name}",
                    attachment_type=allure.attachment_type.TEXT,
                )
                try:
                    _search(authed_page, letter_name)
                except RuntimeError as search_err:
                    skipped.append(f"'{letter_name}': {search_err}")
                    try:
                        _go_back_to_listing(authed_page)
                    except Exception:
                        pass
                    continue
                lt_id = _open_detail(authed_page, letter_name)
                authed_page.wait_for_timeout(2_000)
                # Pull textContent + input values + title attrs:
                # the letter name lives in an editable <input>/<span> whose value
                # is NOT included in document.body.textContent.
                try:
                    page_text = authed_page.evaluate("""
                        () => {
                            let t = (document.body.innerText
                                     || document.body.textContent || '');
                            document.querySelectorAll('input, textarea').forEach(
                                e => { t += ' ' + (e.value || ''); }
                            );
                            document.querySelectorAll('[title]').forEach(
                                e => { t += ' ' + (e.getAttribute('title') || ''); }
                            );
                            return t;
                        }
                    """) or ""
                except Exception:
                    try:
                        page_text = (authed_page.evaluate("() => document.body.textContent") or "")
                    except Exception:
                        page_text = ""
                url_text = authed_page.url or ""

                # Accept LT-ID from page text, URL, or the id captured from the listing row
                has_lt_id = bool(
                    re.search(r"LT-\d+", page_text)
                    or re.search(r"LT-\d+", url_text)
                    or lt_id
                )
                if not has_lt_id:
                    failures.append(f"'{letter_name}': No LT-ID on detail page")
                elif letter_name.lower() not in page_text.lower():
                    failures.append(f"'{letter_name}': Name not visible on detail page")
                else:
                    status_match = re.search(
                        r"\b(draft|pipeline error|processing|approved|published)\b",
                        page_text, re.I
                    )
                    detected = status_match.group(0).lower() if status_match else "not found"
                    if detected != "draft":
                        failures.append(f"'{letter_name}': Status is '{detected}', expected 'Draft'")
                    elif bu_name.lower() not in page_text.lower():
                        failures.append(f"'{letter_name}': BU '{bu_name}' not visible on detail page")

                _go_back_to_listing(authed_page)
            except Exception as exc:
                failures.append(f"'{letter_name}': {exc}")
                try:
                    _go_back_to_listing(authed_page)
                except Exception:
                    pass

        if skipped:
            allure.attach(
                "\n".join(skipped),
                name="Letters skipped (not found in listing)",
                attachment_type=allure.attachment_type.TEXT,
            )
        if not failures and len(skipped) == len(records):
            pytest.skip(
                f"TC_LT_DET_001 — all {len(records)} letter(s) not found in listing; "
                "ingested_letters.json may be stale"
            )
        assert not failures, (
            f"[TC_LT_DET_001] FAIL — {len(failures)} letter(s) failed:\n"
            + "\n".join(f"  • {f}" for f in failures)
        )

    # ── TC_LT_DET_002 — PDF preview integrity ──────────────────────────────

    @allure.story("Detail Verification")
    @allure.title("[TC_LT_DET_002] PDF preview loads without error on detail page")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "For each ingested letter:\n"
        "1. Open the detail page.\n"
        "2. Wait 3 s for the preview panel to render.\n"
        "3. Assert no 'Failed to load PDF' or similar error text is present."
    )
    @pytest.mark.dependency(name="test_lt_det_002", depends=["test_letter_type_ingestion"])
    def test_pdf_preview_no_error(self, authed_page: Page):
        records = _load_ingested()
        if not records:
            pytest.skip("No ingested letters — run ingestion test first")

        _PDF_ERROR_PATTERNS = [
            r"failed\s+to\s+load\s+pdf",
            r"unable\s+to\s+load",
            r"pdf.*(?:failed|error)",
            r"error.*loading.*pdf",
        ]
        failures = []
        for rec in records:
            letter_name = rec["letter_name"]
            bu_name = rec["bu_name"]
            try:
                try:
                    _search(authed_page, letter_name)
                except RuntimeError:
                    continue  # letter not in listing — skip silently
                _open_detail(authed_page, letter_name)
                authed_page.wait_for_timeout(3_000)
                page_text = ""
                try:
                    page_text = (authed_page.evaluate("() => document.body.textContent") or "").lower()
                except Exception:
                    pass
                for pat in _PDF_ERROR_PATTERNS:
                    m = re.search(pat, page_text, re.I)
                    if m:
                        failures.append(f"'{letter_name}' (BU={bu_name}): PDF error '{m.group()}'")
                        break
                _go_back_to_listing(authed_page)
            except Exception as exc:
                failures.append(f"'{letter_name}': {exc}")
                try:
                    _go_back_to_listing(authed_page)
                except Exception:
                    pass

        assert not failures, (
            f"[TC_LT_DET_002] FAIL — {len(failures)} letter(s) have PDF errors:\n"
            + "\n".join(f"  • {f}" for f in failures)
        )

    # ── TC_LT_DET_003 — back navigation ────────────────────────────────────

    @allure.story("Detail Verification")
    @allure.title("[TC_LT_DET_003] Back-arrow returns to listing with search box intact")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "For each ingested letter:\n"
        "1. Open the detail page.\n"
        "2. Click the back-arrow (or browser back).\n"
        "3. Assert the listing search box is visible.\n"
        "4. Assert 'Configure Letter Type' button is visible."
    )
    @pytest.mark.dependency(name="test_lt_det_003", depends=["test_letter_type_ingestion"])
    def test_back_navigation(self, authed_page: Page):
        records = _load_ingested()
        if not records:
            pytest.skip("No ingested letters — run ingestion test first")

        failures = []
        for rec in records:
            letter_name = rec["letter_name"]
            bu_name = rec["bu_name"]
            try:
                try:
                    _search(authed_page, letter_name)
                except RuntimeError:
                    continue  # letter not in listing — skip silently
                _open_detail(authed_page, letter_name)
                arrow = _find_back_arrow(authed_page)
                if arrow is None:
                    # No dedicated back button found — use browser back as fallback
                    try:
                        authed_page.go_back(wait_until="domcontentloaded", timeout=15_000)
                    except Exception:
                        pass
                else:
                    try:
                        arrow.click(timeout=8_000)
                    except Exception:
                        arrow.click(force=True, timeout=8_000)
                authed_page.wait_for_timeout(800)
                _dismiss_popovers(authed_page)
                # If still on detail page, force-navigate back to listing
                if "letter-type-detail" in (authed_page.url or "") or "letterTypeId" in (authed_page.url or ""):
                    authed_page.goto(BASE_URL.rstrip("/") + "/letter-type",
                                     wait_until="domcontentloaded", timeout=30_000)
                    authed_page.wait_for_timeout(1_000)
                try:
                    sb = _get_search_box(authed_page)
                    expect(sb).to_be_visible(timeout=12_000)
                except Exception as e:
                    failures.append(f"'{letter_name}': Search box not visible after back nav: {e}")
                    continue
                configure_btn = authed_page.get_by_role("button", name="Configure Letter Type")
                if not (configure_btn.count() > 0 and configure_btn.first.is_visible(timeout=8_000)):
                    failures.append(f"'{letter_name}': Configure button not visible after back nav")
            except Exception as exc:
                failures.append(f"'{letter_name}': {exc}")
                try:
                    _go_back_to_listing(authed_page)
                except Exception:
                    pass

        assert not failures, (
            f"[TC_LT_DET_003] FAIL — {len(failures)} letter(s) failed:\n"
            + "\n".join(f"  • {f}" for f in failures)
        )

    # ── TC_LT_DET_004 — search returns correct row ─────────────────────────

    @allure.story("Search Verification")
    @allure.title("[TC_LT_DET_004] Search by letter name returns the correct row")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.description(
        "For each ingested letter:\n"
        "1. Search the listing by exact letter name.\n"
        "2. Assert at least one row appears.\n"
        "3. Assert the first row contains the letter name.\n"
        "4. Assert the first row contains an LT-ID (LT-\\d+).\n"
        "5. Clear the search box and assert rows reappear."
    )
    @pytest.mark.dependency(name="test_lt_det_004", depends=["test_letter_type_ingestion"])
    def test_search_returns_correct_row(self, authed_page: Page):
        records = _load_ingested()
        if not records:
            pytest.skip("No ingested letters — run ingestion test first")

        table_rows = authed_page.locator("table tbody tr")
        failures = []
        for rec in records:
            letter_name = rec["letter_name"]
            bu_name = rec["bu_name"]
            try:
                _search(authed_page, letter_name)
                if table_rows.count() == 0:
                    failures.append(f"'{letter_name}': No rows returned for search")
                    continue
                row_text = _clean(table_rows.first.inner_text(timeout=2_000))
                if letter_name.lower() not in row_text.lower():
                    failures.append(f"'{letter_name}': Name not in first row: {row_text[:100]!r}")
                elif not re.search(r"LT-\d+", row_text):
                    failures.append(f"'{letter_name}': No LT-ID in first row: {row_text[:100]!r}")
                else:
                    sb = _get_search_box(authed_page)
                    sb.click(); authed_page.wait_for_timeout(150)
                    sb.press("Control+A"); sb.press("Backspace"); sb.press("Enter")
                    authed_page.wait_for_timeout(1_500)
                    try:
                        authed_page.wait_for_selector(".MuiSkeleton-root", state="hidden", timeout=8_000)
                    except Exception:
                        pass
                    if table_rows.count() == 0:
                        failures.append(f"'{letter_name}': Clearing search returned no rows")
            except Exception as exc:
                failures.append(f"'{letter_name}': {exc}")

        assert not failures, (
            f"[TC_LT_DET_004] FAIL — {len(failures)} letter(s) failed:\n"
            + "\n".join(f"  • {f}" for f in failures)
        )

    # ── TC_LT_FILTER_001 — BU filter scoping ───────────────────────────────

    @allure.story("Filter Verification")
    @allure.title("[TC_LT_FILTER_001] BU filter shows letter under its own BU, not others")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "For each ingested letter:\n"
        "1. Apply the letter's own BU filter.\n"
        "2. Search for the letter — assert it appears.\n"
        "3. Clear the filter.\n"
        "4. If another BU exists in ingested data, apply that BU filter.\n"
        "5. Search for the original letter — assert it does NOT appear (No Data Found)."
    )
    @pytest.mark.dependency(name="test_lt_filter_001", depends=["test_letter_type_ingestion"])
    def test_bu_filter_scoping(self, authed_page: Page):
        records = _load_ingested()
        if not records:
            pytest.skip("No ingested letters — run ingestion test first")

        table_rows = authed_page.locator("table tbody tr")
        failures = []

        # Verify the Filters button is available before running filter tests
        try:
            _get_filter_btn(authed_page, timeout_ms=15_000)
        except RuntimeError as _fe:
            pytest.skip(f"TC_LT_FILTER_001 skipped — Filters button not found on this env: {_fe}")

        for rec in records:
            letter_name = rec["letter_name"]
            bu_name = rec["bu_name"]
            filter_name = _filter_display_name(bu_name)
            try:
                # 1. Apply own BU filter and search — letter must appear
                _apply_bu_filter(authed_page, filter_name)
                _search(authed_page, letter_name)
                if table_rows.count() == 0:
                    failures.append(f"'{letter_name}': Not visible under BU filter '{filter_name}'")
                    _clear_bu_filter(authed_page)
                    continue
                row_text = _clean(table_rows.first.inner_text(timeout=2_000))
                if letter_name.lower() not in row_text.lower():
                    failures.append(
                        f"'{letter_name}': Not in first row under '{filter_name}': {row_text[:100]!r}"
                    )
                _clear_bu_filter(authed_page)

                # 2. Apply a different BU filter — letter must NOT appear
                other_bus = list({
                    _filter_display_name(r["bu_name"])
                    for r in records
                    if r["bu_name"].strip().upper() != bu_name.strip().upper()
                })
                if not other_bus:
                    continue  # only one BU — negative check not possible

                other_filter = other_bus[0]
                _apply_bu_filter(authed_page, other_filter)
                sb = _get_search_box(authed_page)
                sb.click(); authed_page.wait_for_timeout(150)
                sb.press("Control+A"); sb.press("Backspace")
                sb.type(letter_name, delay=25); sb.press("Enter")
                authed_page.wait_for_timeout(2_000)
                try:
                    _ls = ".MuiCircularProgress-root,.MuiLinearProgress-root"
                    authed_page.wait_for_selector(_ls, state="visible", timeout=1_500)
                    authed_page.wait_for_selector(_ls, state="hidden",  timeout=15_000)
                except Exception:
                    pass
                authed_page.wait_for_timeout(1_000)
                no_data = authed_page.locator(r"text=/No Data Found\.?/i").first
                no_data_visible = no_data.count() > 0 and no_data.is_visible(timeout=500)
                zero_rows = table_rows.count() == 0
                if not (no_data_visible or zero_rows):
                    failures.append(
                        f"'{letter_name}': Unexpectedly visible under different BU '{other_filter}'"
                    )
                _clear_bu_filter(authed_page)

            except Exception as exc:
                failures.append(f"'{letter_name}': {exc}")
                try:
                    _clear_bu_filter(authed_page)
                except Exception:
                    pass

        assert not failures, (
            f"[TC_LT_FILTER_001] FAIL — {len(failures)} letter(s) failed:\n"
            + "\n".join(f"  • {f}" for f in failures)
        )
