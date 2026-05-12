// Agentic E2E Testing — PowerPoint Generator
// Run: node docs/build_pptx.js
// Output: docs/Agentic_Testing_Demo_v2.pptx

const pptxgen = require("pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Lead QA Engineer — EX Squared";
pres.title = "Agentic E2E Testing with Gemini AI";

// ── Palette ──────────────────────────────────────────────────────────────────
const C = {
  navy:    "0D1B4B",
  teal:    "028090",
  mint:    "02C39A",
  white:   "FFFFFF",
  offWhite:"F0F6FA",
  silver:  "B0C4D4",
  dark:    "0A1628",
  card:    "112255",
  codeBox: "0A1F3D",
  red:     "E05C5C",
  green:   "02C39A",
  yellow:  "F5C842",
};

const FONT_TITLE = "Calibri";
const FONT_BODY  = "Calibri";
const W = 10, H = 5.625;

// ── Helpers ──────────────────────────────────────────────────────────────────
function makeShadow() {
  return { type: "outer", color: "000000", blur: 10, offset: 3, angle: 135, opacity: 0.25 };
}

function addSlideHeader(slide, title, subtitle) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W, h: 0.07, fill: { color: C.mint }, line: { color: C.mint }
  });
  slide.addText(title, {
    x: 0.5, y: 0.18, w: 9, h: 0.65,
    fontSize: 28, bold: true, color: C.white, fontFace: FONT_TITLE, margin: 0
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.5, y: 0.85, w: 9, h: 0.35,
      fontSize: 13, color: C.mint, fontFace: FONT_BODY, italic: true, margin: 0
    });
  }
  slide.addShape(pres.shapes.LINE, {
    x: 0.5, y: 1.28, w: 9, h: 0,
    line: { color: C.teal, width: 1.2 }
  });
}

function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: opts.fill || C.card },
    line: { color: opts.border || C.teal, width: opts.borderWidth || 1 },
    shadow: makeShadow(),
  });
}

// ── SLIDE 1: Title ────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W, h: 0.12, fill: { color: C.teal }, line: { color: C.teal }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: H - 0.12, w: W, h: 0.12, fill: { color: C.mint }, line: { color: C.mint }
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.12, w: 0.35, h: H - 0.24, fill: { color: C.teal }, line: { color: C.teal }
  });

  s.addText("Agentic E2E Testing", {
    x: 0.7, y: 1.4, w: 8.8, h: 1.1,
    fontSize: 48, bold: true, color: C.white, fontFace: FONT_TITLE, margin: 0
  });
  s.addText("AI-Powered Quality Automation with Gemini", {
    x: 0.7, y: 2.6, w: 8.8, h: 0.55,
    fontSize: 22, color: C.mint, fontFace: FONT_BODY, italic: true, margin: 0
  });
  s.addShape(pres.shapes.LINE, {
    x: 0.7, y: 3.28, w: 5.5, h: 0,
    line: { color: C.teal, width: 2 }
  });
  s.addText("Lead QA Engineer  ·  EX Squared", {
    x: 0.7, y: 3.5, w: 6, h: 0.4,
    fontSize: 14, color: C.silver, fontFace: FONT_BODY, margin: 0
  });
  s.addText("AI", {
    x: 6.5, y: 1.0, w: 3.2, h: 3.2,
    fontSize: 200, bold: true, color: C.teal, fontFace: FONT_TITLE,
    transparency: 80, align: "center", margin: 0
  });
}

// ── SLIDE 2: The Problem ──────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "The Problem with Traditional E2E Tests", "Why today's approach breaks under pressure");

  const problems = [
    { icon: "✗", text: "Selectors break when a developer renames a CSS class or changes placeholder text — test suite goes red", color: C.red },
    { icon: "✗", text: "Writing tests requires deep DOM knowledge — only senior engineers can contribute meaningfully", color: C.red },
    { icon: "✗", text: "Visual regressions (wrong layout, empty states, error banners) need separate, expensive tooling", color: C.red },
    { icon: "✗", text: "High maintenance cost — QA spends more time fixing broken selectors than writing new tests", color: C.red },
  ];

  problems.forEach((p, i) => {
    const y = 1.5 + i * 0.9;
    card(s, 0.5, y, 9, 0.75, { fill: C.card, border: C.red, borderWidth: 0.8 });
    s.addText(p.icon, {
      x: 0.6, y: y + 0.12, w: 0.45, h: 0.5,
      fontSize: 20, bold: true, color: C.red, fontFace: FONT_BODY, margin: 0
    });
    s.addText(p.text, {
      x: 1.15, y: y + 0.1, w: 8.2, h: 0.55,
      fontSize: 13, color: C.white, fontFace: FONT_BODY, margin: 0, valign: "middle"
    });
  });
}

