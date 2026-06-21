#!/usr/bin/env python3
"""Check RunningMate health and optionally send email/restart on failure."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from runningmate_ops_common import read_json, send_alert, state_dir, write_json


DEFAULT_URL = "http://127.0.0.1:3000/healthz"
AUTH_LOGIN_PAYLOAD = {"username": "__runningmate_healthcheck__", "password": "__invalid__"}
DEFAULT_OAUTH_PROVIDERS = ""
OAUTH_PROVIDER_HOSTS = {
    "naver": "nid.naver.com",
    "google": "accounts.google.com",
    "apple": "appleid.apple.com",
}


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


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


def auth_login_url(base_url: str) -> str:
    configured = os.environ.get("RUNNINGMATE_AUTH_LOGIN_URL")
    if configured:
        return configured

    parsed = urllib.parse.urlparse(base_url)
    return urllib.parse.urlunparse(parsed._replace(path="/api/auth/login", params="", query="", fragment=""))


def read_http_error(exc: urllib.error.HTTPError) -> tuple[int, str, str]:
    body = exc.read(4096).decode("utf-8", "replace")
    content_type = exc.headers.get("Content-Type", "")
    return exc.code, body, content_type


def check_auth_login_json(url: str, timeout: float) -> tuple[bool, str]:
    body = json.dumps(AUTH_LOGIN_PAYLOAD).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "User-Agent": "runningmate-healthcheck/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            response_body = response.read(4096).decode("utf-8", "replace")
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        status, response_body, content_type = read_http_error(exc)
    except urllib.error.URLError as exc:
        return False, f"auth_login URL error: {exc.reason}"
    except socket.timeout:
        return False, "auth_login timeout"
    except Exception as exc:
        return False, f"auth_login {type(exc).__name__}: {exc}"

    try:
        payload = json.loads(response_body or "{}")
    except Exception:
        preview = " ".join((response_body or "").split())[:300]
        return False, f"auth_login expected JSON, got HTTP {status} {content_type}: {preview}"

    if status not in (200, 400, 401):
        return False, f"auth_login expected HTTP 200/400/401 for invalid credentials, got HTTP {status}: {payload}"
    if payload.get("success") is not False:
        return False, f"auth_login expected success=false for invalid credentials: {payload}"
    return True, f"auth_login_json_ok: HTTP {status}"


def oauth_start_url(base_url: str, provider: str) -> str:
    configured = os.environ.get(f"RUNNINGMATE_OAUTH_{provider.upper()}_START_URL")
    if configured:
        return configured

    parsed = urllib.parse.urlparse(base_url)
    return urllib.parse.urlunparse(parsed._replace(
        path=f"/api/auth/oauth/{provider}/start",
        params="",
        query="",
        fragment="",
    ))


def parse_providers(raw: str) -> list[str]:
    providers = []
    for item in str(raw or "").split(","):
        provider = item.strip().lower()
        if provider and provider not in providers:
            providers.append(provider)
    return providers


def location_preview(location: str) -> str:
    parsed = urllib.parse.urlparse(str(location or ""))
    if parsed.netloc:
        return f"{parsed.netloc}{parsed.path}"
    return parsed.path or "<missing>"


def check_oauth_start_redirect(url: str, provider: str, timeout: float) -> tuple[bool, str]:
    opener = urllib.request.build_opener(NoRedirectHandler)
    request = urllib.request.Request(url, headers={"User-Agent": "runningmate-healthcheck/1.0"})

    try:
        with opener.open(request, timeout=timeout) as response:
            status = response.status
            location = response.headers.get("Location", "")
    except urllib.error.HTTPError as exc:
        status = exc.code
        location = exc.headers.get("Location", "")
    except urllib.error.URLError as exc:
        return False, f"oauth_{provider} URL error: {exc.reason}"
    except socket.timeout:
        return False, f"oauth_{provider} timeout"
    except Exception as exc:
        return False, f"oauth_{provider} {type(exc).__name__}: {exc}"

    if status not in (301, 302, 303, 307, 308):
        return False, f"oauth_{provider} expected redirect, got HTTP {status}"
    if not location:
        return False, f"oauth_{provider} redirect missing Location"
    if "social_error=social_config_missing" in location:
        return False, f"oauth_{provider} config_missing"

    parsed = urllib.parse.urlparse(location)
    expected_host = OAUTH_PROVIDER_HOSTS.get(provider)
    if expected_host and parsed.netloc.lower() != expected_host:
        return False, f"oauth_{provider} unexpected redirect: {location_preview(location)}"
    return True, f"oauth_{provider}_redirect_ok"


def check_oauth_providers(base_url: str, providers: list[str], timeout: float) -> tuple[bool, str]:
    details = []
    for provider in providers:
        if provider not in OAUTH_PROVIDER_HOSTS:
            return False, f"oauth_{provider} unsupported healthcheck provider"
        ok, detail = check_oauth_start_redirect(oauth_start_url(base_url, provider), provider, timeout)
        details.append(detail)
        if not ok:
            return False, "; ".join(details)
    return True, "; ".join(details)


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
    parser.add_argument("--auth-login-url", default=None)
    parser.add_argument("--skip-auth-login", action="store_true", default=os.environ.get("RUNNINGMATE_SKIP_AUTH_LOGIN_HEALTHCHECK") == "1")
    parser.add_argument("--oauth-providers", default=os.environ.get("RUNNINGMATE_OAUTH_HEALTHCHECK_PROVIDERS", DEFAULT_OAUTH_PROVIDERS))
    parser.add_argument("--skip-oauth", action="store_true", default=os.environ.get("RUNNINGMATE_SKIP_OAUTH_HEALTHCHECK") == "1")
    parser.add_argument("--restart", action="store_true", default=os.environ.get("RUNNINGMATE_HEALTHCHECK_RESTART") == "1")
    parser.add_argument("--dry-run-alert", action="store_true")
    args = parser.parse_args()

    ok, detail = check_url(args.url, args.timeout)
    if ok and not args.skip_auth_login:
        login_url = args.auth_login_url or auth_login_url(args.url)
        login_ok, login_detail = check_auth_login_json(login_url, args.timeout)
        ok = login_ok
        detail = f"{detail}; {login_detail}" if login_ok else login_detail
    oauth_providers = parse_providers(args.oauth_providers)
    if ok and not args.skip_oauth and oauth_providers:
        oauth_ok, oauth_detail = check_oauth_providers(args.url, oauth_providers, args.timeout)
        ok = oauth_ok
        detail = f"{detail}; {oauth_detail}" if oauth_ok else oauth_detail
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
        if ok_after_restart and not args.skip_auth_login:
            login_url = args.auth_login_url or auth_login_url(args.url)
            login_ok_after_restart, login_detail_after_restart = check_auth_login_json(login_url, args.timeout)
            ok_after_restart = login_ok_after_restart
            detail_after_restart = (
                f"{detail_after_restart}; {login_detail_after_restart}"
                if login_ok_after_restart
                else login_detail_after_restart
            )
        if ok_after_restart and not args.skip_oauth and oauth_providers:
            oauth_ok_after_restart, oauth_detail_after_restart = check_oauth_providers(args.url, oauth_providers, args.timeout)
            ok_after_restart = oauth_ok_after_restart
            detail_after_restart = (
                f"{detail_after_restart}; {oauth_detail_after_restart}"
                if oauth_ok_after_restart
                else oauth_detail_after_restart
            )
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
