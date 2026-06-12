#!/usr/bin/env bash
set -euo pipefail

load_env_file() {
  local env_file="$1"
  if [[ -r "${env_file}" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${env_file}"
    set +a
  fi
}

load_env_file "${RUNNINGMATE_DB_ENV_FILE:-/opt/app/config/database.env}"
load_env_file "${RUNNINGMATE_BACKUP_ENV_FILE:-/opt/app/config/backup.env}"

DATA_DIR="${RUNNINGMATE_DATA_DIR:-/opt/app/data}"
IMAGE_DIR="${RUNNINGMATE_UPLOAD_DIR:-/opt/app/data/run_images}"
MEDIA_DIR="${RUNNINGMATE_MEDIA_UPLOAD_DIR:-/opt/app/data/run_media}"
BACKUP_DIR="${RUNNINGMATE_BACKUP_DIR:-/opt/app/data/backups}"
MYSQL_DEFAULTS_FILE="${RUNNINGMATE_DB_MYSQL_DEFAULTS_FILE:-/opt/app/config/mysql-backup.cnf}"
DB_NAME="${RUNNINGMATE_DB_NAME:-}"

DATA_DIR="$(realpath -m "${DATA_DIR}")"
IMAGE_DIR="$(realpath -m "${IMAGE_DIR}")"
MEDIA_DIR="$(realpath -m "${MEDIA_DIR}")"
BACKUP_DIR="$(realpath -m "${BACKUP_DIR}")"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${BACKUP_DIR}/${timestamp}"
mkdir -p "${target}"
chmod 700 "${BACKUP_DIR}" "${target}"

backup_dir() {
  local label="$1"
  local path="$2"
  if [[ -d "${path}" ]]; then
    tar -C "$(dirname "${path}")" -czf "${target}/${label}.tar.gz" "$(basename "${path}")"
  fi
}

if [[ -d "${DATA_DIR}" ]]; then
  data_name="$(basename "${DATA_DIR}")"
  tar -C "$(dirname "${DATA_DIR}")" \
    --exclude="${data_name}/backups" \
    --exclude="${data_name}/run_images" \
    --exclude="${data_name}/run_media" \
    -czf "${target}/data.tar.gz" "${data_name}"
fi
backup_dir "run_images" "${IMAGE_DIR}"
backup_dir "run_media" "${MEDIA_DIR}"

if [[ -n "${MYSQL_DEFAULTS_FILE}" && -r "${MYSQL_DEFAULTS_FILE}" && -n "${DB_NAME}" ]] && command -v mysqldump >/dev/null 2>&1; then
  mysqldump --defaults-extra-file="${MYSQL_DEFAULTS_FILE}" \
    --single-transaction --skip-lock-tables --no-tablespaces --set-gtid-purged=OFF --triggers --events "${DB_NAME}" \
    | gzip -c > "${target}/database.sql.gz"
fi

cat > "${target}/manifest.txt" <<EOF
created_at=${timestamp}
data_dir=${DATA_DIR}
image_dir=${IMAGE_DIR}
media_dir=${MEDIA_DIR}
database_backup=$([[ -f "${target}/database.sql.gz" ]] && echo yes || echo no)
EOF

find "${target}" -type f -exec chmod 600 {} \;
echo "${target}"
