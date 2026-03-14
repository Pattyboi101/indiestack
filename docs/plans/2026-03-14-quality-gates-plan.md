# Quality Gates Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Protect IndieStack's curation signal from vibecoded SaaS spam with a five-layer defence system.

**Architecture:** DB migrations add enrichment columns → `validate_submission_quality()` gains subdomain filter + URL reachability → new async enrichment functions gather domain age, free tier, social proof → admin queue displays enrichment data with updated scoring → post-approval monitoring adds outcome-driven demotion and auto-archive. A static `/guidelines` page creates self-selection pressure.

**Tech Stack:** Python 3, FastAPI, aiosqlite, httpx, python-whois

---

### Task 1: DB Migration — Add Quality Gate Columns

**Files:**
- Modify: `src/indiestack/db.py:1075-1081` (after the `tool_of_the_week` migration block)

**Step 1: Add the migration block**

Add the following after the `tool_of_the_week` migration (around line 1081) in `init_db()`:

```python
        # Migration: quality gate enrichment columns
        for col, ddl in [
            ("domain_age_days", "ALTER TABLE tools ADD COLUMN domain_age_days INTEGER DEFAULT NULL"),
            ("has_free_tier", "ALTER TABLE tools ADD COLUMN has_free_tier INTEGER DEFAULT NULL"),
            ("social_mentions_count", "ALTER TABLE tools ADD COLUMN social_mentions_count INTEGER DEFAULT NULL"),
            ("rejection_reason", "ALTER TABLE tools ADD COLUMN rejection_reason TEXT DEFAULT NULL"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM tools LIMIT 1")
            except Exception:
                await db.execute(ddl)
```

**Step 2: Verify the migration runs**

Run: `cd /home/patty/indiestack && python3 -c "import asyncio; from indiestack.db import init_db; asyncio.run(init_db())"`
Expected: No errors. The columns now exist on the tools table.

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add quality gate enrichment columns (domain_age_days, has_free_tier, social_mentions_count, rejection_reason)"
```

---

### Task 2: Submission Gate — Default Subdomain Filter

**Files:**
- Modify: `src/indiestack/db.py:1772-1787` (`validate_submission_quality()`)

**Step 1: Add the subdomain filter to `validate_submission_quality()`**

Change the function signature to accept `url` and add the check. The full updated function:

```python
# Blocked deployment subdomains — serious indie tools use custom domains
_BLOCKED_SUBDOMAINS = (
    '.vercel.app', '.netlify.app', '.herokuapp.com', '.fly.dev',
    '.railway.app', '.render.com', '.surge.sh', '.pages.dev',
)

def validate_submission_quality(name: str, tagline: str, description: str, url: str = '') -> list[str]:
    """Run quality checks on a submission. Returns list of error messages (empty = pass)."""
    errors = []
    if len(tagline.strip()) < _MIN_TAGLINE_LENGTH:
        errors.append(f"Tagline must be at least {_MIN_TAGLINE_LENGTH} characters (currently {len(tagline.strip())}).")
    if len(description.strip()) < _MIN_DESCRIPTION_LENGTH:
        errors.append(f"Description must be at least {_MIN_DESCRIPTION_LENGTH} characters (currently {len(description.strip())}).")
    if name.strip().lower() == tagline.strip().lower():
        errors.append("Tagline should be different from the name.")
    # Catch obvious spam patterns
    desc = description.strip()
    if desc and desc == desc.upper() and len(desc) > 20:
        errors.append("Description should not be all uppercase.")
    if tagline.strip() and desc and tagline.strip().lower() in desc.lower() and len(desc) < len(tagline.strip()) + 20:
        errors.append("Description should add more detail beyond the tagline.")
    # Block default deployment subdomains
    if url:
        from urllib.parse import urlparse
        try:
            host = urlparse(url).hostname or ''
            if any(host.endswith(blocked) for blocked in _BLOCKED_SUBDOMAINS):
                errors.append(
                    "IndieStack requires a custom domain. Default deployment URLs "
                    f"(e.g. {host.split('.')[-2]}.{host.split('.')[-1]}) are not accepted. "
                    "See /guidelines for submission requirements."
                )
        except Exception:
            pass
    return errors
