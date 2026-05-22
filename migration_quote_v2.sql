-- =====================================================================
-- Oaklian CRM 报价系统重构 - 步骤 1.1 数据库迁移
-- =====================================================================
-- 创建日期: 2026-04-25
-- 适用于: /var/www/crm-oaklian/crm.db
-- 前提: 已备份(crm.db.before_quote_v2.20260425_033117)
--
-- 这个脚本会:
--   A. 清理废弃数据(quotes 表、5 份测试 estimates)
--   B. 给 estimates 表加 14 个新字段
--   C. 新建 11 张表
--   D. 预置标准分区(14)、单价库(20+8)、模板(7)
--   E. 预置 7 条全局设置到 system_settings
--
-- 所有操作包在一个 transaction 里,任意一步失败整个回滚。
-- =====================================================================

BEGIN TRANSACTION;

-- =====================================================================
-- A. 清理
-- =====================================================================

-- A1. 删除废弃的 quotes 表(1 条测试数据,跟现在的 estimates 模块无关)
DROP TABLE IF EXISTS quotes;

-- A2. 清空 estimates 表里的 5 份测试数据(按你的决定:B 全删)
DELETE FROM estimates;
-- 重置自增 id(让新报价从 1 开始)
DELETE FROM sqlite_sequence WHERE name='estimates';

-- A3. estimate_templates 旧表保留不动(里面 3 条作为历史参考)


-- =====================================================================
-- B. 给 estimates 表加新字段(ALTER TABLE 不影响现有数据)
-- =====================================================================

-- 报价类型 renovation/rebuild
ALTER TABLE estimates ADD COLUMN estimate_type TEXT DEFAULT 'renovation';

-- 税率相关
ALTER TABLE estimates ADD COLUMN tax_enabled INTEGER DEFAULT 0;
ALTER TABLE estimates ADD COLUMN tax_rate REAL DEFAULT 0;

-- 完工后留款相关
ALTER TABLE estimates ADD COLUMN holdback_pct REAL DEFAULT 0;
ALTER TABLE estimates ADD COLUMN holdback_mode TEXT DEFAULT 'disabled';
-- holdback_mode: disabled(不留) / immediate(完工后立即收) / delayed(N 天后收)
ALTER TABLE estimates ADD COLUMN holdback_days INTEGER DEFAULT 0;

-- PDF 选项
ALTER TABLE estimates ADD COLUMN pdf_show_unit_price INTEGER DEFAULT 1;
ALTER TABLE estimates ADD COLUMN pdf_show_pct INTEGER DEFAULT 0;
ALTER TABLE estimates ADD COLUMN pdf_language TEXT DEFAULT 'zh';

-- 重建报价专用字段(翻新报价不用)
ALTER TABLE estimates ADD COLUMN rebuild_base_type TEXT;
ALTER TABLE estimates ADD COLUMN rebuild_unit_price REAL;
ALTER TABLE estimates ADD COLUMN rebuild_total_sqft REAL;

-- 凑整规则: exact / 10 / 100 / 1000
ALTER TABLE estimates ADD COLUMN rounding_mode TEXT DEFAULT '100';

-- 来源模板(可选,用于追溯)
ALTER TABLE estimates ADD COLUMN source_template_id INTEGER;


-- =====================================================================
-- C. 新建 11 张表
-- =====================================================================

-- C1. 标准分区主表(14 个 Bay Area 翻新分区,管理员可增删)
CREATE TABLE estimate_sections_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL UNIQUE,
    name_en TEXT NOT NULL,
    name_zh TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- C2. 报价分区(每份报价的拆除/水电/...等)
CREATE TABLE estimate_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id INTEGER NOT NULL,
    master_id INTEGER,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    section_subtotal REAL DEFAULT 0,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE CASCADE,
    FOREIGN KEY (master_id) REFERENCES estimate_sections_master(id) ON DELETE SET NULL
);
CREATE INDEX idx_estimate_sections_estimate ON estimate_sections(estimate_id);

