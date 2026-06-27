"""Authentication routes — login and logout.

  GET  /login   -> render the login form (already-logged-in users are bounced
                   to their home page)
  POST /login   -> validate credentials; on success store user_id in the
                   session and redirect to ?next= (or home); on failure
                   re-render the form with a generic error (HTTP 200)
  POST /logout  -> clear the session and return to /login

Why POST for logout: logging out changes state, so it shouldn't be reachable by
a stray GET (a prefetch or an <img> tag could otherwise log a user out). The nav
uses a small POST form button.

The `next` parameter is sanitised to a same-site path so the redirect can't be
abused to send a user to an external URL after login (open-redirect guard).
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.dependencies import SESSION_USER_KEY, get_db, get_optional_user
from app.models.shift import User
from app.schemas.auth import LoginInput
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")

# Where each role lands after login when no ?next= was supplied. Everything
# currently routes through the home page, which shows role-appropriate links;
# the supervisor/admin stories will point these at their own dashboards.
DEFAULT_LANDING = "/"


def _safe_next(next_url: str | None) -> str:
    """Return `next_url` only if it's a local path; otherwise the default.

    Guards against open redirects: we accept '/operator/...' but reject absolute
    URLs ('http://evil') and protocol-relative ones ('//evil').
    """
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return DEFAULT_LANDING


@router.get("/login", response_class=HTMLResponse)
def login_form(
    request: Request,
    next: str | None = None,
    user: User | None = Depends(get_optional_user),
):
    if user is not None:
        return RedirectResponse(url=_safe_next(next), status_code=303)
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"next": next or "", "error": None},
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form(""),
):
    creds = LoginInput(username=username, password=password)
    user = AuthService(db).authenticate(creds.username, creds.password)
    if user is None:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"next": next, "error": "Invalid username or password."},
            status_code=401,
        )
    # Success: record the user and start a fresh session id.
    request.session[SESSION_USER_KEY] = user.id
    return RedirectResponse(url=_safe_next(next), status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
