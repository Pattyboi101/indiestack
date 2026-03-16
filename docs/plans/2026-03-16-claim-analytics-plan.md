# Claim-to-Reveal Analytics Wall — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Gate tool analytics behind claiming, creating a funnel: teaser → free claim → Pro upgrade.

**Architecture:** Server-side data wall — tool.py and dashboard.py check `claimed_at` / ownership before rendering analytics. No new tables. Claim flow adds email domain verification for instant claims. Three tiers: unclaimed (teaser only), claimed-free (headline numbers), claimed-Pro (full intelligence).

**Tech Stack:** Python 3 / FastAPI / SQLite / aiosqlite / server-side HTML (f-strings)

**Design doc:** `docs/plans/2026-03-16-claim-analytics-design.md`

---

### Task 1: Gate analytics on tool detail page

The tool detail page (`tool.py`) currently shows recommendation count and success rate badges publicly for all tools (lines 184-216). We need to hide these for unclaimed tools and show a teaser + claim CTA instead.

**Files:**
- Modify: `src/indiestack/routes/tool.py:173-216` (token_hint_html section)
- Modify: `src/indiestack/routes/tool.py:289-316` (claim_html section — move higher)

**Step 1: Understand the current code**

In `tool.py`, the `tool_detail` function (line 64) fetches `success_rate` and `recommendation_count` at lines 100-101. These are used to build `mcp_badge` (line 184) and `outcome_badge` (line 191). The claim CTA is built at line 289.

The tool dict has `claimed_at` (set when claimed) and `maker_id` (set when claimed). The viewer is in `user` (from `request.state.user`).

**Step 2: Add ownership check variables**

After line 102 (`click_count = ...`), add:

```python
    # Analytics wall — determine viewer's relationship to this tool
    is_tool_owner = (
        user and user.get('maker_id')
        and tool.get('maker_id')
        and user['maker_id'] == tool['maker_id']
    )
    is_claimed = bool(tool.get('claimed_at'))
    show_analytics = is_claimed and is_tool_owner
```

**Step 3: Wrap analytics badges in ownership check**

Replace the analytics badge section (lines 173-216). The `token_hint_html` (token savings) stays public. Only `mcp_badge` and `outcome_badge` get gated:

