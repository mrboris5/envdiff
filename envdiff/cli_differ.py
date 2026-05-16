"""CLI commands for multi-file diffing."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from typing import List

from envdiff.differ import multi_diff


def cmd_multi_diff(args: Namespace) -> int:
    base: str = args.base
    targets: List[str] = args.targets
    fmt: str = getattr(args, "format", "text")

    try:
        report = multi_diff(base, targets)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    if fmt == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"Base: {report.base}")
        print(f"Targets: {len(report.pairs)}")
        print()
        for pair in report.pairs:
            marker = "=" if not pair.result.has_diff else "!"
            print(f"  [{marker}] {pair.summary()}")
        always = report.keys_always_differing()
        if always:
            print()
            print(f"Keys differing in ALL targets ({len(always)}):")
            for k in always:
                print(f"  - {k}")

    return 1 if report.has_any_diff else 0


def register_differ_commands(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "multi-diff",
        help="Diff multiple env files against a single base",
    )
    p.add_argument("base", help="Base .env file")
    p.add_argument("targets", nargs="+", help="One or more target .env files")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_multi_diff)


def dispatch_differ(args: Namespace) -> int:
    if hasattr(args, "func"):
        return args.func(args)
    return 0
