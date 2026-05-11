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

    # Step 4: Fallback — use raw first meaningful term
    if meaningful_for_cat:
        return meaningful_for_cat[0], "raw_first"

    return query.lower().strip(), "none"


# ---------------------------------------------------------------------------
# Test suite: (query, expected_cat_term)
# ---------------------------------------------------------------------------
TEST_CASES: list[tuple[str, str]] = [
    # ─ Authentication ──────────────────────────────────────────────────────
    ("auth for nextjs", "authentication"),
    ("authentication service", "authentication"),
    ("oauth provider", "authentication"),
    ("sso solution", "authentication"),
    ("single sign-on", "authentication"),
    ("social login", "authentication"),
    ("magic link auth", "authentication"),
    ("passkey authentication", "authentication"),
    ("jwt authentication", "authentication"),
    ("session management", "authentication"),
    ("user authentication", "authentication"),
    ("login system", "authentication"),
    ("identity provider", "authentication"),
    ("clerk alternative", "authentication"),
    ("auth0 alternative", "authentication"),
    ("supabase auth", "authentication"),
    ("firebase auth", "authentication"),
    ("nextauth alternative", "authentication"),
    ("lucia auth", "authentication"),
    ("better-auth alternative", "authentication"),
    ("workos alternative", "authentication"),
    ("stytch alternative", "authentication"),
    ("hanko alternative", "authentication"),
    ("keycloak alternative", "authentication"),
    ("logto alternative", "authentication"),
    ("password manager", "authentication"),
    ("mfa solution", "authentication"),
    ("2fa library", "authentication"),
    ("rbac library", "authentication"),
    ("authorization library", "authentication"),
    ("access control", "authentication"),
    ("permissions library", "authentication"),
    # ─ Payments ──────────────────────────────────────────────────────────
    ("payment gateway", "payments"),
    ("payment processing", "payments"),
    ("stripe alternative", "payments"),
    ("subscription billing", "payments"),
    ("checkout solution", "payments"),
    ("paddle alternative", "payments"),
    ("lemonsqueezy alternative", "payments"),
    ("polar alternative", "payments"),
    ("paypal alternative", "payments"),
    ("monetization tools", "payments"),
    ("merchant account", "payments"),
    # ─ Analytics ─────────────────────────────────────────────────────────
    ("web analytics", "analytics"),
    ("analytics platform", "analytics"),
    ("plausible alternative", "analytics"),
    ("posthog alternative", "analytics"),
    ("mixpanel alternative", "analytics"),
    ("fathom alternative", "analytics"),
    ("umami alternative", "analytics"),
    ("product analytics", "analytics"),
    ("user tracking", "analytics"),
    ("event tracking", "analytics"),
    ("pageview tracking", "analytics"),
    ("session recording", "analytics"),
    # ─ Email ─────────────────────────────────────────────────────────────
    ("transactional email", "email"),
    ("email service provider", "email"),
    ("smtp service", "email"),
    ("resend alternative", "email"),
    ("sendgrid alternative", "email"),
    ("postmark alternative", "email"),
    ("mailgun alternative", "email"),
    ("email delivery", "email"),
    ("email api", "email"),
    ("drip email", "email"),
    # ─ Monitoring ────────────────────────────────────────────────────────
    ("uptime monitoring", "monitoring"),
    ("status page", "monitoring"),
    ("site monitoring", "monitoring"),
    ("error tracking", "monitoring"),
    ("sentry alternative", "monitoring"),
    ("upstatus alternative", "monitoring"),
    ("betterstack alternative", "monitoring"),
    ("opentelemetry alternative", "monitoring"),
    ("grafana alternative", "monitoring"),
    ("datadog alternative", "monitoring"),
    ("application monitoring", "monitoring"),
    ("performance monitoring", "monitoring"),
    ("opentelemetry tracing", "monitoring"),
    ("opentelemetry metrics", "monitoring"),
    ("apm tool", "monitoring"),
    # ─ Forms ──────────────────────────────────────────────────────────────
    ("form builder", "forms"),
    ("contact form", "forms"),
    ("typeform alternative", "forms"),
    ("tally alternative", "forms"),
    ("survey tool", "forms"),
    ("form validation", "forms"),
    # ─ CMS ───────────────────────────────────────────────────────────────
    ("headless cms", "cms"),
    ("content management", "cms"),
    ("contentful alternative", "cms"),
    ("sanity alternative", "cms"),
    ("strapi alternative", "cms"),
    ("payload alternative", "cms"),
    ("directus alternative", "cms"),
    # ─ SEO ───────────────────────────────────────────────────────────────
    ("seo tools", "seo"),
    ("search engine optimization", "seo"),
    ("sitemap generator", "seo"),
    ("meta tags library", "seo"),
    ("structured data", "seo"),
    ("ahrefs alternative", "seo"),
    # ─ DevOps ───────────────────────────────────────────────────────────
    ("ci cd pipeline", "devops"),
    ("docker alternative", "devops"),
    ("kubernetes alternative", "devops"),
    ("infrastructure as code", "devops"),
    ("heroku alternative", "devops"),
    ("vercel alternative", "devops"),
    ("netlify alternative", "devops"),
    ("render alternative", "devops"),
    ("railway alternative", "devops"),
    ("fly.io alternative", "devops"),
    ("cloud hosting", "devops"),
    ("vps provider", "devops"),
    ("load balancer", "devops"),
    ("load balancing", "devops"),
    ("reverse proxy", "devops"),
    ("nginx alternative", "devops"),
    ("caddy server", "devops"),
    ("traefik alternative", "devops"),
    ("coolify alternative", "devops"),
    ("caprover alternative", "devops"),
    ("dokku alternative", "devops"),
    ("kamal deployment", "devops"),
    ("container orchestration", "devops"),
    ("autoscaling solution", "devops"),
    ("auto-scaling", "devops"),
    # ─ Database ──────────────────────────────────────────────────────────
    ("database hosting", "database"),
    ("postgres hosting", "database"),
    ("mysql alternative", "database"),
    ("sqlite alternative", "database"),
    ("redis alternative", "database"),
    ("neon alternative", "database"),
    ("planetscale alternative", "database"),
    ("turso alternative", "database"),
    ("supabase alternative", "database"),
    ("mongodb alternative", "database"),
    ("nosql database", "database"),
    ("vector database", "database"),
    ("time series database", "database"),
    ("orm library", "database"),
    ("prisma alternative", "database"),
    ("drizzle alternative", "database"),
    ("sqlalchemy alternative", "database"),
    ("kysely alternative", "database"),
    ("database migration", "database"),
    ("schema migration", "database"),
    # ─ Frontend ──────────────────────────────────────────────────────────
    ("frontend framework", "frontend"),
    ("react alternative", "frontend"),
    ("vue alternative", "frontend"),
    ("svelte alternative", "frontend"),
    ("nextjs alternative", "frontend"),
    ("remix alternative", "frontend"),
    ("astro alternative", "frontend"),
    ("nuxt alternative", "frontend"),
    ("solidjs alternative", "frontend"),
    ("qwik alternative", "frontend"),
    ("gatsby alternative", "frontend"),
    ("component library", "frontend"),
    ("ui library", "frontend"),
    ("css framework", "frontend"),
    ("tailwind alternative", "frontend"),
    ("state management", "frontend"),
    ("zustand alternative", "frontend"),
    ("redux alternative", "frontend"),
    ("jotai alternative", "frontend"),
    ("tanstack query", "frontend"),
    ("animation library", "frontend"),
    ("framer motion alternative", "frontend"),
    # ─ AI ───────────────────────────────────────────────────────────────
    ("ai sdk", "ai"),
    ("llm api", "ai"),
    ("openai alternative", "ai"),
    ("anthropic alternative", "ai"),
    ("langchain alternative", "ai"),
    ("vector search", "ai"),
    ("embedding api", "ai"),
    ("ai chatbot", "ai"),
    ("rag pipeline", "ai"),
    ("ai agent framework", "ai"),
    ("vercel ai", "ai"),
    # ─ MCP ───────────────────────────────────────────────────────────────
    ("mcp server", "mcp"),
    ("model context protocol", "mcp"),
    ("claude mcp", "mcp"),
    ("mcp registry", "mcp"),
    ("mcp tools", "mcp"),
    # ─ Storage / File management ──────────────────────────────────────
    ("file storage", "file"),
    ("object storage", "file"),
    ("s3 alternative", "file"),
    ("cdn service", "file"),
    ("media storage", "file"),
    ("image storage", "file"),
    ("cloudflare r2 alternative", "file"),
    ("minio alternative", "file"),
    # ─ CRM ───────────────────────────────────────────────────────────────
    ("crm software", "crm"),
    ("sales crm", "crm"),
    ("hubspot alternative", "crm"),
    ("pipedrive alternative", "crm"),
    ("salesforce alternative", "crm"),
    # ─ Developer Tools ───────────────────────────────────────────────
    ("api documentation", "api"),
    ("openapi spec", "api"),
    ("sdk generator", "developer"),
    ("code linting", "developer"),
    ("type checking", "developer"),
    ("env management", "developer"),
    ("dotenv alternative", "developer"),
    ("turborepo alternative", "developer"),
    ("monorepo tool", "developer"),
    ("nx alternative", "developer"),
    ("zod alternative", "developer"),
    ("schema validation", "developer"),
    ("yup alternative", "developer"),
    ("valibot alternative", "developer"),
    ("validation library", "developer"),
    ("dub alternative", "developer"),
    # ─ Background Jobs ───────────────────────────────────────────────
    ("background jobs", "background"),
    ("job queue", "background"),
    ("task queue", "background"),
    ("celery alternative", "background"),
    ("bull alternative", "background"),
    ("bullmq alternative", "background"),
    ("inngest alternative", "background"),
    ("trigger.dev alternative", "background"),
    ("cron jobs", "background"),
    ("scheduled tasks", "background"),
    ("worker queue", "background"),
    ("task-queue alternative", "background"),
    ("async-task library", "background"),
    # ─ Testing ────────────────────────────────────────────────────────────
    ("testing framework", "testing"),
    ("unit testing", "testing"),
    ("e2e testing", "testing"),
    ("playwright alternative", "testing"),
    ("cypress alternative", "testing"),
    ("vitest alternative", "testing"),
    ("jest alternative", "testing"),
    ("pytest alternative", "testing"),
    # ─ Feature Flags ───────────────────────────────────────────────────
    ("feature flags", "feature"),
    ("feature toggles", "feature"),
    ("launchdarkly alternative", "feature"),
    ("unleash alternative", "feature"),
    ("flagsmith alternative", "feature"),
    ("growthbook alternative", "feature"),
    ("posthog feature flags", "feature"),
    # ─ API Tools ─────────────────────────────────────────────────────────
    ("api gateway", "api"),
    ("api management", "api"),
    ("rest api framework", "api"),
    ("graphql server", "api"),
    ("trpc alternative", "api"),
    ("hono alternative", "api"),
    ("fastapi alternative", "api"),
    # ─ Security ──────────────────────────────────────────────────────────
    ("security scanning", "security"),
    ("vulnerability scanning", "security"),
    ("secrets management", "security"),
    ("vault alternative", "security"),
    ("snyk alternative", "security"),
    # ─ Caching ───────────────────────────────────────────────────────────
    ("caching solution", "caching"),
    ("redis caching", "caching"),
    ("memcached alternative", "caching"),
    ("upstash alternative", "caching"),
    ("key-value store", "caching"),
    ("keyvalue store", "caching"),
    # ─ Search ─────────────────────────────────────────────────────────────
    ("full text search", "search"),
    ("search engine", "search"),
    ("elasticsearch alternative", "search"),
    ("meilisearch alternative", "search"),
    ("typesense alternative", "search"),
    ("algolia alternative", "search"),
    # ─ Logging ────────────────────────────────────────────────────────────
    ("logging service", "logging"),
    ("log management", "logging"),
    ("logtail alternative", "logging"),
    ("papertrail alternative", "logging"),
    ("logflare alternative", "logging"),
    # ─ Notifications ─────────────────────────────────────────────────────
    ("push notifications", "notifications"),
    ("in-app notifications", "notifications"),
    ("novu alternative", "notifications"),
    ("onesignal alternative", "notifications"),
    # ─ Message Queue ─────────────────────────────────────────────────────
    ("message queue", "message"),
    ("event streaming", "message"),
    ("kafka alternative", "message"),
    ("rabbitmq alternative", "message"),
    ("nats alternative", "message"),
    # ─ Design ─────────────────────────────────────────────────────────────
    ("design tool", "design"),
    ("ui design", "design"),
    ("figma alternative", "design"),
    ("icon library", "design"),
    # ─ Feedback ───────────────────────────────────────────────────────────
    ("user feedback", "feedback"),
    ("review widget", "feedback"),
    ("canny alternative", "feedback"),
    # ─ Boilerplates ───────────────────────────────────────────────────────
    ("saas boilerplate", "boilerplate"),
    ("starter template", "boilerplate"),
    ("nextjs boilerplate", "boilerplate"),
    ("shipfast alternative", "boilerplate"),
    # ─ Project Management ─────────────────────────────────────────────
    ("project management", "project"),
    ("issue tracker", "project"),
    ("linear alternative", "project"),
    ("jira alternative", "project"),
    # ─ Landing Pages ───────────────────────────────────────────────────
    ("landing page builder", "landing"),
    ("landing page tool", "landing"),
    ("framer alternative", "landing"),
    # ─ Localization ───────────────────────────────────────────────────────
    ("i18n library", "localization"),
    ("internationalization library", "localization"),
    ("translation management", "localization"),
    ("crowdin alternative", "localization"),
    # ─ CLI Tools ─────────────────────────────────────────────────────────
    ("cli framework", "cli"),
    ("command line tool", "cli"),
    ("terminal ui", "cli"),
    ("oclif alternative", "cli"),
    ("ink alternative", "cli"),
    # ─ Documentation ─────────────────────────────────────────────────────
    ("docs platform", "documentation"),
    ("docusaurus alternative", "documentation"),
    ("mintlify alternative", "documentation"),
    ("gitbook alternative", "documentation"),
    # ─ Scheduling ────────────────────────────────────────────────────────
    ("appointment scheduling", "scheduling"),
    ("booking system", "scheduling"),
    ("cal.com alternative", "scheduling"),
    ("calendly alternative", "scheduling"),
    # ─ Customer Support ───────────────────────────────────────────────
    ("live chat", "customer"),
    ("help desk", "support"),
    ("intercom alternative", "customer"),
    ("zendesk alternative", "support"),
    # ─ Maps / Location ────────────────────────────────────────────────
    ("maps api", "maps"),
    ("geocoding api", "maps"),
    ("mapbox alternative", "maps"),
    # ─ Social / Media ─────────────────────────────────────────────────
    ("social media scheduling", "social"),
    ("twitter api alternative", "social"),
    ("media server", "media"),
    ("video streaming", "media"),
    ("jellyfin alternative", "media"),
    # ─ Newsletters ───────────────────────────────────────────────────────
    ("newsletter platform", "newsletters"),
    ("substack alternative", "newsletters"),
    ("beehiiv alternative", "newsletters"),
    # ─ Invoicing ────────────────────────────────────────────────────────
    ("invoicing software", "invoicing"),
    ("billing system", "invoicing"),
    ("invoice generator", "invoicing"),
    # ─ AI Dev Tools ───────────────────────────────────────────────────────
    ("ai coding assistant", "ai dev"),
    ("copilot alternative", "ai dev"),
    ("cursor alternative", "ai dev"),
    ("codeium alternative", "ai dev"),
    ("tabnine alternative", "ai dev"),
    ("github copilot alternative", "ai dev"),
    ("supermaven alternative", "ai dev"),
    ("qodo alternative", "ai dev"),
    ("codiumai alternative", "ai dev"),
    # ─ Learning / Education ─────────────────────────────────────────────
    ("learning platform", "learning"),
    ("online course platform", "learning"),
    ("lms alternative", "learning"),
]


