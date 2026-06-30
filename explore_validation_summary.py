"""Exploratory (headed): ingest one letter, then drive the Validation Summary
XML-upload flow and dump what the page shows. Screenshots saved to reports/."""
import os
from playwright.sync_api import sync_playwright
from pages.login_page import LoginPage
from pages.letter_type_page import LetterTypePage
import tests.test_letter_type_ingestion as ing

UM_DOCX = "test_docx/UM/MHCA Approval_ARB.docx"
UM_XML  = "test_xml/UM-LTR-1778490508970463.xml"
BU_LABEL = "Jasw UM"
SHOT = lambda pg, n: pg.screenshot(path=f"reports/exp_{n}.png", full_page=True)

with sync_playwright() as p:
    b = p.chromium.launch(headless=False, slow_mo=250)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, accept_downloads=True)
    pg = ctx.new_page()

    # ── Login ────────────────────────────────────────────────────────────────
    lp = LoginPage(pg); lp.open(); lp.login()
    ltp = LetterTypePage(pg)
    # Ensure the listing (with the Configure button) is actually loaded
    for _ in range(3):
        ltp.open_direct(); ltp.is_loaded(); ltp.dismiss_ask_auto_popup()
        if pg.locator("button:has-text('Configure Letter Type')").first.is_visible():
            break
        pg.wait_for_timeout(2_000)

    # ── Ingest one UM document (proven ingestion helpers) ─────────────────────
    ing._open_modal(pg)
    print("BU options:", ing._select_bu(pg, BU_LABEL))
    ing._upload_docx(pg, UM_DOCX)
    pg.wait_for_selector("input[placeholder='Enter Letter Type Name']", timeout=25_000)
    sfx = ing._suffix()
    name = ing._append_to_field(pg, "Letter Type Name", sfx)
    extloc = ing._find_external_id_input(pg, name)
    cur = (extloc.input_value() or "").strip()
    ext = (cur[: len(cur) - len(sfx)] + sfx) if len(cur) >= len(sfx) else sfx
    extloc.click(click_count=3); extloc.fill(ext)
    ing._select_dropdown(pg, "mui-component-select-regionDropdown", "CA")
    ing._submit(pg)
    print("INGEST TOAST:", ing._get_toast(pg, 15_000))
    print("INGESTED NAME:", name)
    pg.wait_for_timeout(3_000); SHOT(pg, "1_after_ingest")

    # ── Open the new letter's detail page ─────────────────────────────────────
    import re as _re
    ltp.open_direct(); ltp.search(name)
    ing._wait_for_real_rows(ltp, timeout_s=15)
    pg.wait_for_timeout(1_000); SHOT(pg, "2_search")
    row = pg.locator("table tbody tr").first
    opened = False
    for nth in (1, 0):                      # LT-ID is usually the 2nd cell
        cell = row.locator("td").nth(nth)
        try:
            if cell.count() and cell.is_visible() and _re.match(r"^LT-\d+", (cell.inner_text() or "").strip()):
                cell.click(); opened = True; break
        except Exception:
            pass
    if not opened:
        row.click()
    pg.wait_for_timeout(4_000); SHOT(pg, "3_detail")
    print("DETAIL URL:", pg.url)
    print("CLICKABLE:", pg.eval_on_selector_all(
        "button,[role=tab],a",
        "els=>[...new Set(els.map(e=>(e.innerText||'').trim()).filter(t=>t&&t.length<40))]"))

    # ── Dismiss the "Duplicate Letter Type Detected" modal (Proceed) ──────────
    try:
        proceed = pg.get_by_role("button", name=_re.compile("proceed", _re.I)).first
        if proceed.is_visible(timeout=4_000):
            print("Duplicate modal -> clicking Proceed")
            proceed.click(); pg.wait_for_timeout(2_500)
    except Exception as e:
        print("no duplicate modal:", str(e)[:80])
    SHOT(pg, "3b_after_modal")

    # ── Validation Summary tab → upload XML ───────────────────────────────────
    try:
        vs = pg.get_by_role("tab", name=_re.compile("validation summary", _re.I)).first
        vs.click(timeout=10_000)
        pg.wait_for_timeout(3_000); SHOT(pg, "4_validation_summary")
        print("VS PANEL TEXT:\n", (pg.evaluate("()=>document.body.innerText") or "")[:1200])
        fin = pg.locator("input[type=file]")
        print("FILE INPUTS on VS:", fin.count())
        if fin.count():
            fin.first.set_input_files(UM_XML)
            print("selected XML:", UM_XML)
            pg.wait_for_timeout(1_500); SHOT(pg, "5_selected")
            # The two-step flow: after selecting, click "Upload File" to RUN validation
            upbtn = pg.get_by_role("button", name=_re.compile(r"^\s*upload file\s*$", _re.I)).first
            if upbtn.is_visible(timeout=5_000):
                print("clicking 'Upload File' to run validation")
                upbtn.click()
                pg.wait_for_timeout(15_000)   # let validation run
            else:
                print("Upload File button not found after selecting XML")
        SHOT(pg, "6_after_validate")
        print("VS RESULT TEXT:\n", (pg.evaluate("()=>document.body.innerText") or "")[:2200])
    except Exception as e:
        print("VS STEP ERROR:", str(e)[:200]); SHOT(pg, "5_error")

    pg.wait_for_timeout(8_000)  # leave the window up to look at
    b.close()
print("DONE — screenshots in reports/exp_*.png")
