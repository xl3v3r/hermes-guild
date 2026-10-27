#!/usr/bin/env python3
"""Guild Ledger CLI Helper (v1.3).

Provides easy recording of cards and spending sessions into the SQLite ledger
without raw SQL escaping. Shaman publishes; Paladin inspects costs; SotG monitors pulse.
Includes automated state.db ingestion and effectiveness calculations.
"""

import argparse
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

DEFAULT_DB_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "guild.sqlite"),
    os.path.expanduser("~/guild/ledger/guild.sqlite"),
    os.path.join(os.getcwd(), "ledger", "guild.sqlite"),
    os.path.join(os.getcwd(), "guild.sqlite"),
]

CLASS_GROUPS = {
    "warrior": "keep", "beastlord": "keep", "necromancer": "keep", "shaman": "keep", "warden": "keep",
    "wizard": "works", "druid": "works", "monk": "works", "ranger": "works", "master-of-works": "works",
    "magician": "steward", "bard": "steward", "enchanter": "steward", "paladin": "steward", "steward": "steward",
    "rogue": "watch", "shadowknight": "watch", "berserker": "watch", "cleric": "watch", "captain": "watch",
    "sotg": "steward",
}


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
    conn.execute("PRAGMA foreign_keys = ON")
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
        if args.column in ("done", "closed"):
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
    tag_str = f"card {args.card}" if args.card else "UNTAGGED session"
    print(f"Logged session for {tag_str} ({args.class_slug} / {args.group}).")


def cmd_log_effectiveness(args):
    conn = get_connection(find_db(args.db))
    with conn:
        conn.execute(
            """
            INSERT INTO effectiveness (
                card_id, first_pass_accept, rework_count, done_test_met,
                incident_spawned, ungrounded_claims, verify_bounce_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(card_id) DO UPDATE SET
                first_pass_accept = coalesce(excluded.first_pass_accept, effectiveness.first_pass_accept),
                rework_count = coalesce(excluded.rework_count, effectiveness.rework_count),
                done_test_met = coalesce(excluded.done_test_met, effectiveness.done_test_met),
                incident_spawned = coalesce(excluded.incident_spawned, effectiveness.incident_spawned),
                ungrounded_claims = coalesce(excluded.ungrounded_claims, effectiveness.ungrounded_claims),
                verify_bounce_reason = coalesce(excluded.verify_bounce_reason, effectiveness.verify_bounce_reason)
            """,
            (
                args.card,
                args.first_pass_accept,
                args.rework_count,
                args.done_test_met,
                args.incident_spawned,
                args.ungrounded_claims,
                args.verify_bounce_reason,
            ),
        )
    print(f"Logged effectiveness for card {args.card}.")


def parse_datetime_utc(s):
    """Parse timestamp string into UTC-naive datetime object for arithmetic."""
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def parse_card_tag(text):
    """Extract card ID from string like '[KEEP-101] Fix connection pool' or 'KEEP-101: Fix'."""
    if not text:
        return None
    # Check [TAG-123] pattern
    m = re.search(r"\[([A-Za-z0-9_\-]+)\]", text)
    if m:
        return m.group(1).upper()
    # Check TAG-123 prefix pattern (case-insensitive)
    m = re.search(r"\b([A-Za-z]+-[0-9]+)\b", text)
    if m:
        return m.group(1).upper()
    return None


