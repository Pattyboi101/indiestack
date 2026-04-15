# IndieStack

Dependency guardrail for AI coding agents. Validates packages before installation, catches hallucinations and typosquats, and provides compatibility intelligence across 6,500+ developer tools.

**10,000+ PyPI installs** | **110,000+ unique visitors** | **23 MCP tools**

```bash
claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
```

Then ask your agent:
- "Validate this package before installing"
- "Find an auth solution for my Next.js app"
- "Check compatibility between these two tools"

---

## What it does

Before your AI installs a dependency or writes boilerplate — IndieStack validates it exists, checks for typosquats, and searches 6,500+ curated developer tools with real compatibility data from 4,500+ repos. You get install commands, health scores, and what tools actually work together in production.

"Indie" is the curation filter: independent developers and small teams. Focused, lean, maintained, honest pricing.

---

## Tech stack

- **Backend**: Python 3 / FastAPI / SQLite (FTS5 full-text search, WAL mode)
- **Infrastructure**: Fly.io / Docker / 48-endpoint smoke testing
- **MCP server**: Published on [PyPI](https://pypi.org/project/indiestack/) — 23 tools, 3 resources, 5 prompts
- **Auth**: GitHub OAuth via sessions
- **Payments**: Stripe subscriptions
- **Monitoring**: Event reactor, pattern detection, Telegram alerting

---

## Install

**Claude Code** (zero install — runs via uvx):
```bash
claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
```

**Claude Desktop** — add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "indiestack": {
      "command": "uvx",
      "args": ["--from", "indiestack", "indiestack-mcp"]
    }
  }
}
```

**Cursor / Windsurf** — add to your MCP config:
```json
{"command": "uvx", "args": ["--from", "indiestack", "indiestack-mcp"]}
```

**Persistent install:**
```bash
pipx install indiestack
claude mcp add indiestack -- indiestack-mcp
```

**CLI (terminal use):**
```bash
pip install indiestack

indiestack search "analytics"
indiestack details simple-analytics
indiestack stack "auth, payments, email"
```

---

## Tools (23)

| Tool | What it does |
|------|-------------|
| `find_tools` | Search 6,500+ developer tools with 11 filters: price, health, stars, success rate, language, tags, compatibility |
| `find_compatible` | Find tools compatible with a given tool — grouped by category, with verified stacks and conflict warnings |
| `get_tool_details` | Integration code, pricing, API specs, and compatibility data |
| `scan_project` | Analyze a project description + tech stack, get a complete tool recommendation |
| `report_compatibility` | Report that two tools work well together — builds the compatibility graph |
| `report_outcome` | Report success/failure with `used_with` and `incompatible_with` — feeds the compatibility graph |
| `check_health` | GitHub health audit — maintenance grade, last commit, stars, alternatives for stale tools |
| `list_categories` | Browse all 25 categories |
| `compare_tools` | Side-by-side comparison of any two tools |
| `build_stack` | Turn a 50,000-token generation into a 2,000-token assembly |
| `publish_tool` | Submit a developer tool so other agents can recommend it |
| `browse_new_tools` | Recently added tools with pagination |
| `list_tags` | All tags sorted by popularity |
| `get_market_gaps` | Top unmet needs — what developers search for but can't find |
| `list_stacks` | Curated stacks for common use cases |
| `analyze_dependencies` | Scan package.json/requirements.txt for better alternatives |
| `evaluate_build_vs_buy` | Financial breakdown: build from scratch vs use what exists |
| `get_recommendations` | Personalized suggestions based on your search history |

### Resources

| Resource | What it provides |
|----------|-----------------|
| `indiestack://categories` | All 25 categories with slugs for filtering |
| `indiestack://trending` | Top 10 trending developer tools this week |
| `indiestack://tools-index` | Complete index for prompt caching — include once, reference forever |

### Prompts

| Prompt | When to use |
|--------|-------------|
| `before-you-build` | Check IndieStack before building common functionality |
| `find-alternatives` | Find indie alternatives to mainstream SaaS products |
| `save-tokens` | Audit your project for token-saving opportunities |
| `architect-feature` | Plan a feature using existing indie building blocks |
| `discover-indie` | Explore what indie developers have built |

---

## What's new in v1.19

- **Package validation** — `validate_package()` verifies packages exist and are safe before installation. Catches hallucinated and typosquatted packages.
- **Guardrail-first design** — Built for AI agents that need to validate dependencies, not just discover them.

## Recent highlights

- **Migration intelligence** — Tool details include real migration data from 4,500+ GitHub repos.
- **93,000+ verified package combinations** from production repos.
- **Trust-weighted search** — Tools with higher agent success rates rank higher.
- **Market gaps** — `get_market_gaps()` exposes zero-result queries ranked by search volume.

---

## Links

- [indiestack.ai](https://indiestack.ai)
- [Explore Tools](https://indiestack.ai/explore)
- [Submit Your Tool](https://indiestack.ai/submit)
- [What is IndieStack?](https://indiestack.ai/what-is-indiestack)

---

MIT License
