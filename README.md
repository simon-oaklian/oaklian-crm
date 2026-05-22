# Oaklian CRM

装修公司 CRM 系统（中文后台为主，支持中/英/西），已包含：
- 客户/线索与跟进提醒
- 报价 -> 合同 -> 项目链路
- 项目进度、付款催办、变更单
- 设计师视图与佣金摘要
- 附件上传（含工地照片）
- 报价/合同/变更单打印导出
- 文档模板中心
- 通知中心
- 系统设置中心

## 1. 目录说明

```text
project-root/
├── app.py
├── crm.db
├── assets/
├── static/
├── uploads/
├── logs/
├── .env.example
├── requirements.txt
├── README.md
└── deploy/
    ├── nginx.conf.example
    ├── crm-oaklian.service
    ├── backup.sh
    ├── restore.sh
    ├── init_admin.py
    └── migrate.py
```

说明：
- `uploads/`：客户附件、报价/合同/PDF、工地照片（持久化目录）
- `logs/`：应用日志目录（`app.log`、`error.log`）
- `deploy/`：上线模板与运维脚本

## 2. 本地开发启动

1. 准备 Python 3.9+（当前项目无第三方依赖，标准库可运行）
2. 启动：

```bash
python3 app.py
```

3. 访问：
- `http://127.0.0.1:8000`

## 3. 环境变量说明

复制并编辑：

```bash
cp .env.example .env
```

支持变量（无环境变量时仍可本地启动）：
- `APP_ENV=development|production`
- `HOST=127.0.0.1|0.0.0.0`
- `PORT=8000`
- `CRM_DB_PATH=./crm.db`
- `CRM_UPLOAD_DIR=./uploads`
- `CRM_LOG_DIR=./logs`
- `CRM_SESSION_SECRET=...`（生产必须修改）
- `CRM_WEBHOOK_KEY=...`（网站/Houzz 外部线索写入 key）
- `CRM_DEFAULT_LANGUAGE=zh|en|es`
- `CRM_BASE_URL=https://crm.oaklian.com`

## 4. 生产环境部署步骤（无 Docker）

以下以 `/opt/crm-oaklian` 为例：

1. 上传代码到服务器
2. 创建并配置环境变量：

```bash
cd /opt/crm-oaklian
cp .env.example .env
# 编辑 .env（重点：CRM_SESSION_SECRET / CRM_WEBHOOK_KEY / CRM_BASE_URL）
```

3. 初始化/迁移数据库（幂等）：

```bash
python3 deploy/migrate.py
```

4. 如需重置首个管理员：

```bash
python3 deploy/init_admin.py <username> <password> owner
```

## 5. systemd 配置与启动

1. 复制服务文件：

```bash
sudo cp deploy/crm-oaklian.service /etc/systemd/system/crm-oaklian.service
```

2. 按实际路径调整：
- `WorkingDirectory`
- `ExecStart`
- `EnvironmentFile`
- `User/Group`

3. 启动并设为开机启动：

```bash
sudo systemctl daemon-reload
sudo systemctl enable crm-oaklian
sudo systemctl start crm-oaklian
sudo systemctl status crm-oaklian
```

日志查看：

```bash
tail -f logs/app.log
tail -f logs/error.log
journalctl -u crm-oaklian -f
```

## 6. Nginx 反向代理

示例模板：`deploy/nginx.conf.example`

关键点：
- `server_name crm.oaklian.com`
- 反代到 `127.0.0.1:8000`
- 路径覆盖：`/`、`/api/`、`/print/`、`/assets/`、`/uploads/`
- `client_max_body_size 20m`

部署：

```bash
sudo cp deploy/nginx.conf.example /etc/nginx/conf.d/crm-oaklian.conf
sudo nginx -t
sudo systemctl reload nginx
```

## 7. 备份与恢复

### 7.1 备份

```bash
bash deploy/backup.sh
# 或指定备份目录
bash deploy/backup.sh /data/crm-backups
```

备份内容：
- `crm.db`
- `uploads/`
- `.env`（存在时）

输出：
- 时间戳目录
- 对应 `.tar.gz` 压缩包

### 7.2 恢复

```bash
# 推荐先停服务
sudo systemctl stop crm-oaklian

# 从目录恢复
bash deploy/restore.sh /data/crm-backups/crm_backup_YYYYmmdd_HHMMSS

# 从压缩包恢复（--yes 跳过确认）
bash deploy/restore.sh /data/crm-backups/crm_backup_YYYYmmdd_HHMMSS.tar.gz --yes

# 再启动服务
sudo systemctl start crm-oaklian
```

## 8. 升级/发布注意事项

建议流程：
1. `backup.sh` 先做备份
2. 更新代码
3. 执行 `python3 deploy/migrate.py`
4. 重启 `crm-oaklian`
5. 验证：登录、附件、打印、通知、系统设置

注意：
- `app.py` 已包含自动建表与列补齐逻辑（`init_db()` + `ensure_columns`）
- 升级不要删除 `crm.db` 与 `uploads/`

## 9. 权限与安全最低要求

- 生产必须设置 `CRM_SESSION_SECRET`（不要使用默认占位值）
- 外部线索入口继续使用 webhook key 校验（优先公司设置中的 key，未配置时回退 `CRM_WEBHOOK_KEY`）
- 上传类型限制仍为：`jpg/jpeg/png/pdf`，最大 `20MB`
- 删除附件会同时删除 DB 记录与磁盘文件
- `designer` 角色仍为受限视图，后端接口继续做权限拦截（不是仅前端隐藏）

## 10. 文件与目录权限建议

建议运行用户对以下路径有读写权限：
- `crm.db`
- `uploads/`
- `logs/`

示例：

```bash
sudo chown -R www-data:www-data /opt/crm-oaklian
sudo chmod -R u+rwX,g+rwX /opt/crm-oaklian
```

## 11. 常见问题

1. Logo 不显示
- 检查是否使用站内绝对路径：`/assets/images/...`
- 检查 Nginx 中 `/assets/` 的 `alias` 是否正确

2. 上传后文件打不开
- 检查 `/uploads/` 路由是否被 Nginx 放行
- 检查 `CRM_UPLOAD_DIR` 与目录权限

3. designer 出现 403
- 属于预期：designer 默认不能访问老板/经理模块
- 检查账号模块分配与角色是否正确

4. 系统设置保存后没生效
- 确认保存成功（页面提示）
- 某些逻辑为“新数据生效”（例如新报价后的默认回访天数）

## 12. 默认账号说明

历史开发环境可能存在：
- `boss / boss123`
- `pm / pm123`

生产建议：
- 使用 `deploy/init_admin.py` 创建新 owner
- 立即修改或删除默认测试账号
- 全站使用 HTTPS（由 Nginx/证书层处理）
