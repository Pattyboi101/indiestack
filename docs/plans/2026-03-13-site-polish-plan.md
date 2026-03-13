# Site Polish: Changelog, Micro-Interactions & Demand SEO

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a build-in-public changelog page, sitewide copy-to-clipboard micro-interactions on code blocks, and improve demand signal SEO visibility. Plus small aesthetic touches that push the site toward a more "indie" feel.

**Architecture:** Three new features across existing route files + one new route file. All vanilla JS (sub-100 lines total), server-rendered HTML, no new dependencies. Changelog reads from a markdown-like Python string (no external parser needed — we use the same f-string pattern as everything else).

**Tech Stack:** Python/FastAPI, pure f-string HTML templates, vanilla JS, existing CSS design tokens.

**Testing:** `python3 smoke_test.py` (currently 40 endpoints) + syntax checks via `python3 -c "import ast; ast.parse(open('FILE').read())"`.

---

## Task 1: Sitewide Copy-to-Clipboard Micro-Interactions

**Files:**
- Modify: `src/indiestack/routes/components.py` — add `copy_js()` function and inject into `page_shell()`

**Context:** Several pages already have bespoke clipboard copy handlers (tool.py line 621, embed.py line 158). We're replacing the scattered pattern with a single, sitewide script that auto-attaches to any element with `data-copy`. This gives every code block, install command, and curl snippet a polished copy interaction with visual feedback.

**Step 1: Add the `copy_js()` function**

In `components.py`, add a new function near the other JS functions (`upvote_js`, `wishlist_js`, `theme_js`). Find them by searching for `def upvote_js`.

```python
def copy_js() -> str:
    """Sitewide copy-to-clipboard with micro-interaction feedback."""
    return '''<script>
document.addEventListener('click', function(e) {
    const btn = e.target.closest('[data-copy]');
    if (!btn) return;
    const text = btn.getAttribute('data-copy');
    if (!text) return;
    navigator.clipboard.writeText(text).then(function() {
        const orig = btn.innerHTML;
        const origBg = btn.style.background;
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!';
        btn.style.background = 'var(--accent)';
        btn.style.transform = 'scale(1.05)';
        btn.style.transition = 'transform 0.15s ease, background 0.15s ease';
        setTimeout(function() {
            btn.innerHTML = orig;
            btn.style.background = origBg;
            btn.style.transform = 'scale(1)';
        }, 1500);
    });
});
</script>'''
```

**Step 2: Inject into `page_shell()`**

In the `page_shell()` function (~line 1392), add `{copy_js()}` alongside the other JS injections:

```python
{upvote_js()}
{wishlist_js()}
{theme_js()}
{copy_js()}
```

**Step 3: Add a reusable `copy_button()` component**

Add a small helper function that generates a styled copy button for any text:

```python
def copy_button(text: str, label: str = "Copy") -> str:
    """Render a copy button with data-copy attribute for the sitewide copy handler."""
    safe = escape(text).replace("'", "&#39;").replace('"', "&quot;")
    return f'<button data-copy="{safe}" style="background:var(--slate,#64748B);color:#fff;border:none;border-radius:999px;padding:6px 14px;font-size:12px;font-weight:600;cursor:pointer;font-family:var(--font-body);display:inline-flex;align-items:center;gap:4px;">{label}</button>'
```

