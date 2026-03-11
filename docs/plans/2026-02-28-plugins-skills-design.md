# AI Plugins & Skills Feature Design

## Goal

Let makers submit agent plugins (MCP servers, Claude Code plugins, Cursor extensions, skills) alongside regular SaaS tools, and give developers a dedicated `/plugins` page to discover them.

## Approach

Lightweight column extension — add 3 nullable columns to the existing `tools` table. Plugins are still tools with extra metadata. They appear in search, MCP responses, and explore alongside everything else, but also get a dedicated browse page.

---

## 1. Data Model

Three new nullable columns on `tools`:

| Column | Type | Default | Values |
|--------|------|---------|--------|
| `tool_type` | `TEXT` | `NULL` | `mcp_server`, `plugin`, `extension`, `skill`, or NULL (regular tool) |
| `platforms` | `TEXT` | `''` | Free-text, comma-separated. e.g. "Claude Code, Cursor, Windsurf" |
| `install_command` | `TEXT` | `''` | e.g. "claude mcp add indiestack" |

Rules:
- `tool_type IS NULL` = regular SaaS tool (backwards compatible)
- `tool_type IS NOT NULL` = agent plugin, shows on `/plugins`
- A plugin still has a `category_id` (e.g. an analytics MCP server is in "Analytics & Metrics" AND has `tool_type='mcp_server'`)
- `platforms` and `install_command` are only meaningful when `tool_type` is set

Migration: 3 `ALTER TABLE ADD COLUMN` statements, no data changes needed.

---

## 2. Submission Flow

The existing `/submit` form gets a toggle section after the category dropdown:

**"Is this an agent plugin or extension?"** — checkbox toggle

When ON, three fields slide in:
- **Type** — dropdown: MCP Server, Plugin, Extension, Skill
- **Compatible platforms** — text input, placeholder: "e.g. Claude Code, Cursor, Windsurf"
- **Install command** — monospace text input, placeholder: "e.g. claude mcp add your-tool"

When OFF (default), fields are hidden. Zero friction added for regular tool submissions.

Success page: if `tool_type` is set, the AI discovery callout says "Your MCP server is now searchable by AI coding assistants" instead of the generic message.

---

## 3. `/plugins` Page

Dedicated discovery page at `/plugins`, added to Browse dropdown in nav.

Layout:
- **Hero**: "AI Plugins & Skills" heading + subtext
- **Filter bar**: Type filter pills (All / MCP Servers / Plugins / Extensions / Skills)
- **Platform filter**: Second row of pills for common platforms (parsed from `platforms` field)
- **Results grid**: `card-grid` with `tool_card()`, each card shows type badge + platform tags
- **Empty state**: "No plugins yet? Be the first." → `/submit`

Query: `SELECT * FROM tools WHERE tool_type IS NOT NULL` with optional type and platform filters.

SEO: Target "MCP server directory", "Claude Code plugins", "Cursor extensions".

---

## 4. Tool Detail Page Changes

When `tool_type IS NOT NULL`, three additions to `/tool/{slug}`:

1. **Type badge** — pill next to tool name ("MCP Server" / "Plugin" / "Extension" / "Skill"), accent color, similar to verified badge
2. **Install command block** — dark code block with copy button, below tagline, above description. Primary CTA for plugins.
3. **Platform tags** — small pills below install block showing compatible platforms

Regular tools (`tool_type IS NULL`) render exactly as before.

---

## 5. MCP Server & Search Integration

Enrich existing responses when a result is a plugin:

- **Search API** (`/api/tools/search`): Add `tool_type`, `platforms`, `install_command` to JSON response for plugins
- **MCP server results**: Include install command inline, e.g. "Simple Analytics MCP Server — Install: `claude mcp add simple-analytics`"

No new MCP tools needed.

---

## Files to Modify

- `src/indiestack/db.py` — migration (3 columns), update `create_tool()`
- `src/indiestack/routes/submit.py` — toggle section, 3 new form fields
- `src/indiestack/routes/tool.py` — type badge, install block, platform tags
- `src/indiestack/routes/plugins.py` — NEW file, `/plugins` page with filters
- `src/indiestack/main.py` — register plugins router, enrich search API response
- `src/indiestack/routes/components.py` — nav dropdown: add "Plugins" link
- `src/indiestack/mcp_server.py` — enrich search results with install command