```

**Step 2: Update call sites to pass `url`**

There are 3 call sites. Update each:

**In `src/indiestack/routes/submit.py:474`:**
```python
# Before:
quality_errors = validate_submission_quality(name, tagline, description)
# After:
quality_errors = validate_submission_quality(name, tagline, description, url)
```

**In `src/indiestack/main.py:2407`:**
```python
# Before:
quality_errors = db.validate_submission_quality(name, tagline, description)
# After:
quality_errors = db.validate_submission_quality(name, tagline, description, url)
```

**In `src/indiestack/mcp_server.py`:** The MCP `publish_tool()` does its own inline validation (lines 992-995) and then calls the API endpoint which runs `validate_submission_quality`. No change needed — the API endpoint call site covers it.

**Step 3: Verify locally**

Run: `cd /home/patty/indiestack && python3 -c "
from indiestack.db import validate_submission_quality
# Should fail:
errs = validate_submission_quality('Test', 'A cool test tool', 'This is a description that is long enough to pass the minimum check.', 'https://my-app.vercel.app')
print('Blocked:', errs)
# Should pass:
errs = validate_submission_quality('Test', 'A cool test tool', 'This is a description that is long enough to pass the minimum check.', 'https://example.com')
print('Passed:', errs)
"`
Expected: First call returns error about default deployment URL. Second call returns empty list.

**Step 4: Commit**

```bash
git add src/indiestack/db.py src/indiestack/routes/submit.py src/indiestack/main.py
git commit -m "feat: block default deployment subdomain URLs at submission time"
```

---

### Task 3: Submission Gate — URL Reachability Check

**Files:**
- Modify: `src/indiestack/routes/submit.py:474-481` (after quality gates, before duplicate check)
- Modify: `src/indiestack/main.py:2406-2419` (API submit endpoint)

**Step 1: Add URL reachability check to web form submit**

In `src/indiestack/routes/submit.py`, after the quality gates block (line 475) and before the duplicate URL check (line 478), add:

```python
    # URL reachability check — reject dead URLs before they enter the queue
    if not errors and url.strip():
        import httpx as _httpx
        try:
            async with _httpx.AsyncClient(timeout=10.0, follow_redirects=True) as _client:
                resp = await _client.head(url.strip())
                if resp.status_code >= 400:
                    errors.append(f"Your URL returned HTTP {resp.status_code}. Please check that your tool is live and accessible.")
        except Exception:
            errors.append("We couldn't reach your URL. Please check that your tool is live and accessible, then try again.")
```

**Step 2: Add URL reachability check to API submit**

In `src/indiestack/main.py`, after `validate_submission_quality` (line 2409) and before the duplicate check (line 2417), add:

```python
    # URL reachability check
    if not quality_errors:
        import httpx as _httpx
        try:
            async with _httpx.AsyncClient(timeout=10.0, follow_redirects=True) as _client:
                resp = await _client.head(url)
                if resp.status_code >= 400:
                    return JSONResponse({"error": f"URL returned HTTP {resp.status_code}. Please check your tool is live."}, status_code=400)
        except Exception:
            return JSONResponse({"error": "Could not reach URL. Please check your tool is accessible and try again."}, status_code=400)
```

**Step 3: Verify by running the app**

Run: `cd /home/patty/indiestack && python3 -c "
import asyncio, httpx
async def test():
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as c:
        try:
            r = await c.head('https://httpstat.us/404')
            print(f'Status: {r.status_code}, blocked: {r.status_code >= 400}')
        except Exception as e:
            print(f'Error: {e}')
asyncio.run(test())
"`
Expected: `Status: 404, blocked: True`

**Step 4: Commit**

```bash
git add src/indiestack/routes/submit.py src/indiestack/main.py
git commit -m "feat: check URL reachability at submission time — reject dead URLs"
```