-- C3. 报价明细行
CREATE TABLE estimate_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    price_library_id INTEGER,
    item_name TEXT NOT NULL,
    description TEXT,
    quantity REAL NOT NULL DEFAULT 0,
    unit TEXT,
    material_unit_price REAL DEFAULT 0,
    labor_unit_price REAL DEFAULT 0,
    line_subtotal REAL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    note TEXT,
    is_overridden INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES estimate_sections(id) ON DELETE CASCADE,
    FOREIGN KEY (price_library_id) REFERENCES price_library(id) ON DELETE SET NULL
);
CREATE INDEX idx_estimate_lines_estimate ON estimate_lines(estimate_id);
CREATE INDEX idx_estimate_lines_section ON estimate_lines(section_id);

-- C4. 重建附加项(只用于 rebuild 类型报价)
CREATE TABLE estimate_addons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id INTEGER NOT NULL,
    rebuild_lib_id INTEGER,
    name TEXT NOT NULL,
    description TEXT,
    unit_price REAL DEFAULT 0,
    quantity REAL DEFAULT 1,
    unit TEXT,
    addon_subtotal REAL DEFAULT 0,
    is_selected INTEGER DEFAULT 1,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE CASCADE
);
CREATE INDEX idx_estimate_addons_estimate ON estimate_addons(estimate_id);

-- C5. 报价付款节点(草稿态,确认后复制到 contract_payment_milestones)
CREATE TABLE estimate_payment_milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    trigger_type TEXT NOT NULL DEFAULT 'stage',
    -- trigger_type: signing(签约时) / stage(关联施工阶段) / completion_immediate(完工后立即) / completion_delayed(完工 N 天后)
    trigger_stage_template_item_id INTEGER,
    trigger_days_after_completion INTEGER DEFAULT 0,
    amount_pct REAL NOT NULL DEFAULT 0,
    amount_fixed REAL,
    is_holdback INTEGER DEFAULT 0,
    note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE CASCADE,
    FOREIGN KEY (trigger_stage_template_item_id) REFERENCES project_stage_template_items(id) ON DELETE SET NULL
);
CREATE INDEX idx_epm_estimate ON estimate_payment_milestones(estimate_id);

-- C6. 单价改动留痕
CREATE TABLE estimate_price_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estimate_id INTEGER NOT NULL,
    line_id INTEGER,
    addon_id INTEGER,
    rebuild_unit_price_override INTEGER DEFAULT 0,
    field_name TEXT NOT NULL,
    original_value REAL,
    new_value REAL,
    reason TEXT,
    changed_by INTEGER,
    changed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estimate_id) REFERENCES estimates(id) ON DELETE CASCADE,
    FOREIGN KEY (line_id) REFERENCES estimate_lines(id) ON DELETE CASCADE,
    FOREIGN KEY (addon_id) REFERENCES estimate_addons(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX idx_epo_estimate ON estimate_price_overrides(estimate_id);

-- C7. 单价库(翻新)
CREATE TABLE price_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT,
    section_master_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,
    description TEXT,
    unit TEXT NOT NULL,
    default_qty REAL DEFAULT 1,
    material_unit_price REAL DEFAULT 0,
    labor_unit_price REAL DEFAULT 0,
    customer_visible_note TEXT,
    internal_note TEXT,
    photo_url TEXT,
    vendor_id INTEGER,
    tag TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    FOREIGN KEY (section_master_id) REFERENCES estimate_sections_master(id) ON DELETE RESTRICT,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX idx_price_library_section ON price_library(section_master_id);
CREATE INDEX idx_price_library_active ON price_library(is_active);

-- C8. 单价库(重建,$/sqft 主体 + 附加项)
CREATE TABLE price_library_rebuild (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT,
    item_type TEXT NOT NULL DEFAULT 'base',
    -- item_type: base(主体, $/sqft) / addon(附加项)
    name TEXT NOT NULL,
    description TEXT,
    unit TEXT NOT NULL,
    default_unit_price REAL DEFAULT 0,
    default_qty REAL DEFAULT 1,
    customer_visible_note TEXT,
    internal_note TEXT,
    photo_url TEXT,
    vendor_id INTEGER,
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

-- C9. 新模板主表(取代老 estimate_templates,但老表保留)
CREATE TABLE estimate_template_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    template_type TEXT NOT NULL DEFAULT 'full',
    -- template_type: full(整套模板) / section(分区模板)
    estimate_type TEXT NOT NULL DEFAULT 'renovation',
    -- estimate_type: renovation / rebuild
    description TEXT,
    default_markup_rate REAL DEFAULT 15,
    use_count INTEGER DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER,
    FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
);

-- C10. 模板分区
CREATE TABLE estimate_template_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    section_master_id INTEGER NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES estimate_template_v2(id) ON DELETE CASCADE,
    FOREIGN KEY (section_master_id) REFERENCES estimate_sections_master(id) ON DELETE RESTRICT
);
CREATE INDEX idx_ets_template ON estimate_template_sections(template_id);

