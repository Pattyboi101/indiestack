#!/usr/bin/env bash
# PostToolUse hook: tracks large tool outputs for observation masking.
# Appends a timestamp entry to state.md so the CEO can reference outcomes
# without re-reading old tool outputs.
#
# Called by Claude Code after every tool use.
# Env vars provided by Claude Code: TOOL_NAME, TOOL_INPUT, TOOL_OUTPUT (if available)
#
# This hook is advisory — it doesn't block tool execution.
# Its purpose is to reinforce the observation masking pattern by maintaining
# an external log the CEO can reference instead of scrolling back.

STATE_FILE="$HOME/indiestack/.orchestra/ceo/state.md"
TIMESTAMP=$(date +"%H:%M")

# Only log for tools that produce large outputs
case "$TOOL_NAME" in
    Bash|Read|Grep|Glob|WebFetch|WebSearch)
        # Append a tool usage record to state.md
        # The CEO's CLAUDE.md instructs it to check state.md rather than
        # re-reading old outputs, completing the observation masking loop.
        echo "- [$TIMESTAMP] $TOOL_NAME executed" >> "$STATE_FILE"
        ;;
esac

exit 0
