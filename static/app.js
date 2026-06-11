const I18N = {
  zh: {
    app: "装修公司 CRM",
    login: "登录",
    username: "用户名",
    password: "密码",
    login_tip: "请输入账号和密码登录系统",
    logout: "退出",
    admin: "账号权限",
    dashboard: "仪表盘",
    customers: "客户/线索",
    estimates: "报价/方案",
    contracts: "合同/付款计划",
    projects: "项目/工地",
    change_orders: "变更单",
    documents: "文件中心",
    finance: "财务",
    settings: "设置/权限",
    search: "搜索",
    create: "新建",
    save: "保存",
    reset: "重置",
    edit: "编辑",
    del: "删除",
    detail: "详情",
    generate_estimate: "生成报价",
    generate_contract: "生成合同",
    generate_project: "生成项目/工地",
    view_customer: "查看客户",
    view_estimate: "查看报价",
    view_contract: "查看合同",
    view_project: "查看项目",
    print_estimate_doc: "打印报价单",
    export_estimate_pdf: "导出PDF",
    print_contract_doc: "打印合同",
    export_contract_pdf: "导出PDF",
    confirm_del: "确认删除？",
    no_data: "暂无数据",
    close: "关闭",
    pdf: "PDF",
    dashboard_desc: "老板 / 项目经理快速查看公司运营状态",
    settings_desc: "账号权限与品牌配置",
    monthly_new_leads: "本月新增线索",
    monthly_estimates_sent: "本月已发报价",
    monthly_contracts_signed: "本月已签约数",
    monthly_contracted_amount: "本月签约金额",
    active_projects: "施工中项目",
    monthly_ar_received: "本月已收款",
    monthly_ar_pending: "待收款(AR)",
    monthly_cost: "本月支出",
    monthly_gross_profit: "本月毛利",
    stale_followups: "待跟进客户（3天+）",
    pending_estimates: "待确认报价（7天+）",
    upcoming_payments: "即将到期付款（7天）",
    payment_reminders: "待催办付款节点",
    payment_plan_module: "付款计划 / 付款节点",
    open_issues: "未解决工地问题",
    user_admin: "账号与模块权限",
    create_user: "新建用户",
    create_user_btn: "创建用户",
    role: "角色",
    language: "语言",
    modules: "模块",
    update: "更新",
    pwd_optional: "新密码(可选)",
    owner_only: "仅老板可管理账号",
    brand_settings: "品牌设置",
    save_brand: "保存品牌",
    pdf_lang: "PDF语言",
    templates: "报价模板",
    apply_template: "套用模板",
    template_name: "模板名",
    package_type: "套餐类型",
    create_template: "新建模板",
    quick_lead_entry: "快速录入线索",
    quick_submit_lead: "提交线索",
    filter_source_channel: "来源渠道筛选",
    filter_customer_status: "状态筛选",
    source_info: "来源信息",
    inquiry_info: "需求信息",
    preferred_contact: "联系偏好",
    recent_followups: "最近跟进记录",
    no_followups: "暂无跟进记录",
    confirm_merge_lead: "该手机号已存在，是否合并到已有客户？",
    lead_required_hint: "姓名或电话至少填写一个",
    contract_pdf: "合同PDF",
    progress_flow: "施工流程",
    init_flow: "初始化流程",
    reinit_flow: "重置流程",
    stage_name: "阶段",
    stage_status: "状态",
    pending: "未开始",
    in_progress: "进行中",
    done: "已完成",
    save_stage: "保存阶段",
    no_flow: "当前项目还没有流程，先选择模板初始化",
    actions: "操作",
    project_profit_detail: "项目利润明细",
    ar_aging: "应收账龄",
    ap_aging: "应付账龄",
    ar_ledger: "应收台账",
    ap_ledger: "应付台账",
    bucket: "账龄区间",
    count: "笔数",
    amount: "金额",
    due_date: "到期日",
    received_amount: "已收",
    paid_amount: "已付",
    open_amount: "未结",
    age_days: "账龄(天)",
    revenue: "收入",
    cost: "成本",
    profit: "利润",
    gross_margin_pct: "毛利率%",
    field_id: "ID",
    field_name: "名称",
    field_phone: "电话",
    field_email: "邮箱",
    field_source: "来源",
    field_source_channel: "来源渠道",
    field_source_note: "来源备注",
    field_demand_type: "需求类型",
    field_inquiry_type: "咨询类型",
    field_preferred_contact_method: "联系偏好",
    field_budget_range: "预算范围",
    field_status: "状态",
    field_primary_address: "主地址",
    field_other_addresses: "其他地址",
    field_notes: "备注",
    field_customer_id: "客户ID",
    field_lead_id: "线索ID",
    field_customer_name: "客户姓名",
    field_source_type: "来源类型",
    field_contract_generated: "合同生成",
    field_project_id: "项目ID",
    field_title: "标题",
    field_version: "版本",
    field_valid_until: "有效期",
    field_subtotal: "小计",
    field_markup_rate: "加价率",
    field_total_amount: "总价",
    field_line_items_json: "分项JSON",
    field_estimate_id: "报价ID",
    field_contract_no: "合同号",
    field_signed_status: "签字状态",
    field_signed_date: "签字日期",
    field_contract_id: "合同ID",
    field_address: "地址",
    field_progress_pct: "进度%",
    field_start_date: "开工日期",
    field_estimated_finish_date: "预计完工",
    field_actual_finish_date: "实际完工",
    field_manager: "项目经理",
    field_order_no: "变更单编号",
    field_description: "变更说明",
    field_project_name: "所属项目",
    field_customer_name: "客户",
    field_impact_payment_plan: "影响付款计划",
    field_affect_designer_commission: "影响设计师佣金",
    field_approved_at: "确认时间",
    field_created_by: "创建人",
    field_reason: "变更原因",
    field_items_json: "明细JSON",
    field_amount_delta: "金额变化",
    field_days_delta: "工期变化",
    field_doc_type: "文件类型",
    field_file_name: "文件名",
    field_tags: "标签",
    field_visibility: "可见范围",
    field_node_name: "收款节点",
    field_vendor: "供应商",
    field_type: "类型",
    field_1099_required: "需报1099",
    field_vendor_id: "供应商ID",
    field_bill_id: "账单ID",
    field_bill_no: "账单编号",
    field_bill_date: "账单日期",
    field_tax_id: "税号",
    field_w9_received: "W-9已收",
    field_category: "类别",
    field_method: "付款方式",
    field_payment_date: "付款日",
    field_reference_no: "单号",
    field_updated_at: "最近更新时间",
    ar_total: "应收总额",
    ar_overdue: "应收逾期",
    ap_total: "应付总额",
    ap_overdue: "应付逾期",
    monthly_ap_paid: "本月已付",
    monthly_cashflow: "本月现金流",
    report_1099: "1099 汇总",
    project_cost_ledger: "项目成本台账",
    view_cost_ledger: "查看成本台账",
    open_costs: "Open Costs（未结成本）",
    cost_by_category: "按类别成本汇总",
    payments_total: "已付成本合计",
    vendor_ledger: "供应商台账",
    view_ledger: "查看台账",
    vendor_basic_info: "供应商信息",
    bills_payable: "Bills（应付）",
    payments_paid: "Payments（已付）",
    open_bills_total: "未结账单合计",
    current_outstanding_balance: "当前未结余额",
    finance_ops_panels: "财务录入面板",
    finance_ops_loading: "正在加载录入面板...",
    finance_ops_load_failed: "财务录入面板加载失败，请刷新页面重试",
    vendors_panel: "供应商管理",
    bills_panel: "账单管理",
    payments_panel: "付款管理",
    new_vendor: "新建供应商",
    new_bill: "新建账单",
    new_payment: "新建付款",
    edit_vendor: "编辑供应商",
    edit_bill: "编辑账单",
    edit_payment: "编辑付款",
    total_paid_this_year: "本年支付合计",
    over_600: "是否超过$600",
    required_1099: "1099申报",
    contract_revenue: "合同收入",
    change_revenue: "变更收入",
    total_revenue: "总收入",
    recorded_cost: "已记成本",
    ap_open: "应付未结",
    total_cost: "总成本",
    tab_overview: "总览",
    tab_schedule: "进度任务",
    tab_site_logs: "现场日志",
    tab_issues: "问题整改",
    tab_payments: "收款节点",
    tab_costs: "项目成本",
    tab_files: "文件",
    project_detail: "项目详情",
    source_relation: "来源关联",
    source_estimate: "来源报价",
    source_contract: "来源合同",
    linked_project: "关联合同项目",
    project_info: "项目基础信息",
    customer: "客户",
    contract_info: "关联合同",
    project_progress: "施工进度",
    stage_click_tip: "点击阶段标签可直接切换状态",
    project_logs: "施工日志",
    add_log: "新增日志",
    log_date: "日期",
    log_content: "日志内容",
    log_image: "图片链接(可选)",
    payment_info: "付款信息",
    change_order_summary: "变更单影响摘要",
    approved_change_total: "已确认变更金额总计",
    impact_payment_plan_count: "影响付款计划变更单数量",
    approved_change_commissionable: "已确认变更金额（计佣）",
    approved_change_non_commissionable: "已确认变更金额（不计佣）",
    current_contract_total: "当前合同总额",
    change_order_warn_payment_plan: "有已确认变更单影响付款计划，请检查付款节点",
    project_change_orders: "变更单",
    create_change_order: "新增变更单",
    print_change_order_doc: "打印变更单",
    export_change_order_pdf: "导出PDF",
    mark_sent: "标记已发送",
    mark_approved: "标记已确认",
    mark_rejected: "标记已拒绝",
    open_change_order_module: "查看变更单模块",
    payment_milestones: "付款节点计划",
    milestone_name: "节点名称",
    milestone_type: "节点类型",
    trigger_type: "触发条件",
    trigger_stage: "触发阶段",
    trigger_progress: "触发进度%",
    amount_type: "金额类型",
    amount_value: "金额/比例",
    state: "状态",
    trigger_reason: "触发原因",
    mark_reminded: "标记已提醒",
    mark_paid: "标记已收款",
    mark_completed: "标记已完成",
    add_milestone: "新增节点",
    update_milestone: "更新节点",
    cancel_edit: "取消编辑",
    select_contract: "选择合同",
    no_contracts: "暂无合同，请先创建合同",
    no_milestones: "暂无付款节点",
    designer_info: "设计师协作",
    designer_commission: "设计师佣金",
    recalc_commission: "重算佣金",
    commission_amount: "佣金金额",
    commission_status: "佣金状态",
    commission_base: "佣金基数",
    base_contract_amount: "主合同金额",
    change_order_amount: "变更单金额",
    settlement_mode: "结算条件",
    payment_reminder_list: "项目待催办节点",
    payment_overview: "付款进度概览",
    finance_snapshot: "Finance Snapshot",
    triggered_unpaid_nodes: "已触发未收款节点",
    current_payment_nodes: "当前付款节点",
    recent_paid_node: "最近已收款节点",
    next_trigger_node: "下一个可能触发节点",
    view_project_detail: "查看项目详情",
    view_contract_detail: "查看合同详情",
    default_exclude_change_orders: "默认不含变更单金额",
    delete_milestone: "删除节点",
    confirm_del_milestone: "确认删除该付款节点？",
    milestone_state_untriggered: "未触发",
    milestone_state_pending: "已触发（待催办）",
    milestone_state_reminded: "已提醒",
    milestone_state_paid: "已收款",
    internal_notes: "备注 / 内部记录",
    save_notes: "保存备注",
    notes_saved: "备注已保存",
    no_logs: "暂无施工日志",
    value_pending: "未开始",
    value_in_progress: "进行中",
    value_done: "已完成",
    value_open: "待处理",
    value_fixed: "已修复",
    value_verified: "已验收",
    value_paid: "已支付",
    value_unpaid: "未支付",
    value_overdue: "逾期",
    value_draft: "草稿",
    value_sent: "已发送",
    value_approved: "已确认",
    value_accepted: "已接受",
    value_rejected: "已拒绝",
    value_lead: "线索",
    value_new_lead: "新线索",
    value_contacted: "已联系",
    value_site_visit_booked: "已预约上门",
    value_quoted: "已报价",
    value_measuring: "测量中",
    value_quoting: "报价中",
    value_signed: "已签约",
    value_unsigned: "未签字",
    value_completed: "已完成",
    value_lost: "流失",
    value_customer: "客户",
    value_not_started: "未开工",
    value_on_hold: "暂停",
    value_high: "高",
    value_medium: "中",
    value_low: "低",
    value_owner: "老板",
    value_manager: "项目经理",
    value_designer: "设计师",
    value_website: "官网",
    value_houzz: "Houzz",
    value_phone: "电话",
    value_email: "邮箱",
    value_referral: "转介绍",
    value_walk_in: "到店",
    value_manual: "手动录入",
    value_supplier: "材料供应商",
    value_subcontractor: "分包商",
    value_1099: "1099承包商",
    value_check: "支票",
    value_ach: "ACH",
    value_wire: "电汇",
    value_cash: "现金",
    value_card: "刷卡",
    value_visit: "上门",
    value_note: "备注",
    value_custom_furniture: "定制家具",
    value_bathroom_remodel: "卫生间翻新",
    value_kitchen_remodel: "厨房翻新",
    value_full_remodel: "全屋翻新",
    value_other: "其他",
    value_text: "短信",
    value_wechat: "微信",
    value_contract_signed: "合同签署",
    value_stage_started: "阶段开始",
    value_stage_done: "阶段完成",
    value_progress_percent: "进度达到",
    value_percent: "按比例",
    value_fixed: "固定金额",
    value_untriggered: "未触发",
    value_reminded: "已提醒",
    value_pending_settlement: "待结算",
    value_ungenerated: "未生成",
    value_generated: "已生成",
    value_settled: "已结算",
    value_base_contract_only: "仅主合同",
    value_include_change_orders: "含变更单",
    lang_zh: "中文",
    lang_en: "英文",
    lang_es: "西文",
    user_role: "当前用户",
    role_owner: "老板",
    role_manager: "项目经理",
    role_designer: "设计师",
    field_contract_amount: "合同金额",
    field_pending_amount: "待收款",
    field_cost_amount: "成本",
    field_profit_amount: "利润",
    field_phase: "阶段",
    field_owner: "负责人",
    field_log_date: "日志日期",
    field_work_summary: "工作内容",
    field_crew_info: "施工团队",
    field_materials_info: "材料情况",
    field_issue_note: "问题备注",
    field_template_used: "模板",
    field_photos_json: "照片",
    field_severity: "严重程度",
    field_description: "描述",
    field_received_date: "收款日期",
    field_invoice_no: "发票号",
    field_cost_type: "成本类型",
    field_cost_date: "成本日期",
    field_url: "链接",
    field_designer_id: "设计师ID",
    field_designer_name: "设计师姓名",
    field_designer_commission_type: "佣金类型",
    field_designer_commission_value: "佣金值",
    field_designer_commission_base: "佣金基数",
    field_followup_type: "跟进方式",
    field_content: "内容",
    field_result: "跟进结果",
    field_next_followup_at: "下次跟进时间",
    field_completed: "是否完成",
    related_estimates: "关联报价",
    source_customer: "来源客户/线索",
    followup_records: "跟进记录",
    add_followup: "新增跟进",
    quick_followup: "跟进",
    set_next_followup: "设置下次跟进",
    today_due_followups: "今日待跟进",
    stale_customers_over_3d: "超过3天未跟进客户",
    no_followup_records: "暂无跟进记录",
    followup_saved: "跟进已保存",
    no_next_followup: "未设置",
    status_completed: "已完成",
    status_uncompleted: "未完成",
    attachments: "附件",
    estimate_attachments: "报价附件",
    contract_attachments: "合同附件",
    bill_attachments: "账单附件/凭证",
    payment_attachments: "付款附件/凭证",
    project_file_module: "工地照片 / 项目文件",
    site_photos: "工地照片",
    project_documents: "项目文件",
    upload_file: "上传文件",
    choose_file: "选择文件",
    open_file: "打开文件",
    view_attachment: "查看附件",
    delete_file: "删除文件",
    no_files: "暂无附件",
    field_file_category: "附件分类",
    field_file_size: "文件大小",
    field_uploaded_by: "上传人",
    upload_success: "上传成功",
    file_type_not_supported: "仅支持 jpg/jpeg/png/pdf",
    value_file_category_photo: "现场照片",
    value_file_category_contract: "合同",
    value_file_category_estimate: "报价",
    value_file_category_invoice: "发票",
    value_file_category_change_order: "变更单",
    value_file_category_completion: "完工资料",
    value_file_category_other: "其他",
    value_yes: "是",
    value_no: "否",
    custom_contract: "自定义合同",
    custom_contract_placeholder: "填写自定义合同主体条款。系统仍会使用当前合同的客户、价格和付款计划。",
    field_custom_contract_enabled: "启用自定义合同主体",
    field_custom_contract_text: "自定义合同主体",
  },
  en: {
    app: "Decor CRM",
    login: "Login",
    username: "Username",
    password: "Password",
    login_tip: "Please sign in with your account credentials",
    logout: "Logout",
    admin: "User Admin",
    dashboard: "Dashboard",
    customers: "Customers",
    estimates: "Estimates",
    contracts: "Contracts",
    projects: "Projects",
    change_orders: "Change Orders",
    documents: "Documents",
    finance: "Finance",
    settings: "Settings/Permissions",
    search: "Search",
    create: "Create",
    save: "Save",
    reset: "Reset",
    edit: "Edit",
    del: "Delete",
    detail: "Detail",
    generate_estimate: "Generate Estimate",
    generate_contract: "Generate Contract",
    generate_project: "Generate Project",
    view_customer: "View Customer",
    view_estimate: "View Estimate",
    view_contract: "View Contract",
    view_project: "View Project",
    print_estimate_doc: "Print Estimate",
    export_estimate_pdf: "Export PDF",
    print_contract_doc: "Print Contract",
    export_contract_pdf: "Export PDF",
    confirm_del: "Confirm delete?",
    no_data: "No data",
    close: "Close",
    pdf: "PDF",
    dashboard_desc: "Owner / PM quick company operations overview",
    settings_desc: "Users, permissions and brand configuration",
    monthly_new_leads: "Monthly New Leads",
    monthly_estimates_sent: "Monthly Estimates Sent",
    monthly_contracts_signed: "Monthly Signed Contracts",
    monthly_contracted_amount: "Monthly Contracted Amount",
    active_projects: "Active Projects",
    monthly_ar_received: "Monthly AR Received",
    monthly_ar_pending: "AR Pending",
    monthly_cost: "Monthly Cost",
    monthly_gross_profit: "Monthly Gross Profit",
    stale_followups: "No follow-up 3+ days",
    pending_estimates: "Estimates pending 7+ days",
    upcoming_payments: "Payments due in 7 days",
    payment_reminders: "Payment milestones to chase",
    payment_plan_module: "Payment Plan / Milestones",
    open_issues: "Open site issues",
    user_admin: "Users and Module Permissions",
    create_user: "Create User",
    create_user_btn: "Create",
    role: "Role",
    language: "Language",
    modules: "Modules",
    update: "Update",
    pwd_optional: "New password (optional)",
    owner_only: "Owner only",
    brand_settings: "Brand Settings",
    save_brand: "Save Brand",
    pdf_lang: "PDF Lang",
    templates: "Estimate Templates",
    apply_template: "Apply Template",
    template_name: "Template Name",
    package_type: "Package Type",
    create_template: "Create Template",
    quick_lead_entry: "Quick Lead Intake",
    quick_submit_lead: "Submit Lead",
    filter_source_channel: "Source Filter",
    filter_customer_status: "Status Filter",
    source_info: "Source Info",
    inquiry_info: "Inquiry Info",
    preferred_contact: "Preferred Contact",
    recent_followups: "Recent Follow-ups",
    no_followups: "No follow-ups yet",
    confirm_merge_lead: "This phone already exists. Merge into the existing customer?",
    lead_required_hint: "Please provide at least a name or phone",
    contract_pdf: "Contract PDF",
    progress_flow: "Workflow",
    init_flow: "Init Flow",
    reinit_flow: "Reset Flow",
    stage_name: "Stage",
    stage_status: "Status",
    pending: "Pending",
    in_progress: "In Progress",
    done: "Done",
    save_stage: "Save Stage",
    no_flow: "No workflow yet, initialize from template",
    actions: "Actions",
    project_profit_detail: "Project Profit Detail",
    ar_aging: "AR Aging",
    ap_aging: "AP Aging",
    ar_ledger: "AR Ledger",
    ap_ledger: "AP Ledger",
    bucket: "Bucket",
    count: "Count",
    amount: "Amount",
    due_date: "Due Date",
    received_amount: "Received",
    paid_amount: "Paid",
    open_amount: "Open",
    age_days: "Age(Days)",
    revenue: "Revenue",
    cost: "Cost",
    profit: "Profit",
    gross_margin_pct: "Gross Margin %",
    field_id: "ID",
    field_name: "Name",
    field_phone: "Phone",
    field_email: "Email",
    field_source: "Source",
    field_source_channel: "Source Channel",
    field_source_note: "Source Note",
    field_demand_type: "Demand Type",
    field_inquiry_type: "Inquiry Type",
    field_preferred_contact_method: "Preferred Contact",
    field_budget_range: "Budget Range",
    field_status: "Status",
    field_primary_address: "Primary Address",
    field_other_addresses: "Other Addresses",
    field_notes: "Notes",
    field_customer_id: "Customer ID",
    field_lead_id: "Lead ID",
    field_customer_name: "Customer Name",
    field_source_type: "Source Type",
    field_contract_generated: "Contract Status",
    field_project_id: "Project ID",
    field_title: "Title",
    field_version: "Version",
    field_valid_until: "Valid Until",
    field_subtotal: "Subtotal",
    field_markup_rate: "Markup Rate",
    field_total_amount: "Total Amount",
    field_line_items_json: "Line Items JSON",
    field_estimate_id: "Estimate ID",
    field_contract_no: "Contract No",
    field_signed_status: "Signed Status",
    field_signed_date: "Signed Date",
    field_contract_id: "Contract ID",
    field_address: "Address",
    field_progress_pct: "Progress %",
    field_start_date: "Start Date",
    field_estimated_finish_date: "Estimated Finish",
    field_actual_finish_date: "Actual Finish",
    field_manager: "Manager",
    field_order_no: "Change Order No",
    field_description: "Description",
    field_project_name: "Project",
    field_customer_name: "Customer",
    field_impact_payment_plan: "Impact Payment Plan",
    field_affect_designer_commission: "Affect Designer Commission",
    field_approved_at: "Approved At",
    field_created_by: "Created By",
    field_reason: "Reason",
    field_items_json: "Items JSON",
    field_amount_delta: "Amount Delta",
    field_days_delta: "Days Delta",
    field_doc_type: "Doc Type",
    field_file_name: "File Name",
    field_tags: "Tags",
    field_visibility: "Visibility",
    field_node_name: "Payment Node",
    field_vendor: "Vendor",
    field_type: "Type",
    field_1099_required: "1099 Required",
    field_vendor_id: "Vendor ID",
    field_bill_id: "Bill ID",
    field_bill_no: "Bill No",
    field_bill_date: "Bill Date",
    field_tax_id: "Tax ID",
    field_w9_received: "W-9 Received",
    field_category: "Category",
    field_method: "Method",
    field_payment_date: "Payment Date",
    field_reference_no: "Reference No",
    field_updated_at: "Updated At",
    ar_total: "AR Total",
    ar_overdue: "AR Overdue",
    ap_total: "AP Total",
    ap_overdue: "AP Overdue",
    monthly_ap_paid: "Monthly AP Paid",
    monthly_cashflow: "Monthly Cashflow",
    report_1099: "1099 Summary",
    project_cost_ledger: "Project Cost Ledger",
    view_cost_ledger: "View Cost Ledger",
    open_costs: "Open Costs",
    cost_by_category: "Cost by Category",
    payments_total: "Paid Costs Total",
    vendor_ledger: "Vendor Ledger",
    view_ledger: "View Ledger",
    vendor_basic_info: "Vendor Info",
    bills_payable: "Bills (Payable)",
    payments_paid: "Payments (Paid)",
    open_bills_total: "Open Bills Total",
    current_outstanding_balance: "Current Outstanding Balance",
    finance_ops_panels: "Finance Ops Panels",
    finance_ops_loading: "Loading finance ops panels...",
    finance_ops_load_failed: "Failed to load finance ops panels. Please refresh and retry.",
    vendors_panel: "Vendors",
    bills_panel: "Bills",
    payments_panel: "Payments",
    new_vendor: "New Vendor",
    new_bill: "New Bill",
    new_payment: "New Payment",
    edit_vendor: "Edit Vendor",
    edit_bill: "Edit Bill",
    edit_payment: "Edit Payment",
    total_paid_this_year: "Total Paid This Year",
    over_600: "Over $600",
    required_1099: "1099 Required",
    contract_revenue: "Contract Revenue",
    change_revenue: "Change Revenue",
    total_revenue: "Total Revenue",
    recorded_cost: "Recorded Cost",
    ap_open: "AP Open",
    total_cost: "Total Cost",
    tab_overview: "Overview",
    tab_schedule: "Schedule/Tasks",
    tab_site_logs: "Site Log",
    tab_issues: "Issues",
    tab_payments: "Payments",
    tab_costs: "Costs",
    tab_files: "Files",
    project_detail: "Project Detail",
    source_relation: "Source Links",
    source_estimate: "Source Estimate",
    source_contract: "Source Contract",
    linked_project: "Linked Project",
    project_info: "Project Info",
    customer: "Customer",
    contract_info: "Linked Contract",
    project_progress: "Construction Progress",
    stage_click_tip: "Click stage tags to switch status",
    project_logs: "Construction Logs",
    add_log: "Add Log",
    log_date: "Date",
    log_content: "Content",
    log_image: "Image URL (optional)",
    payment_info: "Payment Info",
    change_order_summary: "Change Order Impact Summary",
    approved_change_total: "Approved Change Total",
    impact_payment_plan_count: "Changes Impacting Payment Plan",
    approved_change_commissionable: "Approved Change (Commissionable)",
    approved_change_non_commissionable: "Approved Change (Non-commissionable)",
    current_contract_total: "Current Contract Total",
    change_order_warn_payment_plan: "Approved change orders impact payment plan. Please review milestones.",
    project_change_orders: "Change Orders",
    create_change_order: "Create Change Order",
    print_change_order_doc: "Print Change Order",
    export_change_order_pdf: "Export PDF",
    mark_sent: "Mark Sent",
    mark_approved: "Mark Approved",
    mark_rejected: "Mark Rejected",
    open_change_order_module: "Open Change Order Module",
    payment_milestones: "Payment Milestones",
    milestone_name: "Milestone Name",
    milestone_type: "Milestone Type",
    trigger_type: "Trigger Type",
    trigger_stage: "Trigger Stage",
    trigger_progress: "Trigger Progress %",
    amount_type: "Amount Type",
    amount_value: "Amount / Percent",
    state: "State",
    trigger_reason: "Trigger Reason",
    mark_reminded: "Mark Reminded",
    mark_paid: "Mark Paid",
    mark_completed: "Mark Completed",
    add_milestone: "Add Milestone",
    update_milestone: "Update Milestone",
    cancel_edit: "Cancel",
    select_contract: "Select Contract",
    no_contracts: "No contracts yet. Create one first.",
    no_milestones: "No payment milestones",
    designer_info: "Designer Collaboration",
    designer_commission: "Designer Commission",
    recalc_commission: "Recalculate",
    commission_amount: "Commission Amount",
    commission_status: "Commission Status",
    commission_base: "Commission Base",
    base_contract_amount: "Base Contract Amount",
    change_order_amount: "Change Order Amount",
    settlement_mode: "Settlement Rule",
    payment_reminder_list: "Project Payment Reminders",
    payment_overview: "Payment Progress Overview",
    finance_snapshot: "Finance Snapshot",
    triggered_unpaid_nodes: "Triggered Unpaid Nodes",
    current_payment_nodes: "Current Payment Nodes",
    recent_paid_node: "Most Recently Paid Node",
    next_trigger_node: "Next Likely Trigger Node",
    view_project_detail: "View Project",
    view_contract_detail: "View Contract",
    default_exclude_change_orders: "Default excludes change order amount",
    delete_milestone: "Delete",
    confirm_del_milestone: "Delete this payment milestone?",
    milestone_state_untriggered: "Untriggered",
    milestone_state_pending: "Triggered (Pending Follow-up)",
    milestone_state_reminded: "Reminded",
    milestone_state_paid: "Paid",
    internal_notes: "Notes / Internal",
    save_notes: "Save Notes",
    notes_saved: "Notes saved",
    no_logs: "No logs",
    value_pending: "Pending",
    value_in_progress: "In Progress",
    value_done: "Done",
    value_open: "Open",
    value_fixed: "Fixed",
    value_verified: "Verified",
    value_paid: "Paid",
    value_unpaid: "Unpaid",
    value_overdue: "Overdue",
    value_draft: "Draft",
    value_sent: "Sent",
    value_approved: "Approved",
    value_accepted: "Accepted",
    value_rejected: "Rejected",
    value_lead: "Lead",
    value_new_lead: "New Lead",
    value_contacted: "Contacted",
    value_site_visit_booked: "On-site Visit Booked",
    value_quoted: "Quoted",
    value_measuring: "Measuring",
    value_quoting: "Quoting",
    value_signed: "Signed",
    value_unsigned: "Unsigned",
    value_completed: "Completed",
    value_lost: "Lost",
    value_customer: "Customer",
    value_not_started: "Not Started",
    value_on_hold: "On Hold",
    value_high: "High",
    value_medium: "Medium",
    value_low: "Low",
    value_owner: "Owner",
    value_manager: "Project Manager",
    value_designer: "Designer",
    value_website: "Website",
    value_houzz: "Houzz",
    value_phone: "Phone",
    value_email: "Email",
    value_referral: "Referral",
    value_walk_in: "Walk-in",
    value_manual: "Manual",
    value_supplier: "Supplier",
    value_subcontractor: "Subcontractor",
    value_1099: "1099 Contractor",
    value_check: "Check",
    value_ach: "ACH",
    value_wire: "Wire",
    value_cash: "Cash",
    value_card: "Card",
    value_visit: "Visit",
    value_note: "Note",
    value_custom_furniture: "Custom Furniture",
    value_bathroom_remodel: "Bathroom Remodel",
    value_kitchen_remodel: "Kitchen Remodel",
    value_full_remodel: "Full Remodel",
    value_other: "Other",
    value_text: "Text",
    value_wechat: "WeChat",
    value_contract_signed: "Contract Signed",
    value_stage_started: "Stage Started",
    value_stage_done: "Stage Completed",
    value_progress_percent: "Progress Reached",
    value_percent: "Percent",
    value_fixed: "Fixed",
    value_untriggered: "Untriggered",
    value_reminded: "Reminded",
    value_pending_settlement: "Pending Settlement",
    value_ungenerated: "Ungenerated",
    value_generated: "Generated",
    value_settled: "Settled",
    value_base_contract_only: "Base Contract Only",
    value_include_change_orders: "Include Change Orders",
    lang_zh: "Chinese",
    lang_en: "English",
    lang_es: "Spanish",
    user_role: "User",
    role_owner: "Owner",
    role_manager: "Project Manager",
    role_designer: "Designer",
    field_contract_amount: "Contract Amount",
    field_pending_amount: "Pending Amount",
    field_cost_amount: "Cost Amount",
    field_profit_amount: "Profit Amount",
    field_phase: "Phase",
    field_owner: "Owner",
    field_log_date: "Log Date",
    field_work_summary: "Work Summary",
    field_crew_info: "Crew/Subcontractor",
    field_materials_info: "Materials",
    field_issue_note: "Issue Note",
    field_template_used: "Template",
    field_photos_json: "Photos",
    field_severity: "Severity",
    field_description: "Description",
    field_received_date: "Received Date",
    field_invoice_no: "Invoice No",
    field_cost_type: "Cost Type",
    field_cost_date: "Cost Date",
    field_url: "URL",
    field_designer_id: "Designer ID",
    field_designer_name: "Designer Name",
    field_designer_commission_type: "Commission Type",
    field_designer_commission_value: "Commission Value",
    field_designer_commission_base: "Commission Base",
    field_followup_type: "Follow-up Type",
    field_content: "Content",
    field_result: "Result",
    field_next_followup_at: "Next Follow-up",
    field_completed: "Completed",
    related_estimates: "Related Estimates",
    source_customer: "Source Customer/Lead",
    followup_records: "Follow-up Records",
    add_followup: "Add Follow-up",
    quick_followup: "Follow-up",
    set_next_followup: "Set Next Follow-up",
    today_due_followups: "Due Today Follow-ups",
    stale_customers_over_3d: "Customers 3+ Days Without Follow-up",
    no_followup_records: "No follow-up records",
    followup_saved: "Follow-up saved",
    no_next_followup: "Not set",
    status_completed: "Completed",
    status_uncompleted: "Uncompleted",
    attachments: "Attachments",
    estimate_attachments: "Estimate Attachments",
    contract_attachments: "Contract Attachments",
    bill_attachments: "Bill Attachments",
    payment_attachments: "Payment Attachments",
    project_file_module: "Site Photos / Project Files",
    site_photos: "Site Photos",
    project_documents: "Project Files",
    upload_file: "Upload File",
    choose_file: "Choose File",
    open_file: "Open File",
    view_attachment: "View Attachment",
    delete_file: "Delete File",
    no_files: "No attachments",
    field_file_category: "Category",
    field_file_size: "File Size",
    field_uploaded_by: "Uploaded By",
    upload_success: "Uploaded",
    file_type_not_supported: "Only jpg/jpeg/png/pdf supported",
    value_file_category_photo: "Photo",
    value_file_category_contract: "Contract",
    value_file_category_estimate: "Estimate",
    value_file_category_invoice: "Invoice",
    value_file_category_change_order: "Change Order",
    value_file_category_completion: "Completion",
    value_file_category_other: "Other",
    value_yes: "Yes",
    value_no: "No",
    custom_contract: "Custom Contract",
    custom_contract_placeholder: "Enter custom contract body terms. Customer, price, and payment schedule still come from this contract.",
    field_custom_contract_enabled: "Use Custom Contract Body",
    field_custom_contract_text: "Custom Contract Body",
  },
  es: {
    app: "CRM de Renovación",
    login: "Iniciar sesión",
    username: "Usuario",
    password: "Contraseña",
    login_tip: "Inicia sesión con tus credenciales",
    logout: "Cerrar sesión",
    admin: "Usuarios",
    dashboard: "Panel",
    customers: "Clientes",
    estimates: "Presupuestos",
    contracts: "Contratos",
    projects: "Proyectos",
    change_orders: "Órdenes de cambio",
    documents: "Documentos",
    finance: "Finanzas",
    settings: "Configuración/Permisos",
    search: "Buscar",
    create: "Crear",
    save: "Guardar",
    reset: "Reiniciar",
    edit: "Editar",
    del: "Eliminar",
    detail: "Detalle",
    generate_estimate: "Generar presupuesto",
    generate_contract: "Generar contrato",
    generate_project: "Generar proyecto",
    view_customer: "Ver cliente",
    view_estimate: "Ver presupuesto",
    view_contract: "Ver contrato",
    view_project: "Ver proyecto",
    print_estimate_doc: "Imprimir presupuesto",
    export_estimate_pdf: "Exportar PDF",
    print_contract_doc: "Imprimir contrato",
    export_contract_pdf: "Exportar PDF",
    confirm_del: "¿Confirmar eliminación?",
    no_data: "Sin datos",
    close: "Cerrar",
    pdf: "PDF",
    dashboard_desc: "Dueño / gerente: vista rápida del estado operativo",
    settings_desc: "Usuarios, permisos y marca",
    monthly_new_leads: "Nuevos leads del mes",
    monthly_estimates_sent: "Presupuestos enviados",
    monthly_contracts_signed: "Contratos firmados",
    monthly_contracted_amount: "Monto contratado",
    active_projects: "Proyectos activos",
    monthly_ar_received: "Cobrado del mes",
    monthly_ar_pending: "AR pendiente",
    monthly_cost: "Costo mensual",
    monthly_gross_profit: "Ganancia bruta",
    stale_followups: "Sin seguimiento 3+ días",
    pending_estimates: "Presupuestos pendientes 7+ días",
    upcoming_payments: "Pagos próximos (7 días)",
    payment_reminders: "Hitos de pago por cobrar",
    payment_plan_module: "Plan de pago / Hitos",
    open_issues: "Problemas abiertos",
    user_admin: "Usuarios y permisos",
    create_user: "Crear usuario",
    create_user_btn: "Crear",
    role: "Rol",
    language: "Idioma",
    modules: "Módulos",
    update: "Actualizar",
    pwd_optional: "Nueva contraseña (opcional)",
    owner_only: "Solo dueño",
    brand_settings: "Marca",
    save_brand: "Guardar marca",
    pdf_lang: "Idioma PDF",
    templates: "Plantillas",
    apply_template: "Aplicar plantilla",
    template_name: "Nombre",
    package_type: "Paquete",
    create_template: "Crear plantilla",
    quick_lead_entry: "Ingreso Rápido de Lead",
    quick_submit_lead: "Guardar Lead",
    filter_source_channel: "Filtro por origen",
    filter_customer_status: "Filtro por estado",
    source_info: "Información de origen",
    inquiry_info: "Información de solicitud",
    preferred_contact: "Contacto preferido",
    recent_followups: "Seguimientos recientes",
    no_followups: "Sin seguimientos",
    confirm_merge_lead: "Este teléfono ya existe. ¿Combinar con el cliente existente?",
    lead_required_hint: "Ingresa al menos nombre o teléfono",
    contract_pdf: "PDF Contrato",
    progress_flow: "Flujo",
    init_flow: "Iniciar flujo",
    reinit_flow: "Reiniciar flujo",
    stage_name: "Etapa",
    stage_status: "Estado",
    pending: "Pendiente",
    in_progress: "En curso",
    done: "Hecho",
    save_stage: "Guardar etapa",
    no_flow: "Aún no hay flujo, inicia desde plantilla",
    actions: "Acciones",
    project_profit_detail: "Detalle de beneficio por proyecto",
    ar_aging: "Antigüedad AR",
    ap_aging: "Antigüedad AP",
    ar_ledger: "Libro AR",
    ap_ledger: "Libro AP",
    bucket: "Rango",
    count: "Cantidad",
    amount: "Monto",
    due_date: "Vencimiento",
    received_amount: "Cobrado",
    paid_amount: "Pagado",
    open_amount: "Pendiente",
    age_days: "Antigüedad(días)",
    revenue: "Ingresos",
    cost: "Costo",
    profit: "Ganancia",
    gross_margin_pct: "Margen %",
    field_id: "ID",
    field_name: "Nombre",
    field_phone: "Teléfono",
    field_email: "Correo",
    field_source: "Origen",
    field_source_channel: "Canal de origen",
    field_source_note: "Nota de origen",
    field_demand_type: "Tipo de demanda",
    field_inquiry_type: "Tipo de consulta",
    field_preferred_contact_method: "Contacto preferido",
    field_budget_range: "Rango de presupuesto",
    field_status: "Estado",
    field_primary_address: "Dirección principal",
    field_other_addresses: "Otras direcciones",
    field_notes: "Notas",
    field_customer_id: "ID Cliente",
    field_lead_id: "ID Lead",
    field_customer_name: "Nombre cliente",
    field_source_type: "Tipo origen",
    field_contract_generated: "Estado contrato",
    field_project_id: "ID Proyecto",
    field_title: "Título",
    field_version: "Versión",
    field_valid_until: "Válido hasta",
    field_subtotal: "Subtotal",
    field_markup_rate: "Margen",
    field_total_amount: "Total",
    field_line_items_json: "Partidas JSON",
    field_estimate_id: "ID Presupuesto",
    field_contract_no: "Nro Contrato",
    field_signed_status: "Estado firma",
    field_signed_date: "Fecha firma",
    field_contract_id: "ID Contrato",
    field_address: "Dirección",
    field_progress_pct: "Progreso %",
    field_start_date: "Inicio",
    field_estimated_finish_date: "Fin estimado",
    field_actual_finish_date: "Fin real",
    field_manager: "Responsable",
    field_order_no: "Nro Orden de cambio",
    field_description: "Descripción",
    field_project_name: "Proyecto",
    field_customer_name: "Cliente",
    field_impact_payment_plan: "Impacta plan de pago",
    field_affect_designer_commission: "Afecta comisión diseñador",
    field_approved_at: "Fecha aprobación",
    field_created_by: "Creado por",
    field_reason: "Razón",
    field_items_json: "Items JSON",
    field_amount_delta: "Cambio monto",
    field_days_delta: "Cambio días",
    field_doc_type: "Tipo doc",
    field_file_name: "Archivo",
    field_tags: "Etiquetas",
    field_visibility: "Visibilidad",
    field_node_name: "Hito pago",
    field_vendor: "Proveedor",
    field_type: "Tipo",
    field_1099_required: "Requiere 1099",
    field_vendor_id: "ID Proveedor",
    field_bill_id: "ID Factura",
    field_bill_no: "Nro Factura",
    field_bill_date: "Fecha de factura",
    field_tax_id: "Tax ID",
    field_w9_received: "W-9 recibido",
    field_category: "Categoría",
    field_method: "Método de pago",
    field_payment_date: "Fecha pago",
    field_reference_no: "Referencia",
    field_updated_at: "Actualizado",
    ar_total: "AR total",
    ar_overdue: "AR vencido",
    ap_total: "AP total",
    ap_overdue: "AP vencido",
    monthly_ap_paid: "AP pagado del mes",
    monthly_cashflow: "Flujo de caja mensual",
    report_1099: "Resumen 1099",
    project_cost_ledger: "Libro de costos del proyecto",
    view_cost_ledger: "Ver libro de costos",
    open_costs: "Costos abiertos",
    cost_by_category: "Costos por categoría",
    payments_total: "Total costos pagados",
    vendor_ledger: "Libro del proveedor",
    view_ledger: "Ver libro",
    vendor_basic_info: "Información del proveedor",
    bills_payable: "Facturas (por pagar)",
    payments_paid: "Pagos (pagados)",
    open_bills_total: "Total facturas abiertas",
    current_outstanding_balance: "Saldo pendiente actual",
    finance_ops_panels: "Paneles operativos",
    finance_ops_loading: "Cargando paneles operativos...",
    finance_ops_load_failed: "No se pudieron cargar los paneles operativos. Actualiza e inténtalo de nuevo.",
    vendors_panel: "Proveedores",
    bills_panel: "Facturas",
    payments_panel: "Pagos",
    new_vendor: "Nuevo proveedor",
    new_bill: "Nueva factura",
    new_payment: "Nuevo pago",
    edit_vendor: "Editar proveedor",
    edit_bill: "Editar factura",
    edit_payment: "Editar pago",
    total_paid_this_year: "Pagado este año",
    over_600: "Supera $600",
    required_1099: "Requiere 1099",
    contract_revenue: "Ingreso por contrato",
    change_revenue: "Ingreso por cambios",
    total_revenue: "Ingreso total",
    recorded_cost: "Costo registrado",
    ap_open: "AP pendiente",
    total_cost: "Costo total",
    tab_overview: "Resumen",
    tab_schedule: "Tareas",
    tab_site_logs: "Bitácora",
    tab_issues: "Incidencias",
    tab_payments: "Pagos",
    tab_costs: "Costos",
    tab_files: "Archivos",
    project_detail: "Detalle del proyecto",
    source_relation: "Vínculos de origen",
    source_estimate: "Presupuesto origen",
    source_contract: "Contrato origen",
    linked_project: "Proyecto vinculado",
    project_info: "Información del proyecto",
    customer: "Cliente",
    contract_info: "Contrato asociado",
    project_progress: "Progreso de obra",
    stage_click_tip: "Haz clic en la etapa para cambiar estado",
    project_logs: "Bitácora",
    add_log: "Agregar registro",
    log_date: "Fecha",
    log_content: "Contenido",
    log_image: "URL de imagen (opcional)",
    payment_info: "Información de pago",
    change_order_summary: "Resumen de impacto de cambios",
    approved_change_total: "Total cambios aprobados",
    impact_payment_plan_count: "Cambios que impactan plan de pago",
    approved_change_commissionable: "Cambios aprobados (con comisión)",
    approved_change_non_commissionable: "Cambios aprobados (sin comisión)",
    current_contract_total: "Total contractual actual",
    change_order_warn_payment_plan: "Hay cambios aprobados que impactan el plan de pago. Revisa los hitos.",
    project_change_orders: "Órdenes de cambio",
    create_change_order: "Crear orden de cambio",
    print_change_order_doc: "Imprimir orden de cambio",
    export_change_order_pdf: "Exportar PDF",
    mark_sent: "Marcar enviado",
    mark_approved: "Marcar aprobado",
    mark_rejected: "Marcar rechazado",
    open_change_order_module: "Abrir módulo de cambios",
    payment_milestones: "Hitos de pago",
    milestone_name: "Nombre del hito",
    milestone_type: "Tipo de hito",
    trigger_type: "Tipo de disparador",
    trigger_stage: "Etapa disparadora",
    trigger_progress: "Progreso disparador %",
    amount_type: "Tipo de monto",
    amount_value: "Monto / Porcentaje",
    state: "Estado",
    trigger_reason: "Razón de disparo",
    mark_reminded: "Marcar recordado",
    mark_paid: "Marcar cobrado",
    mark_completed: "Marcar completado",
    add_milestone: "Agregar hito",
    update_milestone: "Actualizar hito",
    cancel_edit: "Cancelar",
    select_contract: "Seleccionar contrato",
    no_contracts: "No hay contratos. Crea uno primero.",
    no_milestones: "Sin hitos de pago",
    designer_info: "Colaboración de diseñador",
    designer_commission: "Comisión del diseñador",
    recalc_commission: "Recalcular",
    commission_amount: "Monto de comisión",
    commission_status: "Estado de comisión",
    commission_base: "Base de comisión",
    base_contract_amount: "Monto contrato base",
    change_order_amount: "Monto de cambios",
    settlement_mode: "Regla de liquidación",
    payment_reminder_list: "Recordatorios de cobro del proyecto",
    payment_overview: "Resumen de avance de cobro",
    finance_snapshot: "Resumen financiero",
    triggered_unpaid_nodes: "Hitos activados sin cobro",
    current_payment_nodes: "Nodos de pago actuales",
    recent_paid_node: "Último hito cobrado",
    next_trigger_node: "Próximo hito probable",
    view_project_detail: "Ver proyecto",
    view_contract_detail: "Ver contrato",
    default_exclude_change_orders: "Por defecto no incluye órdenes de cambio",
    delete_milestone: "Eliminar",
    confirm_del_milestone: "¿Eliminar este hito de pago?",
    milestone_state_untriggered: "Sin disparar",
    milestone_state_pending: "Activado (pendiente de cobro)",
    milestone_state_reminded: "Recordado",
    milestone_state_paid: "Cobrado",
    internal_notes: "Notas internas",
    save_notes: "Guardar notas",
    notes_saved: "Notas guardadas",
    no_logs: "Sin registros",
    value_pending: "Pendiente",
    value_in_progress: "En curso",
    value_done: "Hecho",
    value_open: "Abierto",
    value_fixed: "Corregido",
    value_verified: "Verificado",
    value_paid: "Pagado",
    value_unpaid: "No pagado",
    value_overdue: "Vencido",
    value_draft: "Borrador",
    value_sent: "Enviado",
    value_approved: "Aprobado",
    value_accepted: "Aceptado",
    value_rejected: "Rechazado",
    value_lead: "Lead",
    value_new_lead: "Lead nuevo",
    value_contacted: "Contactado",
    value_site_visit_booked: "Visita agendada",
    value_quoted: "Presupuestado",
    value_measuring: "Medición",
    value_quoting: "Cotizando",
    value_signed: "Firmado",
    value_unsigned: "Sin firmar",
    value_completed: "Completado",
    value_lost: "Perdido",
    value_customer: "Cliente",
    value_not_started: "No iniciado",
    value_on_hold: "En pausa",
    value_high: "Alta",
    value_medium: "Media",
    value_low: "Baja",
    value_owner: "Dueño",
    value_manager: "Gerente de proyecto",
    value_designer: "Diseñador",
    value_website: "Sitio web",
    value_houzz: "Houzz",
    value_phone: "Teléfono",
    value_email: "Correo",
    value_referral: "Referido",
    value_walk_in: "Visita en tienda",
    value_manual: "Ingreso manual",
    value_supplier: "Proveedor",
    value_subcontractor: "Subcontratista",
    value_1099: "Contratista 1099",
    value_check: "Cheque",
    value_ach: "ACH",
    value_wire: "Transferencia",
    value_cash: "Efectivo",
    value_card: "Tarjeta",
    value_visit: "Visita",
    value_note: "Nota",
    value_custom_furniture: "Muebles a medida",
    value_bathroom_remodel: "Remodelación de baño",
    value_kitchen_remodel: "Remodelación de cocina",
    value_full_remodel: "Remodelación completa",
    value_other: "Otro",
    value_text: "Mensaje",
    value_wechat: "WeChat",
    value_contract_signed: "Contrato firmado",
    value_stage_started: "Etapa iniciada",
    value_stage_done: "Etapa completada",
    value_progress_percent: "Progreso alcanzado",
    value_percent: "Porcentaje",
    value_fixed: "Fijo",
    value_untriggered: "No disparado",
    value_reminded: "Recordado",
    value_pending_settlement: "Pendiente de liquidar",
    value_ungenerated: "Sin generar",
    value_generated: "Generado",
    value_settled: "Liquidado",
    value_base_contract_only: "Solo contrato base",
    value_include_change_orders: "Incluye cambios",
    lang_zh: "Chino",
    lang_en: "Inglés",
    lang_es: "Español",
    user_role: "Usuario",
    role_owner: "Dueño",
    role_manager: "Gerente de proyecto",
    role_designer: "Diseñador",
    field_contract_amount: "Monto contrato",
    field_pending_amount: "Monto pendiente",
    field_cost_amount: "Monto costo",
    field_profit_amount: "Monto ganancia",
    field_phase: "Fase",
    field_owner: "Responsable",
    field_log_date: "Fecha bitácora",
    field_work_summary: "Resumen trabajo",
    field_crew_info: "Cuadrilla/Subcontrata",
    field_materials_info: "Materiales",
    field_issue_note: "Nota incidencia",
    field_template_used: "Plantilla",
    field_photos_json: "Fotos",
    field_severity: "Severidad",
    field_description: "Descripción",
    field_received_date: "Fecha cobro",
    field_invoice_no: "Nro factura",
    field_cost_type: "Tipo costo",
    field_cost_date: "Fecha costo",
    field_url: "URL",
    field_designer_id: "ID Diseñador",
    field_designer_name: "Nombre diseñador",
    field_designer_commission_type: "Tipo comisión",
    field_designer_commission_value: "Valor comisión",
    field_designer_commission_base: "Base comisión",
    field_followup_type: "Tipo seguimiento",
    field_content: "Contenido",
    field_result: "Resultado",
    field_next_followup_at: "Próximo seguimiento",
    field_completed: "Completado",
    related_estimates: "Presupuestos asociados",
    source_customer: "Cliente/Lead origen",
    followup_records: "Registros de seguimiento",
    add_followup: "Agregar seguimiento",
    quick_followup: "Seguimiento",
    set_next_followup: "Programar próximo seguimiento",
    today_due_followups: "Seguimientos para hoy",
    stale_customers_over_3d: "Clientes sin seguimiento por 3+ días",
    no_followup_records: "Sin registros de seguimiento",
    followup_saved: "Seguimiento guardado",
    no_next_followup: "Sin programación",
    status_completed: "Completado",
    status_uncompleted: "Pendiente",
    attachments: "Adjuntos",
    estimate_attachments: "Adjuntos del presupuesto",
    contract_attachments: "Adjuntos del contrato",
    bill_attachments: "Adjuntos de factura",
    payment_attachments: "Adjuntos de pago",
    project_file_module: "Fotos de obra / Archivos del proyecto",
    site_photos: "Fotos de obra",
    project_documents: "Archivos del proyecto",
    upload_file: "Subir archivo",
    choose_file: "Elegir archivo",
    open_file: "Abrir archivo",
    view_attachment: "Ver adjunto",
    delete_file: "Eliminar archivo",
    no_files: "Sin adjuntos",
    field_file_category: "Categoría",
    field_file_size: "Tamaño",
    field_uploaded_by: "Subido por",
    upload_success: "Subido",
    file_type_not_supported: "Solo jpg/jpeg/png/pdf",
    value_file_category_photo: "Foto",
    value_file_category_contract: "Contrato",
    value_file_category_estimate: "Presupuesto",
    value_file_category_invoice: "Factura",
    value_file_category_change_order: "Orden de cambio",
    value_file_category_completion: "Finalización",
    value_file_category_other: "Otro",
    value_yes: "Sí",
    value_no: "No",
    custom_contract: "Contrato personalizado",
    custom_contract_placeholder: "Escriba los términos personalizados. Cliente, precio y plan de pago siguen usando este contrato.",
    field_custom_contract_enabled: "Usar cuerpo personalizado",
    field_custom_contract_text: "Cuerpo personalizado",
  },
};

