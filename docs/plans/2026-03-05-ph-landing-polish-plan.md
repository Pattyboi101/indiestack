# PH Landing Page Polish — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix credibility gaps, stale data, and conversion confusion on the landing page before Product Hunt launch.

**Architecture:** All changes in `landing.py` (string edits) plus one DB update to swap showcase tools. No new routes, no structural changes.

**Tech Stack:** Python/FastAPI, aiosqlite, Fly.io SSH for DB update

**Design doc:** `docs/plans/2026-03-05-ph-landing-polish-design.md`

---

## Task 1: Fix Stale Version and Hardcoded Numbers

**Files:**
- Modify: `src/indiestack/routes/landing.py:121` (banner version)
- Modify: `src/indiestack/routes/landing.py:260` (hardcoded 900+)

**Step 1: Fix banner version**

In `landing.py` line 121, change:
```python
'        &#9889; MCP Server v0.5.0 &mdash; ' + str(tool_count) + ' indie tools. '
```
to:
```python
'        &#9889; MCP Server v0.7.0 &mdash; ' + str(tool_count) + ' indie tools. '
```

**Step 2: Fix hardcoded 900+**

In `landing.py` line 260, change:
```python
                IndieStack&rsquo;s MCP server gives your AI access to 900+ indie tools &mdash; so it finds existing solutions instead of coding from scratch.
```
to:
```python
                IndieStack&rsquo;s MCP server gives your AI access to {tool_count}+ indie tools &mdash; so it finds existing solutions instead of coding from scratch.
```

Note: This line is inside an f-string (`mcp_walkthrough = f"""...`), so `{tool_count}` will interpolate correctly.

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read())"`
Expected: No output

---

## Task 2: Simplify Stats Bar

**Files:**
- Modify: `src/indiestack/routes/landing.py:220-229` (stats pills)

**Step 1: Replace the stats pills block**

Change lines 220-229 from:
```python
        # Stats pills
        f'    <div style="display:inline-flex;flex-wrap:wrap;gap:8px 16px;justify-content:center;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);'
        f'                border-radius:var(--radius-sm);padding:12px 24px;font-size:14px;color:var(--ink-light);'
        f'                backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);">'
        f'        <span>{tool_count} tools</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span>{maker_count} makers</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span style="color:var(--accent);">{ai_recs:,}+ AI recommendations &amp; counting</span>'
        f'    </div>'
```

to:
```python
        # Stats pills
        f'    <div style="display:inline-flex;flex-wrap:wrap;gap:8px 16px;justify-content:center;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);'
        f'                border-radius:var(--radius-sm);padding:12px 24px;font-size:14px;color:var(--ink-light);'
        f'                backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);">'
        f'        <span>{tool_count}+ tools</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span style="color:var(--accent);">{ai_recs:,}+ AI recommendations &amp; counting</span>'
        f'    </div>'
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read())"`

---

## Task 3: Remove Maker CTA from Hero

**Files:**
- Modify: `src/indiestack/routes/landing.py:241-244` (hero maker button)

**Step 1: Remove the "Add Your Tool" button and subtext from the hero**

Delete these lines (241-244):
```python
        f'    <div style="margin-top:16px;">'
        f'        <a href="/submit" class="btn btn-slate" style="padding:12px 24px;font-size:14px;">Add Your Tool &rarr;</a>'
        f'        <p style="font-size:12px;color:var(--ink-muted);margin-top:8px;">Free to list. AI agents start recommending your tool immediately.</p>'
        f'    </div>'
```

Replace with empty string (just remove the 4 lines, keep the closing `'</section>'` on the next line).

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read())"`

---

## Task 4: Add Video Placeholder Section

**Files:**
- Modify: `src/indiestack/routes/landing.py` — add new section variable between `hero` and `mcp_walkthrough` (around line 247)

**Step 1: Add video section**

After the `hero` section definition (after line 246 `')`) and before the `# ── MCP Walkthrough` comment, add:

