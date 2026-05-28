"""
estimates_v2_pdf.py
报价 PDF/HTML 生成模块(v2)

使用方式:从 estimates_v2_module.py 调用 generate_estimate_pdf_html()。
返回完整的 HTML 字符串,带 auto_print=True 时会自动调浏览器打印 → 用户保存为 PDF。

设计要点:
- 复用现有架构:不引入新的 Python PDF 库,沿用"HTML + window.print()"
- 品牌色从 company_settings 表读
- Logo URL 从 company_settings.logo_horizontal_url 读
- 多语言:lang="zh" / "en" / "both"
- 内嵌 CSS,所有样式 inline 或在 <style> 里(避免依赖外部 CSS,PDF 转换更稳)
- 受报价的 pdf_show_unit_price 和 pdf_show_pct 字段控制可见性
"""

import json
import datetime
import html as html_module


def _esc(s):
    """HTML 转义"""
    if s is None:
        return ""
    return html_module.escape(str(s), quote=True)


def _money(n, with_dollar=True):
    n = float(n or 0)
    s = f"{n:,.2f}"
    return f"${s}" if with_dollar else s


def _pct(n, decimals=1):
    return f"{float(n or 0):.{decimals}f}%"


# ====================================================================
# i18n 标签字典
# ====================================================================

_LABELS = {
    "zh": {
        "title": "估价单",
        "payment_title": "付款计划",
        "estimate_no": "报价号",
        "linked_estimate": "关联报价",
        "date": "日期",
        "valid_until": "有效期至",
        "customer_info": "客户信息",
        "customer_name": "客户姓名",
        "customer_phone": "电话",
        "customer_address": "地址",
        "project_title": "项目",
        "estimate_type": "报价类型",
        "type_renovation": "翻新",
        "type_rebuild": "重建",
        "details": "报价明细",
        "section": "分区",
        "section_subtotal": "分区合计",
        "item": "项目",
        "description": "描述",
        "qty": "数量",
        "unit": "单位",
        "unit_price": "单价",
        "material": "材料",
        "labor": "人工",
        "line_subtotal": "小计",
        "summary": "总价",
        "subtotal": "明细小计",
        "rebuild_main": "重建主体",
        "rebuild_addons": "附加项",
        "markup": "加成",
        "tax": "税",
        "manual_adjustment": "人工调整",
        "grand_total": "总计",
        "payment": "付款进度",
        "milestone": "节点",
        "stage": "施工阶段",
        "amount_pct": "百分比",
        "amount": "金额",
        "payment_total": "付款计划合计",
        "holdback_note": "留款说明",
        "payment_terms": [
            "付款节点按双方确认的施工阶段执行。",
            "如项目范围或金额发生变更,付款计划可随变更单调整。",
            "未到达对应阶段前,该节点款项不视为到期。",
        ],
        "holdback_marker": "★ 完工后留款",
        "remarks": "备注 / 说明",
        "default_remarks": [
            "本报价有效期 30 天,过期需重新核算。",
            "价格不含 HOA、城市附加费及第三方检测费用。",
            "客户自行提供材料的工时另议。",
            "如施工中发现现状结构问题,涉及变更需另签变更单。",
            "签约后施工期为相互约定时间,具体顺延以书面通知为准。",
        ],
        "page_footer": "页",
        "of": "/",
    },
    "en": {
        "title": "Estimate / Quote",
        "payment_title": "Payment Schedule",
        "estimate_no": "Estimate #",
        "linked_estimate": "Related Estimate",
        "date": "Date",
        "valid_until": "Valid until",
        "customer_info": "Customer Info",
        "customer_name": "Name",
        "customer_phone": "Phone",
        "customer_address": "Address",
        "project_title": "Project",
        "estimate_type": "Estimate Type",
        "type_renovation": "Renovation",
        "type_rebuild": "Rebuild",
        "details": "Estimate Details",
        "section": "Section",
        "section_subtotal": "Section Subtotal",
        "item": "Item",
        "description": "Description",
        "qty": "Qty",
        "unit": "Unit",
        "unit_price": "Unit Price",
        "material": "Material",
        "labor": "Labor",
        "line_subtotal": "Subtotal",
        "summary": "Summary",
        "subtotal": "Items Subtotal",
        "rebuild_main": "Rebuild Main",
        "rebuild_addons": "Add-ons",
        "markup": "Markup",
        "tax": "Tax",
        "manual_adjustment": "Manual Adjustment",
        "grand_total": "Grand Total",
        "payment": "Payment Schedule",
        "milestone": "Milestone",
        "stage": "Construction Stage",
        "amount_pct": "Percentage",
        "amount": "Amount",
        "payment_total": "Payment Schedule Total",
        "holdback_note": "Holdback Note",
        "payment_terms": [
            "Payments are due according to the agreed construction milestones.",
            "If project scope or contract amount changes, this payment schedule may be adjusted by change order.",
            "A milestone payment is not due before the related stage is reached.",
        ],
        "holdback_marker": "★ Holdback (post-completion)",
        "remarks": "Notes & Terms",
        "default_remarks": [
            "This estimate is valid for 30 days; pricing may change after expiration.",
            "Prices do NOT include HOA fees, city impact fees or third-party inspection costs.",
            "Owner-supplied materials may incur additional labor charges.",
            "Any structural issues discovered during construction may require a Change Order.",
            "Construction schedule is mutually agreed; written notice required for adjustments.",
        ],
        "page_footer": "Page",
        "of": "of",
    },
}


def _L(lang, key):
    if lang == "both":
        zh = _LABELS["zh"].get(key, key)
        en = _LABELS["en"].get(key, key)
        if isinstance(zh, list) or isinstance(en, list):
            return zh or en
        return f"{zh} / {en}"
    return _LABELS.get(lang, _LABELS["zh"]).get(key, key)


# ====================================================================
# 数据加载(从数据库聚合一份完整 estimate 视图)
# ====================================================================

