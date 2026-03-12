# Contrast Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace all hardcoded hex colors in public-facing route files with CSS variables so text is readable in both light and dark mode.

**Architecture:** Mechanical replacement of ~70 hardcoded hex color values across 13 files with existing CSS variables from the `:root` / `[data-theme="dark"]` token system. One new variable (`--warning-border`) needed. Parallel agents per file batch.

**Tech Stack:** Pure Python string HTML templates, CSS custom properties in `components.py`

---

## Reference: Color Mapping

### Status colors (badges, toasts, alerts)
| Hardcoded (light only) | Replace with |
|----------------------|--------------|
| `background:#DCFCE7;color:#166534` | `background:var(--success-bg);color:var(--success-text)` |
| `background:#ECFDF5;color:#065F46` | `background:var(--success-bg);color:var(--success-text)` |
| `background:#E8F5E9;color:#2E7D32` | `background:var(--success-bg);color:var(--success-text)` |
| `background:#FEE2E2;color:#991B1B` | `background:var(--error-bg);color:var(--error-text)` |
| `background:#FDF8EE;color:#92400E` | `background:var(--warning-bg);color:var(--warning-text)` |
| `background:#FEF3C7;color:#D97706` | `background:var(--warning-bg);color:var(--warning-text)` |
| `border:#A7F3D0` / `border:1px solid #A5D6A7` | `border-color:var(--success-border)` |
| `border:#FECACA` | `border-color:var(--error-border)` |

### Text colors
| Hardcoded | Replace with | Notes |
|-----------|-------------|-------|
| `color:#166534` / `color:#16a34a` | `color:var(--success-text)` | Green status text |
| `color:#2E7D32` | `color:var(--success-text)` | Legacy green |
| `color:#991B1B` / `color:#DC2626` | `color:var(--error-text)` | Red/error text |
| `color:#EF4444` | `color:var(--error-text)` | Bright red text |
| `color:#D97706` / `color:#92400E` / `color:#9A3412` | `color:var(--warning-text)` | Amber warning text |
| `color:#94A3B8` / `color:#9CA3AF` | `color:var(--ink-muted)` | Muted gray text |
| `color:#c0392b` | `color:var(--error-text)` | Legacy red |
| `color:#6B7280` | `color:var(--ink-muted)` | Gray text |
| `color:#3B82F6` | `color:var(--info-text)` | Blue text |
| `color:#fff` on colored bg | Keep `#fff` | White-on-color is intentional |
| `color:#0D1B2A` on accent buttons | Keep | Dark-on-cyan is intentional |
| `color:#1A2D4A` on accent buttons | Keep | Same — intentional contrast |

### Background colors on special sections
| Hardcoded | Context | Action |
|-----------|---------|--------|
| `background:linear-gradient(135deg,#1A2D4A,...)` | Dashboard hero | Keep — uses `#fff` text, intentional |
| `background:rgba(0,0,0,0.3)` | Code blocks | Keep — dark bg with light text |
| `background:rgba(59,130,246,0.15)` | API method badges | Replace with `background:var(--info-bg)` |

### Decorative / category-specific colors (what_is.py)
| Hardcoded | Action |
|-----------|--------|
| `color:#e06c75` (Games red) | Keep — decorative label on dark bg section |
| `color:#c678dd` (Creative purple) | Keep — decorative label on dark bg section |
| `color:#4CAF50` (Code badge) | Replace with `color:var(--success-text)` |
| `color:#61afef` (blue) | Replace with `color:var(--info-text)` |

---

## Task 0: Add `--warning-border` variable to components.py

**Files:**
- Modify: `src/indiestack/routes/components.py:86-91` (light `:root`) and `:112-129` (dark `[data-theme="dark"]`)

**Step 1:** Add `--warning-border: #FDE68A;` after `--warning-text` in `:root` block
**Step 2:** Add `--warning-border: #92400E;` after `--warning-text` in `[data-theme="dark"]` block
**Step 3:** Run `python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read())"`

---

## Task 1: Fix dashboard.py (22 instances — HIGH)

**Files:**
- Modify: `src/indiestack/routes/dashboard.py`

**Replacements:**
- `color:#94A3B8` → `color:var(--ink-muted)` (lines ~585, 591)
- `color:#92400E` → `color:var(--warning-text)` (line ~627, 884)
- `color:#991B1B` → `color:var(--error-text)` (line ~886)
- `background:#FDF8EE;color:#92400E` → `background:var(--warning-bg);color:var(--warning-text)` (line ~884)
- `background:#FEE2E2;color:#991B1B` → `background:var(--error-bg);color:var(--error-text)` (line ~886)
- `color:#9CA3AF` → `color:var(--ink-muted)` (line ~1619)
- `color:#EF4444` → `color:var(--error-text)` (line ~1687)
- `color:#E2E8F0` → `color:var(--ink-light)` (code blocks — lines ~296, 307)
- Keep: `color:#fff` on gradient backgrounds (lines ~351, 408, 410, 422, 424, 563, 1707, 1729)
- Keep: `background:linear-gradient(135deg,#1A2D4A,...)` (line ~422)

