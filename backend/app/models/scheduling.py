"""Scheduling ORM models (Part A)."""

from datetime import date
from typing import Optional

from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class Equipment(SQLModel, table=True):
    __tablename__ = "equipment"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=64, unique=True, index=True)

    unit_operations: list["UnitOperation"] = Relationship(back_populates="equipment")


class Batch(SQLModel, table=True):
    __tablename__ = "batch"
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="ck_batch_date_order"),
        Index("ix_batch_dates", "start_date", "end_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=128)
    start_date: date = Field(sa_column=Column(Date, nullable=False))
    end_date: date = Field(sa_column=Column(Date, nullable=False))

    unit_operations: list["UnitOperation"] = Relationship(back_populates="batch")


class UnitOperation(SQLModel, table=True):
    __tablename__ = "unit_operation"
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="ck_unit_operation_date_order"),
        CheckConstraint(
            "type IN ('Seed', 'Bioreactor', 'TFF', 'Spray', 'Sum')",
            name="ck_unit_operation_type",
        ),
        CheckConstraint(
            "status IN ('draft', 'confirmed', 'completed')",
            name="ck_unit_operation_status",
        ),
        Index(
            "ix_unit_operation_equipment_dates",
            "equipment_id",
            "start_date",
            "end_date",
        ),
        Index("ix_unit_operation_batch_id", "batch_id"),
        Index("ix_unit_operation_status", "status"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=128)
    type: str = Field(max_length=32)
    color: str = Field(max_length=32)
    status: str = Field(max_length=32)
    start_date: date = Field(sa_column=Column(Date, nullable=False))
    end_date: date = Field(sa_column=Column(Date, nullable=False))
    batch_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("batch.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    equipment_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("equipment.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )

    batch: Optional[Batch] = Relationship(back_populates="unit_operations")
    equipment: Optional[Equipment] = Relationship(back_populates="unit_operations")


class UnitOperationDependency(SQLModel, table=True):
    """Explicit must-finish-before link. ON DELETE RESTRICT (ADR design choice)."""

    __tablename__ = "unit_operation_dependency"
    __table_args__ = (
        CheckConstraint(
            "from_unitop_id <> to_unitop_id",
            name="ck_unit_operation_dependency_not_self",
        ),
        UniqueConstraint(
            "from_unitop_id",
            "to_unitop_id",
            name="uq_unit_operation_dependency_pair",
        ),
        Index("ix_unit_operation_dependency_from", "from_unitop_id"),
        Index("ix_unit_operation_dependency_to", "to_unitop_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    from_unitop_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("unit_operation.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    to_unitop_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("unit_operation.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
