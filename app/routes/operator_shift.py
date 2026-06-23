"""Shift routes — start a shift and list the operator's shifts.

  GET  /operator/shift/new      -> render the 'open shift' form
  POST /operator/shift/new      -> open (or resume) a shift, redirect to entry
  GET  /operator/shifts         -> list this operator's shifts

Auth is added in B-01. For now a DEFAULT_OPERATOR_ID stands in for the logged-in
user so the flow is usable and testable. Replace with the current user later.
"""

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.shift import ShiftName
from app.repositories.shift_repo import ShiftRepository
from app.schemas.shift import ShiftCreate
from app.services.shift_service import ShiftService

router = APIRouter(prefix="/operator", tags=["operator-shift"])
templates = Jinja2Templates(directory="app/templates")

# Stand-in until auth lands (B-01). The seed creates operator1 as id 2 typically;
# resolved dynamically in the route to avoid a hardcoded mismatch.
DEFAULT_OPERATOR_USERNAME = "operator1"


def _resolve_operator_id(db: Session) -> int:
    """Temporary: look up the demo operator by username until auth exists."""
    from sqlalchemy import select

    from app.models.shift import Role, User

    user = (
        db.execute(select(User).where(User.username == DEFAULT_OPERATOR_USERNAME)).scalars().first()
    )
    if user is None:
        # Fall back to the first operator-role user, else first user.
        user = db.execute(select(User).where(User.role == Role.OPERATOR)).scalars().first()
    if user is None:
        user = db.execute(select(User)).scalars().first()
    return user.id if user else 1


@router.get("/shift/new", response_class=HTMLResponse)
def new_shift_form(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        request,
        "operator/new_shift.html",
        {
            "request": request,
            "today": date.today().isoformat(),
            "shift_names": list(ShiftName),
        },
    )


@router.post("/shift/new")
def open_shift(
    request: Request,
    db: Session = Depends(get_db),
    shift_date: str = Form(...),
    shift_name: str = Form(...),
    line: str | None = Form(None),
):
    operator_id = _resolve_operator_id(db)
    payload = ShiftCreate(shift_date=shift_date, shift_name=shift_name, line=line)
    shift = ShiftService(db).open_shift(payload, operator_id=operator_id)
    # Redirect into the entry form for the freshly opened/resumed shift.
    return RedirectResponse(url=f"/operator/shift/{shift.id}/entry", status_code=303)


@router.get("/shifts", response_class=HTMLResponse)
def list_shifts(request: Request, db: Session = Depends(get_db)):
    operator_id = _resolve_operator_id(db)
    shifts = ShiftRepository(db).list_for_operator(operator_id)
    return templates.TemplateResponse(
        request,
        "operator/shifts.html",
        {"request": request, "shifts": shifts},
    )
