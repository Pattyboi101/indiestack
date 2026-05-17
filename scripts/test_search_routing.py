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