// ── SLIDE 3: What is Agentic Testing? ─────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "What is Agentic Testing?", "Adding an AI brain to your existing automation");

  card(s, 0.5, 1.45, 9, 1.35, { fill: C.codeBox, border: C.teal, borderWidth: 1.5 });
  s.addText("Agentic testing adds an AI layer (Google Gemini — free tier) that can:", {
    x: 0.7, y: 1.55, w: 8.6, h: 0.4,
    fontSize: 13.5, color: C.mint, bold: true, fontFace: FONT_BODY, margin: 0
  });
  s.addText([
    { text: "SEE  ", options: { bold: true, color: C.mint } },
    { text: "the page like a human (via screenshots)     ", options: { color: C.white } },
    { text: "UNDERSTAND  ", options: { bold: true, color: C.mint } },
    { text: "the UI visually, not just by CSS selectors", options: { color: C.white, breakLine: true } },
    { text: "DECIDE  ", options: { bold: true, color: C.mint } },
    { text: "what browser action to take from a plain-English instruction     ", options: { color: C.white } },
    { text: "RECOVER  ", options: { bold: true, color: C.mint } },
    { text: "when selectors break by finding new ones automatically", options: { color: C.white } },
  ], { x: 0.75, y: 1.95, w: 8.5, h: 0.75, fontSize: 12.5, fontFace: FONT_BODY, margin: 0 });

  const pillars = [
    { title: "Level 1", sub: "Visual Assertions", desc: "Gemini answers yes/no questions from screenshots — no selectors" },
    { title: "Level 2", sub: "Self-Healing", desc: "Gemini finds working selectors from the live DOM automatically" },
    { title: "Level 3", sub: "Autonomous Agent", desc: "Gemini executes plain-English test steps in the browser" },
  ];
  pillars.forEach((p, i) => {
    const x = 0.5 + i * 3.1;
    card(s, x, 3.0, 2.9, 2.3, { fill: C.card, border: C.teal });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y: 3.0, w: 2.9, h: 0.1, fill: { color: C.teal }, line: { color: C.teal }
    });
    s.addText(p.title, { x: x + 0.1, y: 3.15, w: 2.7, h: 0.4, fontSize: 16, bold: true, color: C.mint, fontFace: FONT_TITLE, margin: 0 });
    s.addText(p.sub, { x: x + 0.1, y: 3.55, w: 2.7, h: 0.35, fontSize: 12, bold: true, color: C.white, fontFace: FONT_BODY, margin: 0 });
    s.addText(p.desc, { x: x + 0.1, y: 3.95, w: 2.7, h: 0.9, fontSize: 11, color: C.silver, fontFace: FONT_BODY, margin: 0 });
  });
}

// ── SLIDE 4: Level 1 ──────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "Level 1 — Visual Assertions", "Gemini looks at screenshots and answers yes/no questions — no selectors needed");

  card(s, 0.4, 1.45, 4.3, 3.8, { fill: C.codeBox, border: C.red, borderWidth: 1.5 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 1.45, w: 4.3, h: 0.38, fill: { color: C.red }, line: { color: C.red } });
  s.addText("TRADITIONAL", { x: 0.5, y: 1.47, w: 4.1, h: 0.34, fontSize: 13, bold: true, color: C.white, fontFace: FONT_TITLE, margin: 0 });
  s.addText("assert page.locator(\n  \"table tbody tr\"\n).count() > 0", {
    x: 0.55, y: 1.95, w: 4.0, h: 1.1, fontSize: 12, color: C.mint, fontFace: "Consolas", margin: 0
  });
  s.addShape(pres.shapes.LINE, { x: 0.55, y: 3.1, w: 4.0, h: 0, line: { color: C.red, width: 0.8 } });
  s.addText([
    { text: "BREAKS when:", options: { bold: true, color: C.red, breakLine: true } },
    { text: "• CSS class names change", options: { color: C.silver, breakLine: true } },
    { text: "• Placeholder text updated", options: { color: C.silver, breakLine: true } },
    { text: "• DOM structure refactored", options: { color: C.silver } },
  ], { x: 0.55, y: 3.2, w: 4.0, h: 1.8, fontSize: 12, fontFace: FONT_BODY, margin: 0 });

  card(s, 5.3, 1.45, 4.3, 3.8, { fill: C.codeBox, border: C.mint, borderWidth: 1.5 });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.45, w: 4.3, h: 0.38, fill: { color: C.mint }, line: { color: C.mint } });
  s.addText("AI ASSERTION (Gemini)", { x: 5.4, y: 1.47, w: 4.1, h: 0.34, fontSize: 13, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0 });
  s.addText("ai_verify(page,\n  \"Is the letter type\n  table visible with\n  data rows?\")", {
    x: 5.4, y: 1.95, w: 4.1, h: 1.1, fontSize: 12, color: C.mint, fontFace: "Consolas", margin: 0
  });
  s.addShape(pres.shapes.LINE, { x: 5.4, y: 3.1, w: 4.0, h: 0, line: { color: C.mint, width: 0.8 } });
  s.addText([
    { text: "WORKS because:", options: { bold: true, color: C.mint, breakLine: true } },
    { text: "• Gemini sees the page visually", options: { color: C.silver, breakLine: true } },
    { text: "• Understands intent, not markup", options: { color: C.silver, breakLine: true } },
    { text: "• Survives any DOM change", options: { color: C.silver } },
  ], { x: 5.4, y: 3.2, w: 4.1, h: 1.8, fontSize: 12, fontFace: FONT_BODY, margin: 0 });

  s.addText("VS", { x: 4.3, y: 3.0, w: 1.4, h: 0.6, fontSize: 18, bold: true, color: C.silver, align: "center", fontFace: FONT_TITLE, margin: 0 });
}

