#!/usr/bin/env python3
"""Shared helpers for RunningMate private-server operations scripts."""

from __future__ import annotations

import json
import os
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.request
from email.message import EmailMessage
from pathlib import Path


DEFAULT_CONFIG_FILES = (
    "/opt/app/config/ops.env",
    "/opt/app/config/mail.env",
)
DEFAULT_STATE_DIR = "/var/tmp/runningmate-ops"


def load_env_file(path: str | os.PathLike[str]) -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_ops_env() -> None:
    extra = os.environ.get("RUNNINGMATE_OPS_ENV_FILE")
    if extra:
        load_env_file(extra)

    for path in DEFAULT_CONFIG_FILES:
        load_env_file(path)


def state_dir() -> Path:
    path = Path(os.environ.get("RUNNINGMATE_OPS_STATE_DIR", DEFAULT_STATE_DIR))
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default or {}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def alert_recipient() -> str:
    return (
        os.environ.get("RUNNINGMATE_ALERT_EMAIL_TO")
        or os.environ.get("RUNNINGMATE_ALERT_TO")
        or ""
    ).strip()


def alert_sender() -> str:
    return (
        os.environ.get("RUNNINGMATE_ALERT_EMAIL_FROM")
        or os.environ.get("RUNNINGMATE_MAIL_FROM")
        or os.environ.get("SMTP_USERNAME")
        or ""
    ).strip()


def should_repeat_alert(key: str, repeat_seconds: int) -> bool:
    path = state_dir() / f"{key}.json"
    state = read_json(path, {})
    now = int(time.time())
    previous = int(state.get("last_sent_at") or 0)
    if previous and now - previous < repeat_seconds:
        return False
    state["last_sent_at"] = now
    write_json(path, state)
    return True


def _send_via_sendgrid(sender: str, recipient: str, subject: str, body: str) -> None:
    api_key = os.environ["SENDGRID_API_KEY"]
    payload = {
        "personalizations": [{"to": [{"email": recipient}]}],
        "from": {"email": sender},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    request = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status >= 300:
                raise RuntimeError(f"SendGrid returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"SendGrid returned HTTP {exc.code}") from exc


def _send_via_smtp(sender: str, recipient: str, subject: str, body: str) -> None:
    host = os.environ.get("SMTP_HOST", "").strip()
    username = os.environ.get("SMTP_USERNAME", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    if not host or not username or not password:
        raise RuntimeError("SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD must be set")

    port = int(os.environ.get("SMTP_PORT", "587"))
    use_ssl = os.environ.get("SMTP_USE_SSL", "").strip().lower() in {"1", "true", "yes", "on"}
    use_tls = os.environ.get("SMTP_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    context = ssl.create_default_context()
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, context=context, timeout=10) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)
        return

    with smtplib.SMTP(host, port, timeout=10) as smtp:
        if use_tls:
            smtp.starttls(context=context)
        smtp.login(username, password)
        smtp.send_message(message)


def send_alert(subject: str, body: str, dry_run: bool = False) -> bool:
    load_ops_env()
    recipient = alert_recipient()
    sender = alert_sender()
    if not recipient or not sender:
        print("alert_not_sent: RUNNINGMATE_ALERT_EMAIL_TO and sender are required", file=sys.stderr)
        return False

    if dry_run:
        print(f"alert_dry_run: to={recipient} subject={subject}")
        return True

    if os.environ.get("SENDGRID_API_KEY"):
        _send_via_sendgrid(sender, recipient, subject, body)
    else:
        _send_via_smtp(sender, recipient, subject, body)
    print(f"alert_sent: to={recipient} subject={subject}")
    return True
