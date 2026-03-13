---
phase: 01-ai-visibility-score
plan: 01
subsystem: ui, database
tags: [sqlite, percent-rank, dashboard, python-html]

# Dependency graph
requires: []
provides:
  - get_citation_percentile() DB function with PERCENT_RANK() window function
  - AI Visibility card component on maker dashboard
  - 30-day citation window (upgraded from 7-day)
affects: [04-milestone-rewards]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "PERCENT_RANK() window function for category-relative percentile ranking"
    - "Inline responsive CSS scoped with unique class (.ai-viz-grid)"

key-files:
  created: []
  modified:
    - src/indiestack/db.py
    - src/indiestack/routes/dashboard.py

key-decisions:
  - "Used PERCENT_RANK() partitioned by category_id for fair cross-category comparison"
  - "Return percentile=None (not 0) for 0-citation tools to distinguish no-data from bottom-rank"
  - "Duplicated query fetch rather than refactoring existing ai_intel_html block to avoid risk"

patterns-established:
  - "Edge case handling: None sentinel for missing data vs 0 for actual zero values"

requirements-completed: [AIVIZ-01, AIVIZ-02, AIVIZ-03, AIVIZ-04]

# Metrics
duration: 2min
completed: 2026-03-13
---

# Phase 1 Plan 1: AI Visibility Card Summary

**Maker dashboard AI Visibility card showing 30-day citation count, category percentile rank via PERCENT_RANK(), and top-5 discovery queries**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-13T12:20:11Z
- **Completed:** 2026-03-13T12:22:12Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added `get_citation_percentile()` function using SQLite PERCENT_RANK() window function partitioned by category
- Built cohesive AI Visibility card consolidating citation count, percentile rank, and top queries
- Upgraded stat grid from 7-day to 30-day citation window
- Graceful 0-citation handling: shows "No data yet" instead of misleading percentile

## Task Commits

Each task was committed atomically:

1. **Task 1: Add percentile DB function and update citation window to 30 days** - `be8a3f8` (feat)
2. **Task 2: Build AI Visibility card with citation count, top queries, and percentile** - `d53b5af` (feat)

## Files Created/Modified
- `src/indiestack/db.py` - Added get_citation_percentile() with PERCENT_RANK() window function
- `src/indiestack/routes/dashboard.py` - Added AI Visibility card, updated import, 30-day citation fetch, stat grid label

## Decisions Made
- Used PERCENT_RANK() partitioned by category_id so percentile reflects category peers, not global ranking
- Return percentile=None for 0-citation tools to cleanly distinguish "no data" from "bottom of category"
- Fetch top_5_queries separately in the new card block rather than refactoring the existing ai_intel_html fetch -- avoids touching working code

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- AI Visibility card is self-contained; existing AI Distribution Intelligence section preserved below
- Phase 4 (milestone rewards) can reference get_citation_percentile() for citation-based milestones

## Self-Check: PASSED

All files found, all commits verified.

---
*Phase: 01-ai-visibility-score*
*Completed: 2026-03-13*
