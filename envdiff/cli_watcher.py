"""CLI commands for the env file watcher."""

from __future__ import annotations

import argparse
import json
import sys

from envdiff.watcher import EnvWatcher, WatchEvent
from envdiff.formatter import format_diff_text, format_diff_json


def _on_change_text(event: WatchEvent) -> None:
    print(f"\n[envdiff] Change detected: {event.path}")
    print(format_diff_text(event.diff, source=event.path, target="(updated)"))


def _on_change_json(event: WatchEvent) -> None:
    payload = {
        "path": event.path,
        "previous_hash": event.previous_hash,
        "current_hash": event.current_hash,
        "diff": json.loads(format_diff_json(event.diff)),
    }
    print(json.dumps(payload))


def cmd_watch(args: argparse.Namespace) -> int:
    """Watch one or more .env files and print diffs on change."""
    fmt = getattr(args, "format", "text")
    interval = getattr(args, "interval", 1.0)
    callback = _on_change_json if fmt == "json" else _on_change_text

    watcher = EnvWatcher(paths=args.paths, interval=interval)
    if fmt == "text":
        print(f"[envdiff] Watching {len(args.paths)} file(s). Press Ctrl+C to stop.")
    try:
        watcher.start(callback)
    except KeyboardInterrupt:
        if fmt == "text":
            print("\n[envdiff] Stopped.")
    return 0


def register_watch_commands(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("watch", help="Watch .env files for changes")
    p.add_argument("paths", nargs="+", metavar="FILE", help=".env files to watch")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 1.0)",
    )
    p.set_defaults(func=cmd_watch)


def dispatch_watch(args: argparse.Namespace) -> int:
    return cmd_watch(args)
