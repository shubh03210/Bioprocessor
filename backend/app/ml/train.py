"""Offline train/eval for DO forecaster vs persistence baseline."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.ml.baseline import PersistenceBaselineForecaster
from app.ml.data import build_windows, load_run_series
from app.ml.interface import HISTORY_MINUTES, HORIZON_MINUTES
from app.ml.linear import MODEL_VERSION, train_linear_forecaster

ROOT = Path(__file__).resolve().parents[3]
DATA_KIT = ROOT / "data_kit"
ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
ARTIFACT_PATH = ARTIFACT_DIR / f"{MODEL_VERSION}.joblib"
METRICS_PATH = ARTIFACT_DIR / f"{MODEL_VERSION}_metrics.json"


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def evaluate_model(forecaster, x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    preds = np.vstack(
        [
            forecaster.predict(row[:HISTORY_MINUTES], row[HISTORY_MINUTES:])
            for row in x
        ]
    )
    return {"mae": mae(y, preds), "rmse": rmse(y, preds)}


def evaluate_baseline(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    baseline = PersistenceBaselineForecaster()
    preds = np.vstack(
        [
            baseline.predict(row[:HISTORY_MINUTES], row[HISTORY_MINUTES:])
            for row in x
        ]
    )
    return {"mae": mae(y, preds), "rmse": rmse(y, preds)}


def main() -> None:
    train_runs = [DATA_KIT / "run_A.csv", DATA_KIT / "run_B.csv"]
    test_run = DATA_KIT / "run_C.csv"

    x_parts = []
    y_parts = []
    for path in train_runs:
        series = load_run_series(path)
        x, y = build_windows(series["DO"], series["feed_rate"])
        x_parts.append(x)
        y_parts.append(y)
    x_train = np.vstack(x_parts)
    y_train = np.vstack(y_parts)

    test_series = load_run_series(test_run)
    x_test, y_test = build_windows(test_series["DO"], test_series["feed_rate"])

    model = train_linear_forecaster(x_train, y_train)
    model.save(ARTIFACT_PATH)

    model_metrics = evaluate_model(model, x_test, y_test)
    baseline_metrics = evaluate_baseline(x_test, y_test)

    report = {
        "model_version": MODEL_VERSION,
        "train_runs": [p.name for p in train_runs],
        "holdout_run": test_run.name,
        "history_minutes": HISTORY_MINUTES,
        "horizon_minutes": HORIZON_MINUTES,
        "train_windows": int(x_train.shape[0]),
        "test_windows": int(x_test.shape[0]),
        "model": model_metrics,
        "persistence_baseline": baseline_metrics,
        "artifact": str(ARTIFACT_PATH.relative_to(ROOT)) if ARTIFACT_PATH.is_relative_to(ROOT) else str(ARTIFACT_PATH),
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