def _load_estimate_full(get_conn, estimate_id):
    import sqlite3
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM estimates WHERE id=?", (estimate_id,))
    est = cur.fetchone()
    if not est:
        conn.close()
        return None
    est = dict(est)
    # 客户
    if est.get("customer_id"):
        cur.execute("SELECT id, name, phone, primary_address FROM customers WHERE id=?", (est["customer_id"],))
        c = cur.fetchone()
        est["customer"] = dict(c) if c else None
    else:
        est["customer"] = None
    # 分区+明细
    cur.execute(
        """
        SELECT es.*, sm.code AS section_code, sm.name_zh AS section_name_zh, sm.name_en AS section_name_en
        FROM estimate_sections es
        LEFT JOIN estimate_sections_master sm ON sm.id=es.master_id
        WHERE es.estimate_id=?
        ORDER BY es.sort_order, es.id
        """, (estimate_id,),
    )
    sections = [dict(r) for r in cur.fetchall()]
    for sec in sections:
        cur.execute(
            "SELECT * FROM estimate_lines WHERE section_id=? ORDER BY sort_order, id",
            (sec["id"],),
        )
        sec["lines"] = [dict(r) for r in cur.fetchall()]
    est["sections"] = sections
    # 重建附加项
    cur.execute(
        "SELECT * FROM estimate_addons WHERE estimate_id=? AND is_selected=1 ORDER BY sort_order, id",
        (estimate_id,),
    )
    est["addons"] = [dict(r) for r in cur.fetchall()]
    # 付款节点
    cur.execute(
        """
        SELECT epm.*, psti.step_name AS stage_step_name
        FROM estimate_payment_milestones epm
        LEFT JOIN project_stage_template_items psti ON psti.id=epm.trigger_stage_template_item_id
        WHERE epm.estimate_id=?
        ORDER BY epm.sort_order, epm.id
        """, (estimate_id,),
    )
    est["payment_milestones"] = [dict(r) for r in cur.fetchall()]
    # 公司信息(品牌、logo)
    cur.execute("SELECT * FROM company_settings WHERE id=1")
    co = cur.fetchone()
    est["_company"] = dict(co) if co else {}
    conn.close()
    return est


# ====================================================================
# CSS 样式
# ====================================================================

