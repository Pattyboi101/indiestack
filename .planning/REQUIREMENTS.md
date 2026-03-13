# Requirements: IndieStack Growth Features

**Defined:** 2026-03-13
**Core Value:** Surface hidden data as actionable intelligence for makers and developers

## v1 Requirements

### AI Visibility

- [x] **AIVIZ-01**: Maker can see total AI agent citations for their tool (30-day count) on dashboard
- [x] **AIVIZ-02**: Maker can see top 5 search queries that triggered their tool in AI recommendations
- [x] **AIVIZ-03**: Maker can see their tool's citation percentile rank within its category
- [x] **AIVIZ-04**: AI Visibility card displays on the maker dashboard alongside existing analytics

### Compatibility

- [ ] **COMPAT-01**: Tool detail page shows "Confirmed Works With" section listing empirically-reported compatible tools
- [ ] **COMPAT-02**: User can report a new compatibility pairing via one-click "I use this with..." button on tool page
- [ ] **COMPAT-03**: Compatibility pair count is visible on each pairing (e.g., "47 makers confirmed")
- [ ] **COMPAT-04**: Explore page supports "compatible with [Tool X]" filter

### Stack Scan

- [ ] **SCAN-01**: User can paste a package.json or requirements.txt on /stack-scan page
- [ ] **SCAN-02**: System parses dependencies and fuzzy-matches against tool catalog
- [ ] **SCAN-03**: Report shows indie alternatives for each matched dependency
- [ ] **SCAN-04**: Report flags dependencies where upstream project is stale/inactive (using github_freshness)
- [ ] **SCAN-05**: Report has a shareable URL with unique slug
- [ ] **SCAN-06**: Report displays a vendor concentration risk score

### Ego Pings

- [ ] **EGO-01**: Daily cron detects citation milestones (10, 50, 100, 500 citations) for claimed tools
- [ ] **EGO-02**: Daily cron detects when a competitor in same category goes stale
- [ ] **EGO-03**: Daily cron detects view milestones (100, 500, 1000, 5000 views) for claimed tools
- [ ] **EGO-04**: Triggered milestones create notifications in existing notifications table
- [ ] **EGO-05**: Each milestone notification has a "Share" button linking to shareable SVG card
- [ ] **EGO-06**: Shareable SVG cards include IndieStack branding and tool metrics

## v2 Requirements

### AI Visibility

- **AIVIZ-05**: Maker can see which competing tools appear alongside theirs in AI recommendations
- **AIVIZ-06**: Maker can see AI visibility trends over time (weekly chart)
- **AIVIZ-07**: Public "AI Leaderboard" showing most-cited tools per category

### Compatibility

- **COMPAT-05**: Dedicated "Does X work with Y?" SEO pages for each compatibility pair
- **COMPAT-06**: Visual compatibility graph (network visualization)
- **COMPAT-07**: MCP server surfaces compatibility data in tool recommendations

### Stack Scan

- **SCAN-07**: Accept GitHub repo URL directly (fetch package files via API)
- **SCAN-08**: MCP server can generate stack scan reports mid-conversation
- **SCAN-09**: Compatibility scoring for each suggested alternative swap

### Ego Pings

- **EGO-07**: Email notifications for milestone triggers (in addition to in-app)
- **EGO-08**: "Year in Review" summary cards for makers
- **EGO-09**: Stack addition milestones (when N developers add tool to their stack)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time WebSocket updates | Unnecessary complexity for daily cron-based features |
| AI chatbot on homepage | MCP server handles AI discovery better |
| Paid tier for AI Visibility | Monetize later once value is proven |
| Compatibility voting/disputes | Keep it simple -- report pairs, show counts |
| Stack scan for Cargo.toml/go.mod | Start with JS + Python ecosystems only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AIVIZ-01 | Phase 1 | Complete |
| AIVIZ-02 | Phase 1 | Complete |
| AIVIZ-03 | Phase 1 | Complete |
| AIVIZ-04 | Phase 1 | Complete |
| COMPAT-01 | Phase 2 | Pending |
| COMPAT-02 | Phase 2 | Pending |
| COMPAT-03 | Phase 2 | Pending |
| COMPAT-04 | Phase 2 | Pending |
| SCAN-01 | Phase 3 | Pending |
| SCAN-02 | Phase 3 | Pending |
| SCAN-03 | Phase 3 | Pending |
| SCAN-04 | Phase 3 | Pending |
| SCAN-05 | Phase 3 | Pending |
| SCAN-06 | Phase 3 | Pending |
| EGO-01 | Phase 4 | Pending |
| EGO-02 | Phase 4 | Pending |
| EGO-03 | Phase 4 | Pending |
| EGO-04 | Phase 4 | Pending |
| EGO-05 | Phase 4 | Pending |
| EGO-06 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after Phase 1 completion*
