CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status);
CREATE INDEX IF NOT EXISTS idx_alerts_order ON alerts(order_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_yard_day ON deliveries(yard_id, promised_eta);
