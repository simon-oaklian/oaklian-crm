#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

DB_PATH="${CRM_DB_PATH:-$ROOT_DIR/crm.db}"
UPLOAD_DIR="${CRM_UPLOAD_DIR:-$ROOT_DIR/uploads}"
BACKUP_ROOT="${1:-$ROOT_DIR/backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$BACKUP_ROOT/crm_backup_$STAMP"
ARCHIVE_PATH="$BACKUP_ROOT/crm_backup_$STAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

if [[ ! -f "$DB_PATH" ]]; then
  echo "[ERROR] crm.db not found at: $DB_PATH"
  exit 1
fi

if command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/crm.db'"
else
  cp -a "$DB_PATH" "$BACKUP_DIR/crm.db"
fi

if [[ -d "$UPLOAD_DIR" ]]; then
  cp -a "$UPLOAD_DIR" "$BACKUP_DIR/uploads"
fi

if [[ -f "$ENV_FILE" ]]; then
  cp -a "$ENV_FILE" "$BACKUP_DIR/.env"
fi

( cd "$BACKUP_ROOT" && tar -czf "$(basename "$ARCHIVE_PATH")" "$(basename "$BACKUP_DIR")" )

echo "[OK] Backup folder: $BACKUP_DIR"
echo "[OK] Backup archive: $ARCHIVE_PATH"
