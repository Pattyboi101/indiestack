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
Run offline routing audit first (no API needed, catches regressions fast):
  python3 scripts/test_search_routing.py
If any tests fail, fix _CAT_SYNONYMS in db.py before continuing.

Then probe new gaps using the offline route_query() helper. Use these probe strategies:

  STRATEGY A — Named-tool dead zones (peer-tool audit):
    When you map one tool in a category, probe all peer tools in that family.
    New agents/AI: 'agno framework', 'smolagents', 'dspy framework', 'haystack ai', 'pydantic ai'
    New databases: 'turso serverless', 'xata database', 'neon serverless', 'motherduck duckdb'
    New auth: 'hanko passkey', 'scalekit sso', 'stytch auth', 'ory kratos'
    New payments: 'lemon squeezy', 'polar sh', 'creem payments', 'dodopayments'
    New MCP: 'model context protocol server', 'context protocol implementation', 'mcp gateway'

  STRATEGY B — Shadowed single-token probe (probe pattern 55 style):
    For any query where token-0 maps to catA but the INTENT is catB, check if a
    bigram starting at token-1 can override. Example: "model"→ai shadows "protocol"→mcp
    in "model context protocol"; fix: "context protocol"→mcp bigram fires at i=1.
    Test: 'full text search engine', 'server sent events', 'model context protocol server'

  STRATEGY C — Stop-word drop probe (probe pattern 52 style):
    For spaced compound queries, strip all stop words and check if the remainder is
    in _CAT_SYNONYMS. Common stop words: on, of, for, with, using, via, in, at.
    Test: 'on call alerting', 'open source license scanner', 'e2e encryption library'

  STRATEGY D — Category fan-out probe (probe pattern 54 style):
    For any "X Y" where X has a single-token map, probe "X analytics", "X monitoring",
    "X notifications", "X logging" — each non-primary category needs its own bigram.
    Test: 'realtime analytics', 'realtime monitoring', 'realtime notifications'

  STRATEGY E — Short-form/gerund gaps (probe pattern 51 style):
    After adding a bigram "X evaluation"→cat, always add "X eval", "X evaluating" too.
    Test: 'llm eval', 'llm benchmarking', 'ai evaluation framework'

For each misfire, add the missing entry to _CAT_SYNONYMS and a test case. Commit.
After fixing db.py, commit with 'fix: probe pattern N — [short desc] (M/M pass)'.

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
Grep route files for hardcoded stats (tool counts, install counts, category counts).
Verify against production DB: SELECT COUNT(*) FROM tools WHERE status='approved'.
Fix any stale copy that's off by more than 10%. Run smoke_test.py after route changes.

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