def _build_css(brand):
    primary = brand.get("primary_color") or "#2C2C2C"
    accent = brand.get("accent_color") or "#B8965A"
    dark = brand.get("dark_color") or "#2C2C2C"
    light_bg = brand.get("light_bg") or "#FAFAFA"
    return f"""
<style>
  @page {{
    size: Letter;
    margin: 14mm 12mm 16mm 12mm;
    /* 注意:大部分浏览器(Chrome / Edge)对 @page 的 margin-box 支持有限,
       所以多页页眉我们通过 thead 自动重复 + position:fixed 双管齐下 */
  }}
  * {{ box-sizing: border-box; }}
  html, body {{
    margin: 0;
    padding: 0;
    font-family: "PingFang SC", "Microsoft YaHei", "Hiragino Sans GB", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: {dark};
    font-size: 11px;
    line-height: 1.5;
    background: white;
  }}
  .pdf-wrap {{ padding: 0; }}

  /* === 多页固定页眉(打印时每页都显示) === */
  .running-header {{
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 18mm;
    background: white;
    border-bottom: 1.5px solid {accent};
    padding: 4mm 12mm 2mm 12mm;
    display: none;  /* 屏幕预览时不显示;打印时由 @media print 启用 */
    align-items: center;
    justify-content: space-between;
    z-index: 100;
  }}
  .running-header .left {{
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .running-header img.mini-logo {{
    max-height: 10mm;
    max-width: 30mm;
    object-fit: contain;
  }}
  .running-header .company-mini {{
    font-size: 10px;
    color: {primary};
    font-weight: 600;
  }}
  .running-header .est-no-mini {{
    font-size: 10px;
    color: #555;
  }}
  .running-footer {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 12mm;
    background: white;
    border-top: 1px solid #ddd;
    padding: 2mm 12mm;
    display: none;
    text-align: center;
    font-size: 9px;
    color: #888;
    z-index: 100;
  }}

  /* 屏幕预览模式下,把页眉显示出来(降级到普通顶部条) */
  @media screen {{
    .running-header {{
      display: none;
    }}
    .running-footer {{ display: none; }}
  }}

  /* 顶部第一页大头 - 紧凑版,不再有金色边框(避免和页眉打架) */
  .pdf-head {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding-bottom: 4px;
    margin-bottom: 6px;
  }}
  .pdf-head .left {{ flex: 1; }}
  .pdf-head .right {{ text-align: right; }}
  .pdf-head img.logo {{
    max-height: 38px;
    max-width: 160px;
    object-fit: contain;
    /* P2F_PATCH_APPLIED: 强制保留 logo 原色,防止省墨打印模式洗白 */
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}
  .pdf-head .company-name {{
    font-size: 12px;
    font-weight: 600;
    color: {primary};
    margin-top: 2px;
    line-height: 1.2;
  }}
  .pdf-head .tagline {{
    font-size: 9px;
    color: #777;
    margin-top: 1px;
    line-height: 1.2;
  }}
  .pdf-head h1 {{
    font-size: 17px;
    font-weight: 600;
    color: {primary};
    margin: 0 0 3px 0;
    line-height: 1.1;
  }}
  .pdf-head .meta {{
    font-size: 9px;
    color: #555;
    line-height: 1.5;
  }}
  .pdf-head .meta b {{
    color: {dark};
    margin-right: 3px;
  }}

  /* 区块标题 - 紧凑 */
  h2.section-title {{
    font-size: 11px;
    font-weight: 600;
    color: white;
    background: {primary};
    padding: 3px 8px;
    margin: 10px 0 0 0;
    border-radius: 2px 2px 0 0;
    /* 标题不要单独留在页底 */
    page-break-after: avoid;
    break-after: avoid;
  }}
  .pdf-block {{
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .details-block {{
    page-break-inside: auto;
    break-inside: auto;
  }}
  .section-body {{
    /* 不要左右竖线(打印时显示难看) */
    border-bottom: 1px solid #ddd;
    padding: 6px 10px;
    background: white;
    margin-bottom: 3px;
  }}

  /* 客户卡片 - 单行紧凑布局 */
  .customer-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2px 18px;
    font-size: 10.5px;
  }}
  .customer-grid b {{
    color: {primary};
    margin-right: 4px;
    font-weight: 600;
  }}

  /* 分区表 */
  .est-section-title {{
    font-size: 12px;
    font-weight: 600;
    color: {primary};
    background: {light_bg};
    padding: 4px 8px;
    margin: 10px 0 0 0;
    border-left: 3px solid {accent};
    /* 分区标题不要单独在页底 */
    page-break-after: avoid;
    break-after: avoid;
  }}
  table.lines-tbl {{
    width: 100%;
    border-collapse: collapse;
    margin: 0 0 4px 0;
    font-size: 10.5px;
  }}
  .estimate-section-block {{
    page-break-inside: auto;
    break-inside: auto;
  }}
  table.lines-tbl thead {{
    /* 表格跨页时表头自动重复 */
    display: table-header-group;
    page-break-inside: avoid;
    break-inside: avoid;
    page-break-after: avoid;
    break-after: avoid;
  }}
  table.lines-tbl tbody {{
    page-break-inside: auto;
    break-inside: auto;
  }}
  table.lines-tbl th {{
    background: {light_bg};
    color: {primary};
    font-weight: 600;
    text-align: left;
    padding: 5px 8px;
    border-bottom: 1px solid #ccc;
    font-size: 10px;
  }}
  table.lines-tbl td {{
    padding: 4px 8px;
    border-bottom: 1px solid #eee;
    vertical-align: top;
  }}
  table.lines-tbl td.num,
  table.lines-tbl th.num {{
    text-align: right;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }}
  table.lines-tbl tr {{
    /* 行不要被切断 */
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  table.lines-tbl tr.first-line {{
    page-break-before: avoid;
    break-before: avoid;
  }}
  table.lines-tbl tr.keep-with-subtotal {{
    page-break-after: avoid;
    break-after: avoid;
  }}
  table.lines-tbl tr.subtotal-row td {{
    background: {light_bg};
    font-weight: 600;
    border-top: 1px solid #ccc;
    border-bottom: none;
  }}
  /* 分区合计行紧跟在前面的内容,避免单独跑到下一页头 */
  table.lines-tbl tr.subtotal-row {{
    page-break-before: avoid;
    break-before: avoid;
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  .item-name {{
    font-weight: 500;
    color: {dark};
  }}
  .item-desc {{
    font-size: 9.5px;
    color: #888;
    margin-top: 1px;
  }}

  /* 重建专属 */
  .rebuild-summary {{
    background: {light_bg};
    padding: 10px 14px;
    border-left: 3px solid {accent};
    margin-bottom: 10px;
  }}
  .rebuild-summary .row {{
    display: flex;
    justify-content: space-between;
    padding: 2px 0;
  }}

  /* 总价表 */
  .totals-tbl {{
    width: 60%;
    margin-left: auto;
    margin-top: 8px;
    border-collapse: collapse;
    font-size: 11px;
  }}
  .totals-tbl td {{
    padding: 5px 12px;
    border-bottom: 1px solid #eee;
  }}
  .totals-tbl td.lbl {{ color: #555; }}
  .totals-tbl td.val {{
    text-align: right;
    font-variant-numeric: tabular-nums;
  }}
  .totals-tbl tr.grand td {{
    border-top: 2px solid {primary};
    border-bottom: none;
    padding-top: 8px;
    font-size: 13px;
    font-weight: 600;
    color: {primary};
  }}
  /* 短块尽量整块换页,不要把标题留在上一页 */
  .summary-block, .payment-block, .remarks-block, .customer-block {{
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  /* 付款表 */
  table.pay-tbl {{
    width: 100%;
    border-collapse: collapse;
    font-size: 10.5px;
  }}
  table.pay-tbl thead {{
    display: table-header-group;
    page-break-inside: avoid;
    break-inside: avoid;
    page-break-after: avoid;
    break-after: avoid;
  }}
  table.pay-tbl th {{
    background: {light_bg};
    color: {primary};
    font-weight: 600;
    text-align: left;
    padding: 5px 8px;
    border-bottom: 1px solid #ccc;
    font-size: 10px;
  }}
  table.pay-tbl td {{
    padding: 5px 8px;
    border-bottom: 1px solid #eee;
  }}
  table.pay-tbl td.num,
  table.pay-tbl th.num {{
    text-align: right;
    font-variant-numeric: tabular-nums;
  }}
  table.pay-tbl tr {{
    page-break-inside: avoid;
    break-inside: avoid;
  }}
  table.pay-tbl tr.holdback td {{
    background: rgba(184, 150, 90, 0.08);
    font-weight: 500;
  }}
  table.pay-tbl tr.subtotal-row td {{
    background: {light_bg};
    font-weight: 600;
    border-top: 1px solid #ccc;
    border-bottom: none;
  }}
  .payment-note {{
    margin-top: 8px;
    font-size: 10px;
    color: #555;
  }}

  /* 备注 */
  .remarks ul {{
    margin: 4px 0 0 0;
    padding-left: 18px;
    font-size: 10px;
    color: #555;
  }}
  .remarks-block h2.section-title {{
    margin-top: 8px;
  }}
  .remarks li {{ margin-bottom: 3px; page-break-inside: avoid; break-inside: avoid; }}

  /* 末尾页脚(只在最后一页底部) */
  .pdf-footer {{
    border-top: 1px solid #ddd;
    margin-top: 18px;
    padding-top: 8px;
    font-size: 9.5px;
    color: #777;
    text-align: center;
    line-height: 1.7;
  }}
  .pdf-footer .company-line {{
    color: {primary};
    font-weight: 500;
  }}

  /* P2F_PATCH_APPLIED: 控制条(屏幕显示,打印隐藏)
     默认收起为右侧中部 24px 小把手,hover/focus-within 展开 */
  .toolbar {{
    position: fixed;
    top: 50%;
    right: 0;
    transform: translateY(-50%);
    background: {primary};
    color: white;
    border-radius: 4px 0 0 4px;
    box-shadow: -2px 2px 8px rgba(0,0,0,0.2);
    z-index: 9999;
    display: flex;
    align-items: center;
    overflow: hidden;
    width: 24px;
    min-height: 64px;
    opacity: 0.55;
    transition: width 0.25s ease 0.5s, opacity 0.2s ease 0.5s;
  }}
  .toolbar:hover, .toolbar:focus-within {{
    width: 280px;  /* P2F2_PATCH_APPLIED: was 240, widened so close button is not clipped */
    opacity: 1;
    transition: width 0.25s ease 0s, opacity 0.2s ease 0s;
  }}
  .toolbar .toolbar-handle {{
    flex: 0 0 24px;
    width: 24px;
    text-align: center;
    font-size: 16px;
    line-height: 64px;
    color: white;
    user-select: none;
    pointer-events: none;
  }}
  .toolbar:hover .toolbar-handle,
  .toolbar:focus-within .toolbar-handle {{
    display: none;
  }}
  .toolbar .toolbar-body {{
    display: none;
    padding: 8px 14px;
    white-space: nowrap;
    align-items: center;
  }}
  .toolbar:hover .toolbar-body,
  .toolbar:focus-within .toolbar-body {{
    display: flex;
  }}
  .toolbar button {{
    background: white;
    color: {primary};
    border: none;
    padding: 5px 12px;
    border-radius: 3px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 500;
    margin-left: 6px;
  }}

  @media print {{
    .toolbar {{ display: none !important; }}
    /* 打印时:running-header 完全不显示
       (它原本是给多页加固定页眉用的,但会在第一页造成双 logo;
        多页时表格的 thead 会自动重复,客户能识别是同一份估价单) */
    .running-header {{
      display: none !important;
    }}
    .running-footer {{
      display: block !important;
      position: fixed;
    }}
    body {{
      padding-top: 0;
    }}

    /* === 打印时强制改用黑色为主,以正式感为先 === */
    .pdf-head h1 {{
      color: #000 !important;
    }}
    .pdf-head .company-name,
    .pdf-head .meta b,
    .customer-grid b,
    .totals-tbl tr.grand td,
    .pdf-footer .company-line {{
      color: #000 !important;
    }}
    .pdf-head {{
      border-bottom: 1px solid #888 !important;
      padding-bottom: 8px !important;
      margin-bottom: 10px !important;
    }}
    h2.section-title {{
      /* P2F2_PATCH_APPLIED: harden to prevent ghost-text on physical prints */
      background: #f0f0f0 !important;
      background-color: #f0f0f0 !important;
      background-image: none !important;
      color: #000 !important;
      text-shadow: none !important;
      -webkit-text-stroke: 0 !important;
      border-left: 3px solid #888 !important;
    }}
    .est-section-title {{
      /* P2F2_PATCH_APPLIED: harden to prevent ghost-text on physical prints */
      background: #fafafa !important;
      background-color: #fafafa !important;
      background-image: none !important;
      color: #000 !important;
      text-shadow: none !important;
      -webkit-text-stroke: 0 !important;
      border-left: 3px solid #555 !important;
    }}
    table.lines-tbl th,
    table.pay-tbl th {{
      background: #f5f5f5 !important;
      color: #000 !important;
    }}
    table.lines-tbl tr.subtotal-row td {{
      background: #f5f5f5 !important;
      color: #000 !important;
    }}
    table.pay-tbl tr.subtotal-row td {{
      background: #f5f5f5 !important;
      color: #000 !important;
    }}
    /* P2F3_PATCH_APPLIED: force item name + desc to plain black/gray on print */
    .item-name {{
      color: #000 !important;
      text-shadow: none !important;
      -webkit-text-stroke: 0 !important;
      background-image: none !important;
    }}
    .item-desc {{
      color: #555 !important;
      text-shadow: none !important;
    }}
    /* Generic safety net for any td color leakage */
    table.lines-tbl tbody td {{
      color: #000 !important;
    }}
    .totals-tbl tr.grand td {{
      border-top: 2px solid #000 !important;
    }}
    /* 留款行打印时也用浅灰,不要金色 */
    table.pay-tbl tr.holdback td {{
      background: #f5f5f5 !important;
    }}

    h2.section-title {{ break-after: avoid; }}
    .est-section-title {{ break-after: avoid; }}
    .pdf-block, .summary-block, .payment-block, .remarks-block, .customer-block {{
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    .details-block, .estimate-section-block {{
      break-inside: auto;
      page-break-inside: auto;
    }}
    table.lines-tbl thead,
    table.pay-tbl thead {{
      break-inside: avoid;
      page-break-inside: avoid;
      break-after: avoid;
      page-break-after: avoid;
    }}
    table.lines-tbl tr,
    table.pay-tbl tr {{
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    table.lines-tbl tr.keep-with-subtotal {{
      break-after: avoid;
      page-break-after: avoid;
    }}
    table.lines-tbl tr.subtotal-row {{
      break-before: avoid;
      page-break-before: avoid;
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    table {{ break-inside: auto; }}
  }}

  .bilingual-sub {{
    font-size: 9px;
    color: #999;
    font-weight: normal;
    margin-left: 6px;
  }}
</style>
"""


