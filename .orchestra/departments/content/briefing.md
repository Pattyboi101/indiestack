# Briefing — 2026-04-04 15:27

## Task
Review src/indiestack/routes/pricing.py for copy accuracy — check for stale claims, broken promises, outdated stats (tool counts, pricing figures). Cross-check any numeric claims against production DB if possible. Also review src/indiestack/routes/submit.py — assess whether the CTA is clear and trust-building. Fix any obvious copy issues directly in the files.

## S&QA Conditions
- MCP department must NOT attempt a PyPI publish or deploy — only edit the file and note that /publish-mcp is needed afterward
- Content department should verify any stat claims (tool counts, install numbers) against what's in the codebase rather than hardcoding new numbers they can't verify

## Risk Flags
- Gotcha: stats in copy go stale fast — pricing page may claim outdated tool counts. Content dept should flag any numbers they can't verify rather than guessing new ones
- Gotcha: MCP changes need PyPI publish to take effect — without it, edits are dead code until someone remembers to publish
