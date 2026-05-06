// Agentic E2E Testing — PowerPoint Generator
// Run: node docs/build_pptx.js
// Output: docs/Agentic_Testing_Demo.pptx

const pptxgen = require("pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Lead QA Engineer — Autonomize";
pres.title = "Agentic E2E Testing with Claude AI";

// ── Palette ──────────────────────────────────────────────────────────────────
const C = {
  navy:    "0D1B4B",   // dominant dark background
  teal:    "028090",   // primary accent
  mint:    "02C39A",   // secondary accent
  white:   "FFFFFF",
  offWhite:"F0F6FA",
  silver:  "B0C4D4",
  dark:    "0A1628",
  card:    "112255",   // slightly lighter than navy for cards
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
  // Teal top bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W, h: 0.07, fill: { color: C.mint }, line: { color: C.mint }
  });
  // Title
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
  // Separator line
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

function tealBullet(slide, items, x, y, w) {
  const texts = [];
  items.forEach((item, i) => {
    texts.push({
      text: item,
      options: {
        bullet: { code: "25B6", indent: 12 },
        breakLine: i < items.length - 1,
        color: C.white,
        fontSize: 13.5,
        paraSpaceAfter: 6,
      }
    });
  });
  slide.addText(texts, { x, y, w, h: 3.5, fontFace: FONT_BODY, valign: "top" });
}

// ── SLIDE 1: Title ────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Top accent bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: W, h: 0.12, fill: { color: C.teal }, line: { color: C.teal }
  });
  // Bottom accent bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: H - 0.12, w: W, h: 0.12, fill: { color: C.mint }, line: { color: C.mint }
  });

  // Left teal stripe
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0.12, w: 0.35, h: H - 0.24, fill: { color: C.teal }, line: { color: C.teal }
  });

  // Main title
  s.addText("Agentic E2E Testing", {
    x: 0.7, y: 1.4, w: 8.8, h: 1.1,
    fontSize: 48, bold: true, color: C.white, fontFace: FONT_TITLE, margin: 0
  });

  // Subtitle
  s.addText("AI-Powered Quality Automation with Claude", {
    x: 0.7, y: 2.6, w: 8.8, h: 0.55,
    fontSize: 22, color: C.mint, fontFace: FONT_BODY, italic: true, margin: 0
  });

  // Divider
  s.addShape(pres.shapes.LINE, {
    x: 0.7, y: 3.28, w: 5.5, h: 0,
    line: { color: C.teal, width: 2 }
  });

  // Byline
  s.addText("Lead QA Engineer  ·  Autonomize", {
    x: 0.7, y: 3.5, w: 6, h: 0.4,
    fontSize: 14, color: C.silver, fontFace: FONT_BODY, margin: 0
  });

  // Right side decorative element — big faded "AI"
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

  // Centre definition card
  card(s, 0.5, 1.45, 9, 1.35, { fill: C.codeBox, border: C.teal, borderWidth: 1.5 });
  s.addText("Agentic testing adds an AI layer (Claude) that can:", {
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

  // Three pillars
  const pillars = [
    { title: "Level 1", sub: "Visual Assertions", desc: "Claude answers yes/no questions from screenshots" },
    { title: "Level 2", sub: "Self-Healing", desc: "Claude finds working selectors from the live DOM" },
    { title: "Level 3", sub: "Autonomous Agent", desc: "Claude executes plain-English test steps on its own" },
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
  addSlideHeader(s, "Level 1 — Visual Assertions", "Claude looks at screenshots and answers yes/no questions — no selectors needed");

  // Left: Traditional
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

  // Right: AI
  card(s, 5.3, 1.45, 4.3, 3.8, { fill: C.codeBox, border: C.mint, borderWidth: 1.5 });
  s.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.45, w: 4.3, h: 0.38, fill: { color: C.mint }, line: { color: C.mint } });
  s.addText("AI ASSERTION", { x: 5.4, y: 1.47, w: 4.1, h: 0.34, fontSize: 13, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0 });
  s.addText("ai_verify(page,\n  \"Is the letter type\n  table visible with\n  data rows?\")", {
    x: 5.4, y: 1.95, w: 4.1, h: 1.1, fontSize: 12, color: C.mint, fontFace: "Consolas", margin: 0
  });
  s.addShape(pres.shapes.LINE, { x: 5.4, y: 3.1, w: 4.0, h: 0, line: { color: C.mint, width: 0.8 } });
  s.addText([
    { text: "WORKS because:", options: { bold: true, color: C.mint, breakLine: true } },
    { text: "• Claude sees the page visually", options: { color: C.silver, breakLine: true } },
    { text: "• Understands intent, not markup", options: { color: C.silver, breakLine: true } },
    { text: "• Survives any DOM change", options: { color: C.silver } },
  ], { x: 5.4, y: 3.2, w: 4.1, h: 1.8, fontSize: 12, fontFace: FONT_BODY, margin: 0 });

  // Arrow between
  s.addText("VS", { x: 4.3, y: 3.0, w: 1.4, h: 0.6, fontSize: 18, bold: true, color: C.silver, align: "center", fontFace: FONT_TITLE, margin: 0 });
}

