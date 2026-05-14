"""Command-line interface for envdiff."""

import argparse
import sys
from pathlib import Path

from envdiff.core import diff_envs
from envdiff.formatter import format_diff_text, format_diff_json
from envdiff.syncer import apply_sync


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Diff and sync .env files across environments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # diff subcommand
    diff_cmd = subparsers.add_parser("diff", help="Show differences between two .env files")
    diff_cmd.add_argument("source", type=Path, help="Source .env file")
    diff_cmd.add_argument("target", type=Path, help="Target .env file")
    diff_cmd.add_argument("--format", choices=["text", "json"], default="text")

    # sync subcommand
    sync_cmd = subparsers.add_parser("sync", help="Sync missing keys from source to target")
    sync_cmd.add_argument("source", type=Path, help="Source .env file")
    sync_cmd.add_argument("target", type=Path, help="Target .env file")
    sync_cmd.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    sync_cmd.add_argument("--overwrite", action="store_true", help="Also update differing values")

    return parser


def cmd_diff(args) -> int:
    result = diff_envs(args.source, args.target)
    if args.format == "json":
        print(format_diff_json(result))
    else:
        print(format_diff_text(result))
    return 0 if not result.has_diff() else 1


def cmd_sync(args) -> int:
    result = diff_envs(args.source, args.target)
    summary = apply_sync(
        result,
        target_path=args.target,
        dry_run=args.dry_run,
        overwrite_existing=args.overwrite,
    )
    label = "[dry-run] " if args.dry_run else ""
    print(f"{label}Sync complete: +{len(summary['added'])} added, "
          f"~{len(summary['updated'])} updated, "
          f"{len(summary['skipped'])} skipped")
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "diff":
        return cmd_diff(args)
    elif args.command == "sync":
        return cmd_sync(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
