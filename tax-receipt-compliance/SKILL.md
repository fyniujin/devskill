---
name: tax-receipt-compliance
slug: tax-receipt-compliance
displayName: 财税合规全链路助手
description: 财税合规全链路助手：发票OCR识别→真伪查验→报销单自动填充→对接审批系统。企业自主配置，数据本地处理。
version: 1.1.0
category: 财税管理
appName: 财税合规
platforms: [WorkBuddy, QClaw, ima, Claude Code, Cursor]
---

# 财税合规全链路助手

> ⚠️ **使用必读**：本Skill所有功能在本地运行，发票数据绝不外传，但**绝不提供税务咨询**。使用前请先阅读【限制说明】和【风险声明】。

## 功能说明

本Skill提供从发票识别到审批提交的**全链路**财税合规能力。

| 模块 | 功能 | 状态 | 输入 | 输出 |
|------|------|------|------|------|
| 1. 发票OCR识别 | Tesseract本地识别增值税发票 | ✅ 直接可用 | 发票图片 | 结构化JSON |
| 2. 真伪查验 | 对接查验平台，自动获取结果 | ⚠️ 需配置密钥 | 发票代码/号码 | 查验结果 |
| 3. 报销单填充 | 自适应学习模板，一键填充 | ✅ 直接可用 | 发票数据+模板 | Excel文件 |
| 4. 审批对接 | 对接钉钉/企微/飞书审批 | ⚠️ 需配置密钥 | 报销单+配置 | 审批结果 |

> ✅ = 装即用 ｜ ⚠️ = 需在 config.yaml 中配置对应API密钥

### 设计理念

1. **数据安全第一**：所有发票数据处理均在本地，不会上传到任何服务器
2. **企业自主决策**：查验引擎、审批平台的选择权完全交给企业
3. **透明开源**：所有代码可见可审计，无隐藏后门
4. **渐进披露**：基础功能开箱即用，高级功能按配置解锁

## 触发词

| 意图 | 触发词 |
|------|--------|
| 识别发票 | "识别这张发票"、"OCR发票"、"扫描发票" |
| 查验真伪 | "查验这张发票"、"查发票真伪" |
| 生成报销单 | "用XX模板生成报销单"、"填报销单" |
| 提交审批 | "提交报销审批"、"发起审批"、"报销审批" |
| 批量处理 | "批量识别"、"批量报销" |

## 快速开始

### 第一步：环境准备（必做）

运行前请确认：

```bash
# Windows (PowerShell)
.\scripts\install_tesseract.ps1

# Linux/macOS
bash ./scripts/install_tesseract.sh
```

然后安装Python依赖：

```bash
pip install Pillow pytesseract openpyxl pyyaml
```

> 安装完成后运行预检脚本检查环境：
> ```bash
> python scripts/check_env.py
> ```

### 第二步：配置

```bash
cp templates/config_template.yaml config.yaml
# 编辑 config.yaml，填写您的企业配置
```

### 第三步：开始使用

```bash
# 识别单张发票（直接可用）
python scripts/ocr_engine.py --input path/to/invoice.png --output receipt.json

# 查验发票真伪（需先配置查验引擎）
python scripts/verify_engine.py --invoice-code 3100204130 --invoice-number 00564189 --date "2026年06月28日" --amount 10000

# 生成报销单（直接可用）
python scripts/template_matcher.py fill --config config.yaml --receipt receipt.json --template templates/expense_basic.xlsx

# 提交审批（需先配置审批平台）
python scripts/approval_engine.py --config config.yaml --expense expense_output.xlsx

# 环境预检
python scripts/check_env.py
```

## 详细配置说明

见 `references/setup-guide.md`

## 示例

### 示例1：识别单张发票

**输入**：

```
识别发票 D:\invoices\20260628_001.png
```

**输出**：

```json
{
  "success": true,
  "invoice_type": "增值税专用发票",
  "invoice_code": "3100204130",
  "invoice_number": "00564189",
  "invoice_date": "2026年06月28日",
  "seller_name": "上海某某科技有限公司",
  "amount": 10000.00,
  "tax_rate": 0.13,
  "tax_amount": 1300.00,
  "total": 11300.00,
  "remark": "*信息技术服务费*",
  "confidence": 0.96
}
```

