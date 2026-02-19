# IndieStack

A curated directory of 130+ indie SaaS tools with a built-in MCP server that lets AI coding assistants search the catalog before generating boilerplate.

**Your AI is writing code you don't need.** Instead of generating 47,000 tokens of analytics boilerplate, IndieStack finds an existing indie tool in 700 tokens.

[Website](https://indiestack.fly.dev)

---

## MCP Server Quick Start

IndieStack is published on PyPI as a Model Context Protocol (MCP) server. Install it and connect it to your AI coding assistant in under a minute.

### Claude Code

```bash
pip install indiestack
claude mcp add indiestack -- python -m indiestack.mcp_server
```

### Cursor

Add to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "indiestack": {
      "command": "python",
      "args": ["-m", "indiestack.mcp_server"]
    }
  }
}
```

### Windsurf

Add to your `~/.windsurf/mcp.json`:

```json
{
  "mcpServers": {
    "indiestack": {
      "command": "python",
      "args": ["-m", "indiestack.mcp_server"]
    }
  }
}
```

### Available Tools

The MCP server exposes two tools via stdio transport:

| Tool | Description |
|------|-------------|
| `search_indie_tools(query)` | Search the directory by keyword, category, or use case |
| `get_tool_details(slug)` | Get full details for a specific tool |

---

## What It Does

IndieStack is a web directory and discovery platform for independent software products.

- **Browse and search** 130+ curated indie SaaS tools across categories like analytics, auth, payments, email, and more
- **MCP integration** lets AI assistants recommend existing tools instead of generating boilerplate code
- **Maker profiles** for indie developers to showcase their products
- **Alternatives pages** for programmatic SEO (e.g., "IndieStack alternatives to Segment")
- **Stack analyzer** to evaluate tool combinations
- **Stripe Connect** payments for premium placements and Pro maker accounts
- **Reviews, wishlists, and changelogs** for community engagement

---

## Project Structure

```
src/indiestack/
├── main.py            # FastAPI app + route registration
├── db.py              # SQLite database layer
├── auth.py            # Authentication
├── payments.py        # Stripe Connect integration
├── email.py           # Transactional email (SMTP)
├── mcp_server.py      # MCP server (PyPI package entry point)
├── routes/
│   ├── components.py  # Shared UI components (page shell, nav, footer)
│   ├── landing.py     # Homepage
│   ├── browse.py      # Category browsing
│   ├── tool.py        # Tool detail pages
│   ├── search.py      # Search
│   ├── submit.py      # Tool submission
│   ├── admin.py       # Admin panel
│   ├── dashboard.py   # User dashboard
│   ├── maker.py       # Maker profiles
│   ├── alternatives.py# Programmatic SEO pages
│   ├── stacks.py      # Stack analyzer
│   └── ...            # Other routes
```

The frontend uses pure Python string templates with a shared component system -- no Jinja2 or JS framework required.

---

## Self-Hosting

### Requirements

- Python 3.11+
- SQLite

### Setup

```bash
git clone https://github.com/Pattyboi101/indiestack.git
cd indiestack
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[server]"
```

### Environment Variables

Create a `.env` file:

```
SECRET_KEY=your-secret-key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
SMTP_HOST=smtp.gmail.com
SMTP_USER=you@example.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=you@example.com
```

### Run

```bash
uvicorn src.indiestack.main:app --reload
```

The app will be available at `http://localhost:8000`.

### Seed Data

```bash
python3 seed_tools.py
```

Populates the database with sample indie tools for development.

### Deploy to Fly.io

```bash
fly deploy --remote-only
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a pull request

Please keep PRs focused and include a clear description of what changed and why.

---

## License

MIT