// ── SLIDE 5: Level 2 ──────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "Level 2 — Self-Healing Selectors", "When a selector breaks, Claude finds a working one automatically");

  // Flow steps
  const steps = [
    { num: "1", title: "UI Changes", desc: "Developer renames a CSS class or changes placeholder text in the app", color: C.red },
    { num: "2", title: "Test Breaks", desc: "Hardcoded selector no longer matches — traditional test FAILS immediately", color: C.red },
    { num: "3", title: "Claude Inspects", desc: "ai_find_selector() sends the live DOM + screenshot to Claude for analysis", color: C.teal },
    { num: "4", title: "Auto-Healed", desc: "Claude returns the correct selector — test continues with zero downtime", color: C.mint },
  ];

  steps.forEach((step, i) => {
    const x = 0.35 + i * 2.35;
    card(s, x, 1.45, 2.15, 2.8, { fill: C.card, border: step.color, borderWidth: 1.5 });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.45, w: 2.15, h: 0.42, fill: { color: step.color }, line: { color: step.color } });
    s.addText(step.num, { x: x + 0.05, y: 1.48, w: 0.45, h: 0.36, fontSize: 18, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0 });
    s.addText(step.title, { x: x + 0.5, y: 1.5, w: 1.6, h: 0.38, fontSize: 12.5, bold: true, color: C.navy, fontFace: FONT_TITLE, margin: 0 });
    s.addText(step.desc, { x: x + 0.12, y: 1.98, w: 1.9, h: 2.1, fontSize: 11.5, color: C.white, fontFace: FONT_BODY, margin: 0 });
    // Arrow (not after last)
    if (i < 3) {
      s.addText("→", { x: x + 2.17, y: 2.6, w: 0.18, h: 0.4, fontSize: 18, color: C.silver, margin: 0, align: "center" });
    }
  });

  // Bottom stat highlight
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
  addSlideHeader(s, "Level 3 — Autonomous Agent", "Plain-English steps → Claude drives the browser — no selectors written");

  // Left: plain English input
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

  // Arrow
  s.addText("⇒", { x: 4.9, y: 3.1, w: 0.5, h: 0.6, fontSize: 28, color: C.teal, align: "center", margin: 0 });
  s.addText("Claude", { x: 4.78, y: 3.72, w: 0.74, h: 0.3, fontSize: 10, color: C.mint, align: "center", bold: true, margin: 0 });

  // Right: agent action output
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

// ── SLIDE 7: Architecture ─────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "Our Framework — Agent-Ready Architecture", "The AI layer sits on top — nothing replaced, only enhanced");

  // Existing layer label
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

  // Arrow down
  s.addText("＋  AI Layer added on top", {
    x: 0.5, y: 2.58, w: 9, h: 0.32,
    fontSize: 11, bold: true, color: C.teal, fontFace: FONT_TITLE, margin: 0
  });

  // AI layer
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

  // Key takeaway
  card(s, 0.5, 4.42, 9, 0.82, { fill: C.codeBox, border: C.teal, borderWidth: 1.5 });
  s.addText("\"Nothing was replaced. The AI layer sits ON TOP of our existing suite — existing tests keep running normally.\"", {
    x: 0.7, y: 4.5, w: 8.6, h: 0.66,
    fontSize: 13, italic: true, color: C.white, fontFace: FONT_BODY, margin: 0, valign: "middle"
  });
}

// ── SLIDE 8: What We Built ────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };
  addSlideHeader(s, "What We Built — Ready to Run Today", "Branch: agentic_autonomize");

  const files = [
    { file: "utils/ai_agent.py", desc: "Core AI helpers — ai_verify, ai_find_selector, AIAgent class", lines: "330 lines" },
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

  // Run command
  card(s, 0.4, 5.05, 9.2, 0.45, { fill: C.codeBox, border: C.mint, borderWidth: 1.5 });
  s.addText([
    { text: "$ ", options: { color: C.silver } },
    { text: "pytest -m agentic -v -s", options: { color: C.mint, bold: true } },
    { text: "    or    ", options: { color: C.silver } },
    { text: "python demo_agentic.py", options: { color: C.mint, bold: true } },
  ], { x: 0.6, y: 5.1, w: 9.0, h: 0.35, fontSize: 13, fontFace: "Consolas", margin: 0, valign: "middle" });
}

// ── SLIDE 9: Business Value ───────────────────────────────────────────────────
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

// ── SLIDE 10: Next Steps ──────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: C.navy };

  // Top bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: W, h: 0.07, fill: { color: C.mint }, line: { color: C.mint } });
  // Bottom bar
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: H - 0.07, w: W, h: 0.07, fill: { color: C.teal }, line: { color: C.teal } });

  s.addText("Next Steps", {
    x: 0.5, y: 0.18, w: 9, h: 0.65,
    fontSize: 34, bold: true, color: C.white, fontFace: FONT_TITLE, margin: 0
  });
  s.addShape(pres.shapes.LINE, { x: 0.5, y: 0.92, w: 9, h: 0, line: { color: C.teal, width: 1.2 } });

  const steps = [
    { num: "01", time: "1 day",    title: "Enable AI layer in CI/CD",  desc: "Add ANTHROPIC_API_KEY to the pipeline environment. The framework is already integrated.", color: C.teal },
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
const outPath = path.join(__dirname, "Agentic_Testing_Demo.pptx");
pres.writeFile({ fileName: outPath }).then(() => {
  console.log("✔  Created: " + outPath);
}).catch(err => {
  console.error("✘  Error:", err);
  process.exit(1);
});
