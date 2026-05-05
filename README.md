# AutoPythone2e

End-to-end test suite for the **Correspondence Application** (LettersHub), built with [Playwright](https://playwright.dev/python/) and [pytest](https://pytest.org/).

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Prerequisites](#prerequisites)
4. [Setup](#setup)
5. [Configuration](#configuration)
6. [Running Tests](#running-tests)
7. [Test Reports](#test-reports)
8. [Project Structure](#project-structure)
9. [Architecture](#architecture)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The suite covers the full post-login surface of the Correspondence app:

| Test File | What it validates |
|---|---|
| `test_sanity.py` | Environment reachability, login happy/sad path, session persistence |
| `test_dashboard.py` | Stat card counts match the API; tab footer counts match `totalRecords` |
| `test_letter_type.py` | Listing loads, template upload + status polling, filter, download |
| `test_navigation.py` | Every sidebar link opens the correct page |

All tests are tagged `@pytest.mark.sanity` so the full smoke suite runs with a single command.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Browser automation | Playwright (sync API) `>=1.40` |
| Test runner | pytest `>=7.0` |
| Parallel execution | pytest-xdist `>=3.0` |
| HTML reports | pytest-html `>=4.0` |
| Rich reports | allure-pytest `>=2.13` |

---

## Prerequisites

- **Python 3.10+**
- **pip** (comes with Python)
- **Allure CLI** (optional, only to view Allure reports):
  ```bash
  npm install -g allure-commandline
  ```

---

## Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd AutoPythone2e

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Copy the env template and fill in your credentials
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
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
| `SLOW_MO` | `0` | Milliseconds added between Playwright actions (debugging aid) |
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

Parallelism is controlled by the `PYTEST_WORKERS` environment variable or the `-n` flag.
Neither is hardcoded — you choose the right value for your machine.

---

### Sanity suite (recommended — skips slow upload test)

**Windows PowerShell**
```powershell
$env:PYTEST_WORKERS=4; pytest -m "sanity and not slow"
```

**Windows CMD**
```cmd
set PYTEST_WORKERS=4 && pytest -m "sanity and not slow"
```

**macOS / Linux / Git Bash**
```bash
PYTEST_WORKERS=4 pytest -m "sanity and not slow"
```

**Via Makefile (macOS / Linux / Git Bash)**
```bash
make sanity             # 4 workers, chromium, headless
make sanity WORKERS=2   # 2 workers
```

---

### Full sanity suite (includes slow upload-polling test)

```powershell
# Windows PowerShell
$env:PYTEST_WORKERS=4; pytest -m sanity
```
```bash
# macOS / Linux
PYTEST_WORKERS=4 pytest -m sanity
```

> **Note:** The upload test polls the server for up to 120 s. Run it separately
> when you specifically need to verify template upload behaviour:
> ```bash
> pytest -m slow -n 2 --dist loadfile
> ```

---

### Single test file

```powershell
# Windows PowerShell
pytest tests/test_letter_type.py -v
```
```bash
# macOS / Linux
pytest tests/test_letter_type.py -v
```

With parallelism:
```powershell
$env:PYTEST_WORKERS=2; pytest tests/test_letter_type.py
```

---

### Single test case

```bash
pytest tests/test_letter_type.py::TestLetterTypeConfiguration::test_configure_letter_type_upload -v
pytest tests/test_sanity.py::TestAuthentication::test_login_with_valid_credentials -v
pytest tests/test_navigation.py::TestNavigation::test_all_nav_pages_load -v
pytest tests/test_dashboard.py::TestDashboard::test_stat_cards_match_api_status_summary -v
```

---

### By marker

```bash
pytest -m sanity                  # all smoke tests (includes slow)
pytest -m "sanity and not slow"   # fast smoke tests only (recommended for CI / quick checks)
pytest -m slow                    # upload-polling tests only
pytest -m regression              # full regression suite
```

---

### No parallelism — best for debugging

```bash
pytest -p no:xdist -v
```

---

### Headed browser (watch the browser while tests run)

**Windows PowerShell**
```powershell
$env:HEADLESS="false"; pytest -m "sanity and not slow" -p no:xdist -v
```

**macOS / Linux**
```bash
HEADLESS=false pytest -m "sanity and not slow" -p no:xdist -v
```

**Via Makefile**
```bash
make headed
```

---

### Different browser

**Windows PowerShell**
```powershell
$env:PYTEST_WORKERS=4; pytest -m "sanity and not slow" --browser-override firefox
$env:PYTEST_WORKERS=4; pytest -m "sanity and not slow" --browser-override webkit
```

**macOS / Linux**
```bash
PYTEST_WORKERS=4 pytest -m "sanity and not slow" --browser-override firefox
```

**Via Makefile**
```bash
make sanity BROWSER=firefox
```

---

### Slow-motion + headed (step-by-step debugging)

**Windows PowerShell**
```powershell
$env:HEADLESS="false"; $env:SLOW_MO="500"; pytest tests/test_navigation.py -p no:xdist -v -s
```

**macOS / Linux**
```bash
HEADLESS=false SLOW_MO=500 pytest tests/test_navigation.py -p no:xdist -v -s
```

**Via Makefile**
```bash
make debug
```

---

## Test Reports

### HTML report

Auto-generated at `reports/sanity_report.html` after every run.

```bash
# Windows
start reports\sanity_report.html
# macOS
open reports/sanity_report.html
```

### Allure report

Raw results are written to `reports/allure-results/` on every run.

```bash
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

```bash
playwright show-trace traces/<name>.zip
```

---

## Project Structure

```
AutoPythone2e/
│
├── .env                         # Local credentials & settings (gitignored)
├── .env.example                 # Template — copy to .env and fill in values
├── pytest.ini                   # pytest options: markers, reporters, xdist
│
├── config/
│   └── config.py                # Central Config singleton (reads .env)
│
├── pages/                       # Page Object Models (one class per page)
│   ├── base_page.py             # Common Playwright helpers + popup suppressor
│   ├── login_page.py            # Login form with Keycloak OAuth retry logic
│   ├── letter_type_page.py      # Listing, configure upload, filter, download
│   ├── dashboard_page.py        # Stat cards + API response interception
│   ├── nav_page.py              # Sidebar navigation helper
│   ├── ask_auto_page.py
│   ├── audit_logger_page.py
│   ├── component_library_page.py
│   ├── letter_consolidation_page.py
│   ├── letter_control_center_page.py
│   ├── recon_report_page.py
│   └── settings_page.py
│
├── tests/
│   ├── conftest.py              # Fixtures: browser, auth state, page objects
│   ├── test_sanity.py           # Environment health + authentication tests
│   ├── test_dashboard.py        # Dashboard stat cards vs API
│   ├── test_letter_type.py      # Letter Type CRUD + upload flow
│   └── test_navigation.py       # Full sidebar walk-through
│
├── utils/
│   └── logger.py                # Structured logger (console INFO + file DEBUG)
│
└── reports/                     # Generated on every run (gitignored)
    ├── sanity_report.html
    ├── allure-results/
    ├── .auth_state_gw*.json     # Per-worker auth storage state
    └── run_*.log                # Execution logs with timestamps
```

---

## Architecture

### Page Object Model

Every page has a class in `pages/`. Tests never contain selectors — they call named methods like `letter_type_page.apply_filter("Draft")`. A selector change means updating one file.

### Session-scoped authentication

`auth_state` (in `tests/conftest.py`) logs in once per xdist worker, serialises the Playwright `storage_state` (cookies + `localStorage`) to `reports/.auth_state_<worker>.json`, and reuses it for every test in that session. No test re-logs in.

The fixture retries the login up to **3 times** to handle transient Keycloak OAuth redirect failures that happen when multiple workers hit the auth server simultaneously.

### Ask Auto popup suppression

The app shows a chat popup that can block clicks. `BasePage` injects a `MutationObserver` + `setInterval` script into every page before navigation. The script hides the popup the instant it appears — never using `Escape` (which would also close configure/filter panels).

### Parallel execution strategy

`pytest.ini` uses `--dist loadfile` so all tests from the same file run on the same worker. This prevents cross-worker interference on shared state (e.g. letter-type list ordering after an upload).

---

## Troubleshooting

**"URL did not change after login"**

The Keycloak OAuth redirect can be slow on shared environments. The login already retries 3× with a 45 s timeout. Additional steps:

- Verify `APP_USERNAME` / `APP_PASSWORD` in `.env`.
- Run headed: `HEADLESS=false pytest -p no:xdist -v`.
- Drop to one worker: `pytest -n 1`.

---

**Configure upload test times out**

The server processes uploaded templates asynchronously. The test polls every 2 s for up to **120 s**. For consistently slow environments, increase timeouts in `.env`:

```ini
DEFAULT_TIMEOUT=60000
NAVIGATION_TIMEOUT=90000
```

---

**Download button stays disabled**

The Download button requires at least one qualifying letter type in the system. On a fresh or empty database it stays disabled. The test handles this gracefully — it passes after noting the button state without asserting that a file was downloaded.

---

**Navigation test fails on a specific page**

Each `is_loaded()` method first looks for a page-specific heading (15 s), then falls back to checking that `page.url` contains the expected path. If a heading text changed in a UI update, the URL check keeps the test green. To fix permanently, update the `has_text=` value in the relevant page object in `pages/`.

---

**Dashboard stat card counts do not match the API**

The page object tries multiple CSS selector strategies (primary Tailwind classes → positional fallbacks). If all fail, update `_COUNT_SELECTORS` in `pages/dashboard_page.py` to match the current DOM class names. Use browser DevTools → Inspect on a stat card to find the correct selector.

---

**Traces fill up disk space**

Traces for passing tests are deleted automatically. Only failures keep their trace. To disable tracing entirely:

```ini
RECORD_TRACE=false
```
