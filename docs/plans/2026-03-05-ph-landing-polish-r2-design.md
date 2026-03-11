# PH Landing Page Polish Round 2 — Design Document

**Goal:** Fix remaining credibility gaps on the landing page before Product Hunt launch day.

**Scope:** Landing page only (`landing.py` + `components.py`). No structural changes — copy fixes and conditional visibility.

---

## 1. Hide Video Section Until Launch Day

Remove the "Demo coming soon" placeholder. When `DEMO_VIDEO_URL` env var is empty (default), render nothing. When set on launch day, render the iframe embed. One env var change + redeploy = video appears.

Change: `video_section = ""` in the else branch (instead of the placeholder HTML).

## 2. Clarify "AI picked" Badges

Change `"⚡ AI picked 3x"` to `"⚡ 3 AI recommendations"` on tool cards. Same data (`mcp_view_count`), clearer copy. PH visitors won't wonder what "AI picked" means.

Change: `components.py:1074`

## 3. Hide Low Daily Lookup Count in Banner

The pulse banner shows "55 AI lookups today" — underwhelming on quiet days. Only show the pulse count when `today_ai_count >= 100`. Below that threshold, hide the separator and pulse link. On launch day, traffic will easily clear this bar.

Change: `landing.py:124-136` — wrap pulse section in conditional.

## 4. Remove Maker Count from MCP Walkthrough Stats

The "636 makers" stat in the proof stats below the MCP walkthrough is oddly specific and not impressive enough. Remove it, keeping just: AI recommendations + categories.

Change: `landing.py:377-378` — delete the middot separator and maker count span.

---

## Files to Modify

1. `src/indiestack/routes/landing.py` — Video section else branch, banner pulse threshold, MCP walkthrough stats
2. `src/indiestack/routes/components.py` — AI picked badge copy

## Out of Scope

- Adding screenshots/GIFs (no assets ready)
- Structural layout changes
- New pages or routes
