"""CLI commands for the summarizer feature."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace

from envdiff.parser import parse_env_file
from envdiff.summarizer import summarize_env


def cmd_summarize(args: Namespace) -> int:
    path = args.env_file
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw_lines = fh.readlines()
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    env_dict = parse_env_file(path)
    report = summarize_env(source=path, env_dict=env_dict, raw_lines=raw_lines)

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(str(report))

    return 0


def register_summarize_commands(sub) -> None:
    p: ArgumentParser = sub.add_parser(
        "summarize", help="Print a summary report for a .env file"
    )
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )


def dispatch_summarize(args: Namespace) -> int:
    return cmd_summarize(args)
