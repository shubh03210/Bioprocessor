"""Pydantic schemas for scheduling APIs."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

UnitOpType = Literal["Seed", "Bioreactor", "TFF", "Spray", "Sum"]
UnitOpStatus = Literal["draft", "confirmed", "completed"]


class EquipmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_date: date
    end_date: date


class UnitOperationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: UnitOpType
    color: str
    status: UnitOpStatus
    start_date: date
    end_date: date
    batch_id: int
    equipment_id: int


class DependencyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_unitop_id: int
    to_unitop_id: int


class ViolationOut(BaseModel):
    rule_id: str
    message: str
    operation_ids: list[int]


class ScheduleOut(BaseModel):
    start_date: date
    end_date: date
    equipment: list[EquipmentOut]
    batches: list[BatchOut]
    unit_operations: list[UnitOperationOut]
    dependencies: list[DependencyOut]
    violations: list[ViolationOut]


class UnitOperationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: UnitOpType
    color: str = Field(min_length=1, max_length=32)
    status: UnitOpStatus = "draft"
    start_date: date
    end_date: date
    batch_id: int
    equipment_id: int

    @model_validator(mode="after")
    def end_after_start(self) -> UnitOperationCreate:
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class UnitOperationUpdate(BaseModel):
    """Full resource replace (PUT)."""

    name: str = Field(min_length=1, max_length=128)
    type: UnitOpType
    color: str = Field(min_length=1, max_length=32)
    status: UnitOpStatus
    start_date: date
    end_date: date
    batch_id: int
    equipment_id: int

    @model_validator(mode="after")
    def end_after_start(self) -> UnitOperationUpdate:
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class UnitOperationMutationResult(BaseModel):
    unit_operation: UnitOperationOut
    violations: list[ViolationOut]