### 示例2：查验发票真伪

**输入**：

```
查验发票 代码:3100204130 号码:00564189 日期:2026-06-28 金额:10000.00
```

**输出**：

```json
{
  "engine": "国税总局查验平台",
  "status": "ready",
  "verify_url": "https://inv-veri.chinatax.gov.cn/index.html?fpdm=3100204130&fphm=00564189",
  "message": "已为您生成查验链接，点击即可查验",
  "params": {
    "invoice_code": "3100204130",
    "invoice_number": "00564189",
    "billing_date": "2026-06-28",
    "amount": 10000.00
  }
}
```

> 如配置了百望云/诺诺API Key，会自动调用第三方API获取查验结果。

### 示例3：生成报销单

**输入**：

```
用模板 D:\templates\公司报销单.xlsx 生成报销单，数据来自 D:\invoices\receipt.json
```

**输出**：

```
模板分析完成：识别到 6 个字段映射，置信度 0.8+
报销单已生成：D:\output\expense_report_20260629.xlsx
已填充 6 个字段：开票日期、销方名称、金额、税额、价税合计、费用说明
```

### 示例4：批量识别并合并为报销单

```bash
python scripts/batch_process.py --input D:\invoices\ --template D:\templates\公司报销单.xlsx --output D:\output\合并报销单.xlsx
```

### 示例5：提交审批

```bash
python scripts/approval_engine.py --config config.yaml --expense D:\output\报销单.xlsx --user-id manager123 --amount 11300 --expense-type 信息技术服务
```

## 发票类型支持与图片要求

### 支持的发票类型

- ✅ 增值税专用发票
- ✅ 增值税电子发票
- ✅ 增值税普通发票
- ✅ 电子发票（PDF格式，需安装poppler）

### 暂不支持

- ❌ 手写发票
- ❌ 定额发票
- ❌ 机动车销售发票
- ❌ 二手车销售发票
- ❌ 海关缴款书

### 图片质量要求（直接影响识别率）

| 质量等级 | 分辨率 | 光线 | 平整度 | 预期准确率 |
|---------|--------|------|--------|-----------|
| 优秀 | ≥300DPI | 均匀 | 无褶皱 | 95%+ |
| 良好 | 200-300DPI | 较均匀 | 轻微褶皱 | 85-95% |
| 可用 | 150-200DPI | 一般 | 有褶皱 | 70-85% |
| 较差 | <150DPI | 反光/阴影 | 严重褶皱 | <70%，建议重新拍摄 |

> **提高识别率的小技巧**：
> 1. 用手机相机拍摄时，开启"文档模式"或"扫描模式"
> 2. 避免强光直射，减少反光
> 3. 发票平整放置，不要弯曲
> 4. 确保发票代码、号码区域清晰可见
> 5. 如果无法识别，请检查图片中是否有手写涂改

## 限制说明

### 功能限制

| 限制项 | 具体说明 |
|--------|---------|
| OCR识别 | 仅支持增值税发票（专票/普票/电子票） |
| 暂不支持 | 手写发票、定额发票、机动车发票、二手车发票 |
| 查验功能 | 需企业自行申请API密钥，Skill不代为申请 |
| 审批功能 | 需企业管理员在对应平台开通审批API权限 |

### 技术限制

| 限制项 | 具体说明 |
|--------|---------|
| 运行环境 | Python 3.8+ |
| 必须安装 | Tesseract OCR + 中文语言包 |
| 图片格式 | PNG/JPG/TIFF/PDF（PDF需要poppler） |
| 语言 | 中文简体，其他语言准确率显著下降 |
| 并发 | 单线程处理，一次一张 |

### 安全限制

| 限制项 | 具体说明 |
|--------|---------|
| 数据上传 | 绝不将发票图片上传到任何第三方服务器 |
| API调用 | 仅在用户明确授权后执行，且仅调用用户配置的平台 |
| 日志 | 仅记录操作元数据（文件名、时间、状态），不记录发票内容 |
| 临时文件 | 识别完成后自动清理，保留不超过24小时 |

