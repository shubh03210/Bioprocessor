"""POST/PUT/DELETE /api/unit_operations — ADR-005 Option B (save-and-return)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from app.api.deps import get_db
from app.schemas.scheduling import (
    UnitOperationCreate,
    UnitOperationMutationResult,
    UnitOperationOut,
    UnitOperationUpdate,
    ViolationOut,
)
from app.services.scheduling import SchedulingService

router = APIRouter(prefix="/unit_operations", tags=["unit_operations"])


def _violations_out(svc: SchedulingService) -> list[ViolationOut]:
    return [
        ViolationOut(
            rule_id=v.rule_id,
            message=v.message,
            operation_ids=list(v.operation_ids),
        )
        for v in svc.evaluate_violations()
    ]


@router.post(
    "",
    response_model=UnitOperationMutationResult,
    status_code=status.HTTP_201_CREATED,
)
def create_unit_operation(
    body: UnitOperationCreate,
    session: Session = Depends(get_db),
) -> UnitOperationMutationResult:
    """ADR-005 Option B: persist even when schedule rules are violated; return violations."""
    svc = SchedulingService(session)
    op = svc.create_unit_operation(**body.model_dump())
    return UnitOperationMutationResult(
        unit_operation=UnitOperationOut.model_validate(op),
        violations=_violations_out(svc),
    )


@router.put("/{op_id}", response_model=UnitOperationMutationResult)
def update_unit_operation(
    op_id: int,
    body: UnitOperationUpdate,
    session: Session = Depends(get_db),
) -> UnitOperationMutationResult:
    """Full replace. DR-005 blocks completed moves; other rules save-and-return."""
    svc = SchedulingService(session)
    op = svc.update_unit_operation(op_id, **body.model_dump())
    return UnitOperationMutationResult(
        unit_operation=UnitOperationOut.model_validate(op),
        violations=_violations_out(svc),
    )


@router.delete("/{op_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unit_operation(
    op_id: int,
    session: Session = Depends(get_db),
) -> Response:
    svc = SchedulingService(session)
    svc.delete_unit_operation(op_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
