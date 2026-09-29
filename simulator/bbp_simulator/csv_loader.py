"""Load fermentation run CSVs (time_h,signal_name,value,unit)."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


SIGNAL_UNITS = {
    "DO": "%",
    "pH": "-",
    "temp": "degC",
    "feed_rate": "mL/h",
}


@dataclass(frozen=True)
class MinuteSample:
    time_h: float
    DO: float
    pH: float
    temp: float
    feed_rate: float


def load_run_csv(path: Path | str) -> list[MinuteSample]:
    """Parse a long-format run CSV into one sample per process-minute."""
    path = Path(path)
    by_time: dict[float, dict[str, float]] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            t = float(row["time_h"])
            name = row["signal_name"]
            value = float(row["value"])
            by_time.setdefault(t, {})[name] = value

    samples: list[MinuteSample] = []
    for t in sorted(by_time):
        vals = by_time[t]
        missing = [s for s in SIGNAL_UNITS if s not in vals]
        if missing:
            raise ValueError(f"Incomplete sample at time_h={t}: missing {missing}")
        samples.append(
            MinuteSample(
                time_h=t,
                DO=vals["DO"],
                pH=vals["pH"],
                temp=vals["temp"],
                feed_rate=vals["feed_rate"],
            )
        )
    if not samples:
        raise ValueError(f"No samples in {path}")
    return samples
