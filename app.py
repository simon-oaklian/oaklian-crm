#!/usr/bin/env python3
import json
import hashlib
import logging
import mimetypes
import os
import re
import secrets
import sqlite3
import sys
from datetime import datetime, timedelta
from html import escape as html_escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
import estimates_v2_module as ev2_routes

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
ASSETS_DIR = BASE_DIR / "assets"
ARCHIVED_DOCUMENTS_DIR = BASE_DIR / "data" / "documents"


def _env_str(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    raw = str(value).strip()
    return raw if raw else default


def _env_path(name, default_relative):
    raw = _env_str(name, default_relative)
    path_obj = Path(raw).expanduser()
    if not path_obj.is_absolute():
        path_obj = (BASE_DIR / path_obj).resolve()
    return path_obj


APP_ENV = _env_str("APP_ENV", "development").lower()
DEFAULT_HOST = "0.0.0.0" if APP_ENV == "production" else "0.0.0.0"
HOST = _env_str("HOST", DEFAULT_HOST)
try:
    PORT = int(_env_str("PORT", "8000"))
except ValueError:
    PORT = 8000

DB_PATH = _env_path("CRM_DB_PATH", "./crm.db")
UPLOADS_DIR = _env_path("CRM_UPLOAD_DIR", "./uploads")
LOG_DIR = _env_path("CRM_LOG_DIR", "./logs")
SESSION_SECRET = _env_str("CRM_SESSION_SECRET", "CHANGE_ME_IN_PRODUCTION")
WEBHOOK_KEY_ENV = _env_str("CRM_WEBHOOK_KEY", "")
DEFAULT_LANGUAGE = _env_str("CRM_DEFAULT_LANGUAGE", "zh").lower()
if DEFAULT_LANGUAGE not in {"zh", "en", "es"}:
    DEFAULT_LANGUAGE = "zh"
BASE_URL = _env_str("CRM_BASE_URL", f"http://0.0.0.0:{PORT}")

APP_LOG = LOG_DIR / "app.log"
ERROR_LOG = LOG_DIR / "error.log"
APP_LOGGER = logging.getLogger("crm.app")
ERROR_LOGGER = logging.getLogger("crm.error")


def ensure_runtime_dirs():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for entity_type in FILE_ENTITY_TABLE.keys():
        (UPLOADS_DIR / entity_type).mkdir(parents=True, exist_ok=True)


def setup_logging():
    ensure_runtime_dirs()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(APP_LOG, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    error_handler = logging.FileHandler(ERROR_LOG, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    APP_LOGGER.setLevel(logging.INFO)
    ERROR_LOGGER.setLevel(logging.ERROR)

ALL_MODULES = [
    "dashboard",
    "notifications",
    "customers",
    "estimates",
    "contracts",
    "projects",
    "designer_applications",
    "designers",
    "designer_assignments",
    "stage_templates",
    "change_orders",
    "documents",
    "document_templates",
    "system_settings",
    "finance",
    "settings",
]
DESIGNER_ALLOWED_MODULES = ["dashboard", "notifications", "projects", "designer_assignments"]
DESIGNER_PERMISSION_MODULES = ["dashboard", "notifications", "projects", "designer_assignments"]
DESIGNER_ASSIGNMENT_SOURCE_TYPES = {"lead", "project"}
DESIGNER_ASSIGNMENT_TYPE_SET = {"design_consult", "full_design", "design_support"}
DESIGNER_ASSIGNMENT_STATUS_SET = {"new", "invited", "accepted", "declined", "in_progress", "completed", "cancelled"}

DEFAULT_PROJECT_STAGES = ["进场", "拆除", "水电改造", "柜体安装", "台面与五金", "验收"]
FILE_ENTITY_TABLE = {
    "customer": "customers",
    "estimate": "estimates",
    "contract": "contracts",
    "project": "projects",
    "bill": "bills",
    "payment": "payments",
}
FILE_ENTITY_MODULE = {
    "customer": "customers",
    "estimate": "estimates",
    "contract": "contracts",
    "project": "projects",
    "bill": "finance",
    "payment": "finance",
}
FILE_CATEGORY_SET = {"photo", "contract", "estimate", "invoice", "change_order", "completion", "other"}
ALLOWED_UPLOAD_EXTS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_UPLOAD_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_BRAND_LOGO_EXTS = {".jpg", ".jpeg", ".png"}
MAX_BRAND_LOGO_SIZE = 5 * 1024 * 1024

RESOURCE_MODULE = {
    "customers": "customers",
    "followups": "customers",
    "estimates": "estimates",
    "contracts": "contracts",
    "projects": "projects",
    "designer_applications": "designer_applications",
    "designers": "designers",
    "designer_assignments": "designer_assignments",
    "designer_permissions": "designers",
    "project_tasks": "projects",
    "site_logs": "projects",
    "project_issues": "projects",
    "project_payments": "finance",
    "project_costs": "finance",
    "ap_payables": "finance",
    "vendors": "finance",
    "bills": "finance",
    "payments": "finance",
    "change_orders": "change_orders",
    "documents": "documents",
    "estimate_templates": "estimates",
    "project_stage_templates": "stage_templates",
    "project_stage_template_items": "stage_templates",
    "project_stages": "projects",
    "customer_followups": "customers",
    "contract_payment_milestones": "contracts",
    "designer_commissions": "projects",
    "document_templates": "settings",
}

TABLE_FIELDS = {
    "customers": [
        "name",
        "phone",
        "email",
        "source",
        "source_channel",
        "source_note",
        "demand_type",
        "inquiry_type",
        "preferred_contact_method",
        "budget_range",
        "status",
        "primary_address",
        "other_addresses",
        "notes",
    ],
    "followups": ["customer_id", "followup_date", "content", "next_action", "owner"],
    "customer_followups": [
        "customer_id",
        "estimate_id",
        "user_id",
        "followup_type",
        "content",
        "result",
        "next_followup_at",
        "completed",
    ],
    "estimates": [
        "customer_id",
        "lead_id",
        "project_id",
        "contract_id",
        "title",
        "address",
        "version",
        "status",
        "confirm_status",
        "confirmed_at",
        "confirmed_by",
        "confirm_note",
        "valid_until",
        "subtotal",
        "markup_rate",
        "manual_adjustment",
        "total_amount",
        "line_items_json",
    ],
    "contracts": [
        "customer_id",
        "project_id",
        "estimate_id",
        "title",
        "address",
        "contract_no",
        "total_amount",
        "payment_plan_json",
        "signed_status",
        "signed_date",
        "sign_status",
        "signed_at",
        "signed_by",
        "sign_note",
        "attachment_url",
    ],
    "projects": [
        "customer_id",
        "contract_id",
        "estimate_id",
        "stage_template_id",
        "project_type",
        "name",
        "address",
        "status",
        "progress_pct",
        "start_date",
        "estimated_finish_date",
        "actual_finish_date",
        "manager",
        "notes",
        "designer_id",
        "designer_name",
        "designer_commission_type",
        "designer_commission_value",
        "designer_commission_base",
    ],
    "designer_applications": [
        "name",
        "phone",
        "email",
        "company_name",
        "service_area",
        "specialty",
        "years_experience",
        "portfolio_url",
        "source_channel",
        "message",
        "status",
        "contacted_at",
        "reviewed_at",
        "reviewed_by",
        "review_note",
        "designer_id",
        "user_id",
    ],
    "designers": [
        "application_id",
        "user_id",
        "name",
        "phone",
        "email",
        "company_name",
        "service_area",
        "specialty",
        "years_experience",
        "portfolio_url",
        "status",
        "notes",
    ],
    "designer_assignments": [
        "designer_id",
        "source_type",
        "source_id",
        "assignment_type",
        "status",
        "message",
        "assigned_by",
        "assigned_at",
        "responded_at",
        "notes",
    ],
    "designer_permissions": [
        "designer_id",
        "module_key",
        "enabled",
        "updated_by",
    ],
    "project_tasks": ["project_id", "phase", "title", "owner", "start_date", "due_date", "status", "notes"],
    "site_logs": ["project_id", "log_date", "work_summary", "crew_info", "materials_info", "photos_json", "issue_note", "template_used"],
    "project_issues": ["project_id", "title", "description", "severity", "owner", "due_date", "status", "before_photos_json", "after_photos_json"],
    "project_payments": ["project_id", "contract_id", "node_name", "due_date", "amount", "status", "received_date", "invoice_no", "notes"],
    "project_costs": ["project_id", "cost_type", "vendor", "cost_date", "amount", "notes"],
    "ap_payables": ["project_id", "vendor", "category", "bill_date", "due_date", "amount", "paid_amount", "status", "payment_date", "reference_no", "notes"],
    "vendors": ["name", "type", "tax_id", "1099_required", "w9_received"],
    "bills": ["project_id", "vendor_id", "category", "bill_no", "bill_date", "due_date", "amount", "paid_amount", "status", "note"],
    "payments": ["project_id", "vendor_id", "bill_id", "amount", "date", "method", "category", "note"],
    "change_orders": [
        "project_id",
        "contract_id",
        "customer_id",
        "order_no",
        "title",
        "description",
        "amount_delta",
        "impact_payment_plan",
        "affect_designer_commission",
        "status",
        "approved_at",
        "confirmed_at",
        "confirmed_by",
        "confirm_note",
        "created_by",
        "reason",
        "items_json",
        "days_delta",
        "signed_status",
        "signed_date",
        "notes",
    ],
    "documents": ["customer_id", "project_id", "doc_type", "file_name", "tags", "url", "visibility"],
    "estimate_templates": ["name", "package_type", "version", "default_markup_rate", "line_items_json", "notes"],
    "project_stage_templates": ["name", "project_type", "is_default", "is_active", "stages_json", "notes"],
    "project_stage_template_items": ["template_id", "step_name", "step_order", "is_active"],
    "project_stages": ["project_id", "stage_name", "stage_order", "status", "started_at", "completed_at"],
    "contract_payment_milestones": [
        "contract_id",
        "name",
        "node_type",
        "trigger_type",
        "trigger_stage",
        "trigger_progress",
        "amount_type",
        "amount_value",
        "triggered",
        "triggered_at",
        "reminded",
        "reminded_at",
        "paid",
        "paid_at",
        "note",
    ],
    "designer_commissions": [
        "project_id",
        "designer_id",
        "base_contract_amount",
        "change_order_amount",
        "commission_type",
        "commission_value",
        "commission_base",
        "commission_amount",
        "status",
        "note",
    ],
    "document_templates": [
        "template_type",
        "project_type",
        "name",
        "is_default",
        "title_text",
        "intro_text",
        "note_text",
        "terms_text",
        "footer_text",
    ],
}

REQUIRED_FIELDS = {
    "customers": ["name"],
    "followups": ["customer_id", "followup_date", "content"],
    "customer_followups": ["customer_id", "followup_type", "content"],
    "estimates": ["title"],
    "contracts": ["contract_no", "total_amount"],
    "projects": ["name", "status"],
    "designer_applications": ["name"],
    "designers": ["name"],
    "designer_assignments": ["designer_id", "source_type", "source_id", "assignment_type"],
    "project_tasks": ["project_id", "title", "status"],
    "site_logs": ["project_id", "log_date", "work_summary"],
    "project_issues": ["project_id", "title", "status"],
    "project_payments": ["project_id", "node_name", "due_date", "amount", "status"],
    "project_costs": ["project_id", "cost_type", "cost_date", "amount"],
    "ap_payables": ["vendor", "due_date", "amount", "status"],
    "vendors": ["name"],
    "bills": ["vendor_id", "amount"],
    "payments": ["vendor_id", "amount", "date"],
    "change_orders": ["project_id", "title", "amount_delta"],
    "documents": ["doc_type", "file_name"],
    "estimate_templates": ["name", "line_items_json"],
    "project_stage_templates": ["name", "project_type"],
    "project_stage_template_items": ["template_id", "step_name", "step_order"],
    "project_stages": ["project_id", "stage_name", "stage_order", "status"],
    "contract_payment_milestones": ["contract_id", "name", "trigger_type", "amount_type", "amount_value"],
    "designer_commissions": ["project_id", "designer_id"],
    "designer_permissions": ["designer_id", "module_key"],
    "document_templates": ["template_type", "project_type", "name"],
}

TIMESTAMPED_TABLES = set(TABLE_FIELDS.keys())


def now_ts():
    return datetime.now().isoformat(timespec="seconds")


def new_session_token(user_id):
    nonce = secrets.token_urlsafe(24)
    ts = int(datetime.now().timestamp())
    payload = f"{user_id}.{ts}.{nonce}"
    sig = hashlib.sha256(f"{SESSION_SECRET}:{payload}".encode("utf-8")).hexdigest()[:16]
    return f"{payload}.{sig}"


def to_iso_date(dt):
    return dt.strftime("%Y-%m-%d")


def month_start(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


INQUIRY_TYPE_LABEL_ZH = {
    "custom_furniture": "定制家具",
    "bathroom_remodel": "卫生间翻新",
    "kitchen_remodel": "厨房翻新",
    "full_remodel": "全屋翻新",
    "other": "其他",
}

SOURCE_CHANNEL_SET = {"website", "houzz", "phone", "referral", "walk_in", "manual"}
INQUIRY_TYPE_SET = set(INQUIRY_TYPE_LABEL_ZH.keys())
PROJECT_TYPE_SET = {"custom_furniture", "bathroom_remodel", "kitchen_remodel", "full_remodel", "other"}
STAGE_TEMPLATE_PROJECT_TYPE_SET = {"kitchen_remodel", "bathroom_remodel", "adu", "full_home_remodel", "custom"}
DOCUMENT_TEMPLATE_TYPE_SET = {"estimate", "contract", "change_order"}
CONTACT_METHOD_SET = {"phone", "text", "email", "wechat"}
VENDOR_TYPE_SET = {"supplier", "subcontractor", "1099"}
PAYMENT_METHOD_SET = {"check", "ach", "wire", "cash", "card", "other"}
SYSTEM_SETTING_GROUP_SET = {"company", "business", "documents", "notifications", "permissions", "printing"}
SYSTEM_SETTINGS_DEFAULTS = {
    "company_name": ("company", "OAKLIAN Remodeling & Construction"),
    "company_legal_name": ("company", "OAKLIAN Remodeling & Construction LLC"),
    "company_phone": ("company", ""),
    "company_email": ("company", ""),
    "company_website": ("company", ""),
    "company_address": ("company", ""),
    "company_logo_light": ("company", "/assets/images/logo-oaklian-light.png"),
    "company_logo_dark": ("company", "/assets/images/logo-oaklian-dark.png"),
    "default_language": ("company", DEFAULT_LANGUAGE),
    "company_footer_text": ("company", "OAKLIAN Remodeling & Construction"),
    "default_tax_rate": ("business", "0"),
    "default_currency": ("business", "USD"),
    "default_project_manager": ("business", ""),
    "default_designer_commission_type": ("business", "percent"),
    "default_designer_commission_value": ("business", "10"),
    "default_followup_days_after_estimate": ("business", "3"),
    "default_payment_plan_notice": ("business", "付款节点触发后请及时催办并记录沟通结果。"),
    "default_change_order_affect_commission": ("business", "0"),
    "default_change_order_affect_payment_plan": ("business", "0"),
    "default_estimate_template_other": ("documents", ""),
    "default_contract_template_other": ("documents", ""),
    "default_change_order_template_other": ("documents", ""),
    "default_print_language": ("documents", "en"),
    "default_terms_notice": ("documents", "未尽事项请以双方书面补充条款为准。"),
    "default_signature_note": ("documents", "请双方签字后生效。"),
    "notify_followup_due_enabled": ("notifications", "1"),
    "notify_estimate_pending_enabled": ("notifications", "1"),
    "notify_contract_pending_enabled": ("notifications", "1"),
    "notify_payment_reminder_enabled": ("notifications", "1"),
    "notify_designer_commission_enabled": ("notifications", "1"),
    "notify_project_completed_enabled": ("notifications", "1"),
    "notify_change_order_pending_enabled": ("notifications", "1"),
    "print_footer_company_name": ("printing", "OAKLIAN Remodeling & Construction"),
    "print_footer_license_no": ("printing", ""),
    "print_footer_contact": ("printing", ""),
    "print_footer_disclaimer": ("printing", "本文件仅用于项目沟通与签约确认。"),
    "print_show_logo": ("printing", "1"),
    "print_show_signature_hint": ("printing", "1"),
}


def canonical_phone(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) > 10:
        return digits[-10:]
    return digits


def inquiry_type_to_demand_label(value):
    key = normalize_key(value)
    return INQUIRY_TYPE_LABEL_ZH.get(key, "")


def normalize_key(value):
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "新线索": "new_lead",
        "已联系": "contacted",
        "已预约上门": "site_visit_booked",
        "已报价": "quoted",
        "已流失": "lost",
        "new_lead": "new_lead",
        "contacted": "contacted",
        "site_visit_booked": "site_visit_booked",
        "quoted": "quoted",
        "website": "website",
        "官网": "website",
        "web": "website",
        "houzz": "houzz",
        "phone": "phone",
        "电话": "phone",
        "referral": "referral",
        "转介绍": "referral",
        "walk_in": "walk_in",
        "到店": "walk_in",
        "walkin": "walk_in",
        "manual": "manual",
        "手动": "manual",
        "custom_furniture": "custom_furniture",
        "定制家具": "custom_furniture",
        "bathroom": "bathroom_remodel",
        "bathroom_remodel": "bathroom_remodel",
        "卫生间翻新": "bathroom_remodel",
        "卫生间": "bathroom_remodel",
        "kitchen": "kitchen_remodel",
        "kitchen_remodel": "kitchen_remodel",
        "厨房翻新": "kitchen_remodel",
        "厨房": "kitchen_remodel",
        "full_remodel": "full_remodel",
        "remodel": "full_remodel",
        "全屋翻新": "full_remodel",
        "estimate": "estimate",
        "contract": "contract",
        "change_order": "change_order",
        "changeorder": "change_order",
        "报价模板": "estimate",
        "合同模板": "contract",
        "变更单模板": "change_order",
        "other": "other",
        "text": "text",
        "短信": "text",
        "wechat": "wechat",
        "微信": "wechat",
        "email": "email",
        "邮件": "email",
        "visit": "visit",
        "上门": "visit",
        "note": "note",
        "备注": "note",
        "未开始": "pending",
        "待开始": "pending",
        "pending": "pending",
        "进行中": "in_progress",
        "施工中": "in_progress",
        "in_progress": "in_progress",
        "inprogress": "in_progress",
        "已完成": "done",
        "done": "done",
        "completed": "done",
        "草稿": "draft",
        "draft": "draft",
        "已发送": "sent",
        "sent": "sent",
        "已确认": "approved",
        "approved": "approved",
        "已接受": "approved",
        "accepted": "approved",
        "已拒绝": "rejected",
        "rejected": "rejected",
        "signed": "signed",
        "已签约": "signed",
        "签约": "signed",
        "unsigned": "unsigned",
        "未签字": "unsigned",
        "待催办": "pending",
        "已提醒": "reminded",
        "已收款": "paid",
        "未触发": "untriggered",
        "未生成": "ungenerated",
        "待结算": "pending_settlement",
        "已结算": "settled",
    }
    return aliases.get(str(value or "").strip(), aliases.get(raw, raw))


def milestone_state_key(item):
    if int(item.get("paid") or 0) == 1:
        return "paid"
    if int(item.get("reminded") or 0) == 1:
        return "reminded"
    if int(item.get("triggered") or 0) == 1:
        return "pending"
    return "untriggered"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    return dict(row)


def ensure_columns(cur, table_name, column_defs):
    cur.execute(f"PRAGMA table_info({table_name})")
    existing = {row["name"] for row in cur.fetchall()}
    for col_name, col_def in column_defs.items():
        if col_name not in existing:
            cur.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{col_name}" {col_def}')


def init_db():
    ensure_runtime_dirs()
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            linked_designer_id INTEGER,
            language TEXT NOT NULL DEFAULT 'zh',
            modules_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS company_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            company_name TEXT NOT NULL,
            legal_name TEXT,
            tagline TEXT,
            logo_horizontal_url TEXT,
            logo_icon_url TEXT,
            primary_color TEXT,
            accent_color TEXT,
            dark_color TEXT,
            light_bg TEXT,
            website_webhook_key TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            source TEXT,
            source_channel TEXT,
            source_note TEXT,
            demand_type TEXT,
            inquiry_type TEXT,
            preferred_contact_method TEXT,
            budget_range TEXT,
            status TEXT DEFAULT '新线索',
            primary_address TEXT,
            other_addresses TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            followup_date TEXT NOT NULL,
            content TEXT NOT NULL,
            next_action TEXT,
            owner TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS customer_followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            estimate_id INTEGER,
            user_id INTEGER,
            followup_type TEXT NOT NULL DEFAULT 'note',
            content TEXT NOT NULL,
            result TEXT,
            next_followup_at TEXT,
            completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE SET NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role_scope TEXT,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            related_entity_type TEXT,
            related_entity_id INTEGER,
            action_url TEXT,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            read_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read, id DESC);
        CREATE INDEX IF NOT EXISTS idx_notifications_role_read ON notifications(role_scope, is_read, id DESC);
        CREATE INDEX IF NOT EXISTS idx_notifications_type_entity ON notifications(type, related_entity_type, related_entity_id);

        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT NOT NULL UNIQUE,
            setting_value TEXT,
            setting_group TEXT,
            updated_at TEXT NOT NULL,
            updated_by INTEGER
        );
        CREATE INDEX IF NOT EXISTS idx_system_settings_group ON system_settings(setting_group, setting_key);

        CREATE TABLE IF NOT EXISTS estimates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            lead_id INTEGER,
            project_id INTEGER,
            contract_id INTEGER,
            project_type TEXT,
            title TEXT NOT NULL,
            address TEXT,
            version TEXT DEFAULT 'v1',
            status TEXT DEFAULT 'Draft',
            confirm_status TEXT DEFAULT 'draft',
            confirmed_at TEXT,
            confirmed_by INTEGER,
            confirm_note TEXT,
            valid_until TEXT,
            subtotal REAL DEFAULT 0,
            markup_rate REAL DEFAULT 0,
            manual_adjustment REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            line_items_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            project_id INTEGER,
            estimate_id INTEGER,
            project_type TEXT,
            title TEXT,
            address TEXT,
            contract_no TEXT NOT NULL,
            total_amount REAL NOT NULL,
            payment_plan_json TEXT,
            signed_status TEXT DEFAULT 'Unsigned',
            signed_date TEXT,
            sign_status TEXT DEFAULT 'draft',
            signed_at TEXT,
            signed_by INTEGER,
            sign_note TEXT,
            attachment_url TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            contract_id INTEGER,
            estimate_id INTEGER,
            stage_template_id INTEGER,
            project_type TEXT,
            name TEXT NOT NULL,
            address TEXT,
            status TEXT NOT NULL,
            progress_pct INTEGER DEFAULT 0,
            start_date TEXT,
            estimated_finish_date TEXT,
            actual_finish_date TEXT,
            manager TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL,
            FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE SET NULL,
            FOREIGN KEY (stage_template_id) REFERENCES project_stage_templates(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS designer_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            company_name TEXT,
            service_area TEXT,
            specialty TEXT,
            years_experience TEXT,
            portfolio_url TEXT,
            source_channel TEXT NOT NULL DEFAULT 'website',
            message TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            contacted_at TEXT,
            reviewed_at TEXT,
            reviewed_by INTEGER,
            review_note TEXT,
            designer_id INTEGER,
            user_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (designer_id) REFERENCES designers(id) ON DELETE SET NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_designer_applications_status ON designer_applications(status, id DESC);
        CREATE INDEX IF NOT EXISTS idx_designer_applications_email ON designer_applications(email);

        CREATE TABLE IF NOT EXISTS designers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER,
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            company_name TEXT,
            service_area TEXT,
            specialty TEXT,
            years_experience TEXT,
            portfolio_url TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (application_id) REFERENCES designer_applications(id) ON DELETE SET NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_designers_user ON designers(user_id);
        CREATE INDEX IF NOT EXISTS idx_designers_email ON designers(email);

        CREATE TABLE IF NOT EXISTS designer_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            designer_id INTEGER NOT NULL,
            source_type TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            assignment_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            message TEXT,
            assigned_by INTEGER,
            assigned_at TEXT,
            responded_at TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (designer_id) REFERENCES designers(id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_by) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_designer_assignments_designer ON designer_assignments(designer_id, id DESC);
        CREATE INDEX IF NOT EXISTS idx_designer_assignments_source ON designer_assignments(source_type, source_id, id DESC);
        CREATE INDEX IF NOT EXISTS idx_designer_assignments_status ON designer_assignments(status, id DESC);

        CREATE TABLE IF NOT EXISTS designer_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            designer_id INTEGER NOT NULL,
            module_key TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            updated_by INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (designer_id) REFERENCES designers(id) ON DELETE CASCADE,
            FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_designer_permissions_unique ON designer_permissions(designer_id, module_key);

        CREATE TABLE IF NOT EXISTS project_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            phase TEXT,
            title TEXT NOT NULL,
            owner TEXT,
            start_date TEXT,
            due_date TEXT,
            status TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS site_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            work_summary TEXT NOT NULL,
            crew_info TEXT,
            materials_info TEXT,
            photos_json TEXT,
            issue_note TEXT,
            template_used TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS project_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT DEFAULT 'Medium',
            owner TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'Open',
            before_photos_json TEXT,
            after_photos_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS project_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            contract_id INTEGER,
            node_name TEXT NOT NULL,
            due_date TEXT NOT NULL,
            amount REAL NOT NULL,
            received_amount REAL DEFAULT 0,
            status TEXT NOT NULL,
            received_date TEXT,
            payment_method TEXT,
            invoice_no TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS project_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            cost_type TEXT NOT NULL,
            vendor TEXT,
            cost_date TEXT NOT NULL,
            amount REAL NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ap_payables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            vendor TEXT NOT NULL,
            category TEXT,
            bill_date TEXT,
            due_date TEXT NOT NULL,
            amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            status TEXT NOT NULL,
            payment_date TEXT,
            reference_no TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'supplier',
            tax_id TEXT,
            "1099_required" INTEGER NOT NULL DEFAULT 0,
            w9_received INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_vendors_type ON vendors(type, id DESC);
        CREATE UNIQUE INDEX IF NOT EXISTS idx_vendors_name_unique ON vendors(name);

        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            vendor_id INTEGER NOT NULL,
            category TEXT,
            bill_no TEXT,
            bill_date TEXT,
            due_date TEXT,
            amount REAL NOT NULL DEFAULT 0,
            paid_amount REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Open',
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_bills_vendor ON bills(vendor_id, id DESC);
        CREATE INDEX IF NOT EXISTS idx_bills_project ON bills(project_id, id DESC);

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            vendor_id INTEGER NOT NULL,
            bill_id INTEGER,
            amount REAL NOT NULL DEFAULT 0,
            date TEXT NOT NULL,
            method TEXT,
            category TEXT,
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
            FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE CASCADE,
            FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS idx_payments_vendor_date ON payments(vendor_id, date DESC, id DESC);
        CREATE INDEX IF NOT EXISTS idx_payments_project_date ON payments(project_id, date DESC, id DESC);
        CREATE INDEX IF NOT EXISTS idx_payments_bill ON payments(bill_id, id DESC);

        CREATE TABLE IF NOT EXISTS change_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            project_type TEXT,
            reason TEXT NOT NULL,
            items_json TEXT,
            amount_delta REAL NOT NULL,
            days_delta INTEGER DEFAULT 0,
            signed_status TEXT NOT NULL,
            signed_date TEXT,
            confirmed_at TEXT,
            confirmed_by INTEGER,
            confirm_note TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            project_id INTEGER,
            doc_type TEXT NOT NULL,
            file_name TEXT NOT NULL,
            tags TEXT,
            url TEXT,
            visibility TEXT DEFAULT 'Team',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            category TEXT NOT NULL DEFAULT 'other',
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            mime_type TEXT,
            file_size INTEGER NOT NULL DEFAULT 0,
            uploaded_by INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS estimate_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            package_type TEXT,
            version TEXT DEFAULT 'v1',
            default_markup_rate REAL DEFAULT 0,
            line_items_json TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS project_stage_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            project_type TEXT,
            is_default INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            stages_json TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS project_stage_template_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            step_name TEXT NOT NULL,
            step_order INTEGER NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (template_id) REFERENCES project_stage_templates(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS project_stages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            stage_name TEXT NOT NULL,
            stage_order INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            started_at TEXT,
            completed_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS contract_payment_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            node_type TEXT,
            trigger_type TEXT NOT NULL,
            trigger_stage TEXT,
            trigger_progress INTEGER,
            amount_type TEXT NOT NULL DEFAULT 'percent',
            amount_value REAL NOT NULL DEFAULT 0,
            triggered INTEGER NOT NULL DEFAULT 0,
            triggered_at TEXT,
            reminded INTEGER NOT NULL DEFAULT 0,
            reminded_at TEXT,
            paid INTEGER NOT NULL DEFAULT 0,
            paid_at TEXT,
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS designer_commissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            designer_id INTEGER,
            base_contract_amount REAL DEFAULT 0,
            change_order_amount REAL DEFAULT 0,
            commission_type TEXT DEFAULT 'percent',
            commission_value REAL DEFAULT 0,
            commission_base TEXT DEFAULT 'base_contract_only',
            commission_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'ungenerated',
            note TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS document_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_type TEXT NOT NULL,
            project_type TEXT NOT NULL,
            name TEXT NOT NULL,
            is_default INTEGER NOT NULL DEFAULT 0,
            title_text TEXT,
            intro_text TEXT,
            note_text TEXT,
            terms_text TEXT,
            footer_text TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )

    ensure_columns(
        cur,
        "users",
        {
            "linked_designer_id": "INTEGER",
            "language": "TEXT DEFAULT 'zh'",
            "modules_json": "TEXT DEFAULT '[]'",
            "updated_at": "TEXT",
        },
    )
    ensure_columns(cur, "estimate_templates", {"package_type": "TEXT", "version": "TEXT", "default_markup_rate": "REAL DEFAULT 0", "notes": "TEXT", "updated_at": "TEXT"})
    ensure_columns(
        cur,
        "project_stage_templates",
        {
            "project_type": "TEXT",
            "is_default": "INTEGER NOT NULL DEFAULT 0",
            "is_active": "INTEGER NOT NULL DEFAULT 1",
            "notes": "TEXT",
            "updated_at": "TEXT",
        },
    )
    ensure_columns(cur, "project_stage_template_items", {"is_active": "INTEGER NOT NULL DEFAULT 1", "updated_at": "TEXT"})
    ensure_columns(cur, "project_stages", {"started_at": "TEXT", "completed_at": "TEXT", "updated_at": "TEXT"})
    ensure_columns(cur, "company_settings", {"legal_name": "TEXT", "tagline": "TEXT", "logo_horizontal_url": "TEXT", "logo_icon_url": "TEXT", "primary_color": "TEXT", "accent_color": "TEXT", "dark_color": "TEXT", "light_bg": "TEXT", "website_webhook_key": "TEXT"})
    ensure_columns(cur, "files", {"mime_type": "TEXT", "file_size": "INTEGER DEFAULT 0", "uploaded_by": "INTEGER"})
    ensure_columns(
        cur,
        "estimates",
        {
            "lead_id": "INTEGER",
            "contract_id": "INTEGER",
            "project_type": "TEXT",
            "address": "TEXT",
            "confirm_status": "TEXT DEFAULT 'draft'",
            "confirmed_at": "TEXT",
            "confirmed_by": "INTEGER",
            "confirm_note": "TEXT",
            "manual_adjustment": "REAL DEFAULT 0",
            "public_token": "TEXT",
            "sent_at": "TEXT",
            "client_action_at": "TEXT",
            "client_name": "TEXT",
            "client_email": "TEXT",
            "client_phone": "TEXT",
            "client_signature_data": "TEXT",
            "client_ip": "TEXT",
            "client_user_agent": "TEXT",
        },
    )
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_estimates_public_token ON estimates(public_token)")
    ensure_columns(cur, "estimate_payment_milestones", {"custom_stage_name": "TEXT"})
    ensure_columns(
        cur,
        "contracts",
        {
            "title": "TEXT",
            "project_type": "TEXT",
            "address": "TEXT",
            "sign_status": "TEXT DEFAULT 'draft'",
            "signed_at": "TEXT",
            "signed_by": "INTEGER",
            "sign_note": "TEXT",
        },
    )
    ensure_columns(cur, "projects", {"stage_template_id": "INTEGER", "project_type": "TEXT"})
    ensure_columns(cur, "project_payments", {"received_amount": "REAL DEFAULT 0", "payment_method": "TEXT"})
    ensure_columns(cur, "ap_payables", {"project_id": "INTEGER", "category": "TEXT", "bill_date": "TEXT", "paid_amount": "REAL DEFAULT 0", "payment_date": "TEXT", "reference_no": "TEXT", "notes": "TEXT", "updated_at": "TEXT"})
    ensure_columns(cur, "vendors", {"name": "TEXT", "type": "TEXT DEFAULT 'supplier'", "tax_id": "TEXT", "1099_required": "INTEGER DEFAULT 0", "w9_received": "INTEGER DEFAULT 0", "updated_at": "TEXT"})
    ensure_columns(cur, "bills", {"project_id": "INTEGER", "vendor_id": "INTEGER", "category": "TEXT", "bill_no": "TEXT", "bill_date": "TEXT", "due_date": "TEXT", "amount": "REAL DEFAULT 0", "paid_amount": "REAL DEFAULT 0", "status": "TEXT DEFAULT 'Open'", "note": "TEXT", "updated_at": "TEXT"})
    ensure_columns(cur, "payments", {"project_id": "INTEGER", "vendor_id": "INTEGER", "bill_id": "INTEGER", "amount": "REAL DEFAULT 0", "date": "TEXT", "method": "TEXT", "category": "TEXT", "note": "TEXT", "updated_at": "TEXT"})
    ensure_columns(
        cur,
        "customers",
        {
            "email": "TEXT",
            "source_channel": "TEXT",
            "source_note": "TEXT",
            "demand_type": "TEXT",
            "inquiry_type": "TEXT",
            "preferred_contact_method": "TEXT",
            "budget_range": "TEXT",
            "status": "TEXT",
            "primary_address": "TEXT",
            "other_addresses": "TEXT",
            "updated_at": "TEXT",
        },
    )
    ensure_columns(cur, "followups", {"customer_id": "INTEGER", "followup_date": "TEXT", "next_action": "TEXT", "updated_at": "TEXT"})
    ensure_columns(
        cur,
        "customer_followups",
        {
            "estimate_id": "INTEGER",
            "user_id": "INTEGER",
            "followup_type": "TEXT",
            "result": "TEXT",
            "next_followup_at": "TEXT",
            "completed": "INTEGER DEFAULT 0",
            "updated_at": "TEXT",
        },
    )
    ensure_columns(
        cur,
        "notifications",
        {
            "user_id": "INTEGER",
            "role_scope": "TEXT",
            "type": "TEXT",
            "title": "TEXT",
            "content": "TEXT",
            "related_entity_type": "TEXT",
            "related_entity_id": "INTEGER",
            "action_url": "TEXT",
            "is_read": "INTEGER DEFAULT 0",
            "created_at": "TEXT",
            "read_at": "TEXT",
        },
    )
    ensure_columns(
        cur,
        "system_settings",
        {
            "setting_key": "TEXT",
            "setting_value": "TEXT",
            "setting_group": "TEXT",
            "updated_at": "TEXT",
            "updated_by": "INTEGER",
        },
    )
    ensure_columns(
        cur,
        "projects",
        {
            "contract_id": "INTEGER",
            "estimate_id": "INTEGER",
            "progress_pct": "INTEGER",
            "estimated_finish_date": "TEXT",
            "actual_finish_date": "TEXT",
            "updated_at": "TEXT",
            "designer_id": "INTEGER",
            "designer_name": "TEXT",
            "designer_commission_type": "TEXT DEFAULT 'percent'",
            "designer_commission_value": "REAL DEFAULT 0",
            "designer_commission_base": "TEXT DEFAULT 'base_contract_only'",
            "project_type": "TEXT",
        },
    )
    ensure_columns(
        cur,
        "designer_applications",
        {
            "name": "TEXT",
            "phone": "TEXT",
            "email": "TEXT",
            "company_name": "TEXT",
            "service_area": "TEXT",
            "specialty": "TEXT",
            "years_experience": "TEXT",
            "portfolio_url": "TEXT",
            "source_channel": "TEXT DEFAULT 'website'",
            "message": "TEXT",
            "status": "TEXT DEFAULT 'pending'",
            "contacted_at": "TEXT",
            "reviewed_at": "TEXT",
            "reviewed_by": "INTEGER",
            "review_note": "TEXT",
            "designer_id": "INTEGER",
            "user_id": "INTEGER",
            "updated_at": "TEXT",
        },
    )
    ensure_columns(
        cur,
        "designers",
        {
            "application_id": "INTEGER",
            "user_id": "INTEGER",
            "name": "TEXT",
            "phone": "TEXT",
            "email": "TEXT",
            "company_name": "TEXT",
            "service_area": "TEXT",
            "specialty": "TEXT",
            "years_experience": "TEXT",
            "portfolio_url": "TEXT",
            "status": "TEXT DEFAULT 'active'",
            "notes": "TEXT",
            "updated_at": "TEXT",
        },
    )
    ensure_columns(
        cur,
        "designer_permissions",
        {
            "designer_id": "INTEGER",
            "module_key": "TEXT",
            "enabled": "INTEGER DEFAULT 1",
            "updated_by": "INTEGER",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        },
    )
    ensure_columns(
        cur,
        "designer_assignments",
        {
            "designer_id": "INTEGER",
            "source_type": "TEXT",
            "source_id": "INTEGER",
            "assignment_type": "TEXT",
            "status": "TEXT DEFAULT 'new'",
            "message": "TEXT",
            "assigned_by": "INTEGER",
            "assigned_at": "TEXT",
            "responded_at": "TEXT",
            "notes": "TEXT",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        },
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_designer_applications_status ON designer_applications(status, id DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_designer_applications_email ON designer_applications(email)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_designers_user ON designers(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_designers_email ON designers(email)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_designer_assignments_designer ON designer_assignments(designer_id, id DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_designer_assignments_source ON designer_assignments(source_type, source_id, id DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_designer_assignments_status ON designer_assignments(status, id DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_vendors_type ON vendors(type, id DESC)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_vendors_name_unique ON vendors(name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bills_vendor ON bills(vendor_id, id DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_bills_project ON bills(project_id, id DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_vendor_date ON payments(vendor_id, date DESC, id DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_project_date ON payments(project_id, date DESC, id DESC)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_payments_bill ON payments(bill_id, id DESC)")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_designer_permissions_unique ON designer_permissions(designer_id, module_key)")
    ensure_columns(
        cur,
        "change_orders",
        {
            "contract_id": "INTEGER",
            "customer_id": "INTEGER",
            "order_no": "TEXT",
            "title": "TEXT",
            "description": "TEXT",
            "impact_payment_plan": "INTEGER DEFAULT 0",
            "affect_designer_commission": "INTEGER DEFAULT 0",
            "status": "TEXT DEFAULT 'draft'",
            "approved_at": "TEXT",
            "confirmed_at": "TEXT",
            "confirmed_by": "INTEGER",
            "confirm_note": "TEXT",
            "created_by": "INTEGER",
            "project_type": "TEXT",
        },
    )
    ensure_columns(cur, "contract_payment_milestones", {"node_type": "TEXT", "trigger_progress": "INTEGER", "triggered": "INTEGER DEFAULT 0", "triggered_at": "TEXT", "reminded": "INTEGER DEFAULT 0", "reminded_at": "TEXT", "paid": "INTEGER DEFAULT 0", "paid_at": "TEXT", "note": "TEXT", "updated_at": "TEXT"})
    ensure_columns(cur, "designer_commissions", {"designer_id": "INTEGER", "change_order_amount": "REAL DEFAULT 0", "commission_base": "TEXT DEFAULT 'base_contract_only'", "note": "TEXT", "updated_at": "TEXT"})
    ensure_columns(
        cur,
        "document_templates",
        {
            "template_type": "TEXT",
            "project_type": "TEXT",
            "name": "TEXT",
            "is_default": "INTEGER DEFAULT 0",
            "title_text": "TEXT",
            "intro_text": "TEXT",
            "note_text": "TEXT",
            "terms_text": "TEXT",
            "footer_text": "TEXT",
            "updated_at": "TEXT",
        },
    )

    ts = now_ts()
    cur.execute("UPDATE customers SET updated_at=COALESCE(updated_at,created_at,?)", (ts,))
    cur.execute("UPDATE customer_followups SET updated_at=COALESCE(updated_at,created_at,?)", (ts,))
    cur.execute(
        """
        UPDATE customers
        SET status = CASE
            WHEN status='Lead' THEN '新线索'
            WHEN status='In Progress' THEN '已联系'
            WHEN status='Measuring' THEN '已预约上门'
            WHEN status='Quoting' THEN '已报价'
            WHEN status='Signed' THEN '已签约'
            WHEN status='Lost' THEN '已流失'
            ELSE status
        END
        WHERE status IN ('Lead','In Progress','Measuring','Quoting','Signed','Lost')
        """
    )
    cur.execute(
        """
        UPDATE customers
        SET source_channel = CASE
            WHEN LOWER(COALESCE(source,'')) LIKE '%houzz%' THEN 'houzz'
            WHEN LOWER(COALESCE(source,'')) LIKE '%website%' OR LOWER(COALESCE(source,'')) LIKE '%web%' THEN 'website'
            WHEN LOWER(COALESCE(source,'')) LIKE '%referral%' OR source LIKE '%转介绍%' THEN 'referral'
            WHEN LOWER(COALESCE(source,'')) LIKE '%phone%' OR source LIKE '%电话%' THEN 'phone'
            WHEN source LIKE '%到店%' THEN 'walk_in'
            ELSE COALESCE(source_channel, 'manual')
        END
        WHERE source_channel IS NULL OR TRIM(source_channel)=''
        """
    )
    cur.execute(
        """
        UPDATE customers
        SET inquiry_type = CASE
            WHEN demand_type='定制家具' THEN 'custom_furniture'
            WHEN demand_type='卫生间翻新' OR demand_type='Bathroom' THEN 'bathroom_remodel'
            WHEN demand_type='厨房翻新' THEN 'kitchen_remodel'
            WHEN demand_type='全屋翻新' THEN 'full_remodel'
            WHEN inquiry_type IS NULL OR TRIM(inquiry_type)='' THEN 'other'
            ELSE inquiry_type
        END
        """
    )
    cur.execute(
        """
        INSERT INTO customer_followups(customer_id,estimate_id,user_id,followup_type,content,result,next_followup_at,completed,created_at,updated_at)
        SELECT
            f.customer_id,
            NULL,
            NULL,
            'note',
            f.content,
            f.next_action,
            CASE WHEN f.followup_date IS NULL OR TRIM(f.followup_date)='' THEN NULL ELSE f.followup_date || 'T09:00' END,
            0,
            COALESCE(f.created_at, f.followup_date || 'T09:00', ?),
            COALESCE(f.updated_at, f.created_at, f.followup_date || 'T09:00', ?)
        FROM followups f
        JOIN customers c ON c.id=f.customer_id
        WHERE f.customer_id IS NOT NULL
          AND NOT EXISTS (
              SELECT 1
              FROM customer_followups cf
              WHERE cf.customer_id=f.customer_id
                AND COALESCE(cf.content,'')=COALESCE(f.content,'')
                AND COALESCE(cf.next_followup_at,'')=COALESCE(CASE WHEN f.followup_date IS NULL OR TRIM(f.followup_date)='' THEN NULL ELSE f.followup_date || 'T09:00' END,'')
          )
        """,
        (ts, ts),
    )
    cur.execute("UPDATE followups SET updated_at=COALESCE(updated_at,created_at,?)", (ts,))
    cur.execute("UPDATE projects SET updated_at=COALESCE(updated_at,created_at,?)", (ts,))
    cur.execute(
        """
        UPDATE estimates
        SET contract_id = (
            SELECT id FROM contracts c WHERE c.estimate_id = estimates.id ORDER BY c.id ASC LIMIT 1
        )
        WHERE contract_id IS NULL
        """
    )
    cur.execute(
        """
        UPDATE estimates
        SET address = COALESCE(address, (SELECT p.address FROM projects p WHERE p.id=estimates.project_id))
        WHERE address IS NULL OR TRIM(address)=''
        """
    )
    cur.execute(
        """
        UPDATE estimates
        SET address = COALESCE(address, (SELECT c.primary_address FROM customers c WHERE c.id=estimates.customer_id))
        WHERE address IS NULL OR TRIM(address)=''
        """
    )
    cur.execute(
        """
        UPDATE projects
        SET estimate_id = (
            SELECT estimate_id FROM contracts WHERE contracts.id = projects.contract_id
        )
        WHERE estimate_id IS NULL AND contract_id IS NOT NULL
        """
    )
    cur.execute(
        """
        UPDATE projects
        SET estimate_id = (
            SELECT id FROM estimates e WHERE e.project_id = projects.id ORDER BY e.id ASC LIMIT 1
        )
        WHERE estimate_id IS NULL
        """
    )
    cur.execute(
        """
        UPDATE contracts
        SET title = COALESCE(title, (SELECT e.title FROM estimates e WHERE e.id = contracts.estimate_id))
        """
    )
    cur.execute(
        """
        UPDATE contracts
        SET address = COALESCE(address, (SELECT c.primary_address FROM customers c WHERE c.id = contracts.customer_id))
        """
    )
    cur.execute(
        """
        UPDATE projects
        SET project_type = COALESCE(
            NULLIF(project_type, ''),
            (SELECT c.inquiry_type FROM customers c WHERE c.id=projects.customer_id),
            'other'
        )
        WHERE project_type IS NULL OR TRIM(project_type)=''
        """
    )
    cur.execute(
        """
        UPDATE estimates
        SET project_type = COALESCE(
            NULLIF(project_type, ''),
            (SELECT p.project_type FROM projects p WHERE p.id=estimates.project_id),
            (SELECT c.inquiry_type FROM customers c WHERE c.id=estimates.customer_id),
            'other'
        )
        WHERE project_type IS NULL OR TRIM(project_type)=''
        """
    )
    cur.execute(
        """
        UPDATE contracts
        SET project_type = COALESCE(
            NULLIF(project_type, ''),
            (SELECT p.project_type FROM projects p WHERE p.id=contracts.project_id),
            (SELECT e.project_type FROM estimates e WHERE e.id=contracts.estimate_id),
            (SELECT c.inquiry_type FROM customers c WHERE c.id=contracts.customer_id),
            'other'
        )
        WHERE project_type IS NULL OR TRIM(project_type)=''
        """
    )
    cur.execute(
        """
        UPDATE change_orders
        SET project_type = COALESCE(
            NULLIF(project_type, ''),
            (SELECT p.project_type FROM projects p WHERE p.id=change_orders.project_id),
            (SELECT ct.project_type FROM contracts ct WHERE ct.id=change_orders.contract_id),
            (SELECT c.inquiry_type FROM customers c WHERE c.id=change_orders.customer_id),
            'other'
        )
        WHERE project_type IS NULL OR TRIM(project_type)=''
        """
    )
    cur.execute(
        f"""
        UPDATE projects SET project_type='other'
        WHERE project_type IS NULL OR TRIM(project_type)='' OR project_type NOT IN ({','.join(['?']*len(PROJECT_TYPE_SET))})
        """,
        tuple(PROJECT_TYPE_SET),
    )
    cur.execute(
        f"""
        UPDATE estimates SET project_type='other'
        WHERE project_type IS NULL OR TRIM(project_type)='' OR project_type NOT IN ({','.join(['?']*len(PROJECT_TYPE_SET))})
        """,
        tuple(PROJECT_TYPE_SET),
    )
    cur.execute(
        f"""
        UPDATE contracts SET project_type='other'
        WHERE project_type IS NULL OR TRIM(project_type)='' OR project_type NOT IN ({','.join(['?']*len(PROJECT_TYPE_SET))})
        """,
        tuple(PROJECT_TYPE_SET),
    )
    cur.execute(
        f"""
        UPDATE change_orders SET project_type='other'
        WHERE project_type IS NULL OR TRIM(project_type)='' OR project_type NOT IN ({','.join(['?']*len(PROJECT_TYPE_SET))})
        """,
        tuple(PROJECT_TYPE_SET),
    )
    cur.execute(
        """
        UPDATE estimates
        SET confirm_status = CASE
            WHEN confirm_status IS NOT NULL AND TRIM(confirm_status)<>'' THEN LOWER(confirm_status)
            WHEN LOWER(COALESCE(status,''))='sent' OR status='已发送' THEN 'sent'
            WHEN LOWER(COALESCE(status,'')) IN ('confirmed','approved') OR status IN ('已确认','已接受') THEN 'confirmed'
            WHEN LOWER(COALESCE(status,''))='rejected' OR status='已拒绝' THEN 'rejected'
            ELSE 'draft'
        END
        """
    )
    cur.execute(
        """
        UPDATE estimates
        SET confirm_status='draft'
        WHERE confirm_status IS NULL
           OR TRIM(confirm_status)=''
           OR LOWER(confirm_status) NOT IN ('draft','sent','confirmed','rejected')
        """
    )
    cur.execute(
        """
        UPDATE estimates
        SET confirmed_at = COALESCE(confirmed_at, updated_at, created_at)
        WHERE confirm_status='confirmed' AND (confirmed_at IS NULL OR TRIM(confirmed_at)='')
        """
    )
    cur.execute(
        """
        UPDATE contracts
        SET sign_status = CASE
            WHEN sign_status IS NOT NULL AND TRIM(sign_status)<>'' THEN LOWER(sign_status)
            WHEN signed_status='Signed' OR signed_status='已签署' OR signed_status='已签约' THEN 'signed'
            WHEN signed_status='Sent' OR signed_status='已发送' THEN 'sent'
            ELSE 'draft'
        END
        """
    )
    cur.execute(
        """
        UPDATE contracts
        SET sign_status='draft'
        WHERE sign_status IS NULL
           OR TRIM(sign_status)=''
           OR LOWER(sign_status) NOT IN ('draft','sent','signed')
        """
    )
    cur.execute(
        """
        UPDATE contracts
        SET signed_at = COALESCE(signed_at, signed_date, updated_at, created_at)
        WHERE sign_status='signed' AND (signed_at IS NULL OR TRIM(signed_at)='')
        """
    )
    cur.execute(
        """
        UPDATE contracts
        SET signed_date = COALESCE(signed_date, substr(signed_at, 1, 10))
        WHERE sign_status='signed'
          AND (signed_date IS NULL OR TRIM(signed_date)='')
          AND signed_at IS NOT NULL
          AND TRIM(signed_at)<>''
        """
    )
    cur.execute(
        """
        UPDATE contracts
        SET signed_status = CASE
            WHEN sign_status='signed' THEN 'Signed'
            WHEN sign_status='sent' THEN 'Sent'
            ELSE COALESCE(NULLIF(signed_status,''), 'Unsigned')
        END
        """
    )
    cur.execute("UPDATE project_payments SET received_amount = COALESCE(received_amount, CASE WHEN status='Paid' THEN amount ELSE 0 END)")
    cur.execute("UPDATE ap_payables SET paid_amount = COALESCE(paid_amount, CASE WHEN status='Paid' THEN amount ELSE 0 END)")
    cur.execute("SELECT COUNT(1) c FROM bills")
    bills_count = int((cur.fetchone() or {"c": 0})["c"] or 0)
    if bills_count == 0:
        cur.execute(
            """
            SELECT project_id,vendor,category,bill_date,due_date,amount,paid_amount,status,reference_no,notes,created_at,updated_at,payment_date
            FROM ap_payables
            ORDER BY id ASC
            """
        )
        legacy_rows = [row_to_dict(x) for x in cur.fetchall()]
        vendor_id_map = {}
        for item in legacy_rows:
            vendor_name = str(item.get("vendor") or "").strip() or "Unknown Vendor"
            vendor_id = vendor_id_map.get(vendor_name)
            if not vendor_id:
                cur.execute("SELECT id FROM vendors WHERE name=?", (vendor_name,))
                existed = cur.fetchone()
                if existed:
                    vendor_id = existed["id"]
                else:
                    ts_vendor = item.get("updated_at") or item.get("created_at") or now_ts()
                    cur.execute(
                        "INSERT INTO vendors(name,type,tax_id,\"1099_required\",created_at,updated_at) VALUES (?,?,?,?,?,?)",
                        (vendor_name, "supplier", None, 0, ts_vendor, ts_vendor),
                    )
                    vendor_id = cur.lastrowid
                vendor_id_map[vendor_name] = vendor_id
            ts_bill = item.get("updated_at") or item.get("created_at") or now_ts()
            cur.execute(
                """
                INSERT INTO bills(project_id,vendor_id,category,bill_no,bill_date,due_date,amount,paid_amount,status,note,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    item.get("project_id"),
                    vendor_id,
                    item.get("category"),
                    item.get("reference_no"),
                    item.get("bill_date"),
                    item.get("due_date"),
                    float(item.get("amount") or 0),
                    float(item.get("paid_amount") or 0),
                    item.get("status") or "Open",
                    item.get("notes"),
                    item.get("created_at") or ts_bill,
                    ts_bill,
                ),
            )
            bill_id = cur.lastrowid
            paid_amount = float(item.get("paid_amount") or 0)
            if paid_amount > 0:
                pay_date = item.get("payment_date") or item.get("updated_at") or item.get("bill_date") or to_iso_date(datetime.now())
                cur.execute(
                    """
                    INSERT INTO payments(project_id,vendor_id,bill_id,amount,date,method,category,note,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        item.get("project_id"),
                        vendor_id,
                        bill_id,
                        paid_amount,
                        pay_date,
                        "other",
                        item.get("category"),
                        "Migrated from legacy ap_payables",
                        ts_bill,
                        ts_bill,
                    ),
                )
    cur.execute(
        """
        UPDATE change_orders
        SET status = CASE
            WHEN status IS NOT NULL AND TRIM(status)<>'' THEN status
            WHEN signed_status='Signed' THEN 'approved'
            WHEN signed_status='Rejected' THEN 'rejected'
            WHEN signed_status='Sent' THEN 'sent'
            WHEN signed_status='Pending' THEN 'draft'
            ELSE 'draft'
        END
        WHERE status IS NULL OR TRIM(status)=''
        """
    )
    cur.execute(
        """
        UPDATE change_orders
        SET title = COALESCE(NULLIF(title,''), NULLIF(reason,''), '变更单#' || id)
        WHERE title IS NULL OR TRIM(title)=''
        """
    )
    cur.execute(
        """
        UPDATE change_orders
        SET description = COALESCE(NULLIF(description,''), NULLIF(notes,''), NULLIF(reason,''), '')
        WHERE description IS NULL
        """
    )
    cur.execute(
        """
        UPDATE change_orders
        SET contract_id = (
            SELECT p.contract_id FROM projects p WHERE p.id=change_orders.project_id
        )
        WHERE contract_id IS NULL
        """
    )
    cur.execute(
        """
        UPDATE change_orders
        SET customer_id = (
            SELECT p.customer_id FROM projects p WHERE p.id=change_orders.project_id
        )
        WHERE customer_id IS NULL
        """
    )
    cur.execute("UPDATE change_orders SET impact_payment_plan=COALESCE(impact_payment_plan,0)")
    cur.execute("UPDATE change_orders SET affect_designer_commission=COALESCE(affect_designer_commission,0)")
    cur.execute(
        """
        UPDATE change_orders
        SET order_no='CO-' || printf('%05d', id)
        WHERE order_no IS NULL OR TRIM(order_no)=''
        """
    )
    cur.execute(
        """
        UPDATE change_orders
        SET approved_at=COALESCE(approved_at, signed_date, updated_at, created_at)
        WHERE (LOWER(COALESCE(status,''))='approved' OR status='已确认') AND (approved_at IS NULL OR TRIM(approved_at)='')
        """
    )
    cur.execute(
        """
        UPDATE change_orders
        SET signed_status = CASE
            WHEN LOWER(COALESCE(status,''))='approved' OR status='已确认' THEN 'Signed'
            WHEN LOWER(COALESCE(status,''))='rejected' OR status='已拒绝' THEN 'Rejected'
            WHEN LOWER(COALESCE(status,''))='sent' OR status='已发送' THEN 'Sent'
            ELSE COALESCE(NULLIF(signed_status,''), 'Pending')
        END
        """
    )
    cur.execute(
        """
        UPDATE change_orders
        SET confirmed_at=COALESCE(confirmed_at, approved_at, signed_date, updated_at, created_at)
        WHERE (LOWER(COALESCE(status,''))='approved' OR status='已确认')
          AND (confirmed_at IS NULL OR TRIM(confirmed_at)='')
        """
    )

    cur.execute("SELECT COUNT(1) c FROM users")
    if cur.fetchone()["c"] == 0:
        seed_users(cur)
    cur.execute("SELECT COUNT(1) c FROM company_settings")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            """
            INSERT INTO company_settings(
                id, company_name, legal_name, tagline, logo_horizontal_url, logo_icon_url,
                primary_color, accent_color, dark_color, light_bg, website_webhook_key, updated_at
            ) VALUES (1,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "OAKLIAN Remodeling & Construction",
                "OAKLIAN Remodeling & Construction LLC",
                "Remodeling & Construction",
                "/assets/images/logo-oaklian-dark.png",
                "/assets/images/logo-oaklian-light.png",
                "#1E293B",
                "#A38A55",
                "#0F172A",
                "#E2E8F0",
                WEBHOOK_KEY_ENV or "oaklian-webhook-key-change-me",
                now_ts(),
            ),
        )

    # Migrate legacy demo logo paths to deploy-safe asset paths.
    cur.execute(
        "UPDATE company_settings SET logo_horizontal_url='/assets/images/logo-oaklian-dark.png' "
        "WHERE COALESCE(logo_horizontal_url,'') IN ('','/static/brand/logo-horizontal.png')"
    )
    cur.execute(
        "UPDATE company_settings SET logo_icon_url='/assets/images/logo-oaklian-light.png' "
        "WHERE COALESCE(logo_icon_url,'') IN ('','/static/brand/logo-icon.png')"
    )

    cur.execute("SELECT COUNT(1) c FROM customers")
    if cur.fetchone()["c"] == 0:
        seed_demo_data(cur)
    cur.execute("SELECT COUNT(1) c FROM estimate_templates")
    if cur.fetchone()["c"] == 0:
        seed_estimate_templates(cur)
    cur.execute("SELECT COUNT(1) c FROM project_stage_templates")
    if cur.fetchone()["c"] == 0:
        seed_project_stage_templates(cur)
    sync_project_stage_template_items(cur)
    cur.execute("SELECT COUNT(1) c FROM ap_payables")
    if cur.fetchone()["c"] == 0:
        seed_ap_payables(cur)
    cur.execute("SELECT COUNT(1) c FROM document_templates")
    if cur.fetchone()["c"] == 0:
        seed_document_templates(cur)
    for setting_key, (setting_group, default_value) in SYSTEM_SETTINGS_DEFAULTS.items():
        cur.execute(
            """
            INSERT OR IGNORE INTO system_settings(setting_key,setting_value,setting_group,updated_at,updated_by)
            VALUES (?,?,?,?,NULL)
            """,
            (setting_key, str(default_value), setting_group, now_ts()),
        )
    cur.execute("UPDATE system_settings SET setting_group='company' WHERE setting_group IS NULL OR TRIM(setting_group)=''")
    cur.execute(
        """
        INSERT INTO system_settings(setting_key,setting_value,setting_group,updated_at,updated_by)
        SELECT 'company_logo_dark', logo_horizontal_url, 'company', ?, NULL
        FROM company_settings
        WHERE id=1 AND COALESCE(TRIM(logo_horizontal_url),'')<>''
        ON CONFLICT(setting_key) DO UPDATE SET
            setting_value=excluded.setting_value,
            setting_group=excluded.setting_group,
            updated_at=excluded.updated_at
        """,
        (now_ts(),),
    )
    cur.execute(
        """
        INSERT INTO system_settings(setting_key,setting_value,setting_group,updated_at,updated_by)
        SELECT 'company_logo_light', logo_icon_url, 'company', ?, NULL
        FROM company_settings
        WHERE id=1 AND COALESCE(TRIM(logo_icon_url),'')<>''
        ON CONFLICT(setting_key) DO UPDATE SET
            setting_value=excluded.setting_value,
            setting_group=excluded.setting_group,
            updated_at=excluded.updated_at
        """,
        (now_ts(),),
    )

    cur.execute("SELECT id,modules_json FROM users WHERE role='manager'")
    manager_rows = cur.fetchall()
    for mr in manager_rows:
        try:
            modules = json.loads(mr["modules_json"] or "[]")
        except json.JSONDecodeError:
            modules = []
        changed = False
        for required in (
            "document_templates",
            "notifications",
            "system_settings",
            "stage_templates",
            "designer_applications",
            "designers",
            "designer_assignments",
        ):
            if required not in modules:
                modules.append(required)
                changed = True
        if changed:
            cur.execute(
                "UPDATE users SET modules_json=?, updated_at=? WHERE id=?",
                (json.dumps(modules, ensure_ascii=False), now_ts(), mr["id"]),
            )

    cur.execute("DELETE FROM sessions WHERE expires_at < ?", (now_ts(),))

    conn.commit()
    conn.close()


def seed_users(cur):
    ts = now_ts()
    owner_modules = json.dumps(ALL_MODULES, ensure_ascii=False)
    pm_modules = json.dumps(
        [
            "dashboard",
            "notifications",
            "customers",
            "estimates",
            "projects",
            "designer_applications",
            "designers",
            "designer_assignments",
            "change_orders",
            "documents",
            "document_templates",
            "system_settings",
        ],
        ensure_ascii=False,
    )
    cur.execute(
        "INSERT INTO users(username,password,role,language,modules_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
        ("boss", "boss123", "owner", DEFAULT_LANGUAGE, owner_modules, ts, ts),
    )
    cur.execute(
        "INSERT INTO users(username,password,role,language,modules_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
        ("pm", "pm123", "manager", "en", pm_modules, ts, ts),
    )


def seed_demo_data(cur):
    ts = now_ts()
    today = datetime.now()
    ms = month_start(today)

    cur.execute(
        """
        INSERT INTO customers(
            name,phone,email,source,source_channel,source_note,demand_type,inquiry_type,preferred_contact_method,
            budget_range,status,primary_address,other_addresses,notes,created_at,updated_at
        )
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            "张先生",
            "13800000001",
            "zhang@example.com",
            "Xiaohongshu",
            "manual",
            "小红书咨询",
            "全屋翻新",
            "full_remodel",
            "phone",
            "30-40万",
            "已联系",
            "浦东新区XX路88号",
            "虹口区老房",
            "关注工期",
            ts,
            ts,
        ),
    )
    customer_id = cur.lastrowid

    cur.execute(
        "INSERT INTO estimates(customer_id,title,version,status,confirm_status,valid_until,subtotal,markup_rate,total_amount,line_items_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            customer_id,
            "全屋翻新方案",
            "v1",
            "Sent",
            "sent",
            to_iso_date(today + timedelta(days=7)),
            300000,
            0.18,
            354000,
            json.dumps([
                {"category": "Demolition", "material": 5000, "labor": 8000, "qty": 1, "unit_price": 13000, "subtotal": 13000},
                {"category": "Rough", "material": 52000, "labor": 41000, "qty": 1, "unit_price": 93000, "subtotal": 93000},
            ], ensure_ascii=False),
            ts,
            ts,
        ),
    )
    estimate_id = cur.lastrowid

    cur.execute(
        "INSERT INTO contracts(customer_id,estimate_id,contract_no,total_amount,payment_plan_json,signed_status,signed_date,sign_status,signed_at,attachment_url,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            customer_id,
            estimate_id,
            "CT-2026-001",
            354000,
            json.dumps([
                {"node": "Deposit", "due_date": to_iso_date(ms + timedelta(days=2)), "amount": 100000},
                {"node": "Milestone", "due_date": to_iso_date(ms + timedelta(days=20)), "amount": 150000},
                {"node": "Final", "due_date": to_iso_date(ms + timedelta(days=40)), "amount": 104000},
            ], ensure_ascii=False),
            "Signed",
            to_iso_date(ms + timedelta(days=3)),
            "signed",
            (ms + timedelta(days=3)).isoformat(timespec="seconds"),
            "https://example.com/contracts/ct-2026-001.pdf",
            ts,
            ts,
        ),
    )
    contract_id = cur.lastrowid

    cur.execute(
        "INSERT INTO projects(customer_id,contract_id,name,address,status,progress_pct,start_date,estimated_finish_date,manager,notes,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            customer_id,
            contract_id,
            "浦东张先生工地",
            "浦东新区XX路88号",
            "In Progress",
            48,
            to_iso_date(ms + timedelta(days=1)),
            to_iso_date(ms + timedelta(days=70)),
            "王工",
            "当前水电阶段",
            ts,
            ts,
        ),
    )
    project_id = cur.lastrowid

    cur.execute("UPDATE estimates SET project_id=?,updated_at=? WHERE id=?", (project_id, ts, estimate_id))
    cur.execute("UPDATE contracts SET project_id=?,updated_at=? WHERE id=?", (project_id, ts, contract_id))

    cur.execute(
        "INSERT INTO followups(customer_id,followup_date,content,next_action,owner,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
        (customer_id, to_iso_date(today - timedelta(days=4)), "客户确认量房", "3天后发报价", "销售李敏", ts, ts),
    )
    cur.execute(
        "INSERT INTO project_tasks(project_id,phase,title,owner,start_date,due_date,status,notes,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (project_id, "Rough", "水电布线", "王工", to_iso_date(today - timedelta(days=2)), to_iso_date(today + timedelta(days=3)), "In Progress", "等待开关到货", ts, ts),
    )
    cur.execute(
        "INSERT INTO site_logs(project_id,log_date,work_summary,crew_info,materials_info,photos_json,issue_note,template_used,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            project_id,
            to_iso_date(today),
            "厨房电路改造",
            "电工2人",
            "线管到货",
            json.dumps(["https://picsum.photos/640/400?9"], ensure_ascii=False),
            "客厅墙体空鼓待处理",
            "电路模板",
            ts,
            ts,
        ),
    )
    cur.execute(
        "INSERT INTO project_issues(project_id,title,description,severity,owner,due_date,status,before_photos_json,after_photos_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            project_id,
            "墙体空鼓",
            "需要整改",
            "High",
            "王工",
            to_iso_date(today + timedelta(days=2)),
            "Open",
            json.dumps(["https://picsum.photos/640/400?10"], ensure_ascii=False),
            json.dumps([], ensure_ascii=False),
            ts,
            ts,
        ),
    )
    cur.execute(
        "INSERT INTO project_payments(project_id,contract_id,node_name,due_date,amount,status,received_date,invoice_no,notes,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (project_id, contract_id, "Deposit", to_iso_date(ms + timedelta(days=2)), 100000, "Paid", to_iso_date(ms + timedelta(days=2)), "INV-001", "", ts, ts),
    )
    cur.execute(
        "INSERT INTO project_payments(project_id,contract_id,node_name,due_date,amount,status,received_date,invoice_no,notes,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (project_id, contract_id, "Milestone", to_iso_date(today + timedelta(days=5)), 150000, "Pending", "", "", "待确认", ts, ts),
    )
    cur.execute(
        "INSERT INTO project_costs(project_id,cost_type,vendor,cost_date,amount,notes,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?)",
        (project_id, "Material", "建材城A", to_iso_date(today), 38000, "电材", ts, ts),
    )
    cur.execute(
        "INSERT INTO change_orders(project_id,reason,items_json,amount_delta,days_delta,signed_status,signed_date,notes,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            project_id,
            "客户增加柜体",
            json.dumps([{"item": "阳台柜", "qty": 1, "unit_price": 12000}], ensure_ascii=False),
            12000,
            3,
            "Signed",
            to_iso_date(today),
            "已确认",
            ts,
            ts,
        ),
    )
    cur.execute(
        "INSERT INTO documents(customer_id,project_id,doc_type,file_name,tags,url,visibility,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (customer_id, project_id, "Contract", "CT-2026-001.pdf", "合同", "https://example.com/docs/ct-2026-001.pdf", "Manager", ts, ts),
    )


def seed_estimate_templates(cur):
    ts = now_ts()
    templates = [
        (
            "Standard Kitchen Remodel",
            "Kitchen",
            "v1",
            0.15,
            json.dumps(
                [
                    {"category": "Demolition", "qty": 1, "material": 3000, "labor": 6000, "subtotal": 9000},
                    {"category": "Rough Plumbing/Electrical", "qty": 1, "material": 9000, "labor": 12000, "subtotal": 21000},
                    {"category": "Cabinet & Finish", "qty": 1, "material": 18000, "labor": 10000, "subtotal": 28000},
                ],
                ensure_ascii=False,
            ),
            "中档厨房翻新套餐",
        ),
        (
            "Bathroom Basic Package",
            "Bathroom",
            "v1",
            0.12,
            json.dumps(
                [
                    {"category": "Demolition", "qty": 1, "material": 1500, "labor": 3500, "subtotal": 5000},
                    {"category": "Waterproof & Tile", "qty": 1, "material": 5000, "labor": 6000, "subtotal": 11000},
                    {"category": "Fixtures", "qty": 1, "material": 3500, "labor": 2000, "subtotal": 5500},
                ],
                ensure_ascii=False,
            ),
            "基础卫浴套餐",
        ),
        (
            "Full House Premium",
            "Full House",
            "v1",
            0.18,
            json.dumps(
                [
                    {"category": "Demolition", "qty": 1, "material": 6000, "labor": 14000, "subtotal": 20000},
                    {"category": "Rough", "qty": 1, "material": 42000, "labor": 45000, "subtotal": 87000},
                    {"category": "Finish", "qty": 1, "material": 85000, "labor": 52000, "subtotal": 137000},
                ],
                ensure_ascii=False,
            ),
            "高配全屋翻新套餐",
        ),
    ]
    cur.executemany(
        """
        INSERT INTO estimate_templates(name,package_type,version,default_markup_rate,line_items_json,notes,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        [(*row, ts, ts) for row in templates],
    )


def seed_project_stage_templates(cur):
    ts = now_ts()
    templates = [
        (
            "Kitchen Remodel Standard",
            "kitchen_remodel",
            1,
            1,
            json.dumps(["进场", "拆除", "水电改造", "柜体安装", "台面与五金", "验收"], ensure_ascii=False),
            "Kitchen Remodel",
        ),
        (
            "Bathroom Remodel",
            "bathroom_remodel",
            1,
            1,
            json.dumps(["进场", "拆除", "打底/防水", "贴砖", "洁具安装", "验收"], ensure_ascii=False),
            "卫生间改造流程",
        ),
        (
            "ADU Standard",
            "adu",
            1,
            1,
            json.dumps(["现场勘查", "设计与许可", "地基施工", "框架施工", "机电安装", "内装收尾", "验收"], ensure_ascii=False),
            "ADU",
        ),
        (
            "Full Home Remodel Standard",
            "full_home_remodel",
            1,
            1,
            json.dumps(["进场", "拆除", "结构调整", "水电改造", "泥木", "油漆", "安装", "验收"], ensure_ascii=False),
            "Full Home Remodel",
        ),
        (
            "Custom Standard",
            "custom",
            1,
            1,
            json.dumps(["进场", "施工", "验收"], ensure_ascii=False),
            "Custom",
        ),
    ]
    cur.executemany(
        """
        INSERT INTO project_stage_templates(name,project_type,is_default,is_active,stages_json,notes,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        [(*row, ts, ts) for row in templates],
    )


def sync_project_stage_template_items(cur):
    ts = now_ts()
    cur.execute("SELECT id,stages_json FROM project_stage_templates ORDER BY id ASC")
    rows = cur.fetchall()
    for row in rows:
        template_id = row["id"]
        cur.execute("SELECT COUNT(1) c FROM project_stage_template_items WHERE template_id=?", (template_id,))
        has_items = (cur.fetchone() or {"c": 0})["c"] > 0
        if not has_items:
            stage_names = []
            try:
                parsed = json.loads(row["stages_json"] or "[]")
                if isinstance(parsed, list):
                    stage_names = [str(x).strip() for x in parsed if str(x).strip()]
            except json.JSONDecodeError:
                stage_names = []
            if not stage_names:
                stage_names = list(DEFAULT_PROJECT_STAGES)
            for idx, step_name in enumerate(stage_names, start=1):
                cur.execute(
                    """
                    INSERT INTO project_stage_template_items(template_id,step_name,step_order,is_active,created_at,updated_at)
                    VALUES (?,?,?,?,?,?)
                    """,
                    (template_id, step_name, idx, 1, ts, ts),
                )
        cur.execute(
            "SELECT step_name FROM project_stage_template_items WHERE template_id=? AND is_active=1 ORDER BY step_order ASC,id ASC",
            (template_id,),
        )
        names = [str(x["step_name"] or "").strip() for x in cur.fetchall() if str(x["step_name"] or "").strip()]
        if names:
            cur.execute(
                "UPDATE project_stage_templates SET stages_json=?, updated_at=? WHERE id=?",
                (json.dumps(names, ensure_ascii=False), ts, template_id),
            )

    cur.execute("UPDATE project_stage_templates SET is_active=1 WHERE is_active IS NULL")
    for project_type in STAGE_TEMPLATE_PROJECT_TYPE_SET:
        cur.execute("SELECT COUNT(1) c FROM project_stage_templates WHERE project_type=? AND is_default=1", (project_type,))
        has_default = (cur.fetchone() or {"c": 0})["c"] > 0
        if has_default:
            continue
        cur.execute(
            "SELECT id FROM project_stage_templates WHERE project_type=? AND COALESCE(is_active,1)=1 ORDER BY id ASC LIMIT 1",
            (project_type,),
        )
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE project_stage_templates SET is_default=1, updated_at=? WHERE id=?", (ts, row["id"]))


def seed_ap_payables(cur):
    ts = now_ts()
    today = datetime.now()
    due1 = to_iso_date(today + timedelta(days=5))
    due2 = to_iso_date(today - timedelta(days=8))
    cur.execute("SELECT id FROM projects ORDER BY id ASC LIMIT 1")
    row = cur.fetchone()
    project_id = row["id"] if row else None
    rows = [
        (project_id, "ABC Tile Supply", "Material", to_iso_date(today - timedelta(days=2)), due1, 18000, 0, "Pending", None, "BILL-AT-1001", "Tile and grout"),
        (project_id, "West Coast Subcontractors", "Subcontract", to_iso_date(today - timedelta(days=20)), due2, 22000, 5000, "Overdue", to_iso_date(today - timedelta(days=3)), "BILL-WC-2002", "Partial payment made"),
    ]
    cur.executemany(
        """
        INSERT INTO ap_payables(project_id,vendor,category,bill_date,due_date,amount,paid_amount,status,payment_date,reference_no,notes,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        [(*r, ts, ts) for r in rows],
    )


def seed_document_templates(cur):
    ts = now_ts()
    rows = [
        (
            "estimate",
            "other",
            "默认报价模板",
            1,
            "报价单 / 方案",
            "感谢您选择 OAKLIAN。以下为本次项目报价概要，请审核。",
            "价格基于当前施工范围与材料标准，超出部分将按变更单执行。",
            "报价有效期内可沟通调整，最终以签署文件为准。",
            "本报价单仅用于本次装修项目沟通与签约参考。",
        ),
        (
            "contract",
            "other",
            "默认合同模板",
            1,
            "合同",
            "本合同用于明确双方权责、工期安排与付款节点。",
            "如现场条件发生变化，双方可通过变更单确认调整内容。",
            "本合同内容由双方确认后执行，未尽事宜以书面补充条款为准。",
            "感谢信任，期待顺利完工交付。",
        ),
        (
            "change_order",
            "other",
            "默认变更单模板",
            1,
            "变更单",
            "本变更单用于记录施工范围、工期或费用调整事项。",
            "本变更需客户确认后方可执行并计入结算。",
            "未签字确认的变更内容不作为最终结算依据。",
            "请双方确认后签字留档。",
        ),
    ]
    cur.executemany(
        """
        INSERT INTO document_templates(
            template_type,project_type,name,is_default,title_text,intro_text,note_text,terms_text,footer_text,created_at,updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        [(*r, ts, ts) for r in rows],
    )


class CRMHandler(BaseHTTPRequestHandler):
    server_version = "DecorCRM/3.0"

    def log_message(self, format_string, *args):
        APP_LOGGER.info("%s - %s", self.address_string(), format_string % args)

    def log_error(self, format_string, *args):
        ERROR_LOGGER.error("%s - %s", self.address_string(), format_string % args)

    def _set_headers(self, status=200, content_type="application/json; charset=utf-8", extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()

    def _json_response(self, data, status=200, extra_headers=None):
        self._set_headers(status=status, extra_headers=extra_headers)
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _html_response(self, html, status=200):
        self._set_headers(status=status, content_type="text/html; charset=utf-8")
        self.wfile.write(html.encode("utf-8"))

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return None

    def _serve_static_file(self, rel_path, root_dir):
        path = (root_dir / rel_path).resolve()
        root = root_dir.resolve()
        if not str(path).startswith(str(root)) or not path.exists() or not path.is_file():
            self._set_headers(404, "text/plain; charset=utf-8")
            self.wfile.write(b"Not Found")
            return

        guessed = mimetypes.guess_type(path.name)[0]
        ctype = guessed or "application/octet-stream"
        if ctype.startswith("text/") or ctype in {"application/javascript", "application/json", "application/xml"}:
            ctype = f"{ctype}; charset=utf-8"
        self._set_headers(200, ctype)
        self.wfile.write(path.read_bytes())

    def _serve_brand_favicon(self):
        conn = get_conn()
        cur = conn.cursor()
        icon_url = (self._brand_logo_urls(cur).get("light") or "").strip()
        conn.close()
        if icon_url.startswith("/uploads/"):
            return self._serve_static_file(unquote(icon_url[len("/uploads/") :]), UPLOADS_DIR)
        if icon_url.startswith("/assets/"):
            return self._serve_static_file(unquote(icon_url[len("/assets/") :]), ASSETS_DIR)
        return self._serve_static_file("images/favicon.png", ASSETS_DIR)

    def _parse_cookies(self):
        raw = self.headers.get("Cookie", "")
        out = {}
        for part in raw.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                out[k] = v
        return out

    def _current_user(self):
        cookies = self._parse_cookies()
        token = cookies.get("crm_token")
        if not token:
            return None
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT u.* FROM sessions s
            JOIN users u ON u.id=s.user_id
            WHERE s.token=? AND s.expires_at > ?
            """,
            (token, now_ts()),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        user = row_to_dict(row)
        try:
            raw_modules = json.loads(user.get("modules_json") or "[]")
        except json.JSONDecodeError:
            raw_modules = []
        user["modules"] = self._normalized_user_modules(user.get("role"), raw_modules)
        return user

    def _normalized_user_modules(self, role, modules):
        role_key = (role or "").strip()
        if role_key == "owner":
            return list(ALL_MODULES)
        if role_key == "designer":
            requested = [m for m in (modules or []) if m in DESIGNER_ALLOWED_MODULES]
            return requested or list(DESIGNER_ALLOWED_MODULES)
        return [m for m in (modules or []) if m in ALL_MODULES]

    def _has_module(self, user, module):
        if not user:
            return False
        role_key = (user.get("role") or "").strip()
        if role_key == "owner":
            return True
        if role_key == "designer":
            return module in (user.get("modules") or [])
        return module in (user.get("modules") or [])

    def _require_auth(self):
        user = self._current_user()
        if not user:
            self._json_response({"error": "Unauthorized"}, 401)
            return None
        return user

    def _require_module(self, user, module):
        if not self._has_module(user, module):
            self._json_response({"error": f"Forbidden: {module}"}, 403)
            return False
        return True

    def _project_accessible(self, cur, user, project_id):
        if not project_id:
            return False
        if user.get("role") != "designer":
            return True
        cur.execute("SELECT id FROM projects WHERE id=? AND designer_id=?", (project_id, user.get("id")))
        return cur.fetchone() is not None

    def _forbid_if_no_project_access(self, cur, user, project_id):
        if self._project_accessible(cur, user, project_id):
            return False
        self._json_response({"error": "Forbidden: project access denied"}, 403)
        return True

    def _project_status_key(self, value):
        raw = normalize_key(value or "")
        if raw in {"completed", "done", "已完成", "已完工"}:
            return "completed"
        if raw in {"not_started", "not started", "pending", "待开工", "未开始"}:
            return "not_started"
        if raw in {"in_progress", "in progress", "施工中", "进行中"}:
            return "in_progress"
        if raw in {"on_hold", "on hold", "hold", "暂停", "搁置", "已暂停"}:
            return "on_hold"
        return raw

    def _is_project_completed(self, status, progress_pct):
        status_key = self._project_status_key(status)
        if status_key == "completed":
            return True
        try:
            return float(progress_pct or 0) >= 100
        except (TypeError, ValueError):
            return False

    def _project_id_for_table_record(self, cur, table, record_id):
        if table == "projects":
            return record_id
        if table == "designer_assignments":
            cur.execute("SELECT source_type,source_id FROM designer_assignments WHERE id=?", (record_id,))
            row = cur.fetchone()
            if not row:
                return None
            if normalize_key(row["source_type"] or "") == "project":
                try:
                    return int(row["source_id"])
                except (TypeError, ValueError):
                    return None
            return None
        if "project_id" in TABLE_FIELDS.get(table, []):
            cur.execute(f"SELECT project_id FROM {table} WHERE id=?", (record_id,))
            row = cur.fetchone()
            return row["project_id"] if row else None
        if table == "contracts":
            cur.execute("SELECT project_id FROM contracts WHERE id=?", (record_id,))
            row = cur.fetchone()
            return row["project_id"] if row else None
        if table == "contract_payment_milestones":
            cur.execute(
                """
                SELECT p.id AS project_id
                FROM contract_payment_milestones m
                LEFT JOIN contracts c ON c.id=m.contract_id
                LEFT JOIN projects p ON p.contract_id=c.id
                WHERE m.id=?
                ORDER BY p.id ASC LIMIT 1
                """,
                (record_id,),
            )
            row = cur.fetchone()
            return row["project_id"] if row else None
        if table == "designer_commissions":
            cur.execute("SELECT project_id FROM designer_commissions WHERE id=?", (record_id,))
            row = cur.fetchone()
            return row["project_id"] if row else None
        return None

    def _vendor_type_key(self, value):
        key = normalize_key(value or "supplier")
        if key in VENDOR_TYPE_SET:
            return key
        return "supplier"

    def _sync_bill_paid_amount(self, cur, bill_id):
        if not bill_id:
            return
        cur.execute("SELECT id,amount FROM bills WHERE id=?", (bill_id,))
        bill = cur.fetchone()
        if not bill:
            return
        cur.execute("SELECT COALESCE(SUM(amount),0) total_paid FROM payments WHERE bill_id=?", (bill_id,))
        paid_row = cur.fetchone()
        paid = float((paid_row["total_paid"] if paid_row and paid_row["total_paid"] is not None else 0) or 0)
        total = float(bill["amount"] or 0)
        open_amount = max(total - paid, 0)
        if paid <= 0:
            status = "Open"
        elif open_amount <= 0.0001:
            status = "Paid"
        else:
            status = "Partially Paid"
        cur.execute(
            "UPDATE bills SET paid_amount=?, status=?, updated_at=? WHERE id=?",
            (round(min(paid, total), 2), status, now_ts(), bill_id),
        )

    def _vendor_payments_get(self, vendor_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('SELECT id,name,type,tax_id,"1099_required",w9_received FROM vendors WHERE id=?', (vendor_id,))
        vendor = cur.fetchone()
        if not vendor:
            conn.close()
            return self._json_response({"error": "Vendor not found"}, 404)
        query = parse_qs(urlparse(self.path).query)
        year = datetime.now().year
        if query.get("year") and str(query["year"][0]).strip().isdigit():
            year = int(query["year"][0])
        params = [vendor_id]
        where = "WHERE p.vendor_id=?"
        if user.get("role") == "designer":
            where += " AND p.project_id IN (SELECT id FROM projects WHERE designer_id=?)"
            params.append(user.get("id"))
        cur.execute(
            f"""
            SELECT p.*, pr.name AS project_name, b.bill_no
            FROM payments p
            LEFT JOIN projects pr ON pr.id=p.project_id
            LEFT JOIN bills b ON b.id=p.bill_id
            {where}
            ORDER BY p.date DESC,p.id DESC
            """,
            tuple(params),
        )
        rows = [row_to_dict(x) for x in cur.fetchall()]
        total_paid_this_year = 0.0
        prefix = f"{year}-"
        for item in rows:
            d = str(item.get("date") or "")
            if d.startswith(prefix):
                total_paid_this_year += float(item.get("amount") or 0)
        payload = {
            "vendor": row_to_dict(vendor),
            "payments": rows,
            "year": year,
            "total_paid_this_year": round(total_paid_this_year, 2),
            "over_600": 1 if total_paid_this_year >= 600 else 0,
        }
        conn.close()
        return self._json_response(payload)

    def _vendor_ledger_get(self, vendor_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute('SELECT id,name,type,tax_id,"1099_required",w9_received FROM vendors WHERE id=?', (vendor_id,))
        vendor = cur.fetchone()
        if not vendor:
            conn.close()
            return self._json_response({"error": "Vendor not found"}, 404)

        query = parse_qs(urlparse(self.path).query)
        year = datetime.now().year
        if query.get("year") and str(query["year"][0]).strip().isdigit():
            year = int(query["year"][0])
        prefix = f"{year}-"

        bill_params = [vendor_id]
        bill_where = "WHERE b.vendor_id=?"
        pay_params = [vendor_id]
        pay_where = "WHERE p.vendor_id=?"
        if user.get("role") == "designer":
            designer_id = user.get("id")
            bill_where += " AND b.project_id IN (SELECT id FROM projects WHERE designer_id=?)"
            pay_where += " AND p.project_id IN (SELECT id FROM projects WHERE designer_id=?)"
            bill_params.append(designer_id)
            pay_params.append(designer_id)

        cur.execute(
            f"""
            SELECT b.*,pr.name AS project_name
            FROM bills b
            LEFT JOIN projects pr ON pr.id=b.project_id
            {bill_where}
            ORDER BY COALESCE(b.bill_date,b.created_at) DESC,b.id DESC
            """,
            tuple(bill_params),
        )
        bills = [row_to_dict(x) for x in cur.fetchall()]
        self._attach_entity_file_meta(cur, "bill", bills)

        cur.execute(
            f"""
            SELECT p.*,pr.name AS project_name,b.bill_no
            FROM payments p
            LEFT JOIN projects pr ON pr.id=p.project_id
            LEFT JOIN bills b ON b.id=p.bill_id
            {pay_where}
            ORDER BY p.date DESC,p.id DESC
            """,
            tuple(pay_params),
        )
        payments = [row_to_dict(x) for x in cur.fetchall()]
        self._attach_entity_file_meta(cur, "payment", payments)

        total_paid_this_year = 0.0
        for item in payments:
            if str(item.get("date") or "").startswith(prefix):
                total_paid_this_year += float(item.get("amount") or 0)

        open_bills_total = 0.0
        for item in bills:
            amount = float(item.get("amount") or 0)
            paid_amount = float(item.get("paid_amount") or 0)
            item["open_amount"] = round(max(amount - paid_amount, 0), 2)
            open_bills_total += item["open_amount"]

        payload = {
            "vendor": row_to_dict(vendor),
            "year": year,
            "total_paid_this_year": round(total_paid_this_year, 2),
            "over_600": 1 if total_paid_this_year >= 600 else 0,
            "open_bills_total": round(open_bills_total, 2),
            "current_outstanding_balance": round(open_bills_total, 2),
            "bills": bills,
            "payments": payments,
        }
        conn.close()
        return self._json_response(payload)

    def _next_contract_no(self, cur):
        prefix = datetime.now().strftime("CT-%Y%m%d")
        cur.execute("SELECT contract_no FROM contracts WHERE contract_no LIKE ? ORDER BY id DESC LIMIT 1", (f"{prefix}-%",))
        row = cur.fetchone()
        seq = 1
        if row and row["contract_no"]:
            tail = str(row["contract_no"]).split("-")[-1]
            if tail.isdigit():
                seq = int(tail) + 1
        return f"{prefix}-{seq:03d}"

    def _next_change_order_no(self, cur):
        prefix = datetime.now().strftime("CO-%Y%m%d")
        cur.execute("SELECT order_no FROM change_orders WHERE order_no LIKE ? ORDER BY id DESC LIMIT 1", (f"{prefix}-%",))
        row = cur.fetchone()
        seq = 1
        if row and row["order_no"]:
            tail = str(row["order_no"]).split("-")[-1]
            if tail.isdigit():
                seq = int(tail) + 1
        return f"{prefix}-{seq:03d}"

    def _designer_app_status_key(self, value):
        key = normalize_key(value or "")
        aliases = {
            "pending": "pending",
            "new": "pending",
            "new_application": "pending",
            "待审核": "pending",
            "待联系": "pending",
            "contacted": "contacted",
            "已联系": "contacted",
            "approved": "approved",
            "通过": "approved",
            "已通过": "approved",
            "rejected": "rejected",
            "拒绝": "rejected",
            "已拒绝": "rejected",
        }
        return aliases.get(key, "pending")

    def _designer_assignment_status_key(self, value):
        raw = str(value or "").strip()
        norm = raw.lower().replace("-", "_").replace(" ", "_")
        key = normalize_key(raw)
        aliases = {
            "new": "new",
            "pending": "new",
            "未开始": "new",
            "invited": "invited",
            "已邀请": "invited",
            "accepted": "accepted",
            "approved": "accepted",
            "已接受": "accepted",
            "declined": "declined",
            "rejected": "declined",
            "已拒绝": "declined",
            "in_progress": "in_progress",
            "active": "in_progress",
            "进行中": "in_progress",
            "施工中": "in_progress",
            "completed": "completed",
            "done": "completed",
            "已完成": "completed",
            "cancelled": "cancelled",
            "canceled": "cancelled",
            "已取消": "cancelled",
        }
        if raw in aliases:
            return aliases[raw]
        if norm in aliases:
            return aliases[norm]
        if key in aliases:
            return aliases[key]
        if key in DESIGNER_ASSIGNMENT_STATUS_SET:
            return key
        return "new"

    def _designer_modules_from_payload(self, modules):
        if isinstance(modules, str):
            txt = modules.strip()
            if txt.startswith("[") and txt.endswith("]"):
                try:
                    parsed = json.loads(txt)
                    if isinstance(parsed, list):
                        modules = parsed
                    else:
                        modules = [txt]
                except json.JSONDecodeError:
                    modules = [x.strip() for x in txt.split(",") if x.strip()]
            elif txt:
                modules = [x.strip() for x in txt.split(",") if x.strip()]
            else:
                modules = []
        if not isinstance(modules, list):
            modules = []
        cleaned = [normalize_key(x) for x in modules if normalize_key(x)]
        cleaned = [x for x in cleaned if x in DESIGNER_PERMISSION_MODULES]
        if not cleaned:
            cleaned = list(DESIGNER_ALLOWED_MODULES)
        # keep order stable
        return [x for x in DESIGNER_PERMISSION_MODULES if x in cleaned]

    def _upsert_designer_permissions(self, cur, designer_id, modules, updated_by=None):
        allowed = self._designer_modules_from_payload(modules)
        ts = now_ts()
        cur.execute("DELETE FROM designer_permissions WHERE designer_id=?", (designer_id,))
        for module_key in DESIGNER_PERMISSION_MODULES:
            cur.execute(
                """
                INSERT INTO designer_permissions(designer_id,module_key,enabled,updated_by,created_at,updated_at)
                VALUES (?,?,?,?,?,?)
                """,
                (designer_id, module_key, 1 if module_key in allowed else 0, updated_by, ts, ts),
            )
        return allowed

    def _designer_permissions_modules(self, cur, designer_id):
        cur.execute(
            """
            SELECT module_key,enabled
            FROM designer_permissions
            WHERE designer_id=?
            ORDER BY id ASC
            """,
            (designer_id,),
        )
        rows = cur.fetchall()
        if not rows:
            return list(DESIGNER_ALLOWED_MODULES)
        enabled = [normalize_key(r["module_key"]) for r in rows if int(r["enabled"] or 0) == 1]
        enabled = [x for x in enabled if x in DESIGNER_PERMISSION_MODULES]
        return [x for x in DESIGNER_PERMISSION_MODULES if x in enabled] or list(DESIGNER_ALLOWED_MODULES)

    def _designer_ids_for_user(self, cur, user):
        if not user:
            return []
        ids = set()
        try:
            linked_id = int(user.get("linked_designer_id") or 0)
        except (TypeError, ValueError):
            linked_id = 0
        if linked_id > 0:
            ids.add(linked_id)
        cur.execute("SELECT id FROM designers WHERE user_id=?", (user.get("id"),))
        for row in cur.fetchall():
            try:
                ids.add(int(row["id"]))
            except (TypeError, ValueError):
                continue
        return sorted(ids)

    def _require_document_template_manage(self, user):
        role_key = (user.get("role") or "").strip().lower()
        if role_key in {"owner", "manager", "admin"}:
            return True
        self._json_response({"error": "Forbidden: document_templates"}, 403)
        return False

    def _require_system_settings_manage(self, user):
        role_key = normalize_key(user.get("role") or "")
        if role_key not in {"owner", "manager", "admin"}:
            self._json_response({"error": "Forbidden: system_settings"}, 403)
            return False
        if role_key != "owner" and not self._has_module(user, "system_settings"):
            self._json_response({"error": "Forbidden: system_settings"}, 403)
            return False
        return True

    def _require_designer_pipeline_manage(self, user, module="designer_applications"):
        role_key = normalize_key(user.get("role") or "")
        if role_key == "designer":
            self._json_response({"error": "Forbidden: designer_applications"}, 403)
            return False
        if role_key in {"owner", "admin"}:
            return True
        if module and not self._has_module(user, module):
            self._json_response({"error": f"Forbidden: {module}"}, 403)
            return False
        return True

    def _setting_default(self, key):
        group, value = SYSTEM_SETTINGS_DEFAULTS.get(key, ("company", ""))
        return group, str(value)

    def _serialize_setting_value(self, value):
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, bool):
            return "1" if value else "0"
        if value is None:
            return ""
        return str(value)

    def _deserialize_setting_value(self, value):
        raw = str(value or "")
        txt = raw.strip()
        if not txt:
            return ""
        if (txt.startswith("{") and txt.endswith("}")) or (txt.startswith("[") and txt.endswith("]")):
            try:
                return json.loads(txt)
            except json.JSONDecodeError:
                return raw
        return raw

    def _normalize_setting_group(self, key, group):
        g = normalize_key(group or "")
        if g in SYSTEM_SETTING_GROUP_SET:
            return g
        default_group, _ = self._setting_default(key)
        if default_group in SYSTEM_SETTING_GROUP_SET:
            return default_group
        return "company"

    def _ensure_system_setting_defaults(self, cur):
        ts = now_ts()
        for setting_key, (setting_group, default_value) in SYSTEM_SETTINGS_DEFAULTS.items():
            cur.execute(
                """
                INSERT OR IGNORE INTO system_settings(setting_key,setting_value,setting_group,updated_at,updated_by)
                VALUES (?,?,?,?,NULL)
                """,
                (setting_key, str(default_value), setting_group, ts),
            )

    def _system_settings_rows(self, cur, group=None):
        self._ensure_system_setting_defaults(cur)
        sql = "SELECT * FROM system_settings"
        params = []
        if group:
            sql += " WHERE setting_group=?"
            params.append(group)
        sql += " ORDER BY setting_group ASC, setting_key ASC"
        cur.execute(sql, tuple(params))
        rows = []
        for row in cur.fetchall():
            item = row_to_dict(row)
            item["setting_value_parsed"] = self._deserialize_setting_value(item.get("setting_value"))
            rows.append(item)
        return rows

    def _system_setting_lookup(self, cur):
        rows = self._system_settings_rows(cur)
        return {x["setting_key"]: x for x in rows}

    def _system_setting_text(self, cur, setting_key, default_value=""):
        cur.execute("SELECT setting_value FROM system_settings WHERE setting_key=?", (setting_key,))
        row = cur.fetchone()
        if row and row["setting_value"] is not None:
            return str(row["setting_value"])
        _, default_raw = self._setting_default(setting_key)
        return str(default_raw if default_raw is not None else default_value)

    def _system_setting_int(self, cur, setting_key, default_value=0):
        raw = self._system_setting_text(cur, setting_key, default_value)
        try:
            return int(float(str(raw).strip() or str(default_value)))
        except (TypeError, ValueError):
            return int(default_value)

    def _system_setting_bool(self, cur, setting_key, default_value=False):
        raw = self._system_setting_text(cur, setting_key, "1" if default_value else "0")
        if isinstance(raw, str):
            return raw.strip().lower() in {"1", "true", "yes", "on", "y"}
        return bool(raw)

    def _upsert_system_setting(self, cur, setting_key, setting_value, setting_group="company", updated_by=None):
        cur.execute(
            """
            INSERT INTO system_settings(setting_key,setting_value,setting_group,updated_at,updated_by)
            VALUES (?,?,?,?,?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value=excluded.setting_value,
                setting_group=excluded.setting_group,
                updated_at=excluded.updated_at,
                updated_by=excluded.updated_by
            """,
            (setting_key, str(setting_value or ""), setting_group, now_ts(), updated_by),
        )

    def _sync_brand_logo_settings(self, cur, brand=None, updated_by=None):
        brand = brand or self._read_company_settings(cur)
        horizontal = str((brand or {}).get("logo_horizontal_url") or "").strip()
        icon = str((brand or {}).get("logo_icon_url") or "").strip()
        if horizontal:
            self._upsert_system_setting(cur, "company_logo_dark", horizontal, "company", updated_by)
        if icon:
            self._upsert_system_setting(cur, "company_logo_light", icon, "company", updated_by)

    def _brand_logo_urls(self, cur):
        brand = self._read_company_settings(cur)
        dark = str((brand or {}).get("logo_horizontal_url") or "").strip()
        light = str((brand or {}).get("logo_icon_url") or "").strip()
        if not dark:
            dark = self._system_setting_text(cur, "company_logo_dark", "/assets/images/logo-oaklian-dark.png").strip()
        if not light:
            light = self._system_setting_text(cur, "company_logo_light", "/assets/images/logo-oaklian-light.png").strip()
        return {
            "dark": dark or "/assets/images/logo-oaklian-dark.png",
            "light": light or "/assets/images/logo-oaklian-light.png",
            "brand": brand,
        }

    def _system_settings_get(self, query):
        group_raw = (query.get("group", [""])[0] or "").strip()
        group = normalize_key(group_raw) if group_raw else ""
        if group and group not in SYSTEM_SETTING_GROUP_SET:
            return self._json_response({"error": "group must be company/business/documents/notifications/permissions/printing"}, 400)
        conn = get_conn()
        cur = conn.cursor()
        rows = self._system_settings_rows(cur, group=group or None)
        conn.commit()
        conn.close()
        return self._json_response(rows)

    def _normalize_system_setting_payload_item(self, item, require_key=True):
        data = dict(item or {})
        setting_key = str(data.get("setting_key") or "").strip()
        if require_key and not setting_key:
            raise ValueError("setting_key is required")
        setting_value = self._serialize_setting_value(data.get("setting_value"))
        setting_group = self._normalize_setting_group(setting_key, data.get("setting_group"))
        if setting_group not in SYSTEM_SETTING_GROUP_SET:
            raise ValueError("setting_group must be company/business/documents/notifications/permissions/printing")
        return {
            "setting_key": setting_key,
            "setting_value": setting_value,
            "setting_group": setting_group,
        }

    def _system_settings_post(self, user):
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        try:
            item = self._normalize_system_setting_payload_item(payload, require_key=True)
        except ValueError as err:
            return self._json_response({"error": str(err)}, 400)
        conn = get_conn()
        cur = conn.cursor()
        self._ensure_system_setting_defaults(cur)
        cur.execute("SELECT id FROM system_settings WHERE setting_key=?", (item["setting_key"],))
        if cur.fetchone():
            conn.close()
            return self._json_response({"error": "setting_key already exists"}, 409)
        ts = now_ts()
        cur.execute(
            """
            INSERT INTO system_settings(setting_key,setting_value,setting_group,updated_at,updated_by)
            VALUES (?,?,?,?,?)
            """,
            (item["setting_key"], item["setting_value"], item["setting_group"], ts, user.get("id")),
        )
        conn.commit()
        cur.execute("SELECT * FROM system_settings WHERE setting_key=?", (item["setting_key"],))
        row = row_to_dict(cur.fetchone())
        row["setting_value_parsed"] = self._deserialize_setting_value(row.get("setting_value"))
        conn.close()
        return self._json_response(row, 201)

    def _system_settings_put(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 3 or parts[0] != "api" or parts[1] != "system-settings":
            return self._json_response({"error": "Not found"}, 404)
        setting_key = unquote(parts[2]).strip()
        if not setting_key:
            return self._json_response({"error": "Invalid setting key"}, 400)
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        update_group = payload.get("setting_group")
        group = self._normalize_setting_group(setting_key, update_group)
        if group not in SYSTEM_SETTING_GROUP_SET:
            return self._json_response({"error": "setting_group must be company/business/documents/notifications/permissions/printing"}, 400)
        setting_value = self._serialize_setting_value(payload.get("setting_value"))
        conn = get_conn()
        cur = conn.cursor()
        self._ensure_system_setting_defaults(cur)
        ts = now_ts()
        cur.execute(
            """
            INSERT INTO system_settings(setting_key,setting_value,setting_group,updated_at,updated_by)
            VALUES (?,?,?,?,?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value=excluded.setting_value,
                setting_group=excluded.setting_group,
                updated_at=excluded.updated_at,
                updated_by=excluded.updated_by
            """,
            (setting_key, setting_value, group, ts, user.get("id")),
        )
        conn.commit()
        cur.execute("SELECT * FROM system_settings WHERE setting_key=?", (setting_key,))
        row = row_to_dict(cur.fetchone())
        row["setting_value_parsed"] = self._deserialize_setting_value(row.get("setting_value"))
        conn.close()
        return self._json_response(row)

    def _system_settings_bulk_save(self, user):
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        rows_input = []
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            rows_input = payload.get("items") or []
        elif isinstance(payload, dict):
            group = payload.get("setting_group") or payload.get("group")
            if isinstance(payload.get("settings"), dict):
                for k, v in (payload.get("settings") or {}).items():
                    rows_input.append({"setting_key": k, "setting_value": v, "setting_group": group})
            else:
                for k, v in payload.items():
                    if k in {"setting_group", "group"}:
                        continue
                    rows_input.append({"setting_key": k, "setting_value": v, "setting_group": group})
        if not rows_input:
            return self._json_response({"error": "No settings to save"}, 400)

        items = []
        try:
            for row in rows_input:
                items.append(self._normalize_system_setting_payload_item(row, require_key=True))
        except ValueError as err:
            return self._json_response({"error": str(err)}, 400)

        conn = get_conn()
        cur = conn.cursor()
        self._ensure_system_setting_defaults(cur)
        ts = now_ts()
        for item in items:
            cur.execute(
                """
                INSERT INTO system_settings(setting_key,setting_value,setting_group,updated_at,updated_by)
                VALUES (?,?,?,?,?)
                ON CONFLICT(setting_key) DO UPDATE SET
                    setting_value=excluded.setting_value,
                    setting_group=excluded.setting_group,
                    updated_at=excluded.updated_at,
                    updated_by=excluded.updated_by
                """,
                (item["setting_key"], item["setting_value"], item["setting_group"], ts, user.get("id")),
            )
        conn.commit()
        result = []
        for item in items:
            cur.execute("SELECT * FROM system_settings WHERE setting_key=?", (item["setting_key"],))
            row = row_to_dict(cur.fetchone())
            row["setting_value_parsed"] = self._deserialize_setting_value(row.get("setting_value"))
            result.append(row)
        conn.close()
        return self._json_response({"ok": True, "updated": len(result), "items": result})

    def _normalize_document_template_type(self, value):
        key = normalize_key(value)
        aliases = {
            "estimate_template": "estimate",
            "contract_template": "contract",
            "change_order_template": "change_order",
        }
        key = aliases.get(key, key)
        return key if key in DOCUMENT_TEMPLATE_TYPE_SET else ""

    def _normalize_project_type(self, value):
        key = normalize_key(value)
        return key if key in PROJECT_TYPE_SET else ""

    def _normalize_stage_template_project_type(self, value):
        key = normalize_key(value)
        aliases = {
            "kitchen": "kitchen_remodel",
            "bathroom": "bathroom_remodel",
            "full_house": "full_home_remodel",
            "full_remodel": "full_home_remodel",
            "other": "custom",
            "custom_furniture": "custom",
        }
        key = aliases.get(key, key)
        return key if key in STAGE_TEMPLATE_PROJECT_TYPE_SET else ""

    def _map_project_type_to_stage_template_type(self, project_type):
        key = self._normalize_project_type(project_type)
        mapping = {
            "kitchen_remodel": "kitchen_remodel",
            "bathroom_remodel": "bathroom_remodel",
            "full_remodel": "full_home_remodel",
            "custom_furniture": "custom",
            "other": "custom",
        }
        return mapping.get(key, "custom")

    def _normalize_stage_template_payload(self, payload, for_update=False):
        raw = payload or {}
        data = {}
        if not for_update or "name" in raw:
            name = str(raw.get("name") or "").strip()
            if not name:
                raise ValueError("name is required")
            data["name"] = name
        if not for_update or "project_type" in raw:
            project_type = self._normalize_stage_template_project_type(raw.get("project_type"))
            if not project_type:
                raise ValueError("project_type must be kitchen_remodel/bathroom_remodel/adu/full_home_remodel/custom")
            data["project_type"] = project_type
        if not for_update or "is_default" in raw:
            data["is_default"] = self._default_flag(raw.get("is_default"))
        if not for_update or "is_active" in raw:
            data["is_active"] = self._default_flag(raw.get("is_active") if raw.get("is_active") is not None else 1)
        if "notes" in raw:
            data["notes"] = str(raw.get("notes") or "").strip()
        if "stages_json" in raw:
            stages_json = raw.get("stages_json")
            if isinstance(stages_json, list):
                stage_names = [str(x).strip() for x in stages_json if str(x).strip()]
                data["stages_json"] = json.dumps(stage_names, ensure_ascii=False)
            elif isinstance(stages_json, str):
                try:
                    parsed = json.loads(stages_json or "[]")
                    if isinstance(parsed, list):
                        stage_names = [str(x).strip() for x in parsed if str(x).strip()]
                        data["stages_json"] = json.dumps(stage_names, ensure_ascii=False)
                except json.JSONDecodeError:
                    pass
        return data

    def _default_flag(self, value):
        if isinstance(value, str):
            return 1 if value.strip().lower() in {"1", "true", "yes", "on", "y"} else 0
        return 1 if bool(value) else 0

    def _normalize_document_template_payload(self, payload, for_update=False):
        raw = payload or {}
        data = {}

        if not for_update or "template_type" in raw:
            template_type = self._normalize_document_template_type(raw.get("template_type"))
            if not template_type:
                raise ValueError("template_type must be estimate/contract/change_order")
            data["template_type"] = template_type

        if not for_update or "project_type" in raw:
            project_type = self._normalize_project_type(raw.get("project_type"))
            if not project_type:
                raise ValueError("project_type must be custom_furniture/bathroom_remodel/kitchen_remodel/full_remodel/other")
            data["project_type"] = project_type

        if not for_update or "name" in raw:
            name = str(raw.get("name") or "").strip()
            if not name:
                raise ValueError("name is required")
            data["name"] = name

        if not for_update or "is_default" in raw:
            data["is_default"] = self._default_flag(raw.get("is_default"))

        for text_field in ["title_text", "intro_text", "note_text", "terms_text", "footer_text"]:
            if text_field in raw:
                value = raw.get(text_field)
                data[text_field] = str(value).strip() if value is not None else ""

        return data

    def _set_document_template_default(self, cur, template_id, template_type, project_type):
        ts = now_ts()
        cur.execute(
            """
            UPDATE document_templates
            SET is_default=0, updated_at=?
            WHERE template_type=? AND project_type=? AND id<>?
            """,
            (ts, template_type, project_type, template_id),
        )
        cur.execute(
            "UPDATE document_templates SET is_default=1, updated_at=? WHERE id=?",
            (ts, template_id),
        )

    def _set_stage_template_default(self, cur, template_id, project_type):
        ts = now_ts()
        cur.execute(
            "UPDATE project_stage_templates SET is_default=0, updated_at=? WHERE project_type=? AND id<>?",
            (ts, project_type, template_id),
        )
        cur.execute(
            "UPDATE project_stage_templates SET is_default=1, is_active=1, updated_at=? WHERE id=?",
            (ts, template_id),
        )

    def _ensure_stage_template_items(self, cur, template_id):
        cur.execute("SELECT COUNT(1) c FROM project_stage_template_items WHERE template_id=?", (template_id,))
        if int((cur.fetchone() or {"c": 0})["c"] or 0) > 0:
            return
        cur.execute("SELECT stages_json FROM project_stage_templates WHERE id=?", (template_id,))
        row = cur.fetchone()
        stage_names = []
        if row:
            try:
                parsed = json.loads(row["stages_json"] or "[]")
                if isinstance(parsed, list):
                    stage_names = [str(x).strip() for x in parsed if str(x).strip()]
            except json.JSONDecodeError:
                stage_names = []
        if not stage_names:
            stage_names = list(DEFAULT_PROJECT_STAGES)
        ts = now_ts()
        for idx, step_name in enumerate(stage_names, start=1):
            cur.execute(
                """
                INSERT INTO project_stage_template_items(template_id,step_name,step_order,is_active,created_at,updated_at)
                VALUES (?,?,?,?,?,?)
                """,
                (template_id, step_name, idx, 1, ts, ts),
            )

    def _get_stage_template_items(self, cur, template_id):
        self._ensure_stage_template_items(cur, template_id)
        cur.execute(
            """
            SELECT id,template_id,step_name,step_order,is_active,created_at,updated_at
            FROM project_stage_template_items
            WHERE template_id=?
            ORDER BY step_order ASC,id ASC
            """,
            (template_id,),
        )
        return [row_to_dict(x) for x in cur.fetchall()]

    def _stage_template_stage_names(self, cur, template_id):
        items = self._get_stage_template_items(cur, template_id)
        active_items = [it for it in items if int(it.get("is_active") or 0) == 1]
        names = [str(it.get("step_name") or "").strip() for it in active_items if str(it.get("step_name") or "").strip()]
        return names

    def _estimate_custom_payment_stage_names(self, cur, estimate_id):
        if not estimate_id:
            return []
        cur.execute(
            """
            SELECT custom_stage_name
            FROM estimate_payment_milestones
            WHERE estimate_id=?
            ORDER BY sort_order ASC,id ASC
            """,
            (estimate_id,),
        )
        names = []
        seen = set()
        for row in cur.fetchall():
            name = str(row["custom_stage_name"] or "").strip()
            key = name.lower()
            if name and key not in seen:
                seen.add(key)
                names.append(name)
        return names

    def _append_unique_stage_names(self, stage_names, extra_names):
        names = list(stage_names or [])
        seen = {str(name or "").strip().lower() for name in names if str(name or "").strip()}
        for name in extra_names or []:
            clean = str(name or "").strip()
            key = clean.lower()
            if clean and key not in seen:
                names.append(clean)
                seen.add(key)
        return names

    def _sync_stage_template_stages_json(self, cur, template_id):
        names = self._stage_template_stage_names(cur, template_id)
        ts = now_ts()
        cur.execute(
            "UPDATE project_stage_templates SET stages_json=?, updated_at=? WHERE id=?",
            (json.dumps(names, ensure_ascii=False), ts, template_id),
        )

    def _resolve_default_stage_template_id(self, cur, project_type):
        target = self._normalize_stage_template_project_type(project_type)
        if not target:
            target = self._map_project_type_to_stage_template_type(project_type)
        cur.execute(
            """
            SELECT id FROM project_stage_templates
            WHERE project_type=? AND is_default=1 AND COALESCE(is_active,1)=1
            ORDER BY updated_at DESC,id DESC LIMIT 1
            """,
            (target,),
        )
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute(
            """
            SELECT id FROM project_stage_templates
            WHERE project_type=? AND COALESCE(is_active,1)=1
            ORDER BY updated_at DESC,id DESC LIMIT 1
            """,
            (target,),
        )
        row = cur.fetchone()
        if row:
            return row["id"]
        cur.execute(
            """
            SELECT id FROM project_stage_templates
            WHERE project_type='custom' AND COALESCE(is_active,1)=1
            ORDER BY is_default DESC,updated_at DESC,id DESC LIMIT 1
            """
        )
        row = cur.fetchone()
        return row["id"] if row else None

    def _replace_project_stages(self, cur, project_id, stage_names):
        ts = now_ts()
        cleaned = [str(x).strip() for x in (stage_names or []) if str(x).strip()]
        if not cleaned:
            cleaned = list(DEFAULT_PROJECT_STAGES)
        cur.execute("DELETE FROM project_stages WHERE project_id=?", (project_id,))
        for idx, stage_name in enumerate(cleaned, start=1):
            cur.execute(
                """
                INSERT INTO project_stages(project_id,stage_name,stage_order,status,started_at,completed_at,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (project_id, stage_name, idx, "pending", None, None, ts, ts),
            )
        self._recalc_project_progress(cur, project_id)

    def _default_template_content(self, template_type, txt):
        if template_type == "estimate":
            return {
                "title_text": txt.get("estimate_title"),
                "intro_text": "",
                "note_text": txt.get("estimate_note_default"),
                "terms_text": txt.get("contract_clause_default"),
                "footer_text": txt.get("footer_note"),
            }
        if template_type == "contract":
            return {
                "title_text": txt.get("contract_title"),
                "intro_text": txt.get("contract_intro_default"),
                "note_text": "",
                "terms_text": txt.get("contract_clause_default"),
                "footer_text": txt.get("footer_note"),
            }
        return {
            "title_text": txt.get("change_order_title"),
            "intro_text": "",
            "note_text": "",
            "terms_text": txt.get("contract_clause_default"),
            "footer_text": txt.get("footer_note"),
        }

    def _resolve_document_template(self, cur, template_type, project_type):
        tt = self._normalize_document_template_type(template_type)
        pt = self._normalize_project_type(project_type or "other") or "other"
        if not tt:
            return None
        cur.execute(
            """
            SELECT *
            FROM document_templates
            WHERE template_type=? AND project_type=? AND is_default=1
            ORDER BY updated_at DESC,id DESC
            LIMIT 1
            """,
            (tt, pt),
        )
        row = cur.fetchone()
        if row:
            return row_to_dict(row)
        cur.execute(
            """
            SELECT *
            FROM document_templates
            WHERE template_type=? AND project_type='other' AND is_default=1
            ORDER BY updated_at DESC,id DESC
            LIMIT 1
            """,
            (tt,),
        )
        row = cur.fetchone()
        return row_to_dict(row) if row else None

    def _resolve_record_project_type(
        self,
        cur,
        record_project_type=None,
        project_id=None,
        customer_id=None,
        estimate_id=None,
        contract_id=None,
    ):
        project_type = self._normalize_project_type(record_project_type)
        if project_type:
            return project_type
        if project_id:
            cur.execute("SELECT project_type,customer_id,estimate_id,contract_id FROM projects WHERE id=?", (project_id,))
            row = cur.fetchone()
            if row:
                project_type = self._normalize_project_type(row["project_type"])
                if project_type:
                    return project_type
                customer_id = customer_id or row["customer_id"]
                estimate_id = estimate_id or row["estimate_id"]
                contract_id = contract_id or row["contract_id"]
        if estimate_id:
            cur.execute("SELECT project_type,project_id,customer_id FROM estimates WHERE id=?", (estimate_id,))
            row = cur.fetchone()
            if row:
                project_type = self._normalize_project_type(row["project_type"])
                if project_type:
                    return project_type
                project_id = project_id or row["project_id"]
                customer_id = customer_id or row["customer_id"]
                if project_id:
                    cur.execute("SELECT project_type FROM projects WHERE id=?", (project_id,))
                    p = cur.fetchone()
                    if p:
                        project_type = self._normalize_project_type(p["project_type"])
                        if project_type:
                            return project_type
        if contract_id:
            cur.execute("SELECT project_type,project_id,estimate_id,customer_id FROM contracts WHERE id=?", (contract_id,))
            row = cur.fetchone()
            if row:
                project_type = self._normalize_project_type(row["project_type"])
                if project_type:
                    return project_type
                project_id = project_id or row["project_id"]
                estimate_id = estimate_id or row["estimate_id"]
                customer_id = customer_id or row["customer_id"]
                if project_id:
                    cur.execute("SELECT project_type FROM projects WHERE id=?", (project_id,))
                    p = cur.fetchone()
                    if p:
                        project_type = self._normalize_project_type(p["project_type"])
                        if project_type:
                            return project_type
                if estimate_id:
                    cur.execute("SELECT project_type FROM estimates WHERE id=?", (estimate_id,))
                    e = cur.fetchone()
                    if e:
                        project_type = self._normalize_project_type(e["project_type"])
                        if project_type:
                            return project_type
        if customer_id:
            cur.execute("SELECT inquiry_type FROM customers WHERE id=?", (customer_id,))
            row = cur.fetchone()
            if row:
                project_type = self._normalize_project_type(row["inquiry_type"])
                if project_type:
                    return project_type
        return "other"

    def _estimate_confirm_status_key(self, value):
        key = normalize_key(value or "draft")
        if key in {"confirmed", "approved", "accepted"}:
            return "confirmed"
        if key == "sent":
            return "sent"
        if key == "rejected":
            return "rejected"
        return "draft"

    def _estimate_legacy_status(self, confirm_status):
        key = self._estimate_confirm_status_key(confirm_status)
        if key == "sent":
            return "Sent"
        if key == "confirmed":
            return "Confirmed"
        if key == "rejected":
            return "Rejected"
        return "Draft"

    def _contract_sign_status_key(self, value):
        key = normalize_key(value or "draft")
        if key in {"signed", "approved", "confirmed"}:
            return "signed"
        if key == "sent":
            return "sent"
        return "draft"

    def _contract_legacy_signed_status(self, sign_status):
        key = self._contract_sign_status_key(sign_status)
        if key == "signed":
            return "Signed"
        if key == "sent":
            return "Sent"
        return "Unsigned"

    def _change_order_status_key(self, value):
        key = normalize_key(value or "draft")
        if key in {"accepted", "approved"}:
            return "approved"
        if key in {"sent"}:
            return "sent"
        if key in {"rejected"}:
            return "rejected"
        if key in {"draft"}:
            return "draft"
        return "draft"

    def _change_order_signed_status(self, status_key):
        key = self._change_order_status_key(status_key)
        if key == "approved":
            return "Signed"
        if key == "sent":
            return "Sent"
        if key == "rejected":
            return "Rejected"
        return "Pending"

    def _is_change_order_approved(self, row):
        status_key = self._change_order_status_key((row or {}).get("status"))
        if status_key == "approved":
            return True
        signed_key = normalize_key((row or {}).get("signed_status"))
        return signed_key == "signed"

    def _prepare_change_order_payload(self, cur, payload, existing=None):
        data = dict(payload or {})
        if not data.get("title"):
            data["title"] = data.get("reason") or (existing.get("title") if existing else "") or ""
        if not data.get("description"):
            data["description"] = data.get("notes") or data.get("reason") or (existing.get("description") if existing else "") or ""
        if not data.get("reason"):
            data["reason"] = data.get("description") or (existing.get("reason") if existing else "") or ""

        project_id = data.get("project_id") or (existing.get("project_id") if existing else None)
        contract_id = data.get("contract_id") or (existing.get("contract_id") if existing else None)
        customer_id = data.get("customer_id") or (existing.get("customer_id") if existing else None)

        if project_id:
            cur.execute("SELECT contract_id,customer_id FROM projects WHERE id=?", (project_id,))
            proj = cur.fetchone()
            if proj:
                contract_id = contract_id or proj["contract_id"]
                customer_id = customer_id or proj["customer_id"]
        elif contract_id:
            cur.execute("SELECT project_id,customer_id FROM contracts WHERE id=?", (contract_id,))
            c = cur.fetchone()
            if c:
                project_id = project_id or c["project_id"]
                customer_id = customer_id or c["customer_id"]

        data["project_id"] = project_id
        data["contract_id"] = contract_id
        data["customer_id"] = customer_id

        status_source = data.get("status") or data.get("signed_status") or (existing.get("status") if existing else None)
        status_key = self._change_order_status_key(status_source)
        data["status"] = status_key
        data["signed_status"] = self._change_order_signed_status(status_key)
        if status_key == "approved":
            data["approved_at"] = data.get("approved_at") or (existing.get("approved_at") if existing else None) or now_ts()
            data["signed_date"] = data.get("signed_date") or (existing.get("signed_date") if existing else None) or data["approved_at"][:10]
            data["confirmed_at"] = data.get("confirmed_at") or (existing.get("confirmed_at") if existing else None) or data["approved_at"]
            if data.get("confirmed_by") in (None, "") and existing:
                data["confirmed_by"] = existing.get("confirmed_by")
        else:
            if "approved_at" in data:
                data["approved_at"] = data.get("approved_at") or ""
            if status_key == "rejected" and not data.get("signed_date"):
                data["signed_date"] = (existing.get("signed_date") if existing else None) or now_ts()[:10]

        def to_bool_flag(v):
            if v in (None, "", False):
                return 0
            if isinstance(v, str):
                return 1 if v.strip().lower() in {"1", "true", "yes", "on", "y"} else 0
            return 1 if bool(v) else 0

        if existing is None and "impact_payment_plan" not in data:
            data["impact_payment_plan"] = 1 if self._system_setting_bool(cur, "default_change_order_affect_payment_plan", False) else 0
        if existing is None and "affect_designer_commission" not in data:
            data["affect_designer_commission"] = 1 if self._system_setting_bool(cur, "default_change_order_affect_commission", False) else 0

        if "impact_payment_plan" in data or existing is None:
            data["impact_payment_plan"] = to_bool_flag(data.get("impact_payment_plan"))
        if "affect_designer_commission" in data or existing is None:
            data["affect_designer_commission"] = to_bool_flag(data.get("affect_designer_commission"))

        if not data.get("order_no") and not (existing and existing.get("order_no")):
            data["order_no"] = self._next_change_order_no(cur)
        return data

    def _change_order_summary(self, cur, project_id=None, contract_id=None):
        if not project_id and contract_id:
            cur.execute("SELECT project_id FROM contracts WHERE id=?", (contract_id,))
            r = cur.fetchone()
            project_id = r["project_id"] if r else None
        if not contract_id and project_id:
            cur.execute("SELECT contract_id FROM projects WHERE id=?", (project_id,))
            r = cur.fetchone()
            contract_id = r["contract_id"] if r else None

        rows = []
        if project_id:
            cur.execute(
                """
                SELECT amount_delta,impact_payment_plan,affect_designer_commission,status,signed_status
                FROM change_orders
                WHERE project_id=?
                ORDER BY id ASC
                """,
                (project_id,),
            )
            rows = [row_to_dict(x) for x in cur.fetchall()]
        elif contract_id:
            cur.execute(
                """
                SELECT amount_delta,impact_payment_plan,affect_designer_commission,status,signed_status
                FROM change_orders
                WHERE contract_id=?
                ORDER BY id ASC
                """,
                (contract_id,),
            )
            rows = [row_to_dict(x) for x in cur.fetchall()]

        approved_total = 0.0
        approved_payment_plan_count = 0
        approved_commissionable = 0.0
        approved_non_commissionable = 0.0
        for item in rows:
            if not self._is_change_order_approved(item):
                continue
            amt = float(item.get("amount_delta") or 0)
            approved_total += amt
            impact_payment_plan = int(item.get("impact_payment_plan") or 0) == 1
            affect_commission = int(item.get("affect_designer_commission") or 0) == 1
            if impact_payment_plan:
                approved_payment_plan_count += 1
            if affect_commission:
                approved_commissionable += amt
            else:
                approved_non_commissionable += amt

        return {
            "project_id": project_id,
            "contract_id": contract_id,
            "approved_change_amount": round(approved_total, 2),
            "impact_payment_plan_count": approved_payment_plan_count,
            "approved_commissionable_change_amount": round(approved_commissionable, 2),
            "approved_non_commissionable_change_amount": round(approved_non_commissionable, 2),
        }

    def _enrich_resource_rows(self, cur, table, rows):
        if not rows:
            return rows
        if table == "estimates":
            estimate_ids = [int(r["id"]) for r in rows if r.get("id") is not None]
            link_map = {}
            if estimate_ids:
                ph = ",".join(["?"] * len(estimate_ids))
                cur.execute(
                    f"""
                    SELECT id,estimate_id,contract_no,project_id,customer_id,title,address,total_amount
                    FROM contracts
                    WHERE estimate_id IN ({ph})
                    ORDER BY id ASC
                    """,
                    tuple(estimate_ids),
                )
                for c in cur.fetchall():
                    eid = c["estimate_id"]
                    if eid not in link_map:
                        link_map[eid] = row_to_dict(c)
            customer_ids = sorted({int(r["customer_id"]) for r in rows if r.get("customer_id") not in (None, "")})
            customer_map = {}
            if customer_ids:
                ph = ",".join(["?"] * len(customer_ids))
                cur.execute(
                    f"SELECT id,name,phone,primary_address,status FROM customers WHERE id IN ({ph})",
                    tuple(customer_ids),
                )
                customer_map = {c["id"]: row_to_dict(c) for c in cur.fetchall()}
            for r in rows:
                confirm_status = self._estimate_confirm_status_key(r.get("confirm_status") or r.get("status"))
                r["confirm_status"] = confirm_status
                if confirm_status == "confirmed" and not r.get("confirmed_at"):
                    r["confirmed_at"] = r.get("updated_at") or r.get("created_at")
                linked = link_map.get(r.get("id"))
                if linked and linked.get("customer_id") not in (None, "") and r.get("customer_id") not in (None, ""):
                    if int(linked.get("customer_id")) != int(r.get("customer_id")):
                        linked = None
                if not linked and r.get("contract_id"):
                    cur.execute("SELECT id,contract_no,customer_id,total_amount,title,address FROM contracts WHERE id=?", (r.get("contract_id"),))
                    c = cur.fetchone()
                    linked = row_to_dict(c) if c else None
                    if linked and linked.get("customer_id") not in (None, "") and r.get("customer_id") not in (None, ""):
                        if int(linked.get("customer_id")) != int(r.get("customer_id")):
                            linked = None
                r["linked_contract_id"] = linked["id"] if linked else None
                r["linked_contract_no"] = linked["contract_no"] if linked else None
                r["linked_contract_customer_id"] = linked["customer_id"] if linked else None
                r["linked_contract_total_amount"] = linked["total_amount"] if linked else None
                r["linked_contract_title"] = linked["title"] if linked else None
                r["linked_contract_address"] = linked["address"] if linked else None
                if linked and not r.get("contract_id"):
                    r["contract_id"] = linked["id"]
                customer = customer_map.get(r.get("customer_id"))
                r["customer_name"] = (customer or {}).get("name")
                r["customer_phone"] = (customer or {}).get("phone")
                r["customer_address"] = r.get("address") or ((customer or {}).get("primary_address"))
                r["public_url"] = self._public_quote_url(r.get("public_token")) if r.get("public_token") else ""
                r["linked_contract_mismatch"] = False
                source_type = "lead" if normalize_key((customer or {}).get("status") or "") in {
                    "lead",
                    "measuring",
                    "quoting",
                    "new_lead",
                    "contacted",
                    "site_visit_booked",
                    "quoted",
                } else "customer"
                r["source_type"] = source_type
                r["contract_generated"] = "generated" if r.get("linked_contract_id") else "ungenerated"
            return rows

        if table == "projects":
            customer_ids = sorted({int(r["customer_id"]) for r in rows if r.get("customer_id") not in (None, "")})
            customer_map = {}
            if customer_ids:
                ph = ",".join(["?"] * len(customer_ids))
                cur.execute(f"SELECT id,name,phone FROM customers WHERE id IN ({ph})", tuple(customer_ids))
                customer_map = {c["id"]: row_to_dict(c) for c in cur.fetchall()}
            for r in rows:
                customer = customer_map.get(r.get("customer_id"))
                r["customer_name"] = (customer or {}).get("name")
                r["customer_phone"] = (customer or {}).get("phone")
                r["is_completed"] = self._is_project_completed(r.get("status"), r.get("progress_pct"))
                summary = self._recalc_designer_commission_for_project(cur, r.get("id")) if r.get("designer_id") else None
                if summary:
                    r["commission_status"] = summary.get("status") or "ungenerated"
                    r["commission_amount"] = summary.get("commission_amount") or 0
                    r["commission_base_amount"] = summary.get("commission_calc_base_amount") or 0
                    r["commission_base"] = summary.get("commission_base") or "base_contract_only"
                    r["commission_type"] = summary.get("commission_type") or "percent"
                    r["commission_eligible"] = bool(summary.get("eligible"))
                    if summary.get("status") == "settled":
                        r["commission_settlement_reason"] = "已结算"
                    elif summary.get("eligible"):
                        r["commission_settlement_reason"] = "满足结算条件"
                    elif not summary.get("acceptance_done"):
                        r["commission_settlement_reason"] = "验收未完成"
                    elif not summary.get("contract_paid"):
                        r["commission_settlement_reason"] = "主合同未收清"
                    else:
                        r["commission_settlement_reason"] = "未达到结算条件"
                else:
                    r["commission_status"] = "ungenerated"
                    r["commission_amount"] = 0
                    r["commission_base_amount"] = 0
                    r["commission_eligible"] = False
                    r["commission_settlement_reason"] = "未设置设计师"
            return rows

        if table == "designer_applications":
            reviewer_ids = sorted({int(r["reviewed_by"]) for r in rows if r.get("reviewed_by") not in (None, "")})
            designer_ids = sorted({int(r["designer_id"]) for r in rows if r.get("designer_id") not in (None, "")})
            user_ids = sorted({int(r["user_id"]) for r in rows if r.get("user_id") not in (None, "")})
            reviewer_map = {}
            designer_map = {}
            user_map = {}
            if reviewer_ids:
                ph = ",".join(["?"] * len(reviewer_ids))
                cur.execute(f"SELECT id,username FROM users WHERE id IN ({ph})", tuple(reviewer_ids))
                reviewer_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            if designer_ids:
                ph = ",".join(["?"] * len(designer_ids))
                cur.execute(f"SELECT id,name,user_id FROM designers WHERE id IN ({ph})", tuple(designer_ids))
                designer_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            if user_ids:
                ph = ",".join(["?"] * len(user_ids))
                cur.execute(f"SELECT id,username FROM users WHERE id IN ({ph})", tuple(user_ids))
                user_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            for r in rows:
                r["status"] = self._designer_app_status_key(r.get("status"))
                reviewer = reviewer_map.get(r.get("reviewed_by")) or {}
                r["reviewed_by_name"] = reviewer.get("username")
                drow = designer_map.get(r.get("designer_id")) or {}
                r["designer_name"] = drow.get("name")
                if not r.get("user_id") and drow.get("user_id"):
                    r["user_id"] = drow.get("user_id")
                urow = user_map.get(r.get("user_id")) or {}
                r["user_username"] = urow.get("username")
                if not r.get("source_channel"):
                    r["source_channel"] = "website"
            return rows

        if table == "designers":
            user_ids = sorted({int(r["user_id"]) for r in rows if r.get("user_id") not in (None, "")})
            app_ids = sorted({int(r["application_id"]) for r in rows if r.get("application_id") not in (None, "")})
            user_map = {}
            app_map = {}
            if user_ids:
                ph = ",".join(["?"] * len(user_ids))
                cur.execute(f"SELECT id,username,modules_json,linked_designer_id FROM users WHERE id IN ({ph})", tuple(user_ids))
                user_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            if app_ids:
                ph = ",".join(["?"] * len(app_ids))
                cur.execute(f"SELECT id,status,reviewed_at FROM designer_applications WHERE id IN ({ph})", tuple(app_ids))
                app_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            for r in rows:
                urow = user_map.get(r.get("user_id")) or {}
                r["user_username"] = urow.get("username")
                try:
                    parsed_modules = json.loads(urow.get("modules_json") or "[]")
                except json.JSONDecodeError:
                    parsed_modules = []
                r["permission_modules"] = self._designer_modules_from_payload(parsed_modules)
                app = app_map.get(r.get("application_id")) or {}
                r["application_status"] = app.get("status")
                r["application_reviewed_at"] = app.get("reviewed_at")
                if not r.get("status"):
                    r["status"] = "active"
            return rows

        if table == "designer_assignments":
            designer_ids = sorted({int(r["designer_id"]) for r in rows if r.get("designer_id") not in (None, "")})
            assigner_ids = sorted({int(r["assigned_by"]) for r in rows if r.get("assigned_by") not in (None, "")})
            lead_ids = sorted(
                {
                    int(r["source_id"])
                    for r in rows
                    if r.get("source_id") not in (None, "")
                    and normalize_key(r.get("source_type") or "") == "lead"
                }
            )
            project_ids = sorted(
                {
                    int(r["source_id"])
                    for r in rows
                    if r.get("source_id") not in (None, "")
                    and normalize_key(r.get("source_type") or "") == "project"
                }
            )
            designer_map = {}
            assigner_map = {}
            lead_map = {}
            project_map = {}
            if designer_ids:
                ph = ",".join(["?"] * len(designer_ids))
                cur.execute(f"SELECT id,name,user_id,status FROM designers WHERE id IN ({ph})", tuple(designer_ids))
                designer_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            if assigner_ids:
                ph = ",".join(["?"] * len(assigner_ids))
                cur.execute(f"SELECT id,username FROM users WHERE id IN ({ph})", tuple(assigner_ids))
                assigner_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            if lead_ids:
                ph = ",".join(["?"] * len(lead_ids))
                cur.execute(f"SELECT id,name,phone,status FROM customers WHERE id IN ({ph})", tuple(lead_ids))
                lead_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            if project_ids:
                ph = ",".join(["?"] * len(project_ids))
                cur.execute(f"SELECT id,name,customer_id,status,progress_pct FROM projects WHERE id IN ({ph})", tuple(project_ids))
                project_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            for r in rows:
                source_type = normalize_key(r.get("source_type") or "")
                if source_type not in DESIGNER_ASSIGNMENT_SOURCE_TYPES:
                    source_type = "lead"
                assignment_type = normalize_key(r.get("assignment_type") or "")
                if assignment_type not in DESIGNER_ASSIGNMENT_TYPE_SET:
                    assignment_type = "design_support"
                status_key = self._designer_assignment_status_key(r.get("status") or "new")
                r["source_type"] = source_type
                r["assignment_type"] = assignment_type
                r["status"] = status_key
                drow = designer_map.get(r.get("designer_id")) or {}
                r["designer_name"] = drow.get("name")
                r["designer_user_id"] = drow.get("user_id")
                r["designer_status"] = drow.get("status")
                arow = assigner_map.get(r.get("assigned_by")) or {}
                r["assigned_by_name"] = arow.get("username")
                source_name = None
                source_meta = None
                if source_type == "lead":
                    lrow = lead_map.get(r.get("source_id")) or {}
                    source_name = lrow.get("name")
                    source_meta = lrow.get("phone")
                    r["lead_status"] = lrow.get("status")
                elif source_type == "project":
                    prow = project_map.get(r.get("source_id")) or {}
                    source_name = prow.get("name")
                    source_meta = prow.get("status")
                    r["project_progress_pct"] = prow.get("progress_pct")
                r["source_name"] = source_name
                r["source_meta"] = source_meta
            return rows

        if table == "project_stage_templates":
            template_ids = [int(r["id"]) for r in rows if r.get("id") not in (None, "")]
            item_count_map = {}
            ref_count_map = {}
            if template_ids:
                ph = ",".join(["?"] * len(template_ids))
                cur.execute(
                    f"""
                    SELECT template_id,COUNT(1) c
                    FROM project_stage_template_items
                    WHERE template_id IN ({ph}) AND COALESCE(is_active,1)=1
                    GROUP BY template_id
                    """,
                    tuple(template_ids),
                )
                item_count_map = {x["template_id"]: int(x["c"] or 0) for x in cur.fetchall()}
                cur.execute(
                    f"""
                    SELECT stage_template_id,COUNT(1) c
                    FROM projects
                    WHERE stage_template_id IN ({ph})
                    GROUP BY stage_template_id
                    """,
                    tuple(template_ids),
                )
                ref_count_map = {x["stage_template_id"]: int(x["c"] or 0) for x in cur.fetchall()}
            for r in rows:
                r["project_type"] = self._normalize_stage_template_project_type(r.get("project_type")) or "custom"
                r["is_default"] = int(r.get("is_default") or 0)
                r["is_active"] = int(r.get("is_active") if r.get("is_active") is not None else 1)
                if not r.get("stages_json"):
                    r["stages_json"] = "[]"
                r["step_count"] = item_count_map.get(r.get("id"), 0)
                r["linked_project_count"] = ref_count_map.get(r.get("id"), 0)
            return rows

        if table == "project_stage_template_items":
            template_ids = sorted({int(r["template_id"]) for r in rows if r.get("template_id") not in (None, "")})
            template_map = {}
            if template_ids:
                ph = ",".join(["?"] * len(template_ids))
                cur.execute(f"SELECT id,name FROM project_stage_templates WHERE id IN ({ph})", tuple(template_ids))
                template_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            for r in rows:
                r["is_active"] = int(r.get("is_active") if r.get("is_active") is not None else 1)
                trow = template_map.get(r.get("template_id")) or {}
                r["template_name"] = trow.get("name")
            return rows

        if table == "contracts":
            contract_ids = [int(r["id"]) for r in rows if r.get("id") is not None]
            project_map = {}
            if contract_ids:
                ph = ",".join(["?"] * len(contract_ids))
                cur.execute(
                    f"""
                    SELECT id,contract_id,name,address,status
                    FROM projects
                    WHERE contract_id IN ({ph})
                    ORDER BY id ASC
                    """,
                    tuple(contract_ids),
                )
                for p in cur.fetchall():
                    cid = p["contract_id"]
                    if cid not in project_map:
                        project_map[cid] = row_to_dict(p)
            estimate_ids = sorted({int(r["estimate_id"]) for r in rows if r.get("estimate_id") not in (None, "")})
            estimate_map = {}
            if estimate_ids:
                ph = ",".join(["?"] * len(estimate_ids))
                cur.execute(f"SELECT id,title,total_amount FROM estimates WHERE id IN ({ph})", tuple(estimate_ids))
                estimate_map = {e["id"]: row_to_dict(e) for e in cur.fetchall()}
            for r in rows:
                sign_status = self._contract_sign_status_key(r.get("sign_status") or r.get("signed_status"))
                r["sign_status"] = sign_status
                r["signed_status"] = self._contract_legacy_signed_status(sign_status)
                if sign_status == "signed" and not r.get("signed_at"):
                    r["signed_at"] = r.get("signed_date") or r.get("updated_at") or r.get("created_at")
                if r.get("signed_at") and not r.get("signed_date"):
                    r["signed_date"] = str(r.get("signed_at"))[:10]
                linked = project_map.get(r.get("id"))
                linked_project_id = r.get("project_id") or (linked["id"] if linked else None)
                r["linked_project_id"] = linked_project_id
                r["linked_project_name"] = linked["name"] if linked else None
                est = estimate_map.get(r.get("estimate_id"))
                r["source_estimate_title"] = est["title"] if est else None
                r["source_estimate_total_amount"] = est["total_amount"] if est else None
                summary = self._change_order_summary(cur, project_id=linked_project_id, contract_id=r.get("id"))
                base_contract_amount = float(r.get("total_amount") or 0)
                approved_change_amount = float(summary.get("approved_change_amount") or 0)
                r["base_contract_amount"] = round(base_contract_amount, 2)
                r["approved_change_amount"] = round(approved_change_amount, 2)
                r["current_contract_total"] = round(base_contract_amount + approved_change_amount, 2)
                r["change_orders_affect_payment_plan_count"] = int(summary.get("impact_payment_plan_count") or 0)
                r["approved_commissionable_change_amount"] = float(summary.get("approved_commissionable_change_amount") or 0)
                r["approved_non_commissionable_change_amount"] = float(summary.get("approved_non_commissionable_change_amount") or 0)
            return rows

        if table == "vendors":
            vendor_ids = [int(r["id"]) for r in rows if r.get("id") not in (None, "")]
            total_map = {}
            current_year = datetime.now().year
            if vendor_ids:
                ph = ",".join(["?"] * len(vendor_ids))
                cur.execute(
                    f"""
                    SELECT vendor_id,COALESCE(SUM(amount),0) total_paid
                    FROM payments
                    WHERE vendor_id IN ({ph}) AND date LIKE ?
                    GROUP BY vendor_id
                    """,
                    tuple(vendor_ids) + (f"{current_year}-%",),
                )
                total_map = {x["vendor_id"]: float(x["total_paid"] or 0) for x in cur.fetchall()}
            for r in rows:
                r["type"] = self._vendor_type_key(r.get("type"))
                r["1099_required"] = 1 if int(r.get("1099_required") or 0) == 1 or r["type"] == "1099" else 0
                r["w9_received"] = 1 if int(r.get("w9_received") or 0) == 1 else 0
                total_paid = float(total_map.get(r.get("id"), 0) or 0)
                r["total_paid_this_year"] = round(total_paid, 2)
                r["over_600"] = 1 if total_paid >= 600 else 0
            return rows

        if table == "bills":
            vendor_ids = sorted({int(r["vendor_id"]) for r in rows if r.get("vendor_id") not in (None, "")})
            project_ids = sorted({int(r["project_id"]) for r in rows if r.get("project_id") not in (None, "")})
            vendor_map = {}
            project_map = {}
            if vendor_ids:
                ph = ",".join(["?"] * len(vendor_ids))
                cur.execute(f'SELECT id,name,type,tax_id,"1099_required",w9_received FROM vendors WHERE id IN ({ph})', tuple(vendor_ids))
                vendor_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            if project_ids:
                ph = ",".join(["?"] * len(project_ids))
                cur.execute(f"SELECT id,name FROM projects WHERE id IN ({ph})", tuple(project_ids))
                project_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            for r in rows:
                v = vendor_map.get(r.get("vendor_id")) or {}
                p = project_map.get(r.get("project_id")) or {}
                amount = float(r.get("amount") or 0)
                paid_amount = float(r.get("paid_amount") or 0)
                r["vendor_name"] = v.get("name")
                r["vendor_type"] = self._vendor_type_key(v.get("type"))
                r["project_name"] = p.get("name")
                r["open_amount"] = round(max(amount - paid_amount, 0), 2)
            self._attach_entity_file_meta(cur, "bill", rows)
            return rows

        if table == "payments":
            vendor_ids = sorted({int(r["vendor_id"]) for r in rows if r.get("vendor_id") not in (None, "")})
            project_ids = sorted({int(r["project_id"]) for r in rows if r.get("project_id") not in (None, "")})
            bill_ids = sorted({int(r["bill_id"]) for r in rows if r.get("bill_id") not in (None, "")})
            vendor_map = {}
            project_map = {}
            bill_map = {}
            if vendor_ids:
                ph = ",".join(["?"] * len(vendor_ids))
                cur.execute(f"SELECT id,name,type FROM vendors WHERE id IN ({ph})", tuple(vendor_ids))
                vendor_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            if project_ids:
                ph = ",".join(["?"] * len(project_ids))
                cur.execute(f"SELECT id,name FROM projects WHERE id IN ({ph})", tuple(project_ids))
                project_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            if bill_ids:
                ph = ",".join(["?"] * len(bill_ids))
                cur.execute(f"SELECT id,bill_no FROM bills WHERE id IN ({ph})", tuple(bill_ids))
                bill_map = {x["id"]: row_to_dict(x) for x in cur.fetchall()}
            for r in rows:
                v = vendor_map.get(r.get("vendor_id")) or {}
                p = project_map.get(r.get("project_id")) or {}
                b = bill_map.get(r.get("bill_id")) or {}
                r["vendor_name"] = v.get("name")
                r["vendor_type"] = self._vendor_type_key(v.get("type"))
                r["project_name"] = p.get("name")
                r["bill_no"] = b.get("bill_no")
            self._attach_entity_file_meta(cur, "payment", rows)
            return rows

        if table == "designer_commissions":
            project_ids = sorted({int(r["project_id"]) for r in rows if r.get("project_id") not in (None, "")})
            project_map = {}
            if project_ids:
                ph = ",".join(["?"] * len(project_ids))
                cur.execute(
                    f"""
                    SELECT p.id,p.name,p.address,p.status,p.progress_pct,p.manager,p.customer_id,c.name AS customer_name
                    FROM projects p
                    LEFT JOIN customers c ON c.id=p.customer_id
                    WHERE p.id IN ({ph})
                    """,
                    tuple(project_ids),
                )
                project_map = {p["id"]: row_to_dict(p) for p in cur.fetchall()}
            for r in rows:
                project = project_map.get(r.get("project_id")) or {}
                r["project_name"] = project.get("name")
                r["project_address"] = project.get("address")
                r["project_status"] = project.get("status")
                r["project_progress_pct"] = project.get("progress_pct")
                r["project_manager"] = project.get("manager")
                r["customer_name"] = project.get("customer_name")
                r["project_completed"] = self._is_project_completed(project.get("status"), project.get("progress_pct"))
                summary = self._recalc_designer_commission_for_project(cur, r.get("project_id"))
                if summary:
                    r["base_contract_amount"] = summary.get("base_contract_amount") or 0
                    r["approved_change_commissionable_amount"] = summary.get("approved_change_commissionable_amount") or 0
                    r["approved_change_non_commissionable_amount"] = summary.get("approved_change_non_commissionable_amount") or 0
                    r["commission_calc_base_amount"] = summary.get("commission_calc_base_amount") or 0
                    r["commission_amount"] = summary.get("commission_amount") or 0
                    r["status"] = summary.get("status") or r.get("status")
                    r["eligible"] = bool(summary.get("eligible"))
                    r["acceptance_done"] = bool(summary.get("acceptance_done"))
                    r["contract_paid"] = bool(summary.get("contract_paid"))
                    if r["status"] == "settled":
                        r["settlement_reason"] = "已结算"
                    elif r["eligible"]:
                        r["settlement_reason"] = "满足结算条件"
                    elif not r["acceptance_done"]:
                        r["settlement_reason"] = "验收未完成"
                    elif not r["contract_paid"]:
                        r["settlement_reason"] = "主合同未收清"
                    else:
                        r["settlement_reason"] = "未达到结算条件"
                else:
                    r["approved_change_commissionable_amount"] = 0
                    r["approved_change_non_commissionable_amount"] = 0
                    r["commission_calc_base_amount"] = 0
                    r["settlement_reason"] = "未生成"
            return rows

        if table == "change_orders":
            project_ids = sorted({int(r["project_id"]) for r in rows if r.get("project_id") not in (None, "")})
            contract_ids = sorted({int(r["contract_id"]) for r in rows if r.get("contract_id") not in (None, "")})
            customer_ids = sorted({int(r["customer_id"]) for r in rows if r.get("customer_id") not in (None, "")})

            project_map = {}
            if project_ids:
                ph = ",".join(["?"] * len(project_ids))
                cur.execute(f"SELECT id,name,address,contract_id,customer_id FROM projects WHERE id IN ({ph})", tuple(project_ids))
                project_map = {p["id"]: row_to_dict(p) for p in cur.fetchall()}

            contract_map = {}
            if contract_ids:
                ph = ",".join(["?"] * len(contract_ids))
                cur.execute(f"SELECT id,contract_no,title,total_amount FROM contracts WHERE id IN ({ph})", tuple(contract_ids))
                contract_map = {c["id"]: row_to_dict(c) for c in cur.fetchall()}

            customer_map = {}
            if customer_ids:
                ph = ",".join(["?"] * len(customer_ids))
                cur.execute(f"SELECT id,name,phone FROM customers WHERE id IN ({ph})", tuple(customer_ids))
                customer_map = {c["id"]: row_to_dict(c) for c in cur.fetchall()}

            for r in rows:
                project = project_map.get(r.get("project_id"))
                if project:
                    r["project_name"] = project.get("name")
                    r["project_address"] = project.get("address")
                    if not r.get("contract_id"):
                        r["contract_id"] = project.get("contract_id")
                    if not r.get("customer_id"):
                        r["customer_id"] = project.get("customer_id")
                contract = contract_map.get(r.get("contract_id"))
                if contract:
                    r["contract_no"] = contract.get("contract_no")
                    r["contract_title"] = contract.get("title")
                customer = customer_map.get(r.get("customer_id"))
                if customer:
                    r["customer_name"] = customer.get("name")
                    r["customer_phone"] = customer.get("phone")

                status_key = self._change_order_status_key(r.get("status") or r.get("signed_status"))
                r["status"] = status_key
                r["signed_status"] = self._change_order_signed_status(status_key)
                if status_key == "approved" and not r.get("approved_at"):
                    r["approved_at"] = r.get("signed_date") or r.get("updated_at") or r.get("created_at")
                if not r.get("title"):
                    r["title"] = r.get("reason") or f"变更单#{r.get('id')}"
                if not r.get("description"):
                    r["description"] = r.get("notes") or r.get("reason") or ""
                r["impact_payment_plan"] = int(r.get("impact_payment_plan") or 0)
                r["affect_designer_commission"] = int(r.get("affect_designer_commission") or 0)
                if not r.get("order_no"):
                    r["order_no"] = f"CO-{int(r.get('id') or 0):05d}"
                r["is_approved"] = status_key == "approved"
            return rows

        return rows

    def _estimate_generate_contract(self, path, user):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden"}, 403)
        if not self._has_module(user, "contracts"):
            return self._json_response({"error": "Forbidden: contracts"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "estimates" or parts[3] != "generate-contract":
            return self._json_response({"error": "Not found"}, 404)
        try:
            estimate_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid estimate id"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT e.*, c.primary_address AS customer_address
            FROM estimates e
            LEFT JOIN customers c ON c.id=e.customer_id
            WHERE e.id=?
            """,
            (estimate_id,),
        )
        estimate = cur.fetchone()
        if not estimate:
            conn.close()
            return self._json_response({"error": "Estimate not found"}, 404)
        if not estimate["customer_id"]:
            conn.close()
            return self._json_response({"error": "Estimate must be linked to a customer before generating a contract"}, 400)
        confirm_status = self._estimate_confirm_status_key(estimate["confirm_status"] or estimate["status"])
        if confirm_status != "confirmed":
            conn.close()
            return self._json_response({"error": "Estimate must be confirmed before generating a contract"}, 400)
        if user.get("role") == "designer" and estimate["project_id"] and self._forbid_if_no_project_access(cur, user, estimate["project_id"]):
            conn.close()
            return

        existed = None
        if estimate["contract_id"]:
            cur.execute("SELECT * FROM contracts WHERE id=?", (estimate["contract_id"],))
            existed = cur.fetchone()
            if existed and existed["customer_id"] and estimate["customer_id"] and int(existed["customer_id"]) != int(estimate["customer_id"]):
                existed = None
        if not existed:
            cur.execute("SELECT * FROM contracts WHERE estimate_id=? ORDER BY id ASC LIMIT 1", (estimate_id,))
            existed = cur.fetchone()
            if existed and existed["customer_id"] and estimate["customer_id"] and int(existed["customer_id"]) != int(estimate["customer_id"]):
                existed = None
        if existed:
            ts_existing = now_ts()
            if not estimate["contract_id"]:
                cur.execute("UPDATE estimates SET contract_id=?, updated_at=? WHERE id=?", (existed["id"], ts_existing, estimate_id))
            conn.commit()
            row = row_to_dict(existed)
            self._enrich_resource_rows(cur, "contracts", [row])
            conn.close()
            return self._json_response({"created": False, "contract": row})

        project_id = estimate["project_id"]
        address = ""
        if project_id:
            cur.execute("SELECT address FROM projects WHERE id=?", (project_id,))
            pr = cur.fetchone()
            address = (pr["address"] if pr else "") or ""
        if not address:
            address = (estimate["address"] or "").strip()
        if not address:
            address = estimate["customer_address"] or ""
        title = (estimate["title"] or "").strip() or f"报价#{estimate_id}"
        total_amount = estimate["total_amount"] if estimate["total_amount"] not in (None, "") else (estimate["subtotal"] or 0)
        ts = now_ts()
        contract_no = self._next_contract_no(cur)
        cur.execute(
            """
            INSERT INTO contracts(
                customer_id,project_id,estimate_id,title,address,contract_no,total_amount,payment_plan_json,
                signed_status,signed_date,sign_status,signed_at,signed_by,sign_note,attachment_url,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                estimate["customer_id"],
                project_id,
                estimate_id,
                title,
                address,
                contract_no,
                total_amount or 0,
                "[]",
                "Unsigned",
                None,
                "draft",
                None,
                None,
                "",
                "",
                ts,
                ts,
            ),
        )
        contract_id = cur.lastrowid
        self._copy_estimate_payment_milestones_to_contract(cur, estimate_id, contract_id)
        cur.execute("UPDATE estimates SET contract_id=?, updated_at=? WHERE id=?", (contract_id, ts, estimate_id))
        if project_id:
            cur.execute(
                "UPDATE projects SET contract_id=COALESCE(contract_id,?), estimate_id=COALESCE(estimate_id,?), updated_at=? WHERE id=?",
                (contract_id, estimate_id, ts, project_id),
            )
            self._recalc_designer_commission_for_project(cur, project_id)
        self._evaluate_contract_payment_milestones(cur, contract_id=contract_id, project_id=project_id)
        conn.commit()
        cur.execute("SELECT * FROM contracts WHERE id=?", (contract_id,))
        row = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "contracts", [row])
        conn.close()
        return self._json_response({"created": True, "contract": row}, 201)

    def _copy_estimate_payment_milestones_to_contract(self, cur, estimate_id, contract_id):
        cur.execute("SELECT COUNT(1) c FROM contract_payment_milestones WHERE contract_id=?", (contract_id,))
        if (cur.fetchone() or {"c": 0})["c"]:
            return
        cur.execute(
            """
            SELECT epm.*, psti.step_name AS stage_step_name
            FROM estimate_payment_milestones epm
            LEFT JOIN project_stage_template_items psti ON psti.id=epm.trigger_stage_template_item_id
            WHERE epm.estimate_id=?
            ORDER BY epm.sort_order, epm.id
            """,
            (estimate_id,),
        )
        rows = cur.fetchall()
        if not rows:
            return
        ts = now_ts()
        for idx, m in enumerate(rows, start=1):
            amount_pct = float(m["amount_pct"] or 0)
            if amount_pct <= 0:
                continue
            stage_name = (m["custom_stage_name"] or m["stage_step_name"] or "").strip()
            is_holdback = int(m["is_holdback"] or 0) == 1
            trigger_type = "progress_percent" if is_holdback else ("stage_done" if stage_name else "contract_signed")
            trigger_progress = 100 if is_holdback else None
            name = (m["name"] or "").strip() or ("Holdback" if is_holdback else f"Payment {idx}")
            note_parts = []
            if stage_name:
                note_parts.append(f"From estimate stage: {stage_name}")
            if is_holdback:
                note_parts.append("Holdback copied from estimate payment schedule")
            note = " | ".join(note_parts)
            cur.execute(
                """
                INSERT INTO contract_payment_milestones(
                    contract_id,name,node_type,trigger_type,trigger_stage,trigger_progress,amount_type,amount_value,
                    triggered,triggered_at,reminded,reminded_at,paid,paid_at,note,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    contract_id,
                    name,
                    "holdback" if is_holdback else "payment",
                    trigger_type,
                    stage_name or None,
                    trigger_progress,
                    "percent",
                    amount_pct,
                    0,
                    None,
                    0,
                    None,
                    0,
                    None,
                    note,
                    ts,
                    ts,
                ),
            )

    def _contract_generate_project(self, path, user):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden"}, 403)
        if not self._has_module(user, "projects"):
            return self._json_response({"error": "Forbidden: projects"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "contracts" or parts[3] != "generate-project":
            return self._json_response({"error": "Not found"}, 404)
        try:
            contract_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid contract id"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT ct.*, c.primary_address AS customer_address, e.title AS estimate_title, e.customer_id AS estimate_customer_id
            FROM contracts ct
            LEFT JOIN customers c ON c.id=ct.customer_id
            LEFT JOIN estimates e ON e.id=ct.estimate_id
            WHERE ct.id=?
            """,
            (contract_id,),
        )
        contract = cur.fetchone()
        if not contract:
            conn.close()
            return self._json_response({"error": "Contract not found"}, 404)

        existed = None
        if contract["project_id"]:
            cur.execute("SELECT * FROM projects WHERE id=?", (contract["project_id"],))
            existed = cur.fetchone()
        if not existed:
            cur.execute("SELECT * FROM projects WHERE contract_id=? ORDER BY id ASC LIMIT 1", (contract_id,))
            existed = cur.fetchone()
        if existed:
            project = row_to_dict(existed)
            ts = now_ts()
            cur.execute("UPDATE contracts SET project_id=COALESCE(project_id,?), updated_at=? WHERE id=?", (project["id"], ts, contract_id))
            if contract["estimate_id"]:
                cur.execute(
                    "UPDATE estimates SET project_id=COALESCE(project_id,?), contract_id=COALESCE(contract_id,?), updated_at=? WHERE id=?",
                    (project["id"], contract_id, ts, contract["estimate_id"]),
                )
            conn.commit()
            conn.close()
            return self._json_response({"created": False, "project": project})

        sign_status = self._contract_sign_status_key(contract["sign_status"] or contract["signed_status"])
        if sign_status != "signed":
            conn.close()
            return self._json_response({"error": "Contract must be signed before generating a project"}, 400)

        ts = now_ts()
        customer_id = contract["customer_id"] or contract["estimate_customer_id"]
        estimate_id = contract["estimate_id"]
        project_type = self._normalize_project_type(contract.get("project_type")) or "other"
        stage_template_id = self._resolve_default_stage_template_id(cur, project_type)
        name = (contract["title"] or contract["estimate_title"] or contract["contract_no"] or f"项目#{contract_id}").strip()
        address = (contract["address"] or contract["customer_address"] or "").strip()
        cur.execute(
            """
            INSERT INTO projects(
                customer_id,contract_id,estimate_id,stage_template_id,project_type,name,address,status,progress_pct,start_date,
                estimated_finish_date,actual_finish_date,manager,notes,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                customer_id,
                contract_id,
                estimate_id,
                stage_template_id,
                project_type,
                name,
                address,
                "Not Started",
                0,
                None,
                None,
                None,
                "",
                "",
                ts,
                ts,
            ),
        )
        project_id = cur.lastrowid
        cur.execute("UPDATE contracts SET project_id=?, updated_at=? WHERE id=?", (project_id, ts, contract_id))
        if estimate_id:
            cur.execute("UPDATE estimates SET project_id=?, contract_id=?, updated_at=? WHERE id=?", (project_id, contract_id, ts, estimate_id))
        self._init_default_project_stages(cur, project_id)
        self._evaluate_contract_payment_milestones(cur, contract_id=contract_id, project_id=project_id)
        self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        cur.execute("SELECT * FROM projects WHERE id=?", (project_id,))
        project = row_to_dict(cur.fetchone())
        conn.close()
        return self._json_response({"created": True, "project": project}, 201)

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        if ev2_routes.handle_get(self, get_conn): return
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/quote/"):
            return self._public_quote_page(path)
        if path == "/":
            return self._serve_static_file("index.html", STATIC_DIR)
        if path == "/favicon.ico":
            return self._serve_brand_favicon()
        if path.startswith("/assets/"):
            return self._serve_static_file(unquote(path[len("/assets/") :]), ASSETS_DIR)
        if path.startswith("/static/"):
            return self._serve_static_file(unquote(path[len("/static/") :]), STATIC_DIR)
        if path.startswith("/uploads/"):
            return self._serve_static_file(unquote(path[len("/uploads/") :]), UPLOADS_DIR)

        if path.startswith("/print/"):
            user = self._require_auth()
            if not user:
                return
            query = parse_qs(parsed.query)
            if self._handle_estimate_print_view(path, user, query):
                return
            if self._handle_contract_print_view(path, user, query):
                return
            if self._handle_change_order_print_view(path, user, query):
                return
            return self._json_response({"error": "Not found"}, 404)

        if path == "/api/auth/me":
            return self._auth_me()
        if path == "/api/company/settings":
            return self._get_company_settings()

        user = self._require_auth()
        if not user:
            return

        if path.startswith("/data/documents/"):
            return self._serve_static_file(unquote(path[len("/data/documents/") :]), ARCHIVED_DOCUMENTS_DIR)

        if path == "/api/dashboard":
            if not self._require_module(user, "dashboard"):
                return
            return self._dashboard(user)
        if path == "/api/projects/progress-summary":
            if not self._require_module(user, "projects"):
                return
            return self._projects_progress_summary(user)
        if path == "/api/finance/summary":
            if not self._require_module(user, "finance"):
                return
            return self._finance_summary()
        if path == "/api/admin/users":
            if user.get("role") != "owner":
                return self._json_response({"error": "Owner only"}, 403)
            return self._list_users()

        query = parse_qs(parsed.query)

        if path == "/api/system-settings":
            if not self._require_system_settings_manage(user):
                return
            return self._system_settings_get(query)

        if path == "/api/my/designer-assignments":
            return self._my_designer_assignments_get(user)

        if path == "/api/notifications":
            if not self._require_module(user, "notifications"):
                return
            return self._notifications_get(query, user)
        if path == "/api/notifications/unread-count":
            if not self._require_module(user, "notifications"):
                return
            return self._notifications_unread_count_get(user)
        if path == "/api/files":
            return self._files_get(query, user)
        if self._handle_stage_templates_get(path, query, user):
            return

        if self._handle_project_detail(path, user):
            return
        if self._handle_project_cost_ledger_get(path, user):
            return
        if self._handle_project_progress(path, user):
            return
        if self._handle_project_logs_get(path, user):
            return
        if self._handle_contract_payment_milestones_get(path, user):
            return
        if self._handle_project_payment_reminders_get(path, user):
            return
        if self._handle_project_designer_commission_get(path, user):
            return
        if self._handle_lead_designer_assignments_get(path, user):
            return
        if self._handle_project_designer_assignments_get(path, user):
            return
        if self._handle_vendor_ledger_get(path, user):
            return
        if self._handle_vendor_payments_get(path, user):
            return
        if self._handle_customer_followups_get(path, user):
            return
        if self._handle_customer_estimates_get(path, user):
            return
        if self._handle_customer_recent_followups_get(path, user):
            return
        if self._handle_followups_due_today_get(path, user):
            return
        if self._handle_followups_stale_customers_get(path, user):
            return
        if self._handle_change_orders_get(path, query, user):
            return
        if self._handle_project_change_orders_get(path, user):
            return
        if path == "/api/documents":  # F_ARCHIVE_PATCH_APPLIED
            user = self._require_auth()
            if not user:
                return
            self._handle_documents_get(path, query, user)
            return
        if path == "/api/payment-reminders":
            if user.get("role") == "designer":
                return self._json_response({"error": "Forbidden: payment reminders"}, 403)
            if not (self._has_module(user, "dashboard") or self._has_module(user, "contracts") or self._has_module(user, "finance")):
                return self._json_response({"error": "Forbidden: payment reminders"}, 403)
            return self._payment_reminders_list(user)
        if self._handle_estimate_pdf(path, user, query):
            return
        if self._handle_contract_pdf(path, user, query):
            return
        if self._handle_change_order_pdf(path, user, query):
            return

        if path.startswith("/api/"):
            return self._resource_get(path, query, user)

        return self._json_response({"error": "Not found"}, 404)

    def do_POST(self):
        if ev2_routes.handle_post(self, get_conn): return
        path = urlparse(self.path).path
        if path.startswith("/api/public/quotes/") and (path.endswith("/confirm") or path.endswith("/reject")):
            return self._public_quote_action(path)
        if path == "/api/auth/login":
            return self._auth_login()
        if path == "/api/auth/logout":
            return self._auth_logout()
        if path == "/api/public/web-lead":
            return self._public_web_lead(urlparse(self.path).query)
        if path == "/api/leads/intake":
            return self._leads_intake(urlparse(self.path).query)
        if path == "/api/designer-applications":
            return self._designer_applications_intake(urlparse(self.path).query)
        if path == "/api/files/upload":
            user = self._require_auth()
            if not user:
                return
            return self._files_upload(user)
        if path == "/api/company/logo-upload":
            user = self._require_auth()
            if not user:
                return
            if user.get("role") != "owner":
                return self._json_response({"error": "Owner only"}, 403)
            return self._company_logo_upload(user)
        if path == "/api/system-settings":
            user = self._require_auth()
            if not user:
                return
            if not self._require_system_settings_manage(user):
                return
            return self._system_settings_post(user)
        if path == "/api/system-settings/bulk-save":
            user = self._require_auth()
            if not user:
                return
            if not self._require_system_settings_manage(user):
                return
            return self._system_settings_bulk_save(user)
        if path == "/api/notifications/mark-all-read":
            user = self._require_auth()
            if not user:
                return
            if not self._require_module(user, "notifications"):
                return
            return self._notifications_mark_all_read(user)
        if path.startswith("/api/notifications/") and path.endswith("/mark-read"):
            user = self._require_auth()
            if not user:
                return
            if not self._require_module(user, "notifications"):
                return
            return self._notification_mark_read(path, user)
        if path.startswith("/api/projects/") and path.endswith("/progress/init"):
            user = self._require_auth()
            if not user:
                return
            if not self._require_module(user, "projects"):
                return
            return self._init_project_progress(path, user)
        if path.startswith("/api/projects/") and path.endswith("/logs"):
            user = self._require_auth()
            if not user:
                return
            if not self._require_module(user, "projects"):
                return
            return self._project_logs_post(path, user)
        if path.startswith("/api/contracts/") and path.endswith("/payment-milestones"):
            user = self._require_auth()
            if not user:
                return
            if not self._require_module(user, "contracts"):
                return
            return self._contract_payment_milestones_post(path, user)
        if path.startswith("/api/payment-milestones/") and path.endswith("/mark-reminded"):
            user = self._require_auth()
            if not user:
                return
            return self._payment_milestone_mark(path, user, mark="reminded")
        if path.startswith("/api/payment-milestones/") and path.endswith("/mark-paid"):
            user = self._require_auth()
            if not user:
                return
            return self._payment_milestone_mark(path, user, mark="paid")
        if path.startswith("/api/projects/") and path.endswith("/designer-commission/recalculate"):
            user = self._require_auth()
            if not user:
                return
            if not self._require_module(user, "projects"):
                return
            return self._project_designer_commission_recalculate(path, user)
        if path == "/api/change-orders":
            user = self._require_auth()
            if not user:
                return
            if not (self._has_module(user, "change_orders") or self._has_module(user, "projects")):
                return self._json_response({"error": "Forbidden: change_orders/projects"}, 403)
            return self._resource_post("/api/change_orders", user)
        if path.startswith("/api/change-orders/") and path.endswith("/mark-sent"):
            user = self._require_auth()
            if not user:
                return
            return self._change_order_mark(path, user, "sent")
        if path.startswith("/api/change-orders/") and path.endswith("/mark-approved"):
            user = self._require_auth()
            if not user:
                return
            return self._change_order_mark(path, user, "approved")
        if path.startswith("/api/change-orders/") and path.endswith("/mark-rejected"):
            user = self._require_auth()
            if not user:
                return
            return self._change_order_mark(path, user, "rejected")
        if path.startswith("/api/estimates/") and path.endswith("/mark-sent"):
            user = self._require_auth()
            if not user:
                return
            return self._estimate_mark_status(path, user, "sent")
        if path.startswith("/api/estimates/") and path.endswith("/send-to-customer"):
            user = self._require_auth()
            if not user:
                return
            return self._estimate_send_to_customer(path, user)
        if path.startswith("/api/estimates/") and path.endswith("/mark-confirmed"):
            user = self._require_auth()
            if not user:
                return
            return self._estimate_mark_status(path, user, "confirmed")
        if path.startswith("/api/estimates/") and path.endswith("/mark-rejected"):
            user = self._require_auth()
            if not user:
                return
            return self._estimate_mark_status(path, user, "rejected")
        if path.startswith("/api/contracts/") and path.endswith("/mark-sent"):
            user = self._require_auth()
            if not user:
                return
            return self._contract_mark_status(path, user, "sent")
        if path.startswith("/api/contracts/") and path.endswith("/mark-signed"):
            user = self._require_auth()
            if not user:
                return
            return self._contract_mark_status(path, user, "signed")
        if path.startswith("/api/document-templates/") and path.endswith("/set-default"):
            user = self._require_auth()
            if not user:
                return
            return self._document_template_set_default(path, user)
        if path.startswith("/api/estimates/") and path.endswith("/generate-contract"):
            user = self._require_auth()
            if not user:
                return
            return self._estimate_generate_contract(path, user)
        if path.startswith("/api/contracts/") and path.endswith("/generate-project"):
            user = self._require_auth()
            if not user:
                return
            return self._contract_generate_project(path, user)
        if path.startswith("/api/customers/") and path.endswith("/followups"):
            user = self._require_auth()
            if not user:
                return
            return self._customer_followups_post(path, user)
        if path.startswith("/api/customers/") and path.endswith("/generate-estimate"):
            user = self._require_auth()
            if not user:
                return
            return self._customer_generate_estimate(path, user)
        if path.startswith("/api/followups/") and path.endswith("/mark-completed"):
            user = self._require_auth()
            if not user:
                return
            return self._followup_mark_completed(path, user)
        if path.startswith("/api/project-stage-templates"):
            user = self._require_auth()
            if not user:
                return
            return self._handle_stage_templates_post(path, user)
        if path.startswith("/api/designer-applications/") and path.endswith("/approve"):
            user = self._require_auth()
            if not user:
                return
            return self._designer_application_approve(path, user)
        if path.startswith("/api/designer-applications/") and path.endswith("/reject"):
            user = self._require_auth()
            if not user:
                return
            return self._designer_application_reject(path, user)
        if path.startswith("/api/designers/") and path.endswith("/permissions"):
            user = self._require_auth()
            if not user:
                return
            return self._designer_permissions_post(path, user)
        if path.startswith("/api/designer-assignments/") and path.endswith("/accept"):
            user = self._require_auth()
            if not user:
                return
            return self._designer_assignment_mark(path, user, "accept")
        if path.startswith("/api/designer-assignments/") and path.endswith("/decline"):
            user = self._require_auth()
            if not user:
                return
            return self._designer_assignment_mark(path, user, "decline")
        if path.startswith("/api/designer-assignments/") and path.endswith("/progress"):
            user = self._require_auth()
            if not user:
                return
            return self._designer_assignment_mark(path, user, "progress")
        if path.startswith("/api/designer-assignments/") and path.endswith("/complete"):
            user = self._require_auth()
            if not user:
                return
            return self._designer_assignment_mark(path, user, "complete")

        user = self._require_auth()
        if not user:
            return

        if path == "/api/admin/users":
            if user.get("role") != "owner":
                return self._json_response({"error": "Owner only"}, 403)
            return self._create_user()

        if not path.startswith("/api/"):
            return self._json_response({"error": "Not found"}, 404)
        return self._resource_post(path, user)

    def _public_web_lead(self, raw_query):
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        incoming_payload = dict(payload or {})
        intake_payload = {
            "name": payload.get("name"),
            "phone": payload.get("phone"),
            "email": payload.get("email"),
            "address": payload.get("address"),
            "source_channel": "website",
            "source_note": payload.get("source") or "Website Form",
            "inquiry_type": payload.get("inquiry_type") or payload.get("project_type") or payload.get("demand_type"),
            "message": payload.get("message") or payload.get("notes"),
            "preferred_contact_method": payload.get("preferred_contact_method"),
            "merge_existing": True,
        }
        conn = get_conn()
        cur = conn.cursor()
        query = parse_qs(raw_query or "")
        provided_key = self.headers.get("X-Webhook-Key") or query.get("key", [None])[0]
        expected_key = self._expected_webhook_key(cur)
        if not expected_key or provided_key != expected_key:
            conn.close()
            return self._json_response({"error": "Invalid webhook key"}, 401)
        result, status = self._upsert_lead_from_intake(cur, intake_payload, merge_existing=True)
        if status < 400:
            conn.commit()
        conn.close()
        if status >= 400:
            return self._json_response(result, status)
        return self._json_response(
            {
                "ok": True,
                "created": result.get("created"),
                "merged": result.get("merged"),
                "customer_id": (result.get("customer") or {}).get("id"),
            },
            201 if result.get("created") else 200,
        )

    def _insert_followup_compatible(self, cur, customer_id, followup_date, content, next_action="", owner=""):
        cur.execute("PRAGMA table_info(followups)")
        cols = {row["name"] for row in cur.fetchall()}
        ts = now_ts()

        fields = []
        values = []

        def push(field, value):
            if field in cols:
                fields.append(field)
                values.append(value)

        push("customer_id", customer_id)
        push("followup_date", followup_date)
        push("content", content)
        push("next_action", next_action)
        push("owner", owner)
        push("entity_type", "customer")
        push("entity_id", customer_id)
        push("contact_date", followup_date)
        push("method", "Website")
        push("created_at", ts)
        push("updated_at", ts)

        if "entity_type" in cols and "entity_type" not in fields:
            fields.append("entity_type")
            values.append("customer")
        if "entity_id" in cols and "entity_id" not in fields:
            fields.append("entity_id")
            values.append(customer_id)
        if "content" in cols and "content" not in fields:
            fields.append("content")
            values.append(content)
        if "created_at" in cols and "created_at" not in fields:
            fields.append("created_at")
            values.append(ts)

        placeholders = ",".join(["?"] * len(fields))
        cur.execute(f"INSERT INTO followups({','.join(fields)}) VALUES ({placeholders})", values)

    def do_PUT(self):
        if ev2_routes.handle_put(self, get_conn): return
        path = urlparse(self.path).path
        user = self._require_auth()
        if not user:
            return

        if path.startswith("/api/admin/users/"):
            if user.get("role") != "owner":
                return self._json_response({"error": "Owner only"}, 403)
            return self._update_user(path)
        if path == "/api/company/settings":
            if user.get("role") != "owner":
                return self._json_response({"error": "Owner only"}, 403)
            return self._update_company_settings()

        if path == "/api/auth/me/language":
            return self._update_language(user)
        if path.startswith("/api/payment-milestones/"):
            return self._payment_milestone_put(path, user)
        if path.startswith("/api/change-orders/"):
            mapped = path.replace("/api/change-orders/", "/api/change_orders/", 1)
            return self._resource_put(mapped, user)
        if path.startswith("/api/document-templates/"):
            mapped = path.replace("/api/document-templates/", "/api/document_templates/", 1)
            return self._resource_put(mapped, user)
        if path.startswith("/api/project-stage-templates/") or path.startswith("/api/project-stage-template-items/"):
            return self._handle_stage_templates_put(path, user)
        if path.startswith("/api/system-settings/"):
            if not self._require_system_settings_manage(user):
                return
            return self._system_settings_put(path, user)

        if not path.startswith("/api/"):
            return self._json_response({"error": "Not found"}, 404)
        return self._resource_put(path, user)

    def do_DELETE(self):
        if ev2_routes.handle_delete(self, get_conn): return
        path = urlparse(self.path).path
        user = self._require_auth()
        if not user:
            return

        if path.startswith("/api/admin/users/"):
            if user.get("role") != "owner":
                return self._json_response({"error": "Owner only"}, 403)
            return self._delete_user(path)
        if path.startswith("/api/files/"):
            return self._files_delete(path, user)
        if path.startswith("/api/change-orders/"):
            mapped = path.replace("/api/change-orders/", "/api/change_orders/", 1)
            return self._resource_delete(mapped, user)
        if path.startswith("/api/document-templates/"):
            mapped = path.replace("/api/document-templates/", "/api/document_templates/", 1)
            return self._resource_delete(mapped, user)
        if path.startswith("/api/project-stage-templates/") or path.startswith("/api/project-stage-template-items/"):
            return self._handle_stage_templates_delete(path, user)

        if not path.startswith("/api/"):
            return self._json_response({"error": "Not found"}, 404)
        return self._resource_delete(path, user)

    def _auth_login(self):
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        username = payload.get("username", "")
        password = payload.get("password", "")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Invalid credentials"}, 401)

        user = row_to_dict(row)
        token = new_session_token(user["id"])
        expires = (datetime.now() + timedelta(days=7)).isoformat(timespec="seconds")
        cur.execute("INSERT INTO sessions(token,user_id,expires_at,created_at) VALUES (?,?,?,?)", (token, user["id"], expires, now_ts()))
        conn.commit()
        conn.close()

        try:
            raw_modules = json.loads(user.get("modules_json") or "[]")
        except json.JSONDecodeError:
            raw_modules = []
        safe_user = {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "language": user.get("language") or DEFAULT_LANGUAGE,
            "modules": self._normalized_user_modules(
                user.get("role"),
                raw_modules,
            ),
        }
        return self._json_response(
            {"ok": True, "user": safe_user},
            200,
            extra_headers={"Set-Cookie": f"crm_token={token}; Path=/; HttpOnly; SameSite=Lax"},
        )

    def _auth_logout(self):
        cookies = self._parse_cookies()
        token = cookies.get("crm_token")
        if token:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM sessions WHERE token=?", (token,))
            conn.commit()
            conn.close()
        return self._json_response({"ok": True}, extra_headers={"Set-Cookie": "crm_token=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"})

    def _auth_me(self):
        user = self._current_user()
        if not user:
            return self._json_response({"authenticated": False})
        conn = get_conn()
        cur = conn.cursor()
        brand = self._read_company_settings(cur)
        conn.close()
        if user.get("role") != "owner":
            brand.pop("website_webhook_key", None)
        return self._json_response(
            {
                "authenticated": True,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "language": user.get("language") or DEFAULT_LANGUAGE,
                    "modules": user.get("modules") or [],
                },
                "brand": brand,
            }
        )

    def _normalize_file_entity_type(self, value):
        raw = str(value or "").strip().lower()
        aliases = {
            "customers": "customer",
            "estimates": "estimate",
            "contracts": "contract",
            "projects": "project",
            "bills": "bill",
            "payments": "payment",
        }
        return aliases.get(raw, raw)

    def _normalize_file_category(self, value):
        raw = normalize_key(value)
        aliases = {
            "合同": "contract",
            "报价": "estimate",
            "发票": "invoice",
            "变更单": "change_order",
            "完工": "completion",
            "照片": "photo",
            "其他": "other",
        }
        return aliases.get(raw, raw)

    def _serialize_file_row(self, row):
        item = row_to_dict(row)
        rel_path = (item.get("file_path") or "").strip().lstrip("/")
        item["url"] = f"/uploads/{rel_path}" if rel_path else None
        mime = (item.get("mime_type") or "").lower()
        suffix = Path(item.get("original_name") or item.get("filename") or "").suffix.lower()
        item["is_image"] = mime.startswith("image/") or suffix in {".jpg", ".jpeg", ".png", ".webp", ".gif"}
        return item

    def _attach_entity_file_meta(self, cur, entity_type, rows):
        entity_key = normalize_key(entity_type or "")
        if not rows:
            return rows
        ids = sorted({int(r.get("id")) for r in rows if r.get("id") not in (None, "", 0, "0")})
        if not ids:
            for row in rows:
                row["attachment_count"] = 0
                row["latest_attachment_url"] = None
            return rows
        ph = ",".join(["?"] * len(ids))
        cur.execute(
            f"""
            SELECT entity_id,COUNT(1) AS c,MAX(id) AS max_id
            FROM files
            WHERE entity_type=? AND entity_id IN ({ph})
            GROUP BY entity_id
            """,
            tuple([entity_key] + ids),
        )
        summary_map = {int(x["entity_id"]): row_to_dict(x) for x in cur.fetchall()}
        max_ids = [int(x["max_id"]) for x in summary_map.values() if x.get("max_id")]
        latest_file_map = {}
        if max_ids:
            ph2 = ",".join(["?"] * len(max_ids))
            cur.execute(f"SELECT id,file_path FROM files WHERE id IN ({ph2})", tuple(max_ids))
            for row in cur.fetchall():
                rel_path = (row["file_path"] or "").strip().lstrip("/")
                latest_file_map[int(row["id"])] = f"/uploads/{rel_path}" if rel_path else None
        for row in rows:
            rid = int(row.get("id") or 0)
            s = summary_map.get(rid) or {}
            row["attachment_count"] = int(s.get("c") or 0)
            row["latest_attachment_url"] = latest_file_map.get(int(s.get("max_id") or 0))
        return rows

    def _assert_file_entity_access(self, cur, user, entity_type, entity_id):
        table = FILE_ENTITY_TABLE.get(entity_type)
        mod = FILE_ENTITY_MODULE.get(entity_type)
        if not table or not mod:
            self._json_response({"error": "Invalid entity_type"}, 400)
            return False
        if not self._has_module(user, mod):
            self._json_response({"error": f"Forbidden: {mod}"}, 403)
            return False
        cur.execute(f"SELECT id FROM {table} WHERE id=?", (entity_id,))
        if not cur.fetchone():
            self._json_response({"error": f"{entity_type} not found"}, 404)
            return False
        if entity_type == "project" and self._forbid_if_no_project_access(cur, user, entity_id):
            return False
        return True

    def _files_get(self, query, user):
        entity_type = self._normalize_file_entity_type((query.get("entity_type", [""])[0] or "").strip())
        entity_id_raw = (query.get("entity_id", [""])[0] or "").strip()
        category = self._normalize_file_category((query.get("category", [""])[0] or "").strip())
        if not entity_type or not entity_id_raw:
            return self._json_response({"error": "entity_type and entity_id are required"}, 400)
        try:
            entity_id = int(entity_id_raw)
        except ValueError:
            return self._json_response({"error": "entity_id must be integer"}, 400)
        if category and category not in FILE_CATEGORY_SET:
            return self._json_response({"error": "invalid category"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        if not self._assert_file_entity_access(cur, user, entity_type, entity_id):
            conn.close()
            return
        sql = """
            SELECT f.*, u.username AS uploaded_by_name
            FROM files f
            LEFT JOIN users u ON u.id=f.uploaded_by
            WHERE f.entity_type=? AND f.entity_id=?
        """
        params = [entity_type, entity_id]
        if category:
            sql += " AND f.category=?"
            params.append(category)
        sql += " ORDER BY f.id DESC"
        cur.execute(sql, tuple(params))
        rows = [self._serialize_file_row(r) for r in cur.fetchall()]
        conn.close()
        return self._json_response(rows)

    def _read_multipart_form_data(self):
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype:
            return None, None, "multipart/form-data required"
        boundary_match = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', ctype, flags=re.IGNORECASE)
        if not boundary_match:
            return None, None, "Missing multipart boundary"
        boundary = (boundary_match.group(1) or boundary_match.group(2) or "").encode("utf-8", "ignore")
        if not boundary:
            return None, None, "Invalid multipart boundary"
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        body = self.rfile.read(length) if length > 0 else b""
        if not body:
            return {}, {}, None

        fields = {}
        files = {}
        marker = b"--" + boundary
        for raw_part in body.split(marker):
            part = raw_part.strip()
            if not part or part == b"--":
                continue
            if part.startswith(b"--"):
                part = part[2:]
            part = part.strip(b"\r\n")
            head, sep, data = part.partition(b"\r\n\r\n")
            if not sep:
                continue
            header_lines = head.decode("utf-8", "ignore").split("\r\n")
            headers = {}
            for line in header_lines:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
            disposition = headers.get("content-disposition", "")
            name_match = re.search(r'name="([^"]+)"', disposition)
            if not name_match:
                continue
            field_name = name_match.group(1)
            filename_match = re.search(r'filename="([^"]*)"', disposition)
            data = data.rstrip(b"\r\n")
            if filename_match and filename_match.group(1):
                files[field_name] = {
                    "filename": Path(filename_match.group(1)).name,
                    "content": data,
                    "content_type": headers.get("content-type", "application/octet-stream"),
                }
            else:
                fields[field_name] = data.decode("utf-8", "ignore")
        return fields, files, None

    def _files_upload(self, user):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        fields, files, error = self._read_multipart_form_data()
        if error:
            return self._json_response({"error": error}, 400)

        entity_type = self._normalize_file_entity_type(fields.get("entity_type", ""))
        entity_id_raw = str(fields.get("entity_id", "")).strip()
        category = self._normalize_file_category(fields.get("category", "other"))
        if not entity_type or not entity_id_raw:
            return self._json_response({"error": "entity_type and entity_id are required"}, 400)
        try:
            entity_id = int(entity_id_raw)
        except ValueError:
            return self._json_response({"error": "entity_id must be integer"}, 400)
        if category not in FILE_CATEGORY_SET:
            return self._json_response({"error": "invalid category"}, 400)
        if "file" not in files:
            return self._json_response({"error": "file is required"}, 400)
        file_item = files["file"]
        original_name = Path(file_item.get("filename") or "").name
        if not original_name:
            return self._json_response({"error": "file is required"}, 400)

        file_bytes = file_item.get("content") or b""
        file_size = len(file_bytes)
        if file_size <= 0:
            return self._json_response({"error": "empty file"}, 400)
        if file_size > MAX_UPLOAD_FILE_SIZE:
            return self._json_response({"error": "file too large (max 20MB)"}, 400)

        ext = Path(original_name).suffix.lower()
        if ext not in ALLOWED_UPLOAD_EXTS:
            return self._json_response({"error": "Only jpg/jpeg/png/pdf supported"}, 400)
        mime_type = (file_item.get("content_type") or mimetypes.guess_type(original_name)[0] or "application/octet-stream").lower()
        if ext in {".jpg", ".jpeg", ".png"} and not mime_type.startswith("image/"):
            mime_type = mimetypes.guess_type(f"file{ext}")[0] or "image/jpeg"
        if ext == ".pdf":
            mime_type = "application/pdf"

        conn = get_conn()
        cur = conn.cursor()
        if not self._assert_file_entity_access(cur, user, entity_type, entity_id):
            conn.close()
            return

        ts = now_ts()
        safe_ext = ext if re.fullmatch(r"\.[a-z0-9]+", ext) else ".bin"
        stored_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(6)}{safe_ext}"
        target_dir = (UPLOADS_DIR / entity_type).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        rel_path = f"{entity_type}/{stored_name}"
        target_path = (UPLOADS_DIR / rel_path).resolve()
        target_path.write_bytes(file_bytes)

        cur.execute(
            """
            INSERT INTO files(entity_type,entity_id,category,filename,original_name,file_path,mime_type,file_size,uploaded_by,created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                entity_type,
                entity_id,
                category,
                stored_name,
                original_name,
                rel_path,
                mime_type,
                file_size,
                user.get("id"),
                ts,
            ),
        )
        file_id = cur.lastrowid
        conn.commit()
        cur.execute(
            """
            SELECT f.*,u.username AS uploaded_by_name
            FROM files f
            LEFT JOIN users u ON u.id=f.uploaded_by
            WHERE f.id=?
            """,
            (file_id,),
        )
        row = cur.fetchone()
        conn.close()
        return self._json_response(self._serialize_file_row(row), 201)

    def _company_logo_upload(self, user):
        fields, files, error = self._read_multipart_form_data()
        if error:
            return self._json_response({"error": error}, 400)
        slot = normalize_key(fields.get("slot") or "icon")
        if slot not in {"icon", "horizontal"}:
            return self._json_response({"error": "slot must be icon or horizontal"}, 400)
        if "file" not in files:
            return self._json_response({"error": "file is required"}, 400)

        file_item = files["file"]
        original_name = Path(file_item.get("filename") or "").name
        ext = Path(original_name).suffix.lower()
        if ext not in ALLOWED_BRAND_LOGO_EXTS:
            return self._json_response({"error": "Only jpg/jpeg/png supported"}, 400)
        file_bytes = file_item.get("content") or b""
        file_size = len(file_bytes)
        if file_size <= 0:
            return self._json_response({"error": "empty file"}, 400)
        if file_size > MAX_BRAND_LOGO_SIZE:
            return self._json_response({"error": "file too large (max 5MB)"}, 400)

        mime_type = (file_item.get("content_type") or mimetypes.guess_type(original_name)[0] or "application/octet-stream").lower()
        if not mime_type.startswith("image/"):
            mime_type = mimetypes.guess_type(f"file{ext}")[0] or "image/png"

        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        stored_name = f"logo-{slot}-{ts}-{secrets.token_hex(4)}{ext}"
        target_dir = (UPLOADS_DIR / "brand").resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = (target_dir / stored_name).resolve()
        if not str(target_path).startswith(str(UPLOADS_DIR.resolve())):
            return self._json_response({"error": "invalid upload path"}, 400)
        target_path.write_bytes(file_bytes)
        url = f"/uploads/brand/{stored_name}"

        field = "logo_icon_url" if slot == "icon" else "logo_horizontal_url"
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(f"UPDATE company_settings SET {field}=?, updated_at=? WHERE id=1", (url, now_ts()))
        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO company_settings(
                    id, company_name, legal_name, tagline, logo_horizontal_url, logo_icon_url,
                    primary_color, accent_color, dark_color, light_bg, website_webhook_key, updated_at
                ) VALUES (1,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    "Company",
                    "",
                    "",
                    url if slot == "horizontal" else "/assets/images/logo-oaklian-dark.png",
                    url if slot == "icon" else "/assets/images/logo-oaklian-light.png",
                    "#1E293B",
                    "#A38A55",
                    "#0F172A",
                    "#E2E8F0",
                    WEBHOOK_KEY_ENV or "oaklian-webhook-key-change-me",
                    now_ts(),
                ),
            )
        data = self._read_company_settings(cur)
        self._sync_brand_logo_settings(cur, data, user.get("id"))
        conn.commit()
        conn.close()
        return self._json_response({"ok": True, "slot": slot, "url": url, "mime_type": mime_type, "brand": data}, 201)

    def _files_delete(self, path, user):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 3 or parts[0] != "api" or parts[1] != "files":
            return self._json_response({"error": "Not found"}, 404)
        try:
            file_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid file id"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM files WHERE id=?", (file_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "File not found"}, 404)
        item = row_to_dict(row)
        if not self._assert_file_entity_access(cur, user, item.get("entity_type"), int(item.get("entity_id") or 0)):
            conn.close()
            return

        rel_path = (item.get("file_path") or "").strip().lstrip("/")
        abs_path = (UPLOADS_DIR / rel_path).resolve()
        if str(abs_path).startswith(str(UPLOADS_DIR.resolve())) and abs_path.exists() and abs_path.is_file():
            try:
                abs_path.unlink()
            except OSError:
                pass

        cur.execute("DELETE FROM files WHERE id=?", (file_id,))
        conn.commit()
        conn.close()
        return self._json_response({"ok": True, "id": file_id})

    def _read_company_settings(self, cur):
        cur.execute("SELECT * FROM company_settings WHERE id=1")
        row = cur.fetchone()
        if not row:
            return {}
        return row_to_dict(row)

    def _expected_webhook_key(self, cur):
        brand = self._read_company_settings(cur)
        brand_key = str(brand.get("website_webhook_key") or "").strip()
        if brand_key:
            return brand_key
        return str(WEBHOOK_KEY_ENV or "").strip()

    def _get_company_settings(self):
        conn = get_conn()
        cur = conn.cursor()
        data = self._read_company_settings(cur)
        conn.close()
        user = self._current_user()
        if not user or user.get("role") != "owner":
            data.pop("website_webhook_key", None)
        return self._json_response(data)

    def _update_company_settings(self):
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        allowed = [
            "company_name",
            "legal_name",
            "tagline",
            "logo_horizontal_url",
            "logo_icon_url",
            "primary_color",
            "accent_color",
            "dark_color",
            "light_bg",
            "website_webhook_key",
        ]
        fields = [f for f in allowed if f in payload]
        if not fields:
            return self._json_response({"error": "No fields to update"}, 400)
        conn = get_conn()
        cur = conn.cursor()
        sets = [f"{f}=?" for f in fields] + ["updated_at=?"]
        vals = [payload.get(f) for f in fields] + [now_ts()]
        cur.execute(f"UPDATE company_settings SET {','.join(sets)} WHERE id=1", vals)
        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO company_settings(
                    id, company_name, legal_name, tagline, logo_horizontal_url, logo_icon_url,
                    primary_color, accent_color, dark_color, light_bg, website_webhook_key, updated_at
                ) VALUES (1,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    payload.get("company_name") or "Company",
                    payload.get("legal_name") or "",
                    payload.get("tagline") or "",
                    payload.get("logo_horizontal_url") or "/assets/images/logo-oaklian-dark.png",
                    payload.get("logo_icon_url") or "/assets/images/logo-oaklian-light.png",
                    payload.get("primary_color") or "#1E293B",
                    payload.get("accent_color") or "#A38A55",
                    payload.get("dark_color") or "#0F172A",
                    payload.get("light_bg") or "#E2E8F0",
                    payload.get("website_webhook_key") or WEBHOOK_KEY_ENV or "oaklian-webhook-key-change-me",
                    now_ts(),
                ),
            )
        data = self._read_company_settings(cur)
        current_user = self._current_user() or {}
        self._sync_brand_logo_settings(cur, data, current_user.get("id"))
        conn.commit()
        conn.close()
        return self._json_response(data)

    def _update_language(self, user):
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        lang = payload.get("language")
        if lang not in {"zh", "en", "es"}:
            return self._json_response({"error": "language must be zh/en/es"}, 400)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET language=?, updated_at=? WHERE id=?", (lang, now_ts(), user["id"]))
        conn.commit()
        conn.close()
        return self._json_response({"ok": True, "language": lang})

    def _list_users(self):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id,username,role,language,modules_json,created_at,updated_at FROM users ORDER BY id ASC")
        users = []
        for r in cur.fetchall():
            item = row_to_dict(r)
            try:
                parsed_modules = json.loads(item.get("modules_json") or "[]")
            except json.JSONDecodeError:
                parsed_modules = []
            item["modules"] = self._normalized_user_modules(item.get("role"), parsed_modules)
            item.pop("modules_json", None)
            users.append(item)
        conn.close()
        return self._json_response(users)

    def _create_user(self):
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        username = payload.get("username", "").strip()
        password = payload.get("password", "").strip()
        role = payload.get("role", "manager")
        language = payload.get("language", DEFAULT_LANGUAGE)
        modules = payload.get("modules", [])

        if not username or not password:
            return self._json_response({"error": "username/password required"}, 400)
        if role not in {"owner", "manager", "designer"}:
            return self._json_response({"error": "role must be owner/manager/designer"}, 400)
        if language not in {"zh", "en", "es"}:
            return self._json_response({"error": "language must be zh/en/es"}, 400)
        if role == "owner":
            modules = ALL_MODULES
        elif role == "designer":
            modules = list(DESIGNER_ALLOWED_MODULES)
        modules = self._normalized_user_modules(role, modules)

        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users(username,password,role,language,modules_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                (username, password, role, language, json.dumps(modules, ensure_ascii=False), now_ts(), now_ts()),
            )
            user_id = cur.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return self._json_response({"error": "username already exists"}, 409)

        cur.execute("SELECT id,username,role,language,modules_json,created_at,updated_at FROM users WHERE id=?", (user_id,))
        item = row_to_dict(cur.fetchone())
        try:
            parsed_modules = json.loads(item.get("modules_json") or "[]")
        except json.JSONDecodeError:
            parsed_modules = []
        item["modules"] = self._normalized_user_modules(item.get("role"), parsed_modules)
        item.pop("modules_json", None)
        conn.close()
        return self._json_response(item, 201)

    def _update_user(self, path):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4:
            return self._json_response({"error": "Not found"}, 404)
        try:
            uid = int(parts[3])
        except ValueError:
            return self._json_response({"error": "Invalid user id"}, 400)

        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        allowed = ["password", "role", "language", "modules"]
        if not any(k in payload for k in allowed):
            return self._json_response({"error": "No fields to update"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE id=?", (uid,))
        existing_user = cur.fetchone()
        if not existing_user:
            conn.close()
            return self._json_response({"error": "User not found"}, 404)

        target_role = payload.get("role", existing_user["role"])
        fields = []
        values = []
        if "password" in payload:
            fields.append("password=?")
            values.append(payload["password"])
        if "role" in payload:
            role = payload["role"]
            if role not in {"owner", "manager", "designer"}:
                conn.close()
                return self._json_response({"error": "role must be owner/manager/designer"}, 400)
            fields.append("role=?")
            values.append(role)
        if "language" in payload:
            language = payload["language"]
            if language not in {"zh", "en", "es"}:
                conn.close()
                return self._json_response({"error": "language must be zh/en/es"}, 400)
            fields.append("language=?")
            values.append(language)
        if "modules" in payload:
            modules = payload.get("modules", [])
            fields.append("modules_json=?")
            values.append(json.dumps(self._normalized_user_modules(target_role, modules), ensure_ascii=False))
        elif target_role == "owner":
            fields.append("modules_json=?")
            values.append(json.dumps(ALL_MODULES, ensure_ascii=False))
        elif target_role == "designer":
            fields.append("modules_json=?")
            values.append(json.dumps(DESIGNER_ALLOWED_MODULES, ensure_ascii=False))

        fields.append("updated_at=?")
        values.append(now_ts())
        values.append(uid)

        cur.execute(f"UPDATE users SET {','.join(fields)} WHERE id=?", values)
        conn.commit()
        cur.execute("SELECT id,username,role,language,modules_json,created_at,updated_at FROM users WHERE id=?", (uid,))
        item = row_to_dict(cur.fetchone())
        try:
            parsed_modules = json.loads(item.get("modules_json") or "[]")
        except json.JSONDecodeError:
            parsed_modules = []
        item["modules"] = self._normalized_user_modules(item.get("role"), parsed_modules)
        item.pop("modules_json", None)
        conn.close()
        return self._json_response(item)

    def _delete_user(self, path):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4:
            return self._json_response({"error": "Not found"}, 404)
        try:
            uid = int(parts[3])
        except ValueError:
            return self._json_response({"error": "Invalid user id"}, 400)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=?", (uid,))
        if cur.rowcount == 0:
            conn.close()
            return self._json_response({"error": "User not found"}, 404)
        conn.commit()
        conn.close()
        return self._json_response({"ok": True})

    def _dashboard(self, user):
        conn = get_conn()
        cur = conn.cursor()
        now = datetime.now()
        mstart = month_start(now).isoformat(timespec="seconds")
        today = to_iso_date(now)
        in_7_days = to_iso_date(now + timedelta(days=7))

        def scalar(sql, params=()):
            cur.execute(sql, params)
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else 0

        cards = {
            "monthly_new_leads": scalar("SELECT COUNT(1) FROM customers WHERE status IN ('新线索','Lead') AND created_at >= ?", (mstart,)),
            "monthly_estimates_sent": scalar(
                """
                SELECT COUNT(1) FROM estimates
                WHERE (
                    LOWER(COALESCE(confirm_status,''))='sent'
                    OR (
                        (confirm_status IS NULL OR TRIM(confirm_status)='')
                        AND (LOWER(COALESCE(status,''))='sent' OR status='已发送')
                    )
                ) AND created_at >= ?
                """,
                (mstart,),
            ),
            "monthly_contracts_signed": scalar(
                """
                SELECT COUNT(1) FROM contracts
                WHERE (
                    LOWER(COALESCE(sign_status,''))='signed'
                    OR (
                        (sign_status IS NULL OR TRIM(sign_status)='')
                        AND (signed_status='Signed' OR signed_status='已签署' OR signed_status='已签约')
                    )
                ) AND created_at >= ?
                """,
                (mstart,),
            ),
            "monthly_contracted_amount": scalar(
                """
                SELECT COALESCE(SUM(total_amount),0) FROM contracts
                WHERE (
                    LOWER(COALESCE(sign_status,''))='signed'
                    OR (
                        (sign_status IS NULL OR TRIM(sign_status)='')
                        AND (signed_status='Signed' OR signed_status='已签署' OR signed_status='已签约')
                    )
                ) AND created_at >= ?
                """,
                (mstart,),
            ),
            "active_projects": scalar("SELECT COUNT(1) FROM projects WHERE status='In Progress'"),
            "monthly_ar_received": scalar("SELECT COALESCE(SUM(amount),0) FROM project_payments WHERE status='Paid' AND received_date >= ?", (to_iso_date(month_start(now)),)),
            "monthly_ar_pending": scalar("SELECT COALESCE(SUM(amount),0) FROM project_payments WHERE status IN ('Pending','Overdue')"),
            "monthly_cost": scalar("SELECT COALESCE(SUM(amount),0) FROM project_costs WHERE cost_date >= ?", (to_iso_date(month_start(now)),)),
        }
        cards["monthly_gross_profit"] = cards["monthly_ar_received"] - cards["monthly_cost"]

        stale_followups = []
        due_today_followups = []
        stale_customers = []

        cur.execute(
            """
            SELECT
                e.id,e.customer_id,e.title,e.version,e.total_amount,e.created_at,e.updated_at,
                c.name AS customer_name,c.phone AS customer_phone
            FROM estimates e
            LEFT JOIN customers c ON c.id=e.customer_id
            WHERE (
                LOWER(COALESCE(e.confirm_status,''))='sent'
                OR (
                    (e.confirm_status IS NULL OR TRIM(e.confirm_status)='')
                    AND (LOWER(COALESCE(e.status,''))='sent' OR e.status='已发送')
                )
            )
            ORDER BY COALESCE(e.updated_at,e.created_at) ASC
            LIMIT 8
            """
        )
        pending_estimate_confirmations = [row_to_dict(r) for r in cur.fetchall()]
        pending_estimates = pending_estimate_confirmations

        cur.execute(
            """
            SELECT
                ct.id,ct.contract_no,ct.customer_id,ct.total_amount,ct.updated_at,ct.created_at,ct.title,
                c.name AS customer_name,c.phone AS customer_phone
            FROM contracts ct
            LEFT JOIN customers c ON c.id=ct.customer_id
            WHERE (
                LOWER(COALESCE(ct.sign_status,''))='sent'
                OR (
                    (ct.sign_status IS NULL OR TRIM(ct.sign_status)='')
                    AND (ct.signed_status='Sent' OR ct.signed_status='已发送')
                )
            )
            ORDER BY COALESCE(ct.updated_at,ct.created_at) ASC
            LIMIT 8
            """
        )
        pending_contract_signings = [row_to_dict(r) for r in cur.fetchall()]

        cur.execute(
            """
            SELECT id,project_id,node_name,due_date,amount,status
            FROM project_payments
            WHERE status IN ('Pending','Overdue') AND due_date >= ? AND due_date <= ?
            ORDER BY due_date ASC LIMIT 8
            """,
            (today, in_7_days),
        )
        upcoming_payments = [row_to_dict(r) for r in cur.fetchall()]

        cur.execute(
            """
            SELECT i.id,i.project_id,i.title,i.severity,i.status,i.due_date,p.name AS project_name
            FROM project_issues i LEFT JOIN projects p ON p.id=i.project_id
            WHERE i.status IN ('Open','In Progress')
            ORDER BY i.due_date ASC LIMIT 8
            """
        )
        open_issues = [row_to_dict(r) for r in cur.fetchall()]

        cur.execute("SELECT id FROM projects ORDER BY id ASC")
        for pr in cur.fetchall():
            self._evaluate_project_payment_triggers(cur, pr["id"])
        payment_reminders = self._fetch_payment_reminders(cur, user, project_id=None)[:8]
        due_today_followups = self._fetch_due_today_followups(cur, user, limit=8)
        stale_customers = self._fetch_stale_customers(cur, user, limit=8)
        stale_followups = stale_customers
        conn.close()

        if user.get("role") == "designer":
            cards = {
                "monthly_new_leads": None,
                "monthly_estimates_sent": None,
                "monthly_contracts_signed": None,
                "monthly_contracted_amount": None,
                "active_projects": 0,
                "monthly_ar_received": None,
                "monthly_ar_pending": None,
                "monthly_cost": None,
                "monthly_gross_profit": None,
            }
            conn2 = get_conn()
            cur2 = conn2.cursor()
            cur2.execute("SELECT COUNT(1) c FROM projects WHERE designer_id=? AND status='In Progress'", (user.get("id"),))
            cards["active_projects"] = (cur2.fetchone() or {"c": 0})["c"]
            cur2.execute(
                """
                SELECT i.id,i.project_id,i.title,i.severity,i.status,i.due_date,p.name AS project_name
                FROM project_issues i
                JOIN projects p ON p.id=i.project_id
                WHERE p.designer_id=? AND i.status IN ('Open','In Progress')
                ORDER BY i.due_date ASC LIMIT 8
                """,
                (user.get("id"),),
            )
            open_issues = [row_to_dict(r) for r in cur2.fetchall()]
            conn2.close()
            stale_followups = []
            due_today_followups = []
            stale_customers = []
            pending_estimates = []
            pending_estimate_confirmations = []
            pending_contract_signings = []
            upcoming_payments = []

        if not self._has_module(user, "finance"):
            cards["monthly_ar_received"] = None
            cards["monthly_ar_pending"] = None
            cards["monthly_cost"] = None
            cards["monthly_gross_profit"] = None
            upcoming_payments = []
        if not self._has_module(user, "estimates"):
            pending_estimate_confirmations = []
            pending_estimates = []
        if not self._has_module(user, "contracts"):
            pending_contract_signings = []
        if not (self._has_module(user, "contracts") or self._has_module(user, "projects") or self._has_module(user, "finance")):
            payment_reminders = []

        return self._json_response({
            "cards": cards,
            "lists": {
                "stale_followups": stale_followups,
                "due_today_followups": due_today_followups,
                "stale_customers": stale_customers,
                "pending_estimates": pending_estimates,
                "pending_estimate_confirmations": pending_estimate_confirmations,
                "pending_contract_signings": pending_contract_signings,
                "upcoming_payments": upcoming_payments,
                "payment_reminders": payment_reminders,
                "open_issues": open_issues,
            },
        })

    def _finance_summary(self):
        conn = get_conn()
        cur = conn.cursor()
        now = datetime.now()
        mstart = to_iso_date(month_start(now))
        today = now.date()

        def scalar(sql, params=()):
            cur.execute(sql, params)
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else 0

        ar_rows = []
        cur.execute(
            """
            SELECT pp.id, pp.project_id, p.name AS project_name, pp.node_name, pp.due_date,
                   pp.amount, COALESCE(pp.received_amount,0) AS received_amount,
                   pp.status, pp.received_date, pp.invoice_no, pp.payment_method, pp.notes
            FROM project_payments pp
            LEFT JOIN projects p ON p.id=pp.project_id
            ORDER BY pp.due_date ASC, pp.id ASC
            """
        )
        for r in cur.fetchall():
            item = row_to_dict(r)
            open_amount = max((item.get("amount") or 0) - (item.get("received_amount") or 0), 0)
            due_date = item.get("due_date")
            age_days = 0
            if due_date:
                try:
                    age_days = max((today - datetime.strptime(due_date, "%Y-%m-%d").date()).days, 0)
                except ValueError:
                    age_days = 0
            item["open_amount"] = open_amount
            item["age_days"] = age_days
            ar_rows.append(item)

        ap_rows = []
        cur.execute(
            """
            SELECT b.id, b.project_id, p.name AS project_name, b.vendor_id, v.name AS vendor, v.type AS vendor_type,
                   v.tax_id, v."1099_required" AS vendor_1099_required, b.category, b.bill_date, b.due_date,
                   b.amount, COALESCE(b.paid_amount,0) AS paid_amount, b.status, b.bill_no AS reference_no, b.note AS notes
            FROM bills b
            LEFT JOIN projects p ON p.id=b.project_id
            LEFT JOIN vendors v ON v.id=b.vendor_id
            ORDER BY COALESCE(b.due_date,b.bill_date) ASC, b.id ASC
            """
        )
        for r in cur.fetchall():
            item = row_to_dict(r)
            open_amount = max((item.get("amount") or 0) - (item.get("paid_amount") or 0), 0)
            due_date = item.get("due_date")
            age_days = 0
            if due_date:
                try:
                    age_days = max((today - datetime.strptime(due_date, "%Y-%m-%d").date()).days, 0)
                except ValueError:
                    age_days = 0
            item["open_amount"] = open_amount
            item["age_days"] = age_days
            ap_rows.append(item)

        def aging_buckets(rows):
            buckets = [
                {"bucket": "0-30", "amount": 0, "count": 0},
                {"bucket": "31-60", "amount": 0, "count": 0},
                {"bucket": "61-90", "amount": 0, "count": 0},
                {"bucket": "90+", "amount": 0, "count": 0},
            ]
            for x in rows:
                open_amt = x.get("open_amount") or 0
                if open_amt <= 0:
                    continue
                d = x.get("age_days") or 0
                idx = 0 if d <= 30 else 1 if d <= 60 else 2 if d <= 90 else 3
                buckets[idx]["amount"] += open_amt
                buckets[idx]["count"] += 1
            return buckets

        ar_total = sum(x.get("open_amount", 0) for x in ar_rows)
        ar_overdue = sum(x.get("open_amount", 0) for x in ar_rows if (x.get("age_days") or 0) > 0)
        ap_total = sum(x.get("open_amount", 0) for x in ap_rows)
        ap_overdue = sum(x.get("open_amount", 0) for x in ap_rows if (x.get("age_days") or 0) > 0)

        monthly_received = scalar("SELECT COALESCE(SUM(received_amount),0) FROM project_payments WHERE received_date >= ?", (mstart,))
        monthly_ap_paid = scalar("SELECT COALESCE(SUM(amount),0) FROM payments WHERE date >= ?", (mstart,))
        monthly_cost = scalar("SELECT COALESCE(SUM(amount),0) FROM project_costs WHERE cost_date >= ?", (mstart,))
        monthly_cashflow = monthly_received - monthly_ap_paid

        cur.execute(
            """
            SELECT p.id, p.name,
                COALESCE((SELECT SUM(total_amount) FROM contracts c WHERE c.project_id=p.id),0) AS contract_revenue,
                COALESCE((
                    SELECT SUM(amount_delta)
                    FROM change_orders co
                    WHERE co.project_id=p.id
                      AND (
                        LOWER(COALESCE(co.status,''))='approved'
                        OR co.status='已确认'
                        OR co.signed_status='Signed'
                      )
                ),0) AS change_revenue,
                COALESCE((SELECT SUM(received_amount) FROM project_payments pp WHERE pp.project_id=p.id),0) AS received_revenue,
                COALESCE((SELECT SUM(open_amount) FROM (
                    SELECT MAX(COALESCE(amount,0)-COALESCE(received_amount,0),0) AS open_amount
                    FROM project_payments pp2 WHERE pp2.project_id=p.id
                )),0) AS ar_open,
                COALESCE((SELECT SUM(amount) FROM project_costs pc WHERE pc.project_id=p.id),0) AS recorded_cost,
                COALESCE((SELECT SUM(MAX(COALESCE(amount,0)-COALESCE(paid_amount,0),0)) FROM bills b2 WHERE b2.project_id=p.id),0) AS ap_open
            FROM projects p
            ORDER BY p.id DESC
            """
        )
        project_profit_detail = []
        for r in cur.fetchall():
            item = row_to_dict(r)
            total_revenue = (item.get("contract_revenue") or 0) + (item.get("change_revenue") or 0)
            total_cost = (item.get("recorded_cost") or 0) + (item.get("ap_open") or 0)
            item["total_revenue"] = total_revenue
            item["total_cost"] = total_cost
            item["gross_profit"] = total_revenue - total_cost
            item["gross_margin_pct"] = round((item["gross_profit"] / total_revenue) * 100, 2) if total_revenue > 0 else 0
            project_profit_detail.append(item)

        ytd_start = f"{datetime.now().year}-01-01"
        cur.execute(
            """
            SELECT v.id,v.name,v.type,v.tax_id,v."1099_required" AS required_1099,v.w9_received,
                   COALESCE(SUM(p.amount),0) AS total_paid_this_year
            FROM vendors v
            LEFT JOIN payments p
              ON p.vendor_id=v.id AND p.date >= ?
            GROUP BY v.id,v.name,v.type,v.tax_id,v."1099_required",v.w9_received
            ORDER BY total_paid_this_year DESC,v.id DESC
            """,
            (ytd_start,),
        )
        report_1099 = []
        for row in cur.fetchall():
            item = row_to_dict(row)
            vendor_type = self._vendor_type_key(item.get("type"))
            required_1099 = 1 if int(item.get("required_1099") or 0) == 1 or vendor_type == "1099" else 0
            total_paid = float(item.get("total_paid_this_year") or 0)
            if required_1099 == 1 or total_paid > 0:
                report_1099.append(
                    {
                        "vendor_id": item.get("id"),
                        "vendor": item.get("name"),
                        "vendor_type": vendor_type,
                        "tax_id": item.get("tax_id"),
                        "total_paid_this_year": round(total_paid, 2),
                        "over_600": 1 if total_paid >= 600 else 0,
                        "required_1099": required_1099,
                        "w9_received": 1 if int(item.get("w9_received") or 0) == 1 else 0,
                    }
                )

        conn.close()
        return self._json_response({
            "cards": {
                "ar_total": ar_total,
                "ar_overdue": ar_overdue,
                "ap_total": ap_total,
                "ap_overdue": ap_overdue,
                "monthly_received": monthly_received,
                "monthly_ap_paid": monthly_ap_paid,
                "monthly_cost": monthly_cost,
                "monthly_cashflow": monthly_cashflow,
            },
            "ar_aging": aging_buckets(ar_rows),
            "ap_aging": aging_buckets(ap_rows),
            "ar_ledger": ar_rows,
            "ap_ledger": ap_rows,
            "project_profit_detail": project_profit_detail,
            "report_1099": report_1099,
        })

    def _project_cost_ledger(self, project_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.*,c.name AS customer_name,c.phone AS customer_phone
            FROM projects p
            LEFT JOIN customers c ON c.id=p.customer_id
            WHERE p.id=?
            """,
            (project_id,),
        )
        project = cur.fetchone()
        if not project:
            conn.close()
            return self._json_response({"error": "Project not found"}, 404)
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return

        cur.execute("SELECT COALESCE(SUM(total_amount),0) AS total FROM contracts WHERE project_id=?", (project_id,))
        contract_row = cur.fetchone()
        contract_revenue = float((contract_row["total"] if contract_row else 0) or 0)
        cur.execute(
            "SELECT COALESCE(SUM(amount_delta),0) AS total FROM change_orders WHERE project_id=? AND status='approved'",
            (project_id,),
        )
        change_row = cur.fetchone()
        change_revenue = float((change_row["total"] if change_row else 0) or 0)
        total_revenue = contract_revenue + change_revenue

        cur.execute(
            """
            SELECT b.*,v.name AS vendor_name
            FROM bills b
            LEFT JOIN vendors v ON v.id=b.vendor_id
            WHERE b.project_id=?
            ORDER BY COALESCE(b.bill_date,b.created_at) DESC,b.id DESC
            """,
            (project_id,),
        )
        bills = [row_to_dict(r) for r in cur.fetchall()]
        self._attach_entity_file_meta(cur, "bill", bills)

        open_bills_total = 0.0
        category_map = {}
        for bill in bills:
            amount = float(bill.get("amount") or 0)
            paid_amount = float(bill.get("paid_amount") or 0)
            open_amount = max(amount - paid_amount, 0)
            bill["open_amount"] = round(open_amount, 2)
            open_bills_total += open_amount
            cat = str(bill.get("category") or "other").strip() or "other"
            agg = category_map.setdefault(
                cat,
                {
                    "category": cat,
                    "bill_count": 0,
                    "total_amount": 0.0,
                    "paid_amount": 0.0,
                    "open_amount": 0.0,
                },
            )
            agg["bill_count"] += 1
            agg["total_amount"] += amount
            agg["paid_amount"] += paid_amount
            agg["open_amount"] += open_amount

        cur.execute(
            """
            SELECT p.*,v.name AS vendor_name,b.bill_no
            FROM payments p
            LEFT JOIN vendors v ON v.id=p.vendor_id
            LEFT JOIN bills b ON b.id=p.bill_id
            WHERE p.project_id=?
               OR (p.project_id IS NULL AND p.bill_id IN (SELECT id FROM bills WHERE project_id=?))
            ORDER BY p.date DESC,p.id DESC
            """,
            (project_id, project_id),
        )
        payments = [row_to_dict(r) for r in cur.fetchall()]
        self._attach_entity_file_meta(cur, "payment", payments)
        payments_total = sum(float(x.get("amount") or 0) for x in payments)

        total_cost = payments_total + open_bills_total
        gross_profit = total_revenue - total_cost
        gross_margin_pct = round((gross_profit / total_revenue) * 100, 2) if total_revenue > 0 else 0

        cost_by_category = []
        for item in category_map.values():
            cost_by_category.append(
                {
                    "category": item["category"],
                    "bill_count": int(item["bill_count"]),
                    "total_amount": round(item["total_amount"], 2),
                    "paid_amount": round(item["paid_amount"], 2),
                    "open_amount": round(item["open_amount"], 2),
                }
            )
        cost_by_category.sort(key=lambda x: x["total_amount"], reverse=True)

        payload = {
            "project": row_to_dict(project),
            "revenue": {
                "contract_revenue": round(contract_revenue, 2),
                "change_revenue": round(change_revenue, 2),
                "total_revenue": round(total_revenue, 2),
            },
            "costs": {
                "payments_total": round(payments_total, 2),
                "open_bills_total": round(open_bills_total, 2),
                "total_cost": round(total_cost, 2),
                "gross_profit": round(gross_profit, 2),
                "gross_margin_pct": gross_margin_pct,
            },
            "bills": bills,
            "payments": payments,
            "cost_by_category": cost_by_category,
        }
        conn.close()
        return self._json_response(payload)

    def _handle_project_detail(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "detail":
            return False
        try:
            project_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid project id"}, 400)
            return True
        if not self._require_module(user, "projects"):
            return True
        self._project_detail(project_id, user)
        return True

    def _handle_project_cost_ledger_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "cost-ledger":
            return False
        try:
            project_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid project id"}, 400)
            return True
        if not self._require_module(user, "finance"):
            return True
        self._project_cost_ledger(project_id, user)
        return True

    def _handle_project_progress(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "progress":
            return False
        try:
            project_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid project id"}, 400)
            return True
        if not self._require_module(user, "projects"):
            return True
        self._project_progress(project_id, user)
        return True

    def _handle_project_logs_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "logs":
            return False
        try:
            project_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid project id"}, 400)
            return True
        if not self._require_module(user, "projects"):
            return True
        self._project_logs_get(project_id, user)
        return True

    def _handle_contract_payment_milestones_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "contracts" or parts[3] != "payment-milestones":
            return False
        try:
            contract_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid contract id"}, 400)
            return True
        if not self._require_module(user, "contracts"):
            return True
        self._contract_payment_milestones_get(contract_id, user)
        return True

    def _handle_project_payment_reminders_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "payment-reminders":
            return False
        try:
            project_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid project id"}, 400)
            return True
        if not self._require_module(user, "projects"):
            return True
        self._project_payment_reminders_get(project_id, user)
        return True

    def _handle_project_designer_commission_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "designer-commission":
            return False
        try:
            project_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid project id"}, 400)
            return True
        if not self._require_module(user, "projects"):
            return True
        self._project_designer_commission_get(project_id, user)
        return True

    def _handle_lead_designer_assignments_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "leads" or parts[3] != "designer-assignments":
            return False
        try:
            lead_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid lead id"}, 400)
            return True
        if not (self._has_module(user, "customers") or self._has_module(user, "designer_assignments")):
            self._json_response({"error": "Forbidden: customers/designer_assignments"}, 403)
            return True
        self._lead_designer_assignments_get(lead_id, user)
        return True

    def _handle_project_designer_assignments_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "designer-assignments":
            return False
        try:
            project_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid project id"}, 400)
            return True
        if not (self._has_module(user, "projects") or self._has_module(user, "designer_assignments")):
            self._json_response({"error": "Forbidden: projects/designer_assignments"}, 403)
            return True
        self._project_designer_assignments_get(project_id, user)
        return True

    def _handle_vendor_payments_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "vendors" or parts[3] != "payments":
            return False
        try:
            vendor_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid vendor id"}, 400)
            return True
        if not self._require_module(user, "finance"):
            return True
        self._vendor_payments_get(vendor_id, user)
        return True

    def _handle_vendor_ledger_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "vendors" or parts[3] != "ledger":
            return False
        try:
            vendor_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid vendor id"}, 400)
            return True
        if not self._require_module(user, "finance"):
            return True
        self._vendor_ledger_get(vendor_id, user)
        return True

    def _handle_change_orders_get(self, path, query, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "change-orders":
            if not (self._has_module(user, "change_orders") or self._has_module(user, "projects")):
                self._json_response({"error": "Forbidden: change_orders/projects"}, 403)
                return True
            self._resource_get("/api/change_orders", query, user)
            return True
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "change-orders":
            if not (self._has_module(user, "change_orders") or self._has_module(user, "projects")):
                self._json_response({"error": "Forbidden: change_orders/projects"}, 403)
                return True
            try:
                int(parts[2])
            except ValueError:
                self._json_response({"error": "Invalid change order id"}, 400)
                return True
            self._resource_get(path.replace("/api/change-orders/", "/api/change_orders/", 1), query, user)
            return True
        return False

    def _handle_project_change_orders_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "change-orders":
            return False
        try:
            project_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid project id"}, 400)
            return True
        if not (self._has_module(user, "projects") or self._has_module(user, "change_orders")):
            self._json_response({"error": "Forbidden: projects/change_orders"}, 403)
            return True
        self._project_change_orders_get(project_id, user)
        return True

    def _handle_customer_estimates_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "customers" or parts[3] != "estimates":
            return False
        try:
            customer_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid customer id"}, 400)
            return True
        if not (self._has_module(user, "customers") or self._has_module(user, "estimates")):
            self._json_response({"error": "Forbidden: customers/estimates"}, 403)
            return True
        self._customer_estimates_get(customer_id, user)
        return True

    def _handle_customer_followups_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "customers" or parts[3] != "followups":
            return False
        try:
            customer_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid customer id"}, 400)
            return True
        if not self._has_module(user, "customers"):
            self._json_response({"error": "Forbidden: customers"}, 403)
            return True
        self._customer_followups_get(customer_id, user)
        return True

    def _handle_customer_recent_followups_get(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "customers" or parts[3] != "recent-followups":
            return False
        try:
            customer_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid customer id"}, 400)
            return True
        if not self._has_module(user, "customers"):
            self._json_response({"error": "Forbidden: customers"}, 403)
            return True
        self._customer_recent_followups_get(customer_id, user)
        return True

    def _handle_followups_due_today_get(self, path, user):
        if path != "/api/followups/due-today":
            return False
        if not (self._has_module(user, "dashboard") or self._has_module(user, "customers")):
            self._json_response({"error": "Forbidden: dashboard/customers"}, 403)
            return True
        self._followups_due_today_get(user)
        return True

    def _handle_followups_stale_customers_get(self, path, user):
        if path != "/api/followups/stale-customers":
            return False
        if not (self._has_module(user, "dashboard") or self._has_module(user, "customers")):
            self._json_response({"error": "Forbidden: dashboard/customers"}, 403)
            return True
        self._followups_stale_customers_get(user)
        return True

    def _milestone_amount(self, contract_total, amount_type, amount_value):
        total = float(contract_total or 0)
        value = float(amount_value or 0)
        if normalize_key(amount_type) in {"percent", "percentage"}:
            return round(total * value / 100, 2)
        return round(value, 2)

    def _milestone_trigger_reason(self, milestone):
        trigger_type = normalize_key(milestone.get("trigger_type"))
        if trigger_type == "contract_signed":
            return "合同签署"
        if trigger_type == "stage_started":
            return f"阶段开始：{milestone.get('trigger_stage') or '-'}"
        if trigger_type == "stage_done":
            return f"阶段完成：{milestone.get('trigger_stage') or '-'}"
        if trigger_type == "progress_percent":
            return f"项目进度达到 {int(milestone.get('trigger_progress') or 0)}%"
        return trigger_type or "-"

    def _serialize_milestone(self, row, contract_total):
        item = row_to_dict(row) if hasattr(row, "keys") else dict(row)
        item["amount_due"] = self._milestone_amount(contract_total, item.get("amount_type"), item.get("amount_value"))
        item["state"] = milestone_state_key(item)
        item["trigger_reason"] = self._milestone_trigger_reason(item)
        return item

    def _contract_payment_milestones_get(self, contract_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id,project_id,total_amount FROM contracts WHERE id=?", (contract_id,))
        contract = cur.fetchone()
        if not contract:
            conn.close()
            return self._json_response({"error": "Contract not found"}, 404)

        project_id = contract["project_id"]
        if user.get("role") == "designer" and project_id and self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return

        self._evaluate_contract_payment_milestones(cur, contract_id=contract_id, project_id=project_id)
        conn.commit()
        cur.execute("SELECT * FROM contract_payment_milestones WHERE contract_id=? ORDER BY id ASC", (contract_id,))
        rows = [self._serialize_milestone(r, contract["total_amount"]) for r in cur.fetchall()]
        conn.close()
        return self._json_response(rows)

    def _contract_payment_milestones_post(self, path, user):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4:
            return self._json_response({"error": "Not found"}, 404)
        try:
            contract_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid contract id"}, 400)

        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        name = (payload.get("name") or "").strip()
        trigger_type = normalize_key(payload.get("trigger_type") or "")
        amount_type = normalize_key(payload.get("amount_type") or "percent")
        amount_value = payload.get("amount_value")
        if not name:
            return self._json_response({"error": "name is required"}, 400)
        if trigger_type not in {"contract_signed", "stage_started", "stage_done", "progress_percent"}:
            return self._json_response({"error": "invalid trigger_type"}, 400)
        if amount_type not in {"percent", "fixed"}:
            return self._json_response({"error": "amount_type must be percent/fixed"}, 400)
        if amount_value in (None, ""):
            return self._json_response({"error": "amount_value is required"}, 400)
        try:
            amount_value = float(amount_value)
        except (TypeError, ValueError):
            return self._json_response({"error": "amount_value must be number"}, 400)
        trigger_stage = (payload.get("trigger_stage") or "").strip()
        trigger_progress = payload.get("trigger_progress")
        if trigger_type in {"stage_started", "stage_done"} and not trigger_stage:
            return self._json_response({"error": "trigger_stage is required"}, 400)
        if trigger_type == "progress_percent":
            try:
                trigger_progress = int(trigger_progress)
            except (TypeError, ValueError):
                return self._json_response({"error": "trigger_progress must be integer"}, 400)
            trigger_progress = max(min(trigger_progress, 100), 0)
        else:
            trigger_progress = None

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id,project_id,total_amount FROM contracts WHERE id=?", (contract_id,))
        contract = cur.fetchone()
        if not contract:
            conn.close()
            return self._json_response({"error": "Contract not found"}, 404)
        project_id = contract["project_id"]
        if user.get("role") == "designer" and project_id and self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return

        ts = now_ts()
        cur.execute(
            """
            INSERT INTO contract_payment_milestones(
                contract_id,name,node_type,trigger_type,trigger_stage,trigger_progress,amount_type,amount_value,
                triggered,triggered_at,reminded,reminded_at,paid,paid_at,note,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                contract_id,
                name,
                (payload.get("node_type") or "").strip() or None,
                trigger_type,
                trigger_stage or None,
                trigger_progress,
                amount_type,
                amount_value,
                0,
                None,
                0,
                None,
                0,
                None,
                (payload.get("note") or "").strip(),
                ts,
                ts,
            ),
        )
        new_id = cur.lastrowid
        self._evaluate_contract_payment_milestones(cur, contract_id=contract_id, project_id=project_id)
        if project_id:
            self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        cur.execute("SELECT * FROM contract_payment_milestones WHERE id=?", (new_id,))
        row = cur.fetchone()
        conn.close()
        return self._json_response(self._serialize_milestone(row, contract["total_amount"]), 201)

    def _payment_milestone_put(self, path, user):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 3 or parts[0] != "api" or parts[1] != "payment-milestones":
            return self._json_response({"error": "Not found"}, 404)
        try:
            milestone_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid milestone id"}, 400)

        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.*, c.total_amount, c.project_id
            FROM contract_payment_milestones m
            LEFT JOIN contracts c ON c.id=m.contract_id
            WHERE m.id=?
            """,
            (milestone_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Milestone not found"}, 404)
        project_id = row["project_id"]
        if user.get("role") == "designer" and project_id and self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return
        if user.get("role") != "owner" and not (self._has_module(user, "contracts") or self._has_module(user, "projects")):
            conn.close()
            return self._json_response({"error": "Forbidden"}, 403)

        allowed = {"name", "node_type", "trigger_type", "trigger_stage", "trigger_progress", "amount_type", "amount_value", "note"}
        fields = []
        values = []
        for k in allowed:
            if k in payload:
                fields.append(f"{k}=?")
                values.append(payload.get(k))
        if not fields:
            conn.close()
            return self._json_response({"error": "No fields to update"}, 400)

        if "trigger_type" in payload:
            trigger_type = normalize_key(payload.get("trigger_type"))
            if trigger_type not in {"contract_signed", "stage_started", "stage_done", "progress_percent"}:
                conn.close()
                return self._json_response({"error": "invalid trigger_type"}, 400)
            idx = [f.split("=")[0] for f in fields].index("trigger_type")
            values[idx] = trigger_type
        if "amount_type" in payload:
            amount_type = normalize_key(payload.get("amount_type"))
            if amount_type not in {"percent", "fixed"}:
                conn.close()
                return self._json_response({"error": "amount_type must be percent/fixed"}, 400)
            idx = [f.split("=")[0] for f in fields].index("amount_type")
            values[idx] = amount_type
        if "trigger_progress" in payload and payload.get("trigger_progress") not in (None, ""):
            try:
                trigger_progress = max(min(int(payload.get("trigger_progress")), 100), 0)
            except (TypeError, ValueError):
                conn.close()
                return self._json_response({"error": "trigger_progress must be integer"}, 400)
            idx = [f.split("=")[0] for f in fields].index("trigger_progress")
            values[idx] = trigger_progress

        fields.append("updated_at=?")
        values.append(now_ts())
        values.append(milestone_id)
        cur.execute(f"UPDATE contract_payment_milestones SET {','.join(fields)} WHERE id=?", values)
        self._evaluate_contract_payment_milestones(cur, contract_id=row["contract_id"], project_id=project_id)
        if project_id:
            self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        cur.execute("SELECT * FROM contract_payment_milestones WHERE id=?", (milestone_id,))
        updated = cur.fetchone()
        conn.close()
        return self._json_response(self._serialize_milestone(updated, row["total_amount"]))

    def _payment_milestone_mark(self, path, user, mark):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "payment-milestones":
            return self._json_response({"error": "Not found"}, 404)
        try:
            milestone_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid milestone id"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT m.*, c.total_amount, c.project_id
            FROM contract_payment_milestones m
            LEFT JOIN contracts c ON c.id=m.contract_id
            WHERE m.id=?
            """,
            (milestone_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Milestone not found"}, 404)
        project_id = row["project_id"]
        if user.get("role") == "designer" and project_id and self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return
        if user.get("role") != "owner" and not (
            self._has_module(user, "projects") or self._has_module(user, "contracts") or self._has_module(user, "finance")
        ):
            conn.close()
            return self._json_response({"error": "Forbidden"}, 403)

        ts = now_ts()
        if mark == "reminded":
            if int(row["paid"] or 0) == 1:
                conn.close()
                return self._json_response({"error": "Milestone already paid"}, 400)
            if int(row["triggered"] or 0) == 0:
                conn.close()
                return self._json_response({"error": "Milestone not triggered yet"}, 400)
            cur.execute(
                "UPDATE contract_payment_milestones SET reminded=1, reminded_at=COALESCE(reminded_at,?), updated_at=? WHERE id=?",
                (ts, ts, milestone_id),
            )
        else:
            cur.execute(
                """
                UPDATE contract_payment_milestones
                SET triggered=1,
                    triggered_at=COALESCE(triggered_at,?),
                    reminded=1,
                    reminded_at=COALESCE(reminded_at,?),
                    paid=1,
                    paid_at=COALESCE(paid_at,?),
                    updated_at=?
                WHERE id=?
                """,
                (ts, ts, ts, ts, milestone_id),
            )
        self._evaluate_contract_payment_milestones(cur, contract_id=row["contract_id"], project_id=project_id)
        if project_id:
            self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        cur.execute("SELECT * FROM contract_payment_milestones WHERE id=?", (milestone_id,))
        updated = cur.fetchone()
        conn.close()
        return self._json_response(self._serialize_milestone(updated, row["total_amount"]))

    def _fetch_payment_reminders(self, cur, user, project_id=None):
        sql = """
            SELECT
                m.*,
                c.contract_no,
                c.total_amount,
                p.id AS project_id,
                p.name AS project_name,
                p.designer_id AS project_designer_id,
                cu.name AS customer_name
            FROM contract_payment_milestones m
            JOIN contracts c ON c.id=m.contract_id
            LEFT JOIN projects p ON p.id = (
                SELECT id FROM projects px WHERE px.contract_id=c.id ORDER BY px.id ASC LIMIT 1
            )
            LEFT JOIN customers cu ON cu.id=c.customer_id
            WHERE m.triggered=1 AND m.paid=0
        """
        params = []
        if project_id is not None:
            sql += " AND p.id=?"
            params.append(project_id)
        if user.get("role") == "designer":
            sql += " AND p.designer_id=?"
            params.append(user.get("id"))
        sql += " ORDER BY COALESCE(m.triggered_at,m.updated_at,m.created_at) DESC, m.id DESC"
        cur.execute(sql, tuple(params))
        out = []
        for r in cur.fetchall():
            item = self._serialize_milestone(r, r["total_amount"])
            item["project_id"] = r["project_id"]
            item["project_name"] = r["project_name"]
            item["customer_name"] = r["customer_name"]
            item["contract_no"] = r["contract_no"]
            out.append(item)
        return out

    def _project_payment_reminders_get(self, project_id, user):
        conn = get_conn()
        cur = conn.cursor()
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return
        self._evaluate_project_payment_triggers(cur, project_id)
        conn.commit()
        rows = self._fetch_payment_reminders(cur, user, project_id=project_id)
        conn.close()
        return self._json_response(rows)

    def _payment_reminders_list(self, user):
        conn = get_conn()
        cur = conn.cursor()
        # Re-evaluate all linked projects so dashboard reminders are up to date.
        cur.execute("SELECT id FROM projects ORDER BY id ASC")
        for r in cur.fetchall():
            self._evaluate_project_payment_triggers(cur, r["id"])
        conn.commit()
        rows = self._fetch_payment_reminders(cur, user, project_id=None)
        conn.close()
        return self._json_response(rows)

    def _customer_estimates_get(self, customer_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM customers WHERE id=?", (customer_id,))
        if not cur.fetchone():
            conn.close()
            return self._json_response({"error": "Customer not found"}, 404)
        cur.execute("SELECT * FROM estimates WHERE customer_id=? ORDER BY id DESC", (customer_id,))
        rows = [row_to_dict(r) for r in cur.fetchall()]
        self._enrich_resource_rows(cur, "estimates", rows)
        conn.close()
        return self._json_response(rows)

    def _project_change_orders_get(self, project_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id,contract_id,customer_id FROM projects WHERE id=?", (project_id,))
        project = cur.fetchone()
        if not project:
            conn.close()
            return self._json_response({"error": "Project not found"}, 404)
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return
        cur.execute("SELECT * FROM change_orders WHERE project_id=? ORDER BY id DESC", (project_id,))
        rows = [row_to_dict(r) for r in cur.fetchall()]
        self._enrich_resource_rows(cur, "change_orders", rows)
        summary = self._change_order_summary(cur, project_id=project_id, contract_id=project["contract_id"])
        conn.close()
        return self._json_response({"items": rows, "summary": summary})

    def _lead_designer_assignments_get(self, lead_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id,name,status FROM customers WHERE id=?", (lead_id,))
        lead = cur.fetchone()
        if not lead:
            conn.close()
            return self._json_response({"error": "Lead not found"}, 404)
        if user.get("role") == "designer":
            conn.close()
            return self._json_response({"error": "Forbidden: designer cannot access leads"}, 403)
        cur.execute(
            """
            SELECT *
            FROM designer_assignments
            WHERE source_type='lead' AND source_id=?
            ORDER BY id DESC
            """,
            (lead_id,),
        )
        rows = [row_to_dict(r) for r in cur.fetchall()]
        self._enrich_resource_rows(cur, "designer_assignments", rows)
        conn.close()
        return self._json_response(rows)

    def _project_designer_assignments_get(self, project_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM projects WHERE id=?", (project_id,))
        if not cur.fetchone():
            conn.close()
            return self._json_response({"error": "Project not found"}, 404)
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return
        cur.execute(
            """
            SELECT *
            FROM designer_assignments
            WHERE source_type='project' AND source_id=?
            ORDER BY id DESC
            """,
            (project_id,),
        )
        rows = [row_to_dict(r) for r in cur.fetchall()]
        self._enrich_resource_rows(cur, "designer_assignments", rows)
        conn.close()
        return self._json_response(rows)

    def _my_designer_assignments_get(self, user):
        role_key = normalize_key(user.get("role") or "")
        conn = get_conn()
        cur = conn.cursor()
        sql = "SELECT * FROM designer_assignments"
        params = []
        clauses = []
        if role_key in {"owner", "admin"}:
            pass
        elif role_key == "designer":
            designer_ids = self._designer_ids_for_user(cur, user)
            if not designer_ids:
                conn.close()
                return self._json_response([])
            ph = ",".join(["?"] * len(designer_ids))
            clauses.append(f"designer_id IN ({ph})")
            params.extend(designer_ids)
        else:
            conn.close()
            return self._json_response({"error": "Forbidden: designer/owner/admin only"}, 403)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id DESC"
        cur.execute(sql, tuple(params))
        rows = [row_to_dict(r) for r in cur.fetchall()]
        self._enrich_resource_rows(cur, "designer_assignments", rows)
        conn.close()
        return self._json_response(rows)

    def _designer_assignment_mark(self, path, user, action):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "designer-assignments":
            return self._json_response({"error": "Not found"}, 404)
        try:
            assignment_id = int(parts[2])
        except (TypeError, ValueError):
            return self._json_response({"error": "Invalid assignment id"}, 400)

        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        role_key = normalize_key(user.get("role") or "")
        if role_key not in {"owner", "admin", "designer"}:
            return self._json_response({"error": "Forbidden: designer/owner/admin only"}, 403)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM designer_assignments WHERE id=?", (assignment_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Assignment not found"}, 404)
        current = row_to_dict(row)

        if role_key == "designer":
            designer_ids = set(self._designer_ids_for_user(cur, user))
            if not designer_ids or int(current.get("designer_id") or 0) not in designer_ids:
                conn.close()
                return self._json_response({"error": "Forbidden: assignment access denied"}, 403)

        status_now = self._designer_assignment_status_key(current.get("status") or "new")

        note_text = str(payload.get("notes") or payload.get("message") or "").strip()
        note_only = str(payload.get("note_only") or "").strip().lower() in {"1", "true", "yes", "on"}

        target_status = status_now
        allowed = True
        changed = False
        if action == "accept":
            target_status = "accepted"
            if status_now not in {"new", "invited", "accepted"}:
                allowed = False
            changed = target_status != status_now
        elif action == "decline":
            target_status = "declined"
            if status_now not in {"new", "invited", "declined"}:
                allowed = False
            changed = target_status != status_now
        elif action == "progress":
            if note_only:
                target_status = status_now
                changed = False
            else:
                target_status = "in_progress"
                if status_now not in {"accepted", "in_progress"}:
                    allowed = False
                changed = target_status != status_now
        elif action == "complete":
            target_status = "completed"
            if status_now not in {"in_progress", "completed"}:
                allowed = False
            changed = target_status != status_now
        else:
            conn.close()
            return self._json_response({"error": "Unsupported action"}, 404)

        if not allowed:
            conn.close()
            return self._json_response({"error": f"Invalid transition: {status_now} -> {target_status}"}, 400)
        if not changed and not note_text:
            conn.close()
            return self._json_response({"error": "No update content"}, 400)

        ts = now_ts()
        notes_value = str(current.get("notes") or "").strip()
        if note_text:
            stamped = f"[{ts}] {note_text}"
            notes_value = f"{notes_value}\n{stamped}".strip() if notes_value else stamped
        responded_at = current.get("responded_at")
        if changed or note_text:
            responded_at = ts

        cur.execute(
            """
            UPDATE designer_assignments
            SET status=?, responded_at=?, notes=?, updated_at=?
            WHERE id=?
            """,
            (target_status, responded_at, notes_value or None, ts, assignment_id),
        )
        conn.commit()
        cur.execute("SELECT * FROM designer_assignments WHERE id=?", (assignment_id,))
        updated = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "designer_assignments", [updated])
        conn.close()
        return self._json_response(updated)

    def _estimate_mark_status(self, path, user, target_status):
        role_key = normalize_key(user.get("role") or "")
        if role_key not in {"owner", "manager"}:
            return self._json_response({"error": "Forbidden: owner/manager only"}, 403)
        if not self._has_module(user, "estimates"):
            return self._json_response({"error": "Forbidden: estimates"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "estimates":
            return self._json_response({"error": "Not found"}, 404)
        try:
            estimate_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid estimate id"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM estimates WHERE id=?", (estimate_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Estimate not found"}, 404)

        existing = row_to_dict(row)
        current = self._estimate_confirm_status_key(existing.get("confirm_status") or existing.get("status"))
        target = self._estimate_confirm_status_key(target_status)
        allowed_from = {
            "sent": {"draft"},
            "confirmed": {"sent"},
            "rejected": {"sent"},
        }
        if current != target and current not in allowed_from.get(target, set()):
            conn.close()
            return self._json_response({"error": f"Invalid transition: {current} -> {target}"}, 400)

        payload = self._read_json_body() or {}
        note = str(payload.get("confirm_note") or "").strip()
        ts = now_ts()
        confirm_at = existing.get("confirmed_at")
        confirm_by = existing.get("confirmed_by")
        if target == "confirmed":
            confirm_at = confirm_at or ts
            confirm_by = confirm_by or user.get("id")

        cur.execute(
            """
            UPDATE estimates
            SET confirm_status=?,
                status=?,
                confirmed_at=?,
                confirmed_by=?,
                confirm_note=CASE WHEN ?<>'' THEN ? ELSE confirm_note END,
                updated_at=?
            WHERE id=?
            """,
            (
                target,
                self._estimate_legacy_status(target),
                confirm_at,
                confirm_by,
                note,
                note,
                ts,
                estimate_id,
            ),
        )
        conn.commit()
        cur.execute("SELECT * FROM estimates WHERE id=?", (estimate_id,))
        item = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "estimates", [item])
        conn.close()
        return self._json_response(item)

    def _public_quote_url(self, token):
        base = (BASE_URL or "").strip().rstrip("/")
        if not base or base.startswith("http://0.0.0.0"):
            base = ""
        return f"{base}/quote/{token}" if base else f"/quote/{token}"

    def _estimate_send_to_customer(self, path, user):
        role_key = normalize_key(user.get("role") or "")
        if role_key not in {"owner", "manager"}:
            return self._json_response({"error": "Forbidden: owner/manager only"}, 403)
        if not self._has_module(user, "estimates"):
            return self._json_response({"error": "Forbidden: estimates"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "estimates":
            return self._json_response({"error": "Not found"}, 404)
        try:
            estimate_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid estimate id"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM estimates WHERE id=?", (estimate_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Estimate not found"}, 404)
        existing = row_to_dict(row)
        current = self._estimate_confirm_status_key(existing.get("confirm_status") or existing.get("status"))
        if current not in {"draft", "sent"}:
            conn.close()
            return self._json_response({"error": f"Cannot send estimate in {current} status"}, 400)
        ts = now_ts()
        token = existing.get("public_token") or secrets.token_urlsafe(24)
        cur.execute(
            """
            UPDATE estimates
            SET public_token=?, sent_at=COALESCE(sent_at,?), confirm_status='sent', status=?,
                updated_at=?
            WHERE id=?
            """,
            (token, ts, self._estimate_legacy_status("sent"), ts, estimate_id),
        )
        conn.commit()
        cur.execute("SELECT * FROM estimates WHERE id=?", (estimate_id,))
        item = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "estimates", [item])
        conn.close()
        item["public_url"] = self._public_quote_url(token)
        return self._json_response(item)

    def _contract_mark_status(self, path, user, target_status):
        role_key = normalize_key(user.get("role") or "")
        if role_key not in {"owner", "manager"}:
            return self._json_response({"error": "Forbidden: owner/manager only"}, 403)
        if not self._has_module(user, "contracts"):
            return self._json_response({"error": "Forbidden: contracts"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "contracts":
            return self._json_response({"error": "Not found"}, 404)
        try:
            contract_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid contract id"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM contracts WHERE id=?", (contract_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Contract not found"}, 404)
        existing = row_to_dict(row)
        project_id = existing.get("project_id")
        if project_id and self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return

        current = self._contract_sign_status_key(existing.get("sign_status") or existing.get("signed_status"))
        target = self._contract_sign_status_key(target_status)
        allowed_from = {
            "sent": {"draft"},
            "signed": {"sent"},
        }
        if current != target and current not in allowed_from.get(target, set()):
            conn.close()
            return self._json_response({"error": f"Invalid transition: {current} -> {target}"}, 400)

        payload = self._read_json_body() or {}
        note = str(payload.get("sign_note") or "").strip()
        ts = now_ts()
        signed_at = existing.get("signed_at")
        signed_by = existing.get("signed_by")
        signed_date = existing.get("signed_date")
        if target == "signed":
            signed_at = signed_at or ts
            signed_by = signed_by or user.get("id")
            signed_date = signed_date or ts[:10]

        cur.execute(
            """
            UPDATE contracts
            SET sign_status=?,
                signed_status=?,
                signed_at=?,
                signed_by=?,
                signed_date=?,
                sign_note=CASE WHEN ?<>'' THEN ? ELSE sign_note END,
                updated_at=?
            WHERE id=?
            """,
            (
                target,
                self._contract_legacy_signed_status(target),
                signed_at,
                signed_by,
                signed_date,
                note,
                note,
                ts,
                contract_id,
            ),
        )
        self._evaluate_contract_payment_milestones(cur, contract_id=contract_id, project_id=project_id)
        if target == "signed" and existing.get("customer_id"):
            cur.execute("UPDATE customers SET status=?, updated_at=? WHERE id=?", ("已签约", ts, existing["customer_id"]))
        if project_id:
            self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        cur.execute("SELECT * FROM contracts WHERE id=?", (contract_id,))
        item = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "contracts", [item])
        conn.close()
        if target == "signed":  # F_ARCHIVE_PATCH_APPLIED
            try:
                self._archive_document("contract", contract_id, lang="en")
            except Exception:
                pass
        return self._json_response(item)

    def _change_order_mark(self, path, user, target_status):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        if not (self._has_module(user, "change_orders") or self._has_module(user, "projects")):
            return self._json_response({"error": "Forbidden: change_orders/projects"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "change-orders":
            return self._json_response({"error": "Not found"}, 404)
        try:
            change_order_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid change order id"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM change_orders WHERE id=?", (change_order_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Change order not found"}, 404)
        project_id = row["project_id"]
        if user.get("role") == "designer" and project_id and self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return

        body_payload = self._read_json_body() or {}
        payload = {"status": target_status}
        if target_status == "approved":
            payload["approved_at"] = now_ts()
            payload["confirmed_at"] = payload["approved_at"]
            payload["confirmed_by"] = user.get("id")
        note = str(body_payload.get("confirm_note") or "").strip()
        if note:
            payload["confirm_note"] = note
        data = self._prepare_change_order_payload(cur, payload, existing=row_to_dict(row))
        ts = now_ts()
        cur.execute(
            """
            UPDATE change_orders
            SET status=?, signed_status=?, approved_at=?, signed_date=?, confirmed_at=?, confirmed_by=?, confirm_note=COALESCE(?,confirm_note), updated_at=?
            WHERE id=?
            """,
            (
                data.get("status"),
                data.get("signed_status"),
                data.get("approved_at"),
                data.get("signed_date"),
                data.get("confirmed_at"),
                data.get("confirmed_by"),
                data.get("confirm_note"),
                ts,
                change_order_id,
            ),
        )
        if project_id:
            self._evaluate_project_payment_triggers(cur, project_id)
            self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        cur.execute("SELECT * FROM change_orders WHERE id=?", (change_order_id,))
        item = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "change_orders", [item])
        conn.close()
        if target_status == "approved":  # F_ARCHIVE_PATCH_APPLIED
            try:
                self._archive_document("change_order", change_order_id, lang="en")
            except Exception:
                pass
        return self._json_response(item)

    def _archive_document(self, doc_type, source_id, lang="en"):
        """归档 contract / change_order 当前快照到 documents/。失败仅 log,不抛错。  # F_ARCHIVE_PATCH_APPLIED"""
        try:
            import os as _os, json as _json, sqlite3 as _sqlite3
            from datetime import datetime as _dt

            captured = []
            original_html_response = self._html_response

            def _capture(html, status=200):
                captured.append(html)
                return None

            self._html_response = _capture
            try:
                if doc_type == "contract":
                    self._contract_pdf_html(int(source_id), lang, auto_print=False, mode="pdf")
                elif doc_type == "change_order":
                    self._change_order_pdf_html(int(source_id), lang, auto_print=False, mode="pdf")
                else:
                    return
            finally:
                self._html_response = original_html_response

            if not captured:
                return
            html = captured[0]
            if not html:
                return

            base_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data", "documents", doc_type)
            try:
                _os.makedirs(base_dir, exist_ok=True)
            except Exception:
                pass

            conn = get_conn()
            cur = conn.cursor()

            cur.execute(
                "SELECT tags FROM documents WHERE doc_type=?",
                (doc_type,),
            )
            existing_versions = []
            for r in cur.fetchall():
                try:
                    t = _json.loads(r["tags"] or "{}")
                    if int(t.get("source_id") or 0) == int(source_id):
                        existing_versions.append(int(t.get("version") or 0))
                except Exception:
                    continue
            next_version = (max(existing_versions) + 1) if existing_versions else 1

            ts_compact = _dt.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{int(source_id)}_v{next_version}_{ts_compact}.html"
            file_path = _os.path.join(base_dir, file_name)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html)
            except Exception as e:
                sys.stderr.write(f"[archive] write file failed for {doc_type} {source_id}: {e}\n")
                conn.close()
                return

            customer_id = None
            project_id = None
            try:
                if doc_type == "contract":
                    cur.execute("SELECT customer_id, project_id FROM contracts WHERE id=?", (int(source_id),))
                else:
                    cur.execute(
                        "SELECT customer_id, project_id FROM change_orders WHERE id=?",
                        (int(source_id),),
                    )
                row = cur.fetchone()
                if row:
                    customer_id = row["customer_id"] if "customer_id" in row.keys() else None
                    project_id = row["project_id"] if "project_id" in row.keys() else None
            except Exception:
                pass

            tags_json = _json.dumps({"source_id": int(source_id), "version": next_version, "lang": lang})
            url_path = f"/data/documents/{doc_type}/{file_name}"
            ts_iso = now_ts()
            try:
                cur.execute(
                    "INSERT INTO documents(customer_id,project_id,doc_type,file_name,tags,url,visibility,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (customer_id, project_id, doc_type, file_name, tags_json, url_path, "Team", ts_iso, ts_iso),
                )
                conn.commit()
            except Exception as e:
                sys.stderr.write(f"[archive] DB insert failed for {doc_type} {source_id}: {e}\n")
            finally:
                conn.close()

            sys.stderr.write(f"[archive] OK {doc_type}/{file_name}\n")
        except Exception as e:
            try:
                sys.stderr.write(f"[archive] failed for {doc_type} {source_id}: {e}\n")
            except Exception:
                pass

    def _handle_documents_get(self, path, query, user):
        """List archived documents. GET /api/documents  # F_ARCHIVE_PATCH_APPLIED"""
        parts = [p for p in path.split("/") if p]
        if len(parts) != 2 or parts[0] != "api" or parts[1] != "documents":
            return False
        if not (self._has_module(user, "contracts") or self._has_module(user, "projects") or self._has_module(user, "change_orders")):
            self._json_response({"error": "Forbidden: contracts/projects/change_orders"}, 403)
            return True
        try:
            doc_type_filter = (query.get("doc_type") or [None])[0] if isinstance(query, dict) else None
        except Exception:
            doc_type_filter = None
        try:
            source_id_filter = (query.get("source_id") or [None])[0] if isinstance(query, dict) else None
        except Exception:
            source_id_filter = None

        conn = get_conn()
        cur = conn.cursor()
        sql = "SELECT id, customer_id, project_id, doc_type, file_name, tags, url, visibility, created_at, updated_at FROM documents WHERE 1=1"
        params = []
        if doc_type_filter:
            sql += " AND doc_type=?"
            params.append(str(doc_type_filter))
        sql += " ORDER BY created_at DESC LIMIT 100"
        cur.execute(sql, params)
        rows = [row_to_dict(r) for r in cur.fetchall()]

        if source_id_filter:
            try:
                import json as _json
                target_sid = int(source_id_filter)
                filtered = []
                for r in rows:
                    try:
                        t = _json.loads(r.get("tags") or "{}")
                        if int(t.get("source_id") or 0) == target_sid:
                            filtered.append(r)
                    except Exception:
                        continue
                rows = filtered
            except Exception:
                pass

        conn.close()
        self._json_response(rows)
        return True

    def _document_template_set_default(self, path, user):
        if not self._require_document_template_manage(user):
            return
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "document-templates" or parts[3] != "set-default":
            return self._json_response({"error": "Not found"}, 404)
        try:
            template_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid template id"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM document_templates WHERE id=?", (template_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Template not found"}, 404)
        item = row_to_dict(row)
        self._set_document_template_default(cur, template_id, item.get("template_type"), item.get("project_type"))
        conn.commit()
        cur.execute("SELECT * FROM document_templates WHERE id=?", (template_id,))
        updated = row_to_dict(cur.fetchone())
        conn.close()
        return self._json_response(updated)

    def _followup_row_dict(self, row):
        item = row_to_dict(row)
        item["completed"] = bool(item.get("completed"))
        return item

    def _fetch_due_today_followups(self, cur, user, limit=20):
        if user.get("role") == "designer":
            return []
        if not (self._has_module(user, "customers") or self._has_module(user, "dashboard")):
            return []
        today = to_iso_date(datetime.now())
        cur.execute(
            """
            SELECT
                f.id,f.customer_id,f.estimate_id,f.user_id,f.followup_type,f.content,f.result,f.next_followup_at,f.completed,f.created_at,f.updated_at,
                c.name AS customer_name,c.phone AS customer_phone,c.status AS customer_status,
                u.username AS user_name
            FROM customer_followups f
            JOIN customers c ON c.id=f.customer_id
            LEFT JOIN users u ON u.id=f.user_id
            WHERE f.completed=0
              AND f.next_followup_at IS NOT NULL
              AND TRIM(f.next_followup_at)!=''
              AND date(substr(f.next_followup_at,1,10)) <= date(?)
            ORDER BY datetime(substr(f.next_followup_at,1,19)) ASC, f.id DESC
            LIMIT ?
            """,
            (today, int(limit)),
        )
        return [self._followup_row_dict(r) for r in cur.fetchall()]

    def _fetch_stale_customers(self, cur, user, limit=20):
        if user.get("role") == "designer":
            return []
        if not (self._has_module(user, "customers") or self._has_module(user, "dashboard")):
            return []
        today = to_iso_date(datetime.now())
        cur.execute(
            """
            WITH latest AS (
                SELECT customer_id, MAX(created_at) AS last_followup_at
                FROM customer_followups
                GROUP BY customer_id
            ),
            next_open AS (
                SELECT f.customer_id, f.id AS open_followup_id, f.next_followup_at
                FROM customer_followups f
                JOIN (
                    SELECT customer_id, MIN(COALESCE(next_followup_at,'9999-12-31T23:59:59')) AS min_next
                    FROM customer_followups
                    WHERE completed=0
                    GROUP BY customer_id
                ) x ON x.customer_id=f.customer_id AND COALESCE(f.next_followup_at,'9999-12-31T23:59:59')=x.min_next
                WHERE f.completed=0
            )
            SELECT
                c.id AS customer_id,
                c.name,
                c.phone,
                c.status,
                COALESCE(l.last_followup_at, c.created_at) AS last_followup_at,
                n.next_followup_at,
                n.open_followup_id
            FROM customers c
            LEFT JOIN latest l ON l.customer_id=c.id
            LEFT JOIN next_open n ON n.customer_id=c.id
            WHERE c.status NOT IN ('已签约','已流失','Signed','Lost')
              AND (julianday(date(?)) - julianday(date(substr(COALESCE(l.last_followup_at, c.created_at),1,10)))) > 3
            ORDER BY datetime(substr(COALESCE(l.last_followup_at, c.created_at),1,19)) ASC
            LIMIT ?
            """,
            (today, int(limit)),
        )
        return [row_to_dict(r) for r in cur.fetchall()]

    def _customer_followups_get(self, customer_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM customers WHERE id=?", (customer_id,))
        if not cur.fetchone():
            conn.close()
            return self._json_response({"error": "Customer not found"}, 404)
        cur.execute(
            """
            SELECT
                f.id,f.customer_id,f.estimate_id,f.user_id,f.followup_type,f.content,f.result,f.next_followup_at,f.completed,f.created_at,f.updated_at,
                u.username AS user_name,
                e.title AS estimate_title
            FROM customer_followups f
            LEFT JOIN users u ON u.id=f.user_id
            LEFT JOIN estimates e ON e.id=f.estimate_id
            WHERE f.customer_id=?
            ORDER BY f.created_at DESC, f.id DESC
            """,
            (customer_id,),
        )
        rows = [self._followup_row_dict(r) for r in cur.fetchall()]
        conn.close()
        return self._json_response(rows)

    def _customer_followups_post(self, path, user):
        if not self._has_module(user, "customers"):
            return self._json_response({"error": "Forbidden: customers"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "customers" or parts[3] != "followups":
            return self._json_response({"error": "Not found"}, 404)
        try:
            customer_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid customer id"}, 400)
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        followup_type = normalize_key(payload.get("followup_type") or "note")
        if followup_type not in {"phone", "text", "wechat", "email", "visit", "note"}:
            followup_type = "note"
        content = (payload.get("content") or "").strip()
        if not content:
            return self._json_response({"error": "content is required"}, 400)
        result = (payload.get("result") or "").strip()
        next_followup_at = (payload.get("next_followup_at") or "").strip()
        estimate_id = payload.get("estimate_id")
        if estimate_id in ("", None):
            estimate_id = None
        else:
            try:
                estimate_id = int(estimate_id)
            except (TypeError, ValueError):
                return self._json_response({"error": "estimate_id must be integer"}, 400)
        completed = 1 if bool(payload.get("completed")) else 0
        ts = now_ts()

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM customers WHERE id=?", (customer_id,))
        if not cur.fetchone():
            conn.close()
            return self._json_response({"error": "Customer not found"}, 404)
        if estimate_id:
            cur.execute("SELECT id FROM estimates WHERE id=? AND customer_id=?", (estimate_id, customer_id))
            if not cur.fetchone():
                conn.close()
                return self._json_response({"error": "estimate_id does not belong to customer"}, 400)
        cur.execute(
            """
            INSERT INTO customer_followups(
                customer_id,estimate_id,user_id,followup_type,content,result,next_followup_at,completed,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                customer_id,
                estimate_id,
                user.get("id"),
                followup_type,
                content,
                result or None,
                next_followup_at or None,
                completed,
                ts,
                ts,
            ),
        )
        followup_id = cur.lastrowid
        cur.execute("UPDATE customers SET updated_at=? WHERE id=?", (ts, customer_id))
        conn.commit()
        cur.execute(
            """
            SELECT
                f.id,f.customer_id,f.estimate_id,f.user_id,f.followup_type,f.content,f.result,f.next_followup_at,f.completed,f.created_at,f.updated_at,
                u.username AS user_name,
                e.title AS estimate_title
            FROM customer_followups f
            LEFT JOIN users u ON u.id=f.user_id
            LEFT JOIN estimates e ON e.id=f.estimate_id
            WHERE f.id=?
            """,
            (followup_id,),
        )
        row = self._followup_row_dict(cur.fetchone())
        conn.close()
        return self._json_response(row, 201)

    def _followup_mark_completed(self, path, user):
        if not (self._has_module(user, "dashboard") or self._has_module(user, "customers")):
            return self._json_response({"error": "Forbidden: dashboard/customers"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "followups" or parts[3] != "mark-completed":
            return self._json_response({"error": "Not found"}, 404)
        try:
            followup_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid followup id"}, 400)
        conn = get_conn()
        cur = conn.cursor()
        ts = now_ts()
        cur.execute("UPDATE customer_followups SET completed=1, updated_at=? WHERE id=?", (ts, followup_id))
        if cur.rowcount == 0:
            conn.close()
            return self._json_response({"error": "Followup not found"}, 404)
        cur.execute("SELECT customer_id FROM customer_followups WHERE id=?", (followup_id,))
        r = cur.fetchone()
        if r and r["customer_id"]:
            cur.execute("UPDATE customers SET updated_at=? WHERE id=?", (ts, r["customer_id"]))
        conn.commit()
        cur.execute("SELECT * FROM customer_followups WHERE id=?", (followup_id,))
        row = self._followup_row_dict(cur.fetchone())
        conn.close()
        return self._json_response({"ok": True, "followup": row})

    def _followups_due_today_get(self, user):
        conn = get_conn()
        cur = conn.cursor()
        rows = self._fetch_due_today_followups(cur, user, limit=50)
        conn.close()
        return self._json_response(rows)

    def _followups_stale_customers_get(self, user):
        conn = get_conn()
        cur = conn.cursor()
        rows = self._fetch_stale_customers(cur, user, limit=50)
        conn.close()
        return self._json_response(rows)

    def _notification_key(self, *, user_id=None, role_scope=None, notification_type="", related_entity_type=None, related_entity_id=None):
        uid = int(user_id) if user_id not in (None, "") else None
        scope = normalize_key(role_scope or "") or ""
        ntype = normalize_key(notification_type or "") or ""
        ent = normalize_key(related_entity_type or "") or ""
        rid = int(related_entity_id) if related_entity_id not in (None, "") else 0
        return (uid, scope, ntype, ent, rid)

    def _create_notification_if_missing(
        self,
        cur,
        *,
        user_id=None,
        role_scope=None,
        notification_type="",
        title="",
        content="",
        related_entity_type=None,
        related_entity_id=None,
        action_url="",
    ):
        key = self._notification_key(
            user_id=user_id,
            role_scope=role_scope,
            notification_type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
        )
        uid, scope, ntype, ent, rid = key
        cur.execute(
            """
            SELECT id
            FROM notifications
            WHERE COALESCE(user_id,0)=COALESCE(?,0)
              AND COALESCE(LOWER(role_scope),'')=?
              AND COALESCE(LOWER(type),'')=?
              AND COALESCE(LOWER(related_entity_type),'')=?
              AND COALESCE(related_entity_id,0)=?
            ORDER BY id DESC
            LIMIT 1
            """,
            (uid, scope, ntype, ent, rid),
        )
        existed = cur.fetchone()
        if existed:
            return existed["id"], False

        ts = now_ts()
        cur.execute(
            """
            INSERT INTO notifications(
                user_id,role_scope,type,title,content,related_entity_type,related_entity_id,action_url,is_read,created_at,read_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                uid,
                scope or None,
                ntype,
                (title or "").strip() or ntype,
                (content or "").strip(),
                ent or None,
                rid if rid else None,
                (action_url or "").strip(),
                0,
                ts,
                None,
            ),
        )
        return cur.lastrowid, True

    def _notification_related_project_id(self, cur, row):
        related_type = normalize_key((row or {}).get("related_entity_type") or "")
        related_id = (row or {}).get("related_entity_id")
        if related_id in (None, ""):
            return None
        try:
            related_id = int(related_id)
        except (TypeError, ValueError):
            return None
        if related_type == "project":
            return related_id
        if related_type == "contract":
            cur.execute("SELECT project_id FROM contracts WHERE id=?", (related_id,))
            r = cur.fetchone()
            return r["project_id"] if r else None
        if related_type == "estimate":
            cur.execute("SELECT project_id,contract_id FROM estimates WHERE id=?", (related_id,))
            r = cur.fetchone()
            if not r:
                return None
            if r["project_id"]:
                return r["project_id"]
            if r["contract_id"]:
                cur.execute("SELECT project_id FROM contracts WHERE id=?", (r["contract_id"],))
                c = cur.fetchone()
                return c["project_id"] if c else None
            return None
        if related_type == "change_order":
            cur.execute("SELECT project_id FROM change_orders WHERE id=?", (related_id,))
            r = cur.fetchone()
            return r["project_id"] if r else None
        if related_type == "payment":
            cur.execute(
                """
                SELECT c.project_id
                FROM contract_payment_milestones m
                LEFT JOIN contracts c ON c.id=m.contract_id
                WHERE m.id=?
                """,
                (related_id,),
            )
            r = cur.fetchone()
            return r["project_id"] if r else None
        return None

    def _notification_row_visible(self, cur, user, row):
        item = row_to_dict(row) if isinstance(row, sqlite3.Row) else dict(row or {})
        uid = item.get("user_id")
        if uid not in (None, "") and int(uid) != int(user.get("id") or 0):
            return False
        role_key = normalize_key(user.get("role") or "")
        scope_key = normalize_key(item.get("role_scope") or "all")
        if uid in (None, "") and scope_key not in {"", "all", role_key}:
            return False

        ntype = normalize_key(item.get("type") or "")
        if ntype == "followup_due" and not (self._has_module(user, "customers") or self._has_module(user, "dashboard")):
            return False
        if ntype == "estimate_pending_confirmation" and not (self._has_module(user, "estimates") or self._has_module(user, "dashboard")):
            return False
        if ntype == "contract_pending_sign" and not (self._has_module(user, "contracts") or self._has_module(user, "dashboard")):
            return False
        if ntype == "payment_reminder_triggered" and not (
            self._has_module(user, "contracts")
            or self._has_module(user, "projects")
            or self._has_module(user, "finance")
            or self._has_module(user, "dashboard")
        ):
            return False
        if ntype == "change_order_pending" and not (
            self._has_module(user, "change_orders") or self._has_module(user, "projects") or self._has_module(user, "dashboard")
        ):
            return False
        if ntype in {"designer_commission_pending", "project_completed"} and not (
            self._has_module(user, "projects") or self._has_module(user, "dashboard")
        ):
            return False

        if role_key == "designer":
            project_id = self._notification_related_project_id(cur, item)
            if project_id and not self._project_accessible(cur, user, project_id):
                return False
            if ntype in {"followup_due", "estimate_pending_confirmation", "contract_pending_sign", "payment_reminder_triggered"}:
                return False
        return True

    def _sync_notifications(self, cur):
        # Keep payment/commission states fresh before deriving notifications.
        cur.execute("SELECT id FROM projects ORDER BY id ASC")
        for r in cur.fetchall():
            pid = r["id"]
            self._evaluate_project_payment_triggers(cur, pid)
            self._recalc_designer_commission_for_project(cur, pid)

        managed_types = {
            "followup_due",
            "estimate_pending_confirmation",
            "contract_pending_sign",
            "payment_reminder_triggered",
            "designer_commission_pending",
            "project_completed",
            "change_order_pending",
        }
        active_keys = set()
        notify_followup_due_enabled = self._system_setting_bool(cur, "notify_followup_due_enabled", True)
        notify_estimate_pending_enabled = self._system_setting_bool(cur, "notify_estimate_pending_enabled", True)
        notify_contract_pending_enabled = self._system_setting_bool(cur, "notify_contract_pending_enabled", True)
        notify_payment_reminder_enabled = self._system_setting_bool(cur, "notify_payment_reminder_enabled", True)
        notify_designer_commission_enabled = self._system_setting_bool(cur, "notify_designer_commission_enabled", True)
        notify_project_completed_enabled = self._system_setting_bool(cur, "notify_project_completed_enabled", True)
        notify_change_order_pending_enabled = self._system_setting_bool(cur, "notify_change_order_pending_enabled", True)

        def emit(user_id, role_scope, notification_type, title, content, related_entity_type, related_entity_id, action_url):
            key = self._notification_key(
                user_id=user_id,
                role_scope=role_scope,
                notification_type=notification_type,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
            )
            active_keys.add(key)
            self._create_notification_if_missing(
                cur,
                user_id=user_id,
                role_scope=role_scope,
                notification_type=notification_type,
                title=title,
                content=content,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
                action_url=action_url,
            )

        def emit_owner_manager(notification_type, title, content, related_entity_type, related_entity_id, action_url):
            emit(None, "owner", notification_type, title, content, related_entity_type, related_entity_id, action_url)
            emit(None, "manager", notification_type, title, content, related_entity_type, related_entity_id, action_url)

        # 1) 今日待跟进
        if notify_followup_due_enabled:
            cur.execute(
                """
                SELECT
                    f.id,
                    f.customer_id,
                    f.next_followup_at,
                    f.content,
                    c.name AS customer_name,
                    c.phone AS customer_phone
                FROM customer_followups f
                LEFT JOIN customers c ON c.id=f.customer_id
                WHERE COALESCE(f.completed,0)=0
                  AND f.next_followup_at IS NOT NULL
                  AND TRIM(f.next_followup_at)<>''
                  AND DATE(substr(f.next_followup_at,1,10)) <= DATE('now','localtime')
                ORDER BY COALESCE(f.next_followup_at,f.created_at) ASC
                """
            )
            for item in cur.fetchall():
                title = f"今日待跟进：{item['customer_name'] or ('客户#' + str(item['customer_id']))}"
                content = f"{item['customer_phone'] or '-'} · {item['content'] or ''} · 下次跟进 {item['next_followup_at'] or '-'}"
                emit_owner_manager(
                    "followup_due",
                    title,
                    content,
                    "followup",
                    item["id"],
                    f"customers/{item['customer_id']}" if item["customer_id"] else "",
                )

        # 2) 报价待确认
        if notify_estimate_pending_enabled:
            cur.execute(
                """
                SELECT e.id,e.title,e.total_amount,c.name AS customer_name
                FROM estimates e
                LEFT JOIN customers c ON c.id=e.customer_id
                WHERE (
                    LOWER(COALESCE(e.confirm_status,''))='sent'
                    OR (
                        (e.confirm_status IS NULL OR TRIM(e.confirm_status)='')
                        AND (LOWER(COALESCE(e.status,''))='sent' OR e.status='已发送')
                    )
                )
                ORDER BY e.id DESC
                """
            )
            for item in cur.fetchall():
                emit_owner_manager(
                    "estimate_pending_confirmation",
                    f"待客户确认报价：{item['title'] or ('报价#' + str(item['id']))}",
                    f"{item['customer_name'] or '-'} · 金额 ${int(round(float(item['total_amount'] or 0))):,}",
                    "estimate",
                    item["id"],
                    f"estimates/{item['id']}",
                )

        # 3) 合同待签署
        if notify_contract_pending_enabled:
            cur.execute(
                """
                SELECT ct.id,ct.contract_no,ct.total_amount,c.name AS customer_name
                FROM contracts ct
                LEFT JOIN customers c ON c.id=ct.customer_id
                WHERE (
                    LOWER(COALESCE(ct.sign_status,''))='sent'
                    OR (
                        (ct.sign_status IS NULL OR TRIM(ct.sign_status)='')
                        AND (ct.signed_status='Sent' OR ct.signed_status='已发送')
                    )
                )
                ORDER BY ct.id DESC
                """
            )
            for item in cur.fetchall():
                emit_owner_manager(
                    "contract_pending_sign",
                    f"待签署合同：{item['contract_no'] or ('合同#' + str(item['id']))}",
                    f"{item['customer_name'] or '-'} · 金额 ${int(round(float(item['total_amount'] or 0))):,}",
                    "contract",
                    item["id"],
                    f"contracts/{item['id']}",
                )

        # 4) 付款节点触发待催办
        if notify_payment_reminder_enabled:
            cur.execute(
                """
                SELECT
                    m.id,
                    m.contract_id,
                    m.name AS milestone_name,
                    c.contract_no,
                    p.id AS project_id,
                    p.name AS project_name,
                    cu.name AS customer_name
                FROM contract_payment_milestones m
                LEFT JOIN contracts c ON c.id=m.contract_id
                LEFT JOIN projects p ON p.contract_id=c.id
                LEFT JOIN customers cu ON cu.id=c.customer_id
                WHERE COALESCE(m.triggered,0)=1 AND COALESCE(m.paid,0)=0
                ORDER BY m.id DESC
                """
            )
            for item in cur.fetchall():
                title = f"付款节点待催办：{item['milestone_name'] or ('节点#' + str(item['id']))}"
                content = f"{item['project_name'] or '-'} / {item['customer_name'] or '-'} / {item['contract_no'] or '-'}"
                target_url = f"contracts/{item['contract_id']}" if item["contract_id"] else (f"projects/{item['project_id']}" if item["project_id"] else "")
                emit_owner_manager(
                    "payment_reminder_triggered",
                    title,
                    content,
                    "payment",
                    item["id"],
                    target_url,
                )

        # 5) 设计师佣金待结算
        if notify_designer_commission_enabled:
            cur.execute(
                """
                SELECT
                    dc.id,
                    dc.project_id,
                    dc.designer_id,
                    dc.commission_amount,
                    p.name AS project_name
                FROM designer_commissions dc
                LEFT JOIN projects p ON p.id=dc.project_id
                WHERE LOWER(COALESCE(dc.status,''))='pending_settlement'
                  AND dc.designer_id IS NOT NULL
                ORDER BY dc.id DESC
                """
            )
            for item in cur.fetchall():
                designer_id = item["designer_id"]
                title = f"佣金待结算：{item['project_name'] or ('项目#' + str(item['project_id']))}"
                content = f"佣金金额 ${int(round(float(item['commission_amount'] or 0))):,}"
                emit(
                    designer_id,
                    "designer",
                    "designer_commission_pending",
                    title,
                    content,
                    "project",
                    item["project_id"],
                    f"my_commissions/{item['project_id']}",
                )
                emit_owner_manager(
                    "designer_commission_pending",
                    title,
                    content,
                    "project",
                    item["project_id"],
                    f"projects/{item['project_id']}",
                )

        # 6) 项目完工
        if notify_project_completed_enabled:
            cur.execute(
                """
                SELECT id,name,designer_id,progress_pct,status
                FROM projects
                WHERE COALESCE(progress_pct,0) >= 100
                   OR LOWER(COALESCE(status,'')) IN ('completed','done')
                   OR status IN ('已完工','已完成','Completed')
                ORDER BY id DESC
                """
            )
            for item in cur.fetchall():
                title = f"项目已完工：{item['name'] or ('项目#' + str(item['id']))}"
                content = f"当前进度 {int(round(float(item['progress_pct'] or 0)))}%"
                emit_owner_manager(
                    "project_completed",
                    title,
                    content,
                    "project",
                    item["id"],
                    f"projects/{item['id']}",
                )
                if item["designer_id"]:
                    emit(
                        item["designer_id"],
                        "designer",
                        "project_completed",
                        title,
                        content,
                        "project",
                        item["id"],
                        f"projects/{item['id']}",
                    )

        # 7) 变更单待确认（已发送）
        if notify_change_order_pending_enabled:
            cur.execute(
                """
                SELECT
                    co.id,
                    co.project_id,
                    co.title,
                    p.name AS project_name,
                    p.designer_id
                FROM change_orders co
                LEFT JOIN projects p ON p.id=co.project_id
                WHERE (
                    LOWER(COALESCE(co.status,''))='sent'
                    OR co.status='已发送'
                    OR co.signed_status='Sent'
                )
                ORDER BY co.id DESC
                """
            )
            for item in cur.fetchall():
                project_id = item["project_id"]
                title = f"变更单待确认：{item['title'] or ('变更单#' + str(item['id']))}"
                content = f"所属项目：{item['project_name'] or '-'}"
                action_url = f"projects/{project_id}" if project_id else f"change_orders/{item['id']}"
                emit_owner_manager(
                    "change_order_pending",
                    title,
                    content,
                    "change_order",
                    item["id"],
                    action_url,
                )
                if item["designer_id"]:
                    emit(
                        item["designer_id"],
                        "designer",
                        "change_order_pending",
                        title,
                        content,
                        "change_order",
                        item["id"],
                        action_url,
                    )

        managed = tuple(sorted(managed_types))
        ph = ",".join(["?"] * len(managed))
        cur.execute(
            f"""
            SELECT id,user_id,role_scope,type,related_entity_type,related_entity_id
            FROM notifications
            WHERE COALESCE(is_read,0)=0
              AND COALESCE(LOWER(type),'') IN ({ph})
            """,
            managed,
        )
        to_mark_read = []
        for row in cur.fetchall():
            row_key = self._notification_key(
                user_id=row["user_id"],
                role_scope=row["role_scope"],
                notification_type=row["type"],
                related_entity_type=row["related_entity_type"],
                related_entity_id=row["related_entity_id"],
            )
            if row_key not in active_keys:
                to_mark_read.append(row["id"])
        if to_mark_read:
            ts = now_ts()
            ph2 = ",".join(["?"] * len(to_mark_read))
            cur.execute(
                f"UPDATE notifications SET is_read=1, read_at=COALESCE(read_at,?) WHERE id IN ({ph2})",
                (ts, *to_mark_read),
            )

    def _notifications_get(self, query, user):
        conn = get_conn()
        cur = conn.cursor()
        self._sync_notifications(cur)
        unread_only = str((query.get("unread_only", ["0"])[0] or "0")).strip() in {"1", "true", "yes", "on"}
        type_filter = normalize_key((query.get("type", [""])[0] or "").strip())
        try:
            limit = int((query.get("limit", ["50"])[0] or "50").strip())
        except ValueError:
            limit = 50
        limit = max(1, min(limit, 200))

        role_key = normalize_key(user.get("role") or "")
        sql = """
            SELECT *
            FROM notifications n
            WHERE (
                n.user_id=?
                OR (n.user_id IS NULL AND (COALESCE(LOWER(n.role_scope),'') IN ('', 'all', ?)))
            )
        """
        params = [user.get("id"), role_key]
        if unread_only:
            sql += " AND COALESCE(n.is_read,0)=0"
        if type_filter:
            sql += " AND COALESCE(LOWER(n.type),'')=?"
            params.append(type_filter)
        sql += " ORDER BY n.id DESC LIMIT ?"
        params.append(limit)
        cur.execute(sql, tuple(params))
        rows = []
        for row in cur.fetchall():
            if not self._notification_row_visible(cur, user, row):
                continue
            item = row_to_dict(row)
            item["is_read"] = int(item.get("is_read") or 0)
            rows.append(item)
        conn.commit()
        conn.close()
        return self._json_response(rows)

    def _notifications_unread_count_get(self, user):
        conn = get_conn()
        cur = conn.cursor()
        self._sync_notifications(cur)
        role_key = normalize_key(user.get("role") or "")
        cur.execute(
            """
            SELECT *
            FROM notifications n
            WHERE COALESCE(n.is_read,0)=0
              AND (
                n.user_id=?
                OR (n.user_id IS NULL AND (COALESCE(LOWER(n.role_scope),'') IN ('', 'all', ?)))
              )
            ORDER BY n.id DESC
            """,
            (user.get("id"), role_key),
        )
        count = 0
        for row in cur.fetchall():
            if self._notification_row_visible(cur, user, row):
                count += 1
        conn.commit()
        conn.close()
        return self._json_response({"unread_count": count})

    def _notification_mark_read(self, path, user):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "notifications" or parts[3] != "mark-read":
            return self._json_response({"error": "Not found"}, 404)
        try:
            notification_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid notification id"}, 400)
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM notifications WHERE id=?", (notification_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Notification not found"}, 404)
        if not self._notification_row_visible(cur, user, row):
            conn.close()
            return self._json_response({"error": "Forbidden: notification access denied"}, 403)
        ts = now_ts()
        cur.execute(
            "UPDATE notifications SET is_read=1, read_at=COALESCE(read_at,?) WHERE id=?",
            (ts, notification_id),
        )
        conn.commit()
        cur.execute("SELECT * FROM notifications WHERE id=?", (notification_id,))
        item = row_to_dict(cur.fetchone())
        item["is_read"] = int(item.get("is_read") or 0)
        conn.close()
        return self._json_response({"ok": True, "notification": item})

    def _notifications_mark_all_read(self, user):
        conn = get_conn()
        cur = conn.cursor()
        self._sync_notifications(cur)
        role_key = normalize_key(user.get("role") or "")
        cur.execute(
            """
            SELECT *
            FROM notifications n
            WHERE COALESCE(n.is_read,0)=0
              AND (
                n.user_id=?
                OR (n.user_id IS NULL AND (COALESCE(LOWER(n.role_scope),'') IN ('', 'all', ?)))
              )
            """,
            (user.get("id"), role_key),
        )
        visible_ids = []
        for row in cur.fetchall():
            if self._notification_row_visible(cur, user, row):
                visible_ids.append(row["id"])
        if visible_ids:
            ts = now_ts()
            ph = ",".join(["?"] * len(visible_ids))
            cur.execute(
                f"UPDATE notifications SET is_read=1, read_at=COALESCE(read_at,?) WHERE id IN ({ph})",
                (ts, *visible_ids),
            )
        conn.commit()
        conn.close()
        return self._json_response({"ok": True, "updated": len(visible_ids)})

    def _ensure_quote_default_followup(self, cur, customer_id, estimate_id, user_id):
        cur.execute("SELECT COUNT(1) c FROM customer_followups WHERE customer_id=? AND completed=0", (customer_id,))
        if int((cur.fetchone() or {"c": 0})["c"] or 0) > 0:
            return False
        ts = now_ts()
        followup_days = self._system_setting_int(cur, "default_followup_days_after_estimate", 3)
        if followup_days <= 0:
            followup_days = 3
        if followup_days > 60:
            followup_days = 60
        next_at = (datetime.now() + timedelta(days=followup_days)).strftime("%Y-%m-%dT%H:%M")
        cur.execute(
            """
            INSERT INTO customer_followups(
                customer_id,estimate_id,user_id,followup_type,content,result,next_followup_at,completed,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (
                customer_id,
                estimate_id,
                user_id,
                "note",
                f"已生成报价，建议{followup_days}天后回访",
                "等待客户反馈",
                next_at,
                0,
                ts,
                ts,
            ),
        )
        return True

    def _customer_recent_followups_get(self, customer_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM customers WHERE id=?", (customer_id,))
        if not cur.fetchone():
            conn.close()
            return self._json_response({"error": "Customer not found"}, 404)
        cur.execute(
            """
            SELECT id,customer_id,followup_date,content,next_action,owner,created_at,updated_at
            FROM followups
            WHERE customer_id=?
            ORDER BY followup_date DESC, id DESC
            LIMIT 6
            """,
            (customer_id,),
        )
        rows = [row_to_dict(r) for r in cur.fetchall()]
        conn.close()
        return self._json_response(rows)

    def _find_customer_by_phone(self, cur, phone):
        target = canonical_phone(phone)
        if not target:
            return None
        cur.execute("SELECT * FROM customers WHERE phone IS NOT NULL AND TRIM(phone)!='' ORDER BY id ASC")
        for r in cur.fetchall():
            if canonical_phone(r["phone"]) == target:
                return r
        return None

    def _upsert_lead_from_intake(self, cur, payload, merge_existing=False):
        name = (payload.get("name") or "").strip()
        phone = (payload.get("phone") or "").strip()
        email = (payload.get("email") or "").strip()
        address = (payload.get("address") or "").strip()
        source_channel = normalize_key(payload.get("source_channel") or "manual")
        if source_channel not in SOURCE_CHANNEL_SET:
            source_channel = "manual"
        source_note = (payload.get("source_note") or "").strip()
        inquiry_type = normalize_key(payload.get("inquiry_type") or "other")
        if inquiry_type not in INQUIRY_TYPE_SET:
            inquiry_type = "other"
        preferred_contact_method = normalize_key(payload.get("preferred_contact_method") or "")
        if preferred_contact_method and preferred_contact_method not in CONTACT_METHOD_SET:
            preferred_contact_method = "phone"
        message = (payload.get("message") or payload.get("notes") or "").strip()
        ts = now_ts()

        if not (name or phone or email):
            return {"error": "At least one of name/phone/email is required"}, 400

        existed = self._find_customer_by_phone(cur, phone) if phone else None
        if existed and not merge_existing:
            row = row_to_dict(existed)
            return {
                "exists": True,
                "created": False,
                "merged": False,
                "require_merge_confirm": True,
                "customer": row,
                "message": "Phone already exists",
            }, 409

        if existed:
            row = row_to_dict(existed)
            updates = {}
            if name and (not row.get("name") or str(row.get("name")).strip().startswith("客户#")):
                updates["name"] = name
            if email and not row.get("email"):
                updates["email"] = email
            if address and not row.get("primary_address"):
                updates["primary_address"] = address
            if source_channel:
                updates["source_channel"] = source_channel
            if source_note:
                updates["source_note"] = source_note
                updates["source"] = source_note
            elif source_channel and not row.get("source"):
                updates["source"] = source_channel
            if inquiry_type:
                updates["inquiry_type"] = inquiry_type
                demand_label = inquiry_type_to_demand_label(inquiry_type)
                if demand_label:
                    updates["demand_type"] = demand_label
            if preferred_contact_method:
                updates["preferred_contact_method"] = preferred_contact_method
            if message:
                old_note = (row.get("notes") or "").strip()
                updates["notes"] = message if not old_note else f"{old_note}\n{message}"
            if normalize_key(row.get("status")) not in {"signed", "lost"}:
                updates["status"] = "新线索"
            updates["updated_at"] = ts
            set_expr = ",".join([f"{k}=?" for k in updates.keys()])
            cur.execute(f"UPDATE customers SET {set_expr} WHERE id=?", tuple(updates.values()) + (row["id"],))
            if message:
                self._insert_followup_compatible(
                    cur=cur,
                    customer_id=row["id"],
                    followup_date=to_iso_date(datetime.now()),
                    content=f"线索补充：{message}",
                    next_action="销售联系并确认需求",
                    owner=(source_channel or "manual").upper(),
                )
            cur.execute("SELECT * FROM customers WHERE id=?", (row["id"],))
            merged = row_to_dict(cur.fetchone())
            return {"exists": True, "created": False, "merged": True, "customer": merged}, 200

        display_name = name or phone or email or "新线索"
        cur.execute(
            """
            INSERT INTO customers(
                name,phone,email,source,source_channel,source_note,demand_type,inquiry_type,preferred_contact_method,
                budget_range,status,primary_address,other_addresses,notes,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                display_name,
                phone or None,
                email or None,
                (source_note or source_channel),
                source_channel,
                source_note or None,
                inquiry_type_to_demand_label(inquiry_type) or None,
                inquiry_type,
                preferred_contact_method or None,
                None,
                "新线索",
                address or None,
                None,
                message or None,
                ts,
                ts,
            ),
        )
        customer_id = cur.lastrowid
        if message:
            self._insert_followup_compatible(
                cur=cur,
                customer_id=customer_id,
                followup_date=to_iso_date(datetime.now()),
                content=f"线索录入：{message}",
                next_action="销售联系并确认需求",
                owner=(source_channel or "manual").upper(),
            )
        cur.execute("SELECT * FROM customers WHERE id=?", (customer_id,))
        created = row_to_dict(cur.fetchone())
        return {"exists": False, "created": True, "merged": False, "customer": created}, 201

    def _leads_intake(self, raw_query):
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        user = self._current_user()
        query = parse_qs(raw_query or "")
        provided_key = self.headers.get("X-Webhook-Key") or query.get("key", [None])[0]
        merge_existing = bool(payload.get("merge_existing"))

        conn = get_conn()
        cur = conn.cursor()
        if not user:
            expected_key = self._expected_webhook_key(cur)
            if not expected_key or provided_key != expected_key:
                conn.close()
                return self._json_response({"error": "Invalid webhook key"}, 401)
        elif not self._has_module(user, "customers"):
            conn.close()
            return self._json_response({"error": "Forbidden: customers"}, 403)

        result, status = self._upsert_lead_from_intake(cur, payload, merge_existing=merge_existing)
        if status < 400:
            conn.commit()
        conn.close()
        return self._json_response(result, status)

    def _upsert_designer_application_from_intake(self, cur, payload):
        name = str(payload.get("name") or "").strip()
        phone = str(payload.get("phone") or "").strip()
        email = str(payload.get("email") or "").strip()
        company_name = str(payload.get("company_name") or payload.get("company") or "").strip()
        service_area = str(payload.get("service_area") or payload.get("area") or "").strip()
        specialty = str(payload.get("specialty") or payload.get("inquiry_type") or "").strip()
        years_experience = str(payload.get("years_experience") or payload.get("experience") or "").strip()
        portfolio_url = str(payload.get("portfolio_url") or payload.get("portfolio") or "").strip()
        source_channel = normalize_key(payload.get("source_channel") or "website")
        if source_channel not in SOURCE_CHANNEL_SET:
            source_channel = "website"
        message = str(payload.get("message") or payload.get("notes") or "").strip()

        if not (name or phone or email):
            return {"error": "At least one of name/phone/email is required"}, 400

        if not name:
            name = email or phone or "Designer Applicant"

        ts = now_ts()
        cur.execute(
            """
            INSERT INTO designer_applications(
                name,phone,email,company_name,service_area,specialty,years_experience,portfolio_url,
                source_channel,message,status,contacted_at,reviewed_at,reviewed_by,review_note,designer_id,user_id,
                created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                name,
                phone or None,
                email or None,
                company_name or None,
                service_area or None,
                specialty or None,
                years_experience or None,
                portfolio_url or None,
                source_channel,
                message or None,
                "pending",
                None,
                None,
                None,
                None,
                None,
                None,
                ts,
                ts,
            ),
        )
        app_id = cur.lastrowid
        cur.execute("SELECT * FROM designer_applications WHERE id=?", (app_id,))
        row = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "designer_applications", [row])
        return {"created": True, "application": row}, 201

    def _designer_applications_intake(self, raw_query):
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        user = self._current_user()
        query = parse_qs(raw_query or "")
        provided_key = self.headers.get("X-Webhook-Key") or query.get("key", [None])[0]

        conn = get_conn()
        cur = conn.cursor()
        if not user:
            expected_key = self._expected_webhook_key(cur)
            if not expected_key or provided_key != expected_key:
                conn.close()
                return self._json_response({"error": "Invalid webhook key"}, 401)
        else:
            if not self._require_designer_pipeline_manage(user, "designer_applications"):
                conn.close()
                return

        result, status = self._upsert_designer_application_from_intake(cur, payload)
        if status < 400:
            conn.commit()
        conn.close()
        return self._json_response(result, status)

    def _designer_application_approve(self, path, user):
        if not self._require_designer_pipeline_manage(user, "designer_applications"):
            return
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "designer-applications" or parts[3] != "approve":
            return self._json_response({"error": "Not found"}, 404)
        try:
            application_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid application id"}, 400)

        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM designer_applications WHERE id=?", (application_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Application not found"}, 404)
        app = row_to_dict(row)
        status_key = self._designer_app_status_key(app.get("status"))
        if status_key == "approved" and app.get("designer_id") and app.get("user_id"):
            self._enrich_resource_rows(cur, "designer_applications", [app])
            conn.close()
            return self._json_response({"approved": False, "application": app, "message": "Already approved"})

        review_note = str(payload.get("review_note") or app.get("review_note") or "").strip()
        requested_modules = self._designer_modules_from_payload(payload.get("modules"))
        target_language = str(payload.get("language") or "").strip().lower()
        if target_language not in {"zh", "en", "es"}:
            target_language = DEFAULT_LANGUAGE

        designer_id = app.get("designer_id")
        ts = now_ts()
        if designer_id:
            cur.execute("SELECT * FROM designers WHERE id=?", (designer_id,))
            drow = cur.fetchone()
        else:
            drow = None

        if drow:
            d = row_to_dict(drow)
            cur.execute(
                """
                UPDATE designers
                SET name=?,phone=?,email=?,company_name=?,service_area=?,specialty=?,years_experience=?,portfolio_url=?,
                    status='active',updated_at=?
                WHERE id=?
                """,
                (
                    app.get("name") or d.get("name"),
                    app.get("phone") or d.get("phone"),
                    app.get("email") or d.get("email"),
                    app.get("company_name") or d.get("company_name"),
                    app.get("service_area") or d.get("service_area"),
                    app.get("specialty") or d.get("specialty"),
                    app.get("years_experience") or d.get("years_experience"),
                    app.get("portfolio_url") or d.get("portfolio_url"),
                    ts,
                    d.get("id"),
                ),
            )
            designer_id = d.get("id")
        else:
            cur.execute(
                """
                INSERT INTO designers(
                    application_id,user_id,name,phone,email,company_name,service_area,specialty,years_experience,portfolio_url,
                    status,notes,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    application_id,
                    None,
                    app.get("name") or "Designer",
                    app.get("phone"),
                    app.get("email"),
                    app.get("company_name"),
                    app.get("service_area"),
                    app.get("specialty"),
                    app.get("years_experience"),
                    app.get("portfolio_url"),
                    "active",
                    review_note or None,
                    ts,
                    ts,
                ),
            )
            designer_id = cur.lastrowid

        supplied_user_id = payload.get("user_id")
        user_id = int(supplied_user_id) if str(supplied_user_id or "").isdigit() else (app.get("user_id") or None)
        username = str(payload.get("username") or "").strip()
        password = str(payload.get("password") or "").strip()
        temp_password = None

        existing_user = None
        if user_id:
            cur.execute("SELECT * FROM users WHERE id=?", (user_id,))
            existing_user = cur.fetchone()
            if not existing_user:
                conn.close()
                return self._json_response({"error": "user_id not found"}, 404)
        elif username:
            cur.execute("SELECT * FROM users WHERE username=?", (username,))
            existing_user = cur.fetchone()

        if existing_user:
            user_row = row_to_dict(existing_user)
            user_id = user_row.get("id")
            if not username:
                username = user_row.get("username")
            updates = []
            values = []
            updates.append("role=?")
            values.append("designer")
            updates.append("linked_designer_id=?")
            values.append(designer_id)
            updates.append("language=?")
            values.append(target_language or user_row.get("language") or DEFAULT_LANGUAGE)
            updates.append("modules_json=?")
            values.append(json.dumps(requested_modules, ensure_ascii=False))
            if password:
                updates.append("password=?")
                values.append(password)
            updates.append("updated_at=?")
            values.append(ts)
            values.append(user_id)
            cur.execute(f"UPDATE users SET {','.join(updates)} WHERE id=?", values)
        else:
            base_username = username
            if not base_username:
                email_local = normalize_key((app.get("email") or "").split("@")[0]) if app.get("email") else ""
                base_username = email_local or f"designer{application_id}"
            base_username = re.sub(r"[^a-z0-9_.-]+", "", base_username.lower()) or f"designer{application_id}"
            candidate = base_username
            suffix = 1
            while True:
                cur.execute("SELECT id FROM users WHERE username=?", (candidate,))
                if not cur.fetchone():
                    break
                suffix += 1
                candidate = f"{base_username}_{suffix}"
            username = candidate
            if not password:
                temp_password = secrets.token_urlsafe(8)
                password = temp_password
            cur.execute(
                """
                INSERT INTO users(username,password,role,linked_designer_id,language,modules_json,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    username,
                    password,
                    "designer",
                    designer_id,
                    target_language or DEFAULT_LANGUAGE,
                    json.dumps(requested_modules, ensure_ascii=False),
                    ts,
                    ts,
                ),
            )
            user_id = cur.lastrowid

        cur.execute(
            "UPDATE designers SET user_id=?,application_id=COALESCE(application_id,?),updated_at=? WHERE id=?",
            (user_id, application_id, ts, designer_id),
        )
        self._upsert_designer_permissions(cur, designer_id, requested_modules, updated_by=user.get("id"))

        cur.execute(
            """
            UPDATE designer_applications
            SET status='approved',reviewed_at=?,reviewed_by=?,review_note=?,designer_id=?,user_id=?,updated_at=?
            WHERE id=?
            """,
            (ts, user.get("id"), review_note or None, designer_id, user_id, ts, application_id),
        )
        conn.commit()

        cur.execute("SELECT * FROM designer_applications WHERE id=?", (application_id,))
        app_row = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "designer_applications", [app_row])
        cur.execute("SELECT * FROM designers WHERE id=?", (designer_id,))
        designer_row = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "designers", [designer_row])
        conn.close()
        return self._json_response(
            {
                "approved": True,
                "application": app_row,
                "designer": designer_row,
                "user": {
                    "id": user_id,
                    "username": username,
                    "role": "designer",
                    "linked_designer_id": designer_id,
                    "modules": requested_modules,
                    "temporary_password": temp_password,
                },
            }
        )

    def _designer_application_reject(self, path, user):
        if not self._require_designer_pipeline_manage(user, "designer_applications"):
            return
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "designer-applications" or parts[3] != "reject":
            return self._json_response({"error": "Not found"}, 404)
        try:
            application_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid application id"}, 400)

        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        review_note = str(payload.get("review_note") or "").strip()

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM designer_applications WHERE id=?", (application_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Application not found"}, 404)
        ts = now_ts()
        cur.execute(
            """
            UPDATE designer_applications
            SET status='rejected',reviewed_at=?,reviewed_by=?,review_note=?,updated_at=?
            WHERE id=?
            """,
            (ts, user.get("id"), review_note or None, ts, application_id),
        )
        conn.commit()
        cur.execute("SELECT * FROM designer_applications WHERE id=?", (application_id,))
        result = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "designer_applications", [result])
        conn.close()
        return self._json_response({"rejected": True, "application": result})

    def _designer_permissions_post(self, path, user):
        if not self._require_designer_pipeline_manage(user, "designers"):
            return
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "designers" or parts[3] != "permissions":
            return self._json_response({"error": "Not found"}, 404)
        try:
            designer_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid designer id"}, 400)
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM designers WHERE id=?", (designer_id,))
        drow = cur.fetchone()
        if not drow:
            conn.close()
            return self._json_response({"error": "Designer not found"}, 404)
        modules = self._designer_modules_from_payload(payload.get("modules"))
        effective_modules = self._upsert_designer_permissions(cur, designer_id, modules, updated_by=user.get("id"))
        ts = now_ts()
        cur.execute("UPDATE designers SET updated_at=? WHERE id=?", (ts, designer_id))
        user_id = drow["user_id"]
        if user_id:
            cur.execute(
                """
                UPDATE users
                SET role='designer', linked_designer_id=?, modules_json=?, updated_at=?
                WHERE id=?
                """,
                (designer_id, json.dumps(effective_modules, ensure_ascii=False), ts, user_id),
            )
        conn.commit()
        cur.execute("SELECT * FROM designers WHERE id=?", (designer_id,))
        data = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "designers", [data])
        conn.close()
        return self._json_response({"ok": True, "designer": data, "modules": effective_modules})

    def _customer_generate_estimate(self, path, user):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden"}, 403)
        if not self._has_module(user, "estimates"):
            return self._json_response({"error": "Forbidden: estimates"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "customers" or parts[3] != "generate-estimate":
            return self._json_response({"error": "Not found"}, 404)
        try:
            customer_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid customer id"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM customers WHERE id=?", (customer_id,))
        customer = cur.fetchone()
        if not customer:
            conn.close()
            return self._json_response({"error": "Customer not found"}, 404)

        demand = (customer["demand_type"] or "").strip()
        inquiry_type = (customer["inquiry_type"] or "").strip()
        inquiry_label = inquiry_type_to_demand_label(inquiry_type)
        default_type = inquiry_label if inquiry_label else (demand or "装修")
        base_name = (customer["name"] or "").strip()
        title = f"{base_name} {default_type}方案".strip()
        cur.execute("SELECT COUNT(1) c FROM estimates WHERE customer_id=?", (customer_id,))
        seq = int(cur.fetchone()["c"] or 0) + 1
        version = f"v{seq}"
        ts = now_ts()
        customer_status = normalize_key(customer["status"] or "")
        lead_id = customer_id if customer_status in {
            "lead",
            "measuring",
            "quoting",
            "new_lead",
            "contacted",
            "site_visit_booked",
            "quoted",
        } else None
        address = (customer["primary_address"] or "").strip()
        cur.execute(
            """
            INSERT INTO estimates(
                customer_id,lead_id,project_id,contract_id,title,address,version,status,confirm_status,valid_until,subtotal,markup_rate,manual_adjustment,total_amount,line_items_json,rounding_mode,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                customer_id,
                lead_id,
                None,
                None,
                title or f"客户#{customer_id}方案",
                address,
                version,
                "Draft",
                "draft",
                None,
                0,
                0,
                0,
                0,
                "[]",
                "10",
                ts,
                ts,
            ),
        )
        estimate_id = cur.lastrowid
        cur.execute("SELECT * FROM estimates WHERE id=?", (estimate_id,))
        row = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, "estimates", [row])
        self._ensure_quote_default_followup(cur, customer_id=customer_id, estimate_id=estimate_id, user_id=user.get("id"))
        if customer_status not in {"signed", "lost"}:
            cur.execute("UPDATE customers SET status=?, updated_at=? WHERE id=?", ("已报价", ts, customer_id))
        conn.commit()
        conn.close()
        return self._json_response({"created": True, "estimate": row}, 201)

    def _project_designer_commission_get(self, project_id, user):
        conn = get_conn()
        cur = conn.cursor()
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return
        summary = self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        conn.close()
        return self._json_response(summary or {"project_id": project_id, "status": "ungenerated"})

    def _project_designer_commission_recalculate(self, path, user):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 5 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "designer-commission" or parts[4] != "recalculate":
            return self._json_response({"error": "Not found"}, 404)
        try:
            project_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid project id"}, 400)
        conn = get_conn()
        cur = conn.cursor()
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return
        summary = self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        conn.close()
        return self._json_response(summary or {"project_id": project_id, "status": "ungenerated"})

    def _evaluate_project_payment_triggers(self, cur, project_id):
        cur.execute("SELECT contract_id FROM projects WHERE id=?", (project_id,))
        row = cur.fetchone()
        if not row or not row["contract_id"]:
            return
        self._evaluate_contract_payment_milestones(cur, contract_id=row["contract_id"], project_id=project_id)

    def _evaluate_contract_payment_milestones(self, cur, contract_id=None, project_id=None):
        if not contract_id and not project_id:
            return
        if not contract_id and project_id:
            cur.execute("SELECT contract_id FROM projects WHERE id=?", (project_id,))
            p = cur.fetchone()
            contract_id = p["contract_id"] if p else None
        if not contract_id:
            return
        cur.execute("SELECT id,total_amount,signed_status,sign_status FROM contracts WHERE id=?", (contract_id,))
        contract = cur.fetchone()
        if not contract:
            return
        if not project_id:
            cur.execute("SELECT id FROM projects WHERE contract_id=? ORDER BY id ASC LIMIT 1", (contract_id,))
            row = cur.fetchone()
            project_id = row["id"] if row else None

        progress_pct = 0
        stage_states = {}
        if project_id:
            cur.execute("SELECT progress_pct FROM projects WHERE id=?", (project_id,))
            row = cur.fetchone()
            progress_pct = int((row["progress_pct"] if row else 0) or 0)
            cur.execute("SELECT stage_name,status FROM project_stages WHERE project_id=?", (project_id,))
            for st in cur.fetchall():
                stage_states[(st["stage_name"] or "").strip()] = normalize_key(st["status"])

        contract_signed = self._contract_sign_status_key(contract["sign_status"] or contract["signed_status"]) == "signed"
        cur.execute("SELECT * FROM contract_payment_milestones WHERE contract_id=? ORDER BY id ASC", (contract_id,))
        ts = now_ts()
        for m in cur.fetchall():
            item = row_to_dict(m)
            if int(item.get("paid") or 0) == 1 or int(item.get("triggered") or 0) == 1:
                continue
            trigger_type = normalize_key(item.get("trigger_type"))
            trigger_stage = (item.get("trigger_stage") or "").strip()
            should_trigger = False
            if trigger_type == "contract_signed":
                should_trigger = contract_signed
            elif trigger_type == "stage_started":
                st = stage_states.get(trigger_stage)
                should_trigger = st in {"in_progress", "done"}
            elif trigger_type == "stage_done":
                st = stage_states.get(trigger_stage)
                should_trigger = st == "done"
            elif trigger_type == "progress_percent":
                should_trigger = progress_pct >= int(item.get("trigger_progress") or 0)
            if should_trigger:
                cur.execute(
                    """
                    UPDATE contract_payment_milestones
                    SET triggered=1, triggered_at=COALESCE(triggered_at,?), updated_at=?
                    WHERE id=?
                    """,
                    (ts, ts, item["id"]),
                )

    def _is_contract_fully_paid(self, cur, contract_id):
        if not contract_id:
            return False
        cur.execute("SELECT COUNT(1) c FROM contract_payment_milestones WHERE contract_id=?", (contract_id,))
        milestone_count = (cur.fetchone() or {"c": 0})["c"]
        if milestone_count > 0:
            cur.execute("SELECT COUNT(1) c FROM contract_payment_milestones WHERE contract_id=? AND paid=0", (contract_id,))
            return (cur.fetchone() or {"c": 0})["c"] == 0
        cur.execute("SELECT COUNT(1) c FROM project_payments WHERE contract_id=?", (contract_id,))
        payment_count = (cur.fetchone() or {"c": 0})["c"]
        if payment_count > 0:
            cur.execute("SELECT COUNT(1) c FROM project_payments WHERE contract_id=? AND status!='Paid'", (contract_id,))
            return (cur.fetchone() or {"c": 0})["c"] == 0
        cur.execute("SELECT sign_status,signed_status FROM contracts WHERE id=?", (contract_id,))
        row = cur.fetchone()
        if not row:
            return False
        return self._contract_sign_status_key(row["sign_status"] or row["signed_status"]) == "signed"

    def _recalc_designer_commission_for_project(self, cur, project_id):
        cur.execute(
            """
            SELECT id,contract_id,designer_id,designer_name,designer_commission_type,designer_commission_value,designer_commission_base
            FROM projects
            WHERE id=?
            """,
            (project_id,),
        )
        project = cur.fetchone()
        if not project:
            return None
        designer_id = project["designer_id"]
        if not designer_id:
            cur.execute("DELETE FROM designer_commissions WHERE project_id=?", (project_id,))
            return {
                "project_id": project_id,
                "designer_id": None,
                "commission_amount": 0,
                "status": "ungenerated",
                "eligible": False,
                "settlement_mode": "acceptance_and_contract_paid",
            }

        base_contract_amount = 0.0
        if project["contract_id"]:
            cur.execute("SELECT total_amount FROM contracts WHERE id=?", (project["contract_id"],))
            row = cur.fetchone()
            base_contract_amount = float((row["total_amount"] if row else 0) or 0)
        cur.execute(
            "SELECT amount_delta,affect_designer_commission,status,signed_status FROM change_orders WHERE project_id=?",
            (project_id,),
        )
        approved_commissionable_change_amount = 0.0
        approved_non_commissionable_change_amount = 0.0
        for co in cur.fetchall():
            item = row_to_dict(co)
            if not self._is_change_order_approved(item):
                continue
            amount_delta = float(item.get("amount_delta") or 0)
            if int(item.get("affect_designer_commission") or 0) == 1:
                approved_commissionable_change_amount += amount_delta
            else:
                approved_non_commissionable_change_amount += amount_delta
        change_order_amount = round(approved_commissionable_change_amount + approved_non_commissionable_change_amount, 2)

        commission_type = normalize_key(project["designer_commission_type"] or "percent")
        if commission_type not in {"percent", "fixed"}:
            commission_type = "percent"
        commission_value = float(project["designer_commission_value"] or 0)
        commission_base = (project["designer_commission_base"] or "base_contract_only").strip() or "base_contract_only"
        if commission_base not in {"base_contract_only", "include_change_orders"}:
            commission_base = "base_contract_only"

        calc_change_amount = approved_commissionable_change_amount if commission_base == "include_change_orders" else 0
        base_amount_for_calc = base_contract_amount + calc_change_amount
        commission_amount = round(base_amount_for_calc * commission_value / 100, 2) if commission_type == "percent" else round(commission_value, 2)

        cur.execute(
            "SELECT status FROM project_stages WHERE project_id=? AND stage_name='验收' ORDER BY stage_order ASC,id ASC LIMIT 1",
            (project_id,),
        )
        acceptance_row = cur.fetchone()
        if not acceptance_row:
            cur.execute("SELECT status FROM project_stages WHERE project_id=? ORDER BY stage_order DESC,id DESC LIMIT 1", (project_id,))
            acceptance_row = cur.fetchone()
        acceptance_done = normalize_key(acceptance_row["status"] if acceptance_row else "") == "done"
        contract_paid = self._is_contract_fully_paid(cur, project["contract_id"])
        eligible = acceptance_done and contract_paid

        cur.execute("SELECT id,status FROM designer_commissions WHERE project_id=? ORDER BY id ASC", (project_id,))
        existing = cur.fetchall()
        keep_row = existing[0] if existing else None
        if len(existing) > 1:
            ids = [str(r["id"]) for r in existing[1:]]
            cur.execute(f"DELETE FROM designer_commissions WHERE id IN ({','.join(['?'] * len(ids))})", ids)

        target_status = "pending_settlement" if eligible else "ungenerated"
        if keep_row and normalize_key(keep_row["status"]) == "settled":
            target_status = "settled"

        ts = now_ts()
        if keep_row:
            cur.execute(
                """
                UPDATE designer_commissions
                SET designer_id=?, base_contract_amount=?, change_order_amount=?, commission_type=?, commission_value=?,
                    commission_base=?, commission_amount=?, status=?, updated_at=?
                WHERE id=?
                """,
                (
                    designer_id,
                    base_contract_amount,
                    calc_change_amount,
                    commission_type,
                    commission_value,
                    commission_base,
                    commission_amount,
                    target_status,
                    ts,
                    keep_row["id"],
                ),
            )
            commission_id = keep_row["id"]
        else:
            cur.execute(
                """
                INSERT INTO designer_commissions(
                    project_id,designer_id,base_contract_amount,change_order_amount,commission_type,commission_value,
                    commission_base,commission_amount,status,note,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    project_id,
                    designer_id,
                    base_contract_amount,
                    calc_change_amount,
                    commission_type,
                    commission_value,
                    commission_base,
                    commission_amount,
                    target_status,
                    "",
                    ts,
                    ts,
                ),
            )
            commission_id = cur.lastrowid

        return {
            "id": commission_id,
            "project_id": project_id,
            "designer_id": designer_id,
            "designer_name": project["designer_name"],
            "base_contract_amount": base_contract_amount,
            "change_order_amount": change_order_amount,
            "approved_change_commissionable_amount": round(approved_commissionable_change_amount, 2),
            "approved_change_non_commissionable_amount": round(approved_non_commissionable_change_amount, 2),
            "commission_calc_base_amount": round(base_amount_for_calc, 2),
            "commission_type": commission_type,
            "commission_value": commission_value,
            "commission_base": commission_base,
            "commission_amount": commission_amount,
            "status": target_status,
            "eligible": eligible,
            "acceptance_done": acceptance_done,
            "contract_paid": contract_paid,
            "settlement_mode": "acceptance_and_contract_paid",
        }

    def _normalize_site_log(self, row):
        item = row_to_dict(row)
        photos = []
        try:
            parsed = json.loads(item.get("photos_json") or "[]")
            if isinstance(parsed, list):
                photos = [str(x) for x in parsed if str(x).strip()]
        except json.JSONDecodeError:
            photos = []
        return {
            "id": item.get("id"),
            "project_id": item.get("project_id"),
            "log_date": item.get("log_date"),
            "content": item.get("work_summary") or "",
            "image_url": photos[0] if photos else "",
            "photos": photos,
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
        }

    def _project_logs_get(self, project_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id,project_type,stage_template_id FROM projects WHERE id=?", (project_id,))
        project_row = cur.fetchone()
        if not project_row:
            conn.close()
            return self._json_response({"error": "Project not found"}, 404)
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return
        cur.execute(
            """
            SELECT * FROM site_logs
            WHERE project_id=?
            ORDER BY log_date DESC, id DESC
            """,
            (project_id,),
        )
        rows = [self._normalize_site_log(r) for r in cur.fetchall()]
        conn.close()
        return self._json_response(rows)

    def _project_logs_post(self, path, user):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "logs":
            return self._json_response({"error": "Not found"}, 404)
        try:
            project_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid project id"}, 400)

        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        content = (payload.get("content") or "").strip()
        if not content:
            return self._json_response({"error": "content is required"}, 400)
        log_date = (payload.get("log_date") or to_iso_date(datetime.now())).strip()
        image_url = (payload.get("image_url") or "").strip()
        photos_json = json.dumps([image_url], ensure_ascii=False) if image_url else "[]"
        ts = now_ts()

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id,project_type,stage_template_id FROM projects WHERE id=?", (project_id,))
        raw_project = cur.fetchone()
        if not raw_project:
            conn.close()
            return self._json_response({"error": "Project not found"}, 404)
        project_row = row_to_dict(raw_project)
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return

        cur.execute(
            """
            INSERT INTO site_logs(project_id,log_date,work_summary,crew_info,materials_info,photos_json,issue_note,template_used,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?)
            """,
            (project_id, log_date, content, "", "", photos_json, "", "Manual", ts, ts),
        )
        log_id = cur.lastrowid
        conn.commit()
        cur.execute("SELECT * FROM site_logs WHERE id=?", (log_id,))
        row = cur.fetchone()
        conn.close()
        return self._json_response(self._normalize_site_log(row), 201)

    def _project_progress(self, project_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id,name,progress_pct FROM projects WHERE id=?", (project_id,))
        p = cur.fetchone()
        if not p:
            conn.close()
            return self._json_response({"error": "Project not found"}, 404)
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return
        self._init_default_project_stages(cur, project_id)
        self._evaluate_project_payment_triggers(cur, project_id)
        self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        cur.execute("SELECT id,name,progress_pct FROM projects WHERE id=?", (project_id,))
        p = cur.fetchone()
        cur.execute("SELECT * FROM project_stages WHERE project_id=? ORDER BY stage_order ASC, id ASC", (project_id,))
        rows = [row_to_dict(r) for r in cur.fetchall()]
        conn.close()
        return self._json_response({"project": row_to_dict(p), "stages": rows})

    def _projects_progress_summary(self, user):
        conn = get_conn()
        cur = conn.cursor()
        if user.get("role") == "designer":
            cur.execute("SELECT id,name,progress_pct FROM projects WHERE designer_id=? ORDER BY id DESC", (user.get("id"),))
        else:
            cur.execute("SELECT id,name,progress_pct FROM projects ORDER BY id DESC")
        projects = [row_to_dict(r) for r in cur.fetchall()]
        out = []
        for p in projects:
            self._init_default_project_stages(cur, p["id"])
            self._evaluate_project_payment_triggers(cur, p["id"])
            self._recalc_designer_commission_for_project(cur, p["id"])
            cur.execute("SELECT id,stage_name,stage_order,status FROM project_stages WHERE project_id=? ORDER BY stage_order ASC,id ASC", (p["id"],))
            stages = [row_to_dict(r) for r in cur.fetchall()]
            cur.execute("SELECT progress_pct FROM projects WHERE id=?", (p["id"],))
            fresh = cur.fetchone()
            out.append({"project_id": p["id"], "name": p["name"], "progress_pct": (fresh["progress_pct"] if fresh else p.get("progress_pct")) or 0, "stages": stages})
        conn.commit()
        conn.close()
        return self._json_response(out)

    def _init_project_progress(self, path, user):
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        parts = [p for p in path.split("/") if p]
        if len(parts) != 5 or parts[0] != "api" or parts[1] != "projects" or parts[3] != "progress" or parts[4] != "init":
            return self._json_response({"error": "Not found"}, 404)
        try:
            project_id = int(parts[2])
        except ValueError:
            return self._json_response({"error": "Invalid project id"}, 400)
        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id,project_type,stage_template_id,estimate_id FROM projects WHERE id=?", (project_id,))
        raw_project = cur.fetchone()
        if not raw_project:
            conn.close()
            return self._json_response({"error": "Project not found"}, 404)
        project_row = row_to_dict(raw_project)
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return

        stage_names = []
        selected_template_id = None
        if payload.get("stages") and isinstance(payload.get("stages"), list):
            stage_names = [str(s).strip() for s in payload.get("stages") if str(s).strip()]
        elif payload.get("template_id"):
            try:
                selected_template_id = int(payload.get("template_id"))
            except (TypeError, ValueError):
                conn.close()
                return self._json_response({"error": "Invalid template_id"}, 400)
            cur.execute("SELECT id FROM project_stage_templates WHERE id=?", (selected_template_id,))
            if not cur.fetchone():
                conn.close()
                return self._json_response({"error": "Template not found"}, 404)
            stage_names = self._stage_template_stage_names(cur, selected_template_id)
        elif project_row.get("stage_template_id"):
            selected_template_id = int(project_row.get("stage_template_id"))
            stage_names = self._stage_template_stage_names(cur, selected_template_id)

        if not stage_names:
            selected_template_id = self._resolve_default_stage_template_id(cur, project_row.get("project_type"))
            stage_names = self._stage_template_stage_names(cur, selected_template_id) if selected_template_id else list(DEFAULT_PROJECT_STAGES)
        stage_names = self._append_unique_stage_names(
            stage_names,
            self._estimate_custom_payment_stage_names(cur, project_row.get("estimate_id")),
        )

        if selected_template_id:
            cur.execute(
                "UPDATE projects SET stage_template_id=COALESCE(?,stage_template_id), updated_at=? WHERE id=?",
                (selected_template_id, now_ts(), project_id),
            )
        self._replace_project_stages(cur, project_id, stage_names)
        self._evaluate_project_payment_triggers(cur, project_id)
        self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        cur.execute("SELECT * FROM project_stages WHERE project_id=? ORDER BY stage_order ASC,id ASC", (project_id,))
        rows = [row_to_dict(r) for r in cur.fetchall()]
        conn.close()
        return self._json_response({"ok": True, "project_id": project_id, "stages": rows})

    def _replace_stage_template_items(self, cur, template_id, names):
        ts = now_ts()
        cleaned = [str(x).strip() for x in (names or []) if str(x).strip()]
        if not cleaned:
            cleaned = list(DEFAULT_PROJECT_STAGES)
        cur.execute("DELETE FROM project_stage_template_items WHERE template_id=?", (template_id,))
        for idx, step_name in enumerate(cleaned, start=1):
            cur.execute(
                """
                INSERT INTO project_stage_template_items(template_id,step_name,step_order,is_active,created_at,updated_at)
                VALUES (?,?,?,?,?,?)
                """,
                (template_id, step_name, idx, 1, ts, ts),
            )
        self._sync_stage_template_stages_json(cur, template_id)

    def _handle_stage_templates_get(self, path, query, user):
        if path == "/api/project-stage-templates":
            if not self._require_module(user, "stage_templates"):
                return True
            self._resource_get("/api/project_stage_templates", query, user)
            return True
        if path.startswith("/api/project-stage-templates/") and path.endswith("/items"):
            if not self._require_module(user, "stage_templates"):
                return True
            parts = [p for p in path.split("/") if p]
            if len(parts) != 4:
                self._json_response({"error": "Not found"}, 404)
                return True
            try:
                template_id = int(parts[2])
            except ValueError:
                self._json_response({"error": "Invalid template id"}, 400)
                return True
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id FROM project_stage_templates WHERE id=?", (template_id,))
            if not cur.fetchone():
                conn.close()
                self._json_response({"error": "Template not found"}, 404)
                return True
            rows = self._get_stage_template_items(cur, template_id)
            self._enrich_resource_rows(cur, "project_stage_template_items", rows)
            conn.close()
            self._json_response(rows)
            return True
        if path.startswith("/api/project-stage-templates/"):
            if not self._require_module(user, "stage_templates"):
                return True
            mapped = path.replace("/api/project-stage-templates/", "/api/project_stage_templates/", 1)
            self._resource_get(mapped, query, user)
            return True
        return False

    def _handle_stage_templates_post(self, path, user):
        if not path.startswith("/api/project-stage-templates"):
            return False
        if not self._require_module(user, "stage_templates"):
            return True
        if path == "/api/project-stage-templates":
            return self._resource_post("/api/project_stage_templates", user)
        if path.startswith("/api/project-stage-templates/") and path.endswith("/copy"):
            if user.get("role") == "designer":
                return self._json_response({"error": "Forbidden: designer read-only"}, 403)
            parts = [p for p in path.split("/") if p]
            if len(parts) != 4:
                return self._json_response({"error": "Not found"}, 404)
            try:
                template_id = int(parts[2])
            except ValueError:
                return self._json_response({"error": "Invalid template id"}, 400)
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM project_stage_templates WHERE id=?", (template_id,))
            src = cur.fetchone()
            if not src:
                conn.close()
                return self._json_response({"error": "Template not found"}, 404)
            src = row_to_dict(src)
            ts = now_ts()
            cur.execute(
                """
                INSERT INTO project_stage_templates(name,project_type,is_default,is_active,stages_json,notes,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    f"{src.get('name') or 'Template'} Copy",
                    self._normalize_stage_template_project_type(src.get("project_type")) or "custom",
                    0,
                    1,
                    src.get("stages_json") or "[]",
                    src.get("notes") or "",
                    ts,
                    ts,
                ),
            )
            new_id = cur.lastrowid
            items = self._get_stage_template_items(cur, template_id)
            for idx, item in enumerate(items, start=1):
                cur.execute(
                    """
                    INSERT INTO project_stage_template_items(template_id,step_name,step_order,is_active,created_at,updated_at)
                    VALUES (?,?,?,?,?,?)
                    """,
                    (new_id, item.get("step_name"), idx, int(item.get("is_active") or 1), ts, ts),
                )
            self._sync_stage_template_stages_json(cur, new_id)
            conn.commit()
            cur.execute("SELECT * FROM project_stage_templates WHERE id=?", (new_id,))
            row = row_to_dict(cur.fetchone())
            self._enrich_resource_rows(cur, "project_stage_templates", [row])
            conn.close()
            return self._json_response({"created": True, "template": row}, 201)
        if path.startswith("/api/project-stage-templates/") and path.endswith("/set-default"):
            if user.get("role") == "designer":
                return self._json_response({"error": "Forbidden: designer read-only"}, 403)
            parts = [p for p in path.split("/") if p]
            if len(parts) != 4:
                return self._json_response({"error": "Not found"}, 404)
            try:
                template_id = int(parts[2])
            except ValueError:
                return self._json_response({"error": "Invalid template id"}, 400)
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id,project_type FROM project_stage_templates WHERE id=?", (template_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return self._json_response({"error": "Template not found"}, 404)
            project_type = self._normalize_stage_template_project_type(row.get("project_type")) or "custom"
            self._set_stage_template_default(cur, template_id, project_type)
            conn.commit()
            cur.execute("SELECT * FROM project_stage_templates WHERE id=?", (template_id,))
            item = row_to_dict(cur.fetchone())
            self._enrich_resource_rows(cur, "project_stage_templates", [item])
            conn.close()
            return self._json_response({"ok": True, "template": item})
        if path.startswith("/api/project-stage-templates/") and path.endswith("/toggle-active"):
            if user.get("role") == "designer":
                return self._json_response({"error": "Forbidden: designer read-only"}, 403)
            parts = [p for p in path.split("/") if p]
            if len(parts) != 4:
                return self._json_response({"error": "Not found"}, 404)
            try:
                template_id = int(parts[2])
            except ValueError:
                return self._json_response({"error": "Invalid template id"}, 400)
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id,is_active,is_default FROM project_stage_templates WHERE id=?", (template_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return self._json_response({"error": "Template not found"}, 404)
            next_active = 0 if int(row.get("is_active") or 0) == 1 else 1
            if int(row.get("is_default") or 0) == 1 and next_active == 0:
                conn.close()
                return self._json_response({"error": "Default template cannot be disabled"}, 400)
            cur.execute(
                "UPDATE project_stage_templates SET is_active=?, updated_at=? WHERE id=?",
                (next_active, now_ts(), template_id),
            )
            conn.commit()
            cur.execute("SELECT * FROM project_stage_templates WHERE id=?", (template_id,))
            item = row_to_dict(cur.fetchone())
            self._enrich_resource_rows(cur, "project_stage_templates", [item])
            conn.close()
            return self._json_response({"ok": True, "template": item})
        if path.startswith("/api/project-stage-templates/") and path.endswith("/items"):
            if user.get("role") == "designer":
                return self._json_response({"error": "Forbidden: designer read-only"}, 403)
            parts = [p for p in path.split("/") if p]
            if len(parts) != 4:
                return self._json_response({"error": "Not found"}, 404)
            try:
                template_id = int(parts[2])
            except ValueError:
                return self._json_response({"error": "Invalid template id"}, 400)
            payload = self._read_json_body()
            if payload is None:
                return self._json_response({"error": "Invalid JSON"}, 400)
            step_name = str(payload.get("step_name") or "").strip()
            if not step_name:
                return self._json_response({"error": "step_name is required"}, 400)
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id FROM project_stage_templates WHERE id=?", (template_id,))
            if not cur.fetchone():
                conn.close()
                return self._json_response({"error": "Template not found"}, 404)
            cur.execute("SELECT COALESCE(MAX(step_order),0) m FROM project_stage_template_items WHERE template_id=?", (template_id,))
            max_order = int((cur.fetchone() or {"m": 0})["m"] or 0)
            ts = now_ts()
            cur.execute(
                """
                INSERT INTO project_stage_template_items(template_id,step_name,step_order,is_active,created_at,updated_at)
                VALUES (?,?,?,?,?,?)
                """,
                (template_id, step_name, max_order + 1, 1, ts, ts),
            )
            step_id = cur.lastrowid
            self._sync_stage_template_stages_json(cur, template_id)
            conn.commit()
            cur.execute("SELECT * FROM project_stage_template_items WHERE id=?", (step_id,))
            row = row_to_dict(cur.fetchone())
            self._enrich_resource_rows(cur, "project_stage_template_items", [row])
            conn.close()
            return self._json_response(row, 201)
        return self._json_response({"error": "Not found"}, 404)

    def _handle_stage_templates_put(self, path, user):
        if path.startswith("/api/project-stage-templates/") and path.endswith("/items"):
            if not self._require_module(user, "stage_templates"):
                return True
            if user.get("role") == "designer":
                return self._json_response({"error": "Forbidden: designer read-only"}, 403)
            parts = [p for p in path.split("/") if p]
            if len(parts) != 4:
                return self._json_response({"error": "Not found"}, 404)
            try:
                template_id = int(parts[2])
            except ValueError:
                return self._json_response({"error": "Invalid template id"}, 400)
            payload = self._read_json_body()
            if payload is None:
                return self._json_response({"error": "Invalid JSON"}, 400)
            items = payload.get("items") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                return self._json_response({"error": "items list is required"}, 400)
            names = [str(x.get("step_name") if isinstance(x, dict) else x).strip() for x in items]
            names = [x for x in names if x]
            if not names:
                return self._json_response({"error": "At least one active step is required"}, 400)
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT id FROM project_stage_templates WHERE id=?", (template_id,))
            if not cur.fetchone():
                conn.close()
                return self._json_response({"error": "Template not found"}, 404)
            self._replace_stage_template_items(cur, template_id, names)
            conn.commit()
            rows = self._get_stage_template_items(cur, template_id)
            self._enrich_resource_rows(cur, "project_stage_template_items", rows)
            conn.close()
            return self._json_response({"ok": True, "items": rows})
        if path.startswith("/api/project-stage-templates/"):
            if not self._require_module(user, "stage_templates"):
                return True
            mapped = path.replace("/api/project-stage-templates/", "/api/project_stage_templates/", 1)
            return self._resource_put(mapped, user)
        if path.startswith("/api/project-stage-template-items/"):
            if not self._require_module(user, "stage_templates"):
                return True
            mapped = path.replace("/api/project-stage-template-items/", "/api/project_stage_template_items/", 1)
            return self._resource_put(mapped, user)
        return False

    def _handle_stage_templates_delete(self, path, user):
        if path.startswith("/api/project-stage-templates/"):
            if not self._require_module(user, "stage_templates"):
                return True
            mapped = path.replace("/api/project-stage-templates/", "/api/project_stage_templates/", 1)
            return self._resource_delete(mapped, user)
        if path.startswith("/api/project-stage-template-items/"):
            if not self._require_module(user, "stage_templates"):
                return True
            mapped = path.replace("/api/project-stage-template-items/", "/api/project_stage_template_items/", 1)
            return self._resource_delete(mapped, user)
        return False

    def _pdf_text(self, lang):
        texts = {
            "zh": {
                "estimate_title": "报价单 / 方案",
                "contract_title": "合同",
                "change_order_title": "变更单",
                "customer": "客户",
                "project": "项目",
                "details": "施工范围 / 明细",
                "line_description": "描述",
                "unit": "单位",
                "unit_price": "单价",
                "estimate_no": "报价编号",
                "contract_no": "合同编号",
                "change_order_no": "变更单编号",
                "date": "日期",
                "address": "地址",
                "phone": "电话",
                "valid_until": "有效期",
                "status": "状态",
                "signed_status": "签字状态",
                "signed_date": "签字日期",
                "category": "分类",
                "qty": "数量",
                "material": "材料",
                "labor": "人工",
                "subtotal": "小计",
                "markup": "加价率",
                "total": "总计",
                "notes": "备注",
                "terms": "条款说明",
                "signature": "签字确认",
                "customer_signature": "客户签字",
                "company_signature": "公司签字",
                "payment_plan": "付款计划",
                "node": "节点",
                "amount": "金额",
                "description": "变更说明",
                "impact_payment_plan": "影响付款计划",
                "affect_designer_commission": "计入设计师佣金",
                "approved_at": "确认时间",
                "status": "状态",
                "yes": "是",
                "no": "否",
                "generated_at": "生成时间",
                "print_doc": "打印",
                "no_line_items": "暂无分项",
                "no_payment_plan": "暂无付款计划",
                "footer_note": "本报价单仅用于本次装修项目沟通与签约参考。",
                "contract_clause_default": "本合同内容由双方确认后执行，未尽事宜以书面补充条款为准。",
                "estimate_note_default": "感谢您的信任，报价有效期内可继续沟通细节并调整方案。",
            },
            "es": {
                "estimate_title": "Presupuesto / Propuesta",
                "contract_title": "Contrato",
                "change_order_title": "Orden de cambio",
                "customer": "Cliente",
                "project": "Proyecto",
                "details": "Alcance / Detalles",
                "line_description": "Descripción",
                "unit": "Unidad",
                "unit_price": "Precio unitario",
                "estimate_no": "No. Presupuesto",
                "contract_no": "No. Contrato",
                "change_order_no": "No. Orden de cambio",
                "date": "Fecha",
                "address": "Dirección",
                "phone": "Teléfono",
                "valid_until": "Válido hasta",
                "status": "Estado",
                "signed_status": "Estado de firma",
                "signed_date": "Fecha de firma",
                "category": "Categoría",
                "qty": "Cantidad",
                "material": "Material",
                "labor": "Mano de obra",
                "subtotal": "Subtotal",
                "markup": "Margen",
                "total": "Total",
                "notes": "Notas",
                "terms": "Cláusulas",
                "signature": "Firmas",
                "customer_signature": "Firma del cliente",
                "company_signature": "Firma de la empresa",
                "payment_plan": "Plan de pagos",
                "node": "Hito",
                "amount": "Monto",
                "description": "Descripción del cambio",
                "impact_payment_plan": "Impacta plan de pago",
                "affect_designer_commission": "Incluye comisión diseñador",
                "approved_at": "Fecha de aprobación",
                "status": "Estado",
                "yes": "Sí",
                "no": "No",
                "generated_at": "Generado en",
                "print_doc": "Imprimir",
                "no_line_items": "Sin partidas",
                "no_payment_plan": "Sin plan de pagos",
                "footer_note": "Este presupuesto se emite para la comunicación y firma del proyecto actual.",
                "contract_clause_default": "Este contrato se ejecutará tras la confirmación de ambas partes.",
                "estimate_note_default": "Gracias por su confianza. Podemos ajustar el plan dentro del periodo válido.",
            },
            "en": {
                "estimate_title": "Estimate / Proposal",
                "contract_title": "Contract",
                "change_order_title": "Change Order",
                "customer": "Customer",
                "project": "Project",
                "details": "Scope / Details",
                "line_description": "Description",
                "unit": "Unit",
                "unit_price": "Unit Price",
                "estimate_no": "Estimate No.",
                "contract_no": "Contract No.",
                "change_order_no": "Change Order No.",
                "date": "Date",
                "address": "Address",
                "phone": "Phone",
                "valid_until": "Valid Until",
                "status": "Status",
                "signed_status": "Signed Status",
                "signed_date": "Signed Date",
                "category": "Category",
                "qty": "Qty",
                "material": "Material",
                "labor": "Labor",
                "subtotal": "Subtotal",
                "markup": "Markup",
                "total": "Total",
                "notes": "Notes",
                "terms": "Terms",
                "signature": "Signature",
                "customer_signature": "Customer Signature",
                "company_signature": "Company Signature",
                "payment_plan": "Payment Plan",
                "node": "Node",
                "amount": "Amount",
                "description": "Change Description",
                "contract_summary": "Contract Summary",
                "impact_payment_plan": "Impact Payment Plan",
                "affect_designer_commission": "Affect Designer Commission",
                "approved_at": "Approved At",
                "status": "Status",
                "yes": "Yes",
                "no": "No",
                "generated_at": "Generated at",
                "print_doc": "Print",
                "no_line_items": "No line items",
                "no_payment_plan": "No payment plan",
                "footer_note": "This estimate is issued for project communication and signing reference.",
                "contract_clause_default": "This contract is executed upon mutual written confirmation.",
                "contract_intro_default": "This contract defines the agreed project scope, schedule expectations, payment milestones, and signature requirements.",
                "signature_note_default": "This contract becomes effective after both parties sign.",
                "print_disclaimer_default": "This document is issued for project communication and contract confirmation.",
                "estimate_note_default": "Thank you for your trust. Scope can be adjusted within validity period.",
            },
        }
        return texts["zh"] if lang == "zh" else texts["es"] if lang == "es" else texts["en"]

    def _lang_from_query(self, query):
        lang = (query.get("lang", [""])[0] or "").lower().strip()
        if not lang:
            conn = get_conn()
            cur = conn.cursor()
            lang = normalize_key(self._system_setting_text(cur, "default_print_language", "en"))
            conn.close()
        return lang if lang in {"zh", "en", "es"} else "en"

    def _print_settings(self, cur):
        return {
            "company_name": self._system_setting_text(cur, "company_name", ""),
            "company_logo_dark": self._system_setting_text(cur, "company_logo_dark", ""),
            "company_footer_text": self._system_setting_text(cur, "company_footer_text", ""),
            "print_footer_company_name": self._system_setting_text(cur, "print_footer_company_name", ""),
            "print_footer_license_no": self._system_setting_text(cur, "print_footer_license_no", ""),
            "print_footer_contact": self._system_setting_text(cur, "print_footer_contact", ""),
            "print_footer_disclaimer": self._system_setting_text(cur, "print_footer_disclaimer", ""),
            "default_signature_note": self._system_setting_text(cur, "default_signature_note", ""),
            "print_show_logo": self._system_setting_bool(cur, "print_show_logo", True),
            "print_show_signature_hint": self._system_setting_bool(cur, "print_show_signature_hint", True),
        }

    def _handle_estimate_print_view(self, path, user, query):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 3 or parts[0] != "print" or parts[1] != "estimate":
            return False
        if not self._require_module(user, "estimates"):
            return True
        try:
            estimate_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid estimate id"}, 400)
            return True
        autoprint = str(query.get("autoprint", ["0"])[0]).lower() in {"1", "true", "yes"}
        self._estimate_pdf_html(estimate_id, self._lang_from_query(query), auto_print=autoprint, mode="print")
        return True

    def _handle_contract_print_view(self, path, user, query):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 3 or parts[0] != "print" or parts[1] != "contract":
            return False
        if not self._require_module(user, "contracts"):
            return True
        try:
            contract_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid contract id"}, 400)
            return True
        autoprint = str(query.get("autoprint", ["0"])[0]).lower() in {"1", "true", "yes"}
        self._contract_pdf_html(contract_id, self._lang_from_query(query), auto_print=autoprint, mode="print")
        return True

    def _handle_change_order_print_view(self, path, user, query):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 3 or parts[0] != "print" or parts[1] != "change-order":
            return False
        if not (self._has_module(user, "change_orders") or self._has_module(user, "projects")):
            self._json_response({"error": "Forbidden: change_orders/projects"}, 403)
            return True
        try:
            change_order_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid change order id"}, 400)
            return True
        autoprint = str(query.get("autoprint", ["0"])[0]).lower() in {"1", "true", "yes"}
        self._change_order_pdf_html(change_order_id, self._lang_from_query(query), auto_print=autoprint, mode="print")
        return True

    def _handle_estimate_pdf(self, path, user, query):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "estimates" or parts[3] != "pdf":
            return False
        if not self._require_module(user, "estimates"):
            return True
        try:
            estimate_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid estimate id"}, 400)
            return True
        self._estimate_pdf_html(estimate_id, self._lang_from_query(query), auto_print=True, mode="pdf")
        return True

    def _public_quote_lookup(self, token):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT e.*, c.name AS customer_name, c.phone AS customer_phone, c.email AS customer_email,
                   c.primary_address AS customer_address
            FROM estimates e
            LEFT JOIN customers c ON c.id=e.customer_id
            WHERE e.public_token=?
            """,
            (token,),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return None, None, None
        estimate = row_to_dict(row)
        cur.execute("SELECT * FROM estimate_sections WHERE estimate_id=? ORDER BY sort_order,id", (estimate["id"],))
        sections = [row_to_dict(x) for x in cur.fetchall()]
        for sec in sections:
            cur.execute("SELECT * FROM estimate_lines WHERE section_id=? ORDER BY sort_order,id", (sec["id"],))
            sec["lines"] = [row_to_dict(x) for x in cur.fetchall()]
        cur.execute(
            """
            SELECT epm.*, psti.step_name AS stage_step_name
            FROM estimate_payment_milestones epm
            LEFT JOIN project_stage_template_items psti ON psti.id=epm.trigger_stage_template_item_id
            WHERE epm.estimate_id=?
            ORDER BY epm.sort_order, epm.id
            """,
            (estimate["id"],),
        )
        milestones = [row_to_dict(x) for x in cur.fetchall()]
        conn.close()
        return estimate, sections, milestones

    def _public_quote_page(self, path):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 2 or parts[0] != "quote":
            return self._json_response({"error": "Not found"}, 404)
        token = parts[1]
        estimate, sections, milestones = self._public_quote_lookup(token)
        if not estimate:
            return self._html_response("<h1>Quote not found</h1>", 404)
        lang = (estimate.get("pdf_language") or DEFAULT_LANGUAGE or "zh").lower()
        if lang not in {"zh", "en", "es"}:
            lang = "zh"
        labels = {
            "zh": {
                "title": "报价确认", "estimate": "估价单", "customer": "客户信息", "details": "报价明细",
                "summary": "总价", "payment": "付款节点", "confirm": "确认报价",
                "name": "姓名", "email": "邮箱", "phone": "电话", "note": "备注", "download": "打开/下载 PDF",
                "confirm_text": "我确认已阅读并同意此报价内容。正式合同将另行发送签署。",
                "subtotal": "明细小计", "total": "总计", "status": "状态", "already": "该报价已处理。",
                "acceptance": "报价确认", "signature": "确认签名", "date": "确认日期",
            },
            "en": {
                "title": "Quote Confirmation", "estimate": "Estimate", "customer": "Customer Info", "details": "Estimate Details",
                "summary": "Total", "payment": "Payment Milestones", "confirm": "Confirm Quote",
                "name": "Name", "email": "Email", "phone": "Phone", "note": "Note", "download": "Open / Download PDF",
                "confirm_text": "I have reviewed and agree to this quote. The formal contract will be sent separately for signature.",
                "subtotal": "Items Subtotal", "total": "Grand Total", "status": "Status", "already": "This quote has already been processed.",
                "discount": "Discount",
                "acceptance": "Quote Acceptance", "signature": "Signature", "date": "Date",
            },
            "es": {
                "title": "Confirmacion de cotizacion", "estimate": "Cotizacion", "customer": "Cliente", "details": "Detalle",
                "summary": "Total", "payment": "Hitos de pago", "confirm": "Confirmar cotizacion",
                "name": "Nombre", "email": "Correo", "phone": "Telefono", "note": "Nota", "download": "Abrir / Descargar PDF",
                "confirm_text": "He revisado y acepto esta cotizacion. El contrato formal se enviara por separado para firma.",
                "subtotal": "Subtotal", "total": "Total", "status": "Estado", "already": "Esta cotizacion ya fue procesada.",
                "acceptance": "Aceptacion de cotizacion", "signature": "Firma", "date": "Fecha",
            },
        }[lang]
        conn = get_conn()
        cur = conn.cursor()
        print_settings = self._print_settings(cur)
        logo_cfg = self._brand_logo_urls(cur)
        conn.close()
        brand = logo_cfg.get("brand") or {}
        logo_url = (logo_cfg.get("dark") or "/assets/images/logo-oaklian-dark.png").strip()
        company_name = (print_settings.get("company_name") or brand.get("company_name") or "Oaklian Builders").strip()
        footer_text = (print_settings.get("company_footer_text") or "OAKLIAN Remodeling & Construction LLC").strip()

        def money(v):
            return "$" + format(float(v or 0), ",.2f")
        def esc(v):
            return html_escape(str(v or ""))
        manual_adjustment = float(estimate.get("manual_adjustment") or 0)
        discount_html = (
            f"<div class='discount'>{labels.get('discount', 'Discount')}: {money(manual_adjustment)}</div>"
            if manual_adjustment < 0
            else ""
        )
        rows_html = []
        for sec in sections:
            lines = sec.get("lines") or []
            line_rows = "".join(
                f"<tr><td>{esc(x.get('item_name'))}</td><td>{esc(x.get('description'))}</td>"
                f"<td class='num'>{esc(x.get('quantity'))}</td><td class='center'>{esc(x.get('unit'))}</td>"
                f"<td class='num'>{money(x.get('line_subtotal'))}</td></tr>"
                for x in lines
            )
            rows_html.append(
                f"<section class='block'><h3>{esc(sec.get('name_zh') or sec.get('name') or '-')}</h3>"
                f"<table class='quote-table'><colgroup><col class='col-item'><col class='col-desc'><col class='col-qty'><col class='col-unit'><col class='col-subtotal'></colgroup>"
                f"<thead><tr><th>Item</th><th>Description</th><th class='num'>Qty</th><th class='center'>Unit</th><th class='num'>Subtotal</th></tr></thead>"
                f"<tbody>{line_rows}</tbody></table></section>"
            )
        ms_html = "".join(
            f"<tr><td>{esc(m.get('name'))}</td><td>{esc(m.get('custom_stage_name') or m.get('stage_step_name') or '')}</td>"
            f"<td class='num'>{float(m.get('amount_pct') or 0):.1f}%</td></tr>"
            for m in milestones
        ) or "<tr><td colspan='3'>-</td></tr>"
        processed = self._estimate_confirm_status_key(estimate.get("confirm_status")) in {"confirmed", "rejected"}
        if processed:
            form_html = f"<div class='notice'>{labels['already']} {labels['status']}: {esc(estimate.get('confirm_status'))}</div>"
        else:
            form_html = f"""
          <form id="quote-form" class="confirm-box">
            <div class="confirm-head">
              <div>
                <div class="confirm-title">{labels['acceptance']}</div>
                <div class="confirm-text">{labels['confirm_text']}</div>
              </div>
              <button type="button" id="confirm-btn">{labels['confirm']}</button>
            </div>
            <div class="confirm-meta">
              <span><b>{labels['name']}:</b> {esc(estimate.get('customer_name') or '-')}</span>
              <span><b>{labels['date']}:</b> {esc(to_iso_date(datetime.now()))}</span>
            </div>
            <input type="hidden" name="client_name" value="{esc(estimate.get('customer_name') or '')}">
          </form>
        """
        html = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{labels['title']} #{estimate['id']}</title>
<style>
body{{margin:0;background:#e8ebf0;color:#1d2433;font-family:Arial,'Microsoft YaHei',sans-serif}}
.page{{width:min(900px,calc(100vw - 28px));margin:24px auto;background:#fff;padding:36px;box-shadow:0 2px 12px rgba(0,0,0,.18)}}
.top{{display:flex;justify-content:space-between;gap:24px;border-bottom:2px solid #777;padding-bottom:16px}}
.brand{{display:flex;align-items:center;gap:14px;min-width:0}}
.logo{{width:112px;height:56px;object-fit:contain;object-position:left center;flex:0 0 auto}}
.brand-text{{min-width:0}}
h1{{margin:0;font-size:24px}} h2{{font-size:17px;border-left:4px solid #777;padding-left:10px;margin-top:24px}} h3{{font-size:15px;margin:18px 0 8px}}
.muted{{color:#667085}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px 40px}}
table{{width:100%;border-collapse:collapse;font-size:13px;table-layout:fixed}} th,td{{border-bottom:1px solid #ddd;padding:8px;text-align:left;vertical-align:top}} th{{background:#f3f5f8}} .num{{text-align:right}} .center{{text-align:center}}
.quote-table .col-item{{width:26%}} .quote-table .col-desc{{width:34%}} .quote-table .col-qty{{width:12%}} .quote-table .col-unit{{width:10%}} .quote-table .col-subtotal{{width:18%}}
.quote-table td:nth-child(3),.quote-table th:nth-child(3),.quote-table td:nth-child(5),.quote-table th:nth-child(5){{text-align:right}}
.quote-table td:nth-child(4),.quote-table th:nth-child(4){{text-align:center}}
.total{{font-size:22px;font-weight:700;text-align:right;margin-top:12px}} .discount{{font-size:14px;text-align:right;color:#475467;margin-top:8px}} .confirm-box{{margin-top:16px;padding:14px 16px;border:1px solid #d8dee8;background:#fff}}
.confirm-head{{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;border-bottom:1px solid #e6eaf0;padding-bottom:10px;margin-bottom:12px}}
.confirm-title{{font-weight:700;font-size:15px;margin-bottom:4px}} .confirm-text{{color:#475467;font-size:12px;line-height:1.4;max-width:560px}}
.confirm-meta{{display:flex;gap:22px;flex-wrap:wrap;color:#475467;font-size:13px}}
label{{display:block;margin-top:0;font-weight:600}} input,textarea{{box-sizing:border-box;width:100%;padding:10px;border:1px solid #cfd7e3;border-radius:4px;margin-top:4px;font:inherit}} textarea{{min-height:80px}}
.check{{display:flex;gap:8px;align-items:flex-start;font-weight:400}} .check input{{width:auto;margin-top:3px}}
.actions{{display:flex;gap:10px;margin-top:16px}} button{{padding:11px 18px;border:1px solid #1f2937;background:#1f2937;color:#fff;border-radius:4px;font-weight:700;cursor:pointer}} button.secondary{{background:#fff;color:#1f2937}}
.compact-actions{{margin-top:12px}}
.notice{{margin-top:20px;padding:14px;background:#eef7ee;border:1px solid #b8d8b8}}
@media print{{body{{background:#fff}}.page{{box-shadow:none;margin:0;width:auto}}.confirm-box,.download{{display:none}}}}
@media (max-width:700px){{.page{{padding:22px}}.top{{display:block}}.brand{{margin-bottom:16px}}.confirm-head{{display:block}}.confirm-head button{{margin-top:10px}}}}
</style></head>
<body><main class="page">
<div class="top"><div class="brand"><img class="logo" src="{esc(logo_url)}" alt="Oaklian logo"><div class="brand-text"><h1>{esc(company_name)}</h1><div class="muted">{esc(footer_text)}</div></div></div>
<div><h1>{labels['title']}</h1><div>{labels['estimate']} #{int(estimate['id']):05d}</div><div>{esc(estimate.get('updated_at'))}</div></div></div>
<h2>{labels['customer']}</h2><div class="grid"><div><b>Name:</b> {esc(estimate.get('customer_name'))}</div><div><b>Phone:</b> {esc(estimate.get('customer_phone'))}</div>
<div><b>Address:</b> {esc(estimate.get('address') or estimate.get('customer_address'))}</div><div><b>Project:</b> {esc(estimate.get('title'))}</div></div>
<p class="download"><a href="/api/v2/estimates/{estimate['id']}/pdf?lang={lang}" target="_blank">{labels['download']}</a></p>
<h2>{labels['details']}</h2>{''.join(rows_html)}
<h2>{labels['payment']}</h2><table><thead><tr><th>Name</th><th>Stage</th><th>Percent</th></tr></thead><tbody>{ms_html}</tbody></table>
<h2>{labels['summary']}</h2>{discount_html}<div class="total">{labels['total']}: {money(estimate.get('total_amount'))}</div>
{form_html}
</main>
<script>
const token = {json.dumps(token)};
async function send(action) {{
  const form = document.getElementById('quote-form');
  if (!form) return;
  if (action === 'confirm' && !form.reportValidity()) return;
  const data = Object.fromEntries(new FormData(form).entries());
  const res = await fetch(`/api/public/quotes/${{token}}/${{action}}`, {{
    method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(data)
  }});
  const out = await res.json().catch(() => ({{}}));
  if (!res.ok) {{ alert(out.error || 'Failed'); return; }}
  location.reload();
}}
document.getElementById('confirm-btn')?.addEventListener('click', () => send('confirm'));
</script></body></html>"""
        return self._html_response(html)

    def _public_quote_action(self, path):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 5 or parts[0] != "api" or parts[1] != "public" or parts[2] != "quotes":
            return self._json_response({"error": "Not found"}, 404)
        token = parts[3]
        action = parts[4]
        if action not in {"confirm", "reject"}:
            return self._json_response({"error": "Not found"}, 404)
        payload = self._read_json_body() or {}
        name = str(payload.get("client_name") or "").strip()
        email = str(payload.get("client_email") or "").strip()
        phone = str(payload.get("client_phone") or "").strip()
        note = str(payload.get("confirm_note") or "").strip()
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM estimates WHERE public_token=?", (token,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Quote not found"}, 404)
        estimate = row_to_dict(row)
        current = self._estimate_confirm_status_key(estimate.get("confirm_status") or estimate.get("status"))
        if current not in {"sent"}:
            conn.close()
            return self._json_response({"error": f"Quote is not waiting for customer response: {current}"}, 400)
        target = "confirmed" if action == "confirm" else "rejected"
        ts = now_ts()
        ip = self.client_address[0] if self.client_address else ""
        ua = self.headers.get("User-Agent", "")
        if action == "confirm" and not name:
            name = estimate.get("customer_name") or estimate.get("title") or "Customer"
        client_email_value = email if "client_email" in payload else estimate.get("client_email")
        client_phone_value = phone if "client_phone" in payload else estimate.get("client_phone")
        full_note = note
        if action == "confirm":
            full_note = (note + "\n" if note else "") + f"Client confirmed via public quote page: {name}"
        cur.execute(
            """
            UPDATE estimates
            SET confirm_status=?, status=?, confirmed_at=?,
                confirmed_by=NULL, confirm_note=CASE WHEN ?<>'' THEN ? ELSE confirm_note END,
                client_action_at=?, client_name=?, client_email=?, client_phone=?,
                client_signature_data=?, client_ip=?, client_user_agent=?, updated_at=?
            WHERE id=?
            """,
            (
                target,
                self._estimate_legacy_status(target),
                ts if target == "confirmed" else estimate.get("confirmed_at"),
                full_note,
                full_note,
                ts,
                name,
                client_email_value,
                client_phone_value,
                estimate.get("client_signature_data"),
                ip,
                ua,
                ts,
                estimate["id"],
            ),
        )
        conn.commit()
        conn.close()
        return self._json_response({"ok": True, "status": target})

    def _handle_contract_pdf(self, path, user, query):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "contracts" or parts[3] != "pdf":
            return False
        if not self._require_module(user, "contracts"):
            return True
        try:
            contract_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid contract id"}, 400)
            return True
        self._contract_pdf_html(contract_id, self._lang_from_query(query), auto_print=True, mode="pdf")
        return True

    def _handle_change_order_pdf(self, path, user, query):
        parts = [p for p in path.split("/") if p]
        if len(parts) != 4 or parts[0] != "api" or parts[1] != "change-orders" or parts[3] != "pdf":
            return False
        if not (self._has_module(user, "change_orders") or self._has_module(user, "projects")):
            self._json_response({"error": "Forbidden: change_orders/projects"}, 403)
            return True
        try:
            change_order_id = int(parts[2])
        except ValueError:
            self._json_response({"error": "Invalid change order id"}, 400)
            return True
        self._change_order_pdf_html(change_order_id, self._lang_from_query(query), auto_print=True, mode="pdf")
        return True

    def _estimate_pdf_html(self, estimate_id, lang, auto_print=True, mode="pdf"):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                e.*,
                c.name AS customer_name,
                c.phone AS customer_phone,
                c.email AS customer_email,
                c.primary_address AS customer_address,
                c.inquiry_type AS customer_inquiry_type,
                p.project_type AS source_project_type,
                p.name AS project_name
            FROM estimates e
            LEFT JOIN customers c ON c.id = e.customer_id
            LEFT JOIN projects p ON p.id = e.project_id
            WHERE e.id=?
            """,
            (estimate_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Estimate not found"}, 404)
        estimate = row_to_dict(row)
        brand = self._read_company_settings(cur)
        print_cfg = self._print_settings(cur)
        resolved_project_type = self._resolve_record_project_type(
            cur,
            record_project_type=estimate.get("project_type"),
            project_id=estimate.get("project_id"),
            customer_id=estimate.get("customer_id"),
            estimate_id=estimate_id,
        )
        template = self._resolve_document_template(cur, "estimate", resolved_project_type)
        conn.close()
        txt = self._pdf_text(lang)
        fallback_tpl = self._default_template_content("estimate", txt)
        tpl = template or {}

        def money(v):
            try:
                return f"${float(v or 0):,.2f}"
            except (TypeError, ValueError):
                return "$0.00"

        def percent(v):
            try:
                return f"{float(v or 0) * 100:.0f}%"
            except (TypeError, ValueError):
                return "0%"

        created_date = str(estimate.get("created_at") or now_ts())[:10]
        estimate_no = f"EST-{int(estimate_id):05d}"
        logo_url = (brand.get("logo_horizontal_url") or print_cfg.get("company_logo_dark") or "/assets/images/logo-oaklian-dark.png").strip()
        company_name = (print_cfg.get("company_name") or brand.get("company_name") or "OAKLIAN REMODELING").strip()
        address = estimate.get("address") or estimate.get("customer_address") or ""
        doc_title = (tpl.get("title_text") or fallback_tpl.get("title_text") or txt["estimate_title"]).strip()
        intro_text = (tpl.get("intro_text") or fallback_tpl.get("intro_text") or "").strip()
        note_text = (estimate.get("notes") or "").strip() or (tpl.get("note_text") or fallback_tpl.get("note_text") or txt["estimate_note_default"]).strip()
        terms_text = (tpl.get("terms_text") or fallback_tpl.get("terms_text") or txt["contract_clause_default"]).strip()
        footer_text = (tpl.get("footer_text") or fallback_tpl.get("footer_text") or txt["footer_note"]).strip()
        footer_company = (print_cfg.get("company_footer_text") or print_cfg.get("print_footer_company_name") or brand.get("legal_name") or company_name).strip()
        footer_disclaimer = (print_cfg.get("print_footer_disclaimer") or footer_text or txt["footer_note"]).strip()
        footer_contact = (print_cfg.get("print_footer_contact") or "").strip()
        footer_license = (print_cfg.get("print_footer_license_no") or "").strip()
        show_logo = bool(print_cfg.get("print_show_logo"))
        footer_meta_parts = [x for x in [footer_company, footer_license, footer_contact] if x]
        footer_meta_line = " | ".join(footer_meta_parts)
        logo_html = """<img class="logo" src="{src}" onerror="this.style.display='none'" />""".format(src=html_escape(logo_url)) if show_logo and logo_url else ""
        intro_html = f"<div class='notes'><b>{txt['description']}:</b><br>{html_escape(intro_text)}</div>" if intro_text else ""

        try:
            items = json.loads(estimate.get("line_items_json") or "[]")
            if not isinstance(items, list):
                items = []
        except json.JSONDecodeError:
            items = []

        row_parts = []
        for item in items:
            qty = item.get("qty") if item.get("qty") is not None else item.get("quantity")
            subtotal = item.get("subtotal")
            row_parts.append(
                "<tr>"
                f"<td>{html_escape(str(item.get('category') or item.get('name') or '-'))}</td>"
                f"<td>{html_escape(str(qty if qty is not None else ''))}</td>"
                f"<td>{html_escape(str(item.get('material') or item.get('item') or ''))}</td>"
                f"<td>{html_escape(str(item.get('labor') or item.get('description') or ''))}</td>"
                f"<td style='text-align:right'>{money(subtotal)}</td>"
                "</tr>"
            )
        rows_html = "".join(row_parts) if row_parts else f"<tr><td colspan='5'>{txt['no_line_items']}</td></tr>"
        print_script = "<script>window.onload=function(){window.print();}</script>" if auto_print else ""

        html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html_escape(doc_title)} {estimate_no}</title>
<style>
@page{{size:A4;margin:14mm}}
body{{font-family:Arial,sans-serif;background:#f4f5f7;color:#0f172a;margin:0}}
.toolbar{{max-width:210mm;margin:10px auto 0;display:flex;justify-content:flex-end;gap:8px}}
.toolbar button{{border:1px solid #cbd5e1;background:#fff;padding:6px 12px;border-radius:8px;cursor:pointer}}
.paper{{width:210mm;min-height:297mm;margin:8px auto 14px;background:#fff;padding:16mm;box-sizing:border-box;box-shadow:0 8px 24px rgba(2,6,23,.12)}}
.head{{display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid {brand.get('accent_color', '#A38A55')};padding-bottom:12px;margin-bottom:16px}}
.logo{{max-height:64px;max-width:300px}}
.title{{color:{brand.get('dark_color', '#0F172A')};font-size:26px;font-weight:700}}
.meta{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:12px 0}}
.box{{border:1px solid #dbe4eb;border-radius:8px;padding:10px;line-height:1.5}}
table{{width:100%;border-collapse:collapse;margin-top:10px}}
th,td{{border:1px solid #dbe4eb;padding:8px;text-align:left;font-size:13px}}
th{{background:{brand.get('light_bg', '#E2E8F0')}}}
.tot{{margin-top:12px;display:grid;gap:5px;justify-content:end;text-align:right}}
.notes{{margin-top:14px;border:1px solid #dbe4eb;border-radius:8px;padding:10px;min-height:58px}}
.muted{{color:#64748b;font-size:12px;margin-top:18px}}
@media print{{
  body{{background:#fff}}
  .toolbar{{display:none}}
  .paper{{margin:0;width:auto;min-height:auto;box-shadow:none;padding:0}}
}}
</style></head>
<body>
<div class="toolbar no-print"><button onclick="window.print()">{txt['print_doc']}</button></div>
<div class="paper">
  <div class="head">
    <div>
      <div class="title">{html_escape(company_name)}</div>
      <div>{html_escape(brand.get('tagline', ''))}</div>
    </div>
    {logo_html}
  </div>
  <h2>{html_escape(doc_title)}</h2>
  {intro_html}
  <div class="meta">
    <div class="box">
      <b>{txt['customer']}</b><br>
      {html_escape(estimate.get('customer_name') or '')}<br>
      {txt['phone']}: {html_escape(estimate.get('customer_phone') or '')}<br>
      {html_escape(estimate.get('customer_email') or '')}<br>
      {txt['address']}: {html_escape(address)}
    </div>
    <div class="box">
      <b>{txt['project']}</b><br>
      {html_escape(estimate.get('project_name') or estimate.get('title') or '')}<br>
      {txt['estimate_no']}: {estimate_no}<br>
      {txt['date']}: {html_escape(created_date)}<br>
      {txt['valid_until']}: {html_escape(estimate.get('valid_until') or '')}<br>
      {txt['status']}: {html_escape(estimate.get('status') or '')}
    </div>
  </div>
  <table>
    <thead><tr><th>{txt['category']}</th><th>{txt['qty']}</th><th>{txt['material']}</th><th>{txt['labor']}</th><th>{txt['subtotal']}</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  <div class="tot">
    <div>{txt['subtotal']}: {money(estimate.get('subtotal'))}</div>
    <div>{txt['markup']}: {percent(estimate.get('markup_rate'))}</div>
    <div><b>{txt['total']}: {money(estimate.get('total_amount'))}</b></div>
  </div>
  <div class="notes"><b>{txt['notes']}:</b><br>{html_escape(note_text)}</div>
  <div class="notes"><b>{txt['terms']}:</b><br>{html_escape(terms_text)}</div>
  <div class="muted">{html_escape(footer_meta_line or (brand.get('legal_name') or company_name))} | {txt['generated_at']} {html_escape(now_ts())}</div>
  <div class="muted">{html_escape(footer_disclaimer)}</div>
</div>
{print_script}
</body></html>"""
        return self._html_response(html)

    def _contract_pdf_html(self, contract_id, lang, auto_print=True, mode="pdf"):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                ct.*,
                c.name AS customer_name,
                c.phone AS customer_phone,
                c.email AS customer_email,
                c.primary_address AS customer_address,
                c.inquiry_type AS customer_inquiry_type,
                p.name AS project_name,
                p.address AS project_address,
                p.project_type AS source_project_type,
                e.project_type AS source_estimate_project_type
            FROM contracts ct
            LEFT JOIN customers c ON c.id = ct.customer_id
            LEFT JOIN projects p ON p.id = ct.project_id
            LEFT JOIN estimates e ON e.id = ct.estimate_id
            WHERE ct.id=?
            """,
            (contract_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Contract not found"}, 404)
        contract = row_to_dict(row)
        brand = self._read_company_settings(cur)
        print_cfg = self._print_settings(cur)
        txt = self._pdf_text(lang)
        resolved_project_type = self._resolve_record_project_type(
            cur,
            record_project_type=contract.get("project_type"),
            project_id=contract.get("project_id"),
            customer_id=contract.get("customer_id"),
            estimate_id=contract.get("estimate_id"),
            contract_id=contract_id,
        )
        template = self._resolve_document_template(cur, "contract", resolved_project_type)
        fallback_tpl = self._default_template_content("contract", txt)
        tpl = template or {}

        def money(v):
            try:
                return f"${float(v or 0):,.2f}"
            except (TypeError, ValueError):
                return "$0.00"

        def has_cjk(value):
            return any("\u4e00" <= ch <= "\u9fff" for ch in str(value or ""))

        def localized_template_text(value, fallback=""):
            value = str(value or "").strip()
            fallback = str(fallback or "").strip()
            if not value:
                return fallback
            if lang != "zh" and has_cjk(value):
                return fallback
            return value

        created_date = str(contract.get("created_at") or now_ts())[:10]
        logo_url = (brand.get("logo_horizontal_url") or print_cfg.get("company_logo_dark") or "/assets/images/logo-oaklian-dark.png").strip()
        company_name = (print_cfg.get("company_name") or brand.get("company_name") or "OAKLIAN REMODELING").strip()
        address = contract.get("address") or contract.get("project_address") or contract.get("customer_address") or ""
        doc_title = localized_template_text(tpl.get("title_text"), fallback_tpl.get("title_text") or txt["contract_title"])
        intro_text = localized_template_text(tpl.get("intro_text"), fallback_tpl.get("intro_text") or "")
        note_text = localized_template_text(tpl.get("note_text"), fallback_tpl.get("note_text") or "")
        clause_text = localized_template_text(contract.get("notes"), "") or localized_template_text(tpl.get("terms_text"), fallback_tpl.get("terms_text") or txt["contract_clause_default"])
        footer_text = localized_template_text(tpl.get("footer_text"), fallback_tpl.get("footer_text") or txt["footer_note"])
        footer_company = (print_cfg.get("company_footer_text") or print_cfg.get("print_footer_company_name") or brand.get("legal_name") or company_name).strip()
        footer_disclaimer = localized_template_text(print_cfg.get("print_footer_disclaimer"), footer_text or txt.get("print_disclaimer_default") or txt["footer_note"])
        footer_contact = (print_cfg.get("print_footer_contact") or "").strip()
        footer_license = (print_cfg.get("print_footer_license_no") or "").strip()
        show_logo = bool(print_cfg.get("print_show_logo"))
        show_signature_hint = bool(print_cfg.get("print_show_signature_hint"))
        signature_hint_text = localized_template_text(print_cfg.get("default_signature_note"), txt.get("signature_note_default") or "")
        footer_meta_parts = [x for x in [footer_company, footer_license, footer_contact] if x]
        footer_meta_line = " | ".join(footer_meta_parts)
        logo_html = """<img class="logo" src="{src}" onerror="this.style.display='none'" />""".format(src=html_escape(logo_url)) if show_logo and logo_url else ""
        signature_hint_html = f"<div class='muted'>{html_escape(signature_hint_text)}</div>" if show_signature_hint and signature_hint_text else ""
        intro_html = f"<div class='notes'><b>{txt.get('contract_summary', txt['description'])}:</b><br>{html_escape(intro_text)}</div>" if intro_text else ""

        try:
            plans = json.loads(contract.get("payment_plan_json") or "[]")
            if not isinstance(plans, list):
                plans = []
        except json.JSONDecodeError:
            plans = []
        if not plans:
            cur.execute(
                "SELECT name,trigger_type,amount_type,amount_value FROM contract_payment_milestones WHERE contract_id=? ORDER BY id ASC",
                (contract_id,),
            )
            rows = cur.fetchall()
            for r in rows:
                amount_due = self._milestone_amount(contract.get("total_amount") or 0, r["amount_type"], r["amount_value"])
                plans.append(
                    {
                        "node": r["name"],
                        "due_date": r["trigger_type"],
                        "amount": amount_due,
                    }
                )
        section_rows = []
        if contract.get("estimate_id"):
            cur.execute("SELECT * FROM estimate_sections WHERE estimate_id=? ORDER BY sort_order,id", (contract["estimate_id"],))
            for sec in cur.fetchall():
                sec_dict = row_to_dict(sec)
                cur.execute("SELECT * FROM estimate_lines WHERE section_id=? ORDER BY sort_order,id", (sec_dict["id"],))
                sec_dict["lines"] = [row_to_dict(x) for x in cur.fetchall()]
                section_rows.append(sec_dict)
        if not section_rows and contract.get("estimate_id"):
            cur.execute("SELECT line_items_json FROM estimates WHERE id=?", (contract["estimate_id"],))
            est_row = cur.fetchone()
            try:
                legacy_items = json.loads((est_row["line_items_json"] if est_row else "") or "[]")
                if isinstance(legacy_items, list) and legacy_items:
                    section_rows = [{"name": txt["details"], "lines": legacy_items}]
            except (json.JSONDecodeError, AttributeError):
                section_rows = []
        conn.close()

        def num_value(value):
            try:
                return float(value or 0)
            except (TypeError, ValueError):
                return 0

        def line_qty(line):
            return line.get("quantity") if line.get("quantity") is not None else line.get("qty")

        def localized_value(row, base_key):
            if lang in {"en", "es"}:
                value = row.get(f"{base_key}_{lang}")
                if value not in (None, ""):
                    return value
            value = row.get(base_key)
            if value not in (None, ""):
                return value
            return row.get(f"{base_key}_zh") or ""

        scope_blocks = []
        for sec in section_rows:
            lines = sec.get("lines") or []
            line_rows = "".join(
                "<tr>"
                f"<td>{html_escape(str(localized_value(line, 'item_name') or line.get('item') or line.get('name') or '-'))}</td>"
                f"<td>{html_escape(str(localized_value(line, 'description')))}</td>"
                f"<td class='num'>{html_escape(str(line_qty(line) if line_qty(line) is not None else ''))}</td>"
                f"<td class='center'>{html_escape(str(line.get('unit') or ''))}</td>"
                f"<td class='num'>{money(line.get('unit_price') if line.get('unit_price') not in (None, '') else (num_value(line.get('material_cost')) + num_value(line.get('labor_cost'))))}</td>"
                f"<td class='num'>{money(line.get('line_subtotal') if line.get('line_subtotal') not in (None, '') else line.get('subtotal'))}</td>"
                "</tr>"
                for line in lines
            )
            if not line_rows:
                line_rows = f"<tr><td colspan='6'>{txt['no_line_items']}</td></tr>"
            scope_blocks.append(
                f"<section class='doc-section'><h3>{html_escape(str(localized_value(sec, 'name') or '-'))}</h3>"
                "<table class='scope-table'><colgroup><col class='col-item'><col class='col-desc'><col class='col-qty'><col class='col-unit'><col class='col-price'><col class='col-total'></colgroup>"
                f"<thead><tr><th>{txt['category']}</th><th>{txt['line_description']}</th><th class='num'>{txt['qty']}</th><th class='center'>{txt['unit']}</th><th class='num'>{txt['unit_price']}</th><th class='num'>{txt['subtotal']}</th></tr></thead>"
                f"<tbody>{line_rows}</tbody></table></section>"
            )
        scope_html = "".join(scope_blocks) or f"<section class='doc-section'><h3>{txt['details']}</h3><table><tbody><tr><td>{txt['no_line_items']}</td></tr></tbody></table></section>"

        plan_rows = "".join(
            [
                "<tr>"
                f"<td>{html_escape(str(p.get('node', '')))}</td>"
                f"<td>{html_escape(str(p.get('due_date', '')))}</td>"
                f"<td style='text-align:right'>{money(p.get('amount'))}</td>"
                "</tr>"
                for p in plans
            ]
        )
        if not plan_rows:
            plan_rows = f"<tr><td colspan='3'>{txt['no_payment_plan']}</td></tr>"
        print_script = "<script>window.onload=function(){window.print();}</script>" if auto_print else ""

        html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html_escape(doc_title)} #{contract_id}</title>
<style>
@page{{size:A4;margin:14mm}}
body{{font-family:Arial,sans-serif;background:#f4f5f7;color:#0f172a;margin:0}}
.toolbar{{max-width:210mm;margin:10px auto 0;display:flex;justify-content:flex-end;gap:8px}}
.toolbar button{{border:1px solid #cbd5e1;background:#fff;padding:6px 12px;border-radius:8px;cursor:pointer}}
.paper{{width:210mm;min-height:297mm;margin:8px auto 14px;background:#fff;padding:16mm;box-sizing:border-box;box-shadow:0 8px 24px rgba(2,6,23,.12)}}
.head{{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:20px;align-items:start;border-bottom:2px solid #1f2937;padding-bottom:12px;margin-bottom:16px}}
.brand-line{{display:flex;gap:14px;align-items:center}}
.logo{{max-height:48px;max-width:180px;object-fit:contain}}
.company{{color:{brand.get('dark_color', '#0F172A')};font-size:18px;font-weight:800;line-height:1.15}}
.tagline{{color:#475569;font-size:12px;margin-top:2px}}
.doc-title{{text-align:right}}
.doc-title h1{{font-size:24px;margin:0 0 4px;color:#111827}}
.doc-title div{{font-size:12px;line-height:1.45}}
.meta{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin:14px 0 18px}}
.box{{border-top:3px solid #1f2937;background:#f8fafc;padding:10px 12px;line-height:1.55}}
.box-title{{font-weight:800;margin-bottom:5px;color:#111827}}
.doc-section{{break-inside:avoid;page-break-inside:avoid;margin:16px 0}}
.doc-section h3{{border-left:4px solid #777;padding-left:8px;margin:0 0 9px;font-size:15px}}
table{{width:100%;border-collapse:collapse;margin-top:10px}}
th,td{{border-bottom:1px solid #e5e7eb;padding:7px 8px;text-align:left;font-size:12px;vertical-align:top}}
th{{background:#f1f5f9;color:#111827;font-weight:800}}
.num{{text-align:right}}
.center{{text-align:center}}
.col-item{{width:26%}}.col-desc{{width:34%}}.col-qty{{width:8%}}.col-unit{{width:8%}}.col-price{{width:12%}}.col-total{{width:12%}}
.tot{{margin:14px 0 0 auto;width:44%;display:grid;gap:6px;text-align:right}}
.tot-row{{display:flex;justify-content:space-between;border-bottom:1px solid #e5e7eb;padding:4px 0}}
.tot-row.total{{font-size:16px;font-weight:800;border-top:2px solid #111827;border-bottom:0;padding-top:8px}}
.notes{{margin-top:12px;border-top:1px solid #d1d5db;padding:10px 0;min-height:42px;break-inside:avoid;page-break-inside:avoid}}
.sign-grid{{margin-top:30px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:28px;break-inside:avoid;page-break-inside:avoid}}
.sign-box{{border-top:1px solid #64748b;padding-top:8px;min-height:42px;font-size:12px}}
.muted{{color:#64748b;font-size:12px;margin-top:18px}}
@media print{{
  body{{background:#fff}}
  .toolbar{{display:none}}
  .paper{{margin:0;width:auto;min-height:auto;box-shadow:none;padding:0}}
}}
</style></head>
<body>
<div class="toolbar no-print"><button onclick="window.print()">{txt['print_doc']}</button></div>
<div class="paper">
  <div class="head">
    <div class="brand-line">
      {logo_html}
      <div>
        <div class="company">{html_escape(company_name)}</div>
        <div class="tagline">{html_escape(brand.get('legal_name') or '')}</div>
        <div class="tagline">{html_escape(brand.get('tagline', ''))}</div>
      </div>
    </div>
    <div class="doc-title">
      <h1>{html_escape(doc_title)}</h1>
      <div><b>{txt['contract_no']}:</b> {html_escape(contract.get('contract_no') or '')}</div>
      <div><b>{txt['date']}:</b> {html_escape(created_date)}</div>
      <div><b>{txt['signed_status']}:</b> {html_escape(contract.get('signed_status') or '')}</div>
    </div>
  </div>
  {intro_html}
  <div class="meta">
    <div class="box">
      <div class="box-title">{txt['customer']}</div>
      <div><b>{txt['customer']}:</b> {html_escape(contract.get('customer_name') or '')}</div>
      <div><b>{txt['phone']}:</b> {html_escape(contract.get('customer_phone') or '')}</div>
      <div><b>Email:</b> {html_escape(contract.get('customer_email') or '')}</div>
      <div><b>{txt['address']}:</b> {html_escape(address)}</div>
    </div>
    <div class="box">
      <div class="box-title">{txt['project']}</div>
      <div><b>{txt['project']}:</b> {html_escape(contract.get('project_name') or contract.get('title') or '')}</div>
      <div><b>{txt['contract_no']}:</b> {html_escape(contract.get('contract_no') or '')}</div>
      <div><b>{txt['date']}:</b> {html_escape(created_date)}</div>
      <div><b>{txt['signed_date']}:</b> {html_escape(contract.get('signed_date') or '')}</div>
    </div>
  </div>
  {scope_html}
  <section class="doc-section">
  <h3>{txt['payment_plan']}</h3>
  <table>
    <thead><tr><th>{txt['node']}</th><th>{txt['valid_until']}</th><th>{txt['amount']}</th></tr></thead>
    <tbody>{plan_rows}</tbody>
  </table>
  </section>
  <div class="tot"><div class="tot-row total"><span>{txt['total']}</span><span>{money(contract.get('total_amount'))}</span></div></div>
  <div class="notes"><b>{txt['notes']}:</b><br>{html_escape(note_text)}</div>
  <div class="notes"><b>{txt['terms']}:</b><br>{html_escape(clause_text)}</div>
  <h3 style="margin-top:14px;">{txt['signature']}</h3>
  <div class="sign-grid">
    <div class="sign-box">{txt['customer_signature']}：</div>
    <div class="sign-box">{txt['company_signature']}：</div>
  </div>
  {signature_hint_html}
  <div class="muted">{html_escape(footer_meta_line or (brand.get('legal_name') or company_name))} | {txt['generated_at']} {html_escape(now_ts())}</div>
  <div class="muted">{html_escape(footer_disclaimer)}</div>
</div>
{print_script}
</body></html>"""
        return self._html_response(html)

    def _change_order_pdf_html(self, change_order_id, lang, auto_print=True, mode="pdf"):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                co.*,
                p.name AS project_name,
                p.address AS project_address,
                p.project_type AS source_project_type,
                ct.contract_no,
                ct.project_type AS source_contract_project_type,
                c.name AS customer_name,
                c.phone AS customer_phone,
                c.primary_address AS customer_address,
                c.inquiry_type AS customer_inquiry_type
            FROM change_orders co
            LEFT JOIN projects p ON p.id=co.project_id
            LEFT JOIN contracts ct ON ct.id=co.contract_id
            LEFT JOIN customers c ON c.id=co.customer_id
            WHERE co.id=?
            """,
            (change_order_id,),
        )
        row = cur.fetchone()
        if not row:
            conn.close()
            return self._json_response({"error": "Change order not found"}, 404)
        co = row_to_dict(row)
        self._enrich_resource_rows(cur, "change_orders", [co])
        brand = self._read_company_settings(cur)
        print_cfg = self._print_settings(cur)
        resolved_project_type = self._resolve_record_project_type(
            cur,
            record_project_type=co.get("project_type"),
            project_id=co.get("project_id"),
            customer_id=co.get("customer_id"),
            contract_id=co.get("contract_id"),
        )
        template = self._resolve_document_template(cur, "change_order", resolved_project_type)
        conn.close()
        txt = self._pdf_text(lang)
        fallback_tpl = self._default_template_content("change_order", txt)
        tpl = template or {}

        def money(v):
            try:
                return f"${float(v or 0):,.2f}"
            except (TypeError, ValueError):
                return "$0.00"

        status_key = self._change_order_status_key(co.get("status"))
        status_text = {
            "draft": {"zh": "草稿", "en": "Draft", "es": "Borrador"},
            "sent": {"zh": "已发送", "en": "Sent", "es": "Enviado"},
            "approved": {"zh": "已确认", "en": "Approved", "es": "Aprobado"},
            "rejected": {"zh": "已拒绝", "en": "Rejected", "es": "Rechazado"},
        }.get(status_key, {"zh": status_key, "en": status_key, "es": status_key})
        locale_key = "zh" if lang == "zh" else "es" if lang == "es" else "en"
        status_label = status_text.get(locale_key) or status_key

        created_date = str(co.get("created_at") or now_ts())[:10]
        logo_url = (brand.get("logo_horizontal_url") or print_cfg.get("company_logo_dark") or "/assets/images/logo-oaklian-dark.png").strip()
        company_name = (print_cfg.get("company_name") or brand.get("company_name") or "OAKLIAN REMODELING").strip()
        order_no = co.get("order_no") or f"CO-{int(change_order_id):05d}"
        address = co.get("project_address") or co.get("customer_address") or ""
        description = (co.get("description") or co.get("notes") or co.get("reason") or "").strip()
        doc_title = (tpl.get("title_text") or fallback_tpl.get("title_text") or txt["change_order_title"]).strip()
        intro_text = (tpl.get("intro_text") or fallback_tpl.get("intro_text") or "").strip()
        note_text = (tpl.get("note_text") or fallback_tpl.get("note_text") or "").strip()
        terms_text = (tpl.get("terms_text") or fallback_tpl.get("terms_text") or txt["contract_clause_default"]).strip()
        footer_text = (tpl.get("footer_text") or fallback_tpl.get("footer_text") or txt["footer_note"]).strip()
        footer_company = (print_cfg.get("company_footer_text") or print_cfg.get("print_footer_company_name") or brand.get("legal_name") or company_name).strip()
        footer_disclaimer = (print_cfg.get("print_footer_disclaimer") or footer_text or txt["footer_note"]).strip()
        footer_contact = (print_cfg.get("print_footer_contact") or "").strip()
        footer_license = (print_cfg.get("print_footer_license_no") or "").strip()
        show_logo = bool(print_cfg.get("print_show_logo"))
        show_signature_hint = bool(print_cfg.get("print_show_signature_hint"))
        signature_hint_text = (print_cfg.get("default_signature_note") or "").strip()
        footer_meta_parts = [x for x in [footer_company, footer_license, footer_contact] if x]
        footer_meta_line = " | ".join(footer_meta_parts)
        logo_html = """<img class="logo" src="{src}" onerror="this.style.display='none'" />""".format(src=html_escape(logo_url)) if show_logo and logo_url else ""
        signature_hint_html = f"<div class='muted'>{html_escape(signature_hint_text)}</div>" if show_signature_hint and signature_hint_text else ""
        intro_html = f"<div class='notes'><b>{txt['description']}:</b><br>{html_escape(intro_text)}</div>" if intro_text else ""
        print_script = "<script>window.onload=function(){window.print();}</script>" if auto_print else ""

        html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html_escape(doc_title)} {html_escape(order_no)}</title>
<style>
@page{{size:A4;margin:14mm}}
body{{font-family:Arial,sans-serif;background:#f4f5f7;color:#0f172a;margin:0}}
.toolbar{{max-width:210mm;margin:10px auto 0;display:flex;justify-content:flex-end;gap:8px}}
.toolbar button{{border:1px solid #cbd5e1;background:#fff;padding:6px 12px;border-radius:8px;cursor:pointer}}
.paper{{width:210mm;min-height:297mm;margin:8px auto 14px;background:#fff;padding:16mm;box-sizing:border-box;box-shadow:0 8px 24px rgba(2,6,23,.12)}}
.head{{display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid {brand.get('accent_color', '#A38A55')};padding-bottom:12px;margin-bottom:16px}}
.logo{{max-height:64px;max-width:300px}}
.title{{color:{brand.get('dark_color', '#0F172A')};font-size:26px;font-weight:700}}
.meta{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:12px 0}}
.box{{border:1px solid #dbe4eb;border-radius:8px;padding:10px;line-height:1.5}}
.notes{{margin-top:14px;border:1px solid #dbe4eb;border-radius:8px;padding:10px;min-height:88px;white-space:pre-wrap}}
.sign-grid{{margin-top:16px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}}
.sign-box{{border-top:1px solid #94a3b8;padding-top:8px;min-height:56px}}
.muted{{color:#64748b;font-size:12px;margin-top:18px}}
@media print{{
  body{{background:#fff}}
  .toolbar{{display:none}}
  .paper{{margin:0;width:auto;min-height:auto;box-shadow:none;padding:0}}
}}
</style></head>
<body>
<div class="toolbar no-print"><button onclick="window.print()">{txt['print_doc']}</button></div>
<div class="paper">
  <div class="head">
    <div>
      <div class="title">{html_escape(company_name)}</div>
      <div>{html_escape(brand.get('tagline', ''))}</div>
    </div>
    {logo_html}
  </div>
  <h2>{html_escape(doc_title)}</h2>
  {intro_html}
  <div class="meta">
    <div class="box">
      <b>{txt['customer']}</b><br>
      {html_escape(co.get('customer_name') or '')}<br>
      {txt['phone']}: {html_escape(co.get('customer_phone') or '')}<br>
      {txt['address']}: {html_escape(address)}
    </div>
    <div class="box">
      <b>{txt['project']}</b><br>
      {html_escape(co.get('project_name') or co.get('title') or '')}<br>
      {txt['change_order_no']}: {html_escape(order_no)}<br>
      {txt['contract_no']}: {html_escape(co.get('contract_no') or '')}<br>
      {txt['date']}: {html_escape(created_date)}<br>
      {txt['status']}: {html_escape(status_label)}<br>
      {txt['approved_at']}: {html_escape(co.get('approved_at') or '-')}
    </div>
  </div>
  <div class="meta">
    <div class="box"><b>{txt['amount']}</b><br>{money(co.get('amount_delta'))}</div>
    <div class="box"><b>{txt['impact_payment_plan']}</b><br>{txt['yes'] if int(co.get('impact_payment_plan') or 0) == 1 else txt['no']}</div>
    <div class="box"><b>{txt['affect_designer_commission']}</b><br>{txt['yes'] if int(co.get('affect_designer_commission') or 0) == 1 else txt['no']}</div>
  </div>
  <div class="notes"><b>{txt['description']}:</b><br>{html_escape(description)}</div>
  <div class="notes"><b>{txt['notes']}:</b><br>{html_escape(note_text)}</div>
  <div class="notes"><b>{txt['terms']}:</b><br>{html_escape(terms_text)}</div>
  <h3 style="margin-top:14px;">{txt['signature']}</h3>
  <div class="sign-grid">
    <div class="sign-box">{txt['customer_signature']}：</div>
    <div class="sign-box">{txt['company_signature']}：</div>
  </div>
  {signature_hint_html}
  <div class="muted">{html_escape(footer_meta_line or (brand.get('legal_name') or company_name))} | {txt['generated_at']} {html_escape(now_ts())}</div>
  <div class="muted">{html_escape(footer_disclaimer)}</div>
</div>
{print_script}
</body></html>"""
        return self._html_response(html)

    def _project_detail(self, project_id, user):
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.*, c.name AS customer_name, c.phone AS customer_phone
            FROM projects p
            LEFT JOIN customers c ON c.id = p.customer_id
            WHERE p.id=?
            """,
            (project_id,),
        )
        p = cur.fetchone()
        if not p:
            conn.close()
            return self._json_response({"error": "Project not found"}, 404)
        if self._forbid_if_no_project_access(cur, user, project_id):
            conn.close()
            return

        def fetch_many(sql, params=()):
            cur.execute(sql, params)
            return [row_to_dict(r) for r in cur.fetchall()]

        overview = row_to_dict(p)
        stage_template = None
        workflow_customized = False
        cur.execute(
            "SELECT stage_name FROM project_stages WHERE project_id=? ORDER BY stage_order ASC,id ASC",
            (project_id,),
        )
        project_stage_names = [str(x["stage_name"] or "").strip() for x in cur.fetchall() if str(x["stage_name"] or "").strip()]
        if overview.get("stage_template_id"):
            cur.execute(
                "SELECT id,name,project_type,is_default,is_active FROM project_stage_templates WHERE id=?",
                (overview.get("stage_template_id"),),
            )
            trow = cur.fetchone()
            if trow:
                stage_template = row_to_dict(trow)
                template_stage_names = self._stage_template_stage_names(cur, stage_template["id"])
                if project_stage_names:
                    workflow_customized = template_stage_names != project_stage_names
        elif project_stage_names:
            workflow_customized = True

        can_finance = self._has_module(user, "finance")
        can_contracts = self._has_module(user, "contracts") or can_finance or user.get("role") == "owner"
        if can_finance:
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM project_payments WHERE project_id=? AND status='Paid'", (project_id,))
            received = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM project_payments WHERE project_id=? AND status IN ('Pending','Overdue')", (project_id,))
            pending = cur.fetchone()[0]
            cur.execute("SELECT COALESCE(SUM(amount),0) FROM project_costs WHERE project_id=?", (project_id,))
            cost = cur.fetchone()[0]
            cur.execute("SELECT total_amount FROM contracts WHERE id=(SELECT contract_id FROM projects WHERE id=?)", (project_id,))
            row = cur.fetchone()
            contract_amount = row[0] if row and row[0] is not None else 0
            overview.update({
                "contract_amount": contract_amount,
                "received_amount": received,
                "pending_amount": pending,
                "cost_amount": cost,
                "profit_amount": received - cost,
            })

        contract = None
        source_contract = None
        source_estimate = None
        payment_milestones = []
        payment_reminders = []
        change_orders = []
        change_order_summary = {
            "approved_change_amount": 0,
            "impact_payment_plan_count": 0,
            "approved_commissionable_change_amount": 0,
            "approved_non_commissionable_change_amount": 0,
        }
        if overview.get("contract_id"):
            cur.execute("SELECT * FROM contracts WHERE id=?", (overview["contract_id"],))
            c = cur.fetchone()
            if c:
                contract = row_to_dict(c)
                source_contract = {
                    "id": contract.get("id"),
                    "contract_no": contract.get("contract_no"),
                    "title": contract.get("title"),
                    "address": contract.get("address"),
                    "estimate_id": contract.get("estimate_id"),
                }
                self._evaluate_contract_payment_milestones(cur, contract_id=contract["id"], project_id=project_id)
                cur.execute("SELECT * FROM contract_payment_milestones WHERE contract_id=? ORDER BY id ASC", (contract["id"],))
                payment_milestones = [self._serialize_milestone(r, contract.get("total_amount") or 0) for r in cur.fetchall()]
                payment_reminders = [x for x in payment_milestones if x.get("state") in {"pending", "reminded"}]
        cur.execute("SELECT * FROM change_orders WHERE project_id=? ORDER BY id DESC", (project_id,))
        change_orders = [row_to_dict(r) for r in cur.fetchall()]
        self._enrich_resource_rows(cur, "change_orders", change_orders)
        change_order_summary = self._change_order_summary(cur, project_id=project_id, contract_id=overview.get("contract_id"))

        source_estimate_id = overview.get("estimate_id") or ((contract or {}).get("estimate_id") if contract else None)
        if source_estimate_id:
            cur.execute("SELECT id,title,total_amount,status,customer_id,project_id FROM estimates WHERE id=?", (source_estimate_id,))
            er = cur.fetchone()
            if er:
                source_estimate = row_to_dict(er)
                if not overview.get("estimate_id"):
                    overview["estimate_id"] = source_estimate["id"]

        designer_commission = self._recalc_designer_commission_for_project(cur, project_id)
        if contract:
            base_contract_amount = float(contract.get("total_amount") or 0)
            contract["base_contract_amount"] = round(base_contract_amount, 2)
            contract["approved_change_amount"] = float(change_order_summary.get("approved_change_amount") or 0)
            contract["current_contract_total"] = round(
                base_contract_amount + float(change_order_summary.get("approved_change_amount") or 0),
                2,
            )
            contract["change_orders_affect_payment_plan_count"] = int(change_order_summary.get("impact_payment_plan_count") or 0)
            contract["approved_commissionable_change_amount"] = float(
                change_order_summary.get("approved_commissionable_change_amount") or 0
            )
            contract["approved_non_commissionable_change_amount"] = float(
                change_order_summary.get("approved_non_commissionable_change_amount") or 0
            )
        if not can_contracts:
            contract = None
            for item in payment_milestones:
                item["amount_due"] = None
                item["amount_value"] = None
            for item in payment_reminders:
                item["amount_due"] = None
                item["amount_value"] = None

        cur.execute(
            """
            SELECT f.*,u.username AS uploaded_by_name
            FROM files f
            LEFT JOIN users u ON u.id=f.uploaded_by
            WHERE f.entity_type='project' AND f.entity_id=?
            ORDER BY f.id DESC
            """,
            (project_id,),
        )
        project_files = [self._serialize_file_row(r) for r in cur.fetchall()]

        payload = {
            "overview": overview,
            "schedule_tasks": fetch_many("SELECT * FROM project_tasks WHERE project_id=? ORDER BY due_date ASC,id DESC", (project_id,)),
            "site_logs": fetch_many("SELECT * FROM site_logs WHERE project_id=? ORDER BY log_date DESC,id DESC", (project_id,)),
            "issues": fetch_many("SELECT * FROM project_issues WHERE project_id=? ORDER BY id DESC", (project_id,)),
            "files": project_files,
            "can_finance": can_finance,
            "can_contracts": can_contracts,
            "payments": [],
            "costs": [],
            "contract": contract,
            "source_contract": source_contract,
            "source_estimate": source_estimate,
            "stage_template": stage_template,
            "workflow_customized": workflow_customized,
            "change_orders": change_orders,
            "change_order_summary": change_order_summary,
            "payment_milestones": payment_milestones,
            "payment_reminders": payment_reminders,
            "designer": {
                "designer_id": overview.get("designer_id"),
                "designer_name": overview.get("designer_name"),
                "designer_commission_type": overview.get("designer_commission_type") or "percent",
                "designer_commission_value": overview.get("designer_commission_value") or 0,
                "designer_commission_base": overview.get("designer_commission_base") or "base_contract_only",
            },
            "designer_commission": designer_commission,
        }
        if can_finance:
            payload["payments"] = fetch_many("SELECT * FROM project_payments WHERE project_id=? ORDER BY due_date ASC", (project_id,))
            payload["costs"] = fetch_many("SELECT * FROM project_costs WHERE project_id=? ORDER BY cost_date DESC,id DESC", (project_id,))

        conn.commit()
        conn.close()
        return self._json_response(payload)

    def _parse_resource_path(self, path):
        parts = [p for p in path.split("/") if p]
        if len(parts) < 2 or parts[0] != "api":
            return None, None
        table_alias = {
            "change-orders": "change_orders",
            "document-templates": "document_templates",
            "project-stage-templates": "project_stage_templates",
            "project-stage-template-items": "project_stage_template_items",
            "designer-applications": "designer_applications",
            "designer-assignments": "designer_assignments",
            "payables": "bills",
        }
        table = table_alias.get(parts[1], parts[1])
        record_id = None
        if len(parts) >= 3:
            try:
                record_id = int(parts[2])
            except ValueError:
                return None, None
        return table, record_id

    def _resource_get(self, path, query, user):
        table, record_id = self._parse_resource_path(path)
        if table not in TABLE_FIELDS:
            return self._json_response({"error": "Unsupported resource"}, 404)
        mod = RESOURCE_MODULE.get(table)
        if table == "document_templates":
            if not self._require_document_template_manage(user):
                return
        elif table == "change_orders":
            if not (self._has_module(user, "change_orders") or self._has_module(user, "projects")):
                return self._json_response({"error": "Forbidden: change_orders/projects"}, 403)
        else:
            if not self._require_module(user, mod):
                return

        conn = get_conn()
        cur = conn.cursor()
        if record_id is not None:
            cur.execute(f"SELECT * FROM {table} WHERE id=?", (record_id,))
            row = cur.fetchone()
            if row and user.get("role") == "designer":
                if table == "designer_assignments":
                    row_obj = row_to_dict(row)
                    designer_ids = set(self._designer_ids_for_user(cur, user))
                    if not designer_ids or int(row_obj.get("designer_id") or 0) not in designer_ids:
                        conn.close()
                        return self._json_response({"error": "Forbidden: assignment access denied"}, 403)
                else:
                    project_id = self._project_id_for_table_record(cur, table, record_id)
                    if project_id and not self._project_accessible(cur, user, project_id):
                        conn.close()
                        return self._json_response({"error": "Forbidden: project access denied"}, 403)
            if not row:
                conn.close()
                return self._json_response({"error": "Record not found"}, 404)
            data = row_to_dict(row)
            self._enrich_resource_rows(cur, table, [data])
            conn.close()
            return self._json_response(data)

        sql = f"SELECT * FROM {table}"
        clauses = []
        params = []
        if "project_id" in query and "project_id" in TABLE_FIELDS[table]:
            clauses.append("project_id=?")
            params.append(query["project_id"][0])
        if "customer_id" in query and "customer_id" in TABLE_FIELDS[table]:
            clauses.append("customer_id=?")
            params.append(query["customer_id"][0])
        if "contract_id" in query and "contract_id" in TABLE_FIELDS[table]:
            clauses.append("contract_id=?")
            params.append(query["contract_id"][0])
        if "vendor_id" in query and "vendor_id" in TABLE_FIELDS[table]:
            try:
                vendor_id = int(query["vendor_id"][0])
            except (TypeError, ValueError):
                conn.close()
                return self._json_response({"error": "vendor_id must be integer"}, 400)
            clauses.append("vendor_id=?")
            params.append(vendor_id)
        if table == "payments" and "year" in query and query["year"] and str(query["year"][0]).strip().isdigit():
            y = int(query["year"][0])
            clauses.append("date LIKE ?")
            params.append(f"{y}-%")
        if table == "document_templates":
            if "template_type" in query and query["template_type"] and query["template_type"][0].strip():
                tt = self._normalize_document_template_type(query["template_type"][0])
                if tt:
                    clauses.append("template_type=?")
                    params.append(tt)
            if "project_type" in query and query["project_type"] and query["project_type"][0].strip():
                pt = self._normalize_project_type(query["project_type"][0])
                if pt:
                    clauses.append("project_type=?")
                    params.append(pt)
        if table == "project_stage_templates":
            if "project_type" in query and query["project_type"] and query["project_type"][0].strip():
                pt = self._normalize_stage_template_project_type(query["project_type"][0])
                if pt:
                    clauses.append("project_type=?")
                    params.append(pt)
            if "is_active" in query and query["is_active"] and query["is_active"][0].strip() in {"0", "1"}:
                clauses.append("COALESCE(is_active,1)=?")
                params.append(int(query["is_active"][0].strip()))
        if table == "change_orders" and "status" in query and query["status"] and query["status"][0].strip():
            status_key = self._change_order_status_key(query["status"][0])
            if status_key == "approved":
                clauses.append("(LOWER(COALESCE(status,''))='approved' OR status='已确认' OR signed_status='Signed')")
            elif status_key == "sent":
                clauses.append("(LOWER(COALESCE(status,''))='sent' OR status='已发送' OR signed_status='Sent')")
            elif status_key == "rejected":
                clauses.append("(LOWER(COALESCE(status,''))='rejected' OR status='已拒绝' OR signed_status='Rejected')")
            else:
                clauses.append("(LOWER(COALESCE(status,''))='draft' OR status='草稿' OR signed_status IN ('Pending','Draft',''))")
        if table == "customers":
            if "source_channel" in query and query["source_channel"] and query["source_channel"][0].strip():
                source_channel = normalize_key(query["source_channel"][0])
                clauses.append("COALESCE(source_channel,'manual')=?")
                params.append(source_channel)
            if "status" in query and query["status"] and query["status"][0].strip():
                status_filter = query["status"][0].strip()
                nk = normalize_key(status_filter)
                status_aliases = {
                    "new_lead": ["新线索", "Lead"],
                    "contacted": ["已联系", "In Progress"],
                    "site_visit_booked": ["已预约上门", "Measuring"],
                    "quoted": ["已报价", "Quoting"],
                    "signed": ["已签约", "Signed"],
                    "lost": ["已流失", "Lost"],
                }
                vals = status_aliases.get(nk, [status_filter])
                ph = ",".join(["?"] * len(vals))
                clauses.append(f"status IN ({ph})")
                params.extend(vals)
        if table == "designer_applications":
            if "status" in query and query["status"] and query["status"][0].strip():
                status_key = self._designer_app_status_key(query["status"][0])
                clauses.append("LOWER(COALESCE(status,''))=?")
                params.append(status_key)
        if table == "designers":
            if "status" in query and query["status"] and query["status"][0].strip():
                status_key = normalize_key(query["status"][0])
                if status_key not in {"active", "inactive"}:
                    status_key = "active"
                clauses.append("LOWER(COALESCE(status,''))=?")
                params.append(status_key)
        if table == "designer_assignments":
            if "status" in query and query["status"] and query["status"][0].strip():
                status_key = self._designer_assignment_status_key(query["status"][0])
                if status_key in DESIGNER_ASSIGNMENT_STATUS_SET:
                    clauses.append("LOWER(COALESCE(status,''))=?")
                    params.append(status_key)
            if "source_type" in query and query["source_type"] and query["source_type"][0].strip():
                source_type = normalize_key(query["source_type"][0])
                if source_type in DESIGNER_ASSIGNMENT_SOURCE_TYPES:
                    clauses.append("LOWER(COALESCE(source_type,''))=?")
                    params.append(source_type)
            if "designer_id" in query and query["designer_id"] and query["designer_id"][0].strip():
                try:
                    designer_id = int(query["designer_id"][0])
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "designer_id must be integer"}, 400)
                clauses.append("designer_id=?")
                params.append(designer_id)
        if user.get("role") == "designer":
            if table == "projects":
                clauses.append("designer_id=?")
                params.append(user.get("id"))
            elif table == "contracts":
                clauses.append("project_id IN (SELECT id FROM projects WHERE designer_id=?)")
                params.append(user.get("id"))
            elif "project_id" in TABLE_FIELDS[table]:
                clauses.append("project_id IN (SELECT id FROM projects WHERE designer_id=?)")
                params.append(user.get("id"))
            elif table == "contract_payment_milestones":
                clauses.append(
                    "contract_id IN (SELECT c.id FROM contracts c JOIN projects p ON p.contract_id=c.id WHERE p.designer_id=?)"
                )
                params.append(user.get("id"))
            elif table == "designer_commissions":
                clauses.append("project_id IN (SELECT id FROM projects WHERE designer_id=?)")
                params.append(user.get("id"))
            elif table == "designers":
                clauses.append("user_id=?")
                params.append(user.get("id"))
            elif table == "designer_permissions":
                clauses.append("designer_id IN (SELECT id FROM designers WHERE user_id=?)")
                params.append(user.get("id"))
            elif table == "designer_applications":
                clauses.append("(user_id=? OR designer_id IN (SELECT id FROM designers WHERE user_id=?))")
                params.extend([user.get("id"), user.get("id")])
            elif table == "designer_assignments":
                clauses.append("designer_id IN (SELECT id FROM designers WHERE user_id=?)")
                params.append(user.get("id"))
        if "keyword" in query:
            kw = f"%{query['keyword'][0]}%"
            searchable = [
                f
                for f in TABLE_FIELDS[table]
                if f
                in {
                    "name",
                    "title",
                    "order_no",
                    "phone",
                    "email",
                    "status",
                    "reason",
                    "description",
                    "file_name",
                    "content",
                    "source_channel",
                    "source_note",
                    "inquiry_type",
                    "primary_address",
                    "template_type",
                    "project_type",
                    "company_name",
                    "service_area",
                    "specialty",
                    "portfolio_url",
                }
            ]
            if searchable:
                clauses.append("(" + " OR ".join([f"{f} LIKE ?" for f in searchable]) + ")")
                params.extend([kw] * len(searchable))
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        if table == "document_templates":
            sql += " ORDER BY template_type ASC, project_type ASC, is_default DESC, updated_at DESC, id DESC"
        elif table == "project_stage_templates":
            sql += " ORDER BY project_type ASC, is_default DESC, is_active DESC, updated_at DESC, id DESC"
        elif table == "project_stage_template_items":
            sql += " ORDER BY template_id ASC, step_order ASC, id ASC"
        elif table == "payments":
            sql += " ORDER BY date DESC, id DESC"
        elif table == "bills":
            sql += " ORDER BY due_date ASC, id DESC"
        elif table == "vendors":
            sql += " ORDER BY id DESC"
        else:
            sql += " ORDER BY id DESC"

        cur.execute(sql, params)
        rows = [row_to_dict(r) for r in cur.fetchall()]
        self._enrich_resource_rows(cur, table, rows)
        conn.close()
        return self._json_response(rows)

    def _resource_post(self, path, user):
        table, record_id = self._parse_resource_path(path)
        if table not in TABLE_FIELDS or record_id is not None:
            return self._json_response({"error": "Unsupported resource"}, 404)
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        mod = RESOURCE_MODULE.get(table)
        if table == "document_templates":
            if not self._require_document_template_manage(user):
                return
        elif table == "change_orders":
            if not (self._has_module(user, "change_orders") or self._has_module(user, "projects")):
                return self._json_response({"error": "Forbidden: change_orders/projects"}, 403)
        else:
            if not self._require_module(user, mod):
                return

        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        if table == "change_orders" and not payload.get("title") and payload.get("reason"):
            payload["title"] = payload.get("reason")

        missing = [f for f in REQUIRED_FIELDS.get(table, []) if payload.get(f) in (None, "")]
        if missing:
            return self._json_response({"error": f"Missing required fields: {', '.join(missing)}"}, 400)

        conn = get_conn()
        cur = conn.cursor()

        fields = [f for f in TABLE_FIELDS[table] if f in payload]
        values = [payload.get(f) for f in fields]
        if table == "customers":
            source_channel = normalize_key(payload.get("source_channel") or payload.get("source") or "manual")
            if source_channel not in SOURCE_CHANNEL_SET:
                source_channel = "manual"
            inquiry_type = normalize_key(payload.get("inquiry_type") or "")
            if inquiry_type and inquiry_type not in INQUIRY_TYPE_SET:
                inquiry_type = "other"
            preferred = normalize_key(payload.get("preferred_contact_method") or "")
            if preferred and preferred not in CONTACT_METHOD_SET:
                preferred = "phone"
            if not payload.get("status"):
                payload["status"] = "新线索"
            payload["source_channel"] = source_channel
            if payload.get("source_note") in (None, "") and payload.get("source"):
                payload["source_note"] = payload.get("source")
            if source_channel and not payload.get("source"):
                payload["source"] = payload.get("source_note") or source_channel
            if inquiry_type:
                payload["inquiry_type"] = inquiry_type
                if not payload.get("demand_type"):
                    payload["demand_type"] = inquiry_type_to_demand_label(inquiry_type)
            if preferred:
                payload["preferred_contact_method"] = preferred
            # rebuild fields/values to include defaults
            fields = [f for f in TABLE_FIELDS[table] if f in payload]
            values = [payload.get(f) for f in fields]
        if table == "estimates":
            confirm_status = self._estimate_confirm_status_key(payload.get("confirm_status") or payload.get("status"))
            payload["confirm_status"] = confirm_status
            if not payload.get("status"):
                payload["status"] = self._estimate_legacy_status(confirm_status)
            if "status" not in fields:
                fields.append("status")
                values.append(payload.get("status"))
            if confirm_status == "confirmed":
                payload["confirmed_at"] = payload.get("confirmed_at") or now_ts()
                payload["confirmed_by"] = payload.get("confirmed_by") or user.get("id")
            if "confirm_status" not in fields:
                fields.append("confirm_status")
                values.append(payload["confirm_status"])
            if confirm_status == "confirmed":
                if "confirmed_at" not in fields:
                    fields.append("confirmed_at")
                    values.append(payload.get("confirmed_at"))
                if "confirmed_by" not in fields:
                    fields.append("confirmed_by")
                    values.append(payload.get("confirmed_by"))
            if payload.get("customer_id") and not payload.get("address"):
                cur.execute("SELECT primary_address,status FROM customers WHERE id=?", (payload.get("customer_id"),))
                c = cur.fetchone()
                if c and c["primary_address"]:
                    payload["address"] = c["primary_address"]
                    if "address" not in fields:
                        fields.append("address")
                        values.append(payload["address"])
                if c and not payload.get("lead_id") and normalize_key(c["status"] or "") in {
                    "lead",
                    "measuring",
                    "quoting",
                    "new_lead",
                    "contacted",
                    "site_visit_booked",
                    "quoted",
                }:
                    payload["lead_id"] = payload.get("customer_id")
                    if "lead_id" not in fields:
                        fields.append("lead_id")
                        values.append(payload["lead_id"])
        if table == "contracts":
            sign_status = self._contract_sign_status_key(payload.get("sign_status") or payload.get("signed_status"))
            payload["sign_status"] = sign_status
            payload["signed_status"] = self._contract_legacy_signed_status(sign_status)
            if sign_status == "signed":
                payload["signed_at"] = payload.get("signed_at") or now_ts()
                payload["signed_by"] = payload.get("signed_by") or user.get("id")
                payload["signed_date"] = payload.get("signed_date") or str(payload.get("signed_at"))[:10]
            if "sign_status" not in fields:
                fields.append("sign_status")
                values.append(payload.get("sign_status"))
            if "signed_status" not in fields:
                fields.append("signed_status")
                values.append(payload.get("signed_status"))
            if sign_status == "signed":
                if "signed_at" not in fields:
                    fields.append("signed_at")
                    values.append(payload.get("signed_at"))
                if "signed_by" not in fields:
                    fields.append("signed_by")
                    values.append(payload.get("signed_by"))
                if "signed_date" not in fields:
                    fields.append("signed_date")
                    values.append(payload.get("signed_date"))
        if table == "change_orders":
            payload = self._prepare_change_order_payload(cur, payload, existing=None)
            if not payload.get("title"):
                conn.close()
                return self._json_response({"error": "Missing required fields: title"}, 400)
            if not payload.get("project_id"):
                conn.close()
                return self._json_response({"error": "Missing required fields: project_id"}, 400)
            if not payload.get("created_by"):
                payload["created_by"] = user.get("id")
            fields = [f for f in TABLE_FIELDS[table] if f in payload]
            values = [payload.get(f) for f in fields]
        if table == "document_templates":
            try:
                payload = self._normalize_document_template_payload(payload, for_update=False)
            except ValueError as err:
                conn.close()
                return self._json_response({"error": str(err)}, 400)
            fields = [f for f in TABLE_FIELDS[table] if f in payload]
            values = [payload.get(f) for f in fields]
        if table == "project_stage_templates":
            try:
                payload = self._normalize_stage_template_payload(payload, for_update=False)
            except ValueError as err:
                conn.close()
                return self._json_response({"error": str(err)}, 400)
            payload["stages_json"] = payload.get("stages_json") or "[]"
            fields = [f for f in TABLE_FIELDS[table] if f in payload]
            values = [payload.get(f) for f in fields]
        if table == "project_stage_template_items":
            if payload.get("is_active") is None:
                payload["is_active"] = 1
            fields = [f for f in TABLE_FIELDS[table] if f in payload]
            values = [payload.get(f) for f in fields]
        if table == "projects":
            stage_template_id = payload.get("stage_template_id")
            if stage_template_id in ("", None):
                stage_template_id = self._resolve_default_stage_template_id(cur, payload.get("project_type"))
            else:
                try:
                    stage_template_id = int(stage_template_id)
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "Invalid stage_template_id"}, 400)
                cur.execute("SELECT id FROM project_stage_templates WHERE id=?", (stage_template_id,))
                if not cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "stage_template_id not found"}, 404)
            if stage_template_id:
                payload["stage_template_id"] = stage_template_id
                if "stage_template_id" not in fields:
                    fields.append("stage_template_id")
                    values.append(stage_template_id)
        if table == "designer_applications":
            source_channel = normalize_key(payload.get("source_channel") or "website")
            if source_channel not in SOURCE_CHANNEL_SET:
                source_channel = "website"
            payload["source_channel"] = source_channel
            payload["status"] = self._designer_app_status_key(payload.get("status") or "pending")
            if "source_channel" not in fields:
                fields.append("source_channel")
                values.append(payload.get("source_channel"))
            if "status" not in fields:
                fields.append("status")
                values.append(payload.get("status"))
        if table == "designers":
            payload["status"] = normalize_key(payload.get("status") or "active") or "active"
            if "status" not in fields:
                fields.append("status")
                values.append(payload.get("status"))
        if table == "designer_assignments":
            try:
                designer_id = int(payload.get("designer_id"))
            except (TypeError, ValueError):
                conn.close()
                return self._json_response({"error": "designer_id must be integer"}, 400)
            cur.execute("SELECT id,name,status FROM designers WHERE id=?", (designer_id,))
            drow = cur.fetchone()
            if not drow:
                conn.close()
                return self._json_response({"error": "designer_id not found"}, 404)
            source_type = normalize_key(payload.get("source_type") or "")
            if source_type not in DESIGNER_ASSIGNMENT_SOURCE_TYPES:
                conn.close()
                return self._json_response({"error": "source_type must be lead/project"}, 400)
            try:
                source_id = int(payload.get("source_id"))
            except (TypeError, ValueError):
                conn.close()
                return self._json_response({"error": "source_id must be integer"}, 400)
            assignment_type = normalize_key(payload.get("assignment_type") or "")
            if assignment_type not in DESIGNER_ASSIGNMENT_TYPE_SET:
                conn.close()
                return self._json_response({"error": "assignment_type not allowed"}, 400)
            status_key = self._designer_assignment_status_key(payload.get("status") or "new")
            payload["designer_id"] = designer_id
            payload["source_type"] = source_type
            payload["source_id"] = source_id
            payload["assignment_type"] = assignment_type
            payload["status"] = status_key
            payload["assigned_by"] = int(payload.get("assigned_by") or user.get("id") or 0) or None
            payload["assigned_at"] = (payload.get("assigned_at") or "").strip() or now_ts()
            if source_type == "lead":
                cur.execute("SELECT id FROM customers WHERE id=?", (source_id,))
                if not cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "Lead not found"}, 404)
            else:
                cur.execute("SELECT id FROM projects WHERE id=?", (source_id,))
                if not cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "Project not found"}, 404)
            fields = [f for f in TABLE_FIELDS[table] if f in payload]
            values = [payload.get(f) for f in fields]
        if table == "designer_permissions":
            payload["module_key"] = normalize_key(payload.get("module_key") or "")
            if payload["module_key"] not in DESIGNER_PERMISSION_MODULES:
                conn.close()
                return self._json_response({"error": "module_key not allowed"}, 400)
            payload["enabled"] = self._default_flag(payload.get("enabled"))
            if "module_key" not in fields:
                fields.append("module_key")
                values.append(payload.get("module_key"))
            if "enabled" not in fields:
                fields.append("enabled")
                values.append(payload.get("enabled"))
        if table == "vendors":
            vendor_name = str(payload.get("name") or "").strip()
            if not vendor_name:
                conn.close()
                return self._json_response({"error": "Missing required fields: name"}, 400)
            payload["name"] = vendor_name
            payload["type"] = self._vendor_type_key(payload.get("type"))
            payload["1099_required"] = 1 if self._default_flag(payload.get("1099_required")) or payload["type"] == "1099" else 0
            payload["w9_received"] = self._default_flag(payload.get("w9_received"))
            payload["tax_id"] = str(payload.get("tax_id") or "").strip() or None
            cur.execute("SELECT id FROM vendors WHERE LOWER(name)=LOWER(?)", (vendor_name,))
            existed = cur.fetchone()
            if existed:
                conn.close()
                return self._json_response({"error": "Vendor name already exists"}, 409)
            fields = [f for f in TABLE_FIELDS[table] if f in payload]
            values = [payload.get(f) for f in fields]
        if table == "bills":
            try:
                payload["vendor_id"] = int(payload.get("vendor_id"))
            except (TypeError, ValueError):
                conn.close()
                return self._json_response({"error": "vendor_id must be integer"}, 400)
            cur.execute("SELECT id FROM vendors WHERE id=?", (payload["vendor_id"],))
            if not cur.fetchone():
                conn.close()
                return self._json_response({"error": "vendor_id not found"}, 404)
            if payload.get("project_id") not in (None, "", 0, "0"):
                try:
                    payload["project_id"] = int(payload.get("project_id"))
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "project_id must be integer"}, 400)
                cur.execute("SELECT id FROM projects WHERE id=?", (payload["project_id"],))
                if not cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "project_id not found"}, 404)
            else:
                payload["project_id"] = None
            try:
                amount = float(payload.get("amount") or 0)
            except (TypeError, ValueError):
                conn.close()
                return self._json_response({"error": "amount must be number"}, 400)
            if amount <= 0:
                conn.close()
                return self._json_response({"error": "amount must be greater than 0"}, 400)
            payload["amount"] = round(amount, 2)
            try:
                paid_amount = float(payload.get("paid_amount") or 0)
            except (TypeError, ValueError):
                paid_amount = 0
            paid_amount = max(min(paid_amount, payload["amount"]), 0)
            payload["paid_amount"] = round(paid_amount, 2)
            if paid_amount <= 0:
                payload["status"] = "Open"
            elif paid_amount >= payload["amount"]:
                payload["status"] = "Paid"
            else:
                payload["status"] = "Partially Paid"
            if payload.get("bill_no") is not None:
                payload["bill_no"] = str(payload.get("bill_no") or "").strip() or None
            fields = [f for f in TABLE_FIELDS[table] if f in payload]
            values = [payload.get(f) for f in fields]
        if table == "payments":
            try:
                payload["vendor_id"] = int(payload.get("vendor_id"))
            except (TypeError, ValueError):
                conn.close()
                return self._json_response({"error": "vendor_id must be integer"}, 400)
            cur.execute("SELECT id FROM vendors WHERE id=?", (payload["vendor_id"],))
            if not cur.fetchone():
                conn.close()
                return self._json_response({"error": "vendor_id not found"}, 404)
            if payload.get("project_id") not in (None, "", 0, "0"):
                try:
                    payload["project_id"] = int(payload.get("project_id"))
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "project_id must be integer"}, 400)
                cur.execute("SELECT id FROM projects WHERE id=?", (payload["project_id"],))
                if not cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "project_id not found"}, 404)
            else:
                payload["project_id"] = None
            bill_id = None
            if payload.get("bill_id") not in (None, "", 0, "0"):
                try:
                    bill_id = int(payload.get("bill_id"))
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "bill_id must be integer"}, 400)
                cur.execute("SELECT id,vendor_id,project_id,category FROM bills WHERE id=?", (bill_id,))
                bill = cur.fetchone()
                if not bill:
                    conn.close()
                    return self._json_response({"error": "bill_id not found"}, 404)
                if int(bill["vendor_id"] or 0) != int(payload["vendor_id"]):
                    conn.close()
                    return self._json_response({"error": "bill vendor mismatch"}, 400)
                if payload["project_id"] is None and bill["project_id"] is not None:
                    payload["project_id"] = int(bill["project_id"])
                if not payload.get("category") and bill["category"]:
                    payload["category"] = bill["category"]
            payload["bill_id"] = bill_id
            try:
                amount = float(payload.get("amount") or 0)
            except (TypeError, ValueError):
                conn.close()
                return self._json_response({"error": "amount must be number"}, 400)
            if amount <= 0:
                conn.close()
                return self._json_response({"error": "amount must be greater than 0"}, 400)
            payload["amount"] = round(amount, 2)
            payment_date = str(payload.get("date") or "").strip()
            if not payment_date:
                payment_date = to_iso_date(datetime.now())
            payload["date"] = payment_date
            method_key = normalize_key(payload.get("method") or "other")
            payload["method"] = method_key if method_key in PAYMENT_METHOD_SET else "other"
            fields = [f for f in TABLE_FIELDS[table] if f in payload]
            values = [payload.get(f) for f in fields]
        if table == "project_payments":
            if "received_amount" not in fields:
                fields.append("received_amount")
                values.append(payload.get("amount") if payload.get("status") == "Paid" else 0)
            if "payment_method" not in fields:
                fields.append("payment_method")
                values.append(payload.get("payment_method"))
        if table == "ap_payables":
            if "paid_amount" not in fields:
                fields.append("paid_amount")
                values.append(payload.get("amount") if payload.get("status") == "Paid" else 0)
        ts = now_ts()
        fields += ["created_at", "updated_at"]
        values += [ts, ts]
        ph = ",".join(["?"] * len(fields))
        quoted_fields = ",".join([f'"{f}"' for f in fields])
        cur.execute(f'INSERT INTO "{table}"({quoted_fields}) VALUES ({ph})', values)
        new_id = cur.lastrowid

        if table == "projects":
            self._init_default_project_stages(cur, new_id)
            self._recalc_designer_commission_for_project(cur, new_id)

        if table == "change_orders" and payload.get("project_id"):
            self._recalc_designer_commission_for_project(cur, payload.get("project_id"))

        if table == "contracts":
            self._evaluate_contract_payment_milestones(cur, contract_id=new_id, project_id=payload.get("project_id"))
            if payload.get("project_id"):
                self._recalc_designer_commission_for_project(cur, payload.get("project_id"))
            if payload.get("estimate_id"):
                cur.execute(
                    "UPDATE estimates SET contract_id=COALESCE(contract_id,?), updated_at=? WHERE id=?",
                    (new_id, ts, payload.get("estimate_id")),
                )

        if table == "contract_payment_milestones":
            cur.execute("SELECT project_id,total_amount FROM contracts WHERE id=?", (payload.get("contract_id"),))
            c = cur.fetchone()
            if c:
                self._evaluate_contract_payment_milestones(cur, contract_id=payload.get("contract_id"), project_id=c["project_id"])
                if c["project_id"]:
                    self._recalc_designer_commission_for_project(cur, c["project_id"])
        if table == "document_templates" and int(payload.get("is_default") or 0) == 1:
            self._set_document_template_default(cur, new_id, payload.get("template_type"), payload.get("project_type"))
        if table == "project_stage_templates":
            if int(payload.get("is_default") or 0) == 1:
                self._set_stage_template_default(cur, new_id, payload.get("project_type"))
            self._sync_stage_template_stages_json(cur, new_id)
        if table == "project_stage_template_items":
            self._sync_stage_template_stages_json(cur, payload.get("template_id"))
        if table == "payments":
            self._sync_bill_paid_amount(cur, payload.get("bill_id"))

        conn.commit()
        cur.execute(f"SELECT * FROM {table} WHERE id=?", (new_id,))
        row = row_to_dict(cur.fetchone())
        self._enrich_resource_rows(cur, table, [row])
        if table == "project_stages":
            self._recalc_project_progress(cur, row.get("project_id"))
            conn.commit()
        conn.close()
        return self._json_response(row, 201)

    def _resource_put(self, path, user):
        table, record_id = self._parse_resource_path(path)
        if table not in TABLE_FIELDS or record_id is None:
            return self._json_response({"error": "Unsupported resource"}, 404)
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        mod = RESOURCE_MODULE.get(table)
        if table == "document_templates":
            if not self._require_document_template_manage(user):
                return
        elif table == "change_orders":
            if not (self._has_module(user, "change_orders") or self._has_module(user, "projects")):
                return self._json_response({"error": "Forbidden: change_orders/projects"}, 403)
        else:
            if not self._require_module(user, mod):
                return

        payload = self._read_json_body()
        if payload is None:
            return self._json_response({"error": "Invalid JSON"}, 400)
        incoming_payload = dict(payload or {})

        conn = get_conn()
        cur = conn.cursor()
        project_id = self._project_id_for_table_record(cur, table, record_id)
        old_payment_bill_id = None
        if table == "payments":
            cur.execute("SELECT bill_id FROM payments WHERE id=?", (record_id,))
            prow = cur.fetchone()
            old_payment_bill_id = prow["bill_id"] if prow else None

        if table == "change_orders":
            cur.execute("SELECT * FROM change_orders WHERE id=?", (record_id,))
            existing = cur.fetchone()
            if not existing:
                conn.close()
                return self._json_response({"error": "Record not found"}, 404)
            payload = self._prepare_change_order_payload(cur, payload, existing=row_to_dict(existing))
        if table == "document_templates":
            cur.execute("SELECT * FROM document_templates WHERE id=?", (record_id,))
            existing = cur.fetchone()
            if not existing:
                conn.close()
                return self._json_response({"error": "Record not found"}, 404)
            merged = row_to_dict(existing)
            merged.update(incoming_payload)
            try:
                normalized = self._normalize_document_template_payload(merged, for_update=False)
            except ValueError as err:
                conn.close()
                return self._json_response({"error": str(err)}, 400)
            payload = {}
            for key in TABLE_FIELDS["document_templates"]:
                if key in incoming_payload:
                    payload[key] = normalized.get(key)
            if not payload:
                conn.close()
                return self._json_response({"error": "No fields to update"}, 400)
        if table == "project_stage_templates":
            cur.execute("SELECT * FROM project_stage_templates WHERE id=?", (record_id,))
            existing = cur.fetchone()
            if not existing:
                conn.close()
                return self._json_response({"error": "Record not found"}, 404)
            merged = row_to_dict(existing)
            merged.update(incoming_payload)
            try:
                normalized = self._normalize_stage_template_payload(merged, for_update=False)
            except ValueError as err:
                conn.close()
                return self._json_response({"error": str(err)}, 400)
            payload = {}
            for key in TABLE_FIELDS["project_stage_templates"]:
                if key in incoming_payload:
                    payload[key] = normalized.get(key)
            if "stages_json" not in payload:
                payload["stages_json"] = merged.get("stages_json") or "[]"
            if not payload:
                conn.close()
                return self._json_response({"error": "No fields to update"}, 400)
        if table == "project_stage_template_items":
            if "template_id" in incoming_payload:
                try:
                    template_id = int(incoming_payload.get("template_id"))
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "Invalid template_id"}, 400)
                cur.execute("SELECT id FROM project_stage_templates WHERE id=?", (template_id,))
                if not cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "template_id not found"}, 404)
                payload["template_id"] = template_id
            if "is_active" in incoming_payload:
                payload["is_active"] = self._default_flag(incoming_payload.get("is_active"))
            if "step_order" in incoming_payload:
                try:
                    payload["step_order"] = int(incoming_payload.get("step_order"))
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "Invalid step_order"}, 400)
            if "step_name" in incoming_payload:
                step_name = str(incoming_payload.get("step_name") or "").strip()
                if not step_name:
                    conn.close()
                    return self._json_response({"error": "step_name is required"}, 400)
                payload["step_name"] = step_name
        if table == "estimates":
            cur.execute("SELECT * FROM estimates WHERE id=?", (record_id,))
            existing = cur.fetchone()
            if not existing:
                conn.close()
                return self._json_response({"error": "Record not found"}, 404)
            existing = row_to_dict(existing)
            current_confirm = self._estimate_confirm_status_key(existing.get("confirm_status") or existing.get("status"))
            incoming_confirm = None
            if "confirm_status" in incoming_payload or "status" in incoming_payload:
                incoming_confirm = self._estimate_confirm_status_key(payload.get("confirm_status") or payload.get("status"))
                allowed_from = {
                    "sent": {"draft"},
                    "confirmed": {"sent"},
                    "rejected": {"sent"},
                }
                if incoming_confirm != current_confirm and current_confirm not in allowed_from.get(incoming_confirm, set()):
                    conn.close()
                    return self._json_response({"error": f"Invalid transition: {current_confirm} -> {incoming_confirm}"}, 400)
                payload["confirm_status"] = incoming_confirm
                payload["status"] = self._estimate_legacy_status(incoming_confirm)
                if incoming_confirm == "confirmed":
                    payload["confirmed_at"] = payload.get("confirmed_at") or existing.get("confirmed_at") or now_ts()
                    payload["confirmed_by"] = payload.get("confirmed_by") or existing.get("confirmed_by") or user.get("id")

            if "manual_adjustment" in incoming_payload:
                try:
                    payload["manual_adjustment"] = round(float(incoming_payload.get("manual_adjustment") or 0), 2)
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "manual_adjustment must be number"}, 400)

            if current_confirm == "confirmed":
                locked_fields = {"subtotal", "markup_rate", "manual_adjustment", "total_amount", "line_items_json"}
                touched_locked = [k for k in locked_fields if k in incoming_payload]
                if touched_locked:
                    conn.close()
                    return self._json_response({"error": f"Estimate already confirmed. Locked fields: {', '.join(sorted(touched_locked))}"}, 400)
        if table == "contracts":
            cur.execute("SELECT * FROM contracts WHERE id=?", (record_id,))
            existing = cur.fetchone()
            if not existing:
                conn.close()
                return self._json_response({"error": "Record not found"}, 404)
            existing = row_to_dict(existing)
            current_sign = self._contract_sign_status_key(existing.get("sign_status") or existing.get("signed_status"))
            if "sign_status" in incoming_payload or "signed_status" in incoming_payload:
                incoming_sign = self._contract_sign_status_key(payload.get("sign_status") or payload.get("signed_status"))
                allowed_from = {
                    "sent": {"draft"},
                    "signed": {"sent"},
                }
                if incoming_sign != current_sign and current_sign not in allowed_from.get(incoming_sign, set()):
                    conn.close()
                    return self._json_response({"error": f"Invalid transition: {current_sign} -> {incoming_sign}"}, 400)
                payload["sign_status"] = incoming_sign
                payload["signed_status"] = self._contract_legacy_signed_status(incoming_sign)
                if incoming_sign == "signed":
                    payload["signed_at"] = payload.get("signed_at") or existing.get("signed_at") or now_ts()
                    payload["signed_by"] = payload.get("signed_by") or existing.get("signed_by") or user.get("id")
                    payload["signed_date"] = payload.get("signed_date") or existing.get("signed_date") or str(payload.get("signed_at"))[:10]
        fields = [f for f in TABLE_FIELDS[table] if f in payload]
        if not fields:
            conn.close()
            return self._json_response({"error": "No fields to update"}, 400)
        if table == "project_payments" and "status" in payload and payload.get("status") == "Paid" and "received_amount" not in fields:
            fields.append("received_amount")
            payload["received_amount"] = payload.get("amount", 0)
        if table == "ap_payables" and "status" in payload and payload.get("status") == "Paid" and "paid_amount" not in fields:
            fields.append("paid_amount")
            payload["paid_amount"] = payload.get("amount", 0)
        if table == "customers":
            if "source_channel" in payload:
                source_channel = normalize_key(payload.get("source_channel") or "")
                payload["source_channel"] = source_channel if source_channel in SOURCE_CHANNEL_SET else "manual"
                if "source_channel" not in fields:
                    fields.append("source_channel")
            if "inquiry_type" in payload:
                inquiry_type = normalize_key(payload.get("inquiry_type") or "")
                if inquiry_type not in INQUIRY_TYPE_SET:
                    inquiry_type = "other"
                payload["inquiry_type"] = inquiry_type
                if "inquiry_type" not in fields:
                    fields.append("inquiry_type")
                if "demand_type" not in payload and "demand_type" not in fields:
                    payload["demand_type"] = inquiry_type_to_demand_label(inquiry_type)
                    fields.append("demand_type")
            if "preferred_contact_method" in payload:
                preferred = normalize_key(payload.get("preferred_contact_method") or "")
                payload["preferred_contact_method"] = preferred if preferred in CONTACT_METHOD_SET else "phone"
                if "preferred_contact_method" not in fields:
                    fields.append("preferred_contact_method")
            if "source_note" in payload and ("source" not in payload) and "source" not in fields:
                payload["source"] = payload.get("source_note") or payload.get("source_channel") or ""
                fields.append("source")
            # refresh values after customer-specific normalization
            fields = list(dict.fromkeys(fields))
        if table == "projects" and "stage_template_id" in payload:
            stage_template_id = payload.get("stage_template_id")
            if stage_template_id in (None, "", 0, "0"):
                payload["stage_template_id"] = None
            else:
                try:
                    stage_template_id = int(stage_template_id)
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "Invalid stage_template_id"}, 400)
                cur.execute("SELECT id FROM project_stage_templates WHERE id=?", (stage_template_id,))
                if not cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "stage_template_id not found"}, 404)
                payload["stage_template_id"] = stage_template_id
        if table == "designer_applications":
            if "source_channel" in payload:
                source_channel = normalize_key(payload.get("source_channel") or "website")
                if source_channel not in SOURCE_CHANNEL_SET:
                    source_channel = "website"
                payload["source_channel"] = source_channel
            if "status" in payload:
                payload["status"] = self._designer_app_status_key(payload.get("status"))
        if table == "designers" and "status" in payload:
            payload["status"] = normalize_key(payload.get("status") or "active") or "active"
        if table == "designer_assignments":
            if "designer_id" in payload:
                try:
                    payload["designer_id"] = int(payload.get("designer_id"))
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "designer_id must be integer"}, 400)
                cur.execute("SELECT id FROM designers WHERE id=?", (payload.get("designer_id"),))
                if not cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "designer_id not found"}, 404)
            if "source_type" in payload:
                source_type = normalize_key(payload.get("source_type") or "")
                if source_type not in DESIGNER_ASSIGNMENT_SOURCE_TYPES:
                    conn.close()
                    return self._json_response({"error": "source_type must be lead/project"}, 400)
                payload["source_type"] = source_type
            if "source_id" in payload:
                try:
                    payload["source_id"] = int(payload.get("source_id"))
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "source_id must be integer"}, 400)
            source_type_for_check = payload.get("source_type")
            source_id_for_check = payload.get("source_id")
            if source_type_for_check is None or source_id_for_check is None:
                cur.execute("SELECT source_type,source_id FROM designer_assignments WHERE id=?", (record_id,))
                existing_assign = cur.fetchone()
                if existing_assign:
                    if source_type_for_check is None:
                        source_type_for_check = existing_assign["source_type"]
                    if source_id_for_check is None:
                        source_id_for_check = existing_assign["source_id"]
            if source_type_for_check is not None and source_id_for_check is not None:
                source_type_key = normalize_key(source_type_for_check)
                if source_type_key == "lead":
                    cur.execute("SELECT id FROM customers WHERE id=?", (source_id_for_check,))
                    if not cur.fetchone():
                        conn.close()
                        return self._json_response({"error": "Lead not found"}, 404)
                elif source_type_key == "project":
                    cur.execute("SELECT id FROM projects WHERE id=?", (source_id_for_check,))
                    if not cur.fetchone():
                        conn.close()
                        return self._json_response({"error": "Project not found"}, 404)
            if "assignment_type" in payload:
                assignment_type = normalize_key(payload.get("assignment_type") or "")
                if assignment_type not in DESIGNER_ASSIGNMENT_TYPE_SET:
                    conn.close()
                    return self._json_response({"error": "assignment_type not allowed"}, 400)
                payload["assignment_type"] = assignment_type
            if "status" in payload:
                status_key = self._designer_assignment_status_key(payload.get("status") or "new")
                if status_key not in DESIGNER_ASSIGNMENT_STATUS_SET:
                    conn.close()
                    return self._json_response({"error": "status not allowed"}, 400)
                payload["status"] = status_key
            if "assigned_by" in payload:
                if payload.get("assigned_by") in ("", None):
                    payload["assigned_by"] = None
                else:
                    try:
                        payload["assigned_by"] = int(payload.get("assigned_by"))
                    except (TypeError, ValueError):
                        conn.close()
                        return self._json_response({"error": "assigned_by must be integer"}, 400)
        if table == "designer_permissions":
            if "module_key" in payload:
                module_key = normalize_key(payload.get("module_key") or "")
                if module_key not in DESIGNER_PERMISSION_MODULES:
                    conn.close()
                    return self._json_response({"error": "module_key not allowed"}, 400)
                payload["module_key"] = module_key
            if "enabled" in payload:
                payload["enabled"] = self._default_flag(payload.get("enabled"))
        if table == "vendors":
            if "name" in payload:
                vendor_name = str(payload.get("name") or "").strip()
                if not vendor_name:
                    conn.close()
                    return self._json_response({"error": "name cannot be empty"}, 400)
                cur.execute("SELECT id FROM vendors WHERE LOWER(name)=LOWER(?) AND id<>?", (vendor_name, record_id))
                if cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "Vendor name already exists"}, 409)
                payload["name"] = vendor_name
            if "type" in payload:
                payload["type"] = self._vendor_type_key(payload.get("type"))
            if "1099_required" in payload:
                payload["1099_required"] = self._default_flag(payload.get("1099_required"))
            if "w9_received" in payload:
                payload["w9_received"] = self._default_flag(payload.get("w9_received"))
            if "tax_id" in payload:
                payload["tax_id"] = str(payload.get("tax_id") or "").strip() or None
            if payload.get("type") == "1099" and "1099_required" not in payload:
                payload["1099_required"] = 1
                if "1099_required" not in fields:
                    fields.append("1099_required")
        if table == "bills":
            if "vendor_id" in payload:
                try:
                    payload["vendor_id"] = int(payload.get("vendor_id"))
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "vendor_id must be integer"}, 400)
                cur.execute("SELECT id FROM vendors WHERE id=?", (payload["vendor_id"],))
                if not cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "vendor_id not found"}, 404)
            if "project_id" in payload:
                if payload.get("project_id") in (None, "", 0, "0"):
                    payload["project_id"] = None
                else:
                    try:
                        payload["project_id"] = int(payload.get("project_id"))
                    except (TypeError, ValueError):
                        conn.close()
                        return self._json_response({"error": "project_id must be integer"}, 400)
                    cur.execute("SELECT id FROM projects WHERE id=?", (payload["project_id"],))
                    if not cur.fetchone():
                        conn.close()
                        return self._json_response({"error": "project_id not found"}, 404)
            if "amount" in payload:
                try:
                    payload["amount"] = round(float(payload.get("amount") or 0), 2)
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "amount must be number"}, 400)
                if payload["amount"] <= 0:
                    conn.close()
                    return self._json_response({"error": "amount must be greater than 0"}, 400)
            if "paid_amount" in payload:
                try:
                    payload["paid_amount"] = round(float(payload.get("paid_amount") or 0), 2)
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "paid_amount must be number"}, 400)
                payload["paid_amount"] = max(payload["paid_amount"], 0)
            if "bill_no" in payload:
                payload["bill_no"] = str(payload.get("bill_no") or "").strip() or None
            if "amount" in payload or "paid_amount" in payload:
                cur.execute("SELECT amount,paid_amount FROM bills WHERE id=?", (record_id,))
                b = cur.fetchone()
                amount = float(payload.get("amount") if "amount" in payload else (b["amount"] if b else 0) or 0)
                paid_amount = float(payload.get("paid_amount") if "paid_amount" in payload else (b["paid_amount"] if b else 0) or 0)
                paid_amount = max(min(paid_amount, amount), 0)
                payload["paid_amount"] = round(paid_amount, 2)
                payload["status"] = "Open" if paid_amount <= 0 else ("Paid" if paid_amount >= amount else "Partially Paid")
                if "paid_amount" not in fields:
                    fields.append("paid_amount")
                if "status" not in fields:
                    fields.append("status")
        if table == "payments":
            if "vendor_id" in payload:
                try:
                    payload["vendor_id"] = int(payload.get("vendor_id"))
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "vendor_id must be integer"}, 400)
                cur.execute("SELECT id FROM vendors WHERE id=?", (payload["vendor_id"],))
                if not cur.fetchone():
                    conn.close()
                    return self._json_response({"error": "vendor_id not found"}, 404)
            if "project_id" in payload:
                if payload.get("project_id") in (None, "", 0, "0"):
                    payload["project_id"] = None
                else:
                    try:
                        payload["project_id"] = int(payload.get("project_id"))
                    except (TypeError, ValueError):
                        conn.close()
                        return self._json_response({"error": "project_id must be integer"}, 400)
                    cur.execute("SELECT id FROM projects WHERE id=?", (payload["project_id"],))
                    if not cur.fetchone():
                        conn.close()
                        return self._json_response({"error": "project_id not found"}, 404)
            if "bill_id" in payload:
                if payload.get("bill_id") in (None, "", 0, "0"):
                    payload["bill_id"] = None
                else:
                    try:
                        payload["bill_id"] = int(payload.get("bill_id"))
                    except (TypeError, ValueError):
                        conn.close()
                        return self._json_response({"error": "bill_id must be integer"}, 400)
                    cur.execute("SELECT id,vendor_id,project_id,category FROM bills WHERE id=?", (payload["bill_id"],))
                    b = cur.fetchone()
                    if not b:
                        conn.close()
                        return self._json_response({"error": "bill_id not found"}, 404)
                    vendor_for_check = payload.get("vendor_id")
                    if vendor_for_check is None:
                        cur.execute("SELECT vendor_id FROM payments WHERE id=?", (record_id,))
                        prow = cur.fetchone()
                        vendor_for_check = prow["vendor_id"] if prow else None
                    if vendor_for_check is not None and int(vendor_for_check) != int(b["vendor_id"]):
                        conn.close()
                        return self._json_response({"error": "bill vendor mismatch"}, 400)
                    if payload.get("project_id") is None and b["project_id"] is not None:
                        payload["project_id"] = int(b["project_id"])
                        if "project_id" not in fields:
                            fields.append("project_id")
                    if not payload.get("category") and b["category"]:
                        payload["category"] = b["category"]
                        if "category" not in fields:
                            fields.append("category")
            if "amount" in payload:
                try:
                    payload["amount"] = round(float(payload.get("amount") or 0), 2)
                except (TypeError, ValueError):
                    conn.close()
                    return self._json_response({"error": "amount must be number"}, 400)
                if payload["amount"] <= 0:
                    conn.close()
                    return self._json_response({"error": "amount must be greater than 0"}, 400)
            if "date" in payload:
                payload["date"] = str(payload.get("date") or "").strip() or to_iso_date(datetime.now())
            if "method" in payload:
                method_key = normalize_key(payload.get("method") or "other")
                payload["method"] = method_key if method_key in PAYMENT_METHOD_SET else "other"

        payload["updated_at"] = now_ts()
        fields.append("updated_at")
        values = [payload.get(f) for f in fields] + [record_id]
        set_expr = ",".join([f'"{f}"=?' for f in fields])
        cur.execute(f'UPDATE "{table}" SET {set_expr} WHERE id=?', values)
        if cur.rowcount == 0:
            conn.close()
            return self._json_response({"error": "Record not found"}, 404)

        if table == "change_orders" and project_id:
            self._recalc_designer_commission_for_project(cur, project_id)

        conn.commit()
        cur.execute(f"SELECT * FROM {table} WHERE id=?", (record_id,))
        row = row_to_dict(cur.fetchone())
        if table == "project_stages":
            self._recalc_project_progress(cur, row.get("project_id"))
            conn.commit()
        if table == "contracts":
            linked_project_id = payload.get("project_id") or row.get("project_id")
            self._evaluate_contract_payment_milestones(cur, contract_id=record_id, project_id=linked_project_id)
            if linked_project_id:
                self._recalc_designer_commission_for_project(cur, linked_project_id)
            if row.get("estimate_id"):
                cur.execute(
                    "UPDATE estimates SET contract_id=COALESCE(contract_id,?), updated_at=? WHERE id=?",
                    (record_id, now_ts(), row.get("estimate_id")),
                )
            conn.commit()
        if table == "projects":
            self._evaluate_project_payment_triggers(cur, record_id)
            self._recalc_designer_commission_for_project(cur, record_id)
            conn.commit()
        if table == "contract_payment_milestones":
            cur.execute("SELECT project_id,total_amount FROM contracts WHERE id=?", (row.get("contract_id"),))
            c = cur.fetchone()
            self._evaluate_contract_payment_milestones(cur, contract_id=row.get("contract_id"), project_id=(c["project_id"] if c else None))
            if c and c["project_id"]:
                self._recalc_designer_commission_for_project(cur, c["project_id"])
            conn.commit()
        if table == "project_payments" and project_id:
            self._recalc_designer_commission_for_project(cur, project_id)
            conn.commit()
        if table == "document_templates":
            target_type = row.get("template_type")
            target_project_type = row.get("project_type")
            if int(row.get("is_default") or 0) == 1:
                self._set_document_template_default(cur, record_id, target_type, target_project_type)
                conn.commit()
        if table == "project_stage_templates":
            if int(row.get("is_default") or 0) == 1:
                self._set_stage_template_default(cur, record_id, row.get("project_type"))
            self._sync_stage_template_stages_json(cur, record_id)
            conn.commit()
        if table == "project_stage_template_items":
            self._sync_stage_template_stages_json(cur, row.get("template_id"))
            conn.commit()
        if table == "payments":
            self._sync_bill_paid_amount(cur, old_payment_bill_id)
            self._sync_bill_paid_amount(cur, row.get("bill_id"))
            conn.commit()
        self._enrich_resource_rows(cur, table, [row])
        conn.close()
        return self._json_response(row)

    def _resource_delete(self, path, user):
        table, record_id = self._parse_resource_path(path)
        if table not in TABLE_FIELDS or record_id is None:
            return self._json_response({"error": "Unsupported resource"}, 404)
        if user.get("role") == "designer":
            return self._json_response({"error": "Forbidden: designer read-only"}, 403)
        mod = RESOURCE_MODULE.get(table)
        if table == "document_templates":
            if not self._require_document_template_manage(user):
                return
        elif table == "change_orders":
            if not (self._has_module(user, "change_orders") or self._has_module(user, "projects")):
                return self._json_response({"error": "Forbidden: change_orders/projects"}, 403)
        else:
            if not self._require_module(user, mod):
                return

        conn = get_conn()
        cur = conn.cursor()
        project_id = self._project_id_for_table_record(cur, table, record_id)
        deleted_payment_bill_id = None
        if table == "payments":
            cur.execute("SELECT bill_id FROM payments WHERE id=?", (record_id,))
            prow = cur.fetchone()
            deleted_payment_bill_id = prow["bill_id"] if prow else None
        linked_contract_id = None
        if table == "project_stage_templates":
            cur.execute("SELECT COUNT(1) c FROM projects WHERE stage_template_id=?", (record_id,))
            linked_count = int((cur.fetchone() or {"c": 0})["c"] or 0)
            if linked_count > 0:
                ts = now_ts()
                cur.execute("UPDATE project_stage_templates SET is_active=0, updated_at=? WHERE id=?", (ts, record_id))
                conn.commit()
                cur.execute("SELECT * FROM project_stage_templates WHERE id=?", (record_id,))
                row = row_to_dict(cur.fetchone())
                self._enrich_resource_rows(cur, "project_stage_templates", [row])
                conn.close()
                return self._json_response({"ok": True, "soft_disabled": True, "linked_project_count": linked_count, "template": row})
            cur.execute("DELETE FROM project_stage_template_items WHERE template_id=?", (record_id,))
        if table == "contract_payment_milestones":
            cur.execute("SELECT contract_id FROM contract_payment_milestones WHERE id=?", (record_id,))
            r = cur.fetchone()
            linked_contract_id = r["contract_id"] if r else None
        linked_template_id = None
        if table == "project_stage_template_items":
            cur.execute("SELECT template_id FROM project_stage_template_items WHERE id=?", (record_id,))
            r = cur.fetchone()
            linked_template_id = r["template_id"] if r else None
        cur.execute(f"DELETE FROM {table} WHERE id=?", (record_id,))
        if cur.rowcount == 0:
            conn.close()
            return self._json_response({"error": "Record not found"}, 404)
        if table == "project_stages" and project_id:
            self._recalc_project_progress(cur, project_id)
        if table == "contract_payment_milestones" and linked_contract_id:
            self._evaluate_contract_payment_milestones(cur, contract_id=linked_contract_id, project_id=project_id)
        if table == "change_orders" and project_id:
            self._evaluate_project_payment_triggers(cur, project_id)
        if table == "project_stage_template_items" and linked_template_id:
            self._sync_stage_template_stages_json(cur, linked_template_id)
        if table == "payments":
            self._sync_bill_paid_amount(cur, deleted_payment_bill_id)
        if table in {"project_payments", "change_orders", "project_stages", "contract_payment_milestones"} and project_id:
            self._recalc_designer_commission_for_project(cur, project_id)
        conn.commit()
        conn.close()
        return self._json_response({"ok": True})

    def _recalc_project_progress(self, cur, project_id):
        cur.execute("SELECT COUNT(1) c FROM project_stages WHERE project_id=?", (project_id,))
        total = cur.fetchone()["c"]
        done = 0
        in_progress = 0
        if total == 0:
            pct = 0
        else:
            cur.execute("SELECT COUNT(1) c FROM project_stages WHERE project_id=? AND status='done'", (project_id,))
            done = cur.fetchone()["c"]
            cur.execute("SELECT COUNT(1) c FROM project_stages WHERE project_id=? AND status='in_progress'", (project_id,))
            in_progress = cur.fetchone()["c"]
            pct = int(round(done * 100 / total))

        cur.execute("SELECT status FROM projects WHERE id=?", (project_id,))
        project_row = cur.fetchone()
        current_status = project_row["status"] if project_row else ""
        current_status_key = self._project_status_key(current_status)

        is_completed = (pct >= 100) or (total > 0 and done >= total)
        if is_completed:
            next_status = "Completed"
        elif current_status_key == "on_hold":
            # Preserve manually paused projects until user resumes them.
            next_status = current_status or "On Hold"
        elif done == 0 and in_progress == 0:
            next_status = "Not Started"
        else:
            next_status = "In Progress"

        cur.execute(
            "UPDATE projects SET progress_pct=?, status=?, updated_at=? WHERE id=?",
            (pct, next_status, now_ts(), project_id),
        )
        self._evaluate_project_payment_triggers(cur, project_id)
        self._recalc_designer_commission_for_project(cur, project_id)

    def _init_default_project_stages(self, cur, project_id):
        cur.execute("SELECT COUNT(1) c FROM project_stages WHERE project_id=?", (project_id,))
        if (cur.fetchone() or {"c": 0})["c"] > 0:
            return
        cur.execute("SELECT project_type,stage_template_id,estimate_id FROM projects WHERE id=?", (project_id,))
        prow = cur.fetchone()
        p = row_to_dict(prow) if prow else None
        stage_template_id = None
        if p and p.get("stage_template_id"):
            stage_template_id = int(p.get("stage_template_id"))
        if not stage_template_id and p:
            stage_template_id = self._resolve_default_stage_template_id(cur, p.get("project_type"))
            if stage_template_id:
                cur.execute(
                    "UPDATE projects SET stage_template_id=?, updated_at=? WHERE id=?",
                    (stage_template_id, now_ts(), project_id),
                )
        stage_names = self._stage_template_stage_names(cur, stage_template_id) if stage_template_id else []
        if not stage_names:
            stage_names = list(DEFAULT_PROJECT_STAGES)
        if p:
            stage_names = self._append_unique_stage_names(
                stage_names,
                self._estimate_custom_payment_stage_names(cur, p.get("estimate_id")),
            )
        self._replace_project_stages(cur, project_id, stage_names)

    def _apply_change_order(self, cur, change_order_id):
        cur.execute("SELECT project_id,amount_delta,days_delta FROM change_orders WHERE id=?", (change_order_id,))
        row = cur.fetchone()
        if not row:
            return
        project_id = row["project_id"]
        amount_delta = row["amount_delta"] or 0
        days_delta = row["days_delta"] or 0

        cur.execute("SELECT contract_id,estimated_finish_date FROM projects WHERE id=?", (project_id,))
        proj = cur.fetchone()
        if not proj:
            return
        if proj["contract_id"]:
            cur.execute("UPDATE contracts SET total_amount=COALESCE(total_amount,0)+?,updated_at=? WHERE id=?", (amount_delta, now_ts(), proj["contract_id"]))
        if proj["estimated_finish_date"] and days_delta:
            try:
                old_date = datetime.strptime(proj["estimated_finish_date"], "%Y-%m-%d")
                new_date = old_date + timedelta(days=int(days_delta))
                cur.execute("UPDATE projects SET estimated_finish_date=?,updated_at=? WHERE id=?", (to_iso_date(new_date), now_ts(), project_id))
            except ValueError:
                pass


def run(host=None, port=None):
    setup_logging()
    init_db()
    host = host or HOST
    port = int(port or PORT)
    if APP_ENV == "production" and SESSION_SECRET in {"", "CHANGE_ME_IN_PRODUCTION"}:
        ERROR_LOGGER.warning("CRM_SESSION_SECRET is using placeholder value. Please set a strong secret in production.")
    ThreadingHTTPServer.allow_reuse_address = True
    server = ThreadingHTTPServer((host, port), CRMHandler)
    APP_LOGGER.info("CRM running on %s:%s (env=%s, db=%s, uploads=%s, base_url=%s)", host, port, APP_ENV, DB_PATH, UPLOADS_DIR, BASE_URL)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        APP_LOGGER.info("Server interrupted by keyboard, shutting down.")
    except Exception:
        ERROR_LOGGER.exception("Server crashed unexpectedly")
        raise
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
