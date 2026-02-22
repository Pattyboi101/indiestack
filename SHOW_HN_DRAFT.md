# Show HN Submission Draft

> Prepared 2026-02-20. Review and edit before posting.

---

## Title Options (ranked by likely HN engagement)

### 1. "Show HN: A searchable index of indie dev tools with an MCP server for AI coding assistants"
(79 chars) — Leads with the novel angle. MCP is still new enough to be interesting on HN. "Searchable index" signals utility, not marketing. Developers on HN are actively using Claude Code / Cursor and will immediately understand why this matters.

### 2. "Show HN: I built a full marketplace in Python, SQLite, and zero JS frameworks"
(77 chars) — The contrarian tech stack angle. HN loves opinionated simplicity. Pure Python string templates with no React/Vue/Jinja2 is unusual enough to spark discussion. This title invites "how did you handle X without a framework?" comments, which drives engagement.

### 3. "Show HN: IndieStack – Stop your AI assistant from rebuilding solved indie tools"
(78 chars) — Problem-first framing. Slightly riskier because it could read as marketing, but the problem is real and technical. Works best if the MCP integration is polished enough that people can try it immediately.

**Recommendation**: Go with #1. It is specific, technical, and describes exactly what the thing does. HN rewards clarity over cleverness.

---

## Submission URL

https://indiestack.fly.dev

---

## First Comment (The Maker Comment)

Post this immediately after submission — within 60 seconds:

---

Hey HN. I'm Patrick, a CS student at Cardiff University. My co-founder Ed and I built this over 10 weeks as a side project.

**The problem**: AI coding assistants (Claude Code, Cursor, Copilot) routinely spend hundreds of tokens rebuilding authentication, billing, email, and other infrastructure that indie developers have already packaged as working tools. There's no structured way for an AI to check "does a tool for this already exist?" before it starts generating boilerplate.

**The solution**: IndieStack is a curated index of 100+ indie SaaS tools with a JSON API and a standalone MCP server. You point your AI assistant at it, and before it writes an auth system from scratch, it can search for existing tools that solve the problem — complete with integration snippets, pricing, and "tokens saved" estimates.

**Tech stack** (since HN always asks): Pure Python/FastAPI, SQLite with WAL mode and FTS5, zero JavaScript frameworks. The entire frontend is Python string templates — no Jinja2, no React, no build step. 21 route files, 29 database tables, Stripe Connect for payments. Single Fly.io machine. The MCP server is ~150 lines of Python.

**What makes this different from G2/Capterra**: Those are built for enterprise procurement teams comparing Salesforce editions. IndieStack is structured for developer workflows — JSON API, MCP integration, code snippets on every tool page, "replaces" fields that map tools to the incumbents they compete with, and an "Ejectable" badge for tools that guarantee clean data export.

**Honest disclaimer**: We have zero organic users. We deliberately purged all seeded test data (fake reviews, upvotes, etc.) before launching because we'd rather show honest empty states than fake social proof. This is a portfolio project that we're trying to turn into something real. The architecture is genuine, the payments work, but we haven't solved distribution yet.

Would love feedback on two things specifically:
1. The MCP integration approach — is "search before you build" actually useful in your workflow?
2. The architecture choices — the full breadcrumb doc is in the repo at ARCHITECTURE.md

MCP server setup: `python3 -m indiestack.mcp_server` (calls our JSON API at /api/tools/search and /api/tools/{slug}).

---

(~280 words)

---

## Timing Advice

**Best times to post Show HN** (all times US Eastern):

- **Tuesday–Thursday, 8:00–10:00 AM ET** — Peak HN traffic. Most Show HN posts that reach the front page are submitted in this window. The US West Coast is waking up, the East Coast is at work, and Europe is still online in the afternoon.
- **Avoid**: Friday afternoons, weekends, and US holidays. Traffic drops 30-40% and moderators are less active.
- **Avoid**: Monday mornings — too much competing content from the weekend backlog.
- **Second-best**: Wednesday 6:00 AM ET — catches the early-morning crowd with less competition. Good for UK-based posters since it's 11:00 AM GMT.

**For you specifically** (Cardiff, UK = GMT): Post at **1:00–3:00 PM GMT on a Tuesday, Wednesday, or Thursday**. This hits the 8:00–10:00 AM ET sweet spot.

**Important**: Do NOT delete and repost if it doesn't take off. HN penalises resubmissions. You get one shot per URL. If it doesn't gain traction, wait 2+ days and resubmit with a different title.

---

## Common HN Pitfalls to Avoid

1. **Do not use marketing language in comments.** Phrases like "game-changer," "disrupting," "revolutionary," or "the Uber for X" will get you downvoted instantly. Describe what it does in plain technical terms. If you catch yourself writing a superlative, delete it.

2. **Do not get defensive when people criticise your choices.** Someone will say "why not Postgres?" or "SQLite won't scale." The correct response is "you're right, here's the tradeoff I made and here's where it breaks." HN respects builders who understand their own limitations. Arguing back kills goodwill.

3. **Do not ignore comments or disappear after posting.** The maker comment and the first hour of replies are when HN decides if your post is worth upvoting. Be present, respond thoughtfully, and engage for at least 2-3 hours after submission. Going silent signals "I just wanted traffic."

4. **Do not astroturf or ask friends to upvote.** HN's voting ring detection is aggressive. If multiple accounts from the same network upvote within minutes of posting, it will be flagged and potentially killed. Let it succeed or fail organically.

5. **Do not hide the fact that this is a student/portfolio project.** HN is suspicious of stealth marketing but generous toward honest builders. Leading with "CS student, built this as a learning project, zero users" is a strength on HN, not a weakness. Pretending you have traction you don't will get called out, and the thread will turn hostile.
