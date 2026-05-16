"""Generate test case details as an Excel report."""
import openpyxl
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side
)
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Test Cases"

# ── Colours ──────────────────────────────────────────────────────────────────
HEADER_BG   = "1F4E79"   # dark blue
SECTION_BG  = "2E75B6"   # mid blue
ALT_ROW_BG  = "DEEAF1"   # light blue
WHITE       = "FFFFFF"
GREEN       = "70AD47"
ORANGE      = "ED7D31"
GREY        = "D6DCE4"

def cell_fill(colour):
    return PatternFill("solid", fgColor=colour)

def thin_border():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)

# ── Column layout ─────────────────────────────────────────────────────────────
#  A   B          C                               D          E          F
#  #   TC ID      Test Case Title                 Module     Type       Status
COLS = ["#", "TC ID", "Test Case Title", "Module", "Type", "Status"]
COL_WIDTHS = [5, 14, 60, 28, 22, 12]

# ── Header row ────────────────────────────────────────────────────────────────
ws.append(COLS)
for col_idx, (heading, width) in enumerate(zip(COLS, COL_WIDTHS), start=1):
    cell = ws.cell(row=1, column=col_idx)
    cell.font = Font(bold=True, color=WHITE, size=11)
    cell.fill = cell_fill(HEADER_BG)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = thin_border()
    ws.column_dimensions[get_column_letter(col_idx)].width = width
ws.row_dimensions[1].height = 22

