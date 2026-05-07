---
name: gold-report
description: Create, update, and monitor daily gold price reports using NVIDIA AI for analysis. Automatically checks for analysis validity and only sends Telegram notifications when the report is not satisfactory, stopping when it is complete and accurate.
---

# Gold Report Skill

This skill automates the process of generating daily gold price reports, including data collection from various sources (SJC Can Tho, Kitco, Vietcombank), analysis using NVIDIA AI, saving to OneDrive, and sending summary notifications via Telegram.

## Usage:

To initiate or update the gold report, simply ask Jarvis to "generate gold report" or "update gold prices".

## Monitoring:

This skill includes a monitoring mechanism that runs every 10 minutes to check the validity of the generated report. It will send a Telegram notification only if the AI analysis is missing or indicates an error, and will stop sending notifications once a valid report is successfully generated.

## Scripts:

- `scripts/gold_report.py`: The main Python script for data collection, AI analysis, saving, and sending Telegram notifications.
- `scripts/gold_config.py`: Configuration file for API keys and paths.
- `scripts/run_and_check_gold_report.sh`: A shell script to execute `gold_report.py`, read its output, check for analysis validity, and conditionally send Telegram notifications.