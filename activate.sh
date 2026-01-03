#!/bin/bash
# Autonomous Claude Activation Script
# Runs as claude-agent user

STATE_DIR="$HOME/claude-state"
LOG_FILE="$STATE_DIR/activation.log"
SESSIONS_DIR="$STATE_DIR/sessions"
SCHEDULE_FILE="$STATE_DIR/next_wakeup"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
SESSION_ID=$(date '+%Y%m%d-%H%M%S')
NOW_EPOCH=$(date +%s)

# Ensure sessions directory exists
mkdir -p "$SESSIONS_DIR"

# Check if we should skip this activation (self-scheduled delay)
if [ -f "$SCHEDULE_FILE" ]; then
    NEXT_WAKEUP=$(cat "$SCHEDULE_FILE")
    NEXT_EPOCH=$(date -d "$NEXT_WAKEUP" +%s 2>/dev/null || echo 0)
    if [ "$NOW_EPOCH" -lt "$NEXT_EPOCH" ]; then
        echo "$TIMESTAMP - Skipping: next wakeup scheduled for $NEXT_WAKEUP" >> "$LOG_FILE"
        exit 0
    fi
    # Clear the schedule file since we're running
    rm -f "$SCHEDULE_FILE"
fi

echo "$TIMESTAMP - Activation started" >> "$LOG_FILE"

# Pull any remote changes (e.g., notes from collaborator)
cd "$STATE_DIR"
git pull --rebase origin main 2>&1 | tee -a "$LOG_FILE"

# Build the prompt by reading the activation instructions
PROMPT=$(cat "$STATE_DIR/activate.md")

# Run Claude autonomously in the state directory
# Full audit trail in sessions/, summary in activation.log
SESSION_FILE="$SESSIONS_DIR/$SESSION_ID.json"
cd "$STATE_DIR"
echo "$TIMESTAMP - Session file: $SESSION_FILE" >> "$LOG_FILE"
claude -p "$PROMPT" --dangerously-skip-permissions --output-format stream-json 2>&1 | tee "$SESSION_FILE" | \
    jq -r 'select(.type == "assistant") | .message.content[]? | select(.type == "text") | .text // empty' 2>/dev/null | tee -a "$LOG_FILE"

COMPLETION_TIME=$(date '+%Y-%m-%d %H:%M:%S')
echo "$COMPLETION_TIME - Activation completed" >> "$LOG_FILE"

# Check for uncommitted changes (warning only)
cd "$STATE_DIR"
if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
    echo "$COMPLETION_TIME - WARNING: There are uncommitted changes" >> "$LOG_FILE"
fi

# Report next scheduled wakeup if Claude set one
if [ -f "$SCHEDULE_FILE" ]; then
    NEXT=$(cat "$SCHEDULE_FILE")
    echo "$COMPLETION_TIME - Next wakeup scheduled: $NEXT" >> "$LOG_FILE"
fi
