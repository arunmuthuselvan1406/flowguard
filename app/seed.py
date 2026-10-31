"""Create the schema and views on Exasol, then load deterministic SYNTHETIC data.

Run:  python -m app.seed
"""
import pathlib
import random
from datetime import datetime, timedelta

from .db import connect

SQL_DIR = pathlib.Path(__file__).resolve().parent.parent / "sql"
random.seed(42)

START, END = datetime(2026, 10, 25), datetime(2026, 10, 31)
STEP = timedelta(minutes=10)

SENSORS = {  # sensor: (normal mean, normal std-dev)
    "bearing_temp": (70, 2.0), "vibration": (1.2, 0.15), "motor_current": (12, 0.5),
    "oil_pressure": (5.5, 0.2), "line_speed": (1.0, 0.03), "coolant_flow": (8, 0.4),
    "belt_tension": (250, 6), "spindle_load": (55, 3),
}
MACHINES = {
    1: ("Press-07", ["bearing_temp", "vibration", "motor_current", "oil_pressure", "line_speed"]),
    2: ("CNC-12", ["spindle_load", "coolant_flow", "vibration", "bearing_temp", "line_speed"]),
    3: ("Conveyor-03", ["motor_current", "belt_tension", "vibration", "line_speed", "bearing_temp"]),
}
# event_id, machine_id, start, minutes, injected deviation (in sigma) before the stop
DOWNTIME = [
    (1, 1, datetime(2026, 10, 28, 2, 14), 45,
     {"bearing_temp": 4.8, "vibration": 3.1, "motor_current": 1.2, "oil_pressure": -0.6}),
    (2, 2, datetime(2026, 10, 29, 14, 40), 30,
     {"coolant_flow": -4.2, "bearing_temp": 2.0, "spindle_load": 1.1}),
    (3, 3, datetime(2026, 10, 30, 6, 5), 50,
     {"motor_current": 3.6, "belt_tension": -2.9, "vibration": 1.5}),
]
MAINTENANCE = [
    (1, datetime(2026, 10, 25, 2, 0), "Bearings from supplier lot L-4471 installed"),
    (1, datetime(2026, 10, 27, 20, 0), "Tool change"),
    (2, datetime(2026, 10, 20, 9, 0), "Coolant filter service overdue by 9 days"),
    (3, datetime(2026, 10, 18, 11, 0), "Belt replaced"),
]
PARTS = {
    "Bearing 6204": [("Chennai", 40, 14, 10), ("Pune", 6, 18, 8), ("Hosur", 22, 6, 8), ("Coimbatore", 3, 9, 6)],
    "Hydraulic seal H9": [("Chennai", 4, 10, 6), ("Pune", 30, 5, 8), ("Hosur", 12, 4, 5), ("Coimbatore", 25, 6, 6)],
    "Servo drive S2": [("Chennai", 9, 4, 3), ("Pune", 2, 6, 3), ("Hosur", 14, 3, 3), ("Coimbatore", 5, 5, 3)],
}
QC = {
    "A-118": ("drift at station 4", [10.0, 10.1, 9.9, 10.9, 11.4, 11.9, 12.3, 12.6, 12.9]),
    "A-119": ("healthy", [10.0, 9.9, 10.1, 10.0, 10.2, 9.9, 10.1, 10.0, 10.1]),
    "A-120": ("sudden shift at 6", [10.1, 10.0, 9.9, 10.1, 10.0, 11.8, 12.0, 11.9, 12.1]),
}


def run_sql_file(c, name):
    text = (SQL_DIR / name).read_text()
    for stmt in text.split(";"):
        body = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--")).strip()
        if body:
            c.execute(body)


def sensor_rows():
    rows = []
    for mid, (_, sensors) in MACHINES.items():
        t = START
        while t < END:
            for s in sensors:
                mu, sd = SENSORS[s]
                val = random.gauss(mu, sd)
                for _, dm, start, mins, z in DOWNTIME:
                    if dm != mid:
                        continue
                    if start - timedelta(minutes=60) <= t <= start:
                        ramp = 0.5 + 0.5 * (t - (start - timedelta(minutes=60))) / timedelta(minutes=60)
                        val += z.get(s, 0) / 0.75 * sd * ramp   # window average = z sigma
                    if start < t < start + timedelta(minutes=mins):
                        val = None                              # machine is down: no reading
                if val is not None:
                    arrival = t + timedelta(minutes=random.choice([0, 0, 1, 3, 12, 25]))  # late data
                    rows.append((mid, s, t, arrival, round(val, 4)))
            t += STEP
    return rows


def main():
    c = connect()
    run_sql_file(c, "01_schema.sql")
    for tbl in ["machines", "sensor_readings", "downtime_events", "maintenance_events",
                "spare_parts", "qc_spec", "qc_batches", "qc_measurements", "supplier_shipments"]:
        c.execute(f"TRUNCATE TABLE core.{tbl}")
    run_sql_file(c, "02_views.sql")

    c.import_from_iterable([(m, v[0]) for m, v in MACHINES.items()], ("CORE", "MACHINES"))
    readings = sensor_rows()
    c.import_from_iterable(readings, ("CORE", "SENSOR_READINGS"))
    c.import_from_iterable([(e, m, s, mins) for e, m, s, mins, _ in DOWNTIME], ("CORE", "DOWNTIME_EVENTS"))
    c.import_from_iterable(MAINTENANCE, ("CORE", "MAINTENANCE_EVENTS"))
    c.import_from_iterable([(p, *r) for p, rs in PARTS.items() for r in rs], ("CORE", "SPARE_PARTS"))
    c.import_from_iterable([(10.0, 0.45)], ("CORE", "QC_SPEC"))
    c.import_from_iterable([(b, d) for b, (d, _) in QC.items()], ("CORE", "QC_BATCHES"))
    c.import_from_iterable([(b, i + 1, v) for b, (_, vs) in QC.items() for i, v in enumerate(vs)],
                           ("CORE", "QC_MEASUREMENTS"))
    print(f"Loaded {len(readings)} sensor readings, {len(DOWNTIME)} stoppages, "
          f"{sum(len(v) for v in PARTS.values())} stock rows, {len(QC)} QC batches.")


if __name__ == "__main__":
    main()
