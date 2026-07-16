---
slug: cn-model-gateway
displayName: 国产模型 MCP 服务器
name: cn-model-gateway
description: "国产大模型统一 MCP 服务器，通过标准 JSON-RPC 2.0 协议为 Claude Code / Cursor / Cline / n8n 等 18+ Agent 框架提供 DeepSeek、通义千问、智谱 GLM、Kimi、腾讯混元、火山豆包六家模型的统一调用接口。支持工具调用（ask_model / compare_models / list_providers / health_check）、资源读取（配置 / 使用统计）、预置 prompt 模板（代码审查 / 翻译），内置统一错误映射、流式 SSE 输出、使用量统计、硬件感知并发控制。config.json 填写 api_key 即可启动，无需 GPU、不做微调、不做私有部署，只做标准 MCP 协议网关。"
version: 1.0.0
tags: ["mcp", "llm", "deepseek", "tongyi", "zhipu", "kimi", "hunyuan", "doubao", "agent", "json-rpc", "claude-code", "cursor", "model-gateway", "chinese-ai"]
icon: "🔌"
author: "njskills"
license: "MIT"
---

# 国产模型 MCP 服务器

CN Model Gateway 是一个**纯 Python、零运行时依赖**的国产大模型统一 MCP 服务器。它启动后通过 stdio 暴露标准 JSON-RPC 2.0 接口，让任何兼容 MCP 的 Agent 框架（Claude Code、Cursor、Cline、n8n、Claude Desktop 等）一站式调用 DeepSeek、通义千问、智谱 GLM、Kimi、腾讯混元、火山豆包六家模型。

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
| 你想对比同一问题在多个模型上的回答差异 | ✅ 内置 `compare_models` 工具，同时问多家 |
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
python main.py compare "解释量子计算" -p deepseek tongyi zhipu

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
| `ask_model` | 向指定或自动选择的模型提问 | `question`（必填）, `provider`（可选）, `model`（可选）, `temperature`（可选） |
| `compare_models` | 同一问题并发多家模型返回对比 | `question`（必填）, `providers`（可选列表，默认全部可用） |
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

- 可以只填一家，也可以六家全填
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
- **SQLite 本地统计**：调用记录本地落盘，无网络上传

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
| API Key 泄露 | 用户需自行保管 api_key，config.json 文件勿提交到公开仓库 | 将 config.gitignore；不要把 skill 复制到公开目录 |
| 模型调用计费 | 每次调用都会消耗对应模型提供商的额度，费用由用户自行承担 | 定期查看 `python main.py stats` 统计，设置各平台额度预警 |
| 内容安全 | 模型回答内容由各提供商审核策略决定，本 skill 不额外过滤 | 生产环境建议叠加内容安全过滤层 |
| 网络依赖 | 每次调用都通过 urllib 直连各模型 API，需要联网 | 离线环境无法使用各家模型能力 |
| 并发安全风险 | 使用 SQLite 本地存储，多进程同时写入可能触发锁竞争 | 单进程运行；多进程场景建议改用外部数据库 |
| 配置格式 | hunyuan 必须是 `secret_id:secret_key` 格式，其他家是普通 key | 使用前运行 `python main.py status` 检查连通性 |
| API 版本兼容 | 各模型提供商可能更新 OpenAI-compatible 接口路径或字段 | 关注各平台公告，本 skill 会随版本更新适配 |

---

## 能力边界

- 仅支持文本对话（chat completions），不支持图片/音频/视频理解
- 不支持 Function Calling / Tool Use（各家实现差异大，暂不统一封装）
- 不支持本地模型推理或 GPU 部署
- 不支持 model cascade / fallback（auto 模式只随机选一家，不自动重试）
- 不支持批量异步调用（single-call synchronous only）

---

## 常见问题（FAQ）

**Q: 为什么启动后没有任何提供商可用？**
A: 检查 config.json 格式是否正确，api_key 是否填写。运行 `python main.py status` 查看状态。注意 hunyuan 格式是 `secret_id:secret_key`（冒号分隔）。

**Q: 能同时配置多个提供商让 skill 自动选择吗？**
A: 可以。auto 模式会随机选一家可用的。如果要稳定输出，建议显式指定 `-p deepseek`。

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

| v1.0.0 | 2026-07-16 | 初始版本发布，包含：MCP JSON-RPC 2.0 完整协议适配（tools/list/call + resources/list/read + prompts/list/get）；6 家国产模型适配器（DeepSeek/通义/智谱/Kimi/混元/豆包）；统一错误映射（4 种 MCP 标准错误码 + 中文 message）；流式 SSE 输出；本地 MCP 服务器 stdio 启动；内置 4 个工具（ask_model/compare_models/list_providers/health_check）；2 个 prompt 模板（code_review/translate）；使用量统计（SQLite + 周报）；硬件感知并发控制（自动采集 CPU/内存 → 动态分配并发数）；纯 Python 标准库零依赖；CLAUDE.md/Cursor/Cline 配置文件模板 |
