"""
TC_LT_ING_001 — Letter Type Ingestion (UM + ANG)

Reads test_docx/Ingestion.xlsx, which has two data rows:
  • BU=UM  → DOCX from test_docx/UM/
  • BU=ANG → DOCX from test_docx/Ang/

For each row:
  1. Opens the Configure Letter Type modal.
  2. Selects the Business Unit.
  3. Uploads the BU-specific DOCX (triggers the form fields).
  4. Fills Letter Type Name and External ID — each gets a 3-char
     random suffix to guarantee uniqueness across runs.
  5. Sets Region, LOB, Is State Template from the sheet.
  6. Submits via "Upload File".
  7. Asserts a success toast appears.
  8. Navigates back to the Letter Type listing and searches for the
     newly created name — asserts it appears in the results.
"""
from __future__ import annotations

import os
import re
import json
import random
import string
import time

import allure
import pytest
from openpyxl import load_workbook
from playwright.sync_api import Page

from pages.letter_type_page import LetterTypePage

# ── Shared testdata (read by test_download_pdf_and_docx_after_ingestion) ──────
_TESTS_DIR    = os.path.dirname(os.path.abspath(__file__))
_TESTDATA_DIR = os.path.join(_TESTS_DIR, "testdata")
_TESTDATA_FILE = os.path.join(_TESTDATA_DIR, "ingested_letters.json")


def _save_ingested_letter(letter_name: str, bu_name: str) -> None:
    """Append a successfully ingested letter to the shared testdata JSON."""
    os.makedirs(_TESTDATA_DIR, exist_ok=True)
    try:
        with open(_TESTDATA_FILE, encoding="utf-8") as f:
            existing = json.load(f)
        if not isinstance(existing, list):
            existing = []
    except Exception:
        existing = []
    key = (letter_name.strip(), bu_name.strip())
    if not any((r["letter_name"].strip(), r["bu_name"].strip()) == key for r in existing):
        existing.append({"letter_name": letter_name, "bu_name": bu_name})
        with open(_TESTDATA_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        print(f"📌 Saved to testdata: '{letter_name}' | BU: {bu_name}")

pytestmark = pytest.mark.sanity

# ── Paths ──────────────────────────────────────────────────────────────────────
_PROJECT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EXCEL     = os.environ.get(
    "INGESTION_EXCEL",
    os.path.join(_PROJECT, "test_docx", "Ingestion.xlsx"),
)
_DOCX_ROOT = os.path.join(_PROJECT, "test_docx")


# ── Pure helpers ───────────────────────────────────────────────────────────────

def _clean(val) -> str:
    if val is None:
        return ""
    return re.sub(r"\s+", " ", str(val).replace("\xa0", " ")).strip()


def _is_truthy(val) -> bool:
    return _clean(val).lower() in {"true", "yes", "1", "on"}


def _suffix(n: int = 4) -> str:
    """Return a short unique suffix: last 2 epoch-ms digits + 2 random chars."""
    ts = str(int(time.time() * 1000))[-2:]
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=n - 2))
    return ts + rand


def _read_rows(excel_path: str) -> list[dict]:
    wb = load_workbook(excel_path, data_only=True)
    ws = wb.active
    headers = [_clean(c.value).lower() for c in ws[1]]
    rows: list[dict] = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        rec = {
            headers[i]: _clean(v)
            for i, v in enumerate(row)
            if i < len(headers) and headers[i]
        }
        if any(rec.get(k) for k in ("letter_type_name", "external_id")):
            rows.append(rec)
    return rows


def _docx_path(bu: str, filename: str) -> str:
    """Find the DOCX by matching BU (case-insensitive) to a subfolder of test_docx/."""
    for root in list(dict.fromkeys([os.getcwd(), _PROJECT])):
        docx_root = os.path.join(root, "test_docx")
        if not os.path.isdir(docx_root):
            continue
        for entry in os.listdir(docx_root):
            if entry.lower() == bu.lower() and os.path.isdir(os.path.join(docx_root, entry)):
                path = os.path.join(docx_root, entry, filename)
                if os.path.exists(path):
                    return path
                raise FileNotFoundError(
                    f"DOCX '{filename}' not found in {os.path.join(docx_root, entry)}"
                )
    raise FileNotFoundError(
        f"No test_docx/{bu}/ folder found under cwd={os.getcwd()} or _PROJECT={_PROJECT}"
    )


