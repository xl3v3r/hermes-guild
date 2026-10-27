#!/usr/bin/env python3
"""Shaman Pulse Publisher (v1.3).

Deterministic pulse report publisher for Hermes Agent cron (--no-agent).
Compiles and prints the Guild Ledger pulse dashboard directly without LLM tokens.
"""

import os
import sqlite3
import sys

DEFAULT_DB_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ledger", "guild.sqlite"),
    os.path.expanduser("~/guild/ledger/guild.sqlite"),
]


def find_db():
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


def main():
    db_path = find_db()
    if not os.path.exists(db_path):
        print(f"Ledger database not found at {db_path}. Run install.sh first.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cur = conn.execute("SELECT * FROM pulse")
    rows = cur.fetchall()

    fmt_header = f"{'GROUP':<10} | {'CARDS':<5} | {'WIP':<4} | {'DONE':<5} | {'COST ($)':<9} | {'TOKENS':<10} | {'PASS %':<6} | {'CYCLE (h)':<9} | {'REWORK':<6}"
    sep = "=" * len(fmt_header)
    div = "-" * len(fmt_header)

    print("=== Hermes Guild Pulse Report (Shaman) ===")
    print(sep)
    print(fmt_header)
    print(div)

    total_cards = total_wip = total_accepted = total_tokens = total_rework = 0
    total_cost = 0.0
    pass_rates = []
    cycle_times = []

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
        if pass_rate is not None:
            pass_rates.append(pass_rate)
        if cycle_h is not None:
            cycle_times.append(cycle_h)

        print(
            f"{r['group_name']:<10} | {cards:<5} | {wip:<4} | {accepted:<5} | ${cost:<8.4f} | {tokens:<10,d} | {pass_str:<6} | {cycle_str:<9} | {rework:<6}"
        )

    print(div)
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


if __name__ == "__main__":
    main()
