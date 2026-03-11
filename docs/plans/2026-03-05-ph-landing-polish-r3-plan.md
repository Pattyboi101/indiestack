# PH Landing Page Polish Round 3 — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the landing page's value prop visceral with a build-vs-buy terminal mockup and a search widget that demos itself via clickable suggestion pills.

**Architecture:** Both changes are in `landing.py`. Task 1 adds a new `build_vs_buy` section variable and inserts it into page assembly. Task 2 modifies the existing `search_widget` variable (heading, subtext, adds pill HTML + JS click handlers). No backend changes.

**Tech Stack:** Python/FastAPI, inline HTML/CSS/JS

**Design doc:** `docs/plans/2026-03-05-ph-landing-polish-r3-design.md`

---

## Task 1: Add Build vs Buy Terminal Mockup

**Files:**
- Modify: `src/indiestack/routes/landing.py` — add new section variable (after line 360, before the search widget comment), update page assembly (line 498)

**Step 1: Add the build_vs_buy section**

Insert this new section after the MCP walkthrough closing `"""` (line 360) and before the `# ── "What are you building?"` comment (line 362):

```python
    # ── Build vs Buy ──────────────────────────────────────────────────
    build_vs_buy = """
    <section style="padding:48px 24px;">
        <div class="container" style="max-width:720px;">
            <h2 style="font-family:var(--font-display);font-size:clamp(22px,3vw,28px);text-align:center;margin-bottom:8px;color:var(--ink);">
                What happens without IndieStack
            </h2>
            <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:24px;">
                Your AI doesn&rsquo;t know indie tools exist. So it builds from scratch.
            </p>
            <div style="background:var(--ink);border:1px solid rgba(255,255,255,0.1);border-radius:var(--radius);overflow:hidden;
                        box-shadow:var(--shadow-lg);font-family:var(--font-mono);font-size:14px;line-height:1.7;">
                <!-- Terminal title bar -->
                <div style="display:flex;align-items:center;gap:6px;padding:12px 16px;background:rgba(0,0,0,0.3);border-bottom:1px solid rgba(255,255,255,0.06);">
                    <span style="width:10px;height:10px;border-radius:50%;background:#FF5F56;"></span>
                    <span style="width:10px;height:10px;border-radius:50%;background:#FFBD2E;"></span>
                    <span style="width:10px;height:10px;border-radius:50%;background:#27C93F;"></span>
                    <span style="margin-left:8px;font-size:12px;color:var(--ink-muted);">AI Coding Assistant</span>
                </div>

                <!-- Without IndieStack -->
                <div style="padding:20px 24px;border-bottom:1px solid rgba(255,255,255,0.06);">
                    <div style="font-size:11px;font-weight:600;color:#FF5F56;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">Without IndieStack</div>
                    <div style="color:var(--ink-light);">
                        <div><span style="color:var(--accent);">&gt;</span> <span style="color:#E2B764;">Build me a login system with OAuth support</span></div>
                        <div style="margin-top:8px;color:var(--ink-muted);">
                            <div>&#9999;&#65039; Generating auth module...</div>
                            <div style="padding-left:16px;">- Setting up session management...</div>
                            <div style="padding-left:16px;">- Implementing password hashing with bcrypt...</div>
                            <div style="padding-left:16px;">- Adding Google OAuth flow...</div>
                            <div style="padding-left:16px;">- Writing token refresh logic...</div>
                        </div>
                        <div style="margin-top:12px;display:flex;flex-wrap:wrap;gap:8px 24px;">
                            <span style="color:#FF5F56;">&#128196; 847 lines across 6 files</span>
                            <span style="color:#FF5F56;">&#9201; ~52,000 tokens</span>
                        </div>
                    </div>
                </div>

                <!-- With IndieStack -->
                <div style="padding:20px 24px;">
                    <div style="font-size:11px;font-weight:600;color:#27C93F;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">With IndieStack</div>
                    <div style="color:var(--ink-light);">
                        <div><span style="color:var(--accent);">&gt;</span> <span style="color:#E2B764;">Build me a login system with OAuth support</span></div>
                        <div style="margin-top:8px;">
                            <div style="color:var(--accent);">&#128269; Searching IndieStack...</div>
                            <div style="color:#27C93F;">&#9989; Found: Hanko &mdash; Passkey-first auth, open source</div>
                            <div style="padding-left:16px;color:var(--ink-muted);">One integration. Maintained by security experts.</div>
                            <div style="padding-left:16px;color:var(--ink-muted);">&rarr; hanko.io</div>
                        </div>
                        <div style="margin-top:12px;">
                            <span style="color:#27C93F;">&#9201; ~200 tokens</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>
    """
```

**Step 2: Add `build_vs_buy` to page assembly**