```python
    # Token savings hint — always public
    token_hint_html = ''
    cat_slug_val = str(tool.get('category_slug', ''))
    token_cost = CATEGORY_TOKEN_COSTS.get(cat_slug_val, 50_000)
    token_k = token_cost // 1000
    citation_count = await get_tool_total_citations(db, tool_id)
    mcp_views = int(tool.get('mcp_view_count', 0))
    ai_rec_count = max(citation_count, mcp_views)

    # Analytics badges — gated by claim status
    mcp_badge = ''
    outcome_badge = ''
    analytics_teaser = ''

    if show_analytics:
        # Owner sees full analytics
        if ai_rec_count > 0:
            mcp_badge = f'''
            <div style="margin-top:8px;padding:10px 16px;background:linear-gradient(135deg,var(--info-bg),var(--info-bg));border-radius:var(--radius-sm);
                        display:inline-flex;align-items:center;gap:8px;font-size:14px;color:var(--info-text);border:1px solid var(--info-border);font-weight:600;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                Recommended by AI agents {ai_rec_count} time{'s' if ai_rec_count != 1 else ''}
            </div>'''
        if success_rate['total'] > 0:
            rate_color = 'var(--success-text)' if success_rate['rate'] >= 70 else 'var(--warning-text)' if success_rate['rate'] >= 40 else 'var(--error-text)'
            outcome_badge = f'''
            <div style="margin-top:8px;padding:8px 16px;background:var(--card-bg);border-radius:var(--radius-sm);
                        display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--ink-light);border:1px solid var(--border);">
                <span style="font-size:16px;">&#127919;</span>
                <span style="font-weight:600;color:{rate_color};">{success_rate['rate']}%</span> agent success rate
                <span style="color:var(--ink-muted);font-size:12px;">({success_rate['total']} report{'s' if success_rate['total'] != 1 else ''})</span>
            </div>'''
        elif recommendation_count > 0:
            outcome_badge = f'''
            <div style="margin-top:8px;padding:8px 16px;background:var(--card-bg);border-radius:var(--radius-sm);
                        display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--ink-muted);border:1px solid var(--border);">
                <span style="font-size:16px;">&#127919;</span>
                Recommended {recommendation_count} time{'s' if recommendation_count != 1 else ''} &mdash; no outcome reports yet
            </div>'''
    elif is_claimed:
        # Claimed but not the owner — show teaser (no numbers)
        if ai_rec_count > 0:
            analytics_teaser = '''
            <div style="margin-top:8px;padding:10px 16px;background:var(--info-bg);border-radius:var(--radius-sm);
                        display:inline-flex;align-items:center;gap:8px;font-size:14px;color:var(--info-text);border:1px solid var(--info-border);">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                AI agents recommend this tool
            </div>'''
    else:
        # Unclaimed — teaser + claim nudge
        if ai_rec_count > 0:
            analytics_teaser = f'''
            <div style="margin-top:8px;padding:12px 16px;background:linear-gradient(135deg,var(--info-bg),var(--cream-dark));border-radius:var(--radius-sm);
                        border:1px solid var(--info-border);">
                <div style="display:flex;align-items:center;gap:8px;font-size:14px;color:var(--info-text);font-weight:600;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                    AI agents are recommending this tool
                </div>
                <p style="font-size:13px;color:var(--ink-muted);margin-top:4px;">Claim this listing to see how many times and your success rate.</p>
            </div>'''

    token_hint_html = f'''
        <div style="margin-top:16px;padding:8px 16px;background:var(--cream-dark);border-radius:var(--radius-sm);
                    display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--ink-light);">
            <span style="color:var(--slate);display:inline-block;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg></span>
            Using this saves ~{token_k}k tokens vs building from scratch
        </div>
        {mcp_badge}
        {outcome_badge}
        {analytics_teaser}
    '''
```

**Step 4: Update claim CTA copy**

The existing claim CTA (line 305-316) should mention analytics more prominently. Update the description text at line 311:

```python
# Old:
<p style="font-size:13px;color:var(--ink-light);margin-bottom:12px;">This is listed for free on IndieStack &mdash; no commission, no fees. Claim it to update details and track how often AI agents recommend it.</p>

# New:
<p style="font-size:13px;color:var(--ink-light);margin-bottom:12px;">Claim your listing to see exactly how many AI agents recommend this tool, your success rate, and more. Free, no commission, no fees.</p>
```

**Step 5: Add "View full analytics" link for Pro owners**

After the `outcome_badge` section for `show_analytics`, if the user is also Pro, add a dashboard link. Inside the `if show_analytics:` block, after the outcome_badge logic, add:

```python
        # Pro owners get dashboard link
        is_pro = await check_pro(db, user['id'])
        if is_pro:
            outcome_badge += f'''
            <div style="margin-top:8px;">
                <a href="/dashboard#ai-distribution" style="font-size:13px;color:var(--accent);font-weight:600;text-decoration:none;">
                    View full analytics &rarr;
                </a>
            </div>'''
```

Note: Import `check_pro` in tool.py if not already imported. Check imports at top of file.

**Step 6: Test manually**

1. Visit `/tool/{any-unclaimed-tool-with-recommendations}` — should see teaser, no numbers
2. Log in as the tool owner — should see full numbers
3. Log in as someone else — should see teaser for unclaimed, or "AI agents recommend this tool" for claimed-by-other
4. Check that token savings hint still shows for everyone

**Step 7: Commit**

```bash
git add src/indiestack/routes/tool.py
git commit -m "feat: gate analytics badges behind claim status on tool detail page"
```

---

### Task 2: Update dashboard with two-layer gating

