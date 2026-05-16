import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://genesis.dev-v2.platform.autonomize.dev/genesis-platform/auth/realms/autonomize/protocol/openid-connect/auth?client_id=correspondence-automation-copilot-fe&redirect_uri=https%3A%2F%2Fcorrespondence.sprint.autonomize.dev%2F&state=4903b68a-ca32-414f-8460-100ff939d4fc&response_mode=fragment&response_type=code&scope=openid&nonce=96ca883f-ec2f-4bda-acd5-b566d83ac9a8&code_challenge=WJiJcbEhLuY72IOJT8P6gsOJ0ahMdS_vPD65F48nbQY&code_challenge_method=S256")
    page.get_by_role("textbox", name="Username").click()
    page.get_by_role("textbox", name="Username").click()
    page.get_by_role("textbox", name="Username").click()
    page.get_by_role("textbox", name="Username").fill("sapna.bhatt@autonomize.ai")
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").press("CapsLock")
    page.get_by_role("textbox", name="Password").fill("S")
    page.get_by_role("textbox", name="Password").press("CapsLock")
    page.get_by_role("textbox", name="Password").fill("Sapna@2025")
    page.get_by_role("button", name="Login").click()
    page.get_by_role("link", name="Letter Control Center").click()
    page.get_by_role("row", name="LetterHub-LTR-1778837499049478 LetterHub-LTR-EOB Part C EnglishMAYQA EOB Part C").get_by_role("checkbox").check()
    page.get_by_role("row", name="LetterHub-LTR-1778837499049478 LetterHub-LTR-EOB Part C EnglishMAYQA EOB Part C").get_by_role("checkbox").uncheck()
    page.locator(".MuiTableCell-root.MuiTableCell-body").first.click()
    page.get_by_role("button", name="Download").click()
    with page.expect_download() as download_info:
        page.get_by_role("menuitem", name="Download Report (CSV)").click()
    download = download_info.value
    page.get_by_role("row", name="LetterHub-LTR-1778837685988497 LetterHub-LTR-Medicaid Non Par Admission").get_by_role("checkbox").check()
    page.get_by_label("Delete Letters").get_by_role("button").click()
    page.get_by_role("button", name="Submit").click()
    page.get_by_role("button", name="Generate Letter").click()
    page.get_by_role("button", name="Select Letter Type").click()
    page.get_by_role("row", name="LT-1778750338189096 Test UNV3").get_by_role("button").click()
    page.get_by_role("button", name="Select file to Upload").click()
    page.get_by_role("button", name="Select file to Upload").set_input_files("CA_Pega AnG (1).xml")
    page.get_by_role("button", name="Upload File").click()
    page.get_by_role("button", name="Generate Letter").click()
    page.get_by_role("button").filter(has_text=re.compile(r"^$")).click()
    page.get_by_role("cell", name="UM").click()
    page.locator(".MuiButtonBase-root.MuiButton-root.MuiButton-contained").first.click()
    with page.expect_download() as download1_info:
        page.get_by_role("menuitem", name="PDF").click()
    download1 = download1_info.value
    page.locator(".MuiButtonBase-root.MuiButton-root.MuiButton-contained").first.click()
    with page.expect_download() as download2_info:
        page.get_by_role("menuitem", name="DOCX").click()
    download2 = download2_info.value
    page.get_by_role("tab", name="Delivery Logs").click()
    page.get_by_role("tab", name="Validation Summary").click()
    page.get_by_role("banner").locator("svg").first.click()
    page.get_by_role("button", name="Generate Letter").click()
    page.get_by_role("button", name="Ask Auto").click()
    page.goto("https://correspondence.sprint.autonomize.dev/letter-control-center?dateFrom=2026-04-24&dateTo=2026-05-15&timeFrom=00%3A00&timeTo=23%3A59")
    page.locator("tr:nth-child(3) > .MuiTableCell-root.MuiTableCell-body.MuiTableCell-sizeSmall.w-\\[30px\\]").click()
    page.get_by_role("row", name="LetterHub-LTR-1778836806094075 LetterHub-LTR-EOB Part C English3 RV2 EOB Part C").get_by_role("checkbox").check()
    page.get_by_role("button", name="Generate Letter").click()
    page.get_by_role("button", name="Select Letter Type").click()
    page.get_by_role("cell", name="UM", exact=True).click()
    page.get_by_role("button", name="Select file to Upload").click()
    page.get_by_role("button", name="Select file to Upload").set_input_files("UM-LTR-1778490508970463.xml")
    page.get_by_role("button", name="Upload File").click()
    page.get_by_role("row", name="LetterHub-LTR-1778840428558318 LetterHub-LTR-Test UNV3 MHIA Mcaid Red Susp Term").get_by_role("checkbox").check()
    page.get_by_role("cell", name="LetterHub-LTR-1778840428558318").click()
    page.locator(".MuiButtonBase-root.MuiButton-root.MuiButton-contained").first.click()
    with page.expect_download() as download3_info:
        page.get_by_role("menuitem", name="PDF").click()
    download3 = download3_info.value
    page.locator(".MuiButtonBase-root.MuiButton-root.MuiButton-contained").first.click()
    page.get_by_role("menuitem", name="DOCX").click()
    with page.expect_download() as download4_info:
        page.get_by_role("tab", name="Delivery Logs").click()
    download4 = download4_info.value
    page.get_by_role("tab", name="Validation Summary").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
