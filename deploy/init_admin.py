#!/usr/bin/env python3
import json
import sqlite3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app  # noqa: E402


def normalize_role(role):
    key = str(role or "owner").strip().lower()
    if key in {"owner", "admin"}:
        return "owner"
    if key == "manager":
        return "manager"
    return "owner"


def default_modules(role):
    if role == "owner":
        return list(app.ALL_MODULES)
    return [
        "dashboard",
        "notifications",
        "customers",
        "estimates",
        "projects",
        "change_orders",
        "documents",
        "document_templates",
        "system_settings",
    ]


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 deploy/init_admin.py <username> <password> [owner|manager]")
        return 1

    username = sys.argv[1].strip()
    password = sys.argv[2].strip()
    role = normalize_role(sys.argv[3] if len(sys.argv) > 3 else "owner")

    if not username or not password:
        print("[ERROR] username/password required")
        return 1

    app.init_db()
    conn = sqlite3.connect(app.DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    modules = default_modules(role)
    ts = app.now_ts()
    lang = app.DEFAULT_LANGUAGE

    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    if row:
        cur.execute(
            """
            UPDATE users
            SET password=?, role=?, language=?, modules_json=?, updated_at=?
            WHERE id=?
            """,
            (password, role, lang, json.dumps(modules, ensure_ascii=False), ts, row["id"]),
        )
        action = "updated"
        user_id = row["id"]
    else:
        cur.execute(
            """
            INSERT INTO users(username,password,role,language,modules_json,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?)
            """,
            (username, password, role, lang, json.dumps(modules, ensure_ascii=False), ts, ts),
        )
        action = "created"
        user_id = cur.lastrowid

    conn.commit()
    conn.close()

    print(f"[OK] {action} user id={user_id}, username={username}, role={role}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
