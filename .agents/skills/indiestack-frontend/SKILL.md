---
name: indiestack-frontend
description: Frontend UI polish and design tokens enforcing IndieStack styling
---

# IndieStack Frontend Design

Use this skill for ANY visual or UI work on IndieStack — new pages, redesigns, component updates, or polish passes. This enforces the exact aesthetic, tokens, and constraints so nothing drifts.

## Aesthetic Target

**Linear.app meets Stripe Docs.** Clean, precise, confident. Dark mode that looks intentional, not inverted. Warm personality without gratuitous decoration.

**References to study:** Linear (spatial hierarchy, dark mode confidence, typography weight), Stripe Docs (spacing, code blocks, information density), Vercel (motion, transitions, compositional balance).

**Anti-references (NEVER do these):**
- Purple gradients on white backgrounds
- Gradient blobs / mesh backgrounds on content pages
- Stock photos or placeholder illustrations
- Over-rounded everything (16px+ radius on small elements)
- Parallax, scroll-jacking, or animations that delay content
- Generic SaaS template layouts (three-column feature grids with emoji icons)

## Architecture Constraint

**Pure Python f-string HTML.** No React, no Jinja2, no build step. All pages are FastAPI route functions returning `HTMLResponse(page_shell(...))`. CSS lives in `components.py` design tokens or inline styles.

**File structure:**
- `src/indiestack/routes/components.py` — design tokens (`:root`), nav, footer, shared components
- `src/indiestack/routes/<page>.py` — page-specific routes with inline HTML
- New CSS classes go in `components.py` `design_tokens()` function
- Reusable components go in `components.py` as Python functions

## Design Tokens (Enforced)

### Colors — USE THESE EXACT VARIABLES
```css
/* Primary */             --terracotta: #1A2D4A;     /* Navy — legacy name, DO NOT rename */
/* Primary light */       --terracotta-light: #2B4A6E;
/* Primary dark */        --terracotta-dark: #0F1D30;
/* Accent */              --accent / --slate: #00D4F5; /* Cyan */
/* Highlight */           --gold: #E2B764;
/* Surfaces */            --cream: #F7F9FC;  --cream-dark: #EDF1F7;  --card-bg: white;
/* Text */                --ink: #1A1A2E;  --ink-light: #475569;  --ink-muted: #64748B;
/* Border */              --border: #E2E8F0;
```

**Rules:**
- NEVER use hardcoded hex colors — always `var(--token-name)`
- NEVER use `rgba()` with magic numbers — define as a token if needed
- Accent cyan (`--accent`) for interactive elements and emphasis only — not backgrounds
- Gold for verified/premium indicators only
- Navy (`--terracotta`) for primary actions and strong emphasis

### Typography
```css
--font-display: 'DM Serif Display', serif;   /* Headings ONLY */
--font-body: 'DM Sans', sans-serif;           /* Everything else */
--font-mono: 'JetBrains Mono', monospace;     /* Code, tags, technical */
```

**Hierarchy (use these exact sizes):**
| Level | Size | Weight | Font | Use |
|-------|------|--------|------|-----|
| Page title | `clamp(28px, 4vw, 40px)` | 400 | Display | One per page |
| Section heading | `22px` | 400 | Display | Section breaks |
| Card title | `17px` | 400 | Display | Card headers |
| Body | `15px` | 400 | Body | Paragraphs, descriptions |
| Label | `14px` | 600 | Body | Form labels, nav items |
| Small | `13px` | 500 | Body | Metadata, timestamps |
| Micro | `12px` | 600 | Mono | Tags, badges, code |

