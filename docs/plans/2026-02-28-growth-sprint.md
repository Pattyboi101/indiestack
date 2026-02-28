# Growth Sprint Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make IndieStack's existing 66 claimed tools visible to cold visitors, kill ghost-town signals, and prepare for Ed's outreach push.

**Architecture:** Four small edits across 4 files: add "Maker ✓" badge to tool cards (components.py), update landing page stats to show claimed count + live MCP counter (landing.py), boost claimed tools in trending sort (db.py), and reframe pricing page as "coming soon" waitlist (pricing.py). No new tables, no new routes, no new dependencies.

**Tech Stack:** Python/FastAPI, pure string HTML templates, SQLite, aiosqlite

---

### Task 1: "Maker ✓" badge on claimed tool cards

**Files:**
- Modify: `src/indiestack/routes/components.py:827-829`

**Step 1: Modify the badge logic in `tool_card()`**

The current code at line 827-829 shows "Community Listed" for unclaimed tools. Change it to also show "Maker ✓" for claimed tools.

Find this block:

```python
    # Show "Community Listed" for unclaimed tools (no claimed_at)
    if not tool.get('claimed_at') and not is_verified:
        badge += ' <span class="badge badge-muted" style="font-size:10px;">Community Listed</span>'
```

Replace with:

```python
    # Show claim status: "Maker ✓" for claimed tools, "Community Listed" for unclaimed
    if tool.get('claimed_at') and not is_verified:
        badge += ' <span class="badge badge-success" style="font-size:10px;">Maker &#10003;</span>'
    elif not tool.get('claimed_at') and not is_verified:
        badge += ' <span class="badge badge-muted" style="font-size:10px;">Community Listed</span>'
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read())"`
Expected: No output (clean parse)

**Step 3: Commit**

```bash
git add src/indiestack/routes/components.py
git commit -m "feat: show Maker ✓ badge on claimed tool cards"
```

---

### Task 2: Add claimed_count to landing page cache + update stats bar

**Files:**
- Modify: `src/indiestack/routes/landing.py:36-59` (cache block)
- Modify: `src/indiestack/routes/landing.py:119-123` (hero stats bar)
- Modify: `src/indiestack/routes/landing.py:213-219` (MCP walkthrough stats bar)

**Step 1: Add claimed_count query to the cache miss block**

In `src/indiestack/routes/landing.py`, find the cache miss block (around line 36-48). After the `mcp_views` query (line 45-46), add a new query:

```python
        _claimed = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE claimed_at IS NOT NULL AND status='approved'")
        claimed_count = (await _claimed.fetchone())['cnt']
```

**Step 2: Add claimed_count to the cache dict**

In the `_landing_cache['data']` dict (around line 50-58), add `'claimed_count': claimed_count,` after `'mcp_views': mcp_views,`.

**Step 3: Add claimed_count to the cache hit block**

In the cache hit block (around line 26-35), add: `claimed_count = cached.get('claimed_count', 0)` after the `search_trends` line.

**Step 4: Update the hero stats bar (around line 119-123)**

Find:
```python
        f'        <span>{tool_count} tools, hand-curated</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span>{search_stats["this_week"]} searches this week</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span style="color:var(--accent);">{mcp_views} AI agent lookups</span>'
```

Replace with:
```python
        f'        <span>{tool_count} tools</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span>{claimed_count} maker-verified</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span style="color:var(--accent);">{mcp_views:,} agent lookups</span>'
```

**Step 5: Update the MCP walkthrough stats bar (around line 213-219)**

Find:
```python
                <span><strong style="color:var(--accent);">{mcp_views}</strong> agent lookups</span>
                <span style="color:var(--border);">&middot;</span>
                <span><strong style="color:var(--ink);">{tool_count}</strong> tools indexed</span>
                <span style="color:var(--border);">&middot;</span>
                <span><strong style="color:var(--ink);">{search_stats["this_week"]}</strong> searches this week</span>
```

Replace with:
```python
                <span><strong style="color:var(--accent);">{mcp_views:,}</strong> agent lookups</span>
                <span style="color:var(--border);">&middot;</span>
                <span><strong style="color:var(--ink);">{tool_count}</strong> tools</span>
                <span style="color:var(--border);">&middot;</span>
                <span><strong style="color:var(--ink);">{claimed_count}</strong> maker-verified</span>
```

**Step 6: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read())"`
Expected: No output (clean parse)

**Step 7: Commit**

```bash
git add src/indiestack/routes/landing.py
git commit -m "feat: show claimed count and live MCP counter on landing page"
```

---

### Task 3: Boost claimed tools in trending sort

**Files:**
- Modify: `src/indiestack/db.py:2930-2947` (`get_trending_scored()`)

**Step 1: Add claim boost to the heat score SQL**

In `src/indiestack/db.py`, find the `get_trending_scored()` function (line 2927). The current heat score formula is on lines 2933-2934:

```python
               (t.upvote_count + COALESCE(v.view_count, 0)) * 1.0 /
               MAX(1.0, POWER(MAX(1, (julianday('now') - julianday(t.created_at)) * 24), 1.5)) as heat_score,
```

Replace with:

```python
               (t.upvote_count + COALESCE(v.view_count, 0) + (CASE WHEN t.claimed_at IS NOT NULL THEN 20 ELSE 0 END)) * 1.0 /
               MAX(1.0, POWER(MAX(1, (julianday('now') - julianday(t.created_at)) * 24), 1.5)) as heat_score,
```

