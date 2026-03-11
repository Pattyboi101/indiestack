# PH Landing Page Polish — Design Document

**Goal:** Fix credibility gaps, stale data, and conversion confusion on the landing page before Product Hunt launch day.

**Scope:** Landing page only (`landing.py`). No structural changes — visual polish and data fixes.

---

## 1. Fix Stale Data

- **Banner**: `v0.5.0` → `v0.7.0`
- **MCP explainer**: Hardcoded `900+` → dynamic `{tool_count}`
- **Stats bar**: Remove maker count. New format: `{tool_count}+ tools | {ai_recs:,}+ AI recommendations & counting`

## 2. Swap Showcase Tools

Clear all 6 hardcoded `landing_position` values in the database. Set new `landing_position` values for 6 genuinely indie tools, spread across categories. Criteria:
- Maker-claimed (`maker_id IS NOT NULL`)
- Open source preferred (`source_type = 'code'`)
- High quality score
- Category diversity (no two from same category)
- No VC-backed companies (PostHog, Supabase, Clerk, etc.)

## 3. Video Placeholder Section

New section between hero and MCP walkthrough. Simple design:
- Heading: "See it in action"
- Placeholder: Dark card with play button icon, linking to `#mcp-install` for now
- Subtext: "Watch how your AI finds indie tools instead of writing code from scratch."
- When Ed's video is ready, swap the placeholder for an embedded YouTube/Vimeo iframe via `VIDEO_URL` env var or hardcoded URL

## 4. Remove Maker CTA from Hero

- Remove the "Add Your Tool →" button and its subtext from the hero section
- Keep the maker CTA section at the bottom of the page (unchanged)
- Hero now focuses purely on user actions: "Install the MCP Server" + "Browse Tools"

---

## Files to Modify

1. `src/indiestack/routes/landing.py` — Banner version, stats bar, video section, remove hero maker CTA, fix hardcoded 900+
2. Database: UPDATE `landing_position` on tools table (clear old, set new)

## Out of Scope

- Founder story section (explicitly skipped)
- Structural layout changes
- New pages or routes
