#!/usr/bin/env python3
import argparse
import logging
import os
import sqlite3
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("CRM_DB_PATH", str(ROOT_DIR / "crm.db"))).expanduser()
UPLOAD_DIR = Path(os.getenv("CRM_UPLOAD_DIR", str(ROOT_DIR / "uploads"))).expanduser()
LOG_DIR = Path(os.getenv("CRM_LOG_DIR", str(ROOT_DIR / "logs"))).expanduser()
LOG_FILE = LOG_DIR / "cleanup.log"
BACKUP_SCRIPT = ROOT_DIR / "deploy" / "backup.sh"

ASCII_KEYWORDS = ["test", "demo", "dummy", "aaa"]
UNICODE_KEYWORDS = ["测试", "临时"]
PHONE_BLOCKLIST = {"0000000000", "1234567890", "9999999999"}
EMAIL_KEYWORDS = ["test@", "demo@", "example.com"]

VALID_ROOT_TABLES = {"customers", "estimates", "contracts", "projects", "change_orders"}

REQUIRED_DELETE_ORDER = [
    "notifications",
    "customer_followups",
    "files",
    "change_orders",
    "contract_payment_milestones",
    "project_stages",
    "projects",
    "contracts",
    "estimates",
    "customers",
]

EXTRA_DELETE_ORDER = [
    "project_tasks",
    "project_issues",
    "project_payments",
    "project_costs",
    "site_logs",
    "designer_commissions",
    "documents",
    "quotes",
    "ap_payables",
    "leads",
]


def setup_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("cleanup_test_data")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(fmt)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def table_exists(cur: sqlite3.Cursor, table: str) -> bool:
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def chunked(items: Sequence[int], size: int = 800) -> Iterable[List[int]]:
    for i in range(0, len(items), size):
        yield list(items[i : i + size])


def build_text_match_sql(columns: Sequence[str]) -> Tuple[str, List[str]]:
    parts: List[str] = []
    params: List[str] = []
    for col in columns:
        for kw in ASCII_KEYWORDS:
            parts.append(f"LOWER(COALESCE({col},'')) LIKE ?")
            params.append(f"%{kw}%")
        for kw in UNICODE_KEYWORDS:
            parts.append(f"COALESCE({col},'') LIKE ?")
            params.append(f"%{kw}%")
    if not parts:
        return "1=0", []
    return "(" + " OR ".join(parts) + ")", params


def build_recent_sql(table: str, cutoff_ts: str) -> Tuple[str, List[str]]:
    cols_by_table = {
        "customers": ["created_at", "updated_at"],
        "estimates": ["created_at", "updated_at", "confirmed_at"],
        "contracts": ["created_at", "updated_at", "signed_at", "signed_date"],
        "projects": ["created_at", "updated_at", "start_date", "end_date"],
        "change_orders": ["created_at", "updated_at", "approved_at", "confirmed_at"],
        "files": ["created_at"],
        "customer_followups": ["created_at", "updated_at", "next_followup_at"],
        "notifications": ["created_at", "read_at"],
    }
    cols = cols_by_table.get(table, [])
    if not cols:
        return "1=1", []
    exprs = [f"(COALESCE({c},'') <> '' AND {c} >= ?)" for c in cols]
    return "(" + " OR ".join(exprs) + ")", [cutoff_ts] * len(cols)


def fetch_id_set(cur: sqlite3.Cursor, sql: str, params: Sequence[object]) -> Set[int]:
    cur.execute(sql, tuple(params))
    return {int(r[0]) for r in cur.fetchall() if r and r[0] is not None}


def fetch_fk_ids(cur: sqlite3.Cursor, table: str, col: str, ids: Set[int]) -> Set[int]:
    if not ids or not table_exists(cur, table):
        return set()
    out: Set[int] = set()
    values = sorted(ids)
    for part in chunked(values):
        placeholders = ",".join(["?"] * len(part))
        sql = f"SELECT DISTINCT {col} FROM {table} WHERE {col} IN ({placeholders})"
        cur.execute(sql, tuple(part))
        out.update({int(r[0]) for r in cur.fetchall() if r and r[0] is not None})
    return out


