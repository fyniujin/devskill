---
slug: privacy-search
displayName: 隐私搜索
name: privacy-search
description: "隐私优先的多引擎并行搜索 Skill，提供十大搜索引擎（百度/必应/搜狗/360/DuckDuckGo/Yandex/Startpage/Qwant/Brave/本地SearXNG）并行检索。V1.2 提供结果缓存与搜索历史、统一 HTTP 出口（隐私头/UA池/代理/自动重试真正生效）、标准 SimHash 去重、多因子加权排序（共识度/位次/相关度/权威度/域名质量）、多套备选选择器与解析诊断、bangs 语法透传。SearXNG 本地实例双路径部署，隐私模式 normal/strict 一键切换，不污染系统 Python 环境。"
version: 1.2.0
tags: ["privacy", "search", "multi-engine", "duckduckgo", "searxng", "local-first", "simhash", "china-friendly"]
icon: "🔒"
author: "njskills"
license: "MIT"
---

# 隐私搜索（Privacy Search）

隐私优先的多引擎并行搜索 Skill。V1.2 聚焦**搜索质量**与**隐私真实生效**：结果缓存显著降低重复查询开销，统一 HTTP 出口让隐私头与代理真正作用于每一次请求，多因子加权排序替代单一共识度排序。

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

# strict 引擎全部失败时，显式授权降级到国内引擎
python -m scripts.search "关键词" --privacy strict --allow-fallback

# JSON 输出
python -m scripts.search "关键词" --json

# 错误诊断（网络/配置/引擎问题）
python -m scripts.search "关键词" --privacy strict --verbose

# 查看全部可用引擎
python -m scripts.search --list-engines

# 引擎连通性与解析健康度体检
python -m scripts.search --selftest

# 搜索后附带隐私保护摘要
python -m scripts.search "关键词" --privacy strict --privacy-report
```

### 缓存与搜索历史

相同查询在有效期内直接复用结果，输出会标注「来源: 缓存」。

```bash
# 跳过缓存，强制重新搜索
python -m scripts.search "关键词" --no-cache

# 查看缓存占用
python -m scripts.search --cache-stats

# 清空缓存
python -m scripts.search --clear-cache

# 查看最近搜索历史（默认 20 条）
python -m scripts.search --history
python -m scripts.search --history 50

