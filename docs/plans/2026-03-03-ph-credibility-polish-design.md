# PH Credibility Polish — Design

**Goal**: Improve visual credibility and trust signals before Product Hunt launch by adding favicons to tool cards and reframing the landing page stats.

**Architecture**: Minimal changes — one component function edit, one landing page copy edit. No database changes, no new endpoints.

---

## Change 1: Favicons on Tool Cards

**Source**: Google Favicon Service — `https://www.google.com/s2/favicons?domain={domain}&sz=32`

**Domain extraction**: Parse tool's `website` field using `urllib.parse.urlparse()` to get netloc.

**Fallback**: If no website URL, render a styled initial-letter circle (first letter of tool name, neutral gray background).

**Placement**: Left of tool name in card header, 24x24, rounded corners, subtle border. `loading="lazy"` + `onerror` to swap to initial on failure.

**Files**: `src/indiestack/routes/components.py` — `tool_card()` function

## Change 2: Stats Bar Reframe

**Current**: `{ai_recs} AI recommendations · {tool_count} tools · {maker_count} makers`

**New**: `{ai_recs} AI recommendations · {category_count} categories and growing · {maker_count} makers`

**Files**: `src/indiestack/routes/landing.py` — stats bar section

**Data**: `category_count` from existing `get_all_categories()` query (already called on landing page, just need `len()`).
