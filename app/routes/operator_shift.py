"""Shift routes — start a shift and list the operator's shifts.

  GET  /operator/shift/new      -> render the 'open shift' form
  POST /operator/shift/new      -> open (or resume) a shift, redirect to entry
  GET  /operator/shifts         -> list this operator's shifts

These routes require a logged-in user (B-01). The current user *is* the operator
for the shift — there is no longer a stand-in. Operators, supervisors, and admins
may open and list shifts; supervisors get an additional review screen of their own.
"""

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.shift import Role, ShiftName, User
from app.repositories.shift_repo import ShiftRepository
from app.schemas.shift import ShiftCreate
from app.services.shift_service import ShiftService

router = APIRouter(prefix="/operator", tags=["operator-shift"])
templates = Jinja2Templates(directory="app/templates")

# Who may use the operator data-entry screens. Supervisors can key events as
# well as review them, so they're included alongside operators and admins.
operator_access = require_role(Role.OPERATOR, Role.SUPERVISOR, Role.ADMIN)


@router.get("/shift/new", response_class=HTMLResponse)
def new_shift_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_access),
):
    return templates.TemplateResponse(
        request,
        "operator/new_shift.html",
        {
            "request": request,
            "today": date.today().isoformat(),
            "shift_names": list(ShiftName),
            "current_user": current_user,
        },
    )


@router.post("/shift/new")
def open_shift(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_access),
    shift_date: str = Form(...),
    shift_name: str = Form(...),
    line: str | None = Form(None),
):
    payload = ShiftCreate(shift_date=shift_date, shift_name=shift_name, line=line)
    shift = ShiftService(db).open_shift(payload, operator_id=current_user.id)
    # Redirect into the entry form for the freshly opened/resumed shift.
    return RedirectResponse(url=f"/operator/shift/{shift.id}/entry", status_code=303)


@router.get("/shifts", response_class=HTMLResponse)
def list_shifts(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_access),
):
    shifts = ShiftRepository(db).list_for_operator(current_user.id)
    return templates.TemplateResponse(
        request,
        "operator/shifts.html",
        {"request": request, "shifts": shifts, "current_user": current_user},
    )
