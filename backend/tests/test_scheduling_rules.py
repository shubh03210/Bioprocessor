"""Unit tests for DR-001–DR-005 (exclusive end dates)."""

from __future__ import annotations

from datetime import date

import pytest

from app.domain.scheduling_rules import (
    RULE_DR001,
    RULE_DR002,
    RULE_DR003,
    RULE_DR004,
    RULE_DR005,
    BatchView,
    DepView,
    OpView,
    check_batch_containment,
    check_completed_immutability,
    check_equipment_double_booking,
    check_explicit_dependencies,
    check_process_ordering,
    evaluate_schedule,
    intervals_overlap,
)


def _op(
    op_id: int,
    name: str,
    *,
    type: str = "Seed",
    status: str = "draft",
    start: date,
    end: date,
    batch_id: int = 1,
    equipment_id: int = 1,
) -> OpView:
    return OpView(
        id=op_id,
        name=name,
        type=type,
        status=status,
        start_date=start,
        end_date=end,
        batch_id=batch_id,
        equipment_id=equipment_id,
    )


# ----- interval helpers -----


def test_exclusive_ends_do_not_overlap():
    # Oct 1 → Oct 4 and Oct 4 → Oct 6 must NOT overlap
    assert not intervals_overlap(
        date(2025, 10, 1),
        date(2025, 10, 4),
        date(2025, 10, 4),
        date(2025, 10, 6),
    )


def test_overlapping_intervals():
    assert intervals_overlap(
        date(2025, 10, 24),
        date(2025, 10, 31),
        date(2025, 10, 29),
        date(2025, 11, 4),
    )


# ----- DR-001 -----


def test_dr001_valid_containment():
    batch = BatchView(1, "B", date(2025, 10, 1), date(2025, 11, 1))
    op = _op(10, "Seed", start=date(2025, 10, 5), end=date(2025, 10, 10))
    assert check_batch_containment([op], {1: batch}) == []


def test_dr001_invalid_past_batch_end():
    batch = BatchView(1, "B", date(2025, 10, 1), date(2025, 10, 20))
    op = _op(
        10,
        "Bioreactor X",
        type="Bioreactor",
        start=date(2025, 10, 15),
        end=date(2025, 10, 25),
    )
    violations = check_batch_containment([op], {1: batch})
    assert len(violations) == 1
    assert violations[0].rule_id == RULE_DR001
    assert "Bioreactor X" in violations[0].message
    assert "B" in violations[0].message
    assert violations[0].operation_ids == (10,)


def test_dr001_op_may_end_exactly_on_batch_end():
    batch = BatchView(1, "B", date(2025, 10, 1), date(2025, 10, 20))
    op = _op(10, "Seed", start=date(2025, 10, 1), end=date(2025, 10, 20))
    assert check_batch_containment([op], {1: batch}) == []


# ----- DR-002 -----


def test_dr002_valid_bioreactor_starts_when_seed_ends():
    batch = BatchView(1, "Alpha", date(2025, 10, 1), date(2025, 11, 1))
    seed = _op(1, "Seed A", type="Seed", start=date(2025, 10, 21), end=date(2025, 10, 24))
    br = _op(
        2,
        "BR A",
        type="Bioreactor",
        start=date(2025, 10, 24),
        end=date(2025, 10, 31),
        equipment_id=2,
    )
    assert check_process_ordering([seed, br], {1: batch}) == []


def test_dr002_invalid_bioreactor_starts_before_seed_ends():
    batch = BatchView(1, "Alpha", date(2025, 10, 1), date(2025, 11, 1))
    seed = _op(1, "Seed A", type="Seed", start=date(2025, 10, 21), end=date(2025, 10, 24))
    br = _op(
        2,
        "BR A",
        type="Bioreactor",
        start=date(2025, 10, 23),
        end=date(2025, 10, 31),
        equipment_id=2,
    )
    violations = check_process_ordering([seed, br], {1: batch})
    assert len(violations) == 1
    assert violations[0].rule_id == RULE_DR002
    assert violations[0].operation_ids == (1, 2)
    assert "BR A" in violations[0].message
    assert "Seed A" in violations[0].message


def test_dr002_pair_reported_once():
    batch = BatchView(1, "Alpha", date(2025, 10, 1), date(2025, 11, 1))
    seed = _op(1, "Seed A", type="Seed", start=date(2025, 10, 21), end=date(2025, 10, 24))
    br = _op(
        2,
        "BR A",
        type="Bioreactor",
        start=date(2025, 10, 23),
        end=date(2025, 10, 31),
        equipment_id=2,
    )
    v1 = check_process_ordering([seed, br], {1: batch})
    v2 = check_process_ordering([br, seed], {1: batch})
    assert len(v1) == 1 and len(v2) == 1
    assert v1[0].operation_ids == v2[0].operation_ids == (1, 2)


# ----- DR-003 -----


def test_dr003_adjacent_exclusive_ends_ok():
    a = _op(1, "A", start=date(2025, 10, 1), end=date(2025, 10, 4), equipment_id=1)
    b = _op(2, "B", start=date(2025, 10, 4), end=date(2025, 10, 6), equipment_id=1)
    assert check_equipment_double_booking([a, b], {1: "1.5L"}) == []


def test_dr003_double_booking_detected():
    a = _op(
        1,
        "Bioreactor",
        type="Bioreactor",
        start=date(2025, 10, 24),
        end=date(2025, 10, 31),
        equipment_id=1,
    )
    b = _op(
        2,
        "Seed",
        type="Seed",
        start=date(2025, 10, 29),
        end=date(2025, 11, 4),
        equipment_id=1,
        batch_id=2,
    )
    violations = check_equipment_double_booking([a, b], {1: "1.5L"})
    assert len(violations) == 1
    assert violations[0].rule_id == RULE_DR003
    assert set(violations[0].operation_ids) == {1, 2}
    assert "1.5L" in violations[0].message


