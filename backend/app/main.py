import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import CORS_ORIGINS, IS_PRODUCTION
from .core.csrf import CSRFMiddleware
from .core.rate_limit import limiter
from .core.security_headers import SecurityHeadersMiddleware
from .routers import setup, admin, organizers, organizer, doctor

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Study Randomizer API",
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(setup.router)
app.include_router(admin.router)
app.include_router(organizers.router)
app.include_router(organizer.router)
app.include_router(doctor.router)
