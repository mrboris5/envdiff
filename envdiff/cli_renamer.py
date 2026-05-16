"""CLI commands for renaming keys in .env files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.renamer import RenameEntry, rename_keys


def cmd_rename(args: argparse.Namespace) -> int:
    src = Path(args.env_file)
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 1

    old_key: str = args.old_key
    new_key: str = args.new_key
    note: str = getattr(args, "note", "")
    dry_run: bool = getattr(args, "dry_run", False)
    output: str = getattr(args, "output", "text")

    lines = src.read_text().splitlines(keepends=True)
    entry = RenameEntry(old_key=old_key, new_key=new_key, note=note)
    result = rename_keys(lines, [entry], dry_run=dry_run)

    if output == "json":
        data = {
            "applied": [e.to_dict() for e in result.applied],
            "skipped": result.skipped,
            "dry_run": dry_run,
        }
        print(json.dumps(data, indent=2))
    else:
        if result.applied:
            verb = "Would rename" if dry_run else "Renamed"
            for e in result.applied:
                print(f"{verb}: {e}")
        if result.skipped:
            for k in result.skipped:
                print(f"skipped (not found): {k}")
        if not result.applied and not result.skipped:
            print("No changes.")

    if not dry_run and result.has_changes:
        dest = Path(args.out_file) if getattr(args, "out_file", None) else src
        dest.write_text(result.to_env_string())

    return 0


def register_rename_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("rename", help="Rename a key in an .env file")
    p.add_argument("env_file", help="Path to .env file")
    p.add_argument("old_key", help="Key to rename")
    p.add_argument("new_key", help="New key name")
    p.add_argument("--note", default="", help="Optional note")
    p.add_argument("--dry-run", action="store_true", help="Preview without writing")
    p.add_argument("--out-file", default=None, help="Write output to this file")
    p.add_argument("--output", choices=["text", "json"], default="text")


def dispatch_rename(args: argparse.Namespace) -> int:
    return cmd_rename(args)
