"""Supervisor routes — review dashboard, shift review, approve and lock.

  GET  /supervisor                       -> dashboard (Pending / Approved / Locked)
  GET  /supervisor/shift/{id}            -> review one shift: events + anomalies
  POST /supervisor/shift/{id}/approve    -> PENDING_REVIEW -> APPROVED
  POST /supervisor/shift/{id}/lock       -> APPROVED -> LOCKED

All routes require a supervisor (or admin). Anomalies are evaluated live by the
ReviewService when a shift is rendered, so the rule set can grow without a
migration. An illegal transition (e.g. approving a shift that isn't pending)
raises InvalidShiftTransitionError, which we catch and surface as an error
banner on the review page rather than a 500.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.shift import Role, User
from app.services.export_service import ExportService
from app.services.review_service import ReviewService
from app.services.shift_service import InvalidShiftTransitionError

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

router = APIRouter(prefix="/supervisor", tags=["supervisor"])
templates = Jinja2Templates(directory="app/templates")

supervisor_access = require_role(Role.SUPERVISOR, Role.ADMIN)


@router.get("", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(supervisor_access),
):
    groups = ReviewService(db).dashboard()
    return templates.TemplateResponse(
        request,
        "supervisor/dashboard.html",
        {"request": request, "groups": groups, "current_user": current_user},
    )


def _render_review(
    request: Request, db: Session, shift_id: int, current_user: User, error: str | None = None
):
    detail = ReviewService(db).get_review(shift_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    return templates.TemplateResponse(
        request,
        "supervisor/review.html",
        {
            "request": request,
            "detail": detail,
            "current_user": current_user,
            "error": error,
        },
    )


@router.get("/shift/{shift_id}", response_class=HTMLResponse)
def review_shift(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(supervisor_access),
):
    return _render_review(request, db, shift_id, current_user)


@router.post("/shift/{shift_id}/approve")
def approve_shift(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(supervisor_access),
):
    service = ReviewService(db)
    shift = service.shifts.get(shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    try:
        service.approve(shift, supervisor_id=current_user.id)
    except InvalidShiftTransitionError as exc:
        return _render_review(request, db, shift_id, current_user, error=str(exc))
    return RedirectResponse(url=f"/supervisor/shift/{shift_id}", status_code=303)


@router.post("/shift/{shift_id}/lock")
def lock_shift(
    shift_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(supervisor_access),
):
    service = ReviewService(db)
    shift = service.shifts.get(shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    try:
        service.lock(shift, supervisor_id=current_user.id)
    except InvalidShiftTransitionError as exc:
        return _render_review(request, db, shift_id, current_user, error=str(exc))
    return RedirectResponse(url=f"/supervisor/shift/{shift_id}", status_code=303)


@router.get("/shift/{shift_id}/export.xlsx")
def export_shift_xlsx(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(supervisor_access),
):
    """Download the shift's loss events in the legacy 18-column Excel layout."""
    export = ExportService(db)
    shift = ReviewService(db).shifts.get(shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found")
    content = export.build_xlsx_bytes(shift)
    headers = {"Content-Disposition": f'attachment; filename="{export.filename_for(shift)}"'}
    return Response(content=content, media_type=XLSX_MEDIA_TYPE, headers=headers)
