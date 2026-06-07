/* =========================================================================
 * estimates_v2.js
 * Oaklian CRM 报价系统 v2 前端
 *
 * 职责:接管 state.module === "estimates" 时的渲染
 *
 * 加载方式:在 index.html 里 app.js 之后加一行 <script src="estimates_v2.js">
 *
 * 工作原理:
 *   1. 等 app.js 加载完成
 *   2. 在 window.estimatesV2 上挂一个对象
 *   3. monkey-patch 现有的几个入口点,让 estimates 模块走我们的渲染
 *   4. 其他模块完全不受影响
 *
 * 5 个标签页:
 *   - quotes      报价列表 + 编辑器(取代旧的简陋面板)
 *   - lib-reno    单价库(翻新)
 *   - lib-rebuild 单价库(重建)
 *   - templates   报价模板
 *   - sections    分区管理
 * ========================================================================= */

(function () {
  "use strict";

  // ===========================================================================
  // 全局状态
  // ===========================================================================

  const ev2 = {
    activeTab: "quotes",        // 当前标签页
    list: [],                    // 报价列表
    currentEstimate: null,       // 当前编辑的报价完整数据
    priceLib: [],                // 单价库(翻新)
    priceLibRebuild: [],         // 单价库(重建)
    sectionsMaster: [],          // 分区主表
    templates: [],               // 模板列表
    stageItems: [],              // 施工阶段项
    settings: {},                // 全局设置(税率等)
    holdbackOption: 0,           // 当前报价的留款选项 0/5/10
    isOwner: false,
    debounceTimers: {},
  };

  window.estimatesV2 = ev2;

  // ===========================================================================
  // 工具函数
  // ===========================================================================

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }

  function escHtml(s) {
    if (s == null) return "";
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[c]);
  }

  function fmtMoney(n) {
    n = Number(n) || 0;
    return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtMoneyShort(n) {
    n = Number(n) || 0;
    return "$" + n.toLocaleString("en-US", { maximumFractionDigits: 0 });
  }

  function statusLabel(status) {
    const key = String(status || "draft").toLowerCase();
    const labels = {
      draft: tt("ev2_status_draft", "草稿"),
      sent: tt("ev2_status_sent", "已发送"),
      confirmed: tt("ev2_status_confirmed", "已确认"),
      rejected: tt("ev2_status_rejected", "已拒绝"),
    };
    return labels[key] || key;
  }

  function canGenerateContract(row) {
    return String(row.confirm_status || "draft").toLowerCase() === "confirmed"
      && !row.linked_contract_id
      && Number(row.customer_id || 0) > 0;
  }

  function flowButtonsHtml(est) {
    const status = String(est.confirm_status || "draft").toLowerCase();
    const noCustomer = !Number(est.customer_id || (est.customer && est.customer.id) || 0);
    const linkedMismatch = Number(est.linked_contract_mismatch || 0) === 1;
    const buttons = [];
    buttons.push(`<span class="ev2-status ev2-status-${escHtml(status)}">${escHtml(statusLabel(status))}</span>`);
    if (status === "draft") {
      buttons.push(`<button class="ev2-btn" id="ev2-mark-sent">${tt("ev2_btn_send_to_customer", "发送给客户")}</button>`);
      buttons.push(`<span class="ev2-mini">${tt("ev2_send_customer_hint", "生成客户确认链接；邮箱/短信发送后续接入。")}</span>`);
    }
    if (status === "sent") {
      buttons.push(`<button class="ev2-btn" id="ev2-copy-public-link">${tt("ev2_btn_quote_link", "客户链接")}</button>`);
      buttons.push(`<button class="ev2-btn ev2-btn-primary" id="ev2-mark-confirmed">${tt("ev2_btn_manual_confirm", "手动确认")}</button>`);
    }
    if (status === "confirmed" && !est.linked_contract_id) {
      buttons.push(`<button class="ev2-btn ev2-btn-primary" id="ev2-generate-contract" ${noCustomer ? "disabled" : ""}>${tt("ev2_btn_generate_contract", "生成合同草稿")}</button>`);
    }
    if (est.linked_contract_id) {
      buttons.push(`<button class="ev2-btn ${linkedMismatch ? "ev2-btn-warn" : ""}" id="ev2-view-contract">${linkedMismatch ? tt("ev2_btn_contract_mismatch", "关联异常") : tt("ev2_btn_view_contract", "查看合同")}</button>`);
    }
    if (noCustomer && status === "confirmed" && !est.linked_contract_id) {
      buttons.push(`<span class="ev2-mini">${tt("ev2_need_customer_for_contract", "需要先关联客户才能生成合同")}</span>`);
    }
    return `<div class="ev2-flow-bar">${buttons.join("")}</div>`;
  }

  function numberOrDefault(value, fallback) {
    if (value === null || value === undefined || value === "") return fallback;
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }

  function debounce(key, fn, wait) {
    if (ev2.debounceTimers[key]) clearTimeout(ev2.debounceTimers[key]);
    ev2.debounceTimers[key] = setTimeout(fn, wait || 400);
  }

  // 调用 v2 API
  async function api(path, opts) {
    opts = opts || {};
    const init = {
      method: opts.method || "GET",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
    };
    if (opts.body !== undefined) init.body = JSON.stringify(opts.body);
    let url = path.startsWith("/") ? path : "/api/v2/" + path;
    // i18n: GET 请求自动追加当前 UI 语言,后端按 lang 返回三语主字段
    if (init.method === "GET") {
      try {
        const s = (typeof state !== "undefined" && state) ? state : window.state;
        const loc = (s && s.locale) || "zh";
        if (loc === "zh" || loc === "en" || loc === "es") {
          url += (url.indexOf("?") >= 0 ? "&" : "?") + "lang=" + loc;
        }
      } catch (e) { /* state 可能尚未就绪 */ }
    }
    const res = await fetch(url, init);
    let data;
    try { data = await res.json(); } catch (e) { data = {}; }
    if (!res.ok) {
      const msg = data.error || ("HTTP " + res.status);
      throw new Error(msg);
    }
    return data;
  }

  // 简易 toast(用 alert 兜底,如果 app.js 暴露了 toast 用它)
  function toast(msg, type) {
    if (window.toast) { window.toast(msg, type); return; }
    if (type === "error") console.error(msg);
    else console.log(msg);
  }

  function confirm2(msg) { return window.confirm(msg); }

  function tt(key, fallback) {
    try {
      // eslint-disable-next-line no-undef
      if (typeof t === "function") {
        const v = t(key);
        if (v && v !== key) return v;
      }
    } catch (e) { /* fallthrough */ }
    if (window.t && typeof window.t === "function") {
      const v = window.t(key);
      if (v && v !== key) return v;
    }
    return fallback || key;
  }

  // 取当前用户(从 app.js 全局)
  // app.js 用顶层 const state,所以是全局变量(不在 window 上)。
  // 我们用 try 读 state,失败再退到 window.state。
  function getAppState() {
    try {
      // eslint-disable-next-line no-undef
      if (typeof state !== "undefined" && state) return state;
    } catch (e) { /* state 不存在 */ }
    return window.state || null;
  }
  function getCurrentUser() {
    const s = getAppState();
    return s && s.user ? s.user : null;
  }

  function isOwner() {
    const u = getCurrentUser();
    return u && (u.role === "owner");
  }

  // ===========================================================================
  // 主入口:接管 estimates 模块的渲染
  // ===========================================================================

  /**
   * 当 state.module === "estimates" 时,被外部调用
   * 把 #content (或类似容器) 的内容替换成我们的标签页结构
   */
  ev2.takeover = async function () {
    ev2.isOwner = isOwner();
    const host = findContentHost();
    if (!host) { console.warn("[estimates_v2] content host not found"); return; }

    host.innerHTML = renderShell();
    bindShellEvents(host);
    await loadGlobalData();
    await switchTab(ev2.activeTab);
  };

  function findContentHost() {
    // 适应 app.js 的渲染容器(常见名称多试几个)
    return $("#crud-view") || $("#crud") || $("#content") || $("#main") ||
           $("main.content") || $(".main-content") || $("main") ||
           $(".main-view") || $("#app-main") ||
           // 最后兜底:找 .layout 里第一个不是侧边栏的容器
           ($(".layout") && $(".layout").querySelector("main, .content, [role='main']"));
  }

  // ===========================================================================
  // 标签页骨架
  // ===========================================================================

  function renderShell() {
    const ownerOnly = ev2.isOwner;
    return `
      <div class="ev2-shell">
        <div class="ev2-tabs">
          <button class="ev2-tab" data-tab="quotes">${tt("ev2_tab_quotes", "报价列表")}</button>
          ${ownerOnly ? `<button class="ev2-tab" data-tab="lib-reno">${tt("ev2_tab_lib_reno", "单价库 · 翻新")}</button>` : ""}
          ${ownerOnly ? `<button class="ev2-tab" data-tab="lib-rebuild">${tt("ev2_tab_lib_rebuild", "单价库 · 重建")}</button>` : ""}
          ${ownerOnly ? `<button class="ev2-tab" data-tab="templates">${tt("ev2_tab_templates", "报价模板")}</button>` : ""}
          ${ownerOnly ? `<button class="ev2-tab" data-tab="sections">${tt("ev2_tab_sections", "分区管理")}</button>` : ""}
        </div>
        <div class="ev2-tab-content" id="ev2-tab-content">
          <div class="ev2-loading">${tt("ev2_loading", "加载中…")}</div>
        </div>
      </div>
    `;
  }

  function bindShellEvents(host) {
    host.addEventListener("click", (e) => {
      const tabBtn = e.target.closest(".ev2-tab");
      if (tabBtn) {
        e.preventDefault();
        switchTab(tabBtn.dataset.tab);
        return;
      }
    });
  }

  async function switchTab(name) {
    ev2.activeTab = name;
    $$(".ev2-tab").forEach(t => t.classList.toggle("active", t.dataset.tab === name));
    const content = $("#ev2-tab-content");
    if (!content) return;
    content.innerHTML = `<div class="ev2-loading">${tt("ev2_loading", "加载中…")}</div>`;
    try {
      switch (name) {
        case "quotes": await renderQuotesTab(content); break;
        case "lib-reno": await renderPriceLibRenoTab(content); break;
        case "lib-rebuild": await renderPriceLibRebuildTab(content); break;
        case "templates": await renderTemplatesTab(content); break;
        case "sections": await renderSectionsTab(content); break;
      }
    } catch (e) {
      content.innerHTML = `<div class="ev2-error">${tt("ev2_load_failed_prefix", "加载失败:")}${escHtml(e.message)}</div>`;
    }
  }

  // ===========================================================================
  // 全局数据加载(切换报价之间共享)
  // ===========================================================================

  async function loadGlobalData() {
    try {
      const [sm, settings, stages] = await Promise.all([
        api("sections-master"),
        api("settings/estimate"),
        api("stage-template-items"),
      ]);
      ev2.sectionsMaster = sm.items || [];
      ev2.settings = settings || {};
      ev2.stageItems = stages.items || [];
    } catch (e) {
      console.warn("[estimates_v2] load global data failed", e);
    }
  }

  // ===========================================================================
  // 标签页 1: 报价列表 + 编辑器
  // ===========================================================================

  async function renderQuotesTab(container) {
    const data = await fetch("/api/estimates", { credentials: "same-origin" }).then(r => r.json());
    ev2.list = Array.isArray(data) ? data : (data.items || []);
    container.innerHTML = `
      <div class="ev2-section">
        <div class="ev2-toolbar">
          <input type="text" class="ev2-search" id="ev2-quote-search" placeholder="${tt("ev2_search_quote_ph", "搜索客户、标题...")}" />
          <button class="ev2-btn ev2-btn-primary" id="ev2-quote-new">${tt("ev2_btn_new_quote", "+ 新建报价")}</button>
        </div>
        <div class="ev2-table-wrap">
          <table class="ev2-table">
            <thead>
              <tr>
                <th>${tt("ev2_col_id", "ID")}</th>
                <th>${tt("ev2_col_title", "标题")}</th>
                <th>${tt("ev2_col_type", "类型")}</th>
                <th>${tt("ev2_col_customer", "客户")}</th>
                <th>${tt("ev2_col_status", "状态")}</th>
                <th>${tt("ev2_col_total", "总价")}</th>
                <th>${tt("ev2_col_updated", "更新")}</th>
                <th>${tt("ev2_col_actions", "操作")}</th>
              </tr>
            </thead>
            <tbody id="ev2-quote-tbody"></tbody>
          </table>
        </div>
        <div class="ev2-empty" id="ev2-quote-empty" style="display:none;">${tt("ev2_quote_empty", "还没有报价。点击右上 \"新建报价\" 开始。")}</div>
      </div>
    `;
    refreshQuoteList();
    $("#ev2-quote-search").addEventListener("input", (e) => {
      debounce("quote-search", () => refreshQuoteList(e.target.value), 300);
    });
    $("#ev2-quote-new").addEventListener("click", onCreateQuote);
  }

  function refreshQuoteList(search) {
    const tbody = $("#ev2-quote-tbody");
    if (!tbody) return;
    const term = (search || "").trim().toLowerCase();
    let list = ev2.list;
    if (term) {
      list = list.filter(r =>
        String(r.title || "").toLowerCase().includes(term) ||
        String(r.customer_name || "").toLowerCase().includes(term)
      );
    }
    if (list.length === 0) {
      tbody.innerHTML = "";
      $("#ev2-quote-empty").style.display = "block";
      return;
    }
    $("#ev2-quote-empty").style.display = "none";
    tbody.innerHTML = list.map(r => {
      const status = String(r.confirm_status || "draft").toLowerCase();
      const linkedMismatch = Number(r.linked_contract_mismatch || 0) === 1;
      const noCustomer = !Number(r.customer_id || 0);
      const flowButtons = [
        status === "draft" || status === "sent" ? `<button class="ev2-btn-mini" data-act="send-customer" data-id="${r.id}">${status === "sent" ? tt("ev2_btn_quote_link", "客户链接") : tt("ev2_btn_send_to_customer", "发送给客户")}</button>` : "",
        status === "sent" ? `<button class="ev2-btn-mini ev2-btn-primary" data-act="mark-confirmed" data-id="${r.id}">${tt("ev2_btn_manual_confirm", "手动确认")}</button>` : "",
        status === "confirmed" && !r.linked_contract_id
          ? `<button class="ev2-btn-mini ev2-btn-primary" data-act="gen-contract" data-id="${r.id}" ${noCustomer ? "disabled" : ""}>${tt("ev2_btn_generate_contract", "生成合同草稿")}</button>`
          : "",
        r.linked_contract_id
          ? `<button class="ev2-btn-mini ${linkedMismatch ? "ev2-btn-warn" : ""}" data-act="view-contract" data-id="${r.id}" data-contract-id="${r.linked_contract_id}">${linkedMismatch ? tt("ev2_btn_contract_mismatch", "关联异常") : tt("ev2_btn_view_contract", "查看合同")}</button>`
          : "",
      ].filter(Boolean).join("");
      return `
      <tr>
        <td>#${r.id}</td>
        <td>${escHtml(r.title || "-")}</td>
        <td>${r.estimate_type === "rebuild" ? tt("ev2_type_rebuild", "重建") : tt("ev2_type_renovation", "翻新")}</td>
        <td>${escHtml(r.customer_name || "-")}</td>
        <td><span class="ev2-status ev2-status-${escHtml(status)}">${escHtml(statusLabel(status))}</span></td>
        <td class="num">${fmtMoney(r.total_amount || 0)}</td>
        <td class="ev2-mini">${escHtml(r.updated_at || "").slice(0, 16)}</td>
        <td>
          <div class="ev2-actions-wrap">
            <button class="ev2-btn-mini" data-act="edit" data-id="${r.id}">${tt("ev2_btn_edit", "编辑")}</button>
            <button class="ev2-btn-mini" data-act="pdf" data-id="${r.id}">PDF</button>
            ${flowButtons}
            <button class="ev2-btn-mini ev2-btn-danger" data-act="delete" data-id="${r.id}">${tt("ev2_btn_delete", "删除")}</button>
          </div>
        </td>
      </tr>
    `;
    }).join("");
    tbody.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = Number(btn.dataset.id);
        if (btn.dataset.act === "edit") openEstimateEditor(id);
        else if (btn.dataset.act === "pdf") openPdfDialog(id);
        else if (btn.dataset.act === "delete") onDeleteQuote(id);
        else if (btn.dataset.act === "send-customer") sendEstimateToCustomer(id);
        else if (btn.dataset.act === "mark-confirmed") markEstimateStatus(id, "confirmed");
        else if (btn.dataset.act === "gen-contract") generateContractFromEstimate(id);
        else if (btn.dataset.act === "view-contract") openLinkedContract(btn.dataset.contractId);
      });
    });
  }

  function showCustomerQuoteLink(publicUrl) {
    if (!publicUrl) return;
    const url = publicUrl.startsWith("http") ? publicUrl : `${window.location.origin}${publicUrl}`;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).catch(() => {});
    }
    window.prompt(tt("ev2_public_quote_link", "客户确认链接"), url);
  }

  async function sendEstimateToCustomer(id, reopenEditor = false) {
    try {
      const res = await api(`/api/estimates/${id}/send-to-customer`, { method: "POST" });
      toast(tt("ev2_quote_sent_link_ready", "客户确认链接已生成"), "success");
      showCustomerQuoteLink(res && (res.public_url || (res.row && res.row.public_url)));
      if (reopenEditor) await openEstimateEditor(id);
      else await renderQuotesTab($("#ev2-tab-content"));
    } catch (e) {
      toast(tt("ev2_flow_failed_prefix", "流程操作失败: ") + e.message, "error");
    }
  }

  async function markEstimateStatus(id, target) {
    const endpoint = {
      sent: "mark-sent",
      confirmed: "mark-confirmed",
      rejected: "mark-rejected",
    }[target];
    if (!endpoint) return;
    try {
      await api(`/api/estimates/${id}/${endpoint}`, { method: "POST" });
      toast(tt("ev2_flow_saved", "状态已更新"), "success");
      await renderQuotesTab($("#ev2-tab-content"));
    } catch (e) {
      toast(tt("ev2_flow_failed_prefix", "流程操作失败: ") + e.message, "error");
    }
  }

  async function generateContractFromEstimate(id) {
    if (!confirm2(tt("ev2_confirm_generate_contract", "确认用这个已确认报价生成合同草稿?合同草稿检查后再发送客户签署。"))) return;
    try {
      const res = await api(`/api/estimates/${id}/generate-contract`, { method: "POST" });
      toast(tt("ev2_contract_generated", "合同已生成"), "success");
      if (res && res.contract && res.contract.id) {
        openLinkedContract(res.contract.id);
      } else {
        await renderQuotesTab($("#ev2-tab-content"));
      }
    } catch (e) {
      toast(tt("ev2_contract_generate_failed_prefix", "生成合同失败: ") + e.message, "error");
    }
  }

  async function openLinkedContract(contractId) {
    const id = Number(contractId || 0);
    if (!id) return;
    if (typeof window.openContractDetail === "function") {
      await window.openContractDetail(id);
      return;
    }
    toast(tt("ev2_contract_open_hint", "合同已生成,请到合同/付款计划查看。"), "success");
  }

  function bindFlowButtons() {
    const est = ev2.currentEstimate;
    if (!est) return;
    $("#ev2-mark-sent")?.addEventListener("click", () => sendEstimateToCustomer(est.id, true));
    $("#ev2-copy-public-link")?.addEventListener("click", () => {
      if (est.public_url) showCustomerQuoteLink(est.public_url);
      else sendEstimateToCustomer(est.id, true);
    });
    $("#ev2-mark-confirmed")?.addEventListener("click", () => markEstimateStatusFromEditor("confirmed"));
    $("#ev2-generate-contract")?.addEventListener("click", () => generateContractFromEstimate(est.id));
    $("#ev2-view-contract")?.addEventListener("click", () => openLinkedContract(est.linked_contract_id));
  }

  async function markEstimateStatusFromEditor(target) {
    const est = ev2.currentEstimate;
    if (!est) return;
    if (target === "sent") {
      await sendEstimateToCustomer(est.id, true);
      return;
    }
    const endpoint = {
      sent: "mark-sent",
      confirmed: "mark-confirmed",
      rejected: "mark-rejected",
    }[target];
    if (!endpoint) return;
    try {
      await api(`/api/estimates/${est.id}/${endpoint}`, { method: "POST" });
      toast(tt("ev2_flow_saved", "状态已更新"), "success");
      await openEstimateEditor(est.id);
    } catch (e) {
      toast(tt("ev2_flow_failed_prefix", "流程操作失败: ") + e.message, "error");
    }
  }

  async function onCreateQuote() {
    const title = window.prompt(tt("ev2_prompt_new_quote_title", "报价标题(可后续修改):"), tt("ev2_default_quote_title", "新建报价"));
    if (!title) return;
    try {
      // 用现有的 /api/estimates POST(走 app.py 的通用 CRUD)
      const res = await fetch("/api/estimates", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, estimate_type: "renovation", status: "Draft", confirm_status: "draft" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || tt("ev2_create_failed_default", "创建失败"));
      const id = data.id || (data.row && data.row.id) || data;
      await renderQuotesTab($("#ev2-tab-content"));
      if (id) openEstimateEditor(Number(id));
    } catch (e) {
      toast(tt("ev2_create_failed_prefix", "创建失败: ") + e.message, "error");
    }
  }

  async function onDeleteQuote(id) {
    const msg = tt("ev2_confirm_delete_quote", "确定删除报价 #{id}?此操作不可恢复。").replace("{id}", id);
    if (!confirm2(msg)) return;
    try {
      await fetch(`/api/estimates/${id}`, { method: "DELETE", credentials: "same-origin" });
      await renderQuotesTab($("#ev2-tab-content"));
    } catch (e) {
      toast(tt("ev2_delete_failed_prefix", "删除失败: ") + e.message, "error");
    }
  }

  // ===========================================================================
  // 报价编辑器
  // ===========================================================================

  async function openEstimateEditor(id) {
    const content = $("#ev2-tab-content");
    content.innerHTML = `<div class="ev2-loading">${tt("ev2_load_quote", "加载报价中…")}</div>`;
    try {
      const est = await api(`estimates/${id}/full`);
      ev2.currentEstimate = est;
      ev2.holdbackOption = computeHoldbackOption(est.payment_milestones || []);
      // 加载模板列表(用于"从模板加载")
      const tplRes = await api("estimate-templates?estimate_type=" + (est.estimate_type || "renovation"));
      ev2.templatesForLoad = tplRes.items || [];
      renderEstimateEditor(content, est);
    } catch (e) {
      content.innerHTML = `<div class="ev2-error">${tt("ev2_load_failed_prefix", "加载失败:")}${escHtml(e.message)}<br/>
        <button class="ev2-btn" onclick="estimatesV2.takeover()">${tt("ev2_back_btn", "← 返回列表")}</button></div>`;
    }
  }

  function computeHoldbackOption(milestones) {
    const hb = (milestones || []).find(m => m.is_holdback);
    if (!hb) return 0;
    return Math.round(hb.amount_pct || 0);
  }

  function renderEstimateEditor(container, est) {
    if (est.estimate_type === "rebuild") {
      renderRebuildEditor(container, est);
    } else {
      renderRenovationEditor(container, est);
    }
  }

  // -------- 翻新报价编辑器 --------
  function renderRenovationEditor(container, est) {
    const settings = ev2.settings || {};
    const markupMin = numberOrDefault(settings.estimate_markup_min, 0);
    const markupMax = numberOrDefault(settings.estimate_markup_max, 25);
    const taxEnabled = Number(est.tax_enabled || 0);
    const taxRate = Number(est.tax_rate || settings.estimate_tax_rate || 9.25);
    const markup = numberOrDefault(est.markup_rate, numberOrDefault(settings.estimate_markup_default, 0));
    const tplOptions = ev2.templatesForLoad
      .map(t => `<option value="${t.id}">${escHtml(t.name)}</option>`).join("");

    container.innerHTML = `
      <div class="ev2-editor">
        <div class="ev2-editor-head">
          <button class="ev2-btn-link" id="ev2-back">${tt("ev2_back_btn", "← 返回列表")}</button>
          <div class="ev2-editor-title">${tt("ev2_editor_title", "编辑报价 #{id}").replace("{id}", est.id)}</div>
          <div class="ev2-editor-actions">
            <button class="ev2-btn" id="ev2-save-meta">${tt("ev2_btn_save_meta", "保存基本信息")}</button>
            <button class="ev2-btn ev2-btn-primary" id="ev2-export-pdf">${tt("ev2_btn_export_pdf", "导出 PDF")}</button>
          </div>
        </div>
        ${flowButtonsHtml(est)}

        <!-- 顶部:客户/项目/类型/模板 -->
        <div class="ev2-card">
          <div class="ev2-grid-4">
            <div>
              <label class="ev2-label">${tt("ev2_label_title", "标题")}</label>
              <input type="text" class="ev2-input" id="ev2-title" value="${escHtml(est.title || "")}" />
            </div>
            <div>
              <label class="ev2-label">${tt("ev2_label_customer", "客户")}</label>
              <div class="ev2-readonly">${est.customer ? `${escHtml(est.customer.name)} · ${escHtml(est.customer.phone || "")}` : "-"}</div>
            </div>
            <div>
              <label class="ev2-label">${tt("ev2_label_quote_type", "报价类型")}</label>
              <select class="ev2-input" id="ev2-est-type">
                <option value="renovation" ${est.estimate_type !== "rebuild" ? "selected" : ""}>${tt("ev2_type_renovation", "翻新")}</option>
                <option value="rebuild" ${est.estimate_type === "rebuild" ? "selected" : ""}>${tt("ev2_type_rebuild", "重建")}</option>
              </select>
            </div>
            <div>
              <label class="ev2-label">${tt("ev2_label_load_template", "从模板加载")}</label>
              <div class="ev2-row">
                <select class="ev2-input" id="ev2-tpl-select">
                  <option value="">${tt("ev2_tpl_no_use", "— 不使用模板 —")}</option>
                  ${tplOptions}
                </select>
                <button class="ev2-btn" id="ev2-tpl-load">${tt("ev2_btn_load", "加载")}</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 分区+明细 -->
        <div class="ev2-sections" id="ev2-sections">
          ${renderSectionsHtml(est.sections || [])}
        </div>

        <!-- 添加分区 -->
        <div class="ev2-add-section-bar">
          <select class="ev2-input ev2-section-select" id="ev2-new-sec-master">
            <option value="">${tt("ev2_section_select_ph", "选择分区类型...")}</option>
            ${ev2.sectionsMaster.map(s => `<option value="${s.id}">${escHtml(s.name || s.name_zh)} · ${escHtml(s.code)}</option>`).join("")}
            <option value="__custom__">${tt("ev2_section_custom_option", "其它 / 自定义")}</option>
          </select>
          <input class="ev2-input" id="ev2-new-sec-custom-name" style="display:none; max-width:260px;" placeholder="${tt("ev2_section_custom_name_ph", "输入自定义分区名")}" />
          <button class="ev2-btn" id="ev2-add-section">${tt("ev2_btn_add_section", "+ 添加分区")}</button>
        </div>

        <!-- 总价计算面板 -->
        <div class="ev2-totals-panel" id="ev2-totals">
          ${renderTotalsHtml(est, markupMin, markupMax, markup, taxEnabled, taxRate)}
        </div>

        <!-- 付款进度 -->
        <div class="ev2-card ev2-payment">
          ${renderPaymentScheduleHtml(est)}
        </div>

        <!-- 底部 PDF 设置 -->
        <div class="ev2-card ev2-pdf-bar">
          <label><input type="checkbox" id="ev2-pdf-show-unit" ${est.pdf_show_unit_price ? "checked" : ""}/> ${tt("ev2_pdf_show_unit", "PDF 显示明细单价")}</label>
          <span class="ev2-divider">|</span>
          <label><input type="checkbox" id="ev2-pdf-show-material" ${est.pdf_show_material ? "checked" : ""}/> ${tt("ev2_pdf_show_material", "显示\"材料\"列")}</label>
          <label><input type="checkbox" id="ev2-pdf-show-labor" ${est.pdf_show_labor ? "checked" : ""}/> ${tt("ev2_pdf_show_labor", "显示\"人工\"列")}</label>
          <span class="ev2-divider">|</span>
          <label><input type="checkbox" id="ev2-pdf-show-pct" ${est.pdf_show_pct ? "checked" : ""}/> ${tt("ev2_pdf_show_pct", "PDF 显示百分比")}</label>
          <label><input type="checkbox" id="ev2-pdf-show-notes" ${est.pdf_show_notes === 0 ? "" : "checked"}/> ${tt("ev2_pdf_show_notes", "PDF 显示备注条款")}</label>
          <span class="ev2-divider">|</span>
          <label>${tt("ev2_pdf_lang_label", "PDF 语言:")}
            <select class="ev2-input ev2-input-sm" id="ev2-pdf-lang">
              <option value="zh" ${est.pdf_language === "zh" ? "selected" : ""}>中文</option>
              <option value="en" ${(est.pdf_language === "en" || !est.pdf_language || (est.pdf_language !== "zh" && est.pdf_language !== "en")) ? "selected" : ""}>English</option>
            </select>
          </label>
          <div class="ev2-pdf-notes-field">
            <label class="ev2-label" for="ev2-pdf-notes-text">${tt("ev2_pdf_notes_label", "PDF 备注 / 说明")}</label>
            <textarea class="ev2-input ev2-pdf-notes-text" id="ev2-pdf-notes-text" rows="4" placeholder="${tt("ev2_pdf_notes_placeholder", "输入这张报价要显示在 PDF 底部的备注。")}">${escHtml(est.pdf_notes_text || "")}</textarea>
          </div>
        </div>
      </div>
    `;
    bindEditorEvents();
    refreshTotals();
  }

  function renderSectionsHtml(sections) {
    if (!sections.length) {
      return `<div class="ev2-empty">${tt("ev2_section_empty", "还没有分区。从模板加载或下方添加分区开始。")}</div>`;
    }
    return sections.map(sec => `
      <div class="ev2-card ev2-section-card" data-sec-id="${sec.id}">
        <div class="ev2-section-head">
          <div class="ev2-section-title">
            <input type="text" class="ev2-input ev2-section-name" value="${escHtml(sec.name)}" data-sec-id="${sec.id}" />
            <span class="ev2-mini">${tt("ev2_unit_count", "{n} 项").replace("{n}", (sec.lines || []).length)}</span>
          </div>
          <div class="ev2-row">
            <button class="ev2-btn-mini" data-act="add-line" data-sec-id="${sec.id}">${tt("ev2_btn_add_line", "+ 添加明细")}</button>
            <button class="ev2-btn-mini" data-act="add-from-lib" data-sec-id="${sec.id}">${tt("ev2_btn_add_from_lib", "从单价库")}</button>
            <button class="ev2-btn-mini ev2-btn-danger" data-act="del-section" data-sec-id="${sec.id}">${tt("ev2_btn_del_section", "删除分区")}</button>
          </div>
        </div>
        <table class="ev2-table ev2-lines-table">
          <thead>
            <tr>
              <th class="col-name">${tt("ev2_col_item", "项目")}</th>
              <th class="col-desc">${tt("ev2_col_desc", "描述")}</th>
              <th class="col-qty">${tt("ev2_col_qty", "数量")}</th>
              <th class="col-unit">${tt("ev2_col_unit", "单位")}</th>
              <th class="col-mat">${tt("ev2_col_material", "材料 $")}</th>
              <th class="col-lab">${tt("ev2_col_labor", "人工 $")}</th>
              <th class="col-sub">${tt("ev2_col_subtotal", "小计")}</th>
              <th class="col-act"></th>
            </tr>
          </thead>
          <tbody>
            ${(sec.lines || []).map(ln => renderLineRow(ln)).join("") || `<tr class="ev2-empty-row"><td colspan="8">${tt("ev2_line_empty_in_section", "这个分区还没有明细行")}</td></tr>`}
          </tbody>
        </table>
        <div class="ev2-section-footer">
          <span class="ev2-mini">${tt("ev2_section_subtotal", "分区合计")}</span>
          <span class="ev2-section-subtotal" data-sec-id="${sec.id}">${fmtMoney(sec.section_subtotal || 0)}</span>
        </div>
      </div>
    `).join("");
  }

  function renderLineRow(ln) {
    const overridden = ln.is_overridden ? "ev2-line-override" : "";
    return `
      <tr class="ev2-line ${overridden}" data-line-id="${ln.id}" data-sec-id="${ln.section_id}">
        <td><input class="ev2-input" data-field="item_name" value="${escHtml(ln.item_name || "")}" /></td>
        <td><input class="ev2-input" data-field="description" value="${escHtml(ln.description || "")}" /></td>
        <td><input class="ev2-input ev2-input-num" data-field="quantity" value="${escHtml(ln.quantity || 0)}" /></td>
        <td><input class="ev2-input ev2-input-sm" data-field="unit" value="${escHtml(ln.unit || "")}" /></td>
        <td><input class="ev2-input ev2-input-num" data-field="material_unit_price" value="${escHtml(ln.material_unit_price || 0)}" /></td>
        <td><input class="ev2-input ev2-input-num" data-field="labor_unit_price" value="${escHtml(ln.labor_unit_price || 0)}" /></td>
        <td class="num ev2-line-subtotal">${fmtMoney(ln.line_subtotal || 0)}</td>
        <td><button class="ev2-btn-mini ev2-btn-danger" data-act="del-line" data-line-id="${ln.id}">×</button></td>
      </tr>
    `;
  }

  function renderTotalsHtml(est, markupMin, markupMax, markup, taxEnabled, taxRate) {
    const subtotal = est.subtotal || 0;
    const markupAmt = subtotal * markup / 100;
    const afterMarkup = subtotal + markupAmt;
    const taxAmt = taxEnabled ? afterMarkup * taxRate / 100 : 0;
    const manualAdjustment = numberOrDefault(est.manual_adjustment, 0);
    const total = est.total_amount || 0;
    return `
      <div class="ev2-totals-row"><span>${tt("ev2_total_subtotal", "明细小计")}</span><span class="num" id="ev2-t-subtotal">${fmtMoney(subtotal)}</span></div>
      <div class="ev2-totals-row">
        <span>${tt("ev2_total_markup", "加成率 (markup)")} <span class="ev2-mini">[${markupMin}%–${markupMax}%]</span></span>
        <span class="ev2-row">
          <input type="range" min="${markupMin}" max="${markupMax}" step="0.5" value="${markup}" id="ev2-markup-range" class="ev2-range" />
          <span class="num" id="ev2-t-markup">${markup}% · ${fmtMoney(markupAmt)}</span>
        </span>
      </div>
      <div class="ev2-totals-row">
        <span><label><input type="checkbox" id="ev2-tax-toggle" ${taxEnabled ? "checked" : ""}/> ${tt("ev2_total_tax", "税")} (${taxRate}%)</label></span>
        <span class="num" id="ev2-t-tax">${taxEnabled ? fmtMoney(taxAmt) : "—"}</span>
      </div>
      <div class="ev2-totals-row">
        <span>${tt("ev2_total_manual_adjustment", "人工调整")}</span>
        <span class="ev2-row">
          <input type="number" step="1" id="ev2-manual-adjustment" class="ev2-input ev2-input-num" value="${escHtml(manualAdjustment)}" />
          <span class="num" id="ev2-t-manual-adjustment">${fmtMoney(manualAdjustment)}</span>
        </span>
      </div>
      <div class="ev2-totals-row ev2-totals-grand"><span>${tt("ev2_total_grand", "总价")}</span><span class="num" id="ev2-t-grand">${fmtMoney(total)}</span></div>
    `;
  }

  function renderPaymentScheduleHtml(est) {
    const ms = est.payment_milestones || [];
    const stageOpts = renderStageOptions();
    const total = est.total_amount || 0;
    const sumPct = ms.reduce((s, m) => s + (Number(m.amount_pct) || 0), 0);
    const okPct = Math.abs(sumPct - 100) < 0.5;

    return `
      <div class="ev2-payment-head">
        <div class="ev2-section-title-text">${tt("ev2_payment_title", "付款进度")}</div>
        <div class="ev2-payment-controls">
          <span class="ev2-mini">${tt("ev2_holdback_label", "完工后留款:")}</span>
          <label><input type="radio" name="ev2-hb" value="0" ${ev2.holdbackOption === 0 ? "checked" : ""}/> ${tt("ev2_holdback_none", "不留")}</label>
          <label><input type="radio" name="ev2-hb" value="5" ${ev2.holdbackOption === 5 ? "checked" : ""}/> 5%</label>
          <label><input type="radio" name="ev2-hb" value="10" ${ev2.holdbackOption === 10 ? "checked" : ""}/> 10%</label>
        </div>
      </div>
      <table class="ev2-table ev2-payment-table">
        <thead>
          <tr>
            <th class="col-no">#</th>
            <th class="col-name">${tt("ev2_pm_col_name", "节点名称")}</th>
            <th class="col-stage">${tt("ev2_pm_col_stage", "关联施工阶段")}</th>
            <th class="col-pct">${tt("ev2_pm_col_pct", "百分比")}</th>
            <th class="col-amt">${tt("ev2_pm_col_amt", "金额")}</th>
            <th class="col-act"></th>
          </tr>
        </thead>
        <tbody id="ev2-pm-tbody">
          ${ms.map((m, idx) => renderPaymentRow(m, idx, stageOpts, total)).join("") ||
            `<tr class="ev2-empty-row"><td colspan="6">${tt("ev2_pm_empty", "还没有付款节点")}</td></tr>`}
        </tbody>
      </table>
      <div class="ev2-row" style="margin-top:10px;">
        <button class="ev2-btn-mini" id="ev2-pm-add">${tt("ev2_btn_add_milestone", "+ 添加节点")}</button>
        <button class="ev2-btn-mini" id="ev2-pm-save" style="margin-left:auto;">${tt("ev2_btn_save_payment", "保存付款进度")}</button>
      </div>
      <div class="ev2-payment-footer">
        <span>${tt("ev2_pm_total_label", "合计百分比 / 合计金额")}</span>
        <span class="ev2-row">
          <span class="ev2-pill ${okPct ? 'ev2-pill-ok' : 'ev2-pill-warn'}" id="ev2-pm-pct-pill">${sumPct.toFixed(1)}% ${okPct ? '✓' : '⚠'}</span>
          <span class="num">${fmtMoney(total * sumPct / 100)}</span>
        </span>
      </div>
    `;
  }

  function renderStageOptions() {
    const groups = new Map();
    (ev2.stageItems || []).forEach(s => {
      const label = s.template_name || "阶段模板";
      if (!groups.has(label)) groups.set(label, []);
      groups.get(label).push(s);
    });
    return Array.from(groups.entries()).map(([label, items]) => {
      const opts = items.map(s => `<option value="${s.id}">${escHtml(s.step_name || "")}</option>`).join("");
      return `<optgroup label="${escHtml(label)}">${opts}</optgroup>`;
    }).join("");
  }

  function renderPaymentRow(m, idx, stageOpts, total) {
    const amt = total * (Number(m.amount_pct) || 0) / 100;
    const isHb = m.is_holdback ? "ev2-hb-row" : "";
    const lock = m.is_holdback ? "disabled" : "";
    const isCustomStage = !!String(m.custom_stage_name || "").trim();
    const customStyle = isCustomStage ? "" : "display:none;";
    return `
      <tr class="ev2-pm-row ${isHb}" data-idx="${idx}">
        <td class="col-no">${m.is_holdback ? "★" : (idx + 1)}</td>
        <td><input class="ev2-input" data-field="name" value="${escHtml(m.name || "")}" ${lock}/></td>
        <td>
          <select class="ev2-input" data-field="trigger_stage_template_item_id" ${lock}>
            <option value="">${tt("ev2_pm_select_stage", "— 选择施工阶段 —")}</option>
            <option value="__custom__">${tt("ev2_pm_custom_stage", "+ 自定义阶段")}</option>
            ${stageOpts}
          </select>
          <input class="ev2-input" data-field="custom_stage_name" value="${escHtml(m.custom_stage_name || "")}" placeholder="${tt("ev2_pm_custom_stage_placeholder", "输入自定义阶段")}" style="margin-top:6px;${customStyle}" ${lock}/>
        </td>
        <td><input class="ev2-input ev2-input-num" data-field="amount_pct" value="${m.amount_pct || 0}" ${lock}/></td>
        <td class="num">${fmtMoney(amt)}</td>
        <td><button class="ev2-btn-mini ev2-btn-danger" data-act="del-pm" data-idx="${idx}" ${lock}>×</button></td>
      </tr>
    `;
  }

  // ============================ 编辑器事件绑定 ============================

  function bindEditorEvents() {
    // 返回
    $("#ev2-back").addEventListener("click", () => {
      ev2.currentEstimate = null;
      switchTab("quotes");
    });
    // 保存基本信息
    $("#ev2-save-meta").addEventListener("click", saveEstimateMeta);
    // 导出 PDF
    const pdfBtn = $("#ev2-export-pdf");
    if (pdfBtn) pdfBtn.addEventListener("click", () => openPdfDialog(ev2.currentEstimate.id));
    bindFlowButtons();
    // 类型切换
    $("#ev2-est-type").addEventListener("change", async (e) => {
      const est = ev2.currentEstimate;
      est.estimate_type = e.target.value;
      // 重建 vs 翻新切换 → 整页重渲染
      renderEstimateEditor($("#ev2-tab-content"), est);
      await refreshFromServer();
    });
    // 加载模板
    $("#ev2-tpl-load").addEventListener("click", onLoadTemplate);
    // 加分区
    $("#ev2-new-sec-master").addEventListener("change", onNewSectionTypeChange);
    $("#ev2-new-sec-custom-name").addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        onAddSection();
      }
    });
    $("#ev2-add-section").addEventListener("click", onAddSection);
    // 委派:分区/明细行的事件
    $("#ev2-sections").addEventListener("click", onSectionAreaClick);
    $("#ev2-sections").addEventListener("change", onLineFieldChange);
    $("#ev2-sections").addEventListener("input", onSectionNameInput);
    // 总价控件
    const range = $("#ev2-markup-range");
    if (range) range.addEventListener("input", onMarkupInput);
    const taxToggle = $("#ev2-tax-toggle");
    if (taxToggle) taxToggle.addEventListener("change", onTaxToggle);
    const manualAdjustment = $("#ev2-manual-adjustment");
    if (manualAdjustment) manualAdjustment.addEventListener("input", onManualAdjustmentInput);
    // 付款进度
    $$('input[name="ev2-hb"]').forEach(r => r.addEventListener("change", onHoldbackChange));
    $("#ev2-pm-add").addEventListener("click", onAddMilestone);
    $("#ev2-pm-save").addEventListener("click", onSavePaymentMilestones);
    $("#ev2-pm-tbody").addEventListener("click", onPmAreaClick);
    $("#ev2-pm-tbody").addEventListener("input", onPmAreaInput);
    $("#ev2-pm-tbody").addEventListener("change", onPmAreaInput);
    // 同步 stage 下拉框选中值
    syncStageDropdowns();
    // PDF 设置
    ["ev2-pdf-show-unit", "ev2-pdf-show-material", "ev2-pdf-show-labor",
     "ev2-pdf-show-pct", "ev2-pdf-show-notes", "ev2-pdf-lang"].forEach(id => {
      const el = $("#" + id);
      if (el) el.addEventListener("change", onPdfSettingChange);
    });
    const pdfNotesText = $("#ev2-pdf-notes-text");
    if (pdfNotesText) pdfNotesText.addEventListener("input", onPdfSettingChange);
  }

  function syncStageDropdowns() {
    const ms = ev2.currentEstimate.payment_milestones || [];
    $$(".ev2-pm-row").forEach((row, idx) => {
      const m = ms[idx];
      if (!m) return;
      const sel = row.querySelector('[data-field="trigger_stage_template_item_id"]');
      const customInput = row.querySelector('[data-field="custom_stage_name"]');
      const customName = String(m.custom_stage_name || "").trim();
      if (sel && customName) {
        sel.value = "__custom__";
      } else if (sel && m.trigger_stage_template_item_id) {
        sel.value = String(m.trigger_stage_template_item_id);
      }
      if (customInput) {
        customInput.style.display = customName ? "" : "none";
      }
    });
  }

  // ============================ 导出 PDF ============================

  function openPdfDialog(estimateId) {
    if (!estimateId) return;
    // 直接读底部"PDF 语言"下拉的值;没值或非法值兜底为 en
    let lang = "en";
    const sel = document.getElementById("ev2-pdf-lang");
    if (sel && sel.value) {
      const v = String(sel.value).toLowerCase();
      if (v === "zh" || v === "en") {
        lang = v;
      }
    }
    const url = `/api/v2/estimates/${estimateId}/pdf?lang=${lang}`  /* P2F2_PATCH_APPLIED: removed auto_print so user reviews before printing */;
    window.open(url, "_blank");
  }

  // ============================ /导出 PDF ============================

  // ============================ 编辑器:基本信息保存 ============================

  async function saveEstimateMeta() {
    const est = ev2.currentEstimate;
    const title = $("#ev2-title").value.trim();
    const estType = $("#ev2-est-type").value;
    try {
      await fetch(`/api/estimates/${est.id}`, {
        method: "PUT",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, estimate_type: estType }),
      });
      toast(tt("ev2_saved", "已保存"), "success");
    } catch (e) {
      toast(tt("ev2_save_failed_prefix", "保存失败: ") + e.message, "error");
    }
  }

  // ============================ 编辑器:加载模板 ============================

  async function onLoadTemplate() {
    const tplId = Number($("#ev2-tpl-select").value);
    if (!tplId) { toast(tt("ev2_select_template_first", "请先选择模板"), "error"); return; }
    if (!confirm2(tt("ev2_confirm_load_template", "加载模板会清空当前所有分区和明细,确定?"))) return;
    const est = ev2.currentEstimate;
    try {
      await api(`estimates/${est.id}/load-template/${tplId}`, { method: "POST" });
      await refreshFromServer();
      toast(tt("ev2_template_loaded", "模板已加载"), "success");
    } catch (e) {
      toast(tt("ev2_load_failed_prefix", "加载失败: ") + e.message, "error");
    }
  }

  // ============================ 编辑器:分区操作 ============================

  function onNewSectionTypeChange() {
    const sel = $("#ev2-new-sec-master");
    const input = $("#ev2-new-sec-custom-name");
    if (!sel || !input) return;
    const isCustom = sel.value === "__custom__";
    input.style.display = isCustom ? "" : "none";
    if (isCustom) input.focus();
  }

  async function onAddSection() {
    const sectionValue = $("#ev2-new-sec-master").value;
    const isCustom = sectionValue === "__custom__";
    const customName = ($("#ev2-new-sec-custom-name")?.value || "").trim();
    const masterId = isCustom ? 0 : Number(sectionValue);
    if (isCustom && !customName) {
      toast(tt("ev2_custom_section_name_required", "请输入自定义分区名"), "error");
      $("#ev2-new-sec-custom-name")?.focus();
      return;
    }
    if (!isCustom && !masterId) {
      toast(tt("ev2_select_section_first", "请先选择分区类型"), "error");
      return;
    }
    const est = ev2.currentEstimate;
    try {
      const body = isCustom ? { name: customName } : { master_id: masterId };
      await api(`estimates/${est.id}/sections`, {
        method: "POST", body,
      });
      if (isCustom) {
        $("#ev2-new-sec-custom-name").value = "";
        $("#ev2-new-sec-master").value = "";
        onNewSectionTypeChange();
      }
      await refreshFromServer();
    } catch (e) {
      toast(tt("ev2_add_failed_prefix", "添加失败: ") + e.message, "error");
    }
  }

  function onSectionAreaClick(e) {
    const btn = e.target.closest("button[data-act]");
    if (!btn) return;
    const act = btn.dataset.act;
    const secId = Number(btn.dataset.secId);
    const lineId = Number(btn.dataset.lineId);
    if (act === "add-line") onAddLine(secId);
    else if (act === "del-line") onDeleteLine(lineId);
    else if (act === "del-section") onDeleteSection(secId);
    else if (act === "add-from-lib") onAddFromLibrary(secId);
  }

  function onSectionNameInput(e) {
    if (!e.target.classList.contains("ev2-section-name")) return;
    const secId = Number(e.target.dataset.secId);
    const name = e.target.value;
    debounce("sec-name-" + secId, async () => {
      const est = ev2.currentEstimate;
      try {
        await api(`estimates/${est.id}/sections/${secId}`, { method: "PUT", body: { name } });
      } catch (e) { /* swallow */ }
    }, 600);
  }

  async function onDeleteSection(secId) {
    if (!confirm2(tt("ev2_confirm_delete_section", "确定删除这个分区?所有明细行会一起删除。"))) return;
    const est = ev2.currentEstimate;
    try {
      await api(`estimates/${est.id}/sections/${secId}`, { method: "DELETE" });
      await refreshFromServer();
    } catch (e) {
      toast(tt("ev2_delete_failed_prefix", "删除失败: ") + e.message, "error");
    }
  }

  async function onAddLine(secId) {
    const est = ev2.currentEstimate;
    try {
      await api(`estimates/${est.id}/lines`, {
        method: "POST",
        body: { section_id: secId, item_name: "新明细", quantity: 1, unit: "项" },
      });
      await refreshFromServer();
    } catch (e) {
      toast(tt("ev2_add_failed_prefix", "添加失败: ") + e.message, "error");
    }
  }

  async function onDeleteLine(lineId) {
    const est = ev2.currentEstimate;
    try {
      await api(`estimates/${est.id}/lines/${lineId}`, { method: "DELETE" });
      await refreshFromServer();
    } catch (e) {
      toast(tt("ev2_delete_failed_prefix", "删除失败: ") + e.message, "error");
    }
  }

  function onLineFieldChange(e) {
    const input = e.target;
    if (!input.matches("input[data-field]")) return;
    const tr = input.closest(".ev2-line");
    if (!tr) return;
    const lineId = Number(tr.dataset.lineId);
    const field = input.dataset.field;
    const val = input.value;
    debounce("line-" + lineId, async () => {
      const est = ev2.currentEstimate;
      const body = { [field]: val };
      // 如果改了价格,弹出留痕原因输入
      if (field === "material_unit_price" || field === "labor_unit_price") {
        const reason = window.prompt(tt("ev2_prompt_price_override_reason", "修改单价留痕(可选填理由,留空跳过):"));
        if (reason && reason.trim()) {
          body.is_overridden = true;
          body.override_reason = reason.trim();
        }
      }
      try {
        await api(`estimates/${est.id}/lines/${lineId}`, { method: "PUT", body });
        // 不整页刷,只刷小计和总价
        const refreshed = await api(`estimates/${est.id}/full`);
        ev2.currentEstimate = refreshed;
        // 局部更新这一行的小计
        const sec = (refreshed.sections || []).find(s => s.id === Number(tr.dataset.secId));
        if (sec) {
          const ln = (sec.lines || []).find(l => l.id === lineId);
          if (ln) {
            const subEl = tr.querySelector(".ev2-line-subtotal");
            if (subEl) subEl.textContent = fmtMoney(ln.line_subtotal || 0);
          }
          const subSum = $(`.ev2-section-subtotal[data-sec-id="${sec.id}"]`);
          if (subSum) subSum.textContent = fmtMoney(sec.section_subtotal || 0);
        }
        refreshTotals();
      } catch (err) {
        toast(tt("ev2_update_failed_prefix", "更新失败: ") + err.message, "error");
      }
    }, 600);
  }

  // ============================ 编辑器:总价更新 ============================

  function refreshTotals() {
    const est = ev2.currentEstimate;
    if (!est) return;
    const settings = ev2.settings || {};
    const markupMin = numberOrDefault(settings.estimate_markup_min, 0);
    const markupMax = numberOrDefault(settings.estimate_markup_max, 25);
    const range = $("#ev2-markup-range");
    const markup = range ? Number(range.value) : numberOrDefault(est.markup_rate, numberOrDefault(settings.estimate_markup_default, 0));
    const tax = $("#ev2-tax-toggle");
    const taxEnabled = tax ? (tax.checked ? 1 : 0) : Number(est.tax_enabled || 0);
    const taxRate = Number(est.tax_rate || settings.estimate_tax_rate || 9.25);

    const subtotal = est.subtotal || 0;
    const markupAmt = subtotal * markup / 100;
    const afterMarkup = subtotal + markupAmt;
    const taxAmt = taxEnabled ? afterMarkup * taxRate / 100 : 0;
    const manualAdjustmentInput = $("#ev2-manual-adjustment");
    const manualAdjustment = manualAdjustmentInput ? Number(manualAdjustmentInput.value || 0) : numberOrDefault(est.manual_adjustment, 0);
    const total = est.total_amount || 0;

    $("#ev2-t-subtotal") && ($("#ev2-t-subtotal").textContent = fmtMoney(subtotal));
    $("#ev2-t-markup") && ($("#ev2-t-markup").textContent = `${markup}% · ${fmtMoney(markupAmt)}`);
    $("#ev2-t-tax") && ($("#ev2-t-tax").textContent = taxEnabled ? fmtMoney(taxAmt) : "—");
    $("#ev2-t-manual-adjustment") && ($("#ev2-t-manual-adjustment").textContent = fmtMoney(manualAdjustment));
    $("#ev2-t-grand") && ($("#ev2-t-grand").textContent = fmtMoney(total));
    refreshPaymentTotals();
  }

  function onMarkupInput(e) {
    const v = Number(e.target.value);
    const subtotal = ev2.currentEstimate.subtotal || 0;
    $("#ev2-t-markup").textContent = `${v}% · ${fmtMoney(subtotal * v / 100)}`;
    debounce("markup", async () => {
      const est = ev2.currentEstimate;
      try {
        await fetch(`/api/estimates/${est.id}`, {
          method: "PUT",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ markup_rate: v }),
        });
        await api(`estimates/${est.id}/recalc`, { method: "POST" });
        await refreshTotalsFromServer();
      } catch (err) { /* swallow */ }
    }, 500);
  }

  function onTaxToggle(e) {
    const checked = e.target.checked ? 1 : 0;
    ev2.currentEstimate.tax_enabled = checked;
    debounce("tax", async () => {
      const est = ev2.currentEstimate;
      try {
        await fetch(`/api/estimates/${est.id}`, {
          method: "PUT",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tax_enabled: checked, tax_rate: Number(ev2.settings.estimate_tax_rate || 9.25) }),
        });
        await api(`estimates/${est.id}/recalc`, { method: "POST" });
        await refreshTotalsFromServer();
      } catch (err) { /* swallow */ }
    }, 200);
  }

  function onManualAdjustmentInput(e) {
    const v = Number(e.target.value || 0);
    $("#ev2-t-manual-adjustment").textContent = fmtMoney(v);
    debounce("manual-adjustment", async () => {
      const est = ev2.currentEstimate;
      try {
        await fetch(`/api/estimates/${est.id}`, {
          method: "PUT",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ manual_adjustment: v }),
        });
        await api(`estimates/${est.id}/recalc`, { method: "POST" });
        await refreshTotalsFromServer();
      } catch (err) { /* swallow */ }
    }, 500);
  }

  async function refreshTotalsFromServer() {
    const est = ev2.currentEstimate;
    try {
      const refreshed = await api(`estimates/${est.id}/full`);
      ev2.currentEstimate = refreshed;
      refreshTotals();
    } catch (e) { /* swallow */ }
  }

  async function refreshFromServer() {
    const est = ev2.currentEstimate;
    if (!est) return;
    const refreshed = await api(`estimates/${est.id}/full`);
    ev2.currentEstimate = refreshed;
    ev2.holdbackOption = computeHoldbackOption(refreshed.payment_milestones || []);
    renderEstimateEditor($("#ev2-tab-content"), refreshed);
  }

  // ============================ 编辑器:付款进度 ============================

  function onHoldbackChange(e) {
    ev2.holdbackOption = Number(e.target.value);
    const est = ev2.currentEstimate;
    let ms = (est.payment_milestones || []).filter(m => !m.is_holdback);
    // 重新分配前面节点
    if (ms.length === 0) {
      // 默认 4 节点
      ms = [
        { name: "签约首付", amount_pct: 15, trigger_type: "signing", is_holdback: 0 },
        { name: "拆除完成", amount_pct: 25, trigger_type: "stage", is_holdback: 0 },
        { name: "安装完成", amount_pct: 40, trigger_type: "stage", is_holdback: 0 },
        { name: "完工验收", amount_pct: 20, trigger_type: "stage", is_holdback: 0 },
      ];
    }
    const remaining = 100 - ev2.holdbackOption;
    // 等比例缩放
    const currentSum = ms.reduce((s, m) => s + (Number(m.amount_pct) || 0), 0) || 1;
    ms.forEach(m => { m.amount_pct = Math.round((Number(m.amount_pct) || 0) * remaining / currentSum * 10) / 10; });
    if (ev2.holdbackOption > 0) {
      ms.push({
        name: "完工后收",
        amount_pct: ev2.holdbackOption,
        trigger_type: "completion_immediate",
        is_holdback: 1,
      });
    }
    est.payment_milestones = ms;
    rerenderPaymentSection();
  }

  function rerenderPaymentSection() {
    const card = $(".ev2-payment");
    if (!card) return;
    card.innerHTML = renderPaymentScheduleHtml(ev2.currentEstimate);
    // 重新绑定
    $$('input[name="ev2-hb"]').forEach(r => r.addEventListener("change", onHoldbackChange));
    $("#ev2-pm-add").addEventListener("click", onAddMilestone);
    $("#ev2-pm-save").addEventListener("click", onSavePaymentMilestones);
    $("#ev2-pm-tbody").addEventListener("click", onPmAreaClick);
    $("#ev2-pm-tbody").addEventListener("input", onPmAreaInput);
    $("#ev2-pm-tbody").addEventListener("change", onPmAreaInput);
    syncStageDropdowns();
  }

  function refreshPaymentTotals() {
    const est = ev2.currentEstimate;
    if (!est) return;
    const ms = est.payment_milestones || [];
    const total = est.total_amount || 0;
    $$(".ev2-pm-row").forEach((row, idx) => {
      const m = ms[idx];
      if (!m) return;
      const pctInput = row.querySelector('[data-field="amount_pct"]');
      if (pctInput) m.amount_pct = Number(pctInput.value) || 0;
      const amtCell = row.querySelector("td.num");
      if (amtCell) amtCell.textContent = fmtMoney(total * (Number(m.amount_pct) || 0) / 100);
    });
    const sum = ms.reduce((s, m) => s + (Number(m.amount_pct) || 0), 0);
    const ok = Math.abs(sum - 100) < 0.5;
    const pill = $("#ev2-pm-pct-pill");
    if (pill) {
      pill.textContent = `${sum.toFixed(1)}% ${ok ? "✓" : "⚠"}`;
      pill.className = "ev2-pill " + (ok ? "ev2-pill-ok" : "ev2-pill-warn");
    }
  }

  function onAddMilestone() {
    const est = ev2.currentEstimate;
    const ms = est.payment_milestones || [];
    // 在 holdback 之前插
    const hbIdx = ms.findIndex(m => m.is_holdback);
    const newM = { name: "新节点", amount_pct: 0, trigger_type: "stage", trigger_stage_template_item_id: null, custom_stage_name: "", is_holdback: 0 };
    if (hbIdx >= 0) ms.splice(hbIdx, 0, newM);
    else ms.push(newM);
    est.payment_milestones = ms;
    rerenderPaymentSection();
  }

  function onPmAreaClick(e) {
    const btn = e.target.closest('button[data-act="del-pm"]');
    if (!btn) return;
    const idx = Number(btn.dataset.idx);
    const ms = ev2.currentEstimate.payment_milestones || [];
    if (idx >= 0 && idx < ms.length) {
      ms.splice(idx, 1);
      ev2.currentEstimate.payment_milestones = ms;
      rerenderPaymentSection();
    }
  }

  function onPmAreaInput(e) {
    const input = e.target;
    if (!input.matches("[data-field]")) return;
    const row = input.closest(".ev2-pm-row");
    if (!row) return;
    const idx = Number(row.dataset.idx);
    const ms = ev2.currentEstimate.payment_milestones || [];
    if (idx >= 0 && idx < ms.length) {
      const f = input.dataset.field;
      let v = input.value;
      if (f === "amount_pct") v = Number(v) || 0;
      if (f === "trigger_stage_template_item_id") {
        const customInput = row.querySelector('[data-field="custom_stage_name"]');
        if (v === "__custom__") {
          ms[idx].trigger_stage_template_item_id = null;
          ms[idx].custom_stage_name = customInput ? customInput.value : (ms[idx].custom_stage_name || "");
          if (customInput) customInput.style.display = "";
          refreshPaymentTotals();
          return;
        }
        if (customInput) {
          customInput.value = "";
          customInput.style.display = "none";
        }
        ms[idx].custom_stage_name = "";
        v = v ? Number(v) : null;
      }
      if (f === "custom_stage_name") {
        ms[idx].custom_stage_name = v;
        ms[idx].trigger_stage_template_item_id = null;
        const sel = row.querySelector('[data-field="trigger_stage_template_item_id"]');
        if (sel) sel.value = "__custom__";
        refreshPaymentTotals();
        return;
      }
      ms[idx][f] = v;
      refreshPaymentTotals();
    }
  }

  async function onSavePaymentMilestones() {
    const est = ev2.currentEstimate;
    const ms = est.payment_milestones || [];
    const sum = ms.reduce((s, m) => s + (Number(m.amount_pct) || 0), 0);
    if (Math.abs(sum - 100) > 0.5) {
      const msg = tt("ev2_confirm_pct_not_100", "合计百分比是 {pct}%,不等于 100%。仍要保存吗?").replace("{pct}", sum.toFixed(1));
      if (!confirm2(msg)) return;
    }
    try {
      await api(`estimates/${est.id}/payment-milestones`, {
        method: "PUT",
        body: { items: ms },
      });
      toast(tt("ev2_payment_saved", "付款进度已保存"), "success");
    } catch (e) {
      toast(tt("ev2_save_failed_prefix", "保存失败: ") + e.message, "error");
    }
  }

  // ============================ 编辑器:从单价库添加 ============================

  async function onAddFromLibrary(secId) {
    // 简易选择器:弹一个 prompt 让用户输入 SKU 或 ID
    // 后续改成模态框
    const allLib = ev2.priceLib.length ? ev2.priceLib : (await api("price-library")).items;
    ev2.priceLib = allLib;
    const opts = allLib.map(p => `${p.sku || ("#" + p.id)} - ${p.item_name}`).join("\n");
    const promptMsg = tt("ev2_prompt_select_lib_item", "选择单价库项 (输入 SKU 或 ID):\n\n{opts}").replace("{opts}", opts.slice(0, 800));
    const choice = window.prompt(promptMsg, "");
    if (!choice) return;
    const item = allLib.find(p => p.sku === choice.trim() || String(p.id) === choice.trim());
    if (!item) { toast(tt("ev2_lib_item_not_found", "没找到这一项"), "error"); return; }
    const est = ev2.currentEstimate;
    try {
      await api(`estimates/${est.id}/lines`, {
        method: "POST",
        body: {
          section_id: secId,
          price_library_id: item.id,
          item_name: item.item_name,
          description: item.description || "",
          unit: item.unit,
          quantity: item.default_qty || 1,
          material_unit_price: item.material_unit_price || 0,
          labor_unit_price: item.labor_unit_price || 0,
        },
      });
      await refreshFromServer();
    } catch (e) {
      toast(tt("ev2_add_failed_prefix", "添加失败: ") + e.message, "error");
    }
  }

  // ============================ 编辑器:PDF 设置 ============================

  function onPdfSettingChange() {
    const est = ev2.currentEstimate;
    const body = {
      pdf_show_unit_price: $("#ev2-pdf-show-unit").checked ? 1 : 0,
      pdf_show_material: $("#ev2-pdf-show-material").checked ? 1 : 0,
      pdf_show_labor: $("#ev2-pdf-show-labor").checked ? 1 : 0,
      pdf_show_pct: $("#ev2-pdf-show-pct").checked ? 1 : 0,
      pdf_show_notes: $("#ev2-pdf-show-notes").checked ? 1 : 0,
      pdf_notes_text: $("#ev2-pdf-notes-text") ? $("#ev2-pdf-notes-text").value : "",
      pdf_language: $("#ev2-pdf-lang").value,
    };
    // 同步到当前 estimate 对象,这样导出 PDF 时立刻生效
    est.pdf_show_unit_price = body.pdf_show_unit_price;
    est.pdf_show_material = body.pdf_show_material;
    est.pdf_show_labor = body.pdf_show_labor;
    est.pdf_show_pct = body.pdf_show_pct;
    est.pdf_show_notes = body.pdf_show_notes;
    est.pdf_notes_text = body.pdf_notes_text;
    est.pdf_language = body.pdf_language;
    debounce("pdf", async () => {
      try {
        await api(`estimates/${est.id}/pdf-options`, { method: "PUT", body });
      } catch (e) {
        toast(tt("ev2_pdf_save_failed_prefix", "保存 PDF 设置失败: ") + e.message, "error");
      }
    }, 400);
  }

  // -------- 重建报价编辑器(简化版,只占位) --------
  function renderRebuildEditor(container, est) {
    container.innerHTML = `
      <div class="ev2-editor">
        <div class="ev2-editor-head">
          <button class="ev2-btn-link" id="ev2-back">${tt("ev2_back_btn", "← 返回列表")}</button>
          <div class="ev2-editor-title">${tt("ev2_rebuild_editor_title", "重建报价 #{id}").replace("{id}", est.id)}</div>
        </div>
        <div class="ev2-card">
          <p>${tt("ev2_rebuild_placeholder_1", "重建报价编辑页将在步骤 1.5 实现。")}</p>
          <p>${tt("ev2_rebuild_placeholder_2", "当前类型可在顶部切换回\"翻新\"使用完整功能。")}</p>
          <button class="ev2-btn" id="ev2-back-to-reno">${tt("ev2_btn_back_to_reno", "切回翻新")}</button>
        </div>
      </div>
    `;
    $("#ev2-back").addEventListener("click", () => switchTab("quotes"));
    bindFlowButtons();
    $("#ev2-back-to-reno").addEventListener("click", async () => {
      await fetch(`/api/estimates/${est.id}`, {
        method: "PUT",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estimate_type: "renovation" }),
      });
      openEstimateEditor(est.id);
    });
  }

  // ===========================================================================
  // 标签页 2: 单价库 - 翻新
  // ===========================================================================

  async function renderPriceLibRenoTab(container) {
    const data = await api("price-library");
    ev2.priceLib = data.items || [];
    container.innerHTML = `
      <div class="ev2-section">
        <div class="ev2-toolbar">
          <input type="text" class="ev2-search" id="ev2-pl-search" placeholder="${tt("ev2_pl_search_ph", "搜索 SKU、项目、描述、标签...")}" />
          <select class="ev2-input ev2-input-sm" id="ev2-pl-section-filter">
            <option value="">${tt("ev2_pl_filter_all_sections", "所有分区")}</option>
            ${ev2.sectionsMaster.map(s => `<option value="${s.id}">${escHtml(s.name || s.name_zh)}</option>`).join("")}
          </select>
          <button class="ev2-btn ev2-btn-primary" id="ev2-pl-new">${tt("ev2_pl_btn_new", "+ 新增项目")}</button>
        </div>
        <div class="ev2-table-wrap">
          <table class="ev2-table">
            <thead>
              <tr>
                <th>${tt("ev2_col_sku", "SKU")}</th>
                <th>${tt("ev2_col_section", "分区")}</th>
                <th>${tt("ev2_col_item", "项目")}</th>
                <th>${tt("ev2_col_unit", "单位")}</th>
                <th class="num">${tt("ev2_col_material", "材料 $")}</th>
                <th class="num">${tt("ev2_col_labor", "人工 $")}</th>
                <th>${tt("ev2_col_tag", "标签")}</th>
                <th>${tt("ev2_col_actions", "操作")}</th>
              </tr>
            </thead>
            <tbody id="ev2-pl-tbody"></tbody>
          </table>
        </div>
      </div>
    `;
    $("#ev2-pl-search").addEventListener("input", () => renderPriceLibRows());
    $("#ev2-pl-section-filter").addEventListener("change", () => renderPriceLibRows());
    $("#ev2-pl-new").addEventListener("click", onPriceLibNew);
    renderPriceLibRows();
  }

  function renderPriceLibRows() {
    const tbody = $("#ev2-pl-tbody");
    if (!tbody) return;
    const term = ($("#ev2-pl-search").value || "").trim().toLowerCase();
    const sec = $("#ev2-pl-section-filter").value;
    let rows = ev2.priceLib;
    if (sec) rows = rows.filter(r => String(r.section_master_id) === sec);
    if (term) rows = rows.filter(r =>
      String(r.sku || "").toLowerCase().includes(term) ||
      String(r.item_name || "").toLowerCase().includes(term) ||
      String(r.description || "").toLowerCase().includes(term) ||
      String(r.tag || "").toLowerCase().includes(term)
    );
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${escHtml(r.sku || "—")}</td>
        <td>${escHtml(r.section_name || r.section_name_zh || "")}</td>
        <td><b>${escHtml(r.item_name)}</b><br/><span class="ev2-mini">${escHtml(r.description || "")}</span></td>
        <td>${escHtml(r.unit || "")}</td>
        <td class="num">${Number(r.material_unit_price || 0).toFixed(2)}</td>
        <td class="num">${Number(r.labor_unit_price || 0).toFixed(2)}</td>
        <td>${escHtml(r.tag || "")}</td>
        <td>
          <button class="ev2-btn-mini" data-act="edit" data-id="${r.id}">${tt("ev2_btn_edit", "编辑")}</button>
          <button class="ev2-btn-mini ev2-btn-danger" data-act="del" data-id="${r.id}">${tt("ev2_btn_delete", "删除")}</button>
        </td>
      </tr>
    `).join("") || `<tr><td colspan="8" class="ev2-empty">${tt("ev2_no_data", "没有数据")}</td></tr>`;
    tbody.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = Number(btn.dataset.id);
        if (btn.dataset.act === "edit") onPriceLibEdit(id);
        else onPriceLibDelete(id);
      });
    });
  }

  async function onPriceLibNew() {
    showPriceLibModal({});
  }

  async function onPriceLibEdit(id) {
    const item = ev2.priceLib.find(r => r.id === id);
    if (!item) return;
    showPriceLibModal(item);
  }

  function showPriceLibModal(item) {
    const isNew = !item.id;
    const sectionOpts = ev2.sectionsMaster
      .map(s => `<option value="${s.id}" ${s.id === item.section_master_id ? "selected" : ""}>${escHtml(s.name || s.name_zh)}</option>`)
      .join("");
    const html = `
      <div class="ev2-modal-overlay" id="ev2-modal-overlay">
        <div class="ev2-modal">
          <div class="ev2-modal-head">${isNew ? tt("ev2_action_label_new", "新增") : tt("ev2_action_label_edit", "编辑")}${tt("ev2_pl_modal_suffix", "单价库项")}</div>
          <div class="ev2-modal-body">
            <div class="ev2-grid-2">
              <div>
                <label class="ev2-label">${tt("ev2_col_sku", "SKU")}</label>
                <input class="ev2-input" id="m-sku" value="${escHtml(item.sku || "")}" />
              </div>
              <div>
                <label class="ev2-label">${tt("ev2_pl_section_required", "分区 *")}</label>
                <select class="ev2-input" id="m-sec">${sectionOpts}</select>
              </div>
              <div class="ev2-col-span-2">
                <label class="ev2-label">${tt("ev2_pl_label_item_name", "项目名 *")}</label>
                <input class="ev2-input" id="m-name" value="${escHtml(item.item_name || "")}" />
              </div>
              <div class="ev2-col-span-2">
                <label class="ev2-label">${tt("ev2_col_desc", "描述")}</label>
                <input class="ev2-input" id="m-desc" value="${escHtml(item.description || "")}" />
              </div>
              <div>
                <label class="ev2-label">${tt("ev2_col_unit", "单位")}</label>
                <input class="ev2-input" id="m-unit" value="${escHtml(item.unit || "")}" />
              </div>
              <div>
                <label class="ev2-label">${tt("ev2_pl_label_default_qty", "默认数量")}</label>
                <input class="ev2-input" id="m-qty" type="number" step="0.01" value="${item.default_qty || 1}" />
              </div>
              <div>
                <label class="ev2-label">${tt("ev2_pl_label_unit_mat", "材料单价 $")}</label>
                <input class="ev2-input" id="m-mat" type="number" step="0.01" value="${item.material_unit_price || 0}" />
              </div>
              <div>
                <label class="ev2-label">${tt("ev2_pl_label_unit_lab", "人工单价 $")}</label>
                <input class="ev2-input" id="m-lab" type="number" step="0.01" value="${item.labor_unit_price || 0}" />
              </div>
              <div class="ev2-col-span-2">
                <label class="ev2-label">${tt("ev2_pl_label_customer_note", "客户可见说明(出现在 PDF)")}</label>
                <input class="ev2-input" id="m-cnote" value="${escHtml(item.customer_visible_note || "")}" />
              </div>
              <div class="ev2-col-span-2">
                <label class="ev2-label">${tt("ev2_pl_label_internal_note", "内部备注(仅管理员看)")}</label>
                <input class="ev2-input" id="m-inote" value="${escHtml(item.internal_note || "")}" />
              </div>
              <div>
                <label class="ev2-label">${tt("ev2_col_tag", "标签")}</label>
                <input class="ev2-input" id="m-tag" value="${escHtml(item.tag || "")}" placeholder="${tt("ev2_pl_tag_ph", "例如:常用")}" />
              </div>
              <div>
                <label class="ev2-label">${tt("ev2_pl_label_photo_url", "照片 URL")}</label>
                <input class="ev2-input" id="m-photo" value="${escHtml(item.photo_url || "")}" />
              </div>
            </div>
          </div>
          <div class="ev2-modal-footer">
            <button class="ev2-btn" id="m-cancel">${tt("ev2_btn_cancel", "取消")}</button>
            <button class="ev2-btn ev2-btn-primary" id="m-save">${tt("ev2_btn_save", "保存")}</button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML("beforeend", html);
    $("#m-cancel").addEventListener("click", closeModal);
    $("#m-save").addEventListener("click", async () => {
      const body = {
        sku: $("#m-sku").value,
        section_master_id: Number($("#m-sec").value),
        item_name: $("#m-name").value,
        description: $("#m-desc").value,
        unit: $("#m-unit").value,
        default_qty: Number($("#m-qty").value),
        material_unit_price: Number($("#m-mat").value),
        labor_unit_price: Number($("#m-lab").value),
        customer_visible_note: $("#m-cnote").value,
        internal_note: $("#m-inote").value,
        tag: $("#m-tag").value,
        photo_url: $("#m-photo").value,
      };
      try {
        if (isNew) await api("price-library", { method: "POST", body });
        else await api(`price-library/${item.id}`, { method: "PUT", body });
        closeModal();
        await renderPriceLibRenoTab($("#ev2-tab-content"));
      } catch (e) {
        toast(tt("ev2_save_failed_prefix", "保存失败: ") + e.message, "error");
      }
    });
  }

  function closeModal() {
    const o = $("#ev2-modal-overlay");
    if (o) o.remove();
  }

  async function onPriceLibDelete(id) {
    if (!confirm2(tt("ev2_confirm_delete_soft", "确定删除?(软删除,可恢复)"))) return;
    try {
      await api(`price-library/${id}`, { method: "DELETE" });
      await renderPriceLibRenoTab($("#ev2-tab-content"));
    } catch (e) {
      toast(tt("ev2_delete_failed_prefix", "删除失败: ") + e.message, "error");
    }
  }

  // ===========================================================================
  // 标签页 3: 单价库 - 重建
  // ===========================================================================

  async function renderPriceLibRebuildTab(container) {
    const data = await api("price-library-rebuild");
    ev2.priceLibRebuild = data.items || [];
    container.innerHTML = `
      <div class="ev2-section">
        <div class="ev2-toolbar">
          <select class="ev2-input ev2-input-sm" id="ev2-plr-type-filter">
            <option value="">${tt("ev2_plr_filter_all", "全部")}</option>
            <option value="base">${tt("ev2_plr_filter_base", "主体(按 sqft)")}</option>
            <option value="addon">${tt("ev2_plr_filter_addon", "附加项")}</option>
          </select>
          <button class="ev2-btn ev2-btn-primary" id="ev2-plr-new">${tt("ev2_plr_btn_new", "+ 新增")}</button>
        </div>
        <div class="ev2-table-wrap">
          <table class="ev2-table">
            <thead>
              <tr>
                <th>${tt("ev2_col_sku", "SKU")}</th>
                <th>${tt("ev2_col_type", "类型")}</th>
                <th>${tt("ev2_col_name", "名称")}</th>
                <th>${tt("ev2_col_unit", "单位")}</th>
                <th class="num">${tt("ev2_col_default_unit_price", "默认单价 $")}</th>
                <th>${tt("ev2_col_sort", "排序")}</th>
                <th>${tt("ev2_col_actions", "操作")}</th>
              </tr>
            </thead>
            <tbody id="ev2-plr-tbody"></tbody>
          </table>
        </div>
      </div>
    `;
    $("#ev2-plr-type-filter").addEventListener("change", renderPriceLibRebuildRows);
    $("#ev2-plr-new").addEventListener("click", () => showPriceLibRebuildModal({}));
    renderPriceLibRebuildRows();
  }

  function renderPriceLibRebuildRows() {
    const tbody = $("#ev2-plr-tbody");
    if (!tbody) return;
    const filter = $("#ev2-plr-type-filter").value;
    let rows = ev2.priceLibRebuild;
    if (filter) rows = rows.filter(r => r.item_type === filter);
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${escHtml(r.sku || "—")}</td>
        <td>${r.item_type === "base" ? tt("ev2_plr_type_base", "主体") : tt("ev2_plr_type_addon", "附加项")}</td>
        <td><b>${escHtml(r.name)}</b><br/><span class="ev2-mini">${escHtml(r.description || "")}</span></td>
        <td>${escHtml(r.unit || "")}</td>
        <td class="num">${Number(r.default_unit_price || 0).toFixed(2)}</td>
        <td>${r.sort_order || ""}</td>
        <td>
          <button class="ev2-btn-mini" data-act="edit" data-id="${r.id}">${tt("ev2_btn_edit", "编辑")}</button>
          <button class="ev2-btn-mini ev2-btn-danger" data-act="del" data-id="${r.id}">${tt("ev2_btn_delete", "删除")}</button>
        </td>
      </tr>
    `).join("") || `<tr><td colspan="7" class="ev2-empty">${tt("ev2_no_data", "没有数据")}</td></tr>`;
    tbody.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = Number(btn.dataset.id);
        if (btn.dataset.act === "edit") {
          const it = ev2.priceLibRebuild.find(r => r.id === id);
          if (it) showPriceLibRebuildModal(it);
        } else {
          onPriceLibRebuildDelete(id);
        }
      });
    });
  }

  function showPriceLibRebuildModal(item) {
    const isNew = !item.id;
    const html = `
      <div class="ev2-modal-overlay" id="ev2-modal-overlay">
        <div class="ev2-modal">
          <div class="ev2-modal-head">${isNew ? tt("ev2_action_label_new", "新增") : tt("ev2_action_label_edit", "编辑")}${tt("ev2_plr_modal_suffix", "重建单价")}</div>
          <div class="ev2-modal-body">
            <div class="ev2-grid-2">
              <div><label class="ev2-label">${tt("ev2_col_sku", "SKU")}</label><input class="ev2-input" id="m-sku" value="${escHtml(item.sku || "")}" /></div>
              <div>
                <label class="ev2-label">${tt("ev2_plr_label_type_required", "类型 *")}</label>
                <select class="ev2-input" id="m-type">
                  <option value="base" ${item.item_type === "base" ? "selected" : ""}>${tt("ev2_plr_filter_base", "主体(按 sqft)")}</option>
                  <option value="addon" ${item.item_type === "addon" ? "selected" : ""}>${tt("ev2_plr_filter_addon", "附加项")}</option>
                </select>
              </div>
              <div class="ev2-col-span-2"><label class="ev2-label">${tt("ev2_plr_label_name_required", "名称 *")}</label><input class="ev2-input" id="m-name" value="${escHtml(item.name || "")}" /></div>
              <div class="ev2-col-span-2"><label class="ev2-label">${tt("ev2_col_desc", "描述")}</label><input class="ev2-input" id="m-desc" value="${escHtml(item.description || "")}" /></div>
              <div><label class="ev2-label">${tt("ev2_col_unit", "单位")}</label><input class="ev2-input" id="m-unit" value="${escHtml(item.unit || "")}" placeholder="${tt("ev2_plr_unit_ph", "例如:sqft / 个 / 套")}" /></div>
              <div><label class="ev2-label">${tt("ev2_col_default_unit_price", "默认单价 $")}</label><input class="ev2-input" id="m-price" type="number" step="0.01" value="${item.default_unit_price || 0}" /></div>
              <div><label class="ev2-label">${tt("ev2_pl_label_default_qty", "默认数量")}</label><input class="ev2-input" id="m-qty" type="number" step="0.01" value="${item.default_qty || 1}" /></div>
              <div><label class="ev2-label">${tt("ev2_col_sort", "排序")}</label><input class="ev2-input" id="m-sort" type="number" value="${item.sort_order || 99}" /></div>
            </div>
          </div>
          <div class="ev2-modal-footer">
            <button class="ev2-btn" id="m-cancel">${tt("ev2_btn_cancel", "取消")}</button>
            <button class="ev2-btn ev2-btn-primary" id="m-save">${tt("ev2_btn_save", "保存")}</button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML("beforeend", html);
    $("#m-cancel").addEventListener("click", closeModal);
    $("#m-save").addEventListener("click", async () => {
      const body = {
        sku: $("#m-sku").value,
        item_type: $("#m-type").value,
        name: $("#m-name").value,
        description: $("#m-desc").value,
        unit: $("#m-unit").value,
        default_unit_price: Number($("#m-price").value),
        default_qty: Number($("#m-qty").value),
        sort_order: Number($("#m-sort").value),
      };
      try {
        if (isNew) await api("price-library-rebuild", { method: "POST", body });
        else await api(`price-library-rebuild/${item.id}`, { method: "PUT", body });
        closeModal();
        await renderPriceLibRebuildTab($("#ev2-tab-content"));
      } catch (e) {
        toast(tt("ev2_save_failed_prefix", "保存失败: ") + e.message, "error");
      }
    });
  }

  async function onPriceLibRebuildDelete(id) {
    if (!confirm2(tt("ev2_confirm_delete_simple", "确定删除?"))) return;
    try {
      await api(`price-library-rebuild/${id}`, { method: "DELETE" });
      await renderPriceLibRebuildTab($("#ev2-tab-content"));
    } catch (e) {
      toast(tt("ev2_delete_failed_prefix", "删除失败: ") + e.message, "error");
    }
  }

  // ===========================================================================
  // 标签页 4: 报价模板
  // ===========================================================================

  async function renderTemplatesTab(container) {
    const data = await api("estimate-templates");
    ev2.templates = data.items || [];
    container.innerHTML = `
      <div class="ev2-section">
        <div class="ev2-toolbar">
          <select class="ev2-input ev2-input-sm" id="ev2-tpl-filter">
            <option value="">${tt("ev2_tpl_filter_all", "全部类型")}</option>
            <option value="full">${tt("ev2_tpl_filter_full", "整套模板")}</option>
            <option value="section">${tt("ev2_tpl_filter_section", "分区模板")}</option>
          </select>
          <button class="ev2-btn ev2-btn-primary" id="ev2-tpl-new">${tt("ev2_tpl_btn_new", "+ 新建模板")}</button>
        </div>
        <div class="ev2-table-wrap">
          <table class="ev2-table">
            <thead>
              <tr>
                <th>${tt("ev2_col_name", "名称")}</th>
                <th>${tt("ev2_col_type", "类型")}</th>
                <th>${tt("ev2_label_quote_type", "报价类型")}</th>
                <th>${tt("ev2_tpl_col_section_count", "分区数")}</th>
                <th>${tt("ev2_tpl_col_line_count", "明细行")}</th>
                <th>${tt("ev2_tpl_col_use_count", "使用次数")}</th>
                <th>${tt("ev2_col_updated", "更新")}</th>
                <th>${tt("ev2_col_actions", "操作")}</th>
              </tr>
            </thead>
            <tbody id="ev2-tpl-tbody"></tbody>
          </table>
        </div>
      </div>
    `;
    $("#ev2-tpl-filter").addEventListener("change", renderTemplateRows);
    $("#ev2-tpl-new").addEventListener("click", onTemplateNew);
    renderTemplateRows();
  }

  function renderTemplateRows() {
    const tbody = $("#ev2-tpl-tbody");
    if (!tbody) return;
    const filter = $("#ev2-tpl-filter").value;
    let rows = ev2.templates;
    if (filter) rows = rows.filter(r => r.template_type === filter);
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td><b>${escHtml(r.name)}</b><br/><span class="ev2-mini">${escHtml(r.description || "")}</span></td>
        <td><span class="ev2-pill ${r.template_type === "full" ? "ev2-pill-info" : "ev2-pill-warn"}">${r.template_type === "full" ? tt("ev2_tpl_pill_full", "整套") : tt("ev2_tpl_pill_section", "分区")}</span></td>
        <td>${r.estimate_type === "rebuild" ? tt("ev2_type_rebuild", "重建") : tt("ev2_type_renovation", "翻新")}</td>
        <td>${r.section_count || 0}</td>
        <td>${r.line_count || 0}</td>
        <td>${r.use_count || 0}</td>
        <td class="ev2-mini">${escHtml((r.updated_at || "").slice(0, 16))}</td>
        <td>
          <button class="ev2-btn-mini" data-act="view" data-id="${r.id}">${tt("ev2_btn_view", "详情")}</button>
          <button class="ev2-btn-mini ev2-btn-danger" data-act="del" data-id="${r.id}">${tt("ev2_btn_delete", "删除")}</button>
        </td>
      </tr>
    `).join("") || `<tr><td colspan="8" class="ev2-empty">${tt("ev2_tpl_empty", "没有模板")}</td></tr>`;
    tbody.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = Number(btn.dataset.id);
        if (btn.dataset.act === "view") onTemplateView(id);
        else onTemplateDelete(id);
      });
    });
  }

  async function onTemplateNew() {
    const name = window.prompt(tt("ev2_tpl_prompt_name", "模板名称:"), "");
    if (!name) return;
    try {
      await api("estimate-templates", {
        method: "POST",
        body: { name, template_type: "full", estimate_type: "renovation" },
      });
      await renderTemplatesTab($("#ev2-tab-content"));
    } catch (e) {
      toast(tt("ev2_create_failed_prefix", "创建失败: ") + e.message, "error");
    }
  }

  async function onTemplateView(id) {
    try {
      const tpl = await api(`estimate-templates/${id}`);
      const html = `
        <div class="ev2-modal-overlay" id="ev2-modal-overlay">
          <div class="ev2-modal ev2-modal-wide">
            <div class="ev2-modal-head">${tt("ev2_tpl_detail_title", "模板详情:{name}").replace("{name}", escHtml(tpl.name))}</div>
            <div class="ev2-modal-body">
              <div class="ev2-mini">${tt("ev2_tpl_detail_meta", "类型:{type} · 报价类型:{etype} · 默认 markup:{markup}%")
                .replace("{type}", tpl.template_type === "full" ? tt("ev2_tpl_pill_full", "整套") : tt("ev2_tpl_pill_section", "分区"))
                .replace("{etype}", tpl.estimate_type === "rebuild" ? tt("ev2_type_rebuild", "重建") : tt("ev2_type_renovation", "翻新"))
                .replace("{markup}", tpl.default_markup_rate)}</div>
              ${(tpl.sections || []).map(sec => `
                <div class="ev2-card" style="margin-top:10px;">
                  <b>${escHtml(sec.name || sec.section_name_zh)}</b><!-- SECTIONS_ES_FIX_APPLIED -->
                  <ul style="margin:6px 0 0 18px; padding:0;">
                    ${(sec.lines || []).map(ln => `
                      <li>${escHtml(ln.item_name)} · ${escHtml(ln.unit || "")}
                        ${ln.override_material_price !== null && ln.override_material_price !== undefined
                          ? `<span class="ev2-mini" style="color:#c97a00;">[${tt("ev2_tpl_label_overridden", "覆盖单价")}]</span>`
                          : `<span class="ev2-mini">[${tt("ev2_tpl_label_referenced", "引用")} ${escHtml(ln.lib_sku || "#" + ln.price_library_id)}]</span>`}
                      </li>
                    `).join("") || `<li class="ev2-mini">${tt("ev2_tpl_detail_no_lines", "没有明细")}</li>`}
                  </ul>
                </div>
              `).join("") || `<p>${tt("ev2_tpl_detail_no_sections", "这个模板没有分区")}</p>`}
            </div>
            <div class="ev2-modal-footer">
              <button class="ev2-btn" id="m-cancel">${tt("ev2_btn_close", "关闭")}</button>
            </div>
          </div>
        </div>
      `;
      document.body.insertAdjacentHTML("beforeend", html);
      $("#m-cancel").addEventListener("click", closeModal);
    } catch (e) {
      toast(tt("ev2_load_failed_prefix", "加载失败: ") + e.message, "error");
    }
  }

  async function onTemplateDelete(id) {
    if (!confirm2(tt("ev2_confirm_delete_tpl_soft", "确定删除模板?(软删除,可恢复)"))) return;
    try {
      await api(`estimate-templates/${id}`, { method: "DELETE" });
      await renderTemplatesTab($("#ev2-tab-content"));
    } catch (e) {
      toast(tt("ev2_delete_failed_prefix", "删除失败: ") + e.message, "error");
    }
  }

  // ===========================================================================
  // 标签页 5: 分区管理
  // ===========================================================================

  async function renderSectionsTab(container) {
    const data = await api("sections-master");
    ev2.sectionsMaster = data.items || [];
    container.innerHTML = `
      <div class="ev2-section">
        <div class="ev2-toolbar">
          <button class="ev2-btn ev2-btn-primary" id="ev2-sec-new">${tt("ev2_sec_btn_new", "+ 新增分区")}</button>
        </div>
        <div class="ev2-table-wrap">
          <table class="ev2-table">
            <thead>
              <tr>
                <th>${tt("ev2_col_sort", "排序")}</th>
                <th>${tt("ev2_col_code", "代号")}</th>
                <th>${tt("ev2_col_name_zh", "中文名")}</th>
                <th>${tt("ev2_col_name_en", "英文名")}</th>
                <th>${tt("ev2_col_notes", "备注")}</th>
                <th>${tt("ev2_col_actions", "操作")}</th>
              </tr>
            </thead>
            <tbody id="ev2-sec-tbody"></tbody>
          </table>
        </div>
      </div>
    `;
    $("#ev2-sec-new").addEventListener("click", () => showSectionModal({}));
    renderSectionRows();
  }

  function renderSectionRows() {
    const tbody = $("#ev2-sec-tbody");
    if (!tbody) return;
    tbody.innerHTML = ev2.sectionsMaster.map(s => `
      <tr>
        <td>${s.sort_order}</td>
        <td>${escHtml(s.code)}</td>
        <td>${escHtml(s.name_zh)}</td>
        <td>${escHtml(s.name_en || "")}</td>
        <td>${escHtml(s.notes || "")}</td>
        <td>
          <button class="ev2-btn-mini" data-act="edit" data-id="${s.id}">${tt("ev2_btn_edit", "编辑")}</button>
          <button class="ev2-btn-mini ev2-btn-danger" data-act="del" data-id="${s.id}">${tt("ev2_btn_delete", "删除")}</button>
        </td>
      </tr>
    `).join("");
    tbody.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = Number(btn.dataset.id);
        if (btn.dataset.act === "edit") {
          const s = ev2.sectionsMaster.find(x => x.id === id);
          if (s) showSectionModal(s);
        } else {
          onSectionMasterDelete(id);
        }
      });
    });
  }

  function showSectionModal(item) {
    const isNew = !item.id;
    const html = `
      <div class="ev2-modal-overlay" id="ev2-modal-overlay">
        <div class="ev2-modal">
          <div class="ev2-modal-head">${isNew ? tt("ev2_action_label_new", "新增") : tt("ev2_action_label_edit", "编辑")}${tt("ev2_sec_modal_suffix", "分区")}</div>
          <div class="ev2-modal-body">
            <div class="ev2-grid-2">
              <div><label class="ev2-label">${tt("ev2_sec_code_required", "代号 *")}</label><input class="ev2-input" id="m-code" value="${escHtml(item.code || "")}" placeholder="${tt("ev2_sec_code_ph", "例如:DEMO")}" /></div>
              <div><label class="ev2-label">${tt("ev2_col_sort", "排序")}</label><input class="ev2-input" id="m-sort" type="number" value="${item.sort_order || 99}" /></div>
              <div><label class="ev2-label">${tt("ev2_sec_name_zh_required", "中文名 *")}</label><input class="ev2-input" id="m-zh" value="${escHtml(item.name_zh || "")}" /></div>
              <div><label class="ev2-label">${tt("ev2_col_name_en", "英文名")}</label><input class="ev2-input" id="m-en" value="${escHtml(item.name_en || "")}" /></div>
              <div class="ev2-col-span-2"><label class="ev2-label">${tt("ev2_col_notes", "备注")}</label><input class="ev2-input" id="m-notes" value="${escHtml(item.notes || "")}" /></div>
            </div>
          </div>
          <div class="ev2-modal-footer">
            <button class="ev2-btn" id="m-cancel">${tt("ev2_btn_cancel", "取消")}</button>
            <button class="ev2-btn ev2-btn-primary" id="m-save">${tt("ev2_btn_save", "保存")}</button>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentHTML("beforeend", html);
    $("#m-cancel").addEventListener("click", closeModal);
    $("#m-save").addEventListener("click", async () => {
      const body = {
        code: $("#m-code").value.toUpperCase(),
        name_zh: $("#m-zh").value,
        name_en: $("#m-en").value,
        sort_order: Number($("#m-sort").value),
        notes: $("#m-notes").value,
      };
      try {
        if (isNew) await api("sections-master", { method: "POST", body });
        else await api(`sections-master/${item.id}`, { method: "PUT", body });
        closeModal();
        await renderSectionsTab($("#ev2-tab-content"));
      } catch (e) {
        toast(tt("ev2_save_failed_prefix", "保存失败: ") + e.message, "error");
      }
    });
  }

  async function onSectionMasterDelete(id) {
    if (!confirm2(tt("ev2_confirm_delete_sec", "确定删除?(软删除,如果该分区下有单价库项,将无法新建报价时引用)"))) return;
    try {
      await api(`sections-master/${id}`, { method: "DELETE" });
      await renderSectionsTab($("#ev2-tab-content"));
    } catch (e) {
      toast(tt("ev2_delete_failed_prefix", "删除失败: ") + e.message, "error");
    }
  }

  // ===========================================================================
  // 拦截:在适当时机接管 estimates 模块
  // ===========================================================================

  /**
   * 接管策略:monkey-patch app.js 的 loadCrud 函数
   *
   * 当 loadCrud("estimates") 被调用时,我们拦截并自己接管渲染。
   * 其他模块照常走原有逻辑。
   *
   * 由于 estimates_v2.js 是在 app.js 之后加载的,
   * 此时 window.loadCrud 应该已经存在。如果一时不存在,
   * 我们等一会儿再 patch。
   */
  function installLoadCrudPatch() {
    if (typeof window.loadCrud !== "function") {
      // app.js 还没准备好,等一下
      setTimeout(installLoadCrudPatch, 50);
      return;
    }
    if (window.loadCrud.__ev2_patched) {
      return;  // 已经 patch 过了,避免重复
    }
    const original = window.loadCrud;
    window.loadCrud = async function (module) {
      if (module === "estimates") {
        // 拦截!不走 app.js 的旧版渲染,自己接管
        try {
          await ev2.takeover();
        } catch (e) {
          console.error("[estimates_v2] takeover failed:", e);
          // 失败时回退到原始渲染,保证用户至少能看到东西
          return original.apply(this, arguments);
        }
        return;
      }
      return original.apply(this, arguments);
    };
    window.loadCrud.__ev2_patched = true;
    console.log("[estimates_v2] loadCrud monkey-patch installed");

    // 如果当前已经在 estimates 模块上,立刻接管一次
    const s = getAppState();
    if (s && s.module === "estimates") {
      ev2.takeover();
    }
  }

  // 也提供一个手动接管的全局方法
  window.estimatesV2.activate = () => ev2.takeover();

  // 等 DOM 加载完再 patch(确保 app.js 已执行完)
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", installLoadCrudPatch);
  } else {
    installLoadCrudPatch();
  }

  console.log("[estimates_v2] loaded. Installing loadCrud patch...");
})();
