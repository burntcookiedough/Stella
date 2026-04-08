# Stella

Stella is a single-user local-first health analytics app.

Supported product surface:

- FastAPI backend
- React + Vite frontend
- DuckDB local storage
- Ollama-backed LLM integration with supported metrics-only fallback
- `run_stella_docker.bat` as the canonical install path
- `run_stella.bat` as the supported local development path

Legacy code is isolated under `archive/` and `tools/legacy/`. It is not part of the active product runtime.

## Supported startup paths

### Docker-first install path

Double-click `run_stella_docker.bat`.

What it does:

- verifies Docker Desktop and `docker compose`
- creates `.env` from `.env.example` when needed
- generates a strong Docker password and JWT secret on first run
- starts the packaged Stella stack on `http://127.0.0.1:5173`
- opens the app in your browser after the packaged frontend and backend are ready

Notes:

- Docker Desktop is the supported non-technical-user install path
- runtime data is stored only in the `stella-runtime` named Docker volume
- Ollama is optional
- set `STELLA_DOCKER_WITH_OLLAMA=1` before launch if you want the real `local-llm` profile

### Local development path

Double-click `run_stella.bat`.

What it does:

- verifies Python and frontend dependencies
- starts the FastAPI backend on `http://127.0.0.1:8000`
- starts the Vite frontend on `http://127.0.0.1:5173`
- opens the app in your browser once both services are reachable

Local dev keeps convenience auth defaults. Docker mode does not.

## Docker configuration

Use `.env.example` as the template for Docker runtime configuration.

Required Docker runtime values:

- `STELLA_USERNAME`
- `STELLA_PASSWORD`
- `STELLA_JWT_SECRET`
- `STELLA_FRONTEND_ORIGIN`

For the supported Docker product path:

- the launcher generates `.env` automatically on first run
- Docker auth values must be explicit and strong
- the frontend talks to the backend through same-origin `/api/*` and `/ws`

Manual compose commands:

```bash
docker compose up -d --build
docker compose down
```

Optional real Ollama sidecar:

```bash
docker compose --profile local-llm up -d --build
```

## Runtime data

By default Stella keeps runtime state out of the repository.

- Windows: `%LOCALAPPDATA%\Stella`
- macOS: `~/Library/Application Support/Stella`
- Linux: `${XDG_DATA_HOME:-~/.local/share}/stella`

That runtime directory holds the generated DuckDB database, uploads, and copied local `llm_config.yaml`.

Docker uses the named volume `stella-runtime` instead of OS app-data directories.

## First run

Stella starts empty by default.

- no sample data is auto-imported in supported product paths
- login and overview explain that the app is installed correctly but waiting for a real data import
- import a Fitbit, Apple Health, Google Takeout, Oura, Garmin, or manual CSV export to unlock analytics, reports, and chat
- if Ollama is unavailable, Stella remains usable in metrics-only mode

## Tests and smoke

Primary CI gates:

- `ruff check .`
- `pytest`
- `cd frontend && npm run test`
- `cd frontend && npm run build`
- `cd frontend && npm run test:e2e`
- backend Docker build
- frontend Docker build
- `python tools/smoke/docker_smoke.py --mode all`

The Docker smoke entrypoint validates:

- packaged frontend reachability
- backend readiness
- login through the same-origin `/api` path
- first-run empty runtime state
- import flow
- overview and report success
- degraded chat failure when no LLM is available
- successful chat/report behavior in stubbed smoke LLM mode

## Release discipline

Use the release checklist in [docs/release-checklist.md](docs/release-checklist.md).

Versioning policy:

- first Docker-first milestone: `v0.1.0`
- patch for bug-fix-only releases
- minor for user-visible product polish and workflow improvements
