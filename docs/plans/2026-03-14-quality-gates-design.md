# Quality Gates for Vibecoded SaaS Submissions — Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Protect IndieStack's curation signal from low-effort vibecoded SaaS spam without killing legitimate indie SaaS submissions.

**Architecture:** Five-layer defence — submission guidelines (self-selection) → automated submission gates (hard blocks) → async enrichment signals (data gathering) → enhanced admin queue (fast decisions) → post-approval monitoring (self-healing). Each layer catches what the previous one misses.

**Key policy decision:** Free tier / programmatic access is a **soft signal** in admin review, not a hard gate. SaaS tools without a free tier get flagged but not auto-rejected.

---

## Layer 1: Submission Guidelines Page (P0)

Static page at `/guidelines` that sets expectations before submission. Linked prominently from `/submit` form, MCP `publish_tool()` error messages, and API docs.

**Content sections:**

### "What belongs on IndieStack"
- Independently built software — solo founders, small teams, bootstrapped projects
- Actively maintained — your tool should work when someone tries it
- Genuinely useful — solves a real problem for real people

### "What we look for"
- Custom domain (not *.vercel.app or *.netlify.app)
- Working product (not a landing page or waitlist)
- Documentation that an AI agent can parse (structured docs, API reference, or a solid README)
- For SaaS: a free tier, trial, or sandbox so AI agents can verify your tool works

### "What gets rejected"
- Default deployment URLs with no custom domain
- Dead links or tools that return errors
- AI-generated marketing copy with no substance
- Duplicate of a tool already in the catalog
- Paid-only SaaS with no programmatic access path

**Implementation:** Pure HTML page rendered from `components.py` or a new route. No database changes.

---

## Layer 2: Submission-Time Automated Gates (P0)

Run synchronously in `validate_submission_quality()`. Block submission if failed. Apply to all 3 surfaces (web form, REST API, MCP `publish_tool()`).

### Gate: Default Subdomain Filter

**Logic:** Extract hostname from submitted URL. Reject if it matches any of:
- `*.vercel.app`
- `*.netlify.app`
- `*.herokuapp.com`
- `*.fly.dev`
- `*.railway.app`
- `*.render.com`
- `*.surge.sh`

**Error message:** "IndieStack requires a custom domain. Default deployment URLs (e.g., *.vercel.app) are not accepted. See our submission guidelines."

**False positive risk:** Near zero. Established indie tools use custom domains. Pre-launch projects using deployment subdomains aren't ready for a curated directory anyway.

### Gate: URL Reachability Check

**Logic:** HTTP HEAD request to submitted URL with 10-second timeout. Reject if response status ≥ 400 or connection fails.

**Error message:** "We couldn't reach your URL ({url}). Please check that your tool is live and accessible, then try again."

**False positive risk:** Low. Temporary outages may cause rejection, but submitters can retry. Better than letting dead URLs enter the admin queue.

**Note:** This is an async check — use `httpx` with timeout. May need to be handled slightly differently in the synchronous validation flow (run in event loop or move to a quick pre-check step).

---

## Layer 3: Enrichment Signals (P1)

Run asynchronously after successful submission, before admin review. Background task triggered on new pending tool.

### New columns on `tools` table

```sql
domain_age_days INTEGER DEFAULT NULL
has_free_tier INTEGER DEFAULT NULL
social_mentions_count INTEGER DEFAULT NULL
rejection_reason TEXT DEFAULT NULL
```

### Signal: Domain Age

**Mechanism:** `python-whois` library. Query WHOIS for the submitted URL's domain. Extract `creation_date`. Calculate days since creation.

**Storage:** `domain_age_days` on tool record.

**Admin display:** Red if <30 days, yellow if <90 days, green if >90 days.

### Signal: Free Tier Detection

**Mechanism:** HTTP GET the tool's URL. Scan response body for keywords: "free", "free tier", "free plan", "open source", "try free", "no credit card", "get started free". Case-insensitive. Boolean result.

**Storage:** `has_free_tier` (1 = detected, 0 = not found, NULL = not checked).

**Admin display:** Yellow flag if 0 on SaaS tools. No flag for code/open-source tools.

### Signal: Social Proof (HackerNews)

**Mechanism:** Query HN Algolia API: `https://hn.algolia.com/api/v1/search?query={domain}&tags=story`. Count results.

**Storage:** `social_mentions_count` on tool record.

**Admin display:** Red if 0, green if >0.

