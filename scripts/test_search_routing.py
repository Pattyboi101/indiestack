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
    syn_term = None
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


# ── Test cases ──────────────────────────────────────────────────────────────
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
    ("task queue worker", "developer"),      # "task" → developer; use "cron job" for background-jobs routing
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
