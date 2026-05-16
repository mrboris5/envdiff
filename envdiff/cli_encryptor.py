"""CLI commands for encrypting and decrypting .env file values."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace

from envdiff.encryptor import decrypt_env_dict, encrypt_env_dict, generate_key
from envdiff.parser import parse_env_file


def cmd_encrypt(args: Namespace) -> int:
    if not args.key:
        print("error: --key is required", file=sys.stderr)
        return 2
    env = parse_env_file(args.env_file)
    result = encrypt_env_dict(env, args.key, sensitive_only=not args.all)
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"# Encrypted {len(result.encrypted_keys)} key(s), skipped {len(result.skipped_keys)}")
        for entry in result.entries:
            print(f"{entry.key}={entry.result}")
    return 0


def cmd_decrypt(args: Namespace) -> int:
    if not args.key:
        print("error: --key is required", file=sys.stderr)
        return 2
    env = parse_env_file(args.env_file)
    decrypted = decrypt_env_dict(env, args.key)
    if args.format == "json":
        print(json.dumps(decrypted, indent=2))
    else:
        for k, v in decrypted.items():
            print(f"{k}={v}")
    return 0


def cmd_keygen(args: Namespace) -> int:
    print(generate_key())
    return 0


def register_encrypt_commands(subparsers) -> None:
    p_enc = subparsers.add_parser("encrypt", help="Encrypt sensitive values in a .env file")
    p_enc.add_argument("env_file", help="Path to .env file")
    p_enc.add_argument("--key", default="", help="Fernet encryption key")
    p_enc.add_argument("--all", action="store_true", help="Encrypt all values, not just sensitive ones")
    p_enc.add_argument("--format", choices=["text", "json"], default="text")
    p_enc.set_defaults(func=cmd_encrypt)

    p_dec = subparsers.add_parser("decrypt", help="Decrypt values in an encrypted .env file")
    p_dec.add_argument("env_file", help="Path to .env file")
    p_dec.add_argument("--key", default="", help="Fernet encryption key")
    p_dec.add_argument("--format", choices=["text", "json"], default="text")
    p_dec.set_defaults(func=cmd_decrypt)

    p_key = subparsers.add_parser("keygen", help="Generate a new Fernet encryption key")
    p_key.set_defaults(func=cmd_keygen)


def dispatch_encrypt(args: Namespace) -> int:
    return args.func(args)