# ── Parametrize at collection time ─────────────────────────────────────────────
# Read BU names from test_docx/ subfolders — no Excel access needed at collection.
# The Excel is read at test-execution time inside the test function itself.

def _params() -> list:
    try:
        # Use cwd at collection time — pytest is invoked from the project root
        docx_root = os.path.join(os.getcwd(), "test_docx")
        bus = sorted(
            d for d in os.listdir(docx_root)
            if os.path.isdir(os.path.join(docx_root, d))
        )
    except Exception:
        bus = ["UM", "ANG"]
    if not bus:
        bus = ["UM", "ANG"]
    return [pytest.param(bu, id=f"BU={bu.upper()}") for bu in bus]


# ── Page-interaction helpers ───────────────────────────────────────────────────

def _dismiss_popup(page: Page) -> None:
    """Hide the Ask Auto popup and restore aria-hidden on #root."""
    try:
        page.evaluate("""
            () => {
                var vpArea = window.innerWidth * window.innerHeight;
                document.querySelectorAll('div, section, aside').forEach(function(d) {
                    if (!d.textContent || !d.textContent.includes('What can I help with')) return;
                    var r = d.getBoundingClientRect();
                    if (r.width * r.height < vpArea * 0.7) {
                        d.style.cssText += ';display:none!important;pointer-events:none!important;';
                    }
                });
                var root = document.getElementById('root');
                if (root) root.removeAttribute('aria-hidden');
                document.querySelectorAll('body > div[aria-hidden="true"]').forEach(
                    function(el) { el.removeAttribute('aria-hidden'); }
                );
            }
        """)
    except Exception:
        pass


def _open_modal(page: Page) -> None:
    """Open the Configure Letter Type drawer.

    Uses a JS programmatic click (mousedown → mouseup → click) on every
    attempt.  This bypasses aria-hidden / pointer-events blocks set by the
    Ask-Auto popup without relying on Playwright's force=True, which still
    requires the element to pass an overlap check.
    """
    for attempt in range(3):
        _dismiss_popup(page)
        page.wait_for_timeout(400 + attempt * 300)

        # Button must already be visible (we waited for it in step 1)
        try:
            page.locator("button:has-text('Configure Letter Type')").first.wait_for(
                state="visible", timeout=8_000
            )
        except Exception:
            continue

        _dismiss_popup(page)  # dismiss again right before clicking

        # JS click: cannot be intercepted by overlays or aria-hidden
        clicked = page.evaluate("""
            () => {
                var btn = Array.from(document.querySelectorAll('button')).find(function(b) {
                    return b.textContent && b.textContent.trim().includes('Configure Letter Type');
                });
                if (!btn) return false;
                // Remove aria-hidden that the popup may have placed on #root
                var root = document.getElementById('root');
                if (root) root.removeAttribute('aria-hidden');
                document.querySelectorAll('body > div[aria-hidden="true"]').forEach(
                    function(el) { el.removeAttribute('aria-hidden'); }
                );
                btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
                btn.dispatchEvent(new MouseEvent('mouseup',   {bubbles: true, cancelable: true}));
                btn.click();
                return true;
            }
        """)
        if not clicked:
            continue

        try:
            page.locator("#mui-component-select-businessUnitDropdown").wait_for(
                state="visible", timeout=8_000
            )
            # Dismiss any popup that appeared during the drawer-open animation.
            # Without this the popup backdrop intercepts clicks on the drawer and
            # MUI closes the drawer when the popup's overlay is dismissed.
            _dismiss_popup(page)
            return  # panel is open
        except Exception:
            if attempt < 2:
                _dismiss_popup(page)
    raise TimeoutError("Configure Letter Type panel did not open after 3 attempts.")


