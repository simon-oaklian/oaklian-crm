"""
estimates_v2_module.py
========================================================================
Oaklian CRM 报价系统重构 v2 - 后端 API 模块

这个模块**独立于** app.py,不修改 app.py 的核心逻辑。
通过在 app.py 的 do_GET/do_POST/do_PUT/do_DELETE 里各加一行调用,
就能拦截 v2 相关的请求。

所有 API 路径前缀: /api/v2/...

与 app.py 的衔接:
  - 复用 app.py 里 BaseHandler 的方法: _require_auth, _require_module,
    _json_response, _read_body_json, _parse_query
  - 复用 get_conn / now_ts(全局函数)

设计原则:
  - 一个 handle_get/post/put/delete 函数作为路由分发器,返回 True 表示已处理
  - 失败时也返回 True(已发回错误响应),让 app.py 不再继续处理
  - 返回 False 表示这条路径不归 v2 管,让 app.py 继续走原有流程

API 列表:
  分区主表 (sections-master)
    GET    /api/v2/sections-master                列出所有分区
    POST   /api/v2/sections-master                新建分区(owner)
    PUT    /api/v2/sections-master/{id}           修改分区(owner)
    DELETE /api/v2/sections-master/{id}           软删除分区(owner)

  单价库 - 翻新 (price-library)
    GET    /api/v2/price-library                  列表(支持 ?section=&search=)
    GET    /api/v2/price-library/{id}             单条
    POST   /api/v2/price-library                  新建(owner)
    PUT    /api/v2/price-library/{id}             修改(owner)
    DELETE /api/v2/price-library/{id}             软删除(owner)

  单价库 - 重建 (price-library-rebuild)
    GET    /api/v2/price-library-rebuild          列表
    GET    /api/v2/price-library-rebuild/{id}     单条
    POST   /api/v2/price-library-rebuild          新建(owner)
    PUT    /api/v2/price-library-rebuild/{id}     修改(owner)
    DELETE /api/v2/price-library-rebuild/{id}     软删除(owner)

  报价模板 (estimate-templates-v2)
    GET    /api/v2/estimate-templates             列表
    GET    /api/v2/estimate-templates/{id}        单条(含分区+明细)
    POST   /api/v2/estimate-templates             新建(owner)
    PUT    /api/v2/estimate-templates/{id}        修改(owner)
    DELETE /api/v2/estimate-templates/{id}        软删除(owner)

  报价编辑 (estimates-v2)
    GET    /api/v2/estimates/{id}/full            完整报价(含分区/明细/付款节点)
    POST   /api/v2/estimates/{id}/sections        新建分区
    PUT    /api/v2/estimates/{id}/sections/{sid}  修改分区
    DELETE /api/v2/estimates/{id}/sections/{sid}  删除分区
    POST   /api/v2/estimates/{id}/lines           新建明细行
    PUT    /api/v2/estimates/{id}/lines/{lid}     修改明细行
    DELETE /api/v2/estimates/{id}/lines/{lid}     删除明细行
    POST   /api/v2/estimates/{id}/recalc          重算总价
    GET    /api/v2/estimates/{id}/payment-milestones        列表
    PUT    /api/v2/estimates/{id}/payment-milestones        批量替换
    POST   /api/v2/estimates/{id}/load-template/{tid}       从模板加载
    POST   /api/v2/estimates/{id}/addons          新建附加项(rebuild)
    PUT    /api/v2/estimates/{id}/addons/{aid}    修改附加项
    DELETE /api/v2/estimates/{id}/addons/{aid}    删除附加项

  全局设置 (settings)
    GET    /api/v2/settings/estimate              读全部 estimate 类设置
    PUT    /api/v2/settings/estimate              批量保存(owner)

  阶段模板项(给付款节点关联用)
    GET    /api/v2/stage-template-items           列出所有可用施工阶段

  CSV 导入(单价库)
    POST   /api/v2/price-library/import-csv       (owner, multipart/form-data)
"""

import json
import re
import datetime

# v2 PDF 子模块
import estimates_v2_pdf as ev2pdf


# ====================================================================
# 工具函数
# ====================================================================

def _now():
    """当前时间戳(ISO 格式),与 app.py 风格一致"""
    return datetime.datetime.now().isoformat(timespec="seconds")


def _row_to_dict(row, columns):
    """sqlite3 Row 转 dict"""
    if row is None:
        return None
    return {col: row[col] for col in columns}


def _rows_to_dicts(rows):
    """多行转 list of dict"""
    return [dict(r) for r in rows]


def _parse_int(s, default=None):
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def _parse_float(s, default=None):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def _safe_str(s, max_len=None):
    if s is None:
        return ""
    s = str(s).strip()
    if max_len and len(s) > max_len:
        s = s[:max_len]
    return s


# ====================================================================
# i18n 工具函数(Phase 2a 新增)
# ====================================================================

def _pick_lang(zh, en, es, lang):
    """根据请求语言取对应字段值,空了回退到任何已填的语言。
    顺序:请求语言 → 中文 → 英文 → 西语 → 空字符串"""
    candidates = {
        "zh": [zh, en, es],
        "en": [en, zh, es],
        "es": [es, zh, en],
    }
    chain = candidates.get(lang, [zh, en, es])
    for v in chain:
        if v:  # 非空非 None
            return v
    return ""


def _detect_lang(handler):
    """从请求中检测当前 UI 语言。
    优先级:?lang query 参数 > Cookie 'lang' > 'zh'(默认中文,因为老板是主用户)
    """
    try:
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(handler.path).query)
        if "lang" in qs:
            v = qs["lang"][0].lower()
            if v in ("zh", "en", "es"):
                return v
    except Exception:
        pass
    try:
        cookies_hdr = handler.headers.get("Cookie", "") or ""
        for kv in cookies_hdr.split(";"):
            kv = kv.strip()
            if kv.startswith("lang="):
                v = kv.split("=", 1)[1].lower()
                if v in ("zh", "en", "es"):
                    return v
    except Exception:
        pass
    return "zh"


def _attach_picked(rows, base_field_pairs, lang):
    """给一批 dict 行追加按 lang 选好的"主字段"。
    base_field_pairs: list of (output_field, zh_col, en_col, es_col)
    例如 [("name", "name_zh", "name_en", "name_es"), ...]
    rows 会就地修改并返回(同一个对象)。
    """
    for r in rows:
        for output_field, zh_col, en_col, es_col in base_field_pairs:
            zh = r.get(zh_col)
            en = r.get(en_col)
            es = r.get(es_col)
            r[output_field] = _pick_lang(zh, en, es, lang)
    return rows


def _get_owner_only(handler, user):
    """只允许 owner 访问。失败已发响应,返回 False。"""
    if (user.get("role") or "").strip() != "owner":
        handler._json_response({"error": "Forbidden: owner only"}, 403)
        return False
    return True


def _read_body_json(handler):
    """读取请求 body 并解析 JSON,失败返回 None 并发 400"""
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        handler._json_response({"error": "Empty body"}, 400)
        return None
    try:
        raw = handler.rfile.read(length)
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        handler._json_response({"error": f"Invalid JSON: {e}"}, 400)
        return None


def _parse_query_string(query_string):
    """简单的查询字符串解析"""
    out = {}
    if not query_string:
        return out
    for part in query_string.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            try:
                from urllib.parse import unquote
                out[unquote(k)] = unquote(v)
            except Exception:
                out[k] = v
    return out


# ====================================================================
# 总入口:路由分发
# ====================================================================

