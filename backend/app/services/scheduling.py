"""Scheduling application service — CRUD + domain rule evaluation."""

from __future__ import annotations

from datetime import date

from sqlmodel import Session

from app.domain.scheduling_rules import (
    Violation,
    batch_from_model,
    check_completed_immutability,
    dep_from_model,
    evaluate_schedule,
    filter_violations_for_window,
    op_from_model,
)
from app.models import Batch, Equipment, UnitOperation, UnitOperationDependency
from app.repositories import scheduling as repo


class NotFoundError(Exception):
    def __init__(self, entity: str, entity_id: int | str):
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} not found: {entity_id}")


class DomainViolationError(Exception):
    """Raised when a mutation is blocked by domain rules (e.g. DR-005)."""

    def __init__(self, violations: list[Violation]):
        self.violations = violations
        messages = "; ".join(v.message for v in violations)
        super().__init__(messages)


class SchedulingService:
    def __init__(self, session: Session):
        self.session = session

    # Equipment
    def list_equipment(self) -> list[Equipment]:
        return repo.list_equipment(self.session)

    def get_equipment(self, equipment_id: int) -> Equipment:
        row = repo.get_equipment_by_id(self.session, equipment_id)
        if row is None:
            raise NotFoundError("equipment", equipment_id)
        return row

    # Batches
    def list_batches(self) -> list[Batch]:
        return repo.list_batches(self.session)

    def get_batch(self, batch_id: int) -> Batch:
        row = repo.get_batch(self.session, batch_id)
        if row is None:
            raise NotFoundError("batch", batch_id)
        return row

    def create_batch(self, *, name: str, start_date: date, end_date: date) -> Batch:
        return repo.create_batch(
            self.session,
            name=name,
            start_date=start_date,
            end_date=end_date,
        )

    # Unit operations
    def list_unit_operations(self) -> list[UnitOperation]:
        return repo.list_unit_operations(self.session)

    def get_unit_operation(self, op_id: int) -> UnitOperation:
        row = repo.get_unit_operation(self.session, op_id)
        if row is None:
            raise NotFoundError("unit_operation", op_id)
        return row

    def create_unit_operation(
        self,
        *,
        name: str,
        type: str,
        color: str,
        status: str,
        start_date: date,
        end_date: date,
        batch_id: int,
        equipment_id: int,
    ) -> UnitOperation:
        if repo.get_batch(self.session, batch_id) is None:
            raise NotFoundError("batch", batch_id)
        if repo.get_equipment_by_id(self.session, equipment_id) is None:
            raise NotFoundError("equipment", equipment_id)
        return repo.create_unit_operation(
            self.session,
            name=name,
            type=type,
            color=color,
            status=status,
            start_date=start_date,
            end_date=end_date,
            batch_id=batch_id,
            equipment_id=equipment_id,
        )

    def update_unit_operation(self, op_id: int, **fields) -> UnitOperation:
        op = self.get_unit_operation(op_id)
        if "batch_id" in fields and fields["batch_id"] is not None:
            if repo.get_batch(self.session, fields["batch_id"]) is None:
                raise NotFoundError("batch", fields["batch_id"])
        if "equipment_id" in fields and fields["equipment_id"] is not None:
            if repo.get_equipment_by_id(self.session, fields["equipment_id"]) is None:
                raise NotFoundError("equipment", fields["equipment_id"])

        existing = op_from_model(op)
        from app.domain.scheduling_rules import OpView

        proposed = OpView(
            id=existing.id,
            name=fields.get("name", existing.name),
            type=fields.get("type", existing.type),
            status=fields.get("status", existing.status),
            start_date=fields.get("start_date", existing.start_date),
            end_date=fields.get("end_date", existing.end_date),
            batch_id=fields.get("batch_id", existing.batch_id),
            equipment_id=fields.get("equipment_id", existing.equipment_id),
        )
        blocked = check_completed_immutability(existing=existing, proposed=proposed)
        if blocked is not None:
            raise DomainViolationError([blocked])

        return repo.update_unit_operation(self.session, op, **fields)

    def delete_unit_operation(self, op_id: int) -> None:
        op = self.get_unit_operation(op_id)
        blocked = check_completed_immutability(
            existing=op_from_model(op),
            is_delete=True,
        )
        if blocked is not None:
            raise DomainViolationError([blocked])
        repo.delete_unit_operation(self.session, op)

    def list_schedule_window(
        self, *, start_date: date, end_date: date
    ) -> tuple[list[Equipment], list[Batch], list[UnitOperation], list[UnitOperationDependency]]:
        """Load entities needed for a Gantt window."""
        equipment = repo.list_equipment(self.session)
        ops = repo.list_unit_operations_intersecting_range(
            self.session, start_date=start_date, end_date=end_date
        )
        batch_ids = {op.batch_id for op in ops}
        batches = [b for b in repo.list_batches(self.session) if b.id in batch_ids]
        op_ids = {op.id for op in ops}
        deps = [
            d
            for d in repo.list_dependencies(self.session)
            if d.from_unitop_id in op_ids or d.to_unitop_id in op_ids
        ]
        return equipment, batches, ops, deps

    def evaluate_violations(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Violation]:
        """Evaluate DR-001–DR-004 on the persisted schedule.

        If a date window is provided, keep violations that involve any op
        intersecting that window.
        """
        batches = [batch_from_model(b) for b in repo.list_batches(self.session)]
        ops = [op_from_model(o) for o in repo.list_unit_operations(self.session)]
        deps = [dep_from_model(d) for d in repo.list_dependencies(self.session)]
        equipment_names = {
            e.id: e.name for e in repo.list_equipment(self.session) if e.id is not None
        }
        violations = evaluate_schedule(
            batches=batches,
            ops=ops,
            deps=deps,
            equipment_names=equipment_names,
        )
        if start_date is not None and end_date is not None:
            window_ops = repo.list_unit_operations_intersecting_range(
                self.session, start_date=start_date, end_date=end_date
            )
            window_ids = {o.id for o in window_ops if o.id is not None}
            return filter_violations_for_window(violations, window_ids)
        return violations

    def create_dependency(
        self, *, from_unitop_id: int, to_unitop_id: int
    ) -> UnitOperationDependency:
        self.get_unit_operation(from_unitop_id)
        self.get_unit_operation(to_unitop_id)
        return repo.create_dependency(
            self.session,
            from_unitop_id=from_unitop_id,
            to_unitop_id=to_unitop_id,
        )
