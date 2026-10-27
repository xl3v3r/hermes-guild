```text
               /\                                                                  /\
              /  \                                                                /  \
             | /\ |                          E V E R Q U E S T                   | /\ |
           /--/  \--\                                                          /--/  \--\
          |  [ EQ ]  |         _   _ _____ ____  __  __ _____ ____              |  [ EQ ]  |
           \--\  /--/         | | | | ____|  _ \|  \/  | ____/ ___|              \--\  /--/
             | \/ |           | |_| |  _| | |_) | |\/| |  _| \___ \                | \/ |
             /    \           |  _  | |___|  _ <| |  | | |___ ___) |               /    \
            /  /\  \          |_| |_|_____|_| \_\_|  |_|_____|____/               /  /\  \
           /  /  \  \                                                            /  /  \  \
          |  / /\ \  |         ____ _   _ ___ _     ____      _____ ___         |  / /\ \  |
          | | |  | | |        / ___| | | |_ _| |   |  _ \    | ____/ _ \        | | |  | | |
          | | |  | | |       | |  _| | | || || |   | | | |   |  _|| | | |       | | |  | | |
           \ \ \/ / /        | |_| | |_| || || |___| |_| |   | |__| |_| |        \ \ \/ / /
            \ \  / /          \____|\___/|___|_____|____/    |_____\__\_|         \ \  / /
             \/  \/                                                                 \/  \/
                                   ⚔️   O P E R A T I O N S   G U I L D  ⚔️
                                  ✦  KEEP • WORKS • STEWARD • WATCH  ✦
                                   ~ 21 ROLES • ZERO STANDING BLOAT ~
```

# Hermes Operations Guild (v1.3)

> **A role-and-accountability operating system for multi-agent autonomous engineering, platform operations, and governance.**

Instantiates the [Guild Charter v1.3](CHARTER.md) as a complete, ready-to-run Hermes deployment: **21 role profiles**, a unified **Kanban board**, an attribution-focused **SQLite Ledger**, and **8 resident cron watches**.

---

## Table of Contents

