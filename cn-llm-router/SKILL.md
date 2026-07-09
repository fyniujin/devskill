---
slug: cn-llm-router
displayName: cn-llm-router
name: cn-llm-router
description: 国产大模型统一路由。把 DeepSeek、通义千问、智谱 GLM、Kimi、腾讯混元、字节豆包、百度文心、讯飞星火等 8 家国产大模型收敛成一个命令入口；按任务类型（代码/推理/长文/翻译/摘要/抽取）自动或手动选择最合适、最省钱的模型；自动统计跨厂商 token 成本、硬件自适应限流（不拖累电脑）、本地语义缓存省 token、技能更新提醒。当用户需要「调用国产大模型」「多模型比价/降本」「统一管理多个模型 Key」「本地跑大模型路由」「不想被某一家厂商绑定」时使用。
version: 1.0.0
author: njskills
license: MIT
tags: [国产大模型, 模型路由, 成本统计, 多模型, 硬件自适应, 语义缓存, 零密钥]
---

# 国产大模型统一路由（cn-llm-router）

> 一个**核心零依赖（纯 Python 标准库，仅讯飞星火可选一个 `websocket-client`）、零密钥打包**的命令行工具，把 8 家国产大模型收敛成「一个入口、一套命令」。你只管说「我要干嘛」，它帮你挑模型、算成本、限并发；断网或无 Key 时也能演示路由逻辑。

## 一、30 秒速查

```bash
# 不配任何密钥，先看「路由建议」（演示/规划用，不发起调用）
python scripts/router.py route --prompt "用 Python 写个快排" --task code

# 配好密钥后，真正调用（默认 auto 策略 = 任务感知选模型）
export DEEPSEEK_API_KEY=sk-xxx          # 至少一个厂商即可
python scripts/router.py chat --prompt "解释一下快速排序" --model auto

# 看这台电脑的硬件画像与建议并发（不拖累电脑的关键）
python scripts/router.py hardware
```

- 支持厂商（8 家）：DeepSeek、阿里通义千问、智谱 GLM、Kimi、腾讯混元、字节豆包、百度文心、讯飞星火。
- 运行要求：Python 3.8+；**7 家厂商（DeepSeek/通义/智谱/Kimi/混元/豆包/文心）与全部离线功能无需安装任何第三方包**；讯飞星火为可选 `websocket-client`（不装也能用其余 7 家，仅星火调用时给出中文安装指引）。
- 密钥来源：只用**环境变量**，绝不明文落盘、绝不打包进 skill。

## 二、架构

```
cn-llm-router/
├── SKILL.md                  # 本文件（使用说明 + 风险 + 边界 + FAQ）
├── version.json              # 版本号（更新提醒比对用）
├── config.example.json       # 配置模板（无密钥，复制后改）
├── references/
│   ├── models.yaml           # 模型注册表（纯数据，可自助增删厂商）
│   └── routing-rules.md      # 路由策略规则说明
├── scripts/
│   ├── router.py             # 统一 CLI 入口 + 策略引擎（对外只暴露这一个文件）
│   ├── classifier.py         # 任务分类器（规则 + 关键词，离线）
│   ├── config.py             # 配置/密钥读取（仅读环境变量）
│   ├── cost_tracker.py       # 跨厂商成本聚合（SQLite，本地）
│   ├── hardware.py           # 硬件画像 + 并发/子任务数自适应
│   ├── cache.py              # 本地语义缓存（降 token 消耗）
│   ├── report.py             # 文本/HTML 成本报表 + 预算告警
│   ├── update_check.py       # 更新提醒（可离线，失败静默）
│   ├── yaml_simple.py        # 自研零依赖 YAML 解析（不引入 PyYAML）
│   ├── meta.py               # 版本常量
│   └── adapters/             # 各厂商适配器（统一接口）
│       ├── base.py           # AdapterBase + 中文异常
│       ├── openai_compat.py  # OpenAI 兼容端点（6 家通用）
│       ├── ernie.py          # 文心大模型（兼容 + 原生双通道）
│       └── spark.py          # 讯飞星火（WebSocket 签名，可选 websocket-client 做传输）
└── tests/
    └── test_router.py        # 离线测试（18 项，无需密钥）
```

