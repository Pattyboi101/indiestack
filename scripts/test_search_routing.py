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


# ── Test cases ───────────────────────────────────────────────────────────────────────────────────────
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
    ("webhook handler", "api"),
    ("rate limiting", "api"),
    ("ai coding assistant", "ai"),
    ("mcp server", "mcp"),
    ("boilerplate saas starter", "boilerplate"),
    ("feature flag", "feature"),
    ("log management", "logging"),
    ("structured logs", "logging"),
    ("push notification", "notifications"),
    ("i18n library", "localization"),
    ("translation api", "localization"),
    ("cli tool", "cli"),
    ("docs generator", "documentation"),
    ("knowledge base chatbot", "ai"),               # bigram form → AI & Automation
    ("full text search", "search"),
    ("message broker", "message"),
    ("video streaming", "media"),
    # Fix regressions — terms that previously routed wrong
    ("state management react", "frontend"),
    ("bundler vite webpack", "frontend"),
    ("realtime websocket", "api"),
    # React-qualifier bigram pre-pass fixes (added to catch mis-routing after framework stripping)
    ("react form library", "frontend"),          # "react form" bigram pre-pass; was wrongly → forms
    ("react form validation", "frontend"),       # same fix — React Hook Form, Formik
    ("react query setup", "frontend"),           # "react query" bigram pre-pass; was wrongly → database
    ("react query v5", "frontend"),              # TanStack Query v5 queries
    # Payments
    ("checkout api", "payments"),
    ("stripe webhooks", "payments"),
    ("payment processing", "payments"),
    ("subscription management", "payments"),
    # Analytics
    ("product analytics", "analytics"),
    ("session recording", "analytics"),
    ("funnel tracking", "analytics"),
    ("heatmap tool", "analytics"),
    ("conversion tracking", "analytics"),
    # Monitoring
    ("application monitoring", "monitoring"),
    ("distributed tracing", "monitoring"),
    ("log aggregation", "logging"),
    ("alert management", "monitoring"),
    ("infrastructure monitoring", "monitoring"),
    ("status page", "monitoring"),
    ("uptime checker", "monitoring"),
    ("apm tool", "monitoring"),
    ("opentelemetry setup", "monitoring"),
    ("sentry alternative", "monitoring"),
    # AI & Automation
    ("langchain alternative", "ai"),
    ("llm observability", "ai"),
    ("prompt management", "ai"),
    ("vector search embedding", "ai"),
    ("rag pipeline", "ai"),
    ("ai workflow automation", "ai"),
    ("llm gateway", "ai"),
    ("model evaluation framework", "ai standards"),  # bigram "model evaluation" → AI Standards & Specs
    ("ai eval harness", "ai standards"),             # bigram "ai eval" → AI Standards & Specs
    ("ai evals tool", "ai standards"),               # bigram "ai evals" → AI Standards & Specs
    ("safety eval framework", "ai standards"),       # bigram "safety eval" → AI Standards & Specs
    ("capability eval suite", "ai standards"),       # bigram "capability eval" → AI Standards & Specs
    # AI Dev Tools
    ("cursor alternative", "ai"),
    ("copilot alternative", "ai"),
    ("code completion", "ai dev"),
    ("github copilot open source", "ai"),
    ("ai code review", "ai"),
    # DevOps
    ("docker alternative", "devops"),
    ("kubernetes helm", "devops"),
    ("ci cd pipeline", "devops"),
    ("container registry", "devops"),
    ("terraform alternative", "devops"),
    ("deploy nodejs", "devops"),
    ("vps hosting", "devops"),
    ("merge queue tool", "devops"),           # "merge queue" bigram → devops (Mergify, github merge queues), not "queue"→background
    # CRM
    ("customer relationship", "customer"),
    ("lead management", "crm"),
    ("sales automation", "crm"),
    ("pipeline management", "crm"),
    # Email
    ("drip campaign", "email"),
    ("email sequence", "email"),
    ("smtp server", "email"),
    # Database
    ("postgres alternative", "database"),
    ("mysql cloud", "database"),
    ("nosql database", "database"),
    ("sqlite alternative", "database"),
    ("database migration", "database"),
    ("prisma alternative", "database"),
    # Search
    ("search engine", "search"),
    ("typesense setup", "search"),
    ("meilisearch alternative", "search"),
    ("algolia alternative", "search"),
    # Security
    ("secret management", "security"),
    ("vulnerability scanning", "security"),
    ("penetration testing", "security"),
    ("compliance tool", "security"),
    # Forms
    ("contact form", "forms"),
    ("typeform alternative", "forms"),
    # Feedback
    ("customer feedback", "feedback"),
    ("user reviews", "user"),
    ("bug reporting", "analytics"),
    # Support
    ("helpdesk software", "support"),
    ("live chat", "customer"),
    ("ticketing system", "support"),
    # SEO
    ("seo audit", "seo"),
    ("keyword research", "seo"),
    ("backlink checker", "seo"),
    # CMS
    ("blog platform", "cms"),
    ("sanity alternative", "cms"),
    ("strapi alternative", "cms"),
    # Invoicing
    ("invoice generator", "invoicing"),
    ("billing system", "payments"),
    ("accounting software", "invoicing"),
    # Social Media
    ("social media management", "social"),
    ("twitter scheduler", "social"),
    ("social media scheduling", "social"),
    # MCP Servers
    ("mcp server setup", "mcp"),
    ("smithery mcp", "mcp"),
    ("context7 mcp", "mcp"),
    ("docker mcp setup", "mcp"),            # bigram "docker mcp" → Docker MCP Toolkit → MCP Servers
    ("pulsemcp analytics", "mcp"),
    ("mcp tool integration", "mcp"),
    ("claude mcp server", "ai"),            # "claude" fires first → AI (acceptable for now)
    ("model context protocol", "ai"),       # "model" → ai (acceptable; context and protocol stripped)
    ("cursor mcp", "ai"),                   # "cursor" → ai (cursor is an AI tool; "mcp" fires 2nd)
    # AI Standards
    ("garak llm scanner", "ai standards"),
    ("lm-eval setup", "ai standards"),
    ("arc-agi benchmark", "ai standards"),
    # Caching
    ("caching redis", "caching"),
    ("redis alternative", "caching"),
    ("in-memory store", "caching"),
    # Message Queue
    ("message queue kafka", "message"),
    ("task queue worker", "background"),     # bigram "task queue" → background-jobs (more accurate than "task"→developer)
    # Media
    ("media server video", "media"),
    # Maps & Location
    ("geocoding library", "maps"),
    ("leaflet alternative", "maps"),
    # Background Jobs
    ("workflow automation", "background"),
    ("n8n alternative", "background"),
    # Frontend
    ("react state management", "frontend"),
    ("nextjs starter", "frontend"),
    ("svelte alternative", "frontend"),
    ("vite alternative", "frontend"),
    ("esbuild alternative", "frontend"),
    ("css framework", "frontend"),
    ("tailwind alternative", "frontend"),
    ("component library", "frontend"),
    ("ui kit", "frontend"),
    ("design system", "design"),
    ("vue alternative", "frontend"),
    ("angular alternative", "frontend"),
    ("shadcn alternative", "frontend"),
    # Developer Tools
    ("testing framework", "testing"),
    ("unit testing", "testing"),
    ("e2e testing", "testing"),
    ("mocking library", "testing"),
    ("code quality", "testing"),
    # Landing Pages
    ("landing page", "landing"),
    ("static site generator", "frontend"),
    # Learning
    ("online course platform", "learning"),
    ("flashcard app", "learning"),
    # Publishing / Newsletters
    ("newsletter platform", "email"),
    ("blog platform ghost", "cms"),
    # File
    ("object storage", "file"),
    ("media upload", "media"),
    ("cdn storage", "devops"),
    # Creative
    ("music production", "music"),
    ("video editor", "media"),
    # Specific tool queries (regression tests — these exact slugs routed wrong before)
    ("plausible analytics", "analytics"),
    ("posthog alternative", "analytics"),
    ("cal.com alternative", "scheduling"),
    ("railway alternative", "devops"),
    ("render alternative", "devops"),
    ("coolify self hosted", "devops"),
    ("supabase alternative", "database"),
    ("pocketbase alternative", "database"),
    ("neon postgres", "database"),
    ("clerk alternative", "authentication"),
    ("logto alternative", "authentication"),
    ("polar payments", "payments"),
    ("lemon squeezy alternative", "payments"),
    ("resend email", "email"),
    ("plunk email", "email"),
    ("umami analytics", "analytics"),
    ("countly analytics", "analytics"),
    ("typeform alternative", "forms"),
    # Bigram routing tests — bigrams take priority over unigrams at the same position
    ("load balancer nginx", "devops"),       # "load balancer" bigram beats "load"→testing
    ("load balancing setup", "devops"),      # "load balancing" bigram beats "load"→testing
    ("feature gate rollout", "feature"),     # "feature gate" bigram → Feature Flags
    ("vector store embeddings", "database"), # "vector store" bigram → database
    ("server sent events", "api"),           # "server sent" bigram → api-tools (SSE)
    ("token bucket rate limit", "api"),      # bigram "token bucket" beats "token"→authentication
    ("sliding window algorithm", "api"),     # bigram "sliding window" → api (rate limiting pattern)
    ("edge function cloudflare", "devops"),  # "edge function" bigram → devops (Functions category)
    # Hosting / Infrastructure
    ("paas platform", "devops"),
    ("self hosted", "devops"),
    ("fly.io alternative", "devops"),
    # AI-specific terms
    ("chatbot builder", "ai"),
    ("llm fine tuning", "ai"),
    ("embedding model", "ai"),
    ("retrieval augmented", "ai"),
    ("agent framework", "ai"),
    ("openai alternative", "ai"),
    ("claude api", "ai"),
    ("ollama alternative", "ai"),
    # Testing
    ("playwright alternative", "testing"),
    ("cypress alternative", "testing"),
    ("jest alternative", "testing"),
    ("vitest setup", "testing"),
    ("test coverage", "testing"),
    # Specific frameworks / libraries that had wrong routing
    ("htmx alternative", "frontend"),
    ("alpine.js alternative", "frontend"),
    ("solid.js framework", "frontend"),
    ("astro framework", "frontend"),
    ("remix framework", "frontend"),
    ("nuxt alternative", "frontend"),
    ("sveltekit alternative", "frontend"),
    ("gatsby alternative", "frontend"),
    # Localization
    ("next-intl setup", "localization"),
    ("react-i18next", "localization"),
    ("crowdin alternative", "localization"),
    # CLI
    ("ink react cli", "cli"),
    ("oclif framework", "cli"),
    ("cobra cli", "cli"),
    ("zsh alternative", "cli"),
    # Documentation
    ("mintlify alternative", "documentation"),
    ("docusaurus setup", "documentation"),
    ("gitbook alternative", "documentation"),
    ("readme generator", "documentation"),
    # AI Dev Tools — MCP and copilots
    ("cursor rules", "ai"),
    ("windsurf alternative", "ai"),
    ("codeium alternative", "ai"),
    ("tabnine alternative", "ai"),
    # Notifications
    ("novu alternative", "notifications"),
    ("knock notifications", "notifications"),
    ("onesignal alternative", "notifications"),
    # Logging
    ("logtail alternative", "logging"),
    ("papertrail alternative", "logging"),
    ("grafana loki setup", "monitoring"),
    # Maps
    ("mapbox alternative", "maps"),
    ("openstreetmap api", "maps"),
    ("leaflet maps", "maps"),
    # Frontend Frameworks — Angular state management (added May 2026)
    ("ngrx state management", "frontend"),          # "ngrx" → frontend (Angular Redux-style state)
    ("ngxs angular state", "frontend"),             # "ngxs" → frontend (Angular state management)
    ("akita angular state", "frontend"),            # "akita" → frontend (Akita state management)
    # Feature Flags
    ("unleash alternative", "feature"),
    ("flagsmith setup", "feature"),
    ("growthbook alternative", "feature"),
    # Payments — billing edge cases
    ("open source billing", "payments"),
    ("usage based pricing", "invoicing"),
    # Invoicing
    ("open source invoicing", "invoicing"),
    # Games
    ("game engine alternative", "games"),
    ("indie game engine", "games"),
    # Learning
    ("lms platform", "learning"),
    ("quiz builder", "learning"),
    # Publishing
    ("ghost alternative", "cms"),
    ("substack alternative", "email"),
    # Support
    ("zendesk alternative", "support"),
    ("chatwoot setup", "support"),
    ("freshdesk alternative", "support"),
    # Scheduling
    ("cal.com setup", "scheduling"),
    ("appointment booking", "scheduling"),
    # Frontend — bundlers and build tools (May 2026)
    ("rspack bundler alternative", "frontend"),     # Rspack — Rust webpack-compat bundler → Frontend
    ("parcel bundler setup", "frontend"),           # Parcel — zero-config bundler → Frontend
    ("rolldown vite bundler", "frontend"),          # Rolldown — Rust Rollup replacement (Vite 6) → Frontend
    ("turbopack next", "frontend"),                 # Turbopack — Vite competitor (Next.js 15) → Frontend
    ("bun runtime alternative", "frontend"),        # Bun — JS runtime + bundler → Frontend
    # AI — Streaming LLM fix (added to prevent "streaming"→"media" collision)
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
