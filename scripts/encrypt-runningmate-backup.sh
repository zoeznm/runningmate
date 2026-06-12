#!/usr/bin/env bash
set -euo pipefail

BACKUP_PATH="${1:-}"
PASSPHRASE_FILE="${RUNNINGMATE_BACKUP_PASSPHRASE_FILE:-}"

if [[ -z "${BACKUP_PATH}" || ! -d "${BACKUP_PATH}" ]]; then
  echo "Usage: RUNNINGMATE_BACKUP_PASSPHRASE_FILE=/secure/path/passphrase $0 /opt/app/data/backups/YYYYMMDDTHHMMSSZ" >&2
  exit 1
fi

if [[ -z "${PASSPHRASE_FILE}" || ! -r "${PASSPHRASE_FILE}" ]]; then
  echo "RUNNINGMATE_BACKUP_PASSPHRASE_FILE must point to a readable passphrase file." >&2
  exit 1
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required." >&2
  exit 1
fi

BACKUP_PATH="$(realpath -m "${BACKUP_PATH}")"
PARENT="$(dirname "${BACKUP_PATH}")"
NAME="$(basename "${BACKUP_PATH}")"
OUTPUT="${BACKUP_PATH}.tar.gz.enc"

tar -C "${PARENT}" -czf - "${NAME}" \
  | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 -pass "file:${PASSPHRASE_FILE}" -out "${OUTPUT}"

chmod 600 "${OUTPUT}"
sha256sum "${OUTPUT}" > "${OUTPUT}.sha256"
chmod 600 "${OUTPUT}.sha256"
echo "${OUTPUT}"