核心数据流：`prompt → classifier → 策略引擎(resolve) → adapter → 大模型`，同时旁路写入 `cost_tracker`（成本）与 `cache`（命中则跳过调用）。

## 三、能做哪些（功能清单）

| 功能 | 命令 | 说明 |
|------|------|------|
| 智能路由 | `route` | 按任务自动选模型；`--strategy auto/cheap/quality/manual`；无 Key 进「建议模式」只展示不调用 |
| 统一调用 | `chat` | 单入口对话，自动统计成本；支持流式、系统提示词、JSON 输出 |
| 任务分类 | 内置 | 识别 code/reason/summarize/translate/extract 等，驱动路由 |
| 成本统计 | `report` | 日/周/月报，跨厂商聚合花费、成功率、P95 延迟；可导出 HTML |
| 预算保护 | `budget` | 月预算阈值告警，可选推企业微信 |
| 硬件自适应 | `hardware` | 探测 CPU/内存，自动限制最大并发与单批大小，**不拖累电脑** |
| 语义缓存 | `cache` | 相似问题命中本地缓存，跳过 API 调用，省 token 省钱 |
| 更新提醒 | `update-check` | 比对 version.json，提示升级（联网失败静默，不阻塞） |
| 配置查看 | `config` | 列出已配置厂商与环境变量提示 |

**全部命令均可离线运行**（除真正发起 `chat` 调用时），`route/hardware/report/cache/config/update-check/version` 都不需要网络或密钥。

## 四、安装与配置

### 4.1 运行环境
- Python 3.8+（Windows / macOS / Linux 均可）。
- **除讯飞星火的可选 `websocket-client` 外，无需 `pip install` 任何依赖**；其余 7 家与全部离线功能均用标准库实现，讯飞星火签名（hmac/hashlib/base64）也自研，仅 WS 传输用可选客户端。

### 4.2 配置密钥（只用环境变量，三种任选其一）
```bash
# 方式 A：临时（当前终端）
export DEEPSEEK_API_KEY=sk-xxx
export DASHSCOPE_API_KEY=sk-xxx        # 通义千问
export ZHIPU_API_KEY=sk-xxx            # 智谱
export MOONSHOT_API_KEY=sk-xxx         # Kimi
export HUNYUAN_API_KEY=sk-xxx          # 腾讯混元
export ARK_API_KEY=sk-xxx              # 字节豆包
export ERNIE_OPENAI_KEY=sk-xxx         # 文心（OpenAI 兼容端点，推荐）
# 或文心原生：ERNIE_API_KEY=xxx  +  ERNIE_SECRET_KEY=xxx
export SPARK_APP_ID=xxx SPARK_API_KEY=xxx SPARK_API_SECRET=xxx  # 讯飞星火

# 方式 B：写进 shell 配置文件（~/.bashrc / ~/.zshrc）后 source 生效
# 方式 C：Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-xxx"
```
> 仅需配置你**实际要用的那一家**即可，`route` 与 `chat` 会自动只用已配置的厂商做决策。

### 4.3 可选配置文件
把 `config.example.json` 复制为 `config.json`（或 `~/.cn_llm_router_config.json`），可设月预算、更新地址、企微告警 webhook、缓存 TTL 等。**该文件不含任何密钥**。

## 五、命令参考（均可运行，路径相对于技能根目录）

