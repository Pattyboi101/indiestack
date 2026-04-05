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

# Wait for agents to start, then confirm the dev-channels dialog for all windows
echo "  Waiting 8 seconds for agents to start..."
sleep 8

# Confirm --dangerously-load-development-channels dialog (option 1 is pre-selected, just hit Enter)
echo "  Confirming dev-channels dialog..."
if [ "$LAUNCH_CEO" = true ]; then
  tmux send-keys -t "$SESSION:ceo" "Enter"
  sleep 0.5
fi
for dept in "${DEPT_ORDER[@]}"; do
  tmux send-keys -t "$SESSION:$dept" "Enter"
  sleep 0.5
done

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
