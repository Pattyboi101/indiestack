# Frontend Memory

_You are a persistent agent. This file is your long-term knowledge base._
_Read this on startup. Update it after each task with what you learned._
_Focus on: file locations, patterns, gotchas, past decisions, domain knowledge._

---

## 2026-03-30

### pricing.py
- Three-tier pricing: Free (developers), $299/mo (Tool Makers), Custom (Enterprise)
- `_check_icon()` SVG — stroke color should use `style="stroke:var(--accent)"` not `stroke="#00D4F5"`
- `--accent` = `--slate` = `#00D4F5` (defined in components.py :root)
- GitHub Action feature ("stack-health-check") is real — Pattyboi101/stack-health-check
- CTAs are context-aware: logged-in users see Dashboard link, logged-out see Signup

### components.py patterns
- `--accent` is the primary brand color (cyan/slate), used everywhere for highlights, borders, buttons
- `--cyan` also exists as a separate variable (used for maker names)
- SVG inline stroke: use `style="stroke:var(--accent)"` not the `stroke` attribute directly
- Success/error colors: use `var(--success-text)`, `var(--error-text)` — NOT `#10B981` / `#EF4444`
- Copy button pattern in setup.py `_COPY_BTN`: has hardcoded `#e2e8f0` (known violation)

### analyze.py
- `_score_color()` returns hardcoded `#10B981` / `#EF4444` — used in SVG dial stroke (known violation)
- `_render_dial()` uses `stroke="{color}"` with hardcoded hex (same pattern as pricing.py fix)
- `_freshness_badge()` correctly uses CSS variables — use as reference
- "Try sample" button pre-fills textarea with SAMPLE_PACKAGE_JSON constant

### migrations.py
- Migration table rows use hardcoded `#EF4444` (from) and `#10B981` (to) (known violation)
- `/data` route exists in `data_product.py` — API CTA is not a dead link
- Key Insights block is hardcoded editorial text — will drift from DB if data changes
- No cross-sell to /analyze (UX gap flagged to Master)

### tool.py
- `name` = escaped tool name, `tool_id`, `slug_str` are the key variables in the route
- `?claimed=1` → `claim_banner` (top of page, line ~685), `?claimed` → `claim_message` (below tool card, line ~405)
- `quote` from `urllib.parse` already imported; Twitter share URL pattern already exists at line ~710
- f-string quoting gotcha: use string concatenation for tweet text, not nested quotes inside f-strings
- Quick wins card added at `?claimed=1` branch with 3 steps + X share link

### dashboard.py
- AI Distribution Intelligence has 3 branches: A (no claimed tools), B (has claimed tools), C (no maker_id)
- Branch B silent empty state: when `queries or agents` is False AND `_headline_html` is empty, `ai_intel_html` stayed `''` — fixed with `else:` clause
- `get_maker_query_intelligence`, `get_maker_agent_breakdown`, `get_maker_daily_trend` — the three async calls for Branch B

### setup.py
- Tool count inconsistency: subtitle + welcome banner + "What happens next" say "6,500+" but real DB count is ~3,099. CLAUDE.md template inside the page says "3,100+". Three different numbers — credibility issue flagged to Master.
- 4 IDEs: claude-code, cursor, windsurf, other
- GitHub Action in Step 3: `Pattyboi101/stack-health-check@master`
- Welcome banner shown at `?welcome=1` for new signups

### footer (components.py footer_html())
- Footer has 4 columns: Brand, Product, Company, Legal
- Bug report email is `pajebay1@gmail.com` — may want updating (line ~785)
- Footer brand blurb says indie makers — positioning (line ~760)
- /about ✅ EXISTS — served from content.py (was previously noted as 404 — STALE)
- /terms ✅ EXISTS — served from content.py
- /privacy ✅ EXISTS — served from content.py
- /faq NOT in footer (was removed), so no dead link there
- GitHub link IS in footer (line ~778)
- /changelog ✅ exists

