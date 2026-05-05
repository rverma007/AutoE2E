# AutoPythone2e — common development and CI commands
#
# Usage:
#   make install          Install all dependencies + Playwright browser
#   make sanity           Run fast sanity tests (4 parallel workers)
#   make slow             Run slow tests (upload polling, etc.)
#   make regression       Run the full test suite
#   make headed           Run sanity tests with a visible browser (single worker)
#   make debug            Run with a visible browser + 500 ms slow-motion
#   make report           Open the Allure interactive report
#   make clean            Delete all generated artifacts
#
# Overrides:
#   make sanity WORKERS=8
#   make sanity BROWSER=firefox
#   make sanity WORKERS=1 HEADLESS=false

WORKERS  ?= 4
BROWSER  ?= chromium
HEADLESS ?= true

# ── Setup ────────────────────────────────────────────────────────────────────
.PHONY: install
install:
	pip install -r requirements.txt
	playwright install $(BROWSER)

.PHONY: install-all-browsers
install-all-browsers:
	pip install -r requirements.txt
	playwright install

# ── Test suites ──────────────────────────────────────────────────────────────
.PHONY: sanity
sanity:
	PYTEST_WORKERS=$(WORKERS) BROWSER=$(BROWSER) HEADLESS=$(HEADLESS) \
	  pytest -m "sanity and not slow" -n $(WORKERS) --dist loadfile

.PHONY: slow
slow:
	BROWSER=$(BROWSER) HEADLESS=$(HEADLESS) \
	  pytest -m slow -n 2 --dist loadfile

.PHONY: regression
regression:
	PYTEST_WORKERS=$(WORKERS) BROWSER=$(BROWSER) HEADLESS=$(HEADLESS) \
	  pytest -n $(WORKERS) --dist loadfile

# ── Debugging ────────────────────────────────────────────────────────────────
.PHONY: headed
headed:
	HEADLESS=false pytest -m "sanity and not slow" -p no:xdist -v

.PHONY: debug
debug:
	HEADLESS=false SLOW_MO=500 pytest -m "sanity and not slow" -p no:xdist -v -s

# ── Single file / test ────────────────────────────────────────────────────────
# Usage: make file FILE=tests/test_navigation.py
.PHONY: file
file:
	HEADLESS=$(HEADLESS) pytest $(FILE) -p no:xdist -v

# ── Reporting ─────────────────────────────────────────────────────────────────
.PHONY: report
report:
	allure serve reports/allure-results

.PHONY: report-build
report-build:
	allure generate reports/allure-results -o reports/allure-html --clean
	allure open reports/allure-html

.PHONY: open-html
open-html:
	python -c "import webbrowser, pathlib; webbrowser.open(pathlib.Path('reports/sanity_report.html').resolve().as_uri())"

# ── Cleanup ───────────────────────────────────────────────────────────────────
.PHONY: clean
clean:
	rm -rf reports/ screenshots/ traces/ videos/ .pytest_cache/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