def fetch_related_ids(cur: sqlite3.Cursor, table: str, id_col: str, ref_col: str, ref_ids: Set[int]) -> Set[int]:
    if not ref_ids or not table_exists(cur, table):
        return set()
    out: Set[int] = set()
    values = sorted(ref_ids)
    for part in chunked(values):
        placeholders = ",".join(["?"] * len(part))
        sql = f"SELECT DISTINCT {id_col} FROM {table} WHERE {ref_col} IN ({placeholders})"
        cur.execute(sql, tuple(part))
        out.update({int(r[0]) for r in cur.fetchall() if r and r[0] is not None})
    return out


def add_all(target: Set[int], incoming: Set[int]) -> bool:
    before = len(target)
    target.update(incoming)
    return len(target) != before


def collect_seed_ids(
    cur: sqlite3.Cursor,
    selected_roots: Set[str],
    cutoff_ts: str,
) -> Dict[str, Set[int]]:
    seeds: Dict[str, Set[int]] = {k: set() for k in VALID_ROOT_TABLES}

    if "customers" in selected_roots and table_exists(cur, "customers"):
        txt_sql, txt_params = build_text_match_sql(
            ["name", "notes", "address", "primary_address", "source", "source_note"]
        )
        recent_sql, recent_params = build_recent_sql("customers", cutoff_ts)
        phone_sql = (
            "REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(phone,''),'-',''),' ',''),'+',''),'(', '') "
            "IN (?,?,?)"
        )
        email_sql = "(" + " OR ".join(["LOWER(COALESCE(email,'')) LIKE ?"] * len(EMAIL_KEYWORDS)) + ")"
        sql = (
            f"SELECT id FROM customers WHERE {recent_sql} AND "
            f"(({txt_sql}) OR ({phone_sql}) OR ({email_sql}))"
        )
        params: List[object] = []
        params.extend(recent_params)
        params.extend(txt_params)
        params.extend(sorted(PHONE_BLOCKLIST))
        params.extend([f"%{k}%" for k in EMAIL_KEYWORDS])
        seeds["customers"] = fetch_id_set(cur, sql, params)

    if "estimates" in selected_roots and table_exists(cur, "estimates"):
        txt_sql, txt_params = build_text_match_sql(["title", "address"])
        recent_sql, recent_params = build_recent_sql("estimates", cutoff_ts)
        sql = f"SELECT id FROM estimates WHERE {recent_sql} AND ({txt_sql})"
        seeds["estimates"] = fetch_id_set(cur, sql, [*recent_params, *txt_params])

    if "contracts" in selected_roots and table_exists(cur, "contracts"):
        txt_sql, txt_params = build_text_match_sql(["title", "contract_no", "address", "sign_note"])
        recent_sql, recent_params = build_recent_sql("contracts", cutoff_ts)
        sql = f"SELECT id FROM contracts WHERE {recent_sql} AND ({txt_sql})"
        seeds["contracts"] = fetch_id_set(cur, sql, [*recent_params, *txt_params])

    if "projects" in selected_roots and table_exists(cur, "projects"):
        txt_sql, txt_params = build_text_match_sql(["name", "address", "notes", "manager"])
        recent_sql, recent_params = build_recent_sql("projects", cutoff_ts)
        sql = f"SELECT id FROM projects WHERE {recent_sql} AND ({txt_sql})"
        seeds["projects"] = fetch_id_set(cur, sql, [*recent_params, *txt_params])

    if "change_orders" in selected_roots and table_exists(cur, "change_orders"):
        txt_sql, txt_params = build_text_match_sql(["title", "description", "reason", "notes", "order_no"])
        recent_sql, recent_params = build_recent_sql("change_orders", cutoff_ts)
        sql = f"SELECT id FROM change_orders WHERE {recent_sql} AND ({txt_sql})"
        seeds["change_orders"] = fetch_id_set(cur, sql, [*recent_params, *txt_params])

    return seeds