def run_tests(verbose: bool = False, single_query: str | None = None) -> bool:
    """Run all test cases. Returns True if all pass."""
    if single_query:
        cat_term, matched_via = route_query(single_query)
        print(f"Query: {single_query!r}")
        print(f"  → cat_term={cat_term!r}  matched_via={matched_via!r}")
        return True

    passed = 0
    failed = 0
    failures: list[tuple[str, str, str, str]] = []

    for query, expected in TEST_CASES:
        actual, matched_via = route_query(query)
        ok = actual == expected
        if ok:
            passed += 1
            if verbose:
                print(f"  ✓ {query!r} → {actual!r}  (via {matched_via!r})")
        else:
            failed += 1
            failures.append((query, expected, actual, matched_via))
            if verbose:
                print(f"  ✗ {query!r}  expected={expected!r}  got={actual!r}  (via {matched_via!r})")

    print(f"\nResults: {passed}/{passed+failed} passed", end="")
    if failed:
        print(f", {failed} FAILED")
        print()
        for query, expected, actual, matched_via in failures:
            print(f"  FAIL: {query!r}")
            print(f"        expected={expected!r}  got={actual!r}  matched_via={matched_via!r}")
        return False
    else:
        print(" ✔")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test search routing against _CAT_SYNONYMS")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all results")
    parser.add_argument("--query", "-q", help="Test a single query")
    args = parser.parse_args()

    ok = run_tests(verbose=args.verbose, single_query=args.query)
    sys.exit(0 if ok else 1)