---

### Task 4: Enrichment — Domain Age via WHOIS

**Files:**
- Modify: `src/indiestack/db.py` (add new function after `check_duplicate_url`, around line 1809)

**Step 1: Install python-whois**

Run: `pip3 install python-whois`

Check if it's already in pyproject.toml dependencies. If not, add it.

**Step 2: Add the enrichment function**

Add after `check_duplicate_url()` (around line 1809):

```python
async def enrich_domain_age(db: aiosqlite.Connection, tool_id: int, url: str) -> Optional[int]:
    """Look up domain age via WHOIS and store on tool record. Returns age in days or None."""
    from urllib.parse import urlparse
    from datetime import datetime
    try:
        import whois
        hostname = urlparse(url).hostname
        if not hostname:
            return None
        # Strip subdomains to get registrable domain (e.g. app.example.com -> example.com)
        parts = hostname.split('.')
        domain = '.'.join(parts[-2:]) if len(parts) >= 2 else hostname
        w = whois.whois(domain)
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if creation:
            age_days = (datetime.now() - creation).days
            await db.execute(
                "UPDATE tools SET domain_age_days = ? WHERE id = ?",
                (age_days, tool_id),
            )
            await db.commit()
            return age_days
    except Exception:
        pass
    return None
```

**Step 3: Verify WHOIS works**

Run: `cd /home/patty/indiestack && python3 -c "
import whois
from datetime import datetime
w = whois.whois('github.com')
creation = w.creation_date
if isinstance(creation, list): creation = creation[0]
print(f'github.com created: {creation}, age: {(datetime.now() - creation).days} days')
"`
Expected: Shows github.com creation date and age in days (several thousand).

**Step 4: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add domain age enrichment via WHOIS lookup"
```

---

### Task 5: Enrichment — Free Tier Detection

**Files:**
- Modify: `src/indiestack/db.py` (add new function after `enrich_domain_age`)

**Step 1: Add the enrichment function**

```python
async def enrich_free_tier(db: aiosqlite.Connection, tool_id: int, url: str) -> Optional[bool]:
    """Scan a tool's landing page for free tier keywords. Returns True/False/None."""
    import httpx
    _FREE_KEYWORDS = (
        'free tier', 'free plan', 'free trial', 'try free', 'get started free',
        'no credit card', 'open source', 'open-source', 'free forever',
        'free version', 'starter plan', 'hobby plan', 'community edition',
    )
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code < 400:
                text = resp.text.lower()
                has_free = 1 if any(kw in text for kw in _FREE_KEYWORDS) else 0
                await db.execute(
                    "UPDATE tools SET has_free_tier = ? WHERE id = ?",
                    (has_free, tool_id),
                )
                await db.commit()
                return bool(has_free)
    except Exception:
        pass
    return None
```

**Step 2: Verify locally**

Run: `cd /home/patty/indiestack && python3 -c "
import asyncio, httpx
async def test():
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as c:
        r = await c.get('https://plausible.io')
        text = r.text.lower()
        has = any(kw in text for kw in ('free tier','free plan','free trial','open source','open-source'))
        print(f'Plausible free tier detected: {has}')
asyncio.run(test())
"`
Expected: Should detect "open source" or similar keywords on Plausible's page.

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add free tier detection enrichment via landing page scan"
```

---

### Task 6: Enrichment — Social Proof via HackerNews

**Files:**
- Modify: `src/indiestack/db.py` (add new function after `enrich_free_tier`)

**Step 1: Add the enrichment function**

```python
async def enrich_social_proof(db: aiosqlite.Connection, tool_id: int, url: str) -> Optional[int]:
    """Query HackerNews Algolia API for mentions of this tool's domain. Returns mention count."""
    import httpx
    from urllib.parse import urlparse, quote
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return None
        # Strip www. prefix
        if hostname.startswith('www.'):
            hostname = hostname[4:]
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://hn.algolia.com/api/v1/search?query={quote(hostname)}&tags=story&hitsPerPage=0"
            )
            if resp.status_code == 200:
                data = resp.json()
                count = data.get('nbHits', 0)
                await db.execute(
                    "UPDATE tools SET social_mentions_count = ? WHERE id = ?",
                    (count, tool_id),
                )
                await db.commit()
                return count
    except Exception:
        pass
    return None
