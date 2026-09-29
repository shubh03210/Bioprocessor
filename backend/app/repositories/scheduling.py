"""Data-access helpers for scheduling entities."""

from __future__ import annotations

from datetime import date

from sqlmodel import Session, select

from app.models import (
    Batch,
    Equipment,
    UnitOperation,
    UnitOperationDependency,
)


# ----- Equipment -----


def list_equipment(session: Session) -> list[Equipment]:
    return list(session.exec(select(Equipment).order_by(Equipment.id)).all())


def get_equipment_by_id(session: Session, equipment_id: int) -> Equipment | None:
    return session.get(Equipment, equipment_id)


def get_equipment_by_name(session: Session, name: str) -> Equipment | None:
    return session.exec(select(Equipment).where(Equipment.name == name)).first()


# ----- Batch -----


def list_batches(session: Session) -> list[Batch]:
    return list(session.exec(select(Batch).order_by(Batch.id)).all())


def get_batch(session: Session, batch_id: int) -> Batch | None:
    return session.get(Batch, batch_id)


def get_batch_by_name(session: Session, name: str) -> Batch | None:
    return session.exec(select(Batch).where(Batch.name == name)).first()


def create_batch(
    session: Session,
    *,
    name: str,
    start_date: date,
    end_date: date,
    commit: bool = True,
) -> Batch:
    batch = Batch(name=name, start_date=start_date, end_date=end_date)
    session.add(batch)
    if commit:
        session.commit()
        session.refresh(batch)
    else:
        session.flush()
    return batch


# ----- UnitOperation -----


def list_unit_operations(session: Session) -> list[UnitOperation]:
    return list(session.exec(select(UnitOperation).order_by(UnitOperation.id)).all())


def get_unit_operation(session: Session, op_id: int) -> UnitOperation | None:
    return session.get(UnitOperation, op_id)


def list_unit_operations_for_batch(session: Session, batch_id: int) -> list[UnitOperation]:
    return list(
        session.exec(
            select(UnitOperation)
            .where(UnitOperation.batch_id == batch_id)
            .order_by(UnitOperation.start_date, UnitOperation.id)
        ).all()
    )


def list_unit_operations_intersecting_range(
    session: Session,
    *,
    start_date: date,
    end_date: date,
) -> list[UnitOperation]:
    """Ops whose [start, end) intersects [start_date, end_date)."""
    return list(
        session.exec(
            select(UnitOperation)
            .where(UnitOperation.start_date < end_date)
            .where(UnitOperation.end_date > start_date)
            .order_by(UnitOperation.start_date, UnitOperation.id)
        ).all()
    )


def create_unit_operation(
    session: Session,
    *,
    name: str,
    type: str,
    color: str,
    status: str,
    start_date: date,
    end_date: date,
    batch_id: int,
    equipment_id: int,
    commit: bool = True,
) -> UnitOperation:
    op = UnitOperation(
        name=name,
        type=type,
        color=color,
        status=status,
        start_date=start_date,
        end_date=end_date,
        batch_id=batch_id,
        equipment_id=equipment_id,
    )
    session.add(op)
    if commit:
        session.commit()
        session.refresh(op)
    else:
        session.flush()
    return op


def update_unit_operation(
    session: Session,
    op: UnitOperation,
    *,
    commit: bool = True,
    **fields,
) -> UnitOperation:
    for key, value in fields.items():
        if value is not None and hasattr(op, key):
            setattr(op, key, value)
    session.add(op)
    if commit:
        session.commit()
        session.refresh(op)
    else:
        session.flush()
    return op


def delete_unit_operation(
    session: Session,
    op: UnitOperation,
    *,
    commit: bool = True,
) -> None:
    session.delete(op)
    if commit:
        session.commit()
    else:
        session.flush()


# ----- Dependencies -----


def list_dependencies(session: Session) -> list[UnitOperationDependency]:
    return list(
        session.exec(select(UnitOperationDependency).order_by(UnitOperationDependency.id)).all()
    )


def create_dependency(
    session: Session,
    *,
    from_unitop_id: int,
    to_unitop_id: int,
    commit: bool = True,
) -> UnitOperationDependency:
    dep = UnitOperationDependency(
        from_unitop_id=from_unitop_id,
        to_unitop_id=to_unitop_id,
    )
    session.add(dep)
    if commit:
        session.commit()
        session.refresh(dep)
    else:
        session.flush()
    return dep