def test_dr003_pair_once_regardless_of_order():
    a = _op(1, "A", start=date(2025, 10, 24), end=date(2025, 10, 31))
    b = _op(2, "B", start=date(2025, 10, 29), end=date(2025, 11, 4), batch_id=2)
    v1 = check_equipment_double_booking([a, b], {1: "1.5L"})
    v2 = check_equipment_double_booking([b, a], {1: "1.5L"})
    assert len(v1) == 1 and len(v2) == 1
    assert v1[0].operation_ids == v2[0].operation_ids


# ----- DR-004 -----


def test_dr004_valid_target_starts_when_source_ends():
    source = _op(1, "Source", start=date(2025, 10, 1), end=date(2025, 10, 10))
    target = _op(
        2,
        "Target",
        type="Bioreactor",
        start=date(2025, 10, 10),
        end=date(2025, 10, 15),
        equipment_id=2,
    )
    dep = DepView(1, from_unitop_id=1, to_unitop_id=2)
    assert check_explicit_dependencies([source, target], [dep]) == []


def test_dr004_invalid_target_starts_early():
    source = _op(1, "Source", start=date(2025, 10, 1), end=date(2025, 10, 10))
    target = _op(
        2,
        "Target",
        type="Bioreactor",
        start=date(2025, 10, 9),
        end=date(2025, 10, 15),
        equipment_id=2,
    )
    dep = DepView(1, from_unitop_id=1, to_unitop_id=2)
    violations = check_explicit_dependencies([source, target], [dep])
    assert len(violations) == 1
    assert violations[0].rule_id == RULE_DR004
    assert violations[0].operation_ids == (1, 2)


# ----- DR-005 -----


def test_dr005_blocks_delete_of_completed():
    op = _op(
        1,
        "Done",
        status="completed",
        start=date(2025, 10, 1),
        end=date(2025, 10, 5),
    )
    v = check_completed_immutability(existing=op, is_delete=True)
    assert v is not None
    assert v.rule_id == RULE_DR005


def test_dr005_blocks_move_of_completed():
    op = _op(
        1,
        "Done",
        status="completed",
        start=date(2025, 10, 1),
        end=date(2025, 10, 5),
    )
    proposed = _op(
        1,
        "Done",
        status="completed",
        start=date(2025, 10, 2),
        end=date(2025, 10, 5),
    )
    v = check_completed_immutability(existing=op, proposed=proposed)
    assert v is not None


def test_dr005_blocks_status_change_away_from_completed():
    op = _op(
        1,
        "Done",
        status="completed",
        start=date(2025, 10, 1),
        end=date(2025, 10, 5),
    )
    proposed = _op(
        1,
        "Done",
        status="draft",
        start=date(2025, 10, 1),
        end=date(2025, 10, 5),
    )
    v = check_completed_immutability(existing=op, proposed=proposed)
    assert v is not None


def test_dr005_allows_noop_update_on_completed():
    op = _op(
        1,
        "Done",
        status="completed",
        start=date(2025, 10, 1),
        end=date(2025, 10, 5),
    )
    assert check_completed_immutability(existing=op, proposed=op) is None


def test_dr005_allows_delete_of_draft():
    op = _op(1, "Draft", status="draft", start=date(2025, 10, 1), end=date(2025, 10, 5))
    assert check_completed_immutability(existing=op, is_delete=True) is None


# ----- evaluate_schedule collect-all + dedupe -----


def test_evaluate_schedule_collects_multiple_rules():
    batch = BatchView(1, "Charlie", date(2025, 10, 15), date(2025, 11, 15))
    seed = _op(
        5,
        "Charlie Seed 75L",
        type="Seed",
        start=date(2025, 10, 21),
        end=date(2025, 10, 24),
        equipment_id=4,
    )
    br = _op(
        6,
        "Charlie Bioreactor 1500L",
        type="Bioreactor",
        start=date(2025, 10, 23),
        end=date(2025, 10, 30),
        equipment_id=5,
    )
    bravo_br = _op(
        4,
        "Bravo Bioreactor 1.5L",
        type="Bioreactor",
        start=date(2025, 10, 24),
        end=date(2025, 10, 31),
        batch_id=2,
        equipment_id=1,
    )
    charlie_seed_15 = _op(
        7,
        "Charlie Seed 1.5L",
        type="Seed",
        start=date(2025, 10, 29),
        end=date(2025, 11, 4),
        equipment_id=1,
    )
    batch2 = BatchView(2, "Bravo", date(2025, 10, 15), date(2025, 11, 10))
    violations = evaluate_schedule(
        batches=[batch, batch2],
        ops=[seed, br, bravo_br, charlie_seed_15],
        deps=[],
        equipment_names={1: "1.5L", 4: "75L", 5: "1500L"},
    )
    rule_ids = {v.rule_id for v in violations}
    assert RULE_DR002 in rule_ids
    assert RULE_DR003 in rule_ids


def test_evaluate_schedule_dedupes_identical_pairs():
    batch = BatchView(1, "B", date(2025, 10, 1), date(2025, 11, 1))
    a = _op(1, "A", start=date(2025, 10, 1), end=date(2025, 10, 10))
    b = _op(2, "B", start=date(2025, 10, 5), end=date(2025, 10, 12), batch_id=1)
    # evaluate_schedule path already dedupes; calling equipment check twice via evaluate is enough
    v = evaluate_schedule(
        batches=[batch],
        ops=[a, b],
        deps=[],
        equipment_names={1: "1.5L"},
    )
    dr003 = [x for x in v if x.rule_id == RULE_DR003]
    assert len(dr003) == 1