```

**Step 2: Verify locally**

Run: `cd /home/patty/indiestack && python3 -c "
import asyncio, httpx
from urllib.parse import quote
async def test():
    async with httpx.AsyncClient(timeout=10.0) as c:
        r = await c.get(f'https://hn.algolia.com/api/v1/search?query={quote(\"plausible.io\")}&tags=story&hitsPerPage=0')
        print(f'Plausible HN mentions: {r.json().get(\"nbHits\", 0)}')
asyncio.run(test())
"`
Expected: A positive number (Plausible is frequently discussed on HN).

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add social proof enrichment via HackerNews Algolia API"
```

---

### Task 7: Enrichment Trigger — Run on New Submissions

**Files:**
- Modify: `src/indiestack/routes/submit.py:513-529` (after `create_tool` call)
- Modify: `src/indiestack/main.py:2447-2455` (after API submit insert)

**Step 1: Add enrichment calls to web form submit**

In `src/indiestack/routes/submit.py`, after the post-create updates block (around line 529, after `await db.commit()`), add:

```python
    # Async enrichment — gather quality signals for admin review
    import asyncio as _asyncio
    from indiestack.db import enrich_domain_age, enrich_free_tier, enrich_social_proof
    try:
        await _asyncio.gather(
            enrich_domain_age(db, tool_id, url.strip()),
            enrich_free_tier(db, tool_id, url.strip()),
            enrich_social_proof(db, tool_id, url.strip()),
            return_exceptions=True,
        )
    except Exception:
        pass  # Enrichment is best-effort — don't block submission
```

**Step 2: Add enrichment calls to API submit**

In `src/indiestack/main.py`, after `await d.commit()` (line 2453) and before the return (line 2455), add:

```python
    # Async enrichment — gather quality signals for admin review
    import asyncio as _asyncio
    cursor = await d.execute("SELECT id FROM tools WHERE slug = ?", (slug,))
    row = await cursor.fetchone()
    if row:
        from indiestack.db import enrich_domain_age, enrich_free_tier, enrich_social_proof
        try:
            await _asyncio.gather(
                enrich_domain_age(d, row['id'], url),
                enrich_free_tier(d, row['id'], url),
                enrich_social_proof(d, row['id'], url),
                return_exceptions=True,
            )
        except Exception:
            pass
