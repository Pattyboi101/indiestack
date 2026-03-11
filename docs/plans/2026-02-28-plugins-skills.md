# AI Plugins & Skills Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let makers submit agent plugins (MCP servers, plugins, extensions, skills) with install commands and platform info, and give developers a dedicated `/plugins` discovery page.

**Architecture:** Add 3 nullable columns to the existing `tools` table (`tool_type`, `platforms`, `install_command`). Tools with `tool_type IS NOT NULL` are plugins. A new `/plugins` route provides filtered browsing. The submission form gets a toggle that reveals plugin-specific fields. Tool detail pages show install commands with copy buttons for plugins. Search API and MCP server responses are enriched with plugin metadata.

**Tech Stack:** Python/FastAPI, SQLite (aiosqlite), pure Python string HTML templates (f-strings), no Jinja2.

---

### Task 1: Database Migration — Add Plugin Columns

**Files:**
- Modify: `src/indiestack/db.py:568-592` (migration section, after existing ALTER TABLE blocks)

**Step 1: Add migration block**

In `src/indiestack/db.py`, find the migration section (around line 568, after the `replaces` column migration). Add this block:

```python
        # Migration: add plugin metadata columns if missing
        for col, sql in [
            ("tool_type", "ALTER TABLE tools ADD COLUMN tool_type TEXT DEFAULT NULL"),
            ("platforms", "ALTER TABLE tools ADD COLUMN platforms TEXT NOT NULL DEFAULT ''"),
            ("install_command", "ALTER TABLE tools ADD COLUMN install_command TEXT NOT NULL DEFAULT ''"),
        ]:
            try:
                await db.execute(sql)
            except Exception:
                pass  # Column already exists
```

**Step 2: Update `create_tool()` signature and INSERT**

In `src/indiestack/db.py`, find `async def create_tool` (line 884). Add 3 new keyword arguments:

```python
async def create_tool(db: aiosqlite.Connection, *, name: str, tagline: str, description: str,
                      url: str, maker_name: str, maker_url: str, category_id: int, tags: str,
                      price_pence: Optional[int] = None, delivery_type: str = 'link',
                      delivery_url: str = '', stripe_account_id: str = '',
                      tool_type: Optional[str] = None, platforms: str = '',
                      install_command: str = '') -> int:
```

Update the INSERT statement (line 904-909) to include the new columns:

```python
    cursor = await db.execute(
        """INSERT INTO tools (name, slug, tagline, description, url, maker_name, maker_url,
           category_id, tags, price_pence, delivery_type, delivery_url, stripe_account_id, maker_id,
           tool_type, platforms, install_command)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, slug, tagline, description, url, maker_name, maker_url, category_id, tags,
         price_pence, delivery_type, delivery_url, stripe_account_id, maker_id,
         tool_type, platforms, install_command),
    )
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())"`
Expected: No output (success)

**Step 4: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add tool_type, platforms, install_command columns for plugin support"
```

---

### Task 2: Submission Form — Plugin Toggle & Fields

**Files:**
- Modify: `src/indiestack/routes/submit.py:107-290` (submit_form function)
- Modify: `src/indiestack/routes/submit.py:420-510` (POST handler)

**Step 1: Add plugin fields to the form HTML**

In `submit.py`, find `submit_form()`. After the category `<select>` block (around line 241, after `</select></div>`), add this plugin toggle section:

```python
            <!-- Agent Plugin Section -->
            <div style="background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin:24px 0;">
                <label style="display:flex;align-items:center;gap:12px;cursor:pointer;margin-bottom:0;">
                    <input type="checkbox" id="is_plugin" name="is_plugin" value="1"
                           onchange="document.getElementById('plugin-fields').style.display=this.checked?'block':'none'"
                           style="width:20px;height:20px;accent-color:var(--slate);"
                           {"checked" if v.get('tool_type') else ""}>
                    <div>
                        <strong style="font-size:15px;color:var(--ink);">This is an agent plugin or extension</strong>
                        <p style="color:var(--ink-muted);font-size:13px;margin:4px 0 0;">MCP server, Claude Code plugin, Cursor extension, AI skill, etc.</p>
                    </div>
                </label>
                <div id="plugin-fields" style="display:{"block" if v.get("tool_type") else "none"};margin-top:20px;">
                    <div class="form-group">
                        <label for="tool_type">Type *</label>
                        <select id="tool_type" name="tool_type" class="form-select">
                            <option value="">Select type...</option>
                            <option value="mcp_server" {"selected" if v.get("tool_type") == "mcp_server" else ""}>MCP Server</option>
                            <option value="plugin" {"selected" if v.get("tool_type") == "plugin" else ""}>Plugin</option>
                            <option value="extension" {"selected" if v.get("tool_type") == "extension" else ""}>Extension</option>
                            <option value="skill" {"selected" if v.get("tool_type") == "skill" else ""}>Skill</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="platforms">Compatible platforms <span style="color:var(--ink-muted);font-size:13px;font-weight:400;">(comma-separated)</span></label>
                        <input type="text" id="platforms" name="platforms" class="form-input"
                               value="{escape(str(v.get('platforms', '')))}" placeholder="e.g. Claude Code, Cursor, Windsurf">
                    </div>
                    <div class="form-group">
                        <label for="install_command">Install command</label>
                        <input type="text" id="install_command" name="install_command" class="form-input"
                               value="{escape(str(v.get('install_command', '')))}"
                               placeholder="e.g. claude mcp add your-tool"
                               style="font-family:var(--font-mono);font-size:14px;">
                    </div>
                </div>
            </div>
