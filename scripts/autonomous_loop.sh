#!/bin/bash
# Autonomous improvement loop — runs claude (Sonnet) in a cycle every hour
# Uses RAG for context instead of reading full memory files
#
# Launch: tmux new-session -d -s autoloop 'bash scripts/autonomous_loop.sh'
# Stop:   tmux kill-session -t autoloop
#
# Resilience: crash recovery with retries, structured logging, Telegram alerts.
# Watchdog:   scripts/autoloop_watchdog.sh monitors this process externally.

REPO_DIR="$HOME/indiestack"
INTERVAL=3600  # seconds between runs
MCP_CONFIG="$REPO_DIR/.orchestra/mcp-config.json"
LOG_DIR="$REPO_DIR/.orchestra/logs"
HEARTBEAT_FILE="$REPO_DIR/.orchestra/autoloop-heartbeat"
TELEGRAM="$HOME/.claude/telegram.sh"

MAX_RETRIES=3
RETRY_BASE=2  # exponential backoff base (seconds)

cd "$REPO_DIR"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# MCP flags for RAG access
MCP_FLAGS=""
if [ -f "$MCP_CONFIG" ]; then
  MCP_FLAGS="--mcp-config $MCP_CONFIG"
fi

# Structured logging helper
log() {
    local level="$1"
    shift
    local msg="$*"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local logfile="$LOG_DIR/autoloop-$(date +%Y-%m-%d).log"
    echo "[$timestamp] [$level] $msg" | tee -a "$logfile"
}

# Update heartbeat — watchdog checks this file's mtime
update_heartbeat() {
    date '+%Y-%m-%d %H:%M:%S' > "$HEARTBEAT_FILE"
}

# Send Telegram alert
alert() {
    local msg="$1"
    if [ -f "$TELEGRAM" ]; then
        bash "$TELEGRAM" "$msg" 2>/dev/null
    fi
}

# Iteration 0 — reactive event check (fast, no AI, just SSH + Telegram)
run_event_reactor() {
    log "INFO" "Running event reactor (Iteration 0)..."
    if [ -f "$REPO_DIR/scripts/event_reactor.py" ]; then
        python3 "$REPO_DIR/scripts/event_reactor.py" 2>&1 | while read -r line; do
            log "REACTOR" "$line"
        done
        local exit_code=${PIPESTATUS[0]}
        if [ $exit_code -ne 0 ]; then
            log "WARN" "Event reactor exited with code $exit_code"
        else
            log "INFO" "Event reactor complete"
        fi
    else
        log "WARN" "Event reactor script not found, skipping"
    fi
}