-- C11. 模板明细行(引用 price_library,支持覆盖)
CREATE TABLE estimate_template_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_section_id INTEGER NOT NULL,
    price_library_id INTEGER,
    item_name TEXT NOT NULL,
    description TEXT,
    unit TEXT,
    -- 覆盖单价(NULL = 用单价库当前价;有值 = 模板覆盖)
    override_material_price REAL,
    override_labor_price REAL,
    sort_order INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_section_id) REFERENCES estimate_template_sections(id) ON DELETE CASCADE,
    FOREIGN KEY (price_library_id) REFERENCES price_library(id) ON DELETE SET NULL
);
CREATE INDEX idx_etl_section ON estimate_template_lines(template_section_id);


-- =====================================================================
-- D. 预置标准数据
-- =====================================================================

-- D1. 14 个标准分区
INSERT INTO estimate_sections_master (code, name_en, name_zh, sort_order) VALUES
  ('PERMIT',     'Permits & Design',          '许可与设计',       1),
  ('DEMO',       'Demolition',                '拆除',             2),
  ('STRUCT',     'Structural',                '结构(框架/地基)', 3),
  ('PLUMB',      'Plumbing',                  '水管',             4),
  ('ELEC',       'Electrical',                '电',               5),
  ('HVAC',       'HVAC',                      '暖通',             6),
  ('INSUL',      'Insulation & Waterproofing','隔热与防水',       7),
  ('DRYWALL',    'Drywall & Paint',           '墙面与油漆',       8),
  ('FLOOR',      'Flooring',                  '地面',             9),
  ('CABINET',    'Cabinets & Countertops',    '橱柜与台面',      10),
  ('DOORWIN',    'Doors & Windows',           '门窗',            11),
  ('BATHFIX',    'Bath Fixtures',             '卫浴洁具',        12),
  ('EXTERIOR',   'Exterior',                  '外部',            13),
  ('FINISH',     'Finish & Cleanup',          '收尾与清洁',      14);