```

**Step 3: Commit**

```bash
git add src/indiestack/routes/submit.py src/indiestack/main.py
git commit -m "feat: trigger enrichment (domain age, free tier, social proof) on new submissions"
```

---

### Task 8: Admin Queue — Updated Scoring Formula

**Files:**
- Modify: `src/indiestack/db.py:1923-1938` (`get_pending_tools()`)

**Step 1: Update the scoring query**

Replace the `get_pending_tools()` function:

```python
async def get_pending_tools(db: aiosqlite.Connection):
    """Get pending tools sorted by quality signals — best submissions first.
    Incorporates enrichment data: domain age, free tier, social proof, health."""
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name,
           (CASE WHEN t.url LIKE '%github.com%' THEN 10 ELSE 0 END
            + CASE WHEN LENGTH(t.description) > 200 THEN 5 ELSE 0 END
            + CASE WHEN LENGTH(t.description) > 100 THEN 3 ELSE 0 END
            + CASE WHEN t.tags != '' AND t.tags IS NOT NULL THEN 2 ELSE 0 END
            + CASE WHEN t.maker_name != '' AND t.maker_name IS NOT NULL THEN 1 ELSE 0 END
            + CASE WHEN t.domain_age_days > 90 THEN 15
                   WHEN t.domain_age_days > 30 THEN 8
                   WHEN t.domain_age_days IS NOT NULL THEN -10
                   ELSE 0 END
            + CASE WHEN t.has_free_tier = 1 THEN 5
                   WHEN t.has_free_tier = 0 AND t.source_type = 'saas' THEN -5
                   ELSE 0 END
            + CASE WHEN t.social_mentions_count > 3 THEN 10
                   WHEN t.social_mentions_count > 0 THEN 5
                   ELSE 0 END
            - CASE WHEN t.health_status = 'dead' THEN 10 ELSE 0 END
           ) AS submission_quality
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'pending'
           ORDER BY submission_quality DESC, t.created_at DESC"""
    )
    return await cursor.fetchall()
```

**Step 2: Verify query syntax**

Run: `cd /home/patty/indiestack && python3 -c "
import asyncio, aiosqlite
async def test():
    async with aiosqlite.connect('indiestack.db') as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute('''SELECT COUNT(*) as cnt FROM tools WHERE status = \"pending\"''')
        r = await cursor.fetchone()
        print(f'Pending tools: {r[\"cnt\"]}')
asyncio.run(test())
"`
Expected: Shows count of pending tools (likely 0).

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: enhanced admin queue scoring with domain age, free tier, social proof signals"
```

---

### Task 9: Admin Queue — Display Enrichment Columns & Rejection Reasons

**Files:**
- Modify: `src/indiestack/routes/admin.py:446-481` (pending tools rendering in Tools tab)
- Modify: `src/indiestack/routes/admin.py:161-188` (pending tools rendering in Overview tab)
- Modify: `src/indiestack/routes/admin.py:1111-1160` (reject action handler)

**Step 1: Update the Tools tab pending card rendering (lines 446-481)**

Replace the card rendering loop (lines 446-481) with enriched cards:

```python
        for t in pending:
            tid = t['id']
            name = escape(str(t['name']))
            tagline = escape(str(t['tagline']))
            t_url = escape(str(t['url']))
            maker = escape(str(t.get('maker_name', '')))
            cat = escape(str(t.get('category_name', '')))
            price_p = t.get('price_pence')
            price_str = f'£{price_p/100:.2f}' if price_p else 'Free'
            source = t.get('source_type', 'saas')

            # Enrichment badges
            domain_age = t.get('domain_age_days')
            if domain_age is not None:
                if domain_age < 30:
                    age_badge = f'<span style="background:#dc2626;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{domain_age}d old</span>'
                elif domain_age < 90:
                    age_badge = f'<span style="background:#ca8a04;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{domain_age}d old</span>'
                else:
                    years = domain_age // 365
                    age_badge = f'<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{years}y old</span>' if years else f'<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{domain_age}d old</span>'
            else:
                age_badge = '<span style="background:var(--ink-muted);color:white;padding:2px 8px;border-radius:999px;font-size:11px;">Age unknown</span>'

            free_tier = t.get('has_free_tier')
            if free_tier == 1:
                free_badge = '<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">Free tier</span>'
            elif free_tier == 0 and source == 'saas':
                free_badge = '<span style="background:#ca8a04;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">No free tier</span>'
            else:
                free_badge = ''

            social = t.get('social_mentions_count')
            if social is not None and social > 0:
                social_badge = f'<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{social} HN mentions</span>'
            elif social == 0:
                social_badge = '<span style="background:#dc2626;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">0 HN mentions</span>'
            else:
                social_badge = ''

            health = t.get('health_status', 'unknown')
            if health == 'dead':
                health_badge = '<span style="background:#dc2626;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">Dead</span>'
            elif health == 'alive':
                health_badge = '<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">Alive</span>'
            else:
                health_badge = ''

            source_badge = f'<span style="background:var(--accent);color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{source}</span>'

            badges = f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;">{source_badge} {age_badge} {free_badge} {social_badge} {health_badge}</div>'

            # Rejection reason dropdown
            reject_options = ''.join(f'<option value="{r}">{r}</option>' for r in [
                'Default deployment URL',
                'No free tier or trial',
                'Tool appears unmaintained',
                'Insufficient documentation',
                'Duplicate of existing tool',
            ])

            html += f"""
            <div class="card" style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                    <div style="flex:1;min-width:200px;">
                        <strong style="font-size:16px;color:var(--ink);">{name}</strong>
                        <p style="color:var(--ink-muted);font-size:14px;margin-top:4px;">{tagline}</p>
                        <p style="font-size:14px;margin-top:8px;">
                            <a href="{t_url}" target="_blank" rel="noopener">{t_url}</a>
                        </p>
                        <p style="color:var(--ink-muted);font-size:14px;">Maker: {maker} &middot; Category: {cat} &middot; Price: {price_str}</p>
                        {badges}
                    </div>
                    <div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;">
                        <div style="display:flex;gap:8px;align-items:center;">
                            <a href="/admin/edit/{tid}" class="btn" style="background:var(--accent);color:white;padding:8px 16px;text-decoration:none;font-size:14px;">Edit</a>
                            <form method="post" action="/admin">
                                <input type="hidden" name="tool_id" value="{tid}">
                                <input type="hidden" name="action" value="approve">
                                <button type="submit" class="btn" style="background:#16a34a;color:white;padding:8px 16px;">Approve</button>
                            </form>
                        </div>
                        <form method="post" action="/admin" style="display:flex;gap:6px;align-items:center;">
                            <input type="hidden" name="tool_id" value="{tid}">
                            <input type="hidden" name="action" value="reject">
                            <select name="rejection_reason" style="padding:6px 8px;border-radius:8px;font-size:12px;border:1px solid var(--border);background:var(--cream);">
                                <option value="">Reason...</option>
                                {reject_options}
                                <option value="other">Other</option>
                            </select>
                            <button type="submit" class="btn" style="background:#dc2626;color:white;padding:8px 16px;">Reject</button>
                        </form>
                    </div>
                </div>
            </div>
            """
```

**Step 2: Update the reject action handler to store rejection reason**

In `src/indiestack/routes/admin.py`, find the reject action (around line 1111-1113). Update the reject branch:

```python
        elif tool_id_int and action in ("approve", "reject"):
            new_status = "approved" if action == "approve" else "rejected"
            await update_tool_status(db, tool_id_int, new_status)
            # Store rejection reason if provided
            if new_status == "rejected":
                reason = str(form.get("rejection_reason", "")).strip()
                if reason:
                    await db.execute(
                        "UPDATE tools SET rejection_reason = ? WHERE id = ?",
                        (reason, tool_id_int),
                    )
                    await db.commit()
```

**Step 3: Verify by starting the app and visiting /admin**

Run: `cd /home/patty/indiestack && python3 -m indiestack.main &`
Visit `/admin`, check the Tools tab. If there are pending tools, verify the badges render. If not, the HTML should show "No tools pending review."

**Step 4: Commit**

```bash
git add src/indiestack/routes/admin.py
git commit -m "feat: enrichment badges and rejection reasons in admin pending queue"
```

---

### Task 10: Submission Guidelines Page

**Files:**
- Create: `src/indiestack/routes/guidelines.py`
- Modify: `src/indiestack/main.py:3946-3949` (add router include)
- Modify: `src/indiestack/routes/submit.py:459-470` (add link to guidelines)

**Step 1: Create the guidelines route**

Create `src/indiestack/routes/guidelines.py`:

```python
"""Submission guidelines — sets expectations before /submit."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from indiestack.components import page_shell

