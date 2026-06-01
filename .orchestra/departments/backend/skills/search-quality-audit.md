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

## Pattern: Orphaned Second-Token Poisoning

When the **first token has no synonym** (raw_first), the **second token becomes the effective routing signal**. If that second token maps to the *wrong* category, the query is silently mis-routed — unlike raw_first dead zones, these queries *do* return a category, just the wrong one.

Probe: for any two-word tech concept, check (a) whether token-0 is in `_CAT_SYNONYMS`; if NOT, check (b) whether token-1 maps to the right category. High-risk second tokens: `"contract"→testing`, `"proof"→(missing)`, `"recorder"→(missing)`, `"pipeline"→(missing)`.

```python
# Check token-0 then token-1 individually
route_query("smart")     # raw_first → second-token risk
route_query("contract")  # testing → wrong for "smart contract" queries
route_query("smart contract")  # bigram needed
```

Historically found: "smart contract"→testing (was developer), "streaming pipeline"→media (was message), "html to pdf"→frontend (was file) via stop-word "to" removal.

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
| Web3 / blockchain | smart contract, zk proof, zk rollup, hardhat, foundry |
| Screen tools | screen recorder, screen capture (developer tools) |
| Media pipeline | streaming pipeline, data pipeline (message vs media) |
| Document conversion | html to pdf, markdown to html (file management) |
| Frontend naming variants | full stack (vs full-stack), micro-frontend (vs micro frontend), drag-and-drop (vs drag and drop), site generator (vs static site generator), frontend framework (framework is stop word) |
| Streaming collision | streaming api (streaming→media steals it; add video/audio streaming bigrams at pos 0 as guards) |
| Replay/session collision | replay debugging (replay→monitoring; session replay→analytics is correct) |
| Semantic prefix collision | semantic caching (semantic→search steals it; "semantic cache" bigram works but not gerund -ing form) |
| Source map variants | source map (source is stop word — spaced bigram dead), source-map (hyphen), source-maps (hyphen plural) |
| Formal verification | formal verification, formal methods, tla plus, alloy analyzer, dafny, coq proof, theorem prover, model checker |
| HTML email builders | html email builder, mjml alternative, react email template, email html template |
| Versioned tool names | jinja2, ejs, handlebars (versioned/named forms often missing when generic bare form is mapped) |
| ML primitives | tensor library, tensor ops, jax autodiff, cosine similarity, text similarity, graph neural network (category collision with graph→database) |
| Vector math | cosine distance (distance→maps collision), cosine similarity, similarity search, nearest neighbor (nn→?) |
| Code signing | code signing tool, artifact signing, binary signing (signing→security already fixed; watch for new collision patterns) |
| Flow control / resilience | backpressure, backpressure queue, load shedding, bulkhead, exponential backoff |
| Distributed primitives | mutex lock, distributed mutex, distributed semaphore, pessimistic locking |
| Package registries | pypi mirror, private pypi, devpi, cargo registry, verdaccio, nexus repository |
| Stream processing SQL | streaming sql, flink sql, ksql, spark sql streaming, kafka streams sql |
| Code navigation | code navigation, code intelligence, semantic code search, code map, codesearch |
| Human-in-the-loop AI | hitl workflow, human loop annotation, human feedback loop, active learning labeling |
| Classical NLP libraries | spacy (fixed probe 145), nltk (fixed), gensim, stanza, corenlp, stanfordnlp, flair nlp |
| POS tagging / linguistics | pos tagger (fixed), stemmer (fixed), lemmatizer (fixed), dependency parsing, named entity recognition |
| Architecture patterns | architecture bare (fixed probe 145), ddd, domain driven design, event storming, cqrs, saga pattern |
| .js suffix forms | react.js (fixed probe 145), vue.js (fixed), node.js (fixed) — period preserved by str.split(); check other versioned forms: ember.js, backbone.js |
| WebAssembly / WASM | wasm runtime, wasm module, webassembly toolkit, wasi, emscripten |
| Accessibility testing | a11y, wcag checker, axe accessibility, screen reader testing, color contrast checker |
| FinOps / cloud cost | finops tool, cloud cost optimization, infracost, kubecost, cloud cost explorer |
| API versioning | api versioning, api deprecation, semantic versioning, changelog automation, breaking change detection |
| CRDT / collaboration | crdt library, operational transformation, yjs alternative, automerge |
| OpenTelemetry ecosystem | otel collector, opentelemetry collector, otel exporter, otel sdk, trace propagation |
| gRPC tooling | grpc gateway, grpc reflection, grpc web, grpc mock |
| Browser extension dev | chrome extension sdk, webextension, extension boilerplate, manifest v3 |
| Service mesh | istio alternative, linkerd, consul connect, kuma mesh, cilium service mesh |
| Meta-framework spaced forms (probe 146 pattern) | solid start, qwik city, turbo stream, turbo rails — when base token is in _FRAMEWORK_QUERY_TERMS it gets stripped from meaningful_for_cat; spaced bigram pre-pass fires before stripping and solves it. Always probe all three forms: spaced / hyphenated / compounded |
| Hotwire / Rails ecosystem | turbo frame, turbo native, hotwire native, stimulus controller, importmap rails |
| Astro ecosystem | astro island, astro component, astro integration, astro view transitions |
| Remix routing | remix loader, remix action, remix nested routes, remix resource route |
| SvelteKit pages | sveltekit endpoint, sveltekit hooks, sveltekit adapter, sveltekit load |
| Bun ecosystem | bun runtime, bun bundler, bun test, bun shell — "bun" has no single-token synonym; all compound forms at risk |
| Deno ecosystem | deno deploy, deno kv, deno fresh, deno jsx — "deno" single-token check first |
| AI agent frameworks 2026 | composio, julep, e2b, morph (cloud), bolt diy, replit agent, devin alternative |
| LLM routing / gateway | llm proxy, llm gateway, llm load balancer, llm router, model router |
| Prompt management | prompt registry, prompt template, prompt version, prompt hub, promptfoo alternative |
| Multimodal AI | vision model, audio model, speech recognition api, tts api, stt api |
| Structured output | json schema llm, instructor library, outlines llm, guided generation |
| Memory / context stores | agent memory, long term memory llm, conversation memory, vector memory |

## Commit Style

```
fix: N search routing gaps — [short description] (M/M pass)
```

Example: `fix: 13 search routing gaps — snowpack, llamaguard, llms.txt + 10 more (166/166 pass)`
