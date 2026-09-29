"""Seed helpers for Phase 1–2.

Schedule seed inserts ≥3 batches and ≥2 deliberate rule violations directly
into the DB (seed bypass). Domain validation arrives in Phase 3; until then
these rows exist so Part B can highlight them once APIs compute violations.
"""

from __future__ import annotations

from datetime import date

from sqlmodel import Session, select

from app.models import EQUIPMENT_SEED_NAMES, Batch, Equipment, UnitOperation
from app.models.constants import UnitOperationStatus, UnitOperationType
from app.repositories import scheduling as repo

# Stable batch names used for idempotent seeding
BATCH_ALPHA = "Batch Alpha"
BATCH_BRAVO = "Batch Bravo"
BATCH_CHARLIE = "Batch Charlie"

"""
Deliberate violations (documented for README):

1) DR-003 Equipment double-booking on 1.5L
   - Batch Bravo / "Bravo Bioreactor 1.5L": 2025-10-24 → 2025-10-31
   - Batch Charlie / "Charlie Seed 1.5L":   2025-10-29 → 2025-11-04
   (assignment-style overlap)

2) DR-002 Process ordering in Batch Charlie
   - "Charlie Seed 75L":       2025-10-21 → 2025-10-24 on 75L
   - "Charlie Bioreactor 1500L": 2025-10-23 → 2025-10-30 on 1500L
   (Bioreactor starts before Seed ends)

Batch Alpha is fully valid (control / clean schedule).
"""

DELIBERATE_VIOLATIONS: tuple[dict[str, str], ...] = (
    {
        "rule_id": "DR-003",
        "ops": "Bravo Bioreactor 1.5L + Charlie Seed 1.5L",
        "detail": "Same equipment 1.5L overlapping Oct 29-Oct 30",
    },
    {
        "rule_id": "DR-002",
        "ops": "Charlie Seed 75L + Charlie Bioreactor 1500L",
        "detail": "Bioreactor starts Oct 23 before Seed ends Oct 24",
    },
)


def seed_equipment(session: Session) -> list[Equipment]:
    """Idempotently insert the five assignment equipment names."""
    existing = {
        row.name: row for row in session.exec(select(Equipment)).all()
    }
    created: list[Equipment] = []
    for name in EQUIPMENT_SEED_NAMES:
        if name in existing:
            continue
        equipment = Equipment(name=name)
        session.add(equipment)
        created.append(equipment)
    if created:
        session.commit()
        for item in created:
            session.refresh(item)
    return list(session.exec(select(Equipment).order_by(Equipment.id)).all())


