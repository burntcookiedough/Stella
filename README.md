# Stella v2

Stella v2 is a privacy-first health intelligence platform that keeps health data local while exposing a modern ingestion, analytics, and chat workflow.

## What changed

- Unified file imports for Apple Health XML, Google Takeout JSON, Fitbit CSV bundles, Oura JSON, Garmin FIT, and manual CSV.
- DuckDB-backed normalized event storage plus daily overview and correlation materializations.
- Provider-swappable LLM gateway configured through `llm_config.yaml`.
- FastAPI v2 routes with JWT auth, import endpoint, overview analytics, report generation, and WebSocket chat.
- React + Vite frontend replacing the archived Streamlit dashboard at `archive/dashboard_v1.py`.

## Local run

### One-click startup

Double-click `run_stella.bat` from the repo root. It will:

- verify Python and frontend dependencies
- start the FastAPI backend on `http://127.0.0.1:8000`
- start the Vite frontend on `http://127.0.0.1:5173`
- open the app in your browser once both services are reachable

If you want to launch without checking Ollama first, set `STELLA_SKIP_OLLAMA=1` before running the script.

### Backend

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

The backend bootstraps the sample Fitbit files in `data/raw/` if the DuckDB store is empty.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The default frontend origin is `http://127.0.0.1:5173`. Default credentials are `stella / stella` unless overridden with env vars.

## Docker

```bash
docker compose up --build
```

Use the optional Ollama sidecar with:

```bash
docker compose --profile local-llm up --build
```

## Tests

```bash
pytest
cd frontend && npm run test
cd frontend && npm run test:e2e
```

## CI

GitHub Actions now validates the same surface as local development:

- `ruff check .`
- `pytest`
- `npm ci`
- `npm run test`
- `npm run build`
- `npm run test:e2e`
- backend and frontend Docker image builds

## Product direction

The near-term path to a standalone Stella product is:

1. Stabilize local-first runtime: imports, analytics, chat, report generation, launcher, and health checks.
2. Lock CI to the real critical path: lint, backend tests, frontend tests, browser E2E, and container builds.
3. Package the app for non-technical users: Docker-first distribution, then a desktop wrapper or installer once the runtime is stable enough.
4. Harden product boundaries: account setup, persistent user data directories, backups, structured error reporting, and upgrade-safe configuration.
5. Add release discipline: tagged builds, changelog, smoke tests, and signed distributables.

## Architecture

The updated architecture diagram lives at `stella_v2_architecture.svg`.
