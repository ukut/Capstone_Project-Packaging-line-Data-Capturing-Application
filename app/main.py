"""FastAPI application entry point.

Wires together middleware, routes, templates, and lifespan handlers.
Kept minimal — heavy lifting lives in routes/, services/, repositories/.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.dependencies import AuthRequiredError, ForbiddenError, get_optional_user
from app.models.shift import User

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks. Currently a no-op — DB schema is created via scripts/."""
    yield


def create_app() -> FastAPI:
    """Application factory. Useful for testing and for future multi-config setups."""
    app = FastAPI(
        title="Bottling Line Data Capture",
        description="Operator data entry and supervisor review for bottling line production",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Session middleware for cookie-based auth
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.app_secret_key,
        session_cookie=settings.session_cookie_name,
        max_age=settings.session_lifetime_minutes * 60,
        https_only=settings.session_cookie_secure,
        same_site="lax",
    )

    # Static files
    app.mount(
        "/static",
        StaticFiles(directory=str(BASE_DIR / "static")),
        name="static",
    )

    # --- auth exception handlers ---
    # A login-required route raised AuthRequiredError -> bounce to /login,
    # remembering where the user was headed.
    @app.exception_handler(AuthRequiredError)
    async def _auth_required(request: Request, exc: AuthRequiredError):
        target = "/login"
        if exc.next_url and exc.next_url not in ("/", "/login"):
            target = f"/login?next={quote(exc.next_url, safe='')}"
        return RedirectResponse(url=target, status_code=303)

    # A logged-in user hit a route their role can't access -> 403 page.
    @app.exception_handler(ForbiddenError)
    async def _forbidden(request: Request, exc: ForbiddenError):
        return templates.TemplateResponse(
            request, "403.html", {"detail": exc.detail}, status_code=403
        )

    # Health check for Render / Docker
    @app.get("/health", response_class=HTMLResponse, include_in_schema=False)
    async def health():
        return "OK"

    # Landing page. Renders differently for anonymous vs logged-in users; the
    # template shows role-appropriate links when current_user is set.
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def index(request: Request, current_user: User | None = Depends(get_optional_user)):
        return templates.TemplateResponse(
            request,
            "index.html",
            {"app_env": settings.app_env, "current_user": current_user},
        )

    # Routers
    from app.routes import auth, operator, operator_shift, supervisor

    app.include_router(auth.router)
    app.include_router(operator.router)
    app.include_router(operator_shift.router)
    app.include_router(supervisor.router)
    return app


app = create_app()