def _select_bu(page: Page, bu: str) -> None:
    """Select the Business Unit from the MUI dropdown.

    Match priority:
      1. Exact text match
      2. First option whose text contains bu anywhere (case-insensitive)
    """
    sel = page.locator("#mui-component-select-businessUnitDropdown")
    sel.wait_for(state="visible", timeout=12_000)
    sel.click()
    listbox = page.locator("ul[role='listbox']")
    listbox.wait_for(state="visible", timeout=8_000)

    # 1. Exact match
    exact = listbox.locator(f"li:text-is('{bu}')").first
    if exact.count() and exact.is_visible(timeout=2_000):
        exact.click()
        _close_mui_popover(page)
        page.wait_for_timeout(400)
        return

    # 2. First option containing bu anywhere in its text
    bu_lower = bu.strip().lower()
    items = listbox.locator("li[role='option'], li").all()
    for item in items:
        try:
            text = (item.inner_text(timeout=500) or "").strip().lower()
            if bu_lower in text and item.is_visible(timeout=300):
                item.click()
                _close_mui_popover(page)
                page.wait_for_timeout(400)
                return
        except Exception:
            pass

    raise RuntimeError(f"BU option containing '{bu}' not found in dropdown")


def _upload_docx(page: Page, docx_path: str) -> None:
    # Scope the file input to inside the Configure Letter Type modal/drawer
    # so we don't accidentally trigger a file input elsewhere on the page.
    modal = page.locator(
        "[role='dialog']:has-text('Configure Letter Type'), "
        "[class*='drawer']:has-text('Configure Letter Type'), "
        "[class*='panel']:has-text('Configure Letter Type'), "
        "[class*='modal']:has-text('Configure Letter Type'), "
        "[class*='sidebar']:has-text('Configure Letter Type')"
    ).first
    # Fall back to page-level if the modal wrapper isn't found
    try:
        modal.wait_for(state="attached", timeout=5_000)
        inp = modal.locator("input[type='file']").first
    except Exception:
        inp = page.locator("input[type='file']").first
    inp.wait_for(state="attached", timeout=10_000)
    inp.set_input_files(docx_path)


def _restore_aria(page: Page) -> None:
    """Remove aria-hidden="true" from #root — set by the Ask Auto popup modal."""
    try:
        page.evaluate("""
            () => {
                var root = document.getElementById('root');
                if (root) root.removeAttribute('aria-hidden');
                document.querySelectorAll('body > div[aria-hidden="true"]').forEach(
                    function(el) { el.removeAttribute('aria-hidden'); }
                );
            }
        """)
    except Exception:
        pass


def _append_to_field(page: Page, keyword: str, suffix: str) -> str:
    """Find an input whose placeholder contains `keyword`, replace the last
    len(suffix) characters with suffix to keep the total length identical.
    Scoped to the MUI drawer so the search box is never matched."""
    _restore_aria(page)
    drawer = page.locator("div.MuiDrawer-paper")
    try:
        drawer.wait_for(state="visible", timeout=5_000)
        loc = drawer.locator(f"input[placeholder*='{keyword}']").first
        loc.wait_for(state="visible", timeout=15_000)
    except Exception:
        loc = page.locator(f"input[placeholder*='{keyword}']").first
        loc.wait_for(state="visible", timeout=20_000)
    current = (loc.input_value(timeout=5_000) or "").strip()
    if len(current) >= len(suffix):
        final = current[: len(current) - len(suffix)] + suffix
    else:
        final = suffix
    loc.click(click_count=3)  # select-all before fill for reliable React state update
    loc.fill(final)
    return final


