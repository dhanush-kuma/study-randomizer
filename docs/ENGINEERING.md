# Engineering Guide — Study Randomizer

This document is the starting point for engineers who are new to the codebase. It explains **what** the system does, **how** it is built, and **where** to find things.

---

## 1. What is this system?

**Study Randomizer** is a web application for managing clinical study metadata and inviting doctors to participate in studies. It is **not** a full randomization engine yet — it handles user management, study configuration, and doctor invitations.

### User roles

| Role | Purpose | How they get access |
|------|---------|---------------------|
| **Admin** | Bootstrap the system; create/disable organizer accounts | First-run setup (`POST /setup`) with a setup token |
| **Organizer** | Create studies; invite doctors by email | Created by an admin |
| **Doctor** | View studies they are assigned to | Email invitation → signup or login |

### High-level flows

```
First deploy
  └─ Admin runs setup (one time) → creates admin account

Admin
  └─ Logs in → creates organizer accounts → enables/disables them

Organizer
  └─ Logs in → creates studies (metadata + treatment arms)
            → invites doctors by email

Doctor
  └─ Receives email with signup link
  └─ New user: signup → auto-joined to study
  └─ Existing user: login → accept invitation
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
├── backend/                    # FastAPI API server
│   ├── app/
│   │   ├── main.py             # App entry, middleware, router registration
│   │   ├── config.py           # Environment variables & cookie helpers
│   │   ├── database.py         # SQLAlchemy engine & get_db dependency
│   │   ├── models.py           # SQLAlchemy ORM models (database tables)
│   │   ├── schemas.py          # Pydantic request/response models
│   │   ├── core/               # Cross-cutting concerns
│   │   │   ├── security.py     # JWT, auth dependencies, token revocation
│   │   │   ├── csrf.py         # CSRF middleware
│   │   │   ├── rate_limit.py   # slowapi rate limiter
│   │   │   ├── audit.py        # Structured audit logging
│   │   │   ├── email.py        # SMTP send + invitation email template
│   │   │   ├── invitations.py  # Invitation token & acceptance logic
│   │   │   └── security_headers.py
│   │   └── routers/            # HTTP route handlers (one file per area)
│   │       ├── setup.py        # Health check + first-run admin setup
│   │       ├── admin.py        # Admin login/logout/session
│   │       ├── organizers.py   # Admin: CRUD organizers
│   │       ├── organizer.py    # Organizer auth + studies + invitations
│   │       └── doctor.py       # Doctor auth + signup + studies
│   ├── migrations/             # Alembic database migrations
│   ├── alembic.ini
│   ├── requirements.txt
│   └── .env.example            # Copy to .env for local config
│
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── main.jsx            # React DOM entry
│   │   ├── App.jsx             # Route definitions
│   │   ├── api.js              # apiFetch wrapper (cookies, CSRF, JSON)
│   │   ├── config.js           # VITE_API_URL
│   │   ├── components/         # Shared UI (Header, PasswordInput)
│   │   └── pages/              # One file per screen/route
│   ├── .env.example
│   └── package.json
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

### Database

Create a database (example name: `study-randomizer`):

```sql
CREATE DATABASE "study-randomizer";
```

### Backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # edit DATABASE_URL and other values
alembic upgrade head          # apply all migrations
uvicorn app.main:app --reload
```

API: `http://localhost:8000`  
Interactive docs (dev only): `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env          # optional; defaults to localhost:8000
npm run dev
```

App: `http://localhost:5173`

### First admin account

1. Open `http://localhost:5173`
2. Click **Open setup form**
3. Enter setup token (from `SETUP_TOKEN` in `.env`, or leave blank in dev if unset)
4. Create admin username/password (min 12 characters)

Then log in at `/admin/login` and create organizer accounts.

---

## 5. Configuration

All backend config is loaded from environment variables in `backend/app/config.py`. Copy `backend/.env.example` to `backend/.env`.

