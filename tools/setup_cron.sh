#!/usr/bin/env bash
# Installs the cron job for the daily TLDR digest at 8:00 AM (system timezone).
# Safe to run multiple times — it removes any existing TLDR digest entry first.

set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"
CRON_CMD="0 8 * * * cd $DIR && /usr/bin/python3 tools/daily_tldr_digest.py >> .tmp/tldr_cron.log 2>&1"

# Remove any existing TLDR digest entries, then add the new one
(crontab -l 2>/dev/null | grep -v "daily_tldr_digest" ; echo "$CRON_CMD") | crontab -

echo "✅ Cron job installed:"
echo "   $CRON_CMD"
echo ""
echo "Current crontab:"
crontab -l
