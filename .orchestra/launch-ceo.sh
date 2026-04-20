#!/usr/bin/env bash
# CEO Agent Harness — Launcher
# Usage: ./launch-ceo.sh [optional initial prompt]
#
# Launches Claude Code with Opus 4.6 in the ~/indiestack/ directory
# with bypass permissions for autonomous operation.

set -euo pipefail

INDIESTACK_DIR="$HOME/indiestack"
STATE_FILE="$INDIESTACK_DIR/.orchestra/ceo/state.md"

# Reset state for new session
cat > "$STATE_FILE" << 'EOF'
# Session State
## Focus:
## Done:
## Decisions:
## Blocked:
## Next:
EOF

cd "$INDIESTACK_DIR"

if [ $# -gt 0 ]; then
    # One-shot mode with initial prompt
    exec claude \
        --model claude-opus-4-6 \
        --dangerously-skip-permissions \
        -p "$*"
else
    # Interactive mode
    exec claude \
        --model claude-opus-4-6 \
        --dangerously-skip-permissions
fi
