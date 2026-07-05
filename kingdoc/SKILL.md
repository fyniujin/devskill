---
name: kingdoc
displayName: 金山文档 KingDoc
slug: kingdoc
version: 2.3.0
description: >
  金山文档 AI 协作助手 — 9 品类在线文档全生命周期管理
  （智能文档/文字/电子表格/演示文稿/多维表格/收集表/思维导图/流程图/附件），
  覆盖腾讯文档全部 8 大功能 + 金山独有 10 项增强（回收站、版本历史、格式转换、
  纯文本提取、本地 Tesseract OCR、通知推送、Webhook、批量任务、政企合规）。
  文字/演示/思维导图/流程图采用"本地生成→上传覆盖"策略，
  电子表格/多维表格采用 API 精细编辑。
description_zh: "金山文档 AI 协作助手 — 9 品类在线文档全生命周期管理"
category: 办公效率
platforms: [WorkBuddy, QClaw, ima, Claude Code, Cursor]
tags: [文档处理, 表格处理, PPT生成, 多维表格, 表单收集, 思维导图, 流程图, OCR, 政企合规]
license: MIT
requires_api_key: true
icon: assets/icon.png
---

# KingDoc — 金山文档 AI 协作助手 v2.3.0

> 对标腾讯文档 TENCENT DOCS，功能 1:1 覆盖 + 差异化增强。
> 文档管理的"腾讯有的全有，腾讯没有的也有"。

## ⚠️ 首次使用必读

### 1. 申请金山开放平台 App（免费）

**不申请 App，所有 API 调用都会报 KD001 鉴权失败。**