| Variable | Required | Description |
|----------|----------|-------------|
| `ENVIRONMENT` | No | `development` (default) or `production` |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Prod | JWT signing key; must be strong in production |
| `SETUP_TOKEN` | Prod | Protects first-run admin setup |
| `CORS_ORIGINS` | No | Comma-separated frontend URLs (default `http://localhost:5173`) |
| `FRONTEND_URL` | Yes* | Base URL for links in invitation emails |
| `SMTP_HOST` | No** | Mail server hostname |
| `SMTP_PORT` | No | Default `587` |
| `SMTP_USER` / `SMTP_PASSWORD` | No | SMTP credentials |
| `SMTP_FROM` | No** | Sender address shown to recipients |
| `SMTP_USE_TLS` | No | Default `true` |
| `COOKIE_SECURE` | Prod | Set `true` when using HTTPS |
| `COOKIE_SAMESITE` | Prod | Use `none` if frontend and API are on different domains |

\* Required for invitation emails to contain correct links.  
\*\* In development, if SMTP is not configured, invitation links are logged to the console instead of emailed. In production, SMTP is required for invitations.

Frontend config: `frontend/.env` → `VITE_API_URL` (default `http://localhost:8000`).

---

## 6. Database schema

Models live in `backend/app/models.py`. Migrations are in `backend/migrations/versions/`.

### Entity relationship (simplified)

```
Admin                    (standalone)

Organizer ──< Study ──< TreatmentArm
                │
                ├──< StudyInvitation
                └──< StudyDoctor >── Doctor

RevokedToken             (JWT blacklist on logout)
```

### Tables

| Table | Purpose |
|-------|---------|
| `admin` | System administrators |
| `organizer` | Study managers (`is_active` flag) |
| `studies` | Trial metadata (title, protocol, blinding, randomization settings) |
| `treatment_arms` | Arms per study (name, short code, allocation ratio) |
| `doctor` | Doctors (`email`, `username`, optional `full_name`) |
| `study_invitations` | Pending/accepted email invites (token, expiry) |
| `study_doctors` | Many-to-many: which doctors belong to which studies |
| `revoked_tokens` | Invalidated JWT IDs after logout |

### Migrations

Run from `backend/`:

```bash
alembic upgrade head      # apply pending migrations
alembic revision -m "description" --autogenerate   # create new migration (after model changes)
```

Migration chain (oldest → newest):

1. `937fc07f8529` — admin  
2. `53a123b51bd3` — organizer  
3. `8f1e2d3c4b5a` — studies  
4. `c7d8e9f0a1b2` — treatment_arms  
5. `d4e5f6a7b8c9` — revoked_tokens  
6. `e5f6a7b8c9d0` — doctor, study_invitations, study_doctors  

---

## 7. API reference

Base URL: `http://localhost:8000` (dev).

### Public / setup

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/setup/status` | Check if admin exists (requires `X-Setup-Token` header) |
| POST | `/setup` | Create first admin (requires `setup_token` in body) |

### Admin (`/admin`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/admin/login` | — | Login; returns CSRF token |
| POST | `/admin/logout` | Admin | Logout; revokes JWT |
| GET | `/admin/me` | Admin | Current admin info |

### Admin — organizers (`/admin/organizers`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/admin/organizers/` | Admin | Create organizer |
| GET | `/admin/organizers/` | Admin | List organizers |
| PATCH | `/admin/organizers/{id}/status` | Admin | Toggle active/inactive |

### Organizer (`/organizer`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/organizer/login` | — | Login |
| POST | `/organizer/logout` | Organizer | Logout |
| GET | `/organizer/me` | Organizer | Current organizer |
| POST | `/organizer/studies/` | Organizer | Create study + treatment arms |
| GET | `/organizer/studies/` | Organizer | List own studies |
| GET | `/organizer/studies/{id}` | Organizer | Get one study |
| GET | `/organizer/studies/{id}/invitations` | Organizer | List invitations |
| POST | `/organizer/studies/{id}/invitations` | Organizer | Send doctor invitation email |

