#!/bin/bash
# Launch Ed's Outreach Orchestra
# 4 agents: master + research + copy + tracking
#
# Usage:
#   .outreach/launch.sh

set -e

REPO_DIR="$HOME/indiestack"
SESSION="outreach"
CLAUDE_FLAGS="--dangerously-skip-permissions"

declare -a DEPT_ORDER=(master research copy tracking)
declare -A MODELS=(
  [master]="sonnet"
  [research]="sonnet"
  [copy]="sonnet"
  [tracking]="haiku"
)
declare -A LABELS=(
  [master]="ED-MASTER"
  [research]="RESEARCH"
  [copy]="COPY"
  [tracking]="TRACKING"
)

# Kill existing session if running
tmux kill-session -t "$SESSION" 2>/dev/null || true

echo "╔══════════════════════════════════════════╗"
echo "║   Ed's Outreach Orchestra — Launching    ║"
echo "╠══════════════════════════════════════════╣"

FIRST=true
for dept in "${DEPT_ORDER[@]}"; do
  model="${MODELS[$dept]}"
  label="${LABELS[$dept]}"

  cmd="cd $REPO_DIR && claude $CLAUDE_FLAGS --model $model"

  if [ "$FIRST" = true ]; then
    tmux new-session -d -s "$SESSION" -n "$dept" "$cmd"
    FIRST=false
  else
    tmux new-window -t "$SESSION" -n "$dept" "$cmd"
  fi

  echo "║  ✓ ${label} (${model})                       ║" | head -c 45
  echo "║"
done

echo "╠══════════════════════════════════════════╣"
echo "║  4 agents launched                       ║"
echo "║                                          ║"
echo "║  Attach:  tmux attach -t outreach        ║"
echo "║  Switch:  Ctrl+B then window number      ║"
echo "╚══════════════════════════════════════════╝"

# Auto-send init prompts
echo ""
echo "Waiting 8 seconds for agents to start..."
sleep 8

for dept in "${DEPT_ORDER[@]}"; do
  if [ "$dept" = "master" ]; then
    init_content=$(cat "$REPO_DIR/.outreach/master/init-prompt.md")
  else
    init_content=$(cat "$REPO_DIR/.outreach/departments/$dept/init-prompt.md")
  fi

  tmux send-keys -t "$SESSION:$dept" "$init_content" Enter
  echo "  ✓ Sent init prompt to $dept"
  sleep 2
done

echo ""
echo "All 4 agents initialized. Attach with: tmux attach -t outreach"
echo "Ed: switch to window 0 (master) and start chatting."
