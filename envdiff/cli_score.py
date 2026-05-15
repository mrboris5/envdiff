"""CLI commands for env health scoring."""

import argparse
import json
import sys

from envdiff.scorer import score_env


def cmd_score(args: argparse.Namespace) -> int:
    try:
        with open(args.env_file, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.env_file}", file=sys.stderr)
        return 1

    required = args.require.split(",") if args.require else []
    result = score_env(content, required_keys=required)

    if args.format == "json":
        data = {
            "score": result.total,
            "max": result.max_score,
            "grade": result.grade,
            "deductions": [
                {"category": d.category, "deduction": d.deduction, "reason": d.reason}
                for d in result.details
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(str(result))

    if args.min_score and result.total < args.min_score:
        print(f"\nFailed: score {result.total} is below minimum {args.min_score}", file=sys.stderr)
        return 1

    return 0


def register_score_commands(subparsers) -> None:
    p = subparsers.add_parser("score", help="Score a .env file for quality and safety")
    p.add_argument("env_file", help="Path to .env file")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--require", default="", help="Comma-separated list of required keys")
    p.add_argument("--min-score", type=int, default=0, help="Exit non-zero if score is below this value")
    p.set_defaults(func=cmd_score)


def dispatch_score(args: argparse.Namespace) -> int:
    return cmd_score(args)
