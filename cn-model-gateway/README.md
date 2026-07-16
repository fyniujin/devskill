# CN Model Gateway（国产模型 MCP 服务器）

> 国产大模型统一 MCP 服务器，通过标准 JSON-RPC 2.0 协议为 Claude Code / Cursor / Cline / n8n 等 Agent 框架提供 DeepSeek、通义千问、智谱 GLM、Kimi、腾讯混元、火山豆包六家模型的统一调用接口。

## 核心特性

- **标准 MCP 协议**：完整实现 JSON-RPC 2.0，tools/list/call + resources/list/read + prompts/list/get
- **6 家国产模型**：DeepSeek / 通义千问 / 智谱 GLM / Kimi / 腾讯混元 / 火山豆包
- **统一错误映射**：各厂商错误码统一映射为 MCP 标准错误码，全中文提示
- **流式 SSE 输出**：长对话实时返回，不堵内存
- **开箱即用**：4 个内置工具 + 2 个资源 + 2 个 prompt 模板
- **硬件感知**：自动采集 CPU/内存 → 动态限制并发，不吃满你的电脑
- **纯标准库**：零外部依赖，Python 3.9+ 直接跑

## 快速开始

```bash
git clone https://github.com/your-org/cn-model-gateway.git
cd cn-model-gateway
cp config/config.json.example config/config.json
# 编辑 config.json 填入你的 api_key
python main.py run        # 启动 MCP 服务器（stdio 模式）
python main.py ask "写一个快速排序"
python main.py status     # 查看模型提供商状态
python main.py stats      # 查看使用统计
```

## 配置 Claude Code / Cursor / Cline

在 MCP 配置文件中加入：

```json
{
  "mcpServers": {
    "cn-model-gateway": {
      "command": "python",
      "args": ["/path/to/cn-model-gateway/main.py", "run"]
    }
  }
}
```

## 支持模型

| 提供商 | 默认模型 | 特殊说明 |
|--------|---------|---------|
| DeepSeek | deepseek-chat | 普通 API key |
| 通义 (DashScope) | qwen-turbo | OpenAI-compatible 端点 |
| 智谱 | glm-4-flash | 普通 API key |
| Kimi (Moonshot) | moonshot-v1-8k | 普通 API key |
| 混元 | hunyuan-standard | api_key 格式：`secret_id:secret_key` |
| 豆包 (Volcengine) | ep-xxxxx | 普通 API key |

## 架构

```
cn-model-gateway/
├── main.py                    ← CLI 入口
├── src/
│   ├── adapters/              ← 6 家模型适配器
│   │   ├── base.py            ← 抽象基类
│   │   ├── deepseek.py
│   │   ├── tongyi.py
│   │   ├── zhipu.py
│   │   ├── kimi.py
│   │   ├── hunyuan.py         ← 特殊签名机制
│   │   └── doubao.py
│   ├── router.py              ← 路由 + 统一错误映射
│   ├── mcp_server.py          ← MCP JSON-RPC 2.0 实现
│   ├── monitor.py             ← 使用量统计 + 硬件感知
│   └── utils.py               ← 工具函数
├── config/
│   └── config.json.example    ← 配置模板
└── tests/
    └── test_basic.py          ← 基础测试
```

## License

MIT

## 联系

njskills@agent.qq.com