def seed_schedule(session: Session) -> dict:
    """Idempotently load demo schedule if Batch Alpha is missing.

    Returns a summary dict for CLI/tests.
    """
    equipment = {e.name: e for e in seed_equipment(session)}
    required = ("1.5L", "15L", "20L", "75L", "1500L")
    missing_eq = [n for n in required if n not in equipment]
    if missing_eq:
        raise RuntimeError(f"Equipment seed incomplete: {missing_eq}")

    if repo.get_batch_by_name(session, BATCH_ALPHA) is not None:
        batches = repo.list_batches(session)
        ops = repo.list_unit_operations(session)
        deps = repo.list_dependencies(session)
        return {
            "created": False,
            "batches": len(batches),
            "unit_operations": len(ops),
            "dependencies": len(deps),
            "deliberate_violations": list(DELIBERATE_VIOLATIONS),
        }

    # --- Batch Alpha (valid) ---
    alpha = repo.create_batch(
        session,
        name=BATCH_ALPHA,
        start_date=date(2025, 10, 1),
        end_date=date(2025, 11, 1),
        commit=False,
    )
    alpha_seed = repo.create_unit_operation(
        session,
        name="Alpha Seed 1.5L",
        type=UnitOperationType.SEED.value,
        color="#4C9F70",
        status=UnitOperationStatus.CONFIRMED.value,
        start_date=date(2025, 10, 21),
        end_date=date(2025, 10, 24),
        batch_id=alpha.id,  # type: ignore[arg-type]
        equipment_id=equipment["1.5L"].id,  # type: ignore[arg-type]
        commit=False,
    )
    alpha_br = repo.create_unit_operation(
        session,
        name="Alpha Bioreactor 15L",
        type=UnitOperationType.BIOREACTOR.value,
        color="#2F6FED",
        status=UnitOperationStatus.CONFIRMED.value,
        start_date=date(2025, 10, 24),
        end_date=date(2025, 10, 31),
        batch_id=alpha.id,  # type: ignore[arg-type]
        equipment_id=equipment["15L"].id,  # type: ignore[arg-type]
        commit=False,
    )
    repo.create_dependency(
        session,
        from_unitop_id=alpha_seed.id,  # type: ignore[arg-type]
        to_unitop_id=alpha_br.id,  # type: ignore[arg-type]
        commit=False,
    )

    # --- Batch Bravo (participates in DR-003) ---
    bravo = repo.create_batch(
        session,
        name=BATCH_BRAVO,
        start_date=date(2025, 10, 15),
        end_date=date(2025, 11, 10),
        commit=False,
    )
    repo.create_unit_operation(
        session,
        name="Bravo Seed 20L",
        type=UnitOperationType.SEED.value,
        color="#E6A23C",
        status=UnitOperationStatus.DRAFT.value,
        start_date=date(2025, 10, 20),
        end_date=date(2025, 10, 24),
        batch_id=bravo.id,  # type: ignore[arg-type]
        equipment_id=equipment["20L"].id,  # type: ignore[arg-type]
        commit=False,
    )
    # Deliberate DR-003 participant
    repo.create_unit_operation(
        session,
        name="Bravo Bioreactor 1.5L",
        type=UnitOperationType.BIOREACTOR.value,
        color="#E6A23C",
        status=UnitOperationStatus.CONFIRMED.value,
        start_date=date(2025, 10, 24),
        end_date=date(2025, 10, 31),
        batch_id=bravo.id,  # type: ignore[arg-type]
        equipment_id=equipment["1.5L"].id,  # type: ignore[arg-type]
        commit=False,
    )

    # --- Batch Charlie (DR-002 + DR-003 participant) ---
    charlie = repo.create_batch(
        session,
        name=BATCH_CHARLIE,
        start_date=date(2025, 10, 15),
        end_date=date(2025, 11, 15),
        commit=False,
    )
    # Deliberate DR-002: Seed ends Oct 24; Bioreactor starts Oct 23
    repo.create_unit_operation(
        session,
        name="Charlie Seed 75L",
        type=UnitOperationType.SEED.value,
        color="#C4564E",
        status=UnitOperationStatus.CONFIRMED.value,
        start_date=date(2025, 10, 21),
        end_date=date(2025, 10, 24),
        batch_id=charlie.id,  # type: ignore[arg-type]
        equipment_id=equipment["75L"].id,  # type: ignore[arg-type]
        commit=False,
    )
    repo.create_unit_operation(
        session,
        name="Charlie Bioreactor 1500L",
        type=UnitOperationType.BIOREACTOR.value,
        color="#C4564E",
        status=UnitOperationStatus.DRAFT.value,
        start_date=date(2025, 10, 23),
        end_date=date(2025, 10, 30),
        batch_id=charlie.id,  # type: ignore[arg-type]
        equipment_id=equipment["1500L"].id,  # type: ignore[arg-type]
        commit=False,
    )
    # Deliberate DR-003 participant (overlaps Bravo Bioreactor on 1.5L)
    repo.create_unit_operation(
        session,
        name="Charlie Seed 1.5L",
        type=UnitOperationType.SEED.value,
        color="#C4564E",
        status=UnitOperationStatus.DRAFT.value,
        start_date=date(2025, 10, 29),
        end_date=date(2025, 11, 4),
        batch_id=charlie.id,  # type: ignore[arg-type]
        equipment_id=equipment["1.5L"].id,  # type: ignore[arg-type]
        commit=False,
    )

    session.commit()

    batches = repo.list_batches(session)
    ops = repo.list_unit_operations(session)
    deps = repo.list_dependencies(session)
    return {
        "created": True,
        "batches": len(batches),
        "unit_operations": len(ops),
        "dependencies": len(deps),
        "deliberate_violations": list(DELIBERATE_VIOLATIONS),
    }


def describe_seed_schedule() -> str:
    lines = [
        "Demo schedule batches: Batch Alpha (valid), Batch Bravo, Batch Charlie.",
        "Deliberate violations:",
    ]
    for item in DELIBERATE_VIOLATIONS:
        lines.append(f"  - {item['rule_id']}: {item['ops']} - {item['detail']}")
    return "\n".join(lines)
