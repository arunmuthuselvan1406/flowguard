"""FastAPI layer. Every endpoint is a thin wrapper around SQL that runs inside Exasol.

Run:  uvicorn app.api:app --port 8000
"""
import pathlib
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db import connect

app = FastAPI(title="FlowGuard")
WEB = pathlib.Path(__file__).resolve().parent.parent / "web"


def ago(d):
    return f"{d.days} days" if d.days >= 1 else f"{d.seconds // 3600} h"


def query(fn):
    """Run fn(connection); turn any database failure into a 503 so the UI can fall back."""
    try:
        c = connect()
        try:
            return fn(c)
        finally:
            c.close()
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Exasol unavailable: {e}")


@app.get("/api/health")
def health():
    return query(lambda c: {"ok": c.execute("SELECT 1").fetchval() == 1})


@app.get("/api/rootcause")
def rootcause():
    def run(c):
        events = c.execute(
            "SELECT d.event_id, d.machine_id, m.name, d.start_ts FROM core.downtime_events d "
            "JOIN core.machines m ON m.machine_id = d.machine_id ORDER BY d.start_ts"
        ).fetchall()
        out = []
        for eid, mid, name, ts in events:
            z = {s: round(float(v), 1) for s, v in c.execute(
                "SELECT sensor, z_score FROM core.v_rootcause_z WHERE event_id = {eid}",
                {"eid": eid}).fetchall() if v is not None}
            maint = c.execute(
                "SELECT description, event_ts FROM core.maintenance_events "
                "WHERE machine_id = {mid} AND event_ts <= {ts} AND event_ts >= {since} ORDER BY event_ts DESC",
                {"mid": mid, "ts": ts, "since": ts - timedelta(days=14)}).fetchall()
            co = [[f"{d} ({ago(ts - t)} earlier)", 1] for d, t in maint]
            top = max(z.items(), key=lambda kv: abs(kv[1]))
            why = (f"{top[0]} was {abs(top[1]):.1f}σ {'above' if top[1] > 0 else 'below'} its baseline "
                   f"in the hour before the stop."
                   + (" Recent events: " + "; ".join(f"{d.lower()} ({ago(ts - t)} earlier)" for d, t in maint) + "." if maint else ""))
            out.append({"name": f"{name} · {ts:%b %d %H:%M}", "z": z, "co": co, "why": why})
        return out
    return query(run)


@app.get("/api/parts")
def parts():
    def run(c):
        out = {}
        for part, site, oh, dem, mn in c.execute(
                "SELECT part, site, on_hand, demand_14d, min_level FROM core.v_parts_surplus ORDER BY part, site"):
            out.setdefault(part, []).append([site, int(oh), int(dem), int(mn)])
        return out
    return query(run)


@app.get("/api/earlycatch")
def earlycatch():
    def run(c):
        mu, sigma = c.execute("SELECT mu, sigma FROM core.qc_spec").fetchone()
        desc = dict(c.execute("SELECT batch_id, description FROM core.qc_batches").fetchall())
        batches = {}
        for b, _, v in c.execute("SELECT batch_id, station, val FROM core.v_qc_flags ORDER BY batch_id, station"):
            batches.setdefault(f"Batch {b} ({desc.get(b, '')})", []).append(float(v))
        return {"mu": float(mu), "sigma": float(sigma), "batches": batches}
    return query(run)


class Shipment(BaseModel):
    supplier_id: str
    part_id: str
    qty: float
    ship_date: str  # YYYY-MM-DD (already normalised by the mapping step)
    unit_cost_usd: float


@app.post("/api/suppliers/load")
def load_shipments(rows: list[Shipment]):
    data = [(r.supplier_id, r.part_id, int(r.qty),
             datetime.strptime(r.ship_date, "%Y-%m-%d").date(), r.unit_cost_usd) for r in rows]
    return query(lambda c: (c.import_from_iterable(data, ("CORE", "SUPPLIER_SHIPMENTS")), {"loaded": len(data)})[1])


# Serve the dashboard from the same process (must be mounted last)
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")
