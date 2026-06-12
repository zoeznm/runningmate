#!/usr/bin/env bash
set -euo pipefail

APPLY="${RUNNINGMATE_FIREWALL_APPLY:-0}"
SSH_CIDR="${RUNNINGMATE_SSH_ALLOW_CIDR:-}"

run() {
  echo "+ $*"
  if [[ "${APPLY}" == "1" ]]; then
    "$@"
  fi
}

if ! command -v ufw >/dev/null 2>&1; then
  echo "ufw is required. Install it before applying firewall rules." >&2
  exit 1
fi

if [[ "${APPLY}" == "1" && -z "${SSH_CIDR}" ]]; then
  echo "Set RUNNINGMATE_SSH_ALLOW_CIDR before applying, for example 203.0.113.10/32." >&2
  exit 1
fi

run sudo ufw default deny incoming
run sudo ufw default allow outgoing
run sudo ufw allow 80/tcp
run sudo ufw allow 443/tcp

if [[ -n "${SSH_CIDR}" ]]; then
  run sudo ufw allow from "${SSH_CIDR}" to any port 22 proto tcp
else
  echo "+ skip ssh allow rule because RUNNINGMATE_SSH_ALLOW_CIDR is empty"
fi

run sudo ufw deny 3306/tcp
run sudo ufw deny 5432/tcp
run sudo ufw deny 6379/tcp

if [[ "${APPLY}" == "1" ]]; then
  sudo ufw --force enable
  sudo ufw status verbose
else
  echo "Dry-run only. Set RUNNINGMATE_FIREWALL_APPLY=1 to apply."
fi