The dashboard (`dashboard.py`) shows AI Distribution Intelligence at line 252+, currently gated only by Pro status. We need to add a claim-ownership layer: no claimed tools = empty state, claimed-free = headline numbers, claimed-Pro = full intelligence.

**Files:**
- Modify: `src/indiestack/routes/dashboard.py:82-100` (stats section — add claimed tools check)
- Modify: `src/indiestack/routes/dashboard.py:252-351` (AI intel section — add claim gating)

**Step 1: Add `has_claimed_tools` check**

After line 91 (`is_pro = await check_pro(db, user['id'])`), add:

```python
    # Check if user has any claimed tools
    has_claimed_tools = False
    if maker_id:
        _claimed_cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM tools WHERE maker_id = ? AND claimed_at IS NOT NULL AND status = 'approved'",
            (maker_id,),
        )
        _claimed_row = await _claimed_cursor.fetchone()
        has_claimed_tools = (_claimed_row['cnt'] or 0) > 0
```

**Step 2: Add headline analytics for claimed-free users**

The current AI intel section (line 252-351) is only built when `user.get('maker_id')` exists. We need to restructure it:

Before line 252 (`# ── AI Distribution Intelligence`), the section currently checks `if user.get('maker_id'):` at line 254. Replace the entire AI intel section (lines 252-351) with three branches:

```python
    # ── AI Distribution Intelligence ──────────────────────────
    ai_intel_html = ''

    if not has_claimed_tools:
        # No claimed tools — show empty state with search
        ai_intel_html = '''
        <div id="ai-distribution" style="margin-top:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                &#129302; AI Distribution Intelligence
            </h2>
            <div class="card" style="text-align:center;padding:48px 24px;">
                <p style="font-size:32px;margin-bottom:12px;">&#128202;</p>
                <p style="font-weight:700;font-size:16px;color:var(--ink);margin-bottom:4px;">Claim your first tool to unlock analytics</p>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">See how often AI agents recommend your tools, your success rate, and which queries find you.</p>
                <a href="/" style="display:inline-block;padding:10px 24px;background:var(--accent);color:#0F1D30;border-radius:8px;font-size:14px;font-weight:600;text-decoration:none;">
                    Find Your Tool
                </a>
            </div>
        </div>'''

    elif maker_id:
        # Has claimed tools — show analytics (full or gated by Pro)
        queries = await get_maker_query_intelligence(db, maker_id, days=30)
        agents = await get_maker_agent_breakdown(db, maker_id, days=30)
        trend = await get_maker_daily_trend(db, maker_id, days=30)

        # Headline stats (visible to all claimed users)
        _total_recs = sum(a['count'] for a in agents) if agents else 0
        _headline_html = ''
        if _total_recs > 0 or maker_success_rate:
            _sr_text = f'{maker_success_rate}% success rate' if maker_success_rate else 'No outcome reports yet'
            _headline_html = f'''
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px;">
                <div class="card" style="padding:20px;text-align:center;">
                    <p style="font-size:28px;font-weight:700;color:var(--accent);">{_total_recs}</p>
                    <p style="font-size:13px;color:var(--ink-muted);">AI Recommendations (30d)</p>
                </div>
                <div class="card" style="padding:20px;text-align:center;">
                    <p style="font-size:28px;font-weight:700;color:var(--ink);">{_sr_text.split('%')[0]}%</p>
                    <p style="font-size:13px;color:var(--ink-muted);">Agent Success Rate</p>
                </div>
            </div>''' if maker_success_rate else f'''
            <div class="card" style="padding:20px;text-align:center;margin-bottom:24px;">
                <p style="font-size:28px;font-weight:700;color:var(--accent);">{_total_recs}</p>
                <p style="font-size:13px;color:var(--ink-muted);">AI Recommendations (30d)</p>
            </div>'''
```

Then keep the existing query intelligence table and agent breakdown code (lines 259-351) exactly as-is — they already gate on `is_pro`. Just make sure the whole section is inside the `elif maker_id:` block.

The full structure becomes:
```
if not has_claimed_tools → empty state
elif maker_id → headline stats (always) + existing intel section (Pro-gated)
```

