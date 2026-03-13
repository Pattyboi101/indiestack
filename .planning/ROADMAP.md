# Roadmap: IndieStack Growth Features

## Overview

Four features that surface hidden data as growth flywheels for IndieStack.ai. Each phase delivers one complete, independently verifiable feature. Ordered by build complexity: AI Visibility Score (read-only dashboard card) first, then Compatibility Graph (tool page additions), then Stack Import (new page with parser), then Ego Pings (cron system with milestone detection). Phase 4 depends on Phase 1 (citation milestones require the citation counting logic from AI Visibility).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: AI Visibility Score** - Surface citation analytics on maker dashboard
- [ ] **Phase 2: Compatibility Graph** - Show "Works With" pairings on tool pages and explore filter
- [ ] **Phase 3: Stack Import + Vendor Risk** - Web UI for dependency analysis with shareable reports
- [ ] **Phase 4: Maker Ego Pings** - Automated milestone detection with shareable SVG cards

## Phase Details

### Phase 1: AI Visibility Score
**Goal**: Makers can see how often AI agents recommend their tool and which queries trigger those recommendations
**Depends on**: Nothing (first phase)
**Requirements**: AIVIZ-01, AIVIZ-02, AIVIZ-03, AIVIZ-04
**Success Criteria** (what must be TRUE):
  1. Maker sees a 30-day citation count for their tool on the dashboard
  2. Maker sees the top 5 search queries that led AI agents to recommend their tool
  3. Maker sees their tool's citation percentile rank relative to other tools in the same category
  4. AI Visibility card is visually integrated into the existing maker dashboard layout
**Plans**: 1 plan

Plans:
- [ ] 01-01-PLAN.md -- Add AI Visibility card with 30d citations, top-5 queries, and category percentile

### Phase 2: Compatibility Graph
**Goal**: Developers can discover which tools work together based on empirical compatibility reports from the community
**Depends on**: Nothing (independent of Phase 1)
**Requirements**: COMPAT-01, COMPAT-02, COMPAT-03, COMPAT-04
**Success Criteria** (what must be TRUE):
  1. Tool detail page displays a "Confirmed Works With" section listing compatible tools with confirmation counts
  2. Logged-in user can report a new compatibility pairing via "I use this with..." button on any tool page
  3. Explore page filters results to show only tools compatible with a selected tool
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Stack Import + Vendor Risk
**Goal**: Developers can paste a dependency file and get a report showing indie alternatives and vendor risk for every dependency
**Depends on**: Nothing (independent of Phases 1-2)
**Requirements**: SCAN-01, SCAN-02, SCAN-03, SCAN-04, SCAN-05, SCAN-06
**Success Criteria** (what must be TRUE):
  1. User pastes a package.json or requirements.txt on /stack-scan and sees matched dependencies from the catalog
  2. Each matched dependency shows indie alternatives available on IndieStack
  3. Dependencies with stale/inactive upstream projects are flagged with freshness status
  4. Report includes a vendor concentration risk score
  5. Report is accessible via a unique shareable URL
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Maker Ego Pings
**Goal**: Makers automatically receive milestone notifications with shareable branded cards they can post on social media
**Depends on**: Phase 1 (citation milestones require citation counting from AI Visibility)
**Requirements**: EGO-01, EGO-02, EGO-03, EGO-04, EGO-05, EGO-06
**Success Criteria** (what must be TRUE):
  1. Maker receives a dashboard notification when their tool hits a citation milestone (10, 50, 100, 500)
  2. Maker receives a notification when a competitor in the same category goes stale
  3. Maker receives a notification when their tool hits a view milestone (100, 500, 1000, 5000)
  4. Each milestone notification includes a "Share" button that links to a branded SVG card with tool metrics and IndieStack branding
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. AI Visibility Score | 0/1 | Planning complete | - |
| 2. Compatibility Graph | 0/0 | Not started | - |
| 3. Stack Import + Vendor Risk | 0/0 | Not started | - |
| 4. Maker Ego Pings | 0/0 | Not started | - |
