-- Guild Ledger (v1.2) — SQLite schema
-- Shaman publishes. Paladin reads cost. SotG interprets effectiveness.

PRAGMA journal_mode=WAL;

-- Cards (mirror of the Kanban board)
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
               CHECK (column IN ('inbox','mission','ready','doing','verify','done','hold')),
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

-- Views
CREATE VIEW IF NOT EXISTS pulse AS
SELECT c.swimlane AS group_name,
       COUNT(DISTINCT c.card_id) AS cards,
       SUM(CASE WHEN c.column IN ('doing','verify') THEN 1 ELSE 0 END) AS wip,
       SUM(CASE WHEN c.column = 'done' THEN 1 ELSE 0 END) AS accepted,
       COALESCE(SUM(l.cost_provider), 0) AS cost_provider,
       COALESCE(SUM(l.tokens_in + l.tokens_out), 0) AS tokens
FROM cards c
LEFT JOIN ledger_rows l ON l.card_id = c.card_id
GROUP BY c.swimlane;

CREATE VIEW IF NOT EXISTS untagged AS
SELECT * FROM ledger_rows WHERE card_id IS NULL;
