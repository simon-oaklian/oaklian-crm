#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <backup_dir_or_tar.gz> [--yes]"
  exit 1
fi

INPUT_PATH="$1"
AUTO_YES="${2:-}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

DB_PATH="${CRM_DB_PATH:-$ROOT_DIR/crm.db}"
UPLOAD_DIR="${CRM_UPLOAD_DIR:-$ROOT_DIR/uploads}"
TMP_DIR=""
RESTORE_DIR="$INPUT_PATH"

if [[ ! -e "$INPUT_PATH" ]]; then
  echo "[ERROR] Backup path not found: $INPUT_PATH"
  exit 1
fi

if [[ -f "$INPUT_PATH" && "$INPUT_PATH" == *.tar.gz ]]; then
  TMP_DIR="$(mktemp -d)"
  tar -xzf "$INPUT_PATH" -C "$TMP_DIR"
  RESTORE_DIR="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
fi

if [[ ! -d "$RESTORE_DIR" ]]; then
  echo "[ERROR] Restore directory invalid: $RESTORE_DIR"
  [[ -n "$TMP_DIR" ]] && rm -rf "$TMP_DIR"
  exit 1
fi

echo "Restore source : $RESTORE_DIR"
echo "Target DB      : $DB_PATH"
echo "Target uploads : $UPLOAD_DIR"

aif_confirm="no"
if [[ "$AUTO_YES" == "--yes" ]]; then
  aif_confirm="yes"
else
  read -r -p "This will overwrite current data. Continue? (yes/no): " aif_confirm
fi

if [[ "$aif_confirm" != "yes" ]]; then
  echo "Canceled."
  [[ -n "$TMP_DIR" ]] && rm -rf "$TMP_DIR"
  exit 0
fi

mkdir -p "$(dirname "$DB_PATH")"
mkdir -p "$UPLOAD_DIR"

if [[ -f "$DB_PATH" ]]; then
  cp -a "$DB_PATH" "$DB_PATH.bak.$(date +%Y%m%d_%H%M%S)"
fi

if [[ -f "$RESTORE_DIR/crm.db" ]]; then
  cp -a "$RESTORE_DIR/crm.db" "$DB_PATH"
else
  echo "[WARN] crm.db not found in backup."
fi

if [[ -d "$RESTORE_DIR/uploads" ]]; then
  rm -rf "$UPLOAD_DIR"
  cp -a "$RESTORE_DIR/uploads" "$UPLOAD_DIR"
else
  echo "[WARN] uploads directory not found in backup."
fi

echo "[OK] Restore completed."

if [[ -n "$TMP_DIR" ]]; then
  rm -rf "$TMP_DIR"
fi
