---
name: kingdoc
displayName: 金山文档 KingDoc
slug: kingdoc
version: 3.6.0
description: >
  金山文档 AI 协作助手 — 7 品类在线文档全生命周期管理
  （文档/电子表格/演示文稿/多维表格/收集表/可视化/附件），
  深度直连金山文档（WPS）开放平台原生 API，覆盖腾讯文档全部能力 + 金山独有 14 项增强
  （回收站、版本历史、格式转换、纯文本提取、本地 Tesseract OCR、通知推送、Webhook、
  批量任务、政企合规、硬件自适应性能、WPS AI 能力、协同冲突解决、文档合规检查、
  实时协同编辑、文档对比、WPS AI 深度集成、模板市场）。文字/演示/可视化采用"本地生成→上传覆盖"，
  电子表格/多维表格采用 API 精细编辑。本地生成、OCR、硬件画像、WPS AI 等能力零密钥可用。
description_zh: "金山文档 AI 协作助手 — 7 品类在线文档全生命周期管理（深度直连 WPS 开放平台 + WPS AI 深度 + 实时协同 + 文档对比 + 模板市场）"
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

### 7️⃣ WPS AI 能力（v3.2.0 新增，本地降级优先）

> WPS AI 目前无公开开发者 API，本模块采用**本地降级 + 自研逻辑**实现，零密钥可用。
> 未来如 WPS AI 开放 API，只需新增后端即可升级，无需改动上层。

| 工具 | 说明 | 操作 |
|------|------|------|
| `kdoc.wps_ai.write` | AI 写作辅助 | polish(润色) / expand(扩写) / shorten(缩写) / continue_write(续写) / rewrite(改写) |
| `kdoc.wps_ai.analyze` | AI 数据分析 | 自然语言提问 → 基础统计 + 公式建议 |
| `kdoc.wps_ai.ppt` | AI PPT 生成 | Markdown 大纲 → 自动生成 PPT |
| `kdoc.wps_ai.read` | AI 阅读助手 | summarize(总结) / qa(问答) / mindmap(思维导图) |
| `kdoc.wps_ai.detect_intent` | 意图检测 | 识别用户输入匹配的 WPS AI 能力 |

**后端策略**：本地降级优先 → 未来可扩展 WPS Open API / COM 自动化 / Web API

---

## 10. 协同编辑冲突解决（v3.3.0 新增，自研 difflib 实现）

> 多人同时编辑同一文档时经常出现冲突（A 修改了第 3 段，B 也修改了第 3 段）。
> 本模块提供**冲突检测 + 智能合并 + 可视化 diff + 解决模板**，零外部依赖。

### 10.1 冲突检测

| 用户意图 | 直接对 AI 说 |
|---------|-------------|
| 检测冲突 | `「检测这两人修改的冲突」` |
| 查看差异 | `「对比这两个版本的差异」` |
| 自动合并 | `「帮我合并这两个版本」` |
| 保留某版本 | `「保留 A 的版本」` / `「保留 B 的版本」` |

### 10.2 工具列表

| 工具 | 说明 | 操作 |
|------|------|------|
| `kdoc.conflict.detect` | 冲突检测 | 输入基准版+A版+B版 → 返回冲突块列表+统计 |
| `kdoc.conflict.merge` | 智能合并 | 无冲突段自动合并，冲突段标注 `<<<<<<< VERSION_A` |
| `kdoc.conflict.diff` | 冲突可视化 | 生成 Git diff 风格结构化数据 + 可选 HTML |
| `kdoc.conflict.resolve` | 冲突解决 | keep_a / keep_b / manual / auto_merge |

### 10.3 工作流程

```
① 检测：kdoc.version.list → 取最近 2-3 个版本 → conflict.detect() → 冲突块列表
② 合并：conflict.merge() → 自动合并无冲突段 + 标注冲突段 → 合并建议
③ 可视化：conflict.diff() → Git 风格并排 diff（可导出 HTML）
④ 解决：用户选模板 → conflict.resolve() → ⚠️ 强制确认 → kdoc.file.upload 覆盖回云端
```

