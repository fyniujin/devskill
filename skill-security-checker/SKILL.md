---
slug: skill-security-checker
displayName: Skill 安全审计扫描器
name: skill-security-checker
description: 'Skill Security — 安全审计扫描器，帮助你快速发现 Skill 中的安全风险。静态扫描（提示注入/命令注入/SSRF/凭证外泄/路径遍历/危险函数）、依赖漏洞审计、权限审计、质量评分、动态沙箱执行扫描（Docker/Windows Sandbox）、JSON/HTML 报告生成。'
version: 2.0.0
tags: ['security', 'audit', 'skill', 'scanner', 'code-analysis', 'vulnerability']
icon: '🔒'
author: 'njskills'
license: 'MIT'
allowed-tools: 'Bash,Read'
metadata:
  agent_created: true
  schema_version: '1.0'
  release_date: '2026-07-22'
  stability: 'stable'
---

# Skill Security

> 一键扫描 Skill 安全风险，发布前最后一道安全闸门。

## 概述

本工具用于对 **WorkBuddy / ClawHub / SkillHub** 平台上发布的安全技能进行全方位安全合规扫描。它能帮你快速找出代码中的安全漏洞、不安全的依赖项、过度授权的权限配置，并以直观的评分等级和修复建议输出结果。

**适用场景：**

- 发布 Skill 前的安全检查
- 评估第三方 Skill 的安全性
- CI/CD 流水线中的自动化审查
- Skill 质量评估与改进

## 核心功能

### 1. 静态扫描

检测 Skill 文件中的安全漏洞：

| 风险类型 | 检测内容 | 严重度 |
|---------|---------|--------|
| 提示注入 | 越狱指令、"忽略原始指令"、"覆盖系统提示"等文本 | 🔴 严重 |
| 命令注入 | curl/wget 管道执行、反引号替换、$() 中执行 shell | 🔴 严重 |
| SSRF/内网访问 | `127.0.0.1`、`10.x.x.x`、`192.168.x.x` | 🟠 高危 |
| 凭证外泄 | 硬编码 API Key、Token、Password、Bearer Token | 🔴 严重 |
| 路径遍历 | `../`、URL 编码绕过、绝对路径访问 | 🟠 高危 |
| 危险函数 | `eval()`、`exec()`、`os.system()`、`pickle.load()` | 🟡 中等 |

### 2. 依赖漏洞审计

扫描 `requirements.txt`、`package.json`、`Pipfile`、`pyproject.toml` 等依赖文件，与内置的已知 CVE 漏洞库比对。

目前覆盖 **26** 个常见高危依赖的已知漏洞：
`requests`、`urllib3`、`flask`、`django`、`numpy`、`pillow`、`pyyaml`、`jinja2`、`cryptography`、`aiohttp`、`tqdm`、`setuptools`、`node-fetch`、`minimist`、`lodash`、`axios`、`express`、`vue`、`react`、`webpack`、`moment`、`npm`、`tough-cookie`、`word-wrap`、`protobuf`、`eslint`

### 3. 权限审计

检查 `allowed-tools` 声明是否有过度授权：

- 声明了 Bash 但 description 中无对应使用场景 → 🟡 中等告警
- Bash + Write 同时授权 → 🟠 高危告警
- Bash + Exec 同时授权 → 🟠 高危告警
- Bash + Read + Write + Edit 全量授权 → 🟠 高危告警

### 4. 质量评分

检查 SKILL.md 文档的完整性：

| 检查项 | 要求 |
|--------|------|
| 必要字段 | `name`、`description`、`version` |
| 命名规范 | kebab-case（小写字母+数字+连字符） |
| description 长度 | 20-1024 字符 |
| 版本号格式 | 语义化版本 (e.g., `1.0.0`) |
| 硬编码路径 | 检测 `D:\` 等绝对路径 |
| 错误处理 | 文档中需提及异常处理策略 |

### 5. 结构检查

- 文件数量 ≤ 200
- 总大小 ≤ 10MB
- 缺少 README.md 时提醒

### 6. 硬件感知并行（新增）

自动检测当前设备的 CPU 核心数和可用内存，动态调整并发工作线程数（1-8 线程），在扫描速度和系统性能之间取得平衡。

**检测逻辑：**
- CPU 核心数 ÷ 2 = 最大线程数
- 可用内存 < 2GB 时，线程数减半

### 7. 更新检查（新增）

工具运行时会自动检查 GitHub 上的新版本，发现更新时会在结果中提示用户升级。

- ✅ 内置 **24 小时缓存**，避免频繁请求
- ✅ 新增 `--skip-update` 参数可完全关闭此功能
- ✅ 所有网络请求仅获取版本号，不下载任何内容

### 8. `# nosec` 内联排除规则（新增）