def handle_get(handler, get_conn):
    """处理 GET 请求。返回 True 已处理,False 不归我管"""
    full_path = handler.path
    path = full_path.split("?")[0]
    qs = full_path.split("?", 1)[1] if "?" in full_path else ""

    # === PDF 路由(同时支持新 v2 URL 和旧 URL,拦截旧 URL 让我们替代旧的 _estimate_pdf_html) ===
    m_pdf = (re.match(r"^/api/v2/estimates/(\d+)/pdf$", path)
             or re.match(r"^/api/estimates/(\d+)/pdf$", path))
    if m_pdf:
        return _handle_pdf_export(handler, get_conn, int(m_pdf.group(1)), qs)

    if not path.startswith("/api/v2/"):
        return False

    user = handler._require_auth()
    if not user:
        return True
    if not handler._require_module(user, "estimates"):
        return True

    query = _parse_query_string(qs)

    try:
        # 分区主表
        if path == "/api/v2/sections-master":
            return _handle_sections_list(handler, get_conn)
        # 单价库 - 翻新
        if path == "/api/v2/price-library":
            return _handle_price_library_list(handler, get_conn, query)
        m = re.match(r"^/api/v2/price-library/(\d+)$", path)
        if m:
            return _handle_price_library_get(handler, get_conn, int(m.group(1)))
        # 单价库 - 重建
        if path == "/api/v2/price-library-rebuild":
            return _handle_price_library_rebuild_list(handler, get_conn, query)
        m = re.match(r"^/api/v2/price-library-rebuild/(\d+)$", path)
        if m:
            return _handle_price_library_rebuild_get(handler, get_conn, int(m.group(1)))
        # 报价模板
        if path == "/api/v2/estimate-templates":
            return _handle_templates_list(handler, get_conn, query)
        m = re.match(r"^/api/v2/estimate-templates/(\d+)$", path)
        if m:
            return _handle_template_get(handler, get_conn, int(m.group(1)))
        # 报价完整数据
        m = re.match(r"^/api/v2/estimates/(\d+)/full$", path)
        if m:
            return _handle_estimate_full(handler, get_conn, int(m.group(1)))
        # 付款节点列表
        m = re.match(r"^/api/v2/estimates/(\d+)/payment-milestones$", path)
        if m:
            return _handle_payment_milestones_list(handler, get_conn, int(m.group(1)))
        # 全局设置
        if path == "/api/v2/settings/estimate":
            return _handle_settings_get(handler, get_conn)
        # 施工阶段项
        if path == "/api/v2/stage-template-items":
            return _handle_stage_items_list(handler, get_conn, query)

    except Exception as e:
        handler._json_response({"error": f"Server error: {e}"}, 500)
        return True

    handler._json_response({"error": f"Not found: {path}"}, 404)
    return True


def handle_post(handler, get_conn):
    full_path = handler.path
    path = full_path.split("?")[0]

    if not path.startswith("/api/v2/"):
        return False

    user = handler._require_auth()
    if not user:
        return True
    if not handler._require_module(user, "estimates"):
        return True

    try:
        # 分区主表 - 新建
        if path == "/api/v2/sections-master":
            if not _get_owner_only(handler, user):
                return True
            return _handle_section_create(handler, get_conn, user)
        # 单价库翻新 - 新建
        if path == "/api/v2/price-library":
            if not _get_owner_only(handler, user):
                return True
            return _handle_price_library_create(handler, get_conn, user)
        # 单价库重建 - 新建
        if path == "/api/v2/price-library-rebuild":
            if not _get_owner_only(handler, user):
                return True
            return _handle_price_library_rebuild_create(handler, get_conn, user)
        # 模板 - 新建
        if path == "/api/v2/estimate-templates":
            if not _get_owner_only(handler, user):
                return True
            return _handle_template_create(handler, get_conn, user)
        # 报价分区 - 新建
        m = re.match(r"^/api/v2/estimates/(\d+)/sections$", path)
        if m:
            return _handle_section_create_in_estimate(handler, get_conn, int(m.group(1)))
        # 报价明细行 - 新建
        m = re.match(r"^/api/v2/estimates/(\d+)/lines$", path)
        if m:
            return _handle_line_create(handler, get_conn, user, int(m.group(1)))
        # 重算
        m = re.match(r"^/api/v2/estimates/(\d+)/recalc$", path)
        if m:
            return _handle_recalc(handler, get_conn, int(m.group(1)))
        # 从模板加载
        m = re.match(r"^/api/v2/estimates/(\d+)/load-template/(\d+)$", path)
        if m:
            return _handle_load_template(handler, get_conn, int(m.group(1)), int(m.group(2)))
        # 附加项 - 新建
        m = re.match(r"^/api/v2/estimates/(\d+)/addons$", path)
        if m:
            return _handle_addon_create(handler, get_conn, user, int(m.group(1)))
    except Exception as e:
        handler._json_response({"error": f"Server error: {e}"}, 500)
        return True

    handler._json_response({"error": f"Not found: {path}"}, 404)
    return True


def handle_put(handler, get_conn):
    full_path = handler.path
    path = full_path.split("?")[0]

    if not path.startswith("/api/v2/"):
        return False

    user = handler._require_auth()
    if not user:
        return True
    if not handler._require_module(user, "estimates"):
        return True

    try:
        # 分区主表
        m = re.match(r"^/api/v2/sections-master/(\d+)$", path)
        if m:
            if not _get_owner_only(handler, user):
                return True
            return _handle_section_update(handler, get_conn, int(m.group(1)))
        # 单价库翻新
        m = re.match(r"^/api/v2/price-library/(\d+)$", path)
        if m:
            if not _get_owner_only(handler, user):
                return True
            return _handle_price_library_update(handler, get_conn, user, int(m.group(1)))
        # 单价库重建
        m = re.match(r"^/api/v2/price-library-rebuild/(\d+)$", path)
        if m:
            if not _get_owner_only(handler, user):
                return True
            return _handle_price_library_rebuild_update(handler, get_conn, user, int(m.group(1)))
        # 模板
        m = re.match(r"^/api/v2/estimate-templates/(\d+)$", path)
        if m:
            if not _get_owner_only(handler, user):
                return True
            return _handle_template_update(handler, get_conn, user, int(m.group(1)))
        # 分区
        m = re.match(r"^/api/v2/estimates/(\d+)/sections/(\d+)$", path)
        if m:
            return _handle_section_update_in_estimate(handler, get_conn, int(m.group(1)), int(m.group(2)))
        # 明细行
        m = re.match(r"^/api/v2/estimates/(\d+)/lines/(\d+)$", path)
        if m:
            return _handle_line_update(handler, get_conn, user, int(m.group(1)), int(m.group(2)))
        # 付款节点 - 批量替换
        m = re.match(r"^/api/v2/estimates/(\d+)/payment-milestones$", path)
        if m:
            return _handle_payment_milestones_replace(handler, get_conn, int(m.group(1)))
        # 附加项
        m = re.match(r"^/api/v2/estimates/(\d+)/addons/(\d+)$", path)
        if m:
            return _handle_addon_update(handler, get_conn, user, int(m.group(1)), int(m.group(2)))
        # 全局设置
        if path == "/api/v2/settings/estimate":
            if not _get_owner_only(handler, user):
                return True
            return _handle_settings_save(handler, get_conn, user)
        # PDF 显示选项
        m = re.match(r"^/api/v2/estimates/(\d+)/pdf-options$", path)
        if m:
            return _handle_pdf_options_save(handler, get_conn, int(m.group(1)))
    except Exception as e:
        handler._json_response({"error": f"Server error: {e}"}, 500)
        return True

    handler._json_response({"error": f"Not found: {path}"}, 404)
    return True


def handle_delete(handler, get_conn):
    full_path = handler.path
    path = full_path.split("?")[0]

    if not path.startswith("/api/v2/"):
        return False

    user = handler._require_auth()
    if not user:
        return True
    if not handler._require_module(user, "estimates"):
        return True

    try:
        m = re.match(r"^/api/v2/sections-master/(\d+)$", path)
        if m:
            if not _get_owner_only(handler, user):
                return True
            return _handle_section_soft_delete(handler, get_conn, int(m.group(1)))
        m = re.match(r"^/api/v2/price-library/(\d+)$", path)
        if m:
            if not _get_owner_only(handler, user):
                return True
            return _handle_price_library_soft_delete(handler, get_conn, int(m.group(1)))
        m = re.match(r"^/api/v2/price-library-rebuild/(\d+)$", path)
        if m:
            if not _get_owner_only(handler, user):
                return True
            return _handle_price_library_rebuild_soft_delete(handler, get_conn, int(m.group(1)))
        m = re.match(r"^/api/v2/estimate-templates/(\d+)$", path)
        if m:
            if not _get_owner_only(handler, user):
                return True
            return _handle_template_soft_delete(handler, get_conn, int(m.group(1)))
        m = re.match(r"^/api/v2/estimates/(\d+)/sections/(\d+)$", path)
        if m:
            return _handle_section_delete_in_estimate(handler, get_conn, int(m.group(1)), int(m.group(2)))
        m = re.match(r"^/api/v2/estimates/(\d+)/lines/(\d+)$", path)
        if m:
            return _handle_line_delete(handler, get_conn, int(m.group(1)), int(m.group(2)))
        m = re.match(r"^/api/v2/estimates/(\d+)/addons/(\d+)$", path)
        if m:
            return _handle_addon_delete(handler, get_conn, int(m.group(1)), int(m.group(2)))
    except Exception as e:
        handler._json_response({"error": f"Server error: {e}"}, 500)
        return True

    handler._json_response({"error": f"Not found: {path}"}, 404)
    return True