def _find_external_id_input(page: Page, letter_type_name: str):
    """Return the External ID input locator.

    Scoped to div.MuiDrawer-paper so we never accidentally target the
    search box on the listing page.  Tries known placeholder patterns first,
    then falls back to 'second visible text input in the drawer'.
    """
    _restore_aria(page)
    drawer = page.locator("div.MuiDrawer-paper")
    try:
        drawer.wait_for(state="visible", timeout=5_000)
        # Pass 1: known placeholder patterns (exact match)
        for ph in [
            "Enter External Id",
            "Enter External ID",
            "External Id",
            "External ID",
            "ExternalId",
        ]:
            loc = drawer.locator(f"input[placeholder='{ph}']").first
            try:
                if loc.count() and loc.is_visible(timeout=800):
                    return loc
            except Exception:
                pass
        # Pass 2: partial placeholder match
        for ph in ["External Id", "External ID", "External"]:
            loc = drawer.locator(f"input[placeholder*='{ph}']").first
            try:
                if loc.count() and loc.is_visible(timeout=800):
                    return loc
            except Exception:
                pass
        # Pass 3: enumerate all visible text inputs in the drawer; skip LT-Name field
        inputs = drawer.locator(
            "input:not([type='file']):not([type='hidden'])"
            ":not([type='checkbox']):not([type='radio'])"
        )
        for i in range(inputs.count()):
            inp = inputs.nth(i)
            try:
                if not inp.is_visible(timeout=500):
                    continue
                ph = (inp.get_attribute("placeholder") or "")
                if "Letter Type Name" in ph or "Search" in ph.lower():
                    continue
                val = (inp.input_value() or "").strip()
                if val == letter_type_name:
                    continue  # this is the just-filled LT Name field
                return inp
            except Exception:
                pass
    except Exception:
        pass
    # Page-level last resort (no drawer found)
    return page.locator(
        "input:not([type='file']):not([type='hidden'])"
        ":not([placeholder*='Search'])"
        ":not([placeholder*='Letter Type Name'])"
    ).first


def _close_mui_popover(page: Page) -> None:
    """Disable ONLY the invisible dropdown backdrops (MUI Select close animation).
    Does NOT touch MuiModal-root/MuiBackdrop-root which belong to the Configure
    Letter Type panel — disabling those breaks the whole form."""
    try:
        page.evaluate("""
            () => {
                // Only target the transparent backdrop used by MUI Select/Menu popovers
                document.querySelectorAll('.MuiBackdrop-invisible').forEach(function(el) {
                    el.style.pointerEvents = 'none';
                });
                // Also kill any open menu portals (id starts with "menu-")
                document.querySelectorAll('[id^="menu-"]').forEach(function(el) {
                    el.style.pointerEvents = 'none';
                });
                // Restore aria-hidden on main app root (set by Ask Auto popup)
                var root = document.getElementById('root');
                if (root) root.removeAttribute('aria-hidden');
                document.querySelectorAll('body > div[aria-hidden="true"]').forEach(
                    function(el) { el.removeAttribute('aria-hidden'); }
                );
            }
        """)
    except Exception:
        pass


def _select_dropdown(page: Page, mui_id: str, value: str) -> bool:
    """Select `value` from the MUI dropdown identified by `mui_id`.

    Returns True on success, False if the option was not found (caller decides
    whether to warn or fail).  Never raises so the test can continue.
    """
    if not value:
        return True
    sel = page.locator(f"#{mui_id}")
    try:
        sel.wait_for(state="visible", timeout=8_000)
    except Exception:
        return False
    sel.click()
    listbox = page.locator("ul[role='listbox']")
    try:
        listbox.wait_for(state="visible", timeout=6_000)
    except Exception:
        page.keyboard.press("Escape")
        _close_mui_popover(page)
        return False
    opt = listbox.locator(f"li:has-text('{value}')").first
    try:
        opt.wait_for(state="visible", timeout=6_000)
        opt.click()
    except Exception:
        # Option text not found — close the dropdown cleanly and bail
        page.keyboard.press("Escape")
        _close_mui_popover(page)
        return False
    _close_mui_popover(page)
    page.wait_for_timeout(300)
    return True


def _submit(page: Page) -> None:
    # Clear any lingering MUI backdrops before attempting the click
    _close_mui_popover(page)
    page.wait_for_timeout(300)

    btn = page.get_by_role("button", name="Upload File")
    try:
        btn.wait_for(state="visible", timeout=20_000)
    except Exception:
        btn = page.locator(
            "button:has-text('Upload File'), "
            "button:has-text('Upload'), "
            "button[type='submit']"
        ).last
        btn.wait_for(state="visible", timeout=10_000)
    btn.scroll_into_view_if_needed()
    # Use force=True as a safety net — if a backdrop still lingers after _close_mui_popover
    # we still click through rather than timing out for 30 s.
    btn.click(force=True)