# ====================================================================
# HTML 主体生成
# ====================================================================

def _label_with_translation(zh, en, lang):
    """根据 lang 返回 zh / en / 双语"""
    if lang == "en":
        return _esc(en or zh)
    if lang == "both" and en and en != zh:
        return f"{_esc(zh)} <span class='bilingual-sub'>{_esc(en)}</span>"
    return _esc(zh)


def _render_running_header(est, lang):
    """每页都显示的小页眉(打印时固定在页顶)"""
    co = est.get("_company") or {}
    company_name = co.get("company_name") or "Oaklian Builders"
    logo_url = co.get("logo_horizontal_url") or "/assets/images/logo-oaklian-dark.png"
    est_no = f"#{est['id']:05d}"
    title = _L(lang, "title")
    return f"""
    <div class="running-header">
      <div class="left">
        <img class="mini-logo" src="{_esc(logo_url)}" onerror="this.style.display='none'" />
        <span class="company-mini">{_esc(company_name)}</span>
      </div>
      <div class="est-no-mini">{_esc(title)} {_esc(est_no)}</div>
    </div>
    """


def _render_running_footer(est, lang):
    """每页底部页脚"""
    co = est.get("_company") or {}
    company_name = co.get("company_name") or "Oaklian Builders"
    return f"""
    <div class="running-footer">
      <span>{_esc(company_name)} · info@oaklian.com</span>
    </div>
    """


