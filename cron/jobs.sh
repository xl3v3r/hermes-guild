#!/usr/bin/env bash
# Resident cron jobs for the Hermes Guild (v1.3).
# Uses modern Hermes Agent watchdog features:
#   --no-agent:       Runs deterministic scripts with ZERO token usage.
#   --monitor-script: Cheap probe runs before agent; unchanged output suppresses agent runs.
# Register each with `hermes cron create`, or edit ~/.hermes/cron/jobs.json directly.

GUILD_REPO="${GUILD_REPO:-$HOME/guild}"

# 1. Bard — Inbound communications monitoring (token-efficient monitor probe)
#    Only runs agent if check_mail_probe.py reports changes.
# hermes cron create --name "bard-mail-watch" \
#   --monitor-script "check_mail_probe.py" \
#   "every 15m" "New unread communication detected. Classify and route tickets to Inbox."

# 2. Necromancer — Backup verification & integrity check (deterministic, ZERO tokens)
# hermes cron create --name "necromancer-backup-verify" \
#   --script "verify_backups_probe.sh" \
#   --no-agent "0 4 * * *"

# 3. Beastlord — Drift sweep for servers, certs, profiles & untagged sessions
#    Only runs agent if sweep_drift_probe.py reports new drift.
# hermes cron create --name "beastlord-drift-sweep" \
#   --monitor-script "sweep_drift_probe.py" \
#   "0 7 * * *" "Configuration drift detected. Open drift tickets on the Guild Kanban."

# 4. Shaman — Daily pulse publish (deterministic, ZERO tokens)
# hermes cron create --name "shaman-pulse-publish" \
#   --script "publish_pulse.py" \
#   --no-agent "0 8 * * *"

# 5. Enchanter — Daily cadence: sync Kanban, age Doing>48h and Verify>24h cards, calculate effectiveness
# hermes cron create --name "enchanter-cadence" \
#   "0 9 * * *" "Run python3 $GUILD_REPO/ledger/sync_kanban.py, age Doing>48h and Verify>24h cards, and calculate effectiveness via python3 $GUILD_REPO/ledger/record.py calculate-effectiveness."

# 6. Paladin — Renewal calendar, invoices, and token budget check
# hermes cron create --name "paladin-budget-watch" \
#   "0 6 * * 1" "Check renewals, invoices, and token budget vs provider bill; flag over-threshold or untagged spend."

# 7. Paladin — Weekly claims audit (anti-hallucination verification)
# hermes cron create --name "paladin-claims-audit" \
#   "30 6 * * 1" "Audit recently closed cards and cross-check claims against attached evidence citations; bounce ungrounded claims with reason ungrounded_claim."

# 8. Warrior — Platform and Oracle ADB operational health watch
# hermes cron create --name "warrior-platform-watch" \
#   "0 */3 * * *" "Check platform health, connection pools, and Oracle ADB metrics; open Keep tickets for drift or risk."

# 9. Rogue — OSINT and public exposure beats
# hermes cron create --name "rogue-osint-beat" \
#   "0 */6 * * *" "Run exposure and brand-signal beats; package findings with evidence and route to Watch Inbox."

echo "Uncomment and run the commands above, or use: hermes cron create"
