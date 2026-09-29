"""HTTP client for ingest and command polling."""

from __future__ import annotations

from typing import Any

import httpx

from bbp_simulator.csv_loader import SIGNAL_UNITS


class IngestClient:
    def __init__(self, api_base: str, timeout_s: float = 5.0):
        self.api_base = api_base.rstrip("/")
        self.timeout_s = timeout_s

    def post_readings(self, readings: list[dict[str, Any]]) -> dict[str, Any]:
        url = f"{self.api_base}/ingest"
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(url, json={"readings": readings})
            response.raise_for_status()
            return response.json()

    def fetch_pending_commands(self) -> list[dict[str, Any]]:
        url = f"{self.api_base}/api/control/commands/pending"
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return data
            return []

    def ack_command(self, command_id: int) -> dict[str, Any]:
        url = f"{self.api_base}/api/control/commands/{command_id}/ack"
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(url)
            response.raise_for_status()
            return response.json()


def reading_dicts(
    *,
    time_h: float,
    DO: float,
    pH: float,
    temp: float,
    feed_rate: float,
) -> list[dict[str, Any]]:
    values = {
        "DO": DO,
        "pH": pH,
        "temp": temp,
        "feed_rate": feed_rate,
    }
    return [
        {
            "time_h": time_h,
            "signal_name": name,
            "value": values[name],
            "unit": SIGNAL_UNITS[name],
        }
        for name in ("DO", "pH", "temp", "feed_rate")
    ]