def _render_head(est, lang):
    co = est.get("_company") or {}
    company_name = co.get("company_name") or "Oaklian Builders"
    legal_name = co.get("legal_name") or ""
    tagline = co.get("tagline") or ""
    logo_url = co.get("logo_horizontal_url") or "/assets/images/logo-oaklian-dark.png"

    # 报价号
    est_no = f"#{est['id']:05d}"
    today = datetime.date.today().isoformat()
    # 有效期 30 天
    valid_until = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()

    return f"""
    <div class="pdf-head">
      <div class="left">
        <img class="logo" src="{_esc(logo_url)}" onerror="this.style.display='none'" />
        <div class="company-name">{_esc(company_name)}</div>
        {f'<div class="tagline">{_esc(legal_name)}</div>' if legal_name else ''}
        {f'<div class="tagline">{_esc(tagline)}</div>' if tagline else ''}
      </div>
      <div class="right">
        <h1>{_L(lang, 'title')}</h1>
        <div class="meta">
          <div><b>{_L(lang, 'estimate_no')}:</b>{_esc(est_no)}</div>
          <div><b>{_L(lang, 'date')}:</b>{_esc(today)}</div>
          <div><b>{_L(lang, 'valid_until')}:</b>{_esc(valid_until)}</div>
        </div>
      </div>
    </div>
    """


def _render_payment_head(est, lang):
    co = est.get("_company") or {}
    company_name = co.get("company_name") or "Oaklian Builders"
    legal_name = co.get("legal_name") or ""
    tagline = co.get("tagline") or ""
    logo_url = co.get("logo_horizontal_url") or "/assets/images/logo-oaklian-dark.png"

    est_no = f"#{est['id']:05d}"
    today = datetime.date.today().isoformat()

    return f"""
    <div class="pdf-head payment-doc-head">
      <div class="left">
        <img class="logo" src="{_esc(logo_url)}" onerror="this.style.display='none'" />
        <div class="company-name">{_esc(company_name)}</div>
        {f'<div class="tagline">{_esc(legal_name)}</div>' if legal_name else ''}
        {f'<div class="tagline">{_esc(tagline)}</div>' if tagline else ''}
      </div>
      <div class="right">
        <h1>{_L(lang, 'payment_title')}</h1>
        <div class="meta">
          <div><b>{_L(lang, 'linked_estimate')}:</b>{_esc(est_no)}</div>
          <div><b>{_L(lang, 'date')}:</b>{_esc(today)}</div>
          <div><b>{_L(lang, 'grand_total')}:</b>{_money(est.get('total_amount') or 0)}</div>
        </div>
      </div>
    </div>
    """


def _render_customer(est, lang):
    cust = est.get("customer") or {}
    if est.get("estimate_type") == "rebuild":
        type_label = _L(lang, "type_rebuild")
    else:
        type_label = _L(lang, "type_renovation")
    return f"""
    <div class="customer-block pdf-block">
    <h2 class="section-title">{_L(lang, 'customer_info')}</h2>
    <div class="section-body">
      <div class="customer-grid">
        <div><b>{_L(lang, 'customer_name')}:</b>{_esc(cust.get('name') or '-')}</div>
        <div><b>{_L(lang, 'customer_phone')}:</b>{_esc(cust.get('phone') or '-')}</div>
        <div style="grid-column: span 2;"><b>{_L(lang, 'customer_address')}:</b>{_esc(cust.get('primary_address') or '-')}</div>
        <div><b>{_L(lang, 'project_title')}:</b>{_esc(est.get('title') or '-')}</div>
        <div><b>{_L(lang, 'estimate_type')}:</b>{type_label}</div>
      </div>
    </div>
    </div>
    """


