---
phase: 2
slug: compatibility-graph
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | smoke_test.py (custom urllib-based, no pytest) |
| **Config file** | smoke_test.py at project root |
| **Quick run command** | `py smoke_test.py http://localhost:8000` |
| **Full suite command** | `py smoke_test.py http://localhost:8000` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `py smoke_test.py http://localhost:8000`
- **After every plan wave:** Run `py smoke_test.py http://localhost:8000`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | COMPAT-01 | smoke | GET /tool/supabase contains "Confirmed Works With" | Needs addition | ⬜ pending |
| 02-01-02 | 01 | 1 | COMPAT-02 | smoke | POST /tool/supabase/compatible returns 401 (no auth) | Needs addition | ⬜ pending |
| 02-01-03 | 01 | 1 | COMPAT-03 | smoke | "confirmed" text in tool page HTML | Needs addition | ⬜ pending |
| 02-02-01 | 02 | 1 | COMPAT-04 | smoke | GET /explore?compatible_with=supabase returns 200 | Needs addition | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Add smoke test entries to `TESTS` list in smoke_test.py for COMPAT-01 through COMPAT-04
- [ ] Add content check for "Confirmed Works With" substring on tool page

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| "I use this with..." button visible for logged-in users | COMPAT-02 | Requires auth session | Log in, navigate to tool page, verify button appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