如果你确认某行代码是安全的，但触发了误报，可在该行末尾添加 `# nosec` 注释，扫描器将自动跳过该行。

```python
# 这行会被扫描器跳过
os.system('ls')  # nosec
```

### 9. 动态沙箱执行扫描（新增）

静态扫描只能看代码，恶意代码却可以通过**动态下载、加密载荷、条件触发**绕过。动态沙箱在**隔离环境中实际运行** Skill 脚本，捕获运行时行为，检出静态扫描完全无法发现的恶意动作。

**隔离后端（自动选择）：**

| 后端 | 说明 | 隔离手段 |
|------|------|---------|
| Docker | 首选，行为捕获最完整 | `--network=none` 默认断网、只读挂载、CPU/内存/PID 限额、`--cap-drop ALL` |
| Windows Sandbox | Win10/11 专业版可用 | 运行时生成 `.wsb` 配置（断网 + 只读映射） |
| 降级模式 | 无隔离环境时 | 仅做静态扫描并提示「建议在沙箱环境中进行动态扫描」 |

**行为捕获维度：**

- 网络请求（目标 IP / 域名 / 端口）
- 文件读写（路径 / 模式）
- 进程创建（命令行）
- 环境变量读取
- 动态代码执行（exec / compile）

**异常行为标记：**

| 异常行为 | 严重度 |
|---------|--------|
| 访问敏感路径（`~/.ssh`、`/etc/passwd`、`.aws`、`id_rsa` 等） | 🔴 严重 |
| 网络活动 + 动态执行同时出现（疑似下载并执行远程载荷） | 🔴 严重 |
| 向未知目标外联（非白名单域名） | 🟠 高危 |
| 创建 shell / 解释器进程（bash、sh、powershell、cmd） | 🟠 高危 |
| 读取疑似密钥环境变量（token、secret、apikey 等） | 🟡 中等 |

**网络隔离与白名单：** 沙箱默认**完全断网**；如脚本确需联网，可用 `--allow-domain` 逐个放行可信域名，其余外联一律标记为高危。

> ⚠️ 动态扫描为**可选功能**，需显式加 `--dynamic` 开启。若本机无 Docker / Windows Sandbox，工具会自动降级为纯静态扫描并给出提示，不会报错。

## 使用方法

### 基本用法（命令行）

```bash
# 扫描一个 Skill 目录（文本输出）
python D:\skill\skill-security-checker\scripts\audit.py "D:\skill\你的技能名"

# 生成 JSON 报告
python D:\skill\skill-security-checker\scripts\audit.py "D:\skill\你的技能名" --format json

# 生成 HTML 报告并保存为文件
python D:\skill\skill-security-checker\scripts\audit.py "D:\skill\你的技能名" --format html -o report.html

# 跳过更新检查
python D:\skill\skill-security-checker\scripts\audit.py "D:\skill\你的技能名" --skip-update

# 开启动态沙箱执行扫描（需 Docker 或 Windows Sandbox）
python D:\skill\skill-security-checker\scripts\audit.py "D:\skill\你的技能名" --dynamic

# 动态扫描 + 放行白名单域名 + 自定义超时（秒）
python D:\skill\skill-security-checker\scripts\audit.py "D:\skill\你的技能名" --dynamic --allow-domain api.github.com --sandbox-timeout 60
```

### 参数快查

| 参数 | 说明 | 默认 |
|------|------|------|
| `skill_path` | 待扫描的 Skill 目录（必填） | — |
| `--format` | 输出格式：`text` / `json` / `html` | `text` |
| `-o, --output` | 报告输出文件路径 | 打印到终端 |
| `--skip-update` | 跳过更新检查 | 关闭 |
| `--dynamic` | 开启动态沙箱执行扫描 | 关闭 |
| `--allow-domain` | 放行白名单域名（可重复） | 无（默认断网） |
| `--sandbox-timeout` | 沙箱执行超时（秒） | 30 |

### 在 WorkBuddy 中触发

直接告诉 WorkBuddy，触发词覆盖面广：

- **「安全审计」+ 技能路径** → `帮我安全审计 D:\skill\my-skill`
- **「扫描」+ Skill** → `扫描这个 skill 有没有安全问题`
- **「发布前检查」+ 技能名** → `发布前帮我检查一遍 my-skill`
- **「安全检测」+ 路径** → `帮我对这个路径做一份安全检测`
- **「代码审计」+ 文件夹** → `对 D:\skill\project 做代码审计`
- **「Skill 安全吗」** → `这个 skill 安全吗`

