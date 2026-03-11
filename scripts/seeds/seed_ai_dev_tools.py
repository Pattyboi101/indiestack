#!/usr/bin/env python3
"""Seed IndieStack with AI Dev Tools — MCP servers and AI coding assistants.

Usage:
    python3 seed_ai_dev_tools.py

Idempotent — uses INSERT OR IGNORE on unique slugs.
"""

import sqlite3
import os
import re

# Match the DB path from db.py
DB_PATH = os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")

# If the production path doesn't exist, fall back to local
if not os.path.exists(os.path.dirname(DB_PATH) or "/data"):
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indiestack.db")
    os.environ["INDIESTACK_DB_PATH"] = DB_PATH


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


# ── Makers ─────────────────────────────────────────────────────────────────
# (slug, name, url, bio, indie_status)
MAKERS = [
    ("stripe-devtools", "Stripe", "https://stripe.com",
     "Financial infrastructure for the internet.", "small_team"),
    ("fly-io", "Fly.io", "https://fly.io",
     "Run your full-stack apps close to your users.", "small_team"),
    ("anthropic-mcp", "Anthropic", "https://anthropic.com",
     "AI safety company. Creators of Claude and the Model Context Protocol.", "small_team"),
    ("sentry-devtools", "Sentry", "https://sentry.io",
     "Application monitoring for every developer.", "small_team"),
    ("nicholas-griffin", "Nicholas Griffin", "https://github.com/nicholasgriffintn",
     "Full-stack developer building MCP servers.", "solo"),
    ("xeol-io", "Xeol", "https://xeol.io",
     "Developer tools for community platforms.", "small_team"),
    ("cursor-inc", "Cursor Inc", "https://cursor.com",
     "Building the AI-first code editor.", "small_team"),
    ("continue-dev", "Continue", "https://continue.dev",
     "Open-source AI code assistant for any IDE.", "small_team"),
    ("paul-gauthier", "Paul Gauthier", "https://aider.chat",
     "Creator of Aider. AI pair programming in your terminal.", "solo"),
    ("sourcegraph", "Sourcegraph", "https://sourcegraph.com",
     "Code intelligence platform.", "small_team"),
    ("composio-dev", "Composio", "https://composio.dev",
     "Unified tool integrations for AI agents.", "small_team"),
]


