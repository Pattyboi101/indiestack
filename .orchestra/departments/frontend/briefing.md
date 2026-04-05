# Briefing — 2026-04-05

## Task
SEO and copy improvements for the catalog pages.

**Task 1 — Category page meta descriptions:**
Check `/explore?category=frontend-frameworks`, `/explore?category=mcp-servers`, `/explore?category=caching` in the explore route. If these new categories have generic/missing meta descriptions, improve them. Check `src/indiestack/routes/explore.py` for where category meta descriptions are set.

**Task 2 — Tool count in landing copy:**
Run: `curl -s https://indiestack.ai/` and check if any visible copy still says "8,000+" or wrong tool counts. If so, find and fix in the route file.

**Task 3 — Frontend Frameworks category page:**
Check `https://indiestack.ai/explore?category=frontend-frameworks` renders correctly with the new tools (React, Tailwind, etc.). Report what you see.

## Constraints
- Read `src/indiestack/routes/explore.py` and `src/indiestack/routes/components.py` before editing
- All route files return HTMLResponse with Python f-strings — no Jinja2
- Run smoke tests after any changes: `python3 smoke_test.py`
- Commit changes with descriptive message (NO Co-Authored-By line)