def collect_cleanup_sets(
    cur: sqlite3.Cursor,
    selected_roots: Set[str],
    cutoff_ts: str,
) -> Dict[str, Set[int]]:
    seeds = collect_seed_ids(cur, selected_roots, cutoff_ts)

    customer_ids = set(seeds["customers"])
    estimate_ids = set(seeds["estimates"])
    contract_ids = set(seeds["contracts"])
    project_ids = set(seeds["projects"])
    change_order_ids = set(seeds["change_orders"])

    allow_customer_backfill = "customers" in selected_roots

    changed = True
    while changed:
        changed = False

        changed |= add_all(estimate_ids, fetch_related_ids(cur, "estimates", "id", "customer_id", customer_ids))
        changed |= add_all(contract_ids, fetch_related_ids(cur, "contracts", "id", "customer_id", customer_ids))
        changed |= add_all(project_ids, fetch_related_ids(cur, "projects", "id", "customer_id", customer_ids))
        changed |= add_all(change_order_ids, fetch_related_ids(cur, "change_orders", "id", "customer_id", customer_ids))

        changed |= add_all(contract_ids, fetch_related_ids(cur, "contracts", "id", "estimate_id", estimate_ids))
        changed |= add_all(project_ids, fetch_related_ids(cur, "projects", "id", "estimate_id", estimate_ids))
        if allow_customer_backfill:
            changed |= add_all(customer_ids, fetch_fk_ids(cur, "estimates", "customer_id", estimate_ids))

        changed |= add_all(project_ids, fetch_related_ids(cur, "projects", "id", "contract_id", contract_ids))
        if allow_customer_backfill:
            changed |= add_all(customer_ids, fetch_fk_ids(cur, "contracts", "customer_id", contract_ids))
        changed |= add_all(estimate_ids, fetch_fk_ids(cur, "contracts", "estimate_id", contract_ids))
        changed |= add_all(change_order_ids, fetch_related_ids(cur, "change_orders", "id", "contract_id", contract_ids))

        changed |= add_all(contract_ids, fetch_fk_ids(cur, "projects", "contract_id", project_ids))
        changed |= add_all(estimate_ids, fetch_fk_ids(cur, "projects", "estimate_id", project_ids))
        if allow_customer_backfill:
            changed |= add_all(customer_ids, fetch_fk_ids(cur, "projects", "customer_id", project_ids))
        changed |= add_all(change_order_ids, fetch_related_ids(cur, "change_orders", "id", "project_id", project_ids))

        changed |= add_all(project_ids, fetch_fk_ids(cur, "change_orders", "project_id", change_order_ids))
        changed |= add_all(contract_ids, fetch_fk_ids(cur, "change_orders", "contract_id", change_order_ids))
        if allow_customer_backfill:
            changed |= add_all(customer_ids, fetch_fk_ids(cur, "change_orders", "customer_id", change_order_ids))

    milestone_ids = fetch_related_ids(cur, "contract_payment_milestones", "id", "contract_id", contract_ids)
    stage_ids = fetch_related_ids(cur, "project_stages", "id", "project_id", project_ids)

    followup_ids = set()
    followup_ids |= fetch_related_ids(cur, "customer_followups", "id", "customer_id", customer_ids)
    followup_ids |= fetch_related_ids(cur, "customer_followups", "id", "estimate_id", estimate_ids)
    if table_exists(cur, "customer_followups"):
        txt_sql, txt_params = build_text_match_sql(["content", "result"])
        recent_sql, recent_params = build_recent_sql("customer_followups", cutoff_ts)
        sql = f"SELECT id FROM customer_followups WHERE {recent_sql} AND ({txt_sql})"
        followup_ids |= fetch_id_set(cur, sql, [*recent_params, *txt_params])

    file_ids = set()
    file_by_entity = [
        ("customer", customer_ids),
        ("estimate", estimate_ids),
        ("contract", contract_ids),
        ("project", project_ids),
    ]
    if table_exists(cur, "files"):
        for entity_type, ids in file_by_entity:
            if not ids:
                continue
            for part in chunked(sorted(ids)):
                ph = ",".join(["?"] * len(part))
                sql = f"SELECT id FROM files WHERE entity_type=? AND entity_id IN ({ph})"
                params: List[object] = [entity_type, *part]
                file_ids |= fetch_id_set(cur, sql, params)
        txt_sql, txt_params = build_text_match_sql(["filename", "original_name", "file_path"])
        recent_sql, recent_params = build_recent_sql("files", cutoff_ts)
        file_ids |= fetch_id_set(cur, f"SELECT id FROM files WHERE {recent_sql} AND ({txt_sql})", [*recent_params, *txt_params])

    notification_ids = set()
    if table_exists(cur, "notifications"):
        clauses: List[str] = []
        params: List[object] = []
        mapping = [
            ("customer", customer_ids),
            ("estimate", estimate_ids),
            ("contract", contract_ids),
            ("project", project_ids),
            ("change_order", change_order_ids),
            ("payment", milestone_ids),
            ("followup", followup_ids),
        ]
        for related_type, ids in mapping:
            if not ids:
                continue
            for part in chunked(sorted(ids)):
                ph = ",".join(["?"] * len(part))
                clauses.append(f"(related_entity_type=? AND related_entity_id IN ({ph}))")
                params.extend([related_type, *part])
        txt_sql, txt_params = build_text_match_sql(["title", "content", "action_url"])
        recent_sql, recent_params = build_recent_sql("notifications", cutoff_ts)
        if clauses:
            sql = f"SELECT id FROM notifications WHERE ({' OR '.join(clauses)}) OR ({recent_sql} AND ({txt_sql}))"
            params.extend(recent_params)
            params.extend(txt_params)
            notification_ids = fetch_id_set(cur, sql, params)
        else:
            sql = f"SELECT id FROM notifications WHERE {recent_sql} AND ({txt_sql})"
            notification_ids = fetch_id_set(cur, sql, [*recent_params, *txt_params])

    extra_table_ids: Dict[str, Set[int]] = {t: set() for t in EXTRA_DELETE_ORDER}
    extra_table_ids["project_tasks"] = fetch_related_ids(cur, "project_tasks", "id", "project_id", project_ids)
    extra_table_ids["project_issues"] = fetch_related_ids(cur, "project_issues", "id", "project_id", project_ids)
    extra_table_ids["project_costs"] = fetch_related_ids(cur, "project_costs", "id", "project_id", project_ids)
    extra_table_ids["site_logs"] = fetch_related_ids(cur, "site_logs", "id", "project_id", project_ids)
    extra_table_ids["designer_commissions"] = fetch_related_ids(cur, "designer_commissions", "id", "project_id", project_ids)
    extra_table_ids["ap_payables"] = fetch_related_ids(cur, "ap_payables", "id", "project_id", project_ids)
    extra_table_ids["documents"] |= fetch_related_ids(cur, "documents", "id", "project_id", project_ids)
    extra_table_ids["documents"] |= fetch_related_ids(cur, "documents", "id", "customer_id", customer_ids)
    extra_table_ids["quotes"] = fetch_related_ids(cur, "quotes", "id", "project_id", project_ids)
    extra_table_ids["leads"] = fetch_related_ids(cur, "leads", "id", "customer_id", customer_ids)
    extra_table_ids["project_payments"] |= fetch_related_ids(cur, "project_payments", "id", "project_id", project_ids)
    extra_table_ids["project_payments"] |= fetch_related_ids(cur, "project_payments", "id", "contract_id", contract_ids)

    plan: Dict[str, Set[int]] = {
        "notifications": notification_ids,
        "customer_followups": followup_ids,
        "files": file_ids,
        "change_orders": change_order_ids,
        "contract_payment_milestones": milestone_ids,
        "project_stages": stage_ids,
        "projects": project_ids,
        "contracts": contract_ids,
        "estimates": estimate_ids,
        "customers": customer_ids,
    }
    plan.update(extra_table_ids)
    return plan


