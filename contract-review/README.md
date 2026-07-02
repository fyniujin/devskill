# 合同智能审查 Skill (contract-review)

中文合同智能风险审查工具，支持 PDF / Word / 图片 / 纯文本，通过"规则引擎 + LLM 语义审查"双轨机制识别合同风险，输出结构化审查报告。

## 特性

- 多格式支持：PDF（文字/扫描）、Word、图片、纯文本
- 智能文本提取：自动识别文件格式，保留页码和段落结构
- 双轨风险审查：规则引擎（硬规则匹配）+ LLM 语义审查（深度分析）
- 专项合规检查：劳动合同、技术开发、买卖、租赁、融资协议等
- 分级报告输出：🔴严重 / 🟡中等 / 🟢一般 / ℹ️提示
- 修改建议 + 标准范本：每个风险点附具体改法和推荐表述

## 安装

```bash
# 方式一：一键安装
install.bat

# 方式二：手动安装
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 使用方法

### 命令行使用

```bash
# 基础审查
python scripts/main.py 合同文件.pdf

# 指定合同类型和审查视角
python scripts/main.py 劳动合同.docx --type 劳动合同 --role 乙方

# 输出到文件
python scripts/main.py 买卖合同.pdf --output 报告.md

# 仅规则引擎（跳过 LLM）
python scripts/main.py 租赁合同.pdf --no-llm

# 直接审查文本
python scripts/main.py --text "合同内容..." --type 买卖合同
```

### 在 WorkBuddy 中使用

上传合同文件并说：
- "帮我审查这个合同"
- "这个合同有没有风险？"
- "检查一下合同中的风险点"

## 文件结构

```
contract-review/
├── SKILL.md                          # Skill 定义（核心）
├── README.md                         # 使用说明
├── requirements.txt                  # Python 依赖
├── install.bat                       # Windows 安装脚本
├── references/                       # 参考文件
│   ├── risk_rules.yaml               # 风险规则库
│   ├── contract_types.yaml           # 合同类型定义
│   ├── modification_templates.yaml   # 修改建议模板
│   ├── legal_basis.md                # 法律法规依据
│   └── compliance_checklist.md       # 合规检查清单
├── scripts/                          # Python 脚本
│   ├── extract_text.py               # 多格式文本提取
│   ├── parse_structure.py            # 合同结构解析
│   ├── rule_engine.py                # 规则引擎
│   ├── llm_review.py                 # LLM 审查
│   ├── generate_report.py            # 报告生成
│   └── main.py                       # 主入口
└── assets/                           # 模板和素材
    └── report_template.md            # 报告模板
```

## 评分说明

综合评分（0-100 分，分数越高风险越低）：
- 90-100：风险较低，可放心签署
- 70-89：风险中等，建议修改后签署
- 50-69：风险偏高，需要认真修改
- 0-49：风险很高，强烈建议咨询律师

## 免责声明

本报告由 AI 生成，仅供使用者参考，不构成法律意见。对于重大合同（标的额超过 100 万元或涉及核心商业利益），建议咨询专业执业律师。

## 版本

v1.0.0 - 2026-07-02
