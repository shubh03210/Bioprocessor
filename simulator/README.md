# BBP Device Simulator

Replays `data_kit/run_*.csv` at a configurable process speed, applies the assignment
feed/DO response model, and emits DO, pH, temp, feed_rate once per wall-clock second.

## Run (dry-run, default)

```powershell
cd simulator
$env:PYTHONPATH = "."
python -m bbp_simulator --run-file ..\data_kit\run_A.csv --max-ticks 5 --no-sleep
```

With a feed step at t=0:

```powershell
python -m bbp_simulator --run-file ..\data_kit\run_A.csv --command-at 0 --command-value 10 --max-ticks 10 --no-sleep
```

## Options

| Flag | Meaning |
|------|---------|
| `--speed` | Process-minutes per wall-clock second (default 1.0) |
| `--start-time-h` | Start offset into the run |
| `--post-ingest` | POST to backend `/ingest` (Phase 7+) |
| `--dry-run` | Default: print only, no HTTP |

## Response model

- `feed_rate = setpoint` after command apply time
- `DO = clamp(DO_run + dDO, 0, 100)`
- `dDO` FO lag, τ=5 process-minutes, g=2.0 %DO/(mL/h)
