---
slug: privacy-search
displayName: 隐私搜索
name: privacy-search
description: "隐私优先的多引擎并行搜索 Skill，V1.0 提供三大核心功能：多引擎并发搜索（百度/必应/搜狗/360/DuckDuckGo/本地SearXNG）+ SimHash去重排序、SearXNG本地实例自动部署（Docker/pip双路径）、隐私模式（normal/strict一键切换）。启动时异步检查更新，24h不重复。所有搜索请求支持并发控制、超时限制、失败降级，不污染系统 Python 环境。"
version: 1.0.0
tags: ["privacy", "search", "multi-engine", "duckduckgo", "searxng", "local-first", "simhash"]
icon: "🔒"
author: "njskills"
license: "MIT"
---

# 隐私搜索（Privacy Search）

隐私优先的多引擎并行搜索 Skill。V1.0 聚焦核心搜索能力，只做三件事：多引擎并发搜索、本地 SearXNG 实例自动部署、隐私模式切换。启动时异步检查版本更新，24h 不打扰。

## 环境要求

- Python 3.10+
- Docker（可选，推荐用于 SearXNG）
- 网络连接（本地 SearXNG 启动后可离线搜索）
- Windows / macOS / Linux

## 快速安装

```bash
# 1. 安装依赖（推荐 venv 隔离）
python -m venv .venv
. .venv/bin/activate                    # Linux/macOS
# .venv\Scripts\activate                 # Windows

# 2. 安装依赖包
pip install -r requirements.txt

# 3. 复制配置文件
cp references/config.yaml.example config.yaml
```

## 核心命令

### F1：多引擎并行搜索

```bash
# 基础搜索（使用配置中的默认引擎）
python -m scripts.search "搜索关键词"

# 指定引擎（逗号分隔）
python -m scripts.search "关键词" --engines baidu,bing,duckduckgo

# strict 隐私模式搜索
python -m scripts.search "关键词" --privacy strict

# 输出 JSON 格式
python -m scripts.search "关键词" --json

# 调整每个引擎返回结果数
python -m scripts.search "关键词" --num 20
```

### F2：SearXNG 本地实例管理

```bash
# Docker 方式启动（推荐）
python -m scripts.searxng_manager start --method docker

# pip 方式启动（venv 隔离）
python -m scripts.searxng_manager start --method pip

# 查看状态
python -m scripts.searxng_manager status

# 停止服务
python -m scripts.searxng_manager stop
```

### F3：隐私模式切换

```bash
# 查看当前模式
python -m scripts.privacy status

# 切换到 strict 模式
python -m scripts.privacy mode --set strict

# 切换到 normal 模式
python -m scripts.privacy mode --set normal

# 生成隐私保护报告
python -m scripts.privacy report

# 查看 strict 模式允许的引擎
python -m scripts.privacy status --json
```

### 版本更新检查（死规则 11）

```bash
# 手动检查更新（含 force 模式，忽略缓存）
python -m scripts.update_checker check
python -m scripts.update_checker check --force

# 查看当前版本和检查状态
python -m scripts.update_checker status

# 启用/禁用更新检查
python -m scripts.update_checker enable
python -m scripts.update_checker disable
```

## 能做哪些

| 能力 | 说明 |
|------|------|
| 多引擎并发搜索 | 百度/必应/搜狗/360/DuckDuckGo/SearXNG 6 引擎并行请求 |
| SimHash 去重 | 汉明距离 ≤ 3 视为重复，保留摘要最长版本 |
| 交叉验证排序 | 出现在越多引擎的结果排名越靠前 |
| 本地 SearXNG | Docker/pip 双路径部署，query 不出本机 |
| 隐私一键切换 | strict 下无 Cookie/Referrer/DNT=1，仅走隐私友好引擎 |
| 版本更新提醒 | 启动时异步检查，有新版本 CLI 提示 |
| 请求频率控制 | 单引擎日请求上限 + 随机延迟，防封禁 |
| 失败降级 | 单引擎失败不影响其他引擎结果 |
| venv 隔离 | pip 依赖全在虚拟环境，不污染系统 Python |

## 不能做哪些（V1.0 限制）