**Step 4: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read()); print('OK')"
```

**Step 5: Smoke test**

```bash
python3 smoke_test.py
```

---

## Task 2: Retrofit Existing Copy Buttons to Use `data-copy`

**Files:**
- Modify: `src/indiestack/routes/tool.py` — install command copy button (~line 621)
- Modify: `src/indiestack/routes/embed.py` — embed code copy buttons (~lines 158-165)

**Context:** tool.py and embed.py have inline `onclick="navigator.clipboard..."` handlers. We'll replace them with `data-copy` attributes so they get the new micro-interaction (checkmark SVG, color flash, scale transform) for free.

**Step 1: Update tool.py install command copy button**

Read `src/indiestack/routes/tool.py` around lines 614-627. Find the existing copy button with `onclick` and replace the `<button>` with one using `data-copy`:

Replace the inline onclick copy button with:
```python
<button data-copy="{escape(install_cmd)}" style="background:var(--slate,#64748B);color:#fff;border:none;border-radius:999px;padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;">Copy</button>
```

Remove the associated `<script>` block that handled the old copy behavior if there is one inline.

**Step 2: Update embed.py copy buttons**

Read `src/indiestack/routes/embed.py` around lines 80-170. Find the `copyCode` function and the copy buttons. Replace each button's `onclick="copyCode('...')"` with `data-copy="..."` attributes containing the actual text to copy. Remove the `copyCode` JavaScript function.

**Step 3: Verify syntax on both files**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/tool.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/embed.py').read()); print('OK')"
```

**Step 4: Smoke test**

```bash
python3 smoke_test.py
```

---

## Task 3: Changelog Page

**Files:**
- Create: `src/indiestack/routes/changelog.py`
- Modify: `src/indiestack/main.py` — register the router
- Modify: `smoke_test.py` — add `/changelog` endpoint

**Context:** No external markdown parser needed. The changelog entries are defined as a Python list of dicts (date, title, items) and rendered with f-strings. Patrick updates the list in the route file whenever he ships something. Simple, zero-dependency, fits the existing pattern.

**Step 1: Create the changelog route file**

Create `src/indiestack/routes/changelog.py`:

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from indiestack.routes.components import page_shell, nav_html

router = APIRouter()

# Add new entries at the top. Each entry is one ship day.
CHANGELOG = [
    {
        "date": "2026-03-13",
        "title": "Site Polish & Micro-Interactions",
        "items": [
            ("feat", "Sitewide copy-to-clipboard with visual feedback on all code blocks"),
            ("feat", "This changelog page — build in public"),
            ("feat", "Demand signal SEO improvements"),
        ],
    },
    {
        "date": "2026-03-12",
        "title": "Website Rework & Supply Chain Pivot",
        "items": [
            ("feat", "Nav restructure: Explore | For Makers | Resources | Submit"),
            ("feat", "Landing page demand teaser — live gaps from agent searches"),
            ("feat", "Explore page search bar and collapsible filters"),
            ("feat", "Sitewide copy pivot: 'knowledge layer' → 'open-source supply chain'"),
            ("fix", "Hero text contrast on light mode"),
            ("fix", "Returning visitors analytics query"),
        ],
    },
    {
        "date": "2026-03-12",
        "title": "Agentic Package Manager",
        "items": [
            ("feat", "GitHub auto-indexer — 73 queries, catalog grew to 3,095 tools"),
            ("feat", "README enricher — auto-extracted metadata for 1,200+ tools"),
            ("feat", "1,279 compatibility pairs via pair generator"),
            ("feat", "Structured metadata on every tool: api_type, auth_method, sdk_packages, env_vars"),
            ("feat", "MCP Server v1.3.1 — scan_project, report_compatibility, check_health"),
            ("feat", "Per-tool Agent Cards at /cards/{slug}.json"),
            ("feat", "Demand Signals Pro ($15/month) — clusters, trends, export"),
            ("feat", "GEO lead magnet — generate llms.txt + Agent Card from any URL"),
        ],
    },
    {
        "date": "2026-03-07",
        "title": "Product Hunt Launch",
        "items": [
            ("feat", "Launched on Product Hunt"),
            ("feat", "25 categories — added Games, Learning, Newsletters, Creative"),
            ("feat", "'What is IndieStack?' explainer page"),
            ("feat", "Full vision alignment — 'indie tools' → 'indie creations' across 20+ files"),
            ("feat", "MCP Server v1.1.0 on PyPI"),
        ],
    },
    {
        "date": "2026-03-06",
        "title": "Pre-Launch Polish",
        "items": [
            ("feat", "Glassmorphism landing page with interactive grid canvas"),
            ("feat", "SVG icons replacing all emoji across the site"),
            ("feat", "Dark/light mode contrast fixes"),
            ("feat", "Maker stories on tool detail pages"),
            ("feat", "Tool health monitoring via GitHub API"),
            ("feat", "REST API docs page at /api"),
        ],
    },
]


