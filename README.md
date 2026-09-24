# Hermes Guild — Install (v1.2)

Instantiates the [Guild Charter v1.2](../HERMES_GUILD-1-1.md) as a working Hermes
setup: 21 profiles, a Kanban board, a Ledger, and resident cron jobs.

## What you get

| Piece | Location | Purpose |
|---|---|---|
| 16 class profiles | `~/.hermes/profiles/<class>/SOUL.md` | Role profiles, activated on demand |
| 4 sub-whip profiles | `~/.hermes/profiles/<warden\|master-of-works\|steward\|captain>/` | Coordinators |
| 1 SotG profile | `~/.hermes/profiles/sotg/` | Single coordinator above the groups |
| Kanban board | `~/guild/board/kanban.md` | One board, four swimlanes, one owner per card |
| Ledger | `~/guild/ledger/guild.sqlite` | Use / calls / tokens / effectiveness |
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
4. Creates `~/guild/` with the board and an initialized SQLite ledger.
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
hermes --profile warrior     # a class owner; delegate leaf subagents from here
```

Routing: `You → SotG → sub-whip → class owner → leaf subagents`. The first
three arrows are accountability, not nested `delegate_task` calls. Keep
`max_spawn_depth: 1` unless a SotG-approved cross-group mission (severity-1
incident) needs one orchestrator layer.

## Tuning

- Edit `souls/<name>.md`, then re-run `./install.sh` to push changes into profiles.
- Bump `delegation.max_spawn_depth` to 2-3 only for approved incident patterns.
- Swap the markdown board for GitHub Issues + labels if you prefer (see charter §13.7).