### landing.py
- Hero tool count is live from DB (tool_count variable) — accurate
- "847 repos migrated to it last month" in hero code block is hardcoded static text
- Hero features macOS traffic light colors (#FF5F56, #27C93F) — likely intentional
- Tool of the Week: tries `tool_of_the_week=1` flag first, falls back to highest `mcp_view_count`
- Landing cache: 5-minute TTL
- Primary CTA: "Scan Your Stack Free" → /analyze
- Secondary CTA: "View Migration Data" → /migrations

## 2026-03-31

### scripts/synthetic_user.py
- Synthetic user test script created for quality assurance
- Tests 6 key pages: /, /setup, /explore, /analyze, /migrations, /pricing
- Checks for specific content (install commands, value prop, stats, etc.)
- Uses only urllib.request (no external deps)
- Generates markdown report to /tmp/synthetic_user_report.md
- All production tests passing (29/30 checks as of 2026-03-31 12:27:20)

## 2026-04-04

### dashboard.py — claim-to-Pro flow audit
- `has_claimed_tools` flag (line ~107): `SELECT COUNT(*) FROM tools WHERE maker_id=? AND claimed_at IS NOT NULL AND status='approved'`
- `upgrade_html` (line ~165): shows when `not is_pro and has_claimed_tools` — button in header area
- `pro_banner` (line ~98): shows when `not is_pro and maker_id` — thin strip at top for ALL non-Pro makers
- `just_claimed_banner` (added): shows when `?just_claimed=1` param — navy gradient celebration card with Pro CTA
- `pro_nudge_card` (added): shows when `not is_pro and has_claimed_tools and not just_claimed_param` — lighter border card below quality score

### main.py — post-claim redirect
- `/api/claim/verify/{token}` endpoint (line ~3552) was redirecting to `/tool/{slug}?claimed=1`
- Changed to redirect to `/dashboard?just_claimed=1&tool={slug}` so user lands on analytics + Pro CTA
- The `?claimed=1` banner in tool.py is now fallback-only (admin-approval path still uses `?claim_requested=1`)

### JS gotcha: multiple startProCheckout() definitions
- dashboard.py had duplicate function definitions on the same page
- Fixed: `just_claimed_banner` uses `window.startProCheckout = async function()` (highest priority, defines it)
- `upgrade_html` uses `if (typeof startProCheckout === "undefined")` guard
- `pro_nudge_card` uses the same typeof guard
- Pattern: use `window.X = function()` for the "primary" definition, typeof guard for secondaries

### Vision constraints for revenue nudges
- Never gate features behind payment — free analytics always visible
- Nudge copy should be specific about what Pro adds ("search query breakdown", "daily digest") not vague
- "No contract · Cancel any time" below CTA buttons removes friction
- Maker Pro is **$19/mo** — gotchas.md and vision.md are canonical. Previous memory entry saying $49 was WRONG.

## 2026-04-04 (maker pages + nav audit)

### maker.py
- Route: `/maker/{slug}` — calls `get_maker_with_tools(db, slug)` + `get_maker_stats(db, maker_id)`
- 404 branch: returns proper 404 status code, not just a 404-looking page
- All user data escaped via `html.escape()` in name, bio, url
- Production has 12+ real makers with slugs like: ramz404, cirosantilli, patrick-jones, simon, dan
- `cirosantilli` has adversarial name with `<script>alert(1)</script>` — properly escaped, no vuln
- Stats bar renders: tool_count + total_upvotes from `get_maker_stats()`
- `/makers` directory returns 302 without -L flag (redirect to login or similar) — use `-sL` for curl

### nav/footer dead-link audit (2026-04-04)
- All nav links verified 200: /explore, /migrations, /pricing, /submit, /login, /signup, /dashboard, /dashboard/notifications, /logout, /setup
- All footer links verified 200: /explore, /analyze, /stacks, /data, /about, /submit, /changelog, /terms, /privacy
- /about → content.py ✅  |  /terms → content.py ✅  |  /privacy → content.py ✅  |  /data → data_product.py ✅
- NO dead links found anywhere in nav or footer as of this date