After the `_headline_html` assignment, continue with the existing query_rows / agent_rows / sparkline code, then build ai_intel_html as:

```python
        # ... (existing query_rows, agent_rows, trend_html code unchanged) ...

        if queries or agents:
            # (existing _agent_card_content logic — unchanged, already Pro-gated)
            ...

            ai_intel_html = f'''
            <div id="ai-distribution" style="margin-top:32px;">
                <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                    &#129302; AI Distribution Intelligence <span style="font-size:13px;color:var(--ink-muted);font-weight:400;">(last 30 days)</span>
                </h2>
                {_headline_html}
                <style>.ai-intel-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}}@media(max-width:600px){{.ai-intel-grid{{grid-template-columns:1fr}}}}</style>
                <div class="ai-intel-grid">
                    ... (existing cards unchanged) ...
                </div>
            </div>'''
        elif _headline_html:
            # Has recommendations but no query/agent detail yet
            ai_intel_html = f'''
            <div id="ai-distribution" style="margin-top:32px;">
                <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                    &#129302; AI Distribution Intelligence <span style="font-size:13px;color:var(--ink-muted);font-weight:400;">(last 30 days)</span>
                </h2>
                {_headline_html}
                <p style="color:var(--ink-muted);font-size:13px;">As agents recommend your tools more, detailed breakdowns will appear here.</p>
            </div>'''
```

**Step 3: Test manually**

1. Log in as a user with NO claimed tools → should see "Claim your first tool" empty state
2. Log in as a user with claimed tools, no Pro → should see headline numbers + blurred agent breakdown
3. Log in as a Pro user with claimed tools → full dashboard as before

**Step 4: Commit**

```bash
git add src/indiestack/routes/dashboard.py
git commit -m "feat: add claim-gated analytics layer to maker dashboard"
```

---

### Task 3: Email-verified claim flow with domain matching

Upgrade the claim endpoint to support instant claims via email domain verification. If the user's email domain matches the tool's URL domain, send a magic link for instant claim. Otherwise, fall back to admin approval.

**Files:**
- Modify: `src/indiestack/main.py:2897-2923` (existing `/api/claim` endpoint)
- Modify: `src/indiestack/db.py` (add `create_claim_verification_token` and `verify_claim_by_token` functions)
- Add new endpoint: `/api/claim/verify/{token}` in `main.py`

**Step 1: Add helper to extract domain from URL**

In `db.py`, near the other claim functions (around line 4383), add:

```python
def extract_domain(url: str) -> str:
    """Extract base domain from a URL. 'https://www.example.com/path' → 'example.com'"""
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url if '://' in url else f'https://{url}')
        host = parsed.hostname or ''
        # Strip www prefix
        if host.startswith('www.'):
            host = host[4:]
        return host.lower()
    except Exception:
        return ''
```

**Step 2: Add claim verification token functions**

In `db.py`, after the `extract_domain` function:

```python
async def create_claim_verification_token(db, tool_id: int, user_id: int, email: str) -> str:
    """Create a verification token for email-based claim. Expires in 24 hours."""
    import secrets
    token = secrets.token_urlsafe(32)
    await db.execute(
        "INSERT INTO claim_tokens (tool_id, user_id, token, expires_at) VALUES (?, ?, ?, datetime('now', '+1 day'))",
        (tool_id, user_id, token),
    )
    await db.commit()
    return token


async def complete_claim(db, tool_id: int, user_id: int):
    """Finalize a tool claim — set maker_id, claimed_at, and user role."""
    # Get or create maker for this user
    cursor = await db.execute("SELECT name, email FROM users WHERE id = ?", (user_id,))
    user_row = await cursor.fetchone()
    maker_name = user_row['name'] or user_row['email'].split('@')[0]

    from indiestack.db import get_or_create_maker
    maker_id = await get_or_create_maker(db, maker_name)

    await db.execute(
        "UPDATE tools SET maker_id = ?, claimed_at = CURRENT_TIMESTAMP WHERE id = ? AND claimed_at IS NULL",
        (maker_id, tool_id),
    )
    # Update user to maker role if not already
    await db.execute(
        "UPDATE users SET maker_id = COALESCE(maker_id, ?), role = 'maker' WHERE id = ?",
        (maker_id, user_id),
    )
    await db.commit()
    return maker_id
```

