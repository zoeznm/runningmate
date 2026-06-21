#!/usr/bin/env python3
"""Validate runtime secret wiring without printing secret values."""

import os
import re
import stat
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_CONFIG_DIR = Path(os.environ.get("RUNNINGMATE_SERVER_CONFIG_DIR", "/opt/app/config"))

ENV_FILES = {
    "openai": {
        "path": SERVER_CONFIG_DIR / "openai.env",
        "required": ["OPENAI_API_KEY", "RUNNINGMATE_AI_PROVIDER"],
        "expected": {"RUNNINGMATE_AI_PROVIDER": "openai"},
    },
    "oauth": {
        "path": SERVER_CONFIG_DIR / "oauth.env",
        "required": [
            "RUNNINGMATE_PUBLIC_BASE_URL",
            "NAVER_CLIENT_ID",
            "NAVER_CLIENT_SECRET",
            "NAVER_REDIRECT_URI",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI",
            "APPLE_CLIENT_ID",
            "APPLE_REDIRECT_URI",
        ],
        "any_of": [
            ["APPLE_CLIENT_SECRET"],
            ["APPLE_TEAM_ID", "APPLE_KEY_ID", "APPLE_PRIVATE_KEY_PATH"],
        ],
        "file_keys": ["APPLE_PRIVATE_KEY_PATH"],
        "expected": {},
    },
    "mail": {
        "path": SERVER_CONFIG_DIR / "mail.env",
        "required": ["RUNNINGMATE_MAIL_FROM"],
        "any_of": [["SENDGRID_API_KEY"], ["SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"]],
        "expected": {},
    },
    "database": {
        "path": SERVER_CONFIG_DIR / "database.env",
        "required": [
            "RUNNINGMATE_DB_NAME",
            "RUNNINGMATE_DB_USER",
            "RUNNINGMATE_DB_PASSWORD",
            "RUNNINGMATE_DB_HOST",
            "RUNNINGMATE_DB_PORT",
        ],
        "expected": {},
    },
}

SECRET_PATTERNS = [
    ("openai_api_key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("google_oauth_client_secret", re.compile(r"\bGOCSPX-[A-Za-z0-9_-]{20,}\b")),
    ("sendgrid_api_key", re.compile(r"\bSG\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b")),
    ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)?PRIVATE KEY-----")),
    ("plain_password_assignment", re.compile(r"(?i)\bpassword\s*=\s*['\"][^'\"]{8,}['\"]")),
]

SKIP_DIRS = {".git", "node_modules", "__pycache__"}
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff2", ".otf", ".zip", ".gz", ".map"}


def load_env(path):
    data = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def is_set(env_data, key):
    return bool(os.environ.get(key) or env_data.get(key))


def check_env_file(name, spec):
    issues = []
    path = spec["path"]
    env_data = {}

    if path.exists():
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            issues.append(f"{path}: permissions must be 600 or stricter")
        env_data = load_env(path)
    else:
        missing_from_process = [key for key in spec.get("required", []) if not os.environ.get(key)]
        if missing_from_process:
            issues.append(f"{path}: missing and required process env vars are not all set")

    for key in spec.get("required", []):
        if not is_set(env_data, key):
            issues.append(f"{name}: {key} is not set")

    for key in spec.get("file_keys", []):
        value = os.environ.get(key) or env_data.get(key) or ""
        value = value.strip().strip('"').strip("'")
        if value and not Path(value).expanduser().exists():
            issues.append(f"{name}: {key} points to a missing file")

    for group in spec.get("any_of", []):
        if all(is_set(env_data, key) for key in group):
            break
    else:
        groups = spec.get("any_of", [])
        if groups:
            readable = " or ".join("+".join(group) for group in groups)
            issues.append(f"{name}: one of [{readable}] must be set")

    for key, expected in spec.get("expected", {}).items():
        value = os.environ.get(key) or env_data.get(key) or ""
        if str(value).strip().lower() != expected:
            issues.append(f"{name}: {key} must be {expected}")

    return issues


def scan_project():
    findings = []
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for lineno, line in enumerate(lines, 1):
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{path.relative_to(PROJECT_ROOT)}:{lineno}: {label}")
    return findings


def main():
    issues = []
    for name, spec in ENV_FILES.items():
        issues.extend(check_env_file(name, spec))
    issues.extend(scan_project())

    if issues:
        print("Runtime secret verification failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Runtime secret verification passed. No secret values were printed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