const ALL_MODULES = ["dashboard", "customers", "estimates", "contracts", "projects", "change_orders", "documents", "finance", "settings"];
const DEFAULT_PROJECT_STAGE_NAMES = ["进场", "拆除", "水电改造", "柜体安装", "台面与五金", "验收"];

const MODULE_DESC = {
  dashboard: "dashboard_desc",
  customers: "customers",
  estimates: "estimates",
  contracts: "contracts",
  projects: "projects",
  change_orders: "change_orders",
  documents: "documents",
  finance: "finance",
  settings: "settings_desc",
};

const CRUD_SCHEMA = {
  customers: {
    fields: [
      "name",
      "phone",
      "email",
      "source_channel",
      "source_note",
      "inquiry_type",
      "preferred_contact_method",
      "status",
      "primary_address",
      "other_addresses",
      "notes",
    ],
    labels: { name: "name", phone: "phone", email: "email", source: "source", demand_type: "demand", budget_range: "budget", status: "status", primary_address: "address", other_addresses: "addresses", notes: "notes" },
    table: ["id", "name", "phone", "source_channel", "inquiry_type", "status", "updated_at"],
  },
  estimates: {
    fields: ["customer_id", "project_id", "title", "address", "version", "status", "valid_until", "subtotal", "markup_rate", "total_amount", "line_items_json"],
    table: ["id", "customer_name", "source_type", "title", "status", "total_amount", "contract_generated"],
  },
  contracts: {
    fields: ["customer_id", "project_id", "estimate_id", "title", "address", "contract_no", "total_amount", "payment_plan_json", "signed_status", "signed_date", "custom_contract_enabled", "custom_contract_text", "attachment_url"],
    table: ["id", "contract_no", "signed_status", "total_amount", "signed_date"],
  },
  projects: {
    fields: [
      "customer_id",
      "contract_id",
      "estimate_id",
      "name",
      "address",
      "status",
      "progress_pct",
      "start_date",
      "estimated_finish_date",
      "actual_finish_date",
      "manager",
      "designer_id",
      "designer_name",
      "designer_commission_type",
      "designer_commission_value",
      "designer_commission_base",
      "notes",
    ],
    table: ["id", "name", "status", "progress_pct", "manager", "designer_name", "estimated_finish_date"],
  },
  change_orders: {
    fields: [
      "project_id",
      "contract_id",
      "customer_id",
      "title",
      "description",
      "amount_delta",
      "impact_payment_plan",
      "affect_designer_commission",
      "status",
      "approved_at",
      "notes",
    ],
    table: [
      "id",
      "order_no",
      "title",
      "project_name",
      "customer_name",
      "amount_delta",
      "status",
      "impact_payment_plan",
      "affect_designer_commission",
      "created_at",
    ],
  },
  documents: {
    fields: ["customer_id", "project_id", "doc_type", "file_name", "tags", "url", "visibility"],
    table: ["id", "doc_type", "file_name", "tags", "visibility"],
  },
};

const state = {
  user: null,
  locale: "zh",
  brand: null,
  pdfLang: "en",
  module: "dashboard",
  editId: null,
  projectDetail: null,
  contractMilestoneContractId: null,
  editingMilestoneId: null,
  customerSourceFilter: "",
  customerStatusFilter: "",
  changeOrderStatusFilter: "",
  changeOrderProjectFilter: "",
  financeVendorEditId: null,
  financeBillEditId: null,
  financePaymentEditId: null,
  financePrefillProjectId: null,
  financePrefillMode: "",
  crudFormOpen: false,
};

const q = (s) => document.querySelector(s);
const CUSTOMER_STATUS_FLOW = ["新线索", "已联系", "已预约上门", "已报价", "已签约", "已流失"];
const SOURCE_CHANNEL_OPTIONS = ["website", "houzz", "phone", "referral", "walk_in", "manual"];
const INQUIRY_TYPE_OPTIONS = ["custom_furniture", "bathroom_remodel", "kitchen_remodel", "full_remodel", "other"];
const CONTACT_METHOD_OPTIONS = ["phone", "text", "email", "wechat"];
const FOLLOWUP_TYPE_OPTIONS = ["phone", "text", "wechat", "email", "visit", "note"];
const FILE_CATEGORY_OPTIONS = ["photo", "contract", "estimate", "invoice", "change_order", "completion", "other"];
const CHANGE_ORDER_STATUS_OPTIONS = ["draft", "sent", "approved", "rejected"];
const VENDOR_TYPE_OPTIONS = ["supplier", "subcontractor", "1099"];
const PAYMENT_METHOD_OPTIONS = ["check", "ach", "wire", "cash", "card", "other"];
const FILE_CATEGORY_BY_ENTITY = {
  customer: ["photo", "other"],
  estimate: ["estimate", "photo", "other"],
  contract: ["contract", "invoice", "photo", "other"],
  project: ["photo", "change_order", "completion", "contract", "invoice", "other"],
  bill: ["invoice", "contract", "other"],
  payment: ["invoice", "contract", "other"],
};

function renderOptionList(values, current, field = "") {
  return values.map((v) => {
    const selected = String(current ?? "") === String(v) ? "selected" : "";
    const label = valueLabel(field, v) || valueLabel("", v) || v;
    return `<option value="${esc(v)}" ${selected}>${esc(label)}</option>`;
  }).join("");
}

function t(k) {
  return (I18N[state.locale] && I18N[state.locale][k]) || I18N.zh[k] || k;
}

