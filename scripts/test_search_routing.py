#!/usr/bin/env python3
"""
Local search routing simulator — validates _CAT_SYNONYMS mappings without production API.

Simulates the category-routing logic from db.py's search_tools() to verify that
queries route to the expected category. Run after any _CAT_SYNONYMS change to catch
regressions before they reach production.

Usage:
    python3 scripts/test_search_routing.py
    python3 scripts/test_search_routing.py --verbose       # show all results
    python3 scripts/test_search_routing.py --query "state management"  # test one query

Exit code 0 = all pass, 1 = failures found.

── ROUTING AUDIT PROBE PATTERNS (for autonomous improvement loops) ──────────────
When hunting for routing gaps, these query forms are historically tricky:

1. "X engine / X orchestrator" — the category for a tool type may differ from
   the tool's primary verb. "workflow"→ai but "workflow engine"→background.
   Probe: "[verb] engine [tool]", "[verb] orchestrator [tool]"

2. "headless X" — "headless"→cms fires for most headless queries. Always verify:
   "headless browser", "headless chrome", "headless test" → testing
   "headless ui", "headless component" → frontend
   "headless scraper", "headless web" → developer
   "headless cms" → cms (correct, the regression guard)

3. Brand abbreviations — verify short abbrevs have their own token: "og" (open
   graph), "mcp", "cdn", "dns". If missing, "raw_first" fires with no category boost.

4. "rich X" — "rich"→cli fires for Python Rich library; "rich text" must override.

5. "workflow" category split — automation tools (n8n/Make/Zapier)→ai, but engine/
   orchestrator/runtime tools (Temporal/Inngest/Restate)→background.

6. "open X Y" — "open" is in _FTS_STOP_WORDS, so "open graph" can't form a bigram.
   Must use the bare token ("og") or compound form ("opengraph") instead.

7. Domain/infrastructure tokens — check "registrar", "domain", "nameserver": these
   often have no synonym so raw_first fires.

8. "X lookup / X address" — bare noun queries where the noun is a technical term
   with no _CAT_SYNONYMS entry. "ip lookup" → raw_first "ip". "country detection"
   → raw_first "country". Probe: probe the first token of infra/geo queries.

9. "X formatting / X parsing" — utility library queries where the noun carries
   all the routing weight. "number formatting", "date parsing", "currency format".
   These live in developer-tools. Probe: "[noun] formatting", "[noun] parsing".

10. "X map" compound analytics terms — "map"→maps fires for the second word, but
    visual analytics tools use "map" as a noun modifier ("heat map", "click map",
    "scroll map"). Need bigrams to override. Always probe: "heat map", "click map",
    "scroll map", "[visual] map [tool]". Similarly, "X graph" vs "graph database".

11. "X click" / "X drag" / "X rich" — single-word tokens with popular developer tools:
    "click"→cli (Click Python), "drag"→? "rich"→cli (Rich library). Compound forms like
    "click map", "rich text", "drag drop" need bigrams to override. Probe any analytics
    or UI term whose first token collides with a named-tool synonym.

12. "code X" compound queries — "code" alone has no _CAT_SYNONYMS entry (falls back to
    raw_first). For queries where "code" is the first token, a bigram is REQUIRED.
    Covered bigrams: "code generation", "code gen", "code completion", "code review"
    (developer). Probe: "code [noun]" where [noun] is a standalone tool type — if the
    bigram is missing, raw_first fires and no category boost is applied.

13. "Hyphenated-form only" traps — a hyphenated entry like "two-factor" only fires when
    the query is written with a hyphen. The space-separated form "two factor" falls to
    raw_first because hyphen removal happens at FTS normalisation, NOT before bigram
    matching. Always add BOTH "foo bar" (space) and "foo-bar" (hyphen) for compound
    authentication / security terms. Probe: type the term with a space; if raw_first
    fires, the spaced bigram is missing.

14. "Category word as first token" collisions — some tokens are strong synonyms for a
    specific category BUT appear as the FIRST word of a query targeting a DIFFERENT
    category. Examples: "static"→frontend clashes with "static analysis" (testing);
    "design"→design-creative clashes with "design system" (frontend). Always probe
    "[synonym] [qualifier]" pairs where the qualifier changes the category intent. Fix
    with a compound bigram that overrides the single-token mapping.

15. "Noun coordination/concurrency patterns" — database concurrency primitives like
    "optimistic locking", "distributed lock", "distributed locking" have no single-token
    mapping ("optimistic", "distributed" are raw_first). Similarly, "pull request",
    "zero downtime" are DevOps concepts with no token mapping. Probe any architecture
    pattern term by splitting on the first word and checking its raw token mapping.

16. "Conflicting first/second token synonyms" — both tokens have valid synonyms but
    they disagree. The first token wins, routing to the wrong category. Examples:
    "privacy analytics" → "privacy"→security but "analytics"→analytics (want analytics);
    "cookie consent" → "cookie"→authentication but "consent"→security (want security).
    Pattern: any query where first-token and second-token map to different categories.
    Fix: add a bigram that overrides. Probe: for each category boundary, enumerate
    tool-type nouns that could appear after a first-token synonym from a different cat.

17. "Leading data/administrative noun with no synonym" — common in analytics/data-
    engineering queries: "data catalog", "data governance", "data lineage". "data" has
    no _CAT_SYNONYMS entry → raw_first fires with no category boost. These tools live
    in Analytics & Metrics. Similarly check: "schema", "spec", "model", "graph" as
    leading tokens in data-engineering contexts. Probe: "data [noun]" where [noun] is
    a data-engineering or BI concept — if raw_first fires, add the bigram.

18. "Stop-word bigram trap" — a bigram like "source map" CAN NEVER fire because "source"
    is in _FTS_STOP_WORDS; it's stripped before bigram matching. Same for "open source",
    "open graph", "best [tool]", etc. Always check BOTH tokens of a proposed bigram
    against _FTS_STOP_WORDS before adding it. Fix: use the compound form ("sourcemap")
    or map the surviving token directly. Probe: write the bigram, split it, check each
    half against _FTS_STOP_WORDS. If either half is a stop word, the bigram is dead.
    Key stop words to watch: "source", "open", "best", "free", "new", "fast", "simple".

19. "Performance/quality noun collision" — "performance"→monitoring correctly handles
    APM queries, but "performance testing" (k6, Locust, Gatling, Artillery) should route
    to Testing. Similarly, "quality"→testing is broad — "code quality" tools may be in
    Developer Tools. Any time a quality/perf noun also names a specific subcategory of
    tool, probe "[noun] testing/benchmark/load" to check if the bigram is needed.
    Fixed: "performance testing", "performance test" → testing (May 2026).

20. "Synthetic/real modifier collisions" — "synthetic"→ai (synthetic data tools) and
    "real"→api (real-time tools) are correct single-token mappings, BUT compound forms
    like "synthetic monitoring" and "real user monitoring" target Monitoring. Probe any
    category-specific adjective as a first token before a second token from a DIFFERENT
    category. "synthetic [monitoring term]", "real [analytics term]" are the key traps.
    Fixed: "synthetic monitoring" → monitoring, "user monitoring" → monitoring (May 2026).

21. "Column store / key-value store collisions" — "store"→frontend (state management)
    is correct for React/Redux queries but wrong for database storage queries. Bigrams:
    "column store" → database (ClickHouse, DuckDB). Check: "key value store" (both
    "key" and "value" tokens exist but "key value" bigram may be missing). Probe any
    compound where "store" is the second token and the first token names a DB paradigm.

22. "Template/scaffold ambiguity" — "template"→boilerplate and "starter"→boilerplate are
    correct for starter-kit queries, but "template engine" refers to rendering libraries
    (Handlebars, Mustache, Jinja, Nunjucks) that live in Developer Tools. Similarly,
    "scaffold" is a boilerplate concept except "scaffolding tool" (code generation →
    developer). Probe: "[template|scaffold] [rendering noun]" vs "[template|scaffold]
    [starter noun]". Fixed: "template engine" → developer (May 2026).

23. "Dual raw_first dead zone" — queries where BOTH tokens are unmapped (raw_first fires
    for the first meaningful token with no category boost). These are invisible because
    no single token collision exists to alert you. Probe by splitting any compound
    developer term and checking each token individually: if both return raw_first, the
    query is a dead zone. Common dead zones to probe: "[adjective] [tool-type]" where
    the adjective is a modifier not yet in _CAT_SYNONYMS (graceful, incremental, atomic,
    idempotent, composable, reactive). Also check stop-word context loss: when a compound
    like "service catalog" loses its meaningful first token ("service") to stop-word
    stripping, the surviving token ("catalog") may also be unmapped. Probe: "service X",
    "application X", "software X" where X is a tool category noun — if X has no synonym,
    add it. Fixed: "service catalog"→devops, "pair programming"→ai, "graceful"→devops,
    "light mode"→frontend (May 2026).

24. "High-level concept bigrams for niche categories" — for newer/smaller categories
    (ai-standards, mcp-servers, boilerplates, localization), generic concept queries
    ("responsible ai", "red teaming", "ai benchmark") may use tokens that either (a)
    route to a more populous category via single-token fallback ("benchmark"→testing)
    or (b) hit a dead-end first token with no category match ("responsible", "red").
    Always probe high-level concept queries for newer categories: check if the first
    token has a _CAT_SYNONYMS entry, and if that entry points to the right category.
    If not, add the bigram. Probe: "[concept] [tool/framework/suite/alternative]" for
    each sub-domain of ai-standards (safety, governance, benchmarking, red-teaming).
    Fixed: "responsible ai"→ai standards, "red teaming"→ai standards,
    "ai benchmark"→ai standards, "ai safety"→ai standards, "ai governance"→ai standards
    (May 2026).

25. "Plural/compound form gaps" — a token mapped in singular/compound form but NOT in
    its plural or spaced-variant form. "sitemap"→seo was mapped but "sitemaps" wasn't.
    "flamegraph"→monitoring was mapped but "flame graph" (spaced) wasn't — "graph" then
    fired as the first meaningful token, routing to database. Pattern: for each recently
    added single-token synonym, also add the plural (append 's') and the spaced form if
    the token is compound. Also probe "finops" / "cloud cost" style FinOps/cost-mgmt
    queries: these tools (Infracost, OpenCost, Vantage) live in DevOps but "cloud" and
    "finops" had no synonym. Probe: "cloud cost", "cloud pricing", "finops", "infracost"
    — if any hit raw_first or the wrong category, add bare token or bigram. Fixed:
    "sitemaps"→seo, "flame graph"→monitoring, "finops"/"cloud cost"→devops (May 2026).

26. "Category-prefix poisoning" — a word that correctly maps to category A (e.g.
    "saas"→boilerplate, "crm"→crm, "devops"→devops) becomes the first meaningful token
    in a compound query where the SECOND token indicates a completely different category.
    "saas metrics" → "saas"→boilerplate fires, not analytics. "crm analytics" → "crm"→crm
    fires, not analytics (acceptable here, but pattern still applies). Probe: for any
    category-key word, check "[word] analytics", "[word] metrics", "[word] dashboard",
    "[word] monitoring" — if the first token routes to the wrong category, add the bigram.
    Also applies to stop-word + meaningful-token pairs: "time tracking" can never fire as
    a bigram because "tracking" is in _FTS_STOP_WORDS. In that case, add named-tool
    synonyms (toggl, harvest, clockify) instead of the bigram. General fix strategy:
    (a) add bigram for the compound if both tokens survive stop-word filtering, or
    (b) add direct tool-name synonyms when the compound includes a stop word.
    Fixed: "saas metrics"→analytics, "time tracker" bigram + toggl/harvest/clockify→project,
    "expense"/"expenses"→invoicing, "documentation"→documentation (May 2026).

27. "Security / AI / analytics compound dead zones" — advanced compound patterns that each
    involve two unmapped tokens (dual raw_first) or a token that correctly maps to the wrong
    category when context changes. Examples: (a) "zero trust" spaced form — "zerotrust"
    (compound) and "zero-trust" (hyphenated) were mapped but "zero trust network X" routed
    via "network"→monitoring since neither spaced token had a mapping. (b) "reactive" bare
    token — tools like RxJS, MobX, Valtio are reactive but the word "reactive" had no
    synonym so queries like "reactive programming" fired raw_first. (c) "hallucination"
    bare token — LLM hallucination detection tools (Guardrails AI, RAGAS, Giskard) were
    unreachable since "hallucination" had no mapping. (d) "data quality" bigram —
    "quality"→testing fires for code-quality tools but "data quality" should route to
    analytics where Monte Carlo, Soda, Great Expectations live. (e) "schema registry"
    bigram — "schema"→developer fires first but schema registry tools (Confluent, Karapace)
    belong in message-queue ecosystem. Probe: "[adjective/acronym] [category noun]" where
    the adjective is a new domain concept without a synonym. Fixed: "zero trust"→security
    bigram, "ztna"→security, "reactive"→frontend, "hallucination"→ai,
    "data quality"→analytics bigram, "schema registry"→message bigram (May 2026).

28. "TLD-variant domain queries" — users paste tool domain names (make.com, supabase.com,
    railway.app) into search. These become single tokens with the TLD attached and never
    match bare tool names ("make", "supabase", "railway"). Always add TLD-variant entries
    (.com/.io/.app/.so/.tech) alongside bare tool names in _CAT_SYNONYMS. Probe:
    "<toolname>.com alternative" — if UNROUTED, the TLD form is missing.
    Fixed (probe pattern 43, May 2026): make.com, render.com, railway.app, supabase.com,
    vercel.com, planetscale.com, neon.tech, turso.tech, pocketbase.io, clerk.com,
    auth0.com, workos.com, resend.com, loops.so, posthog.com, plane.so, cal.com,
    netlify.com, heroku.com.

29. "Category-prefix poisoning for security" — tokens like "container" and "docker"
    correctly route to DevOps for infra queries, but compound queries like "container
    scanning", "docker security", "container vulnerability" target Security Tools (Trivy,
    Grype, Snyk). The first token wins and sends users to the wrong category. Fix: add
    compound bigrams that override the single-token devops mapping for security-intent
    compound forms. Fixed: "container scanning/security/vulnerability"→security,
    "docker security/vulnerability"→security (probe pattern 44, May 2026).

30. "Spaced form missing for hyphenated/compound synonyms" — a synonym added as
    "supply-chain" (hyphenated) and "supplychain" (compound) misses the natural
    space-separated form "supply chain" because neither bare token ("supply", "chain")
    has a mapping and the router never falls back to try the spaced bigram implicitly.
    Always add all three forms for critical compound terms. Fixed: "supply chain"→security
    bigram (probe pattern 44, May 2026).

31. "Bare noun dead zones for niche security concepts" — abstract security nouns like
    "threat" have no single-token mapping because they're infrequent enough to be
    overlooked in synonym audits. "threat detection" and "threat modeling" both hit
    raw_first. Fix: add the bare noun as a synonym if it's unambiguously tied to one
    category. "threat" in developer tool context exclusively means security. Fixed:
    "threat"→security (probe pattern 44, May 2026).

32. "SaaS category prefix collision with payments" — "saas"→boilerplate fires for any
    "saas X" compound query, including "saas billing", "saas payments", "saas subscription"
    which should route to Payments (Stripe, Polar, LemonSqueezy, Chargebee). Probe any
    category keyword as a first token before billing/payment/subscription second tokens.
    Fixed: bigrams "saas billing"/"saas payments"/"saas subscription"→payments
    (probe pattern 44, May 2026). Note: "saas metrics"→analytics was fixed in probe 26.

33. "Named tool dead zones in covered categories" — when a category has bare synonyms
    (e.g. "consent"→security) but the specific tool names are not mapped, "cookiebot
    alternative" still fires raw_first because "cookiebot" is first and maps to nothing.
    The second token "alternative" has no mapping either, so the bigram fails too.
    Probe: for each covered category, enumerate major tool names and check each one
    directly. Don't assume that mapping "consent"→security means all consent tools
    are reachable — named-tool bare tokens are required. Fixed: cookiebot, osano,
    onetrust, usercentrics, locize, lokalise, phrase, transifex (probe 46, May 2026).

34. "High-strength bare token overriding a GitOps qualifier" — when a tool name maps
    to one category (e.g. "flux"→ai for FLUX.1 image model) but the SAME name is used
    for a completely different tool in a different category (FluxCD, a CNCF GitOps
    operator), bare token collision means all "flux X" queries land in the wrong category
    even when a disambiguating qualifier is present ("cd", "gitops"). Always add
    bigrams "[toolname] [qualifier]" to override high-strength bare-token mappings.
    Fixed: "flux cd"→devops, "flux gitops"→devops (probe 46, May 2026).

35. "Privacy / data-protection dead zones" — PII and compliance technical terms are
    often unmapped because they don't match existing category keywords. The tokens
    ("pii", "hmac", "masking", "anonymization", "residency") are practitioner terms
    but not tool category words, so neither single-token nor bigram mappings exist by
    default. Strategy: enumerate the privacy/data-protection practitioner vocabulary
    and check each term: (a) PII-related: "pii", "pii detection", "pii redaction",
    "data masking", "data anonymization"; (b) Compliance/jurisdiction: "data residency",
    "data sovereignty", "gdpr tooling"; (c) Cryptographic auth: "hmac", "request
    signing", "webhook signature". All of these route to Security Tools. Fixed in
    probe 50 (May 2026). Probe pattern: "personally identifiable information", "data
    masking tool", "hmac library", "request signing aws" — if raw_first fires, the
    bare token or bigram is missing.

36. "Protocol-name disambiguation" — some protocol/standard names collide with existing
    category keywords. "matrix protocol" fires "protocol"→mcp (wrong; Matrix is a
    decentralized messaging protocol, not an MCP server). "graph ql" (space-separated)
    fires "graph"→database (wrong; should be api). Strategy: for any well-known protocol
    that contains a token already mapped to a different category, add a bigram with the
    protocol's disambiguating qualifier. Pattern: "[protocol-name] [qualifier]" bigrams
    take precedence over bare-token synonyms. Always probe both the compound form
    ("graphql") and the spaced form ("graph ql"), since users may type either. Fixed:
    "graph ql"→api, "matrix protocol"→social (probe 50, May 2026).

37. "Team messaging dead zones" — self-hosted/alternative team messaging tools (Mattermost,
    Rocket.Chat, Zulip) live in Developer Tools, but bare "slack" / "discord" have no
    synonym (alternative is stripped by _FTS_STOP_WORDS so "slack alternative" reduces
    to bare "slack"). The generic compound "team messaging" also has no bigram mapping.
    Strategy: probe "[well-known chat tool] alternative" queries by stripping the stop
    word and checking if the bare tool name maps anywhere. Also probe "team messaging",
    "team chat", "group messaging" as generic queries. Note: adding bare "slack"→developer
    risks collisions with "slack oauth"→authentication and "slack notification"→notifications
    — prefer the compound bigram "team messaging"→developer over bare-tool mapping.
    Fixed: "team messaging"→developer (probe 50, May 2026).

38. "Short-form / gerund variant gaps for bigram families" — when a bigram family is
    added (e.g. "llm evaluation", "llm-evaluation", "llm benchmark", "llm-benchmark"),
    the short form ("llm eval") and the gerund form ("llm benchmarking") are often
    overlooked. The first token ("llm"→ai) then wins, routing to the wrong category.
    Strategy: after adding any bigram family, also add (a) the 4-letter abbreviation if
    the second token has a common short form ("evaluation"→"eval", "generation"→"gen"),
    and (b) the gerund form of the second token ("-ing" suffix). Similarly, check
    "ai evaluation" vs "ai eval" — if "ai eval" is mapped but "ai evaluation" is not,
    add the full-word variant. Always probe both short and long forms before committing.
    Fixed: "llm eval"→ai standards, "llm benchmarking"→ai standards,
    "ai evaluation"→ai standards, "evals benchmark"→ai standards (probe 51, May 2026).

39. "Self-hosted dual raw_first dead zone" — "self hosted" and "self-hosted" are very
    common developer queries (searching for self-hostable alternatives to SaaS tools),
    but both tokens ("self", "hosted") have no individual _CAT_SYNONYMS entry so
    raw_first fires with no category boost (Pattern 23). Strategy: add (a) the spaced
    bigram "self hosted"→devops, (b) the hyphenated single token "self-hosted"→devops,
    (c) the gerund "self-hosting"→devops, and (d) "self host"→devops. Route to DevOps &
    Infrastructure since self-hosting implies deployment/infrastructure decisions.
    Fixed: "self hosted", "self-hosted", "self hosting", "self host" → devops (probe 51,
    May 2026).

40. "Shell bare-token dead zones" — "zsh" and "bash" are common shell names that appear
    in CLI tool queries ("zsh alternative", "bash scripting tool") but had no synonyms.
    "fish" (Fish Shell) was already mapped but the other major shells weren't. Strategy:
    after mapping a named tool in a category, probe its peer tools in the same family —
    if Fish Shell→cli is mapped, also probe Zsh and Bash. Fixed: "zsh"→cli, "bash"→cli
    (probe 52, May 2026).

41. "Stop-word prefix dropping first token" — when a query's first word is a stop word
    (e.g. "on" in "on call"), the meaningful token ("call") becomes the first term that
    the router checks. If "call" has no synonym, raw_first fires. Strategy: when adding
    a hyphenated compound ("on-call"→monitoring), also probe the space-separated form
    after stop-word stripping — if the surviving first token ("call") has no synonym,
    add it directly. Fixed: "call"→monitoring (bare token for "on call" queries after
    "on" stripped; probe 52, May 2026).

42. "License compliance dead zone" — "license" as a bare token had no _CAT_SYNONYMS
    entry, so "license checker" and "open source license scanner" fired raw_first. (Note:
    "open" and "source" are both in _FTS_STOP_WORDS, leaving bare "license".) License
    compliance tools (FOSSA, SPDX tooling, LicenseChecker) belong in Security Tools.
    Fixed: "license"→security, "fossa"→security (probe 52, May 2026).

43. "Same-token collision between testing and security" — "e2e"→testing is correct for
    "e2e testing playwright" but wrong for "e2e encryption library". When a token is
    shared between two categories, the category with higher query volume wins the bare-
    token mapping; the lower-volume category needs bigrams. Strategy: for any token that
    correctly maps to category A, probe "[token] [B-concept]" forms to find cases where
    B-context queries need a bigram override. Fixed: "e2e encryption"→security and
    "e2e encrypted"→security bigrams (override bare "e2e"→testing for security queries;
    probe 52, May 2026).

44. "Codegen bigram swallowing first-token route" — when a query has an API-layer tool
    at position 0 followed by "code generator"/"code generation" at positions 1-2, the
    bigram at pos 1 fires before the single-token at pos 0 is ever checked. The
    algorithm scans bigrams forward from position 0; if "tool code" is not in the dict,
    it falls through to "code generator" at the next position. Strategy: for any bigram
    family X that routes to category A (e.g. "code generator"→ai-dev), probe
    "[domain-tool] code" where domain-tool is a well-known term in a DIFFERENT category.
    If the result is wrong, add "[domain-tool] code"→correct-category as a pos-0 bigram
    that fires first. Fixed: "openapi code"→api, "swagger code"→documentation,
    "graphql code"→api, "protobuf code"→developer (probe 53, May 2026).

45. "realtime database vs realtime api" — bare "realtime"→api is correct for
    "realtime api websocket" but wrong for "realtime database firebase" (Firebase
    Realtime DB, Supabase Realtime, ElectricSQL). The two contexts share the first
    token. Strategy: add a bigram "[context] database"→database to route the DB
    variant correctly while leaving the bare token for the API category. Fixed:
    "realtime database"→database (probe 53, May 2026).

46. "Named-concept collision — contract testing vs smart contracts" — "contract"→testing
    (Pact consumer-driven contract testing) fires incorrectly for smart-contract /
    blockchain queries where the word order is "[adjective] contract". Strategy: probe
    "[modifier] [token]" where modifier is a category-specific adjective (here "smart")
    and add a bigram that overrides the bare-token mapping. Fixed: "smart contract"→
    developer, "smart contracts"→developer (probe 53, May 2026).

47. "AI Dev Tools precision — bare 'ai' vs 'ai dev'" — tokens like "cursor", "windsurf",
    "copilot" were mapped to bare "ai", which boosts BOTH "AI & Automation" AND
    "AI Dev Tools" (both category names contain the substring "ai"). Changing to "ai dev"
    uniquely targets "AI Dev Tools" via LOWER(c.name) LIKE '%ai dev%'. Strategy: for
    any AI coding assistant or IDE tool, always use "ai dev" not bare "ai" to get a
    precise category boost. Fixed: cursor/windsurf/copilot → "ai dev" (probe 54, May 2026).

48. "Brand-prefix collision — 'github copilot' dead zone" — "github" alone maps to devops
    (GitHub Actions/CI), which fires first for "github copilot alternative" and routes to
    the wrong category. The second token "copilot"→ai dev never fires since the first
    synonym wins. Strategy: add a bigram for the full brand name that overrides the
    misleading first-token routing. Probe: "[big-tech-tool] [product-name]" where
    big-tech-tool has an existing synonym pointing to a different category. Fixed:
    "github copilot"→ai dev (probe 54, May 2026).

49. "AI IDE dead zone — 'ai' prefix + 'ide' bare token" — "ide" maps to developer
    (VS Code, Zed, Neovim), which is correct for non-AI contexts, but "ai ide" queries
    target AI-enhanced IDEs (Cursor, Windsurf, Aide) in AI Dev Tools. The first
    meaningful token "ai" has no synonym, so "ide"→developer fires. Strategy: add a
    bigram "ai ide"→"ai dev" so the compound query routes correctly. Probe: "ai [X]"
    where X has a correct single-token mapping to a non-AI category; if the "ai" prefix
    changes the intent, the bigram is needed. Fixed: "ai ide"→ai dev (probe 54, May 2026).

50. "File hosting dead zone — 'hosting' prefix overreach" — "hosting"→devops correctly
    routes infrastructure hosting queries, but "file hosting service" should land in
    File Management (MinIO, Backblaze B2, Cloudflare R2). The bare first token "file" has
    no synonym so "hosting"→devops fires at pos 1. Strategy: add bigram "file hosting"→
    file to override. Probe: "file [X]" where X has a synonym pointing to a different
    category. Fixed: "file hosting"→file (probe 54, May 2026).

51. "'ai [X]' wrong-subcategory routing — second token wins when 'ai' is unmapped" —
    "ai" has no _CAT_SYNONYMS entry, so for any "ai [X]" query the SECOND meaningful
    token fires. This is correct when the second token's category matches AI intent
    (e.g. "ai workflow"→"workflow"→ai ✓), but fails when X has a non-AI category
    mapping: "ai tracing"→"tracing"→monitoring (wrong; LLM tracers like LangSmith live
    in AI Dev Tools), "ai observability"→"observability"→monitoring (wrong; LLM
    observability is AI Dev Tools), "ai deployment"→"deployment"→devops (wrong; AI model
    serving is AI & Automation). Strategy: probe every "ai [X]" query where X has a
    non-AI category mapping, and add the bigram when the AI-prefixed version targets a
    different sub-domain. Key LIKE targets: "ai dev" for AI Dev Tools, "ai" for AI &
    Automation. Fixed: "ai tracing"→ai dev, "ai observability"→ai dev,
    "ai deployment"→ai (probe 55, May 2026).

52. "'context management' frontend collision — 'context' first-token overreach" —
    "context"→frontend (React Context API) correctly routes React context queries, but
    "context management" in 2026 predominantly refers to LLM context window management
    (MemGPT, Mem0, AI memory tools) which live in AI & Automation. The existing bigrams
    "context window", "context engineering", "context length" cover specific LLM-context
    compound forms but "context management" was missing. Strategy: whenever a token has
    a broad category mapping (frontend, developer, etc.) and a common "ai" compound form
    exists for a DIFFERENT target category, add the compound bigram explicitly. Check
    the full list of "context [noun]" forms: window, engineering, length, management,
    compression — all should route to AI, not frontend. Fixed: "context management"→ai
    (probe 55, May 2026).

53. "Spaced-form gap in a synonym family" — when a compound security concept has
    hyphenated, compact, and gerund forms mapped but the natural spaced form is missing,
    'raw_first' fires with no category boost. "redteam"→ai standards, "red-team"→ai
    standards, "red teaming"→ai standards were all mapped, but "red team" (two words,
    no hyphen, no gerund) fell through to raw_first "red" which has no category match.
    Strategy: for any concept family with multiple variant entries, explicitly enumerate
    ALL surface forms: [compact] [hyphenated] [spaced] [gerund]. Probe the spaced form
    of every security/AI-standards concept that has only hyphenated or gerund coverage.
    Fixed: "red team"→ai standards (probe 55, May 2026).

54. "Stop-word stripping reveals hidden first-token collision" — when a stop word sits
    between two content tokens and is stripped, two unrelated tokens become adjacent and
    form an unexpected bigram. "static APPLICATION security testing" → strip "application"
    → meaningful = ["static", "security", "testing"]. Now "static" fires first → frontend
    (wrong: should be Security Tools). Fix: add the bigram that spans the now-adjacent
    tokens AFTER stop-word removal ("security testing"→security), so it fires at pos 1-2
    and overrides the earlier single-token match at pos 0. General pattern: any time a
    stop word sits between two content tokens where each token maps to a DIFFERENT category,
    stripping the stop word can create a new first-token collision. Probe: think of
    common query forms "[category-A-word] [stop-word] [category-B-word]" and check which
    fires first. Fixed: "security testing"→security overrides "static"→frontend for
    SAST/DAST queries (probe 61, May 2026).

55. "Short-form / abbreviation gap for multi-word tool names" — tools with long names
    get queried by their abbreviated prefix even when only the full compound form is
    mapped. "pr automation" → "pr" unmapped, "automation"→ai fires (wrong: PR bots are
    DevOps). "mono repo" spaced → "mono" unmapped, raw_first fires (wrong: monorepo is
    mapped but only as one token). Strategy: whenever a well-known compound is added,
    also add the common abbreviation and the space-separated variant. Probe: take each
    compound synonym and split it — does each half have its own mapping? If not, and
    agents commonly use the half-form, add the standalone or bigram. Fixed:
    "mono repo"→developer, "pr automation"→devops, "commit lint"→devops,
    "dev server"→frontend (probe 61, May 2026).

56. "Named-SaaS-tool collision — bare UI token misfires via commercial product synonym"
    — when a bare token is claimed by a well-known SaaS product (via an exact synonym)
    but agents also use that token as a generic UI-component term. Classic case: bare
    "modal"→ai (Modal.com serverless Python) fires for UI queries like "modal component
    react" which should route to frontend. Detection: grep _CAT_SYNONYMS for bare tokens
    that point to a category that doesn't match the UI component meaning. Strategy: add a
    bigram "[component type] component" or "[component type] window" that fires before
    the bare token collision. Pattern also applies to: "toast"→notifications (correct for
    toast notification; but "toast UI editor" should → frontend — bigram "toast editor"
    needed if queried), "graph"→database (correct for graph DB; but "graph component"
    → analytics via bare "graph" — bigram "graph component"→analytics if needed). Always
    check: does the token's category make sense for a "[token] component" query? If not,
    add override bigrams. Fixed: "modal component"/"modal window"→frontend (probe 63,
    May 2026).

57. "Category-semantic mismatch — tool class routed to wrong high-level bucket"
    — a bare token maps to a plausible but wrong category because the token's primary
    meaning overlaps two buckets. Three patterns found: (a) "storybook"→testing (wrong;
    Storybook is a component development environment, not a test runner — changed to
    frontend); (b) component UI tool with a bare noun owned by a media/file bucket
    (e.g., "image"→media makes "image cropper" misroute — add bigram before bare token);
    (c) raw_first dead zone where no token has any mapping (e.g., "custom element" bare
    "custom" is unmapped — add the compound bigram). Strategy: for any agent query with
    a clear expected category that misfires, check which token fires (via route_query --query)
    then add a targeted bigram before it. Fixed: "storybook"→frontend, "image cropper"→
    frontend, "pdf viewer"→frontend, "custom element"→frontend (probe 64, May 2026).

58. "Realtime-collaboration dead zones — unmapped OT/CRDT concept tokens + stop-word
    bigram trap" — realtime collaboration concept terms use academic/architectural words
    ("operational transform", "shared editing", "presence awareness", "live cursors") that
    lack _CAT_SYNONYMS entries. Because these words are technical-context-specific and
    not tool names, they're commonly overlooked in synonym audits. All four misfired to
    raw_first (dead zone). Strategy: when covering a cross-cutting tool category like
    realtime collaboration, enumerate the key architectural concept terms, not just the
    tool names. Probe: "operational [noun]", "shared [editing/workspace]", "presence
    [noun]", "live [noun]". Also found: "multi model database" where bare "model"→ai
    fires before "database"→database — the "multi" prefix has no synonym so the ai
    override isn't blocked. Fix: add bigram "multi model"→database so it fires before
    bare "model"→ai. STOP-WORD TRAP: "presence tracking" bigram CANNOT fire — "tracking"
    is in _FTS_STOP_WORDS. For any proposed bigram where the second token looks like a
    gerund or action verb, check _FTS_STOP_WORDS first: tracking, running, managing are
    all stripped. If the bigram is dead, rely on a surviving third token or add the bare
    first-token synonym if it's unambiguous enough. Fixed: "operational transform"→api,
    "shared editing"→api, "presence awareness"→api, "live cursors"→api,
    "multi model"→database (probe 65, May 2026).

59. "Named-tool first-token overreach — single CLI/framework name as common UI verb or
    noun" — when a popular tool uses a generic word as its name (Python "click", the
    npm masked-input library "masked", etc.) and that word is also a natural UI/UX term,
    the bare token maps to the tool's category rather than the UI concept category.
    Classic instances found in probe 73:
      - "click"→cli (Python Click) misfires for "right click menu" (Frontend) and
        "click heatmap" (Analytics). Bare "click" can't be remapped without breaking
        Click framework routing; must use bigrams at position 0.
      - "image"→media (media server) misfires for "image upload" and "image editor"
        (both Frontend UI components). Add compound bigrams that fire before bare "image".
      - "upload"→file misfires for "file upload react" (Frontend react-dropzone/FilePond).
        Add "file upload"→frontend bigram (fires before bare "upload"→file at pos 0).
      - "number"→developer misfires for "number input component" and "number format react"
        (both Frontend UI widgets). Add bigrams "number input"→frontend, "number format"→frontend.
    Strategy: for any token T that maps to category A, probe:
      (a) "[qualifier] T [suffix]" — "right click menu", "file upload react"
      (b) "T [noun]" — "click heatmap", "upload component"
      (c) "T [UI-pattern]" — "number input", "masked input"
    For each mismatch, add the compound bigram to override. Also probe the bare token
    against the most common UI/UX context words: component, widget, input, picker,
    editor, map, tracking, heatmap. NOTE: "click tracking" CANNOT use a bigram because
    "tracking" is in _FTS_STOP_WORDS — this is a known dead zone (document and skip).
    Fixed: "right click"/"click outside"→frontend, "click heatmap"→analytics,
    "file upload"/"image upload"/"image editor"→frontend,
    "number input"/"number format"→frontend,
    "masked"/"masked input"→frontend,
    "shader"/"glsl"/"opengl"→frontend (WebGL bare tokens),
    "photo crop"→frontend (probe 73, May 2026).
"""

