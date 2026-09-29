"""Scheduling domain rules DR-001–DR-005 (exclusive end dates).

Pure functions — no DB access. Backend is the sole authority for these rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping, Sequence

PROCESS_TYPE_ORDER: dict[str, int] = {
    "Seed": 0,
    "Bioreactor": 1,
    "TFF": 2,
    "Spray": 3,
    "Sum": 4,
}

RULE_DR001 = "DR-001"
RULE_DR002 = "DR-002"
RULE_DR003 = "DR-003"
RULE_DR004 = "DR-004"
RULE_DR005 = "DR-005"


@dataclass(frozen=True, slots=True)
class Violation:
    rule_id: str
    message: str
    operation_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class OpView:
    id: int
    name: str
    type: str
    status: str
    start_date: date
    end_date: date
    batch_id: int
    equipment_id: int


@dataclass(frozen=True, slots=True)
class BatchView:
    id: int
    name: str
    start_date: date
    end_date: date


@dataclass(frozen=True, slots=True)
class DepView:
    id: int
    from_unitop_id: int
    to_unitop_id: int


def intervals_overlap(
    start_a: date,
    end_a: date,
    start_b: date,
    end_b: date,
) -> bool:
    """Half-open [start, end) overlap: start_a < end_b AND start_b < end_a."""
    return start_a < end_b and start_b < end_a


def op_from_model(op) -> OpView:
    return OpView(
        id=op.id,
        name=op.name,
        type=op.type,
        status=op.status,
        start_date=op.start_date,
        end_date=op.end_date,
        batch_id=op.batch_id,
        equipment_id=op.equipment_id,
    )


def batch_from_model(batch) -> BatchView:
    return BatchView(
        id=batch.id,
        name=batch.name,
        start_date=batch.start_date,
        end_date=batch.end_date,
    )


def dep_from_model(dep) -> DepView:
    return DepView(
        id=dep.id,
        from_unitop_id=dep.from_unitop_id,
        to_unitop_id=dep.to_unitop_id,
    )


def _dedupe(violations: Iterable[Violation]) -> list[Violation]:
    """One violation per (rule_id, operation_ids) — ids order preserved as given."""
    seen: set[tuple[str, tuple[int, ...]]] = set()
    result: list[Violation] = []
    for v in violations:
        key = (v.rule_id, v.operation_ids)
        if key in seen:
            continue
        seen.add(key)
        result.append(v)
    return result


def check_batch_containment(
    ops: Sequence[OpView],
    batches: Mapping[int, BatchView],
) -> list[Violation]:
    """DR-001: op fully inside batch [start, end)."""
    out: list[Violation] = []
    for op in ops:
        batch = batches.get(op.batch_id)
        if batch is None:
            continue
        contained = op.start_date >= batch.start_date and op.end_date <= batch.end_date
        if not contained:
            out.append(
                Violation(
                    rule_id=RULE_DR001,
                    message=(
                        f'Unit operation "{op.name}" is outside batch "{batch.name}" '
                        f"date range [{batch.start_date.isoformat()}, {batch.end_date.isoformat()})."
                    ),
                    operation_ids=(op.id,),
                )
            )
    return out


def check_process_ordering(
    ops: Sequence[OpView],
    batches: Mapping[int, BatchView],
) -> list[Violation]:
    """DR-002: later type may not start before every earlier type in same batch ended."""
    out: list[Violation] = []
    by_batch: dict[int, list[OpView]] = {}
    for op in ops:
        by_batch.setdefault(op.batch_id, []).append(op)

    for batch_id, batch_ops in by_batch.items():
        batch = batches.get(batch_id)
        batch_name = batch.name if batch else str(batch_id)
        for later in batch_ops:
            later_rank = PROCESS_TYPE_ORDER.get(later.type)
            if later_rank is None:
                continue
            for earlier in batch_ops:
                if earlier.id == later.id:
                    continue
                earlier_rank = PROCESS_TYPE_ORDER.get(earlier.type)
                if earlier_rank is None or earlier_rank >= later_rank:
                    continue
                # later may start only when earlier has ended
                if later.start_date < earlier.end_date:
                    out.append(
                        Violation(
                            rule_id=RULE_DR002,
                            message=(
                                f'"{later.name}" ({later.type}) starts before '
                                f'"{earlier.name}" ({earlier.type}) ends in batch "{batch_name}".'
                            ),
                            operation_ids=(earlier.id, later.id),
                        )
                    )
    return out


def check_equipment_double_booking(
    ops: Sequence[OpView],
    equipment_names: Mapping[int, str],
) -> list[Violation]:
    """DR-003: same equipment, overlapping [start, end) — unordered pair once."""
    out: list[Violation] = []
    seen_pairs: set[frozenset[int]] = set()
    for i, a in enumerate(ops):
        for b in ops[i + 1 :]:
            if a.equipment_id != b.equipment_id:
                continue
            if not intervals_overlap(a.start_date, a.end_date, b.start_date, b.end_date):
                continue
            pair = frozenset({a.id, b.id})
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            eq_name = equipment_names.get(a.equipment_id, str(a.equipment_id))
            # Stable message order by id
            first, second = sorted([a, b], key=lambda o: o.id)
            out.append(
                Violation(
                    rule_id=RULE_DR003,
                    message=(
                        f'Equipment "{eq_name}" double-booked by '
                        f'"{first.name}" and "{second.name}".'
                    ),
                    operation_ids=tuple(sorted(pair)),
                )
            )
    return out


def check_explicit_dependencies(
    ops: Sequence[OpView],
    deps: Sequence[DepView],
) -> list[Violation]:
    """DR-004: target.start >= source.end."""
    by_id = {op.id: op for op in ops}
    out: list[Violation] = []
    for dep in deps:
        source = by_id.get(dep.from_unitop_id)
        target = by_id.get(dep.to_unitop_id)
        if source is None or target is None:
            continue
        if target.start_date < source.end_date:
            out.append(
                Violation(
                    rule_id=RULE_DR004,
                    message=(
                        f'Dependency violated: "{target.name}" starts before '
                        f'"{source.name}" ends.'
                    ),
                    operation_ids=(source.id, target.id),
                )
            )
    return out


def check_completed_immutability(
    *,
    existing: OpView,
    is_delete: bool = False,
    proposed: OpView | None = None,
) -> Violation | None:
    """DR-005: completed ops cannot be moved or deleted.

    Design choice: also disallow changing status away from completed.
    No-op updates (identical start/end/equipment/status) are allowed.
    """
    if existing.status != "completed":
        return None

    message = f'Completed unit operation "{existing.name}" cannot be moved or deleted.'

    if is_delete:
        return Violation(
            rule_id=RULE_DR005,
            message=message,
            operation_ids=(existing.id,),
        )

    if proposed is None:
        return None

    moved = (
        proposed.start_date != existing.start_date
        or proposed.end_date != existing.end_date
        or proposed.equipment_id != existing.equipment_id
    )
    status_changed = proposed.status != existing.status
    if moved or status_changed:
        return Violation(
            rule_id=RULE_DR005,
            message=message,
            operation_ids=(existing.id,),
        )
    return None


def evaluate_schedule(
    *,
    batches: Sequence[BatchView],
    ops: Sequence[OpView],
    deps: Sequence[DepView],
    equipment_names: Mapping[int, str],
) -> list[Violation]:
    """Evaluate DR-001–DR-004 on a full schedule snapshot (collect-all)."""
    batch_map = {b.id: b for b in batches}
    violations: list[Violation] = []
    violations.extend(check_batch_containment(ops, batch_map))
    violations.extend(check_process_ordering(ops, batch_map))
    violations.extend(check_equipment_double_booking(ops, equipment_names))
    violations.extend(check_explicit_dependencies(ops, deps))
    return _dedupe(violations)


def filter_violations_for_window(
    violations: Sequence[Violation],
    ops_in_window_ids: set[int],
) -> list[Violation]:
    """Include a violation if any involved operation intersects the window."""
    return [v for v in violations if ops_in_window_ids.intersection(v.operation_ids)]