// ── SLIDE 5: Level 2 ──────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "Level 2 — Self-Healing Selectors", "When a selector breaks, Gemini finds a working one automatically");

  const steps = [
    { num: "1", title: "UI Changes", desc: "Developer renames a CSS class or changes placeholder text in the app", color: C.red },
    { num: "2", title: "Test Breaks", desc: "Hardcoded selector no longer matches — traditional test FAILS immediately", color: C.red },
    { num: "3", title: "Gemini Inspects", desc: "ai_find_selector() sends the live DOM + screenshot to Gemini for analysis", color: C.teal },
    { num: "4", title: "Auto-Healed", desc: "Gemini returns the correct selector — test continues with zero downtime", color: C.mint },
  ];

  steps.forEach((step, i) => {
    const x = 0.35 + i * 2.35;
    card(s, x, 1.45, 2.15, 2.8, { fill: C.card, border: step.color, borderWidth: 1.5 });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.45, w: 2.15, h: 0.42, fill: { color: step.color }, line: { color: step.color } });
    s.addText(step.num, { x: x + 0.05, y: 1.48, w: 0.45, h: 0.36, fontSize: 18, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0 });
    s.addText(step.title, { x: x + 0.5, y: 1.5, w: 1.6, h: 0.38, fontSize: 12.5, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0 });
    s.addText(step.desc, { x: x + 0.12, y: 1.98, w: 1.9, h: 2.1, fontSize: 11.5, color: C.white, fontFace: FONT_BODY, margin: 0 });
    if (i < 3) {
      s.addText("→", { x: x + 2.17, y: 2.6, w: 0.18, h: 0.4, fontSize: 18, color: C.silver, margin: 0, align: "center" });
    }
  });

  card(s, 0.5, 4.55, 9, 0.7, { fill: C.codeBox, border: C.yellow, borderWidth: 1.5 });
  s.addText("★  Selector maintenance is the #1 cost of E2E test suites — self-healing eliminates it", {
    x: 0.65, y: 4.62, w: 8.7, h: 0.56,
    fontSize: 13.5, bold: true, color: C.yellow, fontFace: FONT_BODY, margin: 0, valign: "middle"
  });
}