def summarize_plan(plan: Dict[str, Set[int]]) -> OrderedDict:
    summary: OrderedDict = OrderedDict()
    for t in REQUIRED_DELETE_ORDER:
        summary[t] = len(plan.get(t, set()))
    for t in EXTRA_DELETE_ORDER:
        count = len(plan.get(t, set()))
        if count:
            summary[t] = count
    summary["total"] = sum(v for k, v in summary.items() if k != "total")
    return summary


def print_summary(summary: OrderedDict, dry_run: bool) -> None:
    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"\n[{mode}] cleanup plan")
    for table, count in summary.items():
        if table == "total":
            continue
        print(f"  - {table}: {count}")
    print(f"  - total: {summary['total']}")


def require_double_confirmation(total: int) -> None:
    if not sys.stdin.isatty():
        raise RuntimeError("Interactive terminal required for --apply double confirmation")

    c1 = input("First confirmation: type APPLY to continue: ").strip()
    if c1 != "APPLY":
        raise RuntimeError("First confirmation failed")

    expected = f"DELETE {total}"
    c2 = input(f"Second confirmation: type '{expected}' to execute deletion: ").strip()
    if c2 != expected:
        raise RuntimeError("Second confirmation failed")


def run_backup(logger: logging.Logger) -> None:
    if not BACKUP_SCRIPT.exists():
        raise RuntimeError(f"backup script not found: {BACKUP_SCRIPT}")
    logger.info("Running backup script: bash %s", BACKUP_SCRIPT)
    subprocess.run(["bash", str(BACKUP_SCRIPT)], cwd=str(ROOT_DIR), check=True)


