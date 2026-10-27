#!/usr/bin/env bash
# Install the Hermes Guild (v1.3) — creates 21 profiles with descriptions,
# writes SOUL.md, enables kanban toolsets, initializes the native board,
# sets up the ledger and telemetry hooks, and registers resident cron jobs.
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
GUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUILD_REPO="${GUILD_REPO:-$HOME/guild}"

echo "== Hermes Guild installer (v1.3) =="
echo "Hermes home: $HERMES_HOME"
echo "Guild repo:  $GUILD_REPO"

# ---------------------------------------------------------------------------
# 1. Create the 21 profiles with descriptions and clone credentials
# ---------------------------------------------------------------------------
PROFILES=(warrior beastlord necromancer shaman wizard druid monk ranger \
          magician bard enchanter paladin rogue shadowknight berserker cleric \
          warden master-of-works steward captain sotg)

echo
echo "== Provisioning profiles =="
for p in "${PROFILES[@]}"; do
  desc=$(python3 "$GUILD_DIR/generate.py" --describe "$p" 2>/dev/null || echo "")
  if hermes profile create "$p" --clone --no-alias --description "$desc" >/dev/null 2>&1; then
    echo "  + $p (created with credentials and description)"
  else
    # Profile already exists; update its description
    if [[ -n "$desc" ]]; then
      hermes profile describe "$p" --text "$desc" >/dev/null 2>&1 || true
    fi
    echo "  = $p (already exists; description refreshed)"
  fi
  # Enable kanban toolset for the profile
  hermes -p "$p" tools enable kanban >/dev/null 2>&1 || true
done

# ---------------------------------------------------------------------------
# 2. Write SOUL.md into each profile
# ---------------------------------------------------------------------------
echo
echo "== Writing SOUL.md =="
for p in "${PROFILES[@]}"; do
  src="$GUILD_DIR/souls/$p.md"
  dst="$HERMES_HOME/profiles/$p/SOUL.md"
  if [[ -f "$src" ]]; then
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "  + $p/SOUL.md"
  else
    echo "  ! missing soul: $src"
  fi
done

# ---------------------------------------------------------------------------
# 3. Delegation config (flat by default; bump only for approved missions)
# ---------------------------------------------------------------------------
echo
echo "== Delegation config =="
mkdir -p "$GUILD_DIR/config"
cat > "$GUILD_DIR/config/delegation.yaml" <<'YAML'
# Apply with:  hermes config set delegation.max_spawn_depth 1
# Or merge into ~/.hermes/config.yaml
delegation:
  max_spawn_depth: 1        # 1 = flat (default). 2-3 only for SotG-approved
                             # cross-group missions (e.g. severity-1 incident).
  # role="orchestrator" lets a child spawn its own workers, gated by depth.
YAML
echo "  + config/delegation.yaml (set max_spawn_depth: 1 — flat by default)"

# ---------------------------------------------------------------------------
# 4. Initialize native Hermes Kanban board
# ---------------------------------------------------------------------------
echo
echo "== Native Hermes Kanban board =="
if hermes kanban boards list 2>/dev/null | grep -E "^[*● ]*[[:space:]]+guild[[:space:]]+" >/dev/null 2>&1; then
  echo "  = native board 'guild' already exists"
else
  if hermes kanban boards create guild --name "Hermes Operations Guild" >/dev/null 2>&1; then
    echo "  + native board 'guild' created"
  else
    echo "  ! notice: native board create skipped or handled by default"
  fi
fi

# ---------------------------------------------------------------------------
# 5. Guild repo: Kanban board, Ledger, Telemetry & Scripts
# ---------------------------------------------------------------------------
echo
echo "== Guild repo (board, ledger, scripts) =="
mkdir -p "$GUILD_REPO/board" "$GUILD_REPO/ledger" "$GUILD_REPO/scripts"
cp "$GUILD_DIR/board/kanban.md" "$GUILD_REPO/board/kanban.md"
cp "$GUILD_DIR/ledger/schema.sql" "$GUILD_REPO/ledger/schema.sql"
cp "$GUILD_DIR/ledger/record.py" "$GUILD_REPO/ledger/record.py"
chmod +x "$GUILD_REPO/ledger/record.py"

if [[ -f "$GUILD_DIR/ledger/sync_telemetry.py" ]]; then
  cp "$GUILD_DIR/ledger/sync_telemetry.py" "$GUILD_REPO/ledger/sync_telemetry.py"
  chmod +x "$GUILD_REPO/ledger/sync_telemetry.py"
fi

if [[ -f "$GUILD_DIR/ledger/sync_kanban.py" ]]; then
  cp "$GUILD_DIR/ledger/sync_kanban.py" "$GUILD_REPO/ledger/sync_kanban.py"
  chmod +x "$GUILD_REPO/ledger/sync_kanban.py"
fi