## 错误代码速查表

| 错误代码 | 问题描述 | 解决方案 |
|---------|---------|---------|
| `Tesseract not found` | Tesseract未安装或未加入PATH | 运行 `install_tesseract.ps1` 并重启终端 |
| `chi_sim not found` | 中文语言包未安装 | 重新安装Tesseract，勾选Chinese语言包 |
| `PIL not found` | Pillow未安装 | `pip install Pillow` |
| `pytesseract not found` | pytesseract未安装 | `pip install pytesseract` |
| `openpyxl not found` | openpyxl未安装 | `pip install openpyxl` |
| `pdf2image not found` | PDF转图片工具未安装 | `pip install pdf2image` + 安装poppler |
| `empty result` | OCR未识别到文字 | 检查图片质量、光线、平整度 |
| `low confidence` | 识别置信度低于0.7 | 建议重新拍摄，或手动输入发票信息 |
| `verify_engine not configured` | 查验引擎未配置 | 编辑config.yaml，填写对应API Key |
| `approval_engine not configured` | 审批引擎未配置 | 编辑config.yaml，选择并填写审批平台 |
| `token_failed` | 获取AccessToken失败 | 检查API Key/Secret是否正确 |
| `template_not_found` | 模板文件不存在 | 检查template路径是否正确 |

## 风险声明

> 🔴 **使用本Skill前，请务必仔细阅读以下条款：**

### 1. 数据安全责任

- 所有发票数据仅在用户本地设备处理，不会上传到任何服务器
- **但用户需自行确保本地设备的安全**，Skill开发者不对数据泄露承担责任
- 用户需自行负责API密钥的安全保管
- 建议定期轮换API密钥（每90天一次）

### 2. 查验结果免责声明

- 查验引擎返回的结果由第三方平台提供
- Skill仅提供技术对接，**不对查验结果的准确性负责**
- 如对查验结果有疑问，请直接联系相关税务平台

### 3. 审批操作责任

- 审批提交后不可撤销（以各平台规则为准）
- Skill不审批内容的合规性和真实性
- 用户对提交的报销单内容负全部责任

### 4. 财务合规要求

- 本工具仅为技术支持工具，**不提供任何税务咨询或财务建议**
- 所有财务决策应由专业财务人员做出
- 需专业税务意见时，请咨询持牌税务顾问

### 5. 禁止行为

使用本Skill，用户不得：
- 伪造、变造发票
- 使用假发票报销
- 虚增报销金额
- 报销与业务无关的费用
- 进行其他违反财务法规的行为

### 6. 企业自主决策清单

使用前，请确认您已决定以下事项：

- [ ] 查验引擎选择：□ 国税总局平台（免费） □ 百望云 □ 诺诺发票 □ 自建接口
- [ ] 审批平台选择：□ 钉钉 □ 企业微信 □ 飞书 □ 自建系统 □ 暂不使用
- [ ] 数据安全策略：日志保留期限、临时文件清理频率
- [ ] 合规审查：内部审计、外部审计计划

## 配置文件模板

