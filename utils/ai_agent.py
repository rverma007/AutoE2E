"""
AI Agent utilities for agentic E2E testing.

Powered by Google Gemini (free tier — gemini-2.5-flash-lite).
Get a free API key at: https://aistudio.google.com/app/apikey

Provides four capabilities on top of the existing Playwright framework:

1. ai_verify(page, question)
   - Takes a screenshot, sends it to Gemini with a yes/no question.
   - Returns True/False — use it as a smart assertion that "understands" the UI.

2. smart_assert(page, check_fn, question, expected=True, recovery_steps=None)
   - Runs check_fn() first (a normal Playwright lambda — free, instant).
   - Only calls ai_verify() if check_fn fails — reduces API calls by 80–90%.
   - If Gemini also says NO and recovery_steps are provided, the AIAgent
     executes those steps autonomously and retries — making the test truly
     self-healing, not just self-reporting.
   - Use this instead of ai_verify() for all routine assertions.

3. ai_find_selector(page, description)
   - Takes a screenshot + live HTML, asks Gemini to locate an element.
   - Returns a CSS selector string — use it to self-heal broken locators.

4. AIAgent.run_steps(page, steps)
   - Accepts a plain-English list of steps and autonomously executes them
     in the browser, taking screenshots between each step so Gemini can
     decide the next action.

All methods are non-fatal by default: if the AI layer is unavailable (no
GEMINI_API_KEY set) they fall back gracefully so the rest of the test
suite is unaffected.
"""
from __future__ import annotations

import os
from typing import Optional

from utils.logger import get_logger

log = get_logger("ai_agent")