In `landing.py` line 498, change:
```python
    body = hero + _reveal(video_section) + _reveal(mcp_walkthrough) + _reveal(search_widget) + _reveal(trending_strip) + _reveal(categories_compact) + _reveal(maker_cta)
```
to:
```python
    body = hero + _reveal(video_section) + _reveal(mcp_walkthrough) + _reveal(build_vs_buy) + _reveal(search_widget) + _reveal(trending_strip) + _reveal(categories_compact) + _reveal(maker_cta)
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read())"`
Expected: No output

---

## Task 2: Reframe Search Widget with Suggestion Pills

**Files:**
- Modify: `src/indiestack/routes/landing.py:362-435` (search widget section)

**Step 1: Update heading and subtext**

In `landing.py` line 367, change:
```
                What are you building?
```
to:
```
                Try it yourself
```

In `landing.py` lines 369-371, change:
```
            <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:24px;">
                Search our catalog &mdash; your AI already does.
            </p>
```
to:
```
            <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:24px;">
                Search like your AI agent does. Pick one or type your own.
            </p>
```

**Step 2: Add suggestion pills after the search input div**

After the closing `</div>` of the search input flex container (line 384) and before the `landing-search-results` div (line 385), insert:

```html
            <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;max-width:560px;margin:12px auto 0;">
                <button class="search-pill" onclick="document.getElementById('landing-search').value='analytics';document.getElementById('landing-search-btn').click();"
                        style="padding:6px 16px;font-size:13px;font-family:var(--font-body);background:rgba(255,255,255,0.05);
                               border:1px solid rgba(255,255,255,0.1);border-radius:999px;color:var(--ink-muted);cursor:pointer;
                               transition:all 0.15s;"
                        onmouseenter="this.style.borderColor='var(--accent)';this.style.color='var(--accent)'"
                        onmouseleave="this.style.borderColor='rgba(255,255,255,0.1)';this.style.color='var(--ink-muted)'">analytics</button>
                <button class="search-pill" onclick="document.getElementById('landing-search').value='auth';document.getElementById('landing-search-btn').click();"
                        style="padding:6px 16px;font-size:13px;font-family:var(--font-body);background:rgba(255,255,255,0.05);
                               border:1px solid rgba(255,255,255,0.1);border-radius:999px;color:var(--ink-muted);cursor:pointer;
                               transition:all 0.15s;"
                        onmouseenter="this.style.borderColor='var(--accent)';this.style.color='var(--accent)'"
                        onmouseleave="this.style.borderColor='rgba(255,255,255,0.1)';this.style.color='var(--ink-muted)'">auth</button>
                <button class="search-pill" onclick="document.getElementById('landing-search').value='invoicing';document.getElementById('landing-search-btn').click();"
                        style="padding:6px 16px;font-size:13px;font-family:var(--font-body);background:rgba(255,255,255,0.05);
                               border:1px solid rgba(255,255,255,0.1);border-radius:999px;color:var(--ink-muted);cursor:pointer;
                               transition:all 0.15s;"
                        onmouseenter="this.style.borderColor='var(--accent)';this.style.color='var(--accent)'"
                        onmouseleave="this.style.borderColor='rgba(255,255,255,0.1)';this.style.color='var(--ink-muted)'">invoicing</button>
                <button class="search-pill" onclick="document.getElementById('landing-search').value='email';document.getElementById('landing-search-btn').click();"
                        style="padding:6px 16px;font-size:13px;font-family:var(--font-body);background:rgba(255,255,255,0.05);
                               border:1px solid rgba(255,255,255,0.1);border-radius:999px;color:var(--ink-muted);cursor:pointer;
                               transition:all 0.15s;"
                        onmouseenter="this.style.borderColor='var(--accent)';this.style.color='var(--accent)'"
                        onmouseleave="this.style.borderColor='rgba(255,255,255,0.1)';this.style.color='var(--ink-muted)'">email</button>
            </div>
```

Note: The pills use `onclick` to set the input value and click the search button, which triggers the existing `doSearch()` via the button's click event listener. No changes to the JS needed.

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read())"`
Expected: No output

---

## Task 3: Smoke Test and Deploy

**Step 1: Run smoke test**

Run: `python3 smoke_test.py`
Expected: All 38 tests pass

**Step 2: Deploy**

Run: `FLY_ACCESS_TOKEN=$(grep access_token ~/.fly/config.yml | awk '{print $2}') ~/.fly/bin/flyctl deploy --remote-only`

**Step 3: Verify landing page**

Check https://indiestack.fly.dev/ — confirm:
- Build vs Buy terminal mockup visible between "How it works" and search widget
- Terminal shows "Without IndieStack" (red) and "With IndieStack" (green) sections
- Search widget heading says "Try it yourself"
- 4 suggestion pills visible below the search box (analytics, auth, invoicing, email)
- Clicking a pill triggers a search and shows results

---

## Execution Summary

| Task | What | Independent? |
|------|------|-------------|
| 1 | Build vs Buy terminal mockup | Yes |
| 2 | Search widget reframe + pills | Yes |
| 3 | Smoke test + deploy | Needs 1 & 2 |

Tasks 1 and 2 modify different sections of landing.py and are fully independent.