### 10.4 解决模板

| 策略 | 说明 |
|------|------|
| `keep_a` | 保留用户 A 的版本 |
| `keep_b` | 保留用户 B 的版本 |
| `manual` | 手动编辑合并版本（需传 `manual_text`） |
| `auto_merge` | 自动合并（仅无冲突段，冲突段保留标记） |

### 10.5 安全约束

- 合并结果覆盖回云端属于「覆盖文件」危险操作，**必须走强制确认铁律**（见第 6 节）
- 冲突段**绝不自动覆盖**，必须用户明确选择
- 大文档 diff 自动分块处理，不拖累电脑（硬件自适应）

---

## 11. 文档内容合规检查（v3.4.0 新增，自研正则+规则引擎）

> 政企客户对文档内容有严格合规要求，手动检查耗时易遗漏。
> 本模块提供**敏感词扫描 + 数据泄露检测 + 格式规范检查 + 密级标注**，零外部依赖。

### 11.1 工具列表

| 工具 | 说明 | 操作 |
|------|------|------|
| `kdoc.compliance.sensitive` | 敏感词扫描 | 输入全文 → 返回命中词+位置+上下文+风险等级 |
| `kdoc.compliance.leak` | 数据泄露检测 | 扫描手机号/身份证号/银行卡号/邮箱 → 风险等级+脱敏显示 |
| `kdoc.compliance.format` | 格式规范检查 | 输入文件路径 → 返回不合规清单（支持 DOCX/PPTX/TXT/MD） |
| `kdoc.compliance.classify` | 密级自动标注 | 输入全文 → 建议密级（公开/内部/秘密/机密） |

### 11.2 工作流程

```
① 敏感词扫描：kdoc.file.content → 取全文 → compliance.sensitive() → 命中列表+位置
② 泄露检测：compliance.leak() → 正则匹配手机/身份证/银行卡/邮箱 → 风险等级
③ 格式检查：kdoc.local.docx 解析 → compliance.format() → 不合规清单
④ 密级标注：compliance.classify() → 关键词+规则 → 建议密级
```

### 11.3 敏感词库管理

- **内置词库**：`references/sensitive_words.txt`（适配中国监管要求）
- **用户黑名单**：`references/user_blacklist.txt`（追加自定义敏感词）
- **用户白名单**：`references/user_whitelist.txt`（跳过误判词）
- **定期更新**：替换 `sensitive_words.txt` 即可，无需改代码

### 11.4 数据泄露检测能力

| 类型 | 正则匹配 | 额外校验 | 风险等级 |
|------|---------|---------|---------|
| 手机号 | 1[3-9]\d{9} | — | high |
| 身份证号 | 18位 | 校验码验证 | critical |
| 银行卡号 | 16-19位 | Luhn 算法 | critical |
| 邮箱地址 | 标准邮箱正则 | — | medium |
| IP地址 | IPv4 | — | low |

### 11.5 格式规范检查

| 检查项 | 规范 | 严重度 |
|--------|------|--------|
| 字体 | 宋体 | warning |
| 字号 | 10-14pt | warning |
| 行距 | 1.5倍行距 | info |
| 页边距 | 2.54cm/3.17cm | info |
| 行长度 | ≤80字符 | info |
| 标题层级 | 长文档必须有 H1 | warning |

### 11.6 密级标注规则

| 密级 | 关键词示例 |
|------|-----------|
| 机密 | 绝密、核心机密、国家安全、军事机密、情报来源 |
| 秘密 | 商业机密、技术机密、客户名单、未公开财报 |
| 内部 | 内部资料、内部通知、仅限内部、不得外传 |
| 公开 | 无匹配关键词 |

---

## 12. 实时协同编辑（v3.5.0 新增，序列 CRDT 自研实现）

> 多人同时编辑同一文档时经常出现冲突（A 修改了第 3 段，B 也修改了第 3 段）。
> v3.3 冲突解决是事后 difflib 合并，本模块升级为**实时 CRDT 协同**，多人同时编辑无冲突。

