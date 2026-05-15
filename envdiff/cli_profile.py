"""CLI commands for profile management."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.parser import parse_env_file
from envdiff.profiler import EnvProfile, check_profile, load_profile, save_profile


def cmd_profile_check(args: argparse.Namespace) -> int:
    """Check an .env file against a profile."""
    try:
        profile = load_profile(args.profile)
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error loading profile: {exc}", file=sys.stderr)
        return 2

    try:
        env = parse_env_file(args.env_file)
    except FileNotFoundError as exc:
        print(f"Error reading env file: {exc}", file=sys.stderr)
        return 2

    result = check_profile(env, profile)
    print(result.summary())
    return 0 if result.passed else 1


def cmd_profile_create(args: argparse.Namespace) -> int:
    """Create a profile JSON from an existing .env file."""
    try:
        env = parse_env_file(args.env_file)
    except FileNotFoundError as exc:
        print(f"Error reading env file: {exc}", file=sys.stderr)
        return 2

    profile = EnvProfile(
        name=args.name,
        required_keys=list(env.keys()),
        optional_keys=[],
        description=args.description or "",
    )
    save_profile(profile, args.output)
    print(f"Profile '{args.name}' saved to {args.output}")
    return 0


def register_profile_commands(subparsers: argparse._SubParsersAction) -> None:
    p_check = subparsers.add_parser("profile-check", help="Check env file against a profile")
    p_check.add_argument("env_file", help="Path to .env file")
    p_check.add_argument("profile", help="Path to profile JSON")
    p_check.set_defaults(func=cmd_profile_check)

    p_create = subparsers.add_parser("profile-create", help="Create a profile from an env file")
    p_create.add_argument("env_file", help="Path to .env file")
    p_create.add_argument("--name", default="default", help="Profile name")
    p_create.add_argument("--output", default="profile.json", help="Output JSON path")
    p_create.add_argument("--description", default="", help="Profile description")
    p_create.set_defaults(func=cmd_profile_create)


def dispatch_profile(args: argparse.Namespace) -> int:
    if hasattr(args, "func"):
        return args.func(args)
    print("No profile subcommand specified.", file=sys.stderr)
    return 2
