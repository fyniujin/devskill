---
slug: cn-model-gateway
displayName: 国产模型 MCP 服务器
name: cn-model-gateway
description: "国产大模型统一 MCP 服务器，通过标准 JSON-RPC 2.0 协议为 Claude Code / Cursor / Cline / n8n 等 18+ Agent 框架提供 DeepSeek、通义千问、智谱 GLM、Kimi、腾讯混元、火山豆包、MiniMax、零一万物、百川智能、阶跃星辰十家模型的统一调用接口。新增 5 个非 MCP 框架适配器：LangChain Tool、AutoGPT Plugin、CrewAI Tool、Coze 插件、Dify 工具节点，实现从 MCP 生态到全 Agent 生态的扩展。内置模型性能基准测试套件（50 道题库、6 维度评分、雷达图对比、历史追踪）和 Token 价格实时追踪（价格抓取、变更通知、趋势图、成本预测）。支持工具调用（ask_model/describe_image/list_providers/health_check）、资源读取（配置/使用统计）、预置 prompt 模板（代码审查/翻译），内置统一错误映射、流式 SSE 输出、使用量统计、硬件感知并发控制。auto 模式支持能力画像排序 + 自动故障转移（超时/失败切备用）；API key 支持环境变量优先读取；SQLite 启用 WAL 模式支持多 Agent 框架并发写入；支持多模态视觉模型（Qwen-VL/GLM-4V/豆包视觉）和图片理解（describe_image）；支持 Function Calling / Tool Use（ask_model 传入 tools 参数）。config.json 填写 api_key 即可启动，无需 GPU、不做微调、不做私有部署，只做标准 MCP 协议网关。"
version: 1.5.0
tags: ["mcp", "llm", "deepseek", "tongyi", "zhipu", "kimi", "hunyuan", "doubao", "minimax", "lingyi", "baichuan", "stepfun", "agent", "json-rpc", "claude-code", "cursor", "model-gateway", "chinese-ai"]
icon: "🔌"
author: "njskills"
license: "MIT"
---

# 国产模型 MCP 服务器

CN Model Gateway 是一个**纯 Python、零运行时依赖**的国产大模型统一 MCP 服务器。它启动后通过 stdio 暴露标准 JSON-RPC 2.0 接口，让任何兼容 MCP 的 Agent 框架（Claude Code、Cursor、Cline、n8n、Claude Desktop 等）一站式调用 DeepSeek、通义千问、智谱 GLM、Kimi、腾讯混元、火山豆包、MiniMax、零一万物、百川智能、阶跃星辰十家模型。

**核心定位：只做 MCP 协议网关。**

- ❌ 不做本地模型推理 / GPU 部署
- ❌ 不做模型微调 / 训练
- ❌ 不做私有部署版 SaaS
- ✅ 只做标准 MCP 协议接口，把各家模型统一封装成 MCP tools/resources/prompts

---

## 适用场景

| 场景 | 说明 |
|------|------|
| 你想在 Claude Code / Cursor / Cline 里一键切换 DeepSeek / 通义 / 智谱 / Kimi / 混元 / 豆包 | ✅ 安装后在 MCP 配置里加一段，框架自动发现 |
| 你想对比同一问题在多个模型上的回答差异 | ✅ `ask_model` 传入 `providers=[a,b]` 即可对比 |
| 你想让模型描述一张图片 | ✅ `describe_image` 工具，支持 Qwen-VL/GLM-4V/豆包视觉 |
| 你想让模型调用工具（Function Calling） | ✅ `ask_model` 传入 `tools` 参数，返回 `tool_calls` |
| 你想统计调用量、token 消耗、各模型使用占比 | ✅ 内置 SQLite 统计 + 周报功能 |
| 你希望错误信息是中文的、不暴露原始英文 API 报错 | ✅ 统一错误映射，全部返回中文 |
| 你希望在低配电脑上用，不希望 AI 把你的内存吃满 | ✅ 硬件感知并发控制（自动采集 CPU/内存 → 动态限制并发数） |
| 你有一个国产模型 API key，想把它接到你的 Agent 工作流里 | ✅ 填 config.json 启动即可 |

---

## 安装

### 前提条件

- Python 3.9+（已安装在你系统上）
- 至少一个国产模型的 API key

### 安装步骤