```bash
# 1) 路由决策（不调用 API）
python scripts/router.py route --prompt "用 Python 写快排" --task code
python scripts/router.py route --prompt "翻译这段话" --strategy cheap
python scripts/router.py route --prompt "证明一个数学猜想" --strategy quality
python scripts/router.py route --prompt "随便聊聊" --model deepseek:deepseek-chat   # manual
python scripts/router.py route --prompt "..." --json                                # 程序调用用 JSON

# 2) 真正调用（需先配对应厂商密钥）
python scripts/router.py chat --prompt "解释快排" --model auto
python scripts/router.py chat --prompt "..." --stream          # 流式
python scripts/router.py chat --prompt "..." --system "你是中文助手"
python scripts/router.py chat --prompt "..." --no-cache        # 禁用缓存
python scripts/router.py chat --prompt "..." --json            # 结构化输出

# 3) 成本与硬件
python scripts/router.py report --period month                 # 月报
python scripts/router.py report --period month --html report.html
python scripts/router.py hardware                              # 硬件画像 + 建议并发
python scripts/router.py budget                                # 预算检查
python scripts/router.py cache stats                           # 缓存条目数
python scripts/router.py cache clear                           # 清空缓存
python scripts/router.py config                                # 已配置厂商
python scripts/router.py update-check                          # 检查更新
python scripts/router.py version                               # 版本号
```

> Windows 用户把 `python` 换成 `python.exe` 或 `py`；PowerShell 里环境变量用 `$env:XXX="..."`。

## 六、硬件自适应（不拖累电脑）

`hardware.py` 在**首次运行/每次运行**时自动探测本机：
- CPU 逻辑核心数、物理内存总量；
- 据此分级：`low`（≤4 核或 ≤8GB）→ `mid` → `high`（≥8 核且 ≥16GB）；
- 自动推导 `max_concurrency`（最大并发，默认 low=1 / mid=2 / high=4）与 `batch_size`（单批大小）；
- 提供 `recommend_subtasks(total)` 把大任务拆成「不超过并发数」的子任务，**避免一次性铺满 CPU/内存**。

调用方应读取 `hardware.profile()` 的结果来约束自己的并发与批处理，做到「自适应，不抢占用户资源」。语义缓存进一步减少重复 API 调用，间接降低本机网络与等待开销。

## 七、安全风险项（必读）

1. **密钥仅在内存中读取，从环境变量获取**；本技能**不写入、不读取、不打包任何 `.env` 或密钥文件**。请自行保管好环境变量与终端历史。
2. **网络调用只发往各厂商官方 API 域名**（见 `references/models.yaml` 的 `base_url`），不会发往任何第三方。文心/星火签名在本地完成。
3. **成本数据库与缓存为本地 SQLite 文件**（默认在用户目录，如 `~/.cn_llm_router/`），不上传、不含密钥，可随时 `cache clear` 删除。
4. **更新检查联网失败会静默跳过**，不会因此报错阻塞你的工作；更新地址默认指向 SkillHub，可在 `config.json` 改为你信任的地址。
5. **本技能不含任何可执行二进制 / 脚本类风险文件**（无 `.exe/.ps1/.bat/.sh/.vbs` 等），纯 `.py` 源码 + 文档 + 数据，可被只读审查。
6. **不收集任何个人隐私数据**：prompt 内容仅用于本地分类与缓存，默认不上报；如需成本聚合请自行管理本地数据库。

> 依赖风险：除讯飞星火的可选 `websocket-client` 外，本技能无任何强制第三方依赖（自研 YAML 解析、自研 WebSocket 签名），不存在供应链投毒面；不装该包时，星火调用会给出中文安装指引，不影响其余 7 家与全部离线功能。

## 八、能力边界（明确不做）

- ❌ 不托管、不代理、不存储你的厂商 API Key；密钥由你自己的环境变量负责。
- ❌ 不保证各厂商 API 的可用性、速率限制、内容合规——这些由各厂商侧决定，失败会返回中文报错（见下）。
- ❌ 不实现微调/训练/向量库/RAG 管线，这是一个「路由 + 成本 + 限流」层，不是 Agent 框架。
- ❌ 模型实际效果取决于厂商版本与配额；本技能的「最优模型」是基于**注册表里的价格/上下文/推理能力标签**的启发式推荐，非实时基准测试。
- ❌ 语义缓存为本地模糊匹配（余弦相似度阈值），可能误命中或漏命中，关键场景请用 `--no-cache`。
- ❌ 跨厂商价格随官方调整而变化，`references/models.yaml` 中的 `price_*` 是示例值，请以官方最新定价为准。

