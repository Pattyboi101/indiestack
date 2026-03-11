# PH Landing Page Polish Round 3 — Design Document

**Goal:** Make the landing page's value prop visceral — show don't tell — with a build-vs-buy terminal mockup and a search widget that demos itself.

**Scope:** Landing page only (`landing.py`). No new routes, no backend changes.

---

## 1. Reframe Search Widget with Suggestion Pills

**Current:** "What are you building?" + empty search box. Asks the visitor to work.

**New heading:** "Try it yourself"
**New subtext:** "Search like your AI agent does. Pick one or type your own."

Below the search box, add 3-4 clickable suggestion pills: `analytics`, `auth`, `invoicing`, `email`. Clicking a pill:
1. Fills the search input with that term
2. Triggers the existing search function automatically

Pure frontend change — the existing `/api/tools/search` endpoint handles results. The pills use the same `doSearch()` function already in the inline script.

**Pill styling:** Small rounded buttons, `var(--cream-dark)` background, `var(--ink-muted)` text, subtle hover → `var(--accent)` border. Consistent with existing design tokens.

## 2. Build vs Buy Terminal Mockup

New static section between MCP walkthrough and search widget. Styled as a terminal window (dark card, dot-row title bar, monospace font). Two scenarios shown:

**Top half — "Without IndieStack" (dimmed/red accent):**
```
> Build me a login system with OAuth support

✍ Generating auth module...
  - Setting up session management...
  - Implementing password hashing with bcrypt...
  - Adding Google OAuth flow...
  - Writing token refresh logic...

📄 Generated 847 lines across 6 files
⏱ ~52,000 tokens used
```

**Bottom half — "With IndieStack" (bright/green accent):**
```
> Build me a login system with OAuth support

🔍 Searching IndieStack...
✅ Found: Hanko — Passkey-first auth, open source
   One integration. Maintained by security experts.
   → hanko.io

⏱ ~200 tokens used
```

Static HTML, no animations. JetBrains Mono font (already loaded). The terminal frame uses `var(--ink)` background with a subtle border, fitting the dark landing page. Title bar has three dots (red/yellow/green) for the terminal chrome look.

---

## Page Flow (updated)

Hero → Video (when DEMO_VIDEO_URL set) → How it works → **Build vs Buy terminal** → **Try it yourself** → Popular tools → Categories → Maker CTA

## Files to Modify

1. `src/indiestack/routes/landing.py` — search widget copy + pills, new build-vs-buy section, page assembly order

## Out of Scope

- Backend changes
- Interactive build-vs-buy calculator
- Search widget animations/typewriter effects