### 12.1 工具列表

| 工具 | 说明 | 操作 |
|------|------|------|
| `kdoc.realtime.create` | 创建协同文档 | 输入 client_id → 返回文档状态 |
| `kdoc.realtime.insert` | 插入文本 | 输入位置+文本 → 返回操作列表 |
| `kdoc.realtime.delete` | 删除文本 | 输入位置+长度 → 返回操作列表 |
| `kdoc.realtime.get_text` | 获取当前文本 | 输入 client_id → 返回可见文本 |
| `kdoc.realtime.stats` | 获取统计信息 | 输入 client_id → 返回字符数/操作数 |

### 12.2 核心算法：序列 CRDT

- 每个字符带唯一因果 ID（lamport timestamp + client_id + 序列号）
- 插入/删除操作满足交换律，顺序无关
- 删除标记 tombstone（保留因果关系，不真正移除）
- 最终一致性：所有客户端收敛到相同状态
- 无需中央服务器协调（P2P 友好）

### 12.3 工作流程

```
1) kdoc.realtime.create(client_id) → 创建协同文档
2) 用户 A 插入：kdoc.realtime.insert("alice", 0, "Hello")
3) 用户 B 同时插入：kdoc.realtime.insert("bob", 5, " World")
4) 操作自动广播给所有客户端
5) kdoc.realtime.get_text(client_id) → 获取一致文本
```

---

## 13. 文档对比（v3.5.0 新增，复用 difflib 引擎）

> 对应 TOP50「文档对比检测器」，两版文档差异高亮。
> 复用 conflict_resolver.py 的 difflib 引擎，提供面向用户的对比能力。

### 13.1 工具列表

| 工具 | 说明 | 操作 |
|------|------|------|
| `kdoc.compare.diff` | 差异高亮 | 输入两版文本 → 返回差异行+统计+相似度 |
| `kdoc.compare.summary` | 变更摘要 | 输入两版文本 → 返回增删改统计+关键变化 |
| `kdoc.compare.export` | 导出报告 | 输入两版文本 → 返回 Markdown/HTML 报告 |

### 13.2 工作流程

```
1) kdoc.file.content(file_id) → 获取当前版本
2) kdoc.version.list(file_id) → 获取历史版本
3) kdoc.compare.diff(current, history) → 差异高亮
4) kdoc.compare.summary(current, history) → 变更摘要
5) kdoc.compare.export(current, history, format="html") → 导出报告
```

---

## 14. 可视化品类合并（v3.5.0 精简 9→8 品类，v3.6.0 进一步精简为 7 品类）

> 为降低认知门槛、统一渲染管线，v3.6.0 将思维导图和流程图合并为「可视化」品类。

### 14.1 合并前后对比

| 合并前（v3.5.0 8 品类） | 合并后（v3.6.0 7 品类） |
|-------------------------|-------------------------|
| 文档 / 电子表格 / 演示文稿 / 多维表格 / 收集表 / **思维导图** / **流程图** / 附件 | 文档 / 电子表格 / 演示文稿 / 多维表格 / 收集表 / **可视化** / 附件 |

### 14.2 子命令路由

合并后用户仍可用原有表达方式，引擎自动识别子命令：

| 用户表达 | 品类 | 子命令 |
|---------|------|--------|
| "画一个思维导图" | visualization | mindmap |
| "画一个流程图" | visualization | flowchart |
| "画个脑图" | visualization | mindmap |

### 14.3 共享渲染管线

```
用户意图 → 品类路由 → visualization
                              ↓
                    子命令识别：mindmap 或 flowchart
                              ↓
                    共享 mermaid→SVG 渲染管线
                              ↓
                        上传为在线文档
```

### 14.4 引擎逻辑不变

- 底层仍调用 `engine/local/generators.py` 的 `MindmapGenerator` / `FlowchartGenerator`
- 渲染方式仍为 mermaid→SVG→上传覆盖
- 仅改品类元数据（`engine/categories.py`）+ 路由表

---

