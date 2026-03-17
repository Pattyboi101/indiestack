---
paths:
  - "src/indiestack/routes/**/*.py"
  - "src/indiestack/**/components.py"
---

# IndieStack — Design System

## Aesthetic
Linear.app + Stripe Docs — clean, precise, confident. Dark mode that looks intentional.

## Brand Personality
Trusted, Sharp, Human. Professional but not corporate.

## Colors
- Navy `#1A2D4A` (primary)
- Cyan `#00D4F5` (accent)
- Gold `#E2B764` (highlights)

## Typography
- DM Serif Display (headings)
- DM Sans (body)
- JetBrains Mono (code/tags)

## Spacing & Layout
- Shadows: 3-tier system (`--shadow-sm`/`md`/`lg`)
- Radius: 12px cards/buttons, 8px inputs, 999px pills/badges
- Spacing: 8px base (8, 16, 20, 24, 32, 48px scale)
- Breakpoints: 768px (mobile nav), 900px (3-to-2 col), 600px (2-to-1 col)

## Implementation
- Pure Python f-string HTML templates. NO Jinja2, React, Vue, or templating engines.
- All CSS in components.py `:root` block or inline. No external stylesheets.
- Sanitize user data with `html.escape()` before injecting into f-strings.
- `category_icon(slug, size)` from `category_icons.py` for inline SVG category icons.
- `pixel_icon_svg()` in components.py for 7x7 pixel art avatars.
- Google favicons on tool cards (pixel icons take priority if set).

## Modes
- Dark mode default on landing page, user-selectable elsewhere.

## Anti-References
Gradient blobs, stock photos, parallax, enterprise bloat, over-rounded elements.

## Locked
Landing page structure is locked — visual polish only, no structural changes.
