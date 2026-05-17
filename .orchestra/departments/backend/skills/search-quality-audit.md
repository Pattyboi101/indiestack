---
name: search-quality-audit
description: "Audit _CAT_SYNONYMS routing gaps and add missing entries to improve search quality. Use when search queries return wrong categories or raw_first with no category boost."
metadata:
  version: 1.0.0
  author: Master Agent
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

```bash
grep -n '"term"' src/indiestack/db.py | head -20
```

Always grep BEFORE adding — Python dicts silently override duplicate keys with the last value.

### 2. Probe queries offline

```python
PYTHONPATH=src python3 -c "
from scripts.test_search_routing import route_query
queries = ['your queries here']
for q in queries:
    cat, via = route_query(q)
    print(f'{q!r:40s} -> {cat!r} (via {via!r})')
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

### 5. Validate

```bash
PYTHONPATH=src python3 scripts/validate_synonyms.py
PYTHONPATH=src python3 scripts/test_search_routing.py
```

Both must pass with zero failures and zero duplicates before committing.

### 6. Add test cases

Add corresponding test cases to the `TEST_CASES` list in `scripts/test_search_routing.py`. Update the test count comment in `.orchestra/departments/backend/CLAUDE.md`.

## Common Gap Categories to Probe

These areas historically generate `raw_first` misses:

| Domain | Tokens to test |
|--------|---------------|
| AI frameworks 2025-2026 | pydantic ai, agno, mastra, smolagents |
| Local LLM tooling | lm studio, koboldai, llms, llmstxt |
| LLMOps / eval | trulens, braintrust, weave, ragas |
| AI safety | llamaguard, rebuff, guardrails, prompt injection |
| Data engineering | etl, elt, dbt, airbyte, fivetran |
| Edge/serverless | val town, deno deploy, cloudflare workers |
| Standards | llms.txt, a2a, mcp, openai agents |

## Commit Style

```
fix: N search routing gaps — [short description] (M/M pass)
```

Example: `fix: 6 search routing gaps — llms.txt, koboldai, pydantic ai (541/541 pass)`
