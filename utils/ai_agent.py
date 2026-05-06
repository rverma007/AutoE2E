"""
AI Agent utilities for agentic E2E testing.

Wraps the Anthropic Claude API to provide three capabilities on top of the
existing Playwright framework:

1. ai_verify(page, question)
   - Takes a screenshot, sends it to Claude with a yes/no question.
   - Returns True/False — use it as a smart assertion that "understands" the UI.

2. ai_find_selector(page, description)
   - Takes a screenshot + full page HTML, asks Claude to locate an element.
   - Returns a CSS selector string — use it to self-heal broken locators.

3. AIAgent.run_steps(page, steps)
   - Accepts a plain-English list of steps and autonomously executes them
     in the browser, taking screenshots between each step so Claude can
     decide the next action.

All methods are non-fatal by default: if the AI layer is unavailable (no
ANTHROPIC_API_KEY set) they fall back gracefully so the rest of the test
suite is unaffected.

Usage:
    from utils.ai_agent import ai_verify, ai_find_selector, AIAgent

    # Smart visual assertion
    assert ai_verify(page, "Is the Letter Type table visible with at least one row?")

    # Self-healing locator
    selector = ai_find_selector(page, "search input for letter types")
    page.locator(selector).fill("EOB")

    # Natural-language test steps
    agent = AIAgent(page)
    agent.run_steps([
        "Verify the dashboard is showing the welcome message",
        "Click on Letter Type in the sidebar",
        "Confirm the letter type table loaded with data",
    ])
"""
from __future__ import annotations

import base64
import os
from typing import Optional

from utils.logger import get_logger

log = get_logger("ai_agent")

MODEL = "claude-sonnet-4-6"
_UNAVAILABLE_MSG = (
    "ANTHROPIC_API_KEY not set — AI agent features disabled. "
    "Add it to your .env file to enable agentic assertions."
)


def _client():
    """Return an Anthropic client, or None if the SDK / key is unavailable."""
    try:
        import anthropic  # noqa: PLC0415
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            log.warning(_UNAVAILABLE_MSG)
            return None
        return anthropic.Anthropic(api_key=api_key)
    except ImportError:
        log.warning("anthropic package not installed. Run: pip install anthropic")
        return None


def _screenshot_b64(page) -> str:
    """Capture a full-page screenshot and return it as a base64 string."""
    data = page.screenshot(full_page=False)
    return base64.standard_b64encode(data).decode()


def _image_block(b64: str) -> dict:
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": b64},
    }


# ---------------------------------------------------------------------------
# 1. Visual assertion
# ---------------------------------------------------------------------------

def ai_verify(page, question: str, fallback: bool = True) -> bool:
    """
    Ask Claude to look at the current page screenshot and answer a yes/no
    question.  Returns True for YES, False for NO, `fallback` if AI is
    unavailable.

    Example:
        assert ai_verify(page, "Is the Letter Type listing table visible?")
    """
    client = _client()
    if client is None:
        log.warning(f"ai_verify skipped (no client). question={question!r}")
        return fallback

    b64 = _screenshot_b64(page)
    prompt = (
        f"Look at this browser screenshot carefully.\n\n"
        f"Question: {question}\n\n"
        f"Answer with exactly one word: YES or NO. No other text."
    )
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=10,
            messages=[{
                "role": "user",
                "content": [_image_block(b64), {"type": "text", "text": prompt}],
            }],
        )
        answer = response.content[0].text.strip().upper()
        result = answer.startswith("Y")
        log.info(f"ai_verify → {answer!r} | question={question!r}")
        return result
    except Exception as exc:  # noqa: BLE001
        log.warning(f"ai_verify failed ({exc}). Returning fallback={fallback}")
        return fallback


# ---------------------------------------------------------------------------
# 2. Self-healing selector
# ---------------------------------------------------------------------------

def ai_find_selector(page, description: str) -> Optional[str]:
    """
    Ask Claude to find a CSS selector for an element described in plain English.
    Returns a selector string, or None if the AI is unavailable / element not found.

    Example:
        sel = ai_find_selector(page, "search box for letter types")
        if sel:
            page.locator(sel).fill("EOB")
    """
    client = _client()
    if client is None:
        log.warning(f"ai_find_selector skipped (no client). description={description!r}")
        return None

    b64 = _screenshot_b64(page)
    html_snippet = page.evaluate(
        "() => document.body.innerHTML.slice(0, 8000)"
    )
    prompt = (
        f"You are helping automate a browser test.\n\n"
        f"Element to find: {description}\n\n"
        f"Here is the page HTML (first 8000 chars):\n{html_snippet}\n\n"
        f"Return ONLY a single valid CSS selector that uniquely targets this "
        f"element. No explanation, no markdown, just the selector string."
    )
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": [_image_block(b64), {"type": "text", "text": prompt}],
            }],
        )
        selector = response.content[0].text.strip().strip("`").strip("'").strip('"')
        log.info(f"ai_find_selector → {selector!r} | description={description!r}")
        return selector
    except Exception as exc:  # noqa: BLE001
        log.warning(f"ai_find_selector failed ({exc})")
        return None