# 清空搜索历史
python -m scripts.search --clear-history
```

### bangs 快捷语法

查询词中带 `!` 前缀时自动路由到本地 SearXNG，由其转发到目标站点。

```bash
python -m scripts.search "!w 量子计算"      # 维基百科
python -m scripts.search "!gh asyncio"      # GitHub
python -m scripts.search "!yt python 教程"  # YouTube
```

> 该语法依赖本地 SearXNG。未启用时会提示并按普通关键词搜索。

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
| 多引擎并发搜索 | 10 引擎并行，标准 SimHash 去重 |
| 多因子加权排序 | 共识度 + 位次 + 相关度 + 权威度 + 域名质量，权重可配 |
| 结果缓存 | 相同查询秒回，容量上限自动淘汰 |
| 搜索历史 | 本地留存最近 500 条，可查可清 |
| 统一隐私出口 | 隐私头 / UA 池 / 代理 / 重试对全部引擎一致生效 |
| 隐私优先兜底 | strict 下拒绝非白名单引擎，失败不静默降级 |
| 本地 SearXNG | Docker/pip 双路径，query 不出本机 |
| bangs 语法 | `!w` `!gh` `!yt` 等快捷跳转，经 SearXNG 转发 |
| 解析健壮性 | 每引擎多套备选选择器，改版后自动尝试 |
| 解析诊断 | 区分「确实无结果」「被拦截」「选择器失效」 |
| 引擎体检 | `--selftest` 一次性检查各引擎连通与解析状态 |
| 网络自动重试 | 指数退避 + 随机抖动，仅对网络类错误重试 |
| 运行日志 | 级别可配，默认不记录查询词原文 |
| 错误分类诊断 | 网络/配置/引擎三类问题，针对性排查 |
| 版本更新提醒 | 启动异步检查，24h 不重复 |
| 请求频率控制 | 单引擎日上限 200 + 随机延迟 |
| venv 隔离 | pip 依赖全虚拟环境，不污染系统 |

## 不能做哪些（V1.2 限制）

- ❌ **不隐藏 IP 地址**：未配置 `privacy.strict.proxy` 时搜索引擎仍可见您的 IP
- ❌ **不提供 LLM 摘要**（V1.3+ 规划）
- ❌ **不提供网页正文抓取**（V1.3+ 规划）
- ❌ **不提供浏览器插件 / MCP Server**（V2.0+ 规划）
- ❌ **不保证引擎长期可解析**：搜索引擎改版后需等待选择器更新

## 风险声明

### 隐私边界

| 风险 | 说明 | 缓解 |
|------|------|------|
| IP 可见性 | 不配置代理时引擎可见真实 IP | 设置 `privacy.strict.proxy` 或配合 VPN |
| 搜索词明文传输 | 查询词需发送至引擎 | strict 走隐私引擎，或用本地 SearXNG |
| 本地缓存留痕 | 缓存与历史含查询词，明文存于本地 | `--clear-cache` / `--clear-history`，或 `cache.enabled: false` |
| 日志留痕 | 默认 INFO 只记录查询词长度 | 需完全静默可设 `logging.level: OFF` |
| SearXNG 端口暴露 | 默认 127.0.0.1 | 禁止改为 0.0.0.0 |

### 合规使用

| 风险 | 说明 | 缓解 |
|------|------|------|
| 搜索引擎条款 | 自动化访问可能受限 | 尊重 robots.txt，勿调高频率上限 |
| 数据合规 | 缓存与历史存于本地磁盘 | 共享设备建议关闭缓存 |

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
1. 运行 `python -m scripts.search --selftest` 定位具体原因
2. 按诊断结论处理（见下表）
3. 临时规避：用 `--engines` 排除该引擎

### 解析诊断对照

`--selftest` 与 `--verbose` 会输出诊断结论：

| 诊断 | 含义 | 处理 |
|------|------|------|
| 正常 | 解析成功 | 无需处理 |
| 确认无结果 | 该关键词确实无匹配 | 换关键词或换引擎 |
| 被拦截 | 触发验证码或风控 | 降低频率，稍后重试 |
| 选择器失效 | 引擎改版导致解析不到 | 更新到最新版本 |
| 未知 | 页面结构异常 | 用 `--verbose` 查看详情 |

## 常见问题

**Q: strict 模式在国内能用吗？**
A: 可以。strict 默认使用 Yandex（国内快）+ Startpage + Qwant + Brave，DDG 作最后备选。

**Q: strict 模式下指定 `--engines baidu` 为什么没生效？**
A: 这是有意设计。strict 模式会拒绝隐私保护不足的引擎，避免"以为开了 strict 实际仍在向百度发送查询词"。需要用百度请改用 `--privacy normal`。

**Q: strict 模式搜不到结果，直接返回空？**
A: 隐私引擎全部不可用时默认停止搜索，而非静默降级到国内引擎——因为 strict 用户的预期是宁可无结果也不泄露查询词。确需降级请加 `--allow-fallback`，或在配置中开启 `privacy.strict.allow_fallback`。

**Q: 结果是旧的怎么办？**
A: 默认缓存 1 小时。加 `--no-cache` 强制刷新，或调小 `cache.ttl_seconds`。

**Q: 缓存文件会无限增长吗？**
A: 不会。超过 `cache.max_size_mb`（默认 50MB）时自动淘汰最久未使用的条目，历史记录上限 500 条。

**Q: 缓存和历史存在哪？如何彻底清除？**
A: 默认在 `~/.workbuddy/output/privacy-search-cache.db`。`--clear-cache` 清结果，`--clear-history` 清历史，两者独立。

**Q: 怎么确认隐私设置真的生效了？**
A: 加 `--privacy-report` 查看本次搜索实际使用的请求头、代理与被屏蔽引擎。

**Q: 如何隐藏 IP？**
A: 在 config.yaml 设置 `privacy.strict.proxy`，支持 `http://` 与 `socks5://`。留空为直连。

**Q: 某个引擎突然搜不到结果？**
A: 先跑 `--selftest`。若显示「选择器失效」说明该引擎改版了，请更新到最新版本；显示「被拦截」则是触发了风控，稍后再试或换引擎。

**Q: 为什么指定了 searxng 却没用上？**
A: 检查 `searxng.enabled` 是否为 true，以及本地实例是否已启动（`python -m scripts.searxng_manager status`）。

**Q: 排序结果不满意能调吗？**
A: 可以。config.yaml 的 `ranking` 段可调五个权重，例如更看重多引擎共识就调高 `consensus`。

**Q: 中文分词报缺少 jieba？**
A: jieba 为可选依赖，缺失时自动降级为字符级切分，搜索仍可用。安装后相关度排序更准。

**Q: 会记录我搜了什么吗？**
A: 日志默认 INFO 级别，只记录查询词长度不记录原文；搜索历史存于本地且可随时清空。需完全静默可设 `logging.level: OFF`。

**Q: SearXNG 启动失败？**
A: 尝试切换：`--method pip`。确保 Docker 或 Python 3.10+ 可用。

**Q: 如何关闭更新检查？**
A: `python -m scripts.update_checker disable`

