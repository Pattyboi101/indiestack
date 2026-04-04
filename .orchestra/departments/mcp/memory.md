# Mcp Memory

_You are a persistent agent. This file is your long-term knowledge base._
_Read this on startup. Update it after each task with what you learned._
_Focus on: file locations, patterns, gotchas, past decisions, domain knowledge._

---

## Registry Distribution Status (2026-04-01)

### Our identifiers
- PyPI: `indiestack` (current v1.12.0)
- Install: `uvx --from indiestack indiestack-mcp`
- GitHub: `Pattyboi101/indiestack`
- server.json namespace: `io.github.Pattyboi101/indiestack`

### Registry Status
| Registry | Status | Version | Action |
|---|---|---|---|
| Official MCP Registry (registry.modelcontextprotocol.io) | LISTED but stale | 1.4.0 (need 1.12.0) | Re-publish |
| Smithery (smithery.ai) | Unknown (403/429 blocks) | Unknown | Verify manually |
| Glama (glama.ai) | NOT listed | — | Submit via "Add Server" button |
| PulseMCP (pulsemcp.com) | NOT listed | — | Auto-ingests from official registry OR submit URL at /submit |
| mcpservers.org | NOT listed | — | Free form: name/desc/link/category/email |

### server.json
- Already prepared at `/home/patty/indiestack/server.json` (in git modified state)
- Currently says v1.11.1, but PyPI is at v1.12.0 — needs version bump before republish
- Namespace: `io.github.Pattyboi101/indiestack` — valid for GitHub OAuth auth

### Official Registry Publish Process
1. Install mcp-publisher CLI (Homebrew or binary)
2. Update server.json version to match PyPI (1.12.0)
3. `mcp-publisher login github` (device flow)
4. `mcp-publisher publish`
5. PulseMCP auto-ingests daily from official registry

## Dog-Fooding Results (2026-04-01)

### Search Issues Found

| Query | Issue | Severity |
|---|---|---|
| "email" | Top 3 results all have MISSING install_command (`email`, `email-templates`, `email-builder-js`) | High |
| "email" | `logto` (auth tool) appears at #4 — wrong category entirely | High |
| "email" | Resend doesn't appear at all despite being the go-to transactional email tool | High |
| "email sending" | ALL 5 results have MISSING install_command | High |
| "payments" | Killbill (heavy enterprise Java platform) is #1 — poor first impression | Medium |
| "payments" | Zero migration signals across all 5 results | Medium |
| "auth" | authorizer tagline truncated mid-word ("Deployme...") | Low |
| "auth" | authlib tagline truncated mid-word ("JWS, JWE, JWK, JW...") | Low |
| "auth" | logto has emoji in tagline (🧑‍🚀) — can trip up agent text processing | Low |

### Root Cause Hypothesis
- Missing install_commands: generic/template repos get indexed but never had install data enriched
- Wrong ranking: "email" generic term matches library names literally, not semantic intent
- Resend missing from "email": slug is `resend` not `email-*`, so text match score is low

### Gotchas
- Official registry quickstart assumes TypeScript/npm, but we use PyPI — server.json already handles this with `registryType: pypi`
- Smithery blocks automated checks (403/429). Must verify listing manually in browser.
- mcp.run redirects to turbomcp.ai (enterprise gateway), not a public listing directory

---

## Post-FTS-Rebuild Search Audit (2026-04-04)

### Key Findings

**Root cause of "testing" misfire (PostHog #1):**
PostHog is BOTH in Analytics & Metrics AND Testing Tools category. The Testing Tools category
membership gives it the 180-point boost for "testing" query. Meanwhile vitest/jest are in
"Developer Tools" only → no boost → can't beat PostHog. Fix: remove PostHog/flagsmith/go-feature-flag
from Testing Tools; add vitest/jest/pypi-pytest to Testing Tools.

**Root cause of "email" misfire (Logto #1):**  
Logto's FTS-indexed description contains heavy "email" mentions (email auth, email verification).
Its bm25 rank for "email" is stronger than email-specific tools, even with the category boost
those tools receive. Harder to fix — needs description cleaning or category-mismatch penalty.

**Good queries (no action needed):** auth, analytics, database (top 3)

**Category data issues to flag to Backend:**
- PostHog: remove from Testing Tools
- flagsmith, go-feature-flag-1: remove from Testing Tools  
- vitest, jest: add to Testing Tools
- pypi-pytest: has NO categories at all — add to Testing Tools
- matomo: wrong category (SEO Tools → Analytics & Metrics)
- swetrix: in Monitoring & Uptime but is analytics

**Data quality issues for Backend:**
- killbill + kill-bill: duplicates (both approved)
- btcpay-server + btcpayserver: duplicates (both approved)
- 16/20 ORM tools have no install_command (-40pts each in scoring)
- email-marketing-bible: likely a prompt, not a dev tool — should be removed

**Production DB path:** `/data/indiestack.db` (NOT /app/data/)
**SSH inline python:** Use `-C 'python3 -c "..."'` with proper quoting


## 2026-04-04 — Added get_migration_data tool (v1.15.0)

**Task:** Cross-reference data-moat.md + mcp-roadmap.md vs current tool list, implement highest-value missing improvement.

**Decision:** `get_migration_data` — surfaces IndieStack's #1 data moat via MCP for the first time.

**Key finding:** Backend API `/api/migrations?package=X` already exists in `src/indiestack/routes/analyze.py` (line 1222). Returns `migrating_from` (departures) and `migrating_to` (adoptions). Live test: jest returns 3 departures, 6 adoptions.

**Pattern:** For new MCP tools that query existing backend routes, the workflow is:
1. Check routes/ for existing JSON API endpoint
2. Verify it returns data with `curl https://indiestack.ai/api/...`
3. Add tool to mcp_server.py after the closest thematic neighbor (market intelligence → after get_market_gaps)
4. Bump pyproject.toml AND server.json version together
5. DO NOT publish — leave for /publish-mcp

**Other roadmap items (blocked):**
- `get_trending_migrations` — no backend endpoint yet. Backend needs `/api/trending-migrations`.
- `get_session_stack` / `add_to_session_stack` — stack memory tools. Complex, v1.16.
- License/setup snippet in get_tool_details — needs backend DB columns.

**Files changed:** mcp_server.py, pyproject.toml, server.json (1.14.2 → 1.15.0)