// ── SLIDE 6: Level 3 ──────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "Level 3 — Autonomous Agent", "Plain-English steps → Gemini drives the browser — no selectors written");

  card(s, 0.4, 1.45, 4.5, 3.8, { fill: C.codeBox, border: C.teal });
  s.addText("WRITTEN BY QA ENGINEER", { x: 0.5, y: 1.55, w: 4.2, h: 0.35, fontSize: 10, bold: true, color: C.silver, fontFace: FONT_TITLE, margin: 0 });
  const stepTexts = [
    "1.  Verify the dashboard has loaded",
    "2.  Click Letter Configuration in sidebar",
    "3.  Click on Letter Type",
    "4.  Verify table is visible with data",
    "5.  Confirm no error banner is shown",
  ];
  stepTexts.forEach((t, i) => {
    s.addText(t, {
      x: 0.55, y: 1.98 + i * 0.6, w: 4.1, h: 0.52,
      fontSize: 12, color: i < 2 ? C.mint : C.white, fontFace: "Consolas", margin: 0
    });
  });
  s.addText("← Plain English. Zero selectors.", {
    x: 0.5, y: 4.98, w: 4.3, h: 0.3, fontSize: 10.5, italic: true, color: C.silver, fontFace: FONT_BODY, margin: 0
  });

  s.addText("⇒", { x: 4.9, y: 3.1, w: 0.5, h: 0.6, fontSize: 28, color: C.teal, align: "center", margin: 0 });
  s.addText("Gemini", { x: 4.72, y: 3.72, w: 0.86, h: 0.3, fontSize: 10, color: C.mint, align: "center", bold: true, margin: 0 });

  card(s, 5.4, 1.45, 4.2, 3.8, { fill: C.codeBox, border: C.mint });
  s.addText("AGENT EXECUTION LOG", { x: 5.5, y: 1.55, w: 4.0, h: 0.35, fontSize: 10, bold: true, color: C.silver, fontFace: FONT_TITLE, margin: 0 });
  const logs = [
    { t: "✔  Step 1 — verify:  YES (2.1s)", c: C.mint },
    { t: "✔  Step 2 — click:   button.expand-btn (1.4s)", c: C.mint },
    { t: "✔  Step 3 — click:   a[href*=letter-type] (0.9s)", c: C.mint },
    { t: "✔  Step 4 — verify:  YES (1.8s)", c: C.mint },
    { t: "✔  Step 5 — verify:  NO error (1.2s)", c: C.mint },
  ];
  logs.forEach((l, i) => {
    s.addText(l.t, {
      x: 5.55, y: 1.98 + i * 0.6, w: 3.9, h: 0.52,
      fontSize: 11, color: l.c, fontFace: "Consolas", margin: 0
    });
  });
  s.addText("5/5 PASSED ✔", {
    x: 5.5, y: 4.98, w: 4.0, h: 0.3, fontSize: 12, bold: true, color: C.mint, fontFace: FONT_TITLE, margin: 0
  });
}

// ── SLIDE 7: Self-Healing in Real Tests ──────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "Self-Healing in Your Existing Tests", "Wrap any assertion with smart_assert() — it heals itself when selectors break");

  // Before card
  card(s, 0.4, 1.38, 4.4, 2.1, { fill: C.codeBox, border: C.red, borderWidth: 1.5 });
  s.addShape(pres.shapes.RECTANGLE, { x: 0.4, y: 1.38, w: 4.4, h: 0.34, fill: { color: C.red }, line: { color: C.red } });
  s.addText("BEFORE  — Fragile (breaks when selector changes)", {
    x: 0.5, y: 1.4, w: 4.2, h: 0.3, fontSize: 10.5, bold: true, color: C.white, fontFace: FONT_TITLE, margin: 0
  });
  s.addText(
    "# test_sanity.py\nassert letter_type_page\n  .is_loaded()\n\n# BREAKS if search box\n# CSS class is renamed",
    { x: 0.52, y: 1.78, w: 4.15, h: 1.6, fontSize: 11, color: C.red, fontFace: "Consolas", margin: 0 }
  );

  // Arrow
  s.addText("⟹", { x: 4.78, y: 2.2, w: 0.6, h: 0.5, fontSize: 22, color: C.teal, align: "center", bold: true, margin: 0 });
  s.addText("add\nsmart_assert", { x: 4.7, y: 2.72, w: 0.76, h: 0.45, fontSize: 8.5, color: C.mint, align: "center", fontFace: FONT_BODY, margin: 0 });

  // After card
  card(s, 5.3, 1.38, 4.3, 2.1, { fill: C.codeBox, border: C.mint, borderWidth: 1.5 });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.38, w: 4.3, h: 0.34, fill: { color: C.mint }, line: { color: C.mint } });
  s.addText("AFTER  — Self-Healing ✔", {
    x: 5.4, y: 1.4, w: 4.1, h: 0.3, fontSize: 10.5, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0
  });
  s.addText(
    "assert smart_assert(\n  page,\n  lambda: letter_type_page\n    .is_loaded(),\n  \"Is the Letter Type page\n  loaded with search box?\"\n)",
    { x: 5.42, y: 1.78, w: 4.1, h: 1.6, fontSize: 11, color: C.mint, fontFace: "Consolas", margin: 0 }
  );

  // Flow diagram — how it works
  card(s, 0.4, 3.62, 9.2, 1.65, { fill: C.card, border: C.teal, borderWidth: 1 });
  s.addText("HOW IT WORKS AT RUNTIME", {
    x: 0.55, y: 3.68, w: 9, h: 0.26, fontSize: 9.5, bold: true, color: C.silver, fontFace: FONT_TITLE, margin: 0
  });

  const flow = [
    { box: "Playwright check\n(free, instant)", color: C.teal, x: 0.5 },
    { box: "PASS?\nTest done ✔\n0 API calls", color: C.mint, x: 2.85 },
    { box: "FAIL?\nGemini looks\nat screenshot", color: C.yellow, x: 5.2 },
    { box: "YES = test healed\nNO = real bug\nfound ✔", color: C.mint, x: 7.55 },
  ];
  flow.forEach((f, i) => {
    card(s, f.x, 3.98, 2.1, 1.1, { fill: C.codeBox, border: f.color, borderWidth: 1.2 });
    s.addText(f.box, {
      x: f.x + 0.08, y: 4.02, w: 1.95, h: 1.02,
      fontSize: 10, color: f.color, fontFace: FONT_BODY, align: "center", valign: "middle", margin: 0
    });
    if (i < 3) {
      s.addText("→", { x: f.x + 2.12, y: 4.38, w: 0.22, h: 0.32, fontSize: 16, color: C.silver, align: "center", margin: 0 });
    }
  });
}