# ====================================================================
# 分区主表(estimate_sections_master)
# ====================================================================

def _handle_sections_list(handler, get_conn):
    lang = _detect_lang(handler)
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, code, name_en, name_zh, name_es, sort_order, is_active, notes,
               created_at, updated_at
        FROM estimate_sections_master
        WHERE is_active=1
        ORDER BY sort_order, id
        """
    )
    rows = _rows_to_dicts(cur.fetchall())
    conn.close()
    _attach_picked(rows, [("name", "name_zh", "name_en", "name_es")], lang)
    handler._json_response({"items": rows})
    return True


def _handle_section_create(handler, get_conn, user):
    body = _read_body_json(handler)
    if body is None:
        return True
    code = _safe_str(body.get("code"), 32).upper()
    name_en = _safe_str(body.get("name_en"), 100)
    name_zh = _safe_str(body.get("name_zh"), 100)
    sort_order = _parse_int(body.get("sort_order"), 99)
    notes = _safe_str(body.get("notes"), 500)
    if not code or not name_zh:
        handler._json_response({"error": "code 和 name_zh 必填"}, 400)
        return True
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO estimate_sections_master
            (code, name_en, name_zh, sort_order, is_active, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (code, name_en, name_zh, sort_order, notes, _now(), _now()),
        )
        new_id = cur.lastrowid
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        handler._json_response({"error": f"创建失败: {e}"}, 400)
        return True
    conn.close()
    handler._json_response({"id": new_id}, 201)
    return True


def _handle_section_update(handler, get_conn, sid):
    body = _read_body_json(handler)
    if body is None:
        return True
    fields, params = [], []
    if "code" in body:
        fields.append("code=?"); params.append(_safe_str(body["code"], 32).upper())
    if "name_en" in body:
        fields.append("name_en=?"); params.append(_safe_str(body["name_en"], 100))
    if "name_zh" in body:
        fields.append("name_zh=?"); params.append(_safe_str(body["name_zh"], 100))
    if "sort_order" in body:
        fields.append("sort_order=?"); params.append(_parse_int(body["sort_order"], 99))
    if "notes" in body:
        fields.append("notes=?"); params.append(_safe_str(body["notes"], 500))
    if not fields:
        handler._json_response({"error": "无字段需要更新"}, 400)
        return True
    fields.append("updated_at=?"); params.append(_now())
    params.append(sid)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE estimate_sections_master SET {', '.join(fields)} WHERE id=?", params)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


def _handle_section_soft_delete(handler, get_conn, sid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE estimate_sections_master SET is_active=0, updated_at=? WHERE id=?",
        (_now(), sid),
    )
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


# ====================================================================
# 单价库 - 翻新(price_library)
# ====================================================================

def _handle_price_library_list(handler, get_conn, query):
    lang = _detect_lang(handler)
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    where = ["pl.is_active=1"]
    params = []
    section = query.get("section")
    if section:
        section_id = _parse_int(section)
        if section_id:
            where.append("pl.section_master_id=?"); params.append(section_id)
    search = query.get("search", "").strip()
    if search:
        where.append("(pl.item_name LIKE ? OR pl.item_name_en LIKE ? OR pl.item_name_es LIKE ? OR pl.description LIKE ? OR pl.sku LIKE ? OR pl.tag LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like, like, like, like])
    sql = f"""
        SELECT pl.id, pl.sku, pl.section_master_id,
               pl.item_name, pl.item_name_zh, pl.item_name_en, pl.item_name_es,
               pl.description, pl.description_zh, pl.description_en, pl.description_es,
               pl.unit, pl.unit_zh, pl.unit_en, pl.unit_es, pl.default_qty, pl.material_unit_price, pl.labor_unit_price,
               pl.customer_visible_note, pl.internal_note, pl.photo_url, pl.tag,
               pl.created_at, pl.updated_at, pl.updated_by,
               sm.code AS section_code,
               sm.name_zh AS section_name_zh, sm.name_en AS section_name_en, sm.name_es AS section_name_es
        FROM price_library pl
        JOIN estimate_sections_master sm ON sm.id=pl.section_master_id
        WHERE {' AND '.join(where)}
        ORDER BY sm.sort_order, pl.id
    """
    cur.execute(sql, params)
    rows = _rows_to_dicts(cur.fetchall())
    conn.close()
    # 给每行追加按 lang 选好的"主显示字段"
    _attach_picked(rows, [
        ("item_name_picked", "item_name_zh", "item_name_en", "item_name_es"),
        ("description_picked", "description_zh", "description_en", "description_es"),
        ("section_name", "section_name_zh", "section_name_en", "section_name_es"),
        ("unit_picked", "unit_zh", "unit_en", "unit_es"),
    ], lang)
    # 兼容性:如果 _zh 字段为空(老库未填),picked 也回退到旧的 item_name / description 列
    for r in rows:
        if not r.get("item_name_picked"):
            r["item_name_picked"] = r.get("item_name") or ""
        if not r.get("description_picked"):
            r["description_picked"] = r.get("description") or ""
        # 把 picked 字段以"主名"暴露给前端(覆盖老 item_name / description,前端代码改一行就能用三语)
        r["item_name"] = r["item_name_picked"]
        r["description"] = r["description_picked"]
        # P0-C-2: unit also picked per lang; fallback to original unit if empty
        if not r.get("unit_picked"):
            r["unit_picked"] = r.get("unit") or ""
        r["unit"] = r["unit_picked"]
    handler._json_response({"items": rows, "total": len(rows)})
    return True


def _handle_price_library_get(handler, get_conn, item_id):
    lang = _detect_lang(handler)
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM price_library WHERE id=?", (item_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        handler._json_response({"error": "Not found"}, 404)
        return True
    d = dict(row)
    # 如果有三语字段,按 lang 选好暴露;_zh 等字段保留供管理员 modal 编辑
    picked = _pick_lang(d.get("item_name_zh"), d.get("item_name_en"), d.get("item_name_es"), lang)
    if picked:
        d["item_name"] = picked
    picked_d = _pick_lang(d.get("description_zh"), d.get("description_en"), d.get("description_es"), lang)
    if picked_d:
        d["description"] = picked_d
    handler._json_response(d)
    return True


def _handle_price_library_create(handler, get_conn, user):
    body = _read_body_json(handler)
    if body is None:
        return True
    section_id = _parse_int(body.get("section_master_id"))
    item_name = _safe_str(body.get("item_name"), 200)
    if not section_id or not item_name:
        handler._json_response({"error": "section_master_id 和 item_name 必填"}, 400)
        return True
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO price_library
            (sku, section_master_id, item_name, description, unit, default_qty,
             material_unit_price, labor_unit_price, customer_visible_note,
             internal_note, photo_url, tag, is_active, created_at, updated_at, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                _safe_str(body.get("sku"), 64),
                section_id,
                item_name,
                _safe_str(body.get("description"), 500),
                _safe_str(body.get("unit"), 32),
                _parse_float(body.get("default_qty"), 1),
                _parse_float(body.get("material_unit_price"), 0),
                _parse_float(body.get("labor_unit_price"), 0),
                _safe_str(body.get("customer_visible_note"), 500),
                _safe_str(body.get("internal_note"), 500),
                _safe_str(body.get("photo_url"), 500),
                _safe_str(body.get("tag"), 64),
                _now(), _now(), user.get("id"),
            ),
        )
        new_id = cur.lastrowid
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        handler._json_response({"error": f"创建失败: {e}"}, 400)
        return True
    conn.close()
    handler._json_response({"id": new_id}, 201)
    return True


_PL_FIELDS = ["sku", "section_master_id", "item_name", "description", "unit",
              "default_qty", "material_unit_price", "labor_unit_price",
              "customer_visible_note", "internal_note", "photo_url", "tag"]


def _handle_price_library_update(handler, get_conn, user, item_id):
    body = _read_body_json(handler)
    if body is None:
        return True
    fields, params = [], []
    for f in _PL_FIELDS:
        if f in body:
            fields.append(f"{f}=?")
            v = body[f]
            if f in ("section_master_id",):
                v = _parse_int(v)
            elif f in ("default_qty", "material_unit_price", "labor_unit_price"):
                v = _parse_float(v, 0)
            else:
                max_len = 500 if f in ("description", "customer_visible_note", "internal_note", "photo_url") else 200
                v = _safe_str(v, max_len)
            params.append(v)
    if not fields:
        handler._json_response({"error": "无字段需要更新"}, 400)
        return True
    fields.append("updated_at=?"); params.append(_now())
    fields.append("updated_by=?"); params.append(user.get("id"))
    params.append(item_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE price_library SET {', '.join(fields)} WHERE id=?", params)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


def _handle_price_library_soft_delete(handler, get_conn, item_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE price_library SET is_active=0, updated_at=? WHERE id=?",
        (_now(), item_id),
    )
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


# ====================================================================
# 单价库 - 重建(price_library_rebuild)
# ====================================================================

def _handle_price_library_rebuild_list(handler, get_conn, query):
    lang = _detect_lang(handler)
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    where = ["is_active=1"]
    params = []
    item_type = query.get("type")
    if item_type in ("base", "addon"):
        where.append("item_type=?"); params.append(item_type)
    sql = f"""
        SELECT * FROM price_library_rebuild
        WHERE {' AND '.join(where)}
        ORDER BY item_type, sort_order, id
    """
    cur.execute(sql, params)
    rows = _rows_to_dicts(cur.fetchall())
    conn.close()
    # i18n: name_zh/en/es → name; description_zh/en/es → description
    for r in rows:
        n = _pick_lang(r.get("name_zh"), r.get("name_en"), r.get("name_es"), lang)
        if n:
            r["name"] = n
        d = _pick_lang(r.get("description_zh"), r.get("description_en"), r.get("description_es"), lang)
        if d:
            r["description"] = d
        # P0-C-2: unit picked per lang
        u = _pick_lang(r.get("unit_zh"), r.get("unit_en"), r.get("unit_es"), lang)
        if u:
            r["unit"] = u
    handler._json_response({"items": rows, "total": len(rows)})
    return True


def _handle_price_library_rebuild_get(handler, get_conn, item_id):
    lang = _detect_lang(handler)
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM price_library_rebuild WHERE id=?", (item_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        handler._json_response({"error": "Not found"}, 404)
        return True
    d = dict(row)
    n = _pick_lang(d.get("name_zh"), d.get("name_en"), d.get("name_es"), lang)
    if n:
        d["name"] = n
    desc = _pick_lang(d.get("description_zh"), d.get("description_en"), d.get("description_es"), lang)
    if desc:
        d["description"] = desc
    handler._json_response(d)
    return True


def _handle_price_library_rebuild_create(handler, get_conn, user):
    body = _read_body_json(handler)
    if body is None:
        return True
    name = _safe_str(body.get("name"), 200)
    item_type = body.get("item_type", "base")
    if item_type not in ("base", "addon"):
        item_type = "base"
    if not name:
        handler._json_response({"error": "name 必填"}, 400)
        return True
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO price_library_rebuild
        (sku, item_type, name, description, unit, default_unit_price, default_qty,
         customer_visible_note, internal_note, photo_url, sort_order, is_active,
         created_at, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        """,
        (
            _safe_str(body.get("sku"), 64),
            item_type,
            name,
            _safe_str(body.get("description"), 500),
            _safe_str(body.get("unit"), 32),
            _parse_float(body.get("default_unit_price"), 0),
            _parse_float(body.get("default_qty"), 1),
            _safe_str(body.get("customer_visible_note"), 500),
            _safe_str(body.get("internal_note"), 500),
            _safe_str(body.get("photo_url"), 500),
            _parse_int(body.get("sort_order"), 99),
            _now(), _now(), user.get("id"),
        ),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    handler._json_response({"id": new_id}, 201)
    return True


