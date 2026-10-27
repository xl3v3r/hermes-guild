-- Guild Ledger (v1.3) — SQLite schema
-- Shaman publishes. Paladin reads cost. SotG interprets effectiveness.

PRAGMA journal_mode=WAL;

-- Cards (mirror of the Kanban board, supports guild & native Hermes column names)
CREATE TABLE IF NOT EXISTS cards (
  card_id      TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  swimlane     TEXT NOT NULL CHECK (swimlane IN ('keep','works','steward','watch')),
  owner_class  TEXT NOT NULL,
  assists      TEXT,               -- comma-separated class slugs
  source       TEXT,               -- you|bard|rogue|beastlord|enchanter|watch|other
  priority     TEXT,               -- now|next|later
  done_test    TEXT,
  constraints  TEXT,
  column       TEXT NOT NULL DEFAULT 'inbox'
               CHECK (column IN ('inbox','mission','ready','doing','verify','done','hold',
                                 'triage','todo','running','review','blocked')),
  opened_at    TEXT DEFAULT (datetime('now')),
  closed_at    TEXT
);

-- Attribution rows (one per spending session)
CREATE TABLE IF NOT EXISTS ledger_rows (
  row_id        INTEGER PRIMARY KEY AUTOINCREMENT,
  card_id       TEXT REFERENCES cards(card_id),
  group_name    TEXT NOT NULL CHECK (group_name IN ('keep','works','steward','watch')),
  class_slug    TEXT NOT NULL,
  role          TEXT NOT NULL CHECK (role IN ('owner','assistant','subagent')),
  parent_session TEXT,
  source        TEXT NOT NULL CHECK (source IN ('provider_usage','state_db','estimate','plugin')),
  api_calls     INTEGER DEFAULT 0,
  tool_calls    INTEGER DEFAULT 0,
  delegate_spawns INTEGER DEFAULT 0,
  failed_calls  INTEGER DEFAULT 0,
  tokens_in     INTEGER DEFAULT 0,
  tokens_out    INTEGER DEFAULT 0,
  tokens_cache_read  INTEGER DEFAULT 0,
  tokens_cache_write INTEGER DEFAULT 0,
  tokens_reasoning   INTEGER DEFAULT 0,
  cost_provider REAL,
  cost_estimate REAL,
  recorded_at   TEXT DEFAULT (datetime('now'))
);

-- Effectiveness (per card)
CREATE TABLE IF NOT EXISTS effectiveness (
  card_id           TEXT PRIMARY KEY REFERENCES cards(card_id),
  first_pass_accept INTEGER DEFAULT 0,
  rework_count      INTEGER DEFAULT 0,
  cycle_time_h      REAL,
  queue_time_h      REAL,
  blocked_time_h    REAL,
  done_test_met     INTEGER DEFAULT 0,
  incident_spawned  INTEGER DEFAULT 0,
  restore_proof_age_h REAL,
  tokens_per_accepted_card REAL,
  ungrounded_claims INTEGER DEFAULT 0,
  verify_bounce_reason TEXT
);

DROP VIEW IF EXISTS pulse;
CREATE VIEW IF NOT EXISTS pulse AS
WITH groups(group_name) AS (
  VALUES ('keep'), ('works'), ('steward'), ('watch')
),
card_stats AS (
  SELECT
    c.card_id,
    c.swimlane,
    c.column,
    e.first_pass_accept,
    e.cycle_time_h,
    e.rework_count,
    e.ungrounded_claims
  FROM cards c
  LEFT JOIN effectiveness e ON e.card_id = c.card_id
),
card_totals AS (
  SELECT
    swimlane AS group_name,
    COUNT(card_id) AS cards,
    SUM(CASE WHEN column IN ('doing','verify','running','review') THEN 1 ELSE 0 END) AS wip,
    SUM(CASE WHEN column IN ('done','archived') THEN 1 ELSE 0 END) AS accepted,
    ROUND(AVG(CASE WHEN first_pass_accept IS NOT NULL THEN first_pass_accept * 100.0 ELSE NULL END), 1) AS first_pass_rate,
    ROUND(AVG(cycle_time_h), 2) AS avg_cycle_time_h,
    COALESCE(SUM(rework_count), 0) AS total_rework,
    COALESCE(SUM(ungrounded_claims), 0) AS ungrounded_claims
  FROM card_stats
  GROUP BY swimlane
),
spend_totals AS (
  SELECT
    group_name,
    COALESCE(SUM(cost_provider), 0) AS cost_provider,
    COALESCE(SUM(tokens_in + tokens_out), 0) AS tokens
  FROM ledger_rows
  GROUP BY group_name
)
SELECT
  g.group_name,
  COALESCE(ct.cards, 0) AS cards,
  COALESCE(ct.wip, 0) AS wip,
  COALESCE(ct.accepted, 0) AS accepted,
  COALESCE(st.cost_provider, 0) AS cost_provider,
  COALESCE(st.tokens, 0) AS tokens,
  ct.first_pass_rate,
  ct.avg_cycle_time_h,
  COALESCE(ct.total_rework, 0) AS total_rework,
  COALESCE(ct.ungrounded_claims, 0) AS ungrounded_claims
FROM groups g
LEFT JOIN card_totals ct ON ct.group_name = g.group_name
LEFT JOIN spend_totals st ON st.group_name = g.group_name;

CREATE VIEW IF NOT EXISTS untagged AS
SELECT * FROM ledger_rows WHERE card_id IS NULL;
