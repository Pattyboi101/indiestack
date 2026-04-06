# Ed's AGENTS.md Campaign — Pre-Spud Launch

**Priority:** URGENT. Spud (OpenAI GPT-5/6) launches in weeks. AGENTS.md files in repos = IndieStack gets discovered by every Spud agent that reads them. Window closes when Spud ships with defaults locked in.

## What is AGENTS.md?

OpenAI's equivalent of CLAUDE.md. Agents read this file to understand what tools and MCPs are available in a project. If a repo has an AGENTS.md pointing to IndieStack, every Spud agent working in that repo will find IndieStack automatically.

The template is live at: **https://indiestack.ai/setup/agents.md**

## Your Job: PR Blitz

Open PRs to popular repos adding AGENTS.md. Keep them small, professional, and benefit-focused.

### Target Repos (start here, highest star count first)

**Starters / Templates (these get cloned thousands of times):**
- `t3-oss/create-t3-app` — T3 stack starter (Next.js + tRPC + Prisma)
- `t3-oss/t3-turbo` — T3 turbo monorepo
- `shadcn-ui/ui` — shadcn/ui component library  
- `vercel/next.js` — if they have example templates folder
- `expo/expo` — Expo starter templates
- `epicweb-dev/epic-stack` — Kent C. Dodds' full-stack starter
- `PayloadCMS/payload` — headless CMS
- `steven-tey/precedent` — Next.js starter with auth + payments
- `rocketseat-education/ignite` — Rocketseat bootcamp starters

**Auth / Payments tools (high citation = makers should care):**
- `nextauthjs/next-auth` — 23 citations, probably the best target
- `supabase/supabase` — huge, well-maintained
- `clerk/clerk-js` — popular auth SDK
- `stripe/stripe-node` — payments

**Any repo with package.json and no AGENTS.md**

### PR Template

**Title:** `docs: add AGENTS.md for AI agent tool discovery`

**Body:**
```
## What's this?

AGENTS.md is the OpenAI standard for telling AI coding agents (like GPT-5/Spud, Claude Code) what tools are available in a project. Similar to .cursorrules or CLAUDE.md.

This PR adds an AGENTS.md that directs agents to check IndieStack before writing common infrastructure from scratch — auth, payments, analytics, databases, etc.

**Why this is useful for your project:**
- Agents working in this repo will find existing tools instead of generating boilerplate
- Saves 30k–80k tokens per session
- IndieStack has 7,500+ curated developer tools with compatibility data

The template is minimal — agents read it once per session.
```

**AGENTS.md content to add:** Download from https://indiestack.ai/setup/agents.md and commit as `AGENTS.md` in the repo root.

## Reddit Posts (ready to fire on Spud launch day)

### r/OpenAI, r/ChatGPT (post when Spud drops)
**Title:** "How to make your repo discoverable by GPT-5 agents — AGENTS.md explained"

> OpenAI agents (including the new model) read AGENTS.md files in your repo to understand what tools are available. Similar to how Claude reads CLAUDE.md.
>
> If you add an AGENTS.md pointing to IndieStack, every agent working in your project automatically has access to 7,500+ curated developer tools — auth, payments, databases, monitoring, etc.
>
> Takes 2 minutes: https://indiestack.ai/setup — grab the AGENTS.md template.
>
> Anyone else experimenting with this? What MCPs are you adding?

### r/ClaudeAI
**Title:** "AGENTS.md + CLAUDE.md — make your project work with both OpenAI and Anthropic agents"

> Quick tip: if you have CLAUDE.md, also add AGENTS.md. Same idea, OpenAI format. IndieStack has templates for both at https://indiestack.ai/setup
>
> Now any AI agent — Claude Code or Spud — working in your project will auto-discover 7,500+ tools before writing infrastructure from scratch.

### r/LocalLLaMA
**Title:** "AGENTS.md — OpenAI's answer to CLAUDE.md just shipped. Here's how to use it."

> [Explain the format, give the IndieStack template as an example of a good AGENTS.md]

## Metrics to Track

- PRs opened per day (target: 5–10)
- PRs merged (track in a simple list)
- Reddit post upvotes / engagement

## Timing

- Start PRs **today** — don't wait for Spud to launch
- Reddit posts **on launch day** — timing to the announcement gets maximum visibility

## Notes

- Keep PRs small and respectful — one file, clear description
- Don't spam — if a repo already has AGENTS.md or CLAUDE.md, skip it
- If maintainers ask questions, refer them to https://indiestack.ai/setup/agents.md