// ── SLIDE 8: Architecture ─────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "Our Framework — Agent-Ready Architecture", "The AI layer sits on top — nothing replaced, only enhanced");

  s.addText("EXISTING FRAMEWORK  (unchanged)", {
    x: 0.5, y: 1.42, w: 9, h: 0.3,
    fontSize: 10.5, bold: true, color: C.silver, fontFace: FONT_TITLE, margin: 0
  });
  const existing = ["Playwright  +  Python", "Page Objects", "Pytest", "Allure Reports"];
  existing.forEach((item, i) => {
    const x = 0.5 + i * 2.3;
    card(s, x, 1.72, 2.1, 0.72, { fill: C.card, border: C.silver, borderWidth: 0.8 });
    s.addText(item, { x: x + 0.08, y: 1.8, w: 1.95, h: 0.56, fontSize: 12, bold: true, color: C.silver, fontFace: FONT_BODY, align: "center", margin: 0, valign: "middle" });
  });

  s.addText("＋  Google Gemini AI Layer added on top  (free tier — 1,500 req/day)", {
    x: 0.5, y: 2.58, w: 9, h: 0.32,
    fontSize: 11, bold: true, color: C.teal, fontFace: FONT_TITLE, margin: 0
  });

  s.addText("AI LAYER  (new)", {
    x: 0.5, y: 2.9, w: 9, h: 0.3,
    fontSize: 10.5, bold: true, color: C.mint, fontFace: FONT_TITLE, margin: 0
  });
  const aiItems = [
    { name: "ai_verify()", sub: "Visual Assertions" },
    { name: "ai_find_selector()", sub: "Self-Healing" },
    { name: "AIAgent", sub: "Autonomous Steps" },
  ];
  aiItems.forEach((item, i) => {
    const x = 0.5 + i * 3.1;
    card(s, x, 3.2, 2.9, 1.0, { fill: C.codeBox, border: C.mint, borderWidth: 1.5 });
    s.addText(item.name, { x: x + 0.12, y: 3.28, w: 2.65, h: 0.42, fontSize: 14, bold: true, color: C.mint, fontFace: "Consolas", margin: 0 });
    s.addText(item.sub, { x: x + 0.12, y: 3.72, w: 2.65, h: 0.38, fontSize: 11.5, color: C.white, fontFace: FONT_BODY, margin: 0 });
  });

  card(s, 0.5, 4.42, 9, 0.82, { fill: C.codeBox, border: C.teal, borderWidth: 1.5 });
  s.addText("\"Nothing was replaced. The AI layer sits ON TOP of our existing suite — existing tests keep running normally.\"", {
    x: 0.7, y: 4.5, w: 8.6, h: 0.66,
    fontSize: 13, italic: true, color: C.white, fontFace: FONT_BODY, margin: 0, valign: "middle"
  });
}

