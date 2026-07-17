# KingDoc — 金山文档 AI 协作助手

> 让 AI 直接操作你的金山在线文档，创建、编辑、管理一站搞定。
> **v3.2.0**：深度直连 WPS 开放平台原生 API · WPS AI 能力（写作/分析/PPT/阅读）· 硬件自适应性能 · 免密钥本地能力。

## ✨ 特性

- 📝 **9 品类全覆盖** — 文字/表格/演示/多维表格/收集表/智能文档/思维导图/流程图/附件
- 🔗 **全生命周期** — 创建/编辑/删除/移动/复制/权限/版本历史/回收站
- 🆚 **对标腾讯文档** — 腾讯有的全有，腾讯没有的也有（回收站/版本/转换/OCR/通知）
- 🤖 **WPS AI 能力** — 写作辅助/数据分析/PPT 生成/阅读助手，本地降级优先、零密钥可用
- 🧠 **硬件自适应** — 自动按本机 CPU/内存分配并发，绝不拖累电脑
- 🔓 **免密钥本地能力** — 本地生成 DOCX/PPTX/脑图/流程图、本地 OCR、硬件画像、WPS AI，零配置
- 🛡️ **安全优先** — 软删除/权限前置/限流退避/审计日志/危险操作强制确认/文件类型拦截

## 🚀 快速开始

### 1. 安装

```bash
# Linux / macOS
bash D:\skill\kingdoc\setup.sh
# Windows (PowerShell)
powershell -ExecutionPolicy Bypass -File D:\skill\kingdoc\setup.ps1
```

### 2. 配置 App Key（仅云端协作需要）

从 [金山开放平台](https://developer.kdocs.cn) 获取 AppID + AppSecret，安装脚本引导输入。
**本地生成/OCR/硬件画像/WPS AI 无需 Key。**

### 3. 直接使用

对 WorkBuddy 说：
- "帮我写一份会议纪要" → 本地生成并上传
- "把这个 PDF 传到云端" → 上传（自动拦截禁止类型）
- "这份文档改坏了，回退到上周" → 版本回滚
- "识别这张发票的文字" → 本地 OCR（免密钥）
- "帮我润色这段文字" → WPS AI 写作辅助（免密钥）
- "分析这列数据的趋势" → WPS AI 数据分析（免密钥）
- "根据大纲生成 PPT" → WPS AI PPT 生成（免密钥）
- "总结这份文档" → WPS AI 阅读助手（免密钥）

## 📖 支持的文档类型（9 品类）

| 类型 | 创建 | 编辑 |
|------|------|------|
| 文字/智能文档 | ✅ 自动排版 | ✅ 本地生成+上传覆盖 |
| 电子表格 | ✅ 自动创建 | ✅ 单元格/公式精细编辑 |
| 演示文稿 | ✅ 自动排版 | ✅ 本地生成+上传覆盖 |
| 多维表格 | ✅ 自动创建 | ✅ 记录/字段/视图精细编辑 |
| 收集表 | ✅ 自动创建 | ✅ 配置+答卷管理 |
| 思维导图/流程图 | ✅ 本地渲染 SVG | ✅ 上传覆盖 |
| 附件上传 | ✅ — | — |

## 🤖 WPS AI 能力（v3.2.0 新增）

| 能力 | 工具 | 操作 |
|------|------|------|
| AI 写作辅助 | `kdoc.wps_ai.write` | 润色/扩写/缩写/续写/改写 |
| AI 数据分析 | `kdoc.wps_ai.analyze` | 自然语言提问 → 统计+公式建议 |
| AI PPT 生成 | `kdoc.wps_ai.ppt` | Markdown 大纲 → 自动生成 PPT |
| AI 阅读助手 | `kdoc.wps_ai.read` | 总结/问答/思维导图 |
| 意图检测 | `kdoc.wps_ai.detect_intent` | 识别用户输入匹配的能力 |

> WPS AI 目前无公开开发者 API，采用**本地降级 + 自研逻辑**实现，零密钥可用。
> 未来如 WPS AI 开放 API，只需新增后端即可升级。

## 🧠 性能（不拖累电脑）

首次运行自动采集硬件并分配并发子进程数：

| 机器档位 | 并发子进程 | 批量分块 |
|---------|-----------|---------|
| 低端（≤2核/<4GB） | 1 | 50 |
| 普通 | min(核数,4) | 200 |
| 高端（≥8核/≥16GB） | min(核数,8) | 500 |

## 🚫 安全：禁止上传的文件类型

用户上传默认拦截：`.bat .cmd .ps1 .vbs .exe .dll .lnk .msi`、
`.docx .xlsx .pptx .doc .xls .ppt .xlsm .docm .pptm`、
`.iso .dmg .zip .rar .7z .tar .gz .apk .jar`、
`.DS_Store .git .env .log .tmp`、`.sh .com .scr .hta .reg`。
技能内部生成的 docx/pptx/pdf/svg 等经豁免通道上传。

## 📚 文档

- [SKILL.md](SKILL.md) — 完整功能参考（含 FAQ、能力边界、场景案例）
- [references/security.md](references/security.md) — 安全设计
- [references/rate_limit.md](references/rate_limit.md) — 限流与硬件自适应
- [references/office_references.md](references/office_references.md) — 文本提取/格式转换

## 🔄 更新与反馈

每天首次使用自动提醒更新（不自动安装）。
**有更好建议：njskills@agent.qq.com**

## 📄 协议

MIT License
