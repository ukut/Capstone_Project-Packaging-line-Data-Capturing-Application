"""FastAPI application entry point.

Wires together middleware, routes, templates, and lifespan handlers.
Kept minimal — heavy lifting lives in routes/, services/, repositories/.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings

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

    # Health check for Render / Docker
    @app.get("/health", response_class=HTMLResponse, include_in_schema=False)
    async def health():
        return "OK"

    # Landing page placeholder — Sprint 1 replaces this with login redirect
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def index(request: Request):
        return templates.TemplateResponse(
            request,
            "index.html",
            {"app_env": settings.app_env},
        )

    # Routers attached in Sprint 1+:
    # from app.routes import auth, admin, operator, supervisor
    # app.include_router(auth.router)
    # app.include_router(admin.router)
    # app.include_router(operator.router)
    # app.include_router(supervisor.router)
    from app.routes import operator

    app.include_router(operator.router)
    return app


app = create_app()
