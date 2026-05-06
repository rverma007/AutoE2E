# Agentic Testing with Claude AI

## What Is Agentic Testing?

Traditional E2E tests are **fixed scripts** — they execute the exact steps you coded, using hardcoded selectors like `input[placeholder='Search...']`. When the UI changes, the test breaks.

**Agentic testing** adds an AI layer (Claude) that can:
- **See** the page like a human (via screenshots)
- **Understand** the UI visually, not just by selectors
- **Decide** what action to take from a plain-English instruction
- **Recover** when selectors break, by finding new ones from the live DOM

---

## Three Levels Implemented in This Framework

### Level 1 — Visual Assertions (`ai_verify`)

Claude looks at a screenshot and answers a yes/no question about the UI.

```python
# Traditional assertion — breaks if selector changes
assert page.locator("table tbody tr").count() > 0

# AI assertion — works regardless of DOM structure
assert ai_verify(page, "Is the letter type table visible with data rows?")
```

**When to use:** Verifying layout, visual states, error banners, empty states — anything a human would check by looking at the screen.

---

### Level 2 — Self-Healing Selectors (`ai_find_selector`)

When a selector breaks because a developer renamed a CSS class or changed a placeholder, Claude inspects the live DOM and returns a working selector.

```python
# Hardcoded selector — breaks when placeholder text changes
search = page.locator("input[placeholder='Search by Letter Type, Id and External Id']")

# Self-healing — Claude finds it from the live page
selector = ai_find_selector(page, "search input for filtering letter types")
search = page.locator(selector)
```

**When to use:** After UI refactors, when running tests against multiple environments with slightly different markup.

---

### Level 3 — Autonomous Agent (`AIAgent.run_steps`)

The agent receives plain-English steps. Claude decides what browser action to take (click, fill, navigate, verify) by looking at a screenshot between each step.

```python
agent = AIAgent(page)
results = agent.run_steps([
    "Verify the dashboard has loaded with a welcome message",
    "Click on Letter Configuration in the left sidebar",
    "Click on Letter Type",
    "Verify the letter type table is visible with data",
])
```

**When to use:** Exploratory testing, regression checks written by business analysts, testing flows that change frequently.

---

## How to Run

### Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Add your Anthropic API key to .env
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your API key at: https://console.anthropic.com/

### Run only agentic tests

```bash
pytest -m agentic -v -s
```

### Run a single test

```bash
pytest tests/test_agentic.py::TestAIVisualAssertions::test_ai_letter_type_table_visible -v -s
```

### Run everything (sanity + agentic)

```bash
pytest -m "sanity or agentic" -v
```

---

## Without an API Key

All agentic tests **skip gracefully** if `ANTHROPIC_API_KEY` is not set. The regular sanity suite is never blocked.

---

## File Structure

```
utils/
  ai_agent.py          ← Core AI helpers (ai_verify, ai_find_selector, AIAgent)

tests/
  test_agentic.py      ← Showcase test suite (Level 1, 2, 3)

docs/
  AGENTIC_TESTING.md   ← This file
```

---

## Value for the Team

| Problem | Traditional Fix | Agentic Fix |
|---|---|---|
| Selector breaks after UI change | QA manually fixes selector | AI finds new selector automatically |
| New feature needs test coverage | QA writes full script | Describe feature in English, agent writes steps |
| Visual regression (layout, empty state) | Screenshot diff tools | `ai_verify` understands context |
| Non-technical stakeholder wants to add test | Not possible | Plain English → agent executes |

---

## Architecture

```
Test (.py)
    │
    ├── Page Object (existing Playwright code)
    │       └── Stable, deterministic steps
    │
    └── AI Agent (Claude via Anthropic API)
            ├── ai_verify()        → screenshot → Claude → True/False
            ├── ai_find_selector() → screenshot + DOM → Claude → CSS selector
            └── AIAgent.run_steps() → screenshot per step → Claude → action → execute
```

The AI layer sits **on top of** the existing framework — nothing is replaced, only enhanced.
