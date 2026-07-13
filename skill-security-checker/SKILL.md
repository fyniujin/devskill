---
slug: skill-security-checker
displayName: Skill 安全审计扫描器
name: skill-security-checker
description: "Skill Security — 对 WorkBuddy/ClawHub/SkillHub 技能进行安全合规扫描。静态扫描（提示注入/命令注入/SSRF/凭证外泄/路径遍历/危险函数）、依赖漏洞审计、权限过度授权检测、质量评分（SKILL.md 完整性/反模式/硬编码路径）、一键加固建议、JSON/HTML 报告生成。支持硬件感知并行扫描，自动检测 CPU/内存调整并发数。触发词：安全审计、skill 扫描、代码审计、安全检测、检查 skill、skill 安全、发布前检查。"
version: "1.2.0"
tags: ["security", "audit", "skill", "scanner", "code-analysis", "vulnerability", "compliance"]
icon: "🔒"
author: "njskills"
license: "MIT"
schema_version: "1.0"
platforms: ["WorkBuddy", "ClawHub", "SkillHub"]
trigger:
  - "安全审计"
  - "skill 扫描"
  - "代码审计"
  - "安全检测"
  - "检查这个 skill"
  - "skill 安全吗"
  - "发布前检查"
  - "skill audit"
permission:
  - "文件系统访问"
dependency:
  - "Python 3.8+"
allowed-tools: "Bash,Read"
pricing: "免费"
category: "meta"
metadata:
  release_date: "2026-01-13"
  stability: "stable"
---

# 🔒 Skill Security

> 一键扫描你的 Skill，发布前发现安全风险。

## 📌 概述

对 WorkBuddy / ClawHub / SkillHub 平台上发布的技能（Skill）进行全面安全合规扫描，输出评分报告和修复建议。

**适用场景：**

- 发布 Skill 前的安全闸门检查
- 对已安装的第三方 Skill 进行安全审计
- CI/CD 流水线中的自动化安全审查
- Skill 质量评估和改进

## 🔧 核心功能

### 1. 静态扫描

检测以下安全风险：

| 风险类型 | 检测内容 | 严重度 |
|---------|---------|--------|
| 提示注入 | 包含「忽略先前指令」「覆盖系统提示」等越狱类指令文本 | 🔴 严重 |
| 命令注入 | 管道连接curl/wget与Shell、eval执行用户输入、反引号命令替换等 | 🔴 严重 |
| SSRF/内网访问 | `127.0.0.1`、`10.x.x.x`、`192.168.x.x`、`localhost` | 🟠 高危 |
| 凭证外泄 | 硬编码 API Key、Secret、Token、Password | 🔴 严重 |
| 路径遍历 | `../`、`/etc/passwd`、`..%2f`、绝对路径穿越 | 🟠 高危 |
| 危险函数 | `eval()`、`exec()`、`os.system()`、`shell=True`、`pickle.load` | 🟡 中等 |

### 2. 依赖审计

扫描 `requirements.txt`、`package.json`、`Pipfile`、`pyproject.toml` 中的第三方依赖，与已知漏洞库（CVE）比对。

目前覆盖 17 个常见高危依赖的已知漏洞：
`requests`、`urllib3`、`flask`、`django`、`numpy`、`pillow`、`pyyaml`、`jinja2`、`cryptography`、`aiohttp`、`tqdm`、`setuptools`、`node-fetch`、`minimist`、`lodash`、`axios`、`express`

### 3. 权限审计

检查 `allowed-tools` 声明是否过度授权：

- 检测危险权限组合（Bash+Write、Bash+Exec+Read+Edit）
- 检测声明了 Bash 但描述中无对应使用场景
- 提示遵循最小权限原则

### 4. 质量评分

检查 SKILL.md 的完整性：

- 必要字段：`name`、`description`、`version`
- 命名规范：kebab-case、长度 ≤50 字符
- description 质量：长度 20-1024 字符
- 反模式检测：硬编码路径、缺少错误处理

### 5. 结构检查

- 文件数量 ≤200、总大小 ≤10MB
- 缺少 README.md 提醒

### 6. 硬件感知并行

自动检测用户 CPU 核心数和可用内存，动态调整并行工作线程数（1-8），避免拖累用户电脑。

### 7. 更新检查

自动检查 GitHub 上的新版本，发现更新时提示用户。

## 🚀 使用方法

### 基本用法

```bash
# 扫描一个技能目录（文本输出）
python D:\skill\skill-security-checker\scripts\audit.py "D:\skill\your-skill"

# 生成 JSON 报告
python D:\skill\skill-security-checker\scripts\audit.py "D:\skill\your-skill" --format json

# 生成 HTML 报告并保存
python D:\skill\skill-security-checker\scripts\audit.py "D:\skill\your-skill" --format html -o report.html

# 跳过更新检查
python D:\skill\skill-security-checker\scripts\audit.py "D:\skill\your-skill" --skip-update
```

### 在 WorkBuddy 中触发

直接告诉 WorkBuddy：

- "帮我安全审计 D:\skill\my-skill"
- "扫描这个 skill 有没有安全问题"
- "发布前检查 my-skill"
- "/skill-security-checker skill_path"

