# Stella v2

Stella v2 is a privacy-first health intelligence platform that keeps health data local while exposing a modern ingestion, analytics, and chat workflow.

## What changed

- Unified file imports for Apple Health XML, Google Takeout JSON, Fitbit CSV bundles, Oura JSON, Garmin FIT, and manual CSV.
- DuckDB-backed normalized event storage plus daily overview and correlation materializations.
- Provider-swappable LLM gateway configured through `llm_config.yaml`.
- FastAPI v2 routes with JWT auth, import endpoint, overview analytics, report generation, and WebSocket chat.
- React + Vite frontend replacing the archived Streamlit dashboard at `archive/dashboard_v1.py`.

## Local run

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
```

## Architecture

The updated architecture diagram lives at `stella_v2_architecture.svg`.
