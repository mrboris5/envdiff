"""CLI commands for sorting .env files."""

import argparse
import json
import sys

from envdiff.sorter import sort_env_file


def cmd_sort(args: argparse.Namespace) -> int:
    try:
        result = sort_env_file(
            args.env_file,
            custom_order=args.order.split(",") if args.order else None,
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        data = {
            "source": result.source,
            "was_changed": result.was_changed,
            "moved_keys": result.moved_keys,
            "sorted_content": result.to_env_string(),
        }
        print(json.dumps(data, indent=2))
    else:
        if result.was_changed:
            print(f"Sorted: {result.source}")
            if result.moved_keys:
                print(f"  Reordered keys: {', '.join(result.moved_keys)}")
        else:
            print(f"Already sorted: {result.source}")

    if args.write and result.was_changed:
        with open(args.env_file, "w") as fh:
            fh.write(result.to_env_string() + "\n")
        print(f"  Written to {args.env_file}")

    return 0


def register_sort_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("sort", help="Sort keys in a .env file")
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "--write", "-w",
        action="store_true",
        help="Write sorted output back to the file",
    )
    p.add_argument(
        "--order",
        default=None,
        metavar="KEY1,KEY2,...",
        help="Comma-separated list of keys to pin to the top",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    p.set_defaults(func=cmd_sort)


def dispatch_sort(args: argparse.Namespace) -> int:
    return cmd_sort(args)
