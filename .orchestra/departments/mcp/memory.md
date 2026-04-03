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

