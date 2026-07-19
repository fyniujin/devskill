---
slug: privacy-search
displayName: 隐私搜索
name: privacy-search
description: "隐私优先的多引擎并行搜索 Skill，V1.1 提供十大搜索引擎（百度/必应/搜狗/360/DuckDuckGo/Yandex/Startpage/Qwant/Brave/本地SearXNG）+ SimHash去重排序、SearXNG本地实例自动部署（Docker/pip双路径）、隐私模式（normal/strict一键切换，strict 模式国内可用引擎自动降级）、版本更新检查提醒。错误分类诊断（网络/配置/引擎），不污染系统 Python 环境。"
version: 1.1.0
tags: ["privacy", "search", "multi-engine", "duckduckgo", "searxng", "local-first", "simhash", "china-friendly"]
icon: "🔒"
author: "njskills"
license: "MIT"
---

# 隐私搜索（Privacy Search）

隐私优先的多引擎并行搜索 Skill。V1.1 聚焦**国内可用性**和**错误诊断**，新增 5 个国内可用备选引擎，strict 模式自动降级，错误分类提示清晰易懂。

## 环境要求

- Python 3.10+
- Docker（可选，推荐用于 SearXNG）
- 网络连接（本地 SearXNG 启动后可离线搜索）
- Windows / macOS / Linux

## 🚀 快速开始

```bash
# 一键安装
python scripts/quick_setup.py

# 搜索
python scripts/search.py "关键词"
python scripts/search.py "关键词" --privacy strict

# 隐私报告
python scripts/privacy report

# 检查更新
python scripts/update_checker check
```

详细 5 分钟上手指南 → [QUICK_START.md](references/QUICK_START.md)

## 核心命令

### F1：多引擎并行搜索

```bash
# 基础搜索
python -m scripts.search "搜索关键词"

# 指定引擎
python -m scripts.search "关键词" --engines baidu,bing,duckduckgo

# strict 隐私模式
python -m scripts.search "关键词" --privacy strict

# JSON 输出
python -m scripts.search "关键词" --json

# 错误诊断（网络/配置/引擎问题）
python -m scripts.search "关键词" --privacy strict --verbose
```

### F2：SearXNG 本地实例管理

```bash
# Docker 启动（推荐）
python -m scripts.searxng_manager start --method docker

# pip 启动
python -m scripts.searxng_manager start --method pip

# 状态检查
python -m scripts.searxng_manager status

# 停止
python -m scripts.searxng_manager stop
```

### F3：隐私模式切换

```bash
# 状态查看
python -m scripts.privacy status

# 切换到 strict
python -m scripts.privacy mode --set strict

# 切换到 normal
python -m scripts.privacy mode --set normal

# 生成隐私保护报告
python -m scripts.privacy report
```

### 版本更新检查（死规则 11）

```bash
python -m scripts.update_checker check
python -m scripts.update_checker status
```

## 能做哪些

| 能力 | 说明 |
|------|------|
| 多引擎并发搜索 | 10 引擎并行，SimHash 去重，交叉排序 |
| 本地 SearXNG | Docker/pip 双路径，query 不出本机 |
| 隐私一键切换 | strict 下无 Cookie/Referrer/DNT=1 |
| 国内可用 strict | Yandex/Startpage/Qwant/Brave 自动降级 |
| 错误分类诊断 | 网络/配置/引擎三类问题，针对性排查 |
| 版本更新提醒 | 启动异步检查，24h 不重复 |
| 请求频率控制 | 单引擎日上限 200 + 随机延迟 |
| 失败降级 | 单引擎失败不影响其他 |
| venv 隔离 | pip 依赖全虚拟环境，不污染系统 |

## 不能做哪些（V1.1 限制）

- ❌ **不隐藏 IP 地址**：搜索引擎仍可见您的 IP，严格隐私需配合 VPN
- ❌ **不提供 LLM 摘要**（V1.2+ 规划）
- ❌ **不提供搜索历史导出**（V1.2+ 规划）
- ❌ **不提供浏览器插件/CLI 交互**（V2.0+ 规划）

## 风险声明

### 隐私边界

| 风险 | 说明 | 缓解 |
|------|------|------|
| IP 可见性 | strict 仍可见 IP | 建议配合 VPN |
| 搜索词明文传输 | F1 直发 query | strict 仅 DDG/Yandex 等 |
| SearXNG 端口暴露 | 默认 127.0.0.1 | 禁止 0.0.0.0 |

### 合规使用