**Verify:** `python3 -c "import ast; ast.parse(open('src/indiestack/routes/dashboard.py').read())"`

---

## Task 2: Fix alternatives.py (8 instances — HIGH)

**Files:**
- Modify: `src/indiestack/routes/alternatives.py`

**Replacements:**
- Keep: `color:#fff` / `color:#FFFFFF` on dark gradient hero backgrounds — these are intentional
- Any `color:#94A3B8` or similar muted grays → `color:var(--ink-muted)`
- Review each instance in context — the hero section has a dark background so light text is correct

**Verify:** `python3 -c "import ast; ast.parse(open('src/indiestack/routes/alternatives.py').read())"`

---

## Task 3: Fix what_is.py (9 instances — HIGH)

**Files:**
- Modify: `src/indiestack/routes/what_is.py`

**Replacements:**
- `color:#4CAF50` → `color:var(--success-text)` (Code badge)
- Keep: `color:#e06c75`, `color:#c678dd` — decorative labels in a dark hero section
- Any other hardcoded text/background colors → appropriate CSS variable

**Verify:** `python3 -c "import ast; ast.parse(open('src/indiestack/routes/what_is.py').read())"`

---

## Task 4: Fix calculator.py (4 instances — MEDIUM)

**Files:**
- Modify: `src/indiestack/routes/calculator.py`

**Replacements:**
- `color:#94A3B8` → `color:var(--ink-muted)` (all 4 instances — labels, tool count, price suffix)

**Verify:** `python3 -c "import ast; ast.parse(open('src/indiestack/routes/calculator.py').read())"`

---

## Task 5: Fix pulse.py (4 instances — MEDIUM)

**Files:**
- Modify: `src/indiestack/routes/pulse.py`

**Replacements:**
- `color:#EF4444` → `color:var(--error-text)` (gap link)
- `color:#10B981` → `color:var(--success-text)` (recommend dot)
- `color:#00D4F5` → `color:var(--accent)` (search dot)
- `color:#EF4444` → `color:var(--error-text)` (gap dot in legend)

**Verify:** `python3 -c "import ast; ast.parse(open('src/indiestack/routes/pulse.py').read())"`

---

## Task 6: Fix maker.py (3 instances — MEDIUM)

**Files:**
- Modify: `src/indiestack/routes/maker.py`

**Replacements:**
- `color:#0D7377;background:#E0F7F7` (Solo Maker pill) → `color:var(--info-text);background:var(--info-bg)`
- `color:#7C3AED;background:#EDE9FE` (Small Team pill) → needs review, may need new variable or keep
- `color:#EA580C;background:#FFF7ED` (Active pill) → `color:var(--warning-text);background:var(--warning-bg)`

**Verify:** `python3 -c "import ast; ast.parse(open('src/indiestack/routes/maker.py').read())"`

---

## Task 7: Fix stacks.py (3 instances — MEDIUM)

**Files:**
- Modify: `src/indiestack/routes/stacks.py`

**Replacements:**
- Keep: `color:#fff` on gradient logo backgrounds — intentional
- Any muted grays → `color:var(--ink-muted)`

**Verify:** `python3 -c "import ast; ast.parse(open('src/indiestack/routes/stacks.py').read())"`

---

## Task 8: Fix remaining low-priority files

**Files:**
- `src/indiestack/routes/account.py` — `color:#c0392b` → `color:var(--error-text)` (2 instances)
- `src/indiestack/routes/api_docs.py` — `color:#3B82F6` → `color:var(--info-text)` (2 instances), `background:rgba(59,130,246,0.15)` → `background:var(--info-bg)`
- `src/indiestack/routes/explore.py` — 1 instance, review in context
- `src/indiestack/routes/tool.py` — 1 instance, review in context
- `src/indiestack/routes/admin.py` — edit toast: `background:#DCFCE7;color:#166534` → `background:var(--success-bg);color:var(--success-text)` (line ~1366)

**Verify:** Run syntax check on each file after editing

---

## Task 9: Final verification and deploy

**Step 1:** Run full smoke test suite: `python3 smoke_test.py`
**Step 2:** Verify 38/38 pass
**Step 3:** Deploy: `~/.fly/bin/flyctl deploy --remote-only`
**Step 4:** Spot-check key pages in both light and dark mode on live site

---

## Constraints
- Do NOT change colors that are intentionally mode-independent (e.g. white text on colored gradient backgrounds)
- Do NOT change embed.py (25 instances) — embeds render on third-party sites and need self-contained styling
- Run syntax check after each file edit (PostToolUse hook will catch this automatically)
- Run smoke tests before deploying

## Parallelisation Strategy
- Task 0 (components.py) runs first — adds the new variable other tasks depend on
- Tasks 1-3 (high priority) run as parallel agents
- Tasks 4-7 (medium priority) run as parallel agents
- Task 8 (low priority) runs as parallel agents
- Task 9 (verification + deploy) runs last
