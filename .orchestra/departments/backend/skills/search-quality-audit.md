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
| Local LLM tooling | lm studio, koboldai, llms, llmstxt, local ai |
| LLMOps / eval | trulens, braintrust, weave, ragas |
| AI safety | llamaguard, rebuff, guardrails, prompt injection |
| Data engineering | etl, elt, dbt, airbyte, fivetran |
| Edge/serverless | val town, deno deploy, cloudflare workers |
| Standards | llms.txt, a2a, mcp, openai agents |
| Token collision traps | cloud native (native→frontend), commit message (message→queue), local ai (local→raw_first) |
| Async programming | async runtime, coroutine, coroutines, event loop (event→message collision) |
| LLM inference | speculative decoding, kv cache, quantization, token budget |
| Browser extension dev | firefox addon, chrome devtools extension, manifest v3 |
| CI/CD pipeline | pipeline runner, pipeline agent, runner token |
| Code generation | typescript codegen, graphql codegen, openapi codegen |
| Internal developer portals | backstage idp, service catalog, developer portal |
| NLP text processing | stemmer, lemmatizer, tokenizer, pos tagger |
| Game dev primitives | physics engine, pathfinding, collision detection, shader, raycasting |
| Security research | decompiler, bytecode, disassembler, binary analysis, reverse engineering |
| Policy / compliance tooling | policy as code, rego, conftest, opa, cedar |
| DSL / parser tools | dsl, antlr, peg grammar, langium, chevrotain |
| Screen / capture utilities | screen capture, screen share, screen recorder |
| AST / code introspection | abstract syntax tree, syntax tree, ast parser |
| ZKP / cryptography | zero knowledge proof, zkp library, zk snark, zk stark, circom, snarkjs, halo2 |
| Embedded / IoT / RTOS | rtos, freertos, zephyr, arduino, platformio, micropython, yocto, esp32, cocoapods |
| Distributed transactions | two phase commit, distributed transaction, atomikos, seata, saga pattern |
| Secret management | credential rotation, account rotation, key rotation, vault secrets, doppler secrets |
| Property-based testing | pbt framework, hypothesis testing, fast-check, proptest, quickcheck |
| WASM serverless | spin framework, fermyon, wasm serverless, wasmtime, wasmer, component model |
| Code intelligence / syntax | tree sitter, syntax highlighter, code highlighter, highlighting library |
| Remote dev environments | remote development, codespace, devpod, devcontainer, cloud ide |
| AI agent patterns | computer use api, tool calling, structured output, prompt template, llm routing |
| Data observability | data lineage, data catalog, data observability, data quality, data contract |
| Service mesh / networking | service mesh, envoy proxy, istio, linkerd, ebpf networking |
| Software supply chain | sbom generator, slsa provenance, sigstore, cosign, syft, grype |
| Chaos / resilience testing | chaos engineering, fault injection, chaos monkey, litmus chaos, toxiproxy |
| API contract testing | pact contract, wiremock stub, consumer driven contract, prism mock |
| Plural-form gaps | fixtures (→testing), formatters, notifiers — always probe the plural when singular is mapped |
| FaaS spaced forms | function as a service, function as service — "faas" maps but long-form bigrams often missing |
| Data pipeline verbs | data export, data import, data transform — "data" + verb bigrams often raw_first |
| Automation qualifier | automation testing (→testing, not ai), automation workflow (→background) — "automation" bare→ai causes misfires |

### Pattern 16 — "conflicting first/second token" probe queries

For each synonym in `_CAT_SYNONYMS`, test it as the SECOND word of a two-word query where the first word is a common modifier. If the first token has its own synonym routing to a different category, the result is a collision. Examples found:

- `"cloud native"` → "native"→frontend (React Native) collides with intended "devops"
- `"commit message"` → "message"→message-queue collides with intended "developer"
- `"privacy analytics"` → "privacy"→security collides with intended "analytics" (already fixed)
- `"video editor"` → "video"→media collides with intended "creative" (already fixed)

Probe by running: `for q in ["cloud X", "commit X", "hot X", "local X"]: route_query(q)`

## Commit Style

```
fix: N search routing gaps — [short description] (M/M pass)
```

Example: `fix: 6 search routing gaps — llms.txt, koboldai, pydantic ai (541/541 pass)`
