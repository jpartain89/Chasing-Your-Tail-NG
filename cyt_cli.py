"""Unified CLI entry point for CYT workflows."""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List

from probe_analyzer import run_probe_analysis
from surveillance_analyzer import run_surveillance_analysis


def _run_legacy(command: List[str]) -> int:
    result = subprocess.run([sys.executable] + command)
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cyt", description="Chasing Your Tail CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    monitor = subparsers.add_parser("monitor", help="Run secure real-time monitoring")
    monitor.add_argument("--config", default="config.json")
    monitor.add_argument("--once", action="store_true")

    analyze = subparsers.add_parser("analyze", help="Run probe analysis")
    analyze.add_argument(
        "--wigle",
        action="store_true",
        help="Enable WiGLE API queries (disabled by default)",
    )
    analyze.add_argument("--days", type=int)
    analyze.add_argument("--all-logs", action="store_true")
    analyze.add_argument(
        "--local",
        action="store_true",
        help="[DEPRECATED] Ignored. Omitting --wigle already runs local-only analysis.",
    )

    survey = subparsers.add_parser("survey", help="Run surveillance analysis")
    survey.add_argument("--demo", action="store_true")
    survey.add_argument("--kismet-db")
    survey.add_argument("--gps-file")
    survey.add_argument("--stalking-only", action="store_true")
    survey.add_argument("--output-json")
    survey.add_argument("--min-threat", type=float)

    setup = subparsers.add_parser("setup", help="Run setup wizard")
    setup.add_argument("--cli", action="store_true")
    setup.add_argument("--gui", action="store_true")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "monitor":
        cmd = ["chasing_your_tail.py", "--config", args.config]
        if args.once:
            cmd.append("--once")
        return _run_legacy(cmd)

    if args.command == "analyze":
        if args.local and not args.wigle:
            print(
                "Note: --local is deprecated and has no effect. Omitting --wigle already runs local-only analysis."
            )
        use_wigle = args.wigle  # Only --wigle enables API queries; --local is a no-op.
        days = args.days if args.days is not None else 14
        return_code, output = run_probe_analysis(
            use_wigle=use_wigle,
            days_back=days,
            all_logs=args.all_logs,
        )
        print(output, end="")
        return return_code

    if args.command == "survey":
        return_code, output = run_surveillance_analysis(
            demo=args.demo,
            kismet_db=args.kismet_db,
            gps_file=args.gps_file,
            stalking_only=args.stalking_only,
            output_json=args.output_json,
            min_threat=args.min_threat if args.min_threat is not None else 0.5,
        )
        print(output, end="")
        return return_code

    if args.command == "setup":
        cmd = ["setup_wizard.py"]
        if args.cli and not args.gui:
            cmd.append("--cli")
        if args.gui and not args.cli:
            cmd.append("--gui")
        return _run_legacy(cmd)

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