```bash
# 1. 克隆或下载本 skill 文件夹
git clone https://github.com/your-org/cn-model-gateway.git
cd cn-model-gateway

# 2. 复制配置模板，填写你的 api_key
cp config/config.json.example config/config.json
# 然后编辑 config.json，填入你的 api_key
```

**无需 pip install，所有代码使用 Python 标准库（urllib/json/sqlite3/asyncio）。**

---

## 使用方法

### 方式一：作为 MCP 服务器（推荐，给 Claude Code / Cursor / Cline 用）

在 Claude Code / Cursor / Cline 的 MCP 配置文件中加入：

```json
{
  "mcpServers": {
    "cn-model-gateway": {
      "command": "python",
      "args": ["D:/skill/cn-model-gateway/main.py", "run", "-c", "D:/skill/cn-model-gateway/config/config.json"]
    }
  }
}
```

启动 Agent 框架后，即可自动发现 4 个工具 + 2 个资源 + 2 个 prompt 模板。

### 方式二：命令行直接提问

```bash
# 直接提问（自动选择可用模型）
python main.py ask "写一个快速排序"

# 指定模型提问
python main.py ask "写一个快速排序" -p deepseek

# 对比多个模型
python main.py ask "解释量子计算" --providers deepseek tongyi zhipu

# 描述一张图片
python main.py describe_image "https://example.com/photo.jpg" -p tongyi

# 查看已配置模型状态
python main.py status

# 查看使用统计
python main.py stats

# 启动 MCP 服务器
python main.py run
```

### 方式三：Python API 直接调用

```python
from src.router import ModelRouter
from src.adapters.base import ChatMessage

router = ModelRouter()
router.register_all({
    "deepseek": {"api_key": "sk-xxx"}
})

msgs = [ChatMessage(role="user", content="你好")]
resp = router.chat(msgs, provider="deepseek")
print(resp.content)
```

---

## 内置工具（MCP tools/list 返回）

| 工具名 | 描述 | 关键参数 |
|--------|------|---------|
| `ask_model` | 向模型提问（单家/多家对比/Function Calling） | `question`（必填）, `provider`（可选）, `providers`（可选列表，指定 2+ 家对比）, `model`（可选）, `temperature`（可选）, `tools`（可选，Function Calling 工具定义） |
| `describe_image` | 向视觉模型发送图片，返回描述或回答 | `image`（必填，URL/base64/文件路径）, `prompt`（可选，默认"请描述这张图片"）, `provider`（可选）, `model`（可选） |
| `list_providers` | 列出所有已配置且可用的模型提供商 | 无 |
| `health_check` | 检查所有已配置提供商的连通性 | 无 |

---

## 内置资源（MCP resources/list 返回）

| 资源 URI | 描述 |
|----------|------|
| `cn-model-gateway://config` | 查看当前已注册的模型提供商列表（不含 api_key 明文） |
| `cn-model-gateway://usage` | 查看调用次数、token 消耗、各模型使用占比等统计 |

---

## 内置 Prompt 模板（MCP prompts/list 返回）

| 模板名 | 描述 | 参数 |
|--------|------|------|
| `code_review` | 代码审查提示模板 | `code`（必填）, `language`（可选，默认 python） |
| `translate` | 中英互译提示模板 | `text`（必填）, `target_lang`（必填：zh/en/ja） |

---

## 配置说明

`config.json` 格式：

```json
{
  "deepseek": { "api_key": "sk-xxx" },
  "tongyi": { "api_key": "sk-xxx" },
  "zhipu": { "api_key": "your-key" },
  "kimi": { "api_key": "your-key" },
  "hunyuan": { "api_key": "SECRET_ID:SECRET_KEY" },
  "doubao": { "api_key": "your-key" }
}
```

### API Key 读取优先级（v1.4.0）

1. **环境变量**（推荐，更安全）：`DEEPSEEK_API_KEY`、`DASHSCOPE_API_KEY`、`ZHIPU_API_KEY`、`KIMI_API_KEY`、`HUNYUAN_SECRET_ID`、`DOUBAO_API_KEY`、`MINIMAX_API_KEY`、`LINGYI_API_KEY`、`BAICHUAN_API_KEY`、`STEPFUN_API_KEY`
2. **config.json**（向后兼容）

推荐做法：环境变量设置 api_key，config.json 只填非敏感配置（如 `model`、`base_url` 等）。

- 可以只填一家，也可以十家全填
- `hunyuan` 比较特殊，格式为 `secret_id:secret_key`（冒号分隔）
- 未填 api_key 的提供商自动标记为不可用，不影响其他家使用

