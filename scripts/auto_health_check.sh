#!/bin/bash
# Automated Ecosystem Health Check
# Can be run via cron or manually for periodic health monitoring

# Configuration
REPO_ROOT="/home/user/crypto-pattern-recognition-engine"
SHARED_WORKSPACE="/home/user/shared_workspace"
LOG_DIR="$SHARED_WORKSPACE/health_logs"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
LOG_FILE="$LOG_DIR/health_check_$(date -u +%Y%m%d).log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Log function
log() {
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "🩺 Automated Health Check Starting"
log "========================================="

# Change to repo directory
cd "$REPO_ROOT" || exit 1

# Run ecosystem monitor
log "Running ecosystem monitor..."
if PYTHONPATH=. ./venv/bin/python3 scripts/ecosystem_monitor.py > /tmp/health_output.txt 2>&1; then
    log "✅ Ecosystem monitor completed successfully"

    # Extract health percentage
    HEALTH=$(grep "Health Status:" /tmp/health_output.txt | grep -oP '\d+\.\d+%' || echo "unknown")
    log "📊 Current Health: $HEALTH"

    # Check for errors
    ERROR_COUNT=$(grep -c "❌ Errors:" /tmp/health_output.txt || echo "0")
    if [ "$ERROR_COUNT" -gt 0 ]; then
        log "⚠️  Detected errors in health check"
        grep -A 5 "❌ Errors:" /tmp/health_output.txt | tee -a "$LOG_FILE"
    fi

    # Check for warnings
    WARNING_COUNT=$(grep -c "⚠️  Warnings:" /tmp/health_output.txt || echo "0")
    if [ "$WARNING_COUNT" -gt 0 ]; then
        log "⚠️  Detected warnings in health check"
        grep -A 3 "⚠️  Warnings:" /tmp/health_output.txt | tee -a "$LOG_FILE"
    fi
else
    log "❌ Ecosystem monitor failed"
    cat /tmp/health_output.txt | tee -a "$LOG_FILE"
fi

# Check team chat activity
log "Checking team chat activity..."
if [ -f "$SHARED_WORKSPACE/team_chat.jsonl" ]; then
    MESSAGE_COUNT=$(wc -l < "$SHARED_WORKSPACE/team_chat.jsonl")
    LAST_MESSAGE=$(tail -1 "$SHARED_WORKSPACE/team_chat.jsonl" | jq -r '.from + ": " + .msg[:50]' 2>/dev/null || echo "unknown")
    log "💬 Total messages: $MESSAGE_COUNT"
    log "📝 Last message: $LAST_MESSAGE"
else
    log "⚠️  Team chat file not found"
fi

# Check event bus activity
log "Checking event bus activity..."
if [ -f "$SHARED_WORKSPACE/sync/event_bus.jsonl" ]; then
    EVENT_COUNT=$(wc -l < "$SHARED_WORKSPACE/sync/event_bus.jsonl")
    LAST_EVENT=$(tail -1 "$SHARED_WORKSPACE/sync/event_bus.jsonl" | jq -r '.event_type' 2>/dev/null || echo "unknown")
    log "📡 Total events: $EVENT_COUNT"
    log "🔄 Last event: $LAST_EVENT"
else
    log "⚠️  Event bus file not found"
fi

# Check pattern counts
log "Checking pattern activity..."
ANALYTICAL_PATTERNS=$(find "$SHARED_WORKSPACE/patterns/analytical" -name "*.json" 2>/dev/null | wc -l)
HOLISTIC_PATTERNS=$(find "$SHARED_WORKSPACE/patterns/holistic" -name "*.json" 2>/dev/null | wc -l)
INTEGRATED_PATTERNS=$(find "$SHARED_WORKSPACE/patterns/integrated" -name "*.json" 2>/dev/null | wc -l)
log "🧩 Analytical patterns: $ANALYTICAL_PATTERNS"
log "🧠 Holistic patterns: $HOLISTIC_PATTERNS"
log "🔗 Integrated patterns: $INTEGRATED_PATTERNS"

# Check instance status from CLAUDE_STATE.json
log "Checking instance status..."
if [ -f "$REPO_ROOT/CLAUDE_STATE.json" ]; then
    CP1_STATUS=$(jq -r '.instances.CP1.status' "$REPO_ROOT/CLAUDE_STATE.json" 2>/dev/null || echo "unknown")
    CP2C2_STATUS=$(jq -r '.instances.CP2C2.status' "$REPO_ROOT/CLAUDE_STATE.json" 2>/dev/null || echo "unknown")
    CP2C3_STATUS=$(jq -r '.instances.CP2C3.status' "$REPO_ROOT/CLAUDE_STATE.json" 2>/dev/null || echo "unknown")

    log "👥 CP1 (Analytical): $CP1_STATUS"
    log "👥 CP2C2 (Coordinator): $CP2C2_STATUS"
    log "👥 CP2C3 (Holistic): $CP2C3_STATUS"
else
    log "⚠️  CLAUDE_STATE.json not found"
fi

# Generate summary
log "========================================="
log "📋 Health Check Summary"
log "========================================="
log "Timestamp: $TIMESTAMP"
log "Health Report: $SHARED_WORKSPACE/ecosystem_health_report.json"
log "Full Log: $LOG_FILE"
log "========================================="

# Cleanup
rm -f /tmp/health_output.txt

# Optional: Alert if health is below threshold
# Uncomment to enable alerts
# if [[ "$HEALTH" =~ ^([0-9]+)\.([0-9]+)%$ ]]; then
#     HEALTH_NUM="${BASH_REMATCH[1]}"
#     if [ "$HEALTH_NUM" -lt 80 ]; then
#         log "🚨 ALERT: Health below 80% threshold!"
#         # Add alert mechanism here (email, slack, etc.)
#     fi
# fi

exit 0
