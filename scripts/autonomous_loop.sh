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
For each misfire, check if a _CAT_SYNONYMS entry or NEED_MAPPINGS term is missing in db.py.
Before adding any synonym: grep '"<term>"' db.py to avoid silent duplicate-key overrides.
Fix missing mappings. Also check _FTS_STOP_WORDS — overly broad stop words cause misses.
After fixing db.py, commit with 'fix: improve search mappings for [queries]'.

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