def delete_ids(cur: sqlite3.Cursor, table: str, ids: Set[int]) -> int:
    if not ids:
        return 0
    deleted = 0
    values = sorted(ids)
    for part in chunked(values):
        ph = ",".join(["?"] * len(part))
        sql = f"DELETE FROM {table} WHERE id IN ({ph})"
        cur.execute(sql, tuple(part))
        deleted += int(cur.rowcount or 0)
    return deleted


def safe_resolve_upload_path(rel_path: str) -> Optional[Path]:
    if not rel_path:
        return None
    rel = rel_path.strip().lstrip("/").replace("\\", "/")
    if not rel:
        return None
    abs_path = (UPLOAD_DIR / rel).resolve()
    try:
        abs_path.relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        return None
    return abs_path


def delete_file_records(cur: sqlite3.Cursor, file_ids: Set[int], logger: logging.Logger) -> Tuple[int, int, int]:
    if not file_ids or not table_exists(cur, "files"):
        return 0, 0, 0
    disk_deleted = 0
    disk_missing = 0
    db_deleted = 0
    values = sorted(file_ids)
    for part in chunked(values):
        ph = ",".join(["?"] * len(part))
        cur.execute(f"SELECT id,file_path FROM files WHERE id IN ({ph})", tuple(part))
        rows = cur.fetchall()
        for row in rows:
            file_path = safe_resolve_upload_path(row["file_path"])
            if file_path and file_path.exists() and file_path.is_file():
                try:
                    file_path.unlink()
                    disk_deleted += 1
                except OSError:
                    logger.exception("Failed to remove file: %s", file_path)
            else:
                disk_missing += 1
        cur.execute(f"DELETE FROM files WHERE id IN ({ph})", tuple(part))
        db_deleted += int(cur.rowcount or 0)
    return db_deleted, disk_deleted, disk_missing