## 15. WPS AI 深度集成（v3.2 本地降级 → v3.6 段落级 AI 操作）

> v3.2 已实现全文级 AI 写作辅助（polish/expand/shorten），v3.6 升级为**段落级 AI 深度集成**。

### 15.1 工具列表

| 工具 | 说明 | 操作 |
|------|------|------|
| `kdoc.wps_ai.rewrite` | AI 段落改写 | formal/casual/concise/elaborate |
| `kdoc.wps_ai.summarize` | AI 段落总结 | 提取核心要点 |
| `kdoc.wps_ai.continue` | AI 段落续写 | 根据方向继续写作 |

### 15.2 工作流程

```
1) 用户在编辑器中选中段落
2) 触发 AI 操作（改写/总结/续写）
3) 适配器路由到本地降级后端
4) 返回处理结果 → 用户确认 → 替换原段落
5) 未来 WPS AI API 开放后，切换为原生后端，无需改上层代码
```

### 15.3 后端策略

```
当前（v3.6）：本地降级占位（返回原文+提示）
未来：WPS AI 开放 API → 升级为原生后端（实现 WpsAiDeepBackend 接口即可）
```

---

## 16. 文档模板市场（v3.6.0 新增，行业模板库一键复用）

> 降低文档创建门槛，提供行业模板库 + 变量替换 + 一键生成。

### 16.1 工具列表

| 工具 | 说明 | 操作 |
|------|------|------|
| `kdoc.template.list` | 列出所有可用模板 | 可按类别筛选 |
| `kdoc.template.search` | 搜索模板 | 按关键词搜索 |
| `kdoc.template.use` | 使用模板 | 变量替换生成文档 |
| `kdoc.template.refresh` | 刷新模板仓库 | git pull |

### 16.2 模板仓库结构

```
templates/
├── meeting.md          # 会议纪要模板
├── weekly-report.md    # 周报模板
├── project-plan.md     # 项目计划模板
├── contract.md         # 合同模板
├── pitch-deck.md       # 融资路演模板
└── ...
```

### 16.3 变量替换

模板使用 `{{变量名}}` 语法，使用时传入变量字典：

```yaml
---
name: weekly-report
category: 工作汇报
description: 标准周报模板
---

# {{title}}
> 作者：{{author}} | 日期：{{date}}

## 本周完成
{{completed}}

## 下周计划
{{plan}}

## 风险与风险
{{risks}}
```

调用：`kdoc.template.use("weekly-report", {"title": "周报", "author": "张三", ...})`

### 16.4 工作流程

```
1) kdoc.template.list() → 列出可用模板
2) 用户选择模板 → kdoc.template.use(name, variables)
3) 引擎替换变量 → 生成 Markdown → 保存到 output/
4) 返回生成内容 + 文件路径
5) 可选：上传为在线文档
```

---

## 17. 完整场景案例（v3.0.0 新增）

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

### 场景 F：多人协作冲突解决（v3.3.0 新增）
```
1) kdoc.version.list(file_id) → 获取最近 3 个版本（基准版 + A修改 + B修改）
2) kdoc.conflict.detect(base, a, b) → 检测冲突块
3) kdoc.conflict.merge(base, a, b) → 自动合并无冲突段 + 标注冲突段
4) kdoc.conflict.diff(a, b) → Git 风格可视化
5) 用户选择保留A/保留B/手动合并 → kdoc.conflict.resolve(strategy="keep_a")
6) ⚠️ 强制确认 → kdoc.file.upload 覆盖回云端
```

### 场景 G：政企文档合规检查（v3.4.0 新增）
```
1) kdoc.file.content(file_id) → 取全文
2) kdoc.compliance.sensitive(text) → 扫描敏感词（命中"反动"、"毒品"等）
3) kdoc.compliance.leak(text) → 检测数据泄露（手机号/身份证号脱敏）
4) kdoc.compliance.classify(text) → 建议密级（如"秘密"）
5) kdoc.compliance.format(file_path) → 格式规范检查（字体/字号/行距）
6) 生成合规报告 → 用户确认 → 修复不合规项
```

