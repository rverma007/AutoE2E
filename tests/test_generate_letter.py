# Author: Ruchika Verma <testing.ruchika@gmail.com>
"""
TC_GEN_001 — Generate Letter via Validation Summary XML upload

Reads tests/testdata/ingested_letters.json (written by test_letter_type_ingestion.py),
for each record:
  1. Searches the listing by letter name.
  2. Opens the detail page.
  3. Clicks the Validation Summary tab.
  4. Uploads the BU-matched XML from test_xml/.
  5. Clicks Upload, waits for completion.
  6. Clicks Download Letter and saves to tests/downloaded/generated/.
  7. Appends the result to tests/testdata/generated_letters.json.

XML lookup: test_xml/<BU_name>/ subfolder first, then fuzzy match in test_xml/.
Dependency: test_letter_type_ingestion must run first.
"""
import os
import re
import json
import pytest
import allure
from datetime import datetime
from playwright.sync_api import Page, expect

# ── paths ──────────────────────────────────────────────────────────────────
_TESTS_DIR      = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR    = os.path.dirname(_TESTS_DIR)

BASE_URL            = "https://correspondence.sprint.autonomize.dev/"
DEFAULT_XML_ROOT    = os.path.join(_PROJECT_DIR, "test_xml")
DEFAULT_GEN_ROOT    = os.path.join(_TESTS_DIR, "downloaded", "generated")
_TESTDATA_DIR       = os.path.join(_TESTS_DIR, "testdata")
_INGESTED_FILE      = os.path.join(_TESTDATA_DIR, "ingested_letters.json")
_GENERATED_FILE     = os.path.join(_TESTDATA_DIR, "generated_letters.json")

pytestmark = pytest.mark.sanity


# ── testdata helpers ───────────────────────────────────────────────────────

