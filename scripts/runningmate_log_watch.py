#!/usr/bin/env python3
"""Scan new RunningMate log lines and email operational errors."""

from __future__ import annotations

import argparse
import os
import re
import socket
import sys
import time
from pathlib import Path

from runningmate_ops_common import read_json, send_alert, state_dir, write_json


DEFAULT_LOG = "/var/log/wiz/app"
DEFAULT_PATTERN = r"(ERROR|Traceback|OperationalError|Internal Server Error|Access denied|RuntimeError)"


def read_new_text(path: Path, state: dict, max_bytes: int) -> tuple[str, dict]:
    if not path.exists():
        return "", state

    stat = path.stat()
    inode = stat.st_ino
    previous_inode = state.get("inode")
    offset = int(state.get("offset") or 0)
    if previous_inode != inode or offset > stat.st_size:
        offset = 0

    with path.open("rb") as fp:
        fp.seek(offset)
        data = fp.read(max_bytes)
        new_offset = fp.tell()

    state.update({"inode": inode, "offset": new_offset, "size": stat.st_size})
    return data.decode("utf-8", "replace"), state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default=os.environ.get("RUNNINGMATE_LOG_FILE", DEFAULT_LOG))
    parser.add_argument("--pattern", default=os.environ.get("RUNNINGMATE_LOG_ALERT_PATTERN", DEFAULT_PATTERN))
    parser.add_argument("--max-bytes", type=int, default=int(os.environ.get("RUNNINGMATE_LOG_WATCH_MAX_BYTES", "262144")))
    parser.add_argument("--initialize", action="store_true", help="store current log offset without sending alerts")
    parser.add_argument("--dry-run-alert", action="store_true")
    args = parser.parse_args()

    log_path = Path(args.log)
    state_path = state_dir() / f"log-watch-{re.sub(r'[^a-zA-Z0-9]+', '-', str(log_path)).strip('-')}.json"
    state = read_json(state_path, {})
    if args.initialize:
        if log_path.exists():
            stat = log_path.stat()
            state.update({"inode": stat.st_ino, "offset": stat.st_size, "size": stat.st_size})
            write_json(state_path, state)
            print(f"log_watch_initialized: {log_path} offset={stat.st_size}")
            return 0
        print(f"log_watch_initialize_skipped: missing {log_path}")
        return 1

    text, state = read_new_text(log_path, state, args.max_bytes)
    write_json(state_path, state)

    if not text:
        print("log_watch_ok: no new log lines")
        return 0

    pattern = re.compile(args.pattern, re.IGNORECASE)
    matches = [line for line in text.splitlines() if pattern.search(line)]
    if not matches:
        print("log_watch_ok: no matching errors")
        return 0

    max_lines = int(os.environ.get("RUNNINGMATE_LOG_ALERT_MAX_LINES", "80"))
    selected = matches[-max_lines:]
    hostname = socket.gethostname()
    subject = f"[RunningMate] ALERT log errors ({len(matches)})"
    body = (
        f"Host: {hostname}\n"
        f"Log: {log_path}\n"
        f"Checked at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
        f"Matched lines: {len(matches)}\n\n"
        + "\n".join(selected)
        + "\n"
    )
    send_alert(subject, body, dry_run=args.dry_run_alert)
    print(f"log_watch_alert: matches={len(matches)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