def _render_renovation_details(est, lang, show_unit_price, show_material, show_labor):
    sections = est.get("sections") or []
    if not sections:
        return f"""
        <div class="details-block">
        <h2 class="section-title">{_L(lang, 'details')}</h2>
        <div class="section-body"><i style="color:#888">— No items —</i></div>
        </div>
        """
    # 决定要显示哪些列
    # show_unit_price 是总开关:关掉时强制材料和人工都不显示
    if not show_unit_price:
        show_material = False
        show_labor = False

    # 计算列宽和列数
    # 固定列: 项目 + 描述 + 数量 + 单位 + 小计
    # 可选列: 材料$ / 人工$ / 合并单价
    cols_extra = (1 if show_material else 0) + (1 if show_labor else 0) + (1 if show_unit_price else 0)
    total_cols = 5 + cols_extra

    # 列宽分配(根据是否显示材料/人工/合并单价调整)
    if show_unit_price and show_material and show_labor:
        col_widths = ["25%", "22%", "7%", "7%", "10%", "10%", "9%", "10%"]
    elif show_unit_price and (show_material or show_labor):
        col_widths = ["29%", "25%", "8%", "8%", "12%", "8%", "10%"]
    elif show_unit_price:
        col_widths = ["34%", "29%", "8%", "8%", "10%", "11%"]
    else:
        col_widths = ["38%", "32%", "10%", "8%", "12%"]

    # 构造表头
    headers = []
    headers.append(f"<th style='width:{col_widths[0]}'>{_L(lang, 'item')}</th>")
    headers.append(f"<th style='width:{col_widths[1]}'>{_L(lang, 'description')}</th>")
    headers.append(f"<th class='num' style='width:{col_widths[2]}'>{_L(lang, 'qty')}</th>")
    headers.append(f"<th style='width:{col_widths[3]}'>{_L(lang, 'unit')}</th>")
    col_idx = 4
    if show_material:
        headers.append(f"<th class='num' style='width:{col_widths[col_idx]}'>{_L(lang, 'material')}</th>")
        col_idx += 1
    if show_labor:
        headers.append(f"<th class='num' style='width:{col_widths[col_idx]}'>{_L(lang, 'labor')}</th>")
        col_idx += 1
    if show_unit_price:
        headers.append(f"<th class='num' style='width:{col_widths[col_idx]}'>{_L(lang, 'unit_price')}</th>")
        col_idx += 1
    headers.append(f"<th class='num' style='width:{col_widths[col_idx]}'>{_L(lang, 'line_subtotal')}</th>")
    header_html = f"<thead><tr>{''.join(headers)}</tr></thead>"

    parts = [
        "<div class='details-block'>",
        f"<h2 class='section-title'>{_L(lang, 'details')}</h2>",
        "<div class='section-body'>",
    ]
    for sec in sections:
        sec_zh = sec.get("name") or sec.get("section_name_zh") or ""
        sec_en = sec.get("section_name_en") or ""
        sec_label = _label_with_translation(sec_zh, sec_en, lang)
        lines = sec.get("lines") or []
        last_line_idx = len(lines) - 1
        parts.append("<div class='estimate-section-block'>")
        parts.append(f"<div class='est-section-title'>{sec_label}</div>")
        parts.append("<table class='lines-tbl'>")
        parts.append(header_html)
        parts.append("<tbody>")

        for line_idx, ln in enumerate(lines):
            name = _esc(ln.get("item_name") or "-")
            desc = _esc(ln.get("description") or "")
            qty = float(ln.get("quantity") or 0)
            unit = _esc(ln.get("unit") or "")
            mat = float(ln.get("material_unit_price") or 0)
            lab = float(ln.get("labor_unit_price") or 0)
            unit_price = mat + lab
            sub = float(ln.get("line_subtotal") or 0)
            qty_disp = f"{qty:g}"

            cells = [
                f"<td><div class='item-name'>{name}</div></td>",
                f"<td>{desc}</td>",
                f"<td class='num'>{qty_disp}</td>",
                f"<td>{unit}</td>",
            ]
            if show_material:
                cells.append(f"<td class='num'>{_money(mat)}</td>")
            if show_labor:
                cells.append(f"<td class='num'>{_money(lab)}</td>")
            if show_unit_price:
                cells.append(f"<td class='num'>{_money(unit_price)}</td>")
            cells.append(f"<td class='num'>{_money(sub)}</td>")
            row_classes = []
            if line_idx == 0:
                row_classes.append("first-line")
            if line_idx == last_line_idx:
                row_classes.append("keep-with-subtotal")
            cls = f" class='{' '.join(row_classes)}'" if row_classes else ""
            parts.append(f"<tr{cls}>" + "".join(cells) + "</tr>")

        # 分区合计行
        sec_subtotal = float(sec.get("section_subtotal") or 0)
        # 合计行的 colspan = 总列数 - 1(留最后一列放小计)
        colspan = total_cols - 1
        parts.append(f"""
          <tr class='subtotal-row'>
            <td colspan='{colspan}' style='text-align:right'>{_L(lang, 'section_subtotal')}</td>
            <td class='num'>{_money(sec_subtotal)}</td>
          </tr>
        """)
        parts.append("</tbody></table></div>")
    parts.append("</div></div>")
    return "\n".join(parts)


def _render_rebuild_details(est, lang):
    """重建报价的明细呈现:主体单价 × 面积 + 附加项"""
    base_unit = float(est.get("rebuild_unit_price") or 0)
    sqft = float(est.get("rebuild_total_sqft") or 0)
    main_total = base_unit * sqft
    addons = est.get("addons") or []
    parts = [
        "<div class='details-block'>",
        f"<h2 class='section-title'>{_L(lang, 'details')}</h2>",
        "<div class='section-body'>",
        "<div class='rebuild-summary'>",
        f"<div class='row'><span>{_L(lang, 'rebuild_main')}:</span><span>{base_unit:,.2f} × {sqft:g} sqft = <b>{_money(main_total)}</b></span></div>",
        "</div>",
    ]
    if addons:
        parts.append("<div class='estimate-section-block'>")
        parts.append(f"<div class='est-section-title'>{_L(lang, 'rebuild_addons')}</div>")
        parts.append("<table class='lines-tbl'>")
        parts.append(f"""
          <thead><tr>
            <th style='width:40%'>{_L(lang, 'item')}</th>
            <th style='width:30%'>{_L(lang, 'description')}</th>
            <th class='num' style='width:10%'>{_L(lang, 'qty')}</th>
            <th style='width:8%'>{_L(lang, 'unit')}</th>
            <th class='num' style='width:12%'>{_L(lang, 'line_subtotal')}</th>
          </tr></thead>
          <tbody>
        """)
        last_addon_idx = len(addons) - 1
        for addon_idx, a in enumerate(addons):
            row_classes = []
            if addon_idx == 0:
                row_classes.append("first-line")
            if addon_idx == last_addon_idx:
                row_classes.append("keep-with-subtotal")
            cls = f" class='{' '.join(row_classes)}'" if row_classes else ""
            parts.append(f"""
            <tr{cls}>
              <td><div class='item-name'>{_esc(a.get('name'))}</div></td>
              <td>{_esc(a.get('description') or '')}</td>
              <td class='num'>{float(a.get('quantity') or 0):g}</td>
              <td>{_esc(a.get('unit') or '')}</td>
              <td class='num'>{_money(a.get('addon_subtotal') or 0)}</td>
            </tr>
            """)
        parts.append("</tbody></table></div>")
    parts.append("</div></div>")
    return "\n".join(parts)


