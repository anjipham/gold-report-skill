#!/bin/bash

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
STATUS_FILE="${SCRIPT_DIR}/../gold_report_status.json"

# Read config values
TELEGRAM_BOT_TOKEN=$(grep "TELEGRAM_BOT_TOKEN" "${SCRIPT_DIR}/gold_config.py" | cut -d'"' -f2)
TELEGRAM_CHAT_ID=$(grep "TELEGRAM_CHAT_ID" "${SCRIPT_DIR}/gold_config.py" | cut -d'"' -f2)

# Function to send Telegram message
send_telegram_message() {
    local message="$1"
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=${message}" \
            -d "parse_mode=Markdown"
    fi
}

# Get current date and approximate report slot (7AM or 11AM UTC)
TODAY_DATE=$(date +%Y-%m-%d)
CURRENT_HOUR_UTC=$(date -u +%H)
if [ "$CURRENT_HOUR_UTC" -lt 9 ]; then # Before 9:00 UTC for 7AM slot
    REPORT_SLOT="7AM"
elif [ "$CURRENT_HOUR_UTC" -lt 13 ]; then # Before 13:00 UTC for 11AM slot
    REPORT_SLOT="11AM"
else
    # If outside these slots, we don't need to monitor an active report, 
    # but we still need to reset for the next day if it's a new day.
    # For simplicity, we'll only monitor during active slots for now.
    # A more complex cron job could reset status at midnight.
    exit 0
fi

# Read current status
STATUS_JSON_CONTENT=$(cat "$STATUS_FILE" 2>/dev/null || echo '{}')
STATUS_OK=$(echo "$STATUS_JSON_CONTENT" | jq -r ".\"$TODAY_DATE\".\"$REPORT_SLOT\".status == \"OK\"" 2>/dev/null)
LAST_NOTIFIED_NOT_OK=$(echo "$STATUS_JSON_CONTENT" | jq -r ".\"$TODAY_DATE\".\"$REPORT_SLOT\".last_notified_not_ok" 2>/dev/null)

# Check if the report for this slot is already OK
if [ "$STATUS_OK" = "true" ]; then
    echo "Report for ${REPORT_SLOT} on ${TODAY_DATE} is OK. Stopping monitoring for this slot."
    exit 0
fi

echo "Report for ${REPORT_SLOT} on ${TODAY_DATE} is NOT OK or status not found. Running gold_report.py..."

# Run the main gold report script
"${SCRIPT_DIR}/gold_report.py"

# Re-read status after running the main script
STATUS_JSON_CONTENT=$(cat "$STATUS_FILE" 2>/dev/null || echo '{}')
STATUS_OK_AFTER_RUN=$(echo "$STATUS_JSON_CONTENT" | jq -r ".\"$TODAY_DATE\".\"$REPORT_SLOT\".status == \"OK\"" 2>/dev/null)

if [ "$STATUS_OK_AFTER_RUN" = "true" ]; then
    send_telegram_message "🎉 *Báo cáo vàng cho ${REPORT_SLOT} ngày ${TODAY_DATE} đã OK!*\nAnh có thể xem chi tiết trong file đính kèm nhé!"
    # Clear last_notified_not_ok if it's now OK
    jq ".\"$TODAY_DATE\".\"$REPORT_SLOT\".last_notified_not_ok = null" "$STATUS_FILE" > "${STATUS_FILE}.tmp" && mv "${STATUS_FILE}.tmp" "$STATUS_FILE"
    echo "Report for ${REPORT_SLOT} on ${TODAY_DATE} is now OK. Monitoring stopped."
else
    # If it's still NOT_OK and we haven't notified recently (e.g., last 10 mins)
    # For simplicity, we'll always notify if NOT_OK to ensure anh gets updates on persistent issues
    send_telegram_message "⚠️ *Báo cáo vàng cho ${REPORT_SLOT} ngày ${TODAY_DATE} vẫn chưa OK!*\nEm đang cố gắng khắc phục. Anh chờ em một chút nhé!"
    # Update last_notified_not_ok timestamp
    jq ".\"$TODAY_DATE\".\"$REPORT_SLOT\".last_notified_not_ok = \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"" "$STATUS_FILE" > "${STATUS_FILE}.tmp" && mv "${STATUS_FILE}.tmp" "$STATUS_FILE"
    echo "Report for ${REPORT_SLOT} on ${TODAY_DATE} is still NOT OK. Continuing monitoring."
fi
