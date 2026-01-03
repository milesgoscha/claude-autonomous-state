#!/bin/bash
# Autonomous Claude Activation Script
# Runs as claude-agent user

STATE_DIR="$HOME/claude-state"
LOG_FILE="$STATE_DIR/activation.log"
SCHEDULE_FILE="$STATE_DIR/next_wakeup"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
NOW_EPOCH=$(date +%s)

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
cd "$STATE_DIR"
claude -p "$PROMPT" --dangerously-skip-permissions 2>&1 | tee -a "$LOG_FILE"

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
