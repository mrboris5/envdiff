"""CLI commands for the env stripper (remove comments/blanks)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.stripper import strip_env


def cmd_strip(ns: argparse.Namespace) -> int:
    path = Path(ns.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    lines = path.read_text().splitlines(keepends=True)
    result = strip_env(
        lines,
        remove_comments=not ns.keep_comments,
        remove_blanks=not ns.keep_blanks,
        dry_run=ns.dry_run,
    )

    if ns.format == "json":
        data = {
            "file": str(path),
            "removed_count": result.removed_count,
            "was_changed": result.was_changed,
            "removed_lines": [
                {"lineno": ln, "content": content}
                for ln, content in result.removed_lines
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        if not result.was_changed:
            print(f"Nothing to strip in {path}")
        else:
            print(f"Stripped {result.removed_count} line(s) from {path}")
            for lineno, content in result.removed_lines:
                print(f"  - [{lineno:>4}] {content}")

    if result.was_changed and not ns.dry_run:
        path.write_text(result.to_env_string())
        print(f"Written: {path}")

    return 0


def register_strip_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("strip", help="Remove comments and blank lines from a .env file")
    p.add_argument("file", help="Path to .env file")
    p.add_argument("--keep-comments", action="store_true", help="Preserve comment lines")
    p.add_argument("--keep-blanks", action="store_true", help="Preserve blank lines")
    p.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_strip)


def dispatch_strip(ns: argparse.Namespace) -> int:
    return cmd_strip(ns)
