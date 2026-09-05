# Engineering Guide — Study Randomizer

This document is the starting point for engineers who are new to the codebase. It explains **what** the system does, **how** it is built, and **where** to find things.

---

## 1. What is this system?

**Study Randomizer** is a web application for managing clinical study metadata, configuring treatment arms, adding investigators, and running study randomization workflows.

### User roles

| Role | Purpose | How they get access |
|------|---------|---------------------|
| **Admin** | Bootstrap the system; create/disable organizer accounts | First-run setup (`POST /setup`) with a setup token |
| **Organizer** | Create and manage studies; add investigators; configure arms and randomization | Created by an admin |
| **Investigator** | Access a single assigned study (future: contribute trial data) | Organizer adds them — credentials emailed automatically |

### High-level flows

```
First deploy
  └─ Admin runs setup (one time) → creates admin account

Admin
  └─ Logs in → creates organizer accounts → enables/disables them

Organizer
  └─ Logs in → creates studies
            → configures treatment arms & randomization
            → adds investigators (email + optional name)

Investigator
  └─ Receives email with Trial ID, username, and temp password
  └─ Logs in at /investigator/login (no signup flow)
  └─ Can change password after login
```

---

## 2. Tech stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL |
| Auth | bcrypt passwords, JWT in HttpOnly cookies |
| Frontend | React 19, Vite, React Router |
| Email | SMTP via Python `smtplib` |

---

## 3. Repository layout

```
.
├── backend/
│   ├── app/
│   │   ├── main.py             # App entry, middleware, router registration
│   │   ├── config.py           # Environment variables & cookie helpers
│   │   ├── database.py         # SQLAlchemy engine & get_db dependency
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   ├── schemas.py          # Pydantic request/response models
│   │   ├── core/
│   │   │   ├── security.py     # JWT, auth dependencies, token revocation
│   │   │   ├── csrf.py         # CSRF middleware
│   │   │   ├── rate_limit.py   # slowapi rate limiter
│   │   │   ├── audit.py        # Structured audit logging
│   │   │   ├── email.py        # SMTP + investigator credential emails
│   │   │   ├── investigators.py # Username/password generation
│   │   │   └── security_headers.py
│   │   └── routers/
│   │       ├── setup.py        # Health check + first-run admin setup
│   │       ├── admin.py        # Admin login/logout/session
│   │       ├── organizers.py   # Admin: CRUD organizers
│   │       ├── organizer.py    # Organizer auth, studies, investigators
│   │       └── investigator.py # Investigator login, me, change-password
│   ├── migrations/
│   └── .env.example
│
├── frontend/
│   └── src/
│       ├── App.jsx             # Route definitions
│       ├── api.js              # apiFetch wrapper (cookies, CSRF, JSON)
│       └── pages/              # One file per screen
│
└── docs/
    └── ENGINEERING.md          # This file
```

---

## 4. Local development setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL running locally

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

API: `http://localhost:8000` · Docs: `http://localhost:8000/docs` (dev only)

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

### First admin account

1. Open `http://localhost:5173`
2. Click **Open setup form**
3. Enter setup token (from `SETUP_TOKEN` in `.env`, or leave blank in dev if unset)
4. Create admin username/password (min 12 characters)

---

## 5. Configuration

Copy `backend/.env.example` → `backend/.env`.

| Variable | Required | Description |
|----------|----------|-------------|
| `ENVIRONMENT` | No | `development` or `production` |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Prod | JWT signing key |
| `SETUP_TOKEN` | Prod | Protects first-run admin setup |
| `CORS_ORIGINS` | No | Comma-separated frontend URLs |
| `FRONTEND_URL` | Yes* | Base URL in investigator credential emails |
| `SMTP_*` | Prod** | Email delivery for investigator credentials |

\* Required for correct login links in emails.  
\*\* In development without SMTP, credentials are logged to the backend console. In production, SMTP is required.

Frontend: `VITE_API_URL` in `frontend/.env` (default `http://localhost:8000`).

---

## 6. Database schema

### Entity relationship (simplified)

```
Admin                         (standalone)

Organizer ──< Study ──< TreatmentArm
                │
                ├──< Investigator
                └──< RandomizationRecord

RevokedToken                  (JWT blacklist on logout)
```

### Key tables

| Table | Purpose |
|-------|---------|
| `admin` | System administrators |
| `organizer` | Study managers |
| `studies` | Trial metadata (protocol code, blinding, randomization settings) |
| `treatment_arms` | Arms per study |
| `investigator` | Per-study accounts (email, generated username, status) |
| `randomization_records` | Randomization output rows |
| `revoked_tokens` | Invalidated JWT IDs after logout |

