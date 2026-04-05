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

Run the 5-iteration cycle:

ITERATION 1 — SEARCH QUALITY: curl the API for 'auth for nextjs', 'payments', 'email sending', 'database', 'monitoring', 'stripe alternative', 'cron job scheduler nodejs', 'self hosted auth', 'frontend framework', 'state management react', 'caching redis alternative', 'mcp server', 'push notifications', 'trpc', 'htmx'. Flag bad results (wrong category, irrelevant tools) and fix _CAT_SYNONYMS in db.py to correct them.

ITERATION 2 — DATA QUALITY: SSH to prod (fly ssh console -a indiestack) and find tools with high mcp_view_count but missing install_command or description. Fix them. Check for zero-result queries. Rebuild FTS after changes.

ITERATION 3 — COMPETITIVE: Search GitHub for new MCP servers trending this week. Log findings to .orchestra/logs/\$(date +%Y-%m-%d)-research.md

ITERATION 4 — PROVOCATION: Run python3 scripts/provoke.py. Before acting: (1) helps distribution/search/revenue? (2) someone else doing it? (3) under 30 min? Only act if all pass.

ITERATION 5 — RAG HYGIENE: Query RAG for entries tagged 'checkpoint' older than 24h and note any that seem stale. Check if any recent code changes contradict stored knowledge. Clean up as needed.

AFTER: bash ~/.claude/telegram.sh '[Bot] Session summary: [what you checked/fixed/researched]'

Rules: never git add -A, never Co-Authored-By Claude, run smoke_test.py before pushing, DO NOT deploy, OK to exit early if nothing to do."

    echo ""
    echo "Cycle complete: $(date)"
    echo "Sleeping ${INTERVAL}s until next cycle..."
    sleep "$INTERVAL"
done
