# Hermes Guild — Install (v1.2)

Instantiates the [Guild Charter v1.2](CHARTER.md) as a working Hermes
setup: 21 profiles, a Kanban board, a Ledger, and resident cron jobs.

## What you get

| Piece | Location | Purpose |
|---|---|---|
| 16 class profiles | `~/.hermes/profiles/<class>/SOUL.md` | Role profiles, activated on demand |
| 4 sub-whip profiles | `~/.hermes/profiles/<warden\|master-of-works\|steward\|captain>/` | Coordinators |
| 1 SotG profile | `~/.hermes/profiles/sotg/` | Single coordinator above the groups |
| Kanban board | `~/guild/board/kanban.md` | One board, four swimlanes, one owner per card |
| Ledger DB & CLI | `~/guild/ledger/guild.sqlite` & `record.py` | Use / calls / tokens / effectiveness |
| Resident cron jobs | `cron/jobs.sh` | The 8 durable watches |

## Install

```bash
cd hermes-guild
chmod +x install.sh
./install.sh
```

The installer:

1. Creates the 21 profiles (`hermes profile create <name>`).
2. Copies each `souls/<name>.md` into the profile's `SOUL.md`.
3. Writes `config/delegation.yaml` (flat delegation by default).
4. Creates `~/guild/` with the board, initialized SQLite ledger, and `record.py` CLI helper.
5. Points you at `cron/jobs.sh` for the resident jobs.

## After install

```bash
# Flat delegation (the charter's default — no nested spawn trees)
hermes config set delegation.max_spawn_depth 1

# Register resident cron jobs (interactive)
hermes cron create

# Commit the board + ledger so they survive a chat
cd ~/guild && git add -A && git commit -m "guild board + ledger"
```

## How to run the guild

Wake profiles on demand, not all 21 at once. A routine page update is
Druid + Bard + Wizard — not the whole guild.

```bash
hermes --profile sotg        # the coordinator; give it intent, get one status back
hermes --profile warrior --name "[KEEP-101] ADB tune"  # tag session with card ID
```

Routing: `You → SotG → sub-whip → class owner → leaf subagents`. The first
three arrows are accountability, not nested `delegate_task` calls. Keep
`max_spawn_depth: 1` unless a SotG-approved cross-group mission (severity-1
incident) needs one orchestrator layer.

### Recording to the Ledger

Use `ledger/record.py` to add cards, track spend, and check the guild pulse:

```bash
# Add or update a card
python3 ledger/record.py add-card --id KEEP-101 --title "ADB pooling tune" --swimlane keep --owner warrior --column doing

# Log session token and cost attribution
python3 ledger/record.py log-session --card KEEP-101 --group keep --class warrior --tokens-in 1200 --tokens-out 450 --cost-provider 0.015

# View the Guild Pulse table
python3 ledger/record.py pulse
```

## Tuning

- Edit `souls/<name>.md`, then re-run `./install.sh` to push changes into profiles.
- Bump `delegation.max_spawn_depth` to 2-3 only for approved incident patterns.
- Swap the markdown board for GitHub Issues + labels if you prefer (see charter §13.7).