import sys
import re
import argparse
from pathlib import Path

# Load constants from db.py without triggering async machinery
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from indiestack.db import _CAT_SYNONYMS, _FTS_STOP_WORDS, _FRAMEWORK_QUERY_TERMS


def route_query(query: str) -> tuple[str, str]:
    """
    Simulate the category-routing logic from search_tools() in db.py.

    Returns (cat_term, matched_via) where:
    - cat_term: the synonym value (e.g. "authentication", "frontend")
    - matched_via: the token that triggered the match, or "raw_first" / "none"
    """
    # Step 1: Tokenise and filter stop words
    meaningful = [t for t in query.lower().split() if t not in _FTS_STOP_WORDS]

    # Step 2: Filter framework qualifier terms (don't use them for category)
    meaningful_for_cat = [t for t in meaningful if t not in _FRAMEWORK_QUERY_TERMS]
    if not meaningful_for_cat:
        meaningful_for_cat = meaningful  # fallback: use all

    # Step 3: Find first term (or bigram) with a known synonym — bigrams have priority
    # at each position so "load balancing" beats "load"→testing, etc.
    # Pre-pass: check bigrams on meaningful (before framework stripping) to catch
    # "react form", "react query" etc. where stripping the qualifier causes mis-routing.
    syn_term = None
    for i in range(len(meaningful) - 1):
        bigram = f"{meaningful[i]} {meaningful[i + 1]}"
        if bigram in _CAT_SYNONYMS:
            syn_term = bigram
            break
    if syn_term is None:
        for i, tok in enumerate(meaningful_for_cat):
            if i + 1 < len(meaningful_for_cat):
                bigram = f"{tok} {meaningful_for_cat[i + 1]}"
                if bigram in _CAT_SYNONYMS:
                    syn_term = bigram
                    break
            if tok in _CAT_SYNONYMS:
                syn_term = tok
                break
    if syn_term:
        return _CAT_SYNONYMS[syn_term], syn_term

    # Step 4: No synonym — fall back to first meaningful term (raw match against category name)
    raw_cat = meaningful_for_cat[0] if meaningful_for_cat else query.lower()
    return raw_cat, "raw_first"


# ── Test cases ────────────────────────────────────────────────────────────────────────────────────────────────
# Format: (query, expected_cat_term_fragment)
# expected_cat_term_fragment must be a substring of the routed cat_term.
# A query routing to "authentication" passes if expected is "auth" or "authentication".

