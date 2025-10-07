CREATE TABLE IF NOT EXISTS delay_causes (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(64) NOT NULL,
  label VARCHAR(64) NOT NULL,
  confidence NUMERIC(4,3) NOT NULL,
  model_version VARCHAR(64) NOT NULL,
  note_excerpt TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_delay_causes_order ON delay_causes(order_id);