// ── SLIDE 8: Code Examples ────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "Code Examples — The 4 AI Functions", "Real code from utils/ai_agent.py — powered by Google Gemini (free tier)");

  // Top row: ai_verify  |  smart_assert
  const topExamples = [
    {
      title: "1. ai_verify()  — Visual Assertion",
      borderColor: C.mint,
      code: "# Ask Gemini: is the table visible?\nresult = ai_verify(\n  page,\n  \"Is the letter type table\n  visible with data rows?\"\n)\nassert result   # True = YES",
    },
    {
      title: "2. smart_assert()  — Cost-Efficient Check",
      borderColor: C.teal,
      code: "# Playwright first (free). AI only on fail.\nassert smart_assert(\n  page,\n  lambda: page.locator(\n    \"table tbody tr\"\n  ).first.is_visible(),\n  \"Is the table visible?\"\n)",
    },
  ];

  topExamples.forEach((ex, i) => {
    const x = 0.4 + i * 4.8;
    card(s, x, 1.38, 4.4, 2.0, { fill: C.codeBox, border: ex.borderColor, borderWidth: 1.5 });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.38, w: 4.4, h: 0.34, fill: { color: ex.borderColor }, line: { color: ex.borderColor } });
    s.addText(ex.title, { x: x + 0.1, y: 1.4, w: 4.2, h: 0.3, fontSize: 11, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0 });
    s.addText(ex.code, { x: x + 0.12, y: 1.78, w: 4.15, h: 1.5, fontSize: 10.5, color: C.mint, fontFace: "Consolas", margin: 0 });
  });

  // Bottom row: ai_find_selector  |  AIAgent.run_steps
  const botExamples = [
    {
      title: "3. ai_find_selector()  — Self-Healing",
      borderColor: C.yellow,
      code: "# Broken selector? Gemini fixes it.\nsel = ai_find_selector(\n  page,\n  \"search box for letter types\"\n)\nif sel:\n  page.locator(sel).fill(\"EOB\")",
    },
    {
      title: "4. AIAgent.run_steps()  — Autonomous",
      borderColor: C.silver,
      code: "agent = AIAgent(page)\nresults = agent.run_steps([\n  \"Click Letter Config in sidebar\",\n  \"Click on Letter Type\",\n  \"Verify the table is visible\",\n])\n# Gemini decides every click",
    },
  ];

  botExamples.forEach((ex, i) => {
    const x = 0.4 + i * 4.8;
    card(s, x, 3.5, 4.4, 2.0, { fill: C.codeBox, border: ex.borderColor, borderWidth: 1.5 });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 3.5, w: 4.4, h: 0.34, fill: { color: ex.borderColor }, line: { color: ex.borderColor } });
    s.addText(ex.title, { x: x + 0.1, y: 3.52, w: 4.2, h: 0.3, fontSize: 11, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0 });
    s.addText(ex.code, { x: x + 0.12, y: 3.9, w: 4.15, h: 1.5, fontSize: 10.5, color: C.mint, fontFace: "Consolas", margin: 0 });
  });
}

// ── SLIDE 9: What We Built ────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "What We Built — Ready to Run Today", "Branch: agentic_autonomize");

  const files = [
    { file: "utils/ai_agent.py", desc: "Core AI helpers — ai_verify, smart_assert, ai_find_selector, AIAgent class", lines: "330 lines" },
    { file: "tests/test_agentic.py", desc: "9 agentic test cases across all 3 levels, tagged @pytest.mark.agentic", lines: "9 tests" },
    { file: "demo_agentic.py", desc: "Standalone live demo script with colour-coded terminal output", lines: "376 lines" },
    { file: "docs/AGENTIC_TESTING.md", desc: "Full technical documentation with usage guide and architecture diagram", lines: "docs" },
  ];

  files.forEach((f, i) => {
    const y = 1.48 + i * 0.88;
    card(s, 0.4, y, 9.2, 0.76, { fill: C.card, border: C.teal, borderWidth: 1 });
    s.addText(f.file, { x: 0.55, y: y + 0.1, w: 3.5, h: 0.55, fontSize: 13, bold: true, color: C.mint, fontFace: "Consolas", margin: 0 });
    s.addText(f.desc, { x: 4.1, y: y + 0.12, w: 4.6, h: 0.52, fontSize: 12, color: C.white, fontFace: FONT_BODY, margin: 0, valign: "middle" });
    card(s, 8.72, y + 0.1, 0.8, 0.55, { fill: C.codeBox, border: C.silver, borderWidth: 0.8 });
    s.addText(f.lines, { x: 8.72, y: y + 0.15, w: 0.8, h: 0.45, fontSize: 9.5, color: C.silver, fontFace: FONT_BODY, align: "center", margin: 0, valign: "middle" });
  });

  card(s, 0.4, 5.05, 9.2, 0.45, { fill: C.codeBox, border: C.mint, borderWidth: 1.5 });
  s.addText([
    { text: "$ ", options: { color: C.silver } },
    { text: "pytest -m agentic -v -s", options: { color: C.mint, bold: true } },
    { text: "    or    ", options: { color: C.silver } },
    { text: "python demo_agentic.py", options: { color: C.mint, bold: true } },
  ], { x: 0.6, y: 5.1, w: 9.0, h: 0.35, fontSize: 13, fontFace: "Consolas", margin: 0, valign: "middle" });
}

