"""CLI commands for the normalizer feature."""

import argparse
import json
import sys
from pathlib import Path

from .normalizer import normalize_env_lines


def cmd_normalize(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 2

    lines = path.read_text().splitlines()
    result = normalize_env_lines(
        lines,
        uppercase_keys=not args.no_uppercase,
        quote_values=not args.no_quote,
    )

    if args.format == "json":
        payload = {
            "source": str(path),
            "has_changes": result.has_changes,
            "changes": [
                {"key": e.key, "original": e.original_line, "normalized": e.normalized_line}
                for e in result.changed_entries
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        if result.has_changes:
            print(f"Normalization changes for {path}:")
            for entry in result.changed_entries:
                print(f"  {entry}")
        else:
            print(f"No changes needed for {path}.")

    if args.write and result.has_changes:
        path.write_text(result.to_env_string() + "\n")
        print(f"Written: {path}")

    return 0 if not result.has_changes else 1


def register_normalize_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("normalize", help="Normalize a .env file")
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--write", action="store_true", help="Write normalized output back to file")
    p.add_argument("--no-uppercase", action="store_true", help="Do not uppercase keys")
    p.add_argument("--no-quote", action="store_true", help="Do not add quotes around values")
    p.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p.set_defaults(func=cmd_normalize)


def dispatch_normalize(args: argparse.Namespace) -> int:
    return cmd_normalize(args)
