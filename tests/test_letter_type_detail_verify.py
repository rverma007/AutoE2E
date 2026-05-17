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
    sb = _get_search_box(page)
    expect(sb).to_be_visible(timeout=15_000)
    sb.click(); page.wait_for_timeout(150)
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
            if re.search(r"lt-\d+", txt) and all(t in txt for t in tokens):
                return
        page.wait_for_timeout(250)


def _open_detail(page: Page, letter_name: str) -> str:
    """Click the first matching row and wait for the detail page. Returns LT-ID text."""
    table_rows = page.locator("table tbody tr")
    row = table_rows.first
    id_cell = None
    id_txt  = ""
    for nth in [1, 0]:
        try:
            cell = row.locator("td").nth(nth)
            if cell.count() > 0 and cell.is_visible(timeout=1_500):
                t = _clean(cell.inner_text(timeout=1_500))
                if re.match(r"^LT-\d+", t):
                    id_txt = t; id_cell = cell; break
        except Exception:
            pass
    if not id_txt:
        m = re.search(r"LT-\d+", _clean(row.inner_text(timeout=1_000)))
        if m:
            id_txt = m.group(0)
    row.scroll_into_view_if_needed(); page.wait_for_timeout(300)
    try:
        (id_cell or row).click(timeout=5_000)
    except Exception:
        (id_cell or row).click(force=True, timeout=5_000)
    # wait for detail page
    start = page.evaluate("() => Date.now()")
    while page.evaluate("() => Date.now()") - start < 20_000:
        try:
            if "/letter-type/" in (page.url or ""):
                return id_txt
        except Exception:
            pass
        back = page.locator(
            "button[aria-label*='back' i], [data-testid='ArrowBackIcon'], "
            "[data-testid='KeyboardBackspaceIcon']"
        ).first
        if back.count() and back.is_visible(timeout=200):
            return id_txt
        page.wait_for_timeout(300)
    raise RuntimeError(f"Detail page did not open for '{letter_name}'")


def _find_back_arrow(page: Page):
    candidates = [
        page.locator("button[aria-label*='back' i]"),
        page.locator("[data-testid='ArrowBackIcon']"),
        page.locator("[data-testid='ArrowBackIosIcon']"),
        page.locator("[data-testid='KeyboardBackspaceIcon']"),
        page.locator("svg").filter(has=page.locator("path[d^='M20 11H7.83']")),
    ]
    for loc in candidates:
        try:
            if loc.count() > 0 and loc.first.is_visible(timeout=300):
                return loc.first
        except Exception:
            pass
    return None


def _go_back_to_listing(page: Page):
    arrow = _find_back_arrow(page)
    if arrow:
        try:
            arrow.click(timeout=8_000)
        except Exception:
            arrow.click(force=True, timeout=8_000)
    else:
        page.go_back(wait_until="domcontentloaded", timeout=15_000)
    try:
        _get_search_box(page).wait_for(state="visible", timeout=15_000)
    except Exception:
        pass
    page.wait_for_timeout(500)