-- D2. 翻新单价库(20 条核心常用项 - Bay Area 中位价,管理员可调)
-- 注:价格基于 Bay Area 2026 年市场行情参考,实际请管理员根据自己经验调整
INSERT INTO price_library (sku, section_master_id, item_name, description, unit, default_qty, material_unit_price, labor_unit_price, tag) VALUES
  -- 拆除
  ('DEM-001', (SELECT id FROM estimate_sections_master WHERE code='DEMO'),    '拆墙(非承重)',     '室内非承重隔墙拆除',         'sqft',    1,  2.00,  5.00,  '常用'),
  ('DEM-002', (SELECT id FROM estimate_sections_master WHERE code='DEMO'),    '拆地板/地砖',       '现有地面材料拆除',           'sqft',    1,  0.50,  3.50,  '常用'),
  ('DEM-003', (SELECT id FROM estimate_sections_master WHERE code='DEMO'),    '拆橱柜',           '现有橱柜整体拆除',           'linear ft', 1, 0,    25.00, '常用'),
  ('DEM-005', (SELECT id FROM estimate_sections_master WHERE code='DEMO'),    '垃圾清运',         'Dumpster + 运费(每次)',     '次',      1,  0,    500.00, '常用'),
  -- 水管
  ('PLB-001', (SELECT id FROM estimate_sections_master WHERE code='PLUMB'),   '水管改造(厨房)',   '厨房水槽 + 洗碗机水路',      '组',      1,  350,   800,    '常用'),
  ('PLB-002', (SELECT id FROM estimate_sections_master WHERE code='PLUMB'),   '水管改造(浴室)',   '马桶 + 洗手台 + 淋浴水路',   '组',      1,  280,   650,    '常用'),
  ('PLB-003', (SELECT id FROM estimate_sections_master WHERE code='PLUMB'),   '热水器更换',        '50 加仑标准热水器 + 安装',   '台',      1,  900,   400,    '通用'),
  -- 电
  ('ELC-001', (SELECT id FROM estimate_sections_master WHERE code='ELEC'),    '电路改造(厨房)',   '厨房电路 + 加点位',          '组',      1,  300,   850,    '常用'),
  ('ELC-002', (SELECT id FROM estimate_sections_master WHERE code='ELEC'),    '电箱升级',          '主电箱升级到 200A',          '套',      1,  1200,  1500,   '通用'),
  ('ELC-003', (SELECT id FROM estimate_sections_master WHERE code='ELEC'),    '射灯/吸顶灯安装',   '含电路',                     '个',      1,  35,    65,     '通用'),
  -- 墙面与油漆
  ('DRY-001', (SELECT id FROM estimate_sections_master WHERE code='DRYWALL'), '墙面石膏板',        '安装 + 接缝处理',            'sqft',    1,  1.20,  2.50,   '常用'),
  ('DRY-002', (SELECT id FROM estimate_sections_master WHERE code='DRYWALL'), '墙面油漆(2 道)',   'Primer + 2 道面漆',          'sqft',    1,  0.80,  1.50,   '常用'),
  -- 地面
  ('FLR-001', (SELECT id FROM estimate_sections_master WHERE code='FLOOR'),   '地砖铺设',          '不含瓷砖材料,按面积计',      'sqft',    1,  6.50,  5.50,   '常用'),
  ('FLR-002', (SELECT id FROM estimate_sections_master WHERE code='FLOOR'),   '强化木地板',        '含找平和踢脚线',             'sqft',    1,  4.50,  3.50,   '常用'),
  ('FLR-003', (SELECT id FROM estimate_sections_master WHERE code='FLOOR'),   'LVP 防水地板',      '含找平',                     'sqft',    1,  3.80,  3.00,   '常用'),
  -- 橱柜与台面
  ('CAB-001', (SELECT id FROM estimate_sections_master WHERE code='CABINET'), '定制橱柜(中档)',   'IKEA 级别整厨橱柜',          'linear ft',1,  280,   120,    '常用'),
  ('CAB-002', (SELECT id FROM estimate_sections_master WHERE code='CABINET'), '石英台面安装',      '中档石英,含切角和水槽孔',    'sqft',    1,  70,    40,     '常用'),
  ('CAB-003', (SELECT id FROM estimate_sections_master WHERE code='CABINET'), '花岗岩台面安装',    '中档花岗岩,含切角',          'sqft',    1,  85,    40,     '通用'),
  -- 卫浴洁具
  ('BAT-001', (SELECT id FROM estimate_sections_master WHERE code='BATHFIX'), '马桶(标准)',       'Toto 或同级,含安装',         '个',      1,  280,   200,    '常用'),
  ('BAT-002', (SELECT id FROM estimate_sections_master WHERE code='BATHFIX'), '淋浴间(标准)',     '玻璃门 + 淋浴系统,含安装',   '套',      1,  1200,  900,    '常用');


-- D3. 重建单价库(8 条:5 个建筑类型基础单价 + 3 个常见附加项)
INSERT INTO price_library_rebuild (sku, item_type, name, description, unit, default_unit_price, sort_order) VALUES
  -- 主体 (base)
  ('RB-MAIN',   'base',  '新建主屋(标准)',   '标准住宅新建,含基础水电结构',    'sqft', 400,    1),
  ('RB-ADU-D',  'base',  '新建 ADU(独立)',  '独立 ADU 单元,包含基础设施',    'sqft', 380,    2),
  ('RB-ADU-A',  'base',  '新建 ADU(附属)',  '附属在主屋上的 ADU',             'sqft', 350,    3),
  ('RB-GARAGE', 'base',  '新建车库',          '独立或附属车库',                 'sqft', 220,    4),
  ('RB-2ND-FL', 'base',  '2 层加建',          '在现有主屋上加建二层',           'sqft', 320,    5),
  -- 附加项 (addon)
  ('RB-POOL',   'addon', '游泳池',            '标准 12×24 ft 泳池,含基础水电', '个',   50000,  10),
  ('RB-SOLAR',  'addon', '太阳能板系统',      '屋顶 8 kW 系统',                 '套',   22000,  11),
  ('RB-SMART',  'addon', '全屋智能系统',      '灯光 + 温控 + 安防',             '套',   18000,  12);


