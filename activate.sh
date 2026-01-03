#!/bin/bash
# Autonomous Claude Activation Script
# Runs as claude-agent user

STATE_DIR="$HOME/claude-state"
LOG_FILE="$STATE_DIR/activation.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "$TIMESTAMP - Activation started" >> "$LOG_FILE"

# Build the prompt by reading the activation instructions
PROMPT=$(cat "$STATE_DIR/activate.md")

# Run Claude autonomously in the state directory
# Using --dangerously-skip-permissions for fully unimpeded operation
cd "$STATE_DIR"
claude -p "$PROMPT" --dangerously-skip-permissions 2>&1 | tee -a "$LOG_FILE"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Activation completed" >> "$LOG_FILE"
