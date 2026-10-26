# Guild Kanban

One board. Four swimlanes. One owner per card.

Columns: `Inbox → Mission → Ready → Doing → Verify → Done`, with `Hold`.

## Swimlanes

- **Keep** — Infrastructure & Data (Warden of the Keep)
- **Works** — Web & Experience (Master of Works)
- **Steward** — Operations & Governance (Steward of the Guild)
- **Watch** — Security & Response (Captain of the Watch)

## Card template

```text
card_id:  <short id>
title:    <outcome>
swimlane: keep | works | steward | watch
owner:    <class>
assists:  <optional, named>
source:   you | bard | rogue | beastlord | enchanter | watch | other
priority: now | next | later
done:     <definition of done — observable artifact + who verifies it>
constraints: <change window, legal, budget, no-prod, ...>
```

Before Verify, a card must carry: evidence links and a ledger tag
(sessions, API calls, tool calls, tokens in/out, cost signal, result).

Every claim must trace to a tool result, file, URL, or DB row; an
ungrounded claim bounces with reason `ungrounded_claim` (see CHARTER §15).

## WIP limits

| Scope | Cap |
|---|---|
| Class owner | 1 Doing, 1 Verify |
| Group swimlane | 3 Doing + Verify |
| Guild | 8 Doing + Verify |
| Cross-group orchestrated | 1 |
| Watch severity-1 | waived until contained |

Aging: Enchanter flags Doing > 48h and Verify > 24h.

## Current board

<!-- Move cards here. Example:
### Keep
- [ ] card_id — title (owner, Doing)
### Works
### Steward
### Watch
-->