-- D4. 预置 4 个整套模板 + 3 个分区模板
-- D4.1 标准厨房翻新(整套)
INSERT INTO estimate_template_v2 (id, name, template_type, estimate_type, description, default_markup_rate)
VALUES (1, '标准厨房翻新', 'full', 'renovation', 'Bay Area 中档厨房翻新,约 100-150 sqft', 15);

-- 厨房翻新的分区
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 1, 1, id, 1 FROM estimate_sections_master WHERE code='DEMO';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 2, 1, id, 2 FROM estimate_sections_master WHERE code='PLUMB';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 3, 1, id, 3 FROM estimate_sections_master WHERE code='ELEC';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 4, 1, id, 4 FROM estimate_sections_master WHERE code='CABINET';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 5, 1, id, 5 FROM estimate_sections_master WHERE code='DRYWALL';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 6, 1, id, 6 FROM estimate_sections_master WHERE code='FLOOR';

-- 厨房翻新的明细行(引用单价库)
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 1, id, item_name, unit, 1 FROM price_library WHERE sku='DEM-001';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 1, id, item_name, unit, 2 FROM price_library WHERE sku='DEM-003';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 1, id, item_name, unit, 3 FROM price_library WHERE sku='DEM-005';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 2, id, item_name, unit, 1 FROM price_library WHERE sku='PLB-001';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 3, id, item_name, unit, 1 FROM price_library WHERE sku='ELC-001';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 3, id, item_name, unit, 2 FROM price_library WHERE sku='ELC-003';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 4, id, item_name, unit, 1 FROM price_library WHERE sku='CAB-001';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 4, id, item_name, unit, 2 FROM price_library WHERE sku='CAB-002';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 5, id, item_name, unit, 1 FROM price_library WHERE sku='DRY-001';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 5, id, item_name, unit, 2 FROM price_library WHERE sku='DRY-002';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 6, id, item_name, unit, 1 FROM price_library WHERE sku='FLR-001';

-- D4.2 标准浴室翻新(整套)
INSERT INTO estimate_template_v2 (id, name, template_type, estimate_type, description, default_markup_rate)
VALUES (2, '标准浴室翻新', 'full', 'renovation', 'Bay Area 中档浴室翻新,约 40-80 sqft', 15);

INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 7, 2, id, 1 FROM estimate_sections_master WHERE code='DEMO';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 8, 2, id, 2 FROM estimate_sections_master WHERE code='PLUMB';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 9, 2, id, 3 FROM estimate_sections_master WHERE code='ELEC';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 10, 2, id, 4 FROM estimate_sections_master WHERE code='INSUL';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 11, 2, id, 5 FROM estimate_sections_master WHERE code='BATHFIX';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 12, 2, id, 6 FROM estimate_sections_master WHERE code='DRYWALL';
INSERT INTO estimate_template_sections (id, template_id, section_master_id, sort_order)
SELECT 13, 2, id, 7 FROM estimate_sections_master WHERE code='FLOOR';

INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 7, id, item_name, unit, 1 FROM price_library WHERE sku='DEM-002';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 7, id, item_name, unit, 2 FROM price_library WHERE sku='DEM-005';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 8, id, item_name, unit, 1 FROM price_library WHERE sku='PLB-002';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 9, id, item_name, unit, 1 FROM price_library WHERE sku='ELC-003';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 11, id, item_name, unit, 1 FROM price_library WHERE sku='BAT-001';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 11, id, item_name, unit, 2 FROM price_library WHERE sku='BAT-002';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 12, id, item_name, unit, 1 FROM price_library WHERE sku='DRY-002';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT 13, id, item_name, unit, 1 FROM price_library WHERE sku='FLR-001';

-- D4.3 ADU 翻新(整套,包含全部 14 分区,只放主要明细做示例)
INSERT INTO estimate_template_v2 (id, name, template_type, estimate_type, description, default_markup_rate)
VALUES (3, 'ADU 翻新', 'full', 'renovation', 'ADU 整体翻新,涵盖大部分施工类目', 18);