def _render_totals(est, lang):
    subtotal = float(est.get("subtotal") or 0)
    markup_rate = float(est.get("markup_rate") or 0)
    markup_amt = subtotal * markup_rate / 100
    after_markup = subtotal + markup_amt
    tax_enabled = bool(est.get("tax_enabled"))
    tax_rate = float(est.get("tax_rate") or 0)
    tax_amt = (after_markup * tax_rate / 100) if tax_enabled else 0
    manual_adjustment = float(est.get("manual_adjustment") or 0)
    total = float(est.get("total_amount") or 0)
    rows = [
        f"<tr><td class='lbl'>{_L(lang, 'subtotal')}</td><td class='val'>{_money(subtotal)}</td></tr>",
        f"<tr><td class='lbl'>{_L(lang, 'markup')} ({markup_rate:g}%)</td><td class='val'>{_money(markup_amt)}</td></tr>",
    ]
    if tax_enabled:
        rows.append(f"<tr><td class='lbl'>{_L(lang, 'tax')} ({tax_rate:g}%)</td><td class='val'>{_money(tax_amt)}</td></tr>")
    if manual_adjustment:
        rows.append(f"<tr><td class='lbl'>{_L(lang, 'manual_adjustment')}</td><td class='val'>{_money(manual_adjustment)}</td></tr>")
    rows.append(f"<tr class='grand'><td class='lbl'>{_L(lang, 'grand_total')}</td><td class='val'>{_money(total)}</td></tr>")
    # 包成 summary-block,确保整个总价表不被切
    return f"""
    <div class="summary-block">
      <h2 class='section-title'>{_L(lang, 'summary')}</h2>
      <div class='section-body'>
        <table class='totals-tbl'>
          {''.join(rows)}
        </table>
      </div>
    </div>
    """


def _render_payment(est, lang, show_pct):
    ms = est.get("payment_milestones") or []
    if not ms:
        return ""
    total = float(est.get("total_amount") or 0)
    parts = [
        '<div class="payment-block">',
        f"<h2 class='section-title'>{_L(lang, 'payment')}</h2>",
        "<div class='section-body'>",
        "<table class='pay-tbl'>",
    ]
    if show_pct:
        parts.append(f"""
          <thead><tr>
            <th style='width:5%'>#</th>
            <th style='width:38%'>{_L(lang, 'milestone')}</th>
            <th style='width:32%'>{_L(lang, 'stage')}</th>
            <th class='num' style='width:10%'>{_L(lang, 'amount_pct')}</th>
            <th class='num' style='width:15%'>{_L(lang, 'amount')}</th>
          </tr></thead>
          <tbody>
        """)
    else:
        parts.append(f"""
          <thead><tr>
            <th style='width:5%'>#</th>
            <th style='width:48%'>{_L(lang, 'milestone')}</th>
            <th style='width:32%'>{_L(lang, 'stage')}</th>
            <th class='num' style='width:15%'>{_L(lang, 'amount')}</th>
          </tr></thead>
          <tbody>
        """)
    for idx, m in enumerate(ms):
        is_hb = bool(m.get("is_holdback"))
        pct = float(m.get("amount_pct") or 0)
        amt = total * pct / 100
        marker = "★" if is_hb else str(idx + 1)
        row_cls = "holdback" if is_hb else ""
        stage_name = _esc(m.get("custom_stage_name") or m.get("stage_step_name") or "")
        name = _esc(m.get("name") or "")
        if show_pct:
            parts.append(f"""
            <tr class='{row_cls}'>
              <td>{marker}</td>
              <td>{name}</td>
              <td>{stage_name}</td>
              <td class='num'>{pct:.1f}%</td>
              <td class='num'>{_money(amt)}</td>
            </tr>
            """)
        else:
            parts.append(f"""
            <tr class='{row_cls}'>
              <td>{marker}</td>
              <td>{name}</td>
              <td>{stage_name}</td>
              <td class='num'>{_money(amt)}</td>
            </tr>
            """)
    parts.append("</tbody></table></div></div>")
    return "\n".join(parts)


def _render_payment_schedule_document(est, lang):
    ms = est.get("payment_milestones") or []
    total = float(est.get("total_amount") or 0)
    parts = [
        '<div class="payment-block">',
        f"<h2 class='section-title'>{_L(lang, 'payment_title')}</h2>",
        "<div class='section-body'>",
    ]
    if not ms:
        parts.append(f"<i style='color:#888'>— {_L(lang, 'payment')} —</i>")
    else:
        parts.append("<table class='pay-tbl'>")
        parts.append(f"""
          <thead><tr>
            <th style='width:5%'>#</th>
            <th style='width:30%'>{_L(lang, 'milestone')}</th>
            <th style='width:30%'>{_L(lang, 'stage')}</th>
            <th class='num' style='width:12%'>{_L(lang, 'amount_pct')}</th>
            <th class='num' style='width:18%'>{_L(lang, 'amount')}</th>
          </tr></thead>
          <tbody>
        """)
        sum_pct = 0.0
        holdback_rows = []
        for idx, m in enumerate(ms):
            is_hb = bool(m.get("is_holdback"))
            pct = float(m.get("amount_pct") or 0)
            amt = total * pct / 100
            sum_pct += pct
            if is_hb:
                holdback_rows.append(m)
            marker = "★" if is_hb else str(idx + 1)
            row_cls = "holdback" if is_hb else ""
            stage_name = _esc(m.get("custom_stage_name") or m.get("stage_step_name") or "")
            name = _esc(m.get("name") or "")
            parts.append(f"""
            <tr class='{row_cls}'>
              <td>{marker}</td>
              <td>{name}</td>
              <td>{stage_name}</td>
              <td class='num'>{pct:.1f}%</td>
              <td class='num'>{_money(amt)}</td>
            </tr>
            """)
        parts.append(f"""
          <tr class='subtotal-row'>
            <td colspan='3' style='text-align:right'>{_L(lang, 'payment_total')}</td>
            <td class='num'>{sum_pct:.1f}%</td>
            <td class='num'>{_money(total * sum_pct / 100)}</td>
          </tr>
        """)
        parts.append("</tbody></table>")
        if holdback_rows:
            parts.append(f"<div class='payment-note'><b>{_L(lang, 'holdback_note')}:</b> {_L(lang, 'holdback_marker')}</div>")
    parts.append("</div></div>")
    return "\n".join(parts)


def _render_payment_terms(est, lang):
    terms = _LABELS.get(lang, _LABELS["en"]).get("payment_terms") or []
    return f"""
    <div class="remarks-block pdf-block">
      <h2 class='section-title'>{_L(lang, 'remarks')}</h2>
      <div class='section-body remarks'>
        <ul>{''.join(f'<li>{_esc(r)}</li>' for r in terms)}</ul>
      </div>
    </div>
    """