router = APIRouter()


@router.get("/guidelines", response_class=HTMLResponse)
async def guidelines(request: Request):
    body = f"""
    <div style="max-width:680px;margin:0 auto;padding:32px 16px;">
        <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);margin-bottom:8px;">
            Submission Guidelines
        </h1>
        <p style="color:var(--ink-muted);font-size:16px;margin-bottom:32px;">
            IndieStack is a curated directory. AI agents rely on our curation signal to make
            reliable recommendations. These guidelines help us maintain that trust.
        </p>

        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
            What belongs on IndieStack
        </h2>
        <ul style="color:var(--ink);font-size:15px;line-height:1.8;margin-bottom:24px;padding-left:20px;">
            <li><strong>Independently built software</strong> &mdash; solo founders, small teams, bootstrapped projects</li>
            <li><strong>Actively maintained</strong> &mdash; your tool should work when someone tries it</li>
            <li><strong>Genuinely useful</strong> &mdash; solves a real problem for real people</li>
        </ul>

        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
            What we look for
        </h2>
        <ul style="color:var(--ink);font-size:15px;line-height:1.8;margin-bottom:24px;padding-left:20px;">
            <li><strong>Custom domain</strong> &mdash; not *.vercel.app or *.netlify.app</li>
            <li><strong>Working product</strong> &mdash; not a landing page or waitlist</li>
            <li><strong>Documentation</strong> that an AI agent can parse &mdash; structured docs, API reference, or a solid README</li>
            <li><strong>For SaaS:</strong> a free tier, trial, or sandbox so AI agents can verify your tool works</li>
        </ul>

        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
            What gets rejected
        </h2>
        <ul style="color:var(--ink);font-size:15px;line-height:1.8;margin-bottom:24px;padding-left:20px;">
            <li>Default deployment URLs with no custom domain</li>
            <li>Dead links or tools that return errors</li>
            <li>AI-generated marketing copy with no substance</li>
            <li>Duplicate of a tool already in the catalog</li>
            <li>Paid-only SaaS with no programmatic access path</li>
        </ul>

        <div style="background:var(--cream-dark);border-radius:var(--radius);padding:20px 24px;margin-top:32px;">
            <p style="color:var(--ink);font-size:15px;margin:0;">
                <strong>Why these guidelines exist:</strong> IndieStack serves AI agents via the
                <a href="/mcp" style="color:var(--accent);">MCP server</a>. When an agent recommends a tool from our catalog,
                it needs to actually work. Every tool we list is a promise to the agents and developers who trust our curation.
            </p>
        </div>

        <div style="text-align:center;margin-top:32px;">
            <a href="/submit" class="btn" style="background:var(--accent);color:white;padding:12px 32px;text-decoration:none;font-size:16px;font-weight:600;border-radius:999px;">
                Submit Your Creation
            </a>
        </div>
    </div>
    """
    return HTMLResponse(page_shell("Submission Guidelines", body, user=request.state.user))