## 输出说明

### 评分等级

评分从 100 分开始扣分，不同等级对应不同发布建议：

| 等级 | 分数区间 | 发布建议 | 含义 |
|------|---------|---------|------|
| 🟢 A | 90-100 | ✅ 可安全发布 | 优秀 |
| 🟣 B | 75-89 | ⚠️ 建议修复后发布 | 良好 |
| 🟡 C | 60-74 | ⚠️ 需要修复 | 一般 |
| 🟠 D | 40-59 | ❌ 不建议发布 | 较差 |
| 🔴 F | 0-39 | ❌ 禁止发布 | 危险 |

### 严重度分类

- 🔴 **严重**（-25 分/个）：提示注入、命令注入、凭证外泄 → 必须立即修复
- 🟠 **高危**（-15 分/个）：SSRF、路径遍历、危险权限组合 → 建议尽快修复
- 🟡 **中等**（-8 分/个）：危险函数、权限过度授权、description 过短 → 建议修复
- 🔵 **低危**（-3 分/个）：命名规范问题、缺少错误处理说明 → 建议优化
- ⚪ **信息**（0 分）：更新版本提示、参考信息 → 仅供参考

### 返回码（for CI/CD 集成）

| 退出码 | 含义 | CI 行为建议 |
|--------|------|------------|
| 0 | 无问题或仅低危 | ✅ 通过 |
| 1 | 存在中等问题 | ⚠️ 警告 |
| 2 | 存在严重/高危问题 | ❌ 失败，阻断发布 |

## 扫描排除规则

以下内容将被自动跳过，不参与扫描，不计入风险：

### 自动排除的文件类型

1. **可执行/脚本**：`.bat`、`.cmd`、`.ps1`、`.vbs`、`.exe`、`.dll`、`.msi`、`.sh`、`.com`、`.scr`、`.hta`、`.reg`
2. **Office 文档**：`.docx`、`.xlsx`、`.pptx`、`.doc`、`.xls`、`.ppt`、`.xlsm`、`.docm`、`.pptm`
3. **压缩包/镜像**：`.iso`、`.dmg`、`.zip`、`.rar`、`.7z`、`.tar`、`.gz`、`.apk`、`.jar`
4. **缓存/隐藏**：`.DS_Store`、`.pyc`、`.pyo`、`.so`、`.swp`、`.env`、`.log`、`.tmp`

### 自动排除的目录

`__pycache__`、`.git`、`.venv`、`.pytest_cache`、`node_modules`、`.idea`、`.vscode`

## 扫描示例

```
============================================================
  Skill Security Audit Report
============================================================
  Skill: my-cool-skill
  Path: D:\skill\my-cool-skill
  Time: 2026-07-13T14:32:10
  Files: 15 scanned, 2 skipped
============================================================

  Score: 82/100 (Grade: B)
  Found 2 medium issues.

  ──────────────────────────────────────────────────────────
  [MED]   quality_check     SKILL.md         Missing version field
  [MED]   quality_check     SKILL.md         No error handling mentioned
  ──────────────────────────────────────────────────────────

  Fix suggestions:
    [quality_check] Add version field in frontmatter
    [quality_check] Add error handling docs in SKILL.md

  Feedback: njskills@agent.qq.com
============================================================
```

## 常见问答（FAQ）

**Q: 扫描会很慢吗？需要联网吗？**
A: 扫描本身不会慢。工具会自动检测你的 CPU 核心数和可用内存，动态调整并行数（1-8 线程），在本地离线完成扫描，不联网也不会影响结果。可选的更新检查（24 小时缓存）可以通过 `--skip-update` 关闭。

**Q: 扫描结果为 F 等级怎么办？**
A: 请按照输出的修复建议逐一修复问题，特别是严重和高危问题。修复后可重新扫描确认分数是否提升。常见修复步骤：
1. 移除所有硬编码的敏感信息（API Key、Password 等）→ 添加到 `.env` 或环境变量
2. 避免使用 `eval()`/`exec()`/`os.system()` → 使用 `subprocess.run()` 并关闭 `shell=True`
3. 确保所有依赖升级到安全版本（见报告中建议的版本号）
4. 清理硬编码的内网 IP，改用域名或环境变量

**Q: 报告说发现了命令注入，但我只是在说明文档中写了代码示例？**
A: 代码示例中如果包含了 curl、wget、shell 等相关关键词，会被模式匹配命中。这是预期行为——**请在代码示例末尾添加 `# nosec` 注释**即可跳过该行。

