# awesome-claude-code Submission Prep

Created: 2026-04-01
Updated: 2026-04-02
Source: S&QA analysis + form template review
Target submit date: April 7, 2026
Repo: hesreallyhim/awesome-claude-code (35k stars)

## Hard Blockers

1. **GitHub stars: currently 0, need 5+** — bot auto-rejects under 5. Patrick + Ed star + recruit 3 genuine stars by April 5.
2. **LICENSE file missing** — repo has NO LICENSE file (GitHub API confirms `license: None`). The submission form requires selecting a license, and the prep doc incorrectly claimed MIT. **Must add MIT LICENSE file before submitting.**
3. **Submit via GitHub web UI ONLY** — URL: `https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml`. The form explicitly states: "Issues must be submitted by human users using the github.com UI. The system does not allow resource submissions via the `gh` CLI or other programmatic means." Patrick must submit manually.

## Soft Blockers

4. **Frame as focused, NOT marketplace** — form warns: "Try to submit _focused_ resources that differentiate your project from others, not general-purpose marketplaces." Our description must emphasize IndieStack as a Claude Code skill/MCP server, not a catalog.
5. **Maintainer hates AI-generated READMEs** — needs Patrick's voice.
6. **30-sec demo video strongly recommended** — form says "Short examples or demos are tremendously helpful" and "If I can see it in action before I think about running it, you're way ahead of the curve."
7. **Network requests disclosure required** — form says "If your resource involves making ANY network requests except to the Anthropic API, you must state that." Our MCP server calls indiestack.ai API — must disclose.
8. **"Could Opus build this in one session?" test** — maintainer uses this bar. We pass (3,100 tools, curation, API).
9. **Pre-run their evaluation** — maintainer runs `.claude/commands/evaluate-repository.md` against submissions. We should run this ourselves first.

## In Our Favor

- No competing entry (genuine gap in the list)
- Repo age fine (Feb 22, 2026 — well over one week old)
- Passes "Opus test" — too substantial for one session
- Simple install: `claude mcp add indiestack -- uvx --from indiestack indiestack-mcp`
- PyPI package (real distribution, not just a GitHub repo)

## Prep Timeline

| # | Task | Owner | Deadline | Status |
|---|------|-------|----------|--------|
| 1 | Get 5+ GitHub stars | Patrick + Ed | April 5 | **NOT DONE** — Patrick starred, Ed needed + 3 more |
| 2 | Rewrite GitHub README.md | Content dept | April 5 | **DONE** |
| 3 | Record 30-sec demo video | Patrick | April 6 | **NOT DONE** |
| 4 | Draft submission form answers | Strategy | April 6 | **DONE** (see below) |
| 5 | Remove "marketplace" language | Content | April 5 | **DONE** (README rewrite) |
| 6 | Fix .fly.dev → .ai links | Backend dept | April 4 | **DONE** |
| 7 | Add MIT LICENSE file to repo | Patrick/Backend | April 4 | **DONE** (committed 2026-04-02) |
| 8 | Run maintainer's evaluation prompt | Strategy | April 5 | **NOT DONE** |
| 9 | Disclose network requests in submission | Strategy | April 6 | **DONE** (in form draft below) |

## Submission Form Draft (updated to match actual form fields)

**Display Name:** IndieStack MCP Server

**Category:** Agent Skills

**Sub-Category:** General

**Primary Link:** https://github.com/Pattyboi101/indiestack

**Author Name:** Pattyboi101

**Author Link:** https://github.com/Pattyboi101

**License:** MIT (must add LICENSE file first!)

**Description:**
> MCP server that gives Claude Code searchable access to 3,100+ curated developer tools with install commands, compatibility data, and pricing. Searches a maintained catalog instead of hallucinating package names or generating boilerplate infrastructure for auth, payments, monitoring, and 25 other categories. Makes network requests to the indiestack.ai API to serve results.

**Validate Claims:**
> Install the MCP server (`claude mcp add indiestack -- uvx --from indiestack indiestack-mcp`) and ask Claude to help you add any common infrastructure to a project. Claude will search real tools instead of generating code from scratch. No API key needed — unlimited searches.

**Specific Task(s):**
> Ask Claude Code to recommend an authentication solution for a Next.js app, or find a self-hosted analytics tool, or compare payment processors. With IndieStack installed, Claude searches 3,100+ real tools with pricing, install commands, and compatibility data.

**Specific Prompt(s):**
> "I need to add authentication to my Next.js app. What are my options?" — with IndieStack installed, Claude searches real tools with install commands, pricing, and compatibility notes instead of guessing or generating boilerplate.

**Additional Comments:**
> IndieStack's MCP server is published on PyPI (`pip install indiestack` / `uvx`), currently serving tool lookups to Claude Code users. The server makes API calls to indiestack.ai to search the catalog — no other network requests. Built with Claude Code by two indie devs in Cardiff.

## Remaining Risks

1. **Stars = 0 is the #1 blocker** — auto-rejected without 5+
2. **No LICENSE file** — easy fix but must be done before submission
3. **"Marketplace" perception** — description must emphasize the MCP skill, not the catalog
4. **Network request scrutiny** — maintainer is security-conscious, disclosure is mandatory
