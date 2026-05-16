"""CLI commands for the duplicate-key detector."""

import argparse
import json
import sys

from envdiff.duplicator import find_duplicates_in_file


def cmd_duplicates(args: argparse.Namespace) -> int:
    result = find_duplicates_in_file(args.file)

    if args.format == "json":
        data = {
            "source": result.source,
            "has_duplicates": result.has_duplicates,
            "duplicates": [
                {
                    "key": d.key,
                    "values": d.values,
                    "lines": d.lines,
                }
                for d in result.duplicates
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(str(result))

    return 1 if result.has_duplicates else 0


def register_duplicator_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "duplicates",
        help="Detect duplicate keys in a .env file",
    )
    p.add_argument("file", help="Path to the .env file to inspect")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def dispatch_duplicator(args: argparse.Namespace) -> int:
    return cmd_duplicates(args)