## 九、中文报错指引（常见问题 → 怎么办）

| 现象 / 报错 | 原因 | 解决 |
|------------|------|------|
| `当前未检测到任何厂商 API Key...` | 没设环境变量 | 按第四节 `export` 至少一家；或先 `route` 看建议 |
| `调用失败：HTTP 401` | Key 错误/过期 | 重新生成厂商 Key 并刷新环境变量 |
| `调用失败：HTTP 429` | 触发厂商限速 | 降低并发（见 `hardware`），或换策略/厂商 |
| `调用失败：HTTP 404` | 模型名不匹配 | 检查 `references/models.yaml` 中该厂商 `models[].name` |
| `调用失败：timed out` | 网络慢/超时 | 加大 `--timeout`（秒），或重试 |
| `未找到模型: xxx` | manual 指定模型不存在 | 用 `route --model provider:model` 时确认名称 |
| `解析注册表失败` | models.yaml 被改坏 | 用 `git diff` 还原或重新拉取技能 |
| `更新检查失败` | 无网络 | 正常，静默跳过；不影响使用 |

所有报错均为中文，且 `chat`/`route` 异常会被捕获后以 `❌ ...` 友好提示退出（不会抛 Python traceback）。

## 十、FAQ

**Q1：一定要配 Key 才能用吗？**
不一定。`route`（建议模式）、`hardware`、`report`、`cache`、`update-check`、`version` 都**不需要 Key**，可纯离线体验路由逻辑与硬件画像。

**Q2：怎么新增一个厂商？**
编辑 `references/models.yaml`，加一段 `providers.<新厂商>`（填 `adapter`/`base_url`/`env_hint`/`models`），若该厂商走 OpenAI 兼容协议则无需写代码；非兼容协议在 `scripts/adapters/` 加一个适配器即可，路由逻辑零改动。

**Q3：成本统计准吗？**
计费公式透明（`compute_cost(price, in, out)`），但依赖厂商返回的 `usage` 字段；流式输出无法拿精确 usage，会按字符粗估并标注，仅作参考，不作为精确账单。

**Q4：会拖慢我的电脑吗？**
不会。`hardware` 自动限制并发与批大小；调用是网络 I/O 密集型，不占 CPU；缓存减少重复调用。

**Q5：我的对话会被上传吗？**
不会。prompt 只在本地做分类与缓存，默认不上报任何服务器；成本库与缓存在你本地目录。

**Q6：支持流式吗？**
支持，`chat --stream`；流式下 usage 不精确（见 Q3）。

## 十一、更新提醒

本技能内置 `update-check` 命令：比对本地 `version.json` 与发布源版本号，若有新版会提示你升级。**建议在定时任务或每次使用前跑一次**：

```bash
python scripts/router.py update-check
```

升级方式：通过 SkillHub 或你常用的发布流程更新本技能即可。更新日志见各版本 `version.json` 的 `notes` 字段。

## 十二、安全与发布合规

- 本技能**已规避全部默认拦截文件类型**：包内仅含 `.py` 源码、`.md` 文档、`.yaml`/`.json` 数据，**不含** `.bat/.cmd/.ps1/.vbs/.exe/.dll/.lnk/.msi/.docx/.xlsx/.pptx/.iso/.dmg/.zip/.rar/.7z/.tar/.gz/.apk/.jar/.DS_Store/.env/.log/.tmp/.sh/.com/.scr/.hta/.reg` 等任何风险文件。
- 已通过「无硬编码密钥、核心无第三方依赖（讯飞星火仅可选 websocket-client）、纯标准库」的自检，可直接提交安全扫描。

## 十三、反馈与建议

有更好建议、遇到 bug、想加厂商，欢迎来信：**njskills@agent.qq.com**

---

*版本：v1.0.0 ｜ 许可：MIT ｜ 核心纯标准库（讯飞星火可选 websocket-client）、零密钥打包、可只读审计。*
