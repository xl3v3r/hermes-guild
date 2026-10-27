#!/usr/bin/env python3
"""Bard Outlook / Inbound Mail Probe (v1.3).

Lightweight monitor probe for Hermes Agent cron (--monitor-script).
Checks for new unread communications without consuming LLM tokens.
Output is strictly deterministic and timestamp-free: unchanged output
suppresses agent turns; changed output triggers an agent triage run.
"""

import json
import os
import shutil
import subprocess
import sys


def check_composio_outlook():
    """Attempt checking Composio Outlook if CLI and credentials are available."""
    if not shutil.which("composio"):
        return None
    try:
        # Check unread messages via composio CLI
        res = subprocess.run(
            ["composio", "run", "outlook_list_messages", "--query", "isRead:false"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            msgs = data.get("messages", [])
            return msgs
    except Exception:
        pass
    return None


def check_inbox_file():
    """Check local file inbox or mock inbox at ~/.hermes/mail_inbox.json if present."""
    inbox_path = os.path.expanduser("~/.hermes/mail_inbox.json")
    if os.path.exists(inbox_path):
        try:
            with open(inbox_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("messages", [])
        except Exception:
            pass
    return None


def main():
    msgs = check_composio_outlook()
    if msgs is None:
        msgs = check_inbox_file()

    if not msgs:
        # Stable zero-mail output — suppresses agent wakeups
        print("INBOX_STATUS: UNREAD=0")
        return

    # Deterministic output of unread messages (sorted by ID, no timestamps)
    print(f"INBOX_STATUS: UNREAD={len(msgs)}")
    for m in sorted(msgs, key=lambda x: str(x.get("id", ""))):
        sender = m.get("sender") or m.get("from") or "unknown"
        subject = m.get("subject") or "No Subject"
        mid = m.get("id") or "no-id"
        print(f"- MSG_ID: {mid} | FROM: {sender} | SUBJ: {subject}")


if __name__ == "__main__":
    main()
