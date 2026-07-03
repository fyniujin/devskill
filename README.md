# 🎒 Skills Monorepo

> 一个仓库管理所有 Skills，配合 GitHub Actions 实现「改哪个发布哪个」。

---

## 📦 Skill 索引

| 技能 | 路径 | 最新版本 | 描述 |
|------|------|----------|------|
| contract-review | `contract-review/SKILL.md` | v1.0.0 | 对中文合同进行智能风险审查，识别条款风险、提取关键信息、生成审查报告，覆盖买卖/技术/租赁/劳动等常见合同类型。 |
| dgngjx-skill | `dgngjx-skill/SKILL.md` | v2.5.0 | 多功能免费工具箱 - 图片处理、PDF转换、数据换算、文本工具、开发工具、视频工具、教育、生活娱乐。48%零开箱即用，52%需确认安装。v2.0 国内联网... |
| gov-procurement-analyst | `gov-procurement-analyst/SKILL.md` | v3.0.0 | 政府采购全流程智能分析助手。覆盖商机发现、投标决策、文件编制、供应商背调、合规审计、 中标跟踪、资质管理、政策咨询、保证金管理、质疑投诉、合同分析、验收辅... |
| kingdoc | `kingdoc/SKILL.md` | v2.1.0 | 金山文档 AI 协作助手 — 6 品类在线文档全生命周期管理 （文字/电子表格/演示文稿/多维表格/收集表/附件），覆盖创建、编辑、 管理、权限、版本历史... |
| multi-agent-orchestrator | `multi-agent-orchestrator/SKILL.md` | v1.0.0 | 支持多Agent流水线编排（采集→分析→报告），基于DAG调度实现跨技能状态共享、错误重试、断点续传和执行报告生成。AI即编排器，脚本提供基础设施。 |
| tax-receipt-compliance | `tax-receipt-compliance/SKILL.md` | v2.7.0 | 财税合规全链路助手：发票OCR识别→真伪查验→报销单自动填充→对接审批系统。企业自主配置，数据本地处理。 |
| winskill | `winskill/SKILL.md` | v1.6.0 | Windows 服务器运维工具箱 - 磁盘分析、临时文件清理、IIS 站点管理、批量文件操作、服务状态监控、Windows Update 诊断、实时性能监... |
| wps-office-suite | `wps-office-suite/SKILL.md` | v2.2.0 | WPS Office 全家桶 - 四引擎（WPS/MS Office/LibreOffice/纯Python）智能识别用户已安装软件，AI助手零学习成本，... |
| zwjh-skill | `zwjh-skill/SKILL.md` | v1.6.0 | 会思考的进化 AI — 能像人一样理解问题本质、关联上下文、主动发现隐含需求，自动修复并持续成长。不仅能解决表面问题，更能触达根本原因，实现真正的主动进化。 |

> ⚠️ 此表由 GitHub Actions 在发布时自动更新，请勿手动编辑。

---

## 🚀 快速开始

### 添加新技能

1. 在仓库根目录创建一个文件夹，以技能名命名
2. 文件夹内必须包含 `SKILL.md`（技能入口文件）
3. 可选包含 `scripts/`、`references/`、`assets/` 等子目录
4. 提交代码，GitHub Actions 会自动检测并发布

### 技能目录结构

```
your-skill-name/
├── SKILL.md          # 必须 - 技能入口文件
├── scripts/          # 可选 - 脚本文件
├── references/       # 可选 - 参考资料
└── assets/           # 可选 - 静态资源
```

---

## 🔄 自动发布流程

```
git push → GitHub Actions 触发
  → 检测哪些 skill 文件夹有变更
  → 为有变更的 skill 创建/更新 GitHub Release
  → 自动更新本 README.md 的技能索引表
```

---

## 📝 更新历史

---

*最后更新：2026/7/3 10:19:51*
