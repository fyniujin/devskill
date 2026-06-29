---
name: tax-receipt-compliance
slug: tax-receipt-compliance
displayName: 财税合规全链路助手
description: 财税合规全链路助手：发票OCR识别→真伪查验→报销单自动填充→对接审批系统。企业自主配置，数据本地处理。
version: 1.0.0
category: 财税管理
platforms: [WorkBuddy, QClaw, ima, Claude Code, Cursor]
---

# 财税合规全链路助手

## 功能说明

本Skill提供从发票识别到审批提交的全链路财税合规能力。所有功能基于企业自主配置，发票数据本地处理，不依赖任何第三方服务。

### 核心能力

| 模块 | 功能 | 输入 | 输出 |
|------|------|------|------|
| 1. 发票OCR识别 | 基于Tesseract本地引擎识别增值税发票、普通发票、电子发票 | 发票图片路径 | 结构化JSON数据 |
| 2. 真伪查验 | 预留多种查验引擎接口，企业自主配置 | 发票代码/号码/金额 | 查验结果 |
| 3. 报销单填充 | 自适应学习企业模板，自动填充报销单 | 发票数据 + 模板路径 | 填充后的Excel文件 |
| 4. 审批对接 | 预留主流审批平台接口，企业自主配置 | 报销单文件 + 配置 | 审批提交结果 |

### 设计理念

- **数据安全**：所有发票数据仅在本地处理，不会上传到任何服务器
- **企业自主**：查验引擎、审批平台的选择完全由企业自主决定
- **透明开源**：所有脚本代码透明可审计，无隐藏后门
- **渐进披露**：基础功能即装即用，高级功能需企业配置

## 触发词

- "识别发票" / "OCR发票" / "扫描发票"
- "查验发票" / "查发票真伪" / "发票验证"
- "生成报销单" / "填报销单" / "费用报销"
- "提交审批" / "报销审批" / "发起审批"

## 使用方法

### 快速开始

#### 第一步：安装依赖

运行安装脚本，安装Tesseract OCR引擎：

```bash
# Windows (PowerShell)
.\scripts\install_tesseract.ps1

# Linux/macOS (bash)
bash ./scripts/install_tesseract.sh
```

> ⚠️ 若自动安装失败，请手动前往 https://github.com/UB-Mannheim/tesseract/wiki 下载安装

#### 第二步：企业配置

复制配置模板并编辑：

```bash
cp templates/config_template.yaml config.yaml
# 编辑config.yaml，填写您的企业配置
```

#### 第三步：开始使用

```bash
# 识别发票
python scripts/ocr_engine.py --input path/to/invoice.png --output receipt_data.json

# 查验真伪（需先在config.yaml中配置查验引擎）
python scripts/verify_abstract.py --config config.yaml --receipt receipt_data.json

# 生成报销单
python scripts/template_matcher.py --config config.yaml --receipt receipt_data.json --template path/to/expense_template.xlsx

# 提交审批（需先在config.yaml中配置审批平台）
python scripts/approval_abstract.py --config config.yaml --expense expense_output.xlsx
```

### 配置详解

详细配置说明见 `references/setup-guide.md`。

## 示例

### 示例1：识别单张发票

**输入**：
```
识别发票 D:\invoices\20260628_001.png
```

**处理过程**：
1. 图像预处理（灰度化 → 去噪 → 二值化 → 纠偏）
2. Tesseract OCR识别
3. 结构化解析（匹配发票字段）
4. 输出JSON数据

**输出**：
```json
{
  "invoice_type": "增值税专用发票",
  "invoice_code": "3100204130",
  "invoice_number": "00564189",
  "invoice_date": "2026-06-28",
  "seller_name": "上海某某科技有限公司",
  "buyer_name": "北京某某信息技术有限公司",
  "amount": 10000.00,
  "tax_rate": 0.13,
  "tax_amount": 1300.00,
  "total": 11300.00,
  "remark": "*信息技术服务费*",
  "confidence": 0.96,
  "raw_text": "增值税专用发票 发票代码：3100204130 发票号码：00564189..."
}
```