def _render_remarks(est, lang):
    remarks = _LABELS.get(lang if lang != "both" else "zh", _LABELS["zh"])["default_remarks"]
    if lang == "both":
        en_remarks = _LABELS["en"]["default_remarks"]
        items = []
        for zh, en in zip(remarks, en_remarks):
            items.append(f"<li>{_esc(zh)}<br><span style='color:#999;font-size:9.5px'>{_esc(en)}</span></li>")
        return f"""
        <div class="remarks-block pdf-block">
        <h2 class='section-title'>{_L(lang, 'remarks')}</h2>
        <div class='section-body remarks'><ul>{''.join(items)}</ul></div>
        </div>
        """
    return f"""
    <div class="remarks-block pdf-block">
    <h2 class='section-title'>{_L(lang, 'remarks')}</h2>
    <div class='section-body remarks'>
      <ul>{''.join(f'<li>{_esc(r)}</li>' for r in remarks)}</ul>
    </div>
    </div>
    """


def _render_footer(est, lang):
    co = est.get("_company") or {}
    name = co.get("company_name") or "Oaklian Builders"
    legal = co.get("legal_name") or ""
    tagline = co.get("tagline") or ""
    return f"""
    <div class='pdf-footer'>
      <div class='company-line'>{_esc(name)}{(' · ' + _esc(legal)) if legal else ''}</div>
      {f'<div>{_esc(tagline)}</div>' if tagline else ''}
      <div>info@oaklian.com</div>
    </div>
    """


# ====================================================================
# 主函数:生成完整 HTML(含自动打印脚本)
# ====================================================================

def generate_estimate_pdf_html(get_conn, estimate_id, lang="zh", auto_print=True, mode="pdf"):
    """
    生成报价 PDF/打印 HTML。

    参数:
      estimate_id: 报价 ID
      lang: 'zh' / 'en' / 'both'
      auto_print: 是否页面加载后自动调浏览器打印对话框
      mode: 'pdf' = 自动打印 + 关闭页面;'print' = 仅显示打印按钮(不自动)

    返回 HTML 字符串。如果报价不存在返回 None。
    """
    if lang not in ("zh", "en"):
        # 包括废弃值 both / 未来未支持的语言,兜底为 en
        lang = "en"
    est = _load_estimate_full(get_conn, estimate_id)
    if not est:
        return None

    # 沿用报价的字段控制 PDF 显示选项
    show_unit_price = bool(est.get("pdf_show_unit_price"))
    show_pct = bool(est.get("pdf_show_pct"))
    # 新增:材料/人工列各自的开关。
    # 这两个字段如果不存在(老库)默认 0(不显示)
    show_material = bool(est.get("pdf_show_material"))
    show_labor = bool(est.get("pdf_show_labor"))

    brand = est.get("_company") or {}
    css = _build_css(brand)

    # 组装 body
    if est.get("estimate_type") == "rebuild":
        details_html = _render_rebuild_details(est, lang)
    else:
        details_html = _render_renovation_details(est, lang, show_unit_price, show_material, show_labor)

    body_parts = [
        _render_running_header(est, lang),
        _render_head(est, lang),
        _render_customer(est, lang),
        details_html,
        _render_totals(est, lang),
        _render_payment(est, lang, show_pct),
        _render_remarks(est, lang),
        _render_footer(est, lang),
        _render_running_footer(est, lang),
    ]
    body_inner = "\n".join(body_parts)

    # 自动打印脚本
    auto_print_js = ""
    if auto_print:
        auto_print_js = """
        <script>
          window.addEventListener('load', function () {
            // 给浏览器一点时间渲染图片
            setTimeout(function () {
              window.print();
            }, 600);
          });
        </script>
        """

    # 工具栏(不打印时显示)P2F_PATCH_APPLIED: 加 handle + body 双层结构
    toolbar = """
      <div class="toolbar" tabindex="0">
        <span class="toolbar-handle">⋯</span>
        <div class="toolbar-body">
          <span style="font-size:11px">Oaklian PDF</span>
          <button onclick="window.print()">打印 / 保存为 PDF</button>
          <button onclick="window.close()">关闭</button>
        </div>
      </div>
    """

    title = _L(lang, "title") + f" #{est['id']:05d}"

    html_doc = f"""<!DOCTYPE html>
<html lang="{('zh-CN' if lang in ('zh','both') else 'en')}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(title)}</title>
  {css}
</head>
<body>
  {toolbar}
  <div class="pdf-wrap">
    {body_inner}
  </div>
  {auto_print_js}
</body>
</html>
"""
    return html_doc


def generate_payment_schedule_pdf_html(get_conn, estimate_id, lang="zh", auto_print=True, mode="pdf"):
    """
    生成独立付款计划 PDF/打印 HTML。不改变报价 PDF 和付款数据。
    """
    if lang not in ("zh", "en"):
        lang = "en"
    est = _load_estimate_full(get_conn, estimate_id)
    if not est:
        return None

    brand = est.get("_company") or {}
    css = _build_css(brand)
    body_parts = [
        _render_running_header(est, lang),
        _render_payment_head(est, lang),
        _render_customer(est, lang),
        _render_payment_schedule_document(est, lang),
        _render_payment_terms(est, lang),
        _render_footer(est, lang),
        _render_running_footer(est, lang),
    ]
    body_inner = "\n".join(body_parts)

    auto_print_js = ""
    if auto_print:
        auto_print_js = """
        <script>
          window.addEventListener('load', function () {
            setTimeout(function () {
              window.print();
            }, 600);
          });
        </script>
        """

    toolbar = """
      <div class="toolbar" tabindex="0">
        <span class="toolbar-handle">⋯</span>
        <div class="toolbar-body">
          <span style="font-size:11px">Oaklian Payment PDF</span>
          <button onclick="window.print()">打印 / 保存为 PDF</button>
          <button onclick="window.close()">关闭</button>
        </div>
      </div>
    """

    title = _L(lang, "payment_title") + f" #{est['id']:05d}"
    html_doc = f"""<!DOCTYPE html>
<html lang="{('zh-CN' if lang == 'zh' else 'en')}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{_esc(title)}</title>
  {css}
</head>
<body>
  {toolbar}
  <div class="pdf-wrap">
    {body_inner}
  </div>
  {auto_print_js}
</body>
</html>
"""
    return html_doc