function esc(v) {
  return String(v ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

function fieldLabel(key) {
  return t(`field_${key}`) || key;
}

function hasI18n(k) {
  return Object.prototype.hasOwnProperty.call(I18N[state.locale] || {}, k)
    || Object.prototype.hasOwnProperty.call(I18N.zh || {}, k);
}

function normalizeEnum(v) {
  const raw = String(v ?? "").trim();
  if (!raw) return "";
  const normalized = raw.toLowerCase().replaceAll("-", "_").replace(/\s+/g, "_");
  const exactMap = {
    "待开工": "not_started",
    "施工中": "in_progress",
    "已完工": "completed",
    "暂停": "on_hold",
    "未开始": "pending",
    "进行中": "in_progress",
    "已完成": "done",
    "待处理": "open",
    "已修复": "fixed",
    "已验收": "verified",
    "草稿": "draft",
    "已发送": "sent",
    "已确认": "approved",
    "已接受": "approved",
    "已拒绝": "rejected",
    "线索": "lead",
    "新线索": "new_lead",
    "已联系": "contacted",
    "已预约上门": "site_visit_booked",
    "已报价": "quoted",
    "测量中": "measuring",
    "报价中": "quoting",
    "已签约": "signed",
    "未签字": "unsigned",
    "流失": "lost",
    "逾期": "overdue",
    "已支付": "paid",
    "未支付": "unpaid",
    "已提醒": "reminded",
    "未触发": "untriggered",
    "待结算": "pending_settlement",
    "已结算": "settled",
    "未生成": "ungenerated",
    "官网": "website",
    "电话": "phone",
    "短信": "text",
    "邮箱": "email",
    "微信": "wechat",
    "上门": "visit",
    "备注": "note",
    "按比例": "percent",
    "固定金额": "fixed",
    "仅主合同": "base_contract_only",
    "含变更单": "include_change_orders",
    "设计师": "designer",
  };
  const normalizedMap = {
    notstarted: "not_started",
    not_started: "not_started",
    inprogress: "in_progress",
    in_progress: "in_progress",
    onhold: "on_hold",
    on_hold: "on_hold",
    completed: "completed",
    done: "done",
    pending: "pending",
    open: "open",
    fixed: "fixed",
    verified: "verified",
    paid: "paid",
    unpaid: "unpaid",
    overdue: "overdue",
    draft: "draft",
    sent: "sent",
    accepted: "accepted",
    rejected: "rejected",
    lead: "lead",
    new_lead: "new_lead",
    contacted: "contacted",
    site_visit_booked: "site_visit_booked",
    quoted: "quoted",
    measuring: "measuring",
    quoting: "quoting",
    signed: "signed",
    unsigned: "unsigned",
    lost: "lost",
    owner: "owner",
    manager: "manager",
    designer: "designer",
    high: "high",
    medium: "medium",
    low: "low",
    proceso: "in_progress",
    en_curso: "in_progress",
    pendiente: "pending",
    abierto: "open",
    vencido: "overdue",
    pagado: "paid",
    borrador: "draft",
    enviado: "sent",
    aprobado: "approved",
    aceptado: "approved",
    approved: "approved",
    accepted: "approved",
    rechazado: "rejected",
    firmado: "signed",
    sin_firmar: "unsigned",
    completado: "completed",
    perdido: "lost",
    reminded: "reminded",
    untriggered: "untriggered",
    pending_settlement: "pending_settlement",
    ungenerated: "ungenerated",
    settled: "settled",
    percent: "percent",
    fixed: "fixed",
    visit: "visit",
    note: "note",
    base_contract_only: "base_contract_only",
    include_change_orders: "include_change_orders",
  };
  return exactMap[raw] || normalizedMap[normalized] || normalized;
}

function valueLabel(field, val) {
  const raw = String(val ?? "").trim();
  if (!raw) return null;
  const key = normalizeEnum(raw);
  const f = String(field || "").toLowerCase();
  const candidates = [];
  if (f) {
    candidates.push(`value_${f}_${key}`);
    candidates.push(`value_${f}_${raw.toLowerCase().replace(/\s+/g, "_")}`);
  }
  candidates.push(`value_${key}`);
  for (const k of candidates) {
    if (hasI18n(k)) return t(k);
  }
  return null;
}

function displayValue(field, val) {
  if (val === null || val === undefined || val === "") return "-";
  const translated = valueLabel(field, val);
  if (translated) return esc(translated);
  const key = String(field || "").toLowerCase();
  if (key === "impact_payment_plan" || key === "affect_designer_commission") {
    return Number(val) ? esc(t("value_yes")) : esc(t("value_no"));
  }
  if (key === "progress_pct") return `${esc(fmt(val))}%`;
  if (typeof val === "number" || /(_amount|_cost|_pct|subtotal|markup_rate|days_delta|age_days|count)$/.test(key)) {
    return esc(fmt(val));
  }
  return esc(val);
}

function fmt(v) {
  if (v === null || v === undefined || v === "") return "-";
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return n.toLocaleString(state.locale === "zh" ? "zh-CN" : state.locale === "es" ? "es-ES" : "en-US", { maximumFractionDigits: 2 });
}

function fmtMoney(v) {
  if (v === null || v === undefined || v === "") return "-";
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return `$${Math.round(n).toLocaleString("en-US")}`;
}

function milestoneStateLabel(stateKey) {
  const key = normalizeEnum(stateKey || "untriggered");
  const map = {
    untriggered: "milestone_state_untriggered",
    pending: "milestone_state_pending",
    reminded: "milestone_state_reminded",
    paid: "milestone_state_paid",
  };
  return t(map[key] || key);
}

function triggerTypeLabel(triggerType) {
  const key = normalizeEnum(triggerType || "");
  const map = {
    contract_signed: "value_contract_signed",
    stage_started: "value_stage_started",
    stage_done: "value_stage_done",
    progress_percent: "value_progress_percent",
  };
  return t(map[key] || key);
}

function amountTypeLabel(amountType) {
  const key = normalizeEnum(amountType || "");
  if (key === "percent") return t("value_percent");
  if (key === "fixed") return t("value_fixed");
  return key || "-";
}

function applyBrand() {
  const b = state.brand || {};
  if (b.primary_color) document.documentElement.style.setProperty("--main", b.primary_color);
  if (b.dark_color) document.documentElement.style.setProperty("--main-2", b.dark_color);
  if (b.accent_color) document.documentElement.style.setProperty("--accent", b.accent_color);
  if (b.light_bg) document.documentElement.style.setProperty("--bg", b.light_bg);
  if (q("#brand-name")) q("#brand-name").textContent = "OAKLIAN";
  if (q("#brand-subtitle")) q("#brand-subtitle").textContent = "REMODELING";
  if (q("#brand-tagline")) q("#brand-tagline").textContent = "REMODELING & CONSTRUCTION";
  if (q("#brand-icon")) q("#brand-icon").src = "/assets/images/logo-oaklian-light.png";
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData) && !("Content-Type" in headers)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(path, {
    headers,
    ...options,
  });
  let payload = null;
  try {
    payload = await res.json();
  } catch {
    payload = null;
  }
  if (!res.ok) {
    const err = new Error((payload && payload.error) || `HTTP ${res.status}`);
    err.status = res.status;
    err.payload = payload;
    throw err;
  }
  return payload;
}

function can(module) {
  if (!state.user) return false;
  if (state.user.role === "owner") return true;
  return (state.user.modules || []).includes(module);
}

function availableModules() {
  return ALL_MODULES.filter((m) => can(m));
}

function renderLogin() {
  const root = q("#login-view");
  root.innerHTML = `
    <section class="login-card">
      <img src="/assets/images/logo-oaklian-dark.png" alt="Oaklian Remodeling Logo" class="login-logo" />
      <h2>OAKLIAN REMODELING</h2>
      <p class="login-subtitle">${t("login_tip")}</p>
      <div class="field"><label>${t("username")}</label><input id="login-username" /></div>
      <div class="field"><label>${t("password")}</label><input id="login-password" type="password" /></div>
      <div class="row gap" style="margin-top:10px;"><button id="login-btn">${t("login")}</button></div>
    </section>
  `;
  q("#login-btn").addEventListener("click", async () => {
    const username = q("#login-username").value.trim();
    const password = q("#login-password").value.trim();
    try {
      const r = await api("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) });
      state.user = r.user;
      state.locale = state.user.language || "zh";
      state.pdfLang = state.locale;
      state.brand = await api("/api/company/settings");
      applyBrand();
      q("#login-view").classList.add("hidden");
      q("#app-view").classList.remove("hidden");
      if (!availableModules().includes(state.module)) state.module = availableModules()[0] || "dashboard";
      renderApp();
    } catch (e) {
      alert(e.message);
    }
  });
}

function setPageHeader() {
  if (q("#page-title")) q("#page-title").textContent = t(state.module);
  if (q("#page-desc")) q("#page-desc").textContent = t(MODULE_DESC[state.module] || state.module);
  if (q("#logout-btn")) q("#logout-btn").textContent = t("logout");

  if (q("#lang-select")) {
    const currentLang = q("#lang-select").value || state.locale;
    q("#lang-select").innerHTML = `
      <option value="zh">${t("lang_zh")}</option>
      <option value="en">${t("lang_en")}</option>
      <option value="es">${t("lang_es")}</option>
    `;
    q("#lang-select").value = currentLang || state.locale;
  }
  if (q("#user-meta") && state.user) {
    const roleLabel = state.user.role === "owner" ? t("role_owner") : state.user.role === "designer" ? t("role_designer") : t("role_manager");
    q("#user-meta").textContent = `${state.user.username} / ${roleLabel}`;
  }
}

function renderMenu() {
  const menu = q("#menu");
  const mods = availableModules();
  menu.innerHTML = mods.map((m) => `<button data-m="${m}" class="${state.module === m ? "active" : ""}">${t(m)}</button>`).join("");
  menu.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.module = btn.dataset.m;
      state.editId = null;
      renderApp();
    });
  });
}

function renderList(container, items, renderItem) {
  container.innerHTML = items && items.length
    ? `<div class="simple-list">${items.map((x) => `<div class="list-item">${renderItem(x)}</div>`).join("")}</div>`
    : `<div class="list-item">${t("no_data")}</div>`;
}

async function fetchPaymentReminders() {
  return api("/api/payment-reminders");
}

async function openContractDetail(contractId) {
  if (!contractId) return;
  const cid = Number(contractId);
  state.module = "contracts";
  state.editId = String(cid);
  state.contractMilestoneContractId = cid;
  state.editingMilestoneId = null;
  await renderApp();
  const row = await api(`/api/contracts/${cid}`);
  renderForm("contracts", row);
  await renderRecordLinkPanel("contracts", row);
  await renderEntityAttachmentPanel({
    hostSelector: "#record-file-panel",
    entityType: "contract",
    entityId: row.id,
    title: t("contract_attachments"),
    defaultCategory: "contract",
  });
  await renderContractChangeOrderPanel(row);
}

async function openCustomerDetail(customerId) {
  if (!customerId) return;
  const cid = Number(customerId);
  state.module = "customers";
  state.editId = String(cid);
  await renderApp();
  const row = await api(`/api/customers/${cid}`);
  renderForm("customers", row);
  await renderCustomerEstimatePanel(row);
  await renderCustomerFollowupPanel(row);
  await renderEntityAttachmentPanel({
    hostSelector: "#customer-file-panel",
    entityType: "customer",
    entityId: row.id,
    title: t("attachments"),
    defaultCategory: "other",
  });
}

async function openEstimateDetail(estimateId) {
  if (!estimateId) return;
  const eid = Number(estimateId);
  state.module = "estimates";
  state.editId = String(eid);
  await renderApp();
  const row = await api(`/api/estimates/${eid}`);
  renderForm("estimates", row);
  await renderRecordLinkPanel("estimates", row);
  await renderEntityAttachmentPanel({
    hostSelector: "#record-file-panel",
    entityType: "estimate",
    entityId: row.id,
    title: t("estimate_attachments"),
    defaultCategory: "estimate",
  });
}

async function openProjectDetail(projectId) {
  if (!projectId) return;
  const pid = Number(projectId);
  state.module = "projects";
  await renderApp();
  await renderProjectDetail(pid);
}

async function openFinanceFromProject(projectId, mode = "") {
  const pid = Number(projectId || 0);
  if (!pid) return;
  closeProjectDetailDrawer();
  state.module = "finance";
  state.financePrefillProjectId = pid;
  state.financePrefillMode = mode || "";
  await renderApp();
  const target = mode === "payment" ? q("#finance-payment-form") : q("#finance-bill-form");
  if (target && typeof target.scrollIntoView === "function") {
    target.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

async function openChangeOrderDetail(changeOrderId) {
  if (!changeOrderId) return;
  const coid = Number(changeOrderId);
  state.module = "change_orders";
  state.editId = String(coid);
  await renderApp();
  const row = await api(`/api/change-orders/${coid}`);
  renderForm("change_orders", row);
}

async function addCustomerFollowup(customerId, payload) {
  return api(`/api/customers/${customerId}/followups`, { method: "POST", body: JSON.stringify(payload) });
}

async function markFollowupCompleted(followupId) {
  return api(`/api/followups/${followupId}/mark-completed`, { method: "POST" });
}

function fmtFileSize(bytes) {
  const num = Number(bytes || 0);
  if (!Number.isFinite(num) || num <= 0) return "0 B";
  if (num < 1024) return `${num} B`;
  if (num < 1024 * 1024) return `${(num / 1024).toFixed(1)} KB`;
  return `${(num / (1024 * 1024)).toFixed(1)} MB`;
}

function fileCategoryLabel(category) {
  return valueLabel("file_category", category) || category || "-";
}

function entityFileCategoryOptions(entityType) {
  return FILE_CATEGORY_BY_ENTITY[entityType] || FILE_CATEGORY_OPTIONS;
}

async function listEntityFiles(entityType, entityId, category = "") {
  const qs = new URLSearchParams({
    entity_type: entityType,
    entity_id: String(entityId || ""),
  });
  if (category) qs.set("category", category);
  return api(`/api/files?${qs.toString()}`);
}

async function uploadEntityFile(entityType, entityId, category, file) {
  const fd = new FormData();
  fd.append("entity_type", entityType);
  fd.append("entity_id", String(entityId));
  fd.append("category", category || "other");
  fd.append("file", file);
  return api("/api/files/upload", { method: "POST", body: fd });
}

async function deleteEntityFile(fileId) {
  return api(`/api/files/${fileId}`, { method: "DELETE" });
}

async function renderEntityAttachmentPanel({
  hostSelector,
  entityType,
  entityId,
  title,
  defaultCategory = "other",
  categories = [],
}) {
  const host = q(hostSelector);
  if (!host) return;
  if (!entityId) {
    host.innerHTML = `<h4>${title}</h4><div class="list-item">${t("no_data")}</div>`;
    return;
  }
  const rows = await listEntityFiles(entityType, entityId);
  const catOptions = categories.length ? categories : entityFileCategoryOptions(entityType);
  host.innerHTML = `
    <h4>${title}</h4>
    <div class="file-upload-row">
      <select id="${entityType}-file-category">
        ${renderOptionList(catOptions, defaultCategory, "file_category")}
      </select>
      <input id="${entityType}-file-input" type="file" accept=".jpg,.jpeg,.png,.pdf" />
      <button id="${entityType}-file-upload-btn">${t("upload_file")}</button>
    </div>
    <div class="simple-list" style="margin-top:10px;">
      ${rows.length ? rows.map((f) => `
        <div class="list-item file-item-row">
          <div class="file-main">
            <div><b>${esc(f.original_name || f.filename || "-")}</b></div>
            <div>${fieldLabel("file_category")}：${esc(fileCategoryLabel(f.category))}</div>
            <div>${fieldLabel("file_size")}：${esc(fmtFileSize(f.file_size || 0))}</div>
            <div>${fieldLabel("uploaded_by")}：${esc(f.uploaded_by_name || "-")} · ${esc(f.created_at || "-")}</div>
          </div>
          <div class="row gap">
            <a href="${esc(f.url || "#")}" target="_blank" class="btn-link">${t("open_file")}</a>
            <button data-act="del-file" data-id="${f.id}" class="danger">${t("delete_file")}</button>
          </div>
        </div>
      `).join("") : `<div class="list-item">${t("no_files")}</div>`}
    </div>
  `;
  const uploadBtn = q(`#${entityType}-file-upload-btn`);
  if (uploadBtn) {
    uploadBtn.addEventListener("click", async () => {
      const fileInput = q(`#${entityType}-file-input`);
      const category = q(`#${entityType}-file-category`)?.value || defaultCategory;
      const file = fileInput?.files?.[0];
      if (!file) return;
      const lower = (file.name || "").toLowerCase();
      if (!(/\.(jpg|jpeg|png|pdf)$/i.test(lower))) {
        alert(t("file_type_not_supported"));
        return;
      }
      await uploadEntityFile(entityType, entityId, category, file);
      await renderEntityAttachmentPanel({ hostSelector, entityType, entityId, title, defaultCategory, categories: catOptions });
      alert(t("upload_success"));
    });
  }
  host.querySelectorAll("button[data-act='del-file']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm(t("confirm_del"))) return;
      await deleteEntityFile(btn.dataset.id);
      await renderEntityAttachmentPanel({ hostSelector, entityType, entityId, title, defaultCategory, categories: catOptions });
    });
  });
}

async function renderProjectAttachmentPanel(projectId) {
  const host = q("#project-file-panel");
  if (!host) return;
  const files = await listEntityFiles("project", projectId);
  const photos = files.filter((f) => f.is_image || ["photo", "completion"].includes(normalizeEnum(f.category || "")));
  const docs = files.filter((f) => !(f.is_image || ["photo", "completion"].includes(normalizeEnum(f.category || ""))));

  host.innerHTML = `
    <h4>${t("project_file_module")}</h4>
    <div class="file-upload-row">
      <select id="project-file-category">
        ${renderOptionList(entityFileCategoryOptions("project"), "photo", "file_category")}
      </select>
      <input id="project-file-input" type="file" accept=".jpg,.jpeg,.png,.pdf" />
      <button id="project-file-upload-btn">${t("upload_file")}</button>
    </div>
    <div class="grid-2 compact" style="margin-top:10px;">
      <div>
        <div class="kpi-subtitle">${t("site_photos")}</div>
        <div class="file-thumb-grid">
          ${photos.length ? photos.map((f) => `
            <div class="file-thumb-card">
              <a href="${esc(f.url || "#")}" target="_blank">
                <img src="${esc(f.url || "")}" alt="${esc(f.original_name || f.filename || "")}" class="file-thumb" />
              </a>
              <div class="file-thumb-meta">${esc(f.original_name || f.filename || "-")}</div>
              <div class="row gap">
                <a href="${esc(f.url || "#")}" target="_blank" class="btn-link">${t("open_file")}</a>
                <button data-act="del-file" data-id="${f.id}" class="danger">${t("delete_file")}</button>
              </div>
            </div>
          `).join("") : `<div class="list-item">${t("no_files")}</div>`}
        </div>
      </div>
      <div>
        <div class="kpi-subtitle">${t("project_documents")}</div>
        <div class="simple-list">
          ${docs.length ? docs.map((f) => `
            <div class="list-item file-item-row">
              <div class="file-main">
                <div><b>${esc(f.original_name || f.filename || "-")}</b></div>
                <div>${fieldLabel("file_category")}：${esc(fileCategoryLabel(f.category))}</div>
                <div>${fieldLabel("file_size")}：${esc(fmtFileSize(f.file_size || 0))}</div>
                <div>${fieldLabel("uploaded_by")}：${esc(f.uploaded_by_name || "-")} · ${esc(f.created_at || "-")}</div>
              </div>
              <div class="row gap">
                <a href="${esc(f.url || "#")}" target="_blank" class="btn-link">${t("open_file")}</a>
                <button data-act="del-file" data-id="${f.id}" class="danger">${t("delete_file")}</button>
              </div>
            </div>
          `).join("") : `<div class="list-item">${t("no_files")}</div>`}
        </div>
      </div>
    </div>
  `;

  q("#project-file-upload-btn")?.addEventListener("click", async () => {
    const file = q("#project-file-input")?.files?.[0];
    if (!file) return;
    const lower = (file.name || "").toLowerCase();
    if (!(/\.(jpg|jpeg|png|pdf)$/i.test(lower))) {
      alert(t("file_type_not_supported"));
      return;
    }
    const category = q("#project-file-category")?.value || "photo";
    await uploadEntityFile("project", projectId, category, file);
    await renderProjectAttachmentPanel(projectId);
  });
  host.querySelectorAll("button[data-act='del-file']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm(t("confirm_del"))) return;
      await deleteEntityFile(btn.dataset.id);
      await renderProjectAttachmentPanel(projectId);
    });
  });
}

async function quickAddFollowupFromList(customerId) {
  const followupTypeInput = prompt(`${t("field_followup_type")} (phone/text/wechat/email/visit/note)`, "phone");
  if (followupTypeInput === null) return;
  const contentInput = prompt(t("field_content"), "");
  if (contentInput === null || !contentInput.trim()) return;
  const resultInput = prompt(t("field_result"), "");
  let nextFollowupAt = "";
  if (confirm(`${t("set_next_followup")}?`)) {
    const suggested = new Date(Date.now() + 24 * 3600 * 1000).toISOString().slice(0, 16);
    const nextInput = prompt(t("field_next_followup_at"), suggested);
    if (nextInput === null) return;
    nextFollowupAt = (nextInput || "").trim();
  }
  await addCustomerFollowup(customerId, {
    followup_type: normalizeEnum(followupTypeInput || "note") || "note",
    content: contentInput.trim(),
    result: (resultInput || "").trim(),
    next_followup_at: nextFollowupAt || null,
    completed: false,
  });
  alert(t("followup_saved"));
}

function dashboardFollowupActionButtons(item, from = "due") {
  const customerId = Number(item.customer_id || item.id || 0);
  const followupId = Number(item.id || item.open_followup_id || 0);
  return `
    <button data-fu-act="open-customer" data-customer-id="${customerId}" class="secondary">${t("view_customer")}</button>
    ${followupId ? `<button data-fu-act="mark-completed" data-followup-id="${followupId}">${t("mark_completed")}</button>` : ""}
    <button data-fu-act="add-followup" data-customer-id="${customerId}" data-from="${from}" class="secondary">${t("add_followup")}</button>
  `;
}

async function bindDashboardFollowupActions(rootSelector) {
  const root = q(rootSelector);
  if (!root) return;
  root.querySelectorAll("button[data-fu-act]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const act = btn.dataset.fuAct;
      if (act === "open-customer") {
        await openCustomerDetail(btn.dataset.customerId);
        return;
      }
      if (act === "mark-completed") {
        await markFollowupCompleted(btn.dataset.followupId);
        await renderDashboard();
        return;
      }
      if (act === "add-followup") {
        await quickAddFollowupFromList(btn.dataset.customerId);
        await renderDashboard();
      }
    });
  });
}

function reminderActionsHtml(item) {
  const stateKey = normalizeEnum(item.state || "untriggered");
  const parts = [];
  if (stateKey === "pending") {
    parts.push(`<button data-rem-act="mark-reminded" data-id="${item.id}" class="secondary">${t("mark_reminded")}</button>`);
  }
  if (stateKey !== "paid") {
    parts.push(`<button data-rem-act="mark-paid" data-id="${item.id}">${t("mark_paid")}</button>`);
  }
  if (item.project_id) {
    parts.push(`<button data-rem-act="open-project" data-project-id="${item.project_id}" class="secondary">${t("view_project_detail")}</button>`);
  }
  if (item.contract_id) {
    parts.push(`<button data-rem-act="open-contract" data-contract-id="${item.contract_id}" class="secondary">${t("view_contract_detail")}</button>`);
  }
  return parts.join("");
}

async function renderDashboardPaymentReminders(items = null) {
  const container = q("#list-payment-reminders");
  if (!container) return;
  const reminders = items || await fetchPaymentReminders();
  container.innerHTML = reminders.length
    ? `<div class="simple-list">${reminders.map((x) => `
      <div class="list-item reminder-item">
        <div><b>${esc(x.project_name || "-")}</b> / ${esc(x.customer_name || "-")}</div>
        <div>${esc(x.contract_no || `#${x.contract_id || "-"}`)} · ${esc(x.name || "-")}</div>
        <div>${t("trigger_reason")}: ${esc(x.trigger_reason || "-")}</div>
        <div>${fmtMoney(x.amount_due)} · <span class="milestone-pill ${milestoneStateClass(x.state)}">${milestoneStateLabel(x.state)}</span></div>
        <div class="row gap" style="margin-top:6px;">${reminderActionsHtml(x)}</div>
      </div>
    `).join("")}</div>`
    : `<div class="list-item">${t("no_data")}</div>`;

  container.querySelectorAll("button[data-rem-act]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const act = btn.dataset.remAct;
      if (act === "mark-reminded") {
        await api(`/api/payment-milestones/${btn.dataset.id}/mark-reminded`, { method: "POST" });
        await renderDashboardPaymentReminders();
        return;
      }
      if (act === "mark-paid") {
        await api(`/api/payment-milestones/${btn.dataset.id}/mark-paid`, { method: "POST" });
        await renderDashboardPaymentReminders();
        return;
      }
      if (act === "open-project") {
        await renderProjectDetail(btn.dataset.projectId);
        return;
      }
      if (act === "open-contract") {
        await openContractDetail(btn.dataset.contractId);
      }
    });
  });
}

async function refreshVisiblePaymentViews() {
  if (state.module === "dashboard" && q("#list-payment-reminders")) {
    await renderDashboardPaymentReminders();
  }
  if (state.module === "contracts" && q("#contract-milestone-panel")) {
    await renderContractMilestonePanel();
    await renderContractChangeOrderPanel();
  }
}

async function renderDashboard() {
  const data = await api("/api/dashboard");
  q("#main").innerHTML = `
    <section>
      <div class="cards cards-primary" id="dashboard-cards-primary"></div>
      <div class="cards cards-secondary" id="dashboard-cards-secondary"></div>
      <div class="grid-2">
        <article class="panel"><h3>${t("today_due_followups")}</h3><div id="list-followups-due"></div></article>
        <article class="panel"><h3>${t("stale_customers_over_3d")}</h3><div id="list-stale-customers"></div></article>
        <article class="panel"><h3>${t("pending_estimates")}</h3><div id="list-estimates"></div></article>
        <article class="panel"><h3>${t("upcoming_payments")}</h3><div id="list-payments"></div></article>
        <article class="panel"><h3>${t("payment_reminders")}</h3><div id="list-payment-reminders"></div></article>
        <article class="panel"><h3>${t("open_issues")}</h3><div id="list-issues"></div></article>
      </div>
    </section>
  `;

  const cardPairsPrimary = [
    ["monthly_new_leads", data.cards.monthly_new_leads],
    ["monthly_estimates_sent", data.cards.monthly_estimates_sent],
    ["monthly_contracts_signed", data.cards.monthly_contracts_signed],
    ["monthly_contracted_amount", data.cards.monthly_contracted_amount],
    ["active_projects", data.cards.active_projects],
    ["monthly_ar_pending", data.cards.monthly_ar_pending],
  ];
  const cardPairsSecondary = [
    ["monthly_cost", data.cards.monthly_cost],
    ["monthly_gross_profit", data.cards.monthly_gross_profit],
  ];

  const amountKeys = new Set(["monthly_contracted_amount", "monthly_ar_pending", "monthly_cost", "monthly_gross_profit"]);
  q("#dashboard-cards-primary").innerHTML = cardPairsPrimary
    .filter(([, v]) => v !== null)
    .map(([k, v]) => `<div class="card"><div class="k">${t(k)}</div><div class="v" id="${k === "monthly_new_leads" ? "metric-new-leads" : k === "monthly_contracted_amount" ? "metric-signed-amount" : ""}">${amountKeys.has(k) ? fmtMoney(v) : fmt(v)}</div></div>`)
    .join("");
  q("#dashboard-cards-secondary").innerHTML = cardPairsSecondary
    .filter(([, v]) => v !== null)
    .map(([k, v]) => `<div class="card"><div class="k">${t(k)}</div><div class="v">${fmtMoney(v)}</div></div>`)
    .join("");

  const dueRows = data.lists.due_today_followups || [];
  q("#list-followups-due").innerHTML = dueRows.length
    ? `<div class="simple-list">${dueRows.map((x) => `
      <div class="list-item">
        <div><b>${esc(x.customer_name || "-")}</b> / ${esc(x.customer_phone || "-")}</div>
        <div>${displayValue("status", x.customer_status || "-")} · ${displayValue("followup_type", x.followup_type || "note")}</div>
        <div>${esc(x.content || "-")}</div>
        <div>${t("field_next_followup_at")}：${esc(x.next_followup_at || t("no_next_followup"))}</div>
        <div class="row gap" style="margin-top:6px;">${dashboardFollowupActionButtons(x, "due")}</div>
      </div>
    `).join("")}</div>`
    : `<div class="list-item">${t("no_data")}</div>`;

  const staleRows = data.lists.stale_customers || [];
  q("#list-stale-customers").innerHTML = staleRows.length
    ? `<div class="simple-list">${staleRows.map((x) => `
      <div class="list-item">
        <div><b>${esc(x.name || "-")}</b> / ${esc(x.phone || "-")}</div>
        <div>${displayValue("status", x.status || "-")}</div>
        <div>${t("field_next_followup_at")}：${esc(x.next_followup_at || t("no_next_followup"))}</div>
        <div>Last: ${esc(x.last_followup_at || "-")}</div>
        <div class="row gap" style="margin-top:6px;">${dashboardFollowupActionButtons({ customer_id: x.customer_id, open_followup_id: x.open_followup_id }, "stale")}</div>
      </div>
    `).join("")}</div>`
    : `<div class="list-item">${t("no_data")}</div>`;
  renderList(q("#list-estimates"), data.lists.pending_estimates, (x) => `${esc(x.title)} (${esc(x.version)})<br/>${esc(x.created_at)}`);
  renderList(q("#list-payments"), data.lists.upcoming_payments, (x) => `#${x.project_id} ${esc(x.node_name)}<br/>${esc(x.due_date)} / ${fmtMoney(x.amount)}`);
  await renderDashboardPaymentReminders(data.lists.payment_reminders || []);
  renderList(q("#list-issues"), data.lists.open_issues, (x) => `${esc(x.project_name || "")}: ${esc(x.title)}<br/>${displayValue("status", x.status)} / ${displayValue("severity", x.severity)}`);
  await bindDashboardFollowupActions("#list-followups-due");
  await bindDashboardFollowupActions("#list-stale-customers");
}

