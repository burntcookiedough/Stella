# Stella Product Plan

## Current product

Stella is now a local-first health analytics product with:

- a FastAPI backend for auth, imports, analytics, reports, health checks, and chat
- a React + Vite frontend for overview, analytics, chat, and reporting
- DuckDB-backed normalized storage and materialized analytics
- an Ollama-backed LLM layer with graceful fallback when the model is unavailable
- a one-click Windows launcher through `run_stella.bat`

The old Streamlit plan is obsolete. The active product surface is the v2 FastAPI + React stack.

## What Stella should become

The target is a standalone local product that a non-technical user can install, launch, and use without touching terminals.

That means Stella needs:

1. dependable startup
2. clear runtime readiness and error states
3. packaged distribution
4. repeatable CI and release automation
5. durable local data handling

## Execution roadmap

### Phase 1: Runtime stability

- keep chat, reports, imports, overview, and analytics green under local and browser tests
- treat Ollama failures as degraded service instead of app failure
- keep `/healthz` and `/readyz` accurate enough for smoke tests and installers
- finish eliminating repo-owned warnings and noisy failure paths

### Phase 2: Product polish

- tighten navigation, empty states, error recovery, and report UX
- improve frontend bundle strategy so the production app is smaller and faster
- standardize visual language across cards, controls, charts, and dialogs
- add import progress and more explicit data provenance in the UI

### Phase 3: Standalone packaging

- keep Docker as the first supported packaged runtime
- add a desktop wrapper or installer once the local runtime is stable
- move app state, uploads, and DuckDB data into user-safe application directories
- provide upgrade-safe config and data migration rules

### Phase 4: Release discipline

- keep GitHub Actions aligned with the real product gate: lint, pytest, frontend tests, build, E2E, and container builds
- add versioned releases and changelog entries
- add smoke checks for launcher/runtime packaging before release
- publish reproducible artifacts instead of relying on ad hoc local runs

## Near-term priorities

The next concrete priorities should be:

1. fix any remaining CI failures until the pipeline is green on every branch
2. split the large frontend bundle with route-level or chart-level code splitting
3. package Stella into a first installable distribution, likely Docker-first and Windows-friendly
4. harden configuration, secrets, and local data paths for real users instead of repo-root assumptions

## Success criteria

Stella is ready to call a real standalone product when:

- a new user can launch it with one click
- the app explains degraded AI runtime without crashing
- all core flows pass in CI and in browser E2E
- distribution no longer depends on the repo layout or a developer shell

---


