# Stella Docker-First Release Checklist

## Release gate

- GitHub Actions is green:
  - `ruff check .`
  - `pytest`
  - `npm run test`
  - `npm run build`
  - `npm run test:e2e`
  - backend Docker build
  - frontend Docker build
  - Docker smoke
- Windows local launcher check is green with `run_stella.bat`
- Windows Docker launcher check is green with `run_stella_docker.bat`
- Windows Docker launcher check is green with `STELLA_DOCKER_WITH_OLLAMA=1`
- `.env` bootstrap generates a strong password and JWT secret
- Runtime data stays out of repo root in both local and Docker paths

## Docker-first product checks

- `run_stella_docker.bat` creates `.env` automatically when missing
- Docker startup succeeds without Ollama and Stella stays usable in metrics-only mode
- Docker startup with the real `local-llm` profile enables chat and report summaries
- Docker runtime data is persisted in the `stella-runtime` named volume only
- Frontend same-origin proxy works for `/api/*` and `/ws`

## First-run checks

- A fresh runtime starts with `has_data=false`
- Login screen explains that Stella is installed but empty
- Workspace overview shows onboarding instead of blank analytics
- Importing Fitbit fixture data unlocks overview, analytics, chat, and reports
- Reports explain metrics-only output cleanly when the LLM is unavailable

## Versioning policy

- Use semver tags for releaseable local builds
- The first Docker-first milestone ships as `v0.1.0`
- Bug-fix-only releases increment the patch version
- User-visible polish or workflow changes increment the minor version
