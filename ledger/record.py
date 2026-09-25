#!/usr/bin/env python3
"""Guild Ledger CLI Helper (v1.2).

Provides easy recording of cards and spending sessions into the SQLite ledger
without raw SQL escaping. Shaman publishes; Paladin inspects costs; SotG monitors pulse.
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime

DEFAULT_DB_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "guild.sqlite"),
    os.path.expanduser("~/guild/ledger/guild.sqlite"),
    os.path.join(os.getcwd(), "ledger", "guild.sqlite"),
    os.path.join(os.getcwd(), "guild.sqlite"),
]


def find_db(explicit_path=None):
    if explicit_path:
        return explicit_path
    for p in DEFAULT_DB_PATHS:
        if os.path.exists(p):
            return p
    # Default to ~/guild/ledger/guild.sqlite even if not yet created
    return os.path.expanduser("~/guild/ledger/guild.sqlite")


def get_connection(db_path):
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Ensure schema is loaded
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    return conn


def cmd_add_card(args):
    conn = get_connection(find_db(args.db))
    with conn:
        conn.execute(
            """
            INSERT INTO cards (card_id, title, swimlane, owner_class, assists, source, priority, done_test, constraints, column)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(card_id) DO UPDATE SET
                title = excluded.title,
                swimlane = excluded.swimlane,
                owner_class = excluded.owner_class,
                assists = coalesce(excluded.assists, assists),
                source = coalesce(excluded.source, source),
                priority = coalesce(excluded.priority, priority),
                done_test = coalesce(excluded.done_test, done_test),
                constraints = coalesce(excluded.constraints, constraints),
                column = coalesce(excluded.column, column)
            """,
            (
                args.id,
                args.title,
                args.swimlane,
                args.owner,
                args.assists,
                args.source,
                args.priority,
                args.done,
                args.constraints,
                args.column,
            ),
        )
    print(f"Card {args.id} saved in lane '{args.swimlane}' (column: {args.column}).")


def cmd_update_card(args):
    conn = get_connection(find_db(args.db))
    updates = []
    params = []
    if args.column:
        updates.append("column = ?")
        params.append(args.column)
        if args.column == "done":
            updates.append("closed_at = datetime('now')")
    if args.closed:
        updates.append("closed_at = datetime('now')")
    if not updates:
        print("No updates specified.")
        return

    params.append(args.id)
    with conn:
        cur = conn.execute(f"UPDATE cards SET {', '.join(updates)} WHERE card_id = ?", params)
        if cur.rowcount == 0:
            print(f"Warning: Card {args.id} not found.")
        else:
            print(f"Card {args.id} updated.")


def cmd_log_session(args):
    conn = get_connection(find_db(args.db))
    with conn:
        conn.execute(
            """
            INSERT INTO ledger_rows (
                card_id, group_name, class_slug, role, parent_session, source,
                api_calls, tool_calls, delegate_spawns, failed_calls,
                tokens_in, tokens_out, tokens_cache_read, tokens_cache_write, tokens_reasoning,
                cost_provider, cost_estimate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                args.card,
                args.group,
                args.class_slug,
                args.role,
                args.parent_session,
                args.source,
                args.api_calls,
                args.tool_calls,
                args.delegate_spawns,
                args.failed_calls,
                args.tokens_in,
                args.tokens_out,
                args.tokens_cache_read,
                args.tokens_cache_write,
                args.tokens_reasoning,
                args.cost_provider,
                args.cost_estimate,
            ),
        )
    print(f"Logged session for card {args.card} ({args.class_slug} / {args.group}).")


def cmd_pulse(args):
    conn = get_connection(find_db(args.db))
    cur = conn.execute("SELECT * FROM pulse")
    rows = cur.fetchall()
    print("=" * 68)
    print(f"{'GROUP':<10} | {'CARDS':<6} | {'WIP':<5} | {'ACCEPTED':<8} | {'PROVIDER $':<10} | {'TOKENS':<10}")
    print("-" * 68)
    total_cards = total_wip = total_accepted = total_tokens = 0
    total_cost = 0.0
    for r in rows:
        total_cards += r["cards"] or 0
        total_wip += r["wip"] or 0
        total_accepted += r["accepted"] or 0
        cost = r["cost_provider"] or 0.0
        total_cost += cost
        tokens = r["tokens"] or 0
        total_tokens += tokens
        print(
            f"{r['group_name']:<10} | {r['cards'] or 0:<6} | {r['wip'] or 0:<5} | {r['accepted'] or 0:<8} | ${cost:<9.4f} | {tokens:<10}"
        )
    print("-" * 68)
    print(f"{'TOTAL':<10} | {total_cards:<6} | {total_wip:<5} | {total_accepted:<8} | ${total_cost:<9.4f} | {total_tokens:<10}")
    print("=" * 68)


