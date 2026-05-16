"""CLI commands for tagging .env keys."""

from __future__ import annotations

import argparse
import json
import os
import sys

from envdiff.parser import parse_env_file
from envdiff.tagger import TagStore


def cmd_tag_add(args: argparse.Namespace) -> int:
    store = TagStore.load(args.tag_file) if os.path.exists(args.tag_file) else TagStore()
    env = parse_env_file(args.env_file)
    if args.key not in env:
        print(f"ERROR: key '{args.key}' not found in {args.env_file}", file=sys.stderr)
        return 1
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    entry = store.add(args.key, tags, note=args.note)
    store.save(args.tag_file)
    print(f"Tagged: {entry}")
    return 0


def cmd_tag_remove(args: argparse.Namespace) -> int:
    if not os.path.exists(args.tag_file):
        print("ERROR: tag file not found", file=sys.stderr)
        return 1
    store = TagStore.load(args.tag_file)
    if not store.remove(args.key):
        print(f"ERROR: key '{args.key}' not tagged", file=sys.stderr)
        return 1
    store.save(args.tag_file)
    print(f"Removed tags for '{args.key}'")
    return 0


def cmd_tag_list(args: argparse.Namespace) -> int:
    if not os.path.exists(args.tag_file):
        print("No tags found.")
        return 0
    store = TagStore.load(args.tag_file)
    if args.filter:
        entries = [e for e in store.all_entries() if args.filter in e.tags]
    else:
        entries = store.all_entries()
    if args.format == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        if not entries:
            print("No tagged keys.")
        for e in entries:
            print(str(e))
    return 0


def register_tag_commands(sub: argparse._SubParsersAction) -> None:
    p_add = sub.add_parser("tag-add", help="Add tags to a key")
    p_add.add_argument("env_file")
    p_add.add_argument("key")
    p_add.add_argument("tags", help="Comma-separated tags")
    p_add.add_argument("--note", default=None)
    p_add.add_argument("--tag-file", default=".env.tags.json")

    p_rm = sub.add_parser("tag-remove", help="Remove tags from a key")
    p_rm.add_argument("key")
    p_rm.add_argument("--tag-file", default=".env.tags.json")

    p_ls = sub.add_parser("tag-list", help="List tagged keys")
    p_ls.add_argument("--filter", default=None, help="Filter by tag name")
    p_ls.add_argument("--format", choices=["text", "json"], default="text")
    p_ls.add_argument("--tag-file", default=".env.tags.json")


def dispatch_tag(args: argparse.Namespace) -> int:
    return {
        "tag-add": cmd_tag_add,
        "tag-remove": cmd_tag_remove,
        "tag-list": cmd_tag_list,
    }[args.command](args)