def _apply_bu_filter(page: Page, bu_name: str):
    """Open the Filters panel and select the given BU."""
    page.wait_for_selector("xpath=//button[@aria-label='Filters']",
                           state="visible", timeout=20_000)
    try:
        page.wait_for_selector(".MuiSkeleton-root", state="hidden", timeout=10_000)
    except Exception:
        pass
    page.wait_for_timeout(400)
    page.locator("xpath=//button[@aria-label='Filters']").first.click(
        force=True, timeout=10_000)
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
        page.locator("xpath=//button[@aria-label='Filters']").first.click(
            force=True, timeout=8_000)
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
    @pytest.mark.parametrize("letter_name,bu_name", _params())
    def test_detail_page_fields(self, authed_page: Page, letter_name: str, bu_name: str):
        if letter_name == "__skip__":
            pytest.skip("No ingested letters — run ingestion test first")

        allure.attach(
            f"Letter : {letter_name}\nBU     : {bu_name}",
            name="Inputs",
            attachment_type=allure.attachment_type.TEXT,
        )

        with allure.step(f"Search for '{letter_name}' in listing"):
            _search(authed_page, letter_name)

        with allure.step("Open detail page"):
            lt_id = _open_detail(authed_page, letter_name)
            allure.attach(
                f"URL    : {authed_page.url}\nLT-ID  : {lt_id}",
                name="Detail page",
                attachment_type=allure.attachment_type.TEXT,
            )

        page_text = ""
        try:
            page_text = (authed_page.evaluate("() => document.body.textContent") or "").strip()
        except Exception:
            pass

        with allure.step("Assert LT-ID (LT-\\d+) is visible on detail page"):
            lt_id_match = re.search(r"LT-\d+", page_text)
            assert lt_id_match, (
                f"[TC_LT_DET_001] FAIL — No LT-ID (LT-\\d+) found on detail page "
                f"for '{letter_name}' (BU={bu_name}).\nURL: {authed_page.url}"
            )
            allure.attach(lt_id_match.group(0), name="LT-ID found",
                          attachment_type=allure.attachment_type.TEXT)

        with allure.step(f"Assert letter name '{letter_name}' is visible on detail page"):
            assert letter_name.lower() in page_text.lower(), (
                f"[TC_LT_DET_001] FAIL — Letter name '{letter_name}' not visible on "
                f"detail page (BU={bu_name}).\nURL: {authed_page.url}"
            )

        with allure.step("Assert status is 'Draft'"):
            status_match = re.search(
                r"\b(draft|pipeline error|processing|approved|published)\b",
                page_text, re.I
            )
            detected = status_match.group(0).lower() if status_match else "not found"
            allure.attach(f"Detected status: {detected}", name="Status",
                          attachment_type=allure.attachment_type.TEXT)
            assert detected == "draft", (
                f"[TC_LT_DET_001] FAIL — Status is '{detected}', expected 'Draft' "
                f"for '{letter_name}' (BU={bu_name})."
            )

        with allure.step(f"Assert BU '{bu_name}' is visible on detail page"):
            assert bu_name.lower() in page_text.lower(), (
                f"[TC_LT_DET_001] FAIL — BU '{bu_name}' not visible on detail page "
                f"for '{letter_name}'.\nURL: {authed_page.url}"
            )

        _go_back_to_listing(authed_page)

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
    @pytest.mark.parametrize("letter_name,bu_name", _params())
    def test_pdf_preview_no_error(self, authed_page: Page, letter_name: str, bu_name: str):
        if letter_name == "__skip__":
            pytest.skip("No ingested letters — run ingestion test first")

        _PDF_ERROR_PATTERNS = [
            r"failed\s+to\s+load\s+pdf",
            r"unable\s+to\s+load",
            r"pdf.*(?:failed|error)",
            r"error.*loading.*pdf",
        ]

        with allure.step(f"Search and open detail for '{letter_name}'"):
            _search(authed_page, letter_name)
            _open_detail(authed_page, letter_name)

        with allure.step("Wait for preview panel to render"):
            authed_page.wait_for_timeout(3_000)

        with allure.step("Assert no PDF load error is present"):
            page_text = ""
            try:
                page_text = (
                    authed_page.evaluate("() => document.body.textContent") or ""
                ).lower()
            except Exception:
                pass
            for pat in _PDF_ERROR_PATTERNS:
                m = re.search(pat, page_text, re.I)
                assert not m, (
                    f"[TC_LT_DET_002] FAIL — PDF preview error detected for "
                    f"'{letter_name}' (BU={bu_name}): '{m.group()}'.\n"
                    f"URL: {authed_page.url}"
                )

        _go_back_to_listing(authed_page)

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
    @pytest.mark.parametrize("letter_name,bu_name", _params())
    def test_back_navigation(self, authed_page: Page, letter_name: str, bu_name: str):
        if letter_name == "__skip__":
            pytest.skip("No ingested letters — run ingestion test first")

        with allure.step(f"Search and open detail for '{letter_name}'"):
            _search(authed_page, letter_name)
            _open_detail(authed_page, letter_name)

        with allure.step("Click back-arrow to return to listing"):
            arrow = _find_back_arrow(authed_page)
            assert arrow is not None, (
                f"[TC_LT_DET_003] FAIL — No back-arrow found on detail page for "
                f"'{letter_name}' (BU={bu_name}).\nURL: {authed_page.url}"
            )
            try:
                arrow.click(timeout=8_000)
            except Exception:
                arrow.click(force=True, timeout=8_000)
            authed_page.wait_for_timeout(1_000)

        with allure.step("Assert search box is visible on listing page"):
            try:
                sb = _get_search_box(authed_page)
                expect(sb).to_be_visible(timeout=12_000)
            except Exception as e:
                assert False, (
                    f"[TC_LT_DET_003] FAIL — Search box not visible after back navigation "
                    f"from '{letter_name}' (BU={bu_name}): {e}"
                )

        with allure.step("Assert 'Configure Letter Type' button is visible"):
            configure_btn = authed_page.get_by_role("button", name="Configure Letter Type")
            assert configure_btn.count() > 0 and configure_btn.first.is_visible(timeout=8_000), (
                f"[TC_LT_DET_003] FAIL — 'Configure Letter Type' button not visible after "
                f"back navigation from '{letter_name}' (BU={bu_name})."
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
    @pytest.mark.parametrize("letter_name,bu_name", _params())
    def test_search_returns_correct_row(self, authed_page: Page, letter_name: str, bu_name: str):
        if letter_name == "__skip__":
            pytest.skip("No ingested letters — run ingestion test first")

        table_rows = authed_page.locator("table tbody tr")

        with allure.step(f"Search for '{letter_name}'"):
            _search(authed_page, letter_name)

        with allure.step("Assert at least one row is returned"):
            assert table_rows.count() > 0, (
                f"[TC_LT_DET_004] FAIL — No rows returned for search '{letter_name}' "
                f"(BU={bu_name})."
            )

        with allure.step("Assert first row contains letter name and LT-ID"):
            row_text = _clean(table_rows.first.inner_text(timeout=2_000))
            allure.attach(f"First row: {row_text[:200]}", name="First row text",
                          attachment_type=allure.attachment_type.TEXT)
            assert letter_name.lower() in row_text.lower(), (
                f"[TC_LT_DET_004] FAIL — Letter name '{letter_name}' not found in "
                f"first row.\nRow text: {row_text[:200]!r}"
            )
            assert re.search(r"LT-\d+", row_text), (
                f"[TC_LT_DET_004] FAIL — No LT-ID in first row for '{letter_name}'.\n"
                f"Row text: {row_text[:200]!r}"
            )

        with allure.step("Clear search and assert rows reappear"):
            sb = _get_search_box(authed_page)
            sb.click(); authed_page.wait_for_timeout(150)
            sb.press("Control+A"); sb.press("Backspace"); sb.press("Enter")
            authed_page.wait_for_timeout(1_500)
            try:
                authed_page.wait_for_selector(".MuiSkeleton-root",
                                              state="hidden", timeout=8_000)
            except Exception:
                pass
            assert table_rows.count() > 0, (
                f"[TC_LT_DET_004] FAIL — Clearing search returned no rows for "
                f"'{letter_name}' (BU={bu_name})."
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
    @pytest.mark.parametrize("letter_name,bu_name", _params())
    def test_bu_filter_scoping(self, authed_page: Page, letter_name: str, bu_name: str):
        if letter_name == "__skip__":
            pytest.skip("No ingested letters — run ingestion test first")

        table_rows = authed_page.locator("table tbody tr")
        filter_name = _filter_display_name(bu_name)

        with allure.step(f"Apply BU filter: '{filter_name}'"):
            _apply_bu_filter(authed_page, filter_name)

        with allure.step(f"Search for '{letter_name}' — assert it appears under its own BU"):
            _search(authed_page, letter_name)
            assert table_rows.count() > 0, (
                f"[TC_LT_FILTER_001] FAIL — '{letter_name}' not visible under "
                f"BU filter '{filter_name}'."
            )
            row_text = _clean(table_rows.first.inner_text(timeout=2_000))
            assert letter_name.lower() in row_text.lower(), (
                f"[TC_LT_FILTER_001] FAIL — First row does not contain '{letter_name}' "
                f"after BU filter '{filter_name}'.\nRow: {row_text[:200]!r}"
            )

        with allure.step("Clear BU filter"):
            _clear_bu_filter(authed_page)

        # find any OTHER BU in ingested data to test negative scoping
        all_records  = _load_ingested()
        other_bus    = list({
            _filter_display_name(r["bu_name"])
            for r in all_records
            if r["bu_name"].strip().upper() != bu_name.strip().upper()
        })

        if not other_bus:
            allure.attach(
                "Only one BU in ingested data — negative filter check skipped.",
                name="Skip reason",
                attachment_type=allure.attachment_type.TEXT,
            )
            return

        other_filter = other_bus[0]
        with allure.step(f"Apply different BU filter: '{other_filter}'"):
            _apply_bu_filter(authed_page, other_filter)

        with allure.step(f"Search for '{letter_name}' — assert it does NOT appear under '{other_filter}'"):
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

            allure.attach(
                f"no_data_visible={no_data_visible}, zero_rows={zero_rows}",
                name="Negative filter result",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert no_data_visible or zero_rows, (
                f"[TC_LT_FILTER_001] FAIL — '{letter_name}' (BU={bu_name}) unexpectedly "
                f"visible under BU filter '{other_filter}'.\n"
                f"Row text: {_clean(table_rows.first.inner_text(timeout=1_000))[:200] if table_rows.count() > 0 else 'n/a'}"
            )

        with allure.step("Clear BU filter (cleanup)"):
            _clear_bu_filter(authed_page)