**Q: 这个工具支持扫描 Python 以外的文件吗？**
A: 支持。除了 `.py` 文件，还可以扫描 `.js`、`.ts`、`.json`、`.yaml`、`.md`、`.html` 等所有文本格式文件。Office 文档和可执行文件会被自动跳过。

**Q: 检测出误报怎么办？**
A: 主要有两种方式：
1. **临时方案**：在代码行末尾添加 `# nosec` 注释
2. **永久方案**：联系 njskills@agent.qq.com 提供误报规则详情（文件路径和匹配模式），我们会优化规则

**Q: 用于公司 CI/CD 流水线，需要安装什么依赖吗？**
A: 不需要。本工具只需要 **Python 3.8+** 标准库，无第三方依赖。可集成到 GitHub Actions、GitLab CI、Jenkins 等任意 CI 平台。（注：动态扫描 `--dynamic` 需额外具备 Docker 或 Windows Sandbox 环境。）

**Q: 我没有 Docker，能用动态扫描吗？**
A: 可以直接加 `--dynamic`，工具会自动探测环境。若无 Docker / Windows Sandbox，会自动降级为纯静态扫描并提示「建议在沙箱环境中进行动态扫描」，不会报错。想获得完整行为捕获，推荐安装 Docker Desktop。

**Q: 动态扫描会不会有风险？会不会拖慢我电脑？**
A: 动态扫描在隔离环境中运行：Docker 用 `--network=none` 断网 + 只读挂载 + CPU/内存/PID 限额；Windows Sandbox 断网 + 只读映射。默认单次超时 30 秒，CPU 上限自动取核心数的一半，不会拖慢日常使用。被扫描代码无法接触你的真实文件系统和网络。

## 安全声明

- **默认只做静态分析，不会执行被扫描的代码**（静态模式仅读取文件，不写入）
- **动态扫描（`--dynamic`）需显式开启**，且仅在隔离环境（Docker / Windows Sandbox）中执行被扫描代码，沙箱**默认断网**、只读挂载、CPU/内存限额，绝不在宿主机直接运行
- **不会上传任何文件内容到外部服务器**
- **更新检查仅获取 GitHub Release 标题，不下载任何附件**
- **所有扫描在本地完成，保护你的代码隐私**
- Windows Sandbox 的 `.wsb` 配置在运行时动态生成到临时目录，用完即删，不写入 Skill 仓库

## 反馈与支持

如有误报反馈、规则改进建议或功能需求，欢迎联系：

📧 **njskills@agent.qq.com**

你的反馈将直接帮助我们升级规则库，完善检测能力。

## 更新日志

| v2.0.0 | 2026-07-22 | 增加：动态沙箱执行扫描模块，在 Docker 或 Windows Sandbox 隔离环境中实际运行脚本捕获运行时行为；增加：网络请求、文件读写、进程创建、环境变量读取、动态代码执行五类运行时行为捕获；增加：敏感路径访问、未知目标外联、下载并执行远程载荷、shell 进程创建、密钥环境变量读取五类异常行为标记；增加：沙箱默认断网与 --allow-domain 域名白名单机制；增加：--dynamic、--allow-domain、--sandbox-timeout 三个命令行参数；增加：无 Docker/Windows Sandbox 时自动降级为纯静态扫描并给出提示；优化：报告 meta 区展示动态扫描后端与行为统计 |
| v1.3.0 | 2026-07-13 | 修复：base64 编码的命令注入模式中有两个模式解码后正则表达式括号不匹配导致扫描报错；修复：CVE 列表中 protobuf 的 CVE 编号错误；增加：24 小时缓存的更新检查机制避免频繁联网请求；增加：# nosec 内联注释排除规则降低误报；优化：依赖库覆盖范围从 17 个扩展到 26 个常见高危依赖；优化：错误信息改为更友好的中文提示；优化：扫描输出显示优化减少信息密度过高的问题；优化：新增详细说明文档和常见问答
| v1.2.0 | 2026-07-13 | 增加：硬件感知并行度自动调整功能，根据 CPU/内存动态分配线程数；增加：更新检查功能自动提示新版本；优化：依赖审计支持 pyproject.toml 和 Pipfile 格式；修复：凭证外泄检测正则表达式中转义字符导致扫描崩溃的问题
| v1.1.0 | 2026-07-13 | 增加：依赖漏洞审计模块；增加：质量评分维度（包含 SKILL.md 完整性检查）；优化：评分算法改为按严重度区分扣分权重；优化：HTML 报告增加统计卡片和响应式布局
| v1.0.0 | 2026-07-13 | 初始版本发布，包含静态扫描、权限审计、结构检查、JSON/HTML 报告生成
