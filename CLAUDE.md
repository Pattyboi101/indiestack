## Design Context

### Users
- **Primary**: Developers building SaaS products who need to discover indie tools before writing code from scratch
- **Secondary**: AI coding assistants (Claude, Cursor, Windsurf) searching via MCP server
- **Tertiary**: Indie SaaS makers submitting and promoting their tools
- **Context**: Developers are mid-flow, building something. They arrive via AI recommendation, search, or direct browse. They want to evaluate tools quickly and move on.

### Brand Personality
**Trusted, Sharp, Human.**

IndieStack is professional but not corporate. It respects your time — no fluff, no marketing speak. It feels like a tool built by developers for developers, with enough warmth to remind you there are real people behind it. Two uni students in Cardiff who smashed a laptop arguing over prompts.

### Aesthetic Direction
- **Visual tone**: Linear.app-inspired — clean, precise, intentional. Every element earns its place.
- **Not minimalist for minimalism's sake** — has personality and warmth, but nothing gratuitous.
- **References**: Linear (precision, dark mode confidence, typography), Stripe Docs (spacing, code blocks)
- **Anti-references**: Generic SaaS templates (gradient blobs, stock photos), enterprise/corporate (Salesforce bloat), over-designed (parallax, excessive animations, style over substance)
- **Theme**: Dark mode default on landing, user-selectable elsewhere. Both modes must look intentional.

### Design Principles

1. **Earn every pixel.** No decorative elements that don't serve a purpose. If a gradient, shadow, or animation doesn't help the user understand or navigate, remove it.

2. **Consistent rhythm.** Spacing, typography, and color should follow the token system. No magic numbers. 8px base unit, deliberate hierarchy.

3. **Confidence over cleverness.** Bold typography choices, strong contrast, decisive layout. Don't hedge with soft grays and rounded everything — commit to the design.

4. **Warm precision.** Linear's precision + indie personality. The UI should feel crafted, not generated. Small details (hover states, transitions, copy) should feel human.

5. **Function preserves form.** Never sacrifice usability for aesthetics. Interactive elements (search widget, upvote buttons, nav) must remain fully functional through any visual changes.

### Design Tokens (Reference)
- **Colors**: Navy `#1A2D4A` (primary), Cyan `#00D4F5` (accent), Gold `#E2B764` (highlights), Terracotta naming is legacy — these are navy-based
- **Fonts**: DM Serif Display (headings), DM Sans (body), JetBrains Mono (code)
- **Shadows**: 3-tier system (sm/md/lg), subtle in light mode, deeper in dark
- **Radius**: 12px cards/buttons, 8px inputs, 999px pills/badges
- **Spacing**: 8px base (8, 16, 20, 24, 32, 48px scale)
- **Breakpoints**: 768px (mobile nav), 900px (3→2 col), 600px (2→1 col)

### Constraints
- Pure Python string HTML templates (f-strings). No Jinja2, no React, no build step.
- All CSS lives in `components.py` `:root` block or inline. No external stylesheets.
- The landing page structure (hero → MCP walkthrough → search widget → trending → categories → maker CTA) is locked. Visual polish only, no structural changes.