```yaml
# config.yaml - 企业自主配置
# 本文件为示例模板，企业需根据实际情况填写
# 未配置的功能模块将提示手动操作

# ==================== 查验引擎配置 ====================
verify_engine: "tax_bureau"
# 可选值:
# - "tax_bureau": 国税总局查验平台（免费，无需API Key）
# - "bairong": 百望云API（需API Key+Secret）
# - "nuonuo": 诺诺发票API（需API Key+Secret）
# - "custom": 企业自建接口（需接口地址）

# 百望云（如选择bairong）
bairong:
  api_key: "在此填写您的百望云API Key"
  api_secret: "在此填写您的百望云Secret"

# 诺诺发票（如选择nuonuo）
nuonuo:
  api_key: "在此填写您的诺诺发票API Key"
  api_secret: "在此填写您的诺诺发票Secret"

# 自建查验接口（如选择custom）
custom:
  endpoint: "https://your-company.com/api/verify"
  method: "POST"
  headers:
    Authorization: "Bearer YOUR_TOKEN"

# ==================== 审批平台配置 ====================
approval:
  platform: "none"  # dingtalk / wecom / feishu / none

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

**Q1: 安装Tesseract后仍然提示 `Tesseract not found`**

A: 通常是PATH环境变量未生效。

- **Windows**：重启PowerShell/终端，或手动运行 `refreshenv`
- **Linux/macOS**：运行 `source ~/.bashrc` 或 `source ~/.zshrc`
- 紧急方案：使用 `--tesseract` 参数指定完整路径：
  ```bash
  python ocr_engine.py --tesseract "C:\Program Files\Tesseract-OCR\tesseract.exe" --input 发票.png
  ```

**Q2: 识别结果为空或仅识别到少量内容**

A: 按顺序排查：
1. 图片质量是否过低？（拍摄光线、平整度、分辨率）
2. 发票类型是否支持？（手写发票不支持）
3. 是否安装了中文语言包？（运行 `tesseract --list-langs` 检查是否有 `chi_sim`）
4. 尝试提高图片预处理质量（在代码中调整阈值参数）

**Q3: 提示 `PermissionError` 或 `Occupied`**

A: 文件被其他程序关闭。请关闭所有占用目标文件的程序后重试。

**Q4: 查验接口返回失败**

A: 排查顺序：
1. 检查API Key/Secret是否正确（无多余空格）
2. 检查网络是否可访问对应平台
3. 检查是否超出调用频率限制
4. 查看 `logs/verify_engine.log` 了解详细错误

**Q5: 模板匹配失败**

A: 检查以下几点：
1. 模板文件第一行是否为中文表头
2. 模板文件是否未损坏（用Excel打开确认）
3. 字段名是否在预设映射表中（见 `common_mappings`）
4. 可尝试手动指定映射关系

**Q6: 如何减小识别结果文件体积？**

A: 处理完成后，删除 `output/` 目录下的中间文件（`.json`、`.xlsx`），仅保留最终需要的文件。Skill会自动清理临时文件。

**Q7: 支持哪些审批平台？**

A: 钉钉、企业微信、飞书、自建系统（需实现接口）。

**Q8: 如果审批平台不在列表中怎么办？**

A: 使用 `custom` 选项，填写企业自建审批系统的接口地址和鉴权方式。

### 日志文件说明

如果以上方案均无法解决问题，请查看日志文件获取详细信息：

```
logs/
├── ocr_engine.log          # OCR识别详情
├── verify_engine.log       # 查验详情
├── template_matcher.log    # 模板匹配详情
├── approval_engine.log     # 审批详情
└── error.log               # 错误日志（优先查看）
```

## 支持与反馈

- 问题反馈：请在SkillHub平台提交Issue
- 功能建议：欢迎提交Pull Request
- 邮箱：联系Skill开发者

## 更新日志

### v1.1.0 (2026-06-29)
- **新增**：环境预检脚本 `scripts/check_env.py`
- **新增**：错误代码速查表
- **新增**：发票图片质量要求和拍摄建议
- **升级**：真伪查验引擎 `verify_engine.py`，真正对接国税总局/第三方平台
- **升级**：审批引擎 `approval_engine.py`，真正获取Token并调用API
- **升级**：安装脚本增加预检环节
- **升级**：模板匹配支持PDF格式（需poppler）
- **改进**：所有脚本增加更详细的错误提示
- **改进**：配置文件中增加timeout设置

### v1.0.0 (2026-06-28)
- 初始版本发布
- 支持增值税发票OCR识别
- 支持多种查验引擎接口
- 支持模板自适应学习
- 支持多种审批平台对接

## 免责声明

本工具仅提供发票识别和报销单生成的技术支持，**不提供任何税务咨询或财务建议**。所有财务决策应由专业财务人员做出。使用者需确保符合当地法律法规。使用本工具即表示接受《风险声明》中的全部条款。