def _badge(kind: str) -> str:
    colors = {
        "feat": ("var(--accent)", "rgba(0,212,245,0.1)"),
        "fix": ("var(--green,#22C55E)", "rgba(34,197,94,0.1)"),
        "improve": ("var(--gold,#E2B764)", "rgba(226,183,100,0.1)"),
    }
    fg, bg = colors.get(kind, ("var(--ink-muted)", "var(--card-bg)"))
    return f'<span style="display:inline-block;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;padding:2px 8px;border-radius:4px;color:{fg};background:{bg};margin-right:8px;">{kind}</span>'


@router.get("/changelog", response_class=HTMLResponse)
async def changelog_page(request: Request):
    user = getattr(request.state, "user", None)

    entries_html = ""
    for entry in CHANGELOG:
        items_html = ""
        for kind, text in entry["items"]:
            items_html += f'''
            <li style="display:flex;align-items:flex-start;gap:8px;padding:8px 0;border-bottom:1px solid var(--border);">
                {_badge(kind)}
                <span style="color:var(--ink);font-size:14px;line-height:1.5;">{text}</span>
            </li>'''

        entries_html += f'''
        <div style="margin-bottom:48px;">
            <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:16px;">
                <time style="font-family:var(--font-mono);font-size:13px;color:var(--ink-muted);white-space:nowrap;">{entry["date"]}</time>
                <h2 style="font-family:var(--font-display);font-size:var(--heading-sm);color:var(--ink);margin:0;">{entry["title"]}</h2>
            </div>
            <ul style="list-style:none;padding:0;margin:0;">
                {items_html}
            </ul>
        </div>'''

    body = f'''
    {nav_html(user)}
    <main style="max-width:720px;margin:0 auto;padding:48px 20px;">
        <div style="margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin:0 0 8px;">Changelog</h1>
            <p style="color:var(--ink-muted);font-size:15px;margin:0;">What we shipped, when we shipped it. Built in public by two uni students in Cardiff.</p>
        </div>
        {entries_html}
    </main>'''

    return page_shell("Changelog — IndieStack", body, description="What we shipped and when. IndieStack's build-in-public changelog.", user=user)
```

**Step 2: Register the router in main.py**

In `src/indiestack/main.py`, find the router imports section and add:

```python
from indiestack.routes.changelog import router as changelog_router
```

Then find the `app.include_router()` block and add:

```python
app.include_router(changelog_router)
```

**Step 3: Add to smoke test**

In `smoke_test.py`, add `"/changelog"` to the endpoints list with expected status 200.

**Step 4: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/changelog.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('OK')"
```

**Step 5: Smoke test**

```bash
python3 smoke_test.py
```

---

## Task 4: Add Changelog to Navigation & Footer

**Files:**
- Modify: `src/indiestack/routes/components.py` — add changelog link to Resources dropdown and footer

**Context:** The changelog lives under "Resources" in the nav — it's an informational page about the project, same category as "What is IndieStack?" and "Stacks."

**Step 1: Add to desktop nav Resources dropdown**

In the `nav_html()` function, find the Resources dropdown menu (contains "What is IndieStack?", "Demand Board", "Stacks"). Add a changelog link:

```html
<a href="/changelog" class="nav-dropdown-item">Changelog</a>
```

Add it as the last item in the Resources dropdown.

**Step 2: Add to mobile menu**

In the mobile menu flat list, add a "Changelog" link before "Submit":

```html
<a href="/changelog" style="..." >Changelog</a>
```

Use the same styling as the other mobile menu links.

**Step 3: Add to footer**

Find the footer links section in `components.py`. Add a "Changelog" link alongside the other informational links (What is IndieStack?, etc.).

