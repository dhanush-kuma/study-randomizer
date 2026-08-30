# Open Source Study Randomizer

Basic React + FastAPI project scaffold.

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   └── requirements.txt
└── frontend/
    └── (Vite + React app)
```

## Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API runs at `http://localhost:8000`. Hello World endpoint: `GET /`

## Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:5173` and fetches "Hello World" from the backend.

Run both servers in separate terminals for the full flow to work.