### 示例2：批量识别并生成报销单

**输入**：
```
批量识别 D:\invoices\ 并用模板 templates\expense_basic.xlsx 生成报销单
```

**处理过程**：
1. 遍历目录下所有PNG/JPG/PDF文件
2. 逐张OCR识别
3. 汇总有效发票数据
4. 按模板映射关系填充
5. 输出合并后的报销单

**输出**：
```
已识别 5 张发票，合计金额 ¥23,450.00
报销单已生成：D:\skill\tax-receipt-compliance\output\expense_report_20260628.xlsx
```

### 示例3：查验发票真伪

**输入**：
```
查验发票 代码:3100204130 号码:00564189 日期:2026-06-28 金额:10000.00
```

**处理过程**：
1. 读取config.yaml中的查验引擎配置
2. 调用对应查验接口
3. 解析查验结果
4. 输出查验报告

**输出**：
```json
{
  "verify_result": "查验通过",
  "invoice_status": "正常",
  "platform": "国税总局查验平台",
  "verify_time": "2026-06-28T23:55:37",
  "details": {
    "invoice_code": "3100204130",
    "invoice_number": "00564189",
    "billing_date": "2026-06-28",
    "amount": 10000.00,
    "tax_amount": 1300.00
  }
}
```

## 限制说明

### 功能限制

| 限制项 | 说明 |
|--------|------|
| 发票类型 | 仅支持增值税专用发票、增值税电子发票、增值税普通发票 |
| 不支持类型 | 手写发票、定额发票、机动车销售发票、二手车发票 |
| OCR准确率 | 清晰图片≥95%，模糊/倾斜图片可能降至80%以下 |
| 查验引擎 | 需企业自行申请API密钥，Skill不代为申请 |
| 审批对接 | 需企业管理员在对应平台开通审批API权限 |

### 技术限制

| 限制项 | 说明 |
|--------|------|
| 运行环境 | Python 3.8+，需安装Tesseract OCR |
| 图片格式 | 支持PNG/JPG/TIFF/PDF（需安装poppler） |
| 语言支持 | 中文简体发票识别，其他语言准确率下降 |
| 并发处理 | 单线程处理，不支持高并发批量识别 |
| 模板学习 | 首次使用需手动匹配字段，后续自动学习 |

### 安全限制

| 限制项 | 说明 |
|--------|------|
| 数据上传 | **绝不**将发票图片上传到任何第三方服务器 |
| API调用 | 查验/审批API调用仅在用户明确授权后执行 |
| 日志记录 | 仅记录操作元数据，不记录发票全文内容 |
| 缓存清理 | 识别完成后自动清理临时图片文件 |

## 风险声明

### 🔴 重要安全提示

> **使用本Skill前，请务必仔细阅读以下风险声明：**

#### 1. 数据安全责任

- 所有发票数据仅在用户本地设备处理
- **Skill开发者不对数据泄露承担任何责任**
- 用户需自行负责API密钥的安全保管
- 建议定期轮换API密钥

#### 2. 查验结果免责声明

- 查验引擎的返回结果由第三方平台提供
- Skill仅提供技术对接，**不对查验结果的准确性负责**
- 如对查验结果有疑问，请直接联系相关税务平台
- 查验频率受限于各平台规则，Skill不对此负责

#### 3. 审批操作责任

- 审批提交后不可撤销（以各平台规则为准）
- Skill不审批内容的合规性和真实性
- 用户对提交的报销单内容负全部责任
- 建议在提交前进行人工复核

#### 4. 财务合规要求

- 本工具仅为技术支持工具，**不提供税务咨询或财务建议**
- 所有财务决策应由专业财务人员做出
- 使用者需确保符合当地税务法规和会计准则
- 如需专业税务意见，请咨询持牌税务顾问

#### 5. 软件使用限制

- 本Skill仅供合法合规的财务报销用途
- 禁止用于伪造、变造发票或报销欺诈
- 开发者保留追究滥用行为的权利
- 使用即表示接受以上全部条款

### ⚠️ 企业自主决策清单