def cmd_untagged(args):
    conn = get_connection(find_db(args.db))
    cur = conn.execute("SELECT * FROM untagged")
    rows = cur.fetchall()
    if not rows:
        print("No untagged sessions found. (Good!)")
        return
    print(f"Found {len(rows)} untagged session row(s):")
    for r in rows:
        print(f"Row {r['row_id']}: group={r['group_name']} class={r['class_slug']} tokens_in={r['tokens_in']} tokens_out={r['tokens_out']} at {r['recorded_at']}")


def main():
    parser = argparse.ArgumentParser(description="Guild Ledger CLI Helper")
    parser.add_argument("--db", help="Path to SQLite database file", default=None)
    sub = parser.add_subparsers(dest="cmd", required=True)

    # add-card
    p_add = sub.add_parser("add-card", help="Add or update a card on the ledger")
    p_add.add_argument("--id", required=True, help="Card ID (e.g. KEEP-001)")
    p_add.add_argument("--title", required=True, help="Card title or outcome")
    p_add.add_argument("--swimlane", required=True, choices=["keep", "works", "steward", "watch"], help="Swimlane")
    p_add.add_argument("--owner", required=True, help="Owner class slug (e.g. warrior)")
    p_add.add_argument("--assists", default=None, help="Comma-separated assistant class slugs")
    p_add.add_argument("--source", default="you", help="Source (you, bard, rogue, beastlord, etc.)")
    p_add.add_argument("--priority", choices=["now", "next", "later"], default="next")
    p_add.add_argument("--done", default=None, help="Definition of done")
    p_add.add_argument("--constraints", default=None, help="Constraints list")
    p_add.add_argument(
        "--column",
        choices=["inbox", "mission", "ready", "doing", "verify", "done", "hold"],
        default="inbox",
        help="Column",
    )
    p_add.set_defaults(func=cmd_add_card)

    # update-card
    p_up = sub.add_parser("update-card", help="Update card column or status")
    p_up.add_argument("--id", required=True, help="Card ID")
    p_up.add_argument(
        "--column",
        choices=["inbox", "mission", "ready", "doing", "verify", "done", "hold"],
        default=None,
    )
    p_up.add_argument("--closed", action="store_true", help="Mark closed_at timestamp now")
    p_up.set_defaults(func=cmd_update_card)

    # log-session
    p_log = sub.add_parser("log-session", help="Record session spend attributed to a card")
    p_log.add_argument("--card", required=True, help="Card ID")
    p_log.add_argument("--group", required=True, choices=["keep", "works", "steward", "watch"])
    p_log.add_argument("--class", dest="class_slug", required=True, help="Class slug (e.g. warrior)")
    p_log.add_argument("--role", choices=["owner", "assistant", "subagent"], default="owner")
    p_log.add_argument("--parent-session", default=None, help="Parent session UUID if subagent")
    p_log.add_argument(
        "--source",
        choices=["provider_usage", "state_db", "estimate", "plugin"],
        default="provider_usage",
    )
    p_log.add_argument("--api-calls", type=int, default=0)
    p_log.add_argument("--tool-calls", type=int, default=0)
    p_log.add_argument("--delegate-spawns", type=int, default=0)
    p_log.add_argument("--failed-calls", type=int, default=0)
    p_log.add_argument("--tokens-in", type=int, default=0)
    p_log.add_argument("--tokens-out", type=int, default=0)
    p_log.add_argument("--tokens-cache-read", type=int, default=0)
    p_log.add_argument("--tokens-cache-write", type=int, default=0)
    p_log.add_argument("--tokens-reasoning", type=int, default=0)
    p_log.add_argument("--cost-provider", type=float, default=None)
    p_log.add_argument("--cost-estimate", type=float, default=None)
    p_log.set_defaults(func=cmd_log_session)

    # pulse
    p_pulse = sub.add_parser("pulse", help="Display Guild Ledger pulse view")
    p_pulse.set_defaults(func=cmd_pulse)

    # untagged
    p_untagged = sub.add_parser("untagged", help="List untagged sessions")
    p_untagged.set_defaults(func=cmd_untagged)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
