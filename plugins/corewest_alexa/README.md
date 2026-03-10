# Core West College AI LMS — Alexa Plugin

A unified, self-contained FastAPI plugin for the **Core West College AI LMS** that provides:

- 🔐 **JWT Authentication** — login, registration, refresh, API-key validation
- 📚 **Curriculum Monitoring** — coverage analysis, gap detection, department roll-ups
- 📊 **Inspection Readiness** — Ofsted EIF + Cognia weighted scoring, evidence tracking, SEF generation
- 🎨 **Branded Frontend Theme** — Core West College responsive Jinja2 templates
- 🗣️ **Alexa Voice Integration** — Amazon Alexa skill endpoints with curriculum-aware intents

---

## Directory Structure

```
plugins/corewest_alexa/
├── __init__.py
├── main.py                          # Unified FastAPI application entry-point
├── requirements.txt                 # Merged Python dependencies
├── README.md                        # This file
├── README_THEME.md                  # Theme-specific documentation
├── theme_routes.py                  # FastAPI router for branded theme pages
├── conftest.py                      # pytest path configuration
├── auth/                            # JWT authentication module
│   ├── __init__.py
│   ├── api_key.py                   # X-API-Key header validation (Alexa webhook)
│   ├── blacklist.py                 # In-memory token blacklist
│   ├── dependencies.py              # require_authenticated, require_admin
│   ├── jwt_handler.py               # JWT creation / verification
│   ├── login_page.html              # Standalone (non-themed) login form
│   ├── models.py                    # User model with JSON file-based storage
│   ├── rate_limiter.py              # 5 req/min/IP brute-force protection
│   ├── routes.py                    # Auth API endpoints
│   ├── schemas.py                   # Pydantic request/response models
│   ├── seed.py                      # Default admin user seeder
│   └── utils.py                     # bcrypt password hashing
├── curriculum/                      # Curriculum & inspection module
│   ├── __init__.py
│   ├── curriculum_monitor.py        # Coverage %, gap analysis, subject health scores
│   ├── inspection_readiness.py      # Weighted readiness score, SEF generation
│   ├── models.py                    # Pydantic models (Subject, TeachingObservation, …)
│   ├── performance_tracker.py       # Teacher, cohort & at-risk student tracking
│   ├── routes.py                    # 25+ FastAPI endpoints
│   └── standards_framework.py       # Ofsted EIF, Cognia, Danielson, National Curriculum
├── templates/                       # Jinja2 HTML templates (Core West branded)
│   ├── base.html                    # Base layout with nav/footer
│   ├── index.html                   # Homepage
│   ├── about.html                   # About Us
│   ├── divisions.html               # Academic Divisions
│   ├── teaching_learning.html       # Teaching & Learning
│   ├── facilities.html              # Facilities
│   ├── admission.html               # Admissions
│   ├── events.html                  # Events
│   ├── careers.html                 # Careers
│   ├── contact.html                 # Contact
│   ├── login.html                   # Login (POSTs to /auth/login, stores JWT)
│   ├── dashboard.html               # AI Command Center (authenticated)
│   ├── inspection_dashboard.html    # Inspection Readiness Dashboard
│   └── curriculum_dashboard.html    # Curriculum Coverage Dashboard
├── static/
│   ├── css/
│   │   └── style.css                # 1,000+ line component library (navy/gold)
│   └── js/
│       └── main.js                  # Intersection observers, nav, dashboard
└── tests/
    ├── __init__.py
    ├── conftest.py                  # Plugin root sys.path setup
    ├── test_auth.py                 # 25 auth tests (JWT, registration, login)
    ├── test_inspection.py           # Inspection readiness & performance tests
    └── test_standards.py            # Standards framework tests
```

---

## Quick Start

```bash
cd plugins/corewest_alexa

# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export JWT_SECRET_KEY="your-very-secret-key-change-in-production"
export ALEXA_API_KEY="your-alexa-api-key"

# 3. Start the server (auto-seeds admin user on first run)
uvicorn main:app --reload --port 8080
```

Open **http://localhost:8080** to see the Core West College branded homepage.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `JWT_SECRET_KEY` | `change-me-in-production` | Secret key for JWT signing (RS256 / HS256) |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `ALEXA_API_KEY` | `""` | API key for Alexa webhook (`X-API-Key` header) |
| `CORS_ORIGINS` | `*` | Comma-separated allowed CORS origins |
| `RATE_LIMIT_MAX_ATTEMPTS` | `5` | Max login attempts per window |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window in seconds |

---

## API Endpoints

### Public Endpoints (no auth required)

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Homepage (HTML) |
| `GET` | `/about` | About page (HTML) |
| `GET` | `/divisions` | Divisions page (HTML) |
| `GET` | `/teaching-learning` | Teaching & Learning (HTML) |
| `GET` | `/facilities` | Facilities page (HTML) |
| `GET` | `/admission` | Admissions page (HTML) |
| `GET` | `/events` | Events page (HTML) |
| `GET` | `/careers` | Careers page (HTML) |
| `GET` | `/contact` | Contact page (HTML) |
| `GET` | `/login` | Login page (HTML) |
| `GET` | `/alexa/health` | Health check (JSON) |
| `GET` | `/alexa/query` | Voice query endpoint (JSON) |

### Auth Endpoints (`/auth/*`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Login — returns JWT access + refresh tokens |
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/refresh` | Refresh access token |
| `GET` | `/auth/me` | Get current user profile |
| `POST` | `/auth/logout` | Blacklist current token |
| `POST` | `/auth/change-password` | Change password |

### Protected Endpoints (JWT required)

| Method | Path | Description |
|---|---|---|
| `GET` | `/dashboard` | AI Command Center (HTML) |
| `GET` | `/inspection-dashboard` | Inspection Readiness Dashboard (HTML) |
| `GET` | `/curriculum-dashboard` | Curriculum Coverage Dashboard (HTML) |
| `GET` | `/alexa/dashboard` | Dashboard summary (JSON) |
| `POST` | `/alexa/webhook` | Alexa skill webhook (API key required) |
| `GET` | `/curriculum/*` | 25+ curriculum monitoring endpoints |
| `GET` | `/inspection/*` | Inspection readiness endpoints |

---

## School Branding

| Item | Detail |
|---|---|
| **School** | Core West College |
| **Chairman** | Mr. Mahmoud Gohar |
| **Head of Schools** | Mrs. Shereen Moussad |
| **Brand colour — Navy** | `#1a237e` |
| **Brand colour — Gold** | `#ffd700` |
| **Breakpoints** | 576 / 768 / 992 / 1200 px |

---

## Running Tests

```bash
cd plugins/corewest_alexa

# All tests
pytest tests/ -v

# Auth tests only
pytest tests/test_auth.py -v

# Curriculum / inspection tests
pytest tests/test_inspection.py tests/test_standards.py -v
```

---

## Alexa Voice Intents

| Intent | Query Type | Description |
|---|---|---|
| `TodayBriefIntent` | `today` | Daily operational brief |
| `InspectionIntent` / `InspectionReadinessIntent` | `inspection` | Ofsted readiness score |
| `CurriculumCoverageIntent` | `coverage` | Curriculum coverage % |
| `SubjectPerformanceIntent` | `subjects` | Subject-by-subject performance |
| `CurriculumGapsIntent` | `gaps` | Curriculum gaps summary |
| `TeacherSummaryIntent` | `teachers` | Teacher performance overview |
| `StudentRiskIntent` | `at_risk` | At-risk student summary |