_PLR_FIELDS = ["sku", "item_type", "name", "description", "unit",
               "default_unit_price", "default_qty", "customer_visible_note",
               "internal_note", "photo_url", "sort_order"]


def _handle_price_library_rebuild_update(handler, get_conn, user, item_id):
    body = _read_body_json(handler)
    if body is None:
        return True
    fields, params = [], []
    for f in _PLR_FIELDS:
        if f in body:
            fields.append(f"{f}=?")
            v = body[f]
            if f == "sort_order":
                v = _parse_int(v, 99)
            elif f in ("default_unit_price", "default_qty"):
                v = _parse_float(v, 0)
            else:
                max_len = 500 if f in ("description", "customer_visible_note", "internal_note", "photo_url") else 200
                v = _safe_str(v, max_len)
            params.append(v)
    if not fields:
        handler._json_response({"error": "无字段需要更新"}, 400)
        return True
    fields.append("updated_at=?"); params.append(_now())
    fields.append("updated_by=?"); params.append(user.get("id"))
    params.append(item_id)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE price_library_rebuild SET {', '.join(fields)} WHERE id=?", params)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


def _handle_price_library_rebuild_soft_delete(handler, get_conn, item_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE price_library_rebuild SET is_active=0, updated_at=? WHERE id=?",
        (_now(), item_id),
    )
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


# ====================================================================
# 报价模板(estimate_template_v2 + sections + lines)
# ====================================================================

def _handle_templates_list(handler, get_conn, query):
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    where = ["is_active=1"]
    params = []
    template_type = query.get("template_type")
    if template_type in ("full", "section"):
        where.append("template_type=?"); params.append(template_type)
    estimate_type = query.get("estimate_type")
    if estimate_type in ("renovation", "rebuild"):
        where.append("estimate_type=?"); params.append(estimate_type)
    sql = f"""
        SELECT t.*,
            (SELECT COUNT(*) FROM estimate_template_sections WHERE template_id=t.id) AS section_count,
            (SELECT COUNT(*) FROM estimate_template_lines etl
                JOIN estimate_template_sections ets ON ets.id=etl.template_section_id
                WHERE ets.template_id=t.id) AS line_count
        FROM estimate_template_v2 t
        WHERE {' AND '.join(where)}
        ORDER BY t.id
    """
    cur.execute(sql, params)
    rows = _rows_to_dicts(cur.fetchall())
    conn.close()
    # P0B_PATCH_APPLIED: trilingual name/description for templates list
    lang = _detect_lang(handler)
    _attach_picked(rows, [
        ("name_picked", "name_zh", "name_en", "name_es"),
        ("description_picked", "description_zh", "description_en", "description_es"),
    ], lang)
    for r in rows:
        if r.get("name_picked"):
            r["name"] = r["name_picked"]
        if r.get("description_picked") is not None:
            r["description"] = r["description_picked"]
    handler._json_response({"items": rows, "total": len(rows)})
    return True


def _handle_template_get(handler, get_conn, tid):
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM estimate_template_v2 WHERE id=?", (tid,))
    tpl = cur.fetchone()
    if not tpl:
        conn.close()
        handler._json_response({"error": "Not found"}, 404)
        return True
    tpl = dict(tpl)
    cur.execute(
        """
        SELECT ets.id, ets.section_master_id, ets.sort_order,
               sm.code AS section_code, sm.name_zh AS section_name_zh, sm.name_en AS section_name_en, sm.name_es AS section_name_es
        FROM estimate_template_sections ets
        JOIN estimate_sections_master sm ON sm.id=ets.section_master_id
        WHERE ets.template_id=?
        ORDER BY ets.sort_order, ets.id
        """, (tid,),
    )
    sections = _rows_to_dicts(cur.fetchall())
    for sec in sections:
        cur.execute(
            """
            SELECT etl.*, pl.material_unit_price AS lib_material, pl.labor_unit_price AS lib_labor,
                   pl.sku AS lib_sku
            FROM estimate_template_lines etl
            LEFT JOIN price_library pl ON pl.id=etl.price_library_id
            WHERE etl.template_section_id=?
            ORDER BY etl.sort_order, etl.id
            """, (sec["id"],),
        )
        sec["lines"] = _rows_to_dicts(cur.fetchall())
    tpl["sections"] = sections
    conn.close()
    # P0B_PATCH_APPLIED: trilingual top-level name/description for template detail
    lang = _detect_lang(handler)
    _attach_picked([tpl], [
        ("name_picked", "name_zh", "name_en", "name_es"),
        ("description_picked", "description_zh", "description_en", "description_es"),
    ], lang)
    if tpl.get("name_picked"):
        tpl["name"] = tpl["name_picked"]
    if tpl.get("description_picked") is not None:
        tpl["description"] = tpl["description_picked"]
    # SECTIONS_ES_FIX_APPLIED: trilingual section name picking for template detail
    _attach_picked(sections, [
        ("section_name_picked", "section_name_zh", "section_name_en", "section_name_es"),
    ], lang)
    for sec in sections:
        if sec.get("section_name_picked"):
            sec["name"] = sec["section_name_picked"]
    handler._json_response(tpl)
    return True


