#!/usr/bin/env python3
"""Hermes Guild Kanban Synchronizer (v1.3).

Provides bi-directional synchronization between Hermes Agent's native SQLite
Kanban engine (~/.hermes/kanban/boards/guild/kanban.db or ~/.hermes/kanban.db)
and the Guild Ledger database (guild.sqlite), plus live Markdown export to board/kanban.md.
"""

import argparse
from datetime import datetime, timezone
import os
import sqlite3
import sys

# Status translation mappings
HERMES_TO_GUILD_STATUS = {
    "triage": "inbox",
    "todo": "mission",
    "ready": "ready",
    "running": "doing",
    "review": "verify",
    "blocked": "hold",
    "scheduled": "hold",
    "done": "done",
    "archived": "done",
}

GUILD_TO_HERMES_STATUS = {
    "inbox": "triage",
    "mission": "todo",
    "ready": "ready",
    "doing": "running",
    "verify": "review",
    "hold": "blocked",
    "done": "done",
}

CLASS_GROUPS = {
    "warrior": "keep", "beastlord": "keep", "necromancer": "keep", "shaman": "keep", "warden": "keep",
    "wizard": "works", "druid": "works", "monk": "works", "ranger": "works", "master-of-works": "works",
    "magician": "steward", "bard": "steward", "enchanter": "steward", "paladin": "steward", "steward": "steward",
    "rogue": "watch", "shadowknight": "watch", "berserker": "watch", "cleric": "watch", "captain": "watch",
    "sotg": "steward",
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resolve_kanban_db(explicit_path=None, board="guild"):
    if explicit_path:
        return os.path.expanduser(explicit_path)
    env_db = os.environ.get("HERMES_KANBAN_DB")
    if env_db and os.path.exists(os.path.expanduser(env_db)):
        return os.path.expanduser(env_db)
    # Check board path
    board_db = os.path.expanduser(f"~/.hermes/kanban/boards/{board}/kanban.db")
    if os.path.exists(board_db):
        return board_db
    # Check default board
    default_db = os.path.expanduser("~/.hermes/kanban.db")
    if os.path.exists(default_db):
        return default_db
    # Fallback to board path even if not yet initialized
    return board_db


def resolve_guild_db(explicit_path=None):
    if explicit_path:
        return os.path.expanduser(explicit_path)
    env_db = os.environ.get("HERMES_GUILD_DB")
    if env_db and os.path.exists(os.path.expanduser(env_db)):
        return os.path.expanduser(env_db)
    repo = os.environ.get("GUILD_REPO")
    if repo:
        cand = os.path.join(os.path.expanduser(repo), "ledger", "guild.sqlite")
        if os.path.exists(cand):
            return cand
    candidates = [
        os.path.join(ROOT, "ledger", "guild.sqlite"),
        os.path.expanduser("~/guild/ledger/guild.sqlite"),
        os.path.join(os.getcwd(), "ledger", "guild.sqlite"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return os.path.expanduser("~/guild/ledger/guild.sqlite")


def resolve_board_md(explicit_path=None):
    if explicit_path:
        return os.path.expanduser(explicit_path)
    repo = os.environ.get("GUILD_REPO")
    if repo:
        cand = os.path.join(os.path.expanduser(repo), "board", "kanban.md")
        if os.path.exists(cand):
            return cand
    candidates = [
        os.path.join(ROOT, "board", "kanban.md"),
        os.path.expanduser("~/guild/board/kanban.md"),
        os.path.join(os.getcwd(), "board", "kanban.md"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return os.path.expanduser("~/guild/board/kanban.md")


def format_ts(epoch):
    if not epoch:
        return None
    try:
        return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def export_markdown(guild_conn, board_md_path):
    """Render board/kanban.md from current cards table."""
    cur = guild_conn.execute(
        """
        SELECT card_id, title, swimlane, owner_class, assists, source, priority, done_test, constraints, column, opened_at, closed_at
        FROM cards
        ORDER BY opened_at ASC
        """
    )
    cards = [dict(r) for r in cur.fetchall()]

    lines = []
    lines.append("# Guild Kanban (v1.3)")
    lines.append("")
    lines.append("One board. Four swimlanes. One owner per card.")
    lines.append("")
    lines.append("Columns: `Inbox → Mission → Ready → Doing → Verify → Done`, with `Hold / Blocked`.")
    lines.append("Native Hermes Agent mappings: `triage → todo → ready → running → review → done` (`blocked`).")
    lines.append("")
    lines.append("## Swimlanes")
    lines.append("")
    lines.append("- **Keep** — Infrastructure & Data (Warden of the Keep)")
    lines.append("- **Works** — Web & Experience (Master of Works)")
    lines.append("- **Steward** — Operations & Governance (Steward of the Guild)")
    lines.append("- **Watch** — Security & Response (Captain of the Watch)")
    lines.append("")
    lines.append("## Card template")
    lines.append("")
    lines.append("```text")
    lines.append("card_id:  <short id>")
    lines.append("title:    <outcome>")
    lines.append("swimlane: keep | works | steward | watch")
    lines.append("owner:    <class>")
    lines.append("assists:  <optional, named>")
    lines.append("source:   you | bard | rogue | beastlord | enchanter | watch | other")
    lines.append("priority: now | next | later")
    lines.append("done:     <definition of done — observable artifact + who verifies it>")
    lines.append("constraints: <change window, legal, budget, no-prod, ...>")
    lines.append("```")
    lines.append("")
    lines.append("Before Verify, a card must carry: evidence links and a ledger tag")
    lines.append("(sessions, API calls, tool calls, tokens in/out, cost signal, result).")
    lines.append("")
    lines.append("Every claim must trace to a tool result, file, URL, or DB row; an")
    lines.append("ungrounded claim bounces with reason `ungrounded_claim` (see CHARTER §15).")
    lines.append("")
    lines.append("## WIP limits")
    lines.append("")
    lines.append("| Scope | Cap | Active (Doing/Verify) |")
    lines.append("|---|---|---|")

    # Calculate active WIP counts
    swimlanes = ["keep", "works", "steward", "watch"]
    wip_by_lane = {lane: 0 for lane in swimlanes}
    for c in cards:
        lane = c["swimlane"]
        col = c["column"]
        if col in ("doing", "verify", "running", "review") and lane in wip_by_lane:
            wip_by_lane[lane] += 1

    total_wip = sum(wip_by_lane.values())
    lines.append(f"| Group: Keep | 3 Doing + Verify | {wip_by_lane['keep']}/3 |")
    lines.append(f"| Group: Works | 3 Doing + Verify | {wip_by_lane['works']}/3 |")
    lines.append(f"| Group: Steward | 3 Doing + Verify | {wip_by_lane['steward']}/3 |")
    lines.append(f"| Group: Watch | 3 Doing + Verify | {wip_by_lane['watch']}/3 |")
    lines.append(f"| Guild Total | 8 Doing + Verify | {total_wip}/8 |")
    lines.append("| Class Owner | 1 Doing, 1 Verify | Per-class enforcement |")
    lines.append("")
    lines.append("Aging: Enchanter flags Doing > 48h and Verify > 24h.")
    lines.append("")

    lines.append("## Current Board")
    lines.append("")

    for lane in swimlanes:
        lane_title = lane.capitalize()
        lines.append(f"### {lane_title}")
        lane_cards = [c for c in cards if c["swimlane"] == lane]
        if not lane_cards:
            lines.append("*(No active cards)*")
            lines.append("")
            continue

        for c in lane_cards:
            check = "x" if c["column"] in ("done", "closed") else " "
            col_display = c["column"].upper()
            owner = c["owner_class"] or "unassigned"
            lines.append(f"- [{check}] **[{c['card_id']}]** {c['title']} — *{owner}* (`{col_display}`)")
        lines.append("")

    lines.append("---")
    lines.append(f"*Last synchronized: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} via `sync_kanban.py`*")
    lines.append("")

    os.makedirs(os.path.dirname(os.path.abspath(board_md_path)), exist_ok=True)
    with open(board_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def sync(kanban_db_path, guild_db_path, board_md_path, dry_run=False):
    print(f"Kanban DB: {kanban_db_path}")
    print(f"Guild DB:  {guild_db_path}")
    print(f"Board MD:  {board_md_path}")

    # Ensure guild DB schema
    os.makedirs(os.path.dirname(os.path.abspath(guild_db_path)), exist_ok=True)
    g_conn = sqlite3.connect(guild_db_path)
    g_conn.row_factory = sqlite3.Row
    g_conn.execute("PRAGMA foreign_keys = ON")
    schema_path = os.path.join(ROOT, "ledger", "schema.sql")
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            g_conn.executescript(f.read())

    # Check if native kanban DB exists
    k_conn = None
    if os.path.exists(kanban_db_path):
        k_conn = sqlite3.connect(kanban_db_path)
        k_conn.row_factory = sqlite3.Row

    hermes_tasks = []
    if k_conn:
        try:
            k_cur = k_conn.execute("SELECT id, title, body, assignee, status, created_at, completed_at FROM tasks")
            hermes_tasks = [dict(r) for r in k_cur.fetchall()]
        except sqlite3.OperationalError:
            hermes_tasks = []

    # Map hermes tasks into guild cards
    hermes_ids = {t["id"]: t for t in hermes_tasks}
    synced_to_guild = 0
    synced_to_hermes = 0

    if hermes_tasks:
        for t in hermes_tasks:
            cid = t["id"]
            title = t["title"]
            assignee = (t["assignee"] or "sotg").lower()
            owner_class = assignee if assignee in CLASS_GROUPS else "sotg"
            swimlane = CLASS_GROUPS.get(owner_class, "keep")
            guild_col = HERMES_TO_GUILD_STATUS.get(t["status"], "inbox")
            opened_at = format_ts(t.get("created_at"))
            closed_at = format_ts(t.get("completed_at"))

            if not dry_run:
                with g_conn:
                    g_conn.execute(
                        """
                        INSERT INTO cards (card_id, title, swimlane, owner_class, column, opened_at, closed_at)
                        VALUES (?, ?, ?, ?, ?, coalesce(?, datetime('now')), ?)
                        ON CONFLICT(card_id) DO UPDATE SET
                            title = excluded.title,
                            swimlane = excluded.swimlane,
                            owner_class = excluded.owner_class,
                            column = excluded.column,
                            closed_at = coalesce(excluded.closed_at, cards.closed_at)
                        """,
                        (cid, title, swimlane, owner_class, guild_col, opened_at, closed_at),
                    )
            synced_to_guild += 1

    # Check guild cards to sync back to Hermes tasks if missing or completed
    cur = g_conn.execute("SELECT card_id, title, swimlane, owner_class, column, opened_at, closed_at FROM cards")
    guild_cards = [dict(r) for r in cur.fetchall()]

    if k_conn and not dry_run:
        for c in guild_cards:
            cid = c["card_id"]
            h_status = GUILD_TO_HERMES_STATUS.get(c["column"], "todo")
            now_epoch = int(datetime.now(timezone.utc).timestamp())
            assignee = c["owner_class"]

            if cid not in hermes_ids:
                try:
                    with k_conn:
                        k_conn.execute(
                            """
                            INSERT INTO tasks (id, title, assignee, status, created_at, completed_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (cid, c["title"], assignee, h_status, now_epoch, now_epoch if c["column"] in ("done", "closed") else None),
                        )
                    synced_to_hermes += 1
                except sqlite3.OperationalError:
                    pass
            elif c["column"] in ("done", "closed") and hermes_ids[cid]["status"] != "done":
                try:
                    with k_conn:
                        k_conn.execute(
                            "UPDATE tasks SET status = 'done', completed_at = coalesce(completed_at, ?) WHERE id = ?",
                            (now_epoch, cid),
                        )
                    synced_to_hermes += 1
                except sqlite3.OperationalError:
                    pass

    # Export to board/kanban.md
    if not dry_run:
        export_markdown(g_conn, board_md_path)

    dry_prefix = "[DRY-RUN] " if dry_run else ""
    print(f"{dry_prefix}Sync complete: {synced_to_guild} tasks synced Hermes -> Guild, {synced_to_hermes} synced Guild -> Hermes.")
    print(f"{dry_prefix}Updated Markdown view at {board_md_path}")


def main():
    parser = argparse.ArgumentParser(description="Guild Kanban Synchronizer (v1.3)")
    parser.add_argument("--kanban-db", default=None, help="Path to Hermes kanban.db")
    parser.add_argument("--guild-db", default=None, help="Path to guild.sqlite")
    parser.add_argument("--board-md", default=None, help="Path to kanban.md")
    parser.add_argument("--board", default="guild", help="Kanban board slug (default: guild)")
    parser.add_argument("--dry-run", action="store_true", help="Preview sync without writing")
    parser.add_argument("--export-only", action="store_true", help="Only refresh board/kanban.md")
    args = parser.parse_args()

    k_db = resolve_kanban_db(args.kanban_db, args.board)
    g_db = resolve_guild_db(args.guild_db)
    b_md = resolve_board_md(args.board_md)

    if args.export_only:
        os.makedirs(os.path.dirname(os.path.abspath(g_db)), exist_ok=True)
        g_conn = sqlite3.connect(g_db)
        g_conn.row_factory = sqlite3.Row
        export_markdown(g_conn, b_md)
        print(f"Exported Markdown view to {b_md}")
        return

    sync(k_db, g_db, b_md, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