TEST_CASES: list[tuple[str, str]] = [
    # Core categories
    ("auth for nextjs", "authentication"),
    ("login system", "authentication"),
    ("oauth provider", "authentication"),
    ("payments stripe alternative", "payments"),
    ("billing subscriptions", "payments"),
    ("email sending transactional", "email"),
    ("newsletter platform", "email"),        # "newsletter" → email (email-marketing covers newsletters)
    ("database postgres", "database"),
    ("vector database", "database"),
    ("monitoring uptime", "monitoring"),
    ("analytics tracking", "analytics"),
    ("forms surveys", "forms"),
    ("scheduling booking", "scheduling"),
    ("cms headless", "cms"),
    ("customer support chat", "support"),    # "support" → support (customer-support category)
    ("seo tools", "seo"),
    ("file storage upload", "file"),
    ("crm sales pipeline", "crm"),
    ("developer tools sdk", "api"),          # "developer" is stop word; "sdk" → api (acceptable)
    ("design ui", "frontend"),              # "ui" → frontend (UI components/libraries)
    ("feedback nps", "feedback"),
    ("social media scheduling", "social"),   # requires "social" key added May 2026
    ("project management kanban", "project"),   # "project" is stop word; "management"→project (fixed May 2026)
    ("landing page builder", "landing"),
    ("api gateway", "api"),
    # Frontend
    ("state management react", "frontend"),
    ("bundler vite webpack", "frontend"),
    ("build tool esbuild", "frontend"),
    ("react component library", "frontend"),
    ("react form library", "frontend"),          # "react form" bigram pre-pass; was wrongly → forms
    ("react form validation", "frontend"),       # same fix — React Hook Form, Formik
    ("react query setup", "frontend"),           # "react query" bigram pre-pass; was wrongly → database
    ("react query v5", "frontend"),              # TanStack Query v5 queries
    ("javascript framework", "frontend"),
    ("css framework tailwind", "frontend"),
    ("svelte alternative", "frontend"),
    # AI / LLM
    ("llm gateway proxy", "ai"),
    ("local llm inference", "ai"),
    ("agent framework", "ai"),
    ("vibe coding tool", "ai"),
    ("kimi k2 alternative", "ai"),
    ("notebooklm alternative", "ai"),
    ("ai browser automation", "testing"),   # "browser" → testing (correct: browser automation IS testing)
    ("computer use api", "ai"),
    # AI Dev Tools
    ("mcp server setup", "mcp"),
    ("boilerplate saas starter", "boilerplate"),
    ("cursor rules setup", "ai"),
    ("ai coding assistant", "ai"),
    # AI Standards / Eval
    ("garak llm scanner", "ai standards"),
    ("lm-eval setup", "ai standards"),
    ("arc-agi benchmark", "ai standards"),
    ("model evaluation framework", "ai standards"),  # bigram "model evaluation" → AI Standards & Specs
    ("ai eval harness", "ai standards"),             # bigram "ai eval" → AI Standards & Specs
    ("ai evals tool", "ai standards"),               # bigram "ai evals" → AI Standards & Specs
    ("safety eval framework", "ai standards"),       # bigram "safety eval" → AI Standards & Specs
    ("capability eval suite", "ai standards"),       # bigram "capability eval" → AI Standards & Specs
    # DevOps / Infra
    ("hosting deployment", "devops"),
    ("docker kubernetes", "devops"),
    ("paas provider", "devops"),
    ("vps hosting", "devops"),
    ("reverse proxy nginx", "devops"),
    ("ddos protection", "security"),
    ("mergify alternative", "devops"),
    ("gitstream pr automation", "devops"),
    ("linearb engineering metrics", "devops"),
    ("merge queue tool", "devops"),           # "merge queue" bigram → devops (Mergify, github merge queues), not "queue"→background
    # Testing
    ("testing e2e playwright", "testing"),
    ("reviewdog ci setup", "testing"),
    # Search / Caching / Queue
    ("full-text search", "search"),
    ("caching redis", "caching"),
    ("message queue kafka", "message"),
    # Security
    ("secrets management vault", "security"),
    ("vulnerability scanning", "security"),
    # Realtime / API
    ("realtime websocket", "api"),
    ("real time chat", "api"),
    ("rate limiting api", "api"),
    ("webhook delivery", "api"),
    # Database — time-series (series→database added May 2026; "time"→api removed to fix false routing)
    ("time series database", "database"),
    ("time series data influxdb", "database"),
    # Background jobs
    ("cron job scheduler", "background"),
    ("task queue worker", "background"),     # bigram "task queue" → background-jobs (more accurate than "task"→developer)
    # PR review (added May 2026)
    ("pr-agent alternative", "ai"),
    ("qodo-merge setup", "ai"),
    ("ai pr review tool", "developer"),      # "review" → developer; acceptable for AI code review tools
    # MCP registries / servers
    ("smithery mcp", "mcp"),
    ("context7 mcp", "mcp"),
    ("docker mcp setup", "mcp"),            # bigram "docker mcp" → Docker MCP Toolkit → MCP Servers
    ("pulsemcp analytics", "mcp"),
    # Misc
    ("media server video", "media"),        # requires "media" → "media" fix (was "file")
    ("maps geolocation", "maps"),
    ("logging log management", "logging"),
    ("push notification service", "notifications"),
    ("i18n localization", "localization"),
    ("cli command line", "cli"),
    ("documentation api docs", "documentation"),  # "documentation" now mapped; routes to docs (Mintlify, Docusaurus)
    ("feature flag toggle", "feature"),
    # Product adoption / onboarding (added May 2026)
    ("appcues alternative", "feedback"),
    ("userpilot alternative", "feedback"),
    ("chameleon io product adoption", "feedback"),
    ("userflow onboarding", "feedback"),
    ("product tour library javascript", "frontend"),  # "tour" → frontend
    # Behavior analytics / session recording (added May 2026)
    ("mouseflow heatmap", "analytics"),
    ("smartlook session recording", "analytics"),
    # Observability / tracing (complementary terms)
    ("opentelemetry alternative", "monitoring"),
    ("distributed tracing jaeger", "monitoring"),     # "jaeger" → monitoring
    # Monorepo / package management
    ("monorepo build tool", "developer"),
    ("turborepo alternative", "developer"),
    # Code quality / linting — live in testing-tools category
    ("linting eslint alternative", "testing"),
    ("code formatter biome", "testing"),              # biome → testing (intentional)
    # Secrets / environment management
    ("secrets management doppler", "security"),
    # Error tracking
    ("error tracking sentry", "monitoring"),          # "error" → monitoring
    # IaC / infra
    ("infrastructure as code terraform", "devops"),
    # GraphQL / API
    ("graphql api builder", "api"),
    # Headless CMS
    ("headless cms sanity alternative", "cms"),
    # Project management — verifies "management"/"manager" route correctly after May 2026 fix
    ("project manager tool", "project"),            # "manager" → project (fixed)
    ("state management tool", "frontend"),          # "state" fires first → frontend (correct)
    ("state manager zustand", "frontend"),          # "state" fires first → frontend (correct)
    # ORMs and database tooling
    ("drizzle orm database", "database"),           # "drizzle" → database
    ("prisma migrations", "database"),              # "prisma" → database
    # API / tRPC
    ("trpc api server", "api"),                     # "trpc" → api
    ("graphql federation", "api"),                  # "graphql" → api
    # Payments
    ("stripe payment alternative", "payments"),     # "stripe" → payments
    ("paddle billing", "payments"),                 # "paddle" → payments
    # Email
    ("email template builder", "email"),            # "email" → email
    ("transactional email resend", "email"),        # "transactional" → email
    # Auth
    ("supabase auth alternative", "database"),       # "supabase" fires first → database (Supabase is a BaaS/database platform)
    ("oauth2 server", "authentication"),             # "oauth2" → authentication
    # Error tracking
    ("error tracking tool", "monitoring"),          # "error" → monitoring
    # IaC
    ("pulumi infrastructure", "devops"),            # "pulumi" → devops
    # Time-series database (series→database added May 2026; time→api removed)
    ("time series database", "database"),           # "series" → database (not "time" → api)
    ("time series data influxdb", "database"),      # "series" → database
    # Multi-agent AI
    ("multi-agent framework", "ai"),                # "multi-agent" → ai
    ("multi-agent orchestration", "ai"),            # "multi-agent" fires first, beats "orchestration"→background
    # MCP registries / discovery
    ("mcp registry search", "mcp"),                 # "mcp" → mcp
    # RAG / document processing
    ("document chunker python", "database"),        # "document" → database (known: fires before "chunker"→ai)
    ("hybrid search bm25 vector", "search"),        # "hybrid" → search
    # Repo-for-LLM tools
    ("repomix alternative", "ai dev"),              # "repomix" → ai dev
    # E-signature / forms
    ("esignature api", "forms"),                    # "esignature" → forms
    ("digital signature tool", "forms"),            # "signature" → forms
    # Data engineering / ETL (added May 2026)
    ("etl pipeline tool", "background"),            # "etl" → background
    ("data pipeline orchestration", "background"),  # "pipeline" → background
    ("data warehouse alternative", "database"),     # "warehouse" → database
    ("apache airflow alternative", "background"),   # "airflow" → background
    ("dbt alternative", "background"),              # "dbt" → background (data transform = background-jobs)
    # Static site generators / Jamstack
    ("static site generator", "frontend"),          # "static" → frontend
    ("jamstack framework", "frontend"),             # "jamstack" → frontend
    # Desktop app frameworks
    ("electron alternative", "frontend"),           # "electron" → frontend
    ("tauri app framework", "frontend"),            # "tauri" → frontend
    # Usage-based / metered billing — now routed to payments via bigrams (probe 67)
    ("usage based billing", "payments"),            # bigram "usage based"→payments (Metronome, Orb, Lago)
    ("metered billing api", "payments"),            # bigram "metered billing"→payments
    # Screen recording / UX analytics (bigram "screen recording" → analytics)
    ("screen recording tool", "analytics"),         # bigram "screen recording" → analytics
    ("ux recording tool", "analytics"),             # "recording" → analytics
    # Feedback & Reviews
    ("user feedback widget", "feedback"),           # "feedback" → feedback
    ("customer feedback tool", "feedback"),         # "feedback" → feedback
    ("feedback collection", "feedback"),            # "feedback" → feedback (first token)
    # Bigram routing fixes (added May 2026 — these previously routed to wrong categories)
    ("session replay tool", "analytics"),           # bigram "session replay" beats "session"→authentication
    ("user session replay", "analytics"),           # bigram "session replay" fires for mid-query too
    ("load balancer tool", "devops"),               # bigram "load balancer" beats "load"→testing
    ("load balancing nginx", "devops"),             # bigram "load balancing" beats "load"→testing
    ("token bucket rate limit", "api"),             # bigram "token bucket" beats "token"→authentication
    ("sliding window algorithm", "api"),            # bigram "sliding window" → api (rate limiting pattern)
    ("step functions alternative", "background"),   # bigram "step functions" → background-jobs
    ("key rotation policy", "security"),            # bigram "key rotation" → security
    ("version control system", "devops"),           # bigram "version control" → devops
    ("dead letter queue", "message"),               # bigram "dead letter" → message queue
    ("semantic cache llm", "caching"),              # bigram "semantic cache" beats "semantic"→search
    ("dark launch strategy", "feature"),            # bigram "dark launch" beats "dark"→frontend
    ("key value database", "caching"),              # bigram "key value" → caching (no individual match)
    # Bigram routing fixes (added May 2026 — session recording, product adoption, in-app changelog)
    ("session recording tool", "analytics"),        # bigram "session recording" beats "session"→authentication
    ("smartlook session recording", "analytics"),   # named tool first, but also validates bigram fallback
    ("product adoption platform", "feedback"),      # bigram "product adoption" beats individual tokens
    ("user onboarding software", "feedback"),       # bigram "user onboarding" beats "onboarding"→frontend
    ("in-app changelog widget", "feedback"),        # bigram "in-app changelog" beats "changelog"→devops
    ("product changelog tool", "feedback"),         # bigram "product changelog" beats "changelog"→devops
    # Bigram routing fixes (added May 2026 — block goose, docker mcp)
    ("block goose coding agent", "ai dev"),         # spaced bigram "block goose" beats "goose"→database
    ("goose block agent", "ai dev"),                # reversed spaced bigram fires correctly
    ("docker mcp toolkit", "mcp"),                  # spaced bigram "docker mcp" beats "docker"→devops
    # Bigram routing fixes (added May 2026 — status page, image generation, code gen)
    ("status page tool", "monitoring"),             # bigram "status page" beats "status" raw_first (no category match)
    ("status page alternative", "monitoring"),      # bigram "status page" handles alt query
    ("status-page open source", "monitoring"),      # hyphenated form
    ("image generation model", "ai"),               # bigram "image generation" beats "image"→media
    ("image generation api", "ai"),                 # bigram "image generation" beats "image"→media
    ("text to image model", "ai"),                  # "text image" bigram (after stop-word removal of "to") → ai
    ("code generation tool", "ai dev"),             # bigram "code generation" → AI Dev Tools
    ("code gen api", "ai dev"),                     # bigram "code gen" → AI Dev Tools
    ("code completion tool", "ai dev"),             # bigram "code completion" → AI Dev Tools (Codeium, Tabnine)
    ("code completion open source", "ai dev"),      # bigram fires before raw_first fallback
    # Bigram routing fixes (added May 2026 — ai image, ai gateway, sales pipeline, contact management, website builder)
    ("ai image generator", "ai"),                   # bigram "ai image" beats "image"→media for generative AI queries
    ("ai gateway litellm", "ai"),                   # bigram "ai gateway" beats "gateway"→api for LLM proxy queries
    ("sales pipeline software", "crm"),             # bigram "sales pipeline" beats "pipeline"→background for CRM queries
    ("sales tool tracker", "crm"),                  # single "sales"→crm routes sales tracking queries correctly
    ("contact management tool", "crm"),             # bigram "contact management" beats "management"→project
    ("website builder tool", "landing"),            # bigram "website builder" → Landing Pages (Carrd, Webflow)
    ("portfolio site builder", "landing"),          # single "portfolio"→landing routes portfolio queries correctly
    # Regression guard — "ai" prefix must NOT override established non-AI categories
    ("ai browser automation", "testing"),           # "browser"→testing still fires (no broad "ai" single token)
    ("ai pr review tool", "developer"),             # "review"→developer still fires (no broad "ai" single token)
    # Health check — "health" token routes to Monitoring & Uptime
    ("health check library", "monitoring"),         # bare "health"→monitoring for healthcheck queries
    ("healthcheck endpoint", "monitoring"),         # compound form "healthcheck"→monitoring
    ("health-check middleware", "monitoring"),      # hyphenated "health-check"→monitoring
    # Social login — "social login/auth" bigrams override "social"→social-media for OAuth queries
    ("social login provider", "authentication"),    # bigram "social login" beats "social"→social
    ("social auth library", "authentication"),      # bigram "social auth" beats "social"→social
    ("social sign in flow", "authentication"),      # bigram "social sign" beats "social"→social
    # Regression — bare "social media" still routes correctly
    ("social media scheduling", "social"),          # "social"→social still fires for social media queries
    # Context window bigrams (added May 2026 — beat "context"→frontend for LLM context queries)
    ("context window management", "ai"),            # bigram "context window" beats "context"→frontend
    ("context window limit model", "ai"),           # bigram "context window" fires before "limit"→api
    ("context engineering tool", "ai"),             # bigram "context engineering" beats "context"→frontend
    ("llm context engineering", "ai"),              # bigram "context engineering" fires even with "llm" stripped
    ("context length optimization", "ai"),          # bigram "context length" beats "context"→frontend
    # Regression — bare "context" still routes to frontend for React context API queries
    ("react context provider", "frontend"),         # "context"→frontend still fires for React Context API
    ("context api nextjs", "frontend"),             # "context"→frontend fires for context API queries
    # 2026 term regressions — verify key 2026-era synonyms don't break
    ("vibe coding workflow", "ai"),                 # "vibe"→ai routes vibe-coding queries correctly
    ("deepseek r1 local", "ai"),                   # "deepseek"→ai routes DeepSeek model queries
    ("llamastack inference server", "ai"),          # "llamastack"→ai routes LlamaStack queries
    ("mcp server sdk", "mcp"),                      # "mcp"→mcp routes MCP server queries
    ("llm evaluation harness", "ai standards"),     # bigram "llm evaluation" → AI Standards & Specs
    ("llm benchmark comparison", "ai standards"),   # bigram "llm benchmark" → AI Standards & Specs
    # Angular state management libraries (added May 2026)
    ("ngrx state management", "frontend"),          # "ngrx" → frontend (Angular Redux-style state)
    ("ngxs angular store", "frontend"),             # "ngxs" → frontend (NGXS Angular state)
    ("akita angular state", "frontend"),            # "akita" → frontend (Akita state management)
    # GPT-4.1 family (OpenAI, April 2025 — added 142nd pass)
    ("gpt41 alternative", "ai"),                    # compact form routes to AI & Automation
    ("gpt-4-1 api", "ai"),                          # hyphenated form routes to AI & Automation
    ("gpt4-1 pricing", "ai"),                       # mixed form routes to AI & Automation
    ("gpt41-mini alternative", "ai"),               # GPT-4.1 mini compact → AI & Automation
    ("gpt-4-1-mini vs claude", "ai"),               # GPT-4.1 mini hyphenated → AI & Automation
    ("gpt41-nano cost", "ai"),                      # GPT-4.1 nano compact → AI & Automation
    ("gpt-4-1-nano alternative", "ai"),             # GPT-4.1 nano hyphenated → AI & Automation
    # GPT-4o mini (OpenAI, July 2024 — added 142nd pass)
    ("gpt4o-mini alternative", "ai"),               # compact-hyphenated → AI & Automation
    ("gpt-4o-mini pricing", "ai"),                  # fully hyphenated → AI & Automation
    ("gpt4omini setup", "ai"),                      # no-separator compound → AI & Automation
    # 2026 AI models batch — new entries added May 2026 (256th pass)
    # OpenAI reasoning models
    ("o3-mini alternative", "ai"),                  # o3-mini (Jan 2025) small reasoning model → AI & Automation
    ("o4-mini alternative", "ai"),                  # o4-mini (April 2025) fast reasoning → AI & Automation
    ("gpt5 alternative", "ai"),                     # GPT-5 → AI & Automation
    ("gpt-5 vs claude", "ai"),                      # GPT-5 hyphenated → AI & Automation
    ("codex alternative", "ai"),                    # OpenAI Codex agent (2025 relaunch) → AI & Automation
    # Anthropic Claude versions
    ("claude37 sonnet", "ai"),                      # Claude 3.7 compact form → AI & Automation
    ("claude-3-7 alternative", "ai"),               # Claude 3.7 hyphenated form → AI & Automation
    ("claude4 alternative", "ai"),                  # Claude 4 compact → AI & Automation
    ("claude-opus alternative", "ai"),              # Claude Opus tier → AI & Automation
    # Google models
    ("gemini25 pro", "ai"),                         # Gemini 2.5 compact → AI & Automation
    ("gemini-2-5 flash alternative", "ai"),         # Gemini 2.5 hyphenated → AI & Automation
    ("gemma3 setup", "ai"),                         # Gemma 3 open-weight → AI & Automation
    # Meta Llama 4
    ("llama4 alternative", "ai"),                   # Llama 4 compact → AI & Automation
    ("llama4-scout setup", "ai"),                   # Llama 4 Scout variant → AI & Automation
    ("llama4-maverick alternative", "ai"),          # Llama 4 Maverick variant → AI & Automation
    # xAI Grok
    ("grok2 alternative", "ai"),                    # Grok 2 → AI & Automation
    ("grok3 alternative", "ai"),                    # Grok 3 → AI & Automation
    # Mistral variants
    ("devstral alternative", "ai"),                 # Mistral Devstral code LLM → AI & Automation
    ("magistral alternative", "ai"),                # Mistral Magistral reasoning model → AI & Automation
    # DeepSeek variants
    ("deepseek-r1 alternative", "ai"),              # DeepSeek-R1 reasoning model → AI & Automation
    # Amazon Nova
    ("amazon-nova alternative", "ai"),              # Amazon Nova family → AI & Automation
    # AI agent frameworks (2026)
    ("ag2 vs crewai", "ai"),                        # AG2/AutoGen v2 multi-agent → AI & Automation
    ("beeai framework", "ai"),                      # IBM BeeAI agents → AI & Automation
    ("strands agents", "ai"),                       # AWS Strands SDK → AI & Automation
    ("spring-ai alternative", "ai"),                # Spring AI (Java LLM integration) → AI & Automation
    # AI IDE tools (2026)
    ("kiro alternative", "ai"),                     # Amazon Kiro AI IDE → AI & Automation
    ("firebase-studio vs cursor", "ai"),            # Firebase Studio AI IDE → AI & Automation
    # MCP Servers — tooling
    ("mcp-inspector setup", "mcp"),                 # MCP Inspector debug tool → MCP Servers
    ("mcpinspector debug", "mcp"),                  # MCP Inspector compound form → MCP Servers
    # Caching
    ("momento alternative", "caching"),             # Momento Cache serverless → Caching
    # AI modality forms
    ("text-to-speech api", "ai"),                   # TTS → AI & Automation (ElevenLabs, Coqui, Kokoro)
    ("text-to-image model", "ai"),                  # T2I → AI & Automation (Stable Diffusion, Flux)
    # Qwen3 (Alibaba, April 2026)
    ("qwen3 alternative", "ai"),                    # Qwen3 → AI & Automation
    # Rust-based JS/TS toolchain (2025-2026)
    ("rspack bundler alternative", "frontend"),     # Rspack — Rust webpack-compat bundler → Frontend
    ("swc transpiler setup", "frontend"),           # SWC — Rust JS/TS transpiler (Next.js) → Frontend
    ("rolldown vite bundler", "frontend"),          # Rolldown — Rust Rollup replacement (Vite 6) → Frontend
    ("oxc linter javascript", "frontend"),          # OXC — Oxidation Compiler Rust toolchain → Frontend
    ("farm build tool alternative", "frontend"),    # Farm — Rust web build tool → Frontend
    # JS runtimes (regression: bun/deno must NOT route to ai)
    ("bun runtime alternative", "frontend"),        # Bun — JS runtime + bundler → Frontend
    ("deno alternative nodejs", "frontend"),        # Deno 2 — secure JS/TS runtime → Frontend
    # LLM tool/function calling — AI paradigm for models invoking external tools
    ("tool calling api", "ai"),                     # "tool" is stop word → "calling"→ai → AI & Automation
    ("function calling openai", "ai"),              # "function calling" bigram → AI & Automation
    ("function calling alternative", "ai"),         # bigram form → AI & Automation
    # AI proxy — LLM proxy/gateway tools (LiteLLM, Portkey) must NOT route to devops
    ("ai proxy litellm", "ai"),                     # "ai proxy" bigram overrides "proxy"→devops → AI & Automation
    ("ai proxy server alternative", "ai"),          # bigram fires before "proxy" single token → AI & Automation
    # LLM token queries — "token" alone → authentication; bigrams route to AI & Automation
    ("token limit gpt4", "ai"),                     # "token limit" bigram overrides "token"→auth → AI & Automation
    ("token pricing openai", "ai"),                 # "token pricing" bigram overrides "token"→auth → AI & Automation
    # Knowledge base — RAG / vector knowledge base queries (previously raw_first → unrouted)
    ("knowledge base llm", "ai"),                   # "knowledge base" bigram → AI & Automation
    ("knowledge base chatbot", "ai"),               # bigram form → AI & Automation
    # Document QA — LLM document Q&A ("document" alone → database; bigram overrides)
    ("document qa tool", "ai"),                     # "document qa" bigram overrides "document"→database → AI & Automation
    ("document q&a chatbot", "ai"),                 # ampersand variant → AI & Automation
    # Search quality additions (May 2026 — 146th pass)
    # Server-Sent Events — long-form "server sent" bigram (sse→api was already mapped)
    ("server sent events library", "api"),          # "server sent" bigram → API Tools
    ("server-sent events nodejs", "api"),           # hyphenated → API Tools
    # Hypermedia — HTMX/Hotwire pattern (unmapped before this pass)
    ("hypermedia api framework", "frontend"),       # "hypermedia" → Frontend Frameworks
    # Connection string — DB config queries (unmapped before this pass)
    ("connection string postgres", "database"),     # "connection" → Database
    # Streaming LLM — fix "streaming"→media collision for AI streaming queries
    ("streaming llm response", "ai"),               # "streaming llm" bigram → AI & Automation
    ("llm streaming library", "ai"),                # "llm streaming" bigram → AI & Automation
    # Real zero-result queries from gap-queries-2026-04.json — fixed in 147th pass
    ("pass keys auth", "authentication"),           # "pass keys" bigram → Authentication (space-separated passkeys)
    ("snmp monitoring tool", "monitoring"),         # "snmp" → Monitoring & Uptime (SNMP protocol)
    ("go-feature-flag alternative", "feature"),     # "go-feature-flag" → Feature Flags (specific Go library)
    ("payroll api open source", "invoicing"),       # "payroll" → Invoicing & Billing
    ("article generation api", "ai"),               # "article generation" bigram → AI & Automation
    # Thin-category coverage pass — localization, cli, docs, notifications, logging, maps, etc.
    ("i18n library react", "localization"),
    ("translation management", "localization"),
    ("multilingual nextjs", "localization"),        # "multilingual" standalone token fix
    ("cli framework rust", "cli"),                  # "cli" standalone token fix; "rust"→api was winning
    ("tui builder", "cli"),                         # tui → cli
    ("terminal multiplexer", "cli"),
    ("docs site generator", "documentation"),
    ("push notification service", "notifications"),
    ("in-app notifications", "notifications"),
    ("push notifications mobile", "notifications"),  # reordered: "push" fires before "mobile"→frontend
    ("log management", "logging"),
    ("structured logging", "logging"),
    ("log aggregation", "logging"),
    ("geocoding api", "maps"),
    ("map tiles provider", "maps"),
    ("geolocation library", "maps"),
    ("booking calendar", "scheduling"),
    ("appointment scheduler", "scheduling"),
    ("kanban board", "project"),
    ("sprint planning tool", "project"),
    ("file storage upload", "file"),
    ("object storage s3", "file"),
    ("video streaming server", "media"),
    # Routing gaps fixed — eventstoredb, transactional outbox, leader election
    ("eventstoredb alternative", "message"),         # EventStoreDB → Message Queues (was raw_first)
    ("transactional outbox pattern", "background"),  # bigram overrides "transactional"→email → Background Jobs
    ("transactional outbox setup", "background"),    # bigram form → Background Jobs
    ("leader election service", "devops"),           # bigram "leader election" → DevOps (Zookeeper, etcd)
    ("leader election algorithm", "devops"),         # bigram form → DevOps & Infrastructure
    # MCP dept dog-fooding queries — verified routing, added as regression coverage
    ("sequential thinking mcp", "mcp"),             # MCP-specific tool → MCP Servers
    ("n8n alternative", "background"),              # workflow automation → Background Jobs
    ("jmeter alternative", "testing"),              # load/perf testing tool → Testing Tools
    ("appium alternative", "testing"),              # mobile test automation → Testing Tools
    ("localstack alternative", "devops"),           # AWS local emulation → DevOps & Infrastructure
    ("eza alternative", "cli"),                     # modern ls replacement → CLI Tools
    ("btop alternative", "cli"),                    # system monitor TUI → CLI Tools
    ("dlq setup", "message"),                       # dead-letter queue config → Message Queues
    ("event sourcing database", "message"),         # CQRS/ES pattern → Message Queues
    ("kv store for edge", "caching"),               # bigram "kv store" → Caching
    ("saga orchestration", "background"),           # Saga pattern → Background Jobs (Temporal, Restate)
    ("promql alternative", "monitoring"),           # Prometheus query lang → Monitoring & Uptime
    ("logql query", "logging"),                     # Loki query lang → Logging
    ("gemini2 alternative", "ai"),                  # Gemini 2 versioned → AI & Automation
    ("react-compiler setup", "frontend"),           # React 19 compiler → Frontend Frameworks
    ("karpenter vs cluster-autoscaler", "devops"),  # K8s autoscaling → DevOps & Infrastructure
    ("txt2img pipeline", "ai"),                     # text-to-image → AI & Automation
    ("speech-to-text library", "ai"),               # STT API → AI & Automation
    ("zookeeper alternative", "devops"),            # distributed coord → DevOps & Infrastructure
    # Routing gaps fixed — eventstoredb, transactional outbox, leader election, low/no-code, e-commerce
    ("eventstoredb alternative", "message"),         # EventStoreDB → Message Queues (was raw_first)
    ("transactional outbox pattern", "background"),  # bigram overrides "transactional"→email → Background Jobs
    ("transactional outbox setup", "background"),    # bigram form → Background Jobs
    ("leader election service", "devops"),           # bigram "leader election" → DevOps (etcd, ZooKeeper)
    ("leader election algorithm", "devops"),         # bigram form → DevOps & Infrastructure
    ("no code app", "developer"),                    # bigram "no code" beats raw_first → Developer Tools
    ("no code builder", "developer"),                # bigram form → Developer Tools (Webflow, Softr)
    ("low code tool", "developer"),                  # bigram "low code" beats raw_first → Developer Tools
    ("low code platform", "developer"),              # bigram form → Developer Tools (Retool, Budibase)
    ("e-commerce platform", "developer"),            # hyphenated beats raw_first → Developer Tools (Medusa, Saleor)
    ("e-commerce open source", "developer"),         # hyphenated + qualifier → Developer Tools
    # Routing fixes — language-prefixed ORM queries (language token was beating "orm"→database)
    ("typescript orm drizzle", "database"),          # bigram "typescript orm" → Database
    ("ts orm comparison", "database"),               # bigram "ts orm" → Database
    ("python orm async", "database"),                # bigram "python orm" → Database (SQLAlchemy, Tortoise)
    ("go orm gorm", "database"),                     # bigram "go orm" → Database (GORM, Ent)
    ("rust orm diesel", "database"),                 # bigram "rust orm" → Database (Diesel, SeaORM)
    # Routing fixes — serverless/edge database queries (serverless→devops / edge→devops was firing first)
    ("serverless database postgres", "database"),    # bigram "serverless database" → Database (Neon, PlanetScale)
    ("edge database sqlite", "database"),            # bigram "edge database" → Database (Turso, D1)
    # Routing fix — Vercel AI SDK (vercel→devops was firing before ai→ai-automation)
    ("vercel ai sdk alternative", "ai"),             # bigram "vercel ai" → AI & Automation
    ("vercel ai sdk setup", "ai"),                   # bigram form → AI & Automation
    # Routing fixes — headless browser/chrome queries routing to CMS via "headless"→cms
    ("headless browser puppeteer", "testing"),       # bigram "headless browser" → Testing Tools
    ("headless browser testing", "testing"),         # bigram form → Testing Tools
    ("headless chrome screenshot", "testing"),       # bigram "headless chrome" → Testing Tools
    ("headless chrome automation", "testing"),       # bigram form → Testing Tools
    ("headless test runner", "testing"),             # bigram "headless test" → Testing Tools
    # Routing fix — thumbnail has no synonym (raw_first with no boost)
    ("thumbnail generation api", "file"),            # "thumbnail" → File Management
    ("thumbnail resize api", "file"),                # "thumbnail" token → File Management
    # Routing fix — background removal routing to background-jobs via "background"→background
    ("background removal api", "ai"),                # bigram "background removal" → AI & Automation
    ("background removal python", "ai"),             # bigram form → AI & Automation
    # Routing fixes — "hot"/"live"/"tree" had no synonym; raw_first fired returning unmapped token
    ("hot reload dev server", "developer"),          # bigram "hot reload" → Developer Tools
    ("hot reload vite", "developer"),                # bigram form → Developer Tools
    ("live reload webpack", "developer"),            # bigram "live reload" → Developer Tools
    ("hot module replacement", "frontend"),          # bigram "hot module" → Frontend Frameworks
    ("tree shaking bundler", "frontend"),            # bigram "tree shaking" → Frontend Frameworks
    ("tree shaking webpack", "frontend"),            # bigram form → Frontend Frameworks
    # Routing fix — "schema migration" routed to developer via "schema"→developer token
    ("schema migration tool", "database"),           # bigram "schema migration" → Database
    ("schema migration flyway", "database"),         # bigram form → Database
    # Routing fix — "change data capture" routed to raw_first "change" with no mapping
    ("change data capture", "database"),             # bigram "change data" → Database
    ("change data capture tool", "database"),        # bigram form → Database
    # Routing fixes — embedded analytics and object relational mapper (added May 2026)
    ("embedded analytics react", "analytics"),       # bigram "embedded analytics" beats "embedded"→database
    ("embedded analytics dashboard", "analytics"),   # bigram form → Analytics & Metrics
    ("embedded bi dashboard", "analytics"),          # bigram "embedded bi" beats "embedded"→database
    ("embedded bi tool", "analytics"),               # bigram form → Analytics & Metrics
    # Regression — bare "embedded" still routes to database for embedded DB queries
    ("embedded database sqlite", "database"),        # "embedded"→database still fires for embedded DB
    ("object relational mapper python", "database"), # bigram "object relational" beats "object"→file
    ("object relational mapping", "database"),       # bigram form → Database
    # Regression — bare "object" still routes to file for object storage queries
    ("object storage minio", "file"),                # "object"→file still fires for object storage
    # Routing fixes — 12 thin-category gaps found in May 2026 audit
    # Landing pages — component queries had no synonym
    ("coming soon page", "landing"),        # bigram "coming soon" → Landing Pages
    ("coming soon builder", "landing"),     # bigram form → Landing Pages
    ("hero section builder", "landing"),    # bigram "hero section" → Landing Pages
    ("hero section react", "landing"),      # bigram form → Landing Pages
    # Newsletters — "ghost"→cms was firing for newsletter queries
    ("ghost newsletter alternative", "newsletters"),  # bigram "ghost newsletter" → Newsletters
    ("ghost newsletter platform", "newsletters"),     # bigram form → Newsletters
    # SEO — web vitals and page speed were routing wrong
    ("core web vitals", "seo"),             # bigram "web vitals" → SEO Tools (beats "vitals"→monitoring)
    ("web vitals monitoring", "seo"),       # bigram form → SEO Tools
    ("page speed test", "seo"),             # bigram "page speed" → SEO Tools (beats "test"→testing)
    ("page speed optimization", "seo"),     # bigram form → SEO Tools
    # Routing fixes — 7 thin-category gaps found in May 2026 audit
    # "seo" token itself was missing — all "seo X" queries fell through to "audit"→logging etc.
    ("seo audit tool", "seo"),              # "seo"→seo fires before "audit"→logging
    ("seo ranking factor", "seo"),          # "seo" unigram → SEO Tools
    ("seo checklist", "seo"),               # "seo" unigram → SEO Tools
    # Meta tags — "meta" was unmapped, raw_first fired
    ("meta tags generator", "seo"),         # bigram "meta tags" → SEO Tools
    ("meta tags nextjs", "seo"),            # bigram form → SEO Tools
    # XML sitemap — "xml"→developer was firing before "sitemap"→seo
    ("xml sitemap generator", "seo"),       # bigram "xml sitemap" beats "xml"→developer
    ("xml sitemap nextjs", "seo"),          # bigram form → SEO Tools
    # Meeting scheduler — "scheduler"→background was firing wrong for calendar scheduling
    ("meeting scheduler open source", "scheduling"),  # bigram "meeting scheduler" → Scheduling
    ("meeting scheduler app", "scheduling"),          # bigram form → Scheduling & Booking
    # Calendly — brand name unmapped, raw_first fired
    ("calendly alternative", "scheduling"), # "calendly"→scheduling → Scheduling & Booking
    ("calendly open source", "scheduling"), # token form → Scheduling & Booking
    # Help desk — bigram missing, raw_first "help" fired
    ("help desk software", "support"),      # bigram "help desk" → Customer Support
    ("help desk open source", "support"),   # bigram form → Customer Support
    # Coding tutorial — "coding"→ai dev was firing for learning platform queries
    ("coding tutorial platform", "learning"),  # bigram "coding tutorial" → Learning & Education
    ("coding tutorial site", "learning"),      # bigram form → Learning & Education
    # Routing fixes — headless UI/component library (bare "headless"→cms was firing; May 2026)
    ("headless ui component", "frontend"),           # bigram "headless ui" beats "headless"→cms
    ("headless ui react", "frontend"),               # bigram form → Frontend Frameworks
    ("headless ui vue", "frontend"),                 # bigram form → Frontend Frameworks
    ("headless component library", "frontend"),      # bigram "headless component" beats "headless"→cms
    ("headless component react", "frontend"),        # bigram form → Frontend Frameworks
    # Regression — bare "headless" still routes to cms for CMS queries
    ("headless cms nextjs", "cms"),                  # "headless"→cms still fires for actual CMS queries
    # Routing fix — data streaming was routing to media via bare "streaming"→media
    ("data streaming platform", "message"),          # bigram "data streaming" → Message Queues (Kafka, Redpanda)
    ("data streaming kafka", "message"),             # bigram form → Message Queues
    # Routing fixes — micro-prefixed queries
    # "micro service" can't form bigram ("service" is stop word) — compound form already works
    ("microservice framework", "api"),               # "microservice" unigram → API Tools (already mapped)
    ("microservices architecture", "api"),           # "microservices" unigram → API Tools (already mapped)
    # "micro frontend" bigram works ("frontend" is NOT a stop word)
    ("micro frontend framework", "frontend"),        # bigram "micro frontend" → Frontend Frameworks
    ("micro frontend react", "frontend"),            # bigram form → Frontend Frameworks
    # Auth routing fixes — "user management" was routing to project via "management"→project
    ("user management system", "authentication"),    # bigram "user management" → Authentication
    ("user management sdk", "authentication"),       # bigram form → Authentication
    ("account management portal", "authentication"), # bigram "account management" → Authentication
    # CIAM term — no token matched, now explicitly mapped
    ("ciam solution", "authentication"),             # "ciam" token → Authentication
    ("open source ciam", "authentication"),          # "ciam" fires in 3rd position → Authentication
    # Regression — "user authentication" still routes correctly via second token
    ("user authentication library", "authentication"), # "authentication" fires → Authentication (not broken)
    # Documentation routing fix — "syntax highlight" was routing to monitoring via "highlight"→monitoring
    ("syntax highlight library", "documentation"),   # bigram "syntax highlight" → Documentation
    ("syntax highlighting react", "documentation"),  # bigram form → Documentation
    # Regression — bare "highlight" still routes to monitoring (Highlight.io) when no overriding bigram
    ("highlight error tracking", "monitoring"),      # "highlight"→monitoring fires (no overriding bigram)
    # SEO — "og" token routes OG image generator queries (bare "og" = Open Graph abbreviation)
    ("og image tool", "seo"),                   # "og"→seo fires before "image"→media → SEO Tools
    ("og image generator react", "seo"),         # "og" unigram → SEO Tools
    # Frontend — "rich text" bigram overrides "rich"→cli for text editor queries
    ("rich text editor", "frontend"),            # bigram "rich text" → Frontend (TipTap, ProseMirror, Lexical)
    ("rich text component react", "frontend"),   # bigram form → Frontend Frameworks
    # Regression — bare "rich" still routes to CLI (Rich Python library)
    ("rich python terminal", "cli"),             # "rich"→cli still fires for Rich library queries
    # DevOps — "registrar" token routes domain registrar queries to DevOps & Infrastructure
    ("domain registrar alternative", "devops"),  # "registrar"→devops → DevOps & Infrastructure
    ("domain name registrar", "devops"),         # "registrar" fires in 3rd position → DevOps
    # Background Jobs — "workflow engine/orchestrator" bigrams override "workflow"→ai
    ("workflow engine temporal", "background"),      # bigram "workflow engine" → Background Jobs
    ("workflow engine open source", "background"),   # bigram form → Background Jobs
    ("workflow orchestrator temporal", "background"),# bigram "workflow orchestrator" → Background Jobs
    # Regression — "workflow automation" bigram now routes to background (probe 45 fix).
    # n8n IS a background-jobs tool, so this is the correct routing.
    ("workflow automation n8n", "background"),       # bigram "workflow automation"→background (probe 45)
    # Developer Tools — "headless scraper" bigrams override "headless"→cms
    ("headless scraper puppeteer", "developer"),     # bigram "headless scraper" → Developer Tools
    ("headless scraper library", "developer"),       # bigram form → Developer Tools
    ("headless web scraper", "developer"),           # bigram "headless web" → Developer Tools
    # Regression — "headless browser" still routes to testing (not developer)
    ("headless browser playwright", "testing"),      # "headless browser" bigram → Testing Tools
    # Social Media — "activity pub" bigram routes ActivityPub server queries
    ("activity pub server", "social"),               # bigram "activity pub" → Social Media
    ("activity pub implementation", "social"),       # bigram form → Social Media
    # DevOps — "content delivery network" bigram overrides "content"→cms
    ("content delivery network", "devops"),          # bigram "content delivery" → DevOps (CDN tools)
    ("content delivery cdn", "devops"),              # bigram form → DevOps & Infrastructure
    # Regression — bare "content" still routes to cms
    ("content management system", "cms"),            # "content"→cms still fires for CMS queries
    # Background Jobs — "reverse etl" bigram overrides "reverse"→devops
    ("reverse etl census", "background"),            # bigram "reverse etl" → Background Jobs
    ("reverse etl tool", "background"),              # bigram form → Background Jobs
    # Landing Pages — "landing" and "launch" tokens route page builder queries
    ("landing page builder", "landing"),             # "landing"→landing → Landing Pages category
    ("launch page builder", "landing"),              # "launch"→landing → Landing Pages category
    ("product launch page", "landing"),              # "launch" fires for product launch page queries
    # Maps & Location — "ip" and "country" tokens (was raw_first with no category boost)
    ("ip lookup", "maps"),                           # "ip"→maps → Maps & Location (ipapi.co, ipinfo.io)
    ("ip address api", "maps"),                      # "ip" fires in first position → Maps & Location
    ("ip geolocation nodejs", "maps"),               # "ip" wins before framework qualifier strips
    ("country detection", "maps"),                   # "country"→maps → Maps & Location
    ("country lookup api", "maps"),                  # "country" fires → Maps & Location
    # DevOps — "nameserver" and "domain" tokens (was raw_first with no category boost)
    ("nameserver lookup", "devops"),                 # "nameserver"→devops → DevOps & Infrastructure
    ("nameserver configuration", "devops"),          # "nameserver" fires → DevOps
    ("domain management", "devops"),                 # "domain"→devops fires before "management"→project
    ("domain registrar alternative", "devops"),      # "domain"→devops → DevOps & Infrastructure
    # Developer Tools — "number" token routes number-formatting queries (was raw_first)
    ("number formatting", "developer"),              # "number"→developer → Developer Tools
    ("number parsing library", "developer"),         # "number" fires → Developer Tools
    # Analytics — "heat map" two-word form was routing to maps via bare "map" token
    # Bigrams "heat map", "heat maps", "scroll map", "click map" route to Analytics & Metrics
    ("heat map tool", "analytics"),                  # bigram "heat map" → Analytics & Metrics
    ("heat map analytics", "analytics"),             # bigram fires before "analytics" token
    ("heat maps user behavior", "analytics"),        # "heat maps" plural bigram → Analytics & Metrics
    ("scroll map heatmap", "analytics"),             # "scroll map" bigram → Analytics & Metrics
    ("click map tool", "analytics"),                 # "click map" bigram beats "click"→cli → Analytics
    # Regression — "heatmap" (one word) and "hotjar" still route to analytics
    ("heatmap tool", "analytics"),                   # "heatmap"→analytics single token (unchanged)
    ("hotjar alternative", "analytics"),             # "hotjar"→analytics (unchanged)
    # AI — LLM token economics: "token usage" / "token count" were routing to Authentication
    # via bare "token"→authentication. Bigrams fire first so these land in AI & Automation.
    ("token usage api", "ai"),                       # bigram "token usage" → AI & Automation
    ("token usage tracking", "ai"),                  # bigram fires; "tracking" is a stop word → AI
    ("token count library", "ai"),                   # bigram "token count" → AI & Automation
    ("token count openai", "ai"),                    # "token count" bigram beats "token"→auth
    # AI — "content moderation" was routing to CMS via bare "content"→cms token
    ("content moderation api", "ai"),                # bigram "content moderation" → AI & Automation
    ("content moderation llm", "ai"),                # bigram fires before "content"→cms
    # Regression — bare "token" for auth tokens still routes to Authentication
    ("token refresh", "authentication"),             # "token"→authentication (no bigram, unchanged)
    ("access token", "authentication"),              # "token"→authentication (unchanged)
    # Authentication — spaced/hyphenated bigrams for 2FA/MFA: "two factor" and "multi factor"
    # were hitting raw_first because only the hyphenated "two-factor" was in _CAT_SYNONYMS.
    ("two factor auth", "authentication"),           # bigram "two factor" → Authentication
    ("two factor authentication library", "authentication"),  # bigram fires before raw_first
    ("multi factor authentication", "authentication"),        # bigram "multi factor" → Authentication
    ("multi factor otp", "authentication"),          # bigram "multi factor" beats "multi"→raw_first
    ("multi-factor authentication", "authentication"),        # hyphenated compound → Authentication
    # Regression — bare "2fa" and "mfa" still route to Authentication
    ("2fa library", "authentication"),               # "2fa"→authentication (unchanged)
    ("mfa provider", "authentication"),              # "mfa"→authentication (unchanged)
    # Security — bot detection; "bot detection" had no mapping → raw_first with no boost
    ("bot detection service", "security"),           # bigram "bot detection" → Security Tools
    ("bot detection open source", "security"),       # bigram fires before raw_first
    ("bot protection library", "security"),          # bigram "bot protection" → Security Tools
    # Testing — static analysis overrides "static"→frontend for code quality queries
    ("static analysis tool", "testing"),             # bigram fires before "static"→frontend
    ("static analysis typescript", "testing"),       # bigram fires before "static"→frontend
    ("code analysis linting", "testing"),            # bigram "code analysis" → Testing Tools
    # Regression — "static site" still routes to Frontend Frameworks
    ("static site generator", "frontend"),           # "static"→frontend single token (unchanged)
    # Frontend Frameworks — "design system" overrides "design"→design-creative for component queries
    ("design system react", "frontend"),             # bigram fires before "design"→design-creative
    ("open source design system", "frontend"),       # bigram "design system" → Frontend Frameworks
    ("design systems tools", "frontend"),            # plural bigram → Frontend Frameworks
    ("design tokens css", "frontend"),               # bigram "design tokens" → Frontend Frameworks
    # Regression — bare "design" still routes to Design & Creative
    ("design tool", "design"),                       # "design"→design-creative (unchanged)
    ("design software", "design"),                   # "design"→design-creative (unchanged)
    # DevOps — pull request and zero downtime deployment queries hit raw_first before fix
    ("pull request automation", "devops"),           # bigram "pull request" → DevOps
    ("pull request review tool", "devops"),          # bigram fires before raw_first
    ("zero downtime deployment", "devops"),          # bigram "zero downtime" → DevOps
    ("zero downtime migration", "devops"),           # bigram fires before "zero"→raw_first
    # Database — distributed coordination patterns: "optimistic"/"distributed" had no mapping
    ("optimistic locking library", "database"),      # bigram "optimistic locking" → Database
    ("optimistic locking postgres", "database"),     # bigram fires before raw_first
    ("distributed lock redis", "database"),          # bigram "distributed lock" → Database
    ("distributed locking service", "database"),     # bigram fires before "distributed"→raw_first
    # Analytics — data catalog queries had no synonym (raw_first with no boost); now fixed with bigrams.
    # DataHub, Amundsen, OpenMetadata, Apache Atlas live in Analytics & Metrics.
    ("data catalog tool", "analytics"),              # bigram "data catalog" → Analytics & Metrics
    ("open source data catalog", "analytics"),       # bigram fires before raw_first
    ("data governance platform", "analytics"),       # bigram "data governance" → Analytics & Metrics
    ("data governance tool", "analytics"),           # bigram fires before raw_first
    # Analytics — "privacy analytics" must route to Analytics, not Security.
    # Plausible, Fathom, Simple Analytics, Matomo are the canonical tools for this query.
    ("privacy analytics tool", "analytics"),         # bigram "privacy analytics" → Analytics & Metrics
    ("privacy analytics gdpr", "analytics"),         # bigram fires before "privacy"→security
    # Regression — bare "privacy" still routes to Security (GDPR compliance tools)
    ("privacy policy generator", "security"),        # "privacy"→security (unchanged)
    # Security — "cookie consent" overrides bare "cookie"→authentication for consent/GDPR banners.
    ("cookie consent banner", "security"),           # bigram "cookie consent" → Security Tools
    ("cookie consent gdpr", "security"),             # bigram fires before "cookie"→authentication
    # Regression — bare "cookie" still routes to Authentication (session/token queries)
    ("cookie session management", "authentication"), # "cookie"→authentication (unchanged)
    # Creative Tools — video editor / audio production / pixel art routing fixes (May 2026)
    ("video editor open source", "creative"),        # bigram "video editor" overrides "video"→media
    ("video editing software linux", "creative"),    # bigram "video editing" overrides "video"→media
    ("daw software alternative", "creative"),        # "daw" → Creative Tools (was raw_first)
    ("digital audio workstation", "creative"),       # bigram "digital audio" overrides "audio"→media
    ("music production software", "creative"),       # bigram "music production" (was raw_first "music")
    ("pixel art editor", "creative"),                # bigram "pixel art" overrides raw_first "pixel"
    ("aseprite alternative", "creative"),            # "aseprite" → Creative Tools (was raw_first)
    # Regression — bare "video" still routes to Media Servers (jellyfin, Plex queries)
    ("video streaming server", "media"),             # "video"→media (unchanged)
    # Creative Tools — whiteboard now routes to "creative" (boosts Creative Tools + Design & Creative)
    ("whiteboard tool", "creative"),                 # "whiteboard"→creative (was "design"-only)
    ("digital whiteboard open source", "creative"),  # "whiteboard"→creative via second token position
    # Newsletters & Content — brand tools previously returning raw_first with no category boost
    ("writefreely alternative", "newsletters"),      # "writefreely" → Newsletters & Content
    ("audiobookshelf alternative", "newsletters"),   # "audiobookshelf" → Newsletters & Content
    ("wallabag alternative", "newsletters"),         # "wallabag" → Newsletters & Content
    # Customer Support — "contact center" bigram (bare "contact" is unmapped)
    ("contact center software", "support"),          # bigram "contact center" → Customer Support
    ("open source contact center", "support"),       # bigram fires before raw_first "open"
    # AI — llms.txt (LLM-readable web standard); "llms" was unmapped → raw_first
    ("llms txt implementation", "ai"),               # bigram "llms txt" → AI & Automation
    ("llmstxt generator", "ai"),                     # compact "llmstxt" single token → AI & Automation
    ("llms-txt tool", "ai"),                         # hyphenated single token → AI & Automation
    # AI — local LLM tools with unmapped first tokens
    ("koboldai local", "ai"),                        # "koboldai" → AI & Automation
    ("lm studio alternative", "ai"),                 # bigram "lm studio" → AI & Automation
    # AI — "pydantic ai" (spaced) was routing to Developer via "pydantic"→developer
    ("pydantic ai framework", "ai"),                 # bigram "pydantic ai" → AI & Automation
    # Developer Tools — sourcemap compound forms (bigram "source map" CANNOT fire: "source" is a stop word)
    # sourcemap explorer, webpack sourcemaps, etc. now route to Developer Tools
    ("sourcemap explorer", "developer"),             # compound token "sourcemap" → Developer Tools
    ("sourcemaps webpack", "developer"),             # compound plural "sourcemaps" → Developer Tools
    # SEO — "site map" two-word form collides with "map"→maps-location; bigram overrides
    ("site map generator", "seo"),                   # bigram "site map" → SEO Tools
    ("xml site map", "seo"),                         # bigram fires before "xml"→raw_first
    # Regression — "sitemap" (compound) still routes to SEO correctly
    ("sitemap xml generator", "seo"),                # "sitemap"→seo (unchanged)
    # Project Management — "road map" two-word form collides with "map"→maps-location; bigram overrides
    ("road map planning", "project"),                # bigram "road map" → Project Management
    ("product road map", "project"),                 # bigram fires before "product"→raw_first
    # Regression — "roadmap" (compound) still routes to Project Management
    ("roadmap tool", "project"),                     # "roadmap"→project (unchanged)
    # Security — SCA (Software Composition Analysis) had no mapping → raw_first with no boost
    ("sca tool", "security"),                        # "sca" → Security Tools
    ("sca scanner open source", "security"),         # "sca" fires in first position → Security
    # Developer Tools — "commit message" was routing to Message Queue via bare "message"→message
    ("commit message linter", "developer"),          # bigram "commit message" → Developer Tools
    ("commit message format", "developer"),          # bigram fires before "message"→message-queue
    # DevOps — "cloud native" was routing to Frontend via bare "native"→frontend (React Native)
    ("cloud native deployment", "devops"),           # bigram "cloud native" → DevOps & Infrastructure
    ("cloud native monitoring", "devops"),           # bigram fires before "native"→frontend
    # AI — "local ai" was routing to raw_first "local" with no category boost
    ("local ai model", "ai"),                        # bigram "local ai" → AI & Automation
    ("local ai inference", "ai"),                    # bigram fires before "local"→raw_first
    # Security — AI safety tools with no prior synonym entries
    ("llamaguard setup", "security"),                # "llamaguard" → Security Tools (Meta LlamaGuard)
    ("llama-guard alternative", "security"),         # hyphenated form → Security Tools
    ("rebuff prompt injection", "security"),         # "rebuff" → Security Tools
    # AI — data labeling / annotation tools not yet individually mapped
    ("argilla alternative", "ai"),                   # "argilla" → AI & Automation (HF data labeling)
    ("labelstudio alternative", "ai"),               # compact form → AI & Automation
    ("label-studio ml backend", "ai"),               # hyphenated → AI & Automation
    ("label studio alternative", "ai"),              # bigram "label studio" → AI & Automation
    # Frontend — Reflex Python full-stack web framework
    ("reflex alternative", "frontend"),              # "reflex" → Frontend Frameworks
    ("reflexdev python", "frontend"),                # compound form → Frontend Frameworks
    # AI — txtai semantic search and RAG library
    ("txtai alternative", "ai"),                     # "txtai" → AI & Automation
    ("txtai embeddings", "ai"),                      # secondary query → AI & Automation
    # AI — LightRAG graph RAG framework
    ("lightrag alternative", "ai"),                  # "lightrag" → AI & Automation
    ("light-rag setup", "ai"),                       # hyphenated → AI & Automation
    # DevOps — "deno deploy" collision fix (bare "deno" → frontend)
    ("deno deploy alternative", "devops"),           # bigram "deno deploy" → DevOps & Infrastructure
    ("deno deploy setup", "devops"),                 # bigram fires before "deno"→frontend
    # Developer Tools — ID/UUID generation libraries
    ("uuid library", "developer"),                   # "uuid" → Developer Tools
    ("uuid generator nodejs", "developer"),          # "uuid" first token → Developer Tools
    ("ulid library", "developer"),                   # "ulid" → Developer Tools
    ("cuid alternative", "developer"),               # "cuid" → Developer Tools
    ("nanoid alternative", "developer"),             # "nanoid" → Developer Tools
    # Developer Tools — emoji libraries
    ("emoji library javascript", "developer"),       # "emoji" (not flag→feature) → Developer Tools
    ("emoji picker react", "developer"),             # "emoji" first token → Developer Tools
    # Testing — fake data generation (raw "fake" token, no Faker.js brand)
    ("fake data generator", "testing"),              # "fake" → Testing Tools
    ("fake api server", "testing"),                  # "fake" → Testing Tools
    # Developer Tools — timezone handling (spaced form)
    ("time zone library", "developer"),              # bigram "time zone" → Developer Tools
    ("time zone conversion tool", "developer"),      # bigram fires before "time"→raw_cat
    ("timezones javascript", "developer"),           # plural "timezones" → Developer Tools
    # AI — "token counting" (-ing form) routes to auth via "token"→authentication without bigram
    ("token counting library", "ai"),                # bigram "token counting" → AI & Automation
    ("token counting openai", "ai"),                 # bigram fires before "token"→authentication
    # AI — "ai pipeline" routes to background via "pipeline"→background without bigram
    ("ai pipeline framework", "ai"),                 # bigram "ai pipeline" → AI & Automation
    ("ai pipeline langchain", "ai"),                 # bigram fires before "pipeline"→background
    # AI — "ai orchestration" routes to background via "orchestration"→background without bigram
    ("ai orchestration framework", "ai"),            # bigram "ai orchestration" → AI & Automation
    ("ai orchestration crewai", "ai"),               # bigram fires before "orchestration"→background
    # Message Queue — "domain events" routes to devops via "domain"→devops without bigram
    ("domain events pattern", "message"),            # bigram "domain events" → Message Queue
    ("domain events library", "message"),            # bigram fires before "domain"→devops
    # Developer Tools — "domain driven" routes to devops via "domain"→devops without bigram
    ("domain driven design", "developer"),           # bigram "domain driven" → Developer Tools
    ("domain driven architecture", "developer"),     # bigram fires before "domain"→devops
    # Developer Tools — DDD abbreviation (raw_first without mapping)
    ("ddd framework", "developer"),                  # "ddd" → Developer Tools
    ("ddd architecture", "developer"),               # "ddd" → Developer Tools
    # Testing — performance testing bigrams override "performance"→monitoring
    ("performance testing k6", "testing"),           # bigram "performance testing" → Testing Tools
    ("performance test framework", "testing"),       # bigram "performance test" → Testing Tools
    # Regression — bare "performance" still routes to Monitoring
    ("performance monitoring", "monitoring"),         # "performance"→monitoring (unchanged)
    # Monitoring — synthetic monitoring bigram overrides "synthetic"→ai
    ("synthetic monitoring tool", "monitoring"),      # bigram "synthetic monitoring" → Monitoring & Uptime
    # Monitoring — "real user monitoring" RUM bigram overrides "real"→api
    ("real user monitoring", "monitoring"),           # bigram "user monitoring" fires at position 1
    # Database — column store bigram overrides "store"→frontend for columnar DB queries
    ("column store database", "database"),            # bigram "column store" → Database
    # Regression — bare "store" for state-management queries still routes to Frontend
    ("redux store", "frontend"),                      # "store"→frontend (unchanged)
    # Developer Tools — "template engine" bigram overrides "template"→boilerplate
    ("template engine node", "developer"),            # bigram "template engine" → Developer Tools
    ("template engine javascript", "developer"),      # bigram fires before "template"→boilerplate
    # Regression — bare "template" still routes to Boilerplates
    ("template starter kit", "boilerplate"),          # "starter"→boilerplate (unchanged)
    # Background Jobs — RPA queries (n8n, Windmill live in Background Jobs)
    ("rpa tool", "background"),                       # "rpa" → Background Jobs
    ("rpa open source", "background"),                # "rpa" fires first → Background Jobs
    # DevOps — service catalog (Backstage, Cortex, OpsLevel, Port); "service" is a stop word
    ("service catalog", "devops"),                    # "catalog"→devops (service stripped)
    ("internal catalog tool", "devops"),              # "catalog"→devops (internal+tool stripped)
    # Frontend — light mode complement to "dark"→frontend
    ("light mode library", "frontend"),               # "light"→frontend
    ("light theme toggle", "frontend"),               # "light"→frontend
    # AI — pair programming bigram
    ("pair programming tool", "ai"),                  # bigram "pair programming" → AI & Automation
    ("ai pair programmer", "ai"),                     # "ai"→ai fires first (pair unchanged)
    # DevOps — graceful process management
    ("graceful shutdown library", "devops"),          # "graceful"→devops
    ("graceful degradation pattern", "devops"),       # "graceful"→devops
    # AI Standards — high-level concept bigrams (150th pass)
    ("responsible ai framework", "ai standards"),      # "responsible ai" bigram
    ("responsible ai toolkit", "ai standards"),        # second form
    ("red teaming tool", "ai standards"),              # "red teaming" bigram
    ("red teaming llm", "ai standards"),               # second form
    ("ai benchmark tool", "ai standards"),             # "ai benchmark" bigram (overrides "benchmark"→testing)
    ("ai benchmark suite", "ai standards"),            # second form
    ("ai safety framework", "ai standards"),           # "ai safety" bigram
    ("ai safety testing", "ai standards"),             # second form
    ("ai governance framework", "ai standards"),       # "ai governance" bigram
    ("ai governance tool", "ai standards"),            # second form
    # API — "protocol buffer" bigram overrides "protocol"→mcp for protobuf queries
    ("protocol buffer grpc", "api"),                   # bigram "protocol buffer" fires before "protocol"→mcp
    ("protocol buffer golang", "api"),                 # second form
    # Regression — bare "protocol" still routes to MCP (model context protocol queries)
    ("protocol", "mcp"),                              # "protocol"→mcp unchanged
    # Notifications — "telephony" has no synonym; add it for Twilio/Vonage/Telnyx queries
    ("telephony api voip", "notifications"),           # "telephony"→notifications
    ("telephony sdk", "notifications"),               # second form
    # DevOps — "semantic versioning" bigram overrides "semantic"→search for semver/release queries
    ("semantic versioning tool", "devops"),            # bigram "semantic versioning" → DevOps
    ("semantic versioning npm", "devops"),             # second form
    # Regression — bare "semantic" still routes to search for semantic search queries
    ("semantic search engine", "search"),              # "semantic"→search unchanged
    # DevOps — bare "version" for "version bumping", "version management" queries
    ("version bumping", "devops"),                    # "version"→devops
    ("version management", "devops"),                 # second form
    # Regression — "version control" bigram still overrides to devops (unchanged)
    ("version control system", "devops"),             # bigram "version control"→devops (unchanged)
    # Analytics — data lineage tools (Marquez, OpenLineage); "data" has no synonym so bigram needed
    ("data lineage tool", "analytics"),               # bigram "data lineage"→analytics
    ("lineage tracking", "analytics"),                # bare "lineage"→analytics
    # Message Queues — "pub sub" spaced form; "pubsub" already mapped, space form was missing
    ("pub sub messaging", "message"),                 # bigram "pub sub"→message-queue
    ("pub sub pattern", "message"),                   # second form
    # Logging — "access log" bigram overrides "access"→authentication for log parsing queries
    ("access logs nginx", "logging"),                 # bigram "access logs"→logging
    ("access log parser", "logging"),                 # bigram "access log"→logging
    # Regression — bare "access" still routes to authentication (access control unchanged)
    ("access control list", "authentication"),         # "access"→authentication unchanged
    # Security — "cookie banner" bigram overrides "cookie"→authentication for GDPR banner queries
    ("cookie banner gdpr", "security"),               # bigram "cookie banner"→security
    # Regression — "cookie consent" already covered
    ("cookie consent banner", "security"),            # bigram "cookie consent"→security unchanged
    # CLI — "command line" spaced bigram; "commandline" compound was mapped but space form wasn't
    ("command line interface", "cli"),                # bigram "command line"→cli-tools
    ("command line tool", "cli"),                     # second form
    # Frontend — "canvas" bare token for HTML canvas drawing library queries
    ("canvas drawing library", "frontend"),           # "canvas"→frontend (Konva, Fabric, p5.js)
    # Database — "entity" for .NET Entity Framework and ORM entity-relationship queries
    ("entity framework alternative", "database"),     # "entity"→database
    # API — Apache Thrift RPC framework
    ("thrift alternative", "api"),                    # "thrift"→api-tools
    # Developer — "internal" bare token for internal tool builder queries (Retool, Appsmith)
    ("internal tool builder", "developer"),           # "internal"→developer (tool is a stop word → "internal builder")
    # Regression — "internal catalog" bigram keeps service catalog queries routing to DevOps
    ("internal catalog tool", "devops"),             # bigram "internal catalog"→devops (overrides "internal"→developer)
    # Frontend — "design token" singular bigram (design tokens plural was mapped, singular wasn't)
    ("design token system", "frontend"),              # bigram "design token"→frontend (overrides "token"→authentication)
    # Regression — bare "token" still routes to authentication (jwt tokens, access tokens)
    ("jwt token auth", "authentication"),             # "token"→authentication unchanged
    # Frontend — "server actions" spaced bigram (hyphenated form was mapped, space form wasn't)
    ("server actions nextjs", "frontend"),            # bigram "server actions"→frontend
    ("server actions form", "frontend"),              # second form
    # Maps — geo dead zones ("reverse geocoding", "postal code", "distance matrix")
    ("reverse geocoding api", "maps"),                # bigram "reverse geocoding"→maps (overrides "reverse"→devops)
    ("postal code lookup", "maps"),                   # bigram "postal code"→maps
    ("distance matrix api", "maps"),                  # bare "distance"→maps
    # Regression — bare "reverse" still routes to devops for reverse proxy queries
    ("reverse proxy caddy", "devops"),                # "reverse"→devops unchanged
    # Security — "browser fingerprinting" bigram overrides "browser"→testing
    ("browser fingerprinting", "security"),           # bigram "browser fingerprinting"→security
    # Regression — bare "browser" still routes to testing (Playwright, Puppeteer)
    ("browser testing playwright", "testing"),        # "browser"→testing unchanged
    # Security — IP reputation/blacklist bigrams override "ip"→maps for security queries
    ("ip reputation check", "security"),              # bigram "ip reputation"→security
    ("ip blacklist lookup", "security"),              # bigram "ip blacklist"→security
    # Regression — bare "ip" for geolocation still routes to maps
    ("ip address lookup", "maps"),                    # "ip"→maps unchanged
    # Authentication — "phone" bare token for phone verification/OTP queries
    ("phone verification", "authentication"),          # "phone"→authentication (Twilio Verify, Firebase Phone Auth)
    ("phone otp", "authentication"),                   # second form
    # AI — "named entity" bigram overrides "entity"→database for NER queries
    ("named entity recognition", "ai"),               # bigram "named entity"→ai (spaCy, NLTK)
    # Regression — bare "entity" still routes to database (Entity Framework, ORM)
    ("entity framework alternative", "database"),     # "entity"→database unchanged
    # AI — "audio transcription" bigram overrides "audio"→media for speech-to-text queries
    ("audio transcription api", "ai"),                # bigram "audio transcription"→ai (Deepgram, AssemblyAI)
    # Regression — bare "audio" still routes to media for streaming queries
    ("audio streaming", "media"),                     # "audio"→media unchanged
    # Security — "content security" bigram overrides "content"→cms for CSP header queries
    ("content security policy", "security"),          # bigram "content security"→security
    # Regression — "content management" and "content delivery" still route correctly
    ("content management system", "cms"),             # "content"→cms unchanged
    ("content delivery network", "devops"),           # bigram "content delivery"→devops unchanged
    # Frontend — "micro frontends" plural spaced form + "module federation" bigram
    ("micro frontends module federation", "frontend"),# bigram "micro frontends"→frontend
    ("module federation webpack", "frontend"),         # bigram "module federation"→frontend
    # Developer — Web3/DeFi tokens (defi + wallet were dead zones routing to mcp/raw_first)
    ("defi protocol", "developer"),                   # "defi"→developer (was routing to "protocol"→mcp)
    ("wallet connect", "developer"),                  # "wallet"→developer (was raw_first)
    # Analytics — "conversion rate" bigram overrides "rate"→api for CRO queries
    ("conversion rate optimization", "analytics"),    # bigram "conversion rate"→analytics
    # Regression — bare "rate" still routes to api for rate limiting queries
    ("rate limiting api", "api"),                     # "rate"→api unchanged (via "rate limiting" bigram)
    # Design — "ux" bare token for UX design tool queries
    ("ux design tool", "design"),                     # "ux"→design (Design & Creative)
    # Regression — "ux recording" bigram keeps session replay tools in analytics
    ("ux recording tool", "analytics"),               # bigram "ux recording"→analytics (overrides "ux"→design)
    # Design — "customer journey" bigram for journey mapping tools
    ("customer journey map", "design"),               # bigram "customer journey"→design
    # Monitoring — "flame graph" bigram overrides "graph"→database for profiling viz queries
    ("flame graph profiling", "monitoring"),          # bigram "flame graph"→monitoring (flamegraph compound already mapped)
    ("flame graph viewer", "monitoring"),             # second form
    # Regression — "graph"→database still fires for graph database queries
    ("graph database neo4j", "database"),             # "graph"→database unchanged
    # SEO — "sitemaps" plural (bare "sitemap" was mapped, plural form wasn't)
    ("generate sitemaps nextjs", "seo"),              # "sitemaps"→seo (plural form)
    ("sitemaps xml", "seo"),                          # second form
    # Regression — bare "sitemap" still routes to seo
    ("sitemap generator", "seo"),                     # "sitemap"→seo unchanged
    # DevOps — FinOps / cloud cost management (Infracost, Vantage, OpenCost)
    ("finops tool", "devops"),                        # "finops"→devops
    ("cloud cost optimizer", "devops"),               # bigram "cloud cost"→devops
    ("cloud cost monitoring", "devops"),              # second form
    ("infracost alternative", "devops"),              # "infracost"→devops
    ("opencost setup", "devops"),                     # "opencost"→devops
    # Invoicing — expense tracking (Toggl, Harvest, Expense.so)
    ("expense tracker app", "invoicing"),             # "expense"→invoicing
    ("expenses tracking tool", "invoicing"),          # "expenses"→invoicing
    # Project Management — time tracking (Toggl, Harvest, Clockify)
    # Note: "time tracking app" can't use bigram — "tracking" and "app" are stop words;
    # covered instead by named tool synonyms (toggl, harvest, clockify) + "time tracker" bigram
    ("time tracker freelancer", "project"),           # bigram "time tracker"→project
    ("toggl alternative", "project"),                 # "toggl"→project
    ("clockify setup", "project"),                   # "clockify"→project
    ("timesheet software", "project"),               # "timesheet"→project
    # Documentation — bare "documentation" word now mapped
    ("documentation generator", "documentation"),    # "documentation"→documentation
    ("documentation site builder", "documentation"), # second form
    # Analytics — SaaS metrics (prevent "saas"→boilerplate poisoning)
    ("saas metrics dashboard", "analytics"),         # bigram "saas metrics"→analytics
    # DevOps — Envoy Proxy (CNCF service proxy, "envoy" alone now maps to devops)
    ("envoy proxy alternative", "devops"),           # "envoy"→devops
    ("envoy sidecar setup", "devops"),               # second form
    # Logging — Promtail (Grafana Loki log shipping agent)
    ("promtail alternative", "logging"),             # "promtail"→logging
    ("promtail config loki", "logging"),             # second form
    # Monitoring — OpenTelemetry Collector shorthand
    ("otelcol setup", "monitoring"),                 # "otelcol"→monitoring
    ("otelcol config", "monitoring"),                # second form
    # Developer Tools — direnv per-directory env manager
    ("direnv alternative", "developer"),             # "direnv"→developer
    ("direnv setup envrc", "developer"),             # second form
    # Developer Tools — configuration languages (Jsonnet, Dhall, CUE)
    ("jsonnet alternative", "developer"),            # "jsonnet"→developer
    ("jsonnet vs yaml", "developer"),                # second form (yaml stripped as stop word; jsonnet survives)
    ("dhall alternative", "developer"),              # "dhall"→developer
    ("cuelang alternative", "developer"),            # "cuelang"→developer (unambiguous CUE lang form)
    # DevOps — Grafana Tanka (Jsonnet-based k8s config management)
    ("tanka alternative", "devops"),                 # "tanka"→devops
    ("tanka jsonnet kubernetes", "devops"),          # second form
    # Probe pattern 27: Sign-in / SSO / user-X / cloud-function dead zones
    # Auth — "sign": "in"/"on" are stop words so bigrams can't fire; bare "sign" routes correctly
    ("sign in", "authentication"),                   # "in" stripped → bare "sign"→authentication
    ("sign in provider", "authentication"),          # "in" stripped → ["sign", "provider"] → "sign"→auth
    ("sign up flow", "authentication"),              # "up" not a stop word → "sign up" bigram; falls back to "sign"→auth
    ("sign in with google", "authentication"),       # stripped → ["sign", "google"] → "sign"→auth
    # SSO — "single sign on": "on" stripped → ["single", "sign"] → "single sign" bigram
    ("single sign on", "authentication"),            # bigram "single sign"→authentication
    ("single sign on provider", "authentication"),   # second form
    # Auth — user-X bigrams that previously fired raw_first "user"
    ("user registration api", "authentication"),     # bigram "user registration"→authentication
    ("user profile page", "authentication"),         # bigram "user profile"→authentication
    ("user roles management", "authentication"),     # bigram "user roles"→authentication
    # Regression — "user management" bigram still routes to auth
    ("user management system", "authentication"),    # bigram "user management"→authentication (unchanged)
    # Regression — "sign document" routes to forms not auth
    ("sign document api", "forms"),                  # bigram "sign document"→forms (regression guard)
    # DevOps — cloud function bigrams
    ("cloud function alternative", "devops"),        # bigram "cloud function"→devops
    ("cloud functions provider", "devops"),          # bigram "cloud functions"→devops
    ("cloud functions vs lambda", "devops"),         # second form
    # Probe pattern 28: Platform engineering / DX / CVE / progressive delivery dead zones
    # DevOps — "platform" is stop word → "platform engineering" reduces to bare "engineering"
    ("platform engineering tool", "devops"),         # "engineering"→devops
    ("platform engineering alternative", "devops"),  # second form
    # Developer Tools — "developer" is stop word → "developer experience" reduces to bare "experience"
    ("developer experience platform", "developer"),  # "experience"→developer
    ("developer experience tools", "developer"),     # second form
    ("devex platform", "developer"),                 # "devex"→developer
    ("devex improvement", "developer"),              # second form
    # DevOps — IDP golden-path bigram (neither word is a stop word)
    ("paved road tooling", "devops"),                # bigram "paved road"→devops
    ("paved road template", "devops"),               # second form
    # Documentation — "technical writing" bigram
    ("technical writing tool", "documentation"),     # bigram "technical writing"→documentation
    ("technical writing assistant", "documentation"),# second form
    # Notifications — "async communication" bigram
    ("async communication tool", "notifications"),   # bigram "async communication"→notifications
    # Feature Flags — "progressive delivery" overrides "progressive"→frontend PWA misrouting
    ("progressive delivery tool", "feature"),        # bigram "progressive delivery"→feature
    ("progressive delivery platform", "feature"),    # second form
    # Regression — "progressive web app" still routes to frontend via "progressive"→frontend
    ("progressive web app", "frontend"),             # "progressive"→frontend still fires for PWA
    # Security — CVE scanning
    ("cve scanner", "security"),                     # "cve"→security
    ("cve tracker", "security"),                     # second form
    # Probe pattern 29: "data X" dead zones + "environment" local-dev misrouting
    # Background Jobs — "data transformation" / "data extraction" bigrams
    ("data transformation tool", "background"),      # bigram "data transformation"→background (dbt, Dagster)
    ("data transformation pipeline", "background"),  # second form
    ("data extraction tool", "background"),          # bigram "data extraction"→background (ETL tools)
    ("data extraction pipeline", "background"),      # second form
    # Database — "data modeling" bigram for ERD / schema diagramming tools
    ("data modeling tool", "database"),              # bigram "data modeling"→database (dbdiagram, DrawSQL)
    ("data modeling database", "database"),          # second form
    # Monitoring — "playbook" bare token (complement to "runbook"→monitoring)
    ("playbook tool", "monitoring"),                 # "playbook"→monitoring
    ("incident playbook", "monitoring"),             # second form
    # DevOps — "development environment" / "dev environment" bigrams override "environment"→security
    ("development environment tool", "devops"),      # bigram "development environment"→devops
    ("dev environment setup", "devops"),             # bigram "dev environment"→devops
    ("dev environment docker", "devops"),            # second form
    # Regression — bare "environment" (env var/secrets) still routes to security
    ("environment variables management", "security"),# "environment"→security still fires for secrets queries
    ("env secrets manager", "security"),             # "env"→security regression guard
    # Probe pattern 30: ERD / diagramming / web server / code generator / architecture dead zones
    # Database — ERD tools (dbdiagram.io, DrawSQL, ERD editors)
    ("erd", "database"),                             # bare "erd"→database
    ("erd diagram", "database"),                     # bigram "erd diagram"→database
    ("best erd tool", "database"),                   # "tool" stripped; bare "erd" fires
    # Developer Tools — diagramming tools (Mermaid, draw.io, Excalidraw)
    ("diagramming tool", "developer"),               # "tool" stripped; bare "diagramming"→developer
    ("diagramming software", "developer"),           # second form
    # Regression — "architecture diagram" still routes to developer via "diagram"→developer
    ("architecture diagram", "developer"),           # "diagram"→developer bigram still fires
    # API Tools — "web server" dead zone resolved ("web framework" can't be fixed — "framework" is stop word)
    ("web server golang", "api"),                    # bigram "web server"→api
    ("web server rust", "api"),                      # second form
    # AI Dev Tools — "code generator" dead zone resolved
    ("code generator ai", "ai dev"),                 # bigram "code generator"→ai dev
    ("code generator openapi", "ai dev"),            # second form
    # Regression — "code generation" still routes to ai dev
    ("code generation tool", "ai dev"),              # pre-existing bigram still fires
    # Developer Tools — software architecture pattern queries
    ("clean architecture framework", "developer"),   # bigram "clean architecture"→developer
    ("hexagonal architecture framework", "developer"),# bigram "hexagonal architecture"→developer
    ("onion architecture example", "developer"),     # bigram "onion architecture"→developer
    # Probe pattern 31: security dead zones — pentest/dependency-scanning/IAST/git-secrets misrouting
    # Security — penetration testing (OWASP ZAP, BurpSuite) must NOT land in Testing Tools
    ("penetration testing tool", "security"),        # bigram "penetration testing"→security
    ("penetration testing open source", "security"), # second form
    ("penetration test framework", "security"),      # bigram "penetration test"→security
    ("penetration test alternative", "security"),    # second form
    # Security — dependency vulnerability scanning (Snyk, Trivy, OWASP Dependency-Check)
    ("dependency scanning tool", "security"),        # bigram "dependency scanning"→security
    ("dependency scanning ci", "security"),          # second form
    ("dependency check owasp", "security"),          # bigram "dependency check"→security
    ("dependency check alternative", "security"),    # second form
    ("dependency vulnerability scanner", "security"),# bigram "dependency vulnerability"→security
    # Security — Software Composition Analysis (FOSSA, Black Duck, Scancode)
    # "software" is in stop words → meaningful terms are ["composition","analysis"/"scanning"]
    ("software composition analysis", "security"),   # bigram "composition analysis"→security (after stop-word strip)
    ("software composition scanning", "security"),   # bigram "composition scanning"→security (after stop-word strip)
    # Security — IAST (Interactive Application Security Testing)
    ("iast tool", "security"),                       # "iast"→security
    ("iast alternative", "security"),                # second form
    # Security — git secrets scanning (git-secrets, Gitleaks, TruffleHog)
    ("git secrets tool", "security"),                # bigram "git secrets"→security (overrides "git"→devops)
    ("git secret scanning", "security"),             # bigram "git secret"→security
    # Regression — bare "git" queries still route to devops (git hosting/workflows)
    ("git hosting", "devops"),                       # "git"→devops regression guard
    ("git workflow", "devops"),                      # second form
    # Probe pattern 32: "html X" mis-routing — bigrams override broad "html"→frontend
    # Developer Tools — HTML parsers (Cheerio, htmlparser2, BeautifulSoup, html5lib)
    # "html" alone correctly routes to frontend (HTML frameworks, components, templates)
    # but compound queries naming a tool type need bigrams so "html" doesn't win
    ("html parser", "developer"),                    # bigram "html parser"→developer
    ("html parser python", "developer"),             # bigram fires before "html"→frontend
    ("html parsing library", "developer"),           # bigram "html parsing"→developer
    ("html parsing nodejs", "developer"),            # second form
    # Developer Tools — HTML scrapers (complement to "scraper"→developer; html fires first without bigram)
    ("html scraper", "developer"),                   # bigram "html scraper"→developer
    ("html scraping tool", "developer"),             # bigram "html scraping"→developer
    ("html scraping python", "developer"),           # second form
    # Security — HTML sanitizers: bigram overrides "html"→frontend; "sanitizer"→security can't win alone
    ("html sanitizer", "security"),                  # bigram "html sanitizer"→security (DOMPurify, sanitize-html)
    ("html sanitizer javascript", "security"),       # second form
    # Regression — bare "html" and unambiguous html queries still route to frontend
    ("html component", "frontend"),                  # "html"→frontend (html component libraries)
    ("html css", "frontend"),                        # "html"→frontend (Bootstrap, Bulma)
    # Known dead zone — framework "vs" comparison queries (both tokens stripped by _FRAMEWORK_QUERY_TERMS)
    # "react vs vue", "nextjs vs remix" → raw_first "vs" (no category boost, but FTS still runs)
    # Acceptable gap: no safe single-token mapping for "vs". Non-framework comparisons work correctly:
    ("postgres vs mysql", "database"),               # "postgres"→database (not a framework term)
    ("redis vs memcached", "caching"),               # "redis"→caching (not a framework term)
    # Probe pattern 33: AI SDK / private registry / accessibility testing dead zones
    # AI & Automation — "ai sdk" was routing to api via sdk→api (ai→None missed)
    ("ai sdk", "ai"),                                # bigram "ai sdk"→ai (Vercel AI SDK, LangChain)
    ("ai sdk python", "ai"),                         # bigram fires before "sdk"→api
    ("ai sdk javascript", "ai"),                     # second form
    ("sdk python", "api"),                           # regression: bare "sdk"→api unaffected
    ("aisdk", "ai"),                                 # regression: "aisdk" compound form unaffected
    # Developer Tools — private package registries (Verdaccio, Nexus, JFrog Artifactory)
    ("private npm", "developer"),                    # bigram "private npm"→developer
    ("private npm registry", "developer"),           # bigram fires before "npm"→frontend
    ("private registry", "developer"),               # bigram — "private registry docker/npm" → Developer Tools
    ("npm alternative", "frontend"),                 # regression: bare "npm alternative" stays frontend
    # Testing — accessibility testing tools (axe, Wave, Deque) live in Testing Tools
    ("accessibility testing", "testing"),            # bigram "accessibility testing"→testing
    ("accessibility testing tool", "testing"),       # bigram fires before "accessibility"→frontend
    ("accessibility checker", "testing"),            # bigram "accessibility checker"→testing
    ("accessibility library", "frontend"),           # regression: "accessibility"→frontend unaffected
    ("a11y", "frontend"),                            # regression: "a11y"→frontend unaffected
    # Probe pattern 34 — PDF generation + QR code dead zones
    # "pdf generation/generator/creator" were routing to file-management via bare "pdf"→file.
    # "qr code generator" was routing to ai-dev via "code generator" bigram before "qr"→developer.
    ("pdf generation", "developer"),                 # bigram "pdf generation"→developer (PDFKit, WeasyPrint)
    ("pdf generator", "developer"),                  # bigram "pdf generator"→developer
    ("pdf generator nodejs", "developer"),           # bigram "pdf generator" fires before framework strip
    ("pdf creator", "developer"),                    # bigram "pdf creator"→developer
    ("html to pdf", "developer"),                    # "to" stripped → bigram "html pdf"→developer
    ("html to pdf nodejs", "developer"),             # same + framework qualifier
    ("qr code generator", "developer"),              # bigram "qr code"→developer fires before "code generator"→ai-dev
    ("qr code library", "developer"),               # bigram "qr code"→developer (regression guard)
    ("qr code scanner", "developer"),               # "qr code" bigram covers scanner queries
    ("pdf", "file"),                                 # regression: bare "pdf"→file-management unaffected
    ("pdf editor", "file"),                          # regression: "pdf editor"→file (editor not a bigram key)
    # Probe pattern 35 — UX research / user research dead zones
    # "user research", "user interview" etc. fired raw_first via unmapped "user" token.
    # Maze, Lookback, UserTesting, Dovetail → Feedback & Reviews category.
    ("user research", "feedback"),                   # bigram "user research"→feedback (Maze, UserTesting)
    ("user research tool", "feedback"),              # bigram fires before raw_first
    ("user research platform", "feedback"),          # bigram covers platform form too
    ("user interview", "feedback"),                  # bigram "user interview"→feedback (Lookback, Moderated.us)
    ("user interview tool", "feedback"),             # bigram fires before raw_first
    ("qualitative research", "feedback"),            # "qualitative"→feedback covers qualitative UX research
    ("qualitative feedback", "feedback"),            # second form
    ("maze alternative", "feedback"),                # "maze"→feedback (Maze.design UX research)
    ("maze ux research", "feedback"),                # secondary form
    ("usertesting alternative", "feedback"),         # "usertesting"→feedback (UserTesting.com)
    ("lookback alternative", "feedback"),            # "lookback"→feedback (Lookback.io user interviews)
    ("dovetail alternative", "feedback"),            # "dovetail"→feedback (Dovetail research repository)
    # Regressions — unrelated "user X" queries must still route correctly
    ("user authentication", "authentication"),       # "authentication"→auth wins over "user" raw_first
    ("user feedback", "feedback"),                   # "feedback"→feedback wins (already covered)
    ("user analytics", "analytics"),                 # "analytics"→analytics wins over "user" raw_first
    ("user survey", "forms"),                        # "survey"→forms wins over "user" raw_first
    # Probe pattern 36 — binary serialization / content moderation / SVG / address dead zones
    # Serialization: "protocol buffers" (plural) misrouted to mcp via bare "protocol"→mcp
    ("protocol buffers", "api"),                     # bigram plural overrides "protocol"→mcp → API Tools
    ("protocol buffers golang", "api"),              # with qualifier
    ("protobufs", "api"),                            # compound abbreviation → API Tools
    ("protobufs alternative", "api"),                # alternative form
    ("messagepack alternative", "api"),              # MessagePack binary serialization → API Tools
    ("msgpack python", "api"),                       # msgpack alias → API Tools
    # Content moderation: raw_first fires for "profanity" and "toxicity" (no mapping)
    ("profanity filter", "ai"),                      # → AI & Automation (Perspective API, CleanSpeak)
    ("profanity detection", "ai"),                   # detection form
    ("toxicity detection", "ai"),                    # → AI & Automation (Perspective API)
    ("toxicity classifier", "ai"),                   # classifier form
    # SVG: "svg library" → raw_first (no mapping); should route to Frontend Frameworks
    ("svg library", "frontend"),                     # SVG.js, Snap.svg, Paper.js → Frontend Frameworks
    ("svg animation", "frontend"),                   # animation override via "animation"→frontend still works
    # Maps: "address validation" misroutes to developer via bare "validation"→developer
    ("address validation", "maps"),                  # bigram overrides "validation"→developer → Maps & Location
    ("address autocomplete", "maps"),                # address autocomplete apis → Maps & Location
    ("address lookup", "maps"),                      # address lookup services → Maps & Location
    # Regressions — ensure "validation" still routes to developer for non-address contexts
    ("input validation", "developer"),               # "validation"→developer (no bigram override) → Developer Tools
    ("schema validation", "developer"),              # "validation"→developer → Developer Tools
    # Probe pattern 37: SaaS metrics + product feedback dead zones
    # SaaS metrics — mrr/arr/cac/revenue had no mapping → raw_first fired
    ("mrr dashboard tool", "analytics"),             # Monthly Recurring Revenue → Analytics & Metrics
    ("mrr tracker alternative", "analytics"),        # "mrr" bare token → Analytics
    ("arr analytics saas", "analytics"),             # Annual Recurring Revenue → Analytics & Metrics
    ("cac calculation tool", "analytics"),           # Customer Acquisition Cost → Analytics & Metrics
    ("revenue analytics dashboard", "analytics"),    # "revenue" bare token → Analytics
    ("revenue tracking saas", "analytics"),          # "revenue" → Analytics & Metrics
    # Regression: feature flags must NOT be affected
    ("feature flag toggle", "feature"),              # regression — "feature"→feature-flags still fires
    ("feature toggle launchdarkly", "feature"),      # regression — feature toggle → Feature Flags
    # Product feedback — "feature request" must route to feedback NOT feature-flags
    ("feature request tool", "feedback"),            # bigram "feature request" overrides "feature"→feature-flags
    ("feature request board canny", "feedback"),     # bigram fires first → Feedback & Reviews
    ("collect feature requests", "feedback"),        # plural bigram → Feedback & Reviews
    # Release notes — in-app changelog widget queries should route to feedback
    ("release notes widget", "feedback"),            # bigram "release notes" overrides "release"→devops
    ("release notes page alternative", "feedback"),  # bigram form → Feedback & Reviews
    # Regression: git release management still routes to devops via bare "release" token
    ("release version management", "devops"),        # "release"→devops when no "notes" bigram present
    # Probe pattern 38: typography / versioning / modal / contrast / cost / sortable dead zones
    # "typography" raw_first → frontend; font/type tools (Fontsource, typography.js)
    ("typography tool", "frontend"),                 # "typography"→frontend
    ("web typography", "frontend"),                  # bare token
    ("font typography css", "frontend"),             # with qualifier
    # "versioning" raw_first → devops; version management tools (semantic-release, standard-version)
    ("versioning workflow", "devops"),               # "versioning"→devops
    ("package versioning tool", "developer"),        # "package"→developer fires before "versioning"→devops (package managers live in dev-tools)
    # "modal"→ai (Modal.com) but "modal dialog" bigram → frontend
    ("modal dialog component", "frontend"),          # bigram overrides Modal.com routing
    ("react modal dialog", "frontend"),              # with framework qualifier
    # Regression: bare "modal" still routes to ai (Modal.com serverless GPU)
    ("modal serverless gpu", "ai"),                  # "modal"→ai still fires without "dialog"
    # "contrast" raw_first → testing; accessibility contrast checkers (axe, Lighthouse)
    ("contrast checker", "testing"),                 # "contrast"→testing
    ("contrast ratio tool", "testing"),              # with qualifier
    ("color contrast api", "frontend"),              # "color"→frontend fires at i=0 before "contrast" (color tools are frontend)
    # "screen reader" bigram → testing; a11y tools
    ("screen reader testing", "testing"),            # bigram fires
    ("screen reader compatible", "testing"),         # bigram fires
    # "keyboard navigation" bigram → testing; a11y keyboard nav
    ("keyboard navigation testing", "testing"),      # bigram fires
    ("keyboard nav a11y", "frontend"),               # "a11y"→frontend fires (a11y without "testing" suffix routes to frontend)
    # "cost"→devops; cloud cost tools (Infracost)
    ("cost optimization tool", "devops"),            # "cost"→devops
    ("infra cost monitoring", "devops"),             # "infra" raw_first then "cost"→devops fires at i=1
    # Regression: payment billing queries still route to payments
    ("subscription cost billing", "payments"),       # "subscription"→payments fires first
    # "semantic release" bigram → devops; overrides "semantic"→search
    ("semantic release config", "devops"),           # bigram fires before "semantic"→search
    ("semantic release alternative", "devops"),      # bigram fires
    # Regression: semantic search must NOT be affected
    ("semantic search engine", "search"),            # "semantic search" bigram → search
    # "sortable"→frontend; drag-and-drop UI libs (SortableJS, dnd-kit)
    ("sortable list react", "frontend"),             # "sortable"→frontend
    ("sortable table component", "frontend"),        # with qualifier
    # "focus management" bigram → frontend; overrides "management"→project
    ("focus management react", "frontend"),          # bigram fires before "management"→project
    ("keyboard focus management", "frontend"),       # bigram at i=1-2 fires
    # Probe pattern 39: zero-trust / reactive / hallucination / data-quality / schema-registry dead zones
    # "zero trust" (spaced) mis-routed via "network"→monitoring; now bigram "zero trust"→security overrides
    ("zero trust network", "security"),              # bigram fires before "network"→monitoring collision
    ("zero trust access control", "security"),       # bigram fires at i=0
    ("ztna alternative", "security"),               # ZTNA abbreviation → security
    # Regression: hyphenated and compound forms still route to security
    ("zero-trust architecture", "security"),         # hyphenated form unaffected
    ("zerotrust model", "security"),                 # compound form unaffected
    # "reactive"→frontend now maps; RxJS, MobX, Svelte signals queries route to Frontend Frameworks
    ("reactive programming library", "frontend"),    # "reactive"→frontend fires at i=0
    ("reactive ui component", "frontend"),           # "reactive" fires before "component"→frontend
    ("reactive state management", "frontend"),       # "reactive" fires before "state"→frontend (both correct)
    # Regression: event-driven messaging correctly routes to message-queue (event→message fires at i=0)
    ("event driven messaging", "message"),           # "event"→message fires before "reactive" could appear
    # "hallucination"→ai now maps; Guardrails AI / RAGAS / Giskard queries route correctly
    ("hallucination detection tool", "ai"),          # "hallucination"→ai fires at i=0
    ("hallucination checker llm", "ai"),             # "hallucination" fires first (llm→ai would also fire)
    # Regression: "llm hallucination" still routes via "llm"→ai (no change)
    ("llm hallucination mitigation", "ai"),          # "llm"→ai fires at i=0 (regression guard)
    # "data quality" bigram → analytics overrides bare "quality"→testing
    ("data quality tool", "analytics"),              # bigram fires before "quality"→testing
    ("data quality monitoring", "analytics"),        # bigram fires at i=0-1
    # Regression: bare "quality" still routes to testing when "data" prefix is absent
    ("code quality gate", "testing"),               # "quality"→testing fires (no bigram collision)
    # "schema registry" bigram → message overrides bare "schema"→developer for Kafka ecosystem queries
    ("schema registry kafka", "message"),            # bigram fires before "schema"→developer
    ("schema registry alternative", "message"),     # bigram fires at i=0-1
    # Regression: bare "schema" without "registry" still routes to developer
    ("schema validation library", "developer"),     # "schema"→developer fires (no bigram collision)
    # Probe pattern 40 (May 2026): code quality / accessibility testing dead zones.
    # "complexity"→testing; cyclomatic/code complexity analyzers (SonarQube, CodeClimate, Lizard).
    ("cyclomatic complexity", "testing"),           # "complexity"→testing fires at i=1
    ("code complexity analyzer", "testing"),        # "complexity"→testing fires at i=1
    # Regression: "password complexity"→security (password→security fires first)
    ("password complexity check", "security"),      # "password"→security fires at i=0
    # "axe"→testing; Deque axe-core accessibility testing library.
    ("axe alternative", "testing"),                 # "axe"→testing fires at i=0
    ("axe devtools setup", "testing"),              # "axe"→testing fires at i=0
    # "a11y testing" bigram → testing; overrides bare "a11y"→frontend
    ("a11y testing tool", "testing"),               # bigram fires before "a11y"→frontend
    ("a11y test runner", "testing"),                # bigram "a11y test" fires at i=0-1
    # Regression: bare "a11y" without "testing"/"test" still routes to frontend
    ("a11y linting rule", "frontend"),              # "a11y"→frontend fires (no bigram collision)
    # "wcag"→testing; any wcag query routes to Testing Tools
    ("wcag compliance checker", "testing"),         # "wcag"→testing fires at i=0
    ("wcag 2.1 compliance", "testing"),             # "wcag"→testing fires at i=0
    # Regression: bare "compliance" without "wcag" still routes to security
    ("soc2 compliance automation", "security"),     # "compliance"→security fires (no bigram collision)
    # "tech debt" bigram → developer; bare "tech"→raw_first, bare "debt"→raw_first
    ("tech debt tracker", "developer"),             # bigram fires at i=0-1
    ("tech debt management", "developer"),          # bigram fires at i=0-1
    # "dead code" bigram → testing; Knip, ts-prune, unimported
    ("dead code detection", "testing"),             # bigram fires at i=0-1
    ("dead code analyzer", "testing"),              # bigram fires at i=0-1
    # Regression: "accessibility library"→frontend, "accessibility testing"→testing (existing bigrams)
    ("accessibility library react", "frontend"),    # "accessibility"→frontend fires (no dead-code collision)
    ("accessibility testing runner", "testing"),    # "accessibility testing" bigram fires first
    # Probe pattern 41 (May 2026): bundle analysis / project management dead zones.
    # "bundle"→frontend: bundle analysis tools (webpack-bundle-analyzer, Bundlephobia) now route correctly.
    ("bundle size analyzer", "frontend"),           # "bundle"→frontend fires at i=0
    ("bundle stats webpack", "frontend"),           # "bundle"→frontend fires at i=0
    ("bundle budget tool", "frontend"),             # "bundle"→frontend fires at i=0
    # Regression: "webpack bundle analyzer" still routes via "webpack"→frontend (no change)
    ("webpack bundle analyzer", "frontend"),        # "webpack"→frontend fires at i=0
    # "bug"→project: bug trackers (Linear, Plane, Jira) now route to Project Management.
    ("bug tracker", "project"),                     # "bug"→project fires at i=0
    ("bug tracking tool", "project"),               # "bug"→project fires at i=0
    # Regression: "debugging tool"→developer (separate token, not affected by "bug"→project)
    ("debugging tool", "developer"),                # "debugging"→developer fires (not "bug"→project)
    # "retro"/"retrospective"→project: retrospective tools route to Project Management.
    ("retro app", "project"),                       # "retro"→project fires at i=0
    ("retrospective tool agile", "project"),        # "retrospective"→project fires at i=0
    # "okr"→project: OKR tracking tools route to Project Management.
    ("okr tool", "project"),                        # "okr"→project fires at i=0
    ("okr tracking software", "project"),           # "okr"→project fires at i=0
    # "standup"→project: async standup bots route to Project Management.
    ("standup bot", "project"),                     # "standup"→project fires at i=0
    ("daily standup tool", "project"),              # "standup"→project fires at i=1 (daily has no mapping)
    # "issue tracker" bigram → project; note "issue tracking" can't form — "tracking" is a stop word.
    ("issue tracker open source", "project"),       # bigram fires at i=0-1
    ("issue tracker github", "project"),            # bigram fires at i=0-1
    # "knowledge base" spaced bigram intentionally NOT added (see db.py note ~6381).
    # Regression guard: "knowledge base llm" still routes to AI (no bigram collision).
    ("knowledge base llm", "ai"),                   # "llm"→ai fires; no "knowledge base" bigram
    # Regression: "sprint" still routes to project (no change)
    ("sprint planning tool", "project"),            # "sprint"→project fires at i=0

    # Probe pattern 42 (May 2026): DAST / memory-profiler / image-scanning dead zones.
    # "dynamic analysis" fired raw_first — OWASP ZAP, Burp Suite, Nuclei unreachable.
    # "memory profiler"/"memory profiling" routed to caching via bare "memory"→caching
    #   firing before "profiler"→monitoring (token order mattered; bigrams now fix it).
    # "image scanning"/"image scan" routed to media via "image"→media (wrong; Trivy,
    #   Grype, Snyk Container live in security).
    # Fixed: bigram "dynamic analysis"→security, bigrams "memory profiler"/"memory
    #   profiling"→monitoring, bigrams "image scanning"/"image scan"→security.
    ("dynamic analysis tool", "security"),          # bigram "dynamic analysis"→security (was raw_first)
    ("dynamic application security testing", "security"),  # dast bare token also maps → security
    ("memory profiler python", "monitoring"),        # bigram "memory profiler"→monitoring (overrides memory→caching)
    ("memory profiling nodejs", "monitoring"),       # bigram "memory profiling"→monitoring
    ("image scanning docker", "security"),           # bigram "image scanning"→security (was image→media)
    ("image scan trivy grype", "security"),          # bigram "image scan"→security
    # Regression: bare "memory" queries (no profiler) still route to caching.
    ("memory store redis", "caching"),               # "memory"→caching unaffected (no profiler token)
    ("in memory cache", "caching"),                  # "memory"→caching (stop-word "in" stripped)
    # Regression: "dynamic" alone still routes via other tokens.
    ("dynamic import javascript", "frontend"),       # "javascript"→frontend fires (no "analysis" token)
    # Probe pattern 43 (May 2026): TLD-variant dead zones.
    # Queries like "make.com alternative" or "supabase.com alternative" produce a
    # single token ("make.com") that never matched bare "make" → raw_first fired.
    # Fixed: added .com/.app/.io/.tech/.so entries for 19 popular tools.
    ("make.com alternative", "background"),          # make.com → background (workflow automation)
    ("render.com alternative", "devops"),            # render.com → devops
    ("railway.app alternative", "devops"),           # railway.app → devops
    ("supabase.com alternative", "database"),        # supabase.com → database
    ("vercel.com alternative", "devops"),            # vercel.com → devops
    ("planetscale.com alternative", "database"),     # planetscale.com → database
    ("neon.tech alternative", "database"),           # neon.tech → database
    ("turso.tech alternative", "database"),          # turso.tech → database
    ("pocketbase.io alternative", "database"),       # pocketbase.io → database
    ("clerk.com alternative", "authentication"),     # clerk.com → authentication
    ("auth0.com alternative", "authentication"),     # auth0.com → authentication
    ("workos.com alternative", "authentication"),    # workos.com → authentication
    ("resend.com alternative", "email"),             # resend.com → email
    ("loops.so alternative", "email"),               # loops.so → email
    ("posthog.com alternative", "analytics"),        # posthog.com → analytics
    ("plane.so alternative", "project"),             # plane.so → project
    ("cal.com alternative", "scheduling"),           # cal.com → scheduling
    # Regression: bare tool names without TLD still route correctly.
    ("make workflow automation", "background"),      # bare "make"→background unaffected
    ("supabase postgres", "database"),               # bare "supabase"→database unaffected
    ("railway deployment", "devops"),                # bare "railway"→devops unaffected
    # Probe pattern 44 (May 2026): container/docker security collisions + threat dead zones +
    # supply-chain spaced form + SaaS billing collision.
    #
    # Container/Docker security — "container"→devops and "docker"→devops fire correctly for infra
    # queries but "container scanning/security/vulnerability" must route to Security Tools (Trivy, Grype).
    ("container scanning tool", "security"),         # bigram "container scanning"→security (Trivy, Grype)
    ("container security scanner", "security"),      # bigram "container security"→security
    ("container vulnerability scanner", "security"), # bigram "container vulnerability"→security
    ("docker security audit", "security"),           # bigram "docker security"→security
    ("docker vulnerability scan", "security"),       # bigram "docker vulnerability"→security
    # Regression — "container orchestration" / "docker compose" still route to devops.
    ("container orchestration", "devops"),           # "container"→devops single token (unchanged)
    ("docker compose", "devops"),                    # "docker"→devops single token (unchanged)
    #
    # Supply chain spaced form — hyphenated/compound were mapped; spaced bigram was missing.
    ("supply chain security", "security"),           # bigram "supply chain"→security (Sigstore, Syft)
    ("supply chain attack detection", "security"),   # bigram fires at i=0-1
    # Regression — hyphenated/compound forms still route correctly.
    ("supply-chain security", "security"),           # "supply-chain"→security hyphenated (unchanged)
    ("supplychain attack", "security"),              # "supplychain"→security compound (unchanged)
    #
    # Threat detection — bare "threat" had no mapping; raw_first fired for all threat queries.
    ("threat detection tool", "security"),           # "threat"→security bare token
    ("threat modeling", "security"),                 # "threat"→security bare token
    ("threat intelligence", "security"),             # "threat"→security bare token
    #
    # Key management — "key"→? no mapping; "management"→project fires (wrong for KMS queries).
    ("key management system", "security"),           # bigram "key management"→security (Vault, AWS KMS)
    ("key management server", "security"),           # bigram fires at i=0-1
    #
    # SaaS billing collision — "saas"→boilerplate fires before billing/payment/subscription tokens.
    ("saas billing platform", "payments"),           # bigram "saas billing"→payments
    ("saas payments integration", "payments"),       # bigram "saas payments"→payments
    ("saas subscription billing", "payments"),       # bigram "saas subscription"→payments
    ("saas subscription management", "payments"),    # bigram "saas subscription"→payments fires first
    # Regression — "saas metrics" still routes to analytics, "saas boilerplate" still to boilerplate.
    ("saas metrics dashboard", "analytics"),         # bigram "saas metrics"→analytics unchanged
    ("saas starter", "boilerplate"),                 # bare "saas"→boilerplate unchanged for starter queries
    # Probe pattern 45 (May 2026): workflow-automation collisions, LLM monitoring dead zones,
    # SBOM routing, mobile analytics collision.
    #
    # Workflow automation — "workflow"→ai and "visual"→testing collide with no-code automation tool
    # queries. n8n, Make.com, Activepieces, Temporal live in Background Jobs.
    # Fixed: bigrams "workflow builder", "workflow automation", "visual workflow" → background.
    ("workflow builder open source", "background"),  # bigram "workflow builder"→background (overrides workflow→ai)
    ("workflow automation nocode", "background"),    # bigram "workflow automation"→background fires at i=0-1
    ("visual workflow builder", "background"),       # bigram "visual workflow"→background (overrides visual→testing)
    ("visual workflow editor", "background"),        # bigram "visual workflow"→background fires at i=0-1
    # Regression — bare "workflow" without "builder"/"automation" still routes to ai (Dify, Flowise, etc.)
    ("ai workflow orchestration", "ai"),             # "workflow"→ai bare token unchanged
    # Regression — "visual regression testing" must still route to testing (not confused by visual→background)
    ("visual regression testing tool", "testing"),   # "visual regression"→testing bigram fires before "visual workflow"
    #
    # LLM monitoring / observability — Langfuse, Helicone, Arize Phoenix, Traceloop are monitoring
    # tools; "llm"→ai was firing for all llm-prefixed queries including these.
    # Fixed: bigrams "llm monitoring" and "llm observability" → monitoring.
    ("llm monitoring tool", "monitoring"),           # bigram "llm monitoring"→monitoring (overrides llm→ai)
    ("llm monitoring dashboard", "monitoring"),      # bigram fires at i=0-1
    ("llm observability platform", "monitoring"),    # bigram "llm observability"→monitoring
    ("llm observability open source", "monitoring"), # bigram fires at i=0-1
    # Regression — bare "llm" queries (no monitoring/observability) still route to ai.
    ("llm api wrapper", "ai"),                       # "llm"→ai bare token unchanged
    ("llm gateway proxy", "ai"),                     # "llm"→ai fires (no monitoring bigram match)
    #
    # Prompt injection — "prompt"→ai was firing for security-focused injection detection tools.
    # Rebuff, LLM Guard, Guardrails AI belong in Security Tools.
    # Fixed: bigram "prompt injection" → security.
    ("prompt injection detection", "security"),      # bigram "prompt injection"→security (overrides prompt→ai)
    ("prompt injection prevention", "security"),     # bigram fires at i=0-1
    # Regression — bare "prompt" queries without "injection" still route to ai.
    ("prompt management tool", "ai"),                # "prompt"→ai bare token unchanged
    ("prompt template library", "ai"),               # "prompt"→ai fires (no injection bigram match)
    #
    # SBOM / software bill of materials — "software" is a stop word so "software bill of materials"
    # reduces to "bill materials" bigram after stripping. Added "bill materials"→security.
    ("software bill of materials", "security"),      # "bill materials" bigram → Security (SBOM tools)
    ("bill of materials sbom", "security"),          # "bill materials" bigram at i=0-1 (stop-word strip)
    # Regression — bare "sbom" still routes to security (token mapping unchanged).
    ("sbom generator", "security"),                  # "sbom"→security bare token unchanged
    #
    # Mobile analytics — "mobile"→frontend was firing before "analytics" token.
    # Firebase Analytics (mobile), Amplitude Mobile, Mixpanel Mobile are in Analytics.
    # Fixed: bigram "mobile analytics" → analytics.
    ("mobile analytics sdk", "analytics"),           # bigram "mobile analytics"→analytics (overrides mobile→frontend)
    ("mobile analytics dashboard", "analytics"),     # bigram fires at i=0-1
    # Regression — bare "mobile" queries (no analytics) still route to frontend.
    ("mobile sdk integration", "frontend"),          # "mobile"→frontend bare token unchanged
    ("mobile app framework", "frontend"),            # "mobile"→frontend fires (no analytics bigram match)
    #
    # Probe pattern 46 — localization/consent/build-tool/flux dead zones
    #
    # Localization tools — locize and lokalise fired raw_first (no bare token mapping).
    # Weblate and crowdin were already mapped; added locize, lokalise, phrase, transifex.
    ("locize alternative", "localization"),          # bare "locize"→localization (was raw_first)
    ("lokalise alternative", "localization"),        # bare "lokalise"→localization (was raw_first)
    ("phrase i18n", "localization"),                 # bare "phrase"→localization
    ("transifex alternative", "localization"),       # bare "transifex"→localization
    # Regression — "weblate" was already mapped; unchanged.
    ("weblate alternative", "localization"),         # "weblate"→localization unchanged
    #
    # Consent/privacy tools — cookiebot, osano, onetrust, usercentrics all fired raw_first.
    # "consent" and "privacy" bare tokens already mapped to security; added named tools.
    ("cookiebot alternative", "security"),           # bare "cookiebot"→security (was raw_first)
    ("osano alternative", "security"),               # bare "osano"→security (was raw_first)
    ("onetrust alternative", "security"),            # bare "onetrust"→security (was raw_first)
    ("usercentrics alternative", "security"),        # bare "usercentrics"→security (was raw_first)
    # Regression — "consent management" already routed to security via "consent".
    ("gdpr consent banner", "security"),             # "gdpr"→security bare token unchanged
    #
    # Grunt/Gulp — fired raw_first; JS build tools belong in Frontend (same as webpack/esbuild).
    ("grunt build tool", "frontend"),                # bare "grunt"→frontend (was raw_first)
    ("gulp alternative", "frontend"),                # bare "gulp"→frontend (was raw_first)
    # Regression — webpack/esbuild/vite unaffected.
    ("webpack alternative", "frontend"),             # "webpack"→frontend unchanged
    ("esbuild alternative", "frontend"),             # "esbuild"→frontend unchanged
    #
    # FluxCD GitOps — "flux"→ai (FLUX.1 image model) was overriding GitOps queries.
    # fluxcd (compound) already mapped to devops; added "flux cd" and "flux gitops" bigrams.
    ("flux cd alternative", "devops"),               # bigram "flux cd"→devops (overrides flux→ai)
    ("flux gitops kubernetes", "devops"),            # bigram "flux gitops"→devops
    # Regression — bare "flux" without qualifier still routes to ai (ambiguous).
    ("flux image generation", "ai"),                 # "flux"→ai bare token unchanged
    #
    # Code formatting — "code formatting tool" fired raw_first via bare "code".
    # Added bigrams "code formatting"→testing and "code format"→testing.
    ("code formatting tool", "testing"),             # bigram "code formatting"→testing (was raw_first)
    ("code format on save", "testing"),              # bigram "code format"→testing
    # Regression — "code analysis" bigram was already mapped to testing.
    ("static code analysis", "testing"),             # "code analysis" bigram unchanged
    #
    # Probe pattern 47 — PKM/note-taking and CDP dead zones
    #
    # PKM tools (Obsidian, Logseq, Zettlr) are seeded as learning-education in IndieStack.
    # "obsidian", "logseq", "pkm", "zettelkasten", "notetaking", "second brain" all fired raw_first.
    # Fixed: added bare-token synonyms → "learning" and bigrams "note taking", "second brain".
    ("obsidian alternative", "learning"),            # bare "obsidian"→learning (was raw_first)
    ("logseq alternative", "learning"),              # bare "logseq"→learning (was raw_first)
    ("pkm app", "learning"),                         # bare "pkm"→learning (was raw_first)
    ("zettelkasten tool", "learning"),               # bare "zettelkasten"→learning (was raw_first)
    ("note taking app", "learning"),                 # bigram "note taking"→learning (was raw_first)
    ("second brain app", "learning"),                # bigram "second brain"→learning (was raw_first)
    ("notetaking alternative", "learning"),          # compound "notetaking"→learning (was raw_first)
    # Regression — "knowledge base LLM" must still route to AI (no bare "knowledge" token added).
    ("knowledge base llm", "ai"),                    # regression guard: unchanged
    # CDP tools — RudderStack fired raw_first (Segment already maps via "segment"→analytics).
    # Fixed: added bare "rudderstack"→analytics.
    ("rudderstack alternative", "analytics"),        # bare "rudderstack"→analytics (was raw_first)
    # Regression — "segment alternative" still routes to analytics via "segment"→analytics.
    ("segment alternative", "analytics"),            # "segment"→analytics unchanged
    #
    # Probe pattern 48 — "event X" analytics dead zones
    #
    # "event" bare token → message (Message Queue) for event streaming (Kafka, Kinesis).
    # But "event analytics" / "event capture" queries target product analytics (PostHog, Mixpanel).
    # "tracking" is in _FTS_STOP_WORDS so "event tracking" bigram can never fire;
    # use second-token bigrams "event analytics" and "event capture" instead.
    # "product events" fires "events"→message at i=1 — bigram overrides at i=0.
    ("event analytics tool", "analytics"),           # bigram "event analytics"→analytics (overrides "event"→message)
    ("event capture sdk", "analytics"),              # bigram "event capture"→analytics (overrides "event"→message)
    ("product events analytics", "analytics"),       # bigram "product events"→analytics (overrides "events"→message)
    # Regression — event streaming/sourcing must still route to message queue.
    ("event streaming kafka", "message"),            # bare "event"→message unchanged
    ("event driven architecture", "message"),        # bare "event"→message unchanged
    # Probe pattern 49 — social-auth / realtime-sync / github-oauth / edge-caching dead zones
    #
    # "social authentication" was the missing spaced bigram (social login/auth/sign/oauth already existed).
    ("social authentication provider", "authentication"),  # bigram "social authentication"→authentication
    ("social authentication methods", "authentication"),   # bigram fires at i=0 before "social"→social
    # Regression — bare "social" still routes to social-media for non-auth queries.
    ("social media scheduling", "social"),                 # bare "social"→social (no bigram collision)
    #
    # "realtime sync" routes to database (ElectricSQL, PowerSync, InstantDB).
    ("realtime sync engine", "database"),                  # bigram "realtime sync"→database (overrides "realtime"→api)
    ("realtime sync database", "database"),                # bigram form at i=0
    # Regression — "realtime collaboration" still routes to api (Liveblocks, Yjs).
    ("realtime collaboration tool", "api"),                # bare "realtime"→api unchanged
    #
    # "github oauth/sso/login" routes to authentication (GitHub as OAuth provider).
    ("github oauth setup", "authentication"),              # bigram "github oauth"→authentication (overrides "github"→devops)
    ("github sso setup", "authentication"),                # bigram "github sso"→authentication
    ("github login provider", "authentication"),           # bigram "github login"→authentication
    # Regression — "github actions" still routes to devops.
    ("github actions ci", "devops"),                       # bare "github"→devops unchanged
    #
    # "edge caching/cache" routes to caching (Upstash, Cloudflare KV).
    ("edge caching redis", "caching"),                     # bigram "edge caching"→caching (overrides "edge"→devops)
    ("edge cache alternative", "caching"),                 # bigram "edge cache"→caching (singular form)
    # Regression — "edge database" still routes to database (Turso, D1).
    ("edge database sqlite", "database"),                  # bigram "edge database"→database unchanged
    #
    # Probe pattern 50 — favicon / OG / PII / team-messaging / syslog / HMAC dead zones
    #
    # "favicon" → Frontend Frameworks (favicon.io, RealFaviconGenerator)
    ("favicon generator", "frontend"),                     # bare "favicon"→frontend
    ("favicon creator", "frontend"),                       # bare "favicon"→frontend (plural form)
    # Regression — "graph database" still routes to database via bare "graph".
    ("graph database alternative", "database"),            # bare "graph"→database unchanged
    #
    # "meta tag/tags" → SEO Tools (metatags.io, Open Graph Preview)
    ("meta tag generator", "seo"),                         # bigram "meta tag"→seo
    ("meta tags checker", "seo"),                          # bigram "meta tags"→seo (plural)
    #
    # "og image" routes to seo via bare "og"→seo token.
    # Note: "open graph" bigram NOT added — "open" is in _FTS_STOP_WORDS and is always stripped.
    # Users typically use the "og" abbreviation in technical queries.
    ("og image generator", "seo"),                         # bare "og"→seo unchanged
    #
    # "graph ql" spaced form → API Tools (overrides bare "graph"→database)
    ("graph ql alternative", "api"),                       # bigram "graph ql"→api (overrides "graph"→database)
    ("graph ql client", "api"),                            # bigram fires for spaced form
    # Regression — "graphql" compound still routes to api.
    ("graphql client", "api"),                             # bare "graphql"→api unchanged
    #
    # "syslog" / "rsyslog" → Logging (rsyslog, syslog-ng, Papertrail syslog)
    ("syslog server", "logging"),                          # bare "syslog"→logging
    ("rsyslog alternative", "logging"),                    # bare "rsyslog"→logging
    #
    # PII / data-privacy dead zones → Security Tools
    ("pii detection library", "security"),                 # bare "pii"→security
    ("pii redaction api", "security"),                     # bigram "pii redaction"→security
    ("data masking tool", "security"),                     # bigram "data masking"→security
    ("data anonymization gdpr", "security"),               # bigram "data anonymization"→security
    ("data residency compliance", "security"),             # bigram "data residency"→security
    ("data sovereignty cloud", "security"),                # bigram "data sovereignty"→security
    # Regression — "data quality" still routes to analytics (Monte Carlo, Soda).
    ("data quality monitoring", "analytics"),              # bigram "data quality"→analytics unchanged
    #
    # "hmac" / "request signing" → Security Tools
    ("hmac verification", "security"),                     # bare "hmac"→security
    ("request signing library", "security"),               # bigram "request signing"→security
    # Regression — bare "signature"→forms (e-signature tools) unchanged.
    ("signature tool", "forms"),                           # bare "signature"→forms unchanged
    #
    # "team messaging" → Developer Tools (Mattermost, Rocket.Chat, Zulip)
    ("team messaging tool", "developer"),                  # bigram "team messaging"→developer
    ("team messaging self-hosted", "developer"),           # bigram fires before bare "team"→?
    #
    # "matrix protocol" → Social Media (Element, Synapse; overrides "protocol"→mcp)
    ("matrix protocol server", "social"),                  # bigram "matrix protocol"→social (overrides "protocol"→mcp)
    ("matrix protocol alternative", "social"),             # bigram fires at i=0

    # Probe pattern 51 — LLM eval short-form / self-hosted / changesets dead zones
    #
    # "llm eval" short form — "llm evaluation" was mapped but "llm eval" (short) was not.
    # Pattern 25 (plural/compound form gaps): always add short/gerund variants alongside the full form.
    ("llm eval setup", "ai standards"),                    # bigram "llm eval"→ai standards (short form was missing)
    ("llm eval tool", "ai standards"),                     # bigram fires before "llm"→ai
    ("llm benchmarking suite", "ai standards"),            # bigram "llm benchmarking"→ai standards (gerund was missing)
    ("llm benchmarking result", "ai standards"),           # bigram fires; "llm benchmark" (non-gerund) already worked
    #
    # "ai evaluation" — "model evaluation" and "ai eval" bigrams existed but "ai evaluation" full words didn't.
    ("ai evaluation framework", "ai standards"),           # bigram "ai evaluation"→ai standards
    ("ai evaluation tool", "ai standards"),                # bigram fires before "ai"→ai single-token
    # Regression — "ai eval" bigram still works.
    ("ai eval harness", "ai standards"),                   # bare "ai eval"→ai standards unchanged
    #
    # "evals benchmark" — "evals"→ai fires before bigram "evals benchmark" is checked.
    # Fix: bigram "evals benchmark" overrides bare "evals"→ai.
    ("evals benchmark comparison", "ai standards"),        # bigram "evals benchmark"→ai standards
    ("evals benchmark result", "ai standards"),            # bigram fires at i=0
    # Regression — bare "evals" still routes to ai (correct catch-all for AI Automation).
    ("evals pipeline", "ai"),                              # bare "evals"→ai unchanged; only bigram form overrides
    #
    # "self hosted" / "self-hosted" — Pattern 23 (dual raw_first dead zone).
    # Both "self" and "hosted" are individually unmapped; bigrams fix the routing.
    ("self hosted redis", "devops"),                       # bigram "self hosted"→devops
    ("self hosted alternative", "devops"),                 # bigram fires at i=0
    ("self-hosted solution", "devops"),                    # hyphenated single token → devops
    ("self-hosting guide", "devops"),                      # gerund form → devops
    ("self host tool", "devops"),                          # bigram "self host"→devops
    #
    # "changesets" fixed from devops → developer (JS monorepo versioning, not DevOps automation).
    ("changesets npm", "developer"),                       # bare "changesets"→developer (fixed; was "devops")
    ("changesets release", "developer"),                   # bare "changesets"→developer
    # Regression — "semantic release" still routes to devops (CI/CD release automation).
    ("semantic release tool", "devops"),                   # bare "semantic"→devops unchanged

    # Probe pattern 52 — shell bare tokens / on-call stop-word drop / license dead zones / e2e collision
    #
    # "zsh" / "bash" bare tokens — common shell queries fired raw_first (Pattern 23 dual dead zone).
    # Fish Shell was already mapped but Zsh/Bash bare tokens were not.
    ("zsh alternative", "cli"),                            # bare "zsh"→cli (oh-my-zsh, zimfw alternatives)
    ("zsh plugin manager", "cli"),                         # bare "zsh"→cli
    ("bash scripting tool", "cli"),                        # bare "bash"→cli
    ("bash utility library", "cli"),                       # bare "bash"→cli
    # Regression — "fish shell" still routes to cli (was already mapped).
    ("fish shell alternative", "cli"),                     # bare "fish"→cli unchanged
    #
    # "on call" — "on" is a stop word, leaving bare "call" with no synonym.
    # "on-call" (hyphenated) was already mapped to monitoring; spaced form was a dead zone.
    ("on call tool", "monitoring"),                        # bare "call"→monitoring (stop-word "on" stripped)
    ("on call management", "monitoring"),                  # bigram "on call" not needed; bare "call" fires
    # Regression — "on-call schedule" still routes to monitoring (hyphenated form unchanged).
    ("on-call schedule", "monitoring"),                    # "on-call"→monitoring unchanged
    #
    # "license" / "fossa" bare tokens — license compliance tools fired raw_first.
    ("license checker python", "security"),                # bare "license"→security (FOSSA, SPDX, licensecheck)
    ("open source license scanner", "security"),           # "open"/"source" are stop words → "license"→security
    ("fossa alternative", "security"),                     # bare "fossa"→security (FOSSA license tool)
    # Regression — "license compliance scanner" still routes via "compliance"→security (unaffected).
    ("license compliance scanner", "security"),            # "compliance"→security unchanged
    #
    # "e2e encryption" — "e2e"→testing collides with security context for encryption queries.
    # Bigrams "e2e encryption" and "e2e encrypted" override bare "e2e"→testing.
    ("e2e encryption library", "security"),                # bigram "e2e encryption"→security (overrides e2e→testing)
    ("e2e encrypted messenger", "security"),               # bigram "e2e encrypted"→security
    # Regression — bare "e2e testing" still routes to testing.
    ("e2e testing playwright", "testing"),                 # bare "e2e"→testing unchanged
    ("e2e test runner", "testing"),                        # bare "e2e"→testing unchanged

    # Probe pattern 53 — codegen collision / realtime-database / smart-contract dead zones
    #
    # "code generator"/"code generation" bigram fires at position 1+ when an API-layer tool
    # appears at position 0 — overriding correct routing. Fix: "[tool] code" bigrams at pos 0.
    ("openapi code generator", "api"),                     # bigram "openapi code"→api (beats "code generator"→ai-dev)
    ("swagger code generator", "documentation"),           # bigram "swagger code"→documentation
    ("graphql code generator", "api"),                     # bigram "graphql code"→api
    ("protobuf code generation", "developer"),             # bigram "protobuf code"→developer
    ("proto code gen", "developer"),                       # short-form — "proto code"→developer
    # Regression — standalone "code generator" still routes to ai-dev.
    ("code generator javascript", "ai dev"),               # bare "code generator"→ai-dev unchanged
    # Regression — "openapi generator" (no "code") still routes to api.
    ("openapi generator nodejs", "api"),                   # bare "openapi"→api unchanged
    #
    # "realtime database" — "realtime"→api fired but realtime-sync DB tools live in Database.
    ("realtime database firebase", "database"),            # bigram "realtime database"→database
    ("realtime database sync", "database"),                # bigram fires over bare "realtime"→api
    # Regression — bare "realtime sync" still routes to database (probe 49).
    ("realtime sync engine", "database"),                  # bigram "realtime sync"→database unchanged
    # Regression — "realtime api" still routes to api.
    ("realtime api websocket", "api"),                     # bare "realtime"→api unchanged
    #
    # "smart contract" — "contract"→testing (Pact) fired for smart-contract queries.
    ("smart contract solidity", "developer"),              # bigram "smart contract"→developer
    ("smart contracts ethereum", "developer"),             # plural bigram
    ("smart contract audit", "developer"),                 # audit context also → developer (not security)
    # Regression — bare "contract testing" still routes to testing.
    ("contract testing pact", "testing"),                  # bare "contract"→testing unchanged
    # Probe pattern 54 — AI Dev Tools routing precision / GitHub Copilot collision / file-hosting dead zone
    #
    # cursor/windsurf/copilot were mapped to bare "ai" which boosts BOTH AI & Automation AND AI Dev Tools.
    # Changed to "ai dev" to precisely target AI Dev Tools (Cursor, Windsurf, Copilot are AI coding tools).
    ("cursor alternative", "ai dev"),                      # "cursor"→"ai dev" (was "ai")
    ("windsurf alternative", "ai dev"),                    # "windsurf"→"ai dev" (was "ai")
    ("copilot alternative", "ai dev"),                     # "copilot"→"ai dev" (was "ai")
    # Regression — general AI/automation tools still route to "ai" not "ai dev".
    ("langchain alternative", "ai"),                       # "langchain"→"ai" unchanged
    ("n8n workflow", "background"),                        # workflow automation unchanged
    #
    # "github copilot alternative" — bare "github"→devops fired over "copilot"→ai dev.
    # Fix: bigram "github copilot" → "ai dev" wins at position 0 before "github" fires.
    ("github copilot alternative", "ai dev"),              # bigram "github copilot"→"ai dev"
    ("github copilot replacement", "ai dev"),              # same bigram
    ("github copilot vs cursor", "ai dev"),                # bigram fires first at pos 0
    # Regression — bare "github" still routes to devops for non-copilot contexts.
    ("github actions alternative", "devops"),              # "github"→devops unchanged
    #
    # "ai ide" — bare "ide"→developer fired for AI IDE queries.
    # Fix: bigram "ai ide" → "ai dev".
    ("ai ide alternative", "ai dev"),                      # bigram "ai ide"→"ai dev"
    ("ai ide 2025", "ai dev"),                             # same bigram pattern
    # Regression — bare "ide" still routes to developer for non-AI IDE contexts.
    ("ide plugin neovim", "developer"),                    # "ide"→developer unchanged
    #
    # "file hosting" — bare "hosting"→devops fired instead of file-management category.
    # Fix: bigram "file hosting" → "file".
    ("file hosting service", "file"),                      # bigram "file hosting"→file
    ("file hosting s3 compatible", "file"),                # bigram fires first
    # Regression — bare "hosting" still routes to devops for general hosting queries.
    ("hosting provider vps", "devops"),                    # "hosting"→devops unchanged
    #
    # "automation workflow" (reversed word order vs "workflow automation") — "automation"→ai fired.
    # Fix: bigram "automation workflow" → "background" (symmetric with "workflow automation").
    ("automation workflow n8n", "background"),             # bigram "automation workflow"→background
    ("automation workflow engine", "background"),          # same bigram
    # Regression — bare "workflow automation" still routes to background (probe 5).
    ("workflow automation python", "background"),          # "workflow automation"→background unchanged
    # Probe pattern 55 — AI routing dead zones: red-team / context-management / AI observability / AI deployment
    #
    # "red team" (spaced) had no bigram; "red" has no category match so raw_first fired with +0 boost.
    # "redteam", "red-team", "red teaming" were already mapped — this closes the spaced-form gap.
    ("red team evaluation", "ai standards"),               # bigram "red team"→"ai standards"
    ("red team llm testing", "ai standards"),              # bigram fires at pos 0
    ("red team alternative", "ai standards"),              # bigram fires at pos 0
    # Regression — "red teaming" and "redteam" still route correctly.
    ("red teaming tool", "ai standards"),                  # "red teaming"→"ai standards" unchanged
    ("redteam framework", "ai standards"),                 # "redteam"→"ai standards" unchanged
    #
    # "context management" → "context"→frontend misfired; LLM context management ≠ React Context API.
    # Bigram override needed (same pattern as "context window", "context engineering").
    ("context management tool", "ai"),                     # bigram "context management"→ai
    ("llm context management", "ai"),                      # bigram fires at pos 1
    # Regression — React Context API queries still route to frontend.
    ("react context api", "frontend"),                     # "context"→frontend unchanged (react framework-stripped → context first)
    ("context provider react", "frontend"),                # "context"→frontend unchanged
    #
    # "ai tracing" → "tracing"→monitoring misfired; LLM trace viewers live in AI Dev Tools.
    # "ai observability" → "observability"→monitoring misfired; LLM observability tools live in AI Dev Tools.
    ("ai tracing tool", "ai dev"),                         # bigram "ai tracing"→"ai dev"
    ("ai tracing langsmith", "ai dev"),                    # bigram fires at pos 0
    ("ai observability platform", "ai dev"),               # bigram "ai observability"→"ai dev"
    ("ai observability alternative", "ai dev"),            # bigram fires at pos 0
    # Regression — generic tracing/observability still routes to monitoring.
    ("distributed tracing tool", "monitoring"),            # "tracing"→monitoring unchanged
    ("observability platform grafana", "monitoring"),      # "observability"→monitoring unchanged
    #
    # "ai deployment" → "deployment"→devops misfired; AI model serving tools live in AI & Automation.
    ("ai deployment tool", "ai"),                          # bigram "ai deployment"→ai
    ("ai model deployment bentoml", "ai"),                 # bigram fires at pos 0
    # Regression — bare "deployment" still routes to devops for general CI/CD queries.
    ("deployment pipeline github actions", "devops"),      # "deployment"→devops unchanged
    # Probe pattern 56 — AI-prefix wrong-subcategory: memory / chat collisions
    #
    # "ai memory" → "memory"→caching misfired; AI agent memory (MemGPT, Mem0, Zep) live in AI & Automation.
    ("ai memory tool", "ai"),                              # bigram "ai memory"→ai (beats "memory"→caching)
    ("ai agent memory", "ai"),                             # bigram fires at pos 1 (agent→ai at pos 0; ai memory at pos 1+)
    # Regression — bare "memory"/"redis cache" still route to caching.
    ("redis memory cache", "caching"),                     # "redis"→caching unchanged
    #
    # "ai chat" → "chat"→customer misfired; AI chatbot builders (Chatbase, OpenChat) live in AI & Automation.
    ("ai chat tool", "ai"),                                # bigram "ai chat"→ai (beats "chat"→customer)
    ("ai chat alternative", "ai"),                         # bigram fires at pos 0
    # Regression — live/support chat still routes to customer support.
    ("live chat widget", "customer"),                      # "chat"→customer unchanged
    ("customer chat support", "customer"),                 # "customer"→customer unchanged
    # Probe pattern 57 — changelog-widget collision / document-signing dead zone / pre-commit hooks collision
    #
    # "changelog widget" → "changelog"→devops fired (git-cliff/semantic-release type tools).
    # Product changelog widgets (AnnounceKit, Beamer, Featurebase) are Feedback & Reviews, not DevOps.
    ("changelog widget react", "feedback"),                # bigram "changelog widget"→feedback (beats changelog→devops)
    ("changelog widget alternative", "feedback"),          # bigram fires at pos 0
    ("changelog embed tool", "feedback"),                  # bigram "changelog embed"→feedback
    # Regression — git-based changelog tools still route to devops.
    ("changelog generator git", "devops"),                 # "changelog"→devops unchanged
    ("release changelog generator", "devops"),             # "changelog"→devops unchanged
    #
    # "document signing" → "document"→database fired (document-store/MongoDB terminology).
    # E-signature APIs (DocuSign, HelloSign, PandaDoc) live in Forms & Surveys.
    ("document signing api", "forms"),                     # bigram "document signing"→forms (beats document→database)
    ("document signing integration", "forms"),             # bigram fires at pos 0
    ("esign api alternative", "forms"),                    # bare "esign"→forms
    # Regression — document-database queries still route to database.
    ("document database mongodb", "database"),             # "document"→database unchanged
    ("document store nosql", "database"),                  # "document"→database unchanged
    #
    # "pre commit hooks" → "hooks"→frontend fired (React hooks terminology).
    # Pre-commit hook runners (Husky, pre-commit, Lefthook) live in DevOps, not Frontend.
    ("pre commit hooks nodejs", "devops"),                 # bigram "pre commit"→devops (beats hooks→frontend)
    ("pre commit runner alternative", "devops"),           # bigram fires at pos 0
    # Regression — React hooks / git queries still route correctly.
    ("react hooks state", "frontend"),                     # "hooks"→frontend unchanged (react framework-strips react)
    ("git lfs storage", "devops"),                         # "git"→devops unchanged (bare git queries → DevOps)
    # Probe pattern 58 — learning / api-docs / crm / landing / newsletter / image-opt dead zones
    #
    # "coding bootcamp" → "coding"→ai dev misfired; bootcamp platforms are Learning & Education.
    # "developer tutorials" → "tutorials" unmapped; raw_first fired.
    ("coding bootcamp platform", "learning"),              # bigram "coding bootcamp"→learning (beats coding→ai dev)
    ("developer tutorials platform", "learning"),          # bare "tutorials"→learning
    ("bootcamp builder", "learning"),                      # bare "bootcamp"→learning
    ("interactive tutorial", "learning"),                  # bare "tutorial"→learning
    # Regression — AI coding tools still route correctly.
    ("coding assistant aider", "ai dev"),                  # "coding"→ai dev unchanged
    ("coding tutorial platform", "learning"),              # existing bigram "coding tutorial"→learning unchanged
    #
    # "api docs generator" → bare "api"→api fired (wrong; Swagger UI, Stoplight, ReadMe are Documentation).
    ("api docs generator", "documentation"),               # bigram "api docs"→documentation (beats api→api)
    ("api documentation openapi", "documentation"),        # bigram "api documentation"→documentation
    # Regression — bare "api" still routes to api-tools for non-docs queries.
    ("api gateway rate limiting", "api"),                  # "api"→api unchanged
    #
    # "customer relationship management" → "management"→project misfired; CRM tools are CRM category.
    ("customer relationship management", "crm"),           # bigram "customer relationship"→crm (beats management→project)
    # Regression — "project management" still routes correctly.
    ("project management linear", "project"),              # "management"→project unchanged
    #
    # "sales page creator" → "sales"→crm misfired; sales/landing page builders are Landing Pages.
    ("sales page creator", "landing"),                     # bigram "sales page"→landing (beats sales→crm)
    ("sales page builder", "landing"),                     # same bigram
    # Regression — bare "sales" still routes to crm for CRM-intent queries.
    ("sales pipeline crm", "crm"),                         # "sales pipeline" bigram→crm unchanged
    #
    # "newsletter monetization" → "newsletter"→email misfired; newsletter business tools are Newsletters.
    ("newsletter monetization tool", "newsletters"),       # bigram "newsletter monetization"→newsletters
    # Regression — generic newsletter queries still route to email-marketing.
    ("newsletter email marketing", "email"),               # "newsletter"→email unchanged
    ("newsletter sendgrid", "email"),                      # "newsletter"→email unchanged
    #
    # "image optimization cdn" → "image"→media misfired; image CDN/optimization tools are File Management.
    ("image optimization cdn", "file"),                    # bigram "image optimization"→file (beats image→media)
    ("image optimization api", "file"),                    # same bigram
    # Regression — raw image/video queries still route to media.
    ("image processing video", "media"),                   # "image"→media unchanged when no "optimization" bigram
    # Probe pattern 59 — feedback-form collision / 3d dead zone / boilerplate-codegen collision / document-storage
    #
    # "feedback form" → "feedback"→feedback-reviews misfired; form builders (Typeform, Tally, Jotform)
    # for collecting feedback are Forms & Surveys, not Feedback & Reviews (Canny, ProductBoard).
    ("feedback form builder", "forms"),                    # bigram "feedback form"→forms (beats feedback→feedback)
    ("feedback form alternative", "forms"),                # bigram fires at pos 0
    # Regression — feedback/NPS tools still route to feedback-reviews.
    ("feedback widget nps", "feedback"),                   # bare "feedback"→feedback unchanged
    ("product feedback canny", "feedback"),                # "feedback"→feedback unchanged
    #
    # "3d modeling tool" → "3d" unmapped → raw_first. 3D tools (Three.js, Blender, Babylon.js) are Creative Tools.
    ("3d modeling tool", "creative"),                      # bare "3d"→creative
    ("3d rendering api", "creative"),                      # bare "3d"→creative
    ("3d modeling open source", "creative"),               # bigram "3d modeling"→creative
    #
    # "boilerplate code generator" → "code generator"→ai dev bigram fires at pos 1 (wrong).
    # "boilerplate code" bigram added at pos 0 to override.
    ("boilerplate code generator", "boilerplate"),         # bigram "boilerplate code"→boilerplate fires before "code generator"→ai dev
    ("boilerplate code nextjs", "boilerplate"),            # same bigram
    # Regression — generic code generator queries still route to ai dev.
    ("code generator openai api", "ai dev"),               # "code generator"→ai dev unchanged
    #
    # "document storage" → "document"→database misfired (document-store/MongoDB terminology).
    # Document storage APIs (Cloudflare R2, Filestack, Uploadcare) live in File Management.
    ("document storage api", "file"),                      # bigram "document storage"→file (beats document→database)
    ("document storage cloud", "file"),                    # bigram fires at pos 0
    # Regression — document database queries still route to database.
    ("document database couchdb", "database"),             # "document"→database unchanged
    # Probe pattern 60 — model-card dead zone
    #
    # "model card generator" → "model"→ai misfired; model cards are ML documentation for AI Standards.
    ("model card generator", "ai standards"),              # bigram "model card"→ai standards (beats model→ai)
    ("model cards documentation", "ai standards"),         # bigram "model cards"→ai standards
    # Regression — generic model queries still route to ai.
    ("language model api", "ai"),                          # "model"→ai unchanged
    # Probe pattern 61 — mono-repo spaced form / PR automation / security-testing collision /
    #                     dev-server dead zone / commit-lint spaced form
    #
    # Dead zones:
    # "mono repo tool" → raw_first ("mono" unmapped); "monorepo" was mapped but spaced form wasn't.
    # "pr automation github" → "automation"→ai misfired; PR bots live in DevOps.
    # "static application security testing" → "static"→frontend misfired; SAST lives in Security.
    # "dev server vite" → raw_first ("dev" and "server" both unmapped); Vite/webpack-dev-server are Frontend.
    # "commit lint setup" → "lint"→testing misfired; commitlint (and bare form) lives in DevOps.
    ("mono repo tool", "developer"),                       # bigram "mono repo"→developer (spaced form)
    ("mono repo architecture", "developer"),               # bigram "mono repo"→developer
    ("pr automation tool", "devops"),                      # bigram "pr automation"→devops (beats "automation"→ai)
    ("pr automation github", "devops"),                    # bigram "pr automation"→devops
    ("pr bot review", "devops"),                           # bigram "pr bot"→devops
    ("security testing pipeline", "security"),             # bigram "security testing"→security
    ("static application security testing", "security"),   # bigram "security testing" fires at pos 1-2
    ("dev server vite", "frontend"),                       # bigram "dev server"→frontend
    ("dev server setup", "frontend"),                      # bigram "dev server"→frontend
    ("commit lint setup", "devops"),                       # bigram "commit lint"→devops (beats "lint"→testing)
    ("commit lint husky", "devops"),                       # bigram "commit lint"→devops
    # Regressions — nearby tokens should not be affected.
    ("security audit tool", "security"),                   # "security"→security unchanged
    ("monorepo build tool", "developer"),                  # bare "monorepo"→developer unchanged
    ("pull request automation", "devops"),                 # "pull request"→devops bigram unchanged
    ("linting javascript", "testing"),                     # "linting"→testing unchanged
    # Probe pattern 62 — git branching strategy / preview-environment dead zones
    #
    # Dead zones:
    # "trunk based development" → "trunk"→frontend (Trunk.io collision; branching strategy is DevOps).
    # "gitflow branching" → raw_first "gitflow" (GitFlow is a git branching model — DevOps).
    # "branch protection rules" → raw_first "branch" (GitHub branch protection tooling — DevOps).
    # "feature branch deployment" → "feature"→feature-flags (git feature branches are DevOps).
    # "preview environment deployment" → "environment"→security (deploy preview envs are DevOps).
    # "staging environment" → "environment"→security (staging envs are DevOps infra).
    # "ephemeral environment" → "environment"→security (ephemeral deploy envs are DevOps).
    ("trunk based development", "devops"),     # bigram "trunk based"→devops (beats "trunk"→frontend)
    ("trunk based workflow", "devops"),        # bigram "trunk based"→devops
    ("gitflow alternative", "devops"),         # bare "gitflow"→devops
    ("gitflow branching strategy", "devops"),  # bare "gitflow"→devops fires first
    ("branch protection rules", "devops"),     # bigram "branch protection"→devops (branch was raw_first)
    ("branch protection github", "devops"),    # bigram "branch protection"→devops
    ("feature branch deployment", "devops"),   # bigram "feature branch"→devops (beats "feature"→feature)
    ("feature branch workflow", "devops"),     # bigram "feature branch"→devops
    ("preview environment deployment", "devops"),   # bigram "preview environment"→devops (beats environment→security)
    ("preview environment ci", "devops"),           # bigram "preview environment"→devops
    ("staging environment setup", "devops"),        # bigram "staging environment"→devops
    ("staging environment deployment", "devops"),   # bigram "staging environment"→devops
    ("ephemeral environment kubernetes", "devops"), # bigram "ephemeral environment"→devops
    ("ephemeral environment ci", "devops"),         # bigram "ephemeral environment"→devops
    # Regressions — nearby tokens should not be affected.
    ("trunk linter", "frontend"),              # bare "trunk"→frontend unchanged (Trunk.io linter)
    ("feature flag toggle", "feature"),        # "feature flag" bigram unchanged (different from "feature branch")
    ("feature toggle gradual", "feature"),     # "feature"→feature unchanged
    ("environment variables secrets", "security"),  # "environment"→security unchanged for secrets queries
    ("development environment setup", "devops"),    # "development environment"→devops unchanged
    # Probe pattern 63 — UI component dead zones / modal collision
    # "modal component"/"modal window" → bare "modal"→ai fires (Modal.com serverless collision).
    ("modal component react", "frontend"),     # bigram "modal component"→frontend (beats "modal"→ai)
    ("modal component shadcn", "frontend"),    # bigram "modal component"→frontend
    ("modal window component", "frontend"),    # bigram "modal window"→frontend (beats "modal"→ai)
    ("modal window library", "frontend"),      # bigram "modal window"→frontend
    # "dropdown"/"dropdown menu" → unmapped → raw_first; now routes to frontend.
    ("dropdown component", "frontend"),        # bare "dropdown"→frontend
    ("dropdown menu react", "frontend"),       # bigram "dropdown menu"→frontend (fires at pos 0 before bare "dropdown")
    ("dropdown menu accessible", "frontend"),  # bigram "dropdown menu"→frontend
    # "sorting" → unmapped → raw_first; now routes to frontend (TanStack Table, sortable libs).
    ("table sorting react", "frontend"),       # bare "sorting"→frontend fires at pos 1 (after "table"→frontend at pos 0)
    ("sorting library javascript", "frontend"), # bare "sorting"→frontend fires first
    # "infinite scroll" → both tokens unmapped → raw_first; bigram now routes to frontend.
    ("infinite scroll react", "frontend"),     # bigram "infinite scroll"→frontend
    ("infinite scroll component", "frontend"), # bigram "infinite scroll"→frontend
    # "select component" → bigram routes to frontend (React Select, Radix Select).
    ("select component accessible", "frontend"),  # bigram "select component"→frontend
    ("select component react", "frontend"),       # bigram "select component"→frontend
    # Regressions — modal bare token and modal dialog should not be affected.
    ("modal serverless python", "ai"),         # bare "modal"→ai unchanged (Modal.com)
    ("modal dialog component", "frontend"),    # "modal dialog"→frontend bigram (probe 38) still fires
    # Probe pattern 64 — component dead zones: storybook collision, custom element, PDF/image UI components
    # "storybook" → was "testing" (wrong — Storybook is a component dev environment, not a test runner);
    # now routes to "frontend". "storybook alternative" previously hit testing dead zone.
    ("storybook component", "frontend"),       # bare "storybook"→frontend (was testing)
    ("storybook alternative", "frontend"),     # "alternative" is stop word; bare "storybook"→frontend fires
    # "custom element" → bare "custom" was raw_first dead zone; bigram "custom element"→frontend now fires.
    ("custom element lit", "frontend"),        # bigram "custom element"→frontend before bare "custom"
    ("custom element accessible", "frontend"), # bigram "custom element"→frontend
    # "image cropper" → bare "image"→media misfired; bigram "image cropper"→frontend now fires first.
    ("image cropper react", "frontend"),       # bigram "image cropper"→frontend (beats "image"→media)
    ("image cropper component", "frontend"),   # bigram "image cropper"→frontend
    # "pdf viewer" → bare "pdf"→file misfired; bigram "pdf viewer"→frontend now fires first.
    ("pdf viewer react", "frontend"),          # bigram "pdf viewer"→frontend (beats "pdf"→file)
    ("pdf viewer component", "frontend"),      # bigram "pdf viewer"→frontend
    # Regressions — nearby pdf and image entries should not be affected.
    ("pdf generation node", "developer"),      # "pdf generation"→developer bigram unchanged
    ("pdf generator python", "developer"),     # "pdf generator"→developer bigram unchanged
    ("image processing", "media"),             # bare "image"→media unchanged (no cropper token)
    # Probe pattern 65 — realtime-collaboration dead zones and multi-model database collision.
    # "operational transform" → bare "operational" hits raw_first (OT collab algorithm — API Tools).
    # "shared editing" → bare "shared" hits raw_first (Yjs, ShareDB — API Tools).
    # "presence awareness"/"presence tracking" → bare "presence" hits raw_first (Liveblocks — API Tools).
    # "live cursors" → bare "live" hits raw_first (Liveblocks cursors — API Tools).
    # "multi model database" → "model"→ai fires before "database"→database (SurrealDB, FaunaDB → Database).
    ("operational transform sharedb", "api"),      # bigram "operational transform"→api
    ("operational transform algorithm", "api"),    # bigram "operational transform"→api
    ("shared editing yjs", "api"),                 # bigram "shared editing"→api
    ("shared editing crdt", "api"),                # bigram "shared editing"→api
    ("presence awareness liveblocks", "api"),      # bigram "presence awareness"→api
    ("presence awareness realtime", "api"),        # bigram "presence awareness"→api
    ("presence tracking realtime", "api"),         # "tracking" stripped → ["presence","realtime"] → "realtime"→api
    ("presence tracking partykit", "api"),         # "tracking" stripped → ["presence","partykit"] → "partykit"→api
    ("live cursors liveblocks", "api"),            # bigram "live cursors"→api
    ("live cursors component", "api"),             # bigram "live cursors"→api
    ("multi model database surreal", "database"),  # bigram "multi model"→database (beats "model"→ai)
    ("multi model db fauna", "database"),          # bigram "multi model"→database
    # Regressions — nearby tokens should not be affected.
    ("liveblocks realtime", "api"),                # "liveblocks"→api unchanged
    ("model serving", "ai"),                       # bare "model"→ai unchanged (no "multi" prefix)
    ("yjs crdt", "api"),                           # "yjs"→api unchanged
    # ── Probe pattern 66 (May 2026): UI-component second-pass + mind-map/collaborative dead zones ──
    # "mind map tool" → "map"→maps misfired; bigram "mind map"→developer now fires first.
    ("mind map tool", "developer"),                # bigram "mind map"→developer (beats "map"→maps)
    ("mind map react", "developer"),               # bigram "mind map"→developer
    # "mind mapping react" → both tokens unmapped → raw_first; bigram "mind mapping"→developer added.
    ("mind mapping react", "developer"),           # bigram "mind mapping"→developer
    ("mind mapping software", "developer"),        # bigram "mind mapping"→developer ("software" is stop word)
    # "mindmap react" → "mindmap" unmapped → raw_first; bare "mindmap"→developer added.
    ("mindmap open source", "developer"),          # bare "mindmap"→developer
    ("mindmap javascript", "developer"),           # bare "mindmap"→developer (beats "javascript"→frontend)
    # "markdown editor react" → "markdown"→documentation misfired; bigram "markdown editor"→frontend.
    ("markdown editor react", "frontend"),         # bigram "markdown editor"→frontend (beats "markdown"→docs)
    ("markdown editor wysiwyg", "frontend"),       # bigram "markdown editor"→frontend
    # "calendar component" → "calendar"→scheduling misfired; bigram "calendar component"→frontend.
    ("calendar component react", "frontend"),      # bigram "calendar component"→frontend (beats "calendar"→scheduling)
    ("calendar component accessible", "frontend"), # bigram "calendar component"→frontend
    # "toast notification react" → "toast"→notifications misfired; bigram "toast notification"→frontend.
    ("toast notification react", "frontend"),      # bigram "toast notification"→frontend (beats "toast"→notifications)
    ("toast notification library", "frontend"),    # bigram "toast notification"→frontend
    # "breadcrumb navigation" → "breadcrumb" unmapped → raw_first; bare "breadcrumb"→frontend added.
    ("breadcrumb navigation", "frontend"),         # bare "breadcrumb"→frontend
    ("breadcrumb component react", "frontend"),    # bare "breadcrumb"→frontend
    # "collaborative coding" → "collaborative"→api misfired; bigram "collaborative coding"→developer.
    ("collaborative coding tool", "developer"),    # bigram "collaborative coding"→developer (beats "collaborative"→api)
    ("collaborative coding ide", "developer"),     # bigram "collaborative coding"→developer
    # Regressions — nearby tokens should not be affected.
    ("map tiles leaflet", "maps"),                 # bare "map"→maps unchanged (map tiles are Maps & Location)
    ("markdown parser", "documentation"),          # bare "markdown"→docs unchanged (no "editor" token)
    ("calendar api", "scheduling"),                # bare "calendar"→scheduling unchanged (no "component" token)
    ("toast pop up", "notifications"),             # bare "toast"→notifications unchanged (no "notification" token)
    ("collaborative editing", "api"),              # bare "collaborative"→api unchanged (not "coding")
    # ── Probe pattern 67 (May 2026): ETL / metrics / billing / back-office dead zones ──
    # "extract transform load" → bare "load"→testing misfired; bigram "transform load"→background.
    ("extract transform load", "background"),      # bigram "transform load"→background (beats "load"→testing)
    ("extract transform pipeline", "background"),  # bigram "extract transform"→background
    # "metrics collection" → bare "metrics"→analytics misfired; bigram "metrics collection"→monitoring.
    ("metrics collection open source", "monitoring"),  # bigram "metrics collection"→monitoring (beats "metrics"→analytics)
    ("metrics server k8s", "monitoring"),          # bigram "metrics server"→monitoring
    # "metered billing" / "usage billing" → "metered"/"usage"→invoicing misfired; bigrams→payments.
    ("metered billing stripe", "payments"),        # bigram "metered billing"→payments (beats "metered"→invoicing)
    ("metered billing open source", "payments"),   # bigram "metered billing"→payments
    ("usage billing saas", "payments"),            # bigram "usage billing"→payments (beats "usage"→invoicing)
    ("usage based pricing", "payments"),           # bigram "usage based"→payments
    ("consumption billing api", "payments"),       # bigram "consumption billing"→payments
    # "backoffice" → unmapped → raw_first; bare "backoffice"→developer added.
    ("backoffice builder", "developer"),           # bare "backoffice"→developer
    ("back office admin react", "developer"),      # bigram "back office"→developer
    # Regressions — nearby tokens should not be affected.
    ("load testing nodejs", "testing"),            # bare "load"→testing unchanged (not preceded by "transform")
    ("metrics dashboard react", "analytics"),      # bare "metrics"→analytics unchanged (no "collection"/"server" token)
    ("usage tracking", "invoicing"),               # bare "usage"→invoicing unchanged (not preceded by "based"/"billing")
    # ── Probe pattern 68 (May 2026): MCP protocol / file-watcher / AI alignment dead zones ──
    # "model context protocol" → "model"→ai misfired; bigram "model context"→mcp added.
    ("model context protocol", "mcp"),             # bigram "model context"→mcp (beats "model"→ai)
    ("model context mcp server", "mcp"),           # bigram "model context"→mcp
    # "context protocol" → "context"→frontend misfired; bigram "context protocol"→mcp added.
    ("context protocol spec", "mcp"),              # bigram "context protocol"→mcp (beats "context"→frontend)
    # "ai alignment" → both unmapped → raw_first; bigram "ai alignment"→ai standards added.
    ("ai alignment research", "ai standards"),     # bigram "ai alignment"→ai standards
    ("ai alignment tools", "ai standards"),        # bigram "ai alignment"→ai standards
    # "file watcher" → unmapped; bare "watcher"→developer + bigram "file watcher"→developer added.
    ("file watcher nodejs", "developer"),          # bigram "file watcher"→developer
    ("file watcher rust", "developer"),            # bigram "file watcher"→developer
    ("filesystem watcher", "developer"),           # bare "watcher"→developer
    # Regressions — nearby tokens must not be affected.
    ("model deployment cloud", "ai"),              # bare "model"→ai unchanged (not followed by "context")
    ("react context api", "frontend"),             # "react"→frontend fires before bigram check (framework term)
    ("context menu react", "frontend"),            # bare "context"→frontend unchanged (not followed by "protocol")
    # ── Probe pattern 69 (May 2026): DB GUI / distributed SQL / VoIP / big-data dead zones ──
    # "pgadmin" → raw_first dead zone; DB GUI tools live in Developer Tools (like TablePlus, DBeaver).
    ("pgadmin alternative", "developer"),          # bare "pgadmin"→developer
    ("pgadmin open source", "developer"),          # bare "pgadmin"→developer
    # "trino" / "presto" → raw_first dead zones; distributed SQL engines belong in Database.
    ("trino alternative", "database"),             # bare "trino"→database
    ("trino sql", "database"),                     # bare "trino"→database
    ("presto alternative", "database"),            # bare "presto"→database
    ("presto distributed sql", "database"),        # bare "presto"→database (beats "sql"→database)
    # "voip" / "sip" → raw_first dead zones; VoIP tools live in Notifications (Twilio, Telnyx, Vonage).
    ("voip api", "notifications"),                 # bare "voip"→notifications (beats "api"→api at pos 1)
    ("voip sdk nodejs", "notifications"),          # bare "voip"→notifications fires first
    ("sip server", "notifications"),               # bare "sip"→notifications
    ("sip trunk provider", "notifications"),       # bare "sip"→notifications fires first
    # "hbase" / "druid" / "rethinkdb" / "janusgraph" / "hadoop" → raw_first dead zones.
    ("hbase alternative", "database"),             # bare "hbase"→database
    ("hbase nosql", "database"),                   # bare "hbase"→database
    ("druid alternative", "database"),             # bare "druid"→database
    ("druid olap", "database"),                    # bare "druid"→database (beats "olap"→database)
    ("rethinkdb alternative", "database"),         # bare "rethinkdb"→database
    ("janusgraph graph", "database"),              # bare "janusgraph"→database
    ("hadoop mapreduce", "background"),            # bare "hadoop"→background
    ("hadoop alternative", "background"),          # bare "hadoop"→background
    # Regressions — nearby tokens must not be affected.
    ("tableplus alternative", "developer"),        # "tableplus"→developer unchanged (already mapped)
    ("dbeaver alternative", "developer"),          # "dbeaver"→developer unchanged (already mapped)
    ("kafka alternative", "message"),              # "kafka"→message unchanged (not Hadoop)
    ("voip integration", "notifications"),         # "voip"→notifications (integration is stop word)
    # ── Probe pattern 70 (May 2026): Frontend UI / color / font / payments micro dead zones ──
    # "palette" → raw_first; color palette tools (Coolors, Paletton) live in Frontend Frameworks.
    ("palette generator", "frontend"),             # bare "palette"→frontend
    ("color palette react", "frontend"),           # "color"→frontend fires at pos 0 (palette reinforces)
    # "typeface" → raw_first; font/typeface tools (Fontjoy, Bunny Fonts) live in Frontend Frameworks.
    ("typeface pairing", "frontend"),              # bare "typeface"→frontend
    ("typeface tool", "frontend"),                 # bare "typeface"→frontend ("tool" is stop word)
    # "micropayment"/"micropayments" → raw_first; micropayment APIs live in Payments.
    ("micropayment api", "payments"),              # bare "micropayment"→payments fires first
    ("micropayments stripe", "payments"),          # bare "micropayments"→payments fires first
    # "virtualization"/"virtualisation" → raw_first; virtual list libs live in Frontend Frameworks.
    ("virtualization react", "frontend"),          # bare "virtualization"→frontend fires first
    ("list virtualization react", "frontend"),     # bare "virtualization"→frontend (at pos 1)
    ("list virtualisation", "frontend"),           # British spelling → bare "virtualisation"→frontend
    # "multi select" → raw_first; multiselect UI components live in Frontend Frameworks.
    ("multi select react", "frontend"),            # bigram "multi select"→frontend
    ("multi select accessible", "frontend"),       # bigram "multi select"→frontend
    # "progress bar" → raw_first; progress indicator components live in Frontend Frameworks.
    ("progress bar react", "frontend"),            # bigram "progress bar"→frontend
    ("progress bar component", "frontend"),        # bigram "progress bar"→frontend ("component"→frontend also fires)
    # "skeleton loader" → raw_first; skeleton loading UI libs live in Frontend Frameworks.
    ("skeleton loader react", "frontend"),         # bigram "skeleton loader"→frontend
    ("skeleton loading component", "frontend"),    # bare "component"→frontend (skeleton loading bigram not needed)
    # "loading spinner" → raw_first; spinner components live in Frontend Frameworks.
    ("loading spinner react", "frontend"),         # bigram "loading spinner"→frontend
    ("loading spinner component", "frontend"),     # bigram "loading spinner"→frontend ("component"→frontend also)
    # Regressions — nearby tokens must not be affected.
    ("payment processing", "payments"),            # "payment"→payments unchanged (not micropayment)
    ("stripe payments", "payments"),               # "stripe"→payments unchanged
    ("color picker", "frontend"),                  # "color"→frontend unchanged (palette didn't break it)
    # ── Probe pattern 71 (May 2026): AI prompting techniques + auth/security acronym dead zones ──
    # "constitutional ai" → raw_first; Constitutional AI (Anthropic) belongs in AI Standards.
    ("constitutional ai tools", "ai standards"),   # bigram "constitutional ai"→ai standards
    ("constitutional ai research", "ai standards"),# bigram "constitutional ai"→ai standards
    # "chain of thought" → "of" stripped → "chain thought" bigram; belongs in AI & Automation.
    ("chain of thought prompting", "ai"),          # bigram "chain thought"→ai (stop word "of" stripped)
    ("chain of thought reasoning", "ai"),          # bigram "chain thought"→ai
    # "few shot" bigram → AI & Automation.
    ("few shot learning", "ai"),                   # bigram "few shot"→ai
    ("few shot prompting", "ai"),                  # bigram "few shot"→ai
    # "zero shot" bigram → AI & Automation.
    ("zero shot classification", "ai"),            # bigram "zero shot"→ai
    ("zero shot inference", "ai"),                 # bigram "zero shot"→ai
    # "rls" / "row level" → Authentication (access control, same tier as rbac/permissions).
    ("rls supabase", "authentication"),            # bare "rls"→authentication
    ("rls policy postgres", "authentication"),     # bare "rls"→authentication (fires before "postgres"→database)
    ("row level security", "authentication"),      # bigram "row level"→authentication ("security" is stop word)
    ("row level access", "authentication"),        # bigram "row level"→authentication
    # Regressions — nearby tokens must not be affected.
    ("rlhf training", "ai"),                       # "rlhf"→ai unchanged (not rls)
    ("rbac permissions", "authentication"),        # "rbac"→authentication unchanged
    ("zero downtime deploy", "devops"),            # "zero downtime" bigram→devops unchanged (not "zero shot")
    # ── Probe pattern 72 (May 2026): Date/time picker UI + SEO structured data dead zones ──
    # "time picker" → raw_first; time picker UI components live in Frontend Frameworks.
    ("time picker react", "frontend"),             # bigram "time picker"→frontend
    ("time picker accessible", "frontend"),        # bigram "time picker"→frontend
    ("timepicker component", "frontend"),          # bare "timepicker"→frontend (compound form)
    # "structured data" → raw_first; JSON-LD / schema.org structured data belongs in SEO Tools.
    ("structured data json-ld", "seo"),            # bigram "structured data"→seo
    ("structured data generator", "seo"),          # bigram "structured data"→seo
    # "schema markup" → routes via bare "schema"→developer without bigram; schema.org markup → SEO.
    ("schema markup generator", "seo"),            # bigram "schema markup"→seo (beats bare "schema"→developer)
    ("schema markup testing", "seo"),              # bigram "schema markup"→seo
    # "schema org" → raw_first without mapping; schema.org vocabulary → SEO Tools.
    ("schema org validator", "seo"),               # bigram "schema org"→seo
    ("schema org types", "seo"),                   # bigram "schema org"→seo
    # Regressions — nearby tokens must not be affected.
    ("schema validation library", "developer"),    # bare "schema"→developer unchanged (not schema.org)
    ("json schema validator", "developer"),        # "json"→developer unchanged
    ("date picker react", "frontend"),             # "date"→frontend unchanged (not "time picker")
    ("structured logs", "logging"),                # "logs"→logging unchanged (not "structured data")
    ("structured output llm", "ai"),               # "output"→ai fires; "structured" stops before "output"
    # ── Probe pattern 73 (May 2026): "click" UI collision / file-upload component / WebGL graphics / masked-input ──
    # WebGL / graphics dead zones — bare tokens fired raw_first.
    ("glsl shader editor", "frontend"),            # bare "glsl"→frontend (WebGL shader language)
    ("shader programming webgl", "frontend"),      # bare "shader"→frontend (overrides raw_first)
    ("opengl library javascript", "frontend"),     # bare "opengl"→frontend (OpenGL → WebGL context)
    # File upload / image upload UI component collision — "upload"→file, "image"→media fire wrong.
    ("file upload react component", "frontend"),   # bigram "file upload"→frontend (overrides "upload"→file)
    ("file upload dropzone library", "frontend"),  # bigram "file upload"→frontend (fires before "upload"→file)
    ("image upload widget react", "frontend"),     # bigram "image upload"→frontend (overrides "image"→media)
    ("image editor javascript react", "frontend"), # bigram "image editor"→frontend (overrides "image"→media)
    # "click" UI collision — bare "click"→cli (Python Click) fires for non-CLI UI/analytics queries.
    # NOTE: "click tracking" bigram CANNOT fire — "tracking" is in _FTS_STOP_WORDS.
    ("right click menu react", "frontend"),        # bigram "right click"→frontend (context menus; overrides "click"→cli)
    ("right click context menu", "frontend"),      # bigram "right click"→frontend
    ("click outside hook react", "frontend"),      # bigram "click outside"→frontend (overrides "click"→cli)
    ("use click outside react", "frontend"),       # bigram "click outside"→frontend
    ("click heatmap analytics", "analytics"),      # bigram "click heatmap"→analytics (overrides "click"→cli)
    # Masked input / number input UI components — raw_first or wrong category without bigrams.
    ("masked input react", "frontend"),            # bigram "masked input"→frontend (imask.js, Cleave.js)
    ("masked input component", "frontend"),        # bare "masked"→frontend
    ("number input component react", "frontend"),  # bigram "number input"→frontend (overrides "number"→developer)
    ("number format react", "frontend"),           # bigram "number format"→frontend (react-number-format)
    ("photo crop react", "frontend"),              # bigram "photo crop"→frontend (Cropper.js, react-image-crop)
    # Regressions — existing mappings must not be affected.
    ("click python cli", "cli"),                   # bare "click"→cli unchanged (Python Click framework)
    ("click map tool", "analytics"),               # "click map" bigram→analytics unchanged
    ("upload file storage api", "file"),           # bare "upload"→file still fires when no bigram at i=0
    ("number parsing utility", "developer"),       # bare "number"→developer unchanged (no input/format bigram)
    ("image optimization cdn", "file"),            # "image optimization" bigram→file still fires
    ("shader editor vscode", "frontend"),          # "shader"→frontend + "editor" both route frontend
    # ── Probe pattern 74 (May 2026): VoIP/telephony voice collision / service-worker PWA / product-tour dead zones ──
    # "voice call" bigram → Notifications (VoIP/telephony, overrides bare "voice"→ai).
    ("voice call api", "notifications"),           # bigram "voice call"→notifications (Twilio Voice, Telnyx)
    ("voice call sdk", "notifications"),           # bigram "voice call"→notifications
    ("voice calling library", "notifications"),    # bigram "voice call"→notifications (stops at "calling" → "call" stem? no — "calling" not "call")
    # "phone call" bigram → Notifications (telephony, overrides bare "phone"→authentication).
    ("phone call api", "notifications"),           # bigram "phone call"→notifications
    ("phone call automation", "notifications"),    # bigram "phone call"→notifications
    # "service worker pwa" — "service" is a stop word; "worker pwa" bigram fires instead.
    ("service worker pwa", "frontend"),            # bigram "worker pwa"→frontend (service stripped as stop word)
    ("worker pwa integration", "frontend"),        # bigram "worker pwa"→frontend
    # "feature tour" bigram → Frontend Frameworks (overrides bare "feature"→feature-flags).
    ("feature tour component", "frontend"),        # bigram "feature tour"→frontend
    ("feature tour react", "frontend"),            # bigram "feature tour"→frontend
    # "walkthrough" bare → Frontend Frameworks (product tour/onboarding libraries).
    ("walkthrough guide library", "frontend"),     # bare "walkthrough"→frontend
    ("interactive walkthrough tool", "frontend"),  # bigram "interactive walkthrough"→frontend
    # "introjs" → Frontend Frameworks (named library, was raw_first).
    ("introjs alternative", "frontend"),           # bare "introjs"→frontend
    ("introjs tutorial", "frontend"),              # bare "introjs"→frontend (fires before "tutorial"→learning)
    # "interactive demo" bigram → Frontend Frameworks.
    ("interactive demo library", "frontend"),      # bigram "interactive demo"→frontend
    ("interactive demo react", "frontend"),        # bigram "interactive demo"→frontend
    # Regressions — nearby tokens must not be affected.
    ("voice synthesis api", "ai"),                 # bare "voice"→ai unchanged (voice AI, not telephony)
    ("voice cloning tool", "ai"),                  # bare "voice"→ai unchanged (ElevenLabs, etc.)
    ("phone verification api", "authentication"),  # bare "phone"→authentication unchanged (not "phone call")
    ("phone otp sms", "authentication"),           # bare "phone"→authentication unchanged
    ("feature flag management", "feature"),        # bare "feature"→feature-flags unchanged (not "feature tour")
    ("feature toggle library", "feature"),         # bare "toggle"→feature-flags unchanged
    ("interactive tutorial", "learning"),          # bare "tutorial"→learning unchanged (not "interactive demo/walkthrough")
    ("worker thread nodejs", "background"),        # bare "worker"→background unchanged (not "worker pwa")
    # ── Probe pattern 75 (May 2026): LLM response streaming / HTTP streaming / Node.js stream dead zones ──
    # "api response" bigram → API Tools (fires before bare "streaming"→media for streaming API queries).
    ("streaming api response nodejs", "api"),      # bigram "api response"→api (overrides "streaming"→media)
    ("streaming response react", "api"),           # bigram "streaming response"→api
    ("streaming response nodejs", "api"),          # bigram "streaming response"→api
    # "readable stream" bigram → API Tools (overrides "stream"→message for Node.js stream queries).
    ("readable stream nodejs", "api"),             # bigram "readable stream"→api
    ("readable stream browser", "api"),            # bigram "readable stream"→api
    # "stream ai" bigram → AI & Automation (overrides "stream"→message).
    ("stream ai response", "ai"),                  # bigram "stream ai"→ai
    ("stream ai output", "ai"),                    # bigram "stream ai"→ai
    # "token streaming" bigram → AI & Automation (overrides "token"→authentication).
    ("token streaming react", "ai"),               # bigram "token streaming"→ai
    ("token streaming llm", "ai"),                 # bigram "token streaming"→ai
    # "llm streaming" bigram → AI & Automation (reverse of "streaming llm"→ai already mapped).
    ("llm streaming response", "ai"),              # bigram "llm streaming"→ai (also works via bare "llm"→ai)
    ("llm streaming python", "ai"),                # bigram "llm streaming"→ai
    # "eventsource" compound → API Tools (spaced "event source" unfixable: "source" is stop word).
    ("eventsource browser", "api"),                # bare "eventsource"→api
    ("eventsource javascript", "api"),             # bare "eventsource"→api
    # Regressions — nearby patterns must not be affected.
    ("video streaming api", "media"),              # "video"→media fires before "streaming api" (no "streaming api" mapping)
    ("audio streaming", "media"),                  # bare "audio"→media unchanged
    ("live streaming", "media"),                   # bare "streaming"→media unchanged (no earlier match)
    ("jwt token refresh", "authentication"),       # bare "token"→auth (bigram "jwt token" not mapped, "token"→auth fires)
    ("event driven architecture", "message"),      # bare "event"→message unchanged
    ("data streaming kafka", "message"),           # bigram "data streaming"→message unchanged
    # ── Probe pattern 76 (May 2026): AI document-processing + image-AI dead zones ──
    # "image captioning" bigram → AI & Automation (overrides bare "image"→media).
    ("image captioning api", "ai"),                # bigram "image captioning"→ai (BLIP, LLaVA, GPT-4V vision)
    ("image captioning model", "ai"),              # bigram "image captioning"→ai
    # "text extraction" bigram → AI & Automation (was raw_first).
    ("text extraction nlp", "ai"),                 # bigram "text extraction"→ai (spaCy, Textract, Tika)
    ("text extraction python", "ai"),              # bigram "text extraction"→ai
    # "document parsing" bigram → AI & Automation (overrides bare "document"→database).
    ("document parsing api", "ai"),                # bigram "document parsing"→ai (LlamaParse, unstructured.io)
    ("document parsing python", "ai"),             # bigram "document parsing"→ai
    # "pdf parsing" bigram → AI & Automation (overrides bare "pdf"→file).
    ("pdf parsing python", "ai"),                  # bigram "pdf parsing"→ai (AI/RAG PDF extraction)
    ("pdf parsing api", "ai"),                     # bigram "pdf parsing"→ai
    # "document understanding" bigram → AI & Automation (overrides bare "document"→database).
    ("document understanding model", "ai"),        # bigram "document understanding"→ai (LayoutLM, DocTR)
    ("document understanding azure", "ai"),        # bigram "document understanding"→ai (Azure Form Recognizer)
    # Regressions — existing document/image/pdf routing must not be affected.
    ("document database", "database"),             # bare "document"→database unchanged (second loop fires)
    ("document chunker python", "database"),       # bare "document"→database unchanged (bigram "document chunker" not mapped)
    ("document qa tool", "ai"),                    # bigram "document qa"→ai unchanged (existing bigram)
    ("image upload react", "frontend"),            # bigram "image upload"→frontend unchanged
    ("pdf viewer react", "frontend"),              # bigram "pdf viewer"→frontend unchanged
    # ── Probe pattern 77 (May 2026): "image to text" / "pdf to text" stop-word-stripped bigrams ──
    # "to" is in _FTS_STOP_WORDS — "image to text" reduces to bigram "image text" after stripping.
    ("image to text api", "ai"),                   # bigram "image text"→ai (to=stop word; EasyOCR, Textract)
    ("pdf to text python", "ai"),                  # bigram "pdf text"→ai (to=stop word; pdfplumber, LlamaParse)
    # Regressions — adjacent routing must not change.
    ("image upload react", "frontend"),            # bigram "image upload"→frontend unchanged
    ("image captioning api", "ai"),                # bigram "image captioning"→ai unchanged (probe 76)
    ("pdf viewer react", "frontend"),              # bigram "pdf viewer"→frontend unchanged
    ("pdf parsing python", "ai"),                  # bigram "pdf parsing"→ai unchanged (probe 76)
    # ── Probe pattern 78 (May 2026): business intelligence / headless automation / kill switch / user behavior / multivariate dead zones ──
    # "business intelligence" bigram → Analytics (bare "business"→raw_first was missing the spaced form).
    ("business intelligence tool", "analytics"),   # bigram "business intelligence"→analytics (Metabase, Redash, Superset)
    ("business intelligence dashboard", "analytics"), # bigram "business intelligence"→analytics
    # "headless automation" bigram → Testing (overrides bare "headless"→cms).
    ("headless automation puppeteer", "testing"),  # bigram "headless automation"→testing (Playwright, Browserless)
    ("headless automation server", "testing"),     # bigram "headless automation"→testing
    # "kill switch" bigram → Feature Flags (kill switch = instant feature disable without redeploy).
    ("kill switch feature", "feature"),            # bigram "kill switch"→feature-flags
    ("kill switch deployment", "feature"),         # bigram "kill switch"→feature-flags
    # "multivariate" bare token → Feature Flags (A/B + multiple variants experimentation).
    ("multivariate test", "feature"),             # bare "multivariate"→feature-flags
    ("multivariate testing react", "feature"),    # bare "multivariate"→feature-flags
    # "user behavior" bigram → Analytics (PostHog, FullStory, Heap, Mixpanel behavioural analytics).
    ("user behavior tracking", "analytics"),      # bigram "user behavior"→analytics (stop-word "tracking" stripped)
    ("user behavior analytics", "analytics"),     # bigram "user behavior"→analytics
    # Regressions — nearby routes must not change.
    ("business logic validation", "developer"),    # "validation"→developer unchanged; "business"→raw_first doesn't override
    ("headless cms", "cms"),                       # bare "headless"→cms unchanged for headless-cms queries
    ("headless browser testing", "testing"),       # bigram "headless browser"→testing unchanged
    ("feature flag toggle", "feature"),            # bare "feature"→feature-flags unchanged
    ("ab testing tool", "feature"),                # bare "ab"→feature-flags unchanged (probe 77 region)
    ("user research tool", "feedback"),            # bigram "user research"→feedback unchanged (probe 35)
    ("user authentication", "authentication"),     # "user"→raw_first; "authentication"→auth fires second token unchanged
    # ── Probe pattern 79 (May 2026): MLops drift / experiment tracking / graph-RAG / DevEx dead zones ──
    # "drift" bare → AI (Evidently, NannyML, Alibi Detect — MLops data drift monitoring).
    ("drift detection", "ai"),                     # bare "drift"→ai (data/concept drift detection)
    ("data drift detection", "ai"),                # bigram "data drift"→ai (MLops monitoring)
    ("concept drift ml", "ai"),                    # bigram "concept drift"→ai (distribution shift detection)
    # "ml experiment" → AI via "ml" (MLflow/W&B queries with "ml" prefix route correctly).
    # NOTE: "experiment tracking [tool]" can't use a bigram — "tracking" is in _FTS_STOP_WORDS.
    # "ml experiment tracking" routes via "ml"→ai; bare "mlflow"/"wandb" route directly to ai.
    ("ml experiment tracking", "ai"),              # bare "ml"→ai (MLflow, W&B, Neptune MLops context)
    # "graph rag" bigram → AI (knowledge-graph RAG; LlamaIndex, LangChain, Neo4j).
    ("graph rag llama", "ai"),                     # bigram "graph rag"→ai
    ("graph rag neo4j", "ai"),                     # bigram "graph rag"→ai
    # "experimentation platform" bare → Feature Flags (Statsig, Optimizely, Split, VWO).
    ("experimentation platform", "feature"),       # bare "experimentation"→feature-flags
    # "entitlement" → Feature Flags (plan-tier feature access; Unleash, LaunchDarkly).
    ("entitlement management saas", "feature"),    # bigram "entitlement management"→feature-flags
    ("entitlement check api", "feature"),          # bare "entitlement"→feature-flags
    # "golden path" → Developer Tools (IDP concept; Backstage, Port, Cortex).
    ("golden path backstage", "developer"),        # bigram "golden path"→developer
    ("golden path idp", "developer"),              # bigram "golden path"→developer
    # "dx" bare → Developer Tools (developer experience abbreviation).
    ("dx tooling", "developer"),                   # bare "dx"→developer
    ("dx platform", "developer"),                  # bare "dx"→developer
    # CRM — enrichment dead zones (Clearbit, Clay, Apollo, Cognism; bare "data/contact/company" fire raw_first).
    ("data enrichment clearbit", "crm"),           # bigram "data enrichment"→crm
    ("contact enrichment api", "crm"),             # bigram "contact enrichment"→crm
    ("company enrichment apollo", "crm"),          # bigram "company enrichment"→crm
    ("enrichment pipeline", "crm"),                # bare "enrichment"→crm
    # CRM — buyer intent dead zone (Bombora, G2 Intent, Clearbit Intent; bare "buyer" unmapped).
    ("buyer intent data", "crm"),                  # bigram "buyer intent"→crm
    ("buyer signals platform", "crm"),             # bare "buyer"→crm
    # Frontend — "user interface library" dead zone (bare "user" → raw_first).
    ("user interface library", "frontend"),        # bigram "user interface"→frontend
    ("user interface component react", "frontend"), # bigram "user interface"→frontend
    # Frontend — "theming" bare token (Tailwind themes, CSS-in-JS, shadcn theme).
    ("theming library css", "frontend"),           # bare "theming"→frontend
    ("theming react", "frontend"),                 # bare "theming"→frontend
    # Regressions — adjacent routes must not break.
    ("graph database surreal", "database"),        # bare "graph"→database unchanged for DB queries
    ("ab experiment", "feature"),                  # bare "ab"→feature unchanged for A/B testing
    ("growth experiment", "feature"),              # bare "experiment"→feature unchanged for standalone
    ("model drift", "ai"),                         # bare "model"→ai unchanged for model-monitoring queries
    ("lead enrichment", "crm"),                    # bare "lead"→crm unchanged (lead enrichment via lead token)
    ("user authentication", "authentication"),     # "user interface" bigram doesn't break auth routing
    # ── Probe pattern 80 (May 2026): attribution / UTM / PLG / CRO / DAU/MAU dead zones ──
    # "attribution" bare → Analytics (Rockerbox, Triple Whale, Northbeam, Segment attribution).
    ("attribution tool", "analytics"),             # bare "attribution"→analytics
    ("click attribution", "analytics"),            # bare "attribution"→analytics at position 1
    # "marketing attribution" bigram → Analytics.
    ("marketing attribution software", "analytics"), # bigram "marketing attribution"→analytics
    # "multi touch attribution" → Analytics via bigram "multi touch" at i=1.
    ("multi touch attribution", "analytics"),      # bigram "multi touch"→analytics
    # "utm" bare → Analytics (UTM parameter builders/trackers; "tracking" is a stop word).
    ("utm builder", "analytics"),                  # bare "utm"→analytics
    ("utm tracker", "analytics"),                  # bare "utm"→analytics ("tracking" stripped)
    # "cro" bare → Analytics (Conversion Rate Optimization tools).
    ("cro tool", "analytics"),                     # bare "cro"→analytics
    ("cro software", "analytics"),                 # bare "cro"→analytics
    # "conversion" bare → Analytics (stop-word "tracking" stripped; bare conv fires).
    ("conversion tracking", "analytics"),          # bare "conversion"→analytics ("tracking" stripped)
    ("conversion metrics", "analytics"),           # bare "conversion"→analytics
    # "product led growth" → Analytics via bigram "led growth" at i=1 in pre-pass.
    ("product led growth", "analytics"),           # bigram "led growth"→analytics
    ("product led growth tool", "analytics"),      # bigram "led growth"→analytics ("tool" stripped)
    # "growth hacking" bigram → Analytics.
    ("growth hacking tool", "analytics"),          # bigram "growth hacking"→analytics
    ("growth hacking analytics", "analytics"),     # bigram "growth hacking"→analytics
    # "plg" bare → Analytics (Product-Led Growth abbreviation).
    ("plg tool", "analytics"),                     # bare "plg"→analytics
    ("plg saas", "analytics"),                     # bare "plg"→analytics
    # "activation" bare → Analytics (user lifecycle / product analytics).
    ("user activation", "analytics"),              # bare "activation"→analytics at position 1
    ("activation rate", "analytics"),              # bare "activation"→analytics
    ("activation funnel", "analytics"),            # bare "activation"→analytics
    # "dau"/"mau" bare → Analytics (engagement metric dashboards).
    ("dau tracking", "analytics"),                 # bare "dau"→analytics ("tracking" stripped)
    ("mau dashboard", "analytics"),                # bare "mau"→analytics
    ("dau mau ratio", "analytics"),                # bare "dau"→analytics at i=0
    # "heap" bare → Analytics (Heap Analytics; no memory-heap collision).
    ("heap analytics alternative", "analytics"),   # bare "heap"→analytics
    ("heap io", "analytics"),                      # bare "heap"→analytics
    # "inspectlet" bare → Analytics (session recording and heatmaps).
    ("inspectlet alternative", "analytics"),       # bare "inspectlet"→analytics
    # Regressions — nearby routes must not break.
    ("conversion rate optimization", "analytics"), # bigram "conversion rate"→analytics unchanged
    ("memory heap javascript", "caching"),         # "memory"→caching fires before bare "heap"→analytics
    ("ab testing conversion", "feature"),          # bare "ab"→feature-flags wins over "conversion"→analytics
    ("product roadmap", "project"),                # bare "roadmap"→project unchanged
    ("product feedback", "feedback"),              # bare "feedback"→feedback unchanged
    ("growth experiment", "feature"),              # bare "experiment"→feature unchanged (no bare "growth")
    ("lead generation", "crm"),                    # bare "lead"→crm unchanged
    ("email conversion", "email"),                 # bare "email"→email wins over "conversion"→analytics
    # ── Probe pattern 81 (May 2026): RevOps / ABM / CDP / Customer-Success dead zones ──
    # "revops" bare → CRM (Revenue Operations platforms: Clari, Gong, Revenue.io).
    ("revops tool", "crm"),                        # bare "revops"→crm
    ("revops saas", "crm"),                        # bare "revops"→crm
    # "demand" bare → CRM (demand generation/ABM: 6sense, Demandbase, Terminus).
    ("demand generation", "crm"),                  # bare "demand"→crm
    ("demand gen", "crm"),                         # bare "demand"→crm
    # "abm" bare → CRM (Account-Based Marketing abbreviation).
    ("abm tool", "crm"),                           # bare "abm"→crm
    ("abm software", "crm"),                       # bare "abm"→crm
    # "account based" bigram → CRM (ABM strategy tools).
    ("account based marketing", "crm"),            # bigram "account based"→crm
    ("account based selling", "crm"),              # bigram "account based"→crm
    # "customer success" bigram → CRM (Gainsight, ChurnZero, Vitally).
    ("customer success tool", "crm"),              # bigram "customer success"→crm
    ("customer success saas", "crm"),              # bigram "customer success"→crm
    # "cdp" bare → Analytics (Customer Data Platform: Segment, RudderStack, mParticle).
    ("cdp tool", "analytics"),                     # bare "cdp"→analytics
    ("cdp alternative", "analytics"),              # bare "cdp"→analytics
    # "customer data" bigram → Analytics (CDP context; "platform" is a stop word).
    ("customer data platform", "analytics"),       # bigram "customer data"→analytics ("platform" stripped)
    ("customer data pipeline", "analytics"),       # bigram "customer data"→analytics
    # "net promoter" bigram → Feedback (NPS survey tools).
    ("net promoter score", "feedback"),            # bigram "net promoter"→feedback
    ("net promoter survey", "feedback"),           # bigram "net promoter"→feedback
    # Regressions — nearby routes must not break.
    ("revenue analytics", "analytics"),            # bare "revenue"→analytics unchanged
    ("lead scoring crm", "crm"),                   # bare "lead"→crm unchanged
    ("sales intelligence", "crm"),                 # bare "sales"→crm unchanged
    ("nps survey", "feedback"),                    # bare "nps"→feedback unchanged
    ("demand planning", "crm"),                    # bare "demand"→crm (supply chain planning not in catalog)
    ("data pipeline etl", "background"),           # bare "data"→? → "pipeline"→background unchanged
    # Probe pattern 82 (May 2026): segmentation / user journey / ATS / HR dead zones.
    # "customer segmentation" fired raw_first "customer" — segmentation analytics tools
    # (Mixpanel, Amplitude, Braze) belong in Analytics.
    # "user/audience segmentation" also fired raw_first. "user journey" (FullStory, Amplitude) → Analytics.
    # "applicant tracking system" (ATS) and "hr software" (BambooHR, Rippling) belong in CRM.
    ("customer segmentation tool", "analytics"),   # bigram "customer segmentation"→analytics
    ("user segmentation", "analytics"),            # bare "segmentation"→analytics
    ("audience segmentation", "analytics"),        # bare "audience"→analytics
    ("audience analytics", "analytics"),           # bare "audience"→analytics
    ("user journey analytics", "analytics"),       # bigram "user journey"→analytics
    ("user journey funnel", "analytics"),          # bigram "user journey"→analytics
    ("applicant tracking system", "crm"),          # bare "applicant"→crm (ATS tools: Lever, Ashby, Greenhouse)
    ("ats software", "crm"),                       # bare "ats"→crm (ATS abbreviation)
    ("hr management tool", "crm"),                 # bare "hr"→crm (BambooHR, Rippling)
    ("hr software", "crm"),                        # bare "hr"→crm
    # Regressions — probe 82 changes must not break these.
    ("customer support chat", "support"),          # bare "support"→customer-support (unchanged)
    ("customer success platform", "crm"),          # bigram "customer success"→crm (unchanged)
    ("customer data platform", "analytics"),       # bigram "customer data"→analytics (unchanged)
    ("user authentication", "authentication"),     # bare "authentication"→auth (fires before segmentation)
    ("user research tool", "feedback"),            # bigram "user research"→feedback (unchanged)
    ("audience targeting ad", "analytics"),        # bare "audience"→analytics (consistent)
    # Probe pattern 83 (May 2026): infrastructure monitoring collision / capacity / market dead zones.
    # "infrastructure monitoring" mis-routed to devops via "infrastructure"→devops — monitoring tools
    # (Prometheus, Grafana, VictoriaMetrics) belong in Monitoring; bigram added.
    # "capacity planning" fired raw_first — both tokens unmapped; infra capacity tools are DevOps.
    # "market research"/"market intelligence" fired raw_first "market" — market analytics tools
    # (Crayon, Klue, Semrush) belong in Analytics.
    ("infrastructure monitoring", "monitoring"),   # bigram "infrastructure monitoring"→monitoring
    ("capacity planning", "devops"),               # bare "capacity"→devops
    ("capacity management", "devops"),             # bare "capacity"→devops
    ("market research", "analytics"),              # bare "market"→analytics
    ("market intelligence", "analytics"),          # bare "market"→analytics
    ("market data", "analytics"),                  # bare "market"→analytics
    # Regressions — probe 83 changes must not break these.
    ("infrastructure as code", "devops"),          # bare "infrastructure"→devops (unchanged; bigram fires first only for "monitoring" suffix)
    ("infrastructure deployment", "devops"),       # bare "infrastructure"→devops (no bigram collision)
    ("market segmentation", "analytics"),          # works via "market"→analytics (previously via "segmentation"→analytics)

    # Probe pattern 84 (May 2026): competitive analysis / data engineering / data science / feature store / productivity dead zones.
    # "competitive analysis"/"competitive intelligence"/"competitive pricing" → raw_first "competitive";
    # competitive intelligence tools (Crayon, Klue, SimilarWeb) belong in Analytics; bare "competitive"→analytics added.
    # "data engineering" → devops via bare "engineering"→devops (wrong; Airbyte/Fivetran/dbt are Background Jobs);
    # bigram "data engineering"→background added.
    # "data science" → raw_first (both tokens unmapped); data science tools (Jupyter, Pandas) belong in AI; bigram added.
    # "feature store" → feature-flags via bare "feature"→feature (wrong; ML feature stores like Feast/Tecton are AI); bigram added.
    # "developer productivity" → raw_first "productivity" ("developer" stripped by _FTS_STOP_WORDS);
    # developer productivity tools (Raycast, Warp) → Developer Tools; bare "productivity"→developer added.
    # "local first" → raw_first (both tokens unmapped); local-first sync tools (ElectricSQL, PowerSync) → Database; bigram added.
    ("competitive analysis", "analytics"),         # bare "competitive"→analytics
    ("competitive intelligence", "analytics"),     # bare "competitive"→analytics
    ("competitive pricing", "analytics"),          # bare "competitive"→analytics
    ("data engineering tools", "background"),      # bigram "data engineering"→background
    ("data engineering python", "background"),     # bigram "data engineering"→background (python in _FRAMEWORK_QUERY_TERMS)
    ("data science library", "ai"),                # bigram "data science"→ai
    ("data science python", "ai"),                 # bigram "data science"→ai
    ("feature store ml", "ai"),                    # bigram "feature store"→ai (overrides "feature"→feature)
    ("feast feature store", "ai"),                 # bigram "feature store"→ai
    ("developer productivity", "developer"),       # bare "productivity"→developer ("developer" stripped)
    ("productivity tools", "developer"),           # bare "productivity"→developer
    ("local first sync", "database"),              # bigram "local first"→database
    ("local first architecture", "database"),      # bigram "local first"→database
    ("local-first database", "database"),          # hyphenated form "local-first"→database
    # Regressions — probe 84 changes must not break these.
    ("platform engineering", "devops"),            # bare "engineering"→devops unchanged (no "data" prefix)
    ("infrastructure engineering", "devops"),      # bare "engineering"→devops unchanged
    ("feature flag toggle", "feature"),            # bigram "feature flag"→feature (no collision with "feature store" bigram)
    ("feature branch deploy", "devops"),           # bigram "feature branch"→devops
    ("ml experiment tracking", "ai"),              # "ml"→ai fires at pos 0 (correct for ML experiment tracking)
    ("market segmentation", "analytics"),          # "market"→analytics unchanged

    # Probe pattern 85 (May 2026): memory leak / heap dump / SLA / terms / multi-region / tenancy / knowledge / team-collaboration dead zones.
    # "memory leak"/"memory leak detection" → caching via bare "memory"→caching (wrong; Valgrind,
    # LeakCanary, py-spy are Monitoring); bigram "memory leak"→monitoring added.
    # "heap dump" → analytics via bare "heap"→analytics (Heap.io collision; jmap/VisualVM are Monitoring); bigram added.
    # "service level agreement" → raw_first "level" ("service" stripped → ["level","agreement"]);
    # SLA tools → Monitoring; bigram "level agreement"→monitoring added.
    # "terms of service" → raw_first "terms" ("of"+"service" both stripped); Termly/Iubenda → Security; bare "terms"→security added.
    # "multi region"/"multi cloud" → raw_first "multi" (both tokens unmapped); bigrams → DevOps.
    # "multi tenancy" → raw_first "multi" ("tenancy" unmapped); bare "tenancy"→authentication added.
    # "knowledge sharing" → raw_first "knowledge"; bigram "knowledge sharing"→documentation added.
    # "team collaboration" → api via bare "collaboration"→api; bigram "team collaboration"→developer added.
    ("memory leak detection", "monitoring"),       # bigram "memory leak"→monitoring (overrides "memory"→caching)
    ("memory leak nodejs", "monitoring"),          # bigram "memory leak"→monitoring
    ("heap dump analysis", "monitoring"),          # bigram "heap dump"→monitoring (overrides "heap"→analytics)
    ("heap dump java", "monitoring"),              # bigram "heap dump"→monitoring
    ("service level agreement", "monitoring"),     # bigram "level agreement"→monitoring
    ("sla monitoring tool", "monitoring"),         # bare "sla"→monitoring (confirm unchanged)
    ("terms of service generator", "security"),   # bare "terms"→security ("of"+"service" stripped)
    ("terms and conditions", "security"),          # bare "terms"→security ("and" stripped)
    ("multi region deployment", "devops"),         # bigram "multi region"→devops
    ("multi cloud strategy", "devops"),            # bigram "multi cloud"→devops
    ("multiregion kubernetes", "devops"),          # compound "multiregion"→devops
    ("multi tenancy architecture", "authentication"),  # bare "tenancy"→authentication
    ("knowledge sharing wiki", "documentation"),  # bigram "knowledge sharing"→documentation
    ("team collaboration mattermost", "developer"),  # bigram "team collaboration"→developer
    # Regressions — probe 85 changes must not break these.
    ("memory store redis", "caching"),             # bare "memory"→caching unchanged (no "leak" suffix)
    ("memory cache node", "caching"),              # bare "memory"→caching unchanged
    ("heap analytics session", "analytics"),       # bare "heap"→analytics unchanged (no "dump" suffix)
    ("multilingual app", "localization"),           # "multilingual"→localization fires (compound form; spaced "multi language" is a known gap)
    ("multi currency payments", "payments"),       # "currency"→payments fires
    ("collaborative editing yjs", "api"),          # bare "collaborative"→api unchanged (no "team" prefix)

    # Probe pattern 86 (May 2026): visual editor / page builder / site builder / countdown / loyalty dead zones.
    # "visual editor component" → testing via bare "visual"→testing (wrong; WYSIWYG editors like TipTap,
    # ProseMirror are Frontend Frameworks); bigram "visual editor"→frontend added.
    # "page builder"/"site builder" → raw_first (both tokens unmapped); Landing Pages; bigrams added.
    # "countdown timer" → raw_first "countdown" (unmapped); countdown UI components → Frontend; bare added.
    # "loyalty reward"/"loyalty program" → raw_first "loyalty" (unmapped); loyalty tools → CRM; bare added.
    ("visual editor react", "frontend"),           # bigram "visual editor"→frontend (overrides "visual"→testing)
    ("visual editor component", "frontend"),       # bigram "visual editor"→frontend
    ("page builder react", "landing"),             # bigram "page builder"→landing
    ("page builder nextjs", "landing"),            # bigram "page builder"→landing
    ("site builder open source", "landing"),       # bigram "site builder"→landing
    ("countdown timer react", "frontend"),         # bare "countdown"→frontend
    ("countdown component", "frontend"),           # bare "countdown"→frontend
    ("loyalty program tool", "crm"),               # bare "loyalty"→crm
    ("loyalty rewards api", "crm"),                # bare "loyalty"→crm
    # Regressions — probe 86 changes must not break these.
    ("visual regression testing", "testing"),      # bare "visual"→testing unchanged (no "editor" suffix)
    ("visual testing percy", "testing"),           # bare "visual"→testing unchanged
    ("block editor component", "frontend"),        # "editor"→frontend fires at pos 1 (no "visual" prefix needed)
    ("inline editor react", "frontend"),           # "editor"→frontend fires
    ("coming soon page", "landing"),               # bigram "coming soon"→landing unchanged
    ("referral program crm", "crm"),               # "referral"→crm unchanged
]


