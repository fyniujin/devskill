# 企业微信语音消息 Agent Skill

## 概述

一个轻量级的企业微信语音消息 AI Agent 技能。监听企业微信智能机器人接收到的语音消息，自动进行意图识别、任务执行、多轮对话管理和语音回复。

## ✨ 核心特性

- **零 API Key 依赖** - 企业微信内置 ASR 语音转文字免费使用
- **硬件自适应** - 自动检测用户电脑配置，调整并发和缓存策略
- **多轮对话** - 支持上下文保持的连续对话
- **性能优先** - 低配电脑也能流畅运行
- **安全可靠** - 所有数据处理在本地完成，不上传用户隐私

## 📁 项目结构

```
wecom-voice-agent/
├── SKILL.md                      # 技能主文件（包含可运行命令）
├── README.md                     # 项目说明
├── references/
│   └── wecom_bot_api.md          # 企业微信机器人 API 参考
└── scripts/
    ├── detect_hardware.py        # 硬件检测脚本
    ├── voice_simulator.py        # 语音消息模拟器
    └── session_manager.py        # 会话管理器
```

## 🚀 快速开始

### 1. 安装

```bash
# 方式1：从 SkillHub 安装
skillhub install wecom-voice-agent

# 方式2：本地安装
cd D:/skill/wecom-voice-agent
```

### 2. 硬件检测

```bash
python D:/skill/wecom-voice-agent/scripts/detect_hardware.py
```

### 3. 本地模拟测试

```bash
# 模拟语音消息回调
python D:/skill/wecom-voice-agent/scripts/voice_simulator.py --text "明天有什么会议"
```

### 4. 会话管理

```bash
# 创建新会话
python D:/skill/wecom-voice-agent/scripts/session_manager.py create --userid zhangsan

# 查看会话
python D:/skill/wecom-voice-agent/scripts/session_manager.py get --session_id <id> --format table

# 查看所有会话统计
python D:/skill/wecom-voice-agent/scripts/session_manager.py stats

# 清理过期会话
python D:/skill/wecom-voice-agent/scripts/session_manager.py cleanup
```

## 🔧 配置说明

本技能**无需额外配置文件**即可运行。

如需自定义，可在工作目录创建 `.workbuddy/wecom-voice-agent.yaml`：

```yaml
tts_engine: edge  # edge 或 volcengine
log_level: info
session_timeout: 60
max_history: 5
```

## 📋 支持的语音命令示例

| 命令示例 | 功能 |
|---------|------|
| "明天有什么会议？" | 查询日程 |
| "提醒我下午3点提交报告" | 创建待办 |
| "北京今天天气怎么样？" | 查询天气 |
| "发消息给张三：明天开会" | 发送消息 |
| "你能做什么？" | 获取帮助 |
| "退出语音模式" | 切换到文字模式 |

## ⚠️ 限制与边界

- 仅支持企业微信智能机器人场景
- 不支持主动外呼电话
- 语音消息限 60 秒以内
- 当前仅支持单聊（`chattype: single`）

## 🔐 隐私声明

- 本技能**不存储、不上传、不转发**用户的语音数据
- 语音转写完全由企业微信官方接口完成
- 用户在对话中的文本数据仅保存在本地会话缓存中
- 会话过期后（默认60秒无活动）自动清理

## 📧 建议与反馈

如有更好的建议或遇到问题，欢迎发送邮件至：

**njskills@agent.qq.com**

## 📜 许可证

MIT License

© 2026 njskills. 保留所有权利。
