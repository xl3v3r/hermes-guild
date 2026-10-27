#!/usr/bin/env python3
"""Hermes Guild Telemetry Sync Hook (v1.3).

Executes on Hermes Agent's `on_session_end` lifecycle event to automatically
record session tokens, tool calls, and inference costs into the Guild Ledger
(guild.sqlite), attributing spend to active Kanban cards.
"""

import argparse
import json
import os
import re
import sqlite3
import sys

# Class to swimlane mapping
CLASS_GROUPS = {
    "warrior": "keep", "beastlord": "keep", "necromancer": "keep", "shaman": "keep", "warden": "keep",
    "wizard": "works", "druid": "works", "monk": "works", "ranger": "works", "master-of-works": "works",
    "magician": "steward", "bard": "steward", "enchanter": "steward", "paladin": "steward", "steward": "steward",
    "rogue": "watch", "shadowknight": "watch", "berserker": "watch", "cleric": "watch", "captain": "watch",
    "sotg": "steward",
}

DEFAULT_DB_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "guild.sqlite"),
    os.path.expanduser("~/guild/ledger/guild.sqlite"),
    os.path.join(os.getcwd(), "ledger", "guild.sqlite"),
    os.path.join(os.getcwd(), "guild.sqlite"),
]


def find_guild_db():
    env_db = os.environ.get("HERMES_GUILD_DB")
    if env_db and os.path.exists(os.path.expanduser(env_db)):
        return os.path.expanduser(env_db)
    repo = os.environ.get("GUILD_REPO")
    if repo:
        cand = os.path.join(os.path.expanduser(repo), "ledger", "guild.sqlite")
        if os.path.exists(cand):
            return cand
    for p in DEFAULT_DB_PATHS:
        if os.path.exists(p):
            return p
    return os.path.expanduser("~/guild/ledger/guild.sqlite")


def parse_card_tag(text):
    if not text:
        return None
    m = re.search(r"\[([A-Za-z0-9_\-]+)\]", text)
    if m:
        return m.group(1).upper()
    m = re.search(r"\b([A-Za-z]+-[0-9]+)\b", text)
    if m:
        return m.group(1).upper()
    return None


def sync_session_id(session_id, guild_db_path, state_db_path="~/.hermes/state.db"):
    state_db = os.path.expanduser(state_db_path)
    if not os.path.exists(state_db):
        return False

    s_conn = sqlite3.connect(state_db)
    s_conn.row_factory = sqlite3.Row

    os.makedirs(os.path.dirname(os.path.abspath(guild_db_path)), exist_ok=True)
    g_conn = sqlite3.connect(guild_db_path)
    g_conn.row_factory = sqlite3.Row
    g_conn.execute("PRAGMA foreign_keys = ON")

    # Ensure schema exists
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            g_conn.executescript(f.read())

    # Check if already synced
    exists = g_conn.execute(
        "SELECT 1 FROM ledger_rows WHERE parent_session = ? AND source = 'state_db'",
        (session_id,)
    ).fetchone()
    if exists:
        return True

    s = s_conn.execute(
        """
        SELECT id, display_name, title, profile_name,
               input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
               reasoning_tokens, api_call_count, tool_call_count,
               actual_cost_usd, estimated_cost_usd
        FROM sessions WHERE id = ?
        """,
        (session_id,)
    ).fetchone()

    if not s:
        return False

    title_text = s["title"] or s["display_name"] or ""
    card_id = parse_card_tag(title_text)

    profile = (s["profile_name"] or "sotg").lower()
    class_slug = profile if profile in CLASS_GROUPS else "sotg"
    group_name = CLASS_GROUPS.get(class_slug, "keep")

    cost = s["actual_cost_usd"] if s["actual_cost_usd"] is not None else s["estimated_cost_usd"]
    if cost is None:
        cost = 0.0

    if card_id:
        # Check if card exists in cards table
        card_row = g_conn.execute("SELECT swimlane FROM cards WHERE card_id = ?", (card_id,)).fetchone()
        if not card_row:
            with g_conn:
                g_conn.execute(
                    """
                    INSERT OR IGNORE INTO cards (card_id, title, swimlane, owner_class, column)
                    VALUES (?, ?, ?, ?, 'doing')
                    """,
                    (card_id, title_text or f"Session {session_id[:8]}", group_name, class_slug),
                )
            card_group = group_name
        else:
            card_group = card_row["swimlane"]

        with g_conn:
            g_conn.execute(
                """
                INSERT INTO ledger_rows (
                    card_id, group_name, class_slug, role, parent_session, source,
                    api_calls, tool_calls, delegate_spawns, failed_calls,
                    tokens_in, tokens_out, tokens_cache_read, tokens_cache_write, tokens_reasoning,
                    cost_provider, cost_estimate
                ) VALUES (?, ?, ?, 'owner', ?, 'state_db', ?, ?, 0, 0, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    card_id,
                    card_group,
                    class_slug,
                    session_id,
                    s["api_call_count"] or 0,
                    s["tool_call_count"] or 0,
                    s["input_tokens"] or 0,
                    s["output_tokens"] or 0,
                    s["cache_read_tokens"] or 0,
                    s["cache_write_tokens"] or 0,
                    s["reasoning_tokens"] or 0,
                    cost,
                    s["estimated_cost_usd"],
                ),
            )
    else:
        with g_conn:
            g_conn.execute(
                """
                INSERT INTO ledger_rows (
                    card_id, group_name, class_slug, role, parent_session, source,
                    api_calls, tool_calls, delegate_spawns, failed_calls,
                    tokens_in, tokens_out, tokens_cache_read, tokens_cache_write, tokens_reasoning,
                    cost_provider, cost_estimate
                ) VALUES (NULL, ?, ?, 'owner', ?, 'state_db', ?, ?, 0, 0, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    group_name,
                    class_slug,
                    session_id,
                    s["api_call_count"] or 0,
                    s["tool_call_count"] or 0,
                    s["input_tokens"] or 0,
                    s["output_tokens"] or 0,
                    s["cache_read_tokens"] or 0,
                    s["cache_write_tokens"] or 0,
                    s["reasoning_tokens"] or 0,
                    cost,
                    s["estimated_cost_usd"],
                ),
            )
    return True


def main():
    parser = argparse.ArgumentParser(description="Guild Telemetry Hook")
    parser.add_argument("--session-id", default=None, help="Explicit session ID to sync")
    parser.add_argument("--db", default=None, help="Path to guild.sqlite")
    parser.add_argument("--state-db", default="~/.hermes/state.db", help="Path to state.db")
    args = parser.parse_args()

    session_id = args.session_id
    guild_db = args.db or find_guild_db()

    # If no session ID passed via arg, check stdin for hook payload
    if not session_id and not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                payload = json.loads(stdin_data)
                session_id = payload.get("session_id")
        except Exception:
            pass

    if session_id:
        sync_session_id(session_id, guild_db, args.state_db)
    else:
        # Incremental sync of all recent unrecorded sessions
        try:
            state_db = os.path.expanduser(args.state_db)
            if os.path.exists(state_db):
                s_conn = sqlite3.connect(state_db)
                s_conn.row_factory = sqlite3.Row
                rows = s_conn.execute("SELECT id FROM sessions ORDER BY started_at DESC LIMIT 50").fetchall()
                for r in rows:
                    sync_session_id(r["id"], guild_db, args.state_db)
        except Exception:
            pass

    # Shell hooks expect valid JSON on stdout
    print("{}")


if __name__ == "__main__":
    main()
