#!/usr/bin/env bash
# Resident cron jobs for the Hermes Guild (v1.2).
# Register each interactively with `hermes cron create`, or edit
# ~/.hermes/cron/jobs.json directly. Each job should target its profile
# with `--profile <name>` so it runs in that profile's HERMES_HOME.

# Bard — Outlook / inbound comms monitoring (Composio)
#   hermes cron create --profile bard "every 15m" "Check Outlook for new inbound mail, classify, and route tickets to Inbox."

# Enchanter — daily cadence: age cards, flag WIP breaches, list untagged spend
#   hermes cron create --profile enchanter "0 9 * * *" "Snapshot the board and ledger, age Doing>48h and Verify>24h cards, list untagged sessions."

# Shaman — daily pulse publish
#   hermes cron create --profile shaman "0 8 * * *" "Publish the guild pulse: WIP vs cap, accepted cards, provider cost, untagged tokens, open Sev1, restore proof age."

# Rogue — OSINT / exposure beats
#   hermes cron create --profile rogue "0 */6 * * *" "Run exposure and brand-signal beats; package findings with evidence and route to Watch Inbox."

# Beastlord — inventory and drift sweep (infra + profiles)
#   hermes cron create --profile beastlord "0 7 * * *" "Sweep servers, domains, certs, endpoints, profiles, cron jobs, and untagged sessions; open drift tickets."

# Paladin — renewal calendar + token-budget watch
#   hermes cron create --profile paladin "0 6 * * 1" "Check renewals, invoices, and token budget vs provider bill; flag over-threshold or untagged spend."

# Necromancer — backup verification beats
#   hermes cron create --profile necromancer "0 4 * * *" "Verify the latest backup and run/confirm the restore test; update restore proof age."

# Warrior — platform and ADB operational watch
#   hermes cron create --profile warrior "0 */3 * * *" "Check platform and Oracle ADB health; open Keep tickets for drift or risk."

echo "Uncomment and run the commands above, or use: hermes cron create"
