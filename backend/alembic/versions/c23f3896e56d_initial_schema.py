"""initial_schema

Revision ID: c23f3896e56d
Revises:
Create Date: 2026-09-29 14:51:53.482896

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c23f3896e56d"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "batch",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.CheckConstraint("end_date > start_date", name="ck_batch_date_order"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("batch", schema=None) as batch_op:
        batch_op.create_index("ix_batch_dates", ["start_date", "end_date"], unique=False)

    op.create_table(
        "control_command",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("setpoint_name", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("apply_at_time_h", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("control_command", schema=None) as batch_op:
        batch_op.create_index("ix_control_command_apply_at", ["apply_at_time_h"], unique=False)
        batch_op.create_index("ix_control_command_created_at", ["created_at"], unique=False)
        batch_op.create_index(
            "ix_control_command_setpoint_status",
            ["setpoint_name", "status"],
            unique=False,
        )

    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("equipment", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_equipment_name"), ["name"], unique=True)

    op.create_table(
        "prediction",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("made_at_time_h", sa.Float(), nullable=False),
        sa.Column("target_time_h", sa.Float(), nullable=False),
        sa.Column("signal_name", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("prediction", schema=None) as batch_op:
        batch_op.create_index("ix_prediction_made_at", ["made_at_time_h"], unique=False)
        batch_op.create_index(
            "ix_prediction_signal_made_at",
            ["signal_name", "made_at_time_h"],
            unique=False,
        )
        batch_op.create_index("ix_prediction_target_time", ["target_time_h"], unique=False)

    op.create_table(
        "reading",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("time_h", sa.Float(), nullable=False),
        sa.Column("signal_name", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("reading", schema=None) as batch_op:
        batch_op.create_index("ix_reading_signal_time", ["signal_name", "time_h"], unique=False)
        batch_op.create_index("ix_reading_time_h", ["time_h"], unique=False)

    op.create_table(
        "unit_operation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("color", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "status IN ('draft', 'confirmed', 'completed')",
            name="ck_unit_operation_status",
        ),
        sa.CheckConstraint(
            "type IN ('Seed', 'Bioreactor', 'TFF', 'Spray', 'Sum')",
            name="ck_unit_operation_type",
        ),
        sa.CheckConstraint("end_date > start_date", name="ck_unit_operation_date_order"),
        sa.ForeignKeyConstraint(["batch_id"], ["batch.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("unit_operation", schema=None) as batch_op:
        batch_op.create_index("ix_unit_operation_batch_id", ["batch_id"], unique=False)
        batch_op.create_index(
            "ix_unit_operation_equipment_dates",
            ["equipment_id", "start_date", "end_date"],
            unique=False,
        )
        batch_op.create_index("ix_unit_operation_status", ["status"], unique=False)

    op.create_table(
        "unit_operation_dependency",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("from_unitop_id", sa.Integer(), nullable=False),
        sa.Column("to_unitop_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "from_unitop_id <> to_unitop_id",
            name="ck_unit_operation_dependency_not_self",
        ),
        sa.ForeignKeyConstraint(
            ["from_unitop_id"],
            ["unit_operation.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["to_unitop_id"],
            ["unit_operation.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "from_unitop_id",
            "to_unitop_id",
            name="uq_unit_operation_dependency_pair",
        ),
    )
    with op.batch_alter_table("unit_operation_dependency", schema=None) as batch_op:
        batch_op.create_index(
            "ix_unit_operation_dependency_from",
            ["from_unitop_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_unit_operation_dependency_to",
            ["to_unitop_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("unit_operation_dependency", schema=None) as batch_op:
        batch_op.drop_index("ix_unit_operation_dependency_to")
        batch_op.drop_index("ix_unit_operation_dependency_from")

    op.drop_table("unit_operation_dependency")
    with op.batch_alter_table("unit_operation", schema=None) as batch_op:
        batch_op.drop_index("ix_unit_operation_status")
        batch_op.drop_index("ix_unit_operation_equipment_dates")
        batch_op.drop_index("ix_unit_operation_batch_id")

    op.drop_table("unit_operation")
    with op.batch_alter_table("reading", schema=None) as batch_op:
        batch_op.drop_index("ix_reading_time_h")
        batch_op.drop_index("ix_reading_signal_time")

    op.drop_table("reading")
    with op.batch_alter_table("prediction", schema=None) as batch_op:
        batch_op.drop_index("ix_prediction_target_time")
        batch_op.drop_index("ix_prediction_signal_made_at")
        batch_op.drop_index("ix_prediction_made_at")

    op.drop_table("prediction")
    with op.batch_alter_table("equipment", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_equipment_name"))

    op.drop_table("equipment")
    with op.batch_alter_table("control_command", schema=None) as batch_op:
        batch_op.drop_index("ix_control_command_setpoint_status")
        batch_op.drop_index("ix_control_command_created_at")
        batch_op.drop_index("ix_control_command_apply_at")

    op.drop_table("control_command")
    with op.batch_alter_table("batch", schema=None) as batch_op:
        batch_op.drop_index("ix_batch_dates")

    op.drop_table("batch")
