# Admin Streamline — Design

**Goal**: Reorganise the admin Command Centre from a cluttered 5-tab layout into a focused 4-tab layout with proper sub-navigation, honest section labelling, and consistent code patterns.

**Architecture**: Pure reorganisation + cleanup. No new features, no database changes. Move existing sections between tabs, surface hidden sections in Growth, merge Content into Tools, trim Overview to actionables + today's pulse. Standardise tables and deduplicate helpers under the hood.

---

## Tab Structure

| Tab | Sub-nav | Content |
|-----|---------|---------|
| **Overview** | None | Action items + today's pulse |
| **Tools** | Pending · All · Claims · Stacks · Reviews | All tool management in one place |
| **People** | None | Search + role filter + unified table |
| **Growth** | Charts · Tables · Funnels · Search · Email · Magic Links · Makers · Stale Tools · Social | All 9 sections properly surfaced |

Content tab is **deleted**. Stacks and Reviews move to Tools sub-nav.

---

## Tab 1: Overview (Command Centre)

Two-column layout on desktop (stacks vertically on mobile).

### Left column (60%) — Action Items

- **Pending Tools** — Full approve/reject cards. Show ALL pending (no cap). "Approve All / Reject All" bulk buttons.
- **Pending Avatars** — Pixel avatar approve/reject cards.
- **Claim Requests** — Approve/reject claim cards.
- Each section only renders if there are items. If nothing pending → "All clear ✓" message.

### Right column (40%) — Today's Pulse

- **4 compact KPI cards**: Page Views (today), Searches (today), New Signups (today), AI Recs (today).
- **Alerts strip**: Stale tools count, search gaps count, Stripe-less makers count.
- **Latest activity**: Last 5 tool submissions (compact one-liners with name + time-ago).

### Removed from Overview
- 8 lifetime KPI cards (redundant with Growth)
- Recent Purchases table
- Duplicate pending queue capped at 5

---

## Tab 2: Tools

Sub-nav: `Pending (N) | All Tools | Claims | Stacks | Reviews`

### Pending
Same approve/reject cards as Overview (shared renderer). Includes "Approve All / Reject All" bulk buttons. Pending count shown as badge on sub-nav pill.

### All Tools
- Filter bar: text search, status dropdown, special filter, sort dropdown.
- Paginated table (50/page) using `data_table()` helper.
- Columns: Name (linked to `/admin/edit/{id}`), Status badge, Upvotes, Category, Added, Verify toggle, Ejectable toggle, Delete button, Magic Link button.
- **Removed from table rows**: Inline boost input, feature dropdown, price column. These move to the edit page.

### Claims
Claim requests table with Approve/Reject buttons. Moved from being wedged between pending and all-tools.

### Stacks
Moved from Content tab. No functional changes:
- Create stack form (title, emoji, discount, description)
- Add tool to stack form
- Stacks table with delete buttons

### Reviews
Moved from Content tab. No functional changes:
- Recent reviews with tool name, rating, reviewer, body
- Delete button per review

---

## Tab 3: People

No sub-nav.

- **Search bar**: Text input to search by name or email.
- **Role filter pills**: All / Makers / Users.
- **Unified table** using `data_table()` helper.
- Columns: Name (linked), Email, Role badge, Tools count, Stripe status, Last Active, Indie Status dropdown.
- Capped at 100 rows (with search, this is sufficient).

---

## Tab 4: Growth

Sub-nav: `Charts | Tables | Funnels | Search | Email | Magic Links | Makers | Stale Tools | Social`

Horizontal pills, wrapping on mobile.

### Charts (was top half of Traffic)
- Period filter pills: Today / 7d / 30d / All Time.
- 6 KPI cards: Page Views, Unique Visitors, Outbound Clicks, Revenue, Pro Subscribers, MRR.
- Daily traffic bar chart (14 days).
- Hourly heatmap bar chart (24 hours).
- Daily revenue bar chart (30 days).

### Tables (was bottom half of Traffic)
- Top 10 Pages table (with progress bars).
- Top 10 Referrers table.
- Recent Visitors table (last 20).

### Funnels (unchanged)
- Platform funnel bar chart.
- Per-tool funnel table.
- Maker leaderboard.

### Search (unchanged)
- Search volume KPI.
- Search gap analysis table.
- Top search queries table.

### Email (cleaned — was secretly 4 tools)
**Only email-related content:**
- Subscriber count.
- TOTW winner panel with send buttons.
- Weekly Digest panel with test + blast buttons.
- Launch Day Blast panel.
- Maker Launch Countdown panel.
- Marketplace Preview panel.
- Custom Email form.

### Magic Links (promoted from hidden inside Email)
- Recently claimed tools table.
- Unclaimed tools with per-tool "Generate Link" button.
- "Generate All Magic Links" CSV export button.

### Makers (promoted from hidden inside Email)
- 4 readiness KPI cards: Claimed, Stripe Connected, Have Pricing, Ready to Sell.
- Maker activity table with Send Nudge + Stripe Nudge buttons.

### Stale Tools (promoted from hidden inside Email)
- Status pills: Active / Stale / Inactive / Unknown / No GitHub counts.
- Stale + inactive tools table with freshness badges.
- SSH command instructions for freshness checker.

### Social (unchanged)
- Pre-written tweet/post templates with Copy + Tweet buttons.

---

## Code Cleanup

### 1. Deduplicate badge helpers
Move all badge/label functions to `admin_helpers.py`:
- `status_badge()` — exists in admin_helpers.py + admin_outreach.py + inline in admin_analytics.py
- `_days_ago_label()` — exists in admin_helpers.py + admin_outreach.py
- `_freshness_badge()` — only in admin_outreach.py, move to shared helpers

Delete private copies from admin_outreach.py and admin_analytics.py.

### 2. Standardise tables
Replace all hand-rolled `<table>` HTML with the `data_table()` helper from admin_helpers.py. Affected sections: Tools table, People table, Claims table, Magic Links table, Maker Tracker table, Reviews table, Stacks table.

### 3. Delete dead code
- Remove `render_content_tab()` from admin.py
- Remove Content tab from tab navigation renderer
- Remove any Content-specific POST handlers that are now unreachable

### 4. Optimise chart queries
Replace the 38-query loop pattern (14 daily + 24 hourly individual COUNT queries) with 2 `GROUP BY` queries:
- `SELECT DATE(created_at) as day, COUNT(*) FROM page_views WHERE ... GROUP BY day`
- `SELECT strftime('%H', created_at) as hour, COUNT(*) FROM page_views WHERE ... GROUP BY hour`

---

## Files to Modify

1. **`admin.py`** — Tab nav (4 tabs), Overview rewrite, Tools tab sub-nav + stacks/reviews integration, People search bar, Content tab removal
2. **`admin_analytics.py`** — Split Traffic into Charts + Tables, optimise chart queries
3. **`admin_outreach.py`** — Clean Email section (remove magic/makers/stale), promote those to standalone renderers
4. **`admin_helpers.py`** — Absorb deduplicated badge/label/freshness helpers, enhance `data_table()` if needed