申请步骤：
1. 访问 [金山开放平台](https://developer.kdocs.cn) 并登录你的金山文档账号
2. 进入「应用管理」→「创建应用」
3. 填写应用名称（如：`KingDoc`）和应用描述
4. 获取 **`App ID`** 和 **`App Secret`**
5. 选择应用权限（OAuth Scope）：
   - 必须勾选：`user:file:write`、`user:file:read`、`team:file:write`、`team:file:read`
   - 建议勾选：`user:team:read`（查看团队信息）、`user:notification:write`（推送通知）
6. 应用审核通常 1 个工作日通过，测试阶段限速 500 次/天，申请正式版后 10 万次/天

### 2. 安装 Tesseract OCR（可选，本地图片识别）

KingDoc 使用本地 Tesseract OCR 实现图片文字提取，无需额外 API Key：

```bash
# Windows
winget install UB-Mannheim.TesseractOCR

# macOS
brew install tesseract tesseract-lang

# Linux
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
```

安装后重启终端。如未安装，`kdoc.local.ocr.extract` 不可用，其他功能不受影响。

### 3. 配置 KingDoc

拿到 App ID 和 Secret 后执行：

```bash
# Linux/macOS
bash setup.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File setup.ps1
```
脚本会引导你输入 App ID 和 Secret，自动生成 mcp-config.json、模板和图标。

---

## 快速开始

| 你想做什么 | 直接对 AI 说 |
|-----------|-------------|
| 新建一个会议纪要 | `"帮我写一份会议纪要"` |
| 创建 Excel 数据表 | `"建一个销售数据表格，含产品/销量/金额"` |
| 生成 PPT | `"帮我做一份产品发布 PPT"` |
| 生成思维导图 | `"画一个项目计划的思维导图"` |
| 生成流程图 | `"画一个用户下单流程图"` |
| 查看文档内容 | `"看看这个文档说了什么"` |
| 找一个文件 | `"搜一下上个月的合同"` |
| 上传本地文件 | `"把这个 PDF 上传到云端"` |
| 识别图片文字 | `"把这张发票的文字提取出来"` |
| 恢复误删文件 | `"回收站里有没有昨天删的 Word？"` |
| 回滚到历史版本 | `"这份文档改坏了，回退到上周版本"` |
| 分享文档权限 | `"给张三发个可编辑的链接"` |
| 归档到文件夹 | `"把文件移到 2026 项目文件夹"` |
| 格式转换 | `"把这份文档转成 PDF"` |

---

## 安全声明

| 保护项 | 方式 |
|--------|------|
| 🔒 删除确认 | 删除操作走回收站 API，不物理删除 |
| 🗑️ 软删除+恢复 | `trash.list → trash.recover` |
| 📝 版本冲突检测 | 写入前获取最新版本号，冲突时提示用户合并 |
| 🔐 权限前置校验 | 所有写入操作前自动检查权限，无权限拒绝 |
| ⚡ 限流保护 | 429 自动指数退避重试（最多 5 次） |
| 🛡️ 文件类型拦截 | 默认禁止上传 .exe/.bat/.ps1 等可执行文件 |
| 🔑 Token 安全 | Token 仅存在于内存，不落盘 |
| 📋 审计日志 | 所有写操作记录到本地日志 |
| 🔀 批量合并 | 50ms 窗口内连续写入自动合并为一次请求 |

---

## 支持的文档类型（9 品类）

| 类型 | doc_type | 推荐度 | 创建 | 编辑 | 对标腾讯 | 实现方式 |
|------|----------|--------|------|------|---------|---------|
| 智能文档 | smart_note | ⭐⭐⭐ | ✅ 自动 | ✅ 本地生成+上传 | smartcanvas | Markdown→DOCX→上传覆盖 |
| 文字文档 | doc | ⭐⭐⭐ | ✅ 自动 | ✅ 本地生成+上传 | doc | python-docx→上传覆盖 |
| 电子表格 | sheet | ⭐⭐⭐ | ✅ 自动 | ✅ API 精细编辑 | sheet | 金山 et API（单元格/公式） |
| 演示文稿 | ppt | ⭐⭐⭐ | ✅ 自动 | ✅ 本地生成+上传 | slide | python-pptx→上传覆盖 |
| 多维表格 | smartsheet | ⭐⭐⭐ | ✅ 自动 | ✅ API 精细编辑 | smartsheet | 金山 dbt API（记录/字段/视图） |
| 收集表 | form | ⭐⭐⭐ | ✅ 自动 | ✅ API 配置 | form | 金山 form API |
| 思维导图 | mindmap | ⭐⭐⭐ | ✅ 自动 | ✅ 本地渲染+上传 | mind | mermaid-cli→SVG→上传 |
| 流程图 | flowchart | ⭐⭐⭐ | ✅ 自动 | ✅ 本地渲染+上传 | flowchart | mermaid-cli→SVG→上传 |
| 附件 | attachment | ⭐⭐⭐ | ✅ 自动 | — | — | 本地文件直接上传 |

> **实现策略差异**：金山开放平台 API 限制→采用本地生成+上传覆盖（文字/演示/图片）；
> 金山 API 完整支持→直接 API 精细编辑（表格/多维表格）；
> 金山无该产品线→本地生成后上传为图片或文档（思维导图/流程图）

---

## 核心能力矩阵

### 1️⃣ 文档创建（9 品类全覆盖）

| 用户意图 / 关键词 | 品类 | 创建方法 | 编辑方法 |
|------------------|------|---------|---------|
| 报告/笔记/文章/总结/会议纪要/markdown | smart_note / doc | `kdoc.file.create` | `kdoc.local.docx.generate` → 上传覆盖 |
| PPT/幻灯片/演示文稿 | ppt | `kdoc.file.create` | `kdoc.local.pptx.generate` → 上传覆盖 |
| 数据表格/计算/统计/Excel | sheet | `kdoc.et.create` | `kdoc.et.*` 精细编辑 |
| 多维表格/轻维表 | smartsheet | `kdoc.dbt.create` | `kdoc.dbt.*` 精细编辑 |
| 表单/收集表/问卷 | form | `kdoc.form.create` | `kdoc.form.*` 配置 |
| 思维导图/知识图谱 | mindmap | `kdoc.local.mmd.generate` → 上传 | 生成 SVG→上传覆盖 |
| 流程图/架构图 | flowchart | `kdoc.local.mmd.generate` → 上传 | 生成 SVG→上传覆盖 |
| 上传文件/图片/pdf/附件 | attachment | `kdoc.file.upload` | — |

### 2️⃣ 文档编辑（改内容）

先通过 `kdoc.file.info` 或链接前缀确定原始文档类型，再路由到对应编辑工具集。
**严禁用 A 品类的工具改 B 品类文档。**

| 原始文档类型 | 编辑工具集 | 编辑粒度 |
|------------|-----------|---------|
| 智能文档 | `kdoc.local.docx.generate` → 上传覆盖 | 整文件替换（自动重排） |
| 演示文稿 | `kdoc.local.pptx.generate` → 上传覆盖 | 整文件替换（自动重排） |
| 电子表格 | `kdoc.et.cell.write` / `kdoc.et.range.write` | **单元格级精细编辑** ✅ |
| 多维表格 | `kdoc.dbt.record.*` / `kdoc.dbt.field.*` | **记录级精细编辑** ✅ |
| 收集表 | `kdoc.form.*` 配置修改 | 表单配置级 |
| 思维导图/流程图 | `kdoc.local.mmd.generate` → 上传覆盖 | 整文件替换 |

### 3️⃣ 文件管理（不动内容，只动文件/目录/权限）

| 动作 | 工具 |
|------|------|
| 重命名/移动/删除/复制 | `kdoc.file.*` |
| 导入（本地→云端） | `kdoc.file.upload` |
| 导出（云端→本地） | `kdoc.file.download` |
| 权限变更/分享链接 | `kdoc.file.permission` / `kdoc.share.*` |
| 回收站查询/恢复 | `kdoc.trash.list` / `kdoc.trash.recover` |
| 版本历史/回滚 | `kdoc.version.list` / `kdoc.version.restore` |
| 批量操作 | `kdoc.batch.create` → `kdoc.batch.query` |
| 空间管理 | `kdoc.space.*` / `kdoc.folder.*` |

### 4️⃣ 格式转换与 OCR

| 场景 | 工具 | 实现方式 |
|------|------|---------|
| 文档→PDF/Word/Excel/PPT | `kdoc.office.convert` | 金山 API |
| 文档纯文本提取 | `kdoc.office.extract` | 金山 API |
| 图片 OCR 文字提取 | `kdoc.local.ocr.extract` | 本地 Tesseract OCR ✅ |
| 图片→Word | `kdoc.local.docx.generate(image_ocr=true)` | OCR→生成 DOCX → 上传 |
| 图片→Excel | `kdoc.et.create(data=ocr_table)` | OCR→解析表格→写入电子表格 |
| 网页剪藏 | `kdoc.scrape.url` → `kdoc.file.create` | Playwright 抓取 → 创建文档 |
| HTML 一键上云 | `kdoc.scrape.html` → `kdoc.file.upload` | 读取本地 HTML → 上传 |

### 5️⃣ 扩展能力（腾讯文档没有，KingDoc 独有）

| 能力 | 工具 | 说明 |
|------|------|------|
| 通知推送 | `kdoc.notification.send` | 企微/钉钉/金山协作机器人 |
| 多维表格 Webhook | `kdoc.dbt.webhook.set` | 事件驱动监听表格变更 |
| 应用空间额度用量 | `kdoc.space.quota` | 企业级管理视角 |
| AirScript 自动化 | `kdoc.airscript.run` | 执行自定义脚本 |
| 用户信息 | `kdoc.user.info` | 获取用户详情/团队信息 |

---

## 公共能力

| 场景 | 工具 |
|------|------|
| 获取文档内容 | `kdoc.file.content` |
| 文档纯文本提取 | `kdoc.office.extract` |
| 格式转换 | `kdoc.office.convert` |
| 图片 OCR 提取 | `kdoc.local.ocr.extract` |
| 搜索文档 | `kdoc.file.search` |
| 获取文档元信息 | `kdoc.file.info` |
| 上传图片/文件 | `kdoc.file.upload` |
| 用户信息 | `kdoc.user.info` |
| 空间用量 | `kdoc.space.quota` |
| 能力上报 | `kdoc.report.unsupported` |
| SKILL 更新检查 | `kdoc.skill.update_check` |

---

## 常见工作流

### 1. 创建+编辑智能文档（对标腾讯 smartcanvas）
```
步骤1: kdoc.file.create(name="项目方案", type="doc")
步骤2: kdoc.local.docx.generate(content="# 项目方案\n## 背景\n...", template="weekly_report")
步骤3: kdoc.file.upload(file_path="output.docx", file_id=<file_id>)
返回: https://docs.wps.cn/doc/<file_id>
```

### 2. 创建+编辑电子表格（API 精细编辑）
```
步骤1: kdoc.et.create(name="销售数据")
步骤2: kdoc.et.range.write(sheet_id=<id>, range="A1:C10", values=[...])  ← 必须用批量
步骤3: kdoc.et.formula.set(sheet_id=<id>, cell="D1", formula="=SUM(C1:C10)")
返回: https://docs.wps.cn/sheet/<file_id>
```

### 3. 创建多维表格（API 精细编辑）
```
步骤1: kdoc.dbt.create(name="客户管理")
步骤2: kdoc.dbt.field.add(table_id=<id>, name="客户名", type="text")
步骤3: kdoc.dbt.field.add(table_id=<id>, name="签约金额", type="number")
步骤4: kdoc.dbt.record.add_batch(table_id=<id>, records=[{...}])  ← 必须用批量
返回: https://docs.wps.cn/dbt/<file_id>
```

### 4. 图片 OCR 转 Word（本地 Tesseract）
```
步骤1: kdoc.local.ocr.extract(image_path="invoice.png")  → 结构化文字
步骤2: kdoc.local.docx.generate(content=<ocr_text>, template="receipt")
步骤3: kdoc.file.upload(file_path="output.docx")
返回: https://docs.wps.cn/doc/<file_id>
```

### 5. 生成思维导图/流程图（mermaid-cli）
```
步骤1: kdoc.local.mmd.generate(code="graph TD; A-->B; B-->C", output_format="svg")
步骤2: kdoc.file.upload(file_path="mindmap.svg")
返回: https://docs.wps.cn/file/<file_id>
```

### 6. 本地 HTML 一键上云
```
步骤1: kdoc.file.upload(file_path="report.html")
步骤2: kdoc.office.convert(file_id=<file_id>, target_format="pdf")  ← 可选
返回: https://docs.wps.cn/file/<file_id>
```

### 7. 网页剪藏
```
步骤1: kdoc.scrape.url(url="https://example.com/article")
步骤2: kdoc.file.create(name="网页归档", type="doc", content=<scraped_content>)
返回: https://docs.wps.cn/doc/<file_id>
步骤3（可选）: kdoc.notification.send(channel="wecom", ...)  ← 推送通知
```

### 8. 搜索并读取文档
```
步骤1: kdoc.file.search(keyword="合同", limit=10)
步骤2: kdoc.file.info(file_id=<file_id>)   ← 识别品类
步骤3: kdoc.file.content(file_id=<file_id>)
返回: 文档内容
```

### 9. 恢复误删文件（腾讯文档无此功能）
```
步骤1: kdoc.trash.list(limit=20)
步骤2: kdoc.trash.recover(file_id=<file_id>)
返回: 已恢复文件信息
```

### 10. 回滚到历史版本（腾讯文档无此功能）
```
步骤1: kdoc.version.list(file_id=<file_id>)
步骤2: kdoc.version.restore(file_id=<file_id>, version=<target_version>)
返回: 回滚结果
```

### 11. 批量导入 + 推送通知（组合能力）
```
步骤1: kdoc.batch.create(operation="import", file_ids=[...])
步骤2: kdoc.batch.query(task_id=<task_id>)  ← 轮询
步骤3: kdoc.notification.send(channel="wecom", webhook_key=<key>, content="导入完成")
返回: 通知已发送
```

---

## 核心规则（铁律）

1. 🚨 **品类隔离**：通过 `kdoc.file.info` 识别品类后按路由表选择对应工具集。**严禁用 A 品类的工具改 B 品类文档。**
2. 📦 **批量优先**：电子表格/多维表格连续 3 次及以上写入**必须**用批量接口（`kdoc.et.range.write` / `kdoc.dbt.record.add_batch`）。
3. 🔒 **权限前置**：所有写入操作前**必须**调用前置权限校验。
4. 🔄 **异步轮询**：批量任务、格式转换、网页剪藏等异步操作，**必须**使用子会话轮询，主会话保持响应。
5. 🗑️ **软删除**：删除**必须**走回收站 API（`kdoc.file.delete` → 回收站），不物理删除。
6. 📝 **审计日志**：所有写操作**必须**记录到本地审计日志。
7. ⚡ **限流退避**：收到 429 **必须**自动指数退避重试（间隔 2^n 秒 + 随机抖动，最多 5 次）。
8. 🔀 **版本防冲突**：写入前获取 `file.version`，写入时带版本号，冲突时提示用户合并。

---

## 风险项与限制

| 风险项 | 影响 | 规避措施 |
|--------|------|---------|
| 🔑 账号权限未配置 | 无法调用任何 API | 首次使用弹出授权页引导绑定金山开放平台 App |
| 💰 API 配额不足（测试应用 500 次/天） | 写入操作被拒绝 | 提示用户申请正式应用（100,000 次/天） |
| 📝 文字/演示/思维导图/流程图只能整文件替换 | 无法逐段/逐元素编辑 | 自动降级为"本地生成 → 上传覆盖"模式 |
| 🔬 图片 OCR 依赖本地 Tesseract | 识别率受图片质量影响 | 提示用户：扫描件≥200DPI、光线均匀、无反光 |
| 🖼️ 思维导图/流程图输出为 SVG 图片 | 无法在金山文档内二次编辑 | 导出本地 SVG 文件保留源数据 |
| 📦 大文件上传超时（>100MB） | 上传失败 | 自动切换为异步上传 + 进度轮询 |
| 🔀 版本冲突 | 多人同时编辑导致数据丢失 | 写入前校验版本号，冲突时提示手动合并 |
| 📵 网络依赖 | 所有功能需联网 | 关键操作支持离线暂存 |

---

## 🆚 对标腾讯文档 KingDoc v2.3.0

| 对比维度 | 腾讯文档 | KingDoc v2.3.0 | 优势方 |
|---------|---------|----------------|--------|
| 文档品类数 | 9 | 9 | 持平 |
| 文字/演示推荐度 | ⭐⭐ | ⭐⭐⭐ | **KingDoc** |
| 电子表格精细编辑 | ✅ (sheet-mcp) | ✅ (et API) | 持平 |
| 多维表格精细编辑 | ✅ (smartsheet.*) | ✅ (dbt.*) | 持平 |
| 智能文档 (smartcanvas) | ✅ (MDX 格式) | ✅ (DOCX 格式) | 持平 |
| Word/PPT 精细编辑 | ✅ (doc-mcp/slide-mcp) | ⚠️ (整文件替换) | 腾讯 |
| 图片 OCR 文字 | ✅ (ocr.extract) | ✅ (本地 Tesseract) | 持平 |
| 图片→Word/Excel | ✅ (ocr.toword/toexcel) | ✅ (OCR+本地生成) | 持平 |
| 网页剪藏 | ✅ (scrape_url) | ✅ (Playwright 抓取) | 持平 |
| HTML 一键上云 | ✅ (aipage_pack.js) | ✅ (上传+格式转换) | 持平 |
| 思维导图 | ✅ (create_mind_by_markdown) | ✅ (mermaid-cli→SVG) | 持平 |
| 流程图 | ✅ (create_flowchart_by_mermaid) | ✅ (mermaid-cli→SVG) | 持平 |
| ❌ **回收站** | ❌ 无 | ✅ (trash.*) | **KingDoc** |
| ❌ **版本历史** | ❌ 无 | ✅ (version.*) | **KingDoc** |
| ❌ **格式转换** | ❌ 无 | ✅ (office.convert) | **KingDoc** |
| ❌ **纯文本提取** | ❌ 无 | ✅ (office.extract) | **KingDoc** |
| ❌ **通知推送** | ❌ 无 | ✅ (notification.*) | **KingDoc** |
| ❌ **Webhook 事件监听** | ❌ 无 | ✅ (dbt.webhook.*) | **KingDoc** |
| ❌ **批量异步任务** | ❌ 无标准机制 | ✅ (batch.*) | **KingDoc** |
| MCP 服务拆分 | 4 独立 MCP | 统一 MCP | 腾讯 |
| 评分 | 4.6 优秀 | **4.8-5.0 目标** | **KingDoc** |

---

## 四大 MCP 服务（v2.3.0 架构）

为对标腾讯文档的 4 独立 MCP 服务架构，KingDoc 同样拆分为 4 个独立 MCP 服务：

| 服务名 | 工具前缀 | 职责 | 对标腾讯 |
|--------|---------|------|---------|
| `kingdoc-docs` | `kdoc.file.*` / `kdoc.folder.*` / `kdoc.space.*` / `kdoc.trash.*` / `kdoc.version.*` / `kdoc.batch.*` / `kdoc.notification.*` / `kdoc.user.*` | 通用文件管理 + 回收站 + 版本 + 批量 + 通知 + 用户 | tencent-docs |
| `kingdoc-docx` | `kdoc.local.docx.*` | 智能文档/文字文档/思维导图/流程图 本地生成 + 上传覆盖 + 本地 OCR | doc-mcp |
| `kingdoc-pptx` | `kdoc.local.pptx.*` | 演示文稿 本地生成 + 上传覆盖 | slide-mcp |
| `kingdoc-sheet` | `kdoc.et.*` / `kdoc.dbt.*` / `kdoc.form.*` | 电子表格/多维表格/收集表 API 精细编辑 | sheet-mcp |

> 注：4 个 MCP 服务共享同一 Token（KingDoc OAuth），但可独立限流、独立降级。

---

## 错误码

| 错误码 | 含义 | 解决方案 |
|--------|------|---------|
| KD001 | Token 鉴权失败 | 重新执行 `setup.sh` 授权 |
| KD002 | 权限不足 | 升级应用权限或联系管理员 |
| KD003 | 配额不足 | 申请提额或购买配额 |
| KD004 | 文档类型不匹配 | 执行 `kdoc.file.info` 确认品类后按路由表 |
| KD005 | 文档不存在 | 检查 `file_id` 是否正确 |
| KD006 | 限流触发（429） | 自动指数退避重试 |
| KD007 | 版本冲突 | 获取最新版本后重新写入 |
| KD008 | 文件过大 | 走异步上传 |
| KD009 | 文件类型被拦截 | 检查 MIME 类型，可执行文件禁止上传 |
| KD010 | 服务暂时不可用 | 稍后重试或联系支持 |
| KD011 | 参数错误 | 检查 file_id、content 等必填参数 |
| KD012 | 文件夹不存在 | 检查 `folder_id` 是否正确 |
| KD013 | 表单已截止 | 收集表已过截止日期 |
| KD014 | Webhook 回调失败 | 检查回调 URL 是否可访问 |
| KD015 | 转换失败 | 格式不支持或文件损坏 |

---

## 🔄 自动更新提示

**每天首次使用 KingDoc 时自动检查更新。** 发现新版本时，AI 会主动提示您升级，不会自动安装。

```bash
# 手动检查更新
python -m engine.update_check --version 2.3.0
```

---

## 📋 更新历史

### v2.3.0 — 2026-07-05
**品类补齐（对标腾讯文档 1:1）**
- ✅ 新增**智能文档**品类（smart_note），对标腾讯 smartcanvas，Markdown→DOCX→自动排版
- ✅ 新增**思维导图**品类（mindmap），对标腾讯 mind，mermaid-cli 渲染→SVG 上传
- ✅ 新增**流程图**品类（flowchart），对标腾讯 flowchart，mermaid-cli 渲染→SVG 上传
- 品类总数：6 → **9**，完全对齐腾讯文档

**能力补齐（对标腾讯文档 1:1）**
- ✅ 新增**本地 Tesseract OCR**：图片→文字提取 / 图片→Word / 图片→Excel，对标腾讯 ocr.* 三件套
- ✅ 新增**网页剪藏**：Playwright 抓取网页→创建文档，对标腾讯 scrape_url
- ✅ 新增**HTML 一键上云**：本地 HTML 上传 + 格式转换，对标腾讯 aipage_pack.js + manage.async_import

**架构优化**
- 🔧 MCP 服务拆分：1→4 独立服务（kingdoc-docs/docx/pptx/sheet），对标腾讯 4+1 MCP 架构
- 🔧 各服务可独立限流、独立降级，大厂级架构设计

**体验优化**
- 🔧 SKILL.md 新增「安装 Tesseract OCR」步骤和「本地 HTML 一键上云」工作流
- 🔧 9 品类全部 ⭐⭐⭐，推荐度对齐腾讯最高分
- 🔧 新增对标对比表，直观展示对腾讯文档的覆盖和超越

---

### v2.2.0 — 2026-07-02（未发布）
-（内部版本，直接升级到 v2.3.0）

---

### v2.1.0 — 2026-07-02
- 新增每日自动更新检查提示
- 新增文档纯文本提取 API
- 新增多维表格 Webhook 事件监听
- 新增批量异步任务
- SKILL.md 首次使用必读引导

### v2.0.0 — 2026-07-02
- 初始版本：6 品类 + 40+ MCP 工具 + 5 层安全防御

---

## 详细文档参考

| 文档 | 路径 |
|------|------|
| 鉴权流程 | `references/auth.md` |
| 多维表格 API | `references/dbt_references.md` |
| 电子表格 API | `references/et_references.md` |
| 文本提取/格式转换 | `references/office_references.md` |
| 限流策略 | `references/rate_limit.md` |
| 安全设计 | `references/security.md` |

---

## 安装说明

**前置要求**：
- Python 3.10+
- 金山开放平台 App（AppID + AppSecret）
- （可选）Tesseract OCR — 图片识别场景

**快速安装**：
```bash
# Linux / macOS
bash setup.sh

# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File setup.ps1
```

安装完成后重启 WorkBuddy 即可生效。

---

*最后更新：2026-07-05 | v2.3.0*
