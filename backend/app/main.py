from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import setup, admin, organizers

app = FastAPI(title="Study Randomizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(setup.router)
app.include_router(admin.router)
app.include_router(organizers.router)
