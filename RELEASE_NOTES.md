# Hermes Guild v1.3.0

> **A role-and-accountability operating system for multi-agent autonomous engineering, platform operations, and governance.**

Hermes Guild v1.3.0 is a major operational upgrade modernizing the guild to align seamlessly with modern Hermes Agent (v0.22+) runtime capabilities, introducing native SQLite Kanban orchestration, automated telemetry ingestion, token-efficient watchdog probes, and an anti-hallucination grounding contract.

---

### Highlights & Key Improvements

1. **Semantic Role Descriptions & Autonomous Task Routing**:
   - Added concise, semantic `description` strings for all 21 guild profiles in `generate.py` and `install.sh`.
   - Profiles are now fully discoverable by `hermes kanban decompose` for autonomous sub-task routing by specialty.
   - Regenerated all 21 `souls/*.md` files with environment context, workspace paths (`~/guild`), ledger commands, and available Kanban tools (`kanban_show`, `kanban_comment`, `kanban_request_review`, `kanban_complete`, `kanban_block`).

2. **Native Hermes Agent Kanban & Bi-Directional Synchronizer**:
   - Integrated Hermes Agent's native SQLite task board (`~/.hermes/kanban/boards/guild/kanban.db`) as the primary execution engine for agent dispatches, task claims, and worker lanes.
   - Added `ledger/sync_kanban.py` providing bi-directional synchronization between native Hermes tasks and human-readable `board/kanban.md` / `ledger/guild.sqlite`.
   - Aligned lifecycle status mappings: `inbox` ↔ `triage`, `mission` ↔ `todo`, `ready` ↔ `ready`, `doing` ↔ `running`, `verify` ↔ `review`, `hold` ↔ `blocked`, `done` ↔ `done`.

3. **Automated State Telemetry Ingestion**:
   - Created `ledger/sync_telemetry.py` lifecycle hook registered to `on_session_end` in `~/.hermes/config.yaml`.
   - Automatically ingests session tokens (prompt, completion, cache read/write, reasoning), API/tool call counts, and inference cost directly from `~/.hermes/state.db` into `ledger/guild.sqlite`.
   - Implemented `record.py sync-state` for batch reconciliation and detection of untagged token spend.

4. **Grounding & Evidence Contract (Anti-Hallucination)**:
   - Injected the Grounding & Evidence Contract into all 21 role SOULs, requiring verifiable tool citations for all Verify claims.
   - Added Paladin independent claims-audit duty to sample closed cards and challenge unsourced assertions.
   - Enhanced `ledger/schema.sql` and `ledger/record.py` to record `ungrounded_claims` and `verify_bounce_reason`.

5. **Effectiveness Engine & Modernized Pulse Dashboard**:
   - Added `calculate-effectiveness` subcommand to compute `first_pass_accept`, `rework_count`, `cycle_time_h`, and `tokens_per_accepted_card`.
   - Upgraded `record.py pulse` to render a comprehensive ASCII dashboard with first-pass acceptance rates, average cycle times, and rework counts.

6. **Token-Efficient Watchdog Crons & Deterministic Probes**:
   - Converted `cron/jobs.sh` watches to use `--no-agent` (zero LLM token consumption) for deterministic jobs and `--monitor-script` (exact-byte hash suppression) for state changes.
   - Created lightweight probe scripts in `scripts/`:
     - `scripts/check_mail_probe.py`: Deterministic mail/communication monitor for Bard.
     - `scripts/verify_backups_probe.sh`: Deterministic database integrity and backup checker for Necromancer.
     - `scripts/sweep_drift_probe.py`: Profile, SOUL, and untagged session drift detector for Beastlord.
     - `scripts/publish_pulse.py`: Automated zero-token pulse publisher for Shaman.

7. **Installer & CLI Modernization**:
   - Updated `install.sh` to use `hermes profile create "$p" --clone --no-alias --description "$desc"` to automatically inherit credentials from active profiles.
   - Automated enablement of the `kanban` toolset across all 21 profiles.
   - Pre-approves and registers the telemetry hook in `~/.hermes/config.yaml` and `shell-hooks-allowlist.json`.
   - Corrected invalid `--name` CLI argument in `README.md` to `hermes -p <profile> -c "[CARD-ID]..." --create-if-missing`.

---

### Verification
- Tested SOUL regeneration via `python3 generate.py`.
- Tested `ledger/record.py` operations (`add-card`, `log-session`, `update-card`, `calculate-effectiveness`, `sync-state --dry-run`, `pulse`).
- Tested `ledger/sync_kanban.py` with `--dry-run`.
- Tested probe scripts (`check_mail_probe.py`, `verify_backups_probe.sh`, `sweep_drift_probe.py`).
- Verified hook execution with synthetic stdin payload.