**Step 4: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read()); print('OK')"
```

---

## Task 5: Demand Signal SEO — Public Gap Pages

**Files:**
- Modify: `src/indiestack/routes/gaps.py` — add individual gap detail route
- Modify: `smoke_test.py` — add gap page test if needed

**Context:** Right now demand gaps only live on `/gaps` as a list. Each gap could be its own indexable page at `/gaps/{query-slug}` — "AI agents searched for X but nothing exists yet. Build it." These pages are programmatic SEO gold for capturing makers searching "what should I build."

**Step 1: Read the current gaps.py**

Read `src/indiestack/routes/gaps.py` fully to understand the data model and existing queries.

**Step 2: Add individual gap page route**

Add a new route handler below the existing `/gaps` route:

```python
@router.get("/gaps/{query_slug}", response_class=HTMLResponse)
async def gap_detail(request: Request, query_slug: str):
    user = getattr(request.state, "user", None)

    # Convert slug back to query (replace hyphens with spaces)
    query_text = query_slug.replace("-", " ")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Find matching gap(s)
        cursor = await db.execute(
            """SELECT query, COUNT(*) as search_count, MAX(searched_at) as last_searched
               FROM search_logs
               WHERE result_count = 0 AND LOWER(query) = LOWER(?)
               GROUP BY LOWER(query)""",
            (query_text,)
        )
        gap = await cursor.fetchone()

        if not gap:
            # Try fuzzy match
            cursor = await db.execute(
                """SELECT query, COUNT(*) as search_count, MAX(searched_at) as last_searched
                   FROM search_logs
                   WHERE result_count = 0 AND LOWER(REPLACE(query, ' ', '-')) = LOWER(?)
                   GROUP BY LOWER(query)""",
                (query_slug,)
            )
            gap = await cursor.fetchone()

        if not gap:
            return HTMLResponse(status_code=404, content=page_shell(
                "Gap Not Found — IndieStack",
                f'{nav_html(user)}<main style="max-width:600px;margin:80px auto;text-align:center;padding:20px;"><h1>Gap not found</h1><p><a href="/gaps">Back to Demand Board</a></p></main>',
                user=user
            ))

        query_display = gap["query"]
        count = gap["search_count"]

        # Find similar/related gaps
        cursor = await db.execute(
            """SELECT query, COUNT(*) as cnt
               FROM search_logs
               WHERE result_count = 0 AND LOWER(query) != LOWER(?)
               GROUP BY LOWER(query)
               ORDER BY cnt DESC
               LIMIT 5""",
            (query_text,)
        )
        related = await cursor.fetchall()

    # Determine demand tier
    if count >= 10:
        tier, tier_color = "High Demand", "#EF4444"
    elif count >= 5:
        tier, tier_color = "Growing", "#F59E0B"
    elif count >= 2:
        tier, tier_color = "Emerging", "var(--accent)"
    else:
        tier, tier_color = "New Signal", "var(--ink-muted)"

    related_html = ""
    if related:
        items = ""
        for r in related:
            slug = r["query"].lower().replace(" ", "-")
            items += f'<a href="/gaps/{slug}" style="display:block;padding:8px 12px;border-bottom:1px solid var(--border);color:var(--ink);text-decoration:none;font-size:14px;">&quot;{escape(r["query"])}&quot; <span style="color:var(--ink-muted);">({r["cnt"]} searches)</span></a>'
        related_html = f'''
        <div style="margin-top:40px;">
            <h2 style="font-family:var(--font-display);font-size:var(--heading-sm);color:var(--ink);margin-bottom:16px;">Other Gaps</h2>
            <div style="border:1px solid var(--border);border-radius:12px;overflow:hidden;background:var(--card-bg);">
                {items}
            </div>
        </div>'''

    body = f'''
    {nav_html(user)}
    <main style="max-width:640px;margin:0 auto;padding:48px 20px;">
        <p style="margin:0 0 24px;"><a href="/gaps" style="color:var(--accent);text-decoration:none;font-size:14px;">&larr; Back to Demand Board</a></p>

        <span style="display:inline-block;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;padding:4px 10px;border-radius:4px;color:{tier_color};background:{tier_color}15;margin-bottom:12px;">{tier}</span>

        <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin:0 0 8px;">AI agents are searching for &ldquo;{escape(query_display)}&rdquo;</h1>
        <p style="color:var(--ink-muted);font-size:15px;margin:0 0 32px;">This query was searched <strong>{count}</strong> time{"s" if count != 1 else ""} by AI agents using IndieStack — and nothing was found. There&rsquo;s a gap in the indie tool ecosystem here.</p>

        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:24px;margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:var(--heading-sm);color:var(--ink);margin:0 0 12px;">Why this matters</h2>
            <p style="color:var(--ink);font-size:14px;line-height:1.6;margin:0 0 12px;">Every time an AI agent searches for &ldquo;{escape(query_display)}&rdquo; and finds nothing, it falls back to generating code from scratch — wasting tokens, time, and producing something nobody maintains.</p>
            <p style="color:var(--ink);font-size:14px;line-height:1.6;margin:0;">If you build a tool that fills this gap and submit it to IndieStack, every agent that searches for this will recommend <em>your</em> creation instead.</p>
        </div>

        <a href="/submit" style="display:inline-block;background:var(--accent);color:#fff;padding:14px 32px;border-radius:999px;font-weight:600;text-decoration:none;font-size:15px;">Submit a Tool for This Gap &rarr;</a>

        {related_html}
    </main>'''

    return page_shell(
        f'AI agents need "{escape(query_display)}" — IndieStack Demand Signal',
        body,
        description=f'AI agents searched for "{query_display}" {count} times and found nothing. Build this tool and get instant AI-powered distribution.',
        user=user
    )