# Run a single claude cycle with retry logic
run_cycle() {
    local attempt=0
    local delay=$RETRY_BASE

    while [ $attempt -lt $MAX_RETRIES ]; do
        attempt=$((attempt + 1))
        log "INFO" "Cycle attempt $attempt/$MAX_RETRIES starting"

        claude --dangerously-skip-permissions --model sonnet $MCP_FLAGS -p "You are the IndieStack autonomous improvement agent running on Sonnet.

Use rag_query() for context instead of reading full memory files.
After fixing anything, rag_store() the knowledge so other agents benefit.

Run the 6-iteration cycle:

ITERATION 1 — SEARCH QUALITY:
curl the API for these queries and check top-3 results are relevant:
  Core: 'auth for nextjs', 'payments', 'email sending', 'database', 'monitoring',
        'stripe alternative', 'cron job scheduler nodejs', 'self hosted auth'.
  Frontend: 'state management', 'bundler', 'build tool', 'react component library'.
  AI/Voice: 'voice agent', 'text to speech api', 'speech to text', 'tts api',
            'ai coding assistant', 'local llm', 'llm gateway', 'agent framework'.
  AI Models: 'maverick llm', 'llama 4 maverick', 'run maverick locally',
             'task master ai', 'claude task master', 'taskmaster mcp'.
  Infra: 'realtime', 'vector database', 'rate limiting', 'dev environment',
         'cloud dev environment', 'remote development'.
  Search: 'exa alternative', 'exa search api', 'neural search api'.
  CSS/ADK: 'stylelint alternative', 'purgecss setup', 'create react app alternative',
           'cra vs vite', 'adk agent python', 'google adk alternative'.
  New categories: 'mcp server', 'boilerplate saas starter', 'caching redis alternative'.
  OpenAI 2026: 'openai agents sdk', 'responses api openai', 'agents sdk python alternative',
               'openai swarm replacement', 'goose ai agent', 'block goose coding agent'.
  Repo/LLM: 'repomix alternative', 'pack repo for llm', 'gitingest setup', 'repo to llm context'.
  Browser agents: 'ai browser automation', 'browser agent python', 'steel browser alternative',
                  'browserbase alternative', 'hyperbrowser setup', 'cloud browser api'.
  New AI editors: 'aide ide alternative', 'melty vs cursor', 'amp coding agent', 'codestory ide'.
  AI engineers: 'swe-agent alternative', 'sweep ai code review', 'cosine ai genie', 'devin alternative'.
  New AI tools: 'kilo code extension', 'kilo code vs cline', 'amazon q alternative', 'q developer aws',
               'gemini code assist alternative', 'same dev app builder', 'same.dev clone'.
  Dev envs: 'devenv nix', 'devenv alternative', 'devbox jetpack', 'cde tool', 'cloud dev environment',
            'warp terminal alternative', 'nix dev environment', 'reproducible dev environment'.
  Workflows: 'temporal workflow alternative', 'gitops deployment tool', 'argocd alternative',
             'azure promptflow alternative', 'promptfoo llm testing'.
  AI benchmarks: 'mmlu-pro benchmark', 'gpqa diamond score', 'livecodebench leaderboard',
                 'arc-agi benchmark', 'arc agi 2 prize', 'frontiermath eval', 'swe-bench verified'.
  Classic benchmarks: 'gsm8k benchmark', 'hellaswag score', 'truthfulqa evaluation',
                      'mt-bench score', 'chatbot arena ranking', 'bfcl function calling',
                      'alpacaeval leaderboard', 'winogrande benchmark', 'mbpp code eval'.
  MCP servers (official): 'mcp stripe server', 'mcp supabase alternative', 'mcp neon database',
                          'mcp cloudflare workers', 'stripe mcp setup'.
  Kimi K2: 'kimi k2 alternative', 'kimi k2 api', 'kimi k2 weights', 'moonshot kimi model'.
  OpenAI GPT-4.1 (added May 2026 — gpt41/gpt-4-1/gpt41-mini/gpt41-nano/gpt4o-mini synonyms added):
    'gpt-4.1 alternative', 'gpt41 api', 'gpt4-1 setup', 'gpt 4.1 mini alternative',
    'gpt41-mini vs claude', 'gpt41 nano pricing', 'gpt-4o-mini alternative',
    'gpt4o-mini vs claude haiku', 'gpt4omini api'. Must route to AI & Automation.
  Cloud browsers: 'steel browser alternative', 'steel browser api', 'cloud browser api'.
  Official MCP servers: 'github mcp server', 'figma mcp cursor', 'git mcp hallucination',
                        'aws mcp server', 'firecrawl mcp', 'desktop commander mcp',
                        'xcode mcp server', 'google mcp toolbox databases'.
  MCP hyphenated forms: 'stripe-mcp alternative', 'supabase-mcp setup', 'neon-mcp database',
                        'cloudflare-mcp workers', 'context7 mcp docs'.
  Docker MCP: 'docker mcp toolkit', 'docker mcp setup', 'docker-mcp alternative',
              'run mcp server docker', 'dockermcp container'.
  AI research tools: 'notebooklm alternative', 'notebooklm api', 'notebook-lm research'.
  Headless/testing: 'headless browser', 'headless browser testing', 'headless browser automation',
                    'headless ui component', 'browser automation python', 'puppeteer alternative'.
  Enterprise auth: 'scim provisioning', 'ldap directory sync', 'active directory integration',
                   'user provisioning saas', 'directory sync tool'.
  IDE rules files: 'cursor rules setup', 'cursor-rules template', 'cursorrules file',
                   'windsurf rules config', 'windsurfrules example'.
  MCP registries: 'mcp registry', 'mcp-registry alternative', 'pulsemcp analytics',
                  'opentools mcp discovery', 'mcp marketplace search'.
  Multi-agent: 'multi-agent framework', 'multi-agent system', 'multi-agent orchestration'.
  GPU cloud for LLM: 'runpod alternative', 'runpod vs lambda labs', 'vast ai gpu rental',
                     'lambda labs gpu cloud', 'coreweave alternative', 'cheap gpu cloud llm'.
  AI SWE agents: 'sweep ai alternative', 'sweep code review', 'pieces for devs alternative',
                 'pieces app snippets', 'pieces vs github copilot'.
  AI Standards (must route to ai-standards category — fixed May 2026 after hyphen bug):
    'garak llm scanner', 'lm-eval setup', 'inspect-ai alternative', 'swe-bench verified',
    'arc-agi benchmark', 'mmlu-pro benchmark', 'gpqa diamond score', 'lm evaluation harness'.
  Infra & DevOps (added May 2026 — paas/vps/reverse-proxy/gpu synonyms added):
    'gpu cloud', 'gpu compute llm', 'cheap gpu inference', 'paas provider',
    'vps hosting indie', 'reverse proxy setup', 'nginx alternative reverse proxy',
    'ddos protection service', 'cross-platform desktop app', 'tauri vs electron'.
  RAG & document processing (added May 2026 — markitdown/surya/unstructured/bm25 synonyms added):
    'markitdown alternative', 'convert pdf to markdown llm', 'surya ocr alternative',
    'unstructured io document parsing', 'document chunker python', 'text splitter rag',
    'cross encoder reranking', 'bm25 search library', 'mistral ocr api',
    'colpali visual retrieval', 'hybrid search bm25 vector'.
  Forms & e-signature (added May 2026 — fillout/heyform/paperform/esignature synonyms added):
    'fillout alternative', 'heyform self hosted', 'paperform alternative',
    'esignature api', 'e-signature tool', 'digital signature api',
    'pandadoc alternative', 'signnow alternative', 'reform app forms',
    'form backend free', 'html form endpoint', 'docuseal esignature'.
  Waitlist / referral / in-app changelog (added May 2026 — waitlist/referral/affiliate/beamer synonyms added):
    'waitlist tool', 'launch waitlist api', 'pre-launch email collection',
    'referral program software', 'referral tracking tool', 'referralhero alternative',
    'affiliate tracking software', 'rewardful alternative', 'growsurf alternative',
    'beamer alternative', 'in-app changelog widget', 'headway changelog',
    'olvy product changelog', 'featurebase alternative', 'noticeable announcements',
    'product update widget', 'in-app notification tool'.
  Product onboarding & tour libraries (added May 2026 — appcues/userpilot/driverjs synonyms added):
    'appcues alternative', 'userpilot alternative', 'userguiding alternative',
    'product adoption platform', 'user onboarding software',
    'intro.js alternative', 'driver.js alternative', 'shepherd.js alternative',
    'product tour library javascript', 'interactive guide library'.
  Product adoption & behavior analytics (added May 2026 — chameleon/userflow/mouseflow/smartlook synonyms added):
    'chameleon alternative', 'chameleon io product adoption', 'userflow onboarding',
    'mouseflow alternative', 'mouseflow heatmap', 'smartlook alternative',
    'smartlook session recording', 'session recording tool', 'heatmap tool'.
  PR review, merge queues & engineering metrics (added May 2026 — pr-agent/mergify/gitstream/linearb synonyms added):
    'pr-agent alternative', 'pr-agent setup', 'qodo merge alternative', 'qodo-merge setup',
    'qodo gen alternative', 'ai pr review tool', 'ai code review bot',
    'mergify alternative', 'mergify setup', 'github merge queue tool',
    'gitstream alternative', 'gitstream pr automation',
    'linearb alternative', 'linearb engineering metrics',
    'reviewdog alternative', 'reviewdog ci setup', 'inline pr comments linter'.
  Observability & tracing (2026 — opentelemetry/otel/jaeger synonyms confirmed):
    'opentelemetry alternative', 'opentelemetry setup nodejs', 'otel collector setup',
    'distributed tracing jaeger', 'distributed tracing zipkin', 'apm tool open source',
    'signoz alternative', 'grafana alternative', 'self-hosted observability stack'.
  Monorepo & package management (2026 — turborepo/nx/pnpm synonyms confirmed):
    'monorepo build tool', 'turborepo alternative', 'nx monorepo setup',
    'pnpm workspaces setup', 'lerna alternative', 'changesets monorepo versioning'.
  Code quality & linting (2026 — lint/eslint/biome/prettier in testing-tools by design):
    'eslint alternative', 'biome linter setup', 'code formatter prettier alternative',
    'js linter nodejs', 'typescript linter tool'.
  Error tracking & secrets (2026 — error→monitoring, secrets→security):
    'error tracking sentry alternative', 'bugsnag alternative', 'rollbar alternative',
    'secrets management doppler alternative', 'infisical alternative', 'vault secrets'.
  Time-series databases (May 2026 — series→database added; time→api REMOVED to fix false routing):
    'time series database', 'time series data influxdb', 'timescaledb alternative',
    'questdb alternative', 'influxdb alternative', 'time series storage'.
    NOTE: 'time'→api was removed — realtime queries still route via 'real'→api and 'realtime'→api.
  Data engineering & ETL (May 2026 — etl/pipeline/warehouse/lake synonyms confirmed):
    'etl pipeline tool', 'data pipeline orchestration', 'data warehouse alternative',
    'dbt alternative', 'apache airflow alternative', 'batch processing framework',
    'data lake storage', 'stream processing tool'.
  Screen recording & UX analytics (May 2026 — recording/feedback tokens added):
    'screen recording tool', 'ux recording tool', 'user feedback widget',
    'customer feedback tool', 'feedback collection tool'.
  Session recording vs auth (May 2026 — bigram routing added; 'session recording' beats 'session'→auth):
    'session recording tool', 'smartlook session recording'. Must route to analytics, NOT authentication.
  Product adoption vs frontend (May 2026 — bigram routing added):
    'product adoption platform', 'user onboarding software'. Must route to feedback-reviews.
    NOTE: 'product tour library javascript' must still route to FRONTEND (library ≠ SaaS platform).
  In-app changelog vs devops (May 2026 — bigram routing added):
    'in-app changelog widget', 'product changelog tool'. Must route to feedback-reviews.
    NOTE: 'changelog' alone still routes to devops (git-cliff, semantic-release).
  Image generation vs media (May 2026 — bigram routing added; 'image generation' beats 'image'→media):
    'image generation model', 'image generation api', 'text to image model', 'ai image generator',
    'stable diffusion alternative', 'dalle alternative'. Must route to AI, NOT Media Servers.
    NOTE: 'image editor' and 'media server' still route to media (correct).
  Code generation (May 2026 — bigram routing added; 'code generation' and 'code gen' → AI Dev Tools):
    'code generation tool', 'code gen api', 'code generation model', 'ai code generator'.
    NOTE: 'code review' → developer is separate (via 'review'→developer token).
  Status pages (May 2026 — 'status' and 'status page' bigram added → monitoring):
    'status page tool', 'status page alternative', 'status page open source', 'uptime status page'.
    NOTE: 'statuspage'→monitoring (compound form) was already covered; gap was spaced form.
  Health checks (May 2026 — 'health' and 'health-check' added → monitoring):
    'health check library', 'health check api', 'health probe setup', 'health-check middleware'.
    NOTE: 'healthcheck' compound was already at line 3426; only bare 'health' and 'health-check' were new.
  Social login (May 2026 — 'social login/auth/sign' bigrams added → authentication):
    'social login provider', 'social auth library', 'social sign in flow', 'social oauth provider'.
    NOTE: 'social media scheduling' must still route to social-media (regression guard in test suite).
For each misfire, check if a _CAT_SYNONYMS entry or NEED_MAPPINGS term is missing in db.py.
Before adding any synonym: grep '"<term>"' db.py to avoid silent duplicate-key overrides.
Fix missing mappings. Also check _FTS_STOP_WORDS — overly broad stop words cause misses.
BIGRAM ROUTING NOTE (May 2026): db.py routing now checks bigrams BEFORE individual tokens.
  Add spaced compound entries like "session recording" → "analytics" to _CAT_SYNONYMS to override
  individual token collisions. Bigrams are checked left-to-right at adjacent positions.
  Known May 2026 bigram fixes (already applied — skip if 185 routing tests pass):
    'block goose' + 'goose block' → "ai dev"  (was "database" via 'goose'→Go migration tool)
    'docker mcp' → "mcp"  (was "devops" via 'docker'→devops; covers Docker MCP Toolkit queries)
    'image generation' → "ai"  (was "media" via 'image'→media; covers AI image gen queries)
    'code generation' + 'code gen' → "ai dev"  (was raw_first "code"; covers codegen tool queries)
    'status page' → "monitoring"  (was raw_first "status" with no category match)
    'text image' → "ai"  (from "text to image" after stop-word removal; AI image model queries)
    'ai image' → "ai"  (bigram for "ai image generator"; "ai" alone not mapped to avoid wide collisions)
    'ai gateway' → "ai"  (overrides "gateway"→api for LLM proxy/router queries)
    'sales pipeline' → "crm"  (was "background" via 'pipeline'→background)
    'sales' → "crm"  (for "sales tool", "sales tracking" queries)
    'contact management' → "crm"  (was "project" via 'management'→project)
    'website builder' → "landing"  (for website builder tool queries)
    'portfolio' → "landing"  (for portfolio site queries)
    'task queue' → "background"  (overrides "task"→developer for queue queries)
    'data pipeline' → "background"  (prevents 'pipeline management'→crm from stealing data pipeline queries)
    'lead' → "crm"  (for "lead scoring", "lead management", "lead capture")
    'pipeline management' → "crm"  (overrides "pipeline"→background for sales CRM queries)
    'llm evaluation' + 'llm benchmark' → "ai standards"  (overrides "llm"→ai for eval-specific queries)
    'health' + 'health-check' → "monitoring"  (was unrouted via raw_first "health"; added May 2026)
    'social login' + 'social auth' + 'social sign' → "authentication"  (was mis-routing to "social" social-media; added May 2026)
    'erd' + 'erd diagram' → "database"  (ERD tools — was raw_first "erd"; added May 2026)
    'diagramming' → "developer"  (Mermaid/draw.io — was raw_first; added May 2026)
    'web server' → "api"  (backend web servers — was raw_first "web"; added May 2026)
    'code generator' → "ai dev"  (complements "code generation" bigram; added May 2026)
    'clean architecture' + 'hexagonal architecture' + 'onion architecture' → "developer"  (added May 2026)
    NOTE: "web framework" CANNOT be a bigram — "framework" is in _FTS_STOP_WORDS. Known gap.
  CAUTION: Do NOT add "ai" as a single-token fallback — it breaks "ai browser automation"→testing
           and "ai pr review"→developer. Use targeted "ai *" bigrams instead.
  CAUTION: Always run validate_synonyms.py after adding entries to catch duplicate keys.
           Duplicate keys silently override with the last value (Python dict behavior).
           "healthcheck" (line 3426) and "task-queue" (line 6239) are canonical — do not re-add.
  CAUTION: Bigrams that include stop words (framework, tool, service, app, library, etc.) can NEVER fire.
           Stop words are stripped before bigram matching. Always verify both tokens survive.
           Example: "web framework"→impossible (framework is stop word); "web server"→possible.
After fixing db.py, run validate_synonyms.py to check for duplicates, then commit.
  Probe pattern 34 (May 2026): "pdf generation"/"pdf generator"/"pdf creator" were routing to file-management
    via bare "pdf"→file. "qr code generator" was routing to ai-dev via "code generator" bigram which fired
    before bare "qr"→developer. Fixed: bigrams "pdf generation", "pdf generator", "pdf creator"→developer;
    "html pdf"→developer (matches "html to pdf" after stop-word "to" stripping); "qr code"→developer.
    Bare "pdf"→file-management unaffected (editor/viewer queries still route there).
  Probe pattern 35 (May 2026): UX research dead zones — "user research"/"user interview" fired raw_first
    because "user" has no synonym mapping. "maze", "usertesting", "lookback", "dovetail" also unmapped.
    Fixed: bigrams "user research"/"user interview"→feedback; bare "qualitative","maze","usertesting",
    "lookback","dovetail"→feedback. Regressions guarded for "user authentication"→auth, "user analytics"→analytics.
  Probe pattern 37 (May 2026): SaaS metrics + product feedback dead zones — "mrr","arr","cac","revenue"
    had no mapping → raw_first fired. "feature request" mis-routed via "feature"→feature-flags (wrong).
    "release notes" widget queries mis-routed via "release"→devops.
    Fixed: bare "mrr","arr","cac","revenue"→analytics; bigrams "feature request","feature requests"→feedback;
    "release notes"→feedback. Also removed msgpack duplicate (lines 3688+8149).
    Regressions: "feature flag toggle"→feature-flags, "release version management"→devops still pass.
    Test queries: 'mrr dashboard', 'arr analytics', 'cac calculation', 'revenue tracking' → analytics.
    'feature request tool', 'collect feature requests' → feedback.
    'release notes widget' → feedback; 'release version management' → devops.
  Probe pattern 38 (May 2026): typography / versioning / modal-dialog / contrast / cost / sortable dead zones.
    "typography" → raw_first (no boost); "versioning" → raw_first; "contrast checker" → raw_first;
    "modal dialog" → ai (wrong: Modal.com override); "cost optimization" → raw_first; "sortable list" → raw_first;
    "focus management" → project (wrong: "management"→project collision); "semantic release" → search (wrong:
    "semantic"→search collision); "screen reader" → raw_first; "keyboard navigation" → raw_first.
    Fixed: "typography"→frontend; "versioning"→devops; bigram "modal dialog"→frontend (overrides Modal.com);
    "contrast"→testing; bigrams "screen reader"→testing, "keyboard navigation"→testing; "cost"→devops;
    bigram "semantic release"→devops; "sortable"→frontend; bigram "focus management"→frontend.
    Regression guards: "modal serverless gpu"→ai (Modal.com bare token), "subscription cost billing"→payments,
    "semantic search engine"→search all still pass.
  Probe pattern 40 (May 2026): performance/latency monitoring dead zones + supply-chain/cloud-provider.
    "p99"/"p95"/"p50" — latency percentile terms — had no mapping; APM/tracing queries fired raw_first.
    "apdex" — Application Performance Index — monitoring metric with no _CAT_SYNONYMS entry.
    "percentile" — "latency percentile", "99th percentile response" — no mapping, raw_first fired.
    "bottleneck" — "performance bottleneck analysis", "bottleneck profiler" — no monitoring entry.
    "server timing" bigram — Server-Timing HTTP header / APM breakdown — both tokens unmapped.
    "supply chain" bigram — "supply chain attack/security" — bare "supply" had no entry.
    "cloud provider" bigram — "cloud provider alternative" — "cloud" alone intentionally unmapped.
    Fixed: "p99","p95","p50","apdex","percentile","bottleneck"→monitoring; bigrams "server timing"→monitoring,
    "supply chain"→security, "cloud provider"→devops.
    Regression guards: "cloud function runtime"→devops, "sbom generator"→security, "cloud hosting"→devops,
    "bottleneck" not colliding with "profiling"→monitoring or "performance testing"→testing.
After all fixes: python3 scripts/test_search_routing.py should report 939+ tests passing (40 probe patterns).

ITERATION 2 — DATA QUALITY:
SSH to prod (flyctl ssh console -a indiestack) and:
  - Find tools with high mcp_view_count but missing install_command, description, or github_url.
  - Check scripts/add_missing_tools.py — if any slugs from that script are missing from prod, run it.
  - After any DB changes, rebuild FTS: INSERT INTO tools_fts(tools_fts) VALUES('rebuild');
  - Run PRAGMA wal_checkpoint(TRUNCATE).

ITERATION 3 — COMPETITIVE RESEARCH:
Search GitHub for new MCP servers trending this week (search 'mcp server' sort:stars pushed:>2026-03-01).
Log findings to .orchestra/logs/\$(date +%Y-%m-%d)-research.md.
If any trending MCP servers are missing from IndieStack, add them to scripts/add_missing_tools.py.

ITERATION 4 — PROVOCATION:
Run python3 scripts/provoke.py. Before acting on any suggestion, ask:
  (1) Does it help distribution, search quality, or revenue?
  (2) Is someone else already doing it?
  (3) Can it be done in under 30 minutes?
Only act if ALL three pass.

ITERATION 5 — MEMORY HYGIENE:
Check memory/sprint.md exists and is up-to-date (if missing, create it).
Check memory/decisions.md exists with key decisions logged.
Query RAG for entries tagged 'checkpoint' older than 24h — note stale ones.
Check if recent code changes contradict stored RAG knowledge.

ITERATION 6 — COPY AUDIT:
Grep route files AND mcp_server.py for hardcoded stats (tool counts, install counts, category counts).
  grep -n "8,000\|43 categor\|25 categor" src/indiestack/mcp_server.py — fix any matches to match
  current reality (6,500+ tools, 29 categories). mcp_server.py changes do NOT need smoke_test.py.
Verify route-file counts against production DB: SELECT COUNT(*) FROM tools WHERE status='approved'.
Fix any stale copy that's off by more than 10%. Run smoke_test.py after route file changes only.
Also check: 'repomix alternative', 'gitingest setup', 'repo to llm' queries route to ai-dev-tools.

AFTER: bash ~/.claude/telegram.sh '[Bot] Session summary: [what you checked/fixed/researched]'

Rules:
- Never git add -A or git add . — stage specific files only
- Never Co-Authored-By Claude in commits
- Run python3 smoke_test.py before committing any route file changes
- DO NOT deploy
- Commit style: 'fix: ...' or 'feat: ...' or 'chore: ...' lowercase concise
- OK to exit early if nothing needs fixing"

        local exit_code=$?

        if [ $exit_code -eq 0 ]; then
            log "INFO" "Cycle completed successfully"
            return 0
        fi

        log "WARN" "Cycle attempt $attempt failed (exit code $exit_code)"

        if [ $attempt -lt $MAX_RETRIES ]; then
            log "INFO" "Retrying in ${delay}s..."
            sleep "$delay"
            delay=$((delay * 2))
        fi
    done

    # All retries exhausted
    log "ERROR" "Cycle failed after $MAX_RETRIES attempts"
    alert "[Autoloop] Cycle failed after $MAX_RETRIES retries at $(date '+%H:%M %b %d'). Check logs: $LOG_DIR/autoloop-$(date +%Y-%m-%d).log"
    return 1
}

# Main loop
log "INFO" "Autoloop starting (PID $$, interval ${INTERVAL}s, max retries $MAX_RETRIES)"
alert "[Autoloop] Started at $(date '+%H:%M %b %d') (PID $$)"
update_heartbeat

while true; do
    log "INFO" "========== Cycle starting =========="
    update_heartbeat

    # Iteration 0: quick reactive checks before the heavy AI cycle
    run_event_reactor

    run_cycle
    cycle_result=$?

    # Phase 4: Proactive pattern detection (daily cooldown built-in)
    log "INFO" "Running pattern detector..."
    if [ -f "$REPO_DIR/scripts/pattern_detector.py" ]; then
        python3 "$REPO_DIR/scripts/pattern_detector.py" --from-autoloop 2>&1 | while read -r line; do
            log "PATTERN" "$line"
        done
    fi

    update_heartbeat
    log "INFO" "Cycle finished (result=$cycle_result). Sleeping ${INTERVAL}s..."
    sleep "$INTERVAL"
done