// ── SLIDE 10: How to Run + Demo Talking Points ────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "How to Run the Demo", "Practice these commands before the meeting — takes 5 minutes");

  s.addText("SETUP  (run once)", {
    x: 0.45, y: 1.42, w: 4.4, h: 0.28,
    fontSize: 10, bold: true, color: C.silver, fontFace: FONT_TITLE, margin: 0
  });
  card(s, 0.45, 1.7, 4.4, 1.1, { fill: C.codeBox, border: C.teal });
  s.addText([
    { text: "git checkout agentic_autonomize\n", options: { color: C.mint } },
    { text: "pip install -r requirements.txt", options: { color: C.mint } },
  ], { x: 0.6, y: 1.78, w: 4.1, h: 0.9, fontSize: 11, fontFace: "Consolas", margin: 0 });

  s.addText("RUN OPTIONS", {
    x: 0.45, y: 2.9, w: 4.4, h: 0.28,
    fontSize: 10, bold: true, color: C.silver, fontFace: FONT_TITLE, margin: 0
  });

  const runOpts = [
    { label: "Full live demo (recommended)", cmd: "python demo_agentic.py", color: C.mint },
    { label: "All agentic tests", cmd: "pytest -m agentic -v -s", color: C.teal },
    { label: "One test at a time", cmd: "pytest tests/test_agentic.py\n  ::TestAIVisualAssertions -v -s", color: C.silver },
  ];
  runOpts.forEach((r, i) => {
    const y = 3.2 + i * 0.72;
    card(s, 0.45, y, 4.4, 0.65, { fill: C.card, border: r.color, borderWidth: 1 });
    s.addText(r.label, { x: 0.6, y: y + 0.04, w: 4.1, h: 0.24, fontSize: 10, color: C.silver, fontFace: FONT_BODY, margin: 0 });
    s.addText(r.cmd, { x: 0.6, y: y + 0.28, w: 4.1, h: 0.3, fontSize: 10.5, bold: true, color: r.color, fontFace: "Consolas", margin: 0 });
  });

  s.addText("WHAT TO SAY  (talking points per log line)", {
    x: 5.2, y: 1.42, w: 4.6, h: 0.28,
    fontSize: 10, bold: true, color: C.silver, fontFace: FONT_TITLE, margin: 0
  });

  const talking = [
    {
      log: "PASS via normal check",
      say: "Normal check passed — zero API cost, instant",
      logColor: C.mint,
    },
    {
      log: "normal check FAILED — escalating",
      say: "Selector broke, Gemini is now looking at the screenshot",
      logColor: C.yellow,
    },
    {
      log: "ai_verify → 'YES'",
      say: "Gemini confirmed the element is there — test self-healed",
      logColor: C.mint,
    },
    {
      log: "Agent step logs",
      say: "I wrote plain English — Gemini decides what to click",
      logColor: C.teal,
    },
  ];

  talking.forEach((t, i) => {
    const y = 1.7 + i * 0.93;
    card(s, 5.2, y, 4.6, 0.85, { fill: C.card, border: C.teal, borderWidth: 1 });
    s.addText("When you see:", { x: 5.35, y: y + 0.05, w: 4.3, h: 0.22, fontSize: 9, color: C.silver, fontFace: FONT_BODY, margin: 0 });
    s.addText(t.log, { x: 5.35, y: y + 0.24, w: 4.3, h: 0.24, fontSize: 10.5, bold: true, color: t.logColor, fontFace: "Consolas", margin: 0 });
    s.addText("Say: \"" + t.say + "\"", { x: 5.35, y: y + 0.52, w: 4.3, h: 0.28, fontSize: 10.5, italic: true, color: C.white, fontFace: FONT_BODY, margin: 0 });
  });

  card(s, 0.45, 5.07, 9.2, 0.42, { fill: C.codeBox, border: C.yellow, borderWidth: 1.5 });
  s.addText("★  Tip: demo_agentic.py pauses at each level — press ENTER when ready so you can explain before it runs", {
    x: 0.6, y: 5.12, w: 9.0, h: 0.32,
    fontSize: 12, bold: true, color: C.yellow, fontFace: FONT_BODY, margin: 0, valign: "middle"
  });
}

