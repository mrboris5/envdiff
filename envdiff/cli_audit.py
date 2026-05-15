"""CLI helpers for the 'audit' sub-command in envdiff."""

from __future__ import annotations

import sys
from typing import Optional

from envdiff.auditor import AuditLog, AuditEvent


AUDIT_LOG_PATH = ".envdiff_audit.log"


def cmd_audit_show(log_path: str = AUDIT_LOG_PATH, fmt: str = "text") -> int:
    """Print the contents of the audit log file."""
    try:
        with open(log_path, "r", encoding="utf-8") as fh:
            content = fh.read().strip()
    except FileNotFoundError:
        print(f"No audit log found at '{log_path}'.", file=sys.stderr)
        return 1

    if not content:
        print("Audit log is empty.")
        return 0

    if fmt == "json":
        import json
        lines = [ln for ln in content.splitlines() if ln.strip()]
        # Re-emit as JSON array of raw log lines for simplicity
        print(json.dumps(lines, indent=2))
    else:
        print(content)
    return 0


def cmd_audit_clear(log_path: str = AUDIT_LOG_PATH) -> int:
    """Clear the audit log file."""
    try:
        open(log_path, "w").close()
        print(f"Audit log cleared: {log_path}")
        return 0
    except OSError as exc:
        print(f"Error clearing audit log: {exc}", file=sys.stderr)
        return 1


def register_audit_commands(subparsers) -> None:
    """Attach 'audit' sub-commands to an argparse subparsers group."""
    audit_parser = subparsers.add_parser("audit", help="Manage the envdiff audit log")
    audit_sub = audit_parser.add_subparsers(dest="audit_cmd")

    show_p = audit_sub.add_parser("show", help="Display audit log")
    show_p.add_argument("--log", default=AUDIT_LOG_PATH, help="Path to audit log file")
    show_p.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")

    clear_p = audit_sub.add_parser("clear", help="Clear the audit log")
    clear_p.add_argument("--log", default=AUDIT_LOG_PATH, help="Path to audit log file")


def dispatch_audit(args) -> Optional[int]:
    """Dispatch parsed args to the appropriate audit sub-command handler."""
    if args.audit_cmd == "show":
        return cmd_audit_show(log_path=args.log, fmt=args.fmt)
    if args.audit_cmd == "clear":
        return cmd_audit_clear(log_path=args.log)
    print("No audit sub-command specified. Use 'show' or 'clear'.", file=sys.stderr)
    return 1