```

**Step 2: Register the router in main.py**

In `src/indiestack/main.py`, after the `gaps` router include (line 3946), add:

```python
from indiestack.routes import guidelines
app.include_router(guidelines.router)
```

**Step 3: Add guidelines link to the submit form**

In `src/indiestack/routes/submit.py`, find the submit form heading and add a link. Search for the form's `<h1>` or introductory text and add after it:

```python
<p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
    Before submitting, please read our <a href="/guidelines" style="color:var(--accent);font-weight:600;">submission guidelines</a>.
</p>
```

The exact insertion point depends on how `submit_form()` is structured in `submit.py` — find the form opening HTML and add this paragraph right after the heading.

**Step 4: Verify**

Run the app and visit `/guidelines`. Verify the page renders correctly with all three sections.

**Step 5: Commit**

```bash
git add src/indiestack/routes/guidelines.py src/indiestack/main.py src/indiestack/routes/submit.py
git commit -m "feat: add /guidelines page with submission requirements"
```

---

### Task 11: Post-Approval — Outcome-Driven Demotion

**Files:**
- Modify: `src/indiestack/db.py:1493-1532` (`compute_quality_score()`)

**Step 1: Add `degraded` health status support**

Update the health section of `compute_quality_score()` (lines 1523-1529):

```python
    # Health (multiplier)
    health_status = str(tool.get('health_status') or 'unknown')
    if health_status == 'dead':
        dead_days = int(tool.get('dead_days') or 0)
        health = 0.0 if dead_days >= 7 else 1.0
    elif health_status == 'degraded':
        health = 0.3
    else:
        health = 1.0