# ── Data ──────────────────────────────────────────────────────────────────────
# (tc_id, title, module, type, status)
TESTS = [
    # ── Sanity ────────────────────────────────────────────────────────────────
    ("SANITY", "Sanity / Core", None, None, None),
    ("—",   "Base URL loads the login screen",                               "test_sanity.py",           "Sanity | Agentic",  "Automated"),
    ("—",   "Login page contains all required fields",                       "test_sanity.py",           "Sanity | Agentic",  "Automated"),
    ("—",   "Login page has a non-empty document title",                     "test_sanity.py",           "Sanity | Agentic",  "Automated"),
    ("—",   "Valid credentials authenticate and redirect to Letter Type",    "test_sanity.py",           "Sanity | Agentic",  "Automated"),
    ("—",   "Invalid credentials do not grant access",                       "test_sanity.py",           "Sanity | Agentic",  "Automated"),
    ("—",   "Letter Type listing page loads successfully",                   "test_sanity.py",           "Sanity | Agentic",  "Automated"),
    ("—",   "Search box accepts and retains typed input",                    "test_sanity.py",           "Sanity | Agentic",  "Automated"),
    ("—",   "Listing page shows data rows or graceful empty state",          "test_sanity.py",           "Sanity | Agentic",  "Automated"),
    ("—",   "Stored authentication session bypasses the login form",         "test_sanity.py",           "Sanity | Agentic",  "Automated"),

    # ── Letter Type Details ───────────────────────────────────────────────────
    ("DETAILS", "Letter Type Details", None, None, None),
    ("TC_SM_013", "Letter Type Details page loads correctly",                "test_letter_type_details.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_014", "Versioning dropdown is visible",                          "test_letter_type_details.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_015", "Letter type version: Make Current",                       "test_letter_type_details.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_016", "Generate test letter with XML upload",                    "test_letter_type_details.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_017", "Validation Summary executes successfully",                "test_letter_type_details.py", "Sanity | Agentic", "Automated"),

    # ── Letter Type Editor ────────────────────────────────────────────────────
    ("EDITOR", "Letter Type Editor", None, None, None),
    ("TC_SM_018", "Letter Editor loads successfully",                        "test_letter_type_editor.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_019", "Generate Test Letter works from editor",                  "test_letter_type_editor.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_020", "Reset feature reverts editor content",                    "test_letter_type_editor.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_021", "Diff-view displays comparison correctly",                 "test_letter_type_editor.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_022", "Generated letter preview renders correctly",              "test_letter_type_editor.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_023", "Letter Type can be submitted for approval",               "test_letter_type_editor.py", "Sanity | Agentic", "Automated"),

    # ── Letter Import/Export ──────────────────────────────────────────────────
    ("IMPORT_EXPORT", "Letter Import / Export", None, None, None),
    ("TC_SM_024", "Import/Export page is accessible",                        "test_letter_import_export.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_025", "Export generates a valid ZIP file",                       "test_letter_import_export.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_026", "Approved ZIP import works",                               "test_letter_import_export.py", "Sanity | Agentic", "Skipped — pending artifact"),
    ("TC_SM_027", "Admin-only access is enforced",                           "test_letter_import_export.py", "Sanity | Agentic", "Automated"),

    # ── Component Library ─────────────────────────────────────────────────────
    ("COMP_LIB", "Component Library", None, None, None),
    ("TC_SM_028", "Component Library page is accessible",                    "test_component_library.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_029", "Placeholder list loads successfully",                     "test_component_library.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_030", "Insert list loads successfully",                          "test_component_library.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_031", "Condition list loads successfully",                       "test_component_library.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_032", "Block list loads successfully",                           "test_component_library.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_033", "User sample file uploaded successfully",                  "test_component_library.py", "Sanity | Agentic", "Automated"),

    # ── Letter Control Center ─────────────────────────────────────────────────
    ("CONTROL", "Letter Control Center", None, None, None),
    ("TC_SM_034", "Generated Letters page loads successfully",               "test_letter_control_center.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_035", "Filters are present",                                     "test_letter_control_center.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_036", "XML Upload & Generation Flow works",                      "test_letter_control_center.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_037", "Processing → Completed status update works",              "test_letter_control_center.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_038", "PDF & DOCX download works",                               "test_letter_control_center.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_039", "Validation Summary executes successfully",                "test_letter_control_center.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_040", "Bulk download job is triggered",                          "test_letter_control_center.py", "Sanity | Agentic", "Automated"),

    # ── Settings ──────────────────────────────────────────────────────────────
    ("SETTINGS", "Settings", None, None, None),
    ("TC_SM_041", "Global Configuration is visible and saveable",            "test_settings.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_042", "Business Unit Configuration is visible and saveable",     "test_settings.py", "Sanity | Agentic", "Automated"),

    # ── Audit Logger ──────────────────────────────────────────────────────────
    ("AUDIT", "Audit Logger", None, None, None),
    ("TC_SM_043", "Audit Logger page loads successfully",                    "test_audit_logger.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_044", "Letter actions create an audit entry",                    "test_audit_logger.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_045", "Audit data shows correct User / Entity / Action / Date",  "test_audit_logger.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_046", "Search & Date Range filter work",                         "test_audit_logger.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_047", "Download Audit Report works",                             "test_audit_logger.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_048", "Pagination & Rows-Per-Page work correctly",               "test_audit_logger.py", "Sanity | Agentic", "Automated"),

    # ── Recon Report ──────────────────────────────────────────────────────────
    ("RECON", "Recon Report", None, None, None),
    ("TC_SM_049", "Recon Report page loads and list is visible",             "test_recon_report.py", "Sanity | Agentic", "Automated"),

    # ── Letter Consolidation ──────────────────────────────────────────────────
    ("CONSOL", "Letter Consolidation", None, None, None),
    ("TC_SM_050", "Letters are grouped correctly in Letter Consolidation",   "test_letter_consolidation.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_051", "Percentage change after approval",                        "test_letter_consolidation.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_052", "Only one representative per group",                       "test_letter_consolidation.py", "Sanity | Agentic", "Automated"),
    ("TC_SM_053", "Documents can be moved between groups",                   "test_letter_consolidation.py", "Sanity | Agentic", "Automated"),

    # ── Dashboard ─────────────────────────────────────────────────────────────
    ("DASHBOARD", "Dashboard", None, None, None),
    ("—", "Each stat card count matches API statusSummary",                  "test_dashboard.py", "Sanity | Agentic", "Automated"),
    ("—", "Pending Approvals footer matches API totalRecords",               "test_dashboard.py", "Sanity | Agentic", "Automated"),
    ("—", "Approved Versions footer matches API totalRecords",               "test_dashboard.py", "Sanity | Agentic", "Automated"),
    ("—", "Rejected Approvals footer matches API totalRecords",              "test_dashboard.py", "Sanity | Agentic", "Automated"),

    # ── Navigation ────────────────────────────────────────────────────────────
    ("NAV", "Navigation", None, None, None),
    ("—", "All 9 sidebar navigation pages load correctly",                   "test_navigation.py", "Sanity | Agentic", "Automated"),

    # ── Letter Type ───────────────────────────────────────────────────────────
    ("LETTER_TYPE", "Letter Type", None, None, None),
    ("—", "Letter Type list loads with records",                             "test_letter_type.py", "Sanity | Agentic", "Automated"),
    ("—", "Filter by status returns matching results",                       "test_letter_type.py", "Sanity | Agentic", "Automated"),
    ("—", "Download button triggers a file download",                        "test_letter_type.py", "Sanity | Agentic", "Automated"),
    ("—", "Uploaded template transitions Processing → Draft",                "test_letter_type.py", "Sanity | Agentic", "Automated"),

    # ── Pure Agentic AI ───────────────────────────────────────────────────────
    ("AGENTIC", "Pure Agentic AI (Gemini)", None, None, None),
    ("AI-L1-01", "Dashboard shows welcome message after login",              "test_agentic.py", "Level 1 — Visual Assert", "Automated"),
    ("AI-L1-02", "Letter Type table is visible after navigation",            "test_agentic.py", "Level 1 — Visual Assert", "Automated"),
    ("AI-L1-03", "Search box is visible on Letter Type page",                "test_agentic.py", "Level 1 — Visual Assert", "Automated"),
    ("AI-L1-04", "Error message is NOT shown on Letter Type page",           "test_agentic.py", "Level 1 — Visual Assert", "Automated"),
    ("AI-L2-01", "Self-heal: find search box selector from DOM",             "test_agentic.py", "Level 2 — Self-Healing",  "Automated"),
    ("AI-L2-02", "Self-heal: find Letter Type sidebar link selector",        "test_agentic.py", "Level 2 — Self-Healing",  "Automated"),
    ("AI-L3-01", "Navigate to Letter Type using natural language",           "test_agentic.py", "Level 3 — Autonomous",    "Automated"),
    ("AI-L3-02", "Search for a letter type using natural language",          "test_agentic.py", "Level 3 — Autonomous",    "Automated"),
]