# ── Tools ──────────────────────────────────────────────────────────────────
# (name, slug, tagline, description, url, maker_slug, category_slug, tags,
#  price_pence, replaces, upvotes)
TOOLS = [
    # ── MCP Servers ───────────────────────────────────────────────────────
    (
        "Stripe MCP Server",
        "stripe-mcp-server",
        "Official Stripe integration for Claude Code and AI agents",
        "The official Stripe MCP server lets AI agents create customers, manage "
        "subscriptions, issue refunds, and generate invoices directly from Claude "
        "Code. Supports all major Stripe API operations. Install with "
        "npx @stripe/mcp.",
        "https://github.com/stripe/agent-toolkit",
        "stripe-devtools",
        "ai-dev-tools",
        "mcp,mcp-server,payments,stripe,claude-code",
        0,
        "",
        28,
    ),
    (
        "Fly.io MCP Server",
        "flyio-mcp-server",
        "Manage Fly apps, machines, and deployments from Claude",
        "The official Fly.io MCP server gives AI assistants direct access to your "
        "Fly infrastructure. Deploy apps, scale machines, check logs, and manage "
        "secrets without leaving your editor. Built by the Fly.io team.",
        "https://github.com/superfly/fly-mcp",
        "fly-io",
        "ai-dev-tools",
        "mcp,mcp-server,deployment,fly-io,devops",
        0,
        "",
        22,
    ),
    (
        "SQLite MCP Server",
        "sqlite-mcp-server",
        "Query and inspect SQLite databases from Claude Code",
        "The official SQLite MCP server from Anthropic enables natural language "
        "database queries through Claude. Read schemas, run SQL, inspect tables, "
        "and analyze data without writing queries manually. Ideal for local-first "
        "apps and development databases.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic-mcp",
        "ai-dev-tools",
        "mcp,mcp-server,database,sqlite,sql",
        0,
        "",
        30,
    ),
    (
        "GitHub MCP Server",
        "github-mcp-server",
        "Manage PRs, issues, and repos from your AI assistant",
        "The official GitHub MCP server connects Claude Code to your repositories. "
        "Create and review pull requests, manage issues, search code, and automate "
        "Git workflows. Uses your existing GitHub authentication.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic-mcp",
        "ai-dev-tools",
        "mcp,mcp-server,github,git,code-review",
        0,
        "",
        35,
    ),
    (
        "Postgres MCP Server",
        "postgres-mcp-server",
        "Query and manage PostgreSQL databases from Claude",
        "The official PostgreSQL MCP server provides AI assistants with direct "
        "database access. Run queries, inspect schemas, analyze data, and manage "
        "tables through natural language. Supports connection pooling and read-only "
        "mode for safety.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic-mcp",
        "ai-dev-tools",
        "mcp,mcp-server,database,postgresql,sql",
        0,
        "",
        18,
    ),
    (
        "Filesystem MCP Server",
        "filesystem-mcp-server",
        "Secure file operations for AI coding assistants",
        "The official Filesystem MCP server gives Claude controlled access to "
        "read, write, and manage files within specified directories. Sandboxed "
        "by default with configurable permissions. Essential for AI-assisted "
        "development workflows.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic-mcp",
        "ai-dev-tools",
        "mcp,mcp-server,files,filesystem,open-source",
        0,
        "",
        15,
    ),
    (
        "Puppeteer MCP Server",
        "puppeteer-mcp-server",
        "Browser automation and testing from Claude Code",
        "The Puppeteer MCP server enables AI-driven browser automation. Navigate "
        "pages, fill forms, take screenshots, extract data, and run end-to-end "
        "tests through Claude. Built on Puppeteer with full Chrome DevTools "
        "Protocol support.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic-mcp",
        "ai-dev-tools",
        "mcp,mcp-server,browser-automation,testing,puppeteer",
        0,
        "",
        20,
    ),
    (
        "Brave Search MCP",
        "brave-search-mcp",
        "Web search results directly in Claude Code",
        "The Brave Search MCP server brings web search into AI workflows. Get "
        "real-time search results, news, and web content without leaving your "
        "editor. Privacy-focused search powered by Brave's independent index.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic-mcp",
        "ai-dev-tools",
        "mcp,mcp-server,search,web-search,brave",
        0,
        "",
        16,
    ),
    (
        "Sentry MCP Server",
        "sentry-mcp-server",
        "Error tracking and debugging from your AI assistant",
        "The official Sentry MCP server connects Claude to your error monitoring. "
        "Browse issues, analyze stack traces, find root causes, and suggest fixes "
        "without context-switching. Pull real production errors into your AI "
        "coding workflow.",
        "https://github.com/getsentry/sentry-mcp",
        "sentry-devtools",
        "ai-dev-tools",
        "mcp,mcp-server,error-tracking,debugging,sentry",
        0,
        "",
        14,
    ),
    (
        "Memory MCP Server",
        "memory-mcp-server",
        "Persistent knowledge graph for Claude Code sessions",
        "The Memory MCP server gives Claude a persistent knowledge graph that "
        "survives across sessions. Store project context, architectural decisions, "
        "and codebase knowledge. Entities and relationships are saved to a local "
        "JSON file.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic-mcp",
        "ai-dev-tools",
        "mcp,mcp-server,knowledge-graph,memory,context",
        0,
        "",
        19,
    ),
    (
        "Google Search Console MCP",
        "gsc-mcp-server",
        "SEO data and search analytics in Claude Code",
        "An MCP server for Google Search Console that brings SEO data into your "
        "AI workflow. Query search performance, inspect URLs, check indexing "
        "status, and manage sitemaps. Built for developers who want SEO insights "
        "without leaving the terminal.",
        "https://github.com/nicholasgriffintn/mcp-gsc",
        "nicholas-griffin",
        "ai-dev-tools",
        "mcp,mcp-server,seo,google,search-console",
        0,
        "",
        10,
    ),
    (
        "Reddit MCP Server",
        "reddit-mcp-server",
        "Browse and automate Reddit from Claude Code",
        "An MCP server for Reddit that lets AI assistants search subreddits, "
        "read posts and comments, and monitor discussions. Useful for market "
        "research, community engagement, and content analysis directly from "
        "your development environment.",
        "https://github.com/xeol-io/reddit-mcp-buddy",
        "xeol-io",
        "ai-dev-tools",
        "mcp,mcp-server,reddit,social-media,automation",
        0,
        "",
        8,
    ),
    # ── AI Coding Tools ───────────────────────────────────────────────────
    (
        "Cursor",
        "cursor-editor",
        "AI-first code editor built on VS Code",
        "Cursor is an AI-powered code editor forked from VS Code. Tab completion "
        "that predicts your next edit, inline chat for code generation, and "
        "codebase-aware answers. Supports GPT-4, Claude, and custom models. "
        "Free tier available, Pro from $20/mo.",
        "https://cursor.com",
        "cursor-inc",
        "ai-dev-tools",
        "ai-coding,code-editor,ai-assistant,vscode,copilot",
        2000,  # ~$20/mo
        "GitHub Copilot",
        40,
    ),
    (
        "Continue.dev",
        "continue-dev",
        "Open-source AI code assistant for any IDE",
        "Continue is an open-source AI code assistant that works in VS Code and "
        "JetBrains IDEs. Autocomplete, chat, and inline editing powered by any "
        "LLM -- Claude, GPT, Llama, Mistral, or local models. Fully "
        "customizable with your own API keys.",
        "https://continue.dev",
        "continue-dev",
        "ai-dev-tools",
        "ai-coding,open-source,vscode,jetbrains,ai-assistant",
        0,
        "GitHub Copilot",
        24,
    ),
    (
        "Aider",
        "aider",
        "AI pair programming in your terminal",
        "Aider is an open-source AI coding assistant that works in your terminal. "
        "Edit files, write tests, fix bugs, and refactor code through conversation. "
        "Works with Claude, GPT-4, and local models. Understands your entire "
        "git repo for context-aware changes.",
        "https://aider.chat",
        "paul-gauthier",
        "ai-dev-tools",
        "ai-coding,terminal,pair-programming,open-source,cli",
        0,
        "",
        32,
    ),
    (
        "Cody by Sourcegraph",
        "cody-sourcegraph",
        "AI coding assistant with full codebase context",
        "Cody is Sourcegraph's AI coding assistant that understands your entire "
        "codebase. Autocomplete, inline edits, and chat with deep context from "
        "your repositories. Free for individuals, supports Claude and GPT models. "
        "Available for VS Code, JetBrains, and Neovim.",
        "https://sourcegraph.com/cody",
        "sourcegraph",
        "ai-dev-tools",
        "ai-coding,ai-assistant,code-search,context,enterprise",
        0,
        "GitHub Copilot",
        18,
    ),
    (
        "Composio",
        "composio",
        "Unified tool integrations for AI agents and MCP",
        "Composio connects AI agents to 100+ tools through a single API. "
        "GitHub, Slack, Jira, Linear, Notion, and more -- all accessible via "
        "MCP or function calling. Handles auth, rate limits, and error handling. "
        "Free tier with generous limits.",
        "https://composio.dev",
        "composio-dev",
        "ai-dev-tools",
        "mcp,ai-agent,integrations,tools,open-source",
        0,
        "",
        12,
    ),
]