```

**Step 2: Add form parameters to the POST handler**

In `submit.py`, find the `async def submit_tool` POST handler (line ~420). Add these Form parameters:

```python
    is_plugin: str = Form(""),
    tool_type: str = Form(""),
    platforms: str = Form(""),
    install_command: str = Form(""),
```

Add them to the `values` dict too (around line 452):

```python
    values = dict(name=name, tagline=tagline, url=url, description=description,
                  category_id=category_id, maker_name=maker_name, maker_url=maker_url,
                  tags=tags, replaces=replaces, price=price, delivery_type=delivery_type,
                  delivery_url=delivery_url,
                  tool_type=tool_type if is_plugin else None,
                  platforms=platforms if is_plugin else '',
                  install_command=install_command if is_plugin else '')
```

**Step 3: Pass plugin fields to `create_tool()`**

Find the `create_tool()` call (around line 491). Add the plugin fields:

```python
        tool_type=tool_type.strip() if is_plugin and tool_type.strip() else None,
        platforms=platforms.strip() if is_plugin else '',
        install_command=install_command.strip() if is_plugin else '',
```

**Step 4: Update success page message**

In `submit_success_page()` (line 22), find the AI Discovery callout (line 51-55). Replace the static message with:

```python
            <p style="color:white;font-size:15px;line-height:1.6;margin:0;">
                &#129302; {"Your " + escape(str(tool_type or "tool")) + " is" if tool_type else "Your tool is"} now searchable by AI coding assistants (Cursor, Windsurf, Claude Code) through our MCP server.
            </p>
```

Note: `submit_success_page` will need `tool_type` passed in. Add it as a parameter: `def submit_success_page(tool_name, tool_slug, maker_slug="", tool_type=None):`

And pass it when called (around line 499): `submit_success_page(name.strip(), slug, maker_slug=maker_slug, tool_type=tool_type.strip() if is_plugin else None)`

**Step 5: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/submit.py').read())"`

**Step 6: Commit**

```bash
git add src/indiestack/routes/submit.py
git commit -m "feat: add plugin toggle and fields to submission form"
```

---

### Task 3: Tool Detail Page — Type Badge, Install Block, Platform Tags

**Files:**
- Modify: `src/indiestack/routes/tool.py:610-640` (tool detail rendering)

**Step 1: Read the tool's plugin fields**

In `tool.py`, find where tool data is extracted (search for `is_verified = ` or `is_ejectable = `, likely around line 580-600). Add:

```python
    tool_type = tool.get('tool_type') or None
    platforms_raw = tool.get('platforms', '')
    install_command = tool.get('install_command', '')
```

**Step 2: Build the type badge HTML**

Add this helper block near where `verified_badge_html` and `ejectable_badge_html` are called (around line 614-618):

```python
    # Plugin type badge
    type_labels = {'mcp_server': 'MCP Server', 'plugin': 'Plugin', 'extension': 'Extension', 'skill': 'Skill'}
    type_badge = ''
    if tool_type and tool_type in type_labels:
        type_badge = (
            f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:12px;font-weight:600;'
            f'color:var(--slate-dark);background:rgba(0,212,245,0.1);padding:4px 12px;border-radius:999px;'
            f'border:1px solid var(--slate);">'
            f'{escape(type_labels[tool_type])}</span>'
        )
```