def cmd_sync_state(args):
    """Sync session telemetry from ~/.hermes/state.db into the guild ledger."""
    state_db = os.path.expanduser(args.state_db)
    if not os.path.exists(state_db):
        print(f"State DB not found at: {state_db}")
        return

    s_conn = sqlite3.connect(state_db)
    s_conn.row_factory = sqlite3.Row

    g_conn = get_connection(find_db(args.db))

    # Existing synced sessions
    cur = g_conn.execute("SELECT parent_session FROM ledger_rows WHERE source = 'state_db' AND parent_session IS NOT NULL")
    synced_sessions = {r["parent_session"] for r in cur.fetchall()}

    # Known cards
    cur = g_conn.execute("SELECT card_id, swimlane, owner_class FROM cards")
    known_cards = {r["card_id"]: dict(r) for r in cur.fetchall()}

    # Fetch sessions from state.db
    s_cur = s_conn.execute(
        """
        SELECT id, display_name, title, profile_name,
               input_tokens, output_tokens, cache_read_tokens, cache_write_tokens,
               reasoning_tokens, api_call_count, tool_call_count,
               actual_cost_usd, estimated_cost_usd, started_at, ended_at
        FROM sessions
        ORDER BY started_at ASC
        """
    )
    sessions = s_cur.fetchall()

    new_tagged = 0
    new_untagged = 0
    skipped = 0

    for s in sessions:
        sid = s["id"]
        if sid in synced_sessions:
            skipped += 1
            continue

        title_text = s["title"] or s["display_name"] or ""
        card_id = parse_card_tag(title_text)

        profile = (s["profile_name"] or "sotg").lower()
        class_slug = profile if profile in CLASS_GROUPS else "sotg"
        group_name = CLASS_GROUPS.get(class_slug, "keep")

        cost = s["actual_cost_usd"] if s["actual_cost_usd"] is not None else s["estimated_cost_usd"]
        if cost is None:
            cost = 0.0

        if card_id:
            # If card is not in cards table, record or auto-stub it
            if card_id not in known_cards:
                if not args.dry_run:
                    with g_conn:
                        g_conn.execute(
                            """
                            INSERT OR IGNORE INTO cards (card_id, title, swimlane, owner_class, column)
                            VALUES (?, ?, ?, ?, 'doing')
                            """,
                            (card_id, title_text or f"Session {sid[:8]}", group_name, class_slug),
                        )
                known_cards[card_id] = {"swimlane": group_name, "owner_class": class_slug}

            card_group = known_cards[card_id]["swimlane"]
            if not args.dry_run:
                with g_conn:
                    g_conn.execute(
                        """
                        INSERT INTO ledger_rows (
                            card_id, group_name, class_slug, role, parent_session, source,
                            api_calls, tool_calls, delegate_spawns, failed_calls,
                            tokens_in, tokens_out, tokens_cache_read, tokens_cache_write, tokens_reasoning,
                            cost_provider, cost_estimate
                        ) VALUES (?, ?, ?, ?, ?, 'state_db', ?, ?, 0, 0, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            card_id,
                            card_group,
                            class_slug,
                            "owner",
                            sid,
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
            new_tagged += 1
        else:
            # Untagged session
            if not args.dry_run:
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
                            sid,
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
            new_untagged += 1

    dry_prefix = "[DRY-RUN] " if args.dry_run else ""
    print(f"{dry_prefix}Sync complete: {new_tagged} tagged session(s), {new_untagged} untagged, {skipped} already synced.")


def cmd_calculate_effectiveness(args):
    """Compute cycle time, rework, and acceptance metrics for cards."""
    conn = get_connection(find_db(args.db))
    query = "SELECT card_id, opened_at, closed_at, column FROM cards"
    params = []
    if args.card:
        query += " WHERE card_id = ?"
        params.append(args.card)

    cards = conn.execute(query, params).fetchall()
    updated = 0

    for c in cards:
        cid = c["card_id"]
        opened = c["opened_at"]
        closed = c["closed_at"]
        col = c["column"]

        # Calculate cycle time using robust UTC-naive timestamps
        cycle_time_h = None
        if opened and closed:
            t0 = parse_datetime_utc(opened)
            t1 = parse_datetime_utc(closed)
            if t0 and t1:
                cycle_time_h = round(max(0.0, (t1 - t0).total_seconds() / 3600.0), 2)

        # Check tokens from ledger
        tok_row = conn.execute(
            "SELECT SUM(tokens_in + tokens_out) as total_tok FROM ledger_rows WHERE card_id = ?",
            (cid,)
        ).fetchone()
        tokens = tok_row["total_tok"] if tok_row and tok_row["total_tok"] is not None else 0.0

        # Existing effectiveness row
        eff = conn.execute("SELECT * FROM effectiveness WHERE card_id = ?", (cid,)).fetchone()
        rework_count = eff["rework_count"] if eff and eff["rework_count"] is not None else 0
        ungrounded = eff["ungrounded_claims"] if eff and eff["ungrounded_claims"] is not None else 0
        bounce_reason = eff["verify_bounce_reason"] if eff else None

        # First pass accept:
        # 1 if card is completed without rework; 0 if completed after rework; None if not yet completed (WIP/open)
        is_done = col in ("done", "archived") or bool(closed)
        first_pass = (1 if rework_count == 0 else 0) if is_done else None
        done_test_met = 1 if is_done else 0
        tokens_accepted = tokens if is_done else None

        with conn:
            conn.execute(
                """
                INSERT INTO effectiveness (
                    card_id, first_pass_accept, rework_count, cycle_time_h,
                    done_test_met, tokens_per_accepted_card, ungrounded_claims, verify_bounce_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(card_id) DO UPDATE SET
                    first_pass_accept = excluded.first_pass_accept,
                    rework_count = excluded.rework_count,
                    cycle_time_h = coalesce(excluded.cycle_time_h, effectiveness.cycle_time_h),
                    done_test_met = excluded.done_test_met,
                    tokens_per_accepted_card = excluded.tokens_per_accepted_card,
                    ungrounded_claims = excluded.ungrounded_claims,
                    verify_bounce_reason = coalesce(excluded.verify_bounce_reason, effectiveness.verify_bounce_reason)
                """,
                (cid, first_pass, rework_count, cycle_time_h, done_test_met, tokens_accepted, ungrounded, bounce_reason),
            )
        updated += 1

    print(f"Calculated effectiveness metrics for {updated} card(s).")


def cmd_pulse(args):
    conn = get_connection(find_db(args.db))
    cur = conn.execute("SELECT * FROM pulse")
    rows = cur.fetchall()

    fmt_header = f"{'GROUP':<10} | {'CARDS':<5} | {'WIP':<4} | {'DONE':<5} | {'COST ($)':<9} | {'TOKENS':<10} | {'PASS %':<6} | {'CYCLE (h)':<9} | {'REWORK':<6}"
    sep = "=" * len(fmt_header)
    div = "-" * len(fmt_header)

    print(sep)
    print(fmt_header)
    print(div)

    total_cards = total_wip = total_accepted = total_tokens = total_rework = 0
    total_cost = 0.0

    for r in rows:
        cards = r["cards"] or 0
        wip = r["wip"] or 0
        accepted = r["accepted"] or 0
        cost = r["cost_provider"] or 0.0
        tokens = r["tokens"] or 0
        pass_rate = r["first_pass_rate"]
        cycle_h = r["avg_cycle_time_h"]
        rework = r["total_rework"] or 0

        total_cards += cards
        total_wip += wip
        total_accepted += accepted
        total_cost += cost
        total_tokens += tokens
        total_rework += rework

        pass_str = f"{pass_rate:4.1f}%" if pass_rate is not None else "   -  "
        cycle_str = f"{cycle_h:6.1f}h" if cycle_h is not None else "    -   "

        print(
            f"{r['group_name']:<10} | {cards:<5} | {wip:<4} | {accepted:<5} | ${cost:<8.4f} | {tokens:<10,d} | {pass_str:<6} | {cycle_str:<9} | {rework:<6}"
        )

    print(div)
    # Compute overall averages from underlying tables for statistical accuracy
    overall_pass_row = conn.execute("SELECT AVG(first_pass_accept * 100.0) FROM effectiveness WHERE first_pass_accept IS NOT NULL").fetchone()
    overall_pass = overall_pass_row[0] if overall_pass_row and overall_pass_row[0] is not None else None
    overall_cycle_row = conn.execute("SELECT AVG(cycle_time_h) FROM effectiveness WHERE cycle_time_h IS NOT NULL").fetchone()
    overall_cycle = overall_cycle_row[0] if overall_cycle_row and overall_cycle_row[0] is not None else None

    avg_pass = f"{overall_pass:4.1f}%" if overall_pass is not None else "   -  "
    avg_cycle = f"{overall_cycle:6.1f}h" if overall_cycle is not None else "    -   "
    print(
        f"{'TOTAL':<10} | {total_cards:<5} | {total_wip:<4} | {total_accepted:<5} | ${total_cost:<8.4f} | {total_tokens:<10,d} | {avg_pass:<6} | {avg_cycle:<9} | {total_rework:<6}"
    )
    print(sep)


def cmd_untagged(args):
    conn = get_connection(find_db(args.db))
    cur = conn.execute("SELECT * FROM untagged")
    rows = cur.fetchall()
    if not rows:
        print("No untagged sessions found. (Good!)")
        return
    print(f"Found {len(rows)} untagged session row(s):")
    for r in rows:
        cost = r["cost_provider"] or 0.0
        print(f"Row {r['row_id']}: group={r['group_name']} class={r['class_slug']} tokens_in={r['tokens_in']} tokens_out={r['tokens_out']} cost=${cost:.4f} session={r['parent_session']} at {r['recorded_at']}")


def main():
    parser = argparse.ArgumentParser(description="Guild Ledger CLI Helper (v1.3)")
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
        choices=["inbox", "mission", "ready", "doing", "verify", "done", "hold",
                 "triage", "todo", "running", "review", "blocked"],
        default="inbox",
        help="Column",
    )
    p_add.set_defaults(func=cmd_add_card)

    # update-card
    p_up = sub.add_parser("update-card", help="Update card column or status")
    p_up.add_argument("--id", required=True, help="Card ID")
    p_up.add_argument(
        "--column",
        choices=["inbox", "mission", "ready", "doing", "verify", "done", "hold",
                 "triage", "todo", "running", "review", "blocked"],
        default=None,
    )
    p_up.add_argument("--closed", action="store_true", help="Mark closed_at timestamp now")
    p_up.set_defaults(func=cmd_update_card)

    # log-session
    p_log = sub.add_parser("log-session", help="Record session spend attributed to a card")
    p_log.add_argument("--card", default=None, help="Card ID (optional; omit for untagged)")
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

    # log-effectiveness
    p_eff = sub.add_parser("log-effectiveness", help="Record effectiveness metrics for a card")
    p_eff.add_argument("--card", required=True, help="Card ID")
    p_eff.add_argument("--first-pass-accept", type=int, choices=[0, 1], default=None,
                       help="1 if accepted on first review, 0 if rework was needed")
    p_eff.add_argument("--rework-count", type=int, default=None,
                       help="Number of times card bounced back to Doing")
    p_eff.add_argument("--done-test-met", type=int, choices=[0, 1], default=None,
                       help="1 if done-test was proven with evidence, 0 otherwise")
    p_eff.add_argument("--incident-spawned", type=int, default=None,
                       help="Number of Watch incidents spawned by this card")
    p_eff.add_argument("--ungrounded-claims", type=int, default=None,
                       help="Count of claims bounced for lacking evidence citation")
    p_eff.add_argument("--verify-bounce-reason",
                       choices=["ungrounded_claim", "wrong", "style", "req_change"],
                       default=None,
                       help="Reason for the most recent Verify bounce")
    p_eff.set_defaults(func=cmd_log_effectiveness)

    # calculate-effectiveness
    p_calc_eff = sub.add_parser("calculate-effectiveness", help="Compute effectiveness metrics for closed cards")
    p_calc_eff.add_argument("--card", default=None, help="Optional card ID to calculate for")
    p_calc_eff.set_defaults(func=cmd_calculate_effectiveness)

    # sync-state
    p_sync = sub.add_parser("sync-state", help="Sync session telemetry from ~/.hermes/state.db")
    p_sync.add_argument("--state-db", default="~/.hermes/state.db", help="Path to state.db")
    p_sync.add_argument("--dry-run", action="store_true", help="Preview sync without writing")
    p_sync.set_defaults(func=cmd_sync_state)

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
