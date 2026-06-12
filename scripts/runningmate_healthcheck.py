#!/usr/bin/env python3
"""Check RunningMate health and optionally send email/restart on failure."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

from runningmate_ops_common import read_json, send_alert, state_dir, write_json


DEFAULT_URL = "http://127.0.0.1:3000/healthz"


def check_url(url: str, timeout: float) -> tuple[bool, str]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "runningmate-healthcheck/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(4096).decode("utf-8", "replace")
            if 200 <= response.status < 300:
                return True, f"HTTP {response.status}: {body[:300]}"
            return False, f"HTTP {response.status}: {body[:300]}"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return False, f"URL error: {exc.reason}"
    except socket.timeout:
        return False, "timeout"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def maybe_restart(command: str, dry_run: bool) -> str:
    if not command:
        return "restart skipped: RUNNINGMATE_RESTART_COMMAND is not set"
    if dry_run:
        return f"restart dry-run: {command}"
    result = subprocess.run(command, shell=True, check=False, capture_output=True, text=True, timeout=60)
    output = (result.stdout or result.stderr or "").strip()
    return f"restart exit={result.returncode}: {output[:1000]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.environ.get("RUNNINGMATE_HEALTHCHECK_URL", DEFAULT_URL))
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("RUNNINGMATE_HEALTHCHECK_TIMEOUT", "5")))
    parser.add_argument("--restart", action="store_true", default=os.environ.get("RUNNINGMATE_HEALTHCHECK_RESTART") == "1")
    parser.add_argument("--dry-run-alert", action="store_true")
    args = parser.parse_args()

    ok, detail = check_url(args.url, args.timeout)
    state_path = state_dir() / "healthcheck.json"
    state = read_json(state_path, {})
    was_ok = state.get("ok")
    now = int(time.time())
    hostname = socket.gethostname()

    if ok:
        state.update({"ok": True, "last_ok_at": now, "detail": detail})
        write_json(state_path, state)
        if was_ok is False:
            send_alert(
                "[RunningMate] RECOVERY healthcheck ok",
                f"Host: {hostname}\nURL: {args.url}\nResult: {detail}\n",
                dry_run=args.dry_run_alert,
            )
        print(f"health_ok: {detail}")
        return 0

    restart_detail = ""
    if args.restart:
        restart_detail = maybe_restart(os.environ.get("RUNNINGMATE_RESTART_COMMAND", ""), args.dry_run_alert)
        time.sleep(float(os.environ.get("RUNNINGMATE_RECHECK_DELAY", "5")))
        ok_after_restart, detail_after_restart = check_url(args.url, args.timeout)
        if ok_after_restart:
            state.update({"ok": True, "last_ok_at": int(time.time()), "detail": detail_after_restart})
            write_json(state_path, state)
            send_alert(
                "[RunningMate] RECOVERY after restart",
                f"Host: {hostname}\nURL: {args.url}\nInitial: {detail}\nRestart: {restart_detail}\nAfter: {detail_after_restart}\n",
                dry_run=args.dry_run_alert,
            )
            print(f"health_recovered: {detail_after_restart}")
            return 0

    repeat = int(os.environ.get("RUNNINGMATE_ALERT_REPEAT_SECONDS", "3600"))
    should_send = was_ok is not False or now - int(state.get("last_alert_at") or 0) >= repeat
    state.update({"ok": False, "last_fail_at": now, "detail": detail})
    if should_send:
        state["last_alert_at"] = now
    write_json(state_path, state)

    if should_send:
        send_alert(
            "[RunningMate] ALERT healthcheck failed",
            f"Host: {hostname}\nURL: {args.url}\nResult: {detail}\n{restart_detail}\n",
            dry_run=args.dry_run_alert,
        )
    print(f"health_fail: {detail}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
