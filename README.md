# Open Source Study Randomizer

A web app for managing clinical study metadata and inviting doctors to participate in trials. Built with **FastAPI** (backend) and **React + Vite** (frontend).

## What it does today

- **Admin** — first-run setup, create and manage organizer accounts
- **Organizer** — create studies (metadata + treatment arms), invite doctors by email
- **Doctor** — sign up via email invitation, view assigned studies

Randomization schedules are **not** generated yet — only study configuration and user/invitation management.

## Documentation

**New engineers should start here:**

→ **[docs/ENGINEERING.md](docs/ENGINEERING.md)** — architecture, setup, API, auth, database, and where everything lives in the codebase.

## Quick start

### Prerequisites

Python 3.11+, Node.js 18+, PostgreSQL

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
cp .env.example .env            # edit DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload
```

Runs at `http://localhost:8000` · API docs at `/docs` (development only)

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173`

### 3. Bootstrap

Open the frontend → use **First-Run Setup** to create the admin account → log in at `/admin` → create an organizer → log in at `/organizer`.

See [docs/ENGINEERING.md](docs/ENGINEERING.md) for environment variables, SMTP setup, and production deployment.

## Project structure

```
.
├── backend/          # FastAPI + SQLAlchemy + Alembic
│   ├── app/
│   │   ├── routers/  # API endpoints
│   │   ├── core/     # Auth, email, CSRF, audit
│   │   ├── models.py
│   │   └── schemas.py
│   └── migrations/
├── frontend/         # React SPA
│   └── src/
│       ├── pages/    # One file per screen
│       └── api.js    # HTTP client with CSRF
└── docs/
    └── ENGINEERING.md
```

## License

Open source — see repository for license details.