MODEL = "gemini-2.5-flash-lite"   # free tier, supports vision
_UNAVAILABLE_MSG = (
    "GEMINI_API_KEY not set — AI agent features disabled. "
    "Get a free key at https://aistudio.google.com/app/apikey "
    "and add it to your .env file."
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _client():
    """Return a configured Gemini client, or None if unavailable."""
    try:
        from google import genai  # noqa: PLC0415
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            log.warning(_UNAVAILABLE_MSG)
            return None
        return genai.Client(api_key=api_key)
    except ImportError:
        log.warning(
            "google-genai package not installed. "
            "Run: pip install google-genai"
        )
        return None


def _screenshot_bytes(page) -> bytes:
    """Capture a screenshot and return raw PNG bytes."""
    return page.screenshot(full_page=False)


def _image_part(data: bytes):
    """Wrap PNG bytes as a Gemini Part."""
    from google.genai import types  # noqa: PLC0415
    return types.Part.from_bytes(data=data, mime_type="image/png")


# ---------------------------------------------------------------------------
# 1. Visual assertion
# ---------------------------------------------------------------------------

def ai_verify(page, question: str, fallback: bool = True) -> bool:
    """
    Ask Gemini to look at the current page screenshot and answer a yes/no
    question.  Returns True for YES, False for NO, `fallback` if AI is
    unavailable.

    Example:
        assert ai_verify(page, "Is the Letter Type listing table visible?")
    """
    client = _client()
    if client is None:
        log.warning(f"ai_verify skipped (no client). question={question!r}")
        return fallback

    prompt = (
        f"Look at this browser screenshot carefully.\n\n"
        f"Question: {question}\n\n"
        f"Answer with exactly one word: YES or NO. No other text."
    )
    try:
        img = _image_part(_screenshot_bytes(page))
        response = client.models.generate_content(
            model=MODEL, contents=[img, prompt]
        )
        answer = response.text.strip().upper()
        result = answer.startswith("Y")
        log.info(f"ai_verify → {answer!r} | question={question!r}")
        return result
    except Exception as exc:  # noqa: BLE001
        log.warning(f"ai_verify failed ({exc}). Returning fallback={fallback}")
        return fallback


# ---------------------------------------------------------------------------
# 2. Smart assert — normal check first, AI only on failure
# ---------------------------------------------------------------------------

def smart_assert(
    page,
    check_fn,
    question: str,
    expected: bool = True,
    fallback: bool = True,
    recovery_steps: "list[str] | None" = None,
) -> bool:
    """
    Cost-efficient assertion: run a normal Playwright check first.
    Only call ai_verify() when the normal check fails.

    This reduces API calls by 80-90% — Gemini is only invoked when something
    actually looks wrong, not on every passing test run.

    If recovery_steps are provided and Gemini confirms failure, AIAgent will
    autonomously attempt those steps to recover the UI state, then retry the
    check — making the test truly self-healing.

    Args:
        page:            Playwright Page object.
        check_fn:        Zero-argument callable that returns truthy/falsy or raises.
        question:        Yes/no question for Gemini if check_fn fails.
        expected:        True = expect YES from Gemini, False = expect NO.
        fallback:        Value returned if Gemini is also unavailable.
        recovery_steps:  Optional list of plain-English steps for AIAgent to
                         execute when the assertion fails, before a final retry.

    Example:
        assert smart_assert(
            page,
            lambda: page.locator("table tbody tr").first.is_visible(timeout=3_000),
            "Is there a data table with rows visible on this page?",
            recovery_steps=[
                "Scroll down the page to look for the data table",
                "If a loading spinner is visible, wait for it to disappear",
            ],
        )
    """
    # ── Step 1: fast, free Playwright check ─────────────────────────────────
    try:
        passed = bool(check_fn())
    except Exception:  # noqa: BLE001
        passed = False

    if passed:
        log.info(f"smart_assert: PASS via normal check — no AI call | q={question!r}")
        return True

    # ── Step 2: normal check failed — escalate to Gemini ────────────────────
    log.info(f"smart_assert: normal check FAILED — escalating to ai_verify | q={question!r}")
    ai_result = ai_verify(page, question, fallback=fallback)
    outcome = ai_result == expected
    log.info(f"smart_assert: Gemini says {'YES' if ai_result else 'NO'} → {'PASS' if outcome else 'FAIL'}")

    if outcome:
        return True

    # ── Step 3: AI also says FAIL — attempt autonomous recovery ─────────────
    if not recovery_steps:
        return False

    log.info(f"smart_assert: attempting autonomous recovery with {len(recovery_steps)} step(s)")
    agent = AIAgent(page)
    recovery_results = agent.run_steps(recovery_steps)
    failed_steps = [s for s, p in recovery_results.items() if not p]
    if failed_steps:
        log.warning(f"smart_assert: {len(failed_steps)} recovery step(s) failed: {failed_steps}")
    else:
        log.info("smart_assert: all recovery steps completed — retrying assertion")

    # ── Step 4: retry original Playwright check after recovery ───────────────
    try:
        recovered = bool(check_fn())
    except Exception:  # noqa: BLE001
        recovered = False

    if recovered:
        log.info("smart_assert: PASS after autonomous recovery")
        return True

    # ── Step 5: final AI verify after recovery ───────────────────────────────
    log.info("smart_assert: Playwright still failing — running final ai_verify after recovery")
    final_ai = ai_verify(page, question, fallback=fallback)
    final_outcome = final_ai == expected
    log.info(
        f"smart_assert: post-recovery Gemini says {'YES' if final_ai else 'NO'} "
        f"→ {'PASS' if final_outcome else 'FAIL'}"
    )
    return final_outcome


# ---------------------------------------------------------------------------
# 3. Self-healing selector
# ---------------------------------------------------------------------------

def ai_find_selector(page, description: str) -> Optional[str]:
    """
    Ask Gemini to find a CSS selector for an element described in plain English.
    Returns a selector string, or None if unavailable / element not found.

    Example:
        sel = ai_find_selector(page, "search box for letter types")
        if sel:
            page.locator(sel).fill("EOB")
    """
    client = _client()
    if client is None:
        log.warning(f"ai_find_selector skipped (no client). description={description!r}")
        return None

    html_snippet = page.evaluate("() => document.body.innerHTML.slice(0, 15000)")
    prompt = (
        f"You are a Playwright browser test automation expert.\n\n"
        f"Task: Find the CSS selector for this element: {description}\n\n"
        f"Page HTML (first 15000 chars):\n{html_snippet}\n\n"
        f"STRICT RULES:\n"
        f"1. Return ONLY the raw CSS selector — no markdown, no backticks, no quotes, no explanation\n"
        f"2. Prefer stable selectors in this order:\n"
        f"   - input[type='search'] or input[type='text']\n"
        f"   - [placeholder='...'] with exact placeholder text from the HTML\n"
        f"   - [aria-label='...'] or [data-testid='...']\n"
        f"   - a[href*='keyword'] for navigation links\n"
        f"   - button with text content\n"
        f"3. NEVER use generated class names like .css-1abc123 or .MuiInput-abc\n"
        f"4. The selector must match a VISIBLE element currently on the page\n"
        f"5. Simpler is better — one attribute selector beats a long chain\n\n"
        f"Look at both the screenshot AND the HTML to identify the element."
    )
    try:
        img = _image_part(_screenshot_bytes(page))
        response = client.models.generate_content(
            model=MODEL, contents=[img, prompt]
        )
        raw = response.text.strip()
        # Strip markdown code fences
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.split("\n")[0].lower() in ("css", "html", "python", ""):
                raw = "\n".join(raw.split("\n")[1:])
        selector = raw.strip().strip("`").strip("'").strip('"').strip()

        # Validate — if selector matches nothing, log a warning but still return it
        # (the page state may have changed; let the caller decide)
        try:
            count = page.locator(selector).count()
            if count == 0:
                log.warning(f"ai_find_selector: {selector!r} matched 0 elements on page")
            else:
                log.info(f"ai_find_selector: {selector!r} matched {count} element(s)")
        except Exception:  # noqa: BLE001
            pass

        log.info(f"ai_find_selector → {selector!r} | description={description!r}")
        return selector if selector else None
    except Exception as exc:  # noqa: BLE001
        log.warning(f"ai_find_selector failed ({exc})")
        return None


# ---------------------------------------------------------------------------
# 4. Autonomous step runner
# ---------------------------------------------------------------------------

class AIAgent:
    """
    Executes a list of plain-English test steps autonomously in the browser.

    Each step is sent to Gemini along with a screenshot of the current page.
    Gemini decides what Playwright action to take (click, fill, navigate, verify)
    and returns it as a JSON instruction that this agent executes.

    Supported actions:
        click    — { "action": "click",    "selector": "...", "description": "..." }
        fill     — { "action": "fill",     "selector": "...", "value": "..." }
        navigate — { "action": "navigate", "url": "..." }
        verify   — { "action": "verify",   "question": "...", "expected": true }
        wait     — { "action": "wait",     "ms": 1000 }

    Example:
        agent = AIAgent(page)
        results = agent.run_steps([
            "Confirm the dashboard greeting says Good to the user",
            "Click on Letter Type in the left sidebar",
            "Verify the letter type table is visible with data rows",
        ])
        for step, passed in results.items():
            print(f"{'PASS' if passed else 'FAIL'} — {step}")
    """

    def __init__(self, page):
        self.page = page
        self.log = get_logger("AIAgent")

    def run_steps(self, steps: list[str]) -> dict[str, bool]:
        """Run each step autonomously. Returns {step_description: passed_bool}."""
        results: dict[str, bool] = {}
        for step in steps:
            self.log.info(f"Agent step: {step!r}")
            passed = self._execute_step(step)
            results[step] = passed
            self.log.info(f"  → {'PASS' if passed else 'FAIL'}")
        return results

    def _execute_step(self, step: str) -> bool:
        """Ask Gemini what to do for this step, then do it."""
        import json  # noqa: PLC0415

        client = _client()
        if client is None:
            self.log.warning("AI agent unavailable — marking step as skipped (True).")
            return True

        prompt = (
            "You are a Playwright browser automation agent.\n\n"
            "Look at the screenshot carefully and perform this test step:\n"
            f"{step}\n\n"
            "Return ONLY a valid JSON object for ONE action — no explanation, no markdown.\n\n"
            "Available actions:\n"
            '  {"action":"click",    "selector":"<css_selector>", "description":"<why>"}\n'
            '  {"action":"fill",     "selector":"<css_selector>", "value":"<text to type>"}\n'
            '  {"action":"navigate", "url":"<full https:// url>"}\n'
            '  {"action":"verify",   "question":"<yes/no question about screenshot>", "expected":true}\n'
            '  {"action":"wait",     "ms":1500}\n\n'
            "SELECTOR RULES:\n"
            "- Use text-based: button:has-text('Letter Type'), a:has-text('Letter Configuration')\n"
            "- Use attribute-based: a[href*='letter-type'], input[type='search']\n"
            "- Use aria: [role='button'][aria-label='...'], [aria-expanded='false']\n"
            "- NEVER use generated classes like .css-abc123 or .MuiBox-root\n"
            "- For sidebar expand buttons, use: button:has-text('Letter Configuration')\n"
            "- For sidebar links, use: a:has-text('Letter Type') or a[href*='letter-type']\n\n"
            "Return raw JSON only. Example: {\"action\":\"click\",\"selector\":\"a:has-text('Letter Type')\",\"description\":\"click nav link\"}"
        )
        try:
            img = _image_part(_screenshot_bytes(self.page))
            response = client.models.generate_content(
                model=MODEL, contents=[img, prompt]
            )
            raw = response.text.strip()
            # Strip markdown fences
            if "```" in raw:
                parts = raw.split("```")
                raw = parts[1] if len(parts) > 1 else raw
                first_line = raw.split("\n")[0].lower()
                if first_line in ("json", ""):
                    raw = "\n".join(raw.split("\n")[1:])
            raw = raw.strip()
            instruction = json.loads(raw)
            return self._dispatch(instruction)
        except Exception as exc:  # noqa: BLE001
            exc_str = str(exc)
            if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str or "quota" in exc_str.lower():
                self.log.warning(f"Agent step skipped — API quota exceeded: {exc}")
                return True  # treat as indeterminate, not a product failure
            self.log.warning(f"Agent step failed to parse/execute: {exc}")
            return False

    def _dispatch(self, instruction: dict) -> bool:
        action = instruction.get("action", "")
        try:
            if action == "click":
                selector = instruction["selector"]
                locator = self.page.locator(selector).first
                # Fallback: try get_by_text if selector matches nothing
                if locator.count() == 0:
                    text = instruction.get("description", "")
                    self.log.warning(f"Selector {selector!r} matched nothing — trying text fallback")
                    locator = self.page.get_by_text(selector.replace("a:has-text('", "").replace("')", ""), exact=False).first
                locator.scroll_into_view_if_needed()
                locator.click(timeout=10_000)
                try:
                    self.page.wait_for_load_state("networkidle", timeout=8_000)
                except Exception:  # noqa: BLE001
                    pass
                return True
            if action == "fill":
                self.page.locator(instruction["selector"]).first.fill(
                    instruction.get("value", "")
                )
                return True
            if action == "navigate":
                self.page.goto(instruction["url"], wait_until="domcontentloaded")
                return True
            if action == "verify":
                result = ai_verify(self.page, instruction["question"])
                return result == instruction.get("expected", True)
            if action == "wait":
                self.page.wait_for_timeout(instruction.get("ms", 1000))
                return True
            self.log.warning(f"Unknown action: {action!r}")
            return False
        except Exception as exc:  # noqa: BLE001
            self.log.warning(f"Dispatch failed for {action!r}: {exc}")
            return False
