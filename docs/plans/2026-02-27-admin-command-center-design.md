# Admin Command Center — Design Document

## Problem

The admin section is split across 3 pages (`/admin`, `/admin/analytics`, `/admin/outreach`) with 16 sub-tabs. "Makers" and "Users" show different numbers with no explanation of the relationship. The visual styling is monotone with no hierarchy. Daily tasks (approving tools) are buried alongside rarely-used features (import).

## Solution

Consolidate into a single `/admin?tab=X` page with 5 focused tabs: **Overview, Tools, People, Content, Growth**. Merge makers and users into a unified "People" view. Add contextual KPIs, a persistent pending-alert bar, and improved visual hierarchy.

---

## Information Architecture

### Tab Structure

| Tab | Contains | Replaces |
|-----|----------|----------|
| **Overview** | 8 KPI cards, pending queue, alerts strip, recent activity | admin.py KPIs + analytics overview + outreach stale |
| **Tools** | Filterable tools table, inline actions, bulk actions, collapsed import | admin.py tools + import tabs |
| **People** | Unified maker+user table, Stripe status, magic links, nudge actions | admin.py makers + analytics users/growth + outreach makers/magic |
| **Content** | Collections, Stacks, Reviews (3 collapsible sections) | admin.py collections + stacks + reviews tabs |
| **Growth** | Sub-nav: Traffic & Funnels, Search, Email, Social | All of admin_analytics + outreach email/social |

### Pending Alert Bar

Orange bar shown on ALL tabs when pending tools exist:
```
 3 tools pending review  [Review Now]
```

---

## Overview Tab

### KPI Grid (2x4)

Row 1: Tools (total), Makers (claimed), Users (accounts), Revenue (all-time)
Row 2: Pending (orange if >0), Unclaimed, Agent Recs (7d), Pro Subscribers

Each card is clickable — links to the relevant filtered tab.

### Pending Queue

If pending tools exist, show them directly on Overview with approve/reject buttons. Quick-action cards, not a full table.

### Alerts Strip

Compact row of actionable items:
- Search queries with 0 results → Growth tab
- Stale tools (>60d no update) → Tools filtered
- Makers needing Stripe → People filtered

### Recent Activity

Last 10 events timeline: new submissions, purchases, reviews, claims. Simple list with timestamp + description.

---

## Tools Tab

### Filter Bar

Pill-style toggle filters (not dropdowns):
- Status: All | Pending | Approved | Rejected
- Filter: All | Unclaimed | Verified | Boosted
- Text search input

### Table

Same columns as current, but with:
- Alternating row backgrounds
- Icon buttons for actions (checkmark, X, star, boost, trash) with tooltips
- Sticky table header

### Import

Collapsible section at the bottom of the Tools tab. Collapsed by default. Click to expand the JSON import form.

### Bulk Actions

Bar appears contextually: "Approve All Pending (3)", "Generate All Magic Links"

---

## People Tab

### Data Model

LEFT JOIN `users` onto `makers` + include users without maker profiles. One row per person.

### Table Columns

| Name | Email | Role | Tools | Stripe | Last Active | Actions |
|------|-------|------|-------|--------|-------------|---------|
| Jane Doe | jane@... | Maker | 3 | Connected | 2d ago | Nudge |
| Bob Smith | bob@... | Subscriber | — | — | 5d ago | — |
| (Unclaimed) | — | Unclaimed Maker | 1 | — | Never | Magic Link |

### Role Badges

- **Maker** (green) — claimed maker profile with tools
- **Subscriber** (blue) — user account, no maker profile
- **Buyer** (purple) — has made a purchase
- **Unclaimed** (grey) — maker profile with no linked user

A person can have multiple badges.

### Filters

Role dropdown, Stripe status, Activity status (active/idle/dormant)

### Actions

- Magic link generation (unclaimed makers)
- Stripe nudge email (makers without Stripe)
- View profile link

---

## Content Tab

Three collapsible sections with toggle arrows:

```
 Collections (4)
  [Create form] [Collection list with tools]

 Stacks (3)        <- collapsed by default

 Reviews (12)      <- collapsed by default
```

Each section works identically to current admin.py tabs.

---