-- ADU 翻新分区(精简版,管理员可在后台扩充)
INSERT INTO estimate_template_sections (template_id, section_master_id, sort_order) VALUES
  (3, 1, 1), (3, 2, 2), (3, 3, 3), (3, 4, 4), (3, 5, 5),
  (3, 6, 6), (3, 7, 7), (3, 8, 8), (3, 9, 9), (3, 10, 10),
  (3, 11, 11), (3, 12, 12), (3, 13, 13), (3, 14, 14);

-- D4.4 ADU 重建模板(rebuild 类型)
INSERT INTO estimate_template_v2 (id, name, template_type, estimate_type, description, default_markup_rate)
VALUES (4, 'ADU 重建(按 sqft)', 'full', 'rebuild', 'ADU 推倒重建,按面积计算', 18);

-- D4.5/D4.6/D4.7 三个分区模板
INSERT INTO estimate_template_v2 (id, name, template_type, estimate_type, description, default_markup_rate)
VALUES (5, '拆除分区模板', 'section', 'renovation', '快速插入拆除相关明细', 15);
INSERT INTO estimate_template_sections (template_id, section_master_id, sort_order)
SELECT 5, id, 1 FROM estimate_sections_master WHERE code='DEMO';
INSERT INTO estimate_template_lines (template_section_id, price_library_id, item_name, unit, sort_order)
SELECT (SELECT id FROM estimate_template_sections WHERE template_id=5),
       id, item_name, unit, ROW_NUMBER() OVER (ORDER BY sku)
FROM price_library WHERE section_master_id=(SELECT id FROM estimate_sections_master WHERE code='DEMO');

INSERT INTO estimate_template_v2 (id, name, template_type, estimate_type, description, default_markup_rate)
VALUES (6, '水电分区模板', 'section', 'renovation', '快速插入水电明细', 15);
INSERT INTO estimate_template_sections (template_id, section_master_id, sort_order)
SELECT 6, id, 1 FROM estimate_sections_master WHERE code='PLUMB';
INSERT INTO estimate_template_sections (template_id, section_master_id, sort_order)
SELECT 6, id, 2 FROM estimate_sections_master WHERE code='ELEC';

INSERT INTO estimate_template_v2 (id, name, template_type, estimate_type, description, default_markup_rate)
VALUES (7, '收尾分区模板', 'section', 'renovation', '快速插入收尾明细', 15);
INSERT INTO estimate_template_sections (template_id, section_master_id, sort_order)
SELECT 7, id, 1 FROM estimate_sections_master WHERE code='FINISH';


-- =====================================================================
-- E. 预置全局设置(到 system_settings)
-- =====================================================================

-- system_settings 表的实际结构: (setting_key, setting_value, setting_group, updated_at, updated_by)
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_group, updated_at) VALUES
  ('estimate_tax_enabled',      '0',    'estimate', CURRENT_TIMESTAMP),
  ('estimate_tax_rate',         '9.25', 'estimate', CURRENT_TIMESTAMP),
  ('estimate_markup_min',       '10',   'estimate', CURRENT_TIMESTAMP),
  ('estimate_markup_max',       '25',   'estimate', CURRENT_TIMESTAMP),
  ('estimate_markup_default',   '15',   'estimate', CURRENT_TIMESTAMP),
  ('estimate_rounding_mode',    '100',  'estimate', CURRENT_TIMESTAMP),
  ('estimate_holdback_default', '5',    'estimate', CURRENT_TIMESTAMP),
  ('estimate_holdback_max',     '10',   'estimate', CURRENT_TIMESTAMP);


COMMIT;

-- =====================================================================
-- 完成。如需验证,跑下面的查询:
-- =====================================================================
-- .tables
-- SELECT COUNT(*) FROM estimate_sections_master;       -- 应该 14
-- SELECT COUNT(*) FROM price_library;                   -- 应该 20
-- SELECT COUNT(*) FROM price_library_rebuild;           -- 应该 8
-- SELECT COUNT(*) FROM estimate_template_v2;            -- 应该 7
-- SELECT COUNT(*) FROM estimates;                       -- 应该 0(已清空)
-- =====================================================================
