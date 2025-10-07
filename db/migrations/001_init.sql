CREATE TABLE IF NOT EXISTS deliveries (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(64) NOT NULL,
  yard_id VARCHAR(32) NOT NULL,
  route_id VARCHAR(32),
  promised_eta TIMESTAMP NOT NULL,
  actual_eta TIMESTAMP,
  status VARCHAR(24) NOT NULL,
  last_seen TIMESTAMP DEFAULT NOW(),
  UNIQUE(order_id)
);

CREATE TABLE IF NOT EXISTS alerts (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(64) NOT NULL,
  yard_id VARCHAR(32),
  route_id VARCHAR(32),
  lateness_min INTEGER NOT NULL,
  threshold_min INTEGER NOT NULL,
  reason TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sla_history (
  id SERIAL PRIMARY KEY,
  day DATE NOT NULL,
  yard_id VARCHAR(32),
  deliveries_total INT,
  on_time INT,
  late_15 INT,
  late_30 INT,
  p95_lateness_min INT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(day, yard_id)
);
