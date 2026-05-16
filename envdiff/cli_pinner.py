"""CLI commands for env key pinning."""
from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace

from envdiff.parser import parse_env_file
from envdiff.pinner import load_pin_store, save_pin_store

_DEFAULT_PIN_FILE = ".envpins.json"


def cmd_pin_add(args: Namespace) -> int:
    env = parse_env_file(args.env_file)
    if args.key not in env:
        print(f"ERROR: key '{args.key}' not found in {args.env_file}", file=sys.stderr)
        return 1
    store = load_pin_store(args.pin_file)
    entry = store.pin(key=args.key, value=env[args.key], source=args.env_file, note=args.note)
    save_pin_store(store, args.pin_file)
    print(f"Pinned: {entry}")
    return 0


def cmd_pin_remove(args: Namespace) -> int:
    store = load_pin_store(args.pin_file)
    if store.unpin(args.key):
        save_pin_store(store, args.pin_file)
        print(f"Unpinned: {args.key}")
        return 0
    print(f"Key '{args.key}' was not pinned.", file=sys.stderr)
    return 1


def cmd_pin_check(args: Namespace) -> int:
    env = parse_env_file(args.env_file)
    store = load_pin_store(args.pin_file)
    drift = store.check_drift(env)
    if args.format == "json":
        print(json.dumps(drift, indent=2))
    else:
        if not drift:
            print("All pinned keys match.")
        else:
            for d in drift:
                print(f"  [{d['status'].upper()}] {d['key']}: pinned={d['pinned']!r} current={d['current']!r}")
    return 1 if drift else 0


def cmd_pin_list(args: Namespace) -> int:
    store = load_pin_store(args.pin_file)
    pins = store.all_pins()
    if args.format == "json":
        print(json.dumps([p.to_dict() for p in pins], indent=2))
    else:
        if not pins:
            print("No keys pinned.")
        else:
            for p in pins:
                print(f"  {p}")
    return 0


def register_pin_commands(sub) -> None:
    def _add_common(p):
        p.add_argument("--pin-file", default=_DEFAULT_PIN_FILE, help="Path to pin store JSON")
        p.add_argument("--format", choices=["text", "json"], default="text")

    p_add = sub.add_parser("pin-add", help="Pin a key's current value")
    p_add.add_argument("env_file")
    p_add.add_argument("key")
    p_add.add_argument("--note", default=None)
    _add_common(p_add)

    p_rm = sub.add_parser("pin-remove", help="Unpin a key")
    p_rm.add_argument("key")
    _add_common(p_rm)

    p_chk = sub.add_parser("pin-check", help="Check pinned keys against an env file")
    p_chk.add_argument("env_file")
    _add_common(p_chk)

    p_ls = sub.add_parser("pin-list", help="List all pinned keys")
    _add_common(p_ls)


def dispatch_pin(args: Namespace) -> int:
    return {
        "pin-add": cmd_pin_add,
        "pin-remove": cmd_pin_remove,
        "pin-check": cmd_pin_check,
        "pin-list": cmd_pin_list,
    }[args.command](args)