def _load_ingested_letters() -> list:
    if not os.path.exists(_INGESTED_FILE):
        return []
    try:
        with open(_INGESTED_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_generated_letter(letter_name: str, bu_name: str,
                            xml_path: str, generated_path: str, status: str) -> None:
    os.makedirs(_TESTDATA_DIR, exist_ok=True)
    try:
        with open(_GENERATED_FILE, encoding="utf-8") as f:
            existing = json.load(f)
        if not isinstance(existing, list):
            existing = []
    except Exception:
        existing = []
    key = (letter_name.strip(), bu_name.strip())
    for rec in existing:
        if (rec["letter_name"].strip(), rec["bu_name"].strip()) == key:
            rec.update({"xml_path": xml_path, "generated_path": generated_path, "status": status})
            break
    else:
        existing.append({
            "letter_name":    letter_name,
            "bu_name":        bu_name,
            "xml_path":       xml_path,
            "generated_path": generated_path,
            "status":         status,
        })
    with open(_GENERATED_FILE, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


# ── utilities ──────────────────────────────────────────────────────────────

def clean_text(s: str) -> str:
    s = str(s).replace("\xa0", " ")
    s = re.sub(r"[ -‍  ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def make_safe_name(name: str) -> str:
    name = clean_text(name)
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, "_")
    return "_".join(name.strip().split())[:180]


# ── XML resolver ───────────────────────────────────────────────────────────

def _find_xml_for_bu(bu_name: str, xml_root: str) -> str | None:
    """
    Look for an XML file that matches the BU.
    Priority:
      1. test_xml/<bu_name>/ subfolder — first .xml inside
      2. Exact filename match in test_xml/
      3. Fuzzy: file whose stem contains bu_name (case-insensitive)
    """
    bu_lower = bu_name.strip().lower()

    # 1. Subfolder
    sub = os.path.join(xml_root, bu_name)
    if os.path.isdir(sub):
        for fname in sorted(os.listdir(sub)):
            if fname.lower().endswith(".xml"):
                return os.path.join(sub, fname)

    if not os.path.isdir(xml_root):
        return None

    files = [f for f in os.listdir(xml_root) if f.lower().endswith(".xml")]

    # 2. Exact stem match
    for fname in files:
        if os.path.splitext(fname)[0].lower() == bu_lower:
            return os.path.join(xml_root, fname)

    # 3. Fuzzy: stem contains bu name
    for fname in files:
        if bu_lower in fname.lower():
            print(f"   🔍 XML fuzzy match for BU='{bu_name}': {fname}")
            return os.path.join(xml_root, fname)

    print(f"   ⚠️  No XML found for BU='{bu_name}' in {xml_root}")
    return None


# ── page helpers ───────────────────────────────────────────────────────────

def detect_no_data_found(page: Page) -> bool:
    try:
        loc = page.locator(r"text=/No Data Found\.?/i").first
        return loc.count() > 0 and loc.is_visible(timeout=300)
    except Exception:
        return False


def detect_pipeline_error_in_row(row) -> str | None:
    try:
        pill = row.locator(r"text=/\bPipeline Error\b/i").first
        if pill.count() > 0 and pill.is_visible(timeout=250):
            return (pill.inner_text(timeout=200) or "Pipeline Error").strip()
    except Exception:
        pass
    try:
        t = (row.inner_text(timeout=400) or "").strip()
        if re.search(r"\bPipeline Error\b", t, re.I):
            return "Pipeline Error"
    except Exception:
        pass
    return None


def _find_back_arrow(page: Page):
    candidates = [
        page.locator("button[aria-label*='back' i]"),
        page.locator("[data-testid='ArrowBackIcon']"),
        page.locator("[data-testid='ArrowBackIosIcon']"),
        page.locator("[data-testid='ChevronLeftIcon']"),
        page.locator("[data-testid='KeyboardBackspaceIcon']"),
        page.locator("svg").filter(has=page.locator("path[d^='M20 11H7.83']")),
        page.locator("svg").filter(has=page.locator("path[d^='M15.41 16.59']")),
    ]
    for loc in candidates:
        try:
            if loc.count() > 0 and loc.first.is_visible(timeout=300):
                return loc.first
        except Exception:
            pass
    return None


def _wait_for_detail_page(page: Page, timeout_ms: int = 20_000) -> None:
    start = page.evaluate("() => Date.now()")
    while True:
        if page.evaluate("() => Date.now()") - start > timeout_ms:
            raise RuntimeError(f"Timed out waiting for detail page. URL={page.url}")
        try:
            if "/letter-type/" in (page.url or ""):
                return
        except Exception:
            pass
        if _find_back_arrow(page) is not None:
            return
        page.wait_for_timeout(300)


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
    try:
        loc = page.get_by_placeholder(re.compile(r"Search", re.I)).first
        if loc.is_visible(timeout=1_500):
            return loc
    except Exception:
        pass
    raise RuntimeError("Search box not found on Letter Type page")


def _recover_to_listing(page: Page) -> None:
    try:
        if _get_search_box(page).is_visible(timeout=2_000):
            return
    except Exception:
        pass
    try:
        arrow = _find_back_arrow(page)
        if arrow:
            arrow.click(timeout=6_000)
            page.wait_for_timeout(1_500)
            return
    except Exception:
        pass
    try:
        page.go_back(wait_until="domcontentloaded", timeout=15_000)
        page.wait_for_timeout(1_500)
    except Exception:
        pass
    try:
        page.goto(BASE_URL.rstrip("/") + "/letter-type",
                  wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(1_000)
    except Exception:
        pass


# ── core generate logic ────────────────────────────────────────────────────

def _generate_for_letter(page: Page, letter_name: str, bu_name: str,
                          gen_root: str, xml_root: str) -> dict:
    """
    Execute the full generate flow for one letter.
    Returns a result dict with status/saved_path/error keys.
    """
    result = {
        "letter_name":    letter_name,
        "bu_name":        bu_name,
        "xml_path":       None,
        "generated_path": None,
        "status":         "ERROR",
        "error":          None,
    }

    table_rows    = page.locator("table tbody tr")
    configure_btn = page.get_by_role("button", name="Configure Letter Type")

    # ── helpers scoped to this call ────────────────────────────────────────

    def _search(q: str):
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
        # wait for a result row containing the query tokens
        tokens = clean_text(q).lower().split()
        start = page.evaluate("() => Date.now()")
        while True:
            if page.evaluate("() => Date.now()") - start > 30_000:
                raise RuntimeError(f"Timed out waiting for results for '{q}'")
            if detect_no_data_found(page):
                raise RuntimeError(f"NOT FOUND | {q}")
            if table_rows.count() == 0:
                page.wait_for_timeout(250); continue
            txt = clean_text(table_rows.first.inner_text(timeout=1_000)).lower()
            if re.search(r"lt-\d+", txt) and all(t in txt for t in tokens):
                return
            page.wait_for_timeout(250)

    def _open_detail():
        row = table_rows.first
        pe = detect_pipeline_error_in_row(row)
        if pe:
            raise RuntimeError(f"Pipeline Error for '{letter_name}'")
        id_cell = None
        for nth in [1, 0]:
            try:
                cell = row.locator("td").nth(nth)
                if cell.count() > 0 and cell.is_visible(timeout=1_500):
                    t = clean_text(cell.inner_text(timeout=1_500))
                    if re.match(r"^LT-\d+", t):
                        id_cell = cell; break
            except Exception:
                pass
        row.scroll_into_view_if_needed(); page.wait_for_timeout(300)
        try:
            (id_cell or row).click(timeout=5_000)
        except Exception:
            (id_cell or row).click(force=True, timeout=5_000)
        _wait_for_detail_page(page, timeout_ms=20_000)

    def _click_validation_summary_tab():
        page.wait_for_selector(".MuiTab-root, [role='tab']", timeout=15_000)
        page.wait_for_timeout(1_000)
        for sel in (".MuiTab-root", "[role='tab']", "button[role='tab']"):
            tabs = page.locator(sel)
            for i in range(tabs.count()):
                try:
                    tab = tabs.nth(i)
                    txt = (tab.inner_text(timeout=400) or "").strip()
                    if re.search(r"Validation\s*Summary", txt, re.I):
                        tab.scroll_into_view_if_needed()
                        tab.click(timeout=5_000)
                        page.wait_for_timeout(1_000)
                        return
                    for attr in ("aria-label", "title"):
                        val = tab.get_attribute(attr) or ""
                        if re.search(r"Validation\s*Summary", val, re.I):
                            tab.scroll_into_view_if_needed()
                            tab.click(timeout=5_000)
                            page.wait_for_timeout(1_000)
                            return
                except Exception:
                    pass
        for loc in (
            page.get_by_role("tab",   name=re.compile(r"Validation Summary", re.I)),
            page.get_by_role("button", name=re.compile(r"Validation Summary", re.I)),
        ):
            try:
                if loc.count() > 0 and loc.first.is_visible(timeout=2_000):
                    loc.first.scroll_into_view_if_needed()
                    loc.first.click(timeout=5_000)
                    page.wait_for_timeout(1_000)
                    return
            except Exception:
                pass
        raise RuntimeError("Validation Summary tab not found")

    def _upload_xml(xml_path: str):
        file_input = page.locator("input[type='file']")
        try:
            file_input.wait_for(state="attached", timeout=5_000)
            file_input.first.set_input_files(xml_path)
            page.wait_for_timeout(500)
            return
        except Exception:
            pass
        try:
            page.evaluate("""() => {
                document.querySelectorAll("input[type='file']").forEach(el => {
                    el.style.cssText += ';display:block!important;visibility:visible!important;'
                        + 'opacity:1!important;position:fixed!important;top:0;left:0;z-index:9999;';
                });
            }""")
            file_input.first.set_input_files(xml_path)
            page.wait_for_timeout(500)
            return
        except Exception:
            pass
        for btn_loc in (
            page.get_by_role("button", name=re.compile(r"Select file", re.I)),
            page.locator("button:has-text('Select file')"),
            page.locator("button:has-text('Browse')"),
        ):
            try:
                if btn_loc.count() > 0 and btn_loc.first.is_visible(timeout=2_000):
                    with page.expect_file_chooser(timeout=10_000) as fc:
                        btn_loc.first.click(timeout=5_000)
                    fc.value.set_files(xml_path)
                    page.wait_for_timeout(500)
                    return
            except Exception:
                pass
        raise RuntimeError(f"Could not upload XML: {xml_path}")

    def _click_upload():
        for loc in (
            page.get_by_role("button", name=re.compile(r"^Upload$",   re.I)),
            page.get_by_role("button", name=re.compile(r"^Submit$",   re.I)),
            page.get_by_role("button", name=re.compile(r"^Validate$", re.I)),
            page.locator("button:has-text('Upload')"),
            page.locator("button:has-text('Submit')"),
        ):
            try:
                if loc.count() > 0 and loc.first.is_visible(timeout=2_000):
                    loc.first.click(timeout=5_000)
                    page.wait_for_timeout(500)
                    return
            except Exception:
                pass

    def _wait_upload_complete(timeout_ms=90_000):
        start   = page.evaluate("() => Date.now()")
        spinner = page.locator(".MuiCircularProgress-root, [role='progressbar']")
        sigs    = [
            page.locator("text=/Upload.*success/i"),
            page.locator("text=/Validation.*complete/i"),
            page.locator("text=/Last Run/i"),
            page.locator(".MuiAlert-standardSuccess"),
            page.locator("[role='alert']:has-text('success')"),
        ]
        while True:
            now = page.evaluate("() => Date.now()")
            if now - start > timeout_ms:
                return
            for sig in sigs:
                try:
                    if sig.count() > 0 and sig.first.is_visible(timeout=200):
                        page.wait_for_timeout(500)
                        return
                except Exception:
                    pass
            try:
                if spinner.count() == 0 or not spinner.first.is_visible(timeout=200):
                    if now - start > 3_000:
                        page.wait_for_timeout(500)
                        return
            except Exception:
                if now - start > 3_000:
                    return
            page.wait_for_timeout(500)

    def _download_letter() -> str | None:
        for loc in (
            page.get_by_role("button", name="Download Letter"),
            page.locator("button:has-text('Download Letter')"),
            page.locator("text=/Download Letter/i"),
        ):
            try:
                if loc.count() > 0 and loc.first.is_visible(timeout=3_000):
                    os.makedirs(gen_root, exist_ok=True)
                    with page.expect_download(timeout=120_000) as dl_info:
                        loc.first.click(timeout=10_000)
                    dl   = dl_info.value
                    ext  = os.path.splitext(dl.suggested_filename or "")[1] or ".pdf"
                    path = os.path.join(gen_root, make_safe_name(letter_name) + ext)
                    dl.save_as(path)
                    return path
            except Exception:
                pass
        return None

    # ── execute steps ──────────────────────────────────────────────────────
    with allure.step(f"Find XML for BU={bu_name}"):
        xml_path = _find_xml_for_bu(bu_name, xml_root)
        assert xml_path, f"No XML file found for BU='{bu_name}' in {xml_root}"
        result["xml_path"] = xml_path
        allure.attach(xml_path, name="XML path", attachment_type=allure.attachment_type.TEXT)

    with allure.step(f"Search for '{letter_name}'"):
        _search(letter_name)
        assert not detect_no_data_found(page) and table_rows.count() > 0, \
            f"'{letter_name}' not found in listing"

    with allure.step("Open detail page"):
        _open_detail()

    with allure.step("Wait for detail page to load"):
        page.wait_for_load_state("domcontentloaded", timeout=30_000)
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass
        page.wait_for_timeout(2_000)

    with allure.step("Click Validation Summary tab"):
        _click_validation_summary_tab()
        page.wait_for_timeout(1_500)

    with allure.step(f"Upload XML: {os.path.basename(xml_path)}"):
        _upload_xml(xml_path)
        allure.attach(xml_path, name="Uploaded XML",
                      attachment_type=allure.attachment_type.TEXT)

    with allure.step("Click Upload button"):
        _click_upload()

    with allure.step("Wait for upload to complete"):
        _wait_upload_complete(timeout_ms=90_000)

    with allure.step("Click Download Letter"):
        saved_path = _download_letter()
        assert saved_path, "'Download Letter' button not found or download failed"
        result["generated_path"] = saved_path
        result["status"] = "OK"
        allure.attach(saved_path, name="Saved path",
                      attachment_type=allure.attachment_type.TEXT)

    return result


# ── parametrize at collection time ─────────────────────────────────────────

def _params() -> list:
    records = _load_ingested_letters()
    if not records:
        return [pytest.param("__skip__", "__skip__", id="no_ingested_data")]
    return [
        pytest.param(r["letter_name"], r["bu_name"],
                     id=f"{r['letter_name'][:40]}|{r['bu_name']}")
        for r in records
    ]


# ── test class ──────────────────────────────────────────────────────────────

@allure.epic("Correspondence Application")
@allure.feature("Letter Type")
class TestGenerateLetter:

    @pytest.fixture(scope="class", autouse=True)
    def _reset_generated_json(self):
        """Clear generated_letters.json and downloaded/generated/ before each class run."""
        import shutil
        os.makedirs(_TESTDATA_DIR, exist_ok=True)
        with open(_GENERATED_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        if os.path.isdir(DEFAULT_GEN_ROOT):
            shutil.rmtree(DEFAULT_GEN_ROOT)
        os.makedirs(DEFAULT_GEN_ROOT, exist_ok=True)
        yield

    @allure.story("Generate")
    @allure.title("[TC_GEN_001] Generate letter via Validation Summary XML upload")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.description(
        "For each ingested letter:\n"
        "1. Search the listing by letter name.\n"
        "2. Open the detail page.\n"
        "3. Click the Validation Summary tab.\n"
        "4. Upload the BU-matched XML from test_xml/.\n"
        "5. Wait for upload to complete.\n"
        "6. Click Download Letter and save to downloaded/generated/.\n"
        "7. Assert the generated file is saved and non-empty."
    )
    @pytest.mark.dependency(name="test_generate_letter", depends=["test_letter_type_ingestion"])
    @pytest.mark.parametrize("letter_name,bu_name", _params())
    def test_generate_letter(self, authed_page: Page, letter_name: str, bu_name: str):
        if letter_name == "__skip__":
            pytest.skip("No ingested letters found — run test_letter_type_ingestion first")

        allure.attach(
            f"Letter : {letter_name}\nBU     : {bu_name}",
            name="Inputs",
            attachment_type=allure.attachment_type.TEXT,
        )

        try:
            result = _generate_for_letter(
                authed_page, letter_name, bu_name,
                DEFAULT_GEN_ROOT, DEFAULT_XML_ROOT,
            )
        finally:
            _recover_to_listing(authed_page)

        _save_generated_letter(
            letter_name, bu_name,
            result.get("xml_path", ""),
            result.get("generated_path", ""),
            result.get("status", "ERROR"),
        )

        assert result["status"] == "OK", \
            result.get("error") or "Generate failed with no specific error"

        gen_path = result["generated_path"]
        assert os.path.exists(gen_path), f"Generated file not on disk: {gen_path}"
        assert os.path.getsize(gen_path) > 0, f"Generated file is empty: {gen_path}"