def _handle_template_create(handler, get_conn, user):
    body = _read_body_json(handler)
    if body is None:
        return True
    name = _safe_str(body.get("name"), 200)
    if not name:
        handler._json_response({"error": "name 必填"}, 400)
        return True
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO estimate_template_v2
        (name, template_type, estimate_type, description, default_markup_rate,
         is_active, created_at, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
        """,
        (
            name,
            body.get("template_type") if body.get("template_type") in ("full", "section") else "full",
            body.get("estimate_type") if body.get("estimate_type") in ("renovation", "rebuild") else "renovation",
            _safe_str(body.get("description"), 500),
            _parse_float(body.get("default_markup_rate"), 0),
            _now(), _now(), user.get("id"),
        ),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    handler._json_response({"id": new_id}, 201)
    return True


def _handle_template_update(handler, get_conn, user, tid):
    body = _read_body_json(handler)
    if body is None:
        return True
    fields, params = [], []
    if "name" in body:
        fields.append("name=?"); params.append(_safe_str(body["name"], 200))
    if "description" in body:
        fields.append("description=?"); params.append(_safe_str(body["description"], 500))
    if "default_markup_rate" in body:
        fields.append("default_markup_rate=?"); params.append(_parse_float(body["default_markup_rate"], 0))
    if "template_type" in body and body["template_type"] in ("full", "section"):
        fields.append("template_type=?"); params.append(body["template_type"])
    if "estimate_type" in body and body["estimate_type"] in ("renovation", "rebuild"):
        fields.append("estimate_type=?"); params.append(body["estimate_type"])
    # 同时支持替换分区和明细行
    sections = body.get("sections")
    if not fields and sections is None:
        handler._json_response({"error": "无字段需要更新"}, 400)
        return True
    conn = get_conn()
    cur = conn.cursor()
    if fields:
        fields.append("updated_at=?"); params.append(_now())
        fields.append("updated_by=?"); params.append(user.get("id"))
        params.append(tid)
        cur.execute(f"UPDATE estimate_template_v2 SET {', '.join(fields)} WHERE id=?", params)
    if sections is not None and isinstance(sections, list):
        # 全替换:先删旧的(级联),再插新的
        cur.execute("SELECT id FROM estimate_template_sections WHERE template_id=?", (tid,))
        for r in cur.fetchall():
            cur.execute("DELETE FROM estimate_template_lines WHERE template_section_id=?", (r[0],))
        cur.execute("DELETE FROM estimate_template_sections WHERE template_id=?", (tid,))
        for idx, sec in enumerate(sections):
            cur.execute(
                """
                INSERT INTO estimate_template_sections (template_id, section_master_id, sort_order, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (tid, _parse_int(sec.get("section_master_id")), idx + 1, _now()),
            )
            new_sec_id = cur.lastrowid
            for lidx, ln in enumerate(sec.get("lines") or []):
                cur.execute(
                    """
                    INSERT INTO estimate_template_lines
                    (template_section_id, price_library_id, item_name, description, unit,
                     override_material_price, override_labor_price, sort_order, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        new_sec_id,
                        _parse_int(ln.get("price_library_id")) or None,
                        _safe_str(ln.get("item_name"), 200),
                        _safe_str(ln.get("description"), 500),
                        _safe_str(ln.get("unit"), 32),
                        _parse_float(ln.get("override_material_price")) if ln.get("override_material_price") not in (None, "") else None,
                        _parse_float(ln.get("override_labor_price")) if ln.get("override_labor_price") not in (None, "") else None,
                        lidx + 1, _now(),
                    ),
                )
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


def _handle_template_soft_delete(handler, get_conn, tid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE estimate_template_v2 SET is_active=0, updated_at=? WHERE id=?",
        (_now(), tid),
    )
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


# ====================================================================
# 报价完整数据 + 编辑 + 重算
# ====================================================================

def _ensure_estimate_exists(cur, eid):
    cur.execute("SELECT id FROM estimates WHERE id=?", (eid,))
    return cur.fetchone() is not None


def _next_estimate_version(value):
    m = re.search(r"(\d+)", str(value or "v1"))
    return f"v{int(m.group(1)) + 1}" if m else "v2"


def _reset_confirmed_estimate_for_edit(cur, eid):
    cur.execute("SELECT confirm_status, status, version FROM estimates WHERE id=?", (eid,))
    row = cur.fetchone()
    if not row:
        return False
    status = str((row[0] or row[1] or "draft")).strip().lower()
    if status not in {"confirmed", "approved", "accepted"}:
        return False
    cur.execute(
        """
        UPDATE estimates
        SET version=?, confirm_status='draft', status='Draft',
            confirmed_at=NULL, confirmed_by=NULL, confirm_note=NULL,
            sent_at=NULL, client_action_at=NULL, client_name=NULL, client_email=NULL,
            client_phone=NULL, client_ip=NULL, client_user_agent=NULL,
            client_signature_data=NULL, updated_at=?
        WHERE id=?
        """,
        (_next_estimate_version(row[2]), _now(), eid),
    )
    return True


def _handle_estimate_full(handler, get_conn, eid):
    lang = _detect_lang(handler)
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM estimates WHERE id=?", (eid,))
    est = cur.fetchone()
    if not est:
        conn.close()
        handler._json_response({"error": "Not found"}, 404)
        return True
    est = dict(est)
    # 客户信息
    if est.get("customer_id"):
        cur.execute("SELECT id, name, phone, primary_address FROM customers WHERE id=?", (est["customer_id"],))
        c = cur.fetchone()
        if c:
            est["customer"] = dict(c)
    # 分区+明细(同时取 master 的三语 + 实例自己的三语)
    cur.execute(
        """
        SELECT es.*,
               sm.code AS section_code,
               sm.name_zh AS section_master_name_zh,
               sm.name_en AS section_master_name_en,
               sm.name_es AS section_master_name_es
        FROM estimate_sections es
        LEFT JOIN estimate_sections_master sm ON sm.id=es.master_id
        WHERE es.estimate_id=?
        ORDER BY es.sort_order, es.id
        """, (eid,),
    )
    sections = _rows_to_dicts(cur.fetchall())
    for sec in sections:
        # 分区显示名:优先实例自身三语,再回退到 master 三语
        inst_name = _pick_lang(
            sec.get("name_zh"), sec.get("name_en"), sec.get("name_es"), lang
        )
        master_name = _pick_lang(
            sec.get("section_master_name_zh"),
            sec.get("section_master_name_en"),
            sec.get("section_master_name_es"),
            lang,
        )
        # 兼容老数据:section_master_name_zh 列原来叫 section_name_zh
        sec["section_name_zh"] = sec.get("section_master_name_zh")
        sec["section_name_en"] = sec.get("section_master_name_en")
        sec["section_name_es"] = sec.get("section_master_name_es")
        # picked 名(前端可统一读 sec.name)
        if inst_name:
            sec["name"] = inst_name
        elif master_name:
            sec["name"] = master_name
        # master 名(前端可统一读 sec.section_name)
        if master_name:
            sec["section_name"] = master_name
        # 取明细行
        cur.execute(
            "SELECT * FROM estimate_lines WHERE section_id=? ORDER BY sort_order, id",
            (sec["id"],),
        )
        lines = _rows_to_dicts(cur.fetchall())
        for ln in lines:
            n = _pick_lang(
                ln.get("item_name_zh"), ln.get("item_name_en"), ln.get("item_name_es"), lang
            )
            if n:
                ln["item_name"] = n
            d = _pick_lang(
                ln.get("description_zh"), ln.get("description_en"), ln.get("description_es"), lang
            )
            if d:
                ln["description"] = d
        sec["lines"] = lines
    est["sections"] = sections
    # 重建附加项
    cur.execute(
        "SELECT * FROM estimate_addons WHERE estimate_id=? ORDER BY sort_order, id",
        (eid,),
    )
    addons = _rows_to_dicts(cur.fetchall())
    for a in addons:
        n = _pick_lang(a.get("name_zh"), a.get("name_en"), a.get("name_es"), lang)
        if n:
            a["name"] = n
        d = _pick_lang(a.get("description_zh"), a.get("description_en"), a.get("description_es"), lang)
        if d:
            a["description"] = d
    est["addons"] = addons
    # 付款节点
    cur.execute(
        """
        SELECT epm.*, psti.step_name AS stage_step_name
        FROM estimate_payment_milestones epm
        LEFT JOIN project_stage_template_items psti ON psti.id=epm.trigger_stage_template_item_id
        WHERE epm.estimate_id=?
        ORDER BY epm.sort_order, epm.id
        """, (eid,),
    )
    est["payment_milestones"] = _rows_to_dicts(cur.fetchall())
    cur.execute(
        """
        SELECT id,contract_no,customer_id,total_amount,title,address,project_id,sign_status,signed_status
        FROM contracts
        WHERE estimate_id=?
        ORDER BY id ASC
        LIMIT 1
        """,
        (eid,),
    )
    linked = cur.fetchone()
    if not linked and est.get("contract_id"):
        cur.execute(
            """
            SELECT id,contract_no,customer_id,total_amount,title,address,project_id,sign_status,signed_status
            FROM contracts
            WHERE id=?
            """,
            (est.get("contract_id"),),
        )
        linked = cur.fetchone()
    linked = dict(linked) if linked else None
    if linked and est.get("customer_id") not in (None, "") and linked.get("customer_id") not in (None, ""):
        if int(est.get("customer_id")) != int(linked.get("customer_id")):
            linked = None
    est["linked_contract_id"] = linked.get("id") if linked else None
    est["linked_contract_no"] = linked.get("contract_no") if linked else None
    est["linked_contract_customer_id"] = linked.get("customer_id") if linked else None
    est["linked_contract_total_amount"] = linked.get("total_amount") if linked else None
    est["linked_contract_sign_status"] = (linked.get("sign_status") or linked.get("signed_status")) if linked else None
    est["linked_contract_mismatch"] = False
    conn.close()
    handler._json_response(est)
    return True


def _handle_section_create_in_estimate(handler, get_conn, eid):
    body = _read_body_json(handler)
    if body is None:
        return True
    conn = get_conn()
    cur = conn.cursor()
    if not _ensure_estimate_exists(cur, eid):
        conn.close()
        handler._json_response({"error": "Estimate not found"}, 404)
        return True
    master_id = _parse_int(body.get("master_id"))
    name = _safe_str(body.get("name"), 200)
    if master_id and not name:
        # 自动从 master 取中文名
        cur.execute("SELECT name_zh FROM estimate_sections_master WHERE id=?", (master_id,))
        r = cur.fetchone()
        if r:
            name = r[0]
    if not name:
        conn.close()
        handler._json_response({"error": "name 或 master_id 必填"}, 400)
        return True
    sort_order = _parse_int(body.get("sort_order"))
    if sort_order is None:
        cur.execute("SELECT COALESCE(MAX(sort_order),0)+1 FROM estimate_sections WHERE estimate_id=?", (eid,))
        sort_order = cur.fetchone()[0] or 1
    cur.execute(
        """
        INSERT INTO estimate_sections (estimate_id, master_id, name, sort_order, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (eid, master_id, name, sort_order, _safe_str(body.get("notes"), 500), _now(), _now()),
    )
    new_id = cur.lastrowid
    _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"id": new_id}, 201)
    return True


