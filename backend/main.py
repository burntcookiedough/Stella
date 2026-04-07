from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any
import shutil
import uuid

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
import uvicorn

from analytics.anomaly import generate_llm_summary
from analytics.features import get_latest_user_stats
from analytics.pipeline import HealthAnalyticsService
from analytics.store import HealthStore
from backend.auth import decode_token, issue_token, secure_compare
from backend.config import Settings, get_settings
from backend.report import create_health_report
from llm.engine import LLMGateway

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:  # pragma: no cover
    BackgroundScheduler = None

settings = get_settings()
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class ReportRequest(BaseModel):
    source_user_id: str | None = None


def _client_is_loopback(host: str | None) -> bool:
    return host in {"127.0.0.1", "::1", "localhost"}


def _get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _get_service(request: Request) -> HealthAnalyticsService:
    return request.app.state.analytics_service


def _get_gateway(request: Request) -> LLMGateway:
    return request.app.state.llm_gateway


def require_auth(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> dict[str, Any]:
    runtime_settings = _get_settings(request)
    client_host = request.client.host if request.client else None
    if runtime_settings.dev_bypass and _client_is_loopback(client_host):
        return {"sub": runtime_settings.username, "dev_bypass": True}
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing bearer token.")
    try:
        return decode_token(credentials.credentials, runtime_settings.jwt_secret)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _initialize_state(application: FastAPI) -> None:
    application.state.settings = settings
    application.state.store = HealthStore(settings.duckdb_path)
    application.state.analytics_service = HealthAnalyticsService(application.state.store)
    application.state.llm_gateway = LLMGateway(settings.llm_config_path)
    application.state.analytics_service.bootstrap_fitbit_sample(settings.data_dir / "raw")

    if settings.scheduler_enabled and BackgroundScheduler is not None:
        scheduler = BackgroundScheduler(timezone="UTC")
        scheduler.add_job(
            application.state.analytics_service.refresh_materializations,
            trigger="cron",
            hour=2,
            minute=0,
            id="refresh-materializations",
            replace_existing=True,
        )
        scheduler.start()
        application.state.scheduler = scheduler
    else:
        application.state.scheduler = None


def _shutdown_state(application: FastAPI) -> None:
    scheduler = getattr(application.state, "scheduler", None)
    if scheduler is not None:
        scheduler.shutdown(wait=False)


@asynccontextmanager
async def lifespan(application: FastAPI):
    _initialize_state(application)
    try:
        yield
    finally:
        _shutdown_state(application)


app = FastAPI(title="Stella API", version="2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:5173",
        "http://localhost:8501",  # Support legacy streamlit if needed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def startup_event() -> None:
    _initialize_state(app)


async def shutdown_event() -> None:
    _shutdown_state(app)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz(request: Request) -> dict[str, Any]:
    store: HealthStore = request.app.state.store
    return {"status": "ready", "has_data": store.has_events()}


@app.post("/v1/auth/login", response_model=LoginResponse)
def login(request_body: LoginRequest, request: Request) -> LoginResponse:
    runtime_settings = _get_settings(request)
    if not secure_compare(request_body.username, runtime_settings.username) or not secure_compare(
        request_body.password, runtime_settings.password
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = issue_token(runtime_settings.username, runtime_settings.jwt_secret, runtime_settings.token_ttl_minutes)
    return LoginResponse(access_token=token, expires_in_minutes=runtime_settings.token_ttl_minutes)


@app.post("/v1/imports")
async def import_files(
    request: Request,
    _claims: Annotated[dict[str, Any], Depends(require_auth)],
    files: Annotated[list[UploadFile], File(...)],
    source: Annotated[str | None, Form()] = None,
) -> dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required.")

    import_dir = _get_settings(request).uploads_dir / str(uuid.uuid4())
    import_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []
    for upload in files:
        filename = upload.filename or "upload.bin"
        destination = import_dir / filename
        with destination.open("wb") as handle:
            shutil.copyfileobj(upload.file, handle)
        saved_paths.append(destination)

    service = _get_service(request)
    result = service.ingest_paths(saved_paths, source=source)
    return {
        "status": "imported",
        "imported_at": datetime.now(UTC).isoformat(),
        **result,
    }


@app.get("/v1/overview")
def overview(
    request: Request,
    _claims: Annotated[dict[str, Any], Depends(require_auth)],
    source_user_id: str | None = None,
) -> dict[str, Any]:
    return _get_service(request).get_overview(source_user_id=source_user_id)


@app.get("/v1/analytics/correlations")
def correlations(
    request: Request,
    _claims: Annotated[dict[str, Any], Depends(require_auth)],
    source_user_id: str | None = None,
    lag_days: int | None = None,
) -> dict[str, Any]:
    return _get_service(request).get_correlations(source_user_id=source_user_id, lag_days=lag_days)


@app.post("/v1/reports/pdf")
def generate_report(
    request_body: ReportRequest,
    request: Request,
    _claims: Annotated[dict[str, Any], Depends(require_auth)],
) -> Response:
    service = _get_service(request)
    overview_payload = service.get_overview(source_user_id=request_body.source_user_id)
    correlations_payload = service.get_correlations(source_user_id=request_body.source_user_id)
    if overview_payload["latest"] is None:
        raise HTTPException(status_code=404, detail="No overview data available.")

    llm_summary = {
        **generate_llm_summary(
            get_latest_user_stats(
                request.app.state.store.fetch_overview(overview_payload["selected_user"]),
                overview_payload["selected_user"],
            )
        ),
        "correlations": correlations_payload["pairs"][:3],
    }
    ai_text = _get_gateway(request).analyze_health_data(llm_summary)
    pdf_bytes = create_health_report(overview_payload, correlations_payload, ai_text)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=stella-report-{overview_payload['selected_user']}.pdf"},
    )


@app.websocket("/v1/chat/ws")
async def chat_socket(websocket: WebSocket) -> None:
    await websocket.accept()
    runtime_settings: Settings = websocket.app.state.settings
    token = websocket.query_params.get("token")
    client_host = websocket.client.host if websocket.client else None

    try:
        if not (runtime_settings.dev_bypass and _client_is_loopback(client_host)):
            if not token:
                await websocket.send_json({"type": "error", "message": "Missing token."})
                await websocket.close(code=4401)
                return
            decode_token(token, runtime_settings.jwt_secret)

        while True:
            payload = await websocket.receive_json()
            source_user_id = payload.get("source_user_id")
            message = str(payload.get("message", "")).strip()
            if not message:
                await websocket.send_json({"type": "error", "message": "Message is required."})
                continue

            overview_payload = websocket.app.state.analytics_service.get_overview(source_user_id)
            correlations_payload = websocket.app.state.analytics_service.get_correlations(source_user_id)
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are Stella, a privacy-first health intelligence assistant. "
                        "Respond concisely, reference metrics when present, and never diagnose."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Overview: {overview_payload}\n"
                        f"Correlations: {correlations_payload['pairs'][:5]}\n"
                        f"Question: {message}"
                    ),
                },
            ]

            for chunk in websocket.app.state.llm_gateway.stream_chat(messages):
                await websocket.send_json({"type": "chunk", "content": chunk})
            await websocket.send_json({"type": "done"})
    except Exception as exc:
        if websocket.application_state.value == 1:
            await websocket.send_json({"type": "error", "message": str(exc)})
            await websocket.close(code=1011)


if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