### 场景 H：实时协同编辑（v3.5.0 新增）
```
1) kdoc.realtime.create("alice") → Alice 创建协同文档
2) kdoc.realtime.insert("alice", 0, "项目计划：") → Alice 插入文本
3) kdoc.realtime.insert("bob", 5, "第一阶段") → Bob 同时插入
4) kdoc.realtime.get_text("alice") → Alice 看到合并后的文本
5) kdoc.realtime.stats("alice") → 查看协同统计
```

### 场景 I：文档对比（v3.5.0 新增）
```
1) kdoc.file.content(file_id) → 获取当前版本
2) kdoc.version.list(file_id) → 获取历史版本
3) kdoc.compare.diff(current, history) → 差异高亮
4) kdoc.compare.summary(current, history) → 变更摘要
5) kdoc.compare.export(current, history, format="html") → 导出 HTML 报告
```

### 场景 J：7 品类智能路由（v3.6.0 更新）
```
1) 用户说"帮我写一份智能文档" → kdoc.category_resolve("智能文档")
   → {category: "doc", sub_type: "smart_note", edit_method: "local_generate_upload"}
2) 用户说"画一个思维导图" → kdoc.category_resolve("思维导图")
   → {category: "visualization", sub_command: "mindmap", edit_method: "local_render_upload"}
3) 用户说"画一个流程图" → kdoc.category_resolve("流程图")
   → {category: "visualization", sub_command: "flowchart", edit_method: "local_render_upload"}
4) kdoc.category_list() → 列出全部 7 品类
```

### 场景 K：WPS AI 段落改写（v3.6.0 新增）
```
1) 用户在编辑器中选中段落
2) kdoc.wps_ai.rewrite(paragraph="这个方案很好，值得推广。", style="formal")
   → 返回改写后的段落（本地降级占位，API 开放后升级为原生）
3) 用户确认 → 替换原段落
```

