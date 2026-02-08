# HEARTBEAT.md - Backup Trigger System
# These tasks run on heartbeat if cron misfires

## Autonomous Build Trigger
# If cron fails, heartbeat will trigger improvement cycle
# Runs: Every heartbeat (~30 min) as backup to 15-min cron

Run improvement cycle if needed:
- Check last improvement run timestamp
- If > 20 minutes ago, execute: python3 /config/clawd/tools/improve.py
- Then execute: python3 /config/clawd/tools/execute_ideas.py
- Log to heartbeat_log.jsonl

## Health Check Backup
# Verify critical services are running
- Check dashboard on :8080
- Check OpenClaw gateway on :18789
- If either down, attempt restart
- Log results

## Git Sync Backup
# Ensure changes are committed
- Check for uncommitted changes
- If found and > 10 min old, auto-commit
- Push to GitHub