function crudScaffold(module) {
  state.crudFormOpen = false;
  const pdfLangCtl = (module === "estimates" || module === "contracts")
    ? `<label>${t("pdf_lang")} <select id="pdf-lang-select"><option value="zh">中文</option><option value="en">EN</option><option value="es">ES</option></select></label>`
    : "";
  const templatePanel = module === "estimates"
    ? `
      <div class="panel" id="template-panel" style="margin-top:10px;">
        <h4>${t("templates")}</h4>
        <div class="row gap">
          <input id="tpl-name" placeholder="${t("template_name")}" />
          <input id="tpl-package" placeholder="${t("package_type")}" />
          <input id="tpl-markup" placeholder="markup e.g. 0.15" />
        </div>
        <div class="row gap" style="margin-top:8px;">
          <textarea id="tpl-items" placeholder='line_items_json' rows="4"></textarea>
        </div>
        <div class="row gap" style="margin-top:8px;">
          <input id="tpl-notes" placeholder="notes" />
          <button id="tpl-create-btn">${t("create_template")}</button>
        </div>
        <div class="table-wrap"><table id="tpl-table"></table></div>
      </div>
      `
    : "";
  const contractMilestonePanel = module === "contracts"
    ? `<div class="panel" id="contract-milestone-panel" style="margin-top:10px;"></div>`
    : "";
  const relationPanel = (module === "estimates" || module === "contracts")
    ? `<div class="panel" id="record-link-panel" style="margin-top:10px;"></div>`
    : "";
  const recordFilePanel = (module === "estimates" || module === "contracts")
    ? `<div class="panel" id="record-file-panel" style="margin-top:10px;"></div>`
    : "";
  const customerEstimatePanel = module === "customers"
    ? `<div class="panel" id="customer-estimate-panel" style="margin-top:10px;"></div>`
    : "";
  const customerFollowupPanel = module === "customers"
    ? `<div class="panel" id="customer-followup-panel" style="margin-top:10px;"></div>`
    : "";
  const customerFilePanel = module === "customers"
    ? `<div class="panel" id="customer-file-panel" style="margin-top:10px;"></div>`
    : "";
  const customerQuickLeadPanel = module === "customers"
    ? `<div class="panel" id="quick-lead-panel" style="margin-top:10px;"></div>`
    : "";
  const customerFilterCtl = module === "customers"
    ? `
      <select id="customer-source-filter" title="${t("filter_source_channel")}">
        <option value="">${t("filter_source_channel")}</option>
        ${renderOptionList(SOURCE_CHANNEL_OPTIONS, state.customerSourceFilter || "", "source_channel")}
      </select>
      <select id="customer-status-filter" title="${t("filter_customer_status")}">
        <option value="">${t("filter_customer_status")}</option>
        ${renderOptionList(CUSTOMER_STATUS_FLOW, state.customerStatusFilter || "", "status")}
      </select>
    `
    : "";
  const changeOrderFilterCtl = module === "change_orders"
    ? `
      <select id="change-order-status-filter" title="${fieldLabel("status")}">
        <option value="">${fieldLabel("status")}</option>
        ${renderOptionList(CHANGE_ORDER_STATUS_OPTIONS, state.changeOrderStatusFilter || "", "status")}
      </select>
      <select id="change-order-project-filter" title="${fieldLabel("project_name")}">
        <option value="">${fieldLabel("project_name")}</option>
      </select>
    `
    : "";
  const contractChangeOrderPanel = module === "contracts"
    ? `<div class="panel" id="contract-change-order-panel" style="margin-top:10px;"></div>`
    : "";
  q("#main").innerHTML = `
    <section class="grid-main crud-form-closed">
      <article class="panel">
        <div class="row gap">
          <input id="keyword" placeholder="keyword" />
          <button id="search-btn">${t("search")}</button>
          <button id="new-btn">${t("create")}</button>
          ${customerFilterCtl}
          ${changeOrderFilterCtl}
          ${pdfLangCtl}
        </div>
        <div class="table-wrap"><table id="table"></table></div>
      </article>
      <article class="panel crud-editor-panel">
        <h3 id="form-title">${t("create")}</h3>
        <form id="entity-form"></form>
        <div class="row gap">
          <button id="save-btn">${t("save")}</button>
          <button id="reset-btn" class="secondary">${t("reset")}</button>
        </div>
        ${relationPanel}
        ${recordFilePanel}
        ${customerEstimatePanel}
        ${customerFollowupPanel}
        ${customerFilePanel}
        ${customerQuickLeadPanel}
        ${templatePanel}
        ${contractMilestonePanel}
        ${contractChangeOrderPanel}
      </article>
    </section>
  `;
}

function setCrudFormOpen(open) {
  state.crudFormOpen = Boolean(open);
  const grid = q(".grid-main");
  if (!grid) return;
  grid.classList.toggle("crud-form-open", state.crudFormOpen);
  grid.classList.toggle("crud-form-closed", !state.crudFormOpen);
}

function openCrudForm() {
  setCrudFormOpen(true);
}

function closeCrudForm() {
  setCrudFormOpen(false);
}

function renderForm(module, row = {}) {
  const c = CRUD_SCHEMA[module];
  let data = { ...row };
  if (module === "projects" && !state.editId) {
    if (data.progress_pct === undefined || data.progress_pct === null || data.progress_pct === "") data.progress_pct = 0;
    if (!data.status) data.status = "Not Started";
  }
  if (module === "change_orders" && !state.editId) {
    if (!data.status) data.status = "draft";
    if (data.impact_payment_plan === undefined) data.impact_payment_plan = 0;
    if (data.affect_designer_commission === undefined) data.affect_designer_commission = 0;
  }
  const renderInput = (field, value) => {
    if (module === "customers" && field === "status") {
      return `<select name="${field}">${renderOptionList(CUSTOMER_STATUS_FLOW, value, "status")}</select>`;
    }
    if (module === "customers" && field === "source_channel") {
      const selected = value || "manual";
      return `<select name="${field}">${renderOptionList(SOURCE_CHANNEL_OPTIONS, selected, "source_channel")}</select>`;
    }
    if (module === "customers" && field === "inquiry_type") {
      const selected = value || "other";
      return `<select name="${field}">${renderOptionList(INQUIRY_TYPE_OPTIONS, selected, "inquiry_type")}</select>`;
    }
    if (module === "customers" && field === "preferred_contact_method") {
      const selected = value || "phone";
      return `<select name="${field}">${renderOptionList(CONTACT_METHOD_OPTIONS, selected, "preferred_contact_method")}</select>`;
    }
    if (module === "change_orders" && field === "status") {
      const selected = value || "draft";
      return `<select name="${field}">${renderOptionList(CHANGE_ORDER_STATUS_OPTIONS, selected, "status")}</select>`;
    }
    if (module === "change_orders" && (field === "impact_payment_plan" || field === "affect_designer_commission")) {
      const selected = Number(value || 0) ? "1" : "0";
      return `<select name="${field}"><option value="0" ${selected === "0" ? "selected" : ""}>${t("value_no")}</option><option value="1" ${selected === "1" ? "selected" : ""}>${t("value_yes")}</option></select>`;
    }
    if (module === "change_orders" && field === "approved_at") {
      return `<input name="${field}" type="datetime-local" value="${esc(value ?? "")}" />`;
    }
    if (module === "contracts" && field === "custom_contract_enabled") {
      const selected = Number(value || 0) ? "1" : "0";
      return `<select name="${field}"><option value="0" ${selected === "0" ? "selected" : ""}>${t("value_no")}</option><option value="1" ${selected === "1" ? "selected" : ""}>${t("value_yes")}</option></select>`;
    }
    if (module === "contracts" && field === "custom_contract_text") {
      return `<textarea name="${field}" rows="8" placeholder="${esc(t("custom_contract_placeholder"))}">${esc(value ?? "")}</textarea>`;
    }
    if (module === "change_orders" && field === "amount_delta") {
      return `<input name="${field}" type="number" step="0.01" value="${esc(value ?? "")}" />`;
    }
    if (module === "change_orders" && (field === "description" || field === "notes")) {
      return `<textarea name="${field}" rows="3">${esc(value ?? "")}</textarea>`;
    }
    if (field === "notes" || field === "source_note") {
      return `<textarea name="${field}" rows="3">${esc(value ?? "")}</textarea>`;
    }
    return `<input name="${field}" value="${esc(value ?? "")}" />`;
  };
  q("#form-title").textContent = state.editId ? `${t("edit")} ${t(module)}` : `${t("create")} ${t(module)}`;
  q("#entity-form").innerHTML = c.fields.map((f) => `<div class="field"><label>${fieldLabel(f)}</label>${renderInput(f, data[f])}</div>`).join("");
}

function renderInlineProgress(projectId, stages, pct, interactive = false) {
  const pid = projectId || "";
  if (!stages || !stages.length) {
    return `
      <div class="progress-empty">
        <div class="project-progress-bar" data-project-id="${pid}"><div class="progress-fill" style="width:${Number(pct || 0)}%"></div></div>
        <div class="progress-meta project-progress-percent" data-project-id="${pid}">${Number(pct || 0)}%</div>
      </div>
    `;
  }
  const doneCount = stages.filter((s) => normalizeEnum(s.status) === "done").length;
  const calcPct = Math.round((doneCount * 100) / stages.length);
  return `
    <div class="progress-inline">
      <div class="project-progress-bar" data-project-id="${pid}"><div class="progress-fill" style="width:${calcPct}%"></div></div>
      <div class="progress-meta project-progress-percent" data-project-id="${pid}">${calcPct}%</div>
      <div class="progress-stages project-stage-list" data-project-id="${pid}">
        ${stages.map((s, idx) => {
          const stageStatus = normalizeEnum(s.status || "pending");
          const clickCls = interactive && s.id ? "clickable" : "";
          const attrs = interactive && s.id ? `data-stage-id="${s.id}" data-stage-status="${stageStatus}" role="button" tabindex="0"` : "";
          return `<span class="stage-pill ${stageStatus} ${clickCls}" ${attrs}>${idx + 1}. ${esc(s.stage_name)} · ${displayValue("status", s.status || "pending")}</span>`;
        }).join("")}
      </div>
    </div>
  `;
}

function nextStageStatus(currentStatus) {
  const s = normalizeEnum(currentStatus || "pending");
  if (s === "pending") return "in_progress";
  if (s === "in_progress") return "done";
  return "pending";
}

async function updateStageStatus(stageId, status) {
  const today = new Date().toISOString().slice(0, 10);
  const payload = { status };
  if (status === "pending") {
    payload.started_at = "";
    payload.completed_at = "";
  } else if (status === "in_progress") {
    payload.started_at = today;
    payload.completed_at = "";
  } else if (status === "done") {
    payload.completed_at = today;
  }
  await api(`/api/project_stages/${stageId}`, { method: "PUT", body: JSON.stringify(payload) });
}

function bindStagePillActions(container, onUpdated) {
  if (!container) return;
  const runToggle = async (pill) => {
    if (pill.dataset.busy === "1") return;
    pill.dataset.busy = "1";
    try {
      const stageId = Number(pill.dataset.stageId);
      if (!stageId) return;
      const next = nextStageStatus(pill.dataset.stageStatus || "pending");
      await updateStageStatus(stageId, next);
      if (onUpdated) await onUpdated();
    } finally {
      pill.dataset.busy = "0";
    }
  };
  container.querySelectorAll(".stage-pill.clickable[data-stage-id]").forEach((pill) => {
    pill.addEventListener("click", () => runToggle(pill));
    pill.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        runToggle(pill);
      }
    });
  });
}

function changeOrderStatusClass(status) {
  const key = normalizeEnum(status || "draft");
  if (key === "approved") return "approved";
  if (key === "sent") return "sent";
  if (key === "rejected") return "rejected";
  return "draft";
}

function renderTable(module, rows, progressMap = {}) {
  const c = CRUD_SCHEMA[module];
  const cols = c.table;
  const body = rows.map((r) => {
    const renderCell = (col) => {
      if (module === "customers" && col === "status") {
        const current = r.status || "新线索";
        return `
          <td>
            <select data-act="customer-status" data-id="${r.id}">
              ${renderOptionList(CUSTOMER_STATUS_FLOW, current, "status")}
            </select>
          </td>
        `;
      }
      if (module === "change_orders" && col === "status") {
        return `<td><span class="co-status-pill ${changeOrderStatusClass(r.status)}">${displayValue("status", r.status || "draft")}</span></td>`;
      }
      return `<td>${displayValue(col, r[col])}</td>`;
    };
    const base = `<tr>
      ${cols.map((x) => renderCell(x)).join("")}
      <td>
        ${module === "customers"
          ? `<button data-act="gen-estimate-cust" data-id="${r.id}">${t("generate_estimate")}</button>
             <button data-act="quick-followup-cust" data-id="${r.id}" class="secondary">${t("quick_followup")}</button>`
          : ""}
        ${module === "projects" ? `<button data-act="detail" data-id="${r.id}">${t("detail")}</button><button data-act="init-progress" data-id="${r.id}">${t("init_flow")}</button>` : ""}
        ${module === "estimates"
          ? `${r.linked_contract_id
            ? `<button data-act="view-contract" data-id="${r.id}" data-contract-id="${r.linked_contract_id}" class="secondary">${t("view_contract")}</button>`
            : `<button data-act="gen-contract" data-id="${r.id}">${t("generate_contract")}</button>`}
             <button data-act="pdf" data-id="${r.id}">${t("pdf")}</button>`
          : ""}
        ${module === "contracts"
          ? `${(r.linked_project_id || r.project_id)
            ? `<button data-act="view-project" data-id="${r.id}" data-project-id="${r.linked_project_id || r.project_id}" class="secondary">${t("view_project")}</button>`
            : `<button data-act="gen-project" data-id="${r.id}">${t("generate_project")}</button>`}
             <button data-act="contract-pdf" data-id="${r.id}">${t("contract_pdf")}</button>
             <button data-act="custom-contract" data-id="${r.id}" class="secondary">${t("custom_contract")}</button>`
          : ""}
        ${module === "change_orders"
          ? `${normalizeEnum(r.status) === "draft" ? `<button data-act="mark-sent" data-id="${r.id}" class="secondary">${t("mark_sent")}</button>` : ""}
             ${normalizeEnum(r.status) !== "approved" ? `<button data-act="mark-approved" data-id="${r.id}">${t("mark_approved")}</button>` : ""}
             ${normalizeEnum(r.status) !== "rejected" ? `<button data-act="mark-rejected" data-id="${r.id}" class="danger">${t("mark_rejected")}</button>` : ""}
             <button data-act="print-change-order" data-id="${r.id}" class="secondary">${t("print_change_order_doc")}</button>
             <button data-act="pdf-change-order" data-id="${r.id}">${t("export_change_order_pdf")}</button>`
          : ""}
        <button data-act="edit" data-id="${r.id}">${t("edit")}</button>
        <button data-act="del" data-id="${r.id}" class="danger">${t("del")}</button>
      </td>
    </tr>`;
    if (module !== "projects") return base;
    const p = progressMap[r.id] || { progress_pct: r.progress_pct || 0, stages: [] };
    const extra = `<tr class="progress-row"><td colspan="${cols.length + 1}">${renderInlineProgress(r.id, p.stages, p.progress_pct, true)}</td></tr>`;
    return base + extra;
  }).join("");
  q("#table").innerHTML = `
    <thead><tr>${cols.map((x) => `<th>${fieldLabel(x)}</th>`).join("")}<th>${t("actions")}</th></tr></thead>
    <tbody>${body}</tbody>
  `;
  if (module === "projects") {
    bindStagePillActions(q("#table"), async () => {
      await loadCrud("projects");
    });
  }
}

function collectForm() {
  const obj = {};
  new FormData(q("#entity-form")).forEach((v, k) => {
    const val = String(v).trim();
    if (val) obj[k] = val;
  });
  return obj;
}

async function loadCrud(module) {
  const kw = q("#keyword").value.trim();
  const params = new URLSearchParams();
  if (kw) params.set("keyword", kw);
  if (module === "customers") {
    const sourceFilter = (q("#customer-source-filter") && q("#customer-source-filter").value) || state.customerSourceFilter || "";
    const statusFilter = (q("#customer-status-filter") && q("#customer-status-filter").value) || state.customerStatusFilter || "";
    if (sourceFilter) params.set("source_channel", sourceFilter);
    if (statusFilter) params.set("status", statusFilter);
  }
  if (module === "change_orders") {
    const statusFilter = (q("#change-order-status-filter") && q("#change-order-status-filter").value) || state.changeOrderStatusFilter || "";
    const projectFilter = (q("#change-order-project-filter") && q("#change-order-project-filter").value) || state.changeOrderProjectFilter || "";
    if (statusFilter) params.set("status", statusFilter);
    if (projectFilter) params.set("project_id", projectFilter);
  }
  const suffix = params.toString() ? `?${params.toString()}` : "";
  if (module === "change_orders") {
    const rows = await api(`/api/change-orders${suffix}`);
    renderTable(module, rows, {});
    return;
  }
  const rows = await api(`/api/${module}${suffix}`);
  if (module === "projects") {
    const summary = await api("/api/projects/progress-summary");
    const map = {};
    summary.forEach((x) => { map[x.project_id] = x; });
    renderTable(module, rows, map);
    return;
  }
  renderTable(module, rows, {});
}