def _handle_section_update_in_estimate(handler, get_conn, eid, sid):
    body = _read_body_json(handler)
    if body is None:
        return True
    fields, params = [], []
    if "name" in body:
        fields.append("name=?"); params.append(_safe_str(body["name"], 200))
    if "sort_order" in body:
        fields.append("sort_order=?"); params.append(_parse_int(body["sort_order"], 99))
    if "notes" in body:
        fields.append("notes=?"); params.append(_safe_str(body["notes"], 500))
    if not fields:
        handler._json_response({"error": "无字段需要更新"}, 400)
        return True
    fields.append("updated_at=?"); params.append(_now())
    params.extend([sid, eid])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE estimate_sections SET {', '.join(fields)} WHERE id=? AND estimate_id=?", params)
    if cur.rowcount:
        _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


def _handle_section_delete_in_estimate(handler, get_conn, eid, sid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM estimate_sections WHERE id=? AND estimate_id=?", (sid, eid))
    if cur.rowcount:
        _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


def _handle_line_create(handler, get_conn, user, eid):
    body = _read_body_json(handler)
    if body is None:
        return True
    section_id = _parse_int(body.get("section_id"))
    item_name = _safe_str(body.get("item_name"), 200)
    if not section_id or not item_name:
        handler._json_response({"error": "section_id 和 item_name 必填"}, 400)
        return True
    conn = get_conn()
    cur = conn.cursor()
    if not _ensure_estimate_exists(cur, eid):
        conn.close()
        handler._json_response({"error": "Estimate not found"}, 404)
        return True
    qty = _parse_float(body.get("quantity"), 0)
    mat = _parse_float(body.get("material_unit_price"), 0)
    lab = _parse_float(body.get("labor_unit_price"), 0)
    line_subtotal = qty * (mat + lab)
    sort_order = _parse_int(body.get("sort_order"))
    if sort_order is None:
        cur.execute("SELECT COALESCE(MAX(sort_order),0)+1 FROM estimate_lines WHERE section_id=?", (section_id,))
        sort_order = cur.fetchone()[0] or 1
    cur.execute(
        """
        INSERT INTO estimate_lines
        (estimate_id, section_id, price_library_id, item_name, description,
         quantity, unit, material_unit_price, labor_unit_price,
         line_subtotal, sort_order, note, is_overridden, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            eid, section_id,
            _parse_int(body.get("price_library_id")) or None,
            item_name,
            _safe_str(body.get("description"), 500),
            qty,
            _safe_str(body.get("unit"), 32),
            mat, lab, line_subtotal, sort_order,
            _safe_str(body.get("note"), 500),
            1 if body.get("is_overridden") else 0,
            _now(), _now(),
        ),
    )
    new_id = cur.lastrowid
    # 如果有 override 留痕
    if body.get("is_overridden") and body.get("override_reason"):
        cur.execute(
            """
            INSERT INTO estimate_price_overrides
            (estimate_id, line_id, field_name, original_value, new_value, reason, changed_by, changed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (eid, new_id, "line_price",
             _parse_float(body.get("original_total")),
             mat + lab,
             _safe_str(body.get("override_reason"), 500),
             user.get("id"), _now()),
        )
    _recalc_section_subtotal(cur, section_id)
    _recalc_estimate_totals(cur, eid)
    _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"id": new_id, "line_subtotal": line_subtotal}, 201)
    return True


_LINE_FIELDS = ["item_name", "description", "quantity", "unit",
                "material_unit_price", "labor_unit_price",
                "sort_order", "note", "price_library_id"]