### 场景 L：模板市场一键生成（v3.6.0 新增）
```
1) kdoc.template.list() → 列出所有可用模板
2) kdoc.template.search("周报") → 搜索周报模板
3) kdoc.template.use("weekly-report", {"title": "周报", "author": "张三"})
   → 变量替换 → 生成 Markdown → 保存到 output/
4) kdoc.file.upload(output_path) → 上传为在线文档
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

## 更新日志

| v3.6.0 | 2026-08-16 | 增加：文档模板市场引擎 `engine/template_marketplace.py`（git 仓库管理模板，支持 list/search/use/refresh，变量替换一键生成）；增加：WPS AI 深度集成（段落级 AI 操作：rewrite/summarize/continue，本地降级占位，API 开放后升级为原生）；增加：可视化品类合并 `engine/categories.py`（8→7 品类，合并 mindmap+flowchart→visualization，共享 mermaid 渲染管线）；增加：MCP 工具 7 个（kdoc.template.* 4 个、kdoc.wps_ai.* 3 个）；增加：可视化品类合并/WPS AI 深度集成/模板市场场景案例；优化：品类路由表从 8→7，引擎逻辑不变 |
| v3.5.0 | 2026-08-08 | 增加：实时协同编辑引擎 `engine/realtime_collab.py`（序列 CRDT 自研实现，零第三方依赖）；增加：文档对比模块 `engine/doc_comparator.py`（复用 difflib，差异高亮+变更摘要+导出）；增加：品类元数据 `engine/categories.py`（9 品类精简为 8 品类，合并 doc+smart_note，子类型自动识别）；增加：MCP 工具 12 个（kdoc.realtime.* 5 个、kdoc.compare.* 3 个、kdoc.category.* 2 个、kdoc.file.* 品类路由更新）；增加：实时协同+文档对比+8 品类智能路由场景案例；优化：品类路由表从 9→8，引擎逻辑不变 |
| v3.4.0 | 2026-07-30 | 增加：文档内容合规检查模块 `engine/compliance_check.py`（自研正则+规则引擎，零第三方依赖）；增加：敏感词扫描 `kdoc.compliance.sensitive`（内置词库+用户黑白名单）、数据泄露检测 `kdoc.compliance.leak`（手机号/身份证号/银行卡号/邮箱，Luhn+校验码验证）、格式规范检查 `kdoc.compliance.format`（DOCX/PPTX/TXT/MD）、密级自动标注 `kdoc.compliance.classify`（公开/内部/秘密/机密）；增加：合规检查 MCP 工具 4 个；增加：敏感词库 `references/sensitive_words.txt`、格式规范 `references/format_spec.md`、用户黑白名单模板；增加：政企文档合规检查场景案例 |
| v3.3.0 | 2026-07-21 | 增加：协同编辑冲突解决模块 `engine/conflict_resolver.py`（自研 difflib 实现，零第三方依赖）；增加：冲突检测 `kdoc.conflict.detect`、智能合并 `kdoc.conflict.merge`（自动合并无冲突段 + 标注冲突段）、Git diff 可视化 `kdoc.conflict.diff`、解决模板 `kdoc.conflict.resolve`（keep_a/keep_b/manual/auto_merge）；增加：冲突解决 MCP 工具 4 个；增加：大文档 diff 分块硬件自适应处理；增加：多人协作冲突解决场景案例；优化：冲突段强制用户确认，绝不自动覆盖 |
| v3.2.0 | 2026-07-17 | 增加：WPS AI 能力适配层（写作辅助/数据分析/PPT 生成/阅读助手），本地降级优先、自研逻辑实现、零密钥可用；增加：WPS AI 适配器 `engine/wps_ai/adapter.py`；增加：本地降级后端 `engine/wps_ai/backends/local_fallback.py`；增加：能力定义与意图映射 `engine/wps_ai/capabilities.py`；增加：WPS AI API 调研记录 `engine/wps_ai/research_notes.md`；优化：MCP Server 注册 5 个 WPS AI 工具；优化：版本号 3.0.0→3.2.0 |
| v3.1.0 | 2026-07-15 | 增加：wps-office-suite 互通方案调研（已废弃，因平台合规不允许双 skill 互通） |
| v3.0.0 | 2026-07-12 | 增加：危险操作强制确认铁律与确认清单（删除/彻底删除/覆盖/批量/权限/清空回收站/版本回滚/Webhook）；增加：禁止文件类型扩展至完整 35 类（执行脚本/Office 二进制/归档镜像/系统文件/风险脚本）；增加：用户上传拦截与技能内部生成豁免白名单；增加：`engine/hardware.py` 硬件自适应性能调度（自动采集 CPU/内存，自动分配并发子进程数与批量分块）；增加：本地 OCR 模块 `engine/local/ocr.py`（优先本地 Tesseract，降级云端，给安装指引）；增加：能力边界与失败场景专章；增加：自然语言触发示例专章；增加：完整场景案例专章（5 个端到端场景）；增加：FAQ 专章（8 个高频问题）；补齐：缺失参考文档 `et_references.md`/`office_references.md`/`rate_limit.md`；补齐：技能图标 `assets/icon.png`；补齐：`engine/__init__.py` 与 `engine/api/mcp_server.py`（真实 MCP Server 入口）；优化：MCP Server 深度直连金山文档开放平台原生 API；优化：每日更新提醒 + 反馈邮箱 `njskills@agent.qq.com` |
| v2.3.0 | 2026-07-05 | 增加：智能文档/思维导图/流程图 3 品类，品类总数 6→9；增加：本地 Tesseract OCR；增加：网页剪藏；增加：HTML 一键上云；优化：MCP 服务拆分 1→4，独立限流/降级 |
| v2.1.0 | 2026-07-02 | 增加：每日自动更新检查；增加：纯文本提取 API；增加：多维表 Webhook 事件监听；增加：批量异步任务；增加：SKILL.md 首次使用必读引导 |
| v2.0.0 | 2026-07-02 | 初始版本发布：6 品类 + 40+ MCP 工具 + 5 层安全防御 |

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
