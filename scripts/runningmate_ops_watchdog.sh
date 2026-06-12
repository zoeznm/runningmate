#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${RUNNINGMATE_PROJECT_ROOT:-/opt/app/project/main}"
PYTHON_BIN="${RUNNINGMATE_PYTHON_BIN:-/opt/conda/envs/app/bin/python}"
HEALTH_INTERVAL="${RUNNINGMATE_WATCHDOG_HEALTH_INTERVAL_SECONDS:-60}"
LOG_INTERVAL="${RUNNINGMATE_WATCHDOG_LOG_INTERVAL_SECONDS:-300}"
HEALTH_LOG="${RUNNINGMATE_WATCHDOG_HEALTH_LOG:-/var/log/wiz/healthcheck.log}"
LOG_WATCH_LOG="${RUNNINGMATE_WATCHDOG_LOG_WATCH_LOG:-/var/log/wiz/log-watch.log}"

mkdir -p "$(dirname "${HEALTH_LOG}")" "$(dirname "${LOG_WATCH_LOG}")"

cd "${PROJECT_ROOT}"

last_log_check=0
while true; do
  "${PYTHON_BIN}" scripts/runningmate_healthcheck.py >>"${HEALTH_LOG}" 2>&1 || true

  now="$(date +%s)"
  if (( now - last_log_check >= LOG_INTERVAL )); then
    "${PYTHON_BIN}" scripts/runningmate_log_watch.py >>"${LOG_WATCH_LOG}" 2>&1 || true
    last_log_check="${now}"
  fi

  sleep "${HEALTH_INTERVAL}"
done
