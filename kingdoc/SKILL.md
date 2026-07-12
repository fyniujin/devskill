---
name: kingdoc
displayName: 金山文档 KingDoc
slug: kingdoc
version: 3.0.0
description: >
  金山文档 AI 协作助手 — 9 品类在线文档全生命周期管理
  （智能文档/文字/电子表格/演示文稿/多维表格/收集表/思维导图/流程图/附件），
  深度直连金山文档（WPS）开放平台原生 API，覆盖腾讯文档全部能力 + 金山独有 10 项增强
  （回收站、版本历史、格式转换、纯文本提取、本地 Tesseract OCR、通知推送、Webhook、
  批量任务、政企合规、硬件自适应性能）。文字/演示/思维导图/流程图采用"本地生成→上传覆盖"，
  电子表格/多维表格采用 API 精细编辑。本地生成、OCR、硬件画像等能力零密钥可用。
description_zh: "金山文档 AI 协作助手 — 9 品类在线文档全生命周期管理（深度直连 WPS 开放平台）"
category: 办公效率
platforms: [WorkBuddy, QClaw, ima, Claude Code, Cursor]
tags: [文档处理, 表格处理, PPT生成, 多维表格, 表单收集, 思维导图, 流程图, OCR, 政企合规]
license: MIT
requires_api_key: true
icon: assets/icon.png
---

# KingDoc — 金山文档 AI 协作助手 v3.0.0

> 对标腾讯文档 TENCENT DOCS，功能 1:1 覆盖 + 差异化增强。
> **v3.0.0 重点：深度直连在线文档原生 API、危险操作强制确认、硬件自适应性能、免密钥本地能力。**

---

## 📣 评测反馈与本轮（v3.0.0）优化说明

本版本针对第三方评测（综合 4.5/5「优秀」）的降分项做了**逐项闭环**：

| 评测降分点 | v3.0.0 优化 |
|-----------|------------|
| 某些危险操作缺强制确认，可能误操作 | 新增「危险操作强制确认」铁律与确认清单（见第 6、12 节） |
| 高级功能需额外装 Tesseract | 本地 OCR **免密钥**优先；未装 Tesseract 时降级云端，都无则给安装指引 |
| 首次配置需 App Key，对新手复杂 | 明确「本地生成/OCR/硬件画像零配置可用」；云端仅上传/协作需 Key |
| 能力边界说明少（大文件/失败场景） | 新增「能力边界与失败场景」专章（第 13 节） |
| 触发方式不清晰（高级功能怎么说） | 新增「自然语言触发示例」专章（第 5 节） |
| FAQ 不丰富、找不到答案 | 新增 FAQ 专章（第 25 节），安全/错误集中可查 |
| 缺完整场景案例 | 新增「完整场景案例」专章（第 11 节） |
| 创造性/增值不足 | 新增硬件自适应性能调度、网页剪藏、批量任务、Webhook 等增值能力 |
| 性能可能拖累电脑 | 新增硬件自动采集 + 自动分配并发子进程数（第 17 节） |

---

## ⚠️ 首次使用必读

### 1. 申请金山开放平台 App（免费，仅云端协作需要）

**只影响「上传到云端 / 多人协作 / 回收站 / 版本」等联网能力。**
本地生成文档、本地 OCR、硬件画像**完全不需要 Key，开箱即用**。