This adds 20 points to the numerator for claimed tools, giving them a meaningful boost without completely overriding organic engagement.

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())"`
Expected: No output (clean parse)

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: boost claimed tools in trending sort"
```

---

### Task 4: Reframe pricing page as "Coming Soon" waitlist

**Files:**
- Modify: `src/indiestack/routes/pricing.py:68-97` (Pro tier card)

**Step 1: Replace the Pro tier CTA with a waitlist**

In `src/indiestack/routes/pricing.py`, find the Pro tier card (line 68-98). Replace the Pro tier `<div>` (lines 68-98) with a version that keeps the feature list but replaces the purchase button with a "Coming Soon" waitlist.

Find the Pro tier card starting at line 68:

```python
            <!-- Pro Tier -->
            <div class="card" style="padding:32px;border-color:var(--gold);background:linear-gradient(180deg,var(--warning-bg) 0%,white 30%);position:relative;">
                <span style="position:absolute;top:-12px;right:16px;font-size:11px;font-weight:700;color:var(--gold-dark);
                             background:linear-gradient(135deg,var(--gold-light),var(--gold));padding:4px 16px;
                             border-radius:999px;">RECOMMENDED</span>
```

Replace `RECOMMENDED` badge text with `COMING SOON`:

```python
                             border-radius:999px;">COMING SOON</span>
```

Then find the CTA button block at line 97. Replace the entire conditional:

```python
                {'<span class="btn btn-secondary" style="width:100%;justify-content:center;padding:12px;opacity:0.7;cursor:default;">Current Plan</span>' if is_pro else '<a href="/api/subscribe" class="btn" style="width:100%;justify-content:center;padding:12px;background:linear-gradient(135deg,var(--gold),var(--gold-light));color:var(--gold-dark);font-weight:700;border:1px solid var(--gold);">Upgrade to Pro</a>' if user else '<a href="/signup?next=pricing" class="btn" style="width:100%;justify-content:center;padding:12px;background:linear-gradient(135deg,var(--gold),var(--gold-light));color:var(--gold-dark);font-weight:700;border:1px solid var(--gold);">Sign Up &amp; Go Pro</a>'}
```

Replace with:

```python
                {'<span class="btn btn-secondary" style="width:100%;justify-content:center;padding:12px;opacity:0.7;cursor:default;">Current Plan</span>' if is_pro else '<a href="/signup" class="btn" style="width:100%;justify-content:center;padding:12px;background:linear-gradient(135deg,var(--gold),var(--gold-light));color:var(--gold-dark);font-weight:700;border:1px solid var(--gold);">Join the Waitlist</a>'}
```

**Step 2: Update the billing note at the bottom (line 101-103)**

Find:
```python
        <p style="text-align:center;color:var(--ink-muted);font-size:13px;margin-top:24px;">
            All prices in GBP. Pro subscription billed monthly via Stripe. Cancel anytime.
        </p>
```

Replace with:
```python
        <p style="text-align:center;color:var(--ink-muted);font-size:13px;margin-top:24px;">
            Pro launching soon. Sign up free to be first in line when it goes live.
        </p>
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/pricing.py').read())"`
Expected: No output (clean parse)

**Step 4: Commit**

```bash
git add src/indiestack/routes/pricing.py
git commit -m "feat: reframe Pro pricing as coming-soon waitlist"
```

---

### Task 5: Smoke test and deploy

**Step 1: Run all syntax checks**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/routes/pricing.py').read())" && \
echo "All OK"
```

Expected: `All OK`

**Step 2: Run smoke test**

```bash
python3 smoke_test.py
```

Expected: `38 passed, 0 failed / 38 total`

**Step 3: Deploy**

```bash
~/.fly/bin/flyctl deploy --remote-only
```

**Step 4: Manual verification**

1. Visit https://indiestack.fly.dev/ — hero stats bar shows `{N} tools | {M} maker-verified | {X,XXX} agent lookups`
2. Scroll to MCP walkthrough — stats bar shows `{X,XXX} agent lookups · {N} tools · {M} maker-verified`
3. Visit https://indiestack.fly.dev/explore — claimed tools show green "Maker ✓" badge, unclaimed show gray "Community Listed"
4. Check that claimed tools (like Simple Analytics, Coolify) appear near the top of trending sort
5. Visit https://indiestack.fly.dev/pricing — Pro card shows "COMING SOON" badge and "Join the Waitlist" button
6. Check dark mode renders correctly for all changes

**Step 5: Commit any fixes and redeploy if needed**

---

### Non-Code Tasks (Ed + Pat, manual)

These are not implementation tasks — they're manual actions listed here for completeness:

1. **Seed 5-10 real reviews** — Pat and Ed log in to their accounts and write honest 2-3 sentence reviews on tools they actually use (Simple Analytics, Supabase, Cal.com, Resend, Ghost, Coolify)
2. **Blog posts** — Ed writes 2-3 "Best X alternatives" posts or the blog link is removed from nav (in `components.py` lines 507 and 552)
3. **MCP directory submissions** — Ed submits IndieStack MCP server to Smithery, Glama, mcp.so, awesome-mcp-servers
4. **Daily claim outreach** — Ed starts 10 DMs/day routine using admin outreach tab magic claim links
