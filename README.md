# Open Source Study Randomizer

A web app for managing clinical study metadata, configuring randomization, and onboarding investigators. Built with **FastAPI** (backend) and **React + Vite** (frontend).

## What it does today

- **Admin** — first-run setup, create and manage organizer accounts
- **Organizer** — create studies, configure treatment arms and randomization, add investigators
- **Investigator** — receives system-generated credentials by email, logs in with Trial ID + username + password

## Documentation

→ **[docs/ENGINEERING.md](docs/ENGINEERING.md)** — architecture, setup, API, auth, database, and file locations.

## Quick start

### Prerequisites

Python 3.11+, Node.js 18+, PostgreSQL

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

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Bootstrap

1. Create admin via **First-Run Setup** on the home page
2. Log in at `/admin` → create an organizer
3. Log in at `/organizer` → create a study → add investigators at `/organizer/studies/{id}/investigators`

See [docs/ENGINEERING.md](docs/ENGINEERING.md) for SMTP configuration and production deployment.

## Project structure

```
.
├── backend/          # FastAPI + SQLAlchemy + Alembic
├── frontend/         # React SPA
└── docs/
    └── ENGINEERING.md
```

## License

Open source — see repository for license details.
