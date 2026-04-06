# IndieStack MCP Data Brief — for @dsp_ follow-up
*Prepared April 6, 2026. Send within the hour if DSP replies "show me."*

---

## What IndieStack is

An MCP server giving AI coding agents access to 7,500+ curated developer tools.
When a Claude Code or Cursor agent needs auth, payments, email, or a database —
it calls IndieStack before generating code from scratch.

- **PyPI package:** `uvx --from indiestack indiestack-mcp`
- **Registry:** `io.github.Pattyboi101/indiestack` (MCP Registry)
- **23 tools, 3 resources, 5 prompts**

---

## Usage numbers

| Metric | Value |
|---|---|
| PyPI installs | 10,000+ |
| Agent citations (all time) | 1,568 |
| Agent citations (last 7 days) | 1,235 |
| Unique tools ever cited | 571 of 7,500+ |
| Total MCP searches | 3,135 |
| Zero-result rate | 6.0% |

**The W13 spike:** 1,205 citations in a single week (week of March 23) — vs 65–161 in prior weeks. Something changed in agent behaviour. Likely a batch of new Claude Code users or a change in how agents invoke MCP servers. Worth understanding why.

---

## What agents are actually searching for

**Top queries (last 7 days):**

| Rank | Query | Count |
|---|---|---|
| 1 | auth | 216 |
| 2 | email | 160 |
| 3 | analytics | 139 |
| 4 | payments | 48 |
| 5 | email sending | 33 |
| 6 | stripe alternative | 23 |
| 7 | monitoring | 23 |
| 8 | database | 22 |
| 9 | feature flags | 17 |
| 10 | auth for nextjs | 16 |
| 11 | testing | 14 |
| 12 | logging | 14 |
| 13 | background jobs | 14 |
| 14 | self hosted auth | 13 |
| 15 | cron job scheduler nodejs | 12 |

**Pattern:** Auth is 2x more searched than email, 4.5x more than payments. Agents
are overwhelmingly trying to avoid writing authentication from scratch.
"Self hosted auth" (13 searches) and "auth for nextjs" (16) suggest agents are
doing framework-specific searches — they've moved beyond generic queries.

---

## Where the catalog has gaps (zero-result searches)

Filtering out bots/XSS probes, real gaps found:

- `logging nodejs` — searched multiple times, returns results for generic logging but not Node-specific
- `web analytics privacy-friendly` — Plausible/Fathom exist but query doesn't match
- `RAG vector database multi-source` — composite query agents can't decompose
- `SNMP` — network monitoring, legitimately not covered
- `rss scanning` — no RSS aggregator/monitor tools
- `social distribution` — agents looking for tools to post to multiple social platforms

**Implication:** Agents are starting to form complex multi-word queries ("RAG vector database multi-source", "cron job scheduler nodejs") that current search can't decompose. Query intent resolution is the next gap.

---

## Who's citing us

Top cited tools suggest agents are heavily in the analytics + auth + media space:

1. Simple Analytics (30)
2. Plausible Analytics (27)
3. Cloudinary (27)
4. Supabase (24)
5. Next Auth (23)
6. Lucia Auth (16)
7. Firecrawl MCP Server (19)
8. Playwright MCP Server (16)

**Interesting pattern:** MCP servers are appearing in the top cited tools
(Firecrawl MCP, Playwright MCP) — agents are using IndieStack to find other MCP
servers to compose with. Tool-of-tools usage we didn't anticipate.

---

## Agent clients

80 confirmed Claude Code sessions (`indiestack-mcp/1.11.2 (claude-code)`) in the
search logs. The majority of traffic is raw API calls (curl, Python-urllib,
Go-http-client) — likely agents invoking the API directly, not via the MCP
package. The MCP install number (10,000+ PyPI) is the more reliable signal.

---

## The interesting question

The W13 spike (1,205 in a week vs 65–161 prior) hasn't repeated — W14 is at 30
with 2 days left. What caused it? If it was a change in how Claude Code invokes
MCP tools, understanding that pattern would tell you a lot about agent adoption
curves. We don't know the answer — that's partly why sharing this data with the
MCP team seems useful.

---

*IndieStack is built by Patrick (Cardiff University) and Ed. Open to any
conversation about how this data fits into what the MCP team is tracking.*