## 📊 输出说明

### 评分等级

| 等级 | 分数 | 含义 |
|------|------|------|
| 🟢 A | 90-100 | 优秀，可发布 |
| 🟣 B | 75-89 | 良好，建议修复中等问题 |
| 🟡 C | 60-74 | 一般，需要修复 |
| 🟠 D | 40-59 | 较差，不建议发布 |
| 🔴 F | 0-39 | 危险，禁止发布 |

### 严重度分类

- 🔴 **严重**：必须立即修复（提示注入、命令注入、凭证外泄）
- 🟠 **高危**：建议尽快修复（SSRF、路径遍历）
- 🟡 **中等**：建议修复（危险函数、过度权限）
- 🔵 **低危**：建议优化（命名规范、文档完整性）
- ⚪ **信息**：仅供参考

### 返回码

| 退出码 | 含义 |
|--------|------|
| 0 | 无问题或仅低危 |
| 1 | 存在中等问题 |
| 2 | 存在严重/高危问题 |

## ⚠️ 扫描排除规则

### 自动排除的禁止文件类型

以下内容将被自动跳过，不参与扫描：

1. **可执行/脚本**：`.bat`、`.cmd`、`.ps1`、`.vbs`、`.exe`、`.dll`、`.msi`、`.sh`、`.com`、`.scr`、`.hta`、`.reg`
2. **Office 文档**：`.docx`、`.xlsx`、`.pptx`、`.doc`、`.xls`、`.ppt`、`.xlsm`、`.docm`、`.pptm`
3. **压缩包/镜像**：`.iso`、`.dmg`、`.zip`、`.rar`、`.7z`、`.tar`、`.gz`、`.apk`、`.jar`
4. **缓存/隐藏**：`.DS_Store`、`.pyc`、`.pyo`、`.so`、`.swp`、`__pycache__`、`.git` 目录
5. **日志/临时**：`.env`、`.log`、`.tmp`

### 自动排除的目录

`__pycache__`、`.git`、`.venv`、`.pytest_cache`、`node_modules`、`.idea`、`.vscode`

## 🔍 扫描示例

```
============================================================
  🔒 Skill 安全审计报告
============================================================
  技能名称: my-cool-skill
  技能路径: D:\skill\my-cool-skill
  扫描时间: 2026-01-13T14:32:10
  扫描文件: 15 (跳过 2)
============================================================

  📊 评分: 82/100 (等级: B)
  📝 发现 2 个中等问题，建议修复。

  ──────────────────────────────────────────────────────────
  severity category       file                 description
  ──────────────────────────────────────────────────────────
  🟡中等   质量检查       SKILL.md             缺少 version 字段
  🟡中等   质量检查       SKILL.md             未提及错误处理
  ──────────────────────────────────────────────────────────

  💡 修复建议:
    • [质量检查] 在 frontmatter 中添加 version 字段
    • [质量检查] 建议在文档中说明错误处理策略

  📧 建议反馈: njskills@agent.qq.com
============================================================
```

## ❓ 常见问题

**Q: 扫描会很慢吗？**
A: 不会。工具会自动检测你的 CPU 核心数和可用内存，动态调整并行数（1-8 线程），在性能和速度间取得平衡。

**Q: 扫描结果为 F 等级怎么办？**
A: 请按照输出的修复建议逐一修复问题，特别是严重和高危问题。修复后可重新扫描确认。

**Q: 依赖审计需要联网吗？**
A: 当前版本使用内置的已知漏洞数据库进行离线比对，不需要联网。未来版本支持 OSV API 在线查询。

**Q: 误报怎么办？**
A: 部分模式匹配可能存在误报。如果确认是误报，可以在代码中使用注释 `# nosec` 标记跳过。如有疑问请联系 njskills@agent.qq.com。

## 🛡️ 安全声明

- 本工具只做静态分析，**不会执行被扫描的代码**
- 本工具**不会上传任何文件内容**到外部服务器
- 所有扫描在本地完成，保护你的代码隐私
- 工具本身采用最小权限原则，仅读取文件不修改

## 📮 反馈与建议

如有更好的建议或发现问题，请联系：

📧 **njskills@agent.qq.com**

你的反馈将帮助我们改进扫描规则和提升检测精度。

## 更新日志

| v1.2.0 | 2026-01-13 | 增加：硬件感知并行度自动调整功能，根据 CPU/内存动态分配线程数；增加：更新检查功能自动提示新版本；优化：依赖审计支持 pyproject.toml 和 Pipfile 格式；修复：CREDENTIAL_PATTERNS 中正则转义错误导致扫描崩溃的问题 |
| v1.1.0 | 2026-01-10 | 增加：依赖漏洞审计模块；增加：质量评分维度（SKILL.md 完整性检查）；优化：评分算法更合理（区分严重度扣分）；优化：HTML 报告增加统计卡片和响应时间 |
| v1.0.0 | 2026-01-08 | 初始版本发布，包含静态扫描、权限审计、结构检查、JSON/HTML 报告生成 |
