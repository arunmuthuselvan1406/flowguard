-- Normal behaviour per machine and sensor, excluding the 60 minutes before any stoppage
CREATE OR REPLACE VIEW core.baseline AS
SELECT r.machine_id, r.sensor, AVG(r.val) AS mu, STDDEV(r.val) AS sd
FROM core.sensor_readings r
WHERE NOT EXISTS (
  SELECT 1 FROM core.downtime_events d
  WHERE d.machine_id = r.machine_id
    AND r.event_ts BETWEEN ADD_MINUTES(d.start_ts, -60) AND d.start_ts
)
GROUP BY r.machine_id, r.sensor;

-- RootCause: z-score of each sensor in the 60 minutes before a stoppage
CREATE OR REPLACE VIEW core.v_rootcause_z AS
SELECT d.event_id, r.sensor,
       (AVG(r.val) - b.mu) / NULLIF(b.sd, 0) AS z_score
FROM core.downtime_events d
JOIN core.sensor_readings r
  ON r.machine_id = d.machine_id
 AND r.event_ts BETWEEN ADD_MINUTES(d.start_ts, -60) AND d.start_ts
JOIN core.baseline b ON b.machine_id = r.machine_id AND b.sensor = r.sensor
GROUP BY d.event_id, r.sensor, b.mu, b.sd;

-- PartsBalancer: surplus = on hand - expected 14-day demand - minimum level
CREATE OR REPLACE VIEW core.v_parts_surplus AS
SELECT part, site, on_hand, demand_14d, min_level,
       on_hand - demand_14d - min_level AS surplus
FROM core.spare_parts;

-- EarlyCatch: flag measurements outside mean +/- 3 sigma
CREATE OR REPLACE VIEW core.v_qc_flags AS
SELECT q.batch_id, q.station, q.val,
       CASE WHEN q.val > s.mu + 3 * s.sigma OR q.val < s.mu - 3 * s.sigma
            THEN 1 ELSE 0 END AS out_of_control
FROM core.qc_measurements q CROSS JOIN core.qc_spec s;
