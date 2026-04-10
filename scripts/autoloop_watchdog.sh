#!/bin/bash
# Autoloop watchdog — monitors the autoloop tmux session and restarts if dead
#
# Checks every 5 minutes:
#   1. Is the tmux session 'autoloop' alive?
#   2. Is the heartbeat file fresh (updated within last 2 hours)?
#
# If either check fails, restarts the autoloop (capped at 5 restarts/day).
#
# Launch: tmux new-session -d -s watchdog 'bash scripts/autoloop_watchdog.sh'
# Or:     nohup bash scripts/autoloop_watchdog.sh &

REPO_DIR="$HOME/indiestack"
HEARTBEAT_FILE="$REPO_DIR/.orchestra/autoloop-heartbeat"
STATE_FILE="$REPO_DIR/.orchestra/watchdog-state"
TELEGRAM="$HOME/.claude/telegram.sh"
LOG_DIR="$REPO_DIR/.orchestra/logs"

CHECK_INTERVAL=300          # 5 minutes
HEARTBEAT_MAX_AGE=7200      # 2 hours — stale if older
MAX_RESTARTS_PER_DAY=5
TMUX_SESSION="autoloop"

mkdir -p "$LOG_DIR"

log() {
    local level="$1"
    shift
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local logfile="$LOG_DIR/watchdog-$(date +%Y-%m-%d).log"
    echo "[$timestamp] [$level] $*" | tee -a "$logfile"
}

alert() {
    if [ -f "$TELEGRAM" ]; then
        bash "$TELEGRAM" "$1" 2>/dev/null
    fi
}

# Read today's restart count from state file
get_restart_count() {
    local today
    today=$(date +%Y-%m-%d)
    if [ -f "$STATE_FILE" ]; then
        local stored_date count
        stored_date=$(head -1 "$STATE_FILE" 2>/dev/null)
        count=$(tail -1 "$STATE_FILE" 2>/dev/null)
        if [ "$stored_date" = "$today" ]; then
            echo "${count:-0}"
            return
        fi
    fi
    echo "0"
}

# Increment today's restart count
increment_restart_count() {
    local today
    today=$(date +%Y-%m-%d)
    local current
    current=$(get_restart_count)
    local new_count=$((current + 1))
    echo "$today" > "$STATE_FILE"
    echo "$new_count" >> "$STATE_FILE"
    echo "$new_count"
}

# Check if tmux session is running
is_session_alive() {
    tmux has-session -t "$TMUX_SESSION" 2>/dev/null
}

# Check if heartbeat is fresh
is_heartbeat_fresh() {
    if [ ! -f "$HEARTBEAT_FILE" ]; then
        return 1
    fi
    local now hb_mtime age
    now=$(date +%s)
    hb_mtime=$(stat -c %Y "$HEARTBEAT_FILE" 2>/dev/null || echo 0)
    age=$((now - hb_mtime))
    [ "$age" -lt "$HEARTBEAT_MAX_AGE" ]
}

# Restart the autoloop
restart_autoloop() {
    local reason="$1"
    local count
    count=$(get_restart_count)

    if [ "$count" -ge "$MAX_RESTARTS_PER_DAY" ]; then
        log "ERROR" "Restart limit reached ($MAX_RESTARTS_PER_DAY/day). Not restarting. Reason: $reason"
        alert "[Watchdog] Autoloop down but restart limit reached ($MAX_RESTARTS_PER_DAY/day). Reason: $reason. Manual intervention needed."
        return 1
    fi

    # Kill stale session if it exists but is unresponsive
    tmux kill-session -t "$TMUX_SESSION" 2>/dev/null

    log "INFO" "Restarting autoloop. Reason: $reason"
    tmux new-session -d -s "$TMUX_SESSION" "bash $REPO_DIR/scripts/autonomous_loop.sh"

    local new_count
    new_count=$(increment_restart_count)
    log "INFO" "Autoloop restarted (restart $new_count/$MAX_RESTARTS_PER_DAY today)"
    alert "[Watchdog] Restarted autoloop ($new_count/$MAX_RESTARTS_PER_DAY today). Reason: $reason"
}

# Main watchdog loop
log "INFO" "Watchdog starting (PID $$, check every ${CHECK_INTERVAL}s)"

while true; do
    if ! is_session_alive; then
        log "WARN" "Tmux session '$TMUX_SESSION' not found"
        restart_autoloop "tmux session dead"
    elif ! is_heartbeat_fresh; then
        log "WARN" "Heartbeat stale (>$((HEARTBEAT_MAX_AGE / 3600))h old)"
        restart_autoloop "heartbeat stale"
    else
        log "DEBUG" "Autoloop healthy"
    fi

    sleep "$CHECK_INTERVAL"
done