### Doctor (`/doctor`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/doctor/invitations/{token}` | — | Preview invitation |
| POST | `/doctor/signup` | — | Create account + join study |
| POST | `/doctor/invitations/{token}/accept` | Doctor | Join study (existing account) |
| POST | `/doctor/login` | — | Login |
| POST | `/doctor/logout` | Doctor | Logout |
| GET | `/doctor/me` | Doctor | Current doctor |
| GET | `/doctor/studies/` | Doctor | List assigned studies |

Request/response shapes are defined in `backend/app/schemas.py`.

---

## 8. Authentication & security

Implementation: `backend/app/core/security.py`, `backend/app/config.py`, `backend/app/core/csrf.py`.

### How auth works

1. User submits username/password to a login endpoint.
2. Server verifies with bcrypt, creates a JWT containing `sub` (username), `role`, `jti`, and `exp`.
3. JWT is stored in an **HttpOnly cookie** (separate cookie per role):
   - Admin → `access_token`
   - Organizer → `organizer_access_token`
   - Doctor → `doctor_access_token`
4. A **CSRF token** is also set (cookie + returned in login response body).
5. Protected routes use FastAPI dependencies (`get_current_admin`, etc.) that read the cookie, verify role, and check revocation.

### CSRF

Mutating requests (POST/PATCH/DELETE) require the `X-CSRF-Token` header to match the `csrf_token` cookie. Exempt routes: login, signup, setup, invitation preview.

The frontend stores the CSRF token in `sessionStorage` after login (`frontend/src/api.js`) because cross-origin setups cannot read API cookies from JavaScript.

### Other security features

| Feature | Where |
|---------|-------|
| Rate limiting | `core/rate_limit.py` — login/setup/invite endpoints |
| Token revocation on logout | `revoked_tokens` table |
| Audit logging | `core/audit.py` — login, setup, study create, invitations |
| Security headers | `core/security_headers.py` |
| Password policy | min 12 chars for new passwords (`schemas.py`) |
| Setup token | Protects first admin creation in production |

---

## 9. Frontend architecture

### Routing

All routes are in `frontend/src/App.jsx`:

| Path | Page file | Role |
|------|-----------|------|
| `/` | `Home.jsx` | Public — health + admin setup |
| `/admin/login` | `AdminLogin.jsx` | Admin |
| `/admin/home` | `AdminHome.jsx` | Admin — manage organizers |
| `/organizer/login` | `OrganizerLogin.jsx` | Organizer |
| `/organizer/home` | `OrganizerHome.jsx` | Organizer — study list |
| `/organizer/studies/new` | `CreateStudy.jsx` | Organizer — create study |
| `/organizer/studies/:studyId/invites` | `StudyInvites.jsx` | Organizer — invite doctors |
| `/doctor/signup?token=...` | `DoctorSignup.jsx` | Public — invitation signup |
| `/doctor/login` | `DoctorLogin.jsx` | Doctor |
| `/doctor/home` | `DoctorHome.jsx` | Doctor — assigned studies |

`*Guard.jsx` pages (`AdminGuard`, `OrganizerGuard`, `DoctorGuard`) check session and redirect to login or home.

### API calls

Always use `apiFetch` from `frontend/src/api.js` instead of raw `fetch`:

```javascript
import { apiFetch, setCsrfToken, clearCsrfToken } from '../api'

// GET
const res = await apiFetch('/organizer/studies/')

// POST with JSON body
const res = await apiFetch('/organizer/studies/', {
  method: 'POST',
  json: { title: '...', protocol_code: '...', treatment_arms: [] },
})
```

Use `credentials: 'include'` behavior is built in. After login, call `setCsrfToken(data.csrf_token)`. On logout, call `clearCsrfToken()`.

---

## 10. Email invitations

Implementation: `backend/app/core/email.py`, `backend/app/core/invitations.py`, `backend/app/routers/organizer.py` (send), `backend/app/routers/doctor.py` (accept/signup).