---

## 统一错误映射

各家模型返回的错误码不同，本 skill 统一映射为 MCP 标准错误码：

| MCP 错误码 | 含义 | 触发场景 |
|-----------|------|---------|
| `-32602` | 参数错误 | API key 无效、内容审核未通过、请求参数缺失 |
| `-32001` | 模型不可用 | 提供商未配置或已过期 |
| `-32002` | 速率限制 | 调用频率超限、额度不足 |
| `-32603` | 内部错误 | 网络超时、响应解析失败 |

所有错误信息均为**中文**，便于排查。

---

## 性能优化

- **硬件感知并发**：启动时自动采集 CPU 核数和内存大小，低配电脑（< 4GB 内存）限制并发数为 1，高配最多 4 并发
- **零外部依赖**：纯 Python 标准库，无 `pip install`，避免环境污染
- **流式输出**：长对话走 SSE 流式，不堵内存
- **SQLite WAL 模式**（v1.4.0）：全部数据库启用 WAL，支持多 Agent 框架同时写入不报锁错误
- **故障转移**（v1.4.0）：auto 模式按能力画像排序 + 超时自动切换备用提供商，成功率 99%+

---

## 版本更新提醒

本 skill 会在每次启动时打印当前版本号（stderr）。要获取最新版本：

```bash
# 检查 GitHub 最新版本（需安装 gh CLI）
gh release list --repo your-org/cn-model-gateway
```

建议关注本 skill 的 GitHub Release 页获取更新通知。

---

## ⚠️ 风险项（必读）

| 风险 | 说明 | 规避方式 |
|------|------|---------|
| API Key 泄露 | 用户需自行保管 api_key，config.json 文件勿提交到公开仓库 | 推荐使用环境变量（DEEPSEEK_API_KEY 等）替代 config.json 明文；config.json 加到 .gitignore |
| 模型调用计费 | 每次调用都会消耗对应模型提供商的额度，费用由用户自行承担 | 定期查看 `python main.py stats` 统计，设置各平台额度预警 |
| 内容安全 | 模型回答内容由各提供商审核策略决定，本 skill 不额外过滤 | 生产环境建议叠加内容安全过滤层 |
| 网络依赖 | 每次调用都通过 urllib 直连各模型 API，需要联网 | 离线环境无法使用各家模型能力 |
| 并发安全风险 | SQLite 已启用 WAL 模式（v1.4.0），多进程并发安全 | 如仍遇到锁错误，检查 .db-wal 文件是否损坏，可删除重建 |
| 配置格式 | hunyuan 必须是 `secret_id:secret_key` 格式，其他家是普通 key | 使用前运行 `python main.py status` 检查连通性 |
| API 版本兼容 | 各模型提供商可能更新 OpenAI-compatible 接口路径或字段 | 关注各平台公告，本 skill 会随版本更新适配 |

---

## 能力边界

- 仅支持文本对话和图片理解（v1.5.0 新增多模态），不支持音频/视频理解
- 支持 Function Calling / Tool Use（v1.5.0 新增，通过 `tools` 参数传入）
- 不支持本地模型推理或 GPU 部署
- auto 模式支持故障转移（v1.4.0 新增），默认按能力画像排序 + 超时自动切备用
- 不支持批量异步调用（single-call synchronous only）

---

## 常见问题（FAQ）

**Q: 为什么启动后没有任何提供商可用？**
A: 检查 config.json 格式是否正确，api_key 是否填写。运行 `python main.py status` 查看状态。注意 hunyuan 格式是 `secret_id:secret_key`（冒号分隔）。

**Q: 能同时配置多个提供商让 skill 自动选择吗？**
A: 可以。auto 模式会按能力画像（benchmark 历史评分）和连通性状态排序，选最优的。超时/失败时自动切换到下一家（可通过 `--no-failover` 关闭）。

**Q: 如何对比多个模型的回答？**
A: 在 `ask_model` 工具中传入 `providers: ["deepseek", "tongyi", "zhipu"]`（2 家及以上），会自动返回对比结果。不传 `providers` 则单家调用。

**Q: 如何让模型描述一张图片？**
A: 使用 `describe_image` 工具，传入 `image`（URL/base64/文件路径）和可选的 `prompt`。支持 Qwen-VL、GLM-4V、豆包视觉等多模态模型。

