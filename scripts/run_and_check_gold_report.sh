#!/bin/bash

# Run the gold report script
/home/ubuntu/gold_bot_venv/bin/python3 /home/ubuntu/.openclaw/workspace/skills/gold-report/scripts/gold_report.py

# Read the latest report content
REPORT_PATH="/home/ubuntu/onedrive_data/Gold_Reports/$(date +%Y-%m-%d).md"
REPORT_CONTENT=$(cat "$REPORT_PATH")

# Extract the analysis part
ANALYSIS_START=$(echo "$REPORT_CONTENT" | grep -n "## 🧠 Phân tích & Dự báo từ NVIDIA AI:" | cut -d: -f1)
if [ -n "$ANALYSIS_START" ]; then
    ANALYSIS_CONTENT=$(echo "$REPORT_CONTENT" | tail -n +$((ANALYSIS_START + 1)))
    # Limit to 1000 characters for summary
    SUMMARY_TEXT=$(echo "$ANALYSIS_CONTENT" | head -c 1000)
else
    SUMMARY_TEXT="Hệ thống đang thu thập dữ liệu hoặc AI đang bận. Anh hãy xem chi tiết trong file đính kèm nhé!"
fi

# Send a check message to Telegram (using the same bot token and chat ID from gold_config.py)
# Read config values
TELEGRAM_BOT_TOKEN=$(grep "TELEGRAM_BOT_TOKEN" /home/ubuntu/.openclaw/workspace/skills/gold-report/scripts/gold_config.py | cut -d'"' -f2)
TELEGRAM_CHAT_ID=$(grep "TELEGRAM_CHAT_ID" /home/ubuntu/.openclaw/workspace/skills/gold-report/scripts/gold_config.py | cut -d'"' -f2)

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    MESSAGE="🔔 *Kiểm tra báo cáo vàng tự động: (Output từ script)*\n\n${SUMMARY_TEXT}...\n\n📄 Chi tiết tại: ${REPORT_PATH}"
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "text=${MESSAGE}" \
        -d "parse_mode=Markdown"
fi
