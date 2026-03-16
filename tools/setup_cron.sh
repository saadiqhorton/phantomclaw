#!/usr/bin/env bash
# Installs the cron job for the daily TLDR digest at 8:00 AM (system timezone).
# Safe to run multiple times — it removes any existing TLDR digest entry first.

set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"
TLDR_CRON="0 8 * * * cd $DIR && /usr/bin/python3 tools/tldr/daily_tldr_digest.py >> .tmp/tldr_cron.log 2>&1"
SENTINEL_CRON="0 17 * * 5 cd $DIR && /usr/bin/python3 tools/repo_sentinel.py $DIR >> .tmp/sentinel_cron.log 2>&1"

# Remove any existing entries, then add the new ones
(crontab -l 2>/dev/null | grep -v "daily_tldr_digest" | grep -v "repo_sentinel" ; echo "$TLDR_CRON"; echo "$SENTINEL_CRON") | crontab -

echo "✅ Cron jobs installed:"
echo "   $TLDR_CRON"
echo "   $SENTINEL_CRON"
echo ""
echo "Current crontab:"
crontab -l