def run_tests(verbose: bool = False) -> tuple[int, int]:
    passed = 0
    failed = 0
    failures: list[tuple[str, str, str, str]] = []

    for query, expected in TEST_CASES:
        cat_term, via = route_query(query)
        ok = expected.lower() in cat_term.lower()
        if ok:
            passed += 1
            if verbose:
                print(f"  ✅ {query!r:50s} → {cat_term!r} (via {via!r})")
        else:
            failed += 1
            failures.append((query, expected, cat_term, via))
            print(f"  ❌ {query!r:50s} → {cat_term!r} (expected {expected!r}, via {via!r})")

    return passed, failed


def test_single(query: str) -> None:
    cat_term, via = route_query(query)
    print(f"Query:    {query!r}")
    print(f"Routes → {cat_term!r}  (via token {via!r})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Test _CAT_SYNONYMS routing offline")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all results")
    parser.add_argument("--query", "-q", help="Test a single query")
    args = parser.parse_args()

    if args.query:
        test_single(args.query)
        return 0

    print(f"Running {len(TEST_CASES)} routing tests against _CAT_SYNONYMS...\n")
    passed, failed = run_tests(verbose=args.verbose)
    total = passed + failed
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} passed  |  {failed} failed")

    if failed:
        print(f"\nTo add missing mappings, edit _CAT_SYNONYMS in src/indiestack/db.py")
        print("Then re-run: python3 scripts/test_search_routing.py")
        return 1

    print("✅ All routing tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
