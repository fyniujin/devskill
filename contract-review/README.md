# 合同智能审查 Skill (contract-review) v2.5

中文合同智能风险审查工具，支持 PDF / Word / 图片 / 纯文本，通过"规则引擎 + LLM 语义审查"双轨机制识别合同风险，输出结构化审查报告。

## 🆕 v2.4 新特性

- 🔒 **安全性增强**：魔术字节校验、50MB 文件上限、个人信息脱敏、安全 YAML 加载
- 📊 **评分可视化**：扣分逻辑透明化，评分依据一目了然
- 🪄 **首次使用向导**：引导选择运行模式（Ollama 本地 / OpenAI API / 规则引擎）
- 🦙 **Ollama 一键安装**：内建本地模型安装向导
- 📈 **实时进度显示**：每步有状态图标（⏳/✅/⚠️）
- 🚀 **更强易用性**：安装即用，无需配置即可使用基础审查功能
- 📍 **风险定位更准确**：页码+条款编号双重定位，不再显示"第?页"
- 📦 **标准化打包**：pip install -e . 一键安装

## 快速开始

```bash
# 1. pip 安装
pip install -e .

# 2. 运行首次向导
python scripts/main.py --first-time

# 3. 审查合同
python scripts/main.py 合同文件.pdf

# 4. 指定视角
python scripts/main.py 劳动合同.docx --role 乙方 --scope 全面审查

# 5. 保存报告
python scripts/main.py 买卖合同.pdf --output 报告.md
```

## 三种运行模式

| 模式 | 说明 | 需要 |
|------|------|------|
| 🥇 **Ollama 本地** | 完全本地运行，隐私最优 | 下载 Ollama + 模型（约4-8GB） |
| 🥈 **OpenAI API** | 效果最佳 | OpenAI API 密钥 |
| 🥉 **规则引擎** | 开箱即用，无需额外配置 | 无（推荐新手） |

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `file` | 合同文件路径 | - |
| `--type, -t` | 合同类型 | 自动识别 |
| `--role, -r` | 审查视角（甲方/乙方/双方）| 双方 |
| `--output, -o` | 输出文件路径 | report.md |
| `--format, -f` | 输出格式（markdown/json）| markdown |
| `--scope` | 审查范围 | 全面审查 |
| `--no-llm` | 跳过 LLM 审查 | false |
| `--text, -x` | 直接传入合同文本 | - |
| `--install-ollama` | 安装 Ollama 本地模型 | - |
| `--first-time` | 首次使用向导 | - |
| `--verbose, -v` | 显示详细日志 | false |

## 文件结构

```
contract-review/
├── SKILL.md                   ← Skill 定义（v2.4，含完整文档）
├── README.md                  ← 本文件
├── pyproject.toml             ← pip 安装配置
├── requirements.txt           ← 依赖列表（备选安装）
├── references/                ← 参考文件
│   ├── risk_rules.yaml        ← 26条风险规则
│   ├── contract_types.yaml    ← 10种合同类型定义
│   ├── modification_templates.yaml ← 22个修改范本
│   ├── legal_basis.md         ← 法律法规依据（2026年现行有效）
│   └── compliance_checklist.md ← 5套合规检查清单
├── scripts/                   ← Python 脚本
│   ├── extract_text.py        ← 多格式文本提取（安全校验+OCR进度）
│   ├── parse_structure.py     ← 合同结构解析
│   ├── rule_engine.py         ← 规则引擎（安全加载+长度限制）
│   ├── llm_review.py          ← LLM 审查（自动检测多后端）
│   ├── generate_report.py     ← 报告生成（评分说明+脱敏）
│   └── main.py                ← 主入口（首次向导+进度显示）
└── assets/
    └── report_template.md     ← 报告模板
```

## 安装 Ollama（推荐免费方案）

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5:7b
ollama serve

# Windows
# 访问 https://ollama.ai/download 下载 OllamaSetup.exe 安装后：
ollama pull qwen2.5:7b
ollama serve
```

## 评分说明

综合评分（0-100 分，分数越高风险越低）：
- **90-100**：风险较低，可放心签署
- **70-89**：风险中等，建议修改后签署
- **50-69**：风险偏高，需要认真修改
- **0-49**：风险很高，强烈建议咨询律师

**扣分规则**：
- 🔴 严重：-15 分/项
- 🟡 中等：-8 分/项
- 🟢 一般：-3 分/项
- ℹ️ 提示：不扣分

## 安全特性

1. **魔术字节校验**：检查文件实际类型与后缀是否一致，防止恶意文件伪装
2. **文件大小限制**：单文件最大 50MB，防止 DoS 攻击
3. **YAML 安全加载**：使用 `safe_load` 防止反序列化攻击
4. **正则安全检查**：限制正则表达式长度，防止 ReDoS 攻击
5. **个人信息脱敏**：报告中的身份证号、手机号自动替换为 ***
6. **日志隐私保护**：不输出完整文件路径和合同原文到日志
7. **输入长度限制**：规则引擎最大处理 500KB 文本
8. **纯文本模式隐私**：--text 模式下用户粘贴的文本不会写入日志文件

## 免责声明

本报告由 AI 生成，仅供使用者参考，不构成法律意见。对于重大合同（标的额超过 100 万元或涉及核心商业利益），建议咨询专业执业律师。

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.5.0 | 2026-07-04 | 版本号修复 |
| v2.0.0 | 2026-07-04 | 安全性增强、Ollama 向导、首次使用向导、评分可视化 |
| v1.0.0 | 2026-07-02 | 初始版本 |
