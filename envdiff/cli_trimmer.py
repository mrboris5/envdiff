"""CLI commands for the trimmer feature."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Set

from envdiff.parser import parse_env_file
from envdiff.trimmer import trim_env


def cmd_trim(args: argparse.Namespace) -> int:
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"error: source file not found: {source_path}", file=sys.stderr)
        return 2

    reference_keys: Set[str] = set()
    for ref in args.reference:
        ref_path = Path(ref)
        if not ref_path.exists():
            print(f"error: reference file not found: {ref_path}", file=sys.stderr)
            return 2
        reference_keys.update(parse_env_file(ref_path).keys())

    source_content = source_path.read_text()
    result = trim_env(source_content, reference_keys, dry_run=args.dry_run)

    if args.format == "json":
        data = {
            "source": str(source_path),
            "removed": [
                {"key": e.key, "value": e.value, "line": e.line_number}
                for e in result.removed
            ],
            "has_removals": result.has_removals,
            "dry_run": args.dry_run,
        }
        print(json.dumps(data, indent=2))
    else:
        if result.has_removals:
            print(f"Keys to remove from {source_path} ({len(result.removed)} total):")
            for entry in result.removed:
                print(f"  - {entry}")
        else:
            print(f"No unused keys found in {source_path}.")

    if result.has_removals and not args.dry_run:
        if args.output:
            Path(args.output).write_text(result.to_env_string())
            print(f"Written trimmed file to {args.output}")
        else:
            source_path.write_text(result.to_env_string())
            print(f"Updated {source_path} in place.")

    return 1 if result.has_removals else 0


def register_trim_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("trim", help="Remove unused keys from a .env file")
    p.add_argument("source", help=".env file to trim")
    p.add_argument(
        "reference",
        nargs="+",
        help="One or more reference .env files whose keys are considered in-use",
    )
    p.add_argument("--dry-run", action="store_true", help="Report removals without writing")
    p.add_argument("--output", "-o", default="", help="Write result to this path instead of in-place")
    p.add_argument("--format", choices=["text", "json"], default="text")


def dispatch_trim(args: argparse.Namespace) -> int:
    return cmd_trim(args)