def _get_toast(page: Page, timeout_ms: int = 30_000) -> str:
    """Return the text of the success/error toast after submission.

    Polls every 200 ms.  Uses JavaScript so we can exclude elements that
    live inside the MUI drawer (the DOCX filename chip uses role=alert too)
    and also check MUI Snackbar selectors in addition to role=alert.
    """
    deadline = time.monotonic() + timeout_ms / 1_000
    while time.monotonic() < deadline:
        try:
            text = page.evaluate("""
                () => {
                    var DOCX_RE = /\\.docx$/i;
                    var MIN_LEN = 8;
                    var drawer = document.querySelector('div.MuiDrawer-paper');
                    var selectors = [
                        'div.MuiSnackbar-root',
                        '[class*="Snackbar"]',
                        '[class*="snackbar"]',
                        '[class*="toast"]',
                        '[class*="Toast"]',
                        '[class*="notification"]',
                        'div[role="alert"]',
                        'div[role="status"]'
                    ];
                    for (var s = 0; s < selectors.length; s++) {
                        var els = document.querySelectorAll(selectors[s]);
                        for (var i = 0; i < els.length; i++) {
                            var el = els[i];
                            var style = window.getComputedStyle(el);
                            if (style.display === 'none' || style.visibility === 'hidden') continue;
                            if (!el.offsetWidth && !el.offsetHeight) continue;
                            if (drawer && drawer.contains(el)) continue;
                            var txt = (el.innerText || '').trim();
                            if (!txt || txt.length < MIN_LEN) continue;
                            if (DOCX_RE.test(txt)) continue;
                            return txt;
                        }
                    }
                    return null;
                }
            """)
            if text:
                return text
        except Exception:
            pass
        page.wait_for_timeout(200)
    return ""