**Q: 安装依赖失败？**
A: `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

**Q: 支持哪些引擎？**
A: 10 个：百度、必应、搜狗、360、DuckDuckGo、Yandex、Startpage、Qwant、Brave、本地 SearXNG。运行 `--list-engines` 查看完整属性。

**Q: 如何在其他程序里调用？**
A: 当前仅支持命令行，可用 `--json` 获取结构化输出。MCP Server 在 V2.0 规划中。

**Q: 配置项太多，哪些必须改？**
A: 首次只需改 3 项（config.yaml 中标注 [推荐修改]）：`default_engines`、`timeout`、`default_mode`。其他保持默认。

## 项目结构

```
privacy-search/
├── SKILL.md                          # 本文件
├── requirements.txt                  # Python 依赖
├── scripts/
│   ├── __init__.py
│   ├── search.py                     # F1: 搜索编排与 CLI
│   ├── searxng_manager.py            # F2: SearXNG 管理
│   ├── privacy.py                    # F3: 隐私模式与请求上下文
│   ├── engines_registry.py           # 引擎清单单一真相源
│   ├── engine_selectors.py           # 各引擎选择器与解析诊断
│   ├── http_client.py                # 统一 HTTP 出口（UA池/代理/重试）
│   ├── ranking.py                    # SimHash 去重与多因子排序
│   ├── cache.py                      # 结果缓存与搜索历史
│   ├── logging_util.py               # 运行日志
│   ├── version_util.py               # 版本解析单一真相源
│   ├── update_checker.py             # 更新检查（死规则 11）
│   └── quick_setup.py                # 一键安装
├── references/
│   ├── config.yaml.example           # 配置模板（含推荐配置标注）
│   ├── engines.md                    # 引擎适配器文档
│   ├── engines_zh.md                 # 国内引擎与降级策略
│   └── QUICK_START.md                # 快速上手
└── tests/
    ├── test_search.py                # 搜索基础测试
    ├── test_search_v11.py            # 引擎与降级测试
    ├── test_search_v12.py            # 缓存/排序/日志测试
    ├── test_searxng.py               # SearXNG 管理测试
    ├── test_privacy.py               # 隐私模式测试
    └── test_update_checker.py        # 更新检查测试
```

## 更新日志

| v1.2.0 | 2026-07-27 | 增加：结果缓存与搜索历史（TTL可配、容量上限自动淘汰、--no-cache/--clear-cache/--history/--cache-stats）；增加：统一HTTP出口模块，隐私头/UA池/代理/自动重试对全部引擎一致生效；增加：每引擎多套备选选择器与解析诊断分类（无结果/被拦截/选择器失效）；增加：--selftest引擎连通性体检、--list-engines引擎清单、--privacy-report隐私摘要；增加：bangs快捷语法透传本地SearXNG；增加：运行日志模块，级别可配且默认不记录查询词原文；增加：排序权重可在配置中调整；优化：SimHash改为按位加权投票的标准实现；优化：排序改为共识度/位次/相关度/权威度/域名质量多因子加权；优化：jieba改为懒加载，模块导入耗时从0.9秒降至0.1秒；优化：识别搜索引擎跳转链接并降权，提升跨引擎去重准确度；优化：跳转中转地址与同标题直链合并为一条，同一页面不再重复占位并优先展示直链；优化：标题归并容忍全半角标点差异与截断尾缀，跨引擎去重召回率提升；优化：结果列表标注全部收录引擎与引擎数量，直观体现交叉验证；修复：去重时保留被合并条目的引擎来源与最优位次，共识度因子恢复生效；修复：共识度分母改用实际发起搜索的引擎数，部分引擎失败时不再虚高；修复：缓存路径非法时改为静默降级，不再中断搜索；修复：隐私模式配置兼容 default_mode 与 mode 两种键名并容忍大小写，写法有误时不再静默按普通模式运行；修复：版本号改为从SKILL.md解析，更新提醒不再误报；修复：引擎清单收归注册表，隐私报告屏蔽引擎统计由6项补全至10项；修复：num_results、searxng.enabled、logging三项配置由声明改为实际生效；修复：strict模式下显式指定的非白名单引擎改为拒绝，避免隐私承诺被绕过；修复：缺少依赖时改为提示可直接执行的安装命令与虚拟环境建议，不再抛出裸报错；修复：一键安装脚本标题版本号改为从SKILL.md解析，不再显示旧版本；修复：--privacy-report可单独运行，不再要求同时提供搜索关键词；修复：更新提示框按显示列数对齐并对超长内容折行，中文标签与下载链接不再错位或被截断；增加：引擎返回结果数远低于预期时提示可能触发限流，不再只在零结果时诊断；增加：识别引擎兜底响应，整体结果与查询词关联过弱时按引擎提示核对其他来源；修复：测试包在导入与退出时清理字节码缓存，运行测试不再向仓库写入pyc文件；调整：strict引擎全部失败时默认停止搜索而非降级到国内引擎，需经--allow-fallback显式授权 |
| v1.1.0 | 2026-07-19 | 增加4个国内可用备选引擎（Yandex/Startpage/Qwant/Brave）；strict模式自动降级与故障转移；增强错误分类（网络/配置/引擎三类）；增加10+FAQ与常见错误反模式对照；增加normal/strict模式搜索输出示例；增加5分钟快速上手指南QUICK_START.md；增加一键安装脚本quick_setup.py |
| v1.0.0 | 2026-07-18 | 初始版本发布：多引擎并行搜索（F1）；SearXNG本地实例双路径部署（F2）；隐私模式normal/strict切换（F3）；版本更新检查提醒（死规则11）；SimHash去重与交叉验证排序 |

## 支持与反馈

- **联系邮箱**：njskills@agent.qq.com
- **问题反馈**：欢迎通过邮件或 SkillHub 评论提出建议
- **版本更新**：运行 `python -m scripts.update_checker check` 检查新版本