### Flow

1. Organizer POSTs `{ email, full_name? }` to `/organizer/studies/{id}/invitations`.
2. Server creates a `study_invitations` row with a secure token (7-day expiry).
3. `send_study_invitation()` sends an SMTP email with link:  
   `{FRONTEND_URL}/doctor/signup?token={token}`
4. Doctor opens link → frontend calls `GET /doctor/invitations/{token}`.
5. New doctor → `POST /doctor/signup` creates account and joins study.  
   Existing doctor → login → `POST /doctor/invitations/{token}/accept`.

Resending to the same email while status is `pending` refreshes the token and expiry.

---

## 11. What is NOT implemented yet

These are intentional gaps or future work:

- **Randomization execution** — studies store method/settings but no schedule is generated
- **`random_seed`** — column exists but is always `null`; not exposed to users yet
- **Study update/delete** — `StudyUpdate` schema exists; no PATCH/DELETE routes
- **Study detail page for organizers** — only list + create + invites
- **Doctor actions within a study** — doctors can only see assigned studies, not enroll patients
- **Participant/patient role**
- **MFA**
- **Email templates** — plain-text only

When adding features, follow existing patterns: model → migration → schema → router → page.

---

## 12. Adding a new feature (checklist)

Example: “Organizer can edit a study.”

1. **Schema** — add/update Pydantic models in `schemas.py`
2. **Router** — add endpoint in `routers/organizer.py` with `get_current_organizer` dependency
3. **Authorization** — scope queries to `current_organizer.id` (see `get_study_for_organizer` in `core/invitations.py`)
4. **Audit** — call `audit("event.name", ...)` for important actions
5. **Frontend** — new page or form; use `apiFetch`
6. **Migration** — only if the database schema changes: `alembic revision --autogenerate -m "..."`

---

## 13. Running in production (summary)

1. Set `ENVIRONMENT=production`
2. Set strong `SECRET_KEY` and `SETUP_TOKEN`
3. Configure PostgreSQL `DATABASE_URL`
4. Set `CORS_ORIGINS` and `FRONTEND_URL` to your real domains
5. Configure SMTP for invitation emails
6. If frontend and API are on different domains: `COOKIE_SECURE=true`, `COOKIE_SAMESITE=none`
7. Run `alembic upgrade head` before starting the server
8. Build frontend: `npm run build` → serve `dist/` via static host or reverse proxy
9. Run backend with a production ASGI server (e.g. `uvicorn app.main:app --host 0.0.0.0 --port 8000`)

---

## 14. Quick file lookup

| I need to… | Look in… |
|------------|----------|
| Add an API endpoint | `backend/app/routers/` |
| Change DB tables | `backend/app/models.py` + new migration |
| Change request/response validation | `backend/app/schemas.py` |
| Change auth behavior | `backend/app/core/security.py` |
| Change env vars | `backend/app/config.py`, `backend/.env.example` |
| Change email content | `backend/app/core/email.py` |
| Add a frontend page | `frontend/src/pages/` + route in `App.jsx` |
| Change how API calls work | `frontend/src/api.js` |
| Change global styles | `frontend/src/index.css`, `App.css` |

---

## 15. Troubleshooting

| Problem | Likely cause |
|---------|----------------|
| 401 on protected routes | Not logged in, wrong role cookie, or expired/revoked token |
| 403 CSRF validation failed | Missing CSRF header; log in again to refresh token |
| Invitation email not received | SMTP not configured; check backend logs (dev logs link instead) |
| CORS errors | `CORS_ORIGINS` does not include frontend URL |
| `SECRET_KEY must be set` on startup | Production mode without a real secret in `.env` |
| DB errors on startup | Run `alembic upgrade head`; check `DATABASE_URL` |

---

For questions about deployment providers or security hardening history, see git commit messages from the `feat: harden auth` and `feat: add doctor email invitations` changes.
