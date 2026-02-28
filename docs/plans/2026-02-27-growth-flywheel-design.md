# IndieStack Growth Flywheel — Design Doc

**Date**: 2026-02-27
**Inspired by**: Uneed.best (Thomas Sanlis) — directory → launch platform, $870 → $6,700/mo via 7 interconnected growth channels

## Context

IndieStack has ~4,500 weekly visitors, 356 tools, 20 users, 0 marketplace purchases. Most growth infrastructure exists (badges, SEO pages, newsletter, milestone cards) but operates in silos. Uneed's key insight: connect channels into a self-reinforcing flywheel where each action feeds the next.

**Goal**: Wire existing pieces into an automated flywheel + launch week extras. Ed handles social, code handles automation.

## The Flywheel

```
Maker submits → Instant reward (badges, milestone, share) [SHIPPED]
  → 48h later: "Your badge is ready" nudge email
  → Maker embeds badge on site/README
  → Badge = backlink to IndieStack
  → Backlinks boost SEO for /alternatives, /best/ pages
  → SEO brings new visitors
  → Visitors subscribe via click interstitial / newsletter
  → Auto weekly digest promotes Tool of the Week
  → TOTW winner gets email + badge + social assets
  → Winner embeds badge → cycle repeats
```

## Components

### 1. Auto Tool of the Week
- Background task runs daily, checks if Monday
- Selects top tool by 7-day outbound clicks (existing query in admin)
- Sets `tool_of_the_week` flag in DB
- Sends TOTW email to maker (existing template)
- Triggers weekly digest to all subscribers (existing template)
- File: `main.py` (new background task)

### 2. Badge Nudge Email
- New `badge_nudge_html(tool)` template in `email.py`
- Shows badge preview, HTML/Markdown/URL copy snippets
- "Add to your site — get discovered by AI coding assistants"
- Background task runs daily, finds tools approved 48-72h ago without nudge
- New column: `tools.badge_nudge_sent INTEGER DEFAULT 0`
- File: `email.py` (template), `main.py` (background task), `db.py` (migration)

### 3. Auto Weekly Digest
- Background task runs daily, checks if Friday
- Sends existing `weekly_digest_html()` to all subscribers
- Uses existing subscriber list + unsubscribe infrastructure
- File: `main.py` (new background task or extend ego ping pattern)

### 4. Ed's Social Kit
- New section on `/admin/outreach` page
- Auto-generates copy-paste content from DB:
  - TOTW tweet with Twitter intent URL
  - "New this week" tweet listing recent tools
  - Milestone celebration tweets
- File: `admin_outreach.py` (new section in GET handler)

### 5. Launch Week: Early Supporter Badge
- New `?style=early` on `/api/badge/{slug}.svg`
- Gold accent: "Early Supporter" | "IndieStack"
- Only for tools with `created_at < 2026-03-02`
- File: `main.py` (badge endpoint)

### 6. Launch Week: Pre-written Launch Thread
- Admin page section with auto-generated launch thread
- Pulls: tool count, maker count, category count, top 5 tools, growth stats
- Copy-paste format for Twitter thread + Reddit post
- File: `admin_outreach.py` (new section)

## Files Modified

| File | Changes |
|------|---------|
| `main.py` | 3 new background tasks (TOTW, badge nudge, digest), early supporter badge style |
| `email.py` | New `badge_nudge_html()` template |
| `db.py` | Migration: `badge_nudge_sent` column on tools |
| `admin_outreach.py` | Social kit section + launch thread generator |

## Verification

1. Syntax check all 4 files
2. Smoke test 37/37
3. Manual: check `/admin/outreach` shows social kit + launch thread
4. Manual: verify badge nudge email renders correctly (send test)
5. Manual: verify `?style=early` badge renders
6. Deploy
