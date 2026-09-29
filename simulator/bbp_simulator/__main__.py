"""BBP device simulator CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bbp_simulator import __version__
from bbp_simulator.csv_loader import load_run_csv
from bbp_simulator.device import DeviceSimulator, FeedCommand


def _default_data_kit() -> Path:
    return Path(__file__).resolve().parents[2] / "data_kit"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BBP device simulator — replay fermentation run with feed/DO response"
    )
    parser.add_argument("--hello", action="store_true", help="Print version and exit")
    parser.add_argument(
        "--run-file",
        type=Path,
        default=None,
        help="Path to run_A/B/C.csv (default: data_kit/run_A.csv)",
    )
    parser.add_argument(
        "--api-base",
        default="http://127.0.0.1:8000",
        help="Backend base URL for POST /ingest",
    )
    parser.add_argument(
        "--post-ingest",
        action="store_true",
        help="POST readings to /ingest (requires backend)",
    )
    parser.add_argument(
        "--poll-commands",
        action="store_true",
        help="Poll GET /api/control/commands/pending and ack applied (implies live loop)",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Process-minutes advanced per wall-clock second (default 1.0)",
    )
    parser.add_argument(
        "--start-time-h",
        type=float,
        default=0.0,
        help="Start offset into the run (process hours)",
    )
    parser.add_argument(
        "--max-ticks",
        type=int,
        default=5,
        help="Stop after N emits (default 5 for smoke; 0 = until end of run)",
    )
    parser.add_argument(
        "--no-sleep",
        action="store_true",
        help="Do not sleep between ticks (fast replay)",
    )
    parser.add_argument(
        "--command-at",
        type=float,
        default=None,
        help="Optional feed command apply_at_time_h",
    )
    parser.add_argument(
        "--command-value",
        type=float,
        default=None,
        help="Optional feed setpoint mL/h (requires --command-at)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.hello:
        print(f"bbp-simulator {__version__}")
        return 0

    run_file = args.run_file or (_default_data_kit() / "run_A.csv")
    if not run_file.exists():
        print(f"Run file not found: {run_file}", file=sys.stderr)
        return 1

    samples = load_run_csv(run_file)
    commands: list[FeedCommand] = []
    if args.command_at is not None:
        if args.command_value is None:
            print("--command-value required with --command-at", file=sys.stderr)
            return 1
        commands.append(
            FeedCommand(value=args.command_value, apply_at_time_h=args.command_at)
        )

    dry_run = not args.post_ingest
    poll_commands = bool(args.poll_commands and not dry_run)

    def _print(payload: dict) -> None:
        if "_warn" in payload:
            print(f"WARN {payload['_warn']}", file=sys.stderr)
            return
        print(
            f"t={payload['time_h']:.4f}h "
            f"DO={payload['DO']:.3f} (run={payload['DO_run']:.3f}, dDO={payload['dDO']:.3f}) "
            f"feed={payload['feed_rate']:.3f} (run={payload['feed_run']:.3f}) "
            f"pH={payload['pH']:.3f} temp={payload['temp']:.3f}"
        )

    sim = DeviceSimulator(
        samples=samples,
        process_minutes_per_wall_second=args.speed,
        start_time_h=args.start_time_h,
        dry_run=dry_run,
        api_base=args.api_base,
        commands=commands,
        poll_commands=poll_commands,
        on_emit=_print,
    )

    max_ticks = None if args.max_ticks == 0 else args.max_ticks
    print(
        f"bbp-simulator {__version__} run={run_file.name} "
        f"speed={args.speed} min/s dry_run={dry_run} poll_commands={poll_commands} "
        f"samples={len(samples)}"
    )
    ticks = sim.run(max_ticks=max_ticks, realtime=not args.no_sleep)
    print(f"Done. ticks={ticks} final_process_time_h={sim.state.process_time_h:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