| 风险 | 说明 | 缓解 |
|------|------|------|
| 搜索引擎条款 | 自动化访问可能受限 | 尊重 robots.txt |
| 数据合规 | 搜索结果存储需合规 | 默认不保存历史 |

## 常见错误

> 遇到错误时，使用 `--verbose` 查看详细诊断

### 网络故障 🌐

```
💡 网络连接失败，请检查网络或使用 --verbose 查看详情
```

排查：
1. 检查网络：`ping www.baidu.com`
2. 确认网络环境不受限
3. 增大超时：`config.yaml` 中 `search.timeout: 20`

### 配置错误 ⚙️

```
💡 配置错误，请检查 config.yaml 或使用 --verbose 查看详情
```

排查：
1. 确认 YAML 格式正确（冒号后有空格）
2. 复制 `references/config.yaml.example` 重新配置

### 引擎错误 🔧

```
💡 搜索引擎解析失败，请稍后重试或更换引擎
```

排查：
1. 引擎可能已更新页面结构
2. 更新到最新版本
3. 排除该引擎：`--engines` 参数

## 常见问题

**Q: strict 模式在国内能用吗？**
A: V1.1 已增强。strict 默认使用 Yandex（国内快）+ Startpage + Qwant + Brave，自动降级。DDG 仅作最后备选。

**Q: SearXNG 启动失败？**
A: 尝试切换：`--method pip`。确保 Docker 或 Python 3.10+ 可用。

**Q: 如何关闭更新检查？**
A: `python -m scripts.update_checker disable`

**Q: 搜索结果不显示？**
A: 使用 `--verbose` 查看具体错误类别，按上方"常见错误"排查。

**Q: 安装依赖失败？**
A: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

**Q: 如何在其他程序里调用？**
A: V1.1 仅支持命令行调用，V2.0 规划支持 MCP Server / 插件。

**Q: 支持自定义引擎吗？**
A: V1.1 不支持，需修改代码。V1.2 规划支持用户自定义引擎配置。

**Q: 支持哪些引擎？**
A: 10 个引擎：百度、必应、搜狗、360、DuckDuckGo、Yandex、Startpage、Qwant、Brave、本地 SearXNG。默认启用 baidu/bing/DDG/SearXNG。

**Q: 隐私模式对国内搜索有影响吗？**
A: normal 模式无影响（走国内引擎）。strict 模式自动选择 Yandex 等国内可访问引擎，不影响使用。

**Q: 配置项太多，哪些必须改？**
A: 首次只需改 3 项（config.yaml 中标注 [推荐修改]）：`default_engines`、`timeout`、`default_mode`。其他保持默认。

## 项目结构

```
privacy-search/
├── SKILL.md                          # 本文件
├── requirements.txt                  # Python 依赖
├── scripts/
│   ├── __init__.py
│   ├── search.py                     # F1: 搜索（含错误分类）
│   ├── searxng_manager.py            # F2: SearXNG 管理
│   ├── privacy.py                    # F3: 隐私模式
│   ├── update_checker.py             # 更新检查（死规则 11）
│   └── quick_setup.py                # 🆕 V1.1 一键安装
├── references/
│   ├── config.yaml.example           # 配置模板（含推荐配置标注）
│   ├── engines.md                    # 引擎适配器文档
│   ├── engines_zh.md                 # 🆕 V1.1 国内引擎文档
│   └── QUICK_START.md                # 🆕 V1.1 快速上手
└── tests/
    ├── test_search.py                # F1 测试
    ├── test_searxng.py               # F2 测试
    ├── test_privacy.py               # F3 测试
    └── test_update_checker.py        # 更新检查测试
```

## 更新日志

| v1.1.0 | 2026-07-19 | 增加5个国内可用备选引擎（Yandex/Startpage/Qwant/Brave/Ecosia）；strict模式自动降级与故障转移；增强错误分类（网络/配置/引擎三类）；增加10+FAQ与常见错误反模式对照；增加normal/strict模式搜索输出示例；增加5分钟快速上手指南QUICK_START.md；增加一键安装脚本quick_setup.py |
| v1.0.0 | 2026-07-18 | 初始版本发布：多引擎并行搜索（F1）；SearXNG本地实例双路径部署（F2）；隐私模式normal/strict切换（F3）；版本更新检查提醒（死规则11）；SimHash去重与交叉验证排序 |

## 支持与反馈

- **联系邮箱**：njskills@agent.qq.com
- **问题反馈**：欢迎通过邮件或 SkillHub 评论提出建议
- **版本更新**：运行 `python -m scripts.update_checker check` 检查新版本