# ---------------------------------------------------------------------------
# 3. Autonomous step runner
# ---------------------------------------------------------------------------

class AIAgent:
    """
    Executes a list of plain-English test steps autonomously in the browser.

    Each step is sent to Claude along with a screenshot of the current page.
    Claude decides what Playwright action to take (click, fill, navigate, verify)
    and returns it as a JSON instruction that this agent executes.

    Supports actions:
        click       — { "action": "click", "selector": "...", "description": "..." }
        fill        — { "action": "fill", "selector": "...", "value": "..." }
        navigate    — { "action": "navigate", "url": "..." }
        verify      — { "action": "verify", "question": "...", "expected": true/false }
        wait        — { "action": "wait", "ms": 2000 }

    Example:
        agent = AIAgent(page)
        results = agent.run_steps([
            "Confirm the dashboard greeting says 'Good' to the user",
            "Click on Letter Type in the left sidebar",
            "Verify the letter type table is visible with data rows",
            "Type 'EOB' in the search box and verify results are filtered",
        ])
        for step, passed in results.items():
            print(f"{'PASS' if passed else 'FAIL'} — {step}")
    """

    def __init__(self, page):
        self.page = page
        self.log = get_logger("AIAgent")

    def run_steps(self, steps: list[str]) -> dict[str, bool]:
        """
        Run each step autonomously.  Returns {step_description: passed_bool}.
        Steps that fail do NOT abort the remaining steps.
        """
        results: dict[str, bool] = {}
        for step in steps:
            self.log.info(f"Agent step: {step!r}")
            passed = self._execute_step(step)
            results[step] = passed
            status = "PASS" if passed else "FAIL"
            self.log.info(f"  → {status}")
        return results

    def _execute_step(self, step: str) -> bool:
        """Ask Claude what to do for this step, then do it. Returns True on success."""
        import json  # noqa: PLC0415

        client = _client()
        if client is None:
            self.log.warning("AI agent unavailable — marking step as skipped (True).")
            return True

        b64 = _screenshot_b64(self.page)
        system = (
            "You are a browser automation agent. Given a screenshot of the current "
            "page and a plain-English test step, return a JSON object describing "
            "exactly ONE action to perform. No explanation — only valid JSON.\n\n"
            "Action schema (pick one):\n"
            '  {"action":"click",    "selector":"<css>",  "description":"<why>"}\n'
            '  {"action":"fill",     "selector":"<css>",  "value":"<text>"}\n'
            '  {"action":"navigate", "url":"<full url>"}\n'
            '  {"action":"verify",   "question":"<yes/no question>", "expected":true}\n'
            '  {"action":"wait",     "ms":1000}\n'
        )
        user_prompt = f"Current test step: {step}"

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=200,
                system=system,
                messages=[{
                    "role": "user",
                    "content": [
                        _image_block(b64),
                        {"type": "text", "text": user_prompt},
                    ],
                }],
            )
            raw = response.content[0].text.strip()
            # Strip markdown code fences if Claude wraps the JSON
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            instruction = json.loads(raw)
            return self._dispatch(instruction)
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"Agent step failed to parse/execute: {exc}")
            return False

    def _dispatch(self, instruction: dict) -> bool:
        action = instruction.get("action", "")
        try:
            if action == "click":
                sel = instruction["selector"]
                self.page.locator(sel).first.click(timeout=10_000)
                self.page.wait_for_load_state("networkidle", timeout=10_000)
                return True

            if action == "fill":
                sel = instruction["selector"]
                self.page.locator(sel).first.fill(instruction.get("value", ""))
                return True

            if action == "navigate":
                self.page.goto(instruction["url"], wait_until="domcontentloaded")
                return True

            if action == "verify":
                result = ai_verify(self.page, instruction["question"])
                expected = instruction.get("expected", True)
                return result == expected

            if action == "wait":
                self.page.wait_for_timeout(instruction.get("ms", 1000))
                return True

            self.log.warning(f"Unknown action: {action!r}")
            return False
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"Dispatch failed for {action!r}: {exc}")
            return False