if [[ -d "$GUILD_DIR/scripts" ]]; then
  cp -r "$GUILD_DIR/scripts/"* "$GUILD_REPO/scripts/" 2>/dev/null || true
  chmod +x "$GUILD_REPO/scripts/"* 2>/dev/null || true
  mkdir -p "$HERMES_HOME/scripts"
  cp -r "$GUILD_DIR/scripts/"* "$HERMES_HOME/scripts/" 2>/dev/null || true
  chmod +x "$HERMES_HOME/scripts/"* 2>/dev/null || true
  echo "  + scripts provisioned to $GUILD_REPO/scripts and $HERMES_HOME/scripts"
fi

# Initialize SQLite database
if [[ ! -f "$GUILD_REPO/ledger/guild.sqlite" ]]; then
  python3 -c "import sqlite3; con = sqlite3.connect('$GUILD_REPO/ledger/guild.sqlite'); con.executescript(open('$GUILD_DIR/ledger/schema.sql').read())"
  echo "  + ledger/guild.sqlite (initialized schema)"
fi

if [[ -d "$GUILD_REPO/.git" ]]; then
  echo "  = git repo already initialized"
else
  git -C "$GUILD_REPO" init -q 2>/dev/null && echo "  + git init" || echo "  ! git not available; board/ledger are plain files"
fi

# ---------------------------------------------------------------------------
# 6. Register on_session_end telemetry hook in ~/.hermes/config.yaml
# ---------------------------------------------------------------------------
echo
echo "== Registering telemetry hook =="
python3 - <<EOF
import os, json, re
from datetime import datetime, timezone

hermes_home = os.path.expanduser("$HERMES_HOME")
config_path = os.path.join(hermes_home, "config.yaml")
hook_cmd = "python3 $GUILD_REPO/ledger/sync_telemetry.py"

# Safely check and register in config.yaml without stripping comments
if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    if hook_cmd in content:
        print("  = on_session_end hook already registered in config.yaml")
    else:
        # Check if active 'hooks:' section exists
        if re.search(r"^hooks:\s*$", content, re.MULTILINE):
            if re.search(r"^\s+on_session_end:\s*$", content, re.MULTILINE):
                new_content = re.sub(
                    r"(^\s+on_session_end:\s*$)",
                    r'\1\n    - command: "' + hook_cmd + '"',
                    content,
                    count=1,
                    flags=re.MULTILINE,
                )
            else:
                new_content = re.sub(
                    r"(^hooks:\s*$)",
                    r'\1\n  on_session_end:\n    - command: "' + hook_cmd + '"',
                    content,
                    count=1,
                    flags=re.MULTILINE,
                )
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("  + registered on_session_end hook in config.yaml")
        else:
            with open(config_path, "a", encoding="utf-8") as f:
                f.write('\n# Hermes Guild Telemetry Hook\nhooks:\n  on_session_end:\n    - command: "' + hook_cmd + '"\n')
            print("  + registered on_session_end hook in config.yaml")
else:
    with open(config_path, "w", encoding="utf-8") as f:
        f.write('# Hermes Guild Telemetry Hook\nhooks:\n  on_session_end:\n    - command: "' + hook_cmd + '"\n')
    print("  + created config.yaml with on_session_end hook")

allowlist_path = os.path.join(hermes_home, "shell-hooks-allowlist.json")
al_data = {"schema_version": 1, "approvals": []}
if os.path.exists(allowlist_path):
    try:
        with open(allowlist_path, "r", encoding="utf-8") as f:
            al_data = json.load(f)
    except Exception:
        al_data = {"schema_version": 1, "approvals": []}

approvals = al_data.setdefault("approvals", [])
if not any(a.get("event") == "on_session_end" and a.get("command") == hook_cmd for a in approvals):
    approvals.append({
        "event": "on_session_end",
        "command": hook_cmd,
        "approved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    })
    with open(allowlist_path, "w", encoding="utf-8") as f:
        json.dump(al_data, f, indent=2)
    print("  + pre-approved hook in shell-hooks-allowlist.json")
else:
    print("  = hook already pre-approved in shell-hooks-allowlist.json")
EOF

# ---------------------------------------------------------------------------
# 7. Resident cron jobs (interactive prompts — run each or edit jobs.json)
# ---------------------------------------------------------------------------
echo
echo "== Resident cron jobs =="
echo "  See cron/jobs.sh for the 9 resident duties (using --no-agent and --monitor-script)."
echo "  Register interactively with:"
echo "    hermes cron create"
echo "  or edit $HERMES_HOME/cron/jobs.json directly."

echo
echo "Done. Next steps:"
echo "  1. hermes config set delegation.max_spawn_depth 1"
echo "  2. Review souls/ and tweak any SOUL.md, then re-run this script."
echo "  3. Register resident cron jobs (cron/jobs.sh)."
echo "  4. Commit $GUILD_REPO so the board and ledger are durable."
