"""
Integration tests for the unified Core West Alexa Plugin (main.py).
Tests cover the Alexa-specific endpoints of the consolidated plugin.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Set test environment variables before importing the app
os.environ["ALEXA_API_KEY"] = "test-api-key-for-tests"
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-for-tests")

# Ensure the plugin root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Point the user store at a temporary file so tests don't pollute the real store
import auth.models as _auth_models  # noqa: E402
_tmp_dir = tempfile.mkdtemp()
_auth_models._USERS_FILE = Path(_tmp_dir) / "test_users.json"

# Seed the default admin user into the temp store
from auth.seed import seed as _seed  # noqa: E402
_seed()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app, raise_server_exceptions=False)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

WEBHOOK_HEADERS = {"X-API-Key": "test-api-key-for-tests"}


def _get_admin_token() -> str:
    """Log in as admin and return a JWT access token."""
    resp = client.post(
        "/auth/login",
        json={"username": "admin", "password": "CoreWest2024!"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Root / homepage
# ---------------------------------------------------------------------------

def test_root_returns_html():
    """Branded homepage returns 200 HTML."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# /alexa/health
# ---------------------------------------------------------------------------

def test_health():
    resp = client.get("/alexa/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "modules" in data
    assert "alexa" in data["modules"]


# ---------------------------------------------------------------------------
# /alexa/query
# ---------------------------------------------------------------------------

VOICE_QUERY_TYPES = [
    "inspection", "teachers", "today", "curriculum", "subjects", "gaps",
]


@pytest.mark.parametrize("query_type", VOICE_QUERY_TYPES)
def test_query_valid_types(query_type):
    resp = client.get(f"/alexa/query?type={query_type}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["speech_text"]
    assert data["card_title"] == "Core West Brief"


def test_query_unknown_type_still_succeeds():
    """Unknown types return a polite message rather than an error."""
    resp = client.get("/alexa/query?type=unknown")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"


def test_query_default_type():
    """Missing type parameter defaults to 'today' query."""
    resp = client.get("/alexa/query")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"


def test_query_case_insensitive():
    resp = client.get("/alexa/query?type=INSPECTION")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


# ---------------------------------------------------------------------------
# /alexa/dashboard (JWT-protected)
# ---------------------------------------------------------------------------

def test_dashboard_requires_auth():
    """Dashboard should reject unauthenticated requests."""
    resp = client.get("/alexa/dashboard")
    assert resp.status_code == 401


def test_dashboard_with_auth():
    """Authenticated dashboard returns inspection and curriculum data."""
    token = _get_admin_token()
    resp = client.get(
        "/alexa/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "data" in data
    dashboard = data["data"]
    assert "inspection_readiness" in dashboard
    assert "curriculum_coverage" in dashboard


# ---------------------------------------------------------------------------
# /alexa/webhook — API key protection
# ---------------------------------------------------------------------------

def test_webhook_requires_api_key():
    """Webhook should reject requests without the correct API key."""
    payload = {"request": {"type": "LaunchRequest"}}
    resp = client.post("/alexa/webhook", json=payload)
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /alexa/webhook — LaunchRequest
# ---------------------------------------------------------------------------

def test_webhook_launch_request():
    payload = {"request": {"type": "LaunchRequest"}}
    resp = client.post("/alexa/webhook", json=payload, headers=WEBHOOK_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "Welcome to Core West" in body["speech_text"]
    assert body["received"] is True


# ---------------------------------------------------------------------------
# /alexa/webhook — IntentRequest
# ---------------------------------------------------------------------------

CURRICULUM_INTENTS = [
    "TodayBriefIntent",
    "InspectionIntent",
    "InspectionReadinessIntent",
    "CurriculumCoverageIntent",
    "SubjectPerformanceIntent",
    "CurriculumGapsIntent",
    "TeacherSummaryIntent",
    "StudentRiskIntent",
]


@pytest.mark.parametrize("intent_name", CURRICULUM_INTENTS)
def test_webhook_curriculum_intents(intent_name):
    payload = {
        "request": {
            "type": "IntentRequest",
            "intent": {"name": intent_name},
        }
    }
    resp = client.post("/alexa/webhook", json=payload, headers=WEBHOOK_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["received"] is True
    assert body["speech_text"]
    assert body["intent"] == intent_name


def test_webhook_unknown_intent():
    payload = {
        "request": {
            "type": "IntentRequest",
            "intent": {"name": "UnknownIntent"},
        }
    }
    resp = client.post("/alexa/webhook", json=payload, headers=WEBHOOK_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert "did not understand" in body["speech_text"].lower()