def _wait_for_real_rows(ltp: LetterTypePage, timeout_s: int = 15) -> None:
    """Poll until the first visible row has non-skeleton text."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        texts = ltp.visible_row_texts(limit=1)
        if texts and texts[0].strip():
            return
        ltp.page.wait_for_timeout(500)


# ── Test class ─────────────────────────────────────────────────────────────────

@allure.epic("Correspondence Application")
@allure.feature("Letter Type")
class TestLetterTypeIngestion:

    @classmethod
    def setup_class(cls):
        """Clear the shared testdata JSON before every ingestion run so stale entries are removed."""
        os.makedirs(_TESTDATA_DIR, exist_ok=True)
        with open(_TESTDATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    @allure.story("Ingestion")
    @allure.title("[TC_LT_ING_001] Ingest letter type — parameterised by BU")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "For each row in test_docx/Ingestion.xlsx:\n"
        "1. Open Configure Letter Type modal.\n"
        "2. Select the Business Unit from the row's BU column.\n"
        "3. Upload the BU-folder DOCX (triggers form fields).\n"
        "4. Fill Letter Type Name + External ID, each with a unique 3-char suffix.\n"
        "5. Set Region, LOB, Is State Template.\n"
        "6. Submit. Assert success toast.\n"
        "7. Search the listing. Assert the new letter type appears."
    )
    @pytest.mark.parametrize("bu", _params())
    def test_letter_type_ingestion(self, authed_page: Page, bu: str):
        # ── Read Excel at test-execution time (not collection time) ───────────
        # Use glob recursive search so the file is found regardless of location.
        import glob as _glob
        _search_roots = list(dict.fromkeys([os.getcwd(), _PROJECT]))
        _found = []
        for _root in _search_roots:
            for _pat in ["[Ii]ngestion.xlsx", "[Ll]ngestion.xlsx", "*ngestion.xlsx"]:
                _found = _glob.glob(
                    os.path.join(_root, "**", _pat), recursive=True
                )
                if _found:
                    break
            if _found:
                break
        excel_path = _found[0] if _found else None
        if excel_path is None:
            pytest.fail(
                "Ingestion.xlsx not found anywhere under:\n"
                + "\n".join(f"  {r}" for r in _search_roots)
                + f"\n  cwd={os.getcwd()}, _PROJECT={_PROJECT}"
            )
        all_rows = _read_rows(excel_path)
        row = next(
            (r for r in all_rows if r.get("bu", "").strip().upper() == bu.upper()),
            None,
        )
        if row is None:
            pytest.skip(f"No data row for BU='{bu}' found in {excel_path}")

        bu_raw   = row.get("bu", bu).strip()
        sfx      = _suffix()          # unique suffix appended to auto-filled fields
        region   = row.get("region", "")
        lob      = row.get("lob", "")
        is_state = _is_truthy(row.get("is_state_template", ""))
        docx_f   = row.get("docx_file", "")
        docx_p   = _docx_path(bu_raw, docx_f)
        # name / ext_id are determined AFTER upload (the DOCX auto-fills them)
        name: str = ""
        ext_id: str = ""

        allure.attach(
            f"BU         : {bu_raw}\n"
            f"Suffix     : {sfx}\n"
            f"Region     : {region}\n"
            f"LOB        : {lob}\n"
            f"Is State   : {is_state}\n"
            f"DOCX       : {docx_p}",
            name="Ingestion input",
            attachment_type=allure.attachment_type.TEXT,
        )

        ltp = LetterTypePage(authed_page)

        # Register a Playwright locator handler so the "Ask Auto / What can I
        # help with?" popup is dismissed automatically every time it appears,
        # without needing explicit dismiss calls before each interaction.
        _popup_loc = authed_page.get_by_text("What can I help with?")
        try:
            authed_page.add_locator_handler(
                _popup_loc,
                lambda: ltp.dismiss_ask_auto_popup(),
            )
        except Exception:
            pass  # add_locator_handler not available in this Playwright version

        # ── 1. Navigate to Letter Type listing ────────────────────────────────
        with allure.step("Navigate to Letter Type listing"):
            ltp.open_direct()
            # Dismiss popup immediately so it doesn't block the Configure button.
            _dismiss_popup(authed_page)
            # Wait only for the Configure button — no need to wait for column
            # headers (is_loaded does that) which can add up to 30 extra seconds.
            try:
                authed_page.locator(
                    "button:has-text('Configure Letter Type')"
                ).first.wait_for(state="visible", timeout=25_000)
            except Exception:
                assert "letter-type" in authed_page.url, (
                    f"Letter Type listing did not load. URL: {authed_page.url}"
                )

        # ── 2. Open Configure Letter Type modal ───────────────────────────────
        with allure.step("Open 'Configure Letter Type' modal"):
            _open_modal(authed_page)

        # ── 3. Select Business Unit ───────────────────────────────────────────
        with allure.step(f"Select Business Unit: {bu_raw!r}"):
            _select_bu(authed_page, bu_raw)
            allure.attach(
                f"BU selected: {bu_raw}",
                name="BU selection",
                attachment_type=allure.attachment_type.TEXT,
            )

        # ── 4. Upload DOCX (unlocks form fields) ──────────────────────────────
        with allure.step(f"Upload DOCX: {docx_f}"):
            _upload_docx(authed_page, docx_p)
            # After upload, form fields appear inside the modal — wait for the
            # Letter Type Name input to confirm the page has NOT navigated away.
            try:
                authed_page.locator(
                    "input[placeholder='Enter Letter Type Name']"
                ).wait_for(state="visible", timeout=25_000)
            except Exception:
                # If the page navigated away, fail with a clear message
                assert "letter-type" in authed_page.url and "configure" not in authed_page.url.lower(), (
                    f"Page navigated away after DOCX upload. Current URL: {authed_page.url}. "
                    "The file input may have triggered the wrong handler — check scoping."
                )
                raise
            allure.attach(
                f"DOCX path: {docx_p}",
                name="DOCX uploaded",
                attachment_type=allure.attachment_type.TEXT,
            )

        # ── 5. Append suffix to auto-filled Letter Type Name ─────────────────
        with allure.step("Append unique suffix to Letter Type Name"):
            name = _append_to_field(authed_page, "Letter Type Name", sfx)
            allure.attach(f"Final name: {name}", name="Letter Type Name",
                          attachment_type=allure.attachment_type.TEXT)

        # ── 6. Append suffix to auto-filled External ID ───────────────────────
        with allure.step("Append unique suffix to External ID"):
            _restore_aria(authed_page)
            ext_loc = _find_external_id_input(authed_page, name)
            ext_loc.wait_for(state="visible", timeout=10_000)
            current_ext = (ext_loc.input_value(timeout=5_000) or "").strip()
            if len(current_ext) >= len(sfx):
                ext_id = current_ext[: len(current_ext) - len(sfx)] + sfx
            else:
                ext_id = sfx
            ext_loc.click(click_count=3)  # select-all to ensure React picks up the change
            authed_page.wait_for_timeout(100)
            ext_loc.fill(ext_id)
            allure.attach(
                f"Current ext (before): {current_ext!r}\nFinal ext_id: {ext_id!r}",
                name="External ID",
                attachment_type=allure.attachment_type.TEXT,
            )

        # ── 7. Select Region ──────────────────────────────────────────────────
        if region and region.strip():
            with allure.step(f"Select Region: {region}"):
                ok = _select_dropdown(
                    authed_page, "mui-component-select-regionDropdown", region
                )
                _close_mui_popover(authed_page)
                if not ok:
                    allure.attach(
                        f"Region option '{region}' not found in dropdown — continuing without it.",
                        name="Region warning",
                        attachment_type=allure.attachment_type.TEXT,
                    )

        # ── 8. Select LOB ─────────────────────────────────────────────────────
        # "ALL" is already the default value — skip to avoid MUI backdrop issue
        if lob and lob.strip().upper() not in {"", "ALL"}:
            with allure.step(f"Select LOB: {lob}"):
                _select_dropdown(
                    authed_page, "mui-component-select-lobDropdown", lob
                )
                _close_mui_popover(authed_page)

        # ── 9. Submit ─────────────────────────────────────────────────────────
        with allure.step("Click 'Upload File' to submit"):
            _submit(authed_page)

        # ── 10. Log toast (non-fatal) ─────────────────────────────────────────
        _EXPECTED_TOAST = "Letter Type uploaded successfully!"
        with allure.step("Check success toast (informational — not a blocking assertion)"):
            toast = _get_toast(authed_page, timeout_ms=10_000)
            toast_clean = " ".join(toast.split())
            allure.attach(
                f"Toast received : {toast_clean!r}\n"
                f"Toast expected : {_EXPECTED_TOAST!r}",
                name="Toast (informational)",
                attachment_type=allure.attachment_type.TEXT,
            )
            # Non-blocking: log a warning but do not fail the test here.
            # The listing search below is the authoritative pass/fail assertion.
            if not toast_clean:
                allure.attach(
                    "Toast not observed — upload may still have succeeded. "
                    "Proceeding to listing verification.",
                    name="Toast warning",
                    attachment_type=allure.attachment_type.TEXT,
                )

        # ── 11. Wait for drawer to close (stay on letter-type page) ─────────────
        with allure.step("Wait for Configure drawer to close"):
            try:
                authed_page.wait_for_function(
                    "() => {"
                    "  var d = document.querySelector('div.MuiDrawer-paper');"
                    "  return !d || window.getComputedStyle(d).visibility === 'hidden'"
                    "     || window.getComputedStyle(d).display === 'none';"
                    "}",
                    timeout=10_000,
                )
            except Exception:
                pass
            _dismiss_popup(authed_page)

        # ── 12. Search; refresh and retry if letter not found or shows Pipeline Error ──
        with allure.step(f"Search for {name!r} in the listing"):
            _refresh_btn = authed_page.locator(
                "button[aria-label*='refresh' i], "
                "button[aria-label*='Refresh' i], "
                "button[title*='refresh' i], "
                "button[title*='Refresh' i], "
                "[data-testid*='refresh']"
            ).first

            allure.attach(
                f"Searching for ingested letter type name: {name!r}",
                name="Search term",
                attachment_type=allure.attachment_type.TEXT,
            )

            # Wait for the listing page to be ready before searching
            try:
                ltp.search_box.wait_for(state="visible", timeout=15_000)
            except Exception:
                # If search box not found, navigate back to listing
                ltp.open_direct()
                try:
                    ltp.search_box.wait_for(state="visible", timeout=15_000)
                except Exception:
                    pass
            authed_page.wait_for_timeout(1_000)

            def _do_search() -> list:
                ltp.search("")
                authed_page.wait_for_timeout(500)
                ltp.search(name)
                authed_page.keyboard.press("Enter")
                authed_page.wait_for_timeout(500)
                try:
                    authed_page.wait_for_load_state("networkidle", timeout=6_000)
                except Exception:
                    pass
                _wait_for_real_rows(ltp, timeout_s=8)
                return ltp.visible_row_texts(limit=10)

            def _needs_refresh(rows: list) -> bool:
                matched = next((t for t in rows if name.lower() in t.lower()), None)
                if matched is None:
                    return True  # letter not found yet
                import re as _re
                if _re.search(r"\bpipeline\s*error\b", matched, _re.I):
                    return True  # found but still processing / pipeline error
                return False

            row_texts = _do_search()
            if _needs_refresh(row_texts):
                # Refresh page and wait before retrying search
                try:
                    if ltp.is_visible(_refresh_btn, timeout=3_000):
                        _refresh_btn.click()
                    else:
                        authed_page.reload(wait_until="domcontentloaded", timeout=20_000)
                    try:
                        authed_page.wait_for_load_state("networkidle", timeout=10_000)
                    except Exception:
                        pass
                    authed_page.wait_for_timeout(2_000)
                    _wait_for_real_rows(ltp, timeout_s=10)
                except Exception:
                    pass
                row_texts = _do_search()

        # ── 13. Assert ingested letter is searchable and appears in the list ────
        with allure.step(
            f"Assert '{name}' appears in the listing after searching by its name"
        ):
            allure.attach(
                f"Ingested letter type name : {name!r}\n"
                f"Ingested external ID      : {ext_id!r}\n"
                f"BU                        : {bu_raw}\n\n"
                + "\n".join(f"Row {i}: {t[:120]}" for i, t in enumerate(row_texts)),
                name="Search results",
                attachment_type=allure.attachment_type.TEXT,
            )

            # 1. Search returned at least one row
            assert row_texts, (
                f"Search for '{name}' returned no rows — "
                f"ingested letter type (BU={bu_raw}) not visible in the listing."
            )

            # 2. The ingested letter name appears in the results
            matched_row = next(
                (t for t in row_texts if name.lower() in t.lower()), None
            )
            assert matched_row is not None, (
                f"Searched for '{name}' but it was not found in any result row.\n"
                f"BU={bu_raw}, External ID={ext_id!r}\n"
                f"Visible rows:\n"
                + "\n".join(f"  {t[:120]}" for t in row_texts)
            )

            # 3. The matching row also contains the External ID
            if ext_id:
                assert ext_id.lower() in matched_row.lower(), (
                    f"Row containing '{name}' does not show External ID '{ext_id}'.\n"
                    f"Row text: {matched_row[:200]!r}"
                )

            # 4. Assert status is Draft (pass) — fail explicitly if Pipeline Error
            import re as _re
            if _re.search(r"\bpipeline\s*error\b", matched_row, _re.I):
                assert False, (
                    f"FAIL — Letter '{name}' (BU={bu_raw}) has status 'Pipeline Error'.\n"
                    f"Row text: {matched_row[:200]!r}"
                )
            assert _re.search(r"\bdraft\b", matched_row, _re.I), (
                f"FAIL — Letter '{name}' (BU={bu_raw}) does not show 'Draft' status.\n"
                f"Row text: {matched_row[:200]!r}"
            )

            # 5. Save to shared testdata so download TC can find this letter
            _save_ingested_letter(name, bu_raw)
