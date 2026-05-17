# AutoPythone2e

End-to-end test suite for the **Correspondence Application** (LettersHub), built with [Playwright](https://playwright.dev/python/) and [pytest](https://pytest.org/).

**Author:** Ruchika Verma &lt;testing.ruchika@gmail.com&gt;

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Prerequisites](#prerequisites)
4. [Setup](#setup)
5. [Configuration](#configuration)
6. [Running Tests](#running-tests)
7. [Test Suite](#test-suite)
8. [Letter Type Dependency Chain](#letter-type-dependency-chain)
9. [Test Reports](#test-reports)
10. [Project Structure](#project-structure)
11. [Architecture](#architecture)
12. [Troubleshooting](#troubleshooting)

---

## Overview

The suite covers the full post-login surface of the Correspondence application across **19 test files** and **104 test cases**.

All tests are tagged `@pytest.mark.sanity` so the entire suite runs with a single command:

```powershell
pytest tests/ -p no:xdist -v
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Browser automation | Playwright (sync API) `>=1.40` |
| Test runner | pytest `>=7.0` |
| Parallel execution | pytest-xdist `>=3.0` |
| HTML reports | pytest-html `>=4.0` |
| Rich reports | allure-pytest `>=2.13` |
| Test dependency ordering | pytest-dependency |

---

## Prerequisites

- **Python 3.10+**
- **pip** (comes with Python)
- **Allure CLI** (optional — only needed to view Allure reports):
  ```powershell
  npm install -g allure-commandline
  ```

---

## Setup

```powershell
# 1. Clone the repo
git clone <repo-url>
cd AutoPythone2e

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Copy the env template and fill in your credentials
copy .env.example .env
```

Open `.env` and set at minimum:

```ini
BASE_URL=https://correspondence.sprint.autonomize.dev/
APP_USERNAME=your.user@example.com
APP_PASSWORD=YourPassword
```

---

## Configuration

All settings are read from `.env`. **Never commit `.env`** — it is gitignored.

| Variable | Default | Description |
|---|---|---|
| `BASE_URL` | _(required)_ | Full app URL including trailing slash |
| `APP_USERNAME` | _(required)_ | Login e-mail / username |
| `APP_PASSWORD` | _(required)_ | Login password |
| `ENVIRONMENT` | `sprint` | Label shown in the HTML report header |
| `BROWSER` | `chromium` | `chromium` / `firefox` / `webkit` |
| `HEADLESS` | `false` | `true` to hide the browser window |
| `SLOW_MO` | `0` | Milliseconds added between Playwright actions |
| `VIEWPORT_WIDTH` | `1920` | Browser viewport width in pixels |
| `VIEWPORT_HEIGHT` | `1080` | Browser viewport height in pixels |
| `DEFAULT_TIMEOUT` | `30000` | Playwright default action timeout (ms) |
| `NAVIGATION_TIMEOUT` | `60000` | Page navigation timeout (ms) |
| `RECORD_VIDEO` | `false` | Record a `.webm` for each test |
| `RECORD_TRACE` | `true` | Playwright trace; kept only on failure |
| `SCREENSHOT_ON_FAILURE` | `true` | Full-page PNG captured when a test fails |
| `REPORT_TITLE` | `AutoPythone2e Sanity Report` | HTML report title |

---

## Running Tests

> **Important:** Always run from `D:\AutoPythone2e`.

---

### Recommended — two-stage script (parallel where safe, ordered where required)

```powershell
.\run_tests.ps1
```

This is the **recommended way** to run everything. The script handles the dependency order automatically:

```
Stage 1 — sequential (guaranteed order):
  [1] test_letter_type_ingestion.py    → runs fully, writes ingested_letters.json
  [2] test_download_letter.py          → starts only after ingestion completes
  [3] test_generate_letter.py          → starts only after download completes
  [4] test_letter_type_detail_verify.py → starts only after generate completes

Stage 2 — parallel (4 workers):
  test_dashboard.py, test_approval_workflow.py, test_audit_logger.py,
  test_component_library.py, test_letter_control_center.py,
  test_navigation.py, test_settings.py, test_sanity.py ... all at once
```

At the end the script prints a pass/fail summary and the report locations.

**Script options:**

| Command | What it does |
|---|---|
| `.\run_tests.ps1` | Full run — Stage 1 then Stage 2 |
| `.\run_tests.ps1 -Stage 1` | Letter type chain only (sequential) |
| `.\run_tests.ps1 -Stage 2` | All other modules only (parallel) |
| `.\run_tests.ps1 -Workers 2` | Change parallel worker count (default 4) |

> **Why not just `-n 4` for everything?**  
> With parallel execution `ingested_letters.json` is wiped at run start and workers race — download or generate starts before ingestion finishes, finds an empty JSON, and fails. The two-stage script eliminates this race completely.

---

### Run everything sequentially (simple, always safe)

```powershell
pytest tests/ -p no:xdist -v
```

Use this for debugging or when you need a simple single command. Slower than the script because no parallelism, but guaranteed correct order via the `conftest.py` ordering hook.

### Run only the letter type chain

```powershell
pytest tests/test_letter_type_ingestion.py tests/test_download_letter.py tests/test_generate_letter.py tests/test_letter_type_detail_verify.py -p no:xdist -v
```

### Run a single test file

```powershell
pytest tests/test_dashboard.py -v
```

### Run a single test case

```powershell
pytest tests/test_dashboard.py::TestDashboard::test_dashboard_page_loads -v
```

### Headed browser (watch the browser while tests run)

Set `HEADLESS=false` in `.env`, then:

```powershell
.\run_tests.ps1
```

Or override inline for a quick single-file run:

```powershell
$env:HEADLESS="false"; pytest tests/test_letter_type.py -p no:xdist -v
```

### Slow-motion + headed (step-by-step debugging)

```powershell
$env:SLOW_MO="500"; $env:HEADLESS="false"; pytest tests/test_navigation.py -p no:xdist -v
```

### With Allure report generation

```powershell
# The script already writes allure results automatically.
# To view after any run:
allure serve reports/allure-results
```

---

## Test Suite

104 test cases across 19 files — all tagged `@pytest.mark.sanity`.

| File | TCs | What it validates |
|---|---|---|
| `test_letter_type_ingestion.py` | 2 | Ingests DOCX templates per BU (ANG, UM); saves `ingested_letters.json` |
| `test_download_letter.py` | 3 | Downloads PDF + DOCX per ingested letter; saves `downloaded_letters.json` |
| `test_generate_letter.py` | 3 | Generates letters via XML upload per BU; saves `generated_letters.json` |
| `test_letter_type_detail_verify.py` | 10 | Detail page fields, PDF preview, back navigation, search, BU filter scoping |
| `test_letter_type.py` | 4 | Listing loads, template upload + status polling (Processing→Draft), filter, download |
| `test_letter_type_details.py` | 5 | Details page, version dropdown, Make Current, Generate Test Letter, Validation Summary |
| `test_letter_type_editor.py` | 6 | Editor loads, Generate, Reset, Diff View, Preview renders, Submit for Approval |
| `test_sanity.py` | 8 | Environment reachability, login happy/sad path, listing smoke, session persistence |
| `test_dashboard.py` | 12 | Stat card counts vs API `statusSummary`; tab footer vs `totalRecords`; search |
| `test_letter_control_center.py` | 11 | Generated Letters page, filters, XML generation, status polling, PDF/DOCX download, bulk CSV, search, pagination, stats cards |
| `test_letter_consolidation.py` | 4 | Grouping, percentage change, representative, move docs _(all on HOLD — skipped)_ |
| `test_approval_workflow.py` | 7 | Pending/Approved/Rejected tabs, approve flow (Pending−1, Approved+1), reject flow, bulk approve button, refresh |
| `test_audit_logger.py` | 6 | Page load, audit entry present, field data, date filter, download report, pagination |
| `test_component_library.py` | 6 | Page access, Placeholder/Insert/Condition/Block tabs, sample file upload |
| `test_letter_import_export.py` | 4 | Page access, export ZIP, import _(skipped — pending artifact)_, admin access control |
| `test_navigation.py` | 1 | All 9 sidebar links open the correct page |
| `test_settings.py` | 2 | Global Configuration tab, Business Unit Config tab |
| `test_recon_report.py` | 1 | Page load, list visible, download report |
| `test_agentic.py` | 8 | AI visual assertions, self-healing selectors, autonomous agent navigation |

---

## Letter Type Dependency Chain

Four test files form a strict dependency chain and **must run in order**:

```
test_letter_type_ingestion.py
        ↓  produces ingested_letters.json
test_download_letter.py
        ↓  produces downloaded_letters.json
test_generate_letter.py
        ↓  produces generated_letters.json
test_letter_type_detail_verify.py
        ↓  reads ingested_letters.json
```

The `pytest_collection_modifyitems` hook in `conftest.py` automatically enforces this order whenever these files are collected. Always use `-p no:xdist` when running them to prevent parallel execution from breaking the dependency.

### Output files (wiped at the start of each run)

| File | Created by | Used by |
|---|---|---|
| `tests/testdata/ingested_letters.json` | ingestion | download, generate, detail_verify |
| `tests/testdata/downloaded_letters.json` | download | _(available for future compare tests)_ |
| `tests/testdata/generated_letters.json` | generate | _(available for future assertions)_ |
| `tests/downloaded/pdf_docx_downloads/` | download | local file assertions |
| `tests/downloaded/generated/` | generate | local file assertions |

### XML files for generation

BU-specific XML files live in `test_xml/`:

| BU | XML file |
|---|---|
| ANG | `test_xml/CA_Pega AnG (1).xml` |
| UM | `test_xml/UM-LTR-1778490508970463.xml` |

---

## Test Reports

### HTML report

Auto-generated at `reports/sanity_report.html` after every run.

```powershell
# Open in browser (Windows)
start reports\sanity_report.html
```

### Allure report

Raw results are written to `reports/allure-results/` on every run.

```powershell
# Serve interactively (opens browser automatically)
allure serve reports/allure-results

# Or generate a static site
allure generate reports/allure-results -o reports/allure-html --clean
allure open reports/allure-html
```

### Failure artifacts

| Artifact | Saved to | Trigger |
|---|---|---|
| Screenshot (full-page PNG) | `screenshots/` | `SCREENSHOT_ON_FAILURE=true` |
| Playwright trace (`.zip`) | `traces/` | `RECORD_TRACE=true`, failures only |
| Video (`.webm`) | `videos/` | `RECORD_VIDEO=true`, failures only |

Inspect a trace:

```powershell
playwright show-trace traces/<name>.zip
```

---

## Project Structure

```
AutoPythone2e/
│
├── .env                              # Local credentials & settings (gitignored)
├── .env.example                      # Template — copy to .env and fill in values
├── pytest.ini                        # pytest options: markers, reporters
│
├── config/
│   └── config.py                     # Central Config singleton (reads .env)
│
├── pages/                            # Page Object Models (one class per page)
│   ├── base_page.py                  # Common Playwright helpers + popup suppressor
│   ├── login_page.py                 # Login form with Keycloak OAuth retry logic
│   ├── letter_type_page.py           # Listing, configure upload, filter, download
│   ├── letter_type_details_page.py   # Detail view, versioning, generate, approve/reject
│   ├── letter_type_editor_page.py    # Rich-text editor, diff view, submit for approval
│   ├── dashboard_page.py             # Stat cards + API response interception
│   ├── nav_page.py                   # Sidebar navigation helper
│   ├── ask_auto_page.py
│   ├── audit_logger_page.py
│   ├── component_library_page.py
│   ├── letter_consolidation_page.py
│   ├── letter_control_center_page.py
│   ├── letter_import_export_page.py
│   ├── recon_report_page.py
│   └── settings_page.py
│
├── tests/
│   ├── conftest.py                   # Fixtures + pytest_collection_modifyitems ordering hook
│   ├── test_letter_type_ingestion.py # BU ingestion + ingested_letters.json
│   ├── test_download_letter.py       # PDF/DOCX download + downloaded_letters.json
│   ├── test_generate_letter.py       # XML-based generation + generated_letters.json
│   ├── test_letter_type_detail_verify.py  # Detail page assertions
│   ├── test_letter_type.py
│   ├── test_letter_type_details.py
│   ├── test_letter_type_editor.py
│   ├── test_sanity.py
│   ├── test_dashboard.py
│   ├── test_letter_control_center.py
│   ├── test_letter_consolidation.py
│   ├── test_approval_workflow.py
│   ├── test_audit_logger.py
│   ├── test_component_library.py
│   ├── test_letter_import_export.py
│   ├── test_navigation.py
│   ├── test_settings.py
│   ├── test_recon_report.py
│   └── test_agentic.py
│
├── test_xml/                         # BU-specific XML files for generation tests
│   ├── CA_Pega AnG (1).xml           # ANG business unit
│   └── UM-LTR-1778490508970463.xml   # UM business unit
│
├── tests/testdata/                   # JSON tracking files (generated at runtime)
│   ├── ingested_letters.json
│   ├── downloaded_letters.json
│   └── generated_letters.json
│
├── tests/downloaded/                 # Downloaded files (generated at runtime)
│   ├── pdf_docx_downloads/
│   └── generated/
│
├── utils/
│   └── logger.py                     # Structured logger (console INFO + file DEBUG)
│
└── reports/                          # Generated on every run (gitignored)
    ├── sanity_report.html
    ├── allure-results/
    ├── allure-html/
    ├── screenshots/
    ├── traces/
    ├── videos/
    └── .auth_state_master.json       # Serialised Playwright auth state
```

---

## Architecture

### Page Object Model

Every page has a dedicated class in `pages/`. Tests never contain selectors — they call named methods like `letter_type_page.apply_filter("Draft")`. A selector change means updating one file.

### Session-scoped authentication

`auth_state` in `conftest.py` logs in once per session, serialises the Playwright `storage_state` (cookies + `localStorage`) to `reports/.auth_state_master.json`, and reuses it for every test. No test re-logs in. The fixture retries login up to **3 times** to handle transient Keycloak OAuth redirect failures.

### Automatic test ordering

`pytest_collection_modifyitems` in `conftest.py` re-sorts any collected letter type files into dependency order before execution — even when pytest collects them alphabetically. No manual file ordering is needed.

### Ask Auto popup suppression

The app shows a floating chat popup that can intercept clicks. `BasePage` injects a `MutationObserver` script into every page before navigation that hides the popup the instant it appears without using `Escape` (which would close configure/filter panels).

---

## Troubleshooting

**`unrecognized arguments: -n --dist loadfile`**

The `-n` / `--dist` flags must not appear in `pytest.ini` `addopts`. They were removed. Use `.\run_tests.ps1` for the recommended two-stage run, or pass `-n 4 --dist loadfile` explicitly on the command line for non-chain modules only.

---

**`ingested_letters.json` is empty `[]` after the run**

You ran with `-n 4` (full parallel). With parallel execution all workers start simultaneously — download or generate finds an empty JSON because ingestion hasn't finished yet. Fix: use `.\run_tests.ps1` which runs the chain sequentially in Stage 1 before launching parallel Stage 2. Never use `-n 4` directly across the full test suite.

---

**"URL did not change after login"**

- Verify `APP_USERNAME` / `APP_PASSWORD` in `.env`.
- Run headed: `$env:HEADLESS="false"; pytest tests/test_sanity.py -p no:xdist -v`.
- The login fixture retries 3× with a 45 s timeout — check if the Keycloak server is reachable.

---

**Letter type chain tests fail with dependency errors**

Always run the chain without parallelism:

```powershell
pytest tests/test_letter_type_ingestion.py tests/test_download_letter.py tests/test_generate_letter.py tests/test_letter_type_detail_verify.py -p no:xdist -v
```

Or run the full suite with `-p no:xdist` — the ordering hook handles everything automatically.

---

**Configure upload / generation times out**

The server processes uploads asynchronously. The test polls every 2–3 s for up to 120 s. For slow environments increase timeouts in `.env`:

```ini
DEFAULT_TIMEOUT=60000
NAVIGATION_TIMEOUT=90000
```

---

**Validation Summary tab shows no cards**

The Validation Summary tab only renders after a test letter has been generated for the record. Run `test_generate_letter.py` first so generated letters exist in the system.

---

**Traces fill up disk space**

Traces for passing tests are deleted automatically. Only failures keep their trace. To disable tracing entirely:

```ini
RECORD_TRACE=false
```
