"""GET /api/schedule"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session

from app.api.deps import get_db
from app.api.errors import json_error
from app.schemas.scheduling import (
    BatchOut,
    DependencyOut,
    EquipmentOut,
    ScheduleOut,
    UnitOperationOut,
    ViolationOut,
)
from app.services.scheduling import SchedulingService

router = APIRouter(tags=["schedule"])


@router.get("/schedule", response_model=ScheduleOut)
def get_schedule(
    start_date: date = Query(...),
    end_date: date = Query(...),
    session: Session = Depends(get_db),
) -> ScheduleOut | JSONResponse:
    if end_date <= start_date:
        return json_error(
            422,
            "validation_error",
            "end_date must be after start_date",
        )

    svc = SchedulingService(session)
    equipment, batches, ops, deps = svc.list_schedule_window(
        start_date=start_date,
        end_date=end_date,
    )
    violations = svc.evaluate_violations(start_date=start_date, end_date=end_date)

    return ScheduleOut(
        start_date=start_date,
        end_date=end_date,
        equipment=[EquipmentOut.model_validate(e) for e in equipment],
        batches=[BatchOut.model_validate(b) for b in batches],
        unit_operations=[UnitOperationOut.model_validate(o) for o in ops],
        dependencies=[DependencyOut.model_validate(d) for d in deps],
        violations=[
            ViolationOut(
                rule_id=v.rule_id,
                message=v.message,
                operation_ids=list(v.operation_ids),
            )
            for v in violations
        ],
    )