## Growth Tab

### Sub-Navigation

Lighter style than main tabs — text links with underline:
```
Traffic & Funnels  |  Search  |  Email  |  Social
```

### Traffic & Funnels

- Period filter pills (Today, 7d, 30d, All time)
- KPI row: Page Views, Unique Visitors, Outbound Clicks, MRR
- Traffic chart (daily views, last 14 days)
- Top pages, top referrers, recent visitors tables
- Platform funnel visualization
- Per-tool funnel table
- Maker leaderboard

### Search

- Search volume card
- Search gap analysis (0-result queries)
- Top search queries

### Email

- All email blast panels: TOTW, Weekly Digest, Launch Day, Maker Countdown, Marketplace Preview, Custom
- Subscriber count badge

### Social

- Social media kit content

---

## Visual Styling

### Tab Bar

- Active tab: navy bottom border, bold text
- Inactive: muted text, no border
- Remove terracotta accent from admin tabs

### KPI Cards

- Subtle left border color coding:
  - Green: healthy metrics
  - Orange: needs attention (pending, unclaimed)
  - Blue: informational
  - Cyan (accent): agent-related metrics

### Tables

- Alternating row backgrounds (cream-dark on even rows)
- Sticky thead
- Compact padding
- Icon action buttons with tooltips

### Alert Bar

- Warm orange background (#FFF7ED)
- Orange left border
- Clear CTA button aligned right

### Section Headers

- Consistent h2 with subtle bottom border
- Count badges inline

---

## File Structure

### Route Changes

- `admin.py` — sole route handler for `/admin`. Renders Overview, Tools, People tabs.
- `admin_analytics.py` — no routes. Exports rendering helpers (`render_traffic_section`, `render_funnels_section`, `render_search_section`) called by admin.py for Growth tab.
- `admin_outreach.py` — no routes. Exports rendering helpers (`render_email_panel`, `render_social_panel`, `render_magic_links_section`) called by admin.py for Growth tab + People tab.

### Redirects

- `GET /admin/analytics` → 302 to `/admin?tab=growth`
- `GET /admin/outreach` → 302 to `/admin?tab=growth&section=email`
- `POST /admin/outreach` → handled by admin.py POST handler
- `POST /admin/outreach/stripe-nudge` → handled by admin.py POST handler

### Shared Helpers

New helper functions in admin.py:
- `_render_kpi_card(label, value, color, link)` — reusable KPI card
- `_render_pending_alert(count)` — the orange alert bar
- `_render_pill_filter(options, active)` — pill-style filter toggles
- `_render_icon_button(icon, action, tooltip)` — compact action button

---

## Data Queries

### People Tab Query

```sql
SELECT
    COALESCE(u.name, m.name) as name,
    u.email,
    m.id as maker_id,
    m.slug as maker_slug,
    m.indie_status,
    u.id as user_id,
    COUNT(t.id) as tool_count,
    m.stripe_account_id,
    COALESCE(u.created_at, m.created_at) as joined,
    MAX(t.updated_at) as last_active
FROM makers m
LEFT JOIN users u ON u.maker_id = m.id
LEFT JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
GROUP BY m.id

UNION

SELECT
    u.name,
    u.email,
    NULL as maker_id,
    NULL as maker_slug,
    NULL as indie_status,
    u.id as user_id,
    0 as tool_count,
    NULL as stripe_account_id,
    u.created_at as joined,
    u.created_at as last_active
FROM users u
WHERE u.maker_id IS NULL
ORDER BY last_active DESC
```

### Overview Alerts Query

```sql
-- Stale tools (>60 days since update)
SELECT COUNT(*) FROM tools WHERE status='approved'
    AND updated_at < datetime('now', '-60 days');

-- Makers needing Stripe (have priced tools, no stripe)
SELECT COUNT(*) FROM makers m
    JOIN tools t ON t.maker_id = m.id
    WHERE t.price_pence > 0 AND (m.stripe_account_id IS NULL OR m.stripe_account_id = '');

-- Zero-result searches (last 7 days)
SELECT COUNT(DISTINCT query) FROM search_logs
    WHERE results_count = 0 AND created_at > datetime('now', '-7 days');
```