```

**Step 2: Add auto-archive function**

Add a new function after `recompute_all_quality_scores()`:

```python
async def auto_archive_dead_tools(db: aiosqlite.Connection) -> int:
    """Archive tools that have been dead for 30+ consecutive days. Returns count archived."""
    cursor = await db.execute("""
        UPDATE tools SET status = 'archived'
        WHERE status = 'approved'
          AND health_status = 'dead'
          AND first_dead_at IS NOT NULL
          AND first_dead_at < datetime('now', '-30 days')
    """)
    await db.commit()
    return cursor.rowcount


async def check_outcome_demotion(db: aiosqlite.Connection) -> int:
    """Demote tools with high agent failure rates to 'degraded' status. Returns count demoted."""
    cursor = await db.execute("""
        SELECT tool_id,
               COUNT(*) as total_signals,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
        FROM outcome_reports
        GROUP BY tool_id
        HAVING total_signals >= 10
    """)
    rows = await cursor.fetchall()
    demoted = 0
    for row in rows:
        success_rate = row['successes'] / row['total_signals'] if row['total_signals'] else 0
        if success_rate < 0.2:
            await db.execute(
                "UPDATE tools SET health_status = 'degraded' WHERE id = ? AND health_status != 'degraded'",
                (row['tool_id'],),
            )
            demoted += 1
    await db.commit()
    return demoted
```

**Step 3: Verify the outcome_reports table exists**

Run: `cd /home/patty/indiestack && python3 -c "
import asyncio, aiosqlite
async def check():
    async with aiosqlite.connect('indiestack.db') as db:
        try:
            c = await db.execute('SELECT COUNT(*) FROM outcome_reports')
            print(f'outcome_reports rows: {(await c.fetchone())[0]}')
        except Exception as e:
            print(f'Table missing: {e}')
asyncio.run(check())
"`

If the table doesn't exist, check for the correct table name (might be `agent_outcomes` or `outcome_signals` — grep for it). Adjust the query accordingly.

**Step 4: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: outcome-driven demotion and auto-archive for dead tools"
```

---

### Task 12: Update MCP publish_tool() Error Messages

**Files:**
- Modify: `src/indiestack/mcp_server.py:987-995` (error messages in `publish_tool()`)

**Step 1: Update error messages to reference guidelines**

Update the validation error messages in `publish_tool()`:

```python
    if not name or not url or not tagline or not description:
        raise ToolError("name, url, tagline, and description are all required. See https://indiestack.ai/guidelines")

    if len(str(tagline).strip()) < 10:
        raise ToolError("Tagline must be at least 10 characters. See https://indiestack.ai/guidelines")
    if len(str(description).strip()) < 50:
        raise ToolError("Description must be at least 50 characters. See https://indiestack.ai/guidelines")
```

**Step 2: Commit**

```bash
git add src/indiestack/mcp_server.py
git commit -m "feat: reference /guidelines in MCP publish_tool() error messages"
```

---

### Task 13: Final Verification & Deploy

**Step 1: Run the smoke test**

Run: `cd /home/patty/indiestack && python3 smoke_test.py`
Expected: All endpoints return expected status codes. No regressions.

**Step 2: Verify /guidelines page**

Run the app locally and confirm `/guidelines` renders correctly.

**Step 3: Test a submission with a blocked subdomain**

Test the validation manually:
```bash
cd /home/patty/indiestack && python3 -c "
from indiestack.db import validate_submission_quality
print(validate_submission_quality('Test', 'A test tool here', 'Description that is definitely long enough to pass the minimum.', 'https://myapp.vercel.app'))
print(validate_submission_quality('Test', 'A test tool here', 'Description that is definitely long enough to pass the minimum.', 'https://myapp.com'))
"
```
Expected: First returns error, second returns empty list.

**Step 4: Deploy**

```bash
cd /home/patty/indiestack && fly deploy
```

**Step 5: Commit if any fixes were needed**

```bash
git add -A
git commit -m "fix: final adjustments from quality gates verification"
```