- ❌ **不隐藏 IP 地址**：搜索引擎仍可见您的 IP，严格隐私需配合 VPN
- ❌ **不提供 LLM 摘要**（V1.1+ 规划）
- ❌ **不提供搜索历史导出**（V1.2+ 规划）
- ❌ **不提供浏览器插件/CLI 交互**（V2.0+ 规划）
- ❌ SearXNG 需要首次启动时拉取 Docker 镜像或安装 pip 包

## 风险声明

### 隐私边界

| 风险项 | 说明 | 缓解措施 |
|--------|------|---------|
| IP 可见性 | strict 模式隐藏 Cookie/Referrer，但 IP 仍对搜索引擎可见 | 建议配合 VPN 使用 |
| 搜索词明文传输 | F1 直接向搜索引擎发送明文 query | strict 下仅走 DuckDuckGo（隐私友好）+ 本地 SearXNG |
| SearXNG 端口暴露 | 默认绑定 127.0.0.1，但错误配置可能暴露到外网 | 配置文件强制 `host: 127.0.0.1`，禁止 `0.0.0.0` |

### 网络安全

| 风险项 | 说明 | 缓解措施 |
|--------|------|---------|
| 依赖包安全 | pip 依赖可能包含恶意代码 | 固定版本号 + venv 隔离 + 官方源 |
| Docker 镜像安全 | SearXNG 镜像可能被篡改 | 使用官方 `searxng/searxng:latest` 镜像 |
| 搜索引擎封禁 | 高频请求可能触发封禁 | 随机延迟 + 日请求上限 |

### 合规使用

| 风险项 | 说明 | 缓解措施 |
|--------|------|---------|
| robots.txt 合规 | 搜索引擎使用条款可能限制自动化访问 | 代码尊重 robots.txt，用户需遵守各引擎条款 |
| 数据合规 | 搜索结果的存储和使用需符合当地法规 | 默认不保存搜索历史，仅内存中处理 |

## 隐私保护设计

1. **strict 模式默认**：配置文件中 `default_mode: strict`，首次使用即开启
2. **仅本地回环**：SearXNG 强制绑定 `127.0.0.1:8888`，外网不可访问
3. **无持久化搜索历史**：搜索请求在内存中处理，不写入数据库/日志
4. **失败降级不泄露**：引擎失败时返回空结果，不抛异常泄露内部信息
5. **缓存最小化**：更新检查缓存仅存版本号，不含搜索词等敏感信息

## 常见问题

**Q: SearXNG 启动失败怎么办？**
A: 尝试切换安装方式：`--method pip`。确保 Docker 已启动或 Python 3.10+ 可用。

**Q: 如何关闭更新检查？**
A: `python -m scripts.update_checker disable`，或修改 `config.yaml` 中 `update_check.enabled: false`。

**Q: strict 模式搜索速度慢？**
A: strict 仅走 DuckDuckGo + SearXNG 2 个引擎，比 normal 模式引擎数少。首次 SearXNG 搜索会冷启，后续会改善。

**Q: 支持其他搜索引擎吗？**
A: V1.0 固定 6 个引擎，V1.1 规划支持用户自定义引擎配置。

## 项目结构

```
privacy-search/
├── SKILL.md                          # 本文件 - 使用说明与风险声明
├── requirements.txt                  # Python 依赖
├── scripts/
│   ├── search.py                     # F1: 多引擎并行搜索
│   ├── searxng_manager.py            # F2: SearXNG 本地实例管理
│   ├── privacy.py                    # F3: 隐私模式切换
│   └── update_checker.py             # 版本更新检查（死规则 11）
├── references/
│   ├── config.yaml.example           # 配置模板
│   └── engines.md                    # 搜索引擎适配器文档
└── tests/
    ├── test_search.py                # F1 单测
    ├── test_searxng.py               # F2 单测
    ├── test_privacy.py               # F3 单测
    └── test_update_checker.py        # 更新检查单测
```

## 更新日志

| v1.0.0 | 2026-07-18 | 初始版本发布：多引擎并行搜索（F1）；SearXNG本地实例双路径部署（F2）；隐私模式normal/strict切换（F3）；版本更新检查提醒（死规则11）；SimHash去重与交叉验证排序 |

## 支持与反馈

- **联系邮箱**：njskills@agent.qq.com
- **问题反馈**：欢迎通过邮件或 SkillHub 评论提出建议
- **版本更新**：运行 `python -m scripts.update_checker check` 检查新版本