| 决策项 | 企业需自行决定 |
|--------|---------------|
| 查验引擎选择 | □ 国税总局平台（免费） □ 百望云 □ 诺诺发票 □ 自建接口 |
| 审批平台选择 | □ 钉钉 □ 企业微信 □ 飞书 □ 自建系统 |
| API密钥管理 | □ 密钥存储方式 □ 轮换周期 □ 权限范围 |
| 数据安全策略 | □ 临时文件清理频率 □ 日志保留期限 □ 访问控制 |
| 合规审查 | □ 内部合规审查 □ 外部审计 □ 持续监控 |

## 配置文件模板

```yaml
# config.yaml - 企业自主配置
# 本文件为示例模板，企业需根据实际情况填写
# 未配置的功能模块将提示手动操作

# ==================== 查验引擎配置 ====================
verify_engine: "tax_bureau"  # 可选值: tax_bureau / bairong / nuonuo / custom

# 百望云API（如选择bairong）
bairong:
  api_key: "在此填写您的百望云API Key"
  api_secret: "在此填写您的百望云Secret"

# 诺诺发票API（如选择nuonuo）
nuonuo:
  api_key: "在此填写您的诺诺发票API Key"
  api_secret: "在此填写您的诺诺发票Secret"

# 自建查验接口（如选择custom）
custom:
  endpoint: "https://your-company.com/api/verify"
  method: "POST"
  headers:
    Authorization: "Bearer YOUR_TOKEN"
  timeout: 30  # 超时时间（秒）

# ==================== 审批平台配置 ====================
approval:
  platform: "none"  # 可选值: dingtalk / wecom / feishu / custom / none

  # 钉钉审批
  dingtalk:
    app_key: ""
    app_secret: ""
    process_code: ""

  # 企业微信审批
  wecom:
    corp_id: ""
    secret: ""
    template_id: ""

  # 飞书审批
  feishu:
    app_id: ""
    app_secret: ""
    approval_code: ""

  # 自建审批系统
  custom:
    endpoint: ""
    method: "POST"
    headers: {}
    timeout: 30

# ==================== 模板映射配置 ====================
template:
  path: "templates/expense_basic.xlsx"  # 报销单模板路径
  field_mapping:
    invoice_date: "开票日期"
    seller_name: "销方名称"
    amount: "金额（不含税）"
    tax_amount: "税额"
    total: "价税合计"
    remark: "费用说明"
    invoice_code: "发票代码"
    invoice_number: "发票号码"
```

## 故障排除

### 常见问题

**Q1: OCR识别报错 `Tesseract not found`**
- A: 未安装Tesseract，请运行 `.\scripts\install_tesseract.ps1`

**Q2: 识别结果为空**
- A: 图片质量过低，请尝试：1) 提高图片分辨率 2) 确保光线均匀 3) 平整拍摄

**Q3: 查验接口返回失败**
- A: 1) 检查API Key是否正确 2) 检查网络连接 3) 检查是否超出调用频率限制

**Q4: 模板匹配失败**
- A: 1) 检查模板字段名是否为中文 2) 确认模板第一行为表头 3) 查看 `references/setup-guide.md` 中的模板要求

### 日志位置

```
logs/
├── ocr_engine.log          # OCR识别日志
├── verify_abstract.log     # 查验操作日志
├── template_matcher.log    # 模板匹配日志
├── approval_abstract.log   # 审批操作日志
└── error.log               # 错误日志
```

## 支持和反馈

- 文档：`references/` 目录下的参考文档
- 问题反馈：请在SkillHub平台提交Issue
- 功能建议：欢迎提交Pull Request

## 更新日志

### v1.0.0 (2026-06-28)
- 初始版本发布
- 支持增值税发票OCR识别
- 支持多种查验引擎接口
- 支持模板自适应学习
- 支持多种审批平台对接

## 免责声明

本工具仅提供发票识别和报销单生成的技术支持，**不提供任何税务咨询或财务建议**。所有财务决策应由专业财务人员做出。使用者需确保符合当地法律法规。使用本工具即表示接受《风险声明》中的全部条款。