### Investigator model

Each investigator belongs to **one study**:

| Column | Description |
|--------|-------------|
| `username` | Sequential per study: `000001`, `000002`, … |
| `status` | `inactive` → `active` (first login) → `revoked` |
| Login key | `(trial_id, username, password)` where `trial_id` = study `protocol_code` |

### Migrations

```bash
alembic upgrade head
```

Latest migration: `b2c3d4e5f6a7` — replaces old doctor/invitation tables with `investigator`.

---

## 7. API reference

### Organizer — investigators

| Method | Path | Description |
|--------|------|-------------|
| GET | `/organizer/studies/{id}/investigators` | List investigators |
| POST | `/organizer/studies/{id}/investigators` | Create investigator + email credentials |
| PATCH | `/organizer/studies/{id}/investigators/{id}/revoke` | Revoke access |

### Investigator

| Method | Path | Description |
|--------|------|-------------|
| POST | `/investigator/login` | Login with `{ trial_id, username, password }` |
| POST | `/investigator/logout` | Logout |
| GET | `/investigator/me` | Current investigator info |
| POST | `/investigator/change-password` | Change password |

See `/docs` in development for the full API including admin, organizer study, and randomization endpoints.

---

## 8. Authentication & security

### Cookies (one per role)

| Role | Cookie name |
|------|-------------|
| Admin | `access_token` |
| Organizer | `organizer_access_token` |
| Investigator | `investigator_access_token` |

Investigator JWT `sub` stores the **investigator database id** (not username), because usernames are only unique within a study.

### CSRF

Mutating requests require `X-CSRF-Token` header matching the `csrf_token` cookie.  
**Exempt:** `/admin/login`, `/organizer/login`, `/investigator/login`, `/setup`, `/setup`.

The frontend stores CSRF in `sessionStorage` after login (`frontend/src/api.js`).

---

## 9. Frontend routes

| Path | Page | Role |
|------|------|------|
| `/organizer/studies/:studyId/home` | `StudyHome.jsx` | Organizer — study hub |
| `/organizer/studies/:studyId/investigators` | `StudyInvestigators.jsx` | Organizer — add/revoke investigators |
| `/organizer/studies/:studyId/arms` | `StudyArms.jsx` | Organizer — treatment arms |
| `/organizer/studies/:studyId/randomization` | `StudyRandomization.jsx` | Organizer — randomization |
| `/investigator/login` | `InvestigatorLogin.jsx` | Investigator — Trial ID + username + password |
| `/investigator/home` | `InvestigatorHome.jsx` | Investigator dashboard |
| `/investigator/change-password` | `InvestigatorChangePassword.jsx` | Investigator |

Always use `apiFetch` from `frontend/src/api.js` for API calls.

---

## 10. Investigator onboarding (email flow)

Implementation: `core/investigators.py`, `core/email.py`, `routers/organizer.py`.

```
Organizer submits email + optional name
        ↓
POST /organizer/studies/{id}/investigators
        ↓
Backend:
  1. generate_username()  → "000001", "000002", …
  2. generate_temp_password()
  3. INSERT investigator (status=inactive)
  4. send_investigator_credentials() via SMTP
     (dev without SMTP: credentials logged to console)
        ↓
Investigator logs in with Trial ID + username + password
        ↓
status → active on first login
```

No signup page. No invitation tokens. No join tables.

Organizer can **revoke** an investigator → subsequent logins return 401.

---

## 11. What is NOT implemented yet

- Investigator actions within a study (beyond login / change password)
- Participant/patient enrollment
- MFA
- HTML email templates

---

## 12. Quick file lookup

| I need to… | Look in… |
|------------|----------|
| Add investigator logic | `routers/organizer.py`, `core/investigators.py` |
| Change investigator auth | `routers/investigator.py`, `core/security.py` |
| Change credential email | `core/email.py` |
| Change DB schema | `models.py` + Alembic migration |
| Add frontend page | `frontend/src/pages/` + `App.jsx` |

---

## 13. Troubleshooting

| Problem | Likely cause |
|---------|----------------|
| 403 CSRF on investigator login | `/investigator/login` must be CSRF-exempt (see `core/csrf.py`) |
| Investigator login fails | Wrong trial ID (must match study `protocol_code`), wrong username/password, or revoked |
| No email received | SMTP not configured — check backend logs for credentials (dev mode) |
| 401 on protected routes | Expired/revoked token — log in again |
