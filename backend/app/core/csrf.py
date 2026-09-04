from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..config import CSRF_COOKIE_NAME, CSRF_HEADER_NAME

CSRF_EXEMPT_PATHS = {
    "/",
    "/admin/login",
    "/organizer/login",
    "/doctor/login",
    "/doctor/signup",
    "/setup",
    "/setup/status",
}

CSRF_EXEMPT_PREFIXES = (
    "/doctor/invitations/",
)


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)

        if request.url.path in CSRF_EXEMPT_PATHS:
            return await call_next(request)

        if any(request.url.path.startswith(prefix) for prefix in CSRF_EXEMPT_PREFIXES):
            return await call_next(request)

        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)
        if not cookie_token or not header_token or cookie_token != header_token:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF validation failed."},
            )

        return await call_next(request)
