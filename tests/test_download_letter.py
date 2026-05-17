# Author: Ruchika Verma <testing.ruchika@gmail.com>
import os
import re
import sys
import json
import argparse
import pytest
from datetime import datetime
from openpyxl import load_workbook
from playwright.sync_api import expect

BASE_URL = "https://correspondence.sprint.autonomize.dev/"

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DOWNLOAD_ROOT = os.path.join(PROJECT_DIR, "downloaded")

# Shared testdata file — ingestion writes here; PDF/DOCX download test reads from here.
TESTDATA_DIR  = os.path.join(PROJECT_DIR, "testdata")
TESTDATA_FILE = os.path.join(TESTDATA_DIR, "ingested_letters.json")

FAIL_ON_DOWNLOAD_ERRORS = os.environ.get("FAIL_ON_DOWNLOAD_ERRORS", "0") == "1"

DOWNLOADED_FILE = os.path.join(TESTDATA_DIR, "downloaded_letters.json")


def _save_downloaded_letter(letter_name: str, bu_name: str, pdf_path: str, docx_path: str):
    """Append a successfully downloaded letter record to downloaded_letters.json."""
    os.makedirs(TESTDATA_DIR, exist_ok=True)
    try:
        with open(DOWNLOADED_FILE, encoding="utf-8") as f:
            existing = json.load(f)
        if not isinstance(existing, list):
            existing = []
    except Exception:
        existing = []
    key = (letter_name.strip(), bu_name.strip())
    for rec in existing:
        if (rec["letter_name"].strip(), rec["bu_name"].strip()) == key:
            rec["pdf_path"] = pdf_path
            rec["docx_path"] = docx_path
            break
    else:
        existing.append({
            "letter_name": letter_name,
            "bu_name": bu_name,
            "pdf_path": pdf_path,
            "docx_path": docx_path,
        })
    with open(DOWNLOADED_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
    print(f"📌 Saved to downloaded_letters.json: '{letter_name}' | BU: {bu_name}")


@pytest.fixture(scope="module", autouse=True)
def _clean_download_dir_before_run():
    """Wipe pdf_docx_downloads folder and downloaded_letters.json before the module runs."""
    import shutil
    folder = os.path.join(DEFAULT_DOWNLOAD_ROOT, "pdf_docx_downloads")
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder, exist_ok=True)
    os.makedirs(TESTDATA_DIR, exist_ok=True)
    with open(DOWNLOADED_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    yield


# ── testdata helpers ──────────────────────────────────────────────────────────

def _save_ingested_letter(letter_name: str, bu_name: str):
    """
    Append a successfully ingested letter to the shared testdata file.
    Format: [{"letter_name": "...", "bu_name": "..."}, ...]
    Duplicate entries (same letter + BU) are skipped.
    """
    os.makedirs(TESTDATA_DIR, exist_ok=True)
    existing = _load_ingested_letters()
    key = (letter_name.strip(), bu_name.strip())
    if any((r["letter_name"].strip(), r["bu_name"].strip()) == key for r in existing):
        return  # already recorded
    existing.append({"letter_name": letter_name, "bu_name": bu_name})
    with open(TESTDATA_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def _load_ingested_letters() -> list:
    """Return the list of ingested letter records, or [] if file missing/empty."""
    if not os.path.exists(TESTDATA_FILE):
        return []
    try:
        with open(TESTDATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


# ----------------- INGESTION FAIL EXCEPTION + DETECTORS -----------------
class IngestionFailError(RuntimeError):
    """Raised when the PDF cannot be generated/loaded (treat as ingestion fail)."""
    pass


class NotFoundError(RuntimeError):
    """Raised when search returns no matching rows (No Data Found)."""
    pass


def _safe_inner_text(loc, timeout=200):
    try:
        if loc.count() > 0 and loc.first.is_visible(timeout=timeout):
            return (loc.first.inner_text(timeout=timeout) or "").strip()
    except Exception:
        pass
    return ""


def detect_preview_error(page) -> str | None:
    exact = page.locator("text=/Failed to load PDF\\s*:\\s*Unknown error/i")
    msg = _safe_inner_text(exact, timeout=350)
    if msg:
        return msg

    fallbacks = [
        page.locator("text=/Failed to load PDF/i"),
        page.locator("text=/Unable to load/i"),
        page.locator("text=/PDF.*(failed|error)/i"),
        page.locator("[role='alert']"),
        page.locator(".MuiAlert-root"),
        page.locator(".MuiSnackbar-root"),
    ]
    for loc in fallbacks:
        msg = _safe_inner_text(loc, timeout=150)
        if msg:
            return msg
    return None


def detect_no_data_found(page) -> bool:
    try:
        loc = page.locator(r"text=/No Data Found\.?/i").first
        return loc.count() > 0 and loc.is_visible(timeout=300)
    except Exception:
        return False


def fail_if_preview_error(page):
    err = detect_preview_error(page)
    if err:
        raise IngestionFailError(f"INGESTION FAIL | {err}")


def detect_pipeline_error_in_row(row) -> str | None:
    try:
        pill = row.locator("text=/\\bPipeline Error\\b/i").first
        if pill.count() > 0 and pill.is_visible(timeout=250):
            txt = (pill.inner_text(timeout=200) or "").strip()
            return txt or "Pipeline Error"
    except Exception:
        pass

    try:
        t = (row.inner_text(timeout=400) or "").strip()
        if re.search(r"\bPipeline Error\b", t, re.I):
            return "Pipeline Error"
    except Exception:
        pass

    return None
# ------------------------------------------------------------------------


def clean_text(s: str) -> str:
    s = str(s).replace('\xa0', ' ')
    s = re.sub(r"[ -‍  ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def make_safe_name(name: str) -> str:
    name = clean_text(name)
    bad = '<>:"/\\|?*'
    for ch in bad:
        name = name.replace(ch, "_")
    name = "_".join(name.strip().split())
    return name[:180]


def clear_download_dir(folder: str, only_ext: str = ".pdf"):
    os.makedirs(folder, exist_ok=True)
    exts = {".pdf", ".png"}
    for root, _dirs, files in os.walk(folder):
        for fname in files:
            fp = os.path.join(root, fname)
            if fp.lower().endswith(tuple(exts)):
                try:
                    os.remove(fp)
                    print(f"🗑️ Cleared: {fp}")
                except Exception as e:
                    print(f"⚠️ Could not delete {fp}: {e}")


def clear_download_root(download_root: str):
    if not os.path.isdir(download_root):
        return
    for root, _dirs, files in os.walk(download_root):
        for f in files:
            if f.lower().endswith((".pdf", ".png", ".json")):
                try:
                    os.remove(os.path.join(root, f))
                except Exception:
                    pass


def read_file_names_from_excel(path, column_header="actual"):
    wb = load_workbook(path, data_only=True)
    sheet = wb.active

    headers = [str(c.value).strip().lower() if c.value else "" for c in sheet[1]]
    header_key = column_header.strip().lower()
    if header_key not in headers:
        raise ValueError(f"Column '{column_header}' not found. Found headers: {headers}")

    col_index = headers.index(header_key)
    values = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if col_index < len(row) and row[col_index]:
            values.append(clean_text(row[col_index]))
    return values


def _excel_to_folder_name(excel_path: str) -> str:
    base = os.path.basename(excel_path)
    stem, _ = os.path.splitext(base)
    return make_safe_name(stem)


def _apply_ang_donot_use_filter(page):
    _apply_bu_filter(page, "ANG DONOT USE")


def _apply_bu_filter(page, bu_name: str):
    """
    Open the Filters panel, select the given Business Unit name, and click Apply.
    Handles both ANG and real BU names (e.g. 'UNV3', 'ALL', 'ANG DONOT USE').
    """
    print(f"🔧 Applying filter: Business Unit = {bu_name}")

    page.wait_for_selector("xpath=//button[@aria-label='Filters']", state="visible", timeout=20000)

    try:
        page.wait_for_selector(".MuiSkeleton-root", state="hidden", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(500)

    filter_btn = page.locator("xpath=//button[@aria-label='Filters']").first
    filter_btn.scroll_into_view_if_needed()
    filter_btn.click(timeout=10000, force=True)
    print("   ↳ Filters button clicked")

    page.wait_for_selector("text=Filters", state="visible", timeout=10000)
    page.wait_for_timeout(600)
    print("   ↳ Filters dialog open")

    page.get_by_text("Business Unit", exact=True).first.scroll_into_view_if_needed()
    page.wait_for_timeout(300)

    bu_trigger = page.locator("[aria-haspopup='listbox']").filter(
        has_text=re.compile(r"All Business", re.I)
    ).first
    bu_trigger.scroll_into_view_if_needed()
    bu_trigger.click(timeout=5000)
    page.wait_for_timeout(500)
    print("   ↳ BU dropdown opened")

    page.wait_for_selector("[role='listbox']", state="visible", timeout=5000)
    page.locator("[role='listbox']").locator("li, [role='option']").filter(
        has_text=re.compile(rf"^{re.escape(bu_name)}$", re.I)
    ).first.click(timeout=5000)
    page.wait_for_timeout(400)
    print(f"   ↳ {bu_name} selected")

    page.locator("xpath=//button[normalize-space()='Apply']").first.click(timeout=5000)
    page.wait_for_timeout(1000)
    print(f"✅ Filter applied: Business Unit = {bu_name}")


def _login_and_open_letter_type(page, bu_name: str = None):
    search_box = page.locator("input[placeholder='Search by Letter Type and Id']")

    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=600000)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(1500)

    if search_box.is_visible(timeout=3000):
        print("✅ Already on Letter Type listing page.")
        if bu_name is not None:
            _apply_bu_filter(page, bu_name)
        return

    try:
        if page.locator("#username").is_visible(timeout=4000):
            username = os.environ.get("APP_USERNAME", "sapna.bhatt@autonomize.ai")
            password = os.environ.get("APP_PASSWORD", "Sapna@2025")
            page.fill("#username", username)
            page.fill("#password", password)
            with page.expect_navigation(wait_until="networkidle", timeout=60000):
                page.click("//input[@type='submit']")
            print("✅ Login successful.")
            try:
                page.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass
            page.wait_for_timeout(2000)
    except Exception:
        pass

    print(f"📍 Navigating directly to /letter-type…")
    letter_type_url = BASE_URL.rstrip("/") + "/letter-type"
    page.goto(letter_type_url, wait_until="domcontentloaded", timeout=30000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1000)

    try:
        page.wait_for_selector("xpath=//button[@aria-label='Filters']", state="visible", timeout=15000)
    except Exception:
        raise RuntimeError(
            f"Could not reach Letter Type listing page. "
            f"Current URL: {page.url}"
        )

    print("✅ On Letter Type listing page.")
    if bu_name is not None:
        _apply_bu_filter(page, bu_name)


def _get_download_buttons(page):
    """
    Find the (main-download, dropdown-arrow) button pair.
    Tries multiple strategies so changes to SVG icons don't break it.
    """
    try:
        groups = page.locator("[class*='MuiButtonGroup']")
        for i in range(groups.count()):
            g = groups.nth(i)
            btns = g.locator("button")
            if btns.count() >= 2:
                return btns.nth(0), btns.nth(1)
    except Exception:
        pass

    main = page.locator("button:has(svg[viewBox='0 0 15 14'])").first
    if main.count() > 0:
        try:
            group = main.locator("xpath=ancestor::*[contains(@class,'MuiButtonGroup-root')][1]")
            btns = group.locator("button")
            if btns.count() >= 2:
                return btns.nth(0), btns.nth(1)
        except Exception:
            pass
        try:
            sib = main.locator("xpath=following-sibling::button").first
            if sib.count() > 0:
                return main, sib
        except Exception:
            pass
        return main, main

    for attr in ["aria-label", "title"]:
        try:
            btn = page.locator(f"button[{attr}*='download' i], button[{attr}*='Download']").first
            if btn.count() > 0 and btn.is_visible(timeout=500):
                sib = btn.locator("xpath=following-sibling::button").first
                if sib.count() > 0:
                    return btn, sib
                return btn, btn
        except Exception:
            pass

    try:
        arrow_btns = page.locator(
            "button:has(svg[data-testid*='Arrow']), "
            "button:has(svg[data-testid*='Expand']), "
            "button:has(svg[data-testid*='Caret'])"
        )
        for i in range(arrow_btns.count()):
            arrow = arrow_btns.nth(i)
            if not arrow.is_visible(timeout=300):
                continue
            prev = arrow.locator("xpath=preceding-sibling::button").last
            if prev.count() > 0:
                return prev, arrow
    except Exception:
        pass

    fallback = page.locator("button:has(svg[viewBox='0 0 15 14'])").first
    return fallback, fallback


def _find_back_arrow(page):
    candidates = [
        page.locator("svg").filter(has=page.locator("path[d^='M15.41 16.59']")),
        page.locator("svg").filter(has=page.locator("path[d^='M20 11H7.83']")),
        page.locator("svg").filter(has=page.locator("path[d^='M15.41 7.41']")),
        page.locator("svg").filter(has=page.locator("path[d^='M11.67 3.87']")),
        page.locator("button[aria-label*='back' i]"),
        page.locator("button[aria-label*='Back' i]"),
        page.locator("[data-testid='ArrowBackIcon']"),
        page.locator("[data-testid='ArrowBackIosIcon']"),
        page.locator("[data-testid='ChevronLeftIcon']"),
        page.locator("[data-testid='KeyboardBackspaceIcon']"),
    ]
    for loc in candidates:
        try:
            if loc.count() > 0 and loc.first.is_visible(timeout=300):
                return loc.first
        except Exception:
            pass
    return None


def _wait_for_detail_page(page, timeout_ms=20000):
    start = page.evaluate("() => Date.now()")
    print("   ⏳ Waiting for detail page…")

    while True:
        now = page.evaluate("() => Date.now()")
        if now - start > timeout_ms:
            current_url = page.url
            page_title = page.title()
            raise RuntimeError(
                f"Timed out waiting for detail page. URL={current_url} | title={page_title}"
            )

        try:
            current_url = page.url or ""
            if "/letter-type/" in current_url:
                print(f"   ✅ Detail confirmed via URL: {current_url}")
                return
        except Exception:
            pass

        if _find_back_arrow(page) is not None:
            print("   ✅ Detail confirmed via back-arrow")
            return

        try:
            search_gone = page.locator("input[placeholder*='Search by Letter']").count() == 0
            config_gone = page.locator("button:has-text('Configure Letter Type')").count() == 0
            if search_gone and config_gone:
                print("   ✅ Detail confirmed via listing elements gone")
                return
        except Exception:
            pass

        page.wait_for_timeout(300)


def wait_for_preview_ready(page, download_btn_for_enabled_check, timeout_ms=240000, fast_fail_ms=5000):
    page_counter = page.locator("text=/\\b\\d{1,2}\\s*\\/\\s*\\d{1,2}\\b/").first

    render_targets = [
        page.locator("iframe").first,
        page.locator("canvas").first,
        page.locator("svg").first,
        page.locator("[role='document']").first,
    ]
    skeleton = page.locator(".MuiSkeleton-root").first

    start = page.evaluate("() => Date.now()")
    blank_seen_since = None

    while True:
        now = page.evaluate("() => Date.now()")
        if now - start >= fast_fail_ms:
            break
        fail_if_preview_error(page)
        page.wait_for_timeout(250)

    while True:
        fail_if_preview_error(page)

        now = page.evaluate("() => Date.now()")
        if now - start > timeout_ms:
            raise RuntimeError(f"Preview still not ready after {timeout_ms/1000:.0f}s.")

        counter_ok = False
        try:
            counter_ok = page_counter.is_visible(timeout=250)
        except Exception:
            pass

        enabled_ok = False
        try:
            enabled_ok = download_btn_for_enabled_check.is_enabled()
        except Exception:
            pass

        render_ok = False
        for t in render_targets:
            try:
                if t.is_visible(timeout=150):
                    render_ok = True
                    break
            except Exception:
                pass

        skeleton_gone = False
        try:
            skeleton_gone = skeleton.count() == 0 or (not skeleton.is_visible(timeout=400))
        except Exception:
            skeleton_gone = True

        if skeleton_gone and (not render_ok) and (not counter_ok):
            if blank_seen_since is None:
                blank_seen_since = now
            elif now - blank_seen_since > 15000:
                raise IngestionFailError("INGESTION FAIL | Preview blank / PDF not rendered")
        else:
            blank_seen_since = None

        if counter_ok and enabled_ok and (render_ok or skeleton_gone):
            page.wait_for_timeout(250)
            return

        page.wait_for_timeout(400)


def download_for_one_excel(page, excel_path: str, download_root: str, column_header: str = "actual", bu_name: str = "ANG DONOT USE"):
    if not os.path.isabs(excel_path):
        excel_path = os.path.join(PROJECT_DIR, excel_path)

    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel not found: {excel_path}")

    run_folder_name = _excel_to_folder_name(excel_path)
    download_dir = os.path.join(download_root, run_folder_name)
    os.makedirs(download_dir, exist_ok=True)

    print(f"\n===============================")
    print(f"📘 Excel: {excel_path}")
    print(f"📁 Download folder: {download_dir}")
    print(f"===============================\n")

    clear_download_dir(download_dir, only_ext=".pdf")

    file_names = read_file_names_from_excel(excel_path, column_header)
    print(f"📄 Total files to download: {len(file_names)}")

    search_box = page.locator("input[placeholder='Search by Letter Type and Id']")
    table_rows = page.locator("table tbody tr")
    configure_btn = page.get_by_role("button", name="Configure Letter Type")

    not_found = []
    downloaded = []
    ingestion_failed_set = set()
    ingestion_failed_reasons = {}
    failed_set = set()
    failed_reasons = {}

    def normalize_tokens(q: str):
        q = clean_text(q).lower()
        return [t for t in q.split(" ") if t]

    def first_row_text(timeout=2000) -> str:
        if table_rows.count() == 0:
            return ""
        try:
            return clean_text(table_rows.first.inner_text(timeout=timeout))
        except Exception:
            return ""

    def first_row_id_text(timeout=2000) -> str:
        if table_rows.count() == 0:
            return ""
        try:
            row_txt = clean_text(table_rows.first.inner_text(timeout=timeout))
            match = re.search(r"LT-\d+", row_txt)
            if match:
                return match.group(0)
        except Exception:
            pass
        return ""

    def wait_for_filtered_results(q: str, timeout_ms: int = 60000):
        tokens = normalize_tokens(q)
        start = page.evaluate("() => Date.now()")
        confirmed_since = None

        while True:
            now = page.evaluate("() => Date.now()")
            if now - start > timeout_ms:
                rid = first_row_id_text()
                rtxt = first_row_text()
                raise RuntimeError(
                    f"Timed out waiting for filtered results for '{q}'. "
                    f"FirstRowId='{rid}' FirstRowText='{rtxt[:180]}'"
                )

            if detect_no_data_found(page):
                raise NotFoundError(f"NOT FOUND | {q}")
            if table_rows.count() == 0:
                confirmed_since = None
                page.wait_for_timeout(250)
                continue

            rtxt = first_row_text(timeout=2000).lower()
            if not rtxt:
                confirmed_since = None
                page.wait_for_timeout(250)
                continue

            if not re.search(r"lt-\d+", rtxt):
                confirmed_since = None
                page.wait_for_timeout(250)
                continue

            if not all(t in rtxt for t in tokens):
                confirmed_since = None
                page.wait_for_timeout(250)
                continue

            if confirmed_since is None:
                confirmed_since = now
                page.wait_for_timeout(400)
                continue

            rtxt2 = first_row_text(timeout=2000).lower()
            if (rtxt2
                    and re.search(r"lt-\d+", rtxt2)
                    and all(t in rtxt2 for t in tokens)):
                return
            confirmed_since = None
            page.wait_for_timeout(250)

    def _get_search_box():
        selectors = [
            "input[placeholder='Search by Letter Type, Id and External Id']",
            "input[placeholder='Search by Letter Type and Id']",
            "input[placeholder*='Search by Letter Type']",
            "input[placeholder*='Search by Letter']",
            "input[placeholder*='Search']",
        ]
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=1500):
                    return loc.first
            except Exception:
                pass
        try:
            loc = page.get_by_placeholder(re.compile(r"Search", re.I)).first
            if loc.is_visible(timeout=1500):
                return loc
        except Exception:
            pass
        raise RuntimeError("Search box not found on Letter Type page")

    def _is_on_login_page() -> bool:
        try:
            url = page.url or ""
            if "login" in url.lower() or url.rstrip("/") == BASE_URL.rstrip("/"):
                if page.locator("#username").is_visible(timeout=1500):
                    return True
        except Exception:
            pass
        try:
            if page.locator("#username").is_visible(timeout=1500):
                return True
        except Exception:
            pass
        return False

    def _ensure_logged_in():
        if not _is_on_login_page():
            return
        print("🔐 Session expired — re-logging in…")
        try:
            _login_and_open_letter_type(page)
            print("✅ Re-login succeeded.")
        except Exception as login_err:
            raise RuntimeError(f"Auto re-login failed: {login_err}") from login_err

    def search_letter(q: str):
        _ensure_logged_in()

        current_url = page.url or ""
        if "/letter-type" not in current_url:
            print(f"⚠️ search_letter: wrong page ({current_url}), navigating to /letter-type…")
            letter_type_url = BASE_URL.rstrip("/") + "/letter-type"
            page.goto(letter_type_url, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(1000)

        sb = _get_search_box()
        expect(sb).to_be_visible(timeout=15000)

        sb.click()
        page.wait_for_timeout(150)
        sb.press("Control+A")
        sb.press("Backspace")
        sb.type(q, delay=25)
        sb.press("Enter")

        page.wait_for_timeout(700)

        _loading_sel = (
            ".MuiCircularProgress-root, "
            ".MuiLinearProgress-root, "
            "[class*='loading' i], "
            "[class*='spinner' i]"
        )
        try:
            page.wait_for_selector(_loading_sel, state="visible", timeout=1500)
            page.wait_for_selector(_loading_sel, state="hidden",  timeout=20000)
        except Exception:
            pass

        wait_for_filtered_results(q, timeout_ms=30000)

    def _click_row_to_open_detail(row):
        try:
            row.scroll_into_view_if_needed()
            page.wait_for_timeout(200)
        except Exception:
            pass

        try:
            page.evaluate("""() => {
                document.querySelectorAll('[role="tooltip"]').forEach(el => {
                    el.style.visibility = 'hidden';
                    el.style.pointerEvents = 'none';
                    el.style.display = 'none';
                });
            }""")
        except Exception:
            pass

        try:
            row.click(timeout=5000)
            print("   ↳ Strategy 1: row click succeeded")
            return
        except Exception as e:
            print(f"   ↳ Strategy 1 failed: {e}")

        try:
            row.click(force=True, timeout=5000)
            print("   ↳ Strategy 2: force row click succeeded")
            return
        except Exception as e:
            print(f"   ↳ Strategy 2 failed: {e}")

        try:
            row.evaluate("el => el.click()")
            print("   ↳ Strategy 3: JS row click succeeded")
            return
        except Exception as e:
            print(f"   ↳ Strategy 3 failed: {e}")

        raise RuntimeError("All row click strategies exhausted.")

    def open_details_from_first_row(expected_query: str):
        wait_for_filtered_results(expected_query, timeout_ms=20000)
        row = table_rows.first

        pe = detect_pipeline_error_in_row(row)
        if pe:
            raise IngestionFailError(f"INGESTION FAIL | {pe}")

        id_txt = ""
        id_cell = None
        for nth in [1, 0]:
            try:
                cell = row.locator("td").nth(nth)
                if cell.count() > 0 and cell.is_visible(timeout=1500):
                    txt = clean_text(cell.inner_text(timeout=1500))
                    if re.match(r"^LT-\d+", txt):
                        id_txt = txt
                        id_cell = cell
                        break
            except Exception:
                pass

        if not id_txt:
            row_txt = first_row_text(timeout=2000)
            match = re.search(r"LT-\d+", row_txt)
            if match:
                id_txt = match.group(0)

        if not id_txt:
            raise RuntimeError(f"Could not find LT-xxx in first row. Row text: '{first_row_text()[:120]}'")

        print(f"   🖱️  Clicking row: {id_txt}")
        row.scroll_into_view_if_needed()
        page.wait_for_timeout(300)

        if id_cell is not None:
            try:
                id_cell.click(timeout=5000)
                print("   ↳ Clicked LT-ID cell directly")
            except Exception:
                try:
                    id_cell.click(force=True, timeout=5000)
                    print("   ↳ Clicked LT-ID cell (force)")
                except Exception:
                    _click_row_to_open_detail(row)
        else:
            _click_row_to_open_detail(row)

        _wait_for_detail_page(page, timeout_ms=20000)
        print(f"   ✅ On detail page. URL: {page.url}")

    def go_back_to_listing():
        print("   ↩️  Going back to listing…")
        arrow = _find_back_arrow(page)
        if arrow is not None:
            try:
                arrow.click(timeout=8000)
            except Exception:
                arrow.click(timeout=8000, force=True)
        else:
            print("   ⚠️  No back arrow found — using browser back()")
            page.go_back(wait_until="domcontentloaded", timeout=15000)

        try:
            _get_search_box().wait_for(state="visible", timeout=15000)
        except Exception:
            pass
        expect(configure_btn).to_be_visible(timeout=15000)
        page.wait_for_timeout(500)

    pdf_menu_item = page.locator(
        "ul[role='menu'] li[role='menuitem']",
        has_text=re.compile(r"^\s*PDF\s*$", re.I),
    ).first

    def open_download_menu():
        fail_if_preview_error(page)
        main_btn, menu_btn = _get_download_buttons(page)
        menu_btn.wait_for(state="visible", timeout=30000)
        menu_btn.scroll_into_view_if_needed()
        try:
            menu_btn.click(timeout=5000)
        except Exception:
            menu_btn.click(timeout=5000, force=True)
        pdf_menu_item.wait_for(state="visible", timeout=20000)
        page.wait_for_timeout(150)

    def click_pdf_menu_item():
        pdf_menu_item.wait_for(state="visible", timeout=20000)
        pdf_menu_item.scroll_into_view_if_needed()
        page.wait_for_timeout(100)
        for _attempt in range(1, 4):
            try:
                pdf_menu_item.click(timeout=5000)
                return
            except Exception:
                pass
            try:
                pdf_menu_item.click(timeout=5000, force=True)
                return
            except Exception:
                pass
            try:
                pdf_menu_item.dispatch_event("click")
                return
            except Exception:
                pass
            page.wait_for_timeout(150)
        raise RuntimeError("Could not click PDF menu item")

    for file_name in file_names:
        try:
            print(f"\n🔍 Searching: {file_name}")
            search_letter(file_name)

            if detect_no_data_found(page) or table_rows.count() == 0:
                print(f"⚠️ Not found in table: {file_name}")
                not_found.append(file_name)
                continue

            open_details_from_first_row(file_name)
            # Save to shared testdata as soon as detail page confirmed open
            _save_ingested_letter(file_name, bu_name)
            fail_if_preview_error(page)

            main_btn, _menu_btn = _get_download_buttons(page)
            wait_for_preview_ready(page, main_btn, timeout_ms=240000, fast_fail_ms=5000)
            fail_if_preview_error(page)

            open_download_menu()

            with page.expect_download(timeout=240000) as download_info:
                click_pdf_menu_item()

            download = download_info.value
            file_path = os.path.join(download_dir, f"{make_safe_name(file_name)}.pdf")
            download.save_as(file_path)

            downloaded.append({"name": file_name, "path": file_path})
            print(f"✅ PDF saved at: {file_path}")
            print(f"📌 Testdata saved: {file_name} | BU: {bu_name}")

            go_back_to_listing()

        except NotFoundError as e:
            msg = str(e).strip() or "Not found"
            not_found.append(file_name)
            print(f"⚠️ {msg} for '{file_name}'")
            try:
                expect(search_box).to_be_visible(timeout=5000)
                search_box.click()
                search_box.press("Control+A")
                search_box.press("Backspace")
                page.keyboard.press("Enter")
                page.wait_for_timeout(2000)
            except Exception:
                pass
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
            try:
                if _find_back_arrow(page):
                    go_back_to_listing()
            except Exception:
                pass

        except Exception as e:
            msg = str(e).strip() or "Unknown error"
            is_ingestion = isinstance(e, IngestionFailError) or msg.startswith("INGESTION FAIL")

            if is_ingestion:
                ingestion_failed_set.add(file_name)
                ingestion_failed_reasons[file_name] = msg
                print(f"🟥 {msg} for '{file_name}'")
            else:
                failed_set.add(file_name)
                failed_reasons[file_name] = msg
                print(f"❌ Failed for '{file_name}': {msg}")

            try:
                shot = os.path.join(download_dir, f"ERROR_{make_safe_name(file_name)}.png")
                if not _is_on_login_page():
                    page.screenshot(path=shot, full_page=True)
                    print(f"📸 Screenshot saved: {shot}")
                else:
                    print(f"⚠️  Skipped screenshot — session expired")
            except Exception:
                pass
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
            try:
                _ensure_logged_in()
            except Exception:
                pass
            try:
                if _find_back_arrow(page):
                    go_back_to_listing()
            except Exception:
                pass

    def _is_network_or_timeout_error(msg: str) -> bool:
        msg_lower = (msg or "").lower()
        network_keywords = [
            "timeout", "timed out", "net::err", "network",
            "connection", "socket", "econnreset", "econnrefused",
            "err_internet_disconnected", "err_name_not_resolved",
            "err_connection_timed_out", "err_connection_closed",
            "err_empty_response", "navigation", "page.goto",
            "waitfornavigation", "waitfor", "target closed",
        ]
        return any(k in msg_lower for k in network_keywords)

    def _recover_to_listing():
        try:
            if search_box.is_visible(timeout=3000):
                return
        except Exception:
            pass

        try:
            arrow = _find_back_arrow(page)
            if arrow is not None:
                print("   ↩️  Recover: clicking back arrow to return to listing…")
                try:
                    arrow.click(timeout=6000)
                except Exception:
                    arrow.click(timeout=6000, force=True)
                page.wait_for_timeout(1500)
                if search_box.is_visible(timeout=5000):
                    return
        except Exception:
            pass

        try:
            page.go_back(wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1500)
            if search_box.is_visible(timeout=5000):
                return
        except Exception:
            pass

        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            if search_box.is_visible(timeout=3000):
                return
        except Exception:
            pass

        print("⚠️  Recover: full re-login + navigation…")
        try:
            _login_and_open_letter_type(page)
            print("✅  Recover: re-login succeeded.")
        except Exception as login_err:
            print(f"❌  Recover: re-login failed: {login_err}")

    network_ingestion_candidates = {
        name
        for name, reason in ingestion_failed_reasons.items()
        if _is_network_or_timeout_error(reason)
    }

    for name in network_ingestion_candidates:
        ingestion_failed_set.discard(name)
        ingestion_failed_reasons.pop(name, None)
        failed_set.add(name)
        failed_reasons[name] = failed_reasons.get(name, "") or "network/timeout during ingestion check"

    if failed_set:
        retry_candidates = sorted(list(failed_set))
        print(f"\n{'='*40}")
        print(f"🔄 RETRY PASS: {len(retry_candidates)} file(s) will be retried once.")
        print(f"{'='*40}")

        print("⏳  Waiting 5s before retry…")
        page.wait_for_timeout(5000)

        print("🔄 Recovering page state before retry pass…")
        _recover_to_listing()

        for file_name in retry_candidates:
            try:
                print(f"\n🔁 Retrying: {file_name}")
                page.wait_for_timeout(2000)

                try:
                    search_box.wait_for(state="visible", timeout=8000)
                except Exception:
                    print(f"   ↻ Page not on listing — recovering for '{file_name}'…")
                    _recover_to_listing()

                search_letter(file_name)

                if detect_no_data_found(page) or table_rows.count() == 0:
                    print(f"⚠️ Still not found on retry: {file_name}")
                    continue

                open_details_from_first_row(file_name)
                _save_ingested_letter(file_name, bu_name)
                fail_if_preview_error(page)

                main_btn, _menu_btn = _get_download_buttons(page)
                wait_for_preview_ready(page, main_btn, timeout_ms=240000, fast_fail_ms=5000)
                fail_if_preview_error(page)

                open_download_menu()

                with page.expect_download(timeout=240000) as download_info:
                    click_pdf_menu_item()

                download = download_info.value
                file_path = os.path.join(download_dir, f"{make_safe_name(file_name)}.pdf")
                download.save_as(file_path)

                failed_set.discard(file_name)
                failed_reasons.pop(file_name, None)
                downloaded.append({"name": file_name, "path": file_path})
                print(f"✅ Retry succeeded: {file_path}")
                print(f"📌 Testdata saved (retry): {file_name} | BU: {bu_name}")

                go_back_to_listing()

            except NotFoundError as e:
                msg = str(e).strip() or "Not found"
                print(f"⚠️ Retry — {msg} for '{file_name}'")
                failed_set.discard(file_name)
                failed_reasons.pop(file_name, None)
                not_found.append(file_name)
                try:
                    page.keyboard.press("Escape")
                except Exception:
                    pass
                try:
                    _recover_to_listing()
                except Exception:
                    pass

            except Exception as e:
                msg = str(e).strip() or "Unknown error"
                is_ingestion = isinstance(e, IngestionFailError) or msg.startswith("INGESTION FAIL")
                is_network = _is_network_or_timeout_error(msg)

                if is_ingestion and not is_network:
                    failed_set.discard(file_name)
                    failed_reasons.pop(file_name, None)
                    ingestion_failed_set.add(file_name)
                    ingestion_failed_reasons[file_name] = msg
                    print(f"🟥 Retry — {msg} for '{file_name}'")
                elif is_network:
                    failed_reasons[file_name] = f"[RETRY][NETWORK/TIMEOUT] {msg}"
                    print(f"🌐 Retry network/timeout for '{file_name}': {msg}")
                else:
                    failed_reasons[file_name] = f"[RETRY] {msg}"
                    print(f"❌ Retry failed for '{file_name}': {msg}")

                try:
                    shot = os.path.join(download_dir, f"RETRY_ERROR_{make_safe_name(file_name)}.png")
                    if not _is_on_login_page():
                        page.screenshot(path=shot, full_page=True)
                        print(f"📸 Retry screenshot: {shot}")
                    else:
                        print(f"⚠️  Skipped retry screenshot — session expired")
                except Exception:
                    pass
                try:
                    page.keyboard.press("Escape")
                except Exception:
                    pass
                try:
                    _recover_to_listing()
                except Exception:
                    pass

    ingestion_failed = sorted(list(ingestion_failed_set))
    failed = sorted(list(failed_set))

    pipeline_error_list = []
    fail_to_load_list = []
    not_found_ingestion_list = []
    other_ingestion_list = []
    for name in ingestion_failed:
        reason = (ingestion_failed_reasons.get(name) or "").lower()
        if "pipeline error" in reason:
            pipeline_error_list.append(name)
        elif "failed to load pdf" in reason or "fail to load" in reason:
            fail_to_load_list.append(name)
        elif "not found" in reason or "no data found" in reason:
            not_found_ingestion_list.append(name)
        else:
            other_ingestion_list.append(name)

    summary = {
        "run_ts": datetime.now().isoformat(timespec="seconds"),
        "excel": excel_path,
        "download_dir": download_dir,
        "total": len(file_names),
        "downloaded_count": len(downloaded),
        "failed_count": len(failed),
        "not_found_count": len(not_found),
        "ingestion_failed_count": len(ingestion_failed),
        "ingestion_failed": ingestion_failed,
        "ingestion_failed_reasons": ingestion_failed_reasons,
        "ingestion_breakdown": {
            "pipeline_error_count": len(pipeline_error_list),
            "pipeline_error": pipeline_error_list,
            "fail_to_load_count": len(fail_to_load_list),
            "fail_to_load": fail_to_load_list,
            "not_found_count": len(not_found_ingestion_list),
            "not_found": not_found_ingestion_list,
            "other_count": len(other_ingestion_list),
            "other": other_ingestion_list,
        },
        "failed_reasons": failed_reasons,
        "downloaded": downloaded,
        "failed": failed,
        "not_found": not_found,
    }

    summary_path = os.path.join(download_dir, "download_summary1.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n🧾 Download summary saved: {summary_path}")

    if FAIL_ON_DOWNLOAD_ERRORS and (failed or ingestion_failed):
        raise AssertionError(
            f"Some downloads failed.\n"
            f"FAILED={failed}\n"
            f"INGESTION_FAILED={ingestion_failed}"
        )

    return download_dir, summary_path


# =============================================================================
# TC_DL_001 — Download PDF + DOCX for every ingested letter (ANG and BU)
#
# How it works:
#   1. test_download_files_using_ui (ingestion test) automatically saves every
#      successfully opened letter to  tests/testdata/ingested_letters.json
#      as: {"letter_name": "...", "bu_name": "..."}
#   2. This test reads that file, groups letters by BU, and for each letter:
#        • applies the matching BU filter
#        • searches for the letter
#        • opens its detail page
#        • downloads PDF   → assert file saved and size > 0
#        • downloads DOCX  → assert file saved and size > 0
#
# No Excel file or env vars are required — all inputs come from testdata.
# Run order: executes after test_download_files_using_ui (file order).
# =============================================================================

def download_pdf_and_docx_from_testdata(page, download_root: str):
    """
    Read tests/testdata/ingested_letters.json (written by the ingestion test),
    group by BU, apply the correct BU filter once per group, then for each
    letter download both PDF and DOCX and assert both files are non-empty.
    """
    records = _load_ingested_letters()
    if not records:
        raise RuntimeError(
            f"No ingested letters found in testdata file: {TESTDATA_FILE}\n"
            "Run test_download_files_using_ui first so letters are recorded."
        )

    # Group by BU so we apply each filter only once
    from collections import defaultdict
    by_bu: dict[str, list[str]] = defaultdict(list)
    for rec in records:
        by_bu[rec["bu_name"].strip()].append(rec["letter_name"].strip())

    print(f"\n{'='*50}")
    print(f"📋 Testdata file : {TESTDATA_FILE}")
    print(f"📄 Total letters : {len(records)}  ({len(by_bu)} BU group(s))")
    for bu, names in by_bu.items():
        print(f"   • {bu}: {len(names)} letter(s)")
    print(f"{'='*50}\n")

    download_dir = os.path.join(download_root, "pdf_docx_downloads")
    os.makedirs(download_dir, exist_ok=True)

    # ── shared locators ───────────────────────────────────────────────────
    table_rows    = page.locator("table tbody tr")
    configure_btn = page.get_by_role("button", name="Configure Letter Type")

    pdf_menu_item = page.locator(
        "ul[role='menu'] li[role='menuitem']",
        has_text=re.compile(r"^\s*PDF\s*$", re.I),
    ).first

    docx_menu_item = page.locator(
        "ul[role='menu'] li[role='menuitem']",
        has_text=re.compile(r"^\s*DOCX\s*$", re.I),
    ).first

    results: list         = []
    assertion_errors: list = []

    # ── helpers ───────────────────────────────────────────────────────────
    def _first_row_text(timeout=2000) -> str:
        try:
            return clean_text(table_rows.first.inner_text(timeout=timeout))
        except Exception:
            return ""

    def _wait_results(q: str, timeout_ms: int = 30000):
        tokens = [t for t in clean_text(q).lower().split() if t]
        start  = page.evaluate("() => Date.now()")
        seen   = None
        while True:
            now = page.evaluate("() => Date.now()")
            if now - start > timeout_ms:
                raise RuntimeError(f"Timed out waiting for '{q}'")
            if detect_no_data_found(page):
                raise NotFoundError(f"NOT FOUND | {q}")
            if table_rows.count() == 0:
                seen = None; page.wait_for_timeout(250); continue
            txt = _first_row_text().lower()
            if not txt or not re.search(r"lt-\d+", txt) or not all(t in txt for t in tokens):
                seen = None; page.wait_for_timeout(250); continue
            if seen is None:
                seen = now; page.wait_for_timeout(400); continue
            txt2 = _first_row_text().lower()
            if txt2 and re.search(r"lt-\d+", txt2) and all(t in txt2 for t in tokens):
                return
            seen = None; page.wait_for_timeout(250)

    def _get_sb():
        for sel in [
            "input[placeholder='Search by Letter Type, Id and External Id']",
            "input[placeholder='Search by Letter Type and Id']",
            "input[placeholder*='Search by Letter']",
            "input[placeholder*='Search']",
        ]:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=1500):
                    return loc.first
            except Exception:
                pass
        raise RuntimeError("Search box not found")

    def _is_login() -> bool:
        try:
            return page.locator("#username").is_visible(timeout=1500)
        except Exception:
            return False

    def _relogin(bu: str):
        if _is_login():
            _login_and_open_letter_type(page, bu_name=bu)

    def _search(q: str, bu: str):
        _relogin(bu)
        if "/letter-type" not in (page.url or ""):
            page.goto(BASE_URL.rstrip("/") + "/letter-type",
                      wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            page.wait_for_timeout(1000)
        sb = _get_sb()
        expect(sb).to_be_visible(timeout=15000)
        sb.click(); page.wait_for_timeout(150)
        sb.press("Control+A"); sb.press("Backspace")
        sb.type(q, delay=25); sb.press("Enter")
        page.wait_for_timeout(700)
        try:
            _ls = ".MuiCircularProgress-root,.MuiLinearProgress-root"
            page.wait_for_selector(_ls, state="visible", timeout=1500)
            page.wait_for_selector(_ls, state="hidden",  timeout=20000)
        except Exception:
            pass
        _wait_results(q, timeout_ms=30000)

    def _open_detail(q: str):
        _wait_results(q, timeout_ms=20000)
        row = table_rows.first
        pe  = detect_pipeline_error_in_row(row)
        if pe:
            raise IngestionFailError(f"INGESTION FAIL | {pe}")
        id_cell = None
        id_txt  = ""
        for nth in [1, 0]:
            try:
                cell = row.locator("td").nth(nth)
                if cell.count() > 0 and cell.is_visible(timeout=1500):
                    t = clean_text(cell.inner_text(timeout=1500))
                    if re.match(r"^LT-\d+", t):
                        id_txt = t; id_cell = cell; break
            except Exception:
                pass
        if not id_txt:
            m = re.search(r"LT-\d+", _first_row_text())
            if m:
                id_txt = m.group(0)
        if not id_txt:
            raise RuntimeError(f"LT-xxx not found in first row for '{q}'")
        print(f"   🖱️  Clicking: {id_txt}")
        row.scroll_into_view_if_needed(); page.wait_for_timeout(300)
        try:
            (id_cell or row).click(timeout=5000)
        except Exception:
            (id_cell or row).click(force=True, timeout=5000)
        _wait_for_detail_page(page, timeout_ms=20000)
        print(f"   ✅ Detail page: {page.url}")

    def _go_back(bu: str):
        arrow = _find_back_arrow(page)
        if arrow:
            try:
                arrow.click(timeout=8000)
            except Exception:
                arrow.click(force=True, timeout=8000)
        else:
            page.go_back(wait_until="domcontentloaded", timeout=15000)
        try:
            _get_sb().wait_for(state="visible", timeout=15000)
        except Exception:
            pass
        expect(configure_btn).to_be_visible(timeout=15000)
        page.wait_for_timeout(500)

    def _open_menu():
        fail_if_preview_error(page)
        _, menu_btn = _get_download_buttons(page)
        menu_btn.wait_for(state="visible", timeout=30000)
        menu_btn.scroll_into_view_if_needed()
        try:
            menu_btn.click(timeout=5000)
        except Exception:
            menu_btn.click(force=True, timeout=5000)
        pdf_menu_item.wait_for(state="visible", timeout=20000)
        page.wait_for_timeout(150)

    def _click_item(loc, label: str):
        loc.wait_for(state="visible", timeout=20000)
        loc.scroll_into_view_if_needed(); page.wait_for_timeout(100)
        for _ in range(3):
            for method in [
                lambda: loc.click(timeout=5000),
                lambda: loc.click(force=True, timeout=5000),
                lambda: loc.dispatch_event("click"),
            ]:
                try:
                    method(); return
                except Exception:
                    pass
            page.wait_for_timeout(200)
        raise RuntimeError(f"Could not click {label} after 3 attempts")

    # ── per-BU, per-letter loop ───────────────────────────────────────────
    for bu, letter_names in by_bu.items():
        print(f"\n{'━'*50}")
        print(f"🏢 BU: {bu}  ({len(letter_names)} letter(s))")
        print(f"{'━'*50}")

        # Apply BU filter once for this group (map short names to full display names)
        _BU_FILTER_MAP = {"ANG": "ANG DONOT USE"}
        filter_bu = _BU_FILTER_MAP.get(bu.strip().upper(), bu)
        try:
            _apply_bu_filter(page, filter_bu)
        except Exception as e:
            print(f"   ⚠️  Could not apply filter for '{filter_bu}': {e}")

        for letter_name in letter_names:
            result = {
                "letter_name": letter_name,
                "bu_name": bu,
                "pdf_path": None,
                "docx_path": None,
                "pdf_ok": False,
                "docx_ok": False,
                "error": None,
            }
            try:
                print(f"\n   📝 {letter_name}")

                # 1. Search + open detail
                _search(letter_name, bu)
                if detect_no_data_found(page) or table_rows.count() == 0:
                    raise NotFoundError(f"NOT FOUND | {letter_name}")
                _open_detail(letter_name)
                fail_if_preview_error(page)

                # 2. Wait for preview ready
                main_btn, _ = _get_download_buttons(page)
                wait_for_preview_ready(page, main_btn, timeout_ms=240000, fast_fail_ms=5000)
                fail_if_preview_error(page)

                # 3. Download PDF ──────────────────────────────────────────
                print("   ⬇️  Downloading PDF…")
                _open_menu()
                with page.expect_download(timeout=120000) as dl_info:
                    _click_item(pdf_menu_item, "PDF")
                pdf_path = os.path.join(download_dir, f"{make_safe_name(letter_name)}_{make_safe_name(bu)}.pdf")
                dl_info.value.save_as(pdf_path)

                assert os.path.exists(pdf_path), \
                    f"PDF not saved to disk for '{letter_name}' (BU: {bu})"
                assert os.path.getsize(pdf_path) > 0, \
                    f"PDF is empty (0 bytes) for '{letter_name}' (BU: {bu})"

                result["pdf_path"] = pdf_path
                result["pdf_ok"]   = True
                print(f"   ✅ PDF saved: {pdf_path}")

                # 4. Download DOCX ─────────────────────────────────────────
                print("   ⬇️  Downloading DOCX…")
                _open_menu()   # re-open — menu closes after PDF click
                with page.expect_download(timeout=120000) as dl_info:
                    _click_item(docx_menu_item, "DOCX")
                docx_path = os.path.join(download_dir, f"{make_safe_name(letter_name)}_{make_safe_name(bu)}.docx")
                dl_info.value.save_as(docx_path)

                assert os.path.exists(docx_path), \
                    f"DOCX not saved to disk for '{letter_name}' (BU: {bu})"
                assert os.path.getsize(docx_path) > 0, \
                    f"DOCX is empty (0 bytes) for '{letter_name}' (BU: {bu})"

                result["docx_path"] = docx_path
                result["docx_ok"]   = True
                print(f"   ✅ DOCX saved: {docx_path}")

                _go_back(bu)

            except AssertionError as e:
                result["error"] = str(e)
                assertion_errors.append(str(e))
                print(f"   ❌ Assertion: {e}")
                try:
                    page.screenshot(path=os.path.join(
                        download_dir, f"FAIL_{make_safe_name(letter_name)}.png"), full_page=True)
                except Exception:
                    pass
                try:
                    page.keyboard.press("Escape")
                    _go_back(bu)
                except Exception:
                    pass

            except (NotFoundError, IngestionFailError, RuntimeError) as e:
                result["error"] = str(e)
                print(f"   ⚠️  {e}")
                try:
                    page.keyboard.press("Escape")
                    _go_back(bu)
                except Exception:
                    pass

            results.append(result)

    # ── summary ───────────────────────────────────────────────────────────
    pdf_ok   = sum(1 for r in results if r["pdf_ok"])
    docx_ok  = sum(1 for r in results if r["docx_ok"])
    both_ok  = sum(1 for r in results if r["pdf_ok"] and r["docx_ok"])
    failed   = [r["letter_name"] for r in results if not (r["pdf_ok"] and r["docx_ok"])]

    summary = {
        "run_ts": datetime.now().isoformat(timespec="seconds"),
        "testdata_file": TESTDATA_FILE,
        "total": len(results),
        "pdf_ok": pdf_ok,
        "docx_ok": docx_ok,
        "both_ok": both_ok,
        "failed": failed,
        "results": results,
    }
    summary_path = os.path.join(download_dir, "download_pdf_docx_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*50}")
    print(f"📊 PDF + DOCX DOWNLOAD SUMMARY")
    print(f"   Total   : {len(results)}")
    print(f"   PDF  ✅ : {pdf_ok}")
    print(f"   DOCX ✅ : {docx_ok}")
    print(f"   Both ✅ : {both_ok}")
    print(f"   Failed  : {len(failed)}")
    if failed:
        print(f"   ↳ {failed}")
    print(f"   Summary : {summary_path}")
    print(f"{'='*50}\n")

    # ── 4 final assertions: ANG PDF · ANG DOCX · BU PDF · BU DOCX ────────
    ang_results = [r for r in results if "ANG" in r["bu_name"].strip().upper()]
    bu_results  = [r for r in results if "ANG" not in r["bu_name"].strip().upper()]

    ang_pdf_fail  = [r["letter_name"] for r in ang_results if not r["pdf_ok"]]
    ang_docx_fail = [r["letter_name"] for r in ang_results if not r["docx_ok"]]
    bu_pdf_fail   = [r["letter_name"] for r in bu_results  if not r["pdf_ok"]]
    bu_docx_fail  = [r["letter_name"] for r in bu_results  if not r["docx_ok"]]

    assert not ang_pdf_fail, (
        f"[ANG PDF] Download failed for {len(ang_pdf_fail)} letter(s): {ang_pdf_fail}"
    )
    assert not ang_docx_fail, (
        f"[ANG DOCX] Download failed for {len(ang_docx_fail)} letter(s): {ang_docx_fail}"
    )
    assert not bu_pdf_fail, (
        f"[BU PDF] Download failed for {len(bu_pdf_fail)} letter(s): {bu_pdf_fail}"
    )
    assert not bu_docx_fail, (
        f"[BU DOCX] Download failed for {len(bu_docx_fail)} letter(s): {bu_docx_fail}"
    )

    return download_dir, summary_path


def _parse_excel_list_from_env_or_cli(cli_list):
    env_many = os.environ.get("EXCEL_FILES", "").strip()
    env_one = os.environ.get("EXCEL_FILE", "").strip()

    if env_many:
        return [x.strip() for x in env_many.split(",") if x.strip()]
    if env_one:
        return [env_one]

    if not cli_list:
        return []

    out = []
    for item in cli_list:
        out.extend([p.strip() for p in item.split(",") if p.strip()])

    seen, uniq = set(), []
    for p in out:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


def main(page):
    running_under_pytest = "PYTEST_CURRENT_TEST" in os.environ

    excel_files = []
    download_root = DEFAULT_DOWNLOAD_ROOT
    column = "actual"
    bu_name = "ANG DONOT USE"

    if running_under_pytest:
        excel_files = _parse_excel_list_from_env_or_cli(None)
        if not excel_files:
            default = os.path.join(PROJECT_DIR, "unv2_unv3.xlsx")
            if os.path.exists(default):
                excel_files = ["unv2_unv3.xlsx"]
            else:
                pytest.skip(
                    "unv2_unv3.xlsx not found in tests/ — "
                    "set EXCEL_FILE env var to specify an Excel file to use."
                )
                return
        download_root = os.environ.get("DOWNLOAD_ROOT", DEFAULT_DOWNLOAD_ROOT)
        column  = os.environ.get("EXCEL_COLUMN", "actual")
        bu_name = os.environ.get("BU_NAME", "ANG DONOT USE")
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--excel", action="append", required=True)
        parser.add_argument("--download-root", default=DEFAULT_DOWNLOAD_ROOT)
        parser.add_argument("--column", default="actual")
        parser.add_argument("--bu-name", default="ANG DONOT USE")
        args = parser.parse_args()
        excel_files = _parse_excel_list_from_env_or_cli(args.excel)
        download_root = args.download_root
        column  = args.column
        bu_name = args.bu_name

    os.makedirs(download_root, exist_ok=True)

    _login_and_open_letter_type(page, bu_name=bu_name)

    for excel_path in excel_files:
        download_for_one_excel(page, excel_path, download_root, column, bu_name=bu_name)


@pytest.mark.sanity
def test_download_files_using_ui(page):
    main(page)


# =============================================================================
# TC_DL_001 — Verify PDF and DOCX both download successfully for ingested letters
#
# How it works:
#   1. test_download_files_using_ui (ingestion test) automatically saves every
#      successfully opened letter to  tests/testdata/ingested_letters.json
#      as: {"letter_name": "...", "bu_name": "..."}
#   2. This test reads that file, groups letters by BU, and for each letter:
#        • applies the matching BU filter once per group
#        • searches for the letter
#        • opens its detail page
#        • downloads PDF   → assert file saved and size > 0
#        • downloads DOCX  → assert file saved and size > 0
#
# No Excel file or env vars needed — all inputs come from testdata.
# Run order: executes after test_download_files_using_ui (file order).
# =============================================================================
def _run_download_for_bu(page, bu_type: str):
    """
    Read ingested_letters.json, filter by bu_type (ANG or non-ANG), then for each
    letter: open the detail page ONCE, download both PDF and DOCX from that same page,
    then go back. Asserts both files exist and are non-empty.
    """
    all_records = _load_ingested_letters()
    if not all_records:
        pytest.skip(f"No ingested letters found in testdata: {TESTDATA_FILE}")

    if bu_type == "ANG":
        records = [r for r in all_records if "ANG" in r["bu_name"].strip().upper()]
    else:
        records = [r for r in all_records if "ANG" not in r["bu_name"].strip().upper()]

    if not records:
        pytest.skip(f"No {bu_type} letters found in testdata")

    download_dir = os.path.join(DEFAULT_DOWNLOAD_ROOT, "pdf_docx_downloads")
    os.makedirs(download_dir, exist_ok=True)

    _login_and_open_letter_type(page)

    table_rows = page.locator("table tbody tr")

    pdf_menu_item = page.locator(
        "ul[role='menu'] li[role='menuitem']",
        has_text=re.compile(r"^\s*PDF\s*$", re.I),
    ).first
    docx_menu_item = page.locator(
        "ul[role='menu'] li[role='menuitem']",
        has_text=re.compile(r"^\s*DOCX\s*$", re.I),
    ).first

    errors = []

    def _get_sb_local():
        for sel in [
            "input[placeholder='Search by Letter Type, Id and External Id']",
            "input[placeholder='Search by Letter Type and Id']",
            "input[placeholder*='Search by Letter']",
            "input[placeholder*='Search']",
        ]:
            try:
                loc = page.locator(sel)
                if loc.count() > 0 and loc.first.is_visible(timeout=1500):
                    return loc.first
            except Exception:
                pass
        raise RuntimeError("Search box not found")

    def _wait_row(q: str, timeout_ms=30000):
        tokens = clean_text(q).lower().split()
        start = page.evaluate("() => Date.now()")
        confirmed = None
        while True:
            now = page.evaluate("() => Date.now()")
            if now - start > timeout_ms:
                raise RuntimeError(f"Timed out waiting for '{q}' in results")
            if detect_no_data_found(page):
                raise NotFoundError(f"NOT FOUND | {q}")
            if table_rows.count() == 0:
                confirmed = None; page.wait_for_timeout(250); continue
            txt = clean_text(table_rows.first.inner_text(timeout=1000)).lower()
            if not txt or not re.search(r"lt-\d+", txt) or not all(t in txt for t in tokens):
                confirmed = None; page.wait_for_timeout(250); continue
            if confirmed is None:
                confirmed = now; page.wait_for_timeout(400); continue
            txt2 = clean_text(table_rows.first.inner_text(timeout=1000)).lower()
            if txt2 and re.search(r"lt-\d+", txt2) and all(t in txt2 for t in tokens):
                return
            confirmed = None; page.wait_for_timeout(250)

    def _recover():
        try:
            arrow = _find_back_arrow(page)
            if arrow:
                try:
                    arrow.click(timeout=6000)
                except Exception:
                    arrow.click(force=True, timeout=6000)
                page.wait_for_timeout(1000)
                return
        except Exception:
            pass
        try:
            page.go_back(wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1000)
        except Exception:
            pass
        try:
            page.goto(BASE_URL.rstrip("/") + "/letter-type",
                      wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1000)
        except Exception:
            pass

    def _open_menu_and_wait():
        fail_if_preview_error(page)
        _, menu_btn = _get_download_buttons(page)
        menu_btn.wait_for(state="visible", timeout=30000)
        menu_btn.scroll_into_view_if_needed()
        try:
            menu_btn.click(timeout=5000)
        except Exception:
            menu_btn.click(force=True, timeout=5000)
        pdf_menu_item.wait_for(state="visible", timeout=20000)
        page.wait_for_timeout(150)

    def _download_format(menu_item, label: str, file_path: str):
        menu_item.wait_for(state="visible", timeout=10000)
        menu_item.scroll_into_view_if_needed()
        with page.expect_download(timeout=120000) as dl_info:
            for method in [
                lambda: menu_item.click(timeout=5000),
                lambda: menu_item.click(force=True, timeout=5000),
                lambda: menu_item.dispatch_event("click"),
            ]:
                try:
                    method(); break
                except Exception:
                    pass
        dl_info.value.save_as(file_path)
        assert os.path.exists(file_path), f"{label} not saved to disk: {file_path}"
        assert os.path.getsize(file_path) > 0, f"{label} is empty (0 bytes): {file_path}"
        print(f"   ✅ {label} saved: {file_path}")

    for rec in records:
        letter_name = rec["letter_name"].strip()
        bu = rec["bu_name"].strip()
        print(f"\n   📝 [{bu_type}] {letter_name}")
        try:
            # Ensure on listing page
            if "/letter-type" not in (page.url or ""):
                page.goto(BASE_URL.rstrip("/") + "/letter-type",
                          wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(1000)

            # Search
            sb = _get_sb_local()
            expect(sb).to_be_visible(timeout=15000)
            sb.click(); page.wait_for_timeout(150)
            sb.press("Control+A"); sb.press("Backspace")
            sb.type(letter_name, delay=25); sb.press("Enter")
            page.wait_for_timeout(700)
            try:
                _ls = ".MuiCircularProgress-root,.MuiLinearProgress-root"
                page.wait_for_selector(_ls, state="visible", timeout=1500)
                page.wait_for_selector(_ls, state="hidden", timeout=20000)
            except Exception:
                pass
            _wait_row(letter_name, timeout_ms=30000)

            # Open detail page ONCE
            row = table_rows.first
            pe = detect_pipeline_error_in_row(row)
            if pe:
                raise RuntimeError(f"Pipeline Error for '{letter_name}'")
            id_cell = None
            for nth in [1, 0]:
                try:
                    cell = row.locator("td").nth(nth)
                    if cell.count() > 0 and cell.is_visible(timeout=1500):
                        t = clean_text(cell.inner_text(timeout=1500))
                        if re.match(r"^LT-\d+", t):
                            id_cell = cell; break
                except Exception:
                    pass
            row.scroll_into_view_if_needed(); page.wait_for_timeout(300)
            try:
                (id_cell or row).click(timeout=5000)
            except Exception:
                (id_cell or row).click(force=True, timeout=5000)
            _wait_for_detail_page(page, timeout_ms=20000)

            # Wait for preview ready
            main_btn, _ = _get_download_buttons(page)
            wait_for_preview_ready(page, main_btn, timeout_ms=240000, fast_fail_ms=5000)
            fail_if_preview_error(page)

            safe_name = make_safe_name(letter_name)
            safe_bu   = make_safe_name(bu)

            # Download PDF
            print("   ⬇️  Downloading PDF…")
            _open_menu_and_wait()
            pdf_file = os.path.join(download_dir, f"{safe_name}_{safe_bu}.pdf")
            _download_format(pdf_menu_item, "PDF", pdf_file)

            # Download DOCX from the SAME page (re-open menu)
            print("   ⬇️  Downloading DOCX…")
            _open_menu_and_wait()
            docx_file = os.path.join(download_dir, f"{safe_name}_{safe_bu}.docx")
            _download_format(docx_menu_item, "DOCX", docx_file)

            # Record both paths to downloaded_letters.json
            _save_downloaded_letter(letter_name, bu, pdf_file, docx_file)

            # Go back to listing only after both downloads are done
            arrow = _find_back_arrow(page)
            if arrow:
                try:
                    arrow.click(timeout=8000)
                except Exception:
                    arrow.click(force=True, timeout=8000)
            else:
                page.go_back(wait_until="domcontentloaded", timeout=15000)
            try:
                _get_sb_local().wait_for(state="visible", timeout=10000)
            except Exception:
                pass
            page.wait_for_timeout(500)

        except AssertionError:
            errors.append(str(sys.exc_info()[1]))
            try:
                page.screenshot(
                    path=os.path.join(download_dir, f"FAIL_{make_safe_name(letter_name)}.png"),
                    full_page=True
                )
            except Exception:
                pass
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
            _recover()

        except Exception as e:
            errors.append(f"{letter_name}: {e}")
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
            _recover()

    if errors:
        raise AssertionError(
            f"[{bu_type}] {len(errors)} failure(s):\n" + "\n".join(errors)
        )


@pytest.mark.sanity
@pytest.mark.dependency(name="test_download_ang", depends=["test_letter_type_ingestion"])
def test_download_ang(page):
    """TC_DL_001a: ANG letter — download PDF and DOCX from the same detail page."""
    _run_download_for_bu(page, bu_type="ANG")


@pytest.mark.sanity
@pytest.mark.dependency(name="test_download_bu", depends=["test_letter_type_ingestion"])
def test_download_bu(page):
    """TC_DL_001b: BU (non-ANG) letter — download PDF and DOCX from the same detail page."""
    _run_download_for_bu(page, bu_type="BU")