**Step 3: Update the `/api/claim` endpoint**

Replace the existing `/api/claim` handler (main.py lines 2897-2923) with:

```python
@app.post("/api/claim")
async def api_claim(request: Request):
    """Claim a tool — instant if email domain matches, otherwise admin review."""
    from fastapi.responses import RedirectResponse
    user = request.state.user
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    try:
        form = await request.form()
        tool_id = int(form.get("tool_id", 0))
    except (ValueError, TypeError):
        return RedirectResponse(url="/", status_code=303)

    d = request.state.db
    tool = await db.get_tool_by_id(d, tool_id)
    if not tool or tool.get('claimed_at'):
        return RedirectResponse(url=f"/tool/{tool['slug']}" if tool else "/", status_code=303)

    # Check if user's email domain matches tool's URL domain
    user_domain = user['email'].split('@')[1].lower() if '@' in user['email'] else ''
    tool_domain = db.extract_domain(tool.get('url', ''))

    if user_domain and tool_domain and user_domain == tool_domain:
        # Domain match — send verification email with magic link
        token = await db.create_claim_verification_token(d, tool_id, user['id'], user['email'])
        base_url = str(request.base_url).rstrip("/")
        verify_url = f"{base_url}/api/claim/verify/{token}"

        from indiestack.email import send_email
        await send_email(
            to=user['email'],
            subject=f"Verify your claim for {tool['name']} on IndieStack",
            html_body=f"""
            <h2>Claim {tool['name']}</h2>
            <p>Click below to verify you own this tool and unlock your analytics dashboard:</p>
            <p><a href="{verify_url}" style="display:inline-block;padding:12px 24px;background:#00D4F5;color:#0F1D30;border-radius:8px;font-weight:600;text-decoration:none;">Verify &amp; Claim</a></p>
            <p style="color:#888;font-size:13px;">This link expires in 24 hours.</p>
            """,
        )
        return RedirectResponse(url=f"/tool/{tool['slug']}?claim_email_sent=1", status_code=303)
    else:
        # No domain match — fall back to admin approval
        await d.execute(
            "INSERT OR IGNORE INTO claim_requests (tool_id, user_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (tool_id, user['id']),
        )
        await d.commit()
        return RedirectResponse(url=f"/tool/{tool['slug']}?claim_requested=1", status_code=303)
```

**Step 4: Add the verification endpoint**

After the `/api/claim` endpoint in main.py:

```python
@app.get("/api/claim/verify/{token}")
async def api_claim_verify(request: Request, token: str):
    """Verify a claim via email link — instant claim on valid token."""
    from fastapi.responses import RedirectResponse
    d = request.state.db

    result = await db.verify_claim_token(d, token)
    if not result:
        return HTMLResponse(page_shell("Invalid Link",
            '<div class="container" style="text-align:center;padding:64px 0;">'
            '<h1 style="font-family:var(--font-display);">Invalid or Expired Link</h1>'
            '<p class="text-muted mt-4">This claim link has expired or already been used.</p>'
            '<a href="/" class="btn btn-primary mt-4">Back to Home</a></div>',
            user=request.state.user), status_code=400)

    tool_id = result['tool_id']
    user_id = result['user_id']

    # Complete the claim
    await db.complete_claim(d, tool_id, user_id)

    # Get tool slug for redirect
    tool = await db.get_tool_by_id(d, tool_id)
    slug = tool['slug'] if tool else ''

    return RedirectResponse(url=f"/tool/{slug}?claimed=1", status_code=303)
```

**Step 5: Add success messages to tool detail page**

In `tool.py`, after the claim_html section, add handling for the query params:

