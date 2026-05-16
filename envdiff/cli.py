"""CLI entry point for envdiff."""

import argparse
import json
import sys
from pathlib import Path

from envdiff.core import diff_envs
from envdiff.formatter import format_diff_text, format_diff_json
from envdiff.syncer import apply_sync
from envdiff.validator import validate_env
from envdiff.linter import lint_env_string


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff",
        description="Diff and sync .env files across environments safely.",
    )
    sub = parser.add_subparsers(dest="command")

    # diff
    diff_p = sub.add_parser("diff", help="Compare two .env files")
    diff_p.add_argument("base", help="Base .env file")
    diff_p.add_argument("target", help="Target .env file")
    diff_p.add_argument("--format", choices=["text", "json"], default="text")

    # sync
    sync_p = sub.add_parser("sync", help="Sync keys from base into target")
    sync_p.add_argument("base", help="Base .env file")
    sync_p.add_argument("target", help="Target .env file to update")
    sync_p.add_argument("--overwrite", action="store_true", default=False)

    # validate
    val_p = sub.add_parser("validate", help="Validate a .env file")
    val_p.add_argument("file", help=".env file to validate")
    val_p.add_argument("--required", nargs="*", default=[])

    # lint
    lint_p = sub.add_parser("lint", help="Lint a .env file for style issues")
    lint_p.add_argument("file", help=".env file to lint")
    lint_p.add_argument("--strict", action="store_true", default=False,
                        help="Exit non-zero on warnings too")

    return parser


def _check_paths_exist(*paths: str) -> None:
    for p in paths:
        if not Path(p).exists():
            print(f"Error: file not found: {p}", file=sys.stderr)
            sys.exit(2)


def cmd_diff(args: argparse.Namespace) -> int:
    _check_paths_exist(args.base, args.target)
    result = diff_envs(Path(args.base), Path(args.target))
    if args.format == "json":
        print(format_diff_json(result))
    else:
        print(format_diff_text(result))
    return 0 if not result.has_diff() else 1


def cmd_sync(args: argparse.Namespace) -> int:
    _check_paths_exist(args.base, args.target)
    apply_sync(Path(args.base), Path(args.target), overwrite=args.overwrite)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    _check_paths_exist(args.file)
    vresult = validate_env(Path(args.file), required_keys=args.required)
    for issue in vresult.issues:
        print(issue)
    return 0 if vresult.valid else 1


def cmd_lint(args: argparse.Namespace) -> int:
    _check_paths_exist(args.file)
    content = Path(args.file).read_text(encoding="utf-8")
    lresult = lint_env_string(content)
    for issue in lresult.issues:
        print(issue)
    print(f"Lint complete: {lresult.summary()}")
    if lresult.errors:
        return 1
    if args.strict and lresult.warnings:
        return 1
    return 0


def main() -> None:
    """Parse arguments and dispatch to the appropriate subcommand handler."""
    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "diff": cmd_diff,
        "sync": cmd_sync,
        "validate": cmd_validate,
        "lint": cmd_lint,
    }

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    handler = commands.get(args.command)
    if handler is None:
        print(f"Error: unknown command '{args.command}'", file=sys.stderr)
        sys.exit(2)

    sys.exit(handler(args))