def _handle_line_update(handler, get_conn, user, eid, lid):
    body = _read_body_json(handler)
    if body is None:
        return True
    fields, params = [], []
    for f in _LINE_FIELDS:
        if f in body:
            fields.append(f"{f}=?")
            v = body[f]
            if f in ("quantity", "material_unit_price", "labor_unit_price"):
                v = _parse_float(v, 0)
            elif f in ("sort_order", "price_library_id"):
                v = _parse_int(v)
            else:
                max_len = 500 if f in ("description", "note") else 200
                v = _safe_str(v, max_len)
            params.append(v)
    if "is_overridden" in body:
        fields.append("is_overridden=?"); params.append(1 if body["is_overridden"] else 0)
    if not fields:
        handler._json_response({"error": "无字段需要更新"}, 400)
        return True
    fields.append("updated_at=?"); params.append(_now())
    params.extend([lid, eid])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE estimate_lines SET {', '.join(fields)} WHERE id=? AND estimate_id=?", params)
    # 重算 line_subtotal
    cur.execute("SELECT quantity, material_unit_price, labor_unit_price, section_id FROM estimate_lines WHERE id=?", (lid,))
    r = cur.fetchone()
    if r:
        qty, mat, lab, sec_id = r[0] or 0, r[1] or 0, r[2] or 0, r[3]
        cur.execute("UPDATE estimate_lines SET line_subtotal=? WHERE id=?", (qty * (mat + lab), lid))
        _recalc_section_subtotal(cur, sec_id)
    _recalc_estimate_totals(cur, eid)
    # override 留痕
    if body.get("is_overridden") and body.get("override_reason"):
        cur.execute(
            """
            INSERT INTO estimate_price_overrides
            (estimate_id, line_id, field_name, original_value, new_value, reason, changed_by, changed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (eid, lid, "line_price",
             _parse_float(body.get("original_total")),
             _parse_float(body.get("material_unit_price"), 0) + _parse_float(body.get("labor_unit_price"), 0),
             _safe_str(body.get("override_reason"), 500),
             user.get("id"), _now()),
        )
    _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


def _handle_line_delete(handler, get_conn, eid, lid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT section_id FROM estimate_lines WHERE id=? AND estimate_id=?", (lid, eid))
    r = cur.fetchone()
    cur.execute("DELETE FROM estimate_lines WHERE id=? AND estimate_id=?", (lid, eid))
    if r:
        _recalc_section_subtotal(cur, r[0])
    _recalc_estimate_totals(cur, eid)
    if r:
        _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


def _recalc_section_subtotal(cur, section_id):
    if not section_id:
        return
    cur.execute(
        "SELECT COALESCE(SUM(line_subtotal), 0) FROM estimate_lines WHERE section_id=?",
        (section_id,),
    )
    total = cur.fetchone()[0] or 0
    cur.execute(
        "UPDATE estimate_sections SET section_subtotal=?, updated_at=? WHERE id=?",
        (total, _now(), section_id),
    )


def _recalc_estimate_totals(cur, eid):
    """重新计算报价总价。返回 (subtotal, total_amount)"""
    # 1. 明细小计(翻新)
    cur.execute(
        "SELECT COALESCE(SUM(line_subtotal), 0) FROM estimate_lines WHERE estimate_id=?",
        (eid,),
    )
    line_total = cur.fetchone()[0] or 0
    # 2. 重建主体 + 附加项
    cur.execute(
        "SELECT estimate_type, rebuild_unit_price, rebuild_total_sqft, markup_rate, tax_enabled, tax_rate, rounding_mode, manual_adjustment FROM estimates WHERE id=?",
        (eid,),
    )
    r = cur.fetchone()
    if not r:
        return 0, 0
    est_type = r[0] or "renovation"
    rebuild_total = 0
    if est_type == "rebuild":
        rebuild_unit = r[1] or 0
        rebuild_sqft = r[2] or 0
        rebuild_total = rebuild_unit * rebuild_sqft
        # 附加项
        cur.execute(
            "SELECT COALESCE(SUM(addon_subtotal), 0) FROM estimate_addons WHERE estimate_id=? AND is_selected=1",
            (eid,),
        )
        rebuild_total += cur.fetchone()[0] or 0
    subtotal = line_total + rebuild_total
    markup_rate = r[3] or 0
    markup_amount = subtotal * markup_rate / 100.0
    after_markup = subtotal + markup_amount
    # 税
    tax_enabled = r[4] or 0
    tax_rate = r[5] or 0
    tax_amount = after_markup * tax_rate / 100.0 if tax_enabled else 0
    after_tax = after_markup + tax_amount
    manual_adjustment = r[7] or 0
    adjusted_total = after_tax + manual_adjustment
    # 凑整
    rounding = r[6] or "10"
    total_amount = _round_total(adjusted_total, rounding)
    cur.execute(
        "UPDATE estimates SET subtotal=?, total_amount=?, updated_at=? WHERE id=?",
        (subtotal, total_amount, _now(), eid),
    )
    return subtotal, total_amount


def _round_total(amount, mode):
    return round(amount, 2)


def _handle_recalc(handler, get_conn, eid):
    conn = get_conn()
    cur = conn.cursor()
    if not _ensure_estimate_exists(cur, eid):
        conn.close()
        handler._json_response({"error": "Not found"}, 404)
        return True
    subtotal, total = _recalc_estimate_totals(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"subtotal": subtotal, "total_amount": total})
    return True


# ====================================================================
# 付款节点
# ====================================================================

def _handle_payment_milestones_list(handler, get_conn, eid):
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT epm.*, psti.step_name AS stage_step_name
        FROM estimate_payment_milestones epm
        LEFT JOIN project_stage_template_items psti ON psti.id=epm.trigger_stage_template_item_id
        WHERE epm.estimate_id=?
        ORDER BY epm.sort_order, epm.id
        """, (eid,),
    )
    rows = _rows_to_dicts(cur.fetchall())
    conn.close()
    handler._json_response({"items": rows})
    return True