**Rules:**
- DM Serif Display is NEVER bold (it's a display face — weight 400 only)
- Line-height: 1.2 for headings, 1.6 for body, 1.4 for labels
- Letter-spacing: `0.5px` on uppercase labels, `0` elsewhere

### Spacing — 8px Base Grid
**ONLY use these values:** `4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80px`

| Token | Value | Use |
|-------|-------|-----|
| `xs` | `4px` | Badge padding, icon gaps |
| `sm` | `8px` | Tight groupings, inline gaps |
| `md` | `16px` | Standard element spacing |
| `lg` | `24px` | Card padding, section gaps |
| `xl` | `32px` | Between sections |
| `2xl` | `48px` | Major section breaks |
| `3xl` | `64px` | Page section padding |
| `4xl` | `80px` | Hero/CTA vertical padding |

**NEVER use:** `10px`, `15px`, `18px`, `22px`, `28px`, `36px`, `50px`, `60px` or any value not on the scale.

### Elevation — Layered Shadows
```css
/* Light mode */
--shadow-sm: 0 1px 3px rgba(26,45,74,0.06);
--shadow-md: 0 4px 12px rgba(26,45,74,0.08);
--shadow-lg: 0 12px 40px rgba(26,45,74,0.10);

/* Use shadow layering for depth */
/* Resting card:    shadow-sm */
/* Hover card:      shadow-md + translateY(-2px) */
/* Floating:        shadow-lg */
/* Modal/dropdown:  shadow-lg + border */
```

**Rules:**
- Cards at rest: `box-shadow: var(--shadow-sm)` with `border: 1px solid var(--border)`
- Cards on hover: `box-shadow: var(--shadow-md); transform: translateY(-2px)` — NOT `-3px` (too jumpy)
- Dropdowns/modals: `var(--shadow-lg)` with border
- NEVER use `box-shadow: none` on interactive cards

### Radius
- Cards, modals: `12px` (`--radius`)
- Inputs, dropdowns: `8px` (`--radius-sm`)
- Buttons, pills, badges: `999px` (full round)
- NEVER use `4px`, `6px`, or `16px` radius

### Transitions
```css
/* Standard */   transition: all 0.15s ease;
/* Emphasis */   transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
/* Page enter */  animation: fadeUp 0.4s ease-out;
```

**Rules:**
- Every interactive element MUST have a transition
- Hover scale: `transform: scale(1.02)` max — never `1.05`+
- Active/pressed: `transform: scale(0.98)` for tactile feedback
- Stagger animations with `animation-delay` in 50ms increments

## Component Patterns

### Cards
```python
f'''<div class="card" style="padding:24px;">
    <div style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:8px;">{title}</div>
    <div style="font-size:13px;color:var(--ink-muted);line-height:1.6;">{description}</div>
</div>'''
```

### Buttons
Always use `.btn` class. Never inline-style a button from scratch.
```python
f'<a href="{url}" class="btn btn-primary">Label</a>'
f'<button class="btn btn-secondary">Label</button>'
```

### Pills / Filter Buttons
Use the `.pill-filter` class (add to components.py if missing):
```css
.pill-filter {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 8px 16px; border-radius: 999px;
    font-size: 13px; font-weight: 600;
    border: 1px solid var(--border);
    background: var(--card-bg); color: var(--ink-light);
    cursor: pointer; transition: all 0.15s ease;
    min-height: 36px;
}
.pill-filter:hover { border-color: var(--ink-muted); color: var(--ink); }
.pill-filter.active { background: var(--terracotta); color: white; border-color: var(--terracotta); }
```

### Section Layout
```python
f'''<section style="padding:64px 24px;">
    <div class="container" style="max-width:700px;">
        <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:24px;">
            Section Title
        </h2>
        <!-- content -->
    </div>
</section>'''
```

### Badges
Always use `.badge` class with variant: `.badge-success`, `.badge-info`, `.badge-warning`, `.badge-gold`, `.badge-muted`.

## Modern Touches to Apply

1. **Layered borders** — Use `border-left: 3px solid var(--accent)` for emphasis, not just uniform 1px borders
2. **Subtle gradients** — `background: linear-gradient(180deg, var(--cream) 0%, var(--card-bg) 100%)` for section transitions
3. **Backdrop blur** — `backdrop-filter: blur(12px); background: rgba(247,249,252,0.85)` on nav (light) / `rgba(15,20,32,0.85)` (dark)
4. **Custom selects** — Replace `<select>` with styled `<details>` dropdowns
5. **Keyboard hints** — Show `/` shortcut on search, `Esc` on modals
6. **Skeleton loading** — For async content, use `background: linear-gradient(90deg, var(--cream-dark) 25%, var(--cream) 50%, var(--cream-dark) 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite;`
7. **Focus rings** — `outline: 2px solid var(--accent); outline-offset: 2px;` on all focusable elements
8. **Scroll-triggered reveals** — `.reveal` class with IntersectionObserver (already in landing.py, extend to all pages)

## Dark Mode Rules

- Landing page: dark by default (forced via script)
- All other pages: respect user preference
- NEVER hardcode colors — always use `var(--token)`
- Test both modes for every change
- Dark mode nav: `backdrop-filter: blur(12px); background: rgba(15,20,32,0.85);`

## Screenshot Feedback Protocol

When doing visual work:
1. Make the change
2. User takes a screenshot and pastes it
3. Compare against Linear/Stripe reference aesthetic
4. Identify: spacing inconsistencies, color misuse, typography hierarchy breaks, missing hover states
5. Iterate until it feels "expensive"

## Checklist — Before Finishing Any Visual Change

- [ ] All colors use CSS variables (no hardcoded hex/rgba)
- [ ] All spacing values are on the 8px grid scale
- [ ] Typography follows the hierarchy table exactly
- [ ] Interactive elements have hover + focus + active states
- [ ] Dark mode tested (both themes look intentional)
- [ ] Mobile responsive at 768px, 600px, 480px breakpoints
- [ ] Touch targets >= 44px
- [ ] No browser-default form elements visible (style or replace)
- [ ] Transitions on all state changes (0.15s ease minimum)
- [ ] `python3 -c "import ast; ast.parse(open('file.py').read())"` passes
