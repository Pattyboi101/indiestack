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
    ("documentation api docs", "api"),      # "documentation" not in synonyms; "api" → api (acceptable)
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
    # Usage-based / metered billing
    ("usage based billing", "invoicing"),           # "usage" → invoicing (metered billing category)
    ("metered billing api", "invoicing"),           # "metered" → invoicing
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
    # Regression — bare "workflow" still routes to ai for automation tool queries
    ("workflow automation n8n", "ai"),               # "workflow"→ai still fires (no overriding bigram)
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
