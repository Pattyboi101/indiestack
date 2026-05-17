---
name: search-quality-audit
description: "Audit _CAT_SYNONYMS routing gaps and add missing entries to improve search quality. Use when search queries return wrong categories or raw_first with no category boost."
metadata:
  version: 1.0.0
  author: autonomous-loop
  category: search
  updated: 2026-05-17
---

# Search Quality Audit — Backend Department

You are responsible for finding and fixing routing gaps in `_CAT_SYNONYMS` in `src/indiestack/db.py`.

## When to Use This Skill

- Scheduled improvement cycles (autonomous loops)
- A user reports that searching for a tool returns no category boost
- `raw_first` fires for high-volume query terms
- A new product category was added but queries for it have no synonyms

## Workflow

### 1. Check existing coverage for the target area

Always grep BEFORE adding — Python dicts silently override duplicate keys with the last value.

```bash
grep -n '"term"' src/indiestack/db.py | head -20
```

### 2. Probe queries offline

```python
PYTHONPATH=src python3 -c "
from scripts.test_search_routing import route_query
queries = ['your queries here']
for q in queries:
    cat, via = route_query(q)
    print(repr(q) + ' -> ' + repr(cat) + ' via ' + repr(via))
"
```

A result of `via = 'raw_first'` with a token category like `'llms'` means the first meaningful token of the query has no synonym — it's a gap.

### 3. Identify the fix type

| Scenario | Fix |
|----------|-----|
| Single unmapped token | `"token": "category_value"` |
| Hyphenated form missing | `"token-form": "category_value"` |
| Two adjacent unmapped tokens | `"token1 token2": "category_value"` (bigram) |
| Brand name overrides wrong single token | bigram overrides single token at that position |

**Category values** are short-name strings — NOT slugs. See `_CAT_SYNONYMS` header in CLAUDE.md for the full mapping.

### 4. Add the entry

Add single-token entries in the relevant thematic block in `_CAT_SYNONYMS`. Add bigrams (spaced compound keys) near the other bigrams at the bottom of `_CAT_SYNONYMS`.

**Rules:**
- ALWAYS add both hyphenated and non-hyphenated variants for compound terms
- Bigrams that contain a stop word from `_FTS_STOP_WORDS` can NEVER fire — verify both tokens survive
- 3-token compound keys can NEVER fire — use bigram + single-token fallback instead
- Check `_FTS_STOP_WORDS` before adding bigrams: `python3 -c "from indiestack.db import _FTS_STOP_WORDS; print('token' in _FTS_STOP_WORDS)"`

### 5. Validate

```bash
PYTHONPATH=src python3 scripts/test_search_routing.py
```

Must pass with zero failures before committing.

### 6. Add test cases

Add corresponding test cases to the `TEST_CASES` list in `scripts/test_search_routing.py`.

## Pattern: Spaced-Form Gaps + Stop-Word Erosion

Compound terms often have their hyphenated form (`"zero-trust"`) and compounded form (`"zerotrust"`) mapped but the natural spaced two-word form (`"zero trust"`) missing. Always check all three forms:

```
for term in ["zero trust", "zerotrust", "zero-trust"]:
    route_query(term)
```

Also watch for **stop-word erosion**: a phrase like "software bill of materials" has "software" and "of" as stop words, so surviving tokens are `["bill","materials"]`. The bigram `"bill materials"` must be explicitly mapped.

Historically found: "zero trust" (spaced), "zero knowledge", "bill materials" (from SBOM queries).

## Common Gap Categories to Probe

These areas historically generate `raw_first` misses:

| Domain | Tokens to test |
|--------|---------------|
| AI frameworks 2025-2026 | pydantic ai, agno, mastra, smolagents |
| Local LLM tooling | lm studio, koboldai, llms.txt (dot), llmstxt |
| LLMOps / eval | trulens, braintrust, weave, ragas |
| AI safety | llamaguard, rebuff, guardrails, prompt injection |
| Data engineering | etl, elt, dbt, airbyte, fivetran |
| Edge/serverless | val town, deno deploy, cloudflare workers |
| Standards | llms.txt, a2a, mcp, openai agents |
| Frontend build tools | snowpack, farm, parcel, turbopack |
| Email delivery | sparkpost, mailgun, postmark, sendgrid |
| Usage-based billing | m3ter, lago, orb, autumn, stigg |
| Analytics databases | hydrolix, tinybird, clickhouse, motherduck |
| AI hyphenated forms | fine-tuning, llms.txt (dot form), pydantic-ai |
| PII / data privacy | presidio, arcjet, skyflow, private ai |
| Observability new | phoenix (arize), honeycomb, lightstep |
| New AI coding tools | zed editor, helix editor, cursor ide |

## Commit Style

```
fix: N search routing gaps — [short description] (M/M pass)
```

Example: `fix: 13 search routing gaps — snowpack, llamaguard, llms.txt + 10 more (166/166 pass)`
