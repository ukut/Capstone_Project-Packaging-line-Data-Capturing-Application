"""Operator routes — the loss-event entry screen.

Three endpoints:
  GET  /operator/shift/{id}/entry         -> render the entry form
  POST /operator/shift/{id}/entry         -> create an event, re-render with the
                                             updated event list
  GET  /operator/loss-type/{id}/bcs       -> HTMX partial: the suggested BCS
                                             option for a chosen Type of Loss

All three require a logged-in operator (or admin). The created_by of each loss
event is now the authenticated user, not the shift's operator field — they're
usually the same, but attribution should follow whoever actually keyed the row.
"""

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.shift import Role, Shift, User
from app.repositories.loss_event_repo import LookupRepository, LossEventRepository
from app.schemas.loss_event import LossEventCreate
from app.services.derived import derive_fields
from app.services.loss_classification import suggest_bcs_for_loss_type
from app.services.loss_event_service import (
    InvalidEventTimingError,
    LossEventService,
    ShiftNotEditableError,
)

router = APIRouter(prefix="/operator", tags=["operator"])
templates = Jinja2Templates(directory="app/templates")

operator_access = require_role(Role.OPERATOR, Role.SUPERVISOR, Role.ADMIN)


def _entry_context(
    request: Request,
    db: Session,
    shift: Shift,
    current_user: User,
    error: str | None = None,
):
    """Assemble everything the entry template needs."""
    lookups = LookupRepository(db)
    events = LossEventRepository(db).list_for_shift(shift.id)
    rows = [
        {"event": e, "derived": derive_fields(e.event_date, e.event_start, e.event_stop)}
        for e in events
    ]
    return {
        "request": request,
        "shift": shift,
        "skus": lookups.active_skus(),
        "machines": lookups.active_machines(),
        "loss_types": lookups.active_loss_types(),
        "bcs_categories": lookups.active_bcs_categories(),
        "rows": rows,
        "error": error,
        "current_user": current_user,
    }


@router.get("/shift/{shift_id}/entry", response_class=HTMLResponse)
def entry_form(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_access),
):
    shift = db.get(Shift, shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    return templates.TemplateResponse(
        request, "operator/entry.html", _entry_context(request, db, shift, current_user)
    )


@router.post("/shift/{shift_id}/entry", response_class=HTMLResponse)
def submit_event(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_access),
    event_date: str = Form(...),
    event_start: str = Form(...),
    event_stop: str = Form(...),
    sku_id: int = Form(...),
    machine_id: int = Form(...),
    loss_type_id: int = Form(...),
    bcs_category_id: int = Form(...),
    functional_failure_description: str | None = Form(None),
    failure_mode_description: str | None = Form(None),
):
    shift = db.get(Shift, shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")

    error = None
    try:
        payload = LossEventCreate(
            event_date=event_date,
            event_start=event_start,
            event_stop=event_stop,
            sku_id=sku_id,
            machine_id=machine_id,
            loss_type_id=loss_type_id,
            bcs_category_id=bcs_category_id,
            functional_failure_description=functional_failure_description,
            failure_mode_description=failure_mode_description,
        )
        LossEventService(db).create_event(shift, payload, created_by_id=current_user.id)
    except (ShiftNotEditableError, InvalidEventTimingError) as exc:
        error = str(exc)
    except ValueError as exc:
        error = f"Invalid input: {exc}"

    return templates.TemplateResponse(
        request,
        "operator/entry.html",
        _entry_context(request, db, shift, current_user, error=error),
    )


@router.get("/loss-type/{loss_type_id}/bcs", response_class=HTMLResponse)
def suggest_bcs(
    loss_type_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(operator_access),
):
    """HTMX partial: returns BCS <option> tags with the suggested one pre-selected."""
    lookups = LookupRepository(db)
    loss_type = lookups.get_loss_type(loss_type_id)
    suggested = (
        suggest_bcs_for_loss_type(loss_type, lookups.bcs_by_code_map()) if loss_type else None
    )
    suggested_id = suggested.id if suggested else None
    return templates.TemplateResponse(
        request,
        "operator/_bcs_options.html",
        {
            "request": request,
            "bcs_categories": lookups.active_bcs_categories(),
            "suggested_id": suggested_id,
        },
    )
