CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE IF NOT EXISTS core.machines (
  machine_id DECIMAL(9,0), name VARCHAR(50)
);
CREATE TABLE IF NOT EXISTS core.sensor_readings (
  machine_id DECIMAL(9,0), sensor VARCHAR(50),
  event_ts TIMESTAMP, arrival_ts TIMESTAMP, val DOUBLE
);
CREATE TABLE IF NOT EXISTS core.downtime_events (
  event_id DECIMAL(9,0), machine_id DECIMAL(9,0),
  start_ts TIMESTAMP, duration_min DECIMAL(9,0)
);
CREATE TABLE IF NOT EXISTS core.maintenance_events (
  machine_id DECIMAL(9,0), event_ts TIMESTAMP, description VARCHAR(200)
);
CREATE TABLE IF NOT EXISTS core.spare_parts (
  part VARCHAR(50), site VARCHAR(50),
  on_hand DECIMAL(9,0), demand_14d DECIMAL(9,0), min_level DECIMAL(9,0)
);
CREATE TABLE IF NOT EXISTS core.qc_spec (mu DOUBLE, sigma DOUBLE);
CREATE TABLE IF NOT EXISTS core.qc_batches (
  batch_id VARCHAR(20), description VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS core.qc_measurements (
  batch_id VARCHAR(20), station DECIMAL(3,0), val DOUBLE
);
CREATE TABLE IF NOT EXISTS core.supplier_shipments (
  supplier_id VARCHAR(50), part_id VARCHAR(50), qty DECIMAL(12,0),
  ship_date DATE, unit_cost_usd DOUBLE
);