### Signal: Immediate SaaS Health Check

**Mechanism:** Run existing `run_health_checks()` logic on newly submitted SaaS tools immediately, not just on the 24-hour cycle.

**Storage:** Uses existing `health_status` and `last_health_check` columns.

---

## Layer 4: Admin Queue Enhancement (P0)

### Updated Sorting Formula

```
score = (10 if github_url else 0)
      + (5 if len(description) > 200 else 3 if len(description) > 100 else 0)
      + (2 if tags else 0)
      + (1 if maker_name else 0)
      + (15 if domain_age_days > 90 else 8 if domain_age_days > 30 else -10)
      + (5 if has_free_tier == 1 else -5 if has_free_tier == 0 and source_type == 'saas' else 0)
      + (10 if social_mentions_count > 3 else 5 if social_mentions_count > 0 else 0)
      - (10 if health_status == 'dead' else 0)
```

### New Queue Columns

| Column | Values | Color Coding |
|--------|--------|-------------|
| Domain Age | "2 days" / "8 months" / "3 years" | Red <30d, yellow <90d, green >90d |
| Free Tier | "Detected" / "Not found" / "—" | Yellow if "Not found" on SaaS |
| Social Proof | "4 HN mentions" / "0 mentions" | Red if 0, green if >0 |
| Health | "Alive" / "Dead" / "Pending" | Red if dead |
| Source Type | "code" / "saas" badge | Context for review |

### Rejection Reasons

Dropdown on reject action with predefined reasons:
- "Default deployment URL — use a custom domain"
- "No free tier or trial access"
- "Tool appears unmaintained"
- "Insufficient documentation"
- "Duplicate of existing tool"
- "Other" (free text)

**Storage:** `rejection_reason TEXT` column on tools table.

---

## Layer 5: Post-Approval Monitoring (P1)

### SaaS Health Checks

Ensure `run_health_checks()` includes ALL approved tools regardless of `source_type`. Close the gap where 309 SaaS tools have `health_status='unknown'`.

### Outcome-Driven Demotion

New `health_status` value: `degraded`.

| Condition | Action |
|-----------|--------|
| ≥10 outcome signals AND success_rate < 20% | Set `health_status = 'degraded'`. Quality score × 0.3 multiplier. |
| `dead` for 30+ consecutive days | Set `status = 'archived'`. Removed from MCP search entirely. |
| Transitions from `dead` → `alive` | Reset `first_dead_at`. Restore normal quality_score. Self-healing. |

### Auto-Archive

Tools archived after 30 days of continuous `dead` status. This is a new automatic cleanup that prevents the catalog from accumulating dead links over time.

---

## What We're NOT Building (YAGNI)

- OpenAPI/Swagger linting — most SaaS tools don't have public API specs
- MCP schema validation of submitted tools — different from IndieStack's own MCP server
- NLP/AI-generated copy detection — no training data yet
- Endpoint fuzzing — over-engineered for current stage
- Auto-approve/auto-reject thresholds — everything goes through admin review
- Quarantine tier — adds complexity without enough agent traffic to make auto-promotion meaningful
- "Evaluation Prompt" requirement — high friction, low current value
- Reddit/Twitter social proof APIs — auth tokens, rate limits, HN covers 80% of signal

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/indiestack/db.py` | `validate_submission_quality()` — add subdomain filter, URL reachability. New enrichment functions. Updated `get_pending_tools()` scoring. New columns migration. |
| `src/indiestack/routes/submit.py` | Link to `/guidelines` on submit form. |
| `src/indiestack/routes/admin.py` | Display enrichment columns in queue. Rejection reason dropdown. |
| `src/indiestack/main.py` | `/guidelines` route. API submit endpoint updates. |
| `src/indiestack/mcp_server.py` | `publish_tool()` error messages reference guidelines. |
| `src/indiestack/components.py` | Guidelines page HTML. Admin queue column rendering. |

---

## Priority Summary

| Priority | What | Effort |
|----------|------|--------|
| P0 | Submission Guidelines page | ~1 hour |
| P0 | Subdomain filter + URL reachability gates | ~2-3 hours |
| P0 | Admin queue enhancement (columns, scoring, reject reasons) | ~3-4 hours |
| P1 | Enrichment signals (domain age, free tier, social proof, SaaS health) | ~4-5 hours |
| P1 | Post-approval monitoring (outcome demotion, auto-archive) | ~2-3 hours |