```python
    # Claim status messages
    claim_message = ''
    if request.query_params.get('claim_email_sent'):
        claim_message = '''
        <div style="margin:16px 0;padding:16px 24px;background:var(--success-bg);border:1px solid var(--success-border);border-radius:var(--radius-sm);color:var(--success-text);font-size:14px;">
            &#9989; Verification email sent! Check your inbox and click the link to claim this listing.
        </div>'''
    elif request.query_params.get('claimed'):
        claim_message = '''
        <div style="margin:16px 0;padding:16px 24px;background:var(--success-bg);border:1px solid var(--success-border);border-radius:var(--radius-sm);color:var(--success-text);font-size:14px;">
            &#127881; You've claimed this listing! Visit your <a href="/dashboard" style="color:var(--success-text);font-weight:600;">dashboard</a> to see your analytics.
        </div>'''
    elif request.query_params.get('claim_requested'):
        claim_message = '''
        <div style="margin:16px 0;padding:16px 24px;background:var(--info-bg);border:1px solid var(--info-border);border-radius:var(--radius-sm);color:var(--info-text);font-size:14px;">
            &#128233; Claim request submitted! We'll review it within 24 hours.
        </div>'''
```

Then include `{claim_message}` in the page HTML above the tool details section. Find where `claim_html` is inserted in the template and place `{claim_message}` right before it.

**Step 6: Test manually**

1. Log in with an email whose domain matches a tool's URL → should receive verification email
2. Click verification link → should claim the tool, redirect with `?claimed=1`
3. Log in with a non-matching email → should fall back to admin approval with `?claim_requested=1`
4. Try to claim an already-claimed tool → should redirect without action

**Step 7: Commit**

```bash
git add src/indiestack/routes/tool.py src/indiestack/main.py src/indiestack/db.py
git commit -m "feat: email-verified claim flow with domain matching"
```

---

### Task 4: Remove dead boost code

Clean up remnant boost code that's no longer used.

**Files:**
- Modify: `src/indiestack/main.py:2926-2970` (remove `/api/claim-and-boost` endpoint)
- Note: Don't remove boost DB columns/functions yet — that requires a migration and is lower priority. Just remove the dead endpoint.

**Step 1: Delete the `/api/claim-and-boost` endpoint**

In `main.py`, find and delete the entire `api_claim_and_boost` function (starts at line 2926, `@app.post("/api/claim-and-boost")`). Delete from `@app.post("/api/claim-and-boost")` through to the next route decorator or blank line separator.

**Step 2: Remove the boost_html variable from tool.py**

In `tool.py`, find and remove:
```python
    # Boost upsell — hidden for now (re-enable when trust is established)
    boost_html = ''
```

And remove any `{boost_html}` references in the template string.

**Step 3: Commit**

```bash
git add src/indiestack/main.py src/indiestack/routes/tool.py
git commit -m "chore: remove dead claim-and-boost endpoint and boost_html"
```

---

### Task 5: Deploy and verify

**Step 1: Run smoke test**

```bash
cd ~/indiestack && python3 smoke_test.py
```

Expected: All tests pass.

**Step 2: Deploy**

```bash
cd ~/indiestack && ~/.fly/bin/flyctl deploy --remote-only
```

**Step 3: Verify live**

1. Visit an unclaimed tool with recommendations — confirm teaser shows, no numbers
2. Visit a claimed tool as the owner — confirm numbers show
3. Test claim flow on a test tool
4. Check dashboard as a maker — confirm headline stats show

**Step 4: Commit any fixes**

If any issues found during verification, fix and commit.

---

## Summary

| Task | What | Files |
|------|------|-------|
| 1 | Gate analytics on tool detail page | tool.py |
| 2 | Two-layer dashboard gating | dashboard.py |
| 3 | Email-verified claim flow | main.py, db.py, tool.py |
| 4 | Remove dead boost code | main.py, tool.py |
| 5 | Deploy and verify | — |

Total: 5 tasks, touches 4 files. No new tables, no migrations.
