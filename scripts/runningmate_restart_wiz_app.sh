#!/usr/bin/env bash
set -euo pipefail

WIZ_APP="${RUNNINGMATE_WIZ_APP:-/usr/local/bin/wiz.app}"
LOG_FILE="${RUNNINGMATE_WIZ_RESTART_LOG:-/mnt/data/wiz/log/app-restart.log}"
PATTERN='^/opt/conda/envs/app/bin/python3\.14 /opt/conda/envs/app/bin/wiz run --log /var/log/wiz/app$'

parent_pid="$(pgrep -f "${PATTERN}" | head -n 1 || true)"
if [[ -n "${parent_pid}" ]]; then
  pgid="$(ps -o pgid= -p "${parent_pid}" | tr -d ' ' || true)"
  if [[ -n "${pgid}" ]]; then
    kill -TERM "-${pgid}" 2>/dev/null || true
    for _ in $(seq 1 20); do
      if ! ps -o pid= -g "${pgid}" 2>/dev/null | grep -q '[0-9]'; then
        break
      fi
      sleep 0.5
    done
    if ps -o pid= -g "${pgid}" 2>/dev/null | grep -q '[0-9]'; then
      kill -KILL "-${pgid}" 2>/dev/null || true
    fi
  fi
fi

mkdir -p "$(dirname "${LOG_FILE}")"
setsid "${WIZ_APP}" >"${LOG_FILE}" 2>&1 < /dev/null &
echo "started ${WIZ_APP}"