- [The Core Philosophy](#the-core-philosophy)
- [Command Tree & Groups](#command-tree--groups)
- [Load-Bearing Handoff Rules](#load-bearing-handoff-rules)
- [Resident Cron Watches vs. On-Demand Profiles](#resident-cron-watches-vs-on-demand-profiles)
- [What You Get](#what-you-get)
- [Installation & Quickstart](#installation--quickstart)
- [Operating the Guild](#operating-the-guild)
  - [Daily Routing Pattern](#daily-routing-pattern)
  - [Session-to-Card Tagging](#session-to-card-tagging)
- [Guild Kanban Board](#guild-kanban-board)
  - [Lifecycle Columns](#lifecycle-columns)
  - [WIP Limits & Fan-Out Prevention](#wip-limits--fan-out-prevention)
- [Guild Ledger & Telemetry](#guild-ledger--telemetry)
  - [Attribution Contract](#attribution-contract)
  - [Using `ledger/record.py`](#using-ledgerrecordpy)
- [Worked Scenarios](#worked-scenarios)
- [Tuning & Customization](#tuning--customization)

---

## The Core Philosophy

Most multi-agent architectures fail due to **agent sprawl**: they launch dozens of concurrent LLMs that converse in circular loops, burn thousands of dollars in tokens, and leave no clear single owner when production breaks.

**Hermes Guild takes the exact opposite approach:**
1. **Roles, Not Standing Swarms:** 21 defined profiles does **not** mean running 21 models at once. A typical operation wakes only **3 to 6 profiles** on demand.
2. **One Throat to Choke:** Every Kanban card has exactly **one owner class**. Assistants submit evidence; they do not co-own.
3. **Flat Delegation by Default (`max_spawn_depth: 1`):** The hierarchy represents accountability, blame, and review—**not** nested `delegate_task` calls.
4. **Durable Watches, Not Chatty Idle Agents:** Continuous monitoring (backups, certs, DB health, mail) runs in **cron**, not in expensive conversation contexts.
5. **Attribution, Not Invoices:** The Ledger tracks efficiency and outcome effectiveness (`first_pass_accept`, `rework_count`, `incident_spawned`), refusing to treat raw token burn as a measure of productivity.
6. **Grounded, Not Hallucinated:** Every Verify claim must trace to a tool result, file, URL, or DB row. Paladin audits high-stakes claims; Shaman reports `ungrounded_claims` so hallucination is measured, not guessed.

---

## Command Tree & Groups

```text
You (Guildmaster)
└── Speaker of the Guild (SotG) [Single coordinator to You]
    ├── Warden of the Keep — Infrastructure & Data
    │   ├── Warrior          (First Officer: hosting, DNS, Oracle ADB, prod change executor)
    │   ├── Beastlord        (Drift detection, asset/profile inventory)
    │   ├── Necromancer      (Backup design, restore verification & disaster recovery)
    │   └── Shaman           (Platform telemetry, Ledger metrics publisher)
    ├── Master of Works — Web & Experience
    │   ├── Wizard           (First Officer: web/app build, integration, releases)
    │   ├── Druid            (Visual systems, UX specs, accessibility)
    │   ├── Monk             (Page speed, client profiling, query optimization)
    │   └── Ranger           (Technical SEO, visibility, conversion analytics)
    ├── Steward of the Guild — Operations & Governance
    │   ├── Magician         (First Officer: mission composition, skill wiring)
    │   ├── Bard             (Inbound comms, Outlook monitoring, copywriting)
    │   ├── Enchanter        (Cron ops, cadence, Kanban aging, self-improvement)
    │   └── Paladin          (Budgets, spend halts, legal holds, compliance)
    └── Captain of the Watch — Security & Response
        ├── Rogue            (First Officer: OSINT officer, external intelligence)
        ├── Shadowknight     (Adversarial testing, secret scanning, attack-path audit)
        ├── Berserker        (Urgent incident containment, war-room commander)
        └── Cleric           (Doctor work: patching vulnerabilities & broken services)
```

### The Role of First Officers
**Warrior, Wizard, Magician, and Rogue** serve as First Officers for their respective groups:
- They handle intake and triage when their sub-whip is busy.
- **They are not a new management rank.**
- **They are not default doers** for every ticket in their swimlane; they only execute when named as the card owner.

---

## Load-Bearing Handoff Rules

The charter establishes firm guardrails across high-risk operational boundaries:

| Boundary | Rule | Accountability |
|---|---|---|
| **Ship vs. Host** | Works ships *into* Keep. Wizard packages code/releases; Warrior owns hosting truth, DNS, and Oracle ADB. | Releases needing DNS or schema are blocked until Keep accepts the change window. |
| **Who Restores** | Necromancer plans and proves restores; **Warrior presses the prod button**. | Prevents automated DR bots from accidentally executing destructive restores on production. |
| **Incident Command** | Rogue finds and frames threats; Captain declares severity; **Berserker commands containment**. | Rogue does not run the war room. Cleric remediates technical debt only after the incident is contained. |
| **Money & Law** | **Paladin can halt any spend or vendor action**. Attorney matters escalate to `SotG → You`. | Magician cannot overrule Paladin. The guild never invents an AI substitute for a licensed attorney. |
| **Drift is Actionable** | Beastlord’s asset/profile sweeps are not scrapbooks. | Material drift (expired cert, orphan domain, untagged session) must become a Kanban ticket. |
| **Telemetry Split** | Monk = "Is the app fast for users?"<br>Shaman = "Is the platform healthy and what was spent?"<br>Ranger = "Did the page get found and convert?" | Distinct questions with distinct ownership. No dumping Search Console into the financial Ledger. |

---

## Resident Cron Watches vs. On-Demand Profiles

Standing duties run as durable cron tasks defined in [`cron/jobs.sh`](cron/jobs.sh), keeping conversation contexts clean and cost minimal:

| Frequency | Profile | Duty / Watch |
|---|---|---|
| `every 15m` | **Bard** | Inbound communications & Outlook inbox sweep (via Composio). |
| `0 4 * * *` | **Necromancer** | Daily backup verification & restore test validation. |
| `0 6 * * 1` | **Paladin** | Weekly renewal calendar, invoice review, and token budget check. |
| `0 7 * * *` | **Beastlord** | Asset, server, cert, domain, and Hermes profile drift sweep. |
| `0 8 * * *` | **Shaman** | Daily Guild Ledger pulse compilation and platform health summary. |
| `0 9 * * *` | **Enchanter** | Daily cadence: aging cards (>48h Doing, >24h Verify) & untagged sessions. |
| `0 */3 * * *`| **Warrior** | Platform health, database connection pools, and Oracle ADB operational watch. |
| `0 */6 * * *`| **Rogue** | OSINT exposure checks, domain signals, and brand threat monitoring. |

All other work is **On-Demand**: profiles (Wizard, Druid, Monk, Cleric, Berserker, etc.) wake only when assigned an active card.

---

## What You Get

| Piece | Location | Purpose |
|---|---|---|
| **16 Class Profiles** | `~/.hermes/profiles/<class>/SOUL.md` | Single-responsibility role profiles, activated on demand with credentials. |
| **4 Sub-whip Profiles** | `~/.hermes/profiles/<warden\|master-of-works\|steward\|captain>/SOUL.md` | Group coordinators that assign owners and verify evidence. |
| **1 SotG Profile** | `~/.hermes/profiles/sotg/SOUL.md` | Speaker of the Guild: single interface between You and the groups. |
| **Native Kanban Board**| `~/.hermes/kanban/boards/guild/` | Native Hermes Agent SQLite task board and multi-agent coordination engine. |
| **Board Markdown Export**| `~/guild/board/kanban.md` | Exported markdown view for inspection, synced via `ledger/sync_kanban.py`. |
| **Guild Ledger** | `~/guild/ledger/guild.sqlite` | SQLite attribution database tracking use, calls, tokens, cost, and effectiveness. |
| **Ledger CLI Helper** | `~/guild/ledger/record.py` | CLI helper to add cards, sync state telemetry, log effectiveness, and view pulse. |
| **Telemetry Sync Hook**| `~/guild/ledger/sync_telemetry.py` | Automatic `on_session_end` hook ingesting tokens & cost from `state.db`. |
| **Kanban Synchronizer**| `~/guild/ledger/sync_kanban.py` | Bi-directional synchronizer between `kanban.db` and `board/kanban.md`. |
| **Watchdog Probes** | `~/guild/scripts/` | Lightweight deterministic scripts for backup verification, mail, and drift. |
| **Resident Cron Jobs**| `cron/jobs.sh` | Shell specifications for resident watches (`--no-agent` & `--monitor-script`). |

---

## Installation & Quickstart

### Prerequisites
- Linux / macOS host with `git` and `python3` (Python 3.8+).
- [Hermes Agent CLI](https://github.com/xl3v3r) installed (`hermes`).
- `sqlite3` CLI (optional; installer falls back automatically to Python 3).

### 1. Run the Installer
```bash
git clone https://github.com/xl3v3r/hermes-guild.git
cd hermes-guild
chmod +x install.sh
./install.sh
```

The installer will:
1. Initialize all 21 Hermes profiles with descriptions and cloned credentials (`hermes profile create <name> --clone --description "..."`).
2. Write individual `SOUL.md` role instructions into each profile directory.
3. Enable the `kanban` toolset across all profiles.
4. Initialize the native `guild` board (`hermes kanban boards create guild --name "Hermes Operations Guild"`).
5. Register the `on_session_end` telemetry hook in `~/.hermes/config.yaml`.
6. Write `config/delegation.yaml` configuring default flat delegation.
7. Provision `~/guild/` with the Kanban board, SQLite ledger schema, CLI tools, and probe scripts.

### 2. Configure Hermes Delegation & Crons
```bash
# Enforce flat delegation (prevents expensive recursive subagent trees)
hermes config set delegation.max_spawn_depth 1

# Register background watches (interactive or batch from cron/jobs.sh)
hermes cron create

# Commit initial board and ledger into local git tracking
cd ~/guild && git add -A && git commit -m "feat: initialize guild board and ledger"
```

---

## Operating the Guild

### Daily Routing Pattern

```text
You → SotG → Sub-whip → Class Owner → Leaf Subagents
```

1. **State Intent:** Give high-level intent to SotG (`hermes --profile sotg`).
2. **Card Creation:** SotG writes a mission card to the Kanban board with a defined outcome and done-test.
3. **Owner Assignment:** The group sub-whip assigns **one** class owner.
4. **Execution:** The class owner wakes (`hermes --profile <class>`), executes, optionally spawns bounded leaf subagents, and collects verifiable evidence.
5. **Verification & Acceptance:** Sub-whip reviews evidence before promoting to `Done`.
6. **Reporting:** SotG reports one consolidated pulse to You.

### Session-to-Card Tagging

To ensure the Ledger remains accurate and eliminate untagged spend, tag every Hermes session with its target card ID using `-c` / `--chat-id`:

```bash
# Example: Warrior executing database connection pool tuning
hermes -p warrior -c "[KEEP-101] Oracle ADB connection pool tuning" --create-if-missing

# Example: Wizard building a new landing page release
hermes -p wizard -c "[WORKS-204] Responsive landing page build" --create-if-missing
```

---

## Guild Kanban Board

Hermes Guild v1.3 operates in a **dual-mode architecture**:
1. **Execution Engine (Native Hermes Agent Kanban):** Multi-agent task claims, automated routing, and dependency graphs live inside Hermes Agent's native SQLite board (`~/.hermes/kanban/boards/guild/kanban.db`).
2. **Inspection & Human View (Guild Markdown & SQLite):** Synchronized into `~/guild/board/kanban.md` and `~/guild/ledger/guild.sqlite` via `python3 ledger/sync_kanban.py`.

### Dual-Mode Workflow & CLI Commands

```bash
# 1. Create a task on the native guild board
hermes kanban --board guild create "Optimize Oracle ADB connection pool" --assignee warrior

# 2. Decompose a complex task into child tickets routed by role description
hermes kanban --board guild decompose <task-id>

# 3. Synchronize native Hermes tasks to board/kanban.md and guild.sqlite
python3 ledger/sync_kanban.py

# 4. In-session worker tools (available to all 21 profiles):
#    - kanban_show: inspect task specification and parent evidence
#    - kanban_comment: record milestones or questions
#    - kanban_request_review: move card to Verify/Review upon completion
#    - kanban_complete: mark card Done upon sub-whip acceptance
#    - kanban_block: flag card Blocked/Hold
```

### Lifecycle Columns & Native Mapping

```text
Guild:   Inbox  ──▶ Mission ──▶ Ready ──▶ Doing   ──▶ Verify ──▶ Done
Hermes:  Triage ──▶ Todo    ──▶ Ready ──▶ Running ──▶ Review ──▶ Done
                              ↘ Hold / Blocked ↗
                              (Hermes: Blocked)
```

- **Inbox (`triage`):** Raw incoming signals (Bard mail, Rogue OSINT, Beastlord drift, Enchanter cron).
- **Mission (`todo`):** Structured outcome written by SotG; pending owner assignment.
- **Ready (`ready`):** Single owner assigned, constraints known, WIP slot open.
- **Doing (`running`):** Active work. Session must be tagged with `card_id` (`-c "[CARD-ID]..."`).
- **Verify (`review`):** Work complete, evidence attached, ledger row recorded; awaiting sub-whip review.
- **Done (`done`):** Accepted by sub-whip. Card closed.
- **Hold / Blocked (`blocked`):** Paladin financial/legal halt, change-window block, or security pause.

### WIP Limits & Fan-Out Prevention

| Scope | Default WIP Cap | Breach Rule |
|---|---|---|
| **Class Owner** | 1 Doing, 1 Verify | Cannot be assigned a second Doing card. |
| **Swimlane (Group)** | 3 Doing + Verify | Sub-whip must finish or Hold cards before pulling Ready. |
| **Guild Total** | 8 Doing + Verify | SotG halts promotions from Mission to Ready. |
| **Cross-Group Missions** | 1 Active | Requires SotG + You signoff for a second. |
| **Watch Severity-1** | Waived during containment | Parent incident card must exist before the next pulse. |

*Enchanter flags cards aging past **48h in Doing** or **24h in Verify**.*

---

## Guild Ledger & Telemetry

Located at `~/guild/ledger/guild.sqlite`. 

### Attribution Contract
Every token spent in the guild must trace back to a business outcome. The ledger separates:
- **Use:** Activations, owner cards, assist cards, idle classes.
- **Calls:** API requests, tool calls, delegate spawns, failed attempts.
- **Tokens:** Prompt, completion, cache read/write, reasoning, and provider costs.
- **Effectiveness:** `first_pass_accept` rate, rework cycles, cycle time, and post-release incidents.

### Automated Telemetry Ingestion

In v1.3, sessions automatically stream metrics to `~/.hermes/state.db`. The `on_session_end` hook (`ledger/sync_telemetry.py`) ingests token counts and cost into `guild.sqlite` automatically whenever a session ends.

You can also run batch synchronization manually:
```bash
# Sync all session telemetry from ~/.hermes/state.db
python3 ledger/record.py sync-state

# Preview sync without writing
python3 ledger/record.py sync-state --dry-run
```

### Using `ledger/record.py`

The repository includes a dependency-free CLI tool (`ledger/record.py`) to manage the ledger:

```bash
# 1. Add a card to the ledger
python3 ledger/record.py add-card \
  --id KEEP-101 \
  --title "Oracle ADB connection pool tuning" \
  --swimlane keep \
  --owner warrior \
  --priority now \
  --column doing

# 2. Log session spend and token attribution (or let sync-state do it automatically)
python3 ledger/record.py log-session \
  --card KEEP-101 \
  --group keep \
  --class warrior \
  --tokens-in 14200 \
  --tokens-out 1850 \
  --api-calls 12 \
  --tool-calls 8 \
  --cost-provider 0.042 \
  --source provider_usage

# 3. Move card to Verify once evidence is attached
python3 ledger/record.py update-card --id KEEP-101 --column verify

# 4. Mark card Done upon acceptance
python3 ledger/record.py update-card --id KEEP-101 --column done --closed

# 5. Calculate effectiveness metrics (cycle time, first-pass acceptance, token efficiency)
python3 ledger/record.py calculate-effectiveness

# 6. View the comprehensive Guild Pulse dashboard
python3 ledger/record.py pulse
```

Example pulse output (v1.3):
```text
========================================================================================
GROUP      | CARDS | WIP  | DONE  | COST ($)  | TOKENS     | PASS % | CYCLE (h) | REWORK
----------------------------------------------------------------------------------------
keep       | 3     | 1    | 2     | $0.1420   | 52,400     | 100.0% |    4.2h   | 0     
works      | 4     | 2    | 2     | $0.3810   | 128,900    |  50.0% |    8.5h   | 1     
steward    | 1     | 0    | 1     | $0.0150   | 6,200      | 100.0% |    1.1h   | 0     
watch      | 2     | 1    | 1     | $0.0920   | 31,800     | 100.0% |    2.3h   | 0     
----------------------------------------------------------------------------------------
TOTAL      | 10    | 4    | 6     | $0.6300   | 219,300    |  87.5% |    4.0h   | 1     
========================================================================================
```

### Logging effectiveness & Verify bounces

Record verification outcomes and anti-hallucination signals against a card:

```bash
python3 ledger/record.py log-effectiveness \
  --card KEEP-101 \
  --first-pass-accept 1 \
  --rework-count 0

# A claim that couldn't be traced to evidence
python3 ledger/record.py log-effectiveness \
  --card KEEP-101 \
  --verify-bounce-reason ungrounded_claim \
  --ungrounded-claims 1
```

---

## Worked Scenarios

### Scenario A: Routine Web Update
*Objective: Update product pricing page and visual layout.*
1. **You** state intent to **SotG**.
2. **SotG** opens card `WORKS-105` assigned to Works.
3. **Master of Works** names **Wizard** as owner, with **Druid** (UX specs) assisting.
4. **Druid** supplies layout and accessibility tokens.
5. **Wizard** compiles assets and deploys into staging.
6. **Ranger** verifies analytics tags and metadata.
7. Evidence is attached; **Master of Works** accepts and moves card to `Done`.

### Scenario B: Severity-1 Secret Leak
*Objective: Contain compromised API key detected in public repository.*
1. **Rogue** detects exposed key during OSINT beat; drops card in Watch Inbox.
2. **Captain of the Watch** declares Severity 1; WIP limits waived for Watch.
3. **Berserker** commands war room: immediately revokes key and halts external calls.
4. **Warrior** rotates credential in production secret manager.
5. **Cleric** scrubs git history and patches code repositories.
6. Containment confirmed; Berserker stands down.
7. SotG ratifies emergency card at the next pulse.

---

## Tuning & Customization

- **Edit Role Souls:** Modify definitions in [`generate.py`](generate.py) or markdown files in [`souls/`](souls/), then run `./install.sh` to update profile configurations.
- **Regenerate Profiles:** Run `python3 generate.py` to refresh all 21 `souls/*.md` templates.
- **Incident Escalation Depth:** To permit multi-agent parallel trees during major incidents, bump `max_spawn_depth` temporarily:
  ```bash
  hermes config set delegation.max_spawn_depth 2
  ```
  *(Remember to revert to `1` when containment is complete).*

---

## License

MIT © [Taylor Ripley](https://github.com/xl3v3r) / SP4RKL