**Step 3: Build the install command block**

```python
    install_block = ''
    if install_command.strip():
        install_block = (
            f'<div style="background:var(--terracotta-dark);border-radius:var(--radius-sm);padding:16px 24px;'
            f'margin-top:16px;display:flex;align-items:center;justify-content:space-between;gap:16px;">'
            f'<code style="font-family:var(--font-mono);font-size:14px;color:var(--slate);white-space:nowrap;'
            f'overflow-x:auto;">{escape(install_command)}</code>'
            f'<button onclick="navigator.clipboard.writeText(\'{escape(install_command)}\');'
            f'this.textContent=\'Copied!\';setTimeout(()=>this.textContent=\'Copy\',2000)"'
            f' style="background:var(--slate);color:white;border:none;border-radius:999px;'
            f'padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;'
            f'font-family:var(--font-body);min-height:36px;">Copy</button>'
            f'</div>'
        )
```

**Step 4: Build platform tags**

```python
    platform_tags = ''
    if platforms_raw.strip():
        platform_list = [p.strip() for p in platforms_raw.split(',') if p.strip()]
        pills = ''.join(
            f'<span style="display:inline-block;font-size:12px;font-weight:500;padding:4px 12px;'
            f'background:var(--cream-dark);border:1px solid var(--border);border-radius:999px;'
            f'color:var(--ink-light);">{escape(p)}</span>'
            for p in platform_list
        )
        platform_tags = f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;">{pills}</div>'
```

**Step 5: Insert into the page**

Find line 615-622 (the h1 and badges area). Add `type_badge` after the existing badges:

```python
                    {verified_badge_html() if is_verified else ''}
                    {ejectable_badge_html() if is_ejectable else ''}
                    {type_badge}
                    {pulse_html}
```

Find line 622-623 (after tagline, before price_tag_html). Insert install_block and platform_tags:

```python
                <p style="font-size:18px;color:var(--ink-muted);margin-top:8px;">{tagline}</p>
                {install_block}
                {platform_tags}
                {price_tag_html}
```

**Step 6: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/tool.py').read())"`

**Step 7: Commit**

```bash
git add src/indiestack/routes/tool.py
git commit -m "feat: show type badge, install command, and platform tags on plugin detail pages"
```

---

### Task 4: `/plugins` Discovery Page

**Files:**
- Create: `src/indiestack/routes/plugins.py`

**Step 1: Create the plugins route file**

Create `src/indiestack/routes/plugins.py` with this content:

```python
"""AI Plugins & Skills discovery page."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card

router = APIRouter()

TYPE_LABELS = {
    'mcp_server': 'MCP Servers',
    'plugin': 'Plugins',
    'extension': 'Extensions',
    'skill': 'Skills',
}


@router.get("/plugins", response_class=HTMLResponse)
async def plugins_page(request: Request, type: str = "", platform: str = ""):
    db = request.state.db

    # Build query
    conditions = ["t.status = 'approved'", "t.tool_type IS NOT NULL"]
    params = []

    if type and type in TYPE_LABELS:
        conditions.append("t.tool_type = ?")
        params.append(type)

    if platform.strip():
        conditions.append("t.platforms LIKE ?")
        params.append(f"%{platform.strip()}%")

    where = " AND ".join(conditions)
    cursor = await db.execute(
        f"""SELECT t.*, c.name as category_name, c.slug as category_slug
            FROM tools t
            JOIN categories c ON t.category_id = c.id
            WHERE {where}
            ORDER BY t.upvote_count DESC""",
        params,
    )
    tools = [dict(r) for r in await cursor.fetchall()]

    # Get common platforms for filter pills
    all_cursor = await db.execute(
        "SELECT platforms FROM tools WHERE tool_type IS NOT NULL AND platforms != '' AND status = 'approved'"
    )
    all_platforms_rows = await all_cursor.fetchall()
    platform_counts = {}
    for row in all_platforms_rows:
        for p in row['platforms'].split(','):
            p = p.strip()
            if p:
                platform_counts[p] = platform_counts.get(p, 0) + 1
    # Sort by frequency, take top 8
    top_platforms = sorted(platform_counts.keys(), key=lambda x: platform_counts[x], reverse=True)[:8]

    # Type filter pills
    type_pills = f'<a href="/plugins" style="padding:8px 16px;border-radius:999px;font-size:14px;font-weight:600;text-decoration:none;border:1px solid {"var(--slate)" if not type else "var(--border)"};color:{"var(--slate)" if not type else "var(--ink-light)"};background:{"rgba(0,212,245,0.08)" if not type else "transparent"};">All</a>'
    for slug, label in TYPE_LABELS.items():
        active = type == slug
        type_pills += (
            f'<a href="/plugins?type={slug}{"&platform=" + escape(platform) if platform else ""}"'
            f' style="padding:8px 16px;border-radius:999px;font-size:14px;font-weight:600;text-decoration:none;'
            f'border:1px solid {"var(--slate)" if active else "var(--border)"};'
            f'color:{"var(--slate)" if active else "var(--ink-light)"};'
            f'background:{"rgba(0,212,245,0.08)" if active else "transparent"};">{label}</a>'
        )

    # Platform filter pills
    platform_pills = ''
    if top_platforms:
        pills_html = ''
        for p in top_platforms:
            active = platform == p
            pills_html += (
                f'<a href="/plugins?platform={escape(p)}{"&type=" + escape(type) if type else ""}"'
                f' style="padding:4px 12px;border-radius:999px;font-size:13px;font-weight:500;text-decoration:none;'
                f'border:1px solid {"var(--slate)" if active else "var(--border)"};'
                f'color:{"var(--slate)" if active else "var(--ink-muted)"};'
                f'background:{"rgba(0,212,245,0.08)" if active else "transparent"};">{escape(p)}</a>'
            )
        platform_pills = f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;">{pills_html}</div>'

    # Tool cards
    if tools:
        cards = ''.join(tool_card(t) for t in tools)
        grid = f'<div class="card-grid">{cards}</div>'
    else:
        grid = (
            '<div style="text-align:center;padding:64px 24px;">'
            '<p style="font-size:48px;margin-bottom:16px;">&#129302;</p>'
            '<h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:8px;">No plugins yet</h2>'
            '<p style="color:var(--ink-muted);margin-bottom:24px;">Be the first to list an agent plugin or MCP server.</p>'
            '<a href="/submit" class="btn btn-primary">Submit Your Plugin</a>'
            '</div>'
        )

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-xl);margin-bottom:8px;">AI Plugins &amp; Skills</h1>
            <p style="font-size:18px;color:var(--ink-muted);max-width:560px;margin:0 auto;">
                MCP servers, extensions, and skills for your AI coding assistant. Install in one command.
            </p>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-bottom:24px;">
            {type_pills}
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-bottom:40px;">
            {platform_pills}
        </div>
        {grid}
    </div>
    """

    return page_shell(
        title="AI Plugins & Skills for Developers | IndieStack",
        body=body,
        description="Discover MCP servers, Claude Code plugins, Cursor extensions, and AI skills. Install in one command.",
        user=getattr(request.state, 'user', None),
    )
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/plugins.py').read())"`

**Step 3: Commit**

```bash
git add src/indiestack/routes/plugins.py
git commit -m "feat: add /plugins discovery page with type and platform filters"
```

---

### Task 5: Register Router & Nav Link

**Files:**
- Modify: `src/indiestack/main.py:100-111` (imports) and `src/indiestack/main.py:2536-2560` (include_router)
- Modify: `src/indiestack/routes/components.py:496-506` (nav dropdown)

**Step 1: Import and register the plugins router**

In `main.py`, add the import (after the `use_cases` import, around line 110):

```python
from indiestack.routes import plugins
```

Add the router registration (after the last `include_router`, around line 2560):

```python
app.include_router(plugins.router)
```

**Step 2: Add "Plugins" to the nav dropdown**

In `components.py`, find the nav dropdown items (around line 496-506). Add a "Plugins" link after "Best Tools":

```python
                        <a href="/best" class="nav-dropdown-item">Best Tools</a>
                        <a href="/plugins" class="nav-dropdown-item">Plugins</a>
                        <a href="/blog" class="nav-dropdown-item">Blog</a>
```

Also add it to the mobile menu (around line 516-518):

