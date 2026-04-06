# Key Decisions — IndieStack

Rationale captured here to prevent re-litigating.

---

## MCP Server: No API Key Gating (2026-04-05)
**Decision:** Keep MCP server fully anonymous. No API keys, no accounts required.
**Rationale:** We tried gating before and it tanked MCP adoption. Developer tools succeed on frictionless adoption. Soft nudges after repeated use are acceptable; never degrade the anonymous experience.
**Source:** gotchas.md

---

## Maker Pro Pricing: $19/mo (2026-04-05)
**Decision:** Maker Pro subscription is $19/mo.
**Rationale:** Old planning docs had $49 — that was a draft figure. Canonical price is in stripe.md.
**Source:** stripe.md (authoritative), gotchas.md (anti-pattern to copy from old docs)

---

## Curation Scope: Dev Tools Only (2026-04-05)
**Decision:** IndieStack catalogs developer tools only — no games, newsletters, creative tools, or consumer apps.
**Rationale:** "Indie" is the curation quality filter (focused, lean, maintained, honest pricing), not the value prop. Scope creep dilutes the signal for AI agents.
**Source:** vision.md, /guidelines and /submit pages

---

## No Jinja2 / React / Vue — Python f-string Templates (ongoing)
**Decision:** Route files return HTMLResponse with Python f-string templates. No templating engines.
**Rationale:** Keeps the stack minimal and eliminates a dependency layer. Already established; don't change.
**Source:** stack.md

---

## FTS Index Rebuild Required After Data Changes (2026-04-05)
**Decision:** After fixing tool data on production (tags, categories, install commands), always rebuild FTS index.
**Rationale:** Search API serves stale cached results until rebuild; changes aren't reflected immediately.
**Commands:**
```sql
INSERT INTO tools_fts(tools_fts) VALUES('rebuild');
PRAGMA wal_checkpoint(TRUNCATE);
```
**Source:** gotchas.md

---

## Citation Analytics = Maker Pro Unlock (2026-04-05)
**Decision:** Maker Pro's core value prop is agent citation analytics (how often AI agents recommended your tool). Launch Maker Pro when this data is available and rich.
**Rationale:** Meeting consensus (2026-04-05-12). Developers and makers don't pay for badges — they pay for data that proves ROI.
**Source:** MCP Growth & Maker Pro meeting (2026-04-05)

---

## npm-* Tools Rejected (2026-04-05)
**Decision:** 46 empty/duplicate npm-* pending tools rejected in bulk.
**Rationale:** Auto-scraped stubs with no descriptions or meaningful metadata add noise. Only approve tools with real content.
**Source:** Fifth pass catalog cleanup

---

## New Categories Added (2026-04-05)
**Decision:** Added categories: `caching`, `mcp-servers`, `ai-standards` (pending), `frontend-frameworks`, `boilerplates`.
**Rationale:** These are high-demand query categories with real tool density. Frontend-frameworks especially needed (React, Vue, Svelte queries had no good home).
**Source:** Improvement cycle passes 6-12

---

## MCP Server Version: v1.15.1 (current as of 2026-04-06)
**Decision:** Keep version in sync between `pyproject.toml` and `mcp_server.py`.
**Rationale:** PyPI auto-detects the package version. Mismatches confuse users checking pip show indiestack.
**Source:** mcp.md

---

## Production SSH: File Upload Pattern Only (2026-04-05)
**Decision:** Never use `flyctl ssh console -C "python3 -c \"...\""` for production DB writes. Always upload a script file first.
**Rationale:** Nested quotes always fail with SyntaxError. File upload is reliable.
**Pattern:**
1. Write script to `/tmp/fix.py`
2. `flyctl ssh sftp put /tmp/fix.py /tmp/fix.py -a indiestack`
3. `flyctl ssh console -a indiestack -C "python3 /tmp/fix.py"`
**Source:** gotchas.md, backend/CLAUDE.md
