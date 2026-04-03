# Strategy Memory

_You are a persistent agent. This file is your long-term knowledge base._
_Read this on startup. Update it after each task with what you learned._
_Focus on: file locations, patterns, gotchas, past decisions, domain knowledge._

---

## Session: 2026-03-30

### Key Files I Now Know
- `/tmp/maker_claim_emails.md` — generated outreach email drafts (check URLs match route params!)
- `src/indiestack/main.py:3809` — `/claim/magic` route, expects `?token=` param (NOT `?tool=`)
- `src/indiestack/main.py:1526` — `/api/tools/search` endpoint, returns JSON for MCP
- `src/indiestack/routes/dashboard.py` — maker dashboard with quality score, citations, referrals, badges
- `src/indiestack/email.py:939` — `maker_welcome_html()` — welcome email with 3 quick wins
- `src/indiestack/routes/pricing.py` — pricing page, header: "Free for developers. Data for tool makers."
- `src/indiestack/routes/migrations.py` — migration data display page
- `migration_paths` table — uses package names (not slugs), indexed on from_package and to_package

### Patterns Discovered
- Post-claim redirect: `/tool/{slug}?claimed=1` → success banner → link to dashboard
- Welcome email fires on both magic claim and regular claim paths
- Referral programme exists but is buried in dashboard, not surfaced in claim flow
- Migration data coverage is thin (~422 paths across 3,100+ tools) — most tools have none
- Search API results (main.py:1616-1648) originally had no migration signal — approved adding it

### Decisions Made This Session
1. **APPROVED** (with fix): Distribution prep tasks — but flagged 2/4 input files missing, changed scope from "review" to "write"
2. **APPROVED**: Pricing page review + MCP response quality audit — cheap, non-destructive prep for incoming traffic
3. **VETOED (by prior session)**: Duplicate code quality audit — $6 already spent on same scope within 30 minutes
4. **APPROVED**: Migration signal in search results — batch queries only (2 max), omit field when no data
5. **FLAGGED EMERGENCY**: Claim email URLs used `?tool=slug` but route expects `?token=` — would silently bounce all makers to homepage (later reported as fixed)
6. **RECOMMENDED RESTRAINT**: After heavy distribution push, recommended waiting for signal before more outreach

### Strategic Assessment: Current State
- 0 revenue, ~55 users, product technically solid
- Distribution is the bottleneck — now addressed with blog, registries, outreach
- Migration data is the key differentiator but was under-surfaced
- Maker funnel gap: no follow-up after Day 0 welcome email, referral buried
- The "uncomfortable truths": small MCP numbers aren't compelling to big tools (NextAuth gets thousands of installs daily, we showed them 5 recommendations), Reactive Resume may not fit dev-tools-only scope

### What I Look For (Calibration)
- Duplicate/near-duplicate tasks: check playbook timestamps and scope overlap
- Missing input files before dispatching review tasks
- URL/route parameter mismatches in generated content
- Whether "research" tasks are actually just narrative-building with no testable hypothesis
- Whether "improvement" tasks have diminishing returns vs. waiting for real user feedback