```python
            <a href="/stacks">Stacks</a>
            <a href="/plugins">Plugins</a>
            <a href="/submit" class="btn btn-primary">Add Your Tool</a>
```

**Step 3: Verify syntax on both files**

Run:
```bash
python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read())"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read())"
```

**Step 4: Commit**

```bash
git add src/indiestack/main.py src/indiestack/routes/components.py
git commit -m "feat: register plugins router and add Plugins link to nav"
```

---

### Task 6: Enrich Search API & MCP Server

**Files:**
- Modify: `src/indiestack/main.py:985-1002` (search API response builder)
- Modify: `src/indiestack/mcp_server.py:210-217` (search result formatting)

**Step 1: Add plugin fields to search API response**

In `main.py`, find the search results builder (line 992-1002). Add the plugin fields to each result dict:

```python
        result = {
            "name": t['name'],
            "tagline": t.get('tagline', ''),
            "url": t.get('url', ''),
            "indiestack_url": f"{BASE_URL}/tool/{t['slug']}",
            "category": t.get('category_name', ''),
            "price": price_str,
            "is_verified": bool(t.get('is_verified', 0)),
            "upvote_count": int(t.get('upvote_count', 0)),
            "tags": t.get('tags', ''),
        }
        # Add plugin metadata if present
        if t.get('tool_type'):
            result["tool_type"] = t['tool_type']
            result["platforms"] = t.get('platforms', '')
            result["install_command"] = t.get('install_command', '')
        results.append(result)
```

**Step 2: Enrich MCP server search results**

In `mcp_server.py`, find the search result formatting (line 210-217). After the existing line that builds each tool's text, add the install command:

```python
    for t in tools:
        verified = " [Verified]" if t.get("is_verified") else ""
        tool_type_label = ""
        if t.get("tool_type"):
            type_labels = {'mcp_server': 'MCP Server', 'plugin': 'Plugin', 'extension': 'Extension', 'skill': 'Skill'}
            tool_type_label = f" [{type_labels.get(t['tool_type'], t['tool_type'])}]"
        install_line = ""
        if t.get("install_command"):
            install_line = f"\n  Install: `{t['install_command']}`"
        lines.append(
            f"- **{t['name']}**{verified}{tool_type_label} — {t.get('tagline', '')}\n"
            f"  Price: {t.get('price', 'Free')} | Upvotes: {t.get('upvote_count', 0)}{install_line}\n"
            f"  {t.get('indiestack_url', '')}"
        )
```

**Step 3: Verify syntax**

Run:
```bash
python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read())"
python3 -c "import ast; ast.parse(open('src/indiestack/mcp_server.py').read())"
```

**Step 4: Commit**

```bash
git add src/indiestack/main.py src/indiestack/mcp_server.py
git commit -m "feat: enrich search API and MCP server responses with plugin metadata"
```

---

### Task 7: Smoke Test & Add `/plugins` to Test Suite

**Files:**
- Modify: `smoke_test.py` (add /plugins endpoint)

**Step 1: Add `/plugins` to smoke test**

In `smoke_test.py`, find the `TESTS` list. Add after the stacks entries (around line 30):

```python
    ("GET", "/plugins", 200, "Plugins"),
```

**Step 2: Run all route syntax checks**

```bash
for f in src/indiestack/routes/*.py; do echo -n "$(basename $f): "; python3 -c "import ast; ast.parse(open('$f').read()); print('OK')"; done
```

**Step 3: Run the full smoke test**

Run: `python3 smoke_test.py`
Expected: All endpoints pass (38/38 now with plugins)

**Step 4: Commit**

```bash
git add smoke_test.py
git commit -m "test: add /plugins endpoint to smoke test"
```

---

### Task 8: Deploy & Verify

**Step 1: Deploy to Fly.io**

```bash
~/.fly/bin/flyctl deploy --remote-only
```

**Step 2: Verify live**

- Visit `/plugins` — should show empty state with "Submit Your Plugin" CTA
- Visit `/submit` — should show plugin toggle after category dropdown
- Toggle the plugin checkbox — type/platforms/install command fields should slide in
- Visit `/tool/indiestack-mcp` or any tool — regular tools should look unchanged
- Check search API: `/api/tools/search?q=analytics` — results should NOT include `tool_type` for regular tools

**Step 3: Run smoke test against production**

Run: `python3 smoke_test.py`
Expected: 38/38 pass