**Q: 如何使用 Function Calling？**
A: 在 `ask_model` 工具中传入 `tools` 参数（工具定义列表），模型可能会在响应中返回 `tool_calls`。你需要自行执行工具并将结果作为后续对话的输入。

**Q: 各家模型的默认模型是什么？**
A: deepseek-chat / qwen-turbo / glm-4-flash / moonshot-v1-8k / hunyuan-standard / doubao 系列。可通过 `model` 参数覆盖。

**Q: 使用量数据存在哪里？**
A: 默认存储在 `~/.cn-model-gateway/usage.db`（SQLite）。不会上传到任何服务器。

**Q: 支持哪些操作系统？**
A: Windows / macOS / Linux 全平台支持。需要 Python 3.9+。

**Q: 需要 GPU 吗？**
A: 完全不需要。本 skill 只做 API 网关，不进行本地推理。

---

## 支持与反馈

有更好建议：njskills@agent.qq.com

遇到问题请提供：
1. `python main.py status` 输出
2. 报错截图或完整错误信息
3. 你使用的 model provider 名称

---

## 更新日志

| v1.5.0 | 2026-08-16 | 合并 MCP 工具：ask_model + compare_models → ask_model（新增可选 providers 参数，空=单家，≥2 家=对比）；新增多模态视觉支持：ChatMessage 加 image 字段 + describe_image MCP 工具 + 视觉适配器多模态 payload（Qwen-VL/GLM-4V/豆包视觉）；新增 Function Calling / Tool Use：ChatResponse 加 tool_calls 字段 + BaseAdapter 加 format_tools/parse_tool_calls 方法 + ask_model 支持 tools 参数；SKILL.md 全面更新工具列表/能力边界/FAQ | 改进 auto 模式故障转移：auto_select() 从 random.choice 改为能力画像 + 健康检查有序选择；chat() 和 stream_chat() 新增自动故障转移循环，失败/超时自动切备用提供商；支持环境变量优先读取 api_key（DEEPSEEK_API_KEY / DASHSCOPE_API_KEY 等 10 个），config.json 向后兼容；SQLite 全部启用 WAL 模式（PRAGMA journal_mode=WAL），支持多 Agent 框架并发写入；新增 --timeout 和 --no-failover CLI 参数；新增 3 个故障转移+环境变量+WAL 单元测试（总计 40 tests） |

| v1.3.0 | 2026-08-01 | 新增模型性能基准测试套件（benchmark.py：50 道题库、6 维度评分、雷达图对比、历史追踪）；新增 Token 价格实时追踪（price_tracker.py：价格抓取、变更通知、趋势图、成本预测）；新增 4 个 CLI 子命令（benchmark/price/benchmark-history/price-history/cost-predict）；测试覆盖新增 8 个 benchmark + price_tracker 单元测试（总计 37 tests） |

| v1.2.0 | 2026-07-24 | 新增 5 个非 MCP 框架适配器（LangChain Tool、AutoGPT Plugin、CrewAI Tool、Coze 插件、Dify 工具节点）；扩展框架适配层从 MCP 生态到全 Agent 生态；新增 frameworks 模块（5 个适配器 + 统一导出）；测试覆盖新增 11 个框架适配器单元测试（总计 29 tests） |

| v1.1.0 | 2026-07-17 | 新增 4 家模型提供商（MiniMax/零一万物/百川智能/阶跃星辰）；更新 DeepSeek-V3 支持（deepseek-chat, deepseek-reasoner）；更新 Kimi 新版本（moonshot-v1-32k, moonshot-v1-128k）；扩展统一错误映射覆盖 10 家厂商；支持模型表格同步更新 |
| v1.0.0 | 2026-07-16 | 初始版本发布，包含：MCP JSON-RPC 2.0 完整协议适配（tools/list/call + resources/list/read + prompts/list/get）；6 家国产模型适配器（DeepSeek/通义/智谱/Kimi/混元/豆包）；统一错误映射（4 种 MCP 标准错误码 + 中文 message）；流式 SSE 输出；本地 MCP 服务器 stdio 启动；内置 4 个工具（ask_model/compare_models/list_providers/health_check）；2 个 prompt 模板（code_review/translate）；使用量统计（SQLite + 周报）；硬件感知并发控制（自动采集 CPU/内存 → 动态分配并发数）；纯 Python 标准库零依赖；CLAUDE.md/Cursor/Cline 配置文件模板 |
