#!/usr/bin/env bash
# Install the Hermes Guild (v1.2) — creates 21 profiles, writes SOUL.md,
# sets up the Kanban board and Ledger, and registers resident cron jobs.
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
GUILD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUILD_REPO="${GUILD_REPO:-$HOME/guild}"

echo "== Hermes Guild installer (v1.2) =="
echo "Hermes home: $HERMES_HOME"
echo "Guild repo:  $GUILD_REPO"

# ---------------------------------------------------------------------------
# 1. Create the 21 profiles
# ---------------------------------------------------------------------------
PROFILES=(warrior beastlord necromancer shaman wizard druid monk ranger \
          magician bard enchanter paladin rogue shadowknight berserker cleric \
          warden master-of-works steward captain sotg)

echo
echo "== Creating profiles =="
for p in "${PROFILES[@]}"; do
  if hermes profile create "$p" --no-alias >/dev/null 2>&1; then
    echo "  + $p"
  else
    echo "  = $p (already exists)"
  fi
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
# 4. Guild repo: Kanban board + Ledger
# ---------------------------------------------------------------------------
echo
echo "== Guild repo (board + ledger) =="
mkdir -p "$GUILD_REPO/board" "$GUILD_REPO/ledger"
cp "$GUILD_DIR/board/kanban.md" "$GUILD_REPO/board/kanban.md"
cp "$GUILD_DIR/ledger/schema.sql" "$GUILD_REPO/ledger/schema.sql"

if [[ ! -f "$GUILD_REPO/ledger/guild.sqlite" ]]; then
  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$GUILD_REPO/ledger/guild.sqlite" < "$GUILD_DIR/ledger/schema.sql"
    echo "  + ledger/guild.sqlite (initialized)"
  else
    echo "  ! sqlite3 not found — run: sqlite3 $GUILD_REPO/ledger/guild.sqlite < ledger/schema.sql"
  fi
fi

if [[ -d "$GUILD_REPO/.git" ]]; then
  echo "  = git repo already initialized"
else
  git -C "$GUILD_REPO" init -q 2>/dev/null && echo "  + git init" || echo "  ! git not available; board/ledger are plain files"
fi

# ---------------------------------------------------------------------------
# 5. Resident cron jobs (interactive prompts — run each or edit jobs.json)
# ---------------------------------------------------------------------------
echo
echo "== Resident cron jobs =="
echo "  See cron/jobs.sh for the 8 resident duties. Register interactively:"
echo "    hermes cron create"
echo "  or edit $HERMES_HOME/cron/jobs.json directly."

echo
echo "Done. Next steps:"
echo "  1. hermes config set delegation.max_spawn_depth 1"
echo "  2. Review souls/ and tweak any SOUL.md, then re-run this script."
echo "  3. Register resident cron jobs (cron/jobs.sh)."
echo "  4. Commit $GUILD_REPO so the board and ledger are durable."
