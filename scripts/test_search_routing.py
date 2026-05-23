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
"""

import sys
import argparse
from pathlib import Path

# Load constants from db.py without triggering async machinery
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from indiestack.db import _CAT_SYNONYMS, _FTS_STOP_WORDS, _FRAMEWORK_QUERY_TERMS


def route_query(query: str) -> tuple[str, str]:
    """
    Simulate the category-routing logic from search_tools() in db.py.
    Includes bigram lookup (added db.py pass 170) so multi-word entries
    like "semantic cache" → "caching" are matched before single tokens.
    """
    meaningful = [t for t in query.lower().split() if t not in _FTS_STOP_WORDS]
    meaningful_for_cat = [t for t in meaningful if t not in _FRAMEWORK_QUERY_TERMS]
    if not meaningful_for_cat:
        meaningful_for_cat = meaningful

    bigrams = [f"{meaningful_for_cat[i]} {meaningful_for_cat[i+1]}"
               for i in range(len(meaningful_for_cat) - 1)]
    syn_key = (next((bg for bg in bigrams if bg in _CAT_SYNONYMS), None)
               or next((t for t in meaningful_for_cat if t in _CAT_SYNONYMS), None))

    if syn_key:
        return _CAT_SYNONYMS[syn_key], syn_key

    raw_cat = meaningful_for_cat[0] if meaningful_for_cat else query.lower()
    return raw_cat, "raw_first"


TEST_CASES: list[tuple[str, str]] = [
    # Core categories
    ("auth for nextjs", "authentication"),
    ("login system", "authentication"),
    ("oauth provider", "authentication"),
    ("payments stripe alternative", "payments"),
    ("billing subscriptions", "payments"),
    ("email sending transactional", "email"),
    ("newsletter platform", "email"),
    ("database postgres", "database"),
    ("vector database", "database"),
    ("monitoring uptime", "monitoring"),
    ("analytics tracking", "analytics"),
    ("forms surveys", "forms"),
    ("scheduling booking", "scheduling"),
    ("cms headless", "cms"),
    ("customer support chat", "support"),
    ("seo tools", "seo"),
    ("file storage upload", "file"),
    ("crm sales pipeline", "crm"),
    ("developer tools sdk", "api"),
    ("design ui", "frontend"),
    ("feedback nps", "feedback"),
    ("social media scheduling", "social"),
    ("project management kanban", "frontend"),
    ("landing page builder", "landing"),
    ("api gateway", "api"),
    # Frontend
    ("state management react", "frontend"),
    ("bundler vite webpack", "frontend"),
    ("build tool esbuild", "frontend"),
    ("react component library", "frontend"),
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
    ("ai browser automation", "testing"),
    ("computer use api", "ai"),
    # AI Dev Tools
    ("mcp server setup", "mcp"),
    ("boilerplate saas starter", "boilerplate"),
    ("cursor rules setup", "ai"),
    ("ai coding assistant", "ai"),
    # AI Standards / Eval
    ("garak llm scanner", "standard"),
    ("lm-eval setup", "standard"),
    ("arc-agi benchmark", "standard"),
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
    ("merge queue tool", "background"),
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
    ("rate limiting api", "api"),
    ("webhook delivery", "api"),
    # Background jobs
    ("cron job scheduler", "background"),
    ("task queue worker", "developer"),
    # PR review (added May 2026)
    ("pr-agent alternative", "ai"),
    ("qodo-merge setup", "ai"),
    ("ai pr review tool", "developer"),
    # MCP registries / servers
    ("smithery mcp", "mcp"),
    ("context7 mcp", "mcp"),
    ("docker mcp setup", "devops"),
    ("pulsemcp analytics", "mcp"),
    # Misc
    ("media server video", "media"),
    ("maps geolocation", "maps"),
    ("logging log management", "logging"),
    ("push notification service", "notifications"),
    ("i18n localization", "localization"),
    ("cli command line", "cli"),
    ("documentation api docs", "api"),
    ("feature flag toggle", "feature"),
    # Product adoption / onboarding (added May 2026)
    ("appcues alternative", "feedback"),
    ("userpilot alternative", "feedback"),
    ("chameleon io product adoption", "feedback"),
    ("userflow onboarding", "feedback"),
    ("product tour library javascript", "frontend"),
    # Behavior analytics / session recording (added May 2026)
    ("mouseflow heatmap", "analytics"),
    ("smartlook session recording", "analytics"),
    # Observability / tracing
    ("opentelemetry alternative", "monitoring"),
    ("distributed tracing jaeger", "monitoring"),
    # Monorepo / package management
    ("monorepo build tool", "developer"),
    ("turborepo alternative", "developer"),
    # Code quality / linting
    ("linting eslint alternative", "testing"),
    ("code formatter biome", "testing"),
    # Secrets / environment management
    ("secrets management doppler", "security"),
    # Error tracking
    ("error tracking sentry", "monitoring"),
    # IaC / infra
    ("infrastructure as code terraform", "devops"),
    # GraphQL / API
    ("graphql api builder", "api"),
    # Headless CMS
    ("headless cms sanity alternative", "cms"),
    # TanStack products (added May 2026 — all must route to frontend-frameworks)
    ("tanstack-form alternative", "frontend"),
    ("tanstack-router vs react-router", "frontend"),
    ("tanstack-table headless datagrid", "frontend"),
    ("tanstack-virtual list virtualization", "frontend"),
    # Boilerplate hyphenated/compact forms (added May 2026)
    ("t3-stack alternative", "boilerplate"),
    ("t3stack nextjs starter", "boilerplate"),
    # LLM semantic caching (added May 2026 — single-token forms)
    ("gptcache setup", "caching"),
    ("gpt-cache alternative", "caching"),
    ("llm-cache library", "caching"),
    ("ai-cache middleware", "caching"),
    # LLM cache bigrams (bigram lookup added db.py pass 170)
    ("semantic cache llm", "caching"),
    ("llm cache layer", "caching"),
    # Invoicing — expense/bookkeeping/timesheet terms (173rd pass)
    ("expense tracking open source", "invoicing"),   # "expense"→invoicing
    ("expense report tool", "invoicing"),            # fires before "report"→analytics
    ("bookkeeping software indie", "invoicing"),     # "bookkeeping"→invoicing
    ("reimbursement software open source", "invoicing"), # "reimbursement"→invoicing
    ("timesheet tracking app", "invoicing"),         # "timesheet"→invoicing
    ("open source accounting software", "invoicing"), # "accounting"→invoicing (regression guard)
    # Creative Tools — music/MIDI/DAW/pixel-art/3D-modeling (173rd pass)
    ("music production open source", "creative"),    # "music"→creative
    ("midi library python", "creative"),             # "midi"→creative
    ("daw open source alternative", "creative"),     # "daw"→creative
    ("pixel art open source", "creative"),           # bigram "pixel art"→creative
    ("3d modeling open source", "creative"),         # bigram "3d modeling"→creative
    ("video streaming open source", "media"),        # regression: "video"→media unchanged
    # Database — data storage sub-domain bigrams (174th pass)
    ("data lake storage", "database"),               # bigram "data lake"→database (LakeFS, Delta Lake)
    ("open source data lake", "database"),           # "open"/"source" stop words; bigram fires on remaining
    ("time series data", "database"),                # bigram "time series"→database (TimescaleDB, InfluxDB)
    ("column store database", "database"),           # bigram "column store"→database (ClickHouse, DuckDB)
    # Analytics — data quality / lineage bigrams (174th pass)
    ("data quality tool", "analytics"),              # bigram "data quality"→analytics (Great Expectations, Soda)
    ("data lineage tool", "analytics"),              # bigram "data lineage"→analytics (OpenLineage, DataHub)
    # AI — "feature store" spaced bigram (175th pass): "feature"→feature-flags fires first without bigram
    ("feature store ml", "ai"),                      # bigram "feature store"→ai (Feast, Tecton, Hopsworks)
    ("feature store python", "ai"),                  # bigram fires before "feature"→feature-flags single token
    # Regression — bare "feature" still routes to Feature Flags
    ("feature flag react", "feature"),               # "feature"→feature-flags unchanged
    # DevOps — "blue green" spaced bigram (175th pass): "bluegreen" compound exists but agents use spaces
    ("blue green deployment", "devops"),             # bigram "blue green"→devops (Argo Rollouts, Spinnaker)
    ("blue green release", "devops"),                # bigram fires before raw_first "blue"
    # DevOps — rolling deployment strategies (175th pass): "rolling" has no single-token mapping
    ("rolling update kubernetes", "devops"),         # bigram "rolling update"→devops
    ("rolling deploy strategy", "devops"),           # bigram "rolling deploy"→devops
    # API — streaming api / server streaming (176th pass)
    # "streaming"→media fires for bare streaming queries; bigrams override for API-type streaming.
    ("streaming api nodejs", "api"),                 # bigram "streaming api"→api (SSE, gRPC streaming)
    ("streaming api sse", "api"),                    # bigram fires before "streaming"→media
    ("server streaming grpc", "api"),                # bigram "server streaming"→api (gRPC bidirectional)
    ("server streaming http2", "api"),               # bigram form → API Tools
    ("video streaming server", "media"),             # regression: bare "streaming"→media unchanged
    # Testing — performance testing (176th pass)
    # "performance"→monitoring fires for APM queries; bigrams override for testing-specific queries.
    ("performance testing tool", "testing"),         # bigram "performance testing"→testing (k6, Artillery)
    ("performance testing k6", "testing"),           # bigram fires before "performance"→monitoring
    ("performance test runner", "testing"),          # bigram "performance test"→testing
    ("performance test suite", "testing"),           # bigram form → Testing Tools
    ("performance monitoring", "monitoring"),        # regression: bare "performance"→monitoring unchanged
    # Frontend — Snowpack (legacy ESM build tool; "snowpack" was unmapped → raw_first)
    ("snowpack build tool", "frontend"),             # "snowpack" → Frontend Frameworks
    ("snowpack alternative", "frontend"),            # single token — regression check
    # AI — LlamaGuard / Rebuff (AI safety tools; both were unmapped → raw_first)
    ("llamaguard safety", "ai"),                     # "llamaguard" → AI & Automation
    ("rebuff prompt injection", "ai"),               # "rebuff" → AI & Automation (via "rebuff" not "prompt")
    # AI — fine-tuning hyphenated form ("finetuning"/"finetune" existed; hyphen form was gap)
    ("fine-tuning llm", "ai"),                       # hyphenated single token → AI & Automation
    # AI — llms.txt variants (dot-form and spaced bigram were gaps alongside existing "llmstxt")
    ("llms.txt standard", "ai"),                     # dot-separated token → AI & Automation
    ("llmstxt generator", "ai"),                     # compact token → AI & Automation
    ("llms txt implementation", "ai"),               # bigram → AI & Automation
    ("llms-txt tool", "ai"),                         # hyphenated → AI & Automation
    # AI — LM Studio spaced bigram ("lmstudio" existed; "lm studio" with space was raw_first)
    ("lm studio alternative", "ai"),                 # bigram "lm studio" → AI & Automation
    ("lm studio local llm", "ai"),                   # bigram fires before raw_first "lm"
    # AI — KoboldAI (local LLM; "koboldai" was unmapped → raw_first)
    ("koboldai setup", "ai"),                        # "koboldai" → AI & Automation
    # Email — SparkPost (transactional email; "sparkpost" was unmapped → raw_first)
    ("sparkpost alternative", "email"),              # "sparkpost" → Email Marketing
    # Payments — Autumn.js ("autumn" first token was unmapped)
    ("autumn payments", "payments"),                 # "autumn" → Payments
    # Invoicing — m3ter (usage-based billing; "m3ter" was unmapped → raw_first)
    ("m3ter billing", "invoicing"),                  # "m3ter" → Invoicing & Billing
    # Analytics — Hydrolix (streaming analytics; "hydrolix" was unmapped → raw_first)
    ("hydrolix analytics", "analytics"),             # "hydrolix" → Analytics & Metrics
    # Security — Microsoft Presidio (PII detection; "presidio" was unmapped → raw_first)
    ("presidio pii detection", "security"),          # "presidio" → Security Tools
    # Security — Skyflow and Arcjet (PII vault / app security; both unmapped → raw_first)
    ("skyflow pii vault", "security"),               # "skyflow" → Security Tools
    ("arcjet bot detection", "security"),            # "arcjet" → Security Tools
    # Security — "private ai" bigram (bare "private" is too generic; bigram targets the PII SaaS)
    ("private ai redaction", "security"),            # bigram "private ai" → Security Tools
    # AI — "private llm" (self-hosted AI deployments; bigram avoids ambiguity with "private"→raw_first)
    ("private llm hosting", "ai"),                   # bigram "private llm" → AI & Automation
    # Security — "zero trust" spaced form ("zerotrust" compound and "zero-trust" hyphen already mapped)
    ("zero trust model", "security"),               # bigram "zero trust" → Security Tools
    ("zero trust architecture", "security"),        # bigram fires before "zero"→raw_first
    # Regression — compound/hyphenated forms still route correctly
    ("zerotrust network", "security"),              # "zerotrust" → Security Tools (unchanged)
    # Security — "zero knowledge" for ZK proof tooling (snarkjs, bellman, circom)
    ("zero knowledge proof", "security"),           # bigram "zero knowledge" → Security Tools
    # Security — SBOM spaced form ("software bill of materials")
    # Stop words strip "software" and "of" → ["bill","materials"]; bigram covers it
    ("software bill of materials tool", "security"), # bigram "bill materials" → Security Tools
    ("bill of materials generator", "security"),    # bigram fires before "bill"→raw_first
    # Regression — "sbom" abbreviation still routes correctly
    ("sbom scanner", "security"),                   # "sbom" → Security Tools (unchanged)
    # ── Probe pattern: Orphaned second-token poisoning ───────────────────────
    # First token has NO synonym (raw_first), second token maps to wrong category.
    # Web3 — "smart" unmapped, "contract"→testing → mis-routes to testing
    ("smart contract auditor", "developer"),        # bigram "smart contract" → Developer Tools
    ("smart contract development", "developer"),    # second form
    ("smart contracts framework", "developer"),     # plural bigram
    # Regression — bare "contract"→testing still fires for contract testing
    ("contract testing pact", "testing"),           # "contract" → Testing (unchanged)
    # Screen recording — "screen" unmapped, raw_first fires with no boost
    ("screen recorder open source", "developer"),   # bigram "screen recorder" → Developer Tools
    ("screen capture library", "developer"),        # bigram "screen capture" → Developer Tools
    # Security — "zk" abbreviation was raw_first (zero-knowledge proof tools)
    ("zk proof library", "security"),               # "zk" → Security Tools
    ("zk rollup ethereum", "security"),             # second form
    # Regression — "zero knowledge" bigram still routes correctly
    ("zero knowledge proof system", "security"),    # bigram "zero knowledge" → Security Tools (unchanged)
    # Message Queue — "streaming pipeline" routed to media via "streaming"→media
    ("streaming pipeline kafka", "message"),        # bigram overrides "streaming"→media
    # File management — "html to pdf" loses "to" stop word; "html"→frontend fires
    ("html to pdf converter", "file"),              # bigram "html pdf" → File Management
    ("html pdf generator", "file"),                 # second form
    # Regression — bare "html"→frontend still fires for non-pdf queries
    ("html component library", "frontend"),         # "html" → Frontend (unchanged)
    # AI — "ai observability" was routing to Monitoring via "observability"→monitoring
    ("ai observability platform", "ai"),             # bigram "ai observability"→ai (Langfuse, Helicone)
    ("ai observability tool", "ai"),                 # second form
    # Regression — bare "observability" still routes to monitoring for infra queries
    ("observability monitoring tool", "monitoring"), # "observability"→monitoring unchanged
    # AI — "ai cost" / "ai spend" were raw_first; now explicit bigrams
    ("ai cost tracking", "ai"),                      # bigram "ai cost"→ai
    ("ai cost management", "ai"),                    # second form
    ("ai spend monitoring", "ai"),                   # bigram "ai spend"→ai
    # Caching — "browser cache/caching" was routing to Testing via "browser"→testing
    ("browser cache management", "caching"),         # bigram "browser cache"→caching
    ("browser caching headers", "caching"),          # bigram "browser caching"→caching
    # Regression — bare "browser" still routes to testing for automation queries
    ("browser automation puppeteer", "testing"),     # "browser"→testing unchanged
    # ── Probe pattern 39: CLI arg parsing / SEO structured data / mapping ────
    # CLI — bare "argument"/"args" → cli; bigrams for compound parser queries
    ("argument parser python", "cli"),               # "argument"→cli
    ("args parser nodejs", "cli"),                   # "args parser" bigram
    ("arg parser library", "cli"),                   # "arg parser" bigram
    ("flag parser library", "cli"),                  # bigram overrides "flag"→feature
    ("option parser cli", "cli"),                    # "option parser" bigram
    ("argparse alternative", "cli"),                 # "argparse"→cli
    ("minimist alternative", "cli"),                 # "minimist"→cli
    # Regression — bare "flag"→feature still fires without "parser" qualifier
    ("feature flag react", "feature"),               # "feature"→feature unchanged
    # Maps — "mapping" bare token → maps; "data mapping" bigram → developer
    ("mapping library", "maps"),                     # "mapping"→maps
    ("data mapping tool", "developer"),              # "data mapping" bigram overrides "mapping"→maps
    # SEO — structured data and schema markup
    ("structured data validation", "seo"),           # "structured data" bigram
    ("schema markup nextjs", "seo"),                 # bigram overrides "schema"→developer
    ("json ld generator", "seo"),                    # "json ld" bigram
    ("meta tag generator", "seo"),                   # "meta tag" bigram
    # Regression — structured logging must route to logging, not seo
    ("structured logging library", "logging"),       # "structured logging" bigram overrides "structured"→seo
    # Regression — "schema migration" still routes to database
    ("schema migration tool", "database"),           # "schema migration" bigram fires before "schema"→developer
    # Invoicing — revenue recognition bigram
    ("revenue recognition saas", "invoicing"),       # bigram fires; without it "saas"→boilerplate fires
    # Feature Flags — multivariate testing
    ("multivariate test tool", "feature"),           # "multivariate test" bigram
    ("multivariate experiment", "feature"),          # "multivariate"→feature
    # DevOps — changelogs plural
    ("automated changelogs ci", "devops"),           # "changelogs"→devops
    # ── Probe pattern 40: 3D web / CDP / API-mocking / metadata-catalog / error-boundary / web-components ──
    # "three.js" (period-dot form) was unmapped; "babylon.js"/"babylonjs" also unmapped → raw_first
    ("three.js alternative", "frontend"),           # "three.js" bare token → frontend
    ("babylon.js 3d engine", "frontend"),           # "babylon.js" bare token → frontend
    ("babylonjs alternative", "frontend"),          # no-dot compound form → frontend
    # Regression: "threejs" and "r3f" still route to frontend
    ("threejs react alternative", "frontend"),      # "threejs"→frontend (unchanged)
    ("r3f react three fiber", "frontend"),          # "r3f"→frontend (unchanged)
    # "customer data platform" fired raw_first — "customer" + "cdp" had no mapping
    ("customer data platform", "analytics"),        # bigram "customer data" fires
    ("customer data integration", "analytics"),     # bigram at i=0-1
    ("cdp alternative", "analytics"),               # CDP abbreviation → analytics
    # "api mock server" routed to api-tools because "api"→api fired before "mock"→testing
    ("api mock server", "testing"),                 # bigram "api mock" fires at i=0
    ("api mocking tool", "testing"),                # bigram "api mocking" fires at i=0
    # Regression: bare "mock" queries still route to testing
    ("mock api endpoint", "testing"),               # "mock"→testing fires at i=0 (no change)
    # "metadata catalog" fired raw_first — "metadata" and "catalog" were both unmapped
    ("metadata catalog tool", "analytics"),         # bigram fires before raw_first
    ("metadata catalog open source", "analytics"), # bigram at i=0-1
    # Regression: service catalog still routes to devops (bare "catalog"→devops added)
    ("service catalog platform", "devops"),         # "catalog"→devops fires at i=1
    # "error boundary react" routed to monitoring via "error"→monitoring
    ("error boundary react", "frontend"),           # bigram "error boundary" fires before "error"→monitoring
    ("error boundary component", "frontend"),       # bigram at i=0-1
    # Regression: bare "error" queries still route to monitoring
    ("error tracking production", "monitoring"),    # "error"→monitoring fires (no bigram collision)
    # "custom elements registry" routed to devops via "registry"→devops
    ("custom elements registry", "frontend"),       # bigram "custom elements" fires before "registry"→devops
    ("custom elements api", "frontend"),            # bigram at i=0-1
    # Probe pattern 41 (May 2026): fintech / PII / data-privacy dead zones.
    # Fintech — Plaid, Teller, Lean, Open Banking; all previously raw_first with no boost.
    ("plaid alternative", "payments"),              # "plaid"→payments (bank account data API)
    ("plaid sdk", "payments"),                      # "plaid"→payments fires before sdk→api
    ("bank connection api", "payments"),            # "bank"→payments fires before api→api
    ("banking sdk", "payments"),                    # "banking"→payments
    ("banking api", "payments"),                    # "banking"→payments fires before api→api
    ("open banking standard", "payments"),          # "open" stripped → "banking"→payments fires
    ("open banking api", "payments"),               # "open" stripped → "banking"→payments fires
    ("fintech toolkit", "payments"),                # "fintech"→payments
    ("fintech api python", "payments"),             # "fintech"→payments fires before api→api
    # Regression — payment/billing/checkout queries still route to payments
    ("stripe payment alternative", "payments"),     # "stripe"→payments (regression guard)
    ("billing subscriptions", "payments"),          # "billing"→payments (regression guard)
    # PII / data privacy — previously raw_first with no boost.
    ("pii masking tool", "security"),               # "pii"→security fires at i=0
    ("pii redaction api", "security"),              # bigram "pii redaction"→security fires at i=0
    ("pii detection api", "security"),              # bigram "pii detection"→security fires at i=0
    ("pii masking postgres", "security"),           # bigram "pii masking"→security fires at i=0
    ("anonymization library python", "security"),   # "anonymization"→security fires at i=0
    ("data anonymization gdpr", "security"),        # bigram "data anonymization"→security fires at i=0
    ("data anonymization tool", "security"),        # bigram fires at i=0
    ("data masking postgres", "security"),          # bigram "data masking"→security fires at i=0
    ("data masking tool", "security"),              # bigram fires at i=0
    ("masking library", "security"),                # "masking"→security fires at i=0
    # Regression — GDPR compliance tools still route to security
    ("gdpr compliance tool", "security"),           # "gdpr"→security fires at i=0

    # Probe pattern 43 (May 2026): headless commerce / iPaaS / license-compliance dead zones.
    # "headless"→cms fires for ALL "headless X"; bigrams now override for commerce/checkout intent.
    ("headless commerce platform", "developer"),     # bigram "headless commerce"→developer (overrides "headless"→cms)
    ("headless ecommerce engine", "developer"),      # bigram "headless ecommerce"→developer
    ("headless storefront nextjs", "developer"),     # bigram "headless storefront"→developer
    ("headless checkout flow", "payments"),          # bigram "headless checkout"→payments
    # Regression: "headless cms" and "headless blog" still route to cms
    ("headless cms contentful", "cms"),              # "headless"→cms fires (no commerce bigram)
    ("headless blog platform", "cms"),               # "headless"→cms still fires correctly
    # "ipaas" bare token → ai (n8n, Make.com, Zapier alternatives in AI & Automation)
    ("ipaas tool", "ai"),                            # "ipaas"→ai (was raw_first)
    ("ipaas vs zapier", "ai"),                       # "ipaas"→ai fires at i=0
    # "license" bare token → developer; FOSSA, licensecheck, REUSE → Developer Tools
    ("license checker", "developer"),               # "license"→developer (was raw_first)
    ("license scanning tool", "developer"),         # "license"→developer fires at i=0
    ("fossa alternative", "developer"),             # "fossa"→developer (was raw_first)
    # Regression: "compliance" without "license" still routes to security
    ("soc2 compliance tool", "security"),           # "compliance"→security fires (no collision)
    # Probe pattern (May 2026): multi-tenancy / impersonation dead zones.
    # "multi tenancy" (spaced) fired raw_first — neither "multi" nor "tenancy" was mapped.
    # "impersonation"/"impersonate" also fired raw_first. WorkOS, Clerk, Auth0 handle
    # multi-tenant orgs and user impersonation — all live in Authentication.
    ("multi tenancy", "authentication"),             # bigram + "tenancy" token → Authentication
    ("multi tenancy saas", "authentication"),        # 3-token — "tenancy" at position 1 fires
    ("impersonation", "authentication"),             # bare token → Authentication
    ("user impersonation", "authentication"),        # "impersonation" token fires
    ("impersonate user", "authentication"),          # "impersonate" token → Authentication
    # Regression: existing multi-tenant terms still route correctly
    ("multi tenant architecture", "authentication"), # "tenant"→auth pre-existing
    ("tenant isolation", "authentication"),          # "tenant"→auth pre-existing
    #
    # Probe 47 (May 2026): Preview environments / ephemeral deployments dead zones.
    # "environment"→security was overriding "preview environment" and "ephemeral environment"
    # queries that target DevOps tools (Uffizzi, Bunnyshell, Tugboat, Qovery).
    # Fixed: bigrams "preview environment"/"ephemeral environment"→devops;
    #        bare "preview"→devops; bare "uffizzi"/"qovery"/"bunnyshell"→devops.
    ("preview environment tool", "devops"),          # bigram "preview environment"→devops (was "security" via "environment")
    ("ephemeral environment docker", "devops"),      # bigram "ephemeral environment"→devops (was "security")
    ("branch preview deployment", "devops"),         # bare "preview"→devops (was raw_first)
    ("uffizzi alternative", "devops"),               # bare "uffizzi"→devops (was raw_first)
    ("qovery alternative", "devops"),                # bare "qovery"→devops (was raw_first)
    ("bunnyshell preview env", "devops"),            # bare "bunnyshell"→devops (was raw_first)
    # Regressions — "environment variables" still routes to security; "email preview" still routes to email.
    ("environment variables manager", "security"),  # "environment"→security unaffected (no preview bigram)
    ("email preview template", "email"),             # "email"→email fires before "preview"→devops
    #
    # Probe 48 (May 2026): BI + product onboarding/walkthrough dead zones.
    # "business intelligence tool" fired raw_first — bare "business" and "intelligence" had no mapping
    # ("bi" covered the abbreviation but not the spelled-out phrase). Metabase/Redash/Superset unreachable
    # for this natural-language query form. Fixed: bigram "business intelligence"→analytics.
    # "user onboarding software"/"product onboarding flow" mis-routed via "onboarding"→frontend —
    # tool synonyms (appcues/userpilot/userflow) existed but no generic bigrams covered the pattern.
    # "onboarding flow builder" same issue. Fixed: bigrams "user onboarding","product onboarding",
    # "onboarding flow"→feedback.
    # "interactive walkthrough" fired raw_first — bare "walkthrough" unmapped. Appcues/Pendo/Userpilot
    # all use walkthrough as a synonym for in-app product tours. Fixed: bare "walkthrough"→feedback
    # + bigram "interactive walkthrough"→feedback.
    # NOTE: "product tour" bigram intentionally NOT added — would break regression test
    # "product tour library javascript"→frontend (bare "library" is a stop word so meaningful=
    # [product,tour,javascript]; bigram "product tour" fires before "javascript"→frontend).
    ("business intelligence tool", "analytics"),    # bigram "business intelligence"→analytics (was raw_first)
    ("business intelligence platform", "analytics"),# second form
    ("user onboarding software", "feedback"),        # bigram "user onboarding"→feedback (was frontend)
    ("product onboarding flow", "feedback"),         # bigram "product onboarding"→feedback (was frontend)
    ("product onboarding software", "feedback"),     # second form
    ("onboarding flow builder", "feedback"),         # bigram "onboarding flow"→feedback (was frontend)
    ("interactive walkthrough", "feedback"),         # bigram → Feedback (was raw_first)
    ("product walkthrough guide", "feedback"),       # bare "walkthrough"→feedback (was raw_first)
    # Regressions — "bi tool" / "product tour library" unaffected.
    ("bi tool", "analytics"),                        # bare "bi"→analytics unchanged
    ("product tour library javascript", "frontend"), # bare "tour"→frontend unchanged (library=stop word)

    # Probe pattern 54 — headless-X gerunds/abbrevs + realtime-category fan-out + platform-push
    # "headless X" — existing bigrams cover commerce/ecommerce/storefront/checkout (probe 43).
    ("headless testing framework", "testing"),             # bigram "headless testing" → Testing (not CMS)
    ("headless automation testing", "testing"),            # bigram "headless automation" → Testing Tools
    ("headless e2e playwright", "testing"),                # bigram "headless e2e" → Testing Tools
    # Regression — existing headless commerce/ecommerce bigrams unchanged.
    ("headless commerce engine", "developer"),             # existing bigram → Developer Tools
    ("headless ecommerce storefront", "developer"),        # existing bigram → Developer Tools
    # "realtime X" — bare "realtime"→api; new bigrams override for non-api categories.
    ("realtime analytics dashboard", "analytics"),         # bigram "realtime analytics" → Analytics & Metrics
    ("realtime monitoring alerts", "monitoring"),          # bigram "realtime monitoring" → Monitoring & Uptime
    ("realtime push notifications", "notifications"),      # bigram "realtime push" → Notifications
    ("realtime notifications novu", "notifications"),      # bigram "realtime notifications" → Notifications
    ("realtime search nextjs", "search"),                  # bigram "realtime search" → Search Engines
    ("realtime log streaming", "logging"),                 # bigram "realtime log" → Logging
    ("realtime logging service", "logging"),               # bigram "realtime logging" → Logging
    # Regression — bare "realtime"→api unchanged for api-context queries.
    ("realtime api websocket", "api"),                     # bare "realtime"→api unchanged
    # Platform push notifications — "mobile"/"ios"/"android"→frontend fires before "push"→notifications.
    ("mobile push notification sdk", "notifications"),     # bigram "mobile push" → Notifications
    ("ios push notification onesignal", "notifications"),  # bigram "ios push" → Notifications
    ("android push notification firebase", "notifications"), # bigram "android push" → Notifications
    # Regression — bare "mobile"/"ios" still routes to frontend for non-push queries.
    ("mobile app framework", "frontend"),                  # bare "mobile"→frontend unchanged
    ("ios development", "frontend"),                       # bare "ios"→frontend unchanged

    # Probe pattern 55 — "model context protocol" dead zone
    # "model"→ai fires first; "protocol"→mcp never reached. Fix: "context protocol" bigram at i=1.
    ("model context protocol server", "mcp"),              # bigram "context protocol"→mcp at i=1
    ("context protocol implementation", "mcp"),            # bigram fires at i=0
    ("model context protocol typescript", "mcp"),          # bigram fires at i=1 in longer query
    # Regression — bare "mcp server" still routes to mcp.
    ("mcp server typescript", "mcp"),                      # bare "mcp"→mcp unchanged
    # Regression — bare "protocol" without "context" still routes to mcp.
    ("messaging protocol nodejs", "mcp"),                  # bare "protocol"→mcp unchanged

    # Probe pattern 56 — AI agent memory vocabulary colliding with Caching
    # "memory"→caching is correct for Redis/Memcached but wrong for AI agent memory tools
    # (Mem0, Zep, Letta). "long-term memory agent" and "conversational memory llm" both
    # routed to Caching via memory→caching after the first token fell through (unmapped).
    ("long-term memory agent store", "ai"),                # bigram "long-term memory"→ai (was: memory→caching)
    ("long-term memory layer mem0", "ai"),                 # same bigram, different query form
    ("conversational memory llm", "ai"),                   # bigram "conversational memory"→ai
    ("episodic memory retrieval", "ai"),                   # bare "episodic"→ai (Letta, Zep episodic store)
    # Regression — bare "memory" without AI qualifier still routes to caching.
    ("in memory cache redis", "caching"),                  # "memory"→caching unchanged (stop-word "in" stripped)
    ("memory store redis", "caching"),                     # "memory"→caching unchanged
    #
    # Probe pattern 57 — conversion / attribution / user-behaviour / mobile-analytics / data-protection dead zones
    # "tracking" is a stop word so "conversion tracking" → bare "conversion" → was raw_first.
    # "attribution model" was mis-routed to ai via "model"→ai at pos 1 (bare "attribution" unmapped).
    # "mobile attribution" and "mobile analytics" were mis-routed via "mobile"→frontend.
    # "data protection" is a Pattern-23 dual dead zone (neither "data" nor "protection" had a mapping).
    ("conversion tracking", "analytics"),                  # "tracking" stop-word stripped → bare "conversion"→analytics
    ("conversion optimization", "analytics"),              # bare "conversion"→analytics fires first
    ("cro tool", "analytics"),                             # abbreviation "cro"→analytics
    ("attribution model", "analytics"),                    # bare "attribution" fires before "model"→ai at pos 1
    ("marketing attribution", "analytics"),                # bare "attribution" fires at pos 1 ("marketing" unmapped)
    ("mobile attribution platform", "analytics"),          # bigram "mobile attribution"→analytics beats mobile→frontend
    ("mobile app analytics sdk", "analytics"),             # bigram "mobile analytics"→analytics beats mobile→frontend
    ("user behavior analytics", "analytics"),              # bigram "user behavior"→analytics
    ("user journey mapping", "analytics"),                 # bigram "user journey"→analytics
    ("data protection tool", "security"),                  # bigram "data protection"→security (dual raw_first fix)
    # Regressions — existing mappings must be unaffected.
    ("conversion rate optimization", "analytics"),         # bare "conversion"→analytics still correct (or any "conversion rate" bigram)
    ("data protection gdpr", "security"),                  # "data protection" bigram fires; "gdpr"→security also intact
    # Probe pattern 64 — adjective/gerund dead zones + markdown editor + real-time database
    ("virtualized list react", "frontend"),       # bare "virtualized"→frontend (react-virtualized library)
    ("react virtualized", "frontend"),            # bare "virtualized"→frontend (library name; react stripped as framework)
    ("windowing library", "frontend"),            # bare "windowing"→frontend (react-window)
    ("window virtualization react", "frontend"),  # bigram "window virtualization"→frontend
    # Regressions — existing virtual-scroll mappings unchanged.
    ("virtual list component", "frontend"),       # bare "virtual"→frontend unchanged
    # "markdown editor" → frontend (bigram overrides bare "markdown"→documentation).
    ("markdown editor react", "frontend"),        # bigram "markdown editor"→frontend
    ("markdown renderer react", "frontend"),      # bigram "markdown renderer"→frontend
    ("markdown component react", "frontend"),     # bigram "markdown component"→frontend
    # Regressions — bare markdown for docs-intent stays in documentation.
    ("markdown documentation", "documentation"),  # bare "markdown"→docs unchanged
    # "real time database" → database (bigram "time database" fires before bare "real"→api).
    ("real time database", "database"),           # bigram "time database"→database
    ("realtime database sync", "database"),       # bigram "realtime database"→database
    # Regressions — plain realtime queries unaffected.
    ("real time api", "api"),                     # bare "real"→api unchanged
    # Probe pattern 65 — canvas/drawing dead zones + pdf viewer component
    ("canvas drawing", "frontend"),       # bare "canvas"→frontend (Fabric.js, Konva.js)
    ("canvas library javascript", "frontend"),  # bare "canvas"→frontend fires before "javascript"→frontend
    ("html canvas react", "frontend"),    # bare "canvas"→frontend (javascript stripped as framework term)
    ("drawing library react", "frontend"),  # bare "drawing"→frontend
    ("drawing tool javascript", "frontend"),  # bare "drawing"→frontend
    ("pdf viewer react", "frontend"),     # bigram "pdf viewer"→frontend (react-pdf component)
    ("pdf viewer component", "frontend"), # bigram "pdf viewer"→frontend
    # Regressions — PDF generation still routes to file management.
    ("pdf generation react", "file"),     # bare "pdf"→file unchanged for generation queries
    ("html to pdf nodejs", "file"),       # bigram "html pdf"→file unchanged
    # graph visualization / network graph → frontend
    ("graph visualization react", "frontend"),  # bigram "graph visualization"→frontend (D3, vis.js, Cytoscape)
    ("network graph react", "frontend"),        # bigram "network graph"→frontend (vis.js, Sigma.js)
    ("network graph d3", "frontend"),           # bigram fires before bare "network"→monitoring
    # Regressions — graph databases still route to database.
    ("graph database neo4j", "database"),       # bare "graph"→database unchanged
    ("graph db typescript", "database"),        # bare "graph"→database unchanged
    # intl → localization (react-intl / FormatJS)
    ("react intl", "localization"),             # bare "intl"→localization (react stripped as framework)
    ("intl library", "localization"),           # bare "intl"→localization
    # headless browser / chrome → testing (overrides headless→cms)
    ("headless browser nodejs", "testing"),     # bigram "headless browser"→testing
    ("headless chrome puppeteer", "testing"),   # bigram "headless chrome"→testing
    # Regressions — headless CMS queries still route to cms.
    ("headless cms strapi", "cms"),             # bare "headless"→cms unchanged
    # html parser / scraper → developer tools
    ("html parser nodejs", "developer"),        # bigram "html parser"→developer (Cheerio, node-html-parser)
    ("html scraper python", "developer"),       # bigram "html scraper"→developer (BeautifulSoup, Scrapy)
    # money → developer (money formatting/parsing libraries)
    ("money formatting react", "developer"),    # bare "money"→developer (accounting.js, dinero.js)
    ("money library javascript", "developer"),  # bare "money"→developer
    # ── Probe pattern 68 (May 2026): loading-state / navigation UI component dead zones ──
    # "skeleton loader react" → "skeleton" unmapped → raw_first; now routes to frontend.
    ("skeleton loader react", "frontend"),     # bare "skeleton"→frontend
    ("skeleton screen component", "frontend"), # bigram "skeleton screen"→frontend
    ("skeleton component shadcn", "frontend"), # bare "skeleton"→frontend
    # "loading spinner" → both tokens unmapped → raw_first; now routes to frontend.
    ("loading spinner react", "frontend"),     # bigram "loading spinner"→frontend
    ("loading state react", "frontend"),       # bare "loading"→frontend
    ("loading overlay component", "frontend"), # bare "loading"→frontend
    # "progress bar component" → "progress" unmapped → raw_first; now routes to frontend.
    ("progress bar component", "frontend"),    # bigram "progress bar"→frontend
    ("progress indicator circular", "frontend"), # bigram "progress indicator"→frontend
    # "breadcrumb navigation" → both tokens unmapped → raw_first; now routes to frontend.
    ("breadcrumb navigation", "frontend"),     # bare "breadcrumb"→frontend
    ("breadcrumb component react", "frontend"), # bare "breadcrumb"→frontend
    # "navbar component" → "navbar" unmapped → raw_first; now routes to frontend.
    ("navbar component react", "frontend"),    # bare "navbar"→frontend
    ("sidebar navigation component", "frontend"), # bare "sidebar"→frontend
    # "navigation menu radix" → "navigation" unmapped → raw_first; now routes to frontend.
    ("navigation menu radix", "frontend"),     # bigram "navigation menu"→frontend
    ("navigation bar component", "frontend"),  # bare "navigation"→frontend
    # "command palette react" → "command" unmapped → raw_first; now routes to frontend.
    ("command palette react", "frontend"),     # bigram "command palette"→frontend
    ("command palette shadcn", "frontend"),    # bigram "command palette"→frontend
    # Regressions — command line must stay cli, lazy loading stays frontend via "lazy".
    ("command line tool", "cli"),              # "command line"→cli bigram fires before bare "command"
    ("lazy loading images", "frontend"),       # "lazy"→frontend fires before bare "loading"
    # Probe pattern 69 (May 2026): SaaS-prefix category mis-routing.
    # "saas"→boilerplate fired as first token for all "saas X" queries.
    # Bigrams override for specific categories when "saas" and the category word are adjacent.
    ("saas analytics tool", "analytics"),          # bigram "saas analytics"→analytics
    ("saas analytics posthog", "analytics"),       # bigram fires at i=0-1
    ("saas metrics dashboard", "analytics"),       # bigram "saas metrics"→analytics
    ("saas metrics baremetrics", "analytics"),     # bigram fires at i=0-1
    ("saas billing stripe", "payments"),           # bigram "saas billing"→payments
    ("saas billing paddle", "payments"),           # bigram fires at i=0-1
    ("saas payments provider", "payments"),        # bigram "saas payments"→payments
    ("saas subscription billing", "payments"),     # bigram "saas subscription"→payments
    ("saas subscription management", "payments"),  # bigram fires at i=0-1
    ("saas auth provider", "authentication"),      # bigram "saas auth"→authentication
    ("saas auth clerk", "authentication"),         # bigram fires at i=0-1
    ("saas authentication nextjs", "authentication"), # long-form bigram → Authentication
    ("saas crm tool", "crm"),                      # bigram "saas crm"→crm
    ("saas crm attio", "crm"),                     # bigram fires at i=0-1
    ("saas email provider", "email"),              # bigram "saas email"→email
    ("saas email resend", "email"),                # bigram fires at i=0-1
    ("saas monitoring tool", "monitoring"),        # bigram "saas monitoring"→monitoring
    ("saas monitoring sentry", "monitoring"),      # bigram fires at i=0-1
    # Regressions — bare "saas" queries must still route to boilerplate.
    ("saas starter kit", "boilerplate"),           # bare "saas"→boilerplate unchanged
    ("saas boilerplate nextjs", "boilerplate"),    # bare "saas"→boilerplate unchanged
    ("saas template react", "boilerplate"),        # bare "saas"→boilerplate unchanged
]


def run_tests(verbose: bool = False) -> tuple[int, int]:
    passed = 0
    failed = 0

    for query, expected in TEST_CASES:
        cat_term, via = route_query(query)
        ok = expected.lower() in cat_term.lower()
        if ok:
            passed += 1
            if verbose:
                print(f"  OK  {query!r:50s} → {cat_term!r} (via {via!r})")
        else:
            failed += 1
            print(f"  FAIL {query!r:50s} → {cat_term!r} (expected {expected!r}, via {via!r})")

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

    if failed == 0:
        print("All routing tests passed.")
        return 0
    else:
        print(f"\n{failed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
