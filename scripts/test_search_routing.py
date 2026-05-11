#!/usr/bin/env python3
"""
Local search routing simulator — validates _CAT_SYNONYMS mappings without production API.

Simulates the category-routing logic from db.py's search_tools() to verify that
queries like "payroll api" route to "Invoicing" and not some other category.

Usage:
    python3 scripts/test_search_routing.py
"""
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Inline copy of the stop words and synonym dict — kept in sync with db.py
# ---------------------------------------------------------------------------

_FTS_STOP_WORDS = {
    "a", "an", "the", "and", "or", "of", "in", "for", "to", "with",
    "best", "top", "free", "open", "source", "alternative", "alternatives",
    "tool", "tools", "library", "libraries", "framework", "frameworks",
    "solution", "solutions", "platform", "service", "services",
    "integration", "integrations", "plugin", "plugins",
    "api", "sdk", "cli", "app", "apps", "software",
    "like", "similar", "vs", "versus",
    "self", "hosted", "selfhosted",
    "nextjs", "react", "vue", "angular", "svelte", "django", "rails",
    "laravel", "express", "fastapi", "flask", "spring",
    "open-source",
}

# Bigrams that should NOT be split (keep as single token for routing)
_PROTECTED_BIGRAMS = {
    "full text",
    "headless browser",
    "article generation",
    "feature flag",
    "rate limit",
    "rate limiting",
    "log management",
    "error tracking",
    "event streaming",
    "event sourcing",
    "change data",
    "data pipeline",
    "background job",
    "job queue",
    "message queue",
    "email verification",
    "email validation",
    "ip geolocation",
    "time series",
    "vector database",
    "vector search",
    "graph database",
    "document database",
    "object storage",
    "secret management",
    "secret manager",
    "secrets manager",
    "password manager",
    "api gateway",
    "api management",
    "api testing",
    "load testing",
    "a/b testing",
    "ab testing",
    "dark launch",
    "canary deploy",
    "blue green",
    "infrastructure as code",
    "function as a service",
    "platform as a service",
    "continuous integration",
    "continuous deployment",
    "continuous delivery",
    "machine learning",
    "deep learning",
    "natural language",
    "computer vision",
    "speech recognition",
    "text classification",
    "sentiment analysis",
    "named entity",
    "knowledge graph",
    "recommendation engine",
    "search engine",
    "reverse proxy",
    "service mesh",
    "content delivery",
    "edge computing",
    "web scraping",
    "data scraping",
    "screen scraping",
    "pdf generation",
    "pdf parsing",
    "image processing",
    "image recognition",
    "video processing",
    "audio processing",
    "speech synthesis",
    "code generation",
    "code review",
    "code quality",
    "static analysis",
    "dependency injection",
    "event driven",
    "micro frontend",
    "component library",
    "design system",
    "ui component",
    "real time",
    "real-time",
    "server sent",
    "server-sent",
}

_CAT_SYNONYMS: dict[str, str] = {}


def _load_synonyms_from_db():
    """Parse _CAT_SYNONYMS directly from db.py source."""
    global _CAT_SYNONYMS
    db_path = Path(__file__).parent.parent / "src" / "indiestack" / "db.py"
    if not db_path.exists():
        return False

    src = db_path.read_text()
    # Find the _CAT_SYNONYMS block
    start = src.find("_CAT_SYNONYMS: dict[str, str] = {")
    if start == -1:
        start = src.find("_CAT_SYNONYMS = {")
    if start == -1:
        return False

    # Find the matching closing brace
    brace_depth = 0
    i = src.index("{", start)
    dict_start = i
    while i < len(src):
        if src[i] == "{":
            brace_depth += 1
        elif src[i] == "}":
            brace_depth -= 1
            if brace_depth == 0:
                dict_end = i + 1
                break
        i += 1
    else:
        return False

    dict_src = src[dict_start:dict_end]
    # Parse key:value pairs
    # Match: "key": "value"
    pattern = re.compile(r'"([^"]+)"\s*:\s*"([^"]+)"')
    _CAT_SYNONYMS = {m.group(1): m.group(2) for m in pattern.finditer(dict_src)}
    return True


def _tokenize(query: str) -> list[str]:
    """Tokenize query: lowercase, strip punctuation, remove stop words."""
    q = query.lower()
    # Normalize common punctuation
    q = re.sub(r"[^a-z0-9 /\-]", " ", q)
    q = q.replace("-", " ").replace("/", " ")
    tokens = [t for t in q.split() if t and t not in _FTS_STOP_WORDS]
    return tokens


