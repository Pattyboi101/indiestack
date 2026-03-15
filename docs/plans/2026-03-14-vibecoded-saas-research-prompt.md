# Gemini Deep Research Prompt — Quality Gates for Curated AI Tool Directories

> Copy everything below the line into Gemini Deep Research. Attach the context file (2026-03-14-vibecoded-saas-context.md) as a document.

---

## Prompt

I've attached a detailed context document about IndieStack — an open-source supply chain that helps AI agents discover and compose indie-built software. Read it thoroughly before proceeding.

**The situation**: IndieStack has 3,100 tools across 25 categories, served to AI agents via an MCP server. Until now, nearly all tools were auto-indexed from curated awesome-lists (high quality). But as IndieStack grows, manual submissions are arriving — and the 2025-2026 "vibecoding" explosion means a flood of weekend-built, closed-source SaaS products using IndieStack as free advertising. We've had 1 rejection out of 3,100 tools. The approval bar is essentially non-existent, and we need to fix this before it destroys the curation signal that makes IndieStack valuable to AI agents.

**The strategic question**: How should a curated, AI-agent-facing directory implement quality gates that filter low-effort vibecoded SaaS submissions without killing legitimate indie SaaS founders — and what signals actually predict whether a tool is worth recommending?

**The key insight you must factor in**: IndieStack's primary users are AI agents, not humans. A spam tool that fools a human reviewer might still fail when an agent tries to integrate it (broken docs, no API, misleading description). The quality signals that matter most are machine-verifiable: does the tool actually work, does it have documentation agents can parse, does it solve a real problem, is it maintained? Human-facing curation metrics (star count, design quality, brand) matter less.

**Research areas (go deep on each):**

1. **How curated directories handle quality at scale** — Research Product Hunt's moderation model, Awesome Lists' contribution guidelines, F-Droid's inclusion criteria, AlternativeTo's community curation, Homebrew Cask's review process. What automated checks do they use? What's their rejection rate? How do they handle borderline cases? What signals predict rejection?

2. **Vibecoded SaaS detection signals** — The 2025-2026 wave of AI-generated SaaS products has specific fingerprints: Vercel/Netlify deploy URLs, generic landing pages, no documentation beyond a README, no GitHub activity beyond initial commit, pricing pages with no free tier, descriptions that read like AI marketing copy. Research what NLP/heuristic signals reliably distinguish vibecoded weekend projects from serious indie products. Look at research on AI-generated content detection, landing page quality scoring, and documentation maturity metrics.

3. **Free tier as a quality signal** — Many legitimate indie SaaS tools offer free tiers (Plausible, Buttondown, Crisp). Is "has a free tier" a reliable proxy for "genuinely useful to the community"? Research the correlation between free tier availability and tool quality/adoption. What about open-core models? How do directories like G2, Capterra, and AlternativeTo handle paid-only tools?

4. **Automated tool verification** — Beyond static metadata checks, what can be verified automatically? HTTP health checks (already implemented for GitHub repos, but not SaaS). Documentation page detection (does /docs, /api, /getting-started exist?). Social proof verification (do real people mention this tool on Twitter/Reddit/HN?). API endpoint validation (does the claimed API actually respond?). Research what automated verification systems exist for software directories and package registries.

5. **Community-driven quality signals** — Stack Overflow uses reputation and voting. Wikipedia uses editorship tiers. npm uses download counts. What community-driven quality mechanisms work for small catalogs (3,000-10,000 items) with low engagement (60 upvotes total, 4 reviews)? The "cold start" problem is real — IndieStack doesn't have enough community engagement to rely on crowdsourced quality yet.

6. **The "indie" definition problem** — IndieStack's constraint is "indie-built," but this is increasingly meaningless when a solo founder can vibecode a SaaS in a weekend. Research how other communities define and enforce "indie" or "independent": indie games (Steam's indie tag controversy), indie music (label independence), indie publishing. What criteria actually correlate with the spirit of "independently built with care" vs "churned out for SEO/marketing"?

**What I need from you:**

A **quality gate architecture** — a concrete, implementable system with:
1. **Submission-time automated gates** (what gets blocked before human review)
2. **Enrichment signals** (what data to gather automatically post-submission, pre-review)
3. **Admin review scoring** (how to present quality signals to make approve/reject decisions fast)
4. **Post-approval monitoring** (what triggers re-evaluation of approved tools)
5. **The "indie SaaS" policy** — a clear, defensible position on closed-source paid SaaS

For each gate/signal, specify: what it checks, why it works, false positive risk, implementation complexity, and whether it's machine-verifiable.

**Constraints on your analysis:**

- No generic advice like "use machine learning to detect spam." Specify exactly what features, what thresholds, what training data.
- Think in systems, not features. The quality gate system must be self-correcting — tools that slip through should be caught by post-approval decay.
- Assume AI leverage — 2-person team with Claude Code ships 5-10x faster than traditional.
- Indie-first. No ideas requiring hiring, funding, or manual review at scale.
- Research deeply, don't speculate. Cite actual moderation policies, rejection criteria, and quality scoring systems from real platforms.
- Challenge our assumptions. Maybe "keep everything and let quality score sort it out" is actually the right answer. Maybe the approval queue itself is the problem.

**Additional angles to explore:**

- Should IndieStack move to an "approve by default, demote by signal" model instead of manual approval? What are the risks?
- How do package registries (npm, PyPI, crates.io) handle the spam problem? They face the exact same issue at much larger scale.
- Is there a way to use the MCP server's outcome data (success rates, agent citations) as a retroactive quality signal? Tools that agents try but fail to integrate could be automatically flagged.
- What's the optimal rejection rate? Too low (current: 0.03%) means no filtering. Too high means killing submissions. What do healthy curated directories target?
- Could IndieStack require a "proof of value" — e.g., at least one user testimonial, a working demo, or a public roadmap — before approval?

**Format**: Architecture document with clear sections, implementation priorities (P0/P1/P2), and a decision matrix for the "indie SaaS" policy question.

**Depth expectation**: This is an LLM-to-LLM knowledge transfer. I will be implementing your recommendations directly with Claude Code. Be precise. Cite sources. The context document has everything about IndieStack's current state — your job is to bring external research and original thinking about quality systems that work.
