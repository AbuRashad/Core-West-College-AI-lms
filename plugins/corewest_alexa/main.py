"""
Core West College AI LMS — Alexa Plugin
Unified FastAPI application entry-point.

Integrates:
- Core West College branded frontend theme (Jinja2 templates)
- Auth routes (JWT login, registration, API-key validation)
- Curriculum monitoring endpoints (/curriculum/*)
- Inspection readiness endpoints (/inspection/*)
- Alexa voice endpoints (/alexa/*)
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Auth (optional — graceful degradation if not configured)
# ---------------------------------------------------------------------------
try:
    from auth.dependencies import require_authenticated, verify_api_key  # type: ignore[import-not-found]
    from auth.routes import router as auth_router                         # type: ignore[import-not-found]
    from auth.seed import seed as _seed_admin                             # type: ignore[import-not-found]
    _AUTH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _AUTH_AVAILABLE = False
    require_authenticated = None  # type: ignore[assignment]
    verify_api_key = None         # type: ignore[assignment]
    auth_router = None            # type: ignore[assignment]
    _seed_admin = None            # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Curriculum & Inspection routers
# ---------------------------------------------------------------------------
from curriculum.routes import curriculum_router, inspection_router        # noqa: E402
from curriculum.curriculum_monitor import CurriculumMonitor               # noqa: E402
from curriculum.inspection_readiness import InspectionReadinessEngine     # noqa: E402
from curriculum.performance_tracker import PerformanceTracker             # noqa: E402
from data_aggregator import DataAggregator                                # noqa: E402

_monitor = CurriculumMonitor()
_readiness = InspectionReadinessEngine()
_tracker = PerformanceTracker()
_aggregator = DataAggregator()

# ---------------------------------------------------------------------------
# Theme router (branded Jinja2 pages)
# ---------------------------------------------------------------------------
from theme_routes import router as theme_router                           # noqa: E402

# ---------------------------------------------------------------------------
# Lifespan — seed default admin user on startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """Seed the default admin user when the application starts."""
    if _AUTH_AVAILABLE and _seed_admin is not None:
        try:
            _seed_admin()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Admin seed skipped: %s", exc)
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Core West College — Alexa Plugin",
    version="3.0.0",
    description=(
        "Unified plugin for the Core West College AI LMS. "
        "Includes JWT authentication, curriculum monitoring, "
        "inspection readiness, branded theme, and Alexa voice integration."
    ),
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# When credentials (cookies/auth headers) are needed, browsers reject
# allow_origins="*".  We only enable credentials when an explicit origin
# list is supplied; otherwise credentials are disabled.

_cors_origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",")]
_credentials_allowed = "*" not in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_credentials_allowed,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files (theme assets)
# ---------------------------------------------------------------------------

_STATIC_DIR = Path(__file__).parent / "static"
if _STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# Auth endpoints: /auth/login, /auth/register, /auth/refresh, /auth/me, etc.
if _AUTH_AVAILABLE and auth_router is not None:
    app.include_router(auth_router)

# Curriculum endpoints: /curriculum/*
app.include_router(curriculum_router)

# Inspection endpoints: /inspection/*
app.include_router(inspection_router)

# Theme pages: /, /about, /divisions, /login, /dashboard, etc.
app.include_router(theme_router)

# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@app.get("/alexa/health", tags=["Alexa"])
async def health() -> JSONResponse:
    """Health-check — no authentication required."""
    return JSONResponse({
        "status": "ok",
        "version": "3.0.0",
        "auth_available": _AUTH_AVAILABLE,
        "modules": ["alexa", "curriculum", "inspection", "theme"],
    })


SUPPORTED_TYPES = [
    "inspection", "teachers", "students", "today", "tasks", "incidents",
    "curriculum", "subjects", "gaps", "at_risk",
]


@app.get("/alexa/query", tags=["Alexa"])
async def alexa_query(q: str = "", type: str = "today") -> JSONResponse:
    """Voice query endpoint — supports curriculum and inspection query types."""
    query_type = (q or type).strip().lower()

    if query_type in ("curriculum", "subjects", "gaps", "today"):
        speech_text = _monitor.get_voice_summary(query_type)
    elif query_type in ("teachers", "at_risk"):
        speech_text = _tracker.get_voice_summary(query_type)
    elif query_type in ("students", "tasks", "incidents"):
        speech_text = _tracker.get_voice_summary(query_type)
    elif query_type == "inspection":
        speech_text = _readiness.get_voice_summary()
    else:
        speech_text = (
            f"Sorry, I don't recognize the query type '{query_type}'. "
            f"Supported types are: {', '.join(SUPPORTED_TYPES)}."
        )

    return JSONResponse({
        "speech_text": speech_text,
        "card_title": "Core West Brief",
        "card_text": speech_text,
        "query_type": query_type,
        "status": "success",
    })


# ---------------------------------------------------------------------------
# Protected Alexa endpoints
# ---------------------------------------------------------------------------


@app.get("/alexa/dashboard", tags=["Alexa"])
async def alexa_dashboard(
    _user=Depends(require_authenticated) if (_AUTH_AVAILABLE and require_authenticated) else None,
) -> JSONResponse:
    """Dashboard summary — requires a valid JWT."""
    summary: dict = {
        "inspection_readiness": _readiness.calculate_overall_readiness("ofsted"),
        "curriculum_coverage": _monitor.get_coverage_summary(),
    }
    if _AUTH_AVAILABLE and _user:
        summary["welcome"] = f"Welcome, {_user.username}!"
    return JSONResponse({"status": "success", "data": summary})


def _alexa_response(speech_text: str, card_title: str = "Core West") -> dict:
    """Build an Alexa Skills Kit-compliant response envelope."""
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {"type": "PlainText", "text": speech_text},
            "card": {"type": "Simple", "title": card_title, "content": speech_text},
            "shouldEndSession": True,
        },
    }


@app.post("/alexa/webhook", tags=["Alexa"])
async def alexa_webhook(
    payload: dict,
    _key=Depends(verify_api_key) if (_AUTH_AVAILABLE and verify_api_key) else None,
) -> JSONResponse:
    """Alexa webhook — handles skill intents, returns Alexa SKS response envelope."""
    request_type = payload.get("request", {}).get("type", "")
    intent_name = payload.get("request", {}).get("intent", {}).get("name", "")

    if request_type == "LaunchRequest":
        speech = (
            "Welcome to Core West. You can ask for today's brief, "
            "inspection readiness, curriculum coverage, subject performance, "
            "curriculum gaps, or student risk summary."
        )
        return JSONResponse(_alexa_response(speech, "Welcome to Core West"))

    if request_type == "IntentRequest":
        intent_map = {
            "TodayBriefIntent":          ("today",      _tracker.get_voice_summary,  "Core West Daily Brief"),
            "InspectionIntent":          ("inspection", _readiness.get_voice_summary, "Inspection Brief"),
            "InspectionReadinessIntent": ("inspection", _readiness.get_voice_summary, "Inspection Readiness"),
            "CurriculumCoverageIntent":  ("coverage",   _monitor.get_voice_summary,   "Curriculum Coverage"),
            "SubjectPerformanceIntent":  ("subjects",   _monitor.get_voice_summary,   "Subject Performance"),
            "CurriculumGapsIntent":      ("gaps",       _monitor.get_voice_summary,   "Curriculum Gaps"),
            "TeacherSummaryIntent":      ("teachers",   _tracker.get_voice_summary,   "Teacher Summary"),
            "StudentRiskIntent":         ("at_risk",    _tracker.get_voice_summary,   "Student Risk"),
        }

        if intent_name in intent_map:
            query_type, handler, card_title = intent_map[intent_name]
            try:
                try:
                    speech = handler()  # type: ignore[call-arg]
                except TypeError:
                    speech = handler(query_type)  # type: ignore[call-arg]
            except (AttributeError, ValueError) as exc:
                logger.error("Voice handler error for %s: %s", intent_name, exc)
                speech = f"I was unable to retrieve the {query_type} summary."
            return JSONResponse(_alexa_response(speech, card_title))

    return JSONResponse(
        _alexa_response("Sorry, I did not understand that request.", "Core West")
    )


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
