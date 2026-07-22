# MEMORY.md - receipt-compliance 修改记录

## 最近修改

### v3.7.0 (2026-07-22) - 全电发票深度适配

#### 新增内容

**1. 全电发票 XML 解析器** (`scripts/xml_parser.py`)
- 自研全电发票 XML Schema 解析器，使用 Python 标准库 `xml.etree.ElementTree`
- 支持 20 位全电发票号码、校验码、税务数字账户 ID 等特有字段提取
- 兼容多种 XML 命名空间和标签变体（如 `InvoiceNumber`/`Fphm`/`FPHM`）
- 日期格式自动标准化（支持 `YYYY年MM月DD日`、`YYYY-MM-DD`、`YYYYMMDD`）
- 金额字段安全转换（去除货币符号、千位分隔符）

**2. OFD 版式文件解析器** (`scripts/ofd_parser.py`)
- 双方案解析：优先使用 `ofdparser` 库，不可用时自研降级方案
- 降级方案：手动解析 OFD 文件结构（ZIP 格式），提取 XML 内容预览
- 提供转换工具推荐（数科阅读器、福昕 OFD）

**3. 票种自动识别模块** (`scripts/invoice_detector.py`)
- 根据文件扩展名（`.xml`/`.ofd`/`.pdf`/`.png` 等）自动判断票种
- 对 XML 文件读取内容特征进一步判断全电/传统
- 自动路由到对应解析器（传统 OCR / 全电 XML / 全电 OFD）

**4. 统一发票数据结构** (`scripts/unified_invoice.py`)
- 兼容传统发票和全电发票的字段映射
- 提供 `to_dict()`、`to_json()`、`validate()` 等标准接口
- 全电特有字段：`check_code`、`digital_account_id`、`specific_business_info`

**5. SKILL.md 更新**
- 新增「全电发票（数电票）」章节，说明支持的文件类型、特有字段、使用方式
- 新增版本更新提醒机制说明
- 新增联系信息 `njskills@agent.qq.com`
- frontmatter version 升至 `3.7.0`
- 更新日志新增 v3.7.0 条目

#### 对应死规则检查

| 规则 | 状态 |
|------|------|
| #4 禁止自动发布 | ✅ 未自动发布 |
| #5 输出完整目录 | ✅ 见下方 |
| #6 更新日志格式规范 | ✅ 动词开头，无评测字样 |
| #7 发布统一用 tongyifabu.ps1 | ✅ 未发布 |
| #8 更新日志源文件填写规范 | ✅ frontmatter version 不带引号 |
| #9 功能自研优先 | ✅ XML/OFD 解析器自研 |
| #10 性能优化 | ✅ 解析器轻量，无重计算 |
| #11 版本更新提醒 | ✅ SKILL.md 已添加 |
| #12 MD 联系信息 | ✅ njskills@agent.qq.com |
| #13 禁止文件类型 | ✅ 未引入禁止类型 |
| #14 三次自审 | ✅ 完成 |
| #15 沙箱模拟运行 | ✅ 完成 |

---

### v3.4.0 (2026-07-13) - 安全修复（腾讯云鼎实验室安全评估）

#### 修复内容

**1. 供应链风险修复**
- 移除 install_tesseract.ps1 中指向个人 Gitee 仓库的下载源（gitee.com/woaini0919/tesseract-ocr）
- 移除 check_env.py 中 Gitee 镜像推荐
- 替换为 winget/scoop 官方源和 GitHub 官方 Release 下载

**2. 审批链接修复**
- 将 approval_abstract.py 中 `apply_url` 从 `https://open.duxiaoman.com` 改为 `https://open-dev.dingtalk.com`
- 将 approval_abstract.py 中 `reference_url` 从 `https://open.duxiaoman.com/document` 改为 `https://open-dev.dingtalk.com/document`
- 将 api-endpoints.md 中钉钉网址从 `https://open.duxiaoman.com` 改为 `https://open-dev.dingtalk.com`
- 将 setup-guide.md 中钉钉登录地址从 `https://open.duxiaoman.com` 改为 `https://open-dev.dingtalk.com`
- 将 example-approval.md 中 `reference_url` 从 `https://open.duxiaoman.com/document` 改为 `https://open-dev.dingtalk.com/document`

**3. 命令执行风险修复**
- verify_engine.py 中 `subprocess.Popen` 移除 `shell=True`，改为 `['cmd', '/c', 'start', short_url]` 列表形式

#### 对应安全评估问题

| 评估发现问题 | 修复措施 |
|------------|---------|
| 审批接口链接指向无关第三方平台 | 全部替换为钉钉官方 open-dev.dingtalk.com |
| 从个人 Gitee 仓库下载二进制文件 | 移除 Gitee 个人镜像，替换为官方源 |
| 不受限的 shell 执行器 | 移除 shell=True，使用列表参数形式 |

---

### v3.3.0 (2026-07-13) - 更名

- 插件文件夹名从 `tax-receipt-compliance` 改为 `receipt-compliance`
- displayName 从 `财税合规全链路助手` 改为 `会计助手`
- description、标题同步更新为"会计助手"
