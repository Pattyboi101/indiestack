#!/bin/bash
# Launch the IndieStack Orchestra — Dynamic Model Architecture
# CEO (Opus) + 5 departments in tmux, Manager runs separately as Patrick's session
#
# Usage:
#   .orchestra/launch.sh              # launch CEO + all 5 departments
#   .orchestra/launch.sh frontend backend  # launch specific departments only (no CEO)

set -e

REPO_DIR="$HOME/indiestack"
SESSION="orchestra"
MCP_CONFIG="$REPO_DIR/.orchestra/mcp-config.json"
CLAUDE_FLAGS="--dangerously-skip-permissions --dangerously-load-development-channels server:claude-peers"

# Ensure claude-peers broker is running before launching agents
BROKER_PORT="${CLAUDE_PEERS_PORT:-7899}"
if ! curl -sf "http://127.0.0.1:${BROKER_PORT}/" >/dev/null 2>&1; then
  echo "  Starting claude-peers broker..."
  cd "$HOME/claude-peers-mcp" && bun run broker.ts >> /tmp/claude-peers-broker.log 2>&1 &
  sleep 2
  if curl -sf "http://127.0.0.1:${BROKER_PORT}/" >/dev/null 2>&1; then
    echo "  claude-peers broker started"
  else
    echo "  WARNING: claude-peers broker failed to start — peer messaging will not work"
  fi
  cd "$REPO_DIR"
else
  echo "  claude-peers broker already running"
fi

# Add MCP config for RAG if it exists
if [ -f "$MCP_CONFIG" ]; then
  CLAUDE_FLAGS="$CLAUDE_FLAGS --mcp-config $MCP_CONFIG"
fi

# Department order (CEO is separate, launched first)
declare -a DEPT_ORDER=(frontend backend devops content mcp)
declare -A MODELS=(
  [ceo]="opus"
  [frontend]="sonnet"
  [backend]="sonnet"
  [devops]="haiku"
  [content]="sonnet"
  [mcp]="sonnet"
)
declare -A LABELS=(
  [ceo]="CEO"
  [frontend]="FRONTEND"
  [backend]="BACKEND"
  [devops]="DEVOPS"
  [content]="CONTENT"
  [mcp]="MCP"
)

# If specific departments are requested, skip CEO
LAUNCH_CEO=true
if [ $# -gt 0 ]; then
  DEPT_ORDER=("$@")
  LAUNCH_CEO=false
fi

# Kill existing session if running
tmux kill-session -t "$SESSION" 2>/dev/null || true

echo ""
echo "  IndieStack Orchestra — Dynamic Model Architecture"
echo "  =================================================="
echo ""

FIRST=true

# Launch CEO first (unless specific departments requested)
if [ "$LAUNCH_CEO" = true ]; then
  ceo_cmd="cd $REPO_DIR && claude $CLAUDE_FLAGS --model opus"

  tmux new-session -d -s "$SESSION" -n "ceo" "$ceo_cmd"
  FIRST=false
  echo "  CEO (opus) — strategic brain + S&QA gate"
fi

# Launch departments
for dept in "${DEPT_ORDER[@]}"; do
  model="${MODELS[$dept]}"
  label="${LABELS[$dept]}"

  if [ -z "$model" ]; then
    echo "  Unknown department: $dept — skipping"
    continue
  fi

  cmd="cd $REPO_DIR && claude $CLAUDE_FLAGS --model $model"

  if [ "$FIRST" = true ]; then
    tmux new-session -d -s "$SESSION" -n "$dept" "$cmd"
    FIRST=false
  else
    tmux new-window -t "$SESSION" -n "$dept" "$cmd"
  fi

  echo "  ${label} (${model})"
done

echo ""
echo "  Launched in tmux session: orchestra"
echo "  Attach:  tmux attach -t orchestra"
echo "  Switch:  Ctrl+B then window number"
echo "  Detach:  Ctrl+B then D"
echo ""

# Wait for the dev-channels dialog and confirm it — detect rather than guess timing
confirm_dialog() {
  local target="$1"
  local max_wait=30
  local elapsed=0
  while [ $elapsed -lt $max_wait ]; do
    if tmux capture-pane -t "$target" -p 2>/dev/null | grep -q "Enter to confirm"; then
      tmux send-keys -t "$target" "Enter" 2>/dev/null
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  # Dialog never appeared — send Enter anyway as fallback
  tmux send-keys -t "$target" "Enter" 2>/dev/null
}

echo "  Waiting for dev-channels dialogs..."
if [ "$LAUNCH_CEO" = true ]; then
  confirm_dialog "$SESSION:ceo" &
fi
for dept in "${DEPT_ORDER[@]}"; do
  confirm_dialog "$SESSION:$dept" &
done
wait
echo "  All dialogs confirmed."

echo "  Waiting 5 more seconds for agents to load..."
sleep 5

# Send CEO init prompt
if [ "$LAUNCH_CEO" = true ]; then
  ceo_init=$(cat "$REPO_DIR/.orchestra/ceo/init-prompt.md")
  tmux send-keys -t "$SESSION:ceo" "$ceo_init" Enter
  echo "  Sent init prompt to CEO"
  sleep 2
fi

# Send department init prompts
for dept in "${DEPT_ORDER[@]}"; do
  init_file="$REPO_DIR/.orchestra/departments/$dept/init-prompt.md"
  if [ -f "$init_file" ]; then
    init_content=$(cat "$init_file")
    tmux send-keys -t "$SESSION:$dept" "$init_content" Enter
    echo "  Sent init prompt to $dept"
    sleep 2
  fi
done

echo ""
echo "  All agents initialized. Manager (you) runs separately."
echo "  Attach with: tmux attach -t orchestra"
