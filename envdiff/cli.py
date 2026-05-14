"""CLI entry point for envdiff."""

import argparse
import json
import sys
from pathlib import Path

from envdiff.core import diff_envs
from envdiff.formatter import format_diff_json, format_diff_text
from envdiff.parser import parse_env_file
from envdiff.syncer import apply_sync
from envdiff.validator import validate_env_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Diff and sync .env files across environments safely.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # diff
    diff_p = sub.add_parser("diff", help="Show differences between two .env files")
    diff_p.add_argument("base", help="Base .env file")
    diff_p.add_argument("target", help="Target .env file")
    diff_p.add_argument("--format", choices=["text", "json"], default="text")

    # sync
    sync_p = sub.add_parser("sync", help="Sync keys from base into target")
    sync_p.add_argument("base", help="Base .env file (source of truth)")
    sync_p.add_argument("target", help="Target .env file to update")
    sync_p.add_argument("--overwrite", action="store_true", default=False)
    sync_p.add_argument("--dry-run", action="store_true", default=False)

    # validate
    val_p = sub.add_parser("validate", help="Validate a .env file")
    val_p.add_argument("file", help=".env file to validate")
    val_p.add_argument("--require", nargs="*", metavar="KEY", default=[])
    val_p.add_argument("--forbid", nargs="*", metavar="KEY", default=[])

    return parser


def _check_paths_exist(*paths: str) -> None:
    for p in paths:
        if not Path(p).exists():
            print(f"Error: file not found: {p}", file=sys.stderr)
            sys.exit(1)


def cmd_diff(args: argparse.Namespace) -> int:
    _check_paths_exist(args.base, args.target)
    base_env = parse_env_file(args.base)
    target_env = parse_env_file(args.target)
    result = diff_envs(base_env, target_env)
    if args.format == "json":
        print(format_diff_json(result))
    else:
        print(format_diff_text(result))
    return 0 if not result.has_diff() else 1


def cmd_sync(args: argparse.Namespace) -> int:
    _check_paths_exist(args.base, args.target)
    base_env = parse_env_file(args.base)
    target_env = parse_env_file(args.target)
    result = diff_envs(base_env, target_env)
    if args.dry_run:
        print(format_diff_text(result))
        return 0
    apply_sync(result, args.target, overwrite=args.overwrite)
    print(f"Sync complete: {args.target}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    _check_paths_exist(args.file)
    result = validate_env_file(
        args.file,
        required_keys=args.require or None,
        forbidden_keys=args.forbid or None,
    )
    print(str(result))
    return 0 if result.valid else 1


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {"diff": cmd_diff, "sync": cmd_sync, "validate": cmd_validate}
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
