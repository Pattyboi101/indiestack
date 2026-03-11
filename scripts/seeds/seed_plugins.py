#!/usr/bin/env python3
"""Seed the IndieStack database with real MCP servers, plugins, and extensions.

Usage:
    python3 seed_plugins.py

Idempotent — safe to run multiple times. Uses INSERT OR IGNORE on unique slugs.
All tools are auto-approved and have tool_type, platforms, and install_command set.
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
    ("anthropic", "Anthropic", "https://anthropic.com", "Creators of Claude and the Model Context Protocol.", "small_team"),
    ("github-org", "GitHub", "https://github.com", "The world's leading software development platform.", "small_team"),
    ("notion-labs", "Notion", "https://notion.so", "The connected workspace for modern teams.", "small_team"),
    ("stripe-org", "Stripe", "https://stripe.com", "Financial infrastructure for the internet.", "small_team"),
    ("linear-app", "Linear", "https://linear.app", "The issue tracking tool you'll enjoy using.", "small_team"),
    ("cloudflare-org", "Cloudflare", "https://cloudflare.com", "Making the internet faster, safer, and smarter.", "small_team"),
    ("vercel-org", "Vercel", "https://vercel.com", "The platform for frontend developers.", "small_team"),
    ("figma-org", "Figma", "https://figma.com", "The collaborative interface design tool.", "small_team"),
    ("supabase-org", "Supabase", "https://supabase.com", "The open-source Firebase alternative.", "small_team"),
    ("neon-org", "Neon", "https://neon.tech", "Serverless Postgres built for the cloud.", "small_team"),
    ("microsoft-org", "Microsoft", "https://microsoft.com", "Technology for people and organizations.", "small_team"),
    ("brave-org", "Brave", "https://brave.com", "Privacy-first browser and search engine.", "small_team"),
    ("sentry-org", "Sentry", "https://sentry.io", "Application monitoring and error tracking.", "small_team"),
    ("redis-org", "Redis", "https://redis.io", "The real-time data platform.", "small_team"),
    ("firecrawl-org", "Firecrawl", "https://firecrawl.dev", "Turn websites into LLM-ready data.", "small_team"),
    ("e2b-org", "E2B", "https://e2b.dev", "Secure cloud sandboxes for AI agents.", "small_team"),
    ("upstash-org", "Upstash", "https://upstash.com", "Serverless data for developers.", "small_team"),
    ("exa-org", "Exa", "https://exa.ai", "AI-native search built for agents.", "small_team"),
    ("tavily-org", "Tavily", "https://tavily.com", "Search API optimized for AI agents.", "small_team"),
    ("apify-org", "Apify", "https://apify.com", "Web scraping and automation platform.", "small_team"),
    ("prisma-org", "Prisma", "https://prisma.io", "Next-generation Node.js and TypeScript ORM.", "small_team"),
    ("composio-org", "Composio", "https://composio.dev", "250+ SaaS integrations for AI agents.", "small_team"),
    ("yamadashy", "Yamadashy", "https://github.com/yamadashy", "Creator of Repomix.", "solo"),
    ("wonderwhy-er", "Eduard Ruzga", "https://github.com/wonderwhy-er", "Creator of Desktop Commander MCP.", "solo"),
    ("perplexity-org", "Perplexity AI", "https://perplexity.ai", "AI-powered answer engine.", "small_team"),
    ("motherduck-org", "MotherDuck", "https://motherduck.com", "DuckDB in the cloud.", "small_team"),
    ("aws-org", "Amazon Web Services", "https://aws.amazon.com", "Cloud computing by Amazon.", "small_team"),
    ("clickhouse-org", "ClickHouse", "https://clickhouse.com", "Fast open-source OLAP database.", "small_team"),
    ("neo4j-org", "Neo4j", "https://neo4j.com", "The graph database platform.", "small_team"),
    ("postman-org", "Postman", "https://postman.com", "The API platform for building and using APIs.", "small_team"),
    ("dbt-labs", "dbt Labs", "https://getdbt.com", "The analytics engineering platform.", "small_team"),
    ("slack-org", "Slack", "https://slack.com", "Where work happens.", "small_team"),
    ("amplitude-org", "Amplitude", "https://amplitude.com", "Digital analytics for product teams.", "small_team"),
    ("windsurf-org", "Windsurf", "https://windsurf.com", "AI-powered code editor by Codeium.", "small_team"),
]

# ── Plugins & MCP Servers ──────────────────────────────────────────────────
# (name, slug, tagline, description, url, maker_slug, category_slug, tags,
#  tool_type, platforms, install_command, price_pence)

PLUGINS = [
    # ── Official Reference MCP Servers (Anthropic) ──────────────────────────

    (
        "MCP Filesystem Server",
        "mcp-filesystem-server",
        "Secure file operations with configurable access controls",
        "Official reference MCP server for reading, writing, and navigating the local filesystem. "
        "Supports configurable access controls so the AI can only reach directories you permit.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic",
        "developer-tools",
        "filesystem,files,local,read-write,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @modelcontextprotocol/server-filesystem /path/to/allowed",
        None,
    ),
    (
        "MCP Memory Server",
        "mcp-memory-server",
        "Knowledge graph-based persistent memory for AI agents",
        "Official reference MCP server that gives AI assistants a persistent knowledge graph memory. "
        "Entities, relations, and observations survive across sessions, enabling long-term context.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic",
        "ai-automation",
        "memory,knowledge-graph,persistence,context,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @modelcontextprotocol/server-memory",
        None,
    ),
    (
        "MCP Fetch Server",
        "mcp-fetch-server",
        "Web content fetching and conversion for efficient LLM usage",
        "Official reference MCP server that fetches URLs and converts HTML to clean Markdown for LLM consumption. "
        "Strips ads, navigation, and boilerplate automatically.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic",
        "developer-tools",
        "web,fetch,html,markdown,scraping,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @modelcontextprotocol/server-fetch",
        None,
    ),
    (
        "MCP Git Server",
        "mcp-git-server",
        "Read, search, and manipulate Git repositories via MCP",
        "Official reference MCP server providing tools to interact with Git repositories. "
        "Supports reading history, searching commits, diffing branches, and creating commits.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic",
        "developer-tools",
        "git,version-control,commits,diff,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "uvx mcp-server-git",
        None,
    ),
    (
        "MCP Sequential Thinking",
        "mcp-sequential-thinking",
        "Dynamic and reflective problem-solving through thought sequences",
        "Official reference MCP server that structures AI reasoning into explicit sequential thought steps. "
        "Helps AI assistants approach complex problems methodically and revise reasoning mid-stream.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic",
        "ai-automation",
        "reasoning,thinking,chain-of-thought,planning,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @modelcontextprotocol/server-sequential-thinking",
        None,
    ),

    # ── Database MCP Servers ────────────────────────────────────────────────

    (
        "MCP PostgreSQL Server",
        "mcp-postgres-server",
        "Query and inspect PostgreSQL databases via MCP",
        "Official MCP server for connecting AI assistants to PostgreSQL databases. "
        "Supports read-only schema inspection and SQL query execution with full connection string configuration.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic",
        "developer-tools",
        "postgres,sql,database,queries,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @modelcontextprotocol/server-postgres postgresql://localhost/mydb",
        None,
    ),
    (
        "MCP SQLite Server",
        "mcp-sqlite-server",
        "Interact with SQLite databases through MCP",
        "Official MCP server for SQLite database interaction. Allows AI to query, inspect schemas, "
        "and run analytical queries against local SQLite files with built-in memo summarization.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic",
        "developer-tools",
        "sqlite,sql,database,local,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "uvx mcp-server-sqlite --db-path /path/to/db.sqlite",
        None,
    ),
    (
        "Redis MCP Server",
        "redis-mcp-server",
        "Natural language interface for Redis data management",
        "Official Redis MCP server built by the Redis team. Enables AI agents to get, set, search, "
        "and manage data in Redis with support for all major Redis data structures.",
        "https://github.com/redis/mcp-redis",
        "redis-org",
        "developer-tools",
        "redis,cache,key-value,database,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @modelcontextprotocol/server-redis redis://localhost:6379",
        None,
    ),
    (
        "Neon MCP Server",
        "neon-mcp-server",
        "Serverless Postgres management and querying for AI agents",
        "Official MCP server from Neon for interacting with the Neon serverless Postgres platform. "
        "Supports database creation, branching, SQL queries, and management API access.",
        "https://github.com/neondatabase/mcp-server-neon",
        "neon-org",
        "developer-tools",
        "postgres,serverless,database,neon,branching,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "npx -y @neondatabase/mcp-server-neon",
        None,
    ),
    (
        "Supabase MCP Server",
        "supabase-mcp-server",
        "Connect AI assistants to Supabase projects and databases",
        "Official community MCP server for Supabase. Manages databases, tables, auth, storage, "
        "and edge functions. Also accessible via the Supabase dashboard MCP connection tab.",
        "https://github.com/supabase-community/supabase-mcp",
        "supabase-org",
        "developer-tools",
        "supabase,postgres,database,auth,storage,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "npx -y @supabase/mcp-server-supabase@latest",
        None,
    ),
    (
        "MotherDuck MCP Server",
        "motherduck-mcp-server",
        "Query and analyze data with DuckDB and MotherDuck",
        "Official MCP server from MotherDuck for in-process analytical queries via DuckDB. "
        "Supports both local DuckDB files and cloud MotherDuck databases with full SQL analytics.",
        "https://github.com/motherduckdb/mcp-server-motherduck",
        "motherduck-org",
        "analytics-metrics",
        "duckdb,analytics,sql,motherduck,olap,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "uvx mcp-server-motherduck",
        None,
    ),
    (
        "Neo4j MCP Server",
        "neo4j-mcp-server",
        "Query and explore graph databases with natural language",
        "MCP server for Neo4j graph databases with Cypher query support. Enables AI assistants "
        "to traverse relationships, run graph algorithms, and explore connected data structures.",
        "https://github.com/neo4j-contrib/mcp-neo4j",
        "neo4j-org",
        "developer-tools",
        "neo4j,graph-database,cypher,relationships,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "uvx mcp-neo4j",
        None,
    ),
    (
        "ClickHouse MCP Server",
        "clickhouse-mcp-server",
        "Query ClickHouse analytics databases with AI",
        "Official ClickHouse MCP server for connecting AI assistants to ClickHouse OLAP databases. "
        "Supports schema inspection, SQL queries, and high-performance analytical workloads.",
        "https://github.com/ClickHouse/mcp-clickhouse",
        "clickhouse-org",
        "analytics-metrics",
        "clickhouse,analytics,olap,sql,database,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "uvx mcp-clickhouse",
        None,
    ),
    (
        "Prisma MCP Server",
        "prisma-mcp-server",
        "AI-assisted database schema management with Prisma",
        "Official Prisma MCP server for schema migrations, type-safe queries, and database management. "
        "Works with Prisma ORM projects to let AI assistants understand and modify your data model.",
        "https://www.prisma.io/docs/postgres/integrations/mcp-server",
        "prisma-org",
        "developer-tools",
        "prisma,orm,database,schema,migrations,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "npx -y prisma mcp",
        None,
    ),

    # ── Cloud & API MCP Servers ─────────────────────────────────────────────

    (
        "GitHub MCP Server",
        "github-mcp-server",
        "GitHub's official MCP server for repos, issues, and PRs",
        "GitHub's official MCP server written in Go. Gives AI assistants full access to repositories, "
        "issues, pull requests, code search, and GitHub Actions through the GitHub API.",
        "https://github.com/github/github-mcp-server",
        "github-org",
        "developer-tools",
        "github,git,repos,issues,pull-requests,ci-cd,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "docker run ghcr.io/github/github-mcp-server",
        None,
    ),
    (
        "Notion MCP Server",
        "notion-mcp-server",
        "Connect AI assistants to your Notion workspace",
        "Official Notion MCP server with 22 tools for reading, creating, and editing Notion pages "
        "and databases. Optimized for token efficiency with Markdown-based page editing.",
        "https://github.com/makenotion/notion-mcp-server",
        "notion-labs",
        "project-management",
        "notion,notes,workspace,databases,pages,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @notionhq/notion-mcp-server",
        None,
    ),
    (
        "Slack MCP Server",
        "slack-mcp-server",
        "Read and send Slack messages from AI assistants",
        "Official Slack MCP server for channel management, message reading, and posting. "
        "Requires a Slack bot token and supports scoped channel access via environment variables.",
        "https://github.com/modelcontextprotocol/servers",
        "slack-org",
        "project-management",
        "slack,messaging,channels,notifications,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @modelcontextprotocol/server-slack",
        None,
    ),
    (
        "Stripe MCP Server",
        "stripe-mcp-server",
        "Build and test Stripe payment integrations with AI",
        "Official Stripe MCP server for interacting with the Stripe API. Supports customers, payments, "
        "subscriptions, and refunds. Also available as a hosted server at mcp.stripe.com.",
        "https://github.com/stripe/agent-toolkit",
        "stripe-org",
        "payments",
        "stripe,payments,billing,subscriptions,api,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "npx -y @stripe/mcp --api-key=$STRIPE_SECRET_KEY",
        None,
    ),
    (
        "Linear MCP Server",
        "linear-mcp-server",
        "Access and manage Linear issues from AI assistants",
        "Official Linear MCP server hosted by Linear. Supports reading and creating issues, projects, "
        "and documents across your Linear workspace. Connects via OAuth or remote URL.",
        "https://linear.app/docs/mcp",
        "linear-app",
        "project-management",
        "linear,issues,project-management,planning,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "npx -y mcp-remote https://mcp.linear.app/mcp",
        None,
    ),
    (
        "Cloudflare MCP Server",
        "cloudflare-mcp-server",
        "Deploy and manage Cloudflare Workers, KV, and R2 with AI",
        "Official Cloudflare MCP server for interacting with Workers, KV namespaces, R2 buckets, "
        "D1 databases, and Cloudflare observability.",
        "https://github.com/cloudflare/mcp-server-cloudflare",
        "cloudflare-org",
        "developer-tools",
        "cloudflare,workers,serverless,cdn,kv,r2,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "npx -y @cloudflare/mcp-server-cloudflare",
        None,
    ),
    (
        "Vercel MCP Server",
        "vercel-mcp-server",
        "Manage Vercel deployments and projects from AI agents",
        "Official Vercel remote MCP server for project management, deployment monitoring, "
        "environment variables, and build log retrieval. Connects via OAuth.",
        "https://vercel.com/docs/workflow-collaboration/vercel-mcp",
        "vercel-org",
        "developer-tools",
        "vercel,deployment,hosting,serverless,nextjs,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "claude mcp add --transport http vercel https://mcp.vercel.com",
        None,
    ),
    (
        "Figma MCP Server",
        "figma-mcp-server",
        "Translate Figma designs into code with AI",
        "Official Figma MCP server exposing live design structure, tokens, components, and variants "
        "to AI coding assistants. Available as a remote server or via the Figma desktop app.",
        "https://github.com/figma/figma-mcp-server",
        "figma-org",
        "design-creative",
        "figma,design,ui,components,design-to-code,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "claude mcp add --transport http figma https://mcp.figma.com/mcp",
        None,
    ),
    (
        "Google Drive MCP Server",
        "google-drive-mcp-server",
        "List, search, and read files from Google Drive",
        "Official MCP server for Google Drive integration. Reads Google Docs as Markdown, "
        "Sheets as CSV, and Presentations as plain text. Supports full-text search across your Drive.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic",
        "file-management",
        "google-drive,gdocs,gsheets,files,google,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @modelcontextprotocol/server-gdrive",
        None,
    ),
    (
        "AWS MCP Servers",
        "aws-mcp-servers",
        "Official AWS MCP servers for documentation, CDK, and more",
        "A suite of official AWS MCP servers from AWS Labs covering documentation search, "
        "CDK advice, cost analysis, core AWS API access, and Terraform. All Python-based.",
        "https://github.com/awslabs/mcp",
        "aws-org",
        "developer-tools",
        "aws,cloud,documentation,cdk,terraform,infrastructure,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "uvx awslabs.aws-documentation-mcp-server@latest",
        None,
    ),
    (
        "Sentry MCP Server",
        "sentry-mcp-server",
        "Give AI full context on your application errors and issues",
        "Official Sentry remote MCP server with OAuth authentication. Provides AI assistants with "
        "access to Sentry issues, stack traces, Seer AI analysis, and performance data.",
        "https://docs.sentry.io/product/sentry-mcp/",
        "sentry-org",
        "monitoring-uptime",
        "sentry,errors,monitoring,debugging,observability,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "claude mcp add --transport http sentry https://mcp.sentry.dev/mcp",
        None,
    ),

    # ── Browser & Dev Tool MCP Servers ──────────────────────────────────────

    (
        "Playwright MCP Server",
        "playwright-mcp-server",
        "Browser automation and testing via accessibility tree",
        "Official Microsoft MCP server for Playwright browser automation. Uses accessibility snapshots "
        "instead of screenshots for fast, reliable web interaction — no vision model needed.",
        "https://github.com/microsoft/playwright-mcp",
        "microsoft-org",
        "developer-tools",
        "playwright,browser,automation,testing,e2e,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @playwright/mcp@latest",
        None,
    ),
    (
        "Puppeteer MCP Server",
        "puppeteer-mcp-server",
        "Control Chrome with AI via Puppeteer",
        "Official MCP server for Puppeteer browser automation. Enables AI to navigate pages, "
        "click elements, fill forms, take screenshots, and execute JavaScript in a real browser.",
        "https://github.com/modelcontextprotocol/servers",
        "anthropic",
        "developer-tools",
        "puppeteer,browser,chrome,automation,screenshots,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @modelcontextprotocol/server-puppeteer",
        None,
    ),
    (
        "Desktop Commander MCP",
        "desktop-commander-mcp",
        "Terminal control and file management for Claude",
        "Popular community MCP server that gives Claude terminal control, filesystem search, "
        "and diff-based file editing. One of the most-used community MCP servers.",
        "https://github.com/wonderwhy-er/DesktopCommanderMCP",
        "wonderwhy-er",
        "developer-tools",
        "terminal,shell,files,ssh,diff,editing,mcp",
        "mcp_server",
        "Claude Code, Claude Desktop",
        "npx -y @wonderwhy-er/desktop-commander@latest",
        None,
    ),

    # ── Search & Knowledge MCP Servers ──────────────────────────────────────

    (
        "Brave Search MCP Server",
        "brave-search-mcp-server",
        "Privacy-first web search for AI assistants",
        "Official Brave Search MCP server for real-time web, news, image, and video search. "
        "Uses Brave's independent search index with no Google tracking.",
        "https://github.com/brave/brave-search-mcp-server",
        "brave-org",
        "developer-tools",
        "search,web,news,privacy,brave,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @brave/brave-search-mcp-server",
        None,
    ),
    (
        "Exa MCP Server",
        "exa-mcp-server",
        "AI-native semantic web search and research",
        "Official Exa MCP server for semantic web search built specifically for AI use cases. "
        "Supports web search, code search, company research, and content extraction.",
        "https://github.com/exa-labs/exa-mcp-server",
        "exa-org",
        "developer-tools",
        "search,semantic,research,web,ai-search,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "claude mcp add --transport http exa https://mcp.exa.ai/mcp",
        None,
    ),
    (
        "Tavily MCP Server",
        "tavily-mcp-server",
        "Real-time search and extraction optimized for AI agents",
        "Official Tavily MCP server with real-time web search, content extraction, site mapping, "
        "and crawling — all optimized for AI agent workflows. 1,000 free monthly credits.",
        "https://github.com/tavily-ai/tavily-mcp",
        "tavily-org",
        "developer-tools",
        "search,extraction,research,web,ai-agent,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y tavily-mcp@latest",
        None,
    ),
    (
        "Perplexity MCP Server",
        "perplexity-mcp-server",
        "Real-time AI-powered research via Perplexity Sonar",
        "Official Perplexity MCP server using the Sonar API for real-time web research with citations. "
        "Gives AI assistants access to current information beyond their training cutoff.",
        "https://github.com/perplexityai/modelcontextprotocol",
        "perplexity-org",
        "ai-automation",
        "perplexity,search,research,citations,real-time,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @perplexity-ai/mcp-server",
        None,
    ),
    (
        "Context7 MCP Server",
        "context7-mcp-server",
        "Up-to-date library documentation for AI code editors",
        "MCP server by Upstash that fetches version-specific library documentation on demand. "
        "Solves LLM training data staleness by injecting current docs for React, Next.js, Prisma, and more.",
        "https://github.com/upstash/context7",
        "upstash-org",
        "developer-tools",
        "documentation,libraries,context,versioned-docs,coding,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "npx -y @upstash/context7-mcp",
        None,
    ),

    # ── Specialized MCP Servers ─────────────────────────────────────────────

    (
        "Firecrawl MCP Server",
        "firecrawl-mcp-server",
        "Scrape, crawl, and extract web data for AI",
        "Official Firecrawl MCP server for web scraping and data extraction. Turns any website "
        "into clean LLM-ready Markdown by stripping navigation, ads, and HTML noise.",
        "https://github.com/mendableai/firecrawl-mcp-server",
        "firecrawl-org",
        "developer-tools",
        "scraping,web,crawling,extraction,markdown,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y firecrawl-mcp",
        None,
    ),
    (
        "E2B MCP Server",
        "e2b-mcp-server",
        "Secure cloud sandboxes for AI code execution",
        "Official E2B MCP server that adds cloud code execution to AI assistants. Run Python, "
        "JavaScript, and shell commands in secure isolated sandboxes without local setup.",
        "https://github.com/e2b-dev/mcp-server",
        "e2b-org",
        "developer-tools",
        "code-execution,sandbox,python,javascript,cloud,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @e2b/mcp-server",
        None,
    ),
    (
        "Repomix MCP Server",
        "repomix-mcp-server",
        "Pack entire codebases into AI-friendly context",
        "MCP server mode for Repomix, which bundles an entire repository into a single structured "
        "file for LLM context. Respects .gitignore and supports XML, Markdown, or plain text output.",
        "https://repomix.com",
        "yamadashy",
        "developer-tools",
        "codebase,context,repository,packing,analysis,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y repomix --mcp",
        None,
    ),
    (
        "Composio MCP Server",
        "composio-mcp-server",
        "250+ SaaS integrations in a single MCP server",
        "Composio provides a managed MCP server exposing over 250 tool integrations (GitHub, Slack, "
        "Gmail, Notion, HubSpot, Linear) with centralized OAuth and credential management.",
        "https://composio.dev",
        "composio-org",
        "ai-automation",
        "integrations,saas,connectors,oauth,automation,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @composio/mcp@latest",
        None,
    ),
    (
        "Apify MCP Server",
        "apify-mcp-server",
        "3,000+ pre-built cloud actors for web scraping and automation",
        "Official Apify MCP server giving AI assistants access to over 3,000 pre-built cloud actors "
        "for web scraping, data extraction, and browser automation tasks.",
        "https://github.com/apify/actors-mcp-server",
        "apify-org",
        "developer-tools",
        "scraping,automation,actors,web-data,cloud,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf, Claude Desktop",
        "npx -y @apify/actors-mcp-server",
        None,
    ),
    (
        "Postman MCP Server",
        "postman-mcp-server",
        "API testing and collection management for AI agents",
        "Official Postman MCP server for managing API collections, running tests, and interacting "
        "with the Postman platform. Create, modify, and execute API tests programmatically.",
        "https://github.com/postmanlabs/postman-mcp-server",
        "postman-org",
        "api-tools",
        "postman,api,testing,collections,rest,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "npx -y @postman/mcp-server",
        None,
    ),
    (
        "dbt MCP Server",
        "dbt-mcp-server",
        "AI-assisted data transformation with dbt",
        "Official dbt Labs MCP server for interacting with dbt projects. Supports model execution, "
        "lineage exploration, documentation access, and query running across dbt-managed pipelines.",
        "https://github.com/dbt-labs/dbt-mcp",
        "dbt-labs",
        "analytics-metrics",
        "dbt,data-transformation,analytics,sql,pipelines,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "uvx dbt-mcp",
        None,
    ),
    (
        "Datadog MCP Server",
        "datadog-mcp-server",
        "Query Datadog metrics, traces, logs, and dashboards with AI",
        "Official Datadog remote MCP server for monitoring and observability. AI assistants can "
        "query traces, logs, metrics, dashboards, and incidents directly via the Datadog API.",
        "https://www.datadoghq.com/blog/datadog-remote-mcp-server/",
        None,  # No maker entry — Datadog not in our maker list as standalone
        "monitoring-uptime",
        "datadog,monitoring,observability,logs,metrics,tracing,mcp",
        "mcp_server",
        "Claude Code, Cursor, Windsurf",
        "npx -y datadog-mcp-server",
        None,
    ),
]


def main():
    print(f"Seeding plugins at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Ensure plugin columns exist (migration)
    for col, typedef in [
        ("tool_type", "TEXT DEFAULT NULL"),
        ("platforms", "TEXT NOT NULL DEFAULT ''"),
        ("install_command", "TEXT NOT NULL DEFAULT ''"),
    ]:
        try:
            conn.execute(f"SELECT {col} FROM tools LIMIT 1")
        except Exception:
            conn.execute(f"ALTER TABLE tools ADD COLUMN {col} {typedef}")
            print(f"  Added column: {col}")

    # Ensure indie_status column exists on makers
    try:
        conn.execute("SELECT indie_status FROM makers LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE makers ADD COLUMN indie_status TEXT NOT NULL DEFAULT ''")

    conn.commit()

    # ── Build category lookup ──────────────────────────────────────────────
    cat_map = {}
    for row in conn.execute("SELECT id, slug FROM categories").fetchall():
        cat_map[row[1]] = row[0]
    print(f"  Categories loaded: {len(cat_map)}")

    if not cat_map:
        print("  ERROR: No categories found. Run seed_tools.py first.")
        conn.close()
        return

    # ── Insert makers ──────────────────────────────────────────────────────
    maker_inserted = 0
    for slug, name, url, bio, indie_status in MAKERS:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO makers (slug, name, url, bio, indie_status) VALUES (?, ?, ?, ?, ?)",
            (slug, name, url, bio, indie_status),
        )
        if cursor.rowcount:
            maker_inserted += 1
    conn.commit()
    print(f"  Makers: {maker_inserted} new")

    # Build maker slug -> id lookup
    maker_map = {}
    for row in conn.execute("SELECT id, slug FROM makers").fetchall():
        maker_map[row[1]] = row[0]

    # ── Insert plugins ─────────────────────────────────────────────────────
    inserted = 0
    skipped = 0

    for (name, slug, tagline, description, url, maker_slug, category_slug, tags,
         tool_type, platforms, install_command, price_pence) in PLUGINS:

        category_id = cat_map.get(category_slug)
        if not category_id:
            print(f"  WARNING: Unknown category '{category_slug}' for '{name}', skipping")
            skipped += 1
            continue

        maker_id = maker_map.get(maker_slug) if maker_slug else None
        maker_name = ""
        maker_url = ""
        if maker_id:
            maker_row = conn.execute(
                "SELECT name, url FROM makers WHERE id = ?", (maker_id,)
            ).fetchone()
            if maker_row:
                maker_name = maker_row[0]
                maker_url = maker_row[1]

        db_price = price_pence if price_pence and price_pence > 0 else None

        try:
            conn.execute(
                """INSERT OR IGNORE INTO tools
                   (name, slug, tagline, description, url, maker_name, maker_url,
                    category_id, tags, status, is_verified, upvote_count,
                    price_pence, delivery_type, maker_id,
                    tool_type, platforms, install_command)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', 0, 0, ?, 'link', ?, ?, ?, ?)""",
                (name, slug, tagline, description, url, maker_name, maker_url,
                 category_id, tags, db_price, maker_id,
                 tool_type, platforms, install_command),
            )
            if conn.total_changes:
                inserted += 1
        except Exception as e:
            print(f"  ERROR inserting '{name}': {e}")
            skipped += 1

    conn.commit()

    # Count results
    total = conn.execute("SELECT count(*) FROM tools").fetchone()[0]
    plugin_count = conn.execute(
        "SELECT count(*) FROM tools WHERE tool_type IS NOT NULL"
    ).fetchone()[0]
    print(f"  Plugins inserted: {inserted} new ({skipped} skipped)")
    print(f"  Total tools: {total} ({plugin_count} with tool_type)")

    # ── Rebuild FTS indexes ────────────────────────────────────────────────
    print("  Rebuilding FTS indexes...")
    try:
        conn.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
        conn.commit()
        print("  FTS rebuild complete.")
    except Exception as e:
        print(f"  FTS rebuild skipped: {e}")

    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()
