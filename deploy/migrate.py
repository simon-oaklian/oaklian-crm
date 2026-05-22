#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import app  # noqa: E402


if __name__ == "__main__":
    app.init_db()
    print(f"[OK] migration done: db={app.DB_PATH}")