def route_query(query: str) -> str | None:
    """Return the best category match for a query, or None."""
    tokens = _tokenize(query)
    if not tokens:
        return None

    # Check bigrams first (at each position), then unigrams
    for i in range(len(tokens)):
        if i + 1 < len(tokens):
            bigram = tokens[i] + " " + tokens[i + 1]
            if bigram in _CAT_SYNONYMS:
                return _CAT_SYNONYMS[bigram]

    for token in tokens:
        if token in _CAT_SYNONYMS:
            return _CAT_SYNONYMS[token]

    return None


# ---------------------------------------------------------------------------
# Test cases: (query, expected_category_fragment)
# The expected fragment must appear in the routed category name (case-insensitive)
# ---------------------------------------------------------------------------

TEST_CASES: list[tuple[str, str]] = [
    # Auth / Identity
    ("oauth provider", "authentication"),
    ("user authentication", "authentication"),
    ("social login", "authentication"),
    ("jwt tokens", "authentication"),
    ("passkeys", "authentication"),
    ("magic link login", "authentication"),
    ("sso saml", "authentication"),
    ("multi factor auth", "authentication"),
    ("mfa totp", "authentication"),
    ("user management", "authentication"),
    ("rbac permissions", "authentication"),
    ("session management", "authentication"),
    ("biometric authentication library", "authentication"),
    ("biometric login nextjs", "authentication"),
    # Payments / Billing
    ("stripe alternative", "payments"),
    ("payment gateway", "payments"),
    ("subscription billing", "payments"),
    ("usage based billing", "payments"),
    ("metered billing", "payments"),
    ("invoicing", "invoicing"),
    ("invoice generation", "invoicing"),
    ("payroll api open source", "invoicing"),
    # Email
    ("transactional email", "email"),
    ("email delivery", "email"),
    ("smtp service", "email"),
    ("email templates", "email"),
    ("email sending", "email"),
    ("email api", "email"),
    # Storage
    ("file storage", "storage"),
    ("object storage", "storage"),
    ("s3 compatible", "storage"),
    ("file uploads", "storage"),
    ("cdn storage", "storage"),
    ("image storage", "storage"),
    # Database
    ("postgres hosting", "database"),
    ("managed database", "database"),
    ("sqlite hosting", "database"),
    ("mysql cloud", "database"),
    ("redis cache", "database"),
    ("key value store", "database"),
    ("document database", "database"),
    # Search
    ("full text search engine", "search"),
    ("search indexing", "search"),
    ("elasticsearch alternative", "search"),
    ("site search", "search"),
    ("faceted search", "search"),
    # CMS
    ("headless cms", "cms"),
    ("content management", "cms"),
    ("structured content", "cms"),
    # AI / ML
    ("llm api", "ai"),
    ("openai alternative", "ai"),
    ("text generation", "ai"),
    ("article generation api", "ai"),
    ("embeddings api", "ai"),
    ("vector similarity", "ai"),
    ("ai inference", "ai"),
    ("fine tuning", "ai"),
    # Monitoring / Observability
    ("error tracking", "monitoring"),
    ("application monitoring", "monitoring"),
    ("uptime monitoring", "monitoring"),
    ("log aggregation", "monitoring"),
    ("apm tool", "monitoring"),
    ("distributed tracing", "monitoring"),
    ("sentry alternative", "monitoring"),
    # Analytics
    ("web analytics", "analytics"),
    ("product analytics", "analytics"),
    ("event tracking", "analytics"),
    ("user behavior analytics", "analytics"),
    ("mixpanel alternative", "analytics"),
    ("amplitude alternative", "analytics"),
    # Feature Flags
    ("feature flags", "feature"),
    ("feature toggles", "feature"),
    ("launchdarkly alternative", "feature"),
    ("a/b testing flags", "feature"),
    # Notifications
    ("push notifications", "notifications"),
    ("in-app notifications", "notifications"),
    ("sms notifications", "notifications"),
    ("notification service", "notifications"),
    ("web push", "notifications"),
    # Queues / Background Jobs
    ("job queue", "queue"),
    ("background jobs", "queue"),
    ("task queue", "queue"),
    ("message queue", "queue"),
    ("worker queue", "queue"),
    ("cron jobs", "queue"),
    # Testing
    ("unit testing", "testing"),
    ("e2e testing", "testing"),
    ("integration tests", "testing"),
    ("test runner", "testing"),
    ("mocking library", "testing"),
    ("headless browser testing", "testing"),
    ("headless browser automation", "testing"),
    # CI/CD
    ("continuous integration", "ci"),
    ("github actions alternative", "ci"),
    ("deployment pipeline", "ci"),
    ("build automation", "ci"),
    # Infrastructure
    ("infrastructure as code", "infrastructure"),
    ("terraform alternative", "infrastructure"),
    ("cloud provisioning", "infrastructure"),
    # Serverless
    ("serverless functions", "serverless"),
    ("edge functions", "serverless"),
    ("function as a service", "serverless"),
    ("lambda alternative", "serverless"),
    # Containers / Orchestration
    ("kubernetes hosting", "containers"),
    ("docker registry", "containers"),
    ("container orchestration", "containers"),
    ("pod scaling", "containers"),
    # Logging
    ("log management", "logging"),
    ("structured logging", "logging"),
    ("log aggregation service", "logging"),
    ("centralized logging", "logging"),
    # Rate Limiting
    ("rate limiting", "rate"),
    ("api rate limit", "rate"),
    ("throttling service", "rate"),
    # Realtime
    ("websocket server", "real"),
    ("realtime database", "real"),
    ("presence detection", "real"),
    ("live updates", "real"),
    # CDN
    ("cdn provider", "cdn"),
    ("edge caching", "cdn"),
    ("content delivery", "cdn"),
    ("static asset hosting", "cdn"),
    # Secrets Management
    ("secrets manager", "secret"),
    ("env var management", "secret"),
    ("secret rotation", "secret"),
    ("vault alternative", "secret"),
    # GeoIP
    ("ip geolocation", "geo"),
    ("ip to country", "geo"),
    ("geolocation api", "geo"),
    # Payments (extended)
    ("checkout flow", "payments"),
    ("recurring payments", "payments"),
    ("payment processing", "payments"),
    # Developer Productivity
    ("code review tool", "developer"),
    ("developer portal", "developer"),
    ("api documentation", "developer"),
    ("openapi tools", "developer"),
    ("sdk generator", "developer"),
    # Forms
    ("form builder", "forms"),
    ("form submissions", "forms"),
    ("survey tool", "forms"),
    ("typeform alternative", "forms"),
    # ORM / Data Access
    ("orm library", "database"),
    ("query builder", "database"),
    ("database migrations", "database"),
    # Graph Databases
    ("graph database", "database"),
    ("knowledge graph api", "database"),
    # Vector / AI DB
    ("vector database", "ai"),
    ("embedding storage", "ai"),
    ("semantic search", "search"),
    # PDF / Docs
    ("pdf generation", "pdf"),
    ("pdf parsing", "pdf"),
    ("document conversion", "pdf"),
    # Maps
    ("maps api", "maps"),
    ("geocoding api", "maps"),
    ("routing api", "maps"),
    # Media / Images
    ("image optimization", "media"),
    ("image processing api", "media"),
    ("media upload", "media"),
    ("video transcoding", "media"),
    # Chat / Support
    ("live chat widget", "chat"),
    ("customer support chat", "chat"),
    ("helpdesk software", "helpdesk"),
    # CRM
    ("crm api", "crm"),
    ("customer data platform", "crm"),
    # Communication
    ("sms api", "sms"),
    ("voice api", "voice"),
    ("video calling api", "video"),
    ("twilio alternative", "sms"),
    # Caching
    ("caching layer", "caching"),
    ("redis hosting", "caching"),
    ("memcached service", "caching"),
    # Scheduling
    ("appointment booking", "scheduling"),
    ("calendar api", "scheduling"),
    ("meeting scheduler", "scheduling"),
    # E-commerce
    ("ecommerce api", "ecommerce"),
    ("product catalog api", "ecommerce"),
    ("shopping cart api", "ecommerce"),
    # Blockchain / Web3
    ("blockchain api", "blockchain"),
    ("smart contract tools", "blockchain"),
    ("web3 authentication", "blockchain"),
    # Security
    ("penetration testing", "security"),
    ("vulnerability scanner", "security"),
    ("ddos protection", "security"),
    ("waf service", "security"),
    # Compliance
    ("gdpr compliance", "compliance"),
    ("soc2 tools", "compliance"),
    ("audit logging", "compliance"),
    # A/B Testing (standalone)
    ("ab testing platform", "a/b"),
    ("split testing", "a/b"),
    ("experimentation platform", "a/b"),
    # Workflow / Automation
    ("workflow automation", "workflow"),
    ("zapier alternative", "workflow"),
    ("n8n alternative", "workflow"),
    # Localization
    ("i18n library", "localization"),
    ("translation api", "localization"),
    ("localization platform", "localization"),
    # Payments — crypto
    ("crypto payments", "payments"),
    ("bitcoin payments", "payments"),
    # Hosting / PaaS
    ("paas platform", "hosting"),
    ("app hosting", "hosting"),
    ("heroku alternative", "hosting"),
    ("railway alternative", "hosting"),
    # Deployment
    ("zero downtime deploy", "deployment"),
    ("blue green deployment", "deployment"),
    ("canary deployment", "deployment"),
    # DNS
    ("dns management", "dns"),
    ("dns api", "dns"),
    ("custom domain routing", "dns"),
    # Identity Verification
    ("kyc verification", "identity"),
    ("id verification api", "identity"),
    ("document verification", "identity"),
    # Fraud Detection
    ("fraud detection", "fraud"),
    ("bot detection", "fraud"),
    ("captcha alternative", "fraud"),
    # Internal Tools
    ("internal dashboard", "internal"),
    ("admin panel builder", "internal"),
    ("retool alternative", "internal"),
    # Data Pipelines / ETL
    ("etl pipeline", "data"),
    ("data ingestion", "data"),
    ("data transformation", "data"),
    ("fivetran alternative", "data"),
    # Event Streaming
    ("event streaming", "event"),
    ("kafka alternative", "event"),
    ("event bus", "event"),
    # Webhooks
    ("webhook delivery", "webhook"),
    ("webhook management", "webhook"),
    ("svix alternative", "webhook"),
    # Metrics
    ("metrics collection", "metrics"),
    ("prometheus alternative", "metrics"),
    ("time series database", "time"),
    # Screen Recording
    ("session recording", "session"),
    ("screen recording sdk", "session"),
    ("heatmap tool", "session"),
    # Password / Credential
    ("password hashing", "authentication"),
    ("credential management", "secret"),
    # Reverse Proxy
    ("reverse proxy", "reverse"),
    ("ingress controller", "reverse"),
    # Service Mesh
    ("service mesh", "service"),
    ("istio alternative", "service"),
    # Extended auth
    ("two factor authentication", "authentication"),
    ("passwordless login", "authentication"),
    ("oauth 2.0 server", "authentication"),
    # Extended email
    ("email bounce handling", "email"),
    ("email warmup", "email"),
    ("cold email", "email"),
    # Extended storage
    ("blob storage", "storage"),
    ("media storage", "storage"),
    # Extended database
    ("nosql database", "database"),
    ("time series db", "database"),
    ("olap database", "database"),
    # Extended search
    ("autocomplete api", "search"),
    ("type ahead search", "search"),
    ("meilisearch alternative", "search"),
    ("typesense alternative", "search"),
    # Extended monitoring
    ("synthetic monitoring", "monitoring"),
    ("real user monitoring", "monitoring"),
    ("crash reporting", "monitoring"),
    # Extended CI/CD
    ("test parallelization", "ci"),
    ("flaky test detection", "ci"),
    # Extended serverless
    ("serverless containers", "serverless"),
    ("deno deploy alternative", "serverless"),
    # Extended developer tools
    ("api mocking", "developer"),
    ("api versioning", "developer"),
    ("postman alternative", "developer"),
    # Extended forms
    ("conditional forms", "forms"),
    ("multi step forms", "forms"),
    # Extended media
    ("image cdn", "media"),
    ("video hosting", "media"),
    ("audio processing", "media"),
    # Extended localization
    ("string translation", "localization"),
    ("locale management", "localization"),
]