def parse_tables_arg(value: Optional[str]) -> Set[str]:
    if not value:
        return set(VALID_ROOT_TABLES)
    items = {x.strip() for x in value.split(",") if x.strip()}
    invalid = sorted(items - VALID_ROOT_TABLES)
    if invalid:
        raise ValueError(f"Invalid --tables value: {', '.join(invalid)}")
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Cleanup test/demo data from CRM database")
    parser.add_argument("--apply", action="store_true", help="Apply deletion (default is dry-run)")
    parser.add_argument("--recent-hours", type=int, default=24, help="Only seed-match records created/updated in recent N hours (default: 24)")
    parser.add_argument("--tables", type=str, default="", help="Seed tables to scan, e.g. customers,estimates")
    args = parser.parse_args()

    logger = setup_logger()
    dry_run = not args.apply

    if args.recent_hours <= 0:
        print("recent-hours must be > 0", file=sys.stderr)
        return 2

    try:
        selected_roots = parse_tables_arg(args.tables)
    except ValueError as err:
        print(str(err), file=sys.stderr)
        return 2

    if not DB_PATH.exists():
        print(f"DB file not found: {DB_PATH}", file=sys.stderr)
        return 2

    cutoff = datetime.now() - timedelta(hours=int(args.recent_hours))
    cutoff_ts = cutoff.strftime("%Y-%m-%dT%H:%M:%S")

    logger.info(
        "cleanup start | mode=%s | db=%s | uploads=%s | recent_hours=%s | tables=%s",
        "dry-run" if dry_run else "apply",
        DB_PATH,
        UPLOAD_DIR,
        args.recent_hours,
        ",".join(sorted(selected_roots)),
    )

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    try:
        plan = collect_cleanup_sets(cur, selected_roots, cutoff_ts)
        summary = summarize_plan(plan)
        print_summary(summary, dry_run=dry_run)
        logger.info("plan summary: %s", dict(summary))

        if dry_run:
            logger.info("dry-run completed, no deletion executed")
            conn.close()
            return 0

        total = int(summary.get("total", 0))
        if total == 0:
            logger.info("no matching test data found, nothing to delete")
            conn.close()
            return 0

        require_double_confirmation(total)
        run_backup(logger)

        conn.execute("BEGIN")

        deleted_counts: OrderedDict = OrderedDict()
        deleted_counts["notifications"] = delete_ids(cur, "notifications", plan.get("notifications", set()))
        deleted_counts["customer_followups"] = delete_ids(cur, "customer_followups", plan.get("customer_followups", set()))

        files_deleted_db, files_deleted_disk, files_missing_disk = delete_file_records(
            cur, plan.get("files", set()), logger
        )
        deleted_counts["files"] = files_deleted_db

        deleted_counts["change_orders"] = delete_ids(cur, "change_orders", plan.get("change_orders", set()))
        deleted_counts["contract_payment_milestones"] = delete_ids(
            cur, "contract_payment_milestones", plan.get("contract_payment_milestones", set())
        )
        deleted_counts["project_stages"] = delete_ids(cur, "project_stages", plan.get("project_stages", set()))

        for t in EXTRA_DELETE_ORDER:
            if not table_exists(cur, t):
                continue
            deleted_counts[t] = delete_ids(cur, t, plan.get(t, set()))

        deleted_counts["projects"] = delete_ids(cur, "projects", plan.get("projects", set()))
        deleted_counts["contracts"] = delete_ids(cur, "contracts", plan.get("contracts", set()))
        deleted_counts["estimates"] = delete_ids(cur, "estimates", plan.get("estimates", set()))
        deleted_counts["customers"] = delete_ids(cur, "customers", plan.get("customers", set()))

        conn.commit()

        print("\n[APPLY] deletion result")
        for table, count in deleted_counts.items():
            print(f"  - {table}: {count}")
        print(f"  - files_on_disk_deleted: {files_deleted_disk}")
        print(f"  - files_on_disk_missing: {files_missing_disk}")
        print(f"  - total_deleted_rows: {sum(deleted_counts.values())}")

        logger.info("deletion result: %s", dict(deleted_counts))
        logger.info(
            "disk files deleted=%s missing=%s total_rows=%s",
            files_deleted_disk,
            files_missing_disk,
            sum(deleted_counts.values()),
        )
        return 0
    except KeyboardInterrupt:
        logger.warning("interrupted by user")
        conn.rollback()
        return 130
    except Exception:
        logger.exception("cleanup failed")
        conn.rollback()
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
