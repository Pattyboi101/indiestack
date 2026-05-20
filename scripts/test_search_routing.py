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
