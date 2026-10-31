# Deployment and run guide

## 1. Exasol Personal
Deploy Exasol Personal by following Exasol's own instructions. Note the host, port (8563 by default), user and password
it gives you and put them in `.env` (copy from `.env.example`).

## 2. Application
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed                       # one-time (or to reset data)
uvicorn app.api:app --host 0.0.0.0 --port 8000
```

## 3. Hosting the app
Any machine that can reach Exasol on port 8563 works (laptop, VM, container). The API serves the dashboard too,
so there is a single process and a single port to expose.

## 4. Troubleshooting
| Symptom | Fix |
|---|---|
| Dashboard says "simulated data" | The API cannot reach Exasol. Check `/api/health` and your `.env` |
| Certificate error | Keep `EXASOL_VERIFY_CERT=false` for a self-signed certificate |
| `KeyError: EXASOL_PASSWORD` | `.env` is missing or not in the project root |
