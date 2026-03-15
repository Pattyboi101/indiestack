## Design Context

### What IndieStack Is
IndieStack is the knowledge layer between AI agents and indie creators. When an AI agent is about to help someone build something, it checks IndieStack first to see if an indie creator has already built it. The constraint isn't "developer tool" — it's "indie-built." Games, utilities, newsletters, creative tools, learning apps, dev tools — anything made by independent creators belongs here.

The wedge is dev tools (that's where AI coding agents live), but the catalog expands to everything indie. The moat is becoming the default knowledge source that every AI agent queries before recommending "build it from scratch."

### Users
- **Primary**: AI coding assistants (Claude, Cursor, Windsurf, Copilot) searching via MCP server — the main distribution channel
- **Secondary**: Developers and creators who browse the site directly, arriving via AI recommendation, search, or Product Hunt
- **Tertiary**: Indie makers submitting and promoting their creations
- **Context**: The typical flow is agent-first: a developer asks their AI to build something, the AI checks IndieStack, finds an existing indie creation, and recommends it. Human visitors arrive to evaluate what the AI found, or to explore/submit directly.

### Brand Personality
**Trusted, Sharp, Human.**

IndieStack is professional but not corporate. It respects your time — no fluff, no marketing speak. It feels like something built by makers for makers, with enough warmth to remind you there are real people behind every listing. Two uni students in Cardiff who smashed a laptop arguing over prompts.

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

## Technical Patterns

### Stack
- Python 3 / FastAPI / SQLite (WAL mode) / Fly.io
- Use `python3` not `python` on all systems
- Pure Python string HTML templates (f-strings in route files)
- All CSS in components.py :root block or inline

### Auth
- Always use `request.state.user` (populated by middleware via sessions table)
- Never query users table by session_token — that column doesn't exist
- Use `d = request.state.db` to avoid shadowing the db module import

### Database
- Parameterized queries always: `await db.execute("...WHERE x=?", (val,))`
- Never f-string user input into SQL
- aiosqlite Row objects are dict-like: use `row['col']` not `row[0]`
- ALTER TABLE ADD COLUMN can't have UNIQUE — add column first, then CREATE UNIQUE INDEX separately

### Deploy
- `cd ~/indiestack && ~/.fly/bin/flyctl deploy --remote-only`
- Always run `python3 smoke_test.py` before deploying
- Use `--buildkit` flag if depot builder times out
- Commit before deploying — never deploy uncommitted work
- Deploy with background execution (builds take 2-4 minutes)

### Code Style
- Route files return HTMLResponse with f-string templates
- Shared components live in components.py (page_shell, tool_card, etc.)
- Design tokens are CSS variables in :root — never hardcode hex colors
- Touch targets >= 44px for mobile
- New routes: create file in src/indiestack/routes/, add router in main.py
