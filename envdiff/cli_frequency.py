"""CLI commands for key-frequency analysis across multiple .env files."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.differ_multi import analyse_frequency


def cmd_frequency(ns: argparse.Namespace) -> int:
    paths = [Path(p) for p in ns.files]
    missing = [p for p in paths if not p.exists()]
    if missing:
        for m in missing:
            print(f"error: file not found: {m}", file=sys.stderr)
        return 2

    envs = [parse_env_file(p) for p in paths]
    names = [p.name for p in paths]
    report = analyse_frequency(envs, names)

    threshold = getattr(ns, "threshold", 0.5)
    show_sparse = getattr(ns, "sparse", False)
    entries = report.sparse_keys(threshold) if show_sparse else report.entries

    if ns.format == "json":
        data = {"entries": [e.to_dict() for e in entries]}
        print(json.dumps(data, indent=2))
        return 0

    # text output
    print(f"Key frequency across {len(paths)} file(s):\n")
    for e in entries:
        universal = " [universal]" if e.is_universal else ""
        print(f"  {e}{universal}")
    print()
    print(f"Total unique keys : {len(report.entries)}")
    print(f"Universal keys    : {len(report.universal_keys())}")
    print(f"Sparse keys (<{threshold:.0%}): {len(report.sparse_keys(threshold))}")
    return 0


def register_frequency_commands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("frequency", help="Analyse key frequency across env files")
    p.add_argument("files", nargs="+", help="Two or more .env files")
    p.add_argument(
        "--format", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--sparse", action="store_true",
        help="Show only sparse keys (below threshold)",
    )
    p.add_argument(
        "--threshold", type=float, default=0.5, metavar="FLOAT",
        help="Sparse threshold 0.0-1.0 (default: 0.5)",
    )
    p.set_defaults(func=cmd_frequency)


def dispatch_frequency(ns: argparse.Namespace) -> int:
    return cmd_frequency(ns)