def run_tests() -> tuple[int, int]:
    """Run all test cases. Returns (passed, failed)."""
    if not _load_synonyms_from_db():
        print("ERROR: Could not load _CAT_SYNONYMS from db.py", file=sys.stderr)
        return 0, len(TEST_CASES)

    passed = 0
    failed = 0
    failures = []

    for query, expected_fragment in TEST_CASES:
        result = route_query(query)
        if result and expected_fragment.lower() in result.lower():
            passed += 1
        else:
            failed += 1
            failures.append((query, expected_fragment, result))

    if failures:
        print(f"\n{'='*60}")
        print(f"FAILURES ({len(failures)}/{len(TEST_CASES)} test cases):")
        print(f"{'='*60}")
        for query, expected, got in failures:
            print(f"  FAIL: {query!r}")
            print(f"        expected category containing: {expected!r}")
            print(f"        got: {got!r}")
        print()

    print(f"Results: {passed}/{len(TEST_CASES)} passed, {failed} failed")
    return passed, failed


def main() -> int:
    passed, failed = run_tests()
    if failed > 0:
        print("\n❌ Some routing tests failed.")
        print("Fix _CAT_SYNONYMS in src/indiestack/db.py")
        print('Then re-run: python3 scripts/test_search_routing.py')
        return 1

    print("✅ All routing tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
