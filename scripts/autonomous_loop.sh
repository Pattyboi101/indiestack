#!/bin/bash
# Autonomous improvement loop — runs claude (Sonnet) in a cycle every hour
# Uses RAG for context instead of reading full memory files
#
# Launch: tmux new-session -d -s autoloop 'bash scripts/autonomous_loop.sh'
# Stop:   tmux kill-session -t autoloop

REPO_DIR="$HOME/indiestack"
INTERVAL=3600  # seconds between runs
MCP_CONFIG="$REPO_DIR/.orchestra/mcp-config.json"

cd "$REPO_DIR"

# MCP flags for RAG access
MCP_FLAGS=""
if [ -f "$MCP_CONFIG" ]; then
  MCP_FLAGS="--mcp-config $MCP_CONFIG"
fi

while true; do
    echo ""
    echo "=========================================="
    echo "  Autonomous cycle starting: $(date)"
    echo "=========================================="

    claude --dangerously-skip-permissions --model sonnet $MCP_FLAGS -p "You are the IndieStack autonomous improvement agent running on Sonnet.

Use rag_query() for context instead of reading full memory files.
After fixing anything, rag_store() the knowledge so other agents benefit.

Run the 6-iteration cycle:

ITERATION 1 — SEARCH QUALITY:
curl the API for these queries and check top-3 results are relevant:
  'auth for nextjs', 'payments', 'email sending', 'database', 'monitoring',
  'stripe alternative', 'cron job scheduler nodejs', 'self hosted auth',
  'state management', 'bundler', 'realtime', 'vector database', 'rate limiting'.
For each misfire, check BOTH dicts in db.py:
  A) _CAT_SYNONYMS — maps individual query tokens to category slug fragment (used for scoring)
  B) NEED_MAPPINGS terms lists — used by Stack Builder and developer profile interest scoring
  A term can exist in _CAT_SYNONYMS but be absent from NEED_MAPPINGS terms — check both.
Also check _FTS_STOP_WORDS — overly broad stop words cause query word drops.
Before editing, grep db.py for the term to confirm absence (avoids duplicate-key edits).
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

    echo ""
    echo "Cycle complete: $(date)"
    echo "Sleeping ${INTERVAL}s until next cycle..."
    sleep "$INTERVAL"
done