申请步骤：
1. 访问 [金山开放平台](https://developer.kdocs.cn) 并登录金山文档账号
2. 进入「应用管理」→「创建应用」，获取 **`App ID`** 和 **`App Secret`**
3. 勾选权限（OAuth Scope）：
   - 必须：`user:file:write`、`user:file:read`、`team:file:write`、`team:file:read`
   - 建议：`user:team:read`、`user:notification:write`
4. 测试阶段限速 500 次/天，正式版 10 万次/天

### 2. （可选）安装本地 Tesseract OCR

仅「图片文字提取」需要；未装则自动降级云端 OCR 或给指引，**不影响其他功能**。

```bash
# Windows
winget install UB-Mannheim.TesseractOCR
# macOS
brew install tesseract tesseract-lang
# Linux
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
```

### 3. 配置并加载

```bash
# Linux/macOS
bash setup.sh
# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File setup.ps1
```
脚本引导输入 App ID/Secret，自动生成 `config.json`、`mcp-config.json`、模板与图标，并采集本机硬件画像。

---

## 快速开始

| 你想做什么 | 直接对 AI 说 |
|-----------|-------------|
| 新建会议纪要 | `"帮我写一份会议纪要"` |
| 创建数据表 | `"建一个销售数据表格，含产品/销量/金额"` |
| 生成 PPT | `"帮我做一份产品发布 PPT"` |
| 生成思维导图 | `"画一个项目计划的思维导图"` |
| 生成流程图 | `"画一个用户下单流程图"` |
| 看文档内容 | `"看看这个文档说了什么"` |
| 搜文件 | `"搜一下上个月的合同"` |
| 上传本地文件 | `"把这个 PDF 上传到云端"` |
| 识别图片文字 | `"把这张发票的文字提取出来"` |
| 恢复误删 | `"回收站里有没有昨天删的 Word？"` |
| 回滚版本 | `"这份文档改坏了，回退到上周版本"` |
| 分享权限 | `"给张三发个可编辑的链接"` |
| 归档文件夹 | `"把文件移到 2026 项目文件夹"` |
| 格式转换 | `"把这份文档转成 PDF"` |

---

## 5. 自然语言触发示例（高级功能怎么表达）

为避免「不知道怎么开口」，以下给可直接说的话：

- **批量建表**：`"新建客户管理多维表格，字段：客户名(文本)、签约金额(数字)、状态(单选)，并一次写入 20 条记录"`
- **格式转换**：`"把《Q2 报告》导出成 PDF"` / `"转成 Word 发我"`
- **OCR 转文档**：`"识别这张发票图片，生成一份 Word 报销单"` / `"把这张表格图片转成在线电子表格"`
- **网页剪藏**：`"把这个网页 https://... 收藏成金山文档"` 
- **通知推送**：`"导入完成后用企微机器人通知我"` 
- **版本回滚**：`"列出这份文档的历史版本，回退到 7 月 1 日那版"` 
- **权限管理**：`"给团队文件夹『2026 项目』里的文档设置只读"` 
- **本地免密钥生成**：`"本地生成一份周报 DOCX，不用上传"`（无需 App Key）

---

## 安全声明

| 保护项 | 方式 |
|--------|------|
| 🔒 删除确认 | 删除走回收站 API，不物理删除 |
| 🗑️ 软删除+恢复 | `trash.list → trash.recover` |
| 📝 版本冲突检测 | 写入前获取最新版本号，冲突时提示用户合并 |
| 🔐 权限前置校验 | 所有写入操作前自动检查权限，无权限拒绝 |
| ⚡ 限流保护 | 429 自动指数退避重试（最多 5 次） |
| 🛡️ 文件类型拦截 | 默认禁止上传 .exe/.bat/.ps1/.zip 等（见第 18 节） |
| 🔑 Token 安全 | Token 仅存在于内存，不落盘 |
| 📋 审计日志 | 所有写操作记录到本地日志 |
| 🔀 批量合并 | 50ms 窗口内连续写入自动合并为一次请求 |
| 🧠 硬件自适应 | 自动按本机 CPU/内存分配并发，不拖累电脑（第 17 节） |

---

## 6. 🚨 危险操作强制确认（v3.0.0 新增铁律）

> 评测指出「部分危险操作缺少强制确认」。以下操作**执行前必须向用户显式确认**，
> 列出具体影响，待用户明确同意后方可进行；**绝不**静默执行。

| 危险操作 | 确认内容（必须展示给用户） |
|---------|--------------------------|
| 删除文件 `kdoc.file.delete` | 文件名 + 大小 + 「将进入回收站，可恢复」 |
| **彻底删除** `kdoc.trash.destroy` | 文件名 + 「**不可逆**，将永久丢失」⚠️ 二次确认 |
| 覆盖文件 `kdoc.file.upload` | 原文件版本 + 「覆盖后旧内容进入版本历史」 |
| 批量操作 `kdoc.batch.*` | 操作类型 + 文件数量 + 文件清单预览 |
| 权限变更 `kdoc.file.permission` | 目标成员 + 授予/收回的权限 |
| 清空回收站 | 数量 + 「**不可恢复**」⚠️ |
| 回滚版本 `kdoc.version.restore` | 目标版本 + 「当前内容将被历史版本替换」 |
| Webhook 设置 | 回调 URL + 监听事件清单 |

**确认模式**（config.json 可配）：
```json
{ "safety": { "confirm_mode": "dangerous", "dry_run": false, "audit_enabled": true } }
```
- `dangerous`（默认）：仅上表危险操作需确认
- `always`：所有写操作均确认
- `dry_run: true`：只展示将要执行的操作，不真正调用

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
| 思维导图 | mindmap | ⭐⭐⭐ | ✅ 自动 | ✅ 本地渲染+上传 | mind | mermaid→SVG→上传 |
| 流程图 | flowchart | ⭐⭐⭐ | ✅ 自动 | ✅ 本地渲染+上传 | flowchart | mermaid→SVG→上传 |
| 附件 | attachment | ⭐⭐⭐ | ✅ 自动 | — | — | 本地文件直接上传 |

---

## 核心能力矩阵

### 1️⃣ 文档创建（9 品类全覆盖）

| 用户意图 | 品类 | 创建方法 | 编辑方法 |
|---------|------|---------|---------|
| 报告/笔记/文章/纪要/markdown | smart_note / doc | `kdoc.file.create` | `kdoc.local.docx.generate` → 上传覆盖 |
| PPT/幻灯片 | ppt | `kdoc.file.create` | `kdoc.local.pptx.generate` → 上传覆盖 |
| 数据表格/Excel | sheet | `kdoc.et.create` | `kdoc.et.*` 精细编辑 |
| 多维表格 | smartsheet | `kdoc.dbt.create` | `kdoc.dbt.*` 精细编辑 |
| 表单/问卷 | form | `kdoc.form.create` | `kdoc.form.*` 配置 |
| 思维导图 | mindmap | `kdoc.local.mindmap.generate` → 上传 | 生成 SVG→上传覆盖 |
| 流程图 | flowchart | `kdoc.local.flowchart.generate` → 上传 | 生成 SVG→上传覆盖 |
| 上传文件/图片/pdf | attachment | `kdoc.file.upload` | — |

### 2️⃣ 文档编辑（改内容）

先 `kdoc.file.info` 确定品类，再路由对应工具集。**严禁跨品类操作。**

| 原始文档类型 | 编辑工具集 | 编辑粒度 |
|------------|-----------|---------|
| 智能文档/文字 | `kdoc.local.docx.generate` → 上传覆盖 | 整文件替换（自动重排） |
| 演示文稿 | `kdoc.local.pptx.generate` → 上传覆盖 | 整文件替换 |
| 电子表格 | `kdoc.et.cell.write` / `kdoc.et.range.write` | **单元格级** ✅ |
| 多维表格 | `kdoc.dbt.record.*` / `kdoc.dbt.field.*` | **记录级** ✅ |
| 收集表 | `kdoc.form.*` 配置 | 表单配置级 |
| 思维导图/流程图 | `kdoc.local.mmd.generate` → 上传覆盖 | 整文件替换 |

### 3️⃣ 文件管理

| 动作 | 工具 |
|------|------|
| 重命名/移动/删除/复制 | `kdoc.file.*` |
| 导入（本地→云端） | `kdoc.file.upload` |
| 导出（云端→本地） | `kdoc.file.download` |
| 权限/分享链接 | `kdoc.file.permission` / `kdoc.share.*` |
| 回收站查询/恢复 | `kdoc.trash.list` / `kdoc.trash.recover` |
| 版本历史/回滚 | `kdoc.version.list` / `kdoc.version.restore` |
| 批量操作 | `kdoc.batch.create` → `kdoc.batch.query` |
| 空间管理 | `kdoc.space.*` / `kdoc.folder.*` |

### 4️⃣ 格式转换与 OCR

| 场景 | 工具 | 实现方式 |
|------|------|---------|
| 文档→PDF/Word/Excel/PPT | `kdoc.office.convert` | 金山 API |
| 纯文本提取 | `kdoc.office.extract` | 金山 API |
| 图片 OCR 文字提取 | `kdoc.local.ocr.extract` | **本地 Tesseract（免密钥）/ 云端降级** |
| 图片→Word | `kdoc.local.docx.generate(image_ocr=true)` | OCR→生成 DOCX→上传 |
| 图片→Excel | `kdoc.et.create(data=ocr_table)` | OCR→解析表格→写入 |
| 网页剪藏 | `kdoc.scrape.url` → `kdoc.file.create` | 抓取→创建文档 |
| HTML 一键上云 | `kdoc.scrape.html` → `kdoc.file.upload` | 读取本地 HTML→上传 |

### 5️⃣ 扩展能力（金山独有）

| 能力 | 工具 | 说明 |
|------|------|------|
| 通知推送 | `kdoc.notification.send` | 企微/钉钉/金山协作机器人 |
| 多维表格 Webhook | `kdoc.dbt.webhook.set` | 事件驱动监听表格变更 |
| 空间额度用量 | `kdoc.space.quota` | 企业级管理视角 |
| 用户信息 | `kdoc.user.info` | 获取用户/团队信息 |

### 6️⃣ 本地免密钥工具（无需 App Key）

| 工具 | 说明 |
|------|------|
| `kdoc.local.docx.generate` | 本地生成 DOCX（会议纪要/周报/合同） |
| `kdoc.local.pptx.generate` | 本地生成 PPTX |
| `kdoc.local.mindmap.generate` | 本地渲染思维导图 SVG |
| `kdoc.local.flowchart.generate` | 本地渲染流程图 SVG |
| `kdoc.local.ocr.extract` | 本地 OCR 提取图片文字 |
| `kdoc.local.hardware.profile` | 采集本机硬件 + 推荐并发数 |

---

## 11. 完整场景案例（v3.0.0 新增）

### 场景 A：月度销售复盘（全链路）
```
1) kdoc.et.create(name="2026-07 销售复盘")
2) kdoc.et.range.write(sheet_id, "A1:C21", 表头+20 行数据)   ← 批量写入
3) kdoc.et.formula.set(sheet_id, "D2", "=C2*0.1")            ← 提成列
4) kdoc.office.convert(file_id, "pdf")                       ← 导出 PDF
5) kdoc.notification.send(channel="wecom", content="复盘已生成")
```

### 场景 B：合同 OCR → 在线文档（免密钥本地优先）
```
1) kdoc.local.ocr.extract("contract.jpg")        ← 本地 Tesseract，无需 Key
2) kdoc.local.docx.generate(content=<ocr_text>, template="contract")
3) kdoc.file.upload(file_path="output.docx")     ← 上传为在线文档
```

### 场景 C：项目规划脑图 + 流程图（本地渲染）
```
1) kdoc.local.mindmap.generate(code="graph TD; 目标-->阶段1; 阶段1-->任务A")
2) kdoc.local.flowchart.generate(code="flowchart TD; 开始([开始])-->审核{通过?}")
3) 分别 kdoc.file.upload 两个 SVG → 在线可视化
```

### 场景 D：误删恢复（金山独有）
```
1) kdoc.trash.list(limit=20)
2) kdoc.trash.recover(file_id)        ← 救回，不丢数据
```

### 场景 E：大批量导入（硬件自适应）
```
1) kdoc.local.hardware.profile → 取得 workers/batch_chunk
2) 按 batch_chunk 分块调用 kdoc.batch.create
3) kdoc.batch.query 轮询直至完成（并发不超过 workers，不卡机）
```

---

## 12. 核心规则（铁律）

1. 🚨 **品类隔离**：先 `kdoc.file.info` 识别品类再路由，**严禁跨品类操作**。
2. 📦 **批量优先**：电子表格/多维表格连续 3+ 写入**必须**用批量接口。
3. 🔒 **权限前置**：所有写入前**必须**校验权限。
4. 🔄 **异步轮询**：批量/转换/剪藏**必须**子会话轮询，主会话保持响应。
5. 🗑️ **软删除**：删除**必须**走回收站 API，不物理删除。
6. 📝 **审计日志**：所有写操作**必须**记录本地审计日志。
7. ⚡ **限流退避**：收到 429 **必须**自动指数退避（最多 5 次）。
8. 🔀 **版本防冲突**：写入前获取 `version`，冲突时提示合并。
9. ✅ **危险操作强制确认**（v3.0.0）：见第 6 节，**未确认不执行**。
10. 🧠 **性能不拖累**：批量/渲染并发**不得超过** `kdoc.local.hardware.profile` 给出的 `workers`。

---

## 13. 能力边界与失败场景（v3.0.0 新增，务必看清）

| 场景 | 会发生什么 | 应对 |
|------|-----------|------|
| 未配置 App Key | 所有 `*云端*` 工具返回 KD001 友好提示 | 改用 `kdoc.local.*` 免密钥工具 |
| 文件 > 大文件阈值（默认 100MB，低端机 50MB） | 自动转异步上传 + 进度轮询；超限报 KD008 | 压缩或分卷 |
| 多人同时编辑 | 写入带版本号，冲突报 KD007 | 拉最新版本→合并→重写 |
| OCR 识别率低 | 扫描件需 ≥200DPI、光线均匀、无反光 | 提升清晰度或人工校对 |
| 网络中断 | 自动重试（指数退避），关键操作支持离线暂存 | 稍后重试 |
| 限流 429 | 自动退避，不会崩溃 | 等待后继续 |
| 本地未装 Tesseract | OCR 降级云端（需 Key），都无则给安装指引 | 装 Tesseract（免费） |
| 超大表格（>10 万行） | 分块写入，单批不超过 `batch_chunk` | 分批 |
| 思维导图/流程图为 SVG 图片 | 无法在金山内二次编辑，保留源 mermaid | 改源码重渲染 |
| 文字/演示只能整文件替换 | 无法逐段编辑 | 本地改源→重新上传覆盖 |

**明确不支持**：本地直接修改已上传 DOCX/PPTX 的某一段（需整文件重生成）；
对加密/损坏文件 OCR；超过配额的非付费批量操作。

---

## 14. 风险项与限制

| 风险项 | 影响 | 规避 |
|--------|------|------|
| 账号权限未配置 | 无法调用任何 API | 首次使用引导绑定 App |
| API 配额不足（测试 500/天） | 写入被拒 | 申请正式应用（10 万/天） |
| 整文件替换限制 | 文字/演示无法逐段编辑 | 降级为「本地生成→上传覆盖」 |
| OCR 依赖清晰度 | 识别率受图片质量影响 | 提示扫描件 ≥200DPI |
| SVG 不可二次编辑 | 脑图/流程图为图片 | 导出本地 SVG 保留源 |
| 大文件超时（>阈值） | 上传失败 | 异步上传 + 轮询 |
| 版本冲突 | 多人编辑丢数据 | 写入前校验版本号 |
| 网络依赖 | 云端功能需联网 | 关键操作离线暂存 |

---

## 15. 深度绑定在线文档（v3.0.0 强化）

KingDoc **直连金山文档（WPS）开放平台原生 API**（`https://developer.kdocs.cn/api/v1/openapi`），
而非简单桥接：

- **原生能力全覆盖**：文件/文件夹/回收站/版本/权限/空间/通知/用户均调用官方端点。
- **精细编辑**：电子表格走 `et` API（单元格/公式），多维表格走 `dbt` API（记录/字段/视图）。
- **本地增强**：文字/演示/脑图/流程图用本地库生成**原生格式**（DOCX/PPTX/SVG）后上传覆盖，
  既保真又免去服务端复杂排版。
- **政企可用**：国内网络直连、文档全中文、权限模型对齐企业协作。

---

## 16. 四大 MCP 服务（v3.0.0 架构）

| 服务名 | 工具前缀 | 职责 | 对标腾讯 |
|--------|---------|------|---------|
| `kingdoc-docs` | `kdoc.file.*` / `folder.*` / `space.*` / `trash.*` / `version.*` / `batch.*` / `notification.*` / `user.*` | 文件管理+回收站+版本+批量+通知+用户 | tencent-docs |
| `kingdoc-docx` | `kdoc.local.docx.*` | 文字/智能文档/脑图/流程图 本地生成+上传+OCR | doc-mcp |
| `kingdoc-pptx` | `kdoc.local.pptx.*` | 演示文稿 本地生成+上传 | slide-mcp |
| `kingdoc-sheet` | `kdoc.et.*` / `kdoc.dbt.*` / `kdoc.form.*` | 表格/多维表/收集表 API 精细编辑 | sheet-mcp |

> 4 个 MCP 服务共享同一 Token，可独立限流、独立降级。

---

## 17. 性能与硬件自适应（v3.0.0 新增，绝不拖累电脑）

`engine/hardware.py` 在首次运行时**自动采集本机 CPU 核数/内存**并计算出安全并发：

| 机器档位 | 并发子进程 `workers` | 批量分块 | 大文件阈值 |
|---------|---------------------|---------|-----------|
| 低端（≤2核/<4GB） | 1 | 50 | 50MB |
| 普通 | min(核数,4) | 200 | 100MB |
| 高端（≥8核/≥16GB） | min(核数,8) | 500 | 100MB |

- 画像缓存到 `.kingdoc_hardware_profile.json`（30 分钟复用），不频繁探测。
- 批量写表、脑图/流程图并行渲染**不得超过 `workers`**，保证用户电脑流畅。
- AI 在执行批量/渲染任务前应调用 `kdoc.local.hardware.profile` 读取参数。

```bash
python -m engine.hardware          # 查看本机画像与推荐参数
```

---

## 18. 🚫 禁止上传的文件类型（v3.0.0 强化）

为安全，用户「上传附件」默认拦截以下全部类型（来源：产品安全规范）：

1. **Windows 可执行/批处理**：`.bat` `.cmd` `.ps1` `.vbs` `.exe` `.dll` `.lnk` `.msi`
2. **Office 二进制文档**：`.docx` `.xlsx` `.pptx` `.doc` `.xls` `.ppt` `.xlsm` `.docm` `.pptm`
3. **二进制镜像/安装包**：`.iso` `.dmg` `.zip` `.rar` `.7z` `.tar` `.gz` `.apk` `.jar`
4. **系统缓存/隐藏文件**：`.DS_Store` `.git`（目录） `.env` `.log` `.tmp`
5. **其他风险脚本**：`.sh` `.com` `.scr` `.hta` `.reg`

**内部豁免**：技能「本地生成→上传覆盖」产物（`.docx/.pptx/.xlsx/.pdf/.svg/.png/.txt/.md`
等）经 `internal=True` 通道上传，**仅限技能自身生成**，用户无法借道上传任意同类文件。
命中拦截将抛出 `KD009`。详见 `references/security.md`。

---

## 19. 错误码

| 错误码 | 含义 | 解决方案 |
|--------|------|---------|
| KD001 | Token 鉴权失败 | 重新执行 `setup` 授权（或改用本地免密钥工具） |
| KD002 | 权限不足 | 升级应用权限或联系管理员 |
| KD003 | 配额不足 | 申请提额 |
| KD004 | 文档类型不匹配 | `kdoc.file.info` 确认品类后按路由表 |
| KD005 | 文档不存在 | 检查 `file_id` |
| KD006 | 限流（429） | 自动指数退避重试 |
| KD007 | 版本冲突 | 获取最新版本后重写 |
| KD008 | 文件过大 | 走异步上传 |
| KD009 | 文件类型被拦截 | 见第 18 节禁止类型 |
| KD010 | 服务暂不可用 | 稍后重试 |
| KD011 | 参数错误 | 检查 `file_id`/`content` 等必填项 |
| KD012 | 文件夹不存在 | 检查 `folder_id` |
| KD013 | 收集表已截止 | 已过截止日期 |
| KD014 | Webhook 回调失败 | 检查回调 URL |
| KD015 | 转换失败 | 格式不支持或文件损坏 |

---

## 20. 🔄 自动更新提示与反馈

**每天首次使用自动检查更新**（本地缓存，每天仅查一次，离线不打扰）。
发现新版本时 AI 会主动提示升级，**不会自动安装**：

```bash
# 手动检查 / 仅看提醒文案
python -m engine.update_check --version 3.0.0 --reminder
```

> 📮 **有更好建议**：njskills@agent.qq.com

---

## 21. 📋 更新历史

### v3.0.0 — 2026-07-12（深度优化）
**安全强化**
- 🔧 新增「危险操作强制确认」铁律与确认清单（删除/彻底删除/覆盖/批量/权限/清空回收站/版本回滚/Webhook）
- 🔧 禁止文件类型扩展至完整 35 类（执行脚本/Office 二进制/归档镜像/系统文件/风险脚本），并区分「用户上传拦截」与「技能内部生成豁免」

**性能优化（不拖累电脑）**
- ✅ 新增 `engine/hardware.py`：自动采集 CPU/内存，自动分配并发子进程数与批量分块
- ✅ 批量写表、脑图/流程图渲染并发受 `workers` 上限约束

**免密钥能力**
- ✅ 新增本地 OCR 模块 `engine/local/ocr.py`：优先本地 Tesseract（免费无 key），降级云端，给安装指引
- ✅ 明确「本地生成/OCR/硬件画像零配置可用」，降低开箱即用门槛

**文档与体验（针对评测降分项）**
- ✅ 新增「能力边界与失败场景」专章（大文件/冲突/失败/不支持项）
- ✅ 新增「自然语言触发示例」专章（高级功能怎么说）
- ✅ 新增「完整场景案例」专章（5 个端到端场景）
- ✅ 新增 FAQ 专章（安全/错误集中可查）
- ✅ 补齐缺失参考文档：`et_references.md` / `office_references.md` / `rate_limit.md`
- ✅ 生成技能图标 `assets/icon.png`；补齐 `engine/__init__.py`、`engine/api/mcp_server.py`（真实 MCP Server）

**架构**
- 🔧 深度直连金山文档（WPS）开放平台原生 API，四大 MCP 服务稳定运行
- 🔧 新增每日更新提醒 + 反馈邮箱 `njskills@agent.qq.com`

---

### v2.3.0 — 2026-07-05
- ✅ 新增智能文档/思维导图/流程图 3 品类，品类总数 6→9
- ✅ 新增本地 Tesseract OCR、网页剪藏、HTML 一键上云
- 🔧 MCP 服务拆分 1→4，独立限流/降级

### v2.1.0 — 2026-07-02
- 新增每日自动更新检查、纯文本提取、多维表 Webhook、批量异步任务

### v2.0.0 — 2026-07-02
- 初始版本：6 品类 + 40+ MCP 工具 + 5 层安全防御

---

## 22. 详细文档参考

| 文档 | 路径 |
|------|------|
| 鉴权流程 | `references/auth.md` |
| 多维表格 API | `references/dbt_references.md` |
| 电子表格 API | `references/et_references.md` |
| 文本提取/格式转换 | `references/office_references.md` |
| 限流/性能/硬件自适应 | `references/rate_limit.md` |
| 安全设计 | `references/security.md` |
| 错误码 | `references/error_codes.md` |
| 常见工作流 | `references/workflows.md` |

---

## 23. 安装说明

**前置要求**：Python 3.10+；云端功能需金山开放平台 App（免费）；OCR 可选装 Tesseract。

```bash
# Linux / macOS
bash setup.sh
# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File setup.ps1
```
安装后重启 WorkBuddy 生效。本地生成/OCR/硬件画像无需任何配置即可用。

---

## 24. 📮 反馈与建议

本技能持续迭代。有任何功能建议、问题或更好的实现思路，欢迎反馈：

**📧 有更好建议：njskills@agent.qq.com**

也可在每日更新提醒中一键查看新版本。

---

## 25. ❓ FAQ（v3.0.0 新增）

**Q1：没有金山 App Key 能用吗？**
能。本地生成 DOCX/PPTX、思维导图/流程图 SVG、本地 OCR、硬件画像均零密钥可用；
仅「上传云端/多人协作/回收站/版本」等联网能力需 Key。

**Q2：为什么删除前要确认？**
防止误操作。删除进回收站可恢复；「彻底删除」「清空回收站」为不可逆操作，需二次确认（见第 6 节）。

**Q3：OCR 一定要装 Tesseract 吗？**
首选本地 Tesseract（免费、离线、无 key）。未装时自动降级云端 OCR（需 Key），都无则给出安装指引，不崩溃。

**Q4：大文件传不上去？**
超过阈值（默认 100MB，低端机 50MB）会自动转异步上传 + 轮询；仍失败请压缩或分卷。

**Q5：会不会把我的电脑拖卡？**
不会。技能自动按本机硬件分配并发子进程数（见第 17 节），批量/渲染均受限。

**Q6：报 KD009 文件被拦截？**
你上传的文件属于禁止类型（见第 18 节）。技能自身生成的 docx/pptx/pdf/svg 等不受影响。

**Q7：如何升级？**
每天首次使用会自动提醒；也可 `python -m engine.update_check --version 3.0.0 --reminder`。

**Q8：文字/演示文档能改其中一段吗？**
当前为整文件替换模式：本地改源文件→重新上传覆盖。逐段精细编辑需金山在线编辑器。

---

*最后更新：2026-07-12 | v3.0.0*