async function renderChangeOrderProjectFilter() {
  const sel = q("#change-order-project-filter");
  if (!sel) return;
  const projects = await api("/api/projects");
  const current = state.changeOrderProjectFilter || "";
  sel.innerHTML = `
    <option value="">${fieldLabel("project_name")}</option>
    ${projects.map((p) => `<option value="${p.id}" ${String(p.id) === String(current) ? "selected" : ""}>#${p.id} ${esc(p.name || "-")}</option>`).join("")}
  `;
}

function closeProjectDetailDrawer() {
  const drawer = q("#project-detail-drawer");
  if (!drawer) return;
  drawer.classList.add("hidden");
  drawer.innerHTML = "";
  state.projectDetail = null;
}

function closeVendorLedgerDrawer() {
  const drawer = q("#vendor-ledger-drawer");
  if (!drawer) return;
  drawer.classList.add("hidden");
  drawer.innerHTML = "";
}

async function renderVendorLedgerDrawer(vendorId) {
  const drawer = q("#vendor-ledger-drawer");
  if (!drawer) return;
  const data = await api(`/api/vendors/${vendorId}/ledger`);
  const vendor = data.vendor || {};
  const bills = data.bills || [];
  const payments = data.payments || [];

  drawer.innerHTML = `
    <div class="drawer-backdrop" id="vendor-ledger-backdrop"></div>
    <aside class="drawer-panel vendor-ledger-panel" data-vendor-id="${vendorId}">
      <div class="drawer-head">
        <h3>${t("vendor_ledger")} · ${esc(vendor.name || `#${vendorId}`)}</h3>
        <button id="vendor-ledger-close" class="secondary">${t("close")}</button>
      </div>
      <section class="panel">
        <h4>${t("vendor_basic_info")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi"><div class="k">${fieldLabel("name")}</div><div class="v">${esc(vendor.name || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("type")}</div><div class="v">${displayValue("type", vendor.type || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("tax_id")}</div><div class="v">${esc(vendor.tax_id || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("1099_required")}</div><div class="v">${Number(vendor["1099_required"] || 0) ? t("value_yes") : t("value_no")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("w9_received")}</div><div class="v">${Number(vendor.w9_received || 0) ? t("value_yes") : t("value_no")}</div></div>
          <div class="detail-kpi"><div class="k">${t("total_paid_this_year")}</div><div class="v">${fmt(data.total_paid_this_year || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("open_bills_total")}</div><div class="v">${fmt(data.open_bills_total || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("current_outstanding_balance")}</div><div class="v">${fmt(data.current_outstanding_balance || 0)}</div></div>
        </div>
      </section>
      <section class="panel" style="margin-top:10px;">
        <h4>${t("bills_payable")}</h4>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>${fieldLabel("bill_no")}</th><th>${fieldLabel("project_id")}</th><th>${fieldLabel("bill_date")}</th><th>${fieldLabel("due_date")}</th><th>${fieldLabel("category")}</th><th>${fieldLabel("amount")}</th><th>${t("paid_amount")}</th><th>${t("open_amount")}</th><th>${fieldLabel("status")}</th><th>${t("attachments")}</th></tr></thead>
            <tbody>
              ${bills.length ? bills.map((b) => `
                <tr>
                  <td>${b.id}</td>
                  <td>${esc(b.bill_no || "-")}</td>
                  <td>${esc(b.project_name || "-")}</td>
                  <td>${esc(b.bill_date || "-")}</td>
                  <td>${esc(b.due_date || "-")}</td>
                  <td>${esc(b.category || "-")}</td>
                  <td>${fmt(b.amount || 0)}</td>
                  <td>${fmt(b.paid_amount || 0)}</td>
                  <td>${fmt(b.open_amount || 0)}</td>
                  <td>${displayValue("status", b.status || "")}</td>
                  <td>${Number(b.attachment_count || 0) > 0 && b.latest_attachment_url ? `<a href="${esc(b.latest_attachment_url)}" target="_blank" class="btn-link">${t("view_attachment")}</a>` : "-"}</td>
                </tr>
              `).join("") : `<tr><td colspan="11">${t("no_data")}</td></tr>`}
            </tbody>
          </table>
        </div>
      </section>
      <section class="panel" style="margin-top:10px;">
        <h4>${t("payments_paid")}</h4>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>${fieldLabel("payment_date")}</th><th>${fieldLabel("bill_no")}</th><th>${fieldLabel("project_id")}</th><th>${fieldLabel("method")}</th><th>${fieldLabel("category")}</th><th>${fieldLabel("amount")}</th><th>${fieldLabel("notes")}</th><th>${t("attachments")}</th></tr></thead>
            <tbody>
              ${payments.length ? payments.map((p) => `
                <tr>
                  <td>${p.id}</td>
                  <td>${esc(p.date || "-")}</td>
                  <td>${esc(p.bill_no || "-")}</td>
                  <td>${esc(p.project_name || "-")}</td>
                  <td>${displayValue("method", p.method || "")}</td>
                  <td>${esc(p.category || "-")}</td>
                  <td>${fmt(p.amount || 0)}</td>
                  <td>${esc(p.note || "-")}</td>
                  <td>${Number(p.attachment_count || 0) > 0 && p.latest_attachment_url ? `<a href="${esc(p.latest_attachment_url)}" target="_blank" class="btn-link">${t("view_attachment")}</a>` : "-"}</td>
                </tr>
              `).join("") : `<tr><td colspan="9">${t("no_data")}</td></tr>`}
            </tbody>
          </table>
        </div>
      </section>
    </aside>
  `;
  drawer.classList.remove("hidden");
  q("#vendor-ledger-close")?.addEventListener("click", closeVendorLedgerDrawer);
  q("#vendor-ledger-backdrop")?.addEventListener("click", closeVendorLedgerDrawer);
}

function closeProjectCostLedgerDrawer() {
  const drawer = q("#project-cost-ledger-drawer");
  if (!drawer) return;
  drawer.classList.add("hidden");
  drawer.innerHTML = "";
}

async function renderProjectCostLedgerDrawer(projectId) {
  const drawer = q("#project-cost-ledger-drawer");
  if (!drawer) return;
  const data = await api(`/api/projects/${projectId}/cost-ledger`);
  const project = data.project || {};
  const revenue = data.revenue || {};
  const costs = data.costs || {};
  const bills = data.bills || [];
  const payments = data.payments || [];
  const categorySummary = data.cost_by_category || [];

  drawer.innerHTML = `
    <div class="drawer-backdrop" id="project-cost-ledger-backdrop"></div>
    <aside class="drawer-panel" data-project-id="${projectId}">
      <div class="drawer-head">
        <h3>${t("project_cost_ledger")} · ${esc(project.name || `#${projectId}`)}</h3>
        <button id="project-cost-ledger-close" class="secondary">${t("close")}</button>
      </div>

      <section class="panel">
        <h4>${t("project_info")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi"><div class="k">${fieldLabel("name")}</div><div class="v">${esc(project.name || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("customer_name")}</div><div class="v">${esc(project.customer_name || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("address")}</div><div class="v">${esc(project.address || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("manager")}</div><div class="v">${esc(project.manager || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("status")}</div><div class="v">${displayValue("status", project.status || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("progress_pct")}</div><div class="v">${fmt(project.progress_pct || 0)}%</div></div>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("revenue")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi"><div class="k">${t("contract_revenue")}</div><div class="v">${fmt(revenue.contract_revenue || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("change_revenue")}</div><div class="v">${fmt(revenue.change_revenue || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("total_revenue")}</div><div class="v">${fmt(revenue.total_revenue || 0)}</div></div>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("open_costs")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi"><div class="k">${t("payments_total")}</div><div class="v">${fmt(costs.payments_total || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("open_bills_total")}</div><div class="v">${fmt(costs.open_bills_total || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("total_cost")}</div><div class="v">${fmt(costs.total_cost || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("profit")}</div><div class="v">${fmt(costs.gross_profit || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("gross_margin_pct")}</div><div class="v">${fmt(costs.gross_margin_pct || 0)}%</div></div>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("cost_by_category")}</h4>
        <div class="table-wrap">
          <table>
            <thead><tr><th>${fieldLabel("category")}</th><th>${t("count")}</th><th>${t("amount")}</th><th>${t("paid_amount")}</th><th>${t("open_amount")}</th></tr></thead>
            <tbody>
              ${categorySummary.length ? categorySummary.map((x) => `
                <tr>
                  <td>${esc(x.category || "-")}</td>
                  <td>${fmt(x.bill_count || 0)}</td>
                  <td>${fmt(x.total_amount || 0)}</td>
                  <td>${fmt(x.paid_amount || 0)}</td>
                  <td>${fmt(x.open_amount || 0)}</td>
                </tr>
              `).join("") : `<tr><td colspan="5">${t("no_data")}</td></tr>`}
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("bills_payable")}</h4>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>${fieldLabel("bill_no")}</th><th>${fieldLabel("vendor")}</th><th>${fieldLabel("bill_date")}</th><th>${fieldLabel("due_date")}</th><th>${fieldLabel("category")}</th><th>${fieldLabel("amount")}</th><th>${t("paid_amount")}</th><th>${t("open_amount")}</th><th>${fieldLabel("status")}</th><th>${t("attachments")}</th></tr></thead>
            <tbody>
              ${bills.length ? bills.map((b) => `
                <tr>
                  <td>${b.id}</td>
                  <td>${esc(b.bill_no || "-")}</td>
                  <td>${esc(b.vendor_name || "-")}</td>
                  <td>${esc(b.bill_date || "-")}</td>
                  <td>${esc(b.due_date || "-")}</td>
                  <td>${esc(b.category || "-")}</td>
                  <td>${fmt(b.amount || 0)}</td>
                  <td>${fmt(b.paid_amount || 0)}</td>
                  <td>${fmt(b.open_amount || 0)}</td>
                  <td>${displayValue("status", b.status || "")}</td>
                  <td>${Number(b.attachment_count || 0) > 0 && b.latest_attachment_url ? `<a href="${esc(b.latest_attachment_url)}" target="_blank" class="btn-link">${t("view_attachment")}</a>` : "-"}</td>
                </tr>
              `).join("") : `<tr><td colspan="11">${t("no_data")}</td></tr>`}
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("payments_paid")}</h4>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>${fieldLabel("payment_date")}</th><th>${fieldLabel("vendor")}</th><th>${fieldLabel("bill_no")}</th><th>${fieldLabel("method")}</th><th>${fieldLabel("category")}</th><th>${fieldLabel("amount")}</th><th>${fieldLabel("notes")}</th><th>${t("attachments")}</th></tr></thead>
            <tbody>
              ${payments.length ? payments.map((p) => `
                <tr>
                  <td>${p.id}</td>
                  <td>${esc(p.date || "-")}</td>
                  <td>${esc(p.vendor_name || "-")}</td>
                  <td>${esc(p.bill_no || "-")}</td>
                  <td>${displayValue("method", p.method || "")}</td>
                  <td>${esc(p.category || "-")}</td>
                  <td>${fmt(p.amount || 0)}</td>
                  <td>${esc(p.note || "-")}</td>
                  <td>${Number(p.attachment_count || 0) > 0 && p.latest_attachment_url ? `<a href="${esc(p.latest_attachment_url)}" target="_blank" class="btn-link">${t("view_attachment")}</a>` : "-"}</td>
                </tr>
              `).join("") : `<tr><td colspan="9">${t("no_data")}</td></tr>`}
            </tbody>
          </table>
        </div>
      </section>
    </aside>
  `;
  drawer.classList.remove("hidden");
  q("#project-cost-ledger-close")?.addEventListener("click", closeProjectCostLedgerDrawer);
  q("#project-cost-ledger-backdrop")?.addEventListener("click", closeProjectCostLedgerDrawer);
}

async function loadProjectLogs(projectId) {
  return api(`/api/projects/${projectId}/logs`);
}

async function addProjectLog(projectId, payload) {
  return api(`/api/projects/${projectId}/logs`, { method: "POST", body: JSON.stringify(payload) });
}

async function renderProjectLogs(projectId) {
  const list = q("#project-log-list");
  if (!list) return;
  const logs = await loadProjectLogs(projectId);
  list.innerHTML = logs.length
    ? logs.map((x) => `
      <div class="list-item">
        <div><b>${esc(x.log_date || "")}</b></div>
        <div style="margin-top:4px;">${esc(x.content || "")}</div>
        ${x.image_url ? `<div style="margin-top:6px;"><a href="${esc(x.image_url)}" target="_blank">${esc(x.image_url)}</a></div>` : ""}
      </div>
    `).join("")
    : `<div class="list-item">${t("no_logs")}</div>`;
}

async function renderProjectDetail(projectId) {
  state.projectDetail = Number(projectId);
  const d = await api(`/api/projects/${projectId}/detail`);
  const o = d.overview || {};
  const drawer = q("#project-detail-drawer");
  if (!drawer) return;

  const contract = d.contract || null;
  const sourceContract = d.source_contract || null;
  const sourceEstimate = d.source_estimate || null;
  const milestones = d.payment_milestones || [];
  const reminders = d.payment_reminders || [];
  const changeOrders = d.change_orders || [];
  const changeSummary = d.change_order_summary || {};
  const designer = d.designer || {};
  const commission = d.designer_commission || {};
  const canMoney = d.can_contracts || d.can_finance;
  const canFinanceSnapshot = Boolean(d.can_finance);
  let financeSnapshot = null;
  if (canFinanceSnapshot) {
    try {
      financeSnapshot = await api(`/api/projects/${projectId}/cost-ledger`);
    } catch {
      financeSnapshot = null;
    }
  }
  const snapshotRevenue = financeSnapshot?.revenue || {};
  const snapshotCosts = financeSnapshot?.costs || {};
  const contractAmountText = canMoney ? fmtMoney(contract?.total_amount ?? o.contract_amount ?? 0) : "-";
  const receivedAmountText = d.can_finance ? fmtMoney(o.received_amount || 0) : "-";
  const pendingAmountText = d.can_finance ? fmtMoney(o.pending_amount || 0) : "-";
  const triggeredUnpaid = milestones.filter((m) => {
    const key = normalizeEnum(m.state || "untriggered");
    return key === "pending" || key === "reminded";
  });
  const paidNodes = milestones
    .filter((m) => normalizeEnum(m.state || "untriggered") === "paid")
    .sort((a, b) => {
      const da = new Date(a.paid_at || a.updated_at || 0).getTime();
      const db = new Date(b.paid_at || b.updated_at || 0).getTime();
      if (db !== da) return db - da;
      return Number(b.id || 0) - Number(a.id || 0);
    });
  const recentPaidNode = paidNodes[0] || null;
  const nextTriggerNode = milestones.find((m) => normalizeEnum(m.state || "untriggered") === "untriggered") || null;
  const renderNodeItem = (m, showState = true) => `
    <div class="list-item">
      <div><b>${esc(m.name || "-")}</b></div>
      <div>${esc(m.trigger_reason || "-")}</div>
      <div class="row gap" style="margin-top:4px;">
        <span>${canMoney ? milestoneAmountText(m) : "-"}</span>
        ${showState ? `<span class="milestone-pill ${milestoneStateClass(m.state)}">${milestoneStateLabel(m.state)}</span>` : ""}
      </div>
    </div>
  `;

  drawer.innerHTML = `
    <div class="drawer-backdrop" id="project-drawer-backdrop"></div>
    <aside class="drawer-panel" data-project-id="${projectId}">
      <div class="drawer-head">
        <h3>${t("project_detail")} · ${esc(o.name || "")}</h3>
        <button id="project-drawer-close" class="secondary">${t("close")}</button>
      </div>

      <section class="panel">
        <h4>${t("project_info")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi"><div class="k">${fieldLabel("name")}</div><div class="v">${esc(o.name || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${t("customer")}</div><div class="v">${esc(o.customer_name || "-")} / ${esc(o.customer_phone || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("address")}</div><div class="v">${esc(o.address || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("manager")}</div><div class="v">${esc(o.manager || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("status")}</div><div class="v">${displayValue("status", o.status)}</div></div>
          <div class="detail-kpi progress"><div class="k">${fieldLabel("progress_pct")}</div><div class="v">${displayValue("progress_pct", o.progress_pct || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("start_date")}</div><div class="v">${esc(o.start_date || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("estimated_finish_date")}</div><div class="v">${esc(o.estimated_finish_date || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("id")}</div><div class="v">${esc(o.id || "-")}</div></div>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("source_relation")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi">
            <div class="k">${t("source_estimate")}</div>
            <div class="v">
              ${sourceEstimate ? `#${sourceEstimate.id} ${esc(sourceEstimate.title || "")}` : "-"}
            </div>
            ${sourceEstimate ? `<div class="row gap" style="margin-top:6px;"><button class="secondary" data-act="open-source-estimate" data-id="${sourceEstimate.id}">${t("detail")}</button></div>` : ""}
          </div>
          <div class="detail-kpi">
            <div class="k">${t("source_contract")}</div>
            <div class="v">
              ${sourceContract ? `#${sourceContract.id} ${esc(sourceContract.contract_no || "")}` : "-"}
            </div>
            ${sourceContract ? `<div class="row gap" style="margin-top:6px;"><button class="secondary" data-act="open-source-contract" data-id="${sourceContract.id}">${t("detail")}</button></div>` : ""}
          </div>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("project_progress")}</h4>
        <div style="color:var(--sub);font-size:12px;margin-bottom:8px;">${t("stage_click_tip")}</div>
        <div id="project-workflow"></div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("project_logs")}</h4>
        <div class="log-form">
          <input id="project-log-date" type="date" value="${new Date().toISOString().slice(0, 10)}" />
          <input id="project-log-image" placeholder="${t("log_image")}" />
          <textarea id="project-log-content" class="full" rows="3" placeholder="${t("log_content")}"></textarea>
          <div class="full row gap"><button id="add-project-log">${t("add_log")}</button></div>
        </div>
        <div id="project-log-list" class="simple-list" style="margin-top:10px;"></div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <div id="project-file-panel"></div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("project_change_orders")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi"><div class="k">${t("approved_change_total")}</div><div class="v">${fmtMoney(changeSummary.approved_change_amount || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("impact_payment_plan_count")}</div><div class="v">${fmt(changeSummary.impact_payment_plan_count || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("approved_change_commissionable")}</div><div class="v">${fmtMoney(changeSummary.approved_commissionable_change_amount || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("approved_change_non_commissionable")}</div><div class="v">${fmtMoney(changeSummary.approved_non_commissionable_change_amount || 0)}</div></div>
        </div>
        <div class="grid-2 compact" style="margin-top:8px;">
          <div class="field"><label>${fieldLabel("title")}</label><input id="project-co-title" /></div>
          <div class="field"><label>${fieldLabel("amount_delta")}</label><input id="project-co-amount" type="number" step="0.01" /></div>
          <div class="field"><label>${fieldLabel("impact_payment_plan")}</label><select id="project-co-impact-plan"><option value="0">${t("value_no")}</option><option value="1">${t("value_yes")}</option></select></div>
          <div class="field"><label>${fieldLabel("affect_designer_commission")}</label><select id="project-co-affect-commission"><option value="0">${t("value_no")}</option><option value="1">${t("value_yes")}</option></select></div>
          <div class="field" style="grid-column:1/-1;"><label>${fieldLabel("description")}</label><textarea id="project-co-desc" rows="3"></textarea></div>
        </div>
        <div class="row gap" style="margin-top:8px;">
          <button id="project-add-change-order">${t("create_change_order")}</button>
        </div>
        <div class="table-wrap" style="margin-top:8px;">
          <table id="project-change-order-table">
            <thead><tr><th>${fieldLabel("order_no")}</th><th>${fieldLabel("title")}</th><th>${fieldLabel("amount_delta")}</th><th>${fieldLabel("status")}</th><th>${fieldLabel("impact_payment_plan")}</th><th>${fieldLabel("affect_designer_commission")}</th><th>${t("actions")}</th></tr></thead>
            <tbody>
              ${changeOrders.length ? changeOrders.map((x) => `
                <tr>
                  <td>${esc(x.order_no || `CO-${x.id}`)}</td>
                  <td>${esc(x.title || "-")}</td>
                  <td>${fmtMoney(x.amount_delta || 0)}</td>
                  <td><span class="co-status-pill ${changeOrderStatusClass(x.status)}">${displayValue("status", x.status || "draft")}</span></td>
                  <td>${displayValue("impact_payment_plan", x.impact_payment_plan)}</td>
                  <td>${displayValue("affect_designer_commission", x.affect_designer_commission)}</td>
                  <td class="row gap">
                    <button data-co-act="open" data-id="${x.id}" class="secondary">${t("detail")}</button>
                    ${normalizeEnum(x.status) === "draft" ? `<button data-co-act="mark-sent" data-id="${x.id}" class="secondary">${t("mark_sent")}</button>` : ""}
                    ${normalizeEnum(x.status) !== "approved" ? `<button data-co-act="mark-approved" data-id="${x.id}">${t("mark_approved")}</button>` : ""}
                    ${normalizeEnum(x.status) !== "rejected" ? `<button data-co-act="mark-rejected" data-id="${x.id}" class="danger">${t("mark_rejected")}</button>` : ""}
                    <button data-co-act="print" data-id="${x.id}" class="secondary">${t("print_change_order_doc")}</button>
                  </td>
                </tr>
              `).join("") : `<tr><td colspan="7">${t("no_data")}</td></tr>`}
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("payment_overview")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi"><div class="k">${fieldLabel("contract_amount")}</div><div class="v">${contractAmountText}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("received_amount")}</div><div class="v">${receivedAmountText}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("pending_amount")}</div><div class="v">${pendingAmountText}</div></div>
          <div class="detail-kpi"><div class="k">${t("triggered_unpaid_nodes")}</div><div class="v">${fmt(triggeredUnpaid.length)}</div></div>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("finance_snapshot")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi"><div class="k">${t("contract_revenue")}</div><div class="v">${canFinanceSnapshot ? fmt(snapshotRevenue.contract_revenue || 0) : "-"}</div></div>
          <div class="detail-kpi"><div class="k">${t("change_revenue")}</div><div class="v">${canFinanceSnapshot ? fmt(snapshotRevenue.change_revenue || 0) : "-"}</div></div>
          <div class="detail-kpi"><div class="k">${t("total_revenue")}</div><div class="v">${canFinanceSnapshot ? fmt(snapshotRevenue.total_revenue || 0) : "-"}</div></div>
          <div class="detail-kpi"><div class="k">${t("payments_total")}</div><div class="v">${canFinanceSnapshot ? fmt(snapshotCosts.payments_total || 0) : "-"}</div></div>
          <div class="detail-kpi"><div class="k">${t("open_bills_total")}</div><div class="v">${canFinanceSnapshot ? fmt(snapshotCosts.open_bills_total || 0) : "-"}</div></div>
          <div class="detail-kpi"><div class="k">${t("total_cost")}</div><div class="v">${canFinanceSnapshot ? fmt(snapshotCosts.total_cost || 0) : "-"}</div></div>
          <div class="detail-kpi"><div class="k">${t("profit")}</div><div class="v">${canFinanceSnapshot ? fmt(snapshotCosts.gross_profit || 0) : "-"}</div></div>
          <div class="detail-kpi"><div class="k">${t("gross_margin_pct")}</div><div class="v">${canFinanceSnapshot ? `${fmt(snapshotCosts.gross_margin_pct || 0)}%` : "-"}</div></div>
        </div>
        ${canFinanceSnapshot ? `
        <div class="row gap" style="margin-top:8px;">
          <button data-act="open-project-cost-ledger" class="secondary">${t("view_cost_ledger")}</button>
          <button data-act="quick-add-bill" class="secondary">${t("new_bill")}</button>
          <button data-act="quick-add-payment" class="secondary">${t("new_payment")}</button>
        </div>
        ` : ""}
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("current_payment_nodes")}</h4>
        <div class="grid-2 compact payment-node-grid">
          <div>
            <div class="kpi-subtitle">${t("triggered_unpaid_nodes")}</div>
            <div class="simple-list">
              ${triggeredUnpaid.length ? triggeredUnpaid.map((m) => renderNodeItem(m)).join("") : `<div class="list-item">${t("no_data")}</div>`}
            </div>
          </div>
          <div>
            <div class="kpi-subtitle">${t("recent_paid_node")}</div>
            <div class="simple-list">
              ${recentPaidNode ? renderNodeItem(recentPaidNode, false) : `<div class="list-item">${t("no_data")}</div>`}
            </div>
            <div class="kpi-subtitle" style="margin-top:8px;">${t("next_trigger_node")}</div>
            <div class="simple-list">
              ${nextTriggerNode ? renderNodeItem(nextTriggerNode, false) : `<div class="list-item">${t("no_data")}</div>`}
            </div>
          </div>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("contract_info")}</h4>
        ${contract ? `
          <div class="detail-base-grid">
            <div class="detail-kpi"><div class="k">${fieldLabel("contract_no")}</div><div class="v">${esc(contract.contract_no || "-")}</div></div>
            <div class="detail-kpi"><div class="k">${fieldLabel("signed_status")}</div><div class="v">${displayValue("signed_status", contract.signed_status || "-")}</div></div>
            <div class="detail-kpi"><div class="k">${fieldLabel("signed_date")}</div><div class="v">${esc(contract.signed_date || "-")}</div></div>
            <div class="detail-kpi"><div class="k">${fieldLabel("total_amount")}</div><div class="v">${d.can_contracts ? fmtMoney(contract.base_contract_amount ?? contract.total_amount ?? 0) : "-"}</div></div>
            <div class="detail-kpi"><div class="k">${t("approved_change_total")}</div><div class="v">${d.can_contracts ? fmtMoney(contract.approved_change_amount || 0) : "-"}</div></div>
            <div class="detail-kpi"><div class="k">${t("current_contract_total")}</div><div class="v">${d.can_contracts ? fmtMoney(contract.current_contract_total || contract.total_amount || 0) : "-"}</div></div>
          </div>
          ${Number(contract.change_orders_affect_payment_plan_count || 0) > 0 ? `<div class="notice-inline">${t("change_order_warn_payment_plan")}</div>` : ""}
        ` : `<div class="list-item">${t("no_data")}</div>`}
        <h4 style="margin-top:10px;">${t("payment_reminder_list")}</h4>
        <div id="project-reminder-list" class="simple-list">
          ${reminders.length ? reminders.map((r) => `
            <div class="list-item">
              <b>${esc(r.name || "-")}</b>
              <div>${esc(r.trigger_reason || "-")}</div>
              <div>${milestoneStateLabel(r.state)} / ${fmtMoney(r.amount_due)}</div>
            </div>
          `).join("") : `<div class="list-item">${t("no_data")}</div>`}
        </div>
        <div class="table-wrap">
          <table id="project-milestone-table">
            <thead><tr><th>ID</th><th>${t("milestone_name")}</th><th>${t("trigger_type")}</th><th>${t("amount")}</th><th>${t("state")}</th><th>${t("actions")}</th></tr></thead>
            <tbody>
              ${milestones.length ? milestones.map((m) => `
                <tr>
                  <td>${m.id}</td>
                  <td>${esc(m.name || "-")}</td>
                  <td>${milestoneTriggerText(m)}</td>
                  <td>${d.can_contracts ? milestoneAmountText(m) : "-"}</td>
                  <td><span class="milestone-pill ${milestoneStateClass(m.state)}">${milestoneStateLabel(m.state)}</span></td>
                  <td class="row gap">
                    ${m.state === "pending" ? `<button data-act="mark-reminded" data-id="${m.id}" class="secondary">${t("mark_reminded")}</button>` : ""}
                    ${m.state !== "paid" ? `<button data-act="mark-paid" data-id="${m.id}">${t("mark_paid")}</button>` : ""}
                  </td>
                </tr>
              `).join("") : `<tr><td colspan="6">${t("no_milestones")}</td></tr>`}
            </tbody>
          </table>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("designer_info")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi"><div class="k">${fieldLabel("designer_name")}</div><div class="v">${esc(designer.designer_name || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("designer_id")}</div><div class="v">${esc(designer.designer_id || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("designer_commission_type")}</div><div class="v">${displayValue("designer_commission_type", designer.designer_commission_type || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("designer_commission_value")}</div><div class="v">${esc(designer.designer_commission_value ?? "-")}</div></div>
          <div class="detail-kpi"><div class="k">${fieldLabel("designer_commission_base")}</div><div class="v">${displayValue("designer_commission_base", designer.designer_commission_base || "-")}</div></div>
        </div>
        <h4 style="margin-top:10px;">${t("designer_commission")}</h4>
        <div class="detail-base-grid">
          <div class="detail-kpi"><div class="k">${t("base_contract_amount")}</div><div class="v">${fmtMoney(commission.base_contract_amount || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("approved_change_commissionable")}</div><div class="v">${fmtMoney(commission.approved_change_commissionable_amount || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("approved_change_non_commissionable")}</div><div class="v">${fmtMoney(commission.approved_change_non_commissionable_amount || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("commission_base")}</div><div class="v">${displayValue("commission_base", commission.commission_base || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${t("current_contract_total")}</div><div class="v">${fmtMoney(commission.commission_calc_base_amount || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("commission_amount")}</div><div class="v">${fmtMoney(commission.commission_amount || 0)}</div></div>
          <div class="detail-kpi"><div class="k">${t("commission_status")}</div><div class="v">${displayValue("status", commission.status || "-")}</div></div>
          <div class="detail-kpi"><div class="k">${t("settlement_mode")}</div><div class="v">${esc(commission.settlement_mode || "-")}</div></div>
        </div>
        <div class="notice-inline">${t("default_exclude_change_orders")}</div>
        <div class="row gap" style="margin-top:8px;">
          <button id="recalc-commission-btn" class="secondary">${t("recalc_commission")}</button>
        </div>
      </section>

      <section class="panel" style="margin-top:10px;">
        <h4>${t("internal_notes")}</h4>
        <textarea id="project-note" rows="4">${esc(o.notes || "")}</textarea>
        <div class="row gap" style="margin-top:8px;">
          <button id="save-project-note">${t("save_notes")}</button>
        </div>
      </section>
    </aside>
  `;
  drawer.classList.remove("hidden");

  q("#project-drawer-close").addEventListener("click", closeProjectDetailDrawer);
  q("#project-drawer-backdrop").addEventListener("click", closeProjectDetailDrawer);
  drawer.querySelectorAll("button[data-act='open-source-estimate']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      closeProjectDetailDrawer();
      await openEstimateDetail(btn.dataset.id);
    });
  });
  drawer.querySelectorAll("button[data-act='open-source-contract']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      closeProjectDetailDrawer();
      await openContractDetail(btn.dataset.id);
    });
  });
  drawer.querySelectorAll("button[data-act='open-project-cost-ledger']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      closeProjectDetailDrawer();
      await renderProjectCostLedgerDrawer(projectId);
    });
  });
  drawer.querySelectorAll("button[data-act='quick-add-bill']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await openFinanceFromProject(projectId, "bill");
    });
  });
  drawer.querySelectorAll("button[data-act='quick-add-payment']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await openFinanceFromProject(projectId, "payment");
    });
  });
  q("#save-project-note").addEventListener("click", async () => {
    await api(`/api/projects/${projectId}`, { method: "PUT", body: JSON.stringify({ notes: q("#project-note").value }) });
    alert(t("notes_saved"));
  });
  if (q("#project-milestone-table")) {
    q("#project-milestone-table").addEventListener("click", async (e) => {
      const btn = e.target.closest("button[data-act]");
      if (!btn) return;
      const mid = Number(btn.dataset.id);
      if (!mid) return;
      if (btn.dataset.act === "mark-reminded") {
        await api(`/api/payment-milestones/${mid}/mark-reminded`, { method: "POST" });
      }
      if (btn.dataset.act === "mark-paid") {
        await api(`/api/payment-milestones/${mid}/mark-paid`, { method: "POST" });
      }
      await renderProjectDetail(projectId);
      if (state.module === "projects") await loadCrud("projects");
      await refreshVisiblePaymentViews();
    });
  }
  if (q("#project-add-change-order")) {
    q("#project-add-change-order").addEventListener("click", async () => {
      const payload = {
        project_id: Number(projectId),
        contract_id: Number(o.contract_id || sourceContract?.id || 0) || null,
        customer_id: Number(o.customer_id || 0) || null,
        title: (q("#project-co-title")?.value || "").trim(),
        description: (q("#project-co-desc")?.value || "").trim(),
        amount_delta: Number((q("#project-co-amount")?.value || "").trim() || 0),
        impact_payment_plan: Number(q("#project-co-impact-plan")?.value || 0),
        affect_designer_commission: Number(q("#project-co-affect-commission")?.value || 0),
        status: "draft",
      };
      if (!payload.title) {
        alert(fieldLabel("title"));
        return;
      }
      await api("/api/change-orders", { method: "POST", body: JSON.stringify(payload) });
      if (q("#project-co-title")) q("#project-co-title").value = "";
      if (q("#project-co-desc")) q("#project-co-desc").value = "";
      if (q("#project-co-amount")) q("#project-co-amount").value = "";
      await renderProjectDetail(projectId);
      if (state.module === "change_orders") await loadCrud("change_orders");
      await refreshVisiblePaymentViews();
    });
  }
  if (q("#project-change-order-table")) {
    q("#project-change-order-table").addEventListener("click", async (e) => {
      const btn = e.target.closest("button[data-co-act]");
      if (!btn) return;
      const coid = Number(btn.dataset.id);
      if (!coid) return;
      const act = btn.dataset.coAct;
      if (act === "open") {
        closeProjectDetailDrawer();
        await openChangeOrderDetail(coid);
        return;
      }
      if (act === "print") {
        window.open(`/print/change-order/${coid}?lang=${encodeURIComponent(state.pdfLang)}`, "_blank");
        return;
      }
      if (act === "mark-sent") {
        await api(`/api/change-orders/${coid}/mark-sent`, { method: "POST" });
      }
      if (act === "mark-approved") {
        await api(`/api/change-orders/${coid}/mark-approved`, { method: "POST" });
      }
      if (act === "mark-rejected") {
        await api(`/api/change-orders/${coid}/mark-rejected`, { method: "POST" });
      }
      await renderProjectDetail(projectId);
      if (state.module === "change_orders") await loadCrud("change_orders");
      await refreshVisiblePaymentViews();
    });
  }
  if (q("#recalc-commission-btn")) {
    q("#recalc-commission-btn").addEventListener("click", async () => {
      await api(`/api/projects/${projectId}/designer-commission/recalculate`, { method: "POST" });
      await renderProjectDetail(projectId);
      if (state.module === "projects") await loadCrud("projects");
      await refreshVisiblePaymentViews();
    });
  }
  q("#add-project-log").addEventListener("click", async () => {
    const payload = {
      log_date: q("#project-log-date").value,
      content: q("#project-log-content").value.trim(),
      image_url: q("#project-log-image").value.trim(),
    };
    if (!payload.content) {
      alert(t("log_content"));
      return;
    }
    await addProjectLog(projectId, payload);
    q("#project-log-content").value = "";
    q("#project-log-image").value = "";
    await renderProjectLogs(projectId);
  });

  await renderProjectWorkflow(projectId);
  await renderProjectLogs(projectId);
  await renderProjectAttachmentPanel(projectId);
}

async function renderProjectWorkflow(projectId) {
  const root = q("#project-workflow");
  if (!root) return;
  const progressData = await api(`/api/projects/${projectId}/progress`);
  const stages = progressData.stages || [];

  if (!stages.length) {
    root.innerHTML = `
      <div class="row gap">
        <span>${t("no_flow")}</span>
      </div>
      <div class="row gap" style="margin-top:8px;">
        <button id="workflow-init-btn">${t("init_flow")}</button>
      </div>
    `;
    q("#workflow-init-btn").addEventListener("click", async () => {
      await api(`/api/projects/${projectId}/progress/init`, { method: "POST", body: JSON.stringify({ stages: DEFAULT_PROJECT_STAGE_NAMES }) });
      await renderProjectDetail(projectId);
      if (state.module === "projects") await loadCrud("projects");
      await refreshVisiblePaymentViews();
    });
    return;
  }

  const doneCount = stages.filter((s) => normalizeEnum(s.status) === "done").length;
  const pct = Math.round((doneCount * 100) / stages.length);
  root.innerHTML = `
    ${renderInlineProgress(projectId, stages, pct, true)}
    <div class="row gap" style="margin-top:10px;">
      <button id="workflow-reinit-btn" class="secondary">${t("reinit_flow")}</button>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>${t("stage_name")}</th><th>${t("stage_status")}</th></tr></thead>
        <tbody>
          ${stages.map((s) => `<tr>
            <td>${esc(s.stage_name)}</td>
            <td>
              <select data-stage-id="${s.id}" data-key="stage-status" class="stage-editor">
                <option value="pending" ${s.status === "pending" ? "selected" : ""}>${t("pending")}</option>
                <option value="in_progress" ${s.status === "in_progress" ? "selected" : ""}>${t("in_progress")}</option>
                <option value="done" ${s.status === "done" ? "selected" : ""}>${t("done")}</option>
              </select>
            </td>
          </tr>`).join("")}
        </tbody>
      </table>
    </div>
  `;

  q("#workflow-reinit-btn").addEventListener("click", async () => {
    await api(`/api/projects/${projectId}/progress/init`, { method: "POST", body: JSON.stringify({ stages: DEFAULT_PROJECT_STAGE_NAMES }) });
    await renderProjectDetail(projectId);
    if (state.module === "projects") await loadCrud("projects");
    await refreshVisiblePaymentViews();
  });
  bindStagePillActions(root, async () => {
    await renderProjectDetail(projectId);
    if (state.module === "projects") await loadCrud("projects");
    await refreshVisiblePaymentViews();
  });
  root.querySelectorAll("select[data-key='stage-status']").forEach((sel) => {
    sel.addEventListener("change", async () => {
      const sid = sel.dataset.stageId;
      const status = sel.value;
      await updateStageStatus(sid, status);
      await renderProjectDetail(projectId);
      if (state.module === "projects") await loadCrud("projects");
      await refreshVisiblePaymentViews();
    });
  });
}

function calcEstimateFromItems(items, markupRate) {
  const subtotal = (items || []).reduce((sum, it) => sum + Number(it.subtotal || 0), 0);
  const markup = Number(markupRate || 0);
  const total = subtotal * (1 + markup);
  return { subtotal, total };
}

async function renderTemplateTable() {
  const rows = await api("/api/estimate_templates");
  const table = q("#tpl-table");
  if (!table) return;
  table.innerHTML = `
    <thead><tr><th>${fieldLabel("id")}</th><th>${t("template_name")}</th><th>${t("package_type")}</th><th>${fieldLabel("markup_rate")}</th><th>${t("actions")}</th></tr></thead>
    <tbody>
      ${rows.map((r) => `<tr>
        <td>${r.id}</td>
        <td>${esc(r.name)}</td>
        <td>${esc(r.package_type || "")}</td>
        <td>${esc(r.default_markup_rate)}</td>
        <td>
          <button data-act="tpl-apply" data-id="${r.id}">${t("apply_template")}</button>
          <button data-act="tpl-del" data-id="${r.id}" class="danger">${t("del")}</button>
        </td>
      </tr>`).join("")}
    </tbody>
  `;

  table.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const act = btn.dataset.act;
      if (act === "tpl-del") {
        if (!confirm(t("confirm_del"))) return;
        await api(`/api/estimate_templates/${id}`, { method: "DELETE" });
        await renderTemplateTable();
        return;
      }
      if (act === "tpl-apply") {
        const tpl = await api(`/api/estimate_templates/${id}`);
        let items = [];
        try {
          items = JSON.parse(tpl.line_items_json || "[]");
          if (!Array.isArray(items)) items = [];
        } catch {
          items = [];
        }
        const calc = calcEstimateFromItems(items, tpl.default_markup_rate);
        const form = q("#entity-form");
        if (!form) return;
        const setVal = (name, val) => {
          const el = form.querySelector(`[name="${name}"]`);
          if (el) el.value = val ?? "";
        };
        setVal("title", tpl.name || "");
        setVal("line_items_json", tpl.line_items_json || "[]");
        setVal("markup_rate", tpl.default_markup_rate ?? 0);
        setVal("subtotal", calc.subtotal);
        setVal("total_amount", calc.total.toFixed(2));
      }
    });
  });
}

function milestoneStateClass(stateKey) {
  const key = normalizeEnum(stateKey || "untriggered");
  if (["untriggered", "pending", "reminded", "paid"].includes(key)) return key;
  return "untriggered";
}

function milestoneAmountText(item) {
  const tpe = normalizeEnum(item.amount_type || "percent");
  if (tpe === "percent") {
    return `${fmt(item.amount_value)}% (${fmtMoney(item.amount_due)})`;
  }
  return fmtMoney(item.amount_due);
}

function milestoneTriggerText(m) {
  return `${triggerTypeLabel(m.trigger_type)}${m.trigger_stage ? ` / ${esc(m.trigger_stage)}` : ""}${m.trigger_progress !== null && m.trigger_progress !== undefined && m.trigger_progress !== "" ? ` / ${fmt(m.trigger_progress)}%` : ""}`;
}

async function renderContractChangeOrderPanel(contractRow = null) {
  const host = q("#contract-change-order-panel");
  if (!host) return;

  let contractId = Number(state.contractMilestoneContractId || state.editId || 0);
  if (contractRow && contractRow.id) contractId = Number(contractRow.id);
  if (!contractId) {
    host.innerHTML = `<h4>${t("change_order_summary")}</h4><div class="list-item">${t("no_data")}</div>`;
    return;
  }
  const contract = contractRow || await api(`/api/contracts/${contractId}`);
  const changeOrders = await api(`/api/change-orders?contract_id=${contractId}`);
  const warningCount = Number(contract.change_orders_affect_payment_plan_count || 0);

  host.innerHTML = `
    <h4>${t("change_order_summary")}</h4>
    <div class="detail-base-grid">
      <div class="detail-kpi"><div class="k">${fieldLabel("total_amount")}</div><div class="v">${fmtMoney(contract.base_contract_amount ?? contract.total_amount ?? 0)}</div></div>
      <div class="detail-kpi"><div class="k">${t("approved_change_total")}</div><div class="v">${fmtMoney(contract.approved_change_amount || 0)}</div></div>
      <div class="detail-kpi"><div class="k">${t("current_contract_total")}</div><div class="v">${fmtMoney(contract.current_contract_total || 0)}</div></div>
      <div class="detail-kpi"><div class="k">${t("impact_payment_plan_count")}</div><div class="v">${fmt(contract.change_orders_affect_payment_plan_count || 0)}</div></div>
      <div class="detail-kpi"><div class="k">${t("approved_change_commissionable")}</div><div class="v">${fmtMoney(contract.approved_commissionable_change_amount || 0)}</div></div>
      <div class="detail-kpi"><div class="k">${t("approved_change_non_commissionable")}</div><div class="v">${fmtMoney(contract.approved_non_commissionable_change_amount || 0)}</div></div>
    </div>
    ${warningCount > 0 ? `<div class="notice-inline">${t("change_order_warn_payment_plan")}</div>` : ""}
    <div class="row gap" style="margin-top:8px;">
      <button id="contract-open-change-orders" class="secondary">${t("open_change_order_module")}</button>
    </div>
    <div class="table-wrap" style="margin-top:8px;">
      <table id="contract-change-order-table">
        <thead><tr><th>${fieldLabel("order_no")}</th><th>${fieldLabel("title")}</th><th>${fieldLabel("amount_delta")}</th><th>${fieldLabel("status")}</th><th>${fieldLabel("impact_payment_plan")}</th><th>${fieldLabel("affect_designer_commission")}</th><th>${t("actions")}</th></tr></thead>
        <tbody>
          ${changeOrders.length ? changeOrders.map((x) => `
            <tr>
              <td>${esc(x.order_no || `CO-${x.id}`)}</td>
              <td>${esc(x.title || "-")}</td>
              <td>${fmtMoney(x.amount_delta || 0)}</td>
              <td><span class="co-status-pill ${changeOrderStatusClass(x.status)}">${displayValue("status", x.status || "draft")}</span></td>
              <td>${displayValue("impact_payment_plan", x.impact_payment_plan)}</td>
              <td>${displayValue("affect_designer_commission", x.affect_designer_commission)}</td>
              <td class="row gap">
                <button data-act="open-change-order" data-id="${x.id}" class="secondary">${t("detail")}</button>
                <button data-act="print-change-order" data-id="${x.id}">${t("print_change_order_doc")}</button>
              </td>
            </tr>
          `).join("") : `<tr><td colspan="7">${t("no_data")}</td></tr>`}
        </tbody>
      </table>
    </div>
  `;

  const openBtn = q("#contract-open-change-orders");
  if (openBtn) {
    openBtn.addEventListener("click", async () => {
      state.module = "change_orders";
      state.changeOrderStatusFilter = "";
      await renderApp();
      if (q("#change-order-project-filter") && contract.project_id) {
        state.changeOrderProjectFilter = String(contract.project_id);
        q("#change-order-project-filter").value = String(contract.project_id);
      }
      await loadCrud("change_orders");
    });
  }
  const table = q("#contract-change-order-table");
  if (!table) return;
  table.querySelectorAll("button[data-act='open-change-order']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await openChangeOrderDetail(btn.dataset.id);
    });
  });
  table.querySelectorAll("button[data-act='print-change-order']").forEach((btn) => {
    btn.addEventListener("click", () => {
      window.open(`/print/change-order/${btn.dataset.id}?lang=${encodeURIComponent(state.pdfLang)}`, "_blank");
    });
  });
}

async function renderContractMilestonePanel() {
  const host = q("#contract-milestone-panel");
  if (!host) return;

  const contracts = await api("/api/contracts");
  if (!contracts.length) {
    host.innerHTML = `<h4>${t("payment_milestones")}</h4><div class="list-item">${t("no_contracts")}</div>`;
    return;
  }

  let contractId = Number(state.contractMilestoneContractId || state.editId || contracts[0].id);
  if (!contracts.some((x) => Number(x.id) === contractId)) contractId = Number(contracts[0].id);
  state.contractMilestoneContractId = contractId;

  const milestones = await api(`/api/contracts/${contractId}/payment-milestones`);
  const editing = milestones.find((x) => Number(x.id) === Number(state.editingMilestoneId)) || null;
  const triggerType = editing ? normalizeEnum(editing.trigger_type) : "stage_done";
  const amountType = editing ? normalizeEnum(editing.amount_type) : "percent";

  host.innerHTML = `
    <h4>${t("payment_plan_module")}</h4>
    <div class="row gap" style="margin-top:8px;">
      <label style="min-width:110px;">${t("select_contract")}</label>
      <select id="milestone-contract">
        ${contracts.map((c) => `<option value="${c.id}" ${Number(c.id) === contractId ? "selected" : ""}>#${c.id} ${esc(c.contract_no || "")}</option>`).join("")}
      </select>
    </div>
    <div class="grid-2 compact" style="margin-top:8px;">
      <div class="field"><label>${t("milestone_name")}</label><input id="milestone-name" value="${esc(editing?.name || "")}" /></div>
      <div class="field"><label>${t("milestone_type")}</label><input id="milestone-node-type" value="${esc(editing?.node_type || "")}" /></div>
      <div class="field">
        <label>${t("trigger_type")}</label>
        <select id="milestone-trigger-type">
          <option value="contract_signed" ${triggerType === "contract_signed" ? "selected" : ""}>${triggerTypeLabel("contract_signed")}</option>
          <option value="stage_started" ${triggerType === "stage_started" ? "selected" : ""}>${triggerTypeLabel("stage_started")}</option>
          <option value="stage_done" ${triggerType === "stage_done" ? "selected" : ""}>${triggerTypeLabel("stage_done")}</option>
          <option value="progress_percent" ${triggerType === "progress_percent" ? "selected" : ""}>${triggerTypeLabel("progress_percent")}</option>
        </select>
      </div>
      <div class="field" id="milestone-trigger-stage-wrap"><label>${t("trigger_stage")}</label><input id="milestone-trigger-stage" value="${esc(editing?.trigger_stage || "")}" list="milestone-stage-options" /></div>
      <div class="field" id="milestone-trigger-progress-wrap"><label>${t("trigger_progress")}</label><input id="milestone-trigger-progress" type="number" min="0" max="100" value="${esc(editing?.trigger_progress ?? "")}" /></div>
      <div class="field">
        <label>${t("amount_type")}</label>
        <select id="milestone-amount-type">
          <option value="percent" ${amountType === "percent" ? "selected" : ""}>${amountTypeLabel("percent")}</option>
          <option value="fixed" ${amountType === "fixed" ? "selected" : ""}>${amountTypeLabel("fixed")}</option>
        </select>
      </div>
      <div class="field"><label>${t("amount_value")}</label><input id="milestone-amount-value" type="number" step="0.01" value="${esc(editing?.amount_value ?? "")}" /></div>
      <div class="field"><label>${fieldLabel("notes")}</label><input id="milestone-note" value="${esc(editing?.note || "")}" /></div>
    </div>
    <datalist id="milestone-stage-options">
      ${DEFAULT_PROJECT_STAGE_NAMES.map((x) => `<option value="${esc(x)}"></option>`).join("")}
    </datalist>
    <div class="row gap" style="margin-top:8px;">
      <button id="milestone-save-btn">${editing ? t("update_milestone") : t("add_milestone")}</button>
      ${editing ? `<button id="milestone-cancel-btn" class="secondary">${t("cancel_edit")}</button>` : ""}
    </div>
    <div class="table-wrap">
      <table id="milestone-table">
        <thead><tr><th>ID</th><th>${t("milestone_name")}</th><th>${t("trigger_type")}</th><th>${t("amount")}</th><th>${t("state")}</th><th>${t("trigger_reason")}</th><th>${t("actions")}</th></tr></thead>
        <tbody>
          ${milestones.length ? milestones.map((m) => `
            <tr>
              <td>${m.id}</td>
              <td>${esc(m.name || "-")}</td>
              <td>${milestoneTriggerText(m)}</td>
              <td>${milestoneAmountText(m)}</td>
              <td><span class="milestone-pill ${milestoneStateClass(m.state)}">${milestoneStateLabel(m.state)}</span></td>
              <td>${esc(m.trigger_reason || "-")}</td>
              <td class="row gap">
                <button data-act="edit-milestone" data-id="${m.id}" class="secondary">${t("edit")}</button>
                <button data-act="del-milestone" data-id="${m.id}" class="danger">${t("delete_milestone")}</button>
                ${m.state === "pending" ? `<button data-act="mark-reminded" data-id="${m.id}" class="secondary">${t("mark_reminded")}</button>` : ""}
                ${m.state !== "paid" ? `<button data-act="mark-paid" data-id="${m.id}">${t("mark_paid")}</button>` : ""}
              </td>
            </tr>
          `).join("") : `<tr><td colspan="7">${t("no_milestones")}</td></tr>`}
        </tbody>
      </table>
    </div>
  `;

  q("#milestone-contract").addEventListener("change", async () => {
    state.contractMilestoneContractId = Number(q("#milestone-contract").value);
    state.editingMilestoneId = null;
    await renderContractMilestonePanel();
  });

  const triggerTypeEl = q("#milestone-trigger-type");
  const stageWrap = q("#milestone-trigger-stage-wrap");
  const progressWrap = q("#milestone-trigger-progress-wrap");
  const applyTriggerVisibility = () => {
    const tp = triggerTypeEl.value;
    const needStage = tp === "stage_started" || tp === "stage_done";
    const needProgress = tp === "progress_percent";
    stageWrap.classList.toggle("hidden", !needStage);
    progressWrap.classList.toggle("hidden", !needProgress);
  };
  triggerTypeEl.addEventListener("change", applyTriggerVisibility);
  applyTriggerVisibility();

  q("#milestone-save-btn").addEventListener("click", async () => {
    const payload = {
      name: q("#milestone-name").value.trim(),
      node_type: q("#milestone-node-type").value.trim(),
      trigger_type: q("#milestone-trigger-type").value,
      trigger_stage: q("#milestone-trigger-stage").value.trim(),
      trigger_progress: q("#milestone-trigger-progress").value.trim(),
      amount_type: q("#milestone-amount-type").value,
      amount_value: q("#milestone-amount-value").value.trim(),
      note: q("#milestone-note").value.trim(),
    };
    if (payload.trigger_type === "contract_signed") {
      payload.trigger_stage = "";
      payload.trigger_progress = "";
    } else if (payload.trigger_type === "progress_percent") {
      payload.trigger_stage = "";
    } else {
      payload.trigger_progress = "";
    }
    if (!payload.name) {
      alert(t("milestone_name"));
      return;
    }
    if (!payload.amount_value) {
      alert(t("amount_value"));
      return;
    }
    if ((payload.trigger_type === "stage_started" || payload.trigger_type === "stage_done") && !payload.trigger_stage) {
      alert(t("trigger_stage"));
      return;
    }
    if (payload.trigger_type === "progress_percent" && payload.trigger_progress === "") {
      alert(t("trigger_progress"));
      return;
    }

    if (state.editingMilestoneId) {
      await api(`/api/payment-milestones/${state.editingMilestoneId}`, { method: "PUT", body: JSON.stringify(payload) });
    } else {
      await api(`/api/contracts/${state.contractMilestoneContractId}/payment-milestones`, { method: "POST", body: JSON.stringify(payload) });
    }
    state.editingMilestoneId = null;
    await renderContractMilestonePanel();
  });

  if (q("#milestone-cancel-btn")) {
    q("#milestone-cancel-btn").addEventListener("click", async () => {
      state.editingMilestoneId = null;
      await renderContractMilestonePanel();
    });
  }

  q("#milestone-table").addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-act]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    if (!id) return;
    if (btn.dataset.act === "edit-milestone") {
      state.editingMilestoneId = id;
      await renderContractMilestonePanel();
      return;
    }
    if (btn.dataset.act === "del-milestone") {
      if (!confirm(t("confirm_del_milestone"))) return;
      await api(`/api/contract_payment_milestones/${id}`, { method: "DELETE" });
      state.editingMilestoneId = null;
      await renderContractMilestonePanel();
      return;
    }
    if (btn.dataset.act === "mark-reminded") {
      await api(`/api/payment-milestones/${id}/mark-reminded`, { method: "POST" });
      await renderContractMilestonePanel();
      return;
    }
    if (btn.dataset.act === "mark-paid") {
      await api(`/api/payment-milestones/${id}/mark-paid`, { method: "POST" });
      await renderContractMilestonePanel();
    }
  });
}

async function createTemplateFromPanel() {
  let parsed = [];
  try {
    parsed = JSON.parse(q("#tpl-items").value || "[]");
    if (!Array.isArray(parsed)) throw new Error("invalid");
  } catch {
    alert("line_items_json must be a JSON array");
    return;
  }
  const payload = {
    name: q("#tpl-name").value.trim(),
    package_type: q("#tpl-package").value.trim(),
    default_markup_rate: Number(q("#tpl-markup").value || 0),
    line_items_json: JSON.stringify(parsed),
    notes: q("#tpl-notes").value.trim(),
  };
  await api("/api/estimate_templates", { method: "POST", body: JSON.stringify(payload) });
  q("#tpl-name").value = "";
  q("#tpl-package").value = "";
  q("#tpl-markup").value = "";
  q("#tpl-items").value = "";
  q("#tpl-notes").value = "";
  await renderTemplateTable();
}

async function renderCustomerQuickLeadPanel() {
  const host = q("#quick-lead-panel");
  if (!host) return;
  host.innerHTML = `
    <h4>${t("quick_lead_entry")}</h4>
    <div class="row gap" style="margin-top:8px;">
      <input id="quick-lead-name" placeholder="${fieldLabel("name")}" />
      <input id="quick-lead-phone" placeholder="${fieldLabel("phone")}" />
    </div>
    <div class="row gap" style="margin-top:8px;">
      <input id="quick-lead-address" placeholder="${fieldLabel("address")}" />
      <select id="quick-lead-source">
        ${renderOptionList(SOURCE_CHANNEL_OPTIONS, "manual", "source_channel")}
      </select>
    </div>
    <div class="row gap" style="margin-top:8px;">
      <select id="quick-lead-inquiry">
        ${renderOptionList(INQUIRY_TYPE_OPTIONS, "other", "inquiry_type")}
      </select>
      <input id="quick-lead-note" placeholder="${fieldLabel("notes")}" />
    </div>
    <div class="row gap" style="margin-top:8px;">
      <button id="quick-lead-submit">${t("quick_submit_lead")}</button>
    </div>
  `;
  const submitBtn = q("#quick-lead-submit");
  if (!submitBtn) return;
  submitBtn.addEventListener("click", async () => {
    const sourceVal = q("#quick-lead-source")?.value || "manual";
    const payload = {
      name: (q("#quick-lead-name")?.value || "").trim(),
      phone: (q("#quick-lead-phone")?.value || "").trim(),
      address: (q("#quick-lead-address")?.value || "").trim(),
      source_channel: sourceVal,
      inquiry_type: q("#quick-lead-inquiry")?.value || "other",
      source_note: valueLabel("source_channel", sourceVal) || sourceVal,
      message: (q("#quick-lead-note")?.value || "").trim(),
    };
    if (!payload.name && !payload.phone) {
      alert(t("lead_required_hint"));
      return;
    }
    let result = null;
    try {
      result = await api("/api/leads/intake", { method: "POST", body: JSON.stringify(payload) });
    } catch (err) {
      if (err.status === 409 && err.payload?.require_merge_confirm) {
        if (!confirm(t("confirm_merge_lead"))) return;
        payload.merge_existing = true;
        result = await api("/api/leads/intake", { method: "POST", body: JSON.stringify(payload) });
      } else {
        throw err;
      }
    }
    await loadCrud("customers");
    if (result?.customer?.id) {
      await openCustomerDetail(result.customer.id);
    }
  });
}

async function renderCustomerFollowupPanel(customer = null) {
  const host = q("#customer-followup-panel");
  if (!host) return;
  if (!customer || !customer.id) {
    host.innerHTML = `<h4>${t("followup_records")}</h4><div class="list-item">${t("no_data")}</div>`;
    return;
  }
  const customerId = Number(customer.id);
  const rows = await api(`/api/customers/${customerId}/followups`);
  host.innerHTML = `
    <h4>${t("followup_records")}</h4>
    <div class="row gap" style="margin-top:8px;">
      <select id="cust-followup-type">
        ${renderOptionList(FOLLOWUP_TYPE_OPTIONS, "phone", "followup_type")}
      </select>
      <input id="cust-followup-result" placeholder="${fieldLabel("result")}" />
    </div>
    <div class="row gap" style="margin-top:8px;">
      <textarea id="cust-followup-content" rows="2" placeholder="${fieldLabel("content")}"></textarea>
    </div>
    <div class="row gap" style="margin-top:8px; align-items:center;">
      <label style="display:flex; align-items:center; gap:6px;"><input type="checkbox" id="cust-followup-enable-next" /> ${t("set_next_followup")}</label>
      <input id="cust-followup-next-at" type="datetime-local" style="display:none;" />
      <button id="cust-followup-add">${t("add_followup")}</button>
    </div>
    <div class="simple-list" style="margin-top:10px;">
      ${rows.length ? rows.map((x) => `
        <div class="list-item">
          <div><b>${esc(x.created_at || "-")}</b> · ${displayValue("followup_type", x.followup_type || "note")} · ${x.completed ? t("status_completed") : t("status_uncompleted")}</div>
          <div>${fieldLabel("content")}：${esc(x.content || "-")}</div>
          <div>${fieldLabel("result")}：${esc(x.result || "-")}</div>
          <div>${fieldLabel("next_followup_at")}：${esc(x.next_followup_at || t("no_next_followup"))}</div>
          ${!x.completed ? `<div class="row gap" style="margin-top:6px;"><button data-act="followup-complete" data-id="${x.id}" class="secondary">${t("mark_completed")}</button></div>` : ""}
        </div>
      `).join("") : `<div class="list-item">${t("no_followup_records")}</div>`}
    </div>
  `;

  const toggle = q("#cust-followup-enable-next");
  const nextInput = q("#cust-followup-next-at");
  if (toggle && nextInput) {
    toggle.addEventListener("change", () => {
      nextInput.style.display = toggle.checked ? "" : "none";
      if (toggle.checked && !nextInput.value) {
        nextInput.value = new Date(Date.now() + 24 * 3600 * 1000).toISOString().slice(0, 16);
      }
    });
  }
  const addBtn = q("#cust-followup-add");
  if (addBtn) {
    addBtn.addEventListener("click", async () => {
      const payload = {
        followup_type: q("#cust-followup-type")?.value || "note",
        content: (q("#cust-followup-content")?.value || "").trim(),
        result: (q("#cust-followup-result")?.value || "").trim(),
      };
      if (toggle && toggle.checked) {
        payload.next_followup_at = (q("#cust-followup-next-at")?.value || "").trim() || null;
      }
      if (!payload.content) return;
      await addCustomerFollowup(customerId, payload);
      await renderCustomerFollowupPanel(customer);
      alert(t("followup_saved"));
    });
  }
  host.querySelectorAll("button[data-act='followup-complete']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      await markFollowupCompleted(btn.dataset.id);
      await renderCustomerFollowupPanel(customer);
    });
  });
}

async function renderCustomerEstimatePanel(customer = null) {
  const host = q("#customer-estimate-panel");
  if (!host) return;
  if (!customer || !customer.id) {
    host.innerHTML = `<h4>${t("related_estimates")}</h4><div class="list-item">${t("no_data")}</div>`;
    return;
  }
  const customerId = Number(customer.id);
  const rows = await api(`/api/customers/${customerId}/estimates`);
  host.innerHTML = `
    <h4>${t("related_estimates")}</h4>
    <div class="row gap" style="margin-top:8px;">
      <div class="user-meta" style="border-radius:8px;">#${customerId} ${esc(customer.name || "")}</div>
      <button data-act="customer-generate-estimate">${t("generate_estimate")}</button>
    </div>
    <div class="table-wrap">
      <table id="customer-estimate-table">
        <thead><tr><th>ID</th><th>${fieldLabel("title")}</th><th>${t("amount")}</th><th>${fieldLabel("status")}</th><th>${fieldLabel("contract_generated")}</th><th>${t("actions")}</th></tr></thead>
        <tbody>
          ${rows.length ? rows.map((r) => `
            <tr>
              <td>${r.id}</td>
              <td>${esc(r.title || "-")}</td>
              <td>${fmtMoney(r.total_amount || 0)}</td>
              <td>${displayValue("status", r.status || "-")}</td>
              <td>${displayValue("contract_generated", r.contract_generated || "ungenerated")}</td>
              <td><button class="secondary" data-act="open-estimate" data-id="${r.id}">${t("view_estimate")}</button></td>
            </tr>
          `).join("") : `<tr><td colspan="6">${t("no_data")}</td></tr>`}
        </tbody>
      </table>
    </div>
    <div class="simple-list" style="margin-top:10px;">
      <div class="list-item">
        <div><b>${t("source_info")}</b></div>
        <div>${fieldLabel("source_channel")}：${displayValue("source_channel", customer.source_channel || "manual")}</div>
        <div>${fieldLabel("source_note")}：${esc(customer.source_note || customer.source || "-")}</div>
      </div>
      <div class="list-item">
        <div><b>${t("inquiry_info")}</b></div>
        <div>${fieldLabel("inquiry_type")}：${displayValue("inquiry_type", customer.inquiry_type || "other")}</div>
        <div>${fieldLabel("notes")}：${esc(customer.notes || "-")}</div>
      </div>
      <div class="list-item">
        <div><b>${t("preferred_contact")}</b></div>
        <div>${displayValue("preferred_contact_method", customer.preferred_contact_method || "-")}</div>
      </div>
    </div>
  `;

  q("#customer-estimate-panel button[data-act='customer-generate-estimate']").addEventListener("click", async () => {
    const r = await api(`/api/customers/${customerId}/generate-estimate`, { method: "POST" });
    await loadCrud("customers");
    await openEstimateDetail(r.estimate?.id);
  });
  if (q("#customer-estimate-table")) {
    q("#customer-estimate-table").querySelectorAll("button[data-act='open-estimate']").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await openEstimateDetail(btn.dataset.id);
      });
    });
  }
}

async function renderRecordLinkPanel(module, row = null) {
  const host = q("#record-link-panel");
  if (!host) return;
  if (!row || !row.id) {
    host.innerHTML = `<h4>${t("source_relation")}</h4><div class="list-item">${t("no_data")}</div>`;
    return;
  }

  if (module === "estimates") {
    let linkedContractId = row.linked_contract_id ? Number(row.linked_contract_id) : null;
    let linkedContractNo = row.linked_contract_no || "";
    if (!linkedContractId) {
      try {
        const contracts = await api("/api/contracts");
        const linked = (contracts || []).find((x) => Number(x.estimate_id) === Number(row.id));
        if (linked) {
          linkedContractId = Number(linked.id);
          linkedContractNo = linked.contract_no || "";
        }
      } catch {
        linkedContractId = null;
      }
    }
    host.innerHTML = `
      <h4>${t("source_relation")}</h4>
      <div class="simple-list">
        <div class="list-item">
          <div><b>${t("source_customer")}</b></div>
          <div>${row.customer_id ? `#${row.customer_id} ${esc(row.customer_name || "-")}` : "-"}</div>
          <div>${esc(row.customer_phone || "-")} / ${esc(row.customer_address || row.address || "-")}</div>
          <div>${displayValue("source_type", row.source_type || "customer")}</div>
          <div class="row gap" style="margin-top:6px;">
            ${row.customer_id ? `<button data-rel-act="view-customer" data-customer-id="${row.customer_id}" class="secondary">${t("view_customer")}</button>` : ""}
          </div>
        </div>
        <div class="list-item">
          <div><b>${t("source_estimate")} #${row.id}</b></div>
          <div>${esc(row.title || "-")} / ${fmtMoney(row.total_amount || 0)}</div>
          <div>${fieldLabel("status")}：${displayValue("status", row.status || "-")}</div>
        </div>
        <div class="list-item">
          <div><b>${t("source_contract")}</b></div>
          <div>${linkedContractId ? `#${linkedContractId} ${esc(linkedContractNo || "")}` : t("no_data")}</div>
          <div class="row gap" style="margin-top:6px;">
            ${linkedContractId
              ? `<button data-rel-act="view-contract" data-contract-id="${linkedContractId}" class="secondary">${t("view_contract")}</button>`
              : `<button data-rel-act="generate-contract" data-estimate-id="${row.id}">${t("generate_contract")}</button>`}
          </div>
        </div>
        <div class="list-item">
          <div><b>${t("pdf")}</b></div>
          <div class="row gap" style="margin-top:6px;">
            <button data-rel-act="print-estimate" data-estimate-id="${row.id}" class="secondary">${t("print_estimate_doc")}</button>
            <button data-rel-act="export-estimate-pdf" data-estimate-id="${row.id}">${t("export_estimate_pdf")}</button>
          </div>
        </div>
      </div>
    `;
  } else if (module === "contracts") {
    let linkedProjectId = row.linked_project_id ? Number(row.linked_project_id) : (row.project_id ? Number(row.project_id) : null);
    let linkedProjectName = row.linked_project_name || "";
    if (!linkedProjectId && can("projects")) {
      try {
        const projects = await api("/api/projects");
        const linked = (projects || []).find((x) => Number(x.contract_id) === Number(row.id));
        if (linked) {
          linkedProjectId = Number(linked.id);
          linkedProjectName = linked.name || "";
        }
      } catch {
        linkedProjectId = null;
      }
    }
    let sourceEstimateTitle = row.source_estimate_title || "";
    if (row.estimate_id && !sourceEstimateTitle) {
      try {
        const est = await api(`/api/estimates/${row.estimate_id}`);
        sourceEstimateTitle = est.title || "";
      } catch {
        sourceEstimateTitle = "";
      }
    }
    host.innerHTML = `
      <h4>${t("source_relation")}</h4>
      <div class="simple-list">
        <div class="list-item">
          <div><b>${t("source_contract")} #${row.id}</b></div>
          <div>${esc(row.contract_no || "-")} / ${esc(row.title || "-")}</div>
        </div>
        <div class="list-item">
          <div><b>${t("source_estimate")}</b></div>
          <div>${row.estimate_id ? `#${row.estimate_id} ${esc(sourceEstimateTitle || "")}` : t("no_data")}</div>
          <div class="row gap" style="margin-top:6px;">
            ${row.estimate_id ? `<button data-rel-act="view-estimate" data-estimate-id="${row.estimate_id}" class="secondary">${t("view_estimate")}</button>` : ""}
          </div>
        </div>
        <div class="list-item">
          <div><b>${t("linked_project")}</b></div>
          <div>${linkedProjectId ? `#${linkedProjectId} ${esc(linkedProjectName || "")}` : t("no_data")}</div>
          <div class="row gap" style="margin-top:6px;">
            ${linkedProjectId
              ? `<button data-rel-act="view-project" data-project-id="${linkedProjectId}" class="secondary">${t("view_project")}</button>`
              : `<button data-rel-act="generate-project" data-contract-id="${row.id}">${t("generate_project")}</button>`}
          </div>
        </div>
        <div class="list-item">
          <div><b>${t("change_order_summary")}</b></div>
          <div>${t("approved_change_total")}：${fmtMoney(row.approved_change_amount || 0)}</div>
          <div>${t("current_contract_total")}：${fmtMoney(row.current_contract_total || row.total_amount || 0)}</div>
          <div>${t("impact_payment_plan_count")}：${fmt(row.change_orders_affect_payment_plan_count || 0)}</div>
          ${Number(row.change_orders_affect_payment_plan_count || 0) > 0 ? `<div class="notice-inline" style="margin-top:6px;">${t("change_order_warn_payment_plan")}</div>` : ""}
          <div class="row gap" style="margin-top:6px;">
            <button data-rel-act="open-change-orders" data-contract-id="${row.id}" data-project-id="${row.linked_project_id || row.project_id || ""}" class="secondary">${t("open_change_order_module")}</button>
          </div>
        </div>
        <div class="list-item">
          <div><b>${t("pdf")}</b></div>
          <div class="row gap" style="margin-top:6px;">
            <button data-rel-act="print-contract" data-contract-id="${row.id}" class="secondary">${t("print_contract_doc")}</button>
            <button data-rel-act="export-contract-pdf" data-contract-id="${row.id}">${t("export_contract_pdf")}</button>
          </div>
        </div>
      </div>
    `;
  } else {
    host.innerHTML = "";
    return;
  }

  host.querySelectorAll("button[data-rel-act]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const act = btn.dataset.relAct;
      if (act === "generate-contract") {
        const r = await api(`/api/estimates/${btn.dataset.estimateId}/generate-contract`, { method: "POST" });
        await loadCrud("estimates");
        await openContractDetail(r.contract?.id);
        return;
      }
      if (act === "view-contract") {
        await openContractDetail(btn.dataset.contractId);
        return;
      }
      if (act === "view-customer") {
        await openCustomerDetail(btn.dataset.customerId);
        return;
      }
      if (act === "generate-project") {
        const r = await api(`/api/contracts/${btn.dataset.contractId}/generate-project`, { method: "POST" });
        await loadCrud("contracts");
        await openProjectDetail(r.project?.id);
        return;
      }
      if (act === "view-project") {
        await openProjectDetail(btn.dataset.projectId);
        return;
      }
      if (act === "view-estimate") {
        await openEstimateDetail(btn.dataset.estimateId);
        return;
      }
      if (act === "open-change-orders") {
        state.module = "change_orders";
        state.changeOrderStatusFilter = "";
        state.changeOrderProjectFilter = btn.dataset.projectId ? String(btn.dataset.projectId) : "";
        await renderApp();
        if (q("#change-order-project-filter")) {
          q("#change-order-project-filter").value = state.changeOrderProjectFilter || "";
        }
        await loadCrud("change_orders");
        return;
      }
      if (act === "print-estimate") {
        window.open(`/print/estimate/${btn.dataset.estimateId}?lang=${encodeURIComponent(state.pdfLang)}`, "_blank");
        return;
      }
      if (act === "export-estimate-pdf") {
        window.open(`/api/estimates/${btn.dataset.estimateId}/pdf?lang=${encodeURIComponent(state.pdfLang)}`, "_blank");
        return;
      }
      if (act === "print-contract") {
        window.open(`/print/contract/${btn.dataset.contractId}?lang=${encodeURIComponent(state.pdfLang)}`, "_blank");
        return;
      }
      if (act === "export-contract-pdf") {
        window.open(`/api/contracts/${btn.dataset.contractId}/pdf?lang=${encodeURIComponent(state.pdfLang)}`, "_blank");
      }
    });
  });
}

async function renderCrud(module) {
  crudScaffold(module);
  if (q("#pdf-lang-select")) q("#pdf-lang-select").value = state.pdfLang;
  renderForm(module);
  if (module === "customers") {
    await renderCustomerEstimatePanel(null);
    await renderCustomerFollowupPanel(null);
    await renderEntityAttachmentPanel({
      hostSelector: "#customer-file-panel",
      entityType: "customer",
      entityId: null,
      title: t("attachments"),
      defaultCategory: "other",
    });
    await renderCustomerQuickLeadPanel();
  }
  if (module === "estimates" || module === "contracts") {
    await renderRecordLinkPanel(module, null);
    await renderEntityAttachmentPanel({
      hostSelector: "#record-file-panel",
      entityType: module === "estimates" ? "estimate" : "contract",
      entityId: null,
      title: module === "estimates" ? t("estimate_attachments") : t("contract_attachments"),
      defaultCategory: module === "estimates" ? "estimate" : "contract",
    });
  }
  await loadCrud(module);
  if (module === "estimates") await renderTemplateTable();
  if (module === "contracts") await renderContractMilestonePanel();
  if (module === "contracts") await renderContractChangeOrderPanel();
  if (module === "change_orders") await renderChangeOrderProjectFilter();

  q("#search-btn").addEventListener("click", () => loadCrud(module));
  if (module === "customers") {
    if (q("#customer-source-filter")) {
      q("#customer-source-filter").addEventListener("change", async () => {
        state.customerSourceFilter = q("#customer-source-filter").value;
        await loadCrud("customers");
      });
    }
    if (q("#customer-status-filter")) {
      q("#customer-status-filter").addEventListener("change", async () => {
        state.customerStatusFilter = q("#customer-status-filter").value;
        await loadCrud("customers");
      });
    }
  }
  if (module === "change_orders") {
    if (q("#change-order-status-filter")) {
      q("#change-order-status-filter").addEventListener("change", async () => {
        state.changeOrderStatusFilter = q("#change-order-status-filter").value;
        await loadCrud("change_orders");
      });
    }
    if (q("#change-order-project-filter")) {
      q("#change-order-project-filter").addEventListener("change", async () => {
        state.changeOrderProjectFilter = q("#change-order-project-filter").value;
        await loadCrud("change_orders");
      });
    }
  }
  q("#new-btn").addEventListener("click", () => {
    state.editId = null;
    openCrudForm();
    renderForm(module);
    if (module === "customers") {
      renderCustomerEstimatePanel(null);
      renderCustomerFollowupPanel(null);
      renderEntityAttachmentPanel({
        hostSelector: "#customer-file-panel",
        entityType: "customer",
        entityId: null,
        title: t("attachments"),
        defaultCategory: "other",
      });
    }
    if (module === "estimates" || module === "contracts") {
      renderRecordLinkPanel(module, null);
      renderEntityAttachmentPanel({
        hostSelector: "#record-file-panel",
        entityType: module === "estimates" ? "estimate" : "contract",
        entityId: null,
        title: module === "estimates" ? t("estimate_attachments") : t("contract_attachments"),
        defaultCategory: module === "estimates" ? "estimate" : "contract",
      });
    }
    if (module === "contracts") {
      renderContractChangeOrderPanel(null);
    }
  });
  q("#save-btn").addEventListener("click", async () => {
    const data = collectForm();
    const apiBase = module === "change_orders" ? "/api/change-orders" : `/api/${module}`;
    if (state.editId) {
      await api(`${apiBase}/${state.editId}`, { method: "PUT", body: JSON.stringify(data) });
    } else {
      await api(`${apiBase}`, { method: "POST", body: JSON.stringify(data) });
    }
    state.editId = null;
    closeCrudForm();
    renderForm(module);
    if (module === "customers") {
      await renderCustomerEstimatePanel(null);
      await renderCustomerFollowupPanel(null);
      await renderEntityAttachmentPanel({
        hostSelector: "#customer-file-panel",
        entityType: "customer",
        entityId: null,
        title: t("attachments"),
        defaultCategory: "other",
      });
    }
    if (module === "estimates" || module === "contracts") {
      await renderRecordLinkPanel(module, null);
      await renderEntityAttachmentPanel({
        hostSelector: "#record-file-panel",
        entityType: module === "estimates" ? "estimate" : "contract",
        entityId: null,
        title: module === "estimates" ? t("estimate_attachments") : t("contract_attachments"),
        defaultCategory: module === "estimates" ? "estimate" : "contract",
      });
    }
    await loadCrud(module);
    if (module === "contracts") await renderContractMilestonePanel();
    if (module === "contracts") await renderContractChangeOrderPanel();
  });
  q("#reset-btn").addEventListener("click", () => {
    state.editId = null;
    if (module === "contracts") state.editingMilestoneId = null;
    closeCrudForm();
    renderForm(module);
    if (module === "customers") {
      renderCustomerEstimatePanel(null);
      renderCustomerFollowupPanel(null);
      renderEntityAttachmentPanel({
        hostSelector: "#customer-file-panel",
        entityType: "customer",
        entityId: null,
        title: t("attachments"),
        defaultCategory: "other",
      });
    }
    if (module === "estimates" || module === "contracts") {
      renderRecordLinkPanel(module, null);
      renderEntityAttachmentPanel({
        hostSelector: "#record-file-panel",
        entityType: module === "estimates" ? "estimate" : "contract",
        entityId: null,
        title: module === "estimates" ? t("estimate_attachments") : t("contract_attachments"),
        defaultCategory: module === "estimates" ? "estimate" : "contract",
      });
    }
    if (module === "contracts") {
      renderContractChangeOrderPanel(null);
    }
  });
  if (q("#pdf-lang-select")) {
    q("#pdf-lang-select").addEventListener("change", () => {
      state.pdfLang = q("#pdf-lang-select").value;
    });
  }
  if (module === "estimates") {
    q("#tpl-create-btn").addEventListener("click", createTemplateFromPanel);
  }

  q("#table").addEventListener("click", async (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const id = btn.dataset.id;
    const act = btn.dataset.act;
    if (!id) return;
    const apiBase = module === "change_orders" ? "/api/change-orders" : `/api/${module}`;

    if (act === "del") {
      if (!confirm(t("confirm_del"))) return;
      await api(`${apiBase}/${id}`, { method: "DELETE" });
      await loadCrud(module);
      if (module === "contracts") await renderContractMilestonePanel();
      if (module === "contracts") await renderContractChangeOrderPanel();
      return;
    }
    if (act === "edit") {
      const row = await api(`${apiBase}/${id}`);
      state.editId = id;
      openCrudForm();
      if (module === "contracts") {
        state.contractMilestoneContractId = Number(id);
        state.editingMilestoneId = null;
        await renderContractMilestonePanel();
        await renderContractChangeOrderPanel(row);
      }
      renderForm(module, row);
      if (module === "customers") {
        await renderCustomerEstimatePanel(row);
        await renderCustomerFollowupPanel(row);
        await renderEntityAttachmentPanel({
          hostSelector: "#customer-file-panel",
          entityType: "customer",
          entityId: row.id,
          title: t("attachments"),
          defaultCategory: "other",
        });
      }
      if (module === "estimates" || module === "contracts") {
        await renderRecordLinkPanel(module, row);
        await renderEntityAttachmentPanel({
          hostSelector: "#record-file-panel",
          entityType: module === "estimates" ? "estimate" : "contract",
          entityId: row.id,
          title: module === "estimates" ? t("estimate_attachments") : t("contract_attachments"),
          defaultCategory: module === "estimates" ? "estimate" : "contract",
        });
      }
      return;
    }
    if (act === "custom-contract" && module === "contracts") {
      const row = await api(`${apiBase}/${id}`);
      state.editId = id;
      openCrudForm();
      state.contractMilestoneContractId = Number(id);
      state.editingMilestoneId = null;
      const data = { ...row, custom_contract_enabled: Number(row.custom_contract_enabled || 0) ? 1 : 1 };
      renderForm(module, data);
      await renderRecordLinkPanel(module, row);
      await renderEntityAttachmentPanel({
        hostSelector: "#record-file-panel",
        entityType: "contract",
        entityId: row.id,
        title: t("contract_attachments"),
        defaultCategory: "contract",
      });
      await renderContractMilestonePanel();
      await renderContractChangeOrderPanel(row);
      setTimeout(() => q('[name="custom_contract_text"]')?.focus(), 50);
      return;
    }
    if (act === "mark-sent" && module === "change_orders") {
      await api(`/api/change-orders/${id}/mark-sent`, { method: "POST" });
      await loadCrud("change_orders");
      if (state.editId && String(state.editId) === String(id)) {
        const row = await api(`/api/change-orders/${id}`);
        renderForm("change_orders", row);
      }
      return;
    }
    if (act === "mark-approved" && module === "change_orders") {
      await api(`/api/change-orders/${id}/mark-approved`, { method: "POST" });
      await loadCrud("change_orders");
      if (state.editId && String(state.editId) === String(id)) {
        const row = await api(`/api/change-orders/${id}`);
        renderForm("change_orders", row);
      }
      return;
    }
    if (act === "mark-rejected" && module === "change_orders") {
      await api(`/api/change-orders/${id}/mark-rejected`, { method: "POST" });
      await loadCrud("change_orders");
      if (state.editId && String(state.editId) === String(id)) {
        const row = await api(`/api/change-orders/${id}`);
        renderForm("change_orders", row);
      }
      return;
    }
    if (act === "print-change-order" && module === "change_orders") {
      window.open(`/print/change-order/${id}?lang=${encodeURIComponent(state.pdfLang)}`, "_blank");
      return;
    }
    if (act === "pdf-change-order" && module === "change_orders") {
      window.open(`/api/change-orders/${id}/pdf?lang=${encodeURIComponent(state.pdfLang)}`, "_blank");
      return;
    }
    if (act === "pdf" && module === "estimates") {
      window.open(`/api/estimates/${id}/pdf?lang=${encodeURIComponent(state.pdfLang)}`, "_blank");
      return;
    }
    if (act === "contract-pdf" && module === "contracts") {
      window.open(`/api/contracts/${id}/pdf?lang=${encodeURIComponent(state.pdfLang)}`, "_blank");
      return;
    }
    if (act === "detail" && module === "projects") {
      await renderProjectDetail(id);
      return;
    }
    if (act === "gen-estimate-cust" && module === "customers") {
      const r = await api(`/api/customers/${id}/generate-estimate`, { method: "POST" });
      await loadCrud(module);
      await openEstimateDetail(r.estimate?.id);
      return;
    }
    if (act === "quick-followup-cust" && module === "customers") {
      await quickAddFollowupFromList(id);
      await loadCrud("customers");
      if (state.editId && String(state.editId) === String(id)) {
        const row = await api(`/api/customers/${id}`);
        renderForm("customers", row);
        await renderCustomerEstimatePanel(row);
        await renderCustomerFollowupPanel(row);
        await renderEntityAttachmentPanel({
          hostSelector: "#customer-file-panel",
          entityType: "customer",
          entityId: row.id,
          title: t("attachments"),
          defaultCategory: "other",
        });
      }
      return;
    }
    if (act === "gen-contract" && module === "estimates") {
      const r = await api(`/api/estimates/${id}/generate-contract`, { method: "POST" });
      await loadCrud(module);
      await openContractDetail(r.contract?.id);
      return;
    }
    if (act === "view-contract" && module === "estimates") {
      if (!btn.dataset.contractId) return;
      await openContractDetail(btn.dataset.contractId);
      return;
    }
    if (act === "gen-project" && module === "contracts") {
      const r = await api(`/api/contracts/${id}/generate-project`, { method: "POST" });
      await loadCrud(module);
      await openProjectDetail(r.project?.id);
      return;
    }
    if (act === "view-project" && module === "contracts") {
      if (!btn.dataset.projectId) return;
      await openProjectDetail(btn.dataset.projectId);
      return;
    }
    if (act === "init-progress" && module === "projects") {
      await api(`/api/projects/${id}/progress/init`, { method: "POST", body: JSON.stringify({ stages: DEFAULT_PROJECT_STAGE_NAMES }) });
      await loadCrud(module);
    }
  });
  if (module === "customers") {
    q("#table").addEventListener("change", async (e) => {
      const sel = e.target.closest("select[data-act='customer-status']");
      if (!sel) return;
      const customerId = sel.dataset.id;
      const status = sel.value;
      await api(`/api/customers/${customerId}`, { method: "PUT", body: JSON.stringify({ status }) });
      await loadCrud("customers");
      if (state.editId && String(state.editId) === String(customerId)) {
        const row = await api(`/api/customers/${customerId}`);
        renderForm("customers", row);
        await renderCustomerEstimatePanel(row);
        await renderCustomerFollowupPanel(row);
        await renderEntityAttachmentPanel({
          hostSelector: "#customer-file-panel",
          entityType: "customer",
          entityId: row.id,
          title: t("attachments"),
          defaultCategory: "other",
        });
      }
    });
  }
}


// ============================================================
//  FINANCE MODULE — complete rewrite
//  Tabs: 概览 | 收款(AR) | 应付(AP) | 供应商 | 账单 | 付款记录 | 利润分析 | 1099
// ============================================================

const FIN_TABS = [
  { key: "overview",  labelZh: "概览",     labelEn: "Overview"  },
  { key: "ar",        labelZh: "客户收款",  labelEn: "AR"        },
  { key: "ap",        labelZh: "应付账款",  labelEn: "AP"        },
  { key: "vendors",   labelZh: "供应商",    labelEn: "Vendors"   },
  { key: "bills",     labelZh: "账单",      labelEn: "Bills"     },
  { key: "payments",  labelZh: "付款记录",  labelEn: "Payments"  },
  { key: "profit",    labelZh: "利润分析",  labelEn: "Profit"    },
  { key: "tax1099",   labelZh: "1099",      labelEn: "1099"      },
];

if (!state.finTab) state.finTab = "overview";

// ── helpers ────────────────────────────────────────────────
function fmtMoney(v) {
  const n = Number(v) || 0;
  return "$" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function finTabLabel(tab) {
  const lang = (state.lang || "zh");
  return lang === "zh" ? tab.labelZh : tab.labelEn;
}
function finStatusBadge(status) {
  const s = (status || "").toLowerCase();
  const map = {
    paid: "badge-green", open: "badge-blue", overdue: "badge-red",
    partial: "badge-yellow", "已付": "badge-green", "未付": "badge-blue",
    "逾期": "badge-red", "部分付款": "badge-yellow",
    signed: "badge-green", sent: "badge-blue", draft: "badge-gray",
  };
  const cls = map[s] || map[status] || "badge-gray";
  return `<span class="fin-badge ${cls}">${esc(status || "-")}</span>`;
}
function ageDaysLabel(days) {
  const d = Number(days) || 0;
  if (d === 0) return `<span style="color:var(--sub)">0天</span>`;
  if (d <= 30) return `<span style="color:#b45309">${d}天</span>`;
  return `<span style="color:var(--warn);font-weight:600">${d}天</span>`;
}

// ── main entry ────────────────────────────────────────────
async function renderFinance() {
  const main = q("#main");
  if (!main) return;

  // render shell immediately with tabs
  main.innerHTML = `
    <div class="fin-shell">
      <div class="fin-tabs" id="fin-tabs">
        ${FIN_TABS.map(tab => `
          <button class="fin-tab${state.finTab === tab.key ? " active" : ""}" data-tab="${tab.key}">
            ${finTabLabel(tab)}
          </button>
        `).join("")}
      </div>
      <div id="fin-body" class="fin-body">
        <div class="fin-loading">加载中…</div>
      </div>
    </div>
  `;

  q("#fin-tabs").addEventListener("click", async (e) => {
    const btn = e.target.closest(".fin-tab");
    if (!btn) return;
    state.finTab = btn.dataset.tab;
    q("#fin-tabs").querySelectorAll(".fin-tab").forEach(b =>
      b.classList.toggle("active", b.dataset.tab === state.finTab)
    );
    await renderFinTab();
  });

  await renderFinTab();
}

async function renderFinTab() {
  const body = q("#fin-body");
  if (!body) return;
  body.innerHTML = `<div class="fin-loading">加载中…</div>`;
  try {
    const tab = state.finTab || "overview";
    if (tab === "overview")  await renderFinOverview(body);
    else if (tab === "ar")   await renderFinAR(body);
    else if (tab === "ap")   await renderFinAP(body);
    else if (tab === "vendors") await renderFinVendors(body);
    else if (tab === "bills")   await renderFinBills(body);
    else if (tab === "payments") await renderFinPayments(body);
    else if (tab === "profit")  await renderFinProfit(body);
    else if (tab === "tax1099") await renderFin1099(body);
  } catch (err) {
    console.error("renderFinTab error", err);
    if (body) body.innerHTML = `<div class="fin-error">加载失败，请刷新重试</div>`;
  }
}

// ── TAB: 概览 Overview ────────────────────────────────────
async function renderFinOverview(body) {
  const data = await api("/api/finance/summary");
  const c = data.cards || {};

  const kpi = [
    { label: "应收总额",    value: c.ar_total,         sub: `逾期 ${fmtMoney(c.ar_overdue)}`,   color: "kpi-blue"   },
    { label: "应付总额",    value: c.ap_total,         sub: `逾期 ${fmtMoney(c.ap_overdue)}`,   color: "kpi-orange" },
    { label: "本月已收",    value: c.monthly_received, sub: "客户款",                            color: "kpi-green"  },
    { label: "本月已付",    value: c.monthly_ap_paid,  sub: "供应商付款",                        color: "kpi-red"    },
    { label: "本月成本",    value: c.monthly_cost,     sub: "项目成本",                          color: "kpi-gray"   },
    { label: "本月现金流",  value: c.monthly_cashflow, sub: "收 - 付",                          color: (Number(c.monthly_cashflow)||0) >= 0 ? "kpi-green" : "kpi-red" },
  ];

  const arAging = data.ar_aging || [];
  const apAging = data.ap_aging || [];

  // overdue AR items (age_days > 0, open_amount > 0)
  const overdueAR = (data.ar_ledger || []).filter(r => (r.age_days||0) > 0 && (r.open_amount||0) > 0)
    .sort((a,b) => (b.age_days||0) - (a.age_days||0)).slice(0, 8);

  body.innerHTML = `
    <div class="fin-overview">
      <div class="fin-kpi-grid">
        ${kpi.map(k => `
          <div class="fin-kpi ${k.color}">
            <div class="fin-kpi-label">${k.label}</div>
            <div class="fin-kpi-value">${fmtMoney(k.value)}</div>
            <div class="fin-kpi-sub">${k.sub}</div>
          </div>
        `).join("")}
      </div>

      <div class="fin-aging-row">
        <div class="fin-panel">
          <div class="fin-panel-head">📥 应收账款账龄 (AR Aging)</div>
          <table class="fin-table">
            <thead><tr><th>账龄区间</th><th>笔数</th><th>金额</th></tr></thead>
            <tbody>
              ${arAging.map(r => `
                <tr>
                  <td>${r.bucket} 天</td>
                  <td>${r.count}</td>
                  <td>${fmtMoney(r.amount)}</td>
                </tr>
              `).join("") || `<tr><td colspan="3" style="text-align:center;color:var(--sub)">暂无数据</td></tr>`}
            </tbody>
          </table>
        </div>
        <div class="fin-panel">
          <div class="fin-panel-head">📤 应付账款账龄 (AP Aging)</div>
          <table class="fin-table">
            <thead><tr><th>账龄区间</th><th>笔数</th><th>金额</th></tr></thead>
            <tbody>
              ${apAging.map(r => `
                <tr>
                  <td>${r.bucket} 天</td>
                  <td>${r.count}</td>
                  <td>${fmtMoney(r.amount)}</td>
                </tr>
              `).join("") || `<tr><td colspan="3" style="text-align:center;color:var(--sub)">暂无数据</td></tr>`}
            </tbody>
          </table>
        </div>
      </div>

      ${overdueAR.length ? `
      <div class="fin-panel" style="margin-top:12px">
        <div class="fin-panel-head">⚠️ 逾期未收款（前8条）</div>
        <table class="fin-table">
          <thead><tr><th>项目</th><th>节点</th><th>到期日</th><th>待收</th><th>逾期天数</th></tr></thead>
          <tbody>
            ${overdueAR.map(r => `
              <tr>
                <td>${esc(r.project_name||"-")}</td>
                <td>${esc(r.node_name||"-")}</td>
                <td>${esc(r.due_date||"-")}</td>
                <td>${fmtMoney(r.open_amount)}</td>
                <td>${ageDaysLabel(r.age_days)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>` : ""}
    </div>
  `;
}

// ── TAB: 客户收款 AR ──────────────────────────────────────
async function renderFinAR(body) {
  const data = await api("/api/finance/summary");
  const rows = (data.ar_ledger || []);

  // filter state
  if (!state.arFilter) state.arFilter = "all";

  const filterBtns = [
    { key: "all",     label: "全部" },
    { key: "open",    label: "未收" },
    { key: "overdue", label: "逾期" },
    { key: "paid",    label: "已收" },
  ];

  const filterRow = (r) => {
    if (state.arFilter === "all") return true;
    if (state.arFilter === "overdue") return (r.age_days||0) > 0 && (r.open_amount||0) > 0;
    if (state.arFilter === "open") return (r.open_amount||0) > 0;
    if (state.arFilter === "paid") return (r.open_amount||0) <= 0;
    return true;
  };
  const filtered = rows.filter(filterRow);
  const totalAmt = filtered.reduce((s,r) => s + (r.amount||0), 0);
  const totalOpen = filtered.reduce((s,r) => s + (r.open_amount||0), 0);
  const totalReceived = filtered.reduce((s,r) => s + (r.received_amount||0), 0);

  body.innerHTML = `
    <div class="fin-panel">
      <div class="fin-toolbar">
        <div class="fin-filter-group">
          ${filterBtns.map(f => `
            <button class="fin-filter-btn${state.arFilter===f.key?" active":""}" data-filter="${f.key}">${f.label}</button>
          `).join("")}
        </div>
        <div class="fin-summary-chips">
          <span class="fin-chip">合计 ${fmtMoney(totalAmt)}</span>
          <span class="fin-chip green">已收 ${fmtMoney(totalReceived)}</span>
          <span class="fin-chip red">待收 ${fmtMoney(totalOpen)}</span>
        </div>
      </div>
      <div class="fin-table-wrap">
        <table class="fin-table">
          <thead>
            <tr>
              <th>项目</th><th>收款节点</th><th>到期日</th>
              <th class="num">金额</th><th class="num">已收</th>
              <th class="num">待收</th><th>逾期天数</th><th>状态</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.length ? filtered.map(r => `
              <tr class="${(r.age_days||0)>30?"row-warn":(r.age_days||0)>0?"row-caution":""}">
                <td>${esc(r.project_name||"-")}</td>
                <td>${esc(r.node_name||"-")}</td>
                <td>${esc(r.due_date||"-")}</td>
                <td class="num">${fmtMoney(r.amount)}</td>
                <td class="num">${fmtMoney(r.received_amount)}</td>
                <td class="num bold">${fmtMoney(r.open_amount)}</td>
                <td>${ageDaysLabel(r.age_days)}</td>
                <td>${finStatusBadge(r.status)}</td>
              </tr>
            `).join("") : `<tr><td colspan="8" class="fin-empty">暂无数据</td></tr>`}
          </tbody>
        </table>
      </div>
    </div>
  `;

  body.querySelector(".fin-filter-group").addEventListener("click", async (e) => {
    const btn = e.target.closest(".fin-filter-btn");
    if (!btn) return;
    state.arFilter = btn.dataset.filter;
    await renderFinAR(body);
  });
}

// ── TAB: 应付账款 AP ──────────────────────────────────────
async function renderFinAP(body) {
  const data = await api("/api/finance/summary");
  const rows = (data.ap_ledger || []);
  if (!state.apFilter) state.apFilter = "all";

  const filterBtns = [
    { key: "all",     label: "全部" },
    { key: "open",    label: "未付" },
    { key: "overdue", label: "逾期" },
    { key: "paid",    label: "已付" },
  ];
  const filterRow = (r) => {
    if (state.apFilter === "all") return true;
    if (state.apFilter === "overdue") return (r.age_days||0) > 0 && (r.open_amount||0) > 0;
    if (state.apFilter === "open") return (r.open_amount||0) > 0;
    if (state.apFilter === "paid") return (r.open_amount||0) <= 0;
    return true;
  };
  const filtered = rows.filter(filterRow);
  const totalAmt = filtered.reduce((s,r) => s + (r.amount||0), 0);
  const totalOpen = filtered.reduce((s,r) => s + (r.open_amount||0), 0);
  const totalPaid = filtered.reduce((s,r) => s + (r.paid_amount||0), 0);

  body.innerHTML = `
    <div class="fin-panel">
      <div class="fin-toolbar">
        <div class="fin-filter-group">
          ${filterBtns.map(f => `
            <button class="fin-filter-btn${state.apFilter===f.key?" active":""}" data-filter="${f.key}">${f.label}</button>
          `).join("")}
        </div>
        <div class="fin-summary-chips">
          <span class="fin-chip">合计 ${fmtMoney(totalAmt)}</span>
          <span class="fin-chip green">已付 ${fmtMoney(totalPaid)}</span>
          <span class="fin-chip red">未付 ${fmtMoney(totalOpen)}</span>
        </div>
      </div>
      <div class="fin-table-wrap">
        <table class="fin-table">
          <thead>
            <tr>
              <th>项目</th><th>供应商</th><th>类别</th><th>到期日</th>
              <th class="num">金额</th><th class="num">已付</th>
              <th class="num">未付</th><th>逾期天数</th><th>状态</th>
            </tr>
          </thead>
          <tbody>
            ${filtered.length ? filtered.map(r => `
              <tr class="${(r.age_days||0)>30?"row-warn":(r.age_days||0)>0?"row-caution":""}">
                <td>${esc(r.project_name||"-")}</td>
                <td>${esc(r.vendor||"-")}</td>
                <td>${esc(r.category||"-")}</td>
                <td>${esc(r.due_date||"-")}</td>
                <td class="num">${fmtMoney(r.amount)}</td>
                <td class="num">${fmtMoney(r.paid_amount)}</td>
                <td class="num bold">${fmtMoney(r.open_amount)}</td>
                <td>${ageDaysLabel(r.age_days)}</td>
                <td>${finStatusBadge(r.status)}</td>
              </tr>
            `).join("") : `<tr><td colspan="9" class="fin-empty">暂无数据</td></tr>`}
          </tbody>
        </table>
      </div>
    </div>
  `;

  body.querySelector(".fin-filter-group").addEventListener("click", async (e) => {
    const btn = e.target.closest(".fin-filter-btn");
    if (!btn) return;
    state.apFilter = btn.dataset.filter;
    await renderFinAP(body);
  });
}

// ── TAB: 供应商 Vendors ───────────────────────────────────
async function renderFinVendors(body) {
  const vendors = await api("/api/vendors");
  if (!state.finVendorEditId) state.finVendorEditId = null;
  const editing = (vendors||[]).find(v => v.id === state.finVendorEditId) || null;

  const VENDOR_TYPES = [
    { value: "supplier",    label: "供应商" },
    { value: "subcontractor", label: "分包商" },
    { value: "1099",        label: "1099独立承包商" },
    { value: "employee",    label: "员工" },
    { value: "other",       label: "其他" },
  ];

  body.innerHTML = `
    <div class="fin-split">
      <div class="fin-form-card">
        <div class="fin-form-title">${editing ? "✏️ 编辑供应商" : "➕ 新建供应商"}</div>
        <form id="fin-vendor-form" class="fin-form">
          <div class="fin-field">
            <label>供应商名称 *</label>
            <input id="fv-name" value="${esc(editing?.name||"")}" placeholder="公司/个人名称" required />
          </div>
          <div class="fin-field">
            <label>类型</label>
            <select id="fv-type">
              ${VENDOR_TYPES.map(vt => `<option value="${vt.value}"${(editing?.type||"supplier")===vt.value?" selected":""}>${vt.label}</option>`).join("")}
            </select>
          </div>
          <div class="fin-field">
            <label>税号 (Tax ID / EIN)</label>
            <input id="fv-tax" value="${esc(editing?.tax_id||"")}" placeholder="XX-XXXXXXX" />
          </div>
          <div class="fin-field">
            <label>联系电话</label>
            <input id="fv-phone" value="${esc(editing?.phone||"")}" placeholder="可选" />
          </div>
          <div class="fin-field">
            <label>邮箱</label>
            <input id="fv-email" value="${esc(editing?.email||"")}" placeholder="可选" />
          </div>
          <div class="fin-field fin-field-full">
            <label>备注</label>
            <input id="fv-notes" value="${esc(editing?.notes||"")}" />
          </div>
          <div class="fin-field fin-field-full fin-checks">
            <label class="fin-check-label">
              <input type="checkbox" id="fv-1099" ${Number(editing?.["1099_required"]||0)?"checked":""} />
              需要发送 1099
            </label>
            <label class="fin-check-label">
              <input type="checkbox" id="fv-w9" ${Number(editing?.w9_received||0)?"checked":""} />
              W-9 已收取
            </label>
          </div>
          <div class="fin-form-actions fin-field-full">
            <button type="submit" class="fin-btn-primary">${editing ? "保存更改" : "创建供应商"}</button>
            ${editing ? `<button type="button" id="fv-cancel" class="fin-btn-secondary">取消</button>` : ""}
          </div>
        </form>
      </div>

      <div class="fin-table-card">
        <div class="fin-panel-head">供应商列表（${(vendors||[]).length} 个）</div>
        <div class="fin-table-wrap">
          <table class="fin-table">
            <thead>
              <tr><th>ID</th><th>名称</th><th>类型</th><th>Tax ID</th><th>1099</th><th>W-9</th><th>操作</th></tr>
            </thead>
            <tbody>
              ${(vendors||[]).length ? (vendors||[]).map(v => `
                <tr class="${v.id===state.finVendorEditId?"row-editing":""}">
                  <td style="color:var(--sub);font-size:12px">#${v.id}</td>
                  <td><strong>${esc(v.name||"-")}</strong></td>
                  <td>${esc(v.type||"-")}</td>
                  <td style="font-family:monospace">${esc(v.tax_id||"-")}</td>
                  <td>${Number(v["1099_required"]) ? "✅" : "—"}</td>
                  <td>${Number(v.w9_received) ? "✅" : "—"}</td>
                  <td>
                    <button class="fin-btn-xs" data-act="edit-vendor" data-id="${v.id}">编辑</button>
                    <button class="fin-btn-xs danger" data-act="del-vendor" data-id="${v.id}">删除</button>
                  </td>
                </tr>
              `).join("") : `<tr><td colspan="7" class="fin-empty">暂无供应商，请先创建</td></tr>`}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  body.querySelector("#fin-vendor-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      name: q("#fv-name").value.trim(),
      type: q("#fv-type").value,
      tax_id: q("#fv-tax").value.trim(),
      "1099_required": q("#fv-1099").checked ? 1 : 0,
      w9_received: q("#fv-w9").checked ? 1 : 0,
    };
    if (!payload.name) { alert("请填写供应商名称"); return; }
    if (state.finVendorEditId) {
      await api(`/api/vendors/${state.finVendorEditId}`, { method: "PUT", body: JSON.stringify(payload) });
    } else {
      await api("/api/vendors", { method: "POST", body: JSON.stringify(payload) });
    }
    state.finVendorEditId = null;
    await renderFinVendors(body);
  });

  body.querySelector("#fv-cancel")?.addEventListener("click", async () => {
    state.finVendorEditId = null;
    await renderFinVendors(body);
  });

  body.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-act]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    if (btn.dataset.act === "edit-vendor") {
      state.finVendorEditId = id;
      await renderFinVendors(body);
    }
    if (btn.dataset.act === "del-vendor") {
      if (!confirm("确认删除此供应商？")) return;
      await api(`/api/vendors/${id}`, { method: "DELETE" });
      if (state.finVendorEditId === id) state.finVendorEditId = null;
      await renderFinVendors(body);
    }
  });
}

// ── TAB: 账单 Bills ───────────────────────────────────────
async function renderFinBills(body) {
  const [bills, vendors, projects] = await Promise.all([
    api("/api/bills"),
    api("/api/vendors"),
    api("/api/projects"),
  ]);
  if (!state.finBillEditId) state.finBillEditId = null;
  if (!state.finBillFilter) state.finBillFilter = "all";

  const editing = (bills||[]).find(b => b.id === state.finBillEditId) || null;
  const today = new Date().toISOString().slice(0,10);

  const vendorOpts = (vendors||[]).map(v =>
    `<option value="${v.id}"${(editing?.vendor_id||"")===v.id||String(editing?.vendor_id)===String(v.id)?" selected":""}>#${v.id} ${esc(v.name)}</option>`
  ).join("");
  const projOpts = `<option value="">— 无关联项目 —</option>` + (projects||[]).map(p =>
    `<option value="${p.id}"${String(editing?.project_id||"")===String(p.id)?" selected":""}>#${p.id} ${esc(p.name||"")}</option>`
  ).join("");

  const BILL_STATUSES = ["Open","Partial","Paid","Void"];
  const filterBtns = [
    { key: "all", label: "全部" },
    { key: "Open", label: "未付" },
    { key: "Partial", label: "部分付款" },
    { key: "Paid", label: "已付" },
  ];
  const filtered = (state.finBillFilter==="all") ? (bills||[]) : (bills||[]).filter(b=>(b.status||"")=== state.finBillFilter);
  const totalAmt = filtered.reduce((s,b) => s+(b.amount||0), 0);
  const totalOpen = filtered.reduce((s,b) => s+(b.open_amount||b.amount-b.paid_amount||0), 0);

  body.innerHTML = `
    <div class="fin-split">
      <div class="fin-form-card">
        <div class="fin-form-title">${editing ? "✏️ 编辑账单" : "➕ 新建账单"}</div>
        <form id="fin-bill-form" class="fin-form">
          <div class="fin-field">
            <label>供应商 *</label>
            <select id="fb-vendor"${!vendorOpts?"disabled":""}>
              <option value="">— 选择供应商 —</option>
              ${vendorOpts}
            </select>
          </div>
          <div class="fin-field">
            <label>关联项目</label>
            <select id="fb-project">${projOpts}</select>
          </div>
          <div class="fin-field">
            <label>账单号</label>
            <input id="fb-billno" value="${esc(editing?.bill_no||"")}" placeholder="供应商账单编号" />
          </div>
          <div class="fin-field">
            <label>类别</label>
            <input id="fb-cat" value="${esc(editing?.category||"")}" placeholder="材料/人工/设备…" list="fin-cat-list" />
            <datalist id="fin-cat-list">
              <option value="材料">
              <option value="人工">
              <option value="设备租赁">
              <option value="分包">
              <option value="运输">
              <option value="其他">
            </datalist>
          </div>
          <div class="fin-field">
            <label>账单日期</label>
            <input id="fb-date" type="date" value="${esc(editing?.bill_date||today)}" />
          </div>
          <div class="fin-field">
            <label>到期日</label>
            <input id="fb-due" type="date" value="${esc(editing?.due_date||"")}" />
          </div>
          <div class="fin-field">
            <label>金额 *</label>
            <input id="fb-amount" type="number" step="0.01" min="0" value="${esc(editing?.amount??"")}"/>
          </div>
          <div class="fin-field">
            <label>状态</label>
            <select id="fb-status">
              ${BILL_STATUSES.map(s=>`<option value="${s}"${(editing?.status||"Open")===s?" selected":""}>${s}</option>`).join("")}
            </select>
          </div>
          <div class="fin-field fin-field-full">
            <label>备注</label>
            <input id="fb-note" value="${esc(editing?.note||"")}" />
          </div>
          <div class="fin-form-actions fin-field-full">
            <button type="submit" class="fin-btn-primary">${editing?"保存更改":"创建账单"}</button>
            ${editing?`<button type="button" id="fb-cancel" class="fin-btn-secondary">取消</button>`:""}
          </div>
        </form>
        ${!vendorOpts ? `<div class="fin-hint">⚠️ 请先在「供应商」标签页创建供应商</div>` : ""}
      </div>

      <div class="fin-table-card">
        <div class="fin-toolbar">
          <div class="fin-filter-group">
            ${filterBtns.map(f=>`<button class="fin-filter-btn${state.finBillFilter===f.key?" active":""}" data-filter="${f.key}">${f.label}</button>`).join("")}
          </div>
          <div class="fin-summary-chips">
            <span class="fin-chip">合计 ${fmtMoney(totalAmt)}</span>
            <span class="fin-chip red">未付 ${fmtMoney(totalOpen)}</span>
          </div>
        </div>
        <div class="fin-table-wrap">
          <table class="fin-table">
            <thead>
              <tr><th>账单号</th><th>供应商</th><th>项目</th><th>类别</th><th>账单日</th><th>到期日</th><th class="num">金额</th><th class="num">已付</th><th class="num">未付</th><th>状态</th><th>操作</th></tr>
            </thead>
            <tbody>
              ${filtered.length ? filtered.map(b => {
                const open = Math.max(0,(b.amount||0)-(b.paid_amount||0));
                return `
                <tr class="${b.id===state.finBillEditId?"row-editing":""}">
                  <td style="font-family:monospace">${esc(b.bill_no||"-")}</td>
                  <td>${esc(b.vendor_name||b.vendor||"-")}</td>
                  <td>${esc(b.project_name||"-")}</td>
                  <td>${esc(b.category||"-")}</td>
                  <td>${esc(b.bill_date||"-")}</td>
                  <td>${esc(b.due_date||"-")}</td>
                  <td class="num">${fmtMoney(b.amount)}</td>
                  <td class="num">${fmtMoney(b.paid_amount)}</td>
                  <td class="num bold">${fmtMoney(open)}</td>
                  <td>${finStatusBadge(b.status)}</td>
                  <td>
                    <button class="fin-btn-xs" data-act="edit-bill" data-id="${b.id}">编辑</button>
                    <button class="fin-btn-xs" data-act="pay-bill" data-id="${b.id}" data-vendor="${b.vendor_id||""}" data-proj="${b.project_id||""}">付款</button>
                  </td>
                </tr>`;
              }).join("") : `<tr><td colspan="11" class="fin-empty">暂无账单</td></tr>`}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  body.querySelector("#fin-bill-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const vendorId = Number(q("#fb-vendor").value);
    const amount = Number(q("#fb-amount").value);
    if (!vendorId) { alert("请选择供应商"); return; }
    if (!(amount > 0)) { alert("金额必须大于0"); return; }
    const payload = {
      vendor_id: vendorId,
      project_id: q("#fb-project").value ? Number(q("#fb-project").value) : null,
      bill_no: q("#fb-billno").value.trim(),
      category: q("#fb-cat").value.trim(),
      bill_date: q("#fb-date").value,
      due_date: q("#fb-due").value,
      amount,
      status: q("#fb-status").value,
      note: q("#fb-note").value.trim(),
    };
    if (state.finBillEditId) {
      await api(`/api/bills/${state.finBillEditId}`, { method: "PUT", body: JSON.stringify(payload) });
    } else {
      await api("/api/bills", { method: "POST", body: JSON.stringify(payload) });
    }
    state.finBillEditId = null;
    await renderFinBills(body);
  });

  body.querySelector("#fb-cancel")?.addEventListener("click", async () => {
    state.finBillEditId = null;
    await renderFinBills(body);
  });

  body.querySelector(".fin-filter-group")?.addEventListener("click", async (e) => {
    const btn = e.target.closest(".fin-filter-btn");
    if (!btn) return;
    state.finBillFilter = btn.dataset.filter;
    await renderFinBills(body);
  });

  body.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-act]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    if (btn.dataset.act === "edit-bill") {
      state.finBillEditId = id;
      await renderFinBills(body);
    }
    if (btn.dataset.act === "pay-bill") {
      // switch to payments tab with prefill
      state.finTab = "payments";
      state.finPaymentPrefillBillId = id;
      state.finPaymentPrefillVendorId = Number(btn.dataset.vendor||0)||null;
      state.finPaymentPrefillProjId = Number(btn.dataset.proj||0)||null;
      q("#fin-tabs").querySelectorAll(".fin-tab").forEach(b =>
        b.classList.toggle("active", b.dataset.tab === "payments")
      );
      await renderFinTab();
    }
  });
}

// ── TAB: 付款记录 Payments ────────────────────────────────
async function renderFinPayments(body) {
  const [payments, vendors, bills, projects] = await Promise.all([
    api("/api/payments"),
    api("/api/vendors"),
    api("/api/bills"),
    api("/api/projects"),
  ]);
  if (!state.finPaymentEditId) state.finPaymentEditId = null;

  // prefill from "付款" button in bills tab
  const prefillBillId   = state.finPaymentPrefillBillId   || null;
  const prefillVendorId = state.finPaymentPrefillVendorId || null;
  const prefillProjId   = state.finPaymentPrefillProjId   || null;
  state.finPaymentPrefillBillId = null;
  state.finPaymentPrefillVendorId = null;
  state.finPaymentPrefillProjId = null;

  const editing = (payments||[]).find(p => p.id === state.finPaymentEditId) || null;
  const today = new Date().toISOString().slice(0,10);

  const currentVendorId = editing?.vendor_id || prefillVendorId || "";
  const currentBillId   = editing?.bill_id   || prefillBillId   || "";
  const currentProjId   = editing?.project_id|| prefillProjId   || "";

  const vendorOpts = `<option value="">— 选择供应商 —</option>` + (vendors||[]).map(v =>
    `<option value="${v.id}"${String(currentVendorId)===String(v.id)?" selected":""}>${esc(v.name)}</option>`
  ).join("");

  const billsByVendor = currentVendorId
    ? (bills||[]).filter(b => String(b.vendor_id)===String(currentVendorId))
    : (bills||[]);
  const billOpts = `<option value="">— 关联账单（可选）—</option>` + billsByVendor.map(b =>
    `<option value="${b.id}"${String(currentBillId)===String(b.id)?" selected":""}>#${b.id} ${esc(b.bill_no||"")} ${fmtMoney(b.amount)}</option>`
  ).join("");

  const projOpts = `<option value="">— 无关联项目 —</option>` + (projects||[]).map(p =>
    `<option value="${p.id}"${String(currentProjId)===String(p.id)?" selected":""}>#${p.id} ${esc(p.name||"")}</option>`
  ).join("");

  const METHODS = [
    { value: "check",  label: "支票 Check" },
    { value: "ach",    label: "ACH/银行转账" },
    { value: "wire",   label: "Wire Transfer" },
    { value: "credit", label: "信用卡" },
    { value: "cash",   label: "现金" },
    { value: "zelle",  label: "Zelle" },
    { value: "other",  label: "其他" },
  ];

  const totalPaid = (payments||[]).reduce((s,p)=>s+(p.amount||0),0);

  body.innerHTML = `
    <div class="fin-split">
      <div class="fin-form-card">
        <div class="fin-form-title">${editing?"✏️ 编辑付款记录":"➕ 录入付款"}</div>
        <form id="fin-pay-form" class="fin-form">
          <div class="fin-field">
            <label>供应商 *</label>
            <select id="fp-vendor">${vendorOpts}</select>
          </div>
          <div class="fin-field">
            <label>关联账单</label>
            <select id="fp-bill">${billOpts}</select>
          </div>
          <div class="fin-field">
            <label>关联项目</label>
            <select id="fp-proj">${projOpts}</select>
          </div>
          <div class="fin-field">
            <label>付款金额 *</label>
            <input id="fp-amount" type="number" step="0.01" min="0" value="${esc(editing?.amount??"")}"/>
          </div>
          <div class="fin-field">
            <label>付款日期 *</label>
            <input id="fp-date" type="date" value="${esc(editing?.date||today)}" />
          </div>
          <div class="fin-field">
            <label>付款方式</label>
            <select id="fp-method">
              ${METHODS.map(m=>`<option value="${m.value}"${(editing?.method||"check")===m.value?" selected":""}>${m.label}</option>`).join("")}
            </select>
          </div>
          <div class="fin-field">
            <label>类别</label>
            <input id="fp-cat" value="${esc(editing?.category||"")}" placeholder="材料/人工…" list="fin-cat-list" />
          </div>
          <div class="fin-field">
            <label>参考号/支票号</label>
            <input id="fp-ref" value="${esc(editing?.reference_no||"")}" placeholder="可选" />
          </div>
          <div class="fin-field fin-field-full">
            <label>备注</label>
            <input id="fp-note" value="${esc(editing?.note||"")}" />
          </div>
          <div class="fin-form-actions fin-field-full">
            <button type="submit" class="fin-btn-primary">${editing?"保存更改":"录入付款"}</button>
            ${editing?`<button type="button" id="fp-cancel" class="fin-btn-secondary">取消</button>`:""}
          </div>
        </form>
      </div>

      <div class="fin-table-card">
        <div class="fin-panel-head">
          付款记录（共 ${(payments||[]).length} 条）
          <span class="fin-chip" style="float:right">总计 ${fmtMoney(totalPaid)}</span>
        </div>
        <div class="fin-table-wrap">
          <table class="fin-table">
            <thead>
              <tr><th>日期</th><th>供应商</th><th>关联账单</th><th>项目</th><th>方式</th><th>类别</th><th class="num">金额</th><th>操作</th></tr>
            </thead>
            <tbody>
              ${(payments||[]).length ? (payments||[]).map(p => `
                <tr class="${p.id===state.finPaymentEditId?"row-editing":""}">
                  <td>${esc(p.date||"-")}</td>
                  <td>${esc(p.vendor_name||"-")}</td>
                  <td>${p.bill_id?`#${p.bill_id} ${esc(p.bill_no||"")}`:"-"}</td>
                  <td>${esc(p.project_name||"-")}</td>
                  <td>${esc(p.method||"-")}</td>
                  <td>${esc(p.category||"-")}</td>
                  <td class="num bold">${fmtMoney(p.amount)}</td>
                  <td>
                    <button class="fin-btn-xs" data-act="edit-pay" data-id="${p.id}">编辑</button>
                    <button class="fin-btn-xs danger" data-act="del-pay" data-id="${p.id}">删除</button>
                  </td>
                </tr>
              `).join("") : `<tr><td colspan="8" class="fin-empty">暂无付款记录</td></tr>`}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `;

  // vendor change → reload bill options
  const fpVendor = body.querySelector("#fp-vendor");
  const fpBill   = body.querySelector("#fp-bill");
  if (fpVendor && fpBill) {
    fpVendor.addEventListener("change", () => {
      const vid = fpVendor.value;
      const filtered = vid ? (bills||[]).filter(b=>String(b.vendor_id)===String(vid)) : (bills||[]);
      fpBill.innerHTML = `<option value="">— 关联账单（可选）—</option>` +
        filtered.map(b=>`<option value="${b.id}">#${b.id} ${esc(b.bill_no||"")} ${fmtMoney(b.amount)}</option>`).join("");
    });
    // bill selection auto-fills vendor + project
    fpBill.addEventListener("change", () => {
      const bid = Number(fpBill.value);
      if (!bid) return;
      const bill = (bills||[]).find(b=>b.id===bid);
      if (!bill) return;
      if (fpVendor) fpVendor.value = String(bill.vendor_id||"");
      const fpProj = body.querySelector("#fp-proj");
      if (fpProj && bill.project_id) fpProj.value = String(bill.project_id);
    });
  }

  body.querySelector("#fin-pay-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const vendorId = Number(body.querySelector("#fp-vendor").value);
    const amount = Number(body.querySelector("#fp-amount").value);
    if (!vendorId) { alert("请选择供应商"); return; }
    if (!(amount > 0)) { alert("金额必须大于0"); return; }
    const payload = {
      vendor_id: vendorId,
      bill_id: body.querySelector("#fp-bill").value ? Number(body.querySelector("#fp-bill").value) : null,
      project_id: body.querySelector("#fp-proj").value ? Number(body.querySelector("#fp-proj").value) : null,
      amount,
      date: body.querySelector("#fp-date").value || today,
      method: body.querySelector("#fp-method").value || "other",
      category: body.querySelector("#fp-cat").value.trim(),
      note: body.querySelector("#fp-note").value.trim(),
    };
    if (state.finPaymentEditId) {
      await api(`/api/payments/${state.finPaymentEditId}`, { method: "PUT", body: JSON.stringify(payload) });
    } else {
      await api("/api/payments", { method: "POST", body: JSON.stringify(payload) });
    }
    state.finPaymentEditId = null;
    await renderFinPayments(body);
  });

  body.querySelector("#fp-cancel")?.addEventListener("click", async () => {
    state.finPaymentEditId = null;
    await renderFinPayments(body);
  });

  body.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-act]");
    if (!btn) return;
    const id = Number(btn.dataset.id);
    if (btn.dataset.act === "edit-pay") {
      state.finPaymentEditId = id;
      await renderFinPayments(body);
    }
    if (btn.dataset.act === "del-pay") {
      if (!confirm("确认删除此付款记录？")) return;
      await api(`/api/payments/${id}`, { method: "DELETE" });
      if (state.finPaymentEditId === id) state.finPaymentEditId = null;
      await renderFinPayments(body);
    }
  });
}

// ── TAB: 利润分析 Profit ──────────────────────────────────
async function renderFinProfit(body) {
  const data = await api("/api/finance/summary");
  const rows = data.project_profit_detail || [];

  const totalRevenue = rows.reduce((s,r)=>s+(r.total_revenue||0),0);
  const totalCost    = rows.reduce((s,r)=>s+(r.total_cost||0),0);
  const totalProfit  = rows.reduce((s,r)=>s+(r.gross_profit||0),0);
  const avgMargin    = totalRevenue > 0 ? ((totalProfit/totalRevenue)*100).toFixed(1) : "0.0";

  body.innerHTML = `
    <div class="fin-panel">
      <div class="fin-kpi-grid" style="margin-bottom:16px">
        <div class="fin-kpi kpi-blue">
          <div class="fin-kpi-label">总合同收入</div>
          <div class="fin-kpi-value">${fmtMoney(totalRevenue)}</div>
        </div>
        <div class="fin-kpi kpi-orange">
          <div class="fin-kpi-label">总成本</div>
          <div class="fin-kpi-value">${fmtMoney(totalCost)}</div>
        </div>
        <div class="fin-kpi ${totalProfit>=0?"kpi-green":"kpi-red"}">
          <div class="fin-kpi-label">总毛利</div>
          <div class="fin-kpi-value">${fmtMoney(totalProfit)}</div>
          <div class="fin-kpi-sub">毛利率 ${avgMargin}%</div>
        </div>
      </div>
      <div class="fin-table-wrap">
        <table class="fin-table">
          <thead>
            <tr>
              <th>项目</th>
              <th class="num">合同金额</th><th class="num">变更单</th><th class="num">总收入</th>
              <th class="num">已录成本</th><th class="num">未付AP</th><th class="num">总成本</th>
              <th class="num">毛利</th><th class="num">毛利率</th>
            </tr>
          </thead>
          <tbody>
            ${rows.length ? rows.map(r => {
              const margin = Number(r.gross_margin_pct)||0;
              const markerCls = margin >= 25 ? "green" : margin >= 10 ? "yellow" : "red";
              return `
              <tr>
                <td><strong>${esc(r.name||"-")}</strong></td>
                <td class="num">${fmtMoney(r.contract_revenue)}</td>
                <td class="num">${fmtMoney(r.change_revenue)}</td>
                <td class="num bold">${fmtMoney(r.total_revenue)}</td>
                <td class="num">${fmtMoney(r.recorded_cost)}</td>
                <td class="num">${fmtMoney(r.ap_open)}</td>
                <td class="num">${fmtMoney(r.total_cost)}</td>
                <td class="num bold ${Number(r.gross_profit)>=0?"":"text-red"}">${fmtMoney(r.gross_profit)}</td>
                <td class="num"><span class="fin-badge badge-${markerCls}">${margin.toFixed(1)}%</span></td>
              </tr>`;
            }).join("") : `<tr><td colspan="9" class="fin-empty">暂无项目数据</td></tr>`}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

// ── TAB: 1099 ─────────────────────────────────────────────
async function renderFin1099(body) {
  const data = await api("/api/finance/summary");
  const rows = data.report_1099 || [];
  const required = rows.filter(r => r.required_1099);
  const over600  = rows.filter(r => r.over_600);

  body.innerHTML = `
    <div class="fin-panel">
      <div class="fin-panel-head">
        1099 报表（当年）
        <span style="margin-left:12px;font-size:13px;color:var(--sub)">
          需发送 1099：${required.length} 个 &nbsp;|&nbsp; 年付款 ≥ $600：${over600.length} 个
        </span>
      </div>
      <div class="fin-table-wrap">
        <table class="fin-table">
          <thead>
            <tr>
              <th>供应商</th><th>类型</th><th>Tax ID</th>
              <th class="num">年付款总额</th><th>≥ $600</th>
              <th>需要 1099</th><th>W-9 已收</th>
            </tr>
          </thead>
          <tbody>
            ${rows.length ? rows.map(r => `
              <tr class="${Number(r.required_1099)&&!Number(r.w9_received)?"row-warn":""}">
                <td><strong>${esc(r.vendor||"-")}</strong></td>
                <td>${esc(r.vendor_type||"-")}</td>
                <td style="font-family:monospace">${esc(r.tax_id||"-")}</td>
                <td class="num bold">${fmtMoney(r.total_paid_this_year)}</td>
                <td>${Number(r.over_600)?"✅ 是":"—"}</td>
                <td>${Number(r.required_1099)?`<span class="fin-badge badge-red">需要</span>`:`<span class="fin-badge badge-gray">不需要</span>`}</td>
                <td>${Number(r.w9_received)?`<span class="fin-badge badge-green">已收</span>`:`<span class="fin-badge badge-yellow">未收</span>`}</td>
              </tr>
            `).join("") : `<tr><td colspan="7" class="fin-empty">暂无数据</td></tr>`}
          </tbody>
        </table>
      </div>
      ${required.filter(r=>!r.w9_received).length ? `
        <div class="fin-hint warn">⚠️ 有 ${required.filter(r=>!r.w9_received).length} 个供应商需要 1099 但 W-9 未收取，请尽快跟进</div>
      ` : ""}
    </div>
  `;
}

// ── legacy aliases (called from other parts of the codebase) ──
function financeSelectOptions(rows, selected, labelGetter, includeEmpty = true, emptyLabel = "-") {
  const options = [];
  if (includeEmpty) options.push(`<option value="">${esc(emptyLabel)}</option>`);
  (rows || []).forEach((row) => {
    const value = String(row.id);
    const selectedAttr = String(selected ?? "") === value ? "selected" : "";
    const label = labelGetter ? labelGetter(row) : `${row.id}`;
    options.push(`<option value="${esc(value)}" ${selectedAttr}>${esc(label)}</option>`);
  });
  return options.join("");
}

async function renderFinanceOpsPanels() {
  // legacy stub — new UI handles everything in renderFinance()
}

async function renderSettings() {
  if (state.user.role !== "owner") {
    q("#main").innerHTML = `<section class="panel"><h3>${t("settings")}</h3><p>${t("owner_only")}</p></section>`;
    return;
  }

  q("#main").innerHTML = `
    <section class="settings-grid">
      <article class="panel">
        <h3 id="admin-create-title">${t("create_user")}</h3>
        <div class="row gap">
          <input id="new-username" placeholder="${t("username")}" />
          <input id="new-password" placeholder="${t("password")}" />
          <select id="new-role">
            <option value="manager">${t("value_manager")}</option>
            <option value="designer">${t("value_designer")}</option>
            <option value="owner">${t("value_owner")}</option>
          </select>
          <select id="new-language">
            <option value="zh">${t("lang_zh")}</option>
            <option value="en">${t("lang_en")}</option>
            <option value="es">${t("lang_es")}</option>
          </select>
          <button id="create-user-btn">${t("create_user_btn")}</button>
        </div>
      </article>
      <article class="panel">
        <h3 id="brand-settings-title">${t("brand_settings")}</h3>
        <div class="row gap">
          <input id="brand-company-name" placeholder="company name" />
          <input id="brand-tagline-input" placeholder="tagline" />
          <input id="brand-logo-horizontal" placeholder="/assets/images/logo-oaklian-dark.png" />
        </div>
        <div class="row gap" style="margin-top:8px;">
          <input id="brand-logo-icon" placeholder="/assets/images/logo-oaklian-light.png" />
          <input id="brand-primary-color" placeholder="#0B6B55" />
          <input id="brand-accent-color" placeholder="#C89B3C" />
          <input id="brand-webhook-key" placeholder="website webhook key" />
          <button id="save-brand-btn">${t("save_brand")}</button>
        </div>
      </article>
      <article class="panel">
        <h3>${t("user_admin")}</h3>
        <div class="table-wrap"><table id="admin-table"></table></div>
      </article>
    </section>
  `;

  q("#brand-company-name").value = (state.brand && state.brand.company_name) || "";
  q("#brand-tagline-input").value = (state.brand && state.brand.tagline) || "";
  q("#brand-logo-horizontal").value = (state.brand && state.brand.logo_horizontal_url) || "";
  q("#brand-logo-icon").value = (state.brand && state.brand.logo_icon_url) || "";
  q("#brand-primary-color").value = (state.brand && state.brand.primary_color) || "";
  q("#brand-accent-color").value = (state.brand && state.brand.accent_color) || "";
  if (q("#brand-webhook-key")) q("#brand-webhook-key").value = (state.brand && state.brand.website_webhook_key) || "";

  q("#create-user-btn").addEventListener("click", createUser);
  q("#save-brand-btn").addEventListener("click", saveBrand);
  await renderUserTable();
}

async function renderUserTable() {
  const users = await api("/api/admin/users");
  if (!q("#admin-table")) return;
  q("#admin-table").innerHTML = `
    <thead><tr><th>ID</th><th>${t("username")}</th><th>${t("role")}</th><th>${t("language")}</th><th>${t("modules")}</th><th>${t("pwd_optional")}</th><th>${t("update")}</th></tr></thead>
    <tbody>
      ${users.map((u) => `<tr>
        <td>${u.id}</td>
        <td>${esc(u.username)}</td>
        <td><select data-key="role" data-id="${u.id}"><option value="manager" ${u.role === "manager" ? "selected" : ""}>${t("value_manager")}</option><option value="designer" ${u.role === "designer" ? "selected" : ""}>${t("value_designer")}</option><option value="owner" ${u.role === "owner" ? "selected" : ""}>${t("value_owner")}</option></select></td>
        <td><select data-key="language" data-id="${u.id}"><option value="zh" ${u.language === "zh" ? "selected" : ""}>${t("lang_zh")}</option><option value="en" ${u.language === "en" ? "selected" : ""}>${t("lang_en")}</option><option value="es" ${u.language === "es" ? "selected" : ""}>${t("lang_es")}</option></select></td>
        <td>${ALL_MODULES.map((m) => `<label style="display:inline-block;margin-right:6px;"><input type="checkbox" data-key="mod" data-mod="${m}" data-id="${u.id}" ${u.modules.includes(m) ? "checked" : ""}/> ${t(m)}</label>`).join("")}</td>
        <td><input data-key="password" data-id="${u.id}" type="password" /></td>
        <td><button data-key="save-user" data-id="${u.id}">${t("update")}</button></td>
      </tr>`).join("")}
    </tbody>
  `;

  q("#admin-table").querySelectorAll("button[data-key='save-user']").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      const role = q(`select[data-key='role'][data-id='${id}']`).value;
      const language = q(`select[data-key='language'][data-id='${id}']`).value;
      const password = q(`input[data-key='password'][data-id='${id}']`).value.trim();
      const modules = Array.from(document.querySelectorAll(`input[data-key='mod'][data-id='${id}']`)).filter((x) => x.checked).map((x) => x.dataset.mod);
      const payload = { role, language, modules };
      if (password) payload.password = password;
      await api(`/api/admin/users/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      await renderUserTable();
    });
  });
}

async function createUser() {
  if (!q("#new-username")) return;
  const username = q("#new-username").value.trim();
  const password = q("#new-password").value.trim();
  const role = q("#new-role").value;
  const language = q("#new-language").value;
  const modules = role === "designer" ? ["dashboard", "projects"] : ["dashboard", "projects"];
  await api("/api/admin/users", { method: "POST", body: JSON.stringify({ username, password, role, language, modules }) });
  q("#new-username").value = "";
  q("#new-password").value = "";
  await renderUserTable();
}

async function saveBrand() {
  if (!q("#brand-company-name")) return;
  const payload = {
    company_name: q("#brand-company-name").value.trim(),
    tagline: q("#brand-tagline-input").value.trim(),
    logo_horizontal_url: q("#brand-logo-horizontal").value.trim(),
    logo_icon_url: q("#brand-logo-icon").value.trim(),
    primary_color: q("#brand-primary-color").value.trim(),
    accent_color: q("#brand-accent-color").value.trim(),
    website_webhook_key: q("#brand-webhook-key").value.trim(),
  };
  const updated = await api("/api/company/settings", { method: "PUT", body: JSON.stringify(payload) });
  state.brand = updated;
  applyBrand();
  renderApp();
}

async function renderApp() {
  setPageHeader();
  renderMenu();
  q("#lang-select").value = state.locale;

  if (state.module === "dashboard") return renderDashboard();
  if (state.module === "finance") return renderFinance();
  if (state.module === "settings") return renderSettings();
  return renderCrud(state.module);
}

async function initApp() {
  try {
    state.brand = await api("/api/company/settings");
    applyBrand();
  } catch {
    state.brand = null;
  }

  q("#logout-btn").addEventListener("click", async () => {
    await api("/api/auth/logout", { method: "POST" });
    state.user = null;
    q("#app-view").classList.add("hidden");
    q("#login-view").classList.remove("hidden");
    renderLogin();
  });

  q("#lang-select").addEventListener("change", async () => {
    state.locale = q("#lang-select").value;
    state.pdfLang = state.locale;
    await api("/api/auth/me/language", { method: "PUT", body: JSON.stringify({ language: state.locale }) });
    renderApp();
  });

  const me = await api("/api/auth/me");
  if (!me.authenticated) {
    q("#login-view").classList.remove("hidden");
    q("#app-view").classList.add("hidden");
    renderLogin();
    return;
  }

  state.user = me.user;
  state.locale = state.user.language || "zh";
  state.pdfLang = state.locale;
  state.brand = me.brand || state.brand;
  applyBrand();
  const mods = availableModules();
  state.module = mods.includes("dashboard") ? "dashboard" : (mods[0] || "dashboard");
  q("#login-view").classList.add("hidden");
  q("#app-view").classList.remove("hidden");
  renderApp();
}

initApp().catch((e) => {
  alert(e.message);
});