row_num = 2
tc_counter = 0

for entry in TESTS:
    tc_id, title, module, tc_type, status = entry

    # Section header row
    if module is None:
        ws.merge_cells(f"A{row_num}:F{row_num}")
        cell = ws.cell(row=row_num, column=1, value=f"  {title}")
        cell.font = Font(bold=True, color=WHITE, size=10)
        cell.fill = cell_fill(SECTION_BG)
        cell.alignment = Alignment(vertical="center")
        cell.border = thin_border()
        ws.row_dimensions[row_num].height = 18
        row_num += 1
        tc_counter = 0
        continue

    tc_counter += 1
    is_alt = tc_counter % 2 == 0
    bg = ALT_ROW_BG if is_alt else WHITE

    row_data = [tc_counter, tc_id, title, module, tc_type, status]
    for col_idx, value in enumerate(row_data, start=1):
        cell = ws.cell(row=row_num, column=col_idx, value=value)
        cell.border = thin_border()
        cell.alignment = Alignment(vertical="center", wrap_text=(col_idx == 3))

        # Status colour coding
        if col_idx == 6:
            if status == "Automated":
                cell.fill = cell_fill("E2EFDA")
                cell.font = Font(color="375623", bold=True)
            elif "Skipped" in (status or ""):
                cell.fill = cell_fill("FFF2CC")
                cell.font = Font(color="7F6000", bold=True)
            else:
                cell.fill = cell_fill(bg)
        elif col_idx == 5:
            if "Level 3" in (tc_type or ""):
                cell.font = Font(color="7030A0", bold=True)
                cell.fill = cell_fill("EAD1DC")
            elif "Level 2" in (tc_type or ""):
                cell.font = Font(color="833C00", bold=True)
                cell.fill = cell_fill("FCE4D6")
            elif "Level 1" in (tc_type or ""):
                cell.font = Font(color="375623", bold=True)
                cell.fill = cell_fill("E2EFDA")
            else:
                cell.fill = cell_fill(bg)
        else:
            cell.fill = cell_fill(bg)

    ws.row_dimensions[row_num].height = 20
    row_num += 1

# ── Summary tab ───────────────────────────────────────────────────────────────
ws2 = wb.create_sheet("Summary")
ws2.column_dimensions["A"].width = 35
ws2.column_dimensions["B"].width = 15

summary_data = [
    ("Metric", "Count"),
    ("Total Test Cases", 67),
    ("Automated", 66),
    ("Skipped (pending artifact)", 1),
    ("", ""),
    ("Sanity Tests", 59),
    ("Pure Agentic AI Tests", 8),
    ("", ""),
    ("Test Files", 13),
    ("smart_assert call sites", 115),
    ("Tests with recovery_steps", 5),
    ("", ""),
    ("AI Model", "gemini-2.5-flash-lite"),
    ("Marks", "pytest.mark.sanity | pytest.mark.agentic"),
]

for r_idx, (label, value) in enumerate(summary_data, start=1):
    c1 = ws2.cell(row=r_idx, column=1, value=label)
    c2 = ws2.cell(row=r_idx, column=2, value=value)
    if r_idx == 1:
        for c in (c1, c2):
            c.font = Font(bold=True, color=WHITE)
            c.fill = cell_fill(HEADER_BG)
            c.alignment = Alignment(horizontal="center")
    elif label:
        c1.font = Font(bold=True)
        c1.fill = cell_fill(ALT_ROW_BG)
        c2.fill = cell_fill(ALT_ROW_BG)
    for c in (c1, c2):
        c.border = thin_border()
        c.alignment = Alignment(vertical="center")
    ws2.row_dimensions[r_idx].height = 18

# ── Freeze panes & auto-filter ────────────────────────────────────────────────
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:F1"

# ── Save ──────────────────────────────────────────────────────────────────────
out = "docs/AutoE2E_TestCases.xlsx"
wb.save(out)
print(f"Saved: {out}")