// ── SLIDE 11: Business Value ───────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "Business Value", "What this means for the team and the product");

  const values = [
    { icon: "⚡", title: "FASTER",      color: C.yellow, desc: "New test cases written in plain English in minutes, not hours. No selector research needed." },
    { icon: "🛡", title: "RESILIENT",   color: C.mint,   desc: "Self-healing selectors reduce test maintenance cost. UI changes no longer break the suite." },
    { icon: "👥", title: "ACCESSIBLE",  color: C.teal,   desc: "Business Analysts and PMs can write test cases without coding or DOM knowledge." },
    { icon: "👁", title: "CONFIDENT",   color: C.silver, desc: "Visual AI assertions catch UI regressions that selector-based tests miss entirely." },
  ];

  values.forEach((v, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = 0.5 + col * 4.8;
    const y = 1.48 + row * 2.0;
    card(s, x, y, 4.5, 1.75, { fill: C.card, border: v.color, borderWidth: 2 });
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: 4.5, h: 0.12, fill: { color: v.color }, line: { color: v.color } });
    s.addText(v.icon + "  " + v.title, {
      x: x + 0.15, y: y + 0.2, w: 4.2, h: 0.45,
      fontSize: 18, bold: true, color: v.color, fontFace: FONT_TITLE, margin: 0
    });
    s.addText(v.desc, {
      x: x + 0.15, y: y + 0.68, w: 4.2, h: 0.95,
      fontSize: 12, color: C.white, fontFace: FONT_BODY, margin: 0
    });
  });
}

// ── SLIDE 12: Next Steps ──────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: W, h: 0.07, fill: { color: C.mint }, line: { color: C.mint } });
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: H - 0.07, w: W, h: 0.07, fill: { color: C.teal }, line: { color: C.teal } });

  s.addText("Next Steps", {
    x: 0.5, y: 0.18, w: 9, h: 0.65,
    fontSize: 34, bold: true, color: C.white, fontFace: FONT_TITLE, margin: 0
  });
  s.addShape(pres.shapes.LINE, { x: 0.5, y: 0.92, w: 9, h: 0, line: { color: C.teal, width: 1.2 } });

  const steps = [
    { num: "01", time: "1 day",    title: "Enable AI layer in CI/CD",  desc: "Add GEMINI_API_KEY to the pipeline environment (free key from aistudio.google.com). Framework is already integrated.", color: C.teal },
    { num: "02", time: "1 week",   title: "Harden flaky selectors",    desc: "Wrap the top 10 most-brittle selectors with ai_find_selector() as an automatic fallback.", color: C.mint },
    { num: "03", time: "1 sprint", title: "Pilot plain-English tests", desc: "Write the next sprint's new test cases using AIAgent.run_steps() — measure time saved vs traditional.", color: C.yellow },
  ];

  steps.forEach((step, i) => {
    const y = 1.08 + i * 1.35;
    card(s, 0.5, y, 9, 1.2, { fill: C.card, border: step.color, borderWidth: 1.5 });
    s.addShape(pres.shapes.RECTANGLE, { x: 0.5, y, w: 0.1, h: 1.2, fill: { color: step.color }, line: { color: step.color } });
    s.addText(step.num, { x: 0.65, y: y + 0.08, w: 0.8, h: 0.55, fontSize: 28, bold: true, color: step.color, fontFace: FONT_TITLE, margin: 0 });
    s.addText(step.time, { x: 0.65, y: y + 0.65, w: 0.8, h: 0.4, fontSize: 10, color: C.silver, fontFace: FONT_BODY, margin: 0 });
    s.addText(step.title, { x: 1.6, y: y + 0.12, w: 7.6, h: 0.42, fontSize: 16, bold: true, color: step.color, fontFace: FONT_TITLE, margin: 0 });
    s.addText(step.desc, { x: 1.6, y: y + 0.58, w: 7.6, h: 0.52, fontSize: 12, color: C.white, fontFace: FONT_BODY, margin: 0 });
  });

  s.addText("The infrastructure is ready.  We just need to turn it on.", {
    x: 0.5, y: 5.18, w: 9, h: 0.35,
    fontSize: 14, bold: true, italic: true, color: C.mint, fontFace: FONT_BODY, align: "center", margin: 0
  });
}

// ── Write file ────────────────────────────────────────────────────────────────
const outPath = path.join(__dirname, "Agentic_Testing_Demo_v4.pptx");
pres.writeFile({ fileName: outPath }).then(() => {
  console.log("✔  Created: " + outPath);
}).catch(err => {
  console.error("✘  Error:", err);
  process.exit(1);
});
