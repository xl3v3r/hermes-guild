#!/usr/bin/env python3
"""Beastlord Drift Sweep Probe (v1.3).

Lightweight monitor probe for Hermes Agent cron (--monitor-script).
Detects profile configuration drift, missing SOUL files, and untagged sessions.
Deterministic and timestamp-free: unchanged output suppresses agent turns.
"""

import os
import sqlite3
import sys

HERMES_PROFILES = [
    "warrior", "beastlord", "necromancer", "shaman", "wizard", "druid", "monk", "ranger",
    "magician", "bard", "enchanter", "paladin", "rogue", "shadowknight", "berserker", "cleric",
    "warden", "master-of-works", "steward", "captain", "sotg"
]


def check_profile_drift(hermes_home):
    profiles_dir = os.path.join(hermes_home, "profiles")
    missing_profiles = []
    missing_souls = []

    for p in sorted(HERMES_PROFILES):
        p_path = os.path.join(profiles_dir, p)
        if not os.path.exists(p_path):
            missing_profiles.append(p)
        else:
            soul_path = os.path.join(p_path, "SOUL.md")
            if not os.path.exists(soul_path):
                missing_souls.append(p)

    return missing_profiles, missing_souls


def check_untagged_sessions(hermes_home):
    state_db = os.path.join(hermes_home, "state.db")
    if not os.path.exists(state_db):
        return 0
    try:
        conn = sqlite3.connect(state_db)
        cur = conn.execute(
            """
            SELECT COUNT(*) FROM sessions
            WHERE (title IS NULL OR title NOT LIKE '%[%]%')
              AND (display_name IS NULL OR display_name NOT LIKE '%[%]%')
            """
        )
        return cur.fetchone()[0]
    except Exception:
        return 0


def main():
    hermes_home = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
    missing_p, missing_s = check_profile_drift(hermes_home)
    untagged_count = check_untagged_sessions(hermes_home)

    drift_items = []
    if missing_p:
        drift_items.append(f"MISSING_PROFILES: {','.join(missing_p)}")
    if missing_s:
        drift_items.append(f"MISSING_SOULS: {','.join(missing_s)}")
    if untagged_count > 0:
        drift_items.append(f"UNTAGGED_SESSIONS: {untagged_count}")

    if not drift_items:
        print("DRIFT_STATUS: NO_DRIFT_DETECTED")
    else:
        print("DRIFT_STATUS: DRIFT_DETECTED")
        for item in sorted(drift_items):
            print(f"- {item}")


if __name__ == "__main__":
    main()