```

You'll need to import `escape` from `html` and `aiosqlite` and `DB_PATH` at the top of gaps.py if not already imported — check existing imports first.

**Step 3: Link gaps from the list page**

In the existing `/gaps` route, make each gap query clickable. Find where gap queries are displayed and wrap them in an `<a>` tag:

```python
slug = gap_query.lower().replace(" ", "-")
f'<a href="/gaps/{slug}" style="color:var(--ink);text-decoration:none;">&quot;{escape(gap_query)}&quot;</a>'
```

**Step 4: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/gaps.py').read()); print('OK')"
```

**Step 5: Smoke test**

```bash
python3 smoke_test.py
```

---

## Task 6: Deploy & Verify

**Step 1: Final syntax check all modified files**

```bash
cd /home/patty/indiestack
python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read()); print('components OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/tool.py').read()); print('tool OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/embed.py').read()); print('embed OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/changelog.py').read()); print('changelog OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/gaps.py').read()); print('gaps OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('main OK')"
```

**Step 2: Full smoke test**

```bash
python3 smoke_test.py
```

Expected: All tests pass (41+ with new /changelog endpoint).

**Step 3: Commit**

Stage all changed/new files and commit.

**Step 4: Deploy**

```bash
cd /home/patty/indiestack && ~/.fly/bin/flyctl deploy --remote-only
```

**Step 5: Verify live pages**

Check these load correctly on production:
- `/changelog` — changelog page renders with entries
- `/tool/hanko` — copy button has new micro-interaction
- `/gaps` — gap queries are clickable links
- `/gaps/authentication-mcp` or similar — individual gap page renders

---

## Parallelisation

**Group A (independent — can run in parallel):**
- Task 1: Copy-to-clipboard micro-interactions (components.py)
- Task 3: Changelog route (new file + main.py registration)
- Task 5: Demand signal gap pages (gaps.py)

**Group B (depends on Task 1):**
- Task 2: Retrofit existing copy buttons (tool.py, embed.py)
- Task 4: Add changelog to nav/footer (components.py — same file as Task 1, must be sequential)

**Group C (depends on all):**
- Task 6: Deploy & verify