def main():
    print(f"Seeding AI Dev Tools at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Ensure AI Dev Tools category exists
    conn.execute(
        "INSERT OR IGNORE INTO categories (name, slug, description, icon) "
        "VALUES ('AI Dev Tools', 'ai-dev-tools', "
        "'MCP servers, AI coding assistants, and dev agent tools', '🧠')"
    )
    conn.commit()

    # Ensure replaces column exists
    try:
        conn.execute("SELECT replaces FROM tools LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE tools ADD COLUMN replaces TEXT NOT NULL DEFAULT ''")
        conn.commit()

    # Ensure indie_status column exists on makers
    try:
        conn.execute("SELECT indie_status FROM makers LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE makers ADD COLUMN indie_status TEXT NOT NULL DEFAULT ''")
        conn.commit()

    # ── Insert makers ──────────────────────────────────────────────────────
    for slug, name, url, bio, indie_status in MAKERS:
        conn.execute(
            "INSERT OR IGNORE INTO makers (slug, name, url, bio, indie_status) "
            "VALUES (?, ?, ?, ?, ?)",
            (slug, name, url, bio, indie_status),
        )
    conn.commit()
    print(f"  Makers: {conn.execute('SELECT count(*) FROM makers').fetchone()[0]}")

    # Build lookups
    cat_map = {}
    for row in conn.execute("SELECT id, slug FROM categories").fetchall():
        cat_map[row[1]] = row[0]

    maker_map = {}
    for row in conn.execute("SELECT id, slug FROM makers").fetchall():
        maker_map[row[1]] = row[0]

    # ── Insert tools ───────────────────────────────────────────────────────
    inserted = 0
    skipped = 0
    for (name, slug, tagline, description, url, maker_slug, category_slug,
         tags, price_pence, replaces, upvotes) in TOOLS:

        category_id = cat_map.get(category_slug)
        maker_id = maker_map.get(maker_slug)

        if not category_id:
            print(f"  WARNING: Unknown category '{category_slug}' for tool '{name}', skipping")
            skipped += 1
            continue

        # Look up maker name/url for denormalized fields
        maker_row = conn.execute(
            "SELECT name, url FROM makers WHERE id = ?", (maker_id,)
        ).fetchone()
        maker_name = maker_row[0] if maker_row else ""
        maker_url = maker_row[1] if maker_row else ""

        # price_pence: 0 for free tools -> store as NULL
        db_price = price_pence if price_pence and price_pence > 0 else None

        try:
            conn.execute(
                """INSERT OR IGNORE INTO tools
                   (name, slug, tagline, description, url, maker_name, maker_url,
                    category_id, tags, status, is_verified, upvote_count,
                    price_pence, delivery_type, maker_id, replaces)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', 0, ?, ?, 'link', ?, ?)""",
                (name, slug, tagline, description, url, maker_name, maker_url,
                 category_id, tags, upvotes, db_price, maker_id, replaces),
            )
            if conn.total_changes:
                inserted += 1
        except Exception as e:
            print(f"  ERROR inserting '{name}': {e}")
            skipped += 1

    conn.commit()
    tool_count = conn.execute("SELECT count(*) FROM tools WHERE status = 'approved'").fetchone()[0]
    print(f"  Tools: {tool_count} approved ({inserted} new this run, {skipped} skipped)")

    # ── Rebuild FTS indexes ────────────────────────────────────────────────
    print("  Rebuilding FTS indexes...")
    conn.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
    try:
        conn.execute("INSERT INTO makers_fts(makers_fts) VALUES('rebuild')")
    except Exception:
        pass  # makers_fts may not exist in all environments
    conn.commit()
    print("  FTS rebuild complete.")

    # ── Summary ────────────────────────────────────────────────────────────
    ai_count = conn.execute(
        "SELECT count(*) FROM tools WHERE status = 'approved' AND category_id = ?",
        (cat_map.get("ai-dev-tools"),)
    ).fetchone()[0]
    total = conn.execute("SELECT count(*) FROM tools WHERE status = 'approved'").fetchone()[0]
    print(f"\nDone. AI Dev Tools: {ai_count} | Total approved: {total}")

    conn.close()


if __name__ == "__main__":
    main()