def _handle_payment_milestones_replace(handler, get_conn, eid):
    """前端发整个节点列表过来,后端整体替换"""
    body = _read_body_json(handler)
    if body is None:
        return True
    items = body.get("items", [])
    if not isinstance(items, list):
        handler._json_response({"error": "items 必须是数组"}, 400)
        return True
    conn = get_conn()
    cur = conn.cursor()
    if not _ensure_estimate_exists(cur, eid):
        conn.close()
        handler._json_response({"error": "Not found"}, 404)
        return True
    cur.execute("DELETE FROM estimate_payment_milestones WHERE estimate_id=?", (eid,))
    for idx, m in enumerate(items):
        custom_stage_name = _safe_str(m.get("custom_stage_name"), 100).strip()
        stage_item_id = _parse_int(m.get("trigger_stage_template_item_id")) or None
        if custom_stage_name:
            stage_item_id = None
        cur.execute(
            """
            INSERT INTO estimate_payment_milestones
            (estimate_id, name, sort_order, trigger_type, trigger_stage_template_item_id, custom_stage_name,
             trigger_days_after_completion, amount_pct, amount_fixed, is_holdback, note,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                eid,
                _safe_str(m.get("name"), 100),
                idx + 1,
                m.get("trigger_type") if m.get("trigger_type") in (
                    "signing", "stage", "completion_immediate", "completion_delayed"
                ) else "stage",
                stage_item_id,
                custom_stage_name,
                _parse_int(m.get("trigger_days_after_completion"), 0),
                _parse_float(m.get("amount_pct"), 0),
                _parse_float(m.get("amount_fixed")) if m.get("amount_fixed") not in (None, "") else None,
                1 if m.get("is_holdback") else 0,
                _safe_str(m.get("note"), 500),
                _now(), _now(),
            ),
        )
    _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True, "count": len(items)})
    return True


# ====================================================================
# 从模板加载
# ====================================================================

def _handle_load_template(handler, get_conn, eid, tid):
    """把模板的分区+明细复制到报价。会清空当前报价的分区+明细。"""
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    if not _ensure_estimate_exists(cur, eid):
        conn.close()
        handler._json_response({"error": "Estimate not found"}, 404)
        return True
    cur.execute("SELECT * FROM estimate_template_v2 WHERE id=? AND is_active=1", (tid,))
    tpl = cur.fetchone()
    if not tpl:
        conn.close()
        handler._json_response({"error": "Template not found"}, 404)
        return True
    # 清空现有分区+明细
    cur.execute("DELETE FROM estimate_lines WHERE estimate_id=?", (eid,))
    cur.execute("DELETE FROM estimate_sections WHERE estimate_id=?", (eid,))
    # 模板分区
    cur.execute(
        """
        SELECT ets.*, sm.name_zh AS section_name_zh
        FROM estimate_template_sections ets
        JOIN estimate_sections_master sm ON sm.id=ets.section_master_id
        WHERE ets.template_id=?
        ORDER BY ets.sort_order, ets.id
        """, (tid,),
    )
    sections = cur.fetchall()
    for sec in sections:
        cur.execute(
            """
            INSERT INTO estimate_sections (estimate_id, master_id, name, sort_order, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (eid, sec["section_master_id"], sec["section_name_zh"], sec["sort_order"], _now(), _now()),
        )
        new_sec_id = cur.lastrowid
        cur.execute(
            """
            SELECT etl.*, pl.material_unit_price AS lib_mat, pl.labor_unit_price AS lib_lab
            FROM estimate_template_lines etl
            LEFT JOIN price_library pl ON pl.id=etl.price_library_id
            WHERE etl.template_section_id=?
            ORDER BY etl.sort_order, etl.id
            """, (sec["id"],),
        )
        for ln in cur.fetchall():
            mat = ln["override_material_price"] if ln["override_material_price"] is not None else (ln["lib_mat"] or 0)
            lab = ln["override_labor_price"] if ln["override_labor_price"] is not None else (ln["lib_lab"] or 0)
            cur.execute(
                """
                INSERT INTO estimate_lines
                (estimate_id, section_id, price_library_id, item_name, description, quantity, unit,
                 material_unit_price, labor_unit_price, line_subtotal, sort_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, 0, ?, ?, ?)
                """,
                (
                    eid, new_sec_id, ln["price_library_id"], ln["item_name"], ln["description"] or "",
                    ln["unit"] or "", mat, lab, ln["sort_order"], _now(), _now(),
                ),
            )
    # markup 也用模板的
    cur.execute(
        "UPDATE estimates SET markup_rate=?, source_template_id=?, estimate_type=?, updated_at=? WHERE id=?",
        (tpl["default_markup_rate"], tid, tpl["estimate_type"], _now(), eid),
    )
    cur.execute("UPDATE estimate_template_v2 SET use_count=COALESCE(use_count,0)+1 WHERE id=?", (tid,))
    _recalc_estimate_totals(cur, eid)
    _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


# ====================================================================
# 重建附加项
# ====================================================================

def _handle_addon_create(handler, get_conn, user, eid):
    body = _read_body_json(handler)
    if body is None:
        return True
    name = _safe_str(body.get("name"), 200)
    if not name:
        handler._json_response({"error": "name 必填"}, 400)
        return True
    conn = get_conn()
    cur = conn.cursor()
    if not _ensure_estimate_exists(cur, eid):
        conn.close()
        handler._json_response({"error": "Estimate not found"}, 404)
        return True
    qty = _parse_float(body.get("quantity"), 1)
    unit_price = _parse_float(body.get("unit_price"), 0)
    addon_subtotal = qty * unit_price
    cur.execute(
        """
        INSERT INTO estimate_addons
        (estimate_id, rebuild_lib_id, name, description, unit_price, quantity, unit,
         addon_subtotal, is_selected, sort_order, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            eid, _parse_int(body.get("rebuild_lib_id")) or None,
            name, _safe_str(body.get("description"), 500),
            unit_price, qty,
            _safe_str(body.get("unit"), 32),
            addon_subtotal,
            1 if body.get("is_selected", True) else 0,
            _parse_int(body.get("sort_order"), 99),
            _now(), _now(),
        ),
    )
    new_id = cur.lastrowid
    _recalc_estimate_totals(cur, eid)
    _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"id": new_id, "addon_subtotal": addon_subtotal}, 201)
    return True


_ADDON_FIELDS = ["name", "description", "unit_price", "quantity", "unit",
                 "is_selected", "sort_order", "rebuild_lib_id"]


def _handle_addon_update(handler, get_conn, user, eid, aid):
    body = _read_body_json(handler)
    if body is None:
        return True
    fields, params = [], []
    for f in _ADDON_FIELDS:
        if f in body:
            fields.append(f"{f}=?")
            v = body[f]
            if f in ("unit_price", "quantity"):
                v = _parse_float(v, 0)
            elif f in ("sort_order", "rebuild_lib_id"):
                v = _parse_int(v)
            elif f == "is_selected":
                v = 1 if v else 0
            else:
                max_len = 500 if f == "description" else 200
                v = _safe_str(v, max_len)
            params.append(v)
    if not fields:
        handler._json_response({"error": "无字段需要更新"}, 400)
        return True
    fields.append("updated_at=?"); params.append(_now())
    params.extend([aid, eid])
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE estimate_addons SET {', '.join(fields)} WHERE id=? AND estimate_id=?", params)
    updated = cur.rowcount
    cur.execute(
        "UPDATE estimate_addons SET addon_subtotal=quantity*unit_price WHERE id=? AND estimate_id=?",
        (aid, eid),
    )
    _recalc_estimate_totals(cur, eid)
    if updated:
        _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


def _handle_addon_delete(handler, get_conn, eid, aid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM estimate_addons WHERE id=? AND estimate_id=?", (aid, eid))
    deleted = cur.rowcount
    _recalc_estimate_totals(cur, eid)
    if deleted:
        _reset_confirmed_estimate_for_edit(cur, eid)
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


# ====================================================================
# 全局设置
# ====================================================================

_SETTINGS_KEYS = [
    "estimate_tax_enabled", "estimate_tax_rate",
    "estimate_markup_min", "estimate_markup_max", "estimate_markup_default",
    "estimate_rounding_mode",
    "estimate_holdback_default", "estimate_holdback_max",
]


def _handle_settings_get(handler, get_conn):
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    placeholders = ",".join(["?"] * len(_SETTINGS_KEYS))
    cur.execute(
        f"SELECT setting_key, setting_value FROM system_settings WHERE setting_key IN ({placeholders})",
        _SETTINGS_KEYS,
    )
    out = {r["setting_key"]: r["setting_value"] for r in cur.fetchall()}
    conn.close()
    handler._json_response(out)
    return True


def _handle_settings_save(handler, get_conn, user):
    body = _read_body_json(handler)
    if body is None:
        return True
    if not isinstance(body, dict):
        handler._json_response({"error": "Body must be object"}, 400)
        return True
    conn = get_conn()
    cur = conn.cursor()
    for k, v in body.items():
        if k not in _SETTINGS_KEYS:
            continue
        cur.execute(
            """
            INSERT INTO system_settings (setting_key, setting_value, setting_group, updated_at, updated_by)
            VALUES (?, ?, 'estimate', ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value, updated_at=excluded.updated_at, updated_by=excluded.updated_by
            """,
            (k, str(v), _now(), user.get("id")),
        )
    conn.commit()
    conn.close()
    handler._json_response({"ok": True})
    return True


# ====================================================================
# 阶段模板项(给付款节点关联用)
# ====================================================================

def _handle_stage_items_list(handler, get_conn, query):
    """列出所有 active 的阶段模板项"""
    conn = get_conn()
    conn.row_factory = __import__("sqlite3").Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT psti.id, psti.template_id, psti.step_name, psti.step_order,
               pst.name AS template_name, pst.project_type
        FROM project_stage_template_items psti
        JOIN project_stage_templates pst ON pst.id=psti.template_id
        WHERE psti.is_active=1 AND pst.is_active=1
        ORDER BY pst.id, psti.step_order
        """,
    )
    rows = _rows_to_dicts(cur.fetchall())
    conn.close()
    handler._json_response({"items": rows})
    return True


# ====================================================================
# PDF 显示选项保存(每报价独立)
# ====================================================================

_PDF_OPTION_FIELDS = [
    "pdf_show_unit_price",
    "pdf_show_pct",
    "pdf_show_material",
    "pdf_show_labor",
    "pdf_language",
]


def _handle_pdf_options_save(handler, get_conn, eid):
    """PUT /api/v2/estimates/{id}/pdf-options
    保存 PDF 显示相关的开关。"""
    body = _read_body_json(handler)
    if body is None:
        return True
    fields, params = [], []
    for f in _PDF_OPTION_FIELDS:
        if f in body:
            fields.append(f"{f}=?")
            v = body[f]
            if f == "pdf_language":
                if v not in ("zh", "en"):
                    v = "en"
            else:
                v = 1 if v else 0
            params.append(v)
    if not fields:
        handler._json_response({"error": "无字段需要更新"}, 400)
        return True
    fields.append("updated_at=?")
    params.append(_now())
    params.append(eid)
    conn = get_conn()
    cur = conn.cursor()
    if not _ensure_estimate_exists(cur, eid):
        conn.close()
        handler._json_response({"error": "Estimate not found"}, 404)
        return True
    try:
        cur.execute(f"UPDATE estimates SET {', '.join(fields)} WHERE id=?", params)
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        handler._json_response({"error": f"保存失败: {e}"}, 400)
        return True
    conn.close()
    handler._json_response({"ok": True})
    return True


# ====================================================================
# PDF 导出(返回 HTML,浏览器自动打印)
# ====================================================================

def _handle_pdf_export(handler, get_conn, estimate_id, qs):
    """处理 GET /api/v2/estimates/{id}/pdf 或 /api/estimates/{id}/pdf
    返回 HTML 文档,浏览器自动调起打印对话框。"""
    user = handler._require_auth()
    if not user:
        return True
    if not handler._require_module(user, "estimates"):
        return True

    query = _parse_query_string(qs)
    lang = query.get("lang", "en")
    if lang not in ("zh", "en"):
        # 包括废弃值 both / zh+en / zh+es 等,统一兜底为 en
        lang = "en"
    auto_print_q = query.get("auto_print", "0")  # P2F3_PATCH_APPLIED: default no-auto-print, user clicks toolbar to print
    auto_print = auto_print_q not in ("0", "false", "no")

    try:
        html_doc = ev2pdf.generate_estimate_pdf_html(
            get_conn, estimate_id, lang=lang, auto_print=auto_print, mode="pdf",
        )
    except Exception as e:
        handler._json_response({"error": f"PDF 生成失败: {e}"}, 500)
        return True

    if html_doc is None:
        handler._json_response({"error": "Estimate not found"}, 404)
        return True

    # 直接发 HTML
    payload = html_doc.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
    handler.end_headers()
    handler.wfile.write(payload)
    return True
