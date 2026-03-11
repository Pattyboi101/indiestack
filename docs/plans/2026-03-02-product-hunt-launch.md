# Product Hunt Launch — Complete Battle Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Launch IndieStack on Product Hunt and get featured (#1 Dev Tools of the Day)

**Strategy:** Prep everything tonight → 2 weeks engaging on PH → launch on a Tuesday/Wednesday

**Research basis:** Modelled after Stackfix (#1 POTW, 1,200 upvotes), Appwrite Sites (#1 POTD, 579 upvotes), Permit.io (#1 POTD, $800 budget)

---

## Phase 1: Tonight — Lock Down All Assets

Everything below gets prepped tonight so launch day is pure execution.

---

### Task 1: Consolidate Launch Kit (delete old docs)

**What:** Delete the two outdated marketing docs that reference marketplace/95% payouts. Replace with one definitive file.

**Step 1:** Delete old files
```bash
rm marketing/product-hunt-launch.md marketing/product-hunt-relaunch.md
rm LAUNCH_DAY.md PRODUCT_HUNT_LAUNCH.md
```

**Step 2:** This plan IS the definitive doc. All copy lives here.

---

### Task 2: Final Tagline & Description

**Tagline (47 chars):**
```
The tool knowledge layer AI agents are missing
```

Why: Follows the Appwrite pattern — positions against a known gap. Instantly clear what it is. Under 60 chars.

**Description (258 chars):**
```
AI agents rebuild auth, analytics, and payments from scratch every session. IndieStack gives them a searchable catalog of 900+ tools so they recommend existing solutions instead. Free MCP server for Claude, Cursor, and Windsurf. Built by two uni students.
```

**Topics:**
1. Developer Tools
2. Artificial Intelligence
3. Open Source
4. Productivity
5. Software Engineering

---

### Task 3: Rewrite Maker Comment (SHORT — Cursor/Stackfix style)

Research says: under 300 words. Current draft is 350+. Cut to the bone.

**Patrick's maker comment (final):**

```
Patrick here. Two CS students in Cardiff.

We kept watching AI agents waste tokens rebuilding things that already exist. Ask Claude to "add analytics" and it writes 200 lines from scratch — when Plausible exists and takes two lines to integrate. Not because agents are bad. Because they start every session with zero knowledge of what's already been built.

So we built the knowledge layer. IndieStack is a catalog of 900+ indie tools that AI agents search via MCP before writing code. Install it (`claude mcp add indiestack -- uvx indiestack`) and your agent checks what exists before rebuilding.

The whole thing runs on Python/FastAPI/SQLite on a single Fly.io machine. Under $10/mo. Zero JS frameworks.

Listing is completely free. No commission, no fees. We're focused on making the catalog as complete and useful as possible.

If you've built something useful — no matter how small — list it. Every solved problem is one less thing an agent rebuilds from scratch.

— Patrick & Ed
```

**Word count: ~150.** Half the previous draft. Hits: problem, solution, tech story, free, CTA.

---

### Task 4: Ed's Co-Founder Comment (post 2 hours after launch)

```
Ed here, Patrick's co-founder.

I handle the community side. Over the past few weeks I've personally talked to hundreds of indie makers — the pattern is always the same. They've built something genuinely useful, but nobody can find it. Not because it's bad. Because there's no layer between "someone built this" and "an AI agent knows it exists."

That's the gap we're filling. 900+ tools from 634 makers across 21 categories. The MCP server is free and already being used in Claude Code, Cursor, and Windsurf.

We're two uni students who haven't slept properly in weeks. If you have feedback on anything — the search, the tool pages, the MCP integration — we read everything. Genuinely.

— Ed
```

**Word count: ~120.** Different angle: community, maker stories, human.

---

### Task 5: Q&A Rapid-Fire Prep (paste-ready responses)

Keep these in a doc you can copy-paste from during launch day.

**"How is this different from awesome-lists / GitHub?"**
> GitHub stores code. Awesome-lists are static markdown. IndieStack is structured and agent-readable — pricing, trust signals, categories, alternatives, integration snippets. Agents don't browse READMEs. They need queryable data.

**"How do you make money?"**
> We don't, yet. Everything is free — listing, searching, claiming. Focused 100% on making the catalog useful before worrying about revenue.

**"Is this just a directory?"**
> Directories are for humans. IndieStack has 11 MCP tools, a Stack Builder API, agent memory that learns your tech stack, and a Prompt Cache Index. AI agents don't browse websites — they need programmable, structured data.

**"What stops you from just scraping everything?"**
> We want makers engaged. Claimed tools get better data, changelogs, trust badges. The catalog is only as good as its structured metadata — that comes from makers, not scraping.

**"Can I list my tool?"**
> Yes. Completely free. No approval process. If it solves a developer problem — full SaaS, script, utility, whatever — list it.

**"Why should I trust this?"**
> Open source on GitHub. We don't sell data. Agent memory tracks category interests only, never raw queries. Full privacy controls at /developer.

**"What about quality control?"**
> Maker ✓ badge for claimed tools, community upvotes, agent usage data (how often agents recommend it), and the Dead Tool Detector that flags abandoned projects.

---

### Task 6: Demo Video Script (60 seconds)

This is the #1 asset. All top PH dev tools in 2025 had demo videos. Authentic screen recording > polished production.

**Script:**

```
[SCREEN: Terminal with Claude Code open]

CAPTION: "You ask Claude to add analytics..."

> User types: "Add privacy-friendly analytics to my app"

[Claude Code searches IndieStack via MCP — show the search happening]

CAPTION: "Your agent searches 900+ indie tools first"

[Results appear: Plausible, Simple Analytics, Umami — with pricing and descriptions]

CAPTION: "Instead of writing 200 lines from scratch..."

[Claude recommends Plausible, shows integration snippet]

CAPTION: "It recommends what already exists."

[SCREEN: Cut to IndieStack explore page — grid of tools]

CAPTION: "900+ tools. 634 makers. Free MCP server."

[SCREEN: indiestack.fly.dev with tagline visible]

CAPTION: "claude mcp add indiestack -- uvx indiestack"

[END — 60 seconds]
```

**How to record:**
- QuickTime screen recording (Mac) or OBS (Linux/Windows)
- Record at 1920x1080, export at 635x380 for PH gallery
- No voiceover needed — captions only (PH autoplays muted)
- Keep it snappy. Cut dead air. Every second counts.

---

### Task 7: Screenshot List (capture tonight)

All screenshots at 635x380 px minimum. Capture in dark mode for consistency.

| # | Screenshot | What to show | Why |
|---|---|---|---|
| 1 | **Demo video** (uploaded as first gallery item) | MCP server in Claude Code | Money shot — differentiator |
| 2 | **Landing page hero** | Full hero with stats bar, search | Shows polish + scale |
| 3 | **Explore page** | Tool grid with Maker ✓ badges, filters | Shows breadth (900+ tools) |
| 4 | **Tool detail page** | Badges, "Listed for free", structured data | Shows depth + trust signals |
| 5 | **Terminal: pip install** | `claude mcp add indiestack -- uvx indiestack` + MCP config | Shows how easy setup is |

**Order matters.** PH shows first gallery item as the hero. Video goes first.

---

### Task 8: Reddit Cross-Posts (draft tonight, post on launch day)

All posts link to PH listing URL, NOT indiestack.fly.dev. PH counts referral traffic.

**r/ClaudeAI** (already drafted — use the revised version that passed auto-mod rules)

**r/SaaS:**
```
Title: AI agents keep rebuilding solved problems — we built a knowledge layer to fix it

Body:
We just launched on Product Hunt. The idea is simple: AI coding agents (Claude, Cursor, Windsurf) rebuild auth, analytics, and payments from scratch every session because they don't know what already exists.

IndieStack is a catalog of 900+ indie tools that agents search via MCP before writing code. Instead of 200 lines of custom analytics, your agent recommends Plausible. Instead of billing logic, it finds an existing invoicing tool.

Free to list, free to search. No commission.

We're two CS students. The whole thing runs on a single server for $10/mo.

[Product Hunt link]
```

**r/webdev:**
```
Title: We indexed 900+ dev tools so AI agents stop rebuilding everything from scratch

Body:
Every time you ask an AI coding assistant to "add auth" or "add analytics," it writes the whole thing from scratch. We built an MCP server that gives agents a catalog of existing tools to search first.

900+ tools across 21 categories. Free MCP server — claude mcp add indiestack -- uvx indiestack. Works with Claude Code, Cursor, Windsurf.

Just launched on Product Hunt — would love feedback from the webdev community.

[Product Hunt link]
```

**r/SideProject:**
```
Title: Two uni students built a tool catalog that AI agents search before writing code — just launched on PH

Body:
10 weeks ago we started with 100 indie tools in a directory. Today we have 900+ tools, 634 makers, an MCP server on PyPI, and AI agents actively using it.

The idea: when you ask Claude to "add analytics," it should check if Plausible exists before writing 200 lines of custom code. We built that layer.

Python/FastAPI/SQLite, single Fly.io machine, $10/mo. Zero JS frameworks.

Just launched on Product Hunt — feedback welcome.

[Product Hunt link]
```

---

### Task 9: Maker Activation Email (claimed tools only — 66 makers)

**NOT a mass blast.** Only goes to the ~66 makers who actively claimed their tools. They opted in.

**Subject:** IndieStack is launching on Product Hunt — your tool is featured

**Body:**
```
Hey [maker_name],

Quick heads up — we're launching IndieStack on Product Hunt on [DATE].

Your tool [tool_name] is part of the catalog that AI agents search. On launch day, thousands of developers will see it.

If you have a moment, we'd love for you to:
- Check your listing is up to date: indiestack.fly.dev/tool/[slug]
- Drop by the Product Hunt page if you're curious: [PH LINK]

No pressure at all. Just wanted you to know it's happening.

— Patrick & Ed
```

**Key:** No "please upvote." No urgency tricks. Just awareness. The research shows warm activation > desperate asks.

---

### Task 10: Social Posts (draft tonight)

**Twitter/X thread:**
```
We just launched IndieStack on Product Hunt.

The problem: AI agents rebuild auth, analytics, and payments from scratch every session — because they don't know what already exists.

The fix: a catalog of 900+ indie tools that agents search via MCP before writing code.

🧵 Thread:

1/ Ask Claude to "add analytics" → it searches IndieStack → recommends Plausible instead of writing 200 lines of custom code.

2/ The MCP server works with Claude Code, Cursor, Windsurf. claude mcp add indiestack -- uvx indiestack. That's it.

3/ 900+ tools from 634 indie makers. Completely free to list, search, and claim.

4/ Built by two uni students in Cardiff on Python/FastAPI/SQLite. Single server. $10/mo.

5/ Check it out on Product Hunt: [LINK]
```

**LinkedIn:**
```
We just launched IndieStack on Product Hunt.

The short version: AI coding agents (Claude, Cursor, Windsurf) rebuild things from scratch every session because they don't know what already exists. We built the knowledge layer — 900+ indie tools that agents search via MCP before writing code.

Two CS students. Python/FastAPI/SQLite. Single server. $10/month.

Product Hunt link: [LINK]
```

---

## Phase 2: Pre-Launch Engagement (2 weeks before launch)

This is what separates 50 upvotes from 500+. The research is unanimous: PH rewards community members who engage BEFORE launching.

### Week 1: Build PH Presence

| Day | Action | Who | Time |
|-----|--------|-----|------|
| Day 1 | Create/complete PH maker profiles (photo, bio, links, IndieStack URL) | Both | 30 min |
| Day 1 | Upvote and comment on 5 dev tool launches on PH | Both | 30 min |
| Day 2 | Comment on 5 more PH launches (genuine, helpful comments) | Both | 20 min |
| Day 3 | Comment on 5 PH launches + join 2 PH discussions | Both | 20 min |
| Day 4 | Comment on 5 PH launches | Both | 20 min |
| Day 5 | Comment on 5 PH launches + post in PH discussions about MCP/AI tools | Patrick | 20 min |
| Day 6-7 | Rest / catch up on any missed days | — | — |

**Rules:**
- Comments must be genuine — actually try the products, give real feedback
- Don't mention IndieStack yet. Build reputation first.
- Both accounts should have 10+ comments before launch day

### Week 2: Pre-Launch Setup

| Day | Action | Who | Time |
|-----|--------|-----|------|
| Day 8 | Continue daily PH commenting (5/day) | Both | 20 min |
| Day 9 | Record demo video | Patrick | 2-4 hrs |
| Day 10 | Capture all 5 screenshots, upload to PH draft | Patrick | 1 hr |
| Day 11 | Create PH "upcoming" page with all assets | Patrick | 1 hr |
| Day 11 | Send maker activation email to 66 claimed makers | Patrick | 30 min |
| Day 12 | Final review of all copy, comments, Q&A | Both | 1 hr |
| Day 13 | Share "upcoming" page with close supporters (5-10 people) | Both | 30 min |
| Day 14 | REST. Do not touch anything. Everything is locked. | Both | — |

---

## Phase 3: Launch Day (L-Day)

**Launch date:** Pick a Tuesday or Wednesday, 2 weeks from prep completion.

**All times in PT (Pacific) / UK:**

| Time (PT) | Time (UK) | Action | Who |
|-----------|-----------|--------|-----|
| 12:01 AM | 8:01 AM | Go live on PH. Post Patrick's maker comment within 60 seconds. | Patrick |
| 12:05 AM | 8:05 AM | Share PH link with close network (WhatsApp, Discord, DMs) | Ed |
| 2:00 AM | 10:00 AM | Ed posts co-founder comment on PH | Ed |
| 2:00 AM | 10:00 AM | Post r/ClaudeAI thread (link to PH) | Patrick |
| 3:00 AM | 11:00 AM | Post r/SaaS thread | Ed |
| 4:00 AM | 12:00 PM | Post r/webdev thread | Patrick |
| 5:00 AM | 1:00 PM | Post r/SideProject thread | Ed |
| 5:00 AM | 1:00 PM | Twitter/X thread goes live | Patrick |
| 5:00 AM | 1:00 PM | LinkedIn post goes live | Patrick |
| 6:00 AM | 2:00 PM | First sweep: reply to ALL PH comments | Both |
| 9:00 AM | 5:00 PM | Second sweep: reply to all new comments | Both |
| 12:00 PM | 8:00 PM | Mid-day PH update comment: share stats | Patrick |
| 3:00 PM | 11:00 PM | Reply sweep + thank early supporters | Both |
| 6:00 PM | 2:00 AM+1 | Final comment sweep | Patrick |
| 9:00 PM | 5:00 AM+1 | End of day. Post final thank-you comment on PH. | Patrick |

**Critical rules:**
- Reply to EVERY comment within 10-30 minutes. Research says each unanswered comment costs ~5 ranking positions.
- NEVER ask for upvotes. Say "check it out" or "would love feedback."
- NEVER edit the live PH page. Editing resets your trending score.
- Share PH link everywhere, not indiestack.fly.dev (so traffic counts toward PH ranking).
- Both Patrick and Ed comment separately — two voices > one.

---

## Phase 4: Post-Launch (Days 2-7)

| Day | Action |
|-----|--------|
| Day 2 | Reply to all remaining PH comments. Share final stats on Twitter/LinkedIn. |
| Day 3 | Write "What we learned launching on PH" post for r/SideProject (drives long-tail traffic) |
| Day 4 | Follow up with any makers who commented on PH — offer to feature them |
| Day 5 | Send weekly digest to subscribers with PH results |
| Day 7 | Retrospective: what worked, what didn't, save learnings |

---

## Success Metrics

| Metric | Target | Stretch |
|--------|--------|---------|
| Upvotes | 200+ | 500+ |
| Comments | 30+ | 75+ |
| PH ranking | Top 5 Dev Tools | #1 Dev Tools of Day |
| New signups | 30+ | 100+ |
| New tool claims | 10+ | 25+ |
| MCP installs (PyPI) | 50+ | 200+ |
| Featured on PH homepage | Yes | — |

---

## Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `docs/plans/2026-03-02-product-hunt-launch.md` | This plan (definitive) | ✅ |
| `marketing/product-hunt-launch.md` | OLD — delete | ❌ Delete |
| `marketing/product-hunt-relaunch.md` | OLD — delete | ❌ Delete |
| `LAUNCH_DAY.md` | OLD — delete | ❌ Delete |
| `PRODUCT_HUNT_LAUNCH.md` | OLD — delete | ❌ Delete |
| `docs/launch-day-prep.md` | OLD — delete | ❌ Delete |

---

## What We're NOT Doing

- ❌ Mass email to 634 makers (learned from backlash)
- ❌ Asking for upvotes anywhere
- ❌ Buying PH ads or promotion
- ❌ Mentioning boost/marketplace/paid features (paused)
- ❌ Editing the PH page after launch
- ❌ Posting on HN (hostile thread still recent — revisit later)
