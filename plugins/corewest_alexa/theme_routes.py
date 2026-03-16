"""
Core West College Theme Routes
FastAPI router serving all branded HTML template pages.
"""
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()

# ---------------------------------------------------------------------------
# Auth dependency — imported lazily so the theme module can be used without
# the auth package (graceful degradation).
# ---------------------------------------------------------------------------

try:
    from auth.dependencies import require_authenticated as _require_authenticated  # type: ignore[import-not-found]
    _AUTH_AVAILABLE = True
except ImportError:  # pragma: no cover
    _AUTH_AVAILABLE = False
    _require_authenticated = None  # type: ignore[assignment]


def _auth_dep() -> list[Any]:
    """Return the auth dependency list when auth is configured."""
    if _AUTH_AVAILABLE:
        return [Depends(_require_authenticated)]
    return []


def render(request: Request, template: str, **context):
    """Helper to render a template with common context."""
    return templates.TemplateResponse(
        request,
        template,
        {
            "page_title": context.pop("page_title", "Core West College"),
            **context,
        },
    )


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage(request: Request):
    return render(request, "index.html", page_title="Home")


@router.get("/about", response_class=HTMLResponse, include_in_schema=False)
async def about(request: Request):
    return render(request, "about.html", page_title="About Us")


@router.get("/divisions", response_class=HTMLResponse, include_in_schema=False)
async def divisions(request: Request):
    return render(request, "divisions.html", page_title="Academic Divisions")


@router.get("/teaching-learning", response_class=HTMLResponse, include_in_schema=False)
async def teaching_learning(request: Request):
    return render(request, "teaching_learning.html", page_title="Teaching & Learning")


@router.get("/facilities", response_class=HTMLResponse, include_in_schema=False)
async def facilities(request: Request):
    return render(request, "facilities.html", page_title="Facilities")


@router.get("/admission", response_class=HTMLResponse, include_in_schema=False)
async def admission(request: Request):
    return render(request, "admission.html", page_title="Admission")


@router.get("/events", response_class=HTMLResponse, include_in_schema=False)
async def events(request: Request):
    return render(request, "events.html", page_title="Events")


@router.get("/careers", response_class=HTMLResponse, include_in_schema=False)
async def careers(request: Request):
    return render(request, "careers.html", page_title="Careers")


@router.get("/contact", response_class=HTMLResponse, include_in_schema=False)
async def contact(request: Request):
    return render(request, "contact.html", page_title="Contact Us")


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login(request: Request):
    return render(request, "login.html", page_title="Login")


# ---------------------------------------------------------------------------
# Dashboard pages — client-side auth check (JS redirects to /login if no JWT)
# ---------------------------------------------------------------------------


@router.get(
    "/dashboard",
    response_class=HTMLResponse,
    include_in_schema=False,
    dependencies=_auth_dep(),
)
async def dashboard(request: Request):
    return render(request, "dashboard.html", page_title="AI Command Center")


@router.get(
    "/inspection-dashboard",
    response_class=HTMLResponse,
    include_in_schema=False,
    dependencies=_auth_dep(),
)
async def inspection_dashboard(request: Request):
    return render(request, "inspection_dashboard.html", page_title="Inspection Dashboard")


@router.get(
    "/curriculum-dashboard",
    response_class=HTMLResponse,
    include_in_schema=False,
    dependencies=_auth_dep(),
)
async def curriculum_dashboard(request: Request):
    return render(request, "curriculum_dashboard.html", page_title="Curriculum Dashboard")
