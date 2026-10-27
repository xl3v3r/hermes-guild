#!/usr/bin/env bash
# Necromancer Backup Verification Probe (v1.3)
# Runs under Hermes Agent cron with --no-agent for zero-token deterministic checks.
# Verifies database integrity and recent backup existence.
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
GUILD_REPO="${GUILD_REPO:-$HOME/guild}"
STATE_DB="$HERMES_HOME/state.db"
GUILD_DB="$GUILD_REPO/ledger/guild.sqlite"

ERRORS=0

echo "=== Necromancer Backup & Integrity Verification ==="

# 1. Verify state.db integrity
if [[ -f "$STATE_DB" ]]; then
  CHECK=$(python3 -c "import sqlite3; con=sqlite3.connect('$STATE_DB'); print(con.execute('PRAGMA integrity_check').fetchone()[0])" 2>/dev/null || echo "FAIL")
  if [[ "$CHECK" == "ok" ]]; then
    echo "  ✓ state.db integrity: OK"
  else
    echo "  ✗ state.db integrity check failed: $CHECK"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo "  - state.db not found"
fi

# 2. Verify guild.sqlite integrity
if [[ -f "$GUILD_DB" ]]; then
  CHECK=$(python3 -c "import sqlite3; con=sqlite3.connect('$GUILD_DB'); print(con.execute('PRAGMA integrity_check').fetchone()[0])" 2>/dev/null || echo "FAIL")
  if [[ "$CHECK" == "ok" ]]; then
    echo "  ✓ guild.sqlite integrity: OK"
  else
    echo "  ✗ guild.sqlite integrity check failed: $CHECK"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo "  - guild.sqlite not found (run install.sh or record.py)"
fi

# 3. Check for backup snapshots
BACKUP_DIR="${HERMES_BACKUP_DIR:-$HOME/backups}"
if [[ -d "$BACKUP_DIR" ]]; then
  LATEST_BACKUP=$(find "$BACKUP_DIR" -type f -mtime -1 2>/dev/null | head -n 1 || true)
  if [[ -n "$LATEST_BACKUP" ]]; then
    echo "  ✓ Latest backup snapshot verified: $LATEST_BACKUP"
  else
    echo "  ! Warning: No backup found in $BACKUP_DIR within last 24h"
  fi
else
  echo "  - Backup directory $BACKUP_DIR not configured"
fi

if [[ $ERRORS -eq 0 ]]; then
  echo "Status: ALL SYSTEMS HEALTHY"
  exit 0
else
  echo "Status: INTEGRITY DEGRADED ($ERRORS issues)"
  exit 1
fi