```python
    # ── Video Section ──────────────────────────────────────────────────
    _video_url = os.environ.get("DEMO_VIDEO_URL", "")
    if _video_url:
        video_section = f"""
        <section style="padding:48px 24px 0;background:var(--cream);">
            <div class="container" style="max-width:720px;text-align:center;">
                <h2 style="font-family:var(--font-display);font-size:clamp(22px,3vw,28px);margin-bottom:8px;color:var(--ink);">
                    See it in action
                </h2>
                <p style="color:var(--ink-muted);font-size:16px;margin-bottom:24px;">
                    Watch how your AI finds indie tools instead of writing code from scratch.
                </p>
                <div style="position:relative;padding-bottom:56.25%;height:0;border-radius:var(--radius);overflow:hidden;
                            box-shadow:var(--shadow-floating);">
                    <iframe src="{_video_url}" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;"
                            allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>
                </div>
            </div>
        </section>
        """
    else:
        video_section = """
        <section style="padding:48px 24px 0;background:var(--cream);">
            <div class="container" style="max-width:720px;text-align:center;">
                <h2 style="font-family:var(--font-display);font-size:clamp(22px,3vw,28px);margin-bottom:8px;color:var(--ink);">
                    See it in action
                </h2>
                <p style="color:var(--ink-muted);font-size:16px;margin-bottom:24px;">
                    Watch how your AI finds indie tools instead of writing code from scratch.
                </p>
                <a href="#mcp-install" style="display:block;max-width:720px;margin:0 auto;aspect-ratio:16/9;background:var(--ink);
                          border-radius:var(--radius);position:relative;text-decoration:none;
                          box-shadow:var(--shadow-floating);overflow:hidden;">
                    <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                        <div style="width:64px;height:64px;border-radius:50%;background:var(--accent);display:flex;
                                    align-items:center;justify-content:center;margin-bottom:12px;">
                            <span style="color:white;font-size:24px;margin-left:4px;">&#9654;</span>
                        </div>
                        <span style="color:var(--ink-light);font-size:14px;">Demo coming soon</span>
                    </div>
                </a>
            </div>
        </section>
        """
```

**Step 2: Add `video_section` to the page assembly**

Find the assembly section (around line 478+) where `_reveal()` calls chain the sections. Add `video_section` between `hero` and `mcp_walkthrough`:

```python
    + _reveal(video_section)
    + _reveal(mcp_walkthrough)
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read())"`

---

## Task 5: Swap Showcase Tools in Database

**Step 1: Clear old landing_position values**

Via Fly SSH:
```bash
FLY_ACCESS_TOKEN=... flyctl ssh console -a indiestack -C "python3 -c \"
import sqlite3
db = sqlite3.connect('/data/indiestack.db')
db.execute('UPDATE tools SET landing_position = NULL WHERE landing_position IS NOT NULL')
db.commit()
print('Cleared all landing_position values')
\""
```

**Step 2: Set new indie showcase tools**

```bash
FLY_ACCESS_TOKEN=... flyctl ssh console -a indiestack -C "python3 -c \"
import sqlite3
db = sqlite3.connect('/data/indiestack.db')
# 6 genuinely indie tools, diverse categories
showcase = [
    (1, 46),   # Plausible Analytics — Analytics (bootstrapped, privacy-first)
    (2, 177),  # Hanko — Auth (open-source passkeys)
    (3, 132),  # Coolify — DevTools (self-hosted Heroku)
    (4, 58),   # Typefully — Social Media (bootstrapped)
    (5, 50),   # Invoice Ninja — Invoicing (open-source)
    (6, 252),  # Aptabase — Analytics/Mobile (open-source)
]
for pos, tool_id in showcase:
    db.execute('UPDATE tools SET landing_position = ? WHERE id = ?', (pos, tool_id))
db.commit()
print('Set 6 indie showcase tools')
\""
```

**Step 3: Verify**

Check the landing page loads with new tools visible.

---

## Task 6: Smoke Test and Deploy

**Step 1: Run smoke test**

Run: `python3 smoke_test.py`
Expected: All 38 tests pass

**Step 2: Deploy**

Run: `FLY_ACCESS_TOKEN=$(grep access_token ~/.fly/config.yml | awk '{print $2}') ~/.fly/bin/flyctl deploy --remote-only`

**Step 3: Verify landing page**

Check https://indiestack.fly.dev/ — confirm:
- Banner says v0.7.0
- Stats bar shows tools + AI recs (no maker count)
- No "Add Your Tool" in hero section
- Video placeholder section visible
- 6 indie tools in Popular section (Plausible, Hanko, Coolify, Typefully, Invoice Ninja, Aptabase)

---

## Execution Summary

| Task | What | Independent? |
|------|------|-------------|
| 1 | Fix version + hardcoded numbers | Yes |
| 2 | Simplify stats bar | Yes |
| 3 | Remove hero maker CTA | Yes |
| 4 | Add video placeholder | Yes |
| 5 | Swap showcase tools (DB) | Yes |
| 6 | Smoke test + deploy | Needs all |

**All tasks 1-5 are independent** and modify different sections of landing.py. Can be done by a single agent in sequence (small file, predictable edits) or tasks 1-4 by one agent and task 5 by another in parallel.
