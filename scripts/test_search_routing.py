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
    # AI Standards & Benchmarks — new bigrams (added May 2026)
    ("ai benchmark tool", "ai standards"),          # "ai benchmark" bigram → AI Standards & Specs
    ("red teaming framework llm", "ai standards"),  # "red teaming" bigram → AI Standards & Specs
    ("model comparison leaderboard", "ai standards"),  # "model comparison" bigram → AI Standards & Specs
    ("hallucination benchmark open source", "ai standards"),  # "hallucination" → AI Standards & Specs
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
