---
name: wps-office-suite
displayName: WPS Office 全家桶
slug: wps-office-suite
description: WPS Office 全家桶 - 四引擎（WPS/MS Office/LibreOffice/纯Python）智能识别用户已安装软件，AI助手零学习成本，自然语言驱动，含目录生成、环境自检、错误速查手册、格式设置、表格插入
version: 2.2.0
category: 办公协作与生产力工具
platforms:
  - windows
  - macos
  - linux
permission:
  - 文件系统访问
  - 应用程序控制（WPS / MS Office / LibreOffice / 纯Python）
dependency:
  - "Python 3.8+"
  - "pywin32（Windows COM 模式，可选）"
  - "python-docx / openpyxl / python-pptx（纯Python模式，可选）"
  - "WPS Office 2019+ 或 Microsoft Office（可选，增强模式）"
  - "LibreOffice（可选，跨平台兜底转换）"
pricing: 免费
tags:
  - WPS
  - MS-Office
  - LibreOffice
  - Office
  - Word
  - Excel
  - PPT
  - 四引擎
  - 智能识别
  - 纯Python
  - 自动化
  - 办公提效
  - AI助手
---

# WPS Office 全家桶 v2.2.0 ✅

> 🏗️ **四引擎智能识别**：自动检测用户电脑已安装的软件，按 WPS → MS Office → LibreOffice → 纯Python 顺序选择最合适的引擎
> 🤖 **AI助手零学习成本**：自然语言直接调用，傻瓜式教程
> 🛡️ **四道安全防线**：引擎自检 + 路径校验 + 错误中文化 + 数据零上传
> 📚 **完全文档体系**：FAQ + 错误速查 + 用例库 + 环境自检 + 能力边界说明

---

## 🚀 分钟上手

### 1. 检查环境

```bash
python scripts/wps_test.py
```

### 2. 查看当前引擎

```bash
python scripts/wps_word.py engine-info
```

### 3. 创建文件

```bash
python scripts/wps_word.py create --title "测试文档"
python scripts/wps_excel.py create --name "预算表" --sheets "收入,支出"
python scripts/wps_ppt.py create --title "推广方案"
```

---

## 🔧 功能矩阵

| 功能 | WPS 模式 | MS Office 模式 | LibreOffice 模式 | 纯Python 模式 |
|------|----------|---------------|-----------------|----------|
| **创建 Word** | ✅ | ✅ | ✅（回退） | ✅ |
| **编辑 Word** | ✅ | ✅ | ❌ | ✅ |
| **格式设置（字体/对齐/颜色）** | ✅ | ✅ | ❌ | ✅ |
| **表格创建/编辑** | ✅ | ✅ | ❌ | ✅ |
| **图片插入** | ✅ | ❌ | ❌ | ✅ |
| **目录生成** | ✅ | ✅ | ❌ | ✅ |
| **Word → PDF/HTML/TXT** | ✅ | ✅ | ✅ | ✅（需LibreOffice） |
| **创建 Excel** | ✅ | ✅ | ✅（回退） | ✅ |
| **数据录入** | ✅ | ❌ | ❌ | ✅ |
| **公式计算** | ✅ | ❌ | ❌ | ❌ |
| **图表生成（柱/折/饼）** | ✅ | ❌ | ❌ | ❌ |
| **多列排序** | ✅ | ❌ | ❌ | ❌ |
| **多条件筛选（AND/OR）** | ✅ | ❌ | ❌ | ❌ |
| **创建 PPT** | ✅ | ✅ | ✅（回退） | ✅ |
| **添加幻灯片** | ✅ | ❌ | ❌ | ❌ |
| **插入内容** | ✅ | ❌ | ❌ | ❌ |
| **PPT 主题应用** | ✅ | ❌ | ❌ | ❌ |
| **PPT → PDF/PNG** | ✅ | ❌ | ✅ | ✅（需LibreOffice） |
| **环境自检** | ✅ | ✅ | ✅ | ✅ |
| **反馈入口** | ✅ | ✅ | ✅ | ✅ |

---

## 🏗️ 引擎智能选择 v2.2

自动检测用户电脑**实际已安装**的软件，无需手动配置：

```
检测流程：
  ① 尝试 WPS Office → ✅ WPS 模式（功能最全，推荐）
  ② 尝试 Microsoft Office → ✅ MS Office 模式（兼容）
  ③ 尝试 LibreOffice Headless → ✅ LibreOffice 模式（跨平台兜底）
  ④ 都没有 → ✅ 纯Python 模式（免安装，创建+编辑基础功能）
```

### 引擎检测原理

| 检测项 | 方法 | 适用平台 |
|--------|------|---------|
| WPS | COM 接口调用测试 | Windows |
| MS Word | COM 接口调用测试 | Windows |
| MS Excel | COM 接口调用测试 | Windows |
| MS PPT | COM 接口调用测试 | Windows |
| LibreOffice | `soffice` PATH 检测 + 注册表查询 | Windows / Linux / macOS |

> 📝 **说明**：LibreOffice 模式使用 Headless（无界面）调用，命令为 `soffice --headless --convert-to pdf`，支持 PDF/HTML/TXT 格式转换。

---

## 💬 AI 助手对话示例

### 场景 1：零基础上手

```
你：帮我做个 Word 文档，标题"项目汇报"
AI：好的...
    python scripts/wps_word.py create --title "项目汇报"
✅ 已创建：项目汇报.docx
   当前引擎：WPS Office（功能最全）
```

### 场景 2：跨平台兼容（无WPS环境）

```
你：把 contract.docx 转成 PDF
AI：⚠️ 未检测到 WPS/MS Office，尝试 LibreOffice Headless...
    soffice --headless --convert-to pdf contract.docx
✅ 已生成：contract.pdf（LibreOffice模式）
```

### 场景 3：纯Python兜底

```
你：帮我创建一个 Excel 表格
AI：⚠️ 未检测到任何 Office 软件，启动纯 Python 模式...
✅ 已创建：纯Python模式 → data.xlsx
   提示：安装 WPS Office 2019+ 获取完整功能
```

---

## ⚠️ 能力边界说明

| 限制项 | 说明 | 解决方案 |
|--------|------|---------|
| **文件大小** | WPS/Excel 模式建议 < 50MB | 大文件先分片处理（拆分 Sheet/Section） |
| **复杂度** | 透视表/VBA/ActiveX 不支持 | 使用 pandas 或手动处理 |
| **网络文件** | 不支持 HTTP/URL 下载 | 先手动下载到本地，再调用 Skill |
| **并发限制** | 同一时间只能操作同一引擎的一个实例 | 等待上次操作完成后再发起 |
| **中文名文件路径** | 建议改用英文路径 | 路径中避免中文和特殊字符 |
| **实时协作** | 不支持多人同时编辑同一文件 | 通过手动分发和合并 |
| **跨平台** | LibreOffice 模式仅限格式转换 | 创建/编辑仍需 WPS/MS Office |

---

## 🚨 错误速查手册 v2.2（15个错误ID）

### E001-E010：用户可自助解决

| ID | 错误 | 解决 |
|----|------|------|
| E001 | WPS 未安装或 COM 注册失败 | 安装 WPS 后重启电脑 |
| E002 | python-docx 未安装 | `pip install python-docx openpyxl python-pptx` |
| E003 | 文件路径不存在或无法访问 | 改用英文路径或以管理员运行 |
| E004 | 格式转换失败（纯Python不支持） | 安装 WPS 或 LibreOffice |
| E005 | 排序/筛选/图表需要 WPS 模式 | 安装 WPS Office 2019+ |
| E006 | WPS/LibreOffice 卡住无响应 | 任务管理器结束进程；更新到最新版 |
| E007 | 权限不足 | 或以管理员运行；检查文件只读属性 |
| E008 | pywin32 导入失败 |  `pip uninstall pywin32 && pip install pywin32` |
| E009 | Python 版本过低 | 升级到 Python 3.8+ |
| E010 | 当前引擎不支持此功能 | 安装 WPS 或改用 info 查看能力矩阵 |

### E011-E015：需要进一步排查

| ID | 错误 | 解决 |
|----|------|------|
| E011 | LibreOffice 未安装 | 下载 LibreOffice 并添加到 PATH |
| E012 | LibreOffice 转换失败 | 检查源文件是否损坏；避免中文路径 |
| E013 | 文件不存在 | 确认路径正确；未被删除或移动 |
| E014 | 未知运行时错误 | 运行环境自检 `wps_test.py`；联系反馈 |
| E015 | 不支持的操作或格式 | 输出格式改为 pdf/txt/html |

---

## 📋 命令速查

### Word

```bash
python scripts/wps_word.py create --title "report" --body "正文内容"
python scripts/wps_word.py edit --file "report.docx" --text "新增内容" --position end
python scripts/wps_word.py format --file "report.docx" --font "微软雅黑" --size 14 --align center --bold
python scripts/wps_word.py export --file "report.docx" --format pdf
python scripts/wps_word.py info --file "report.docx"
python scripts/wps_word.py engine-info
```

### Excel

```bash
python scripts/wps_excel.py create --name "Sales" --sheets "Q1,Q2,Q3"
python scripts/wps_excel.py input --file "Sales.xlsx" --sheet "Q1" --data '[["A",100],["B",200]]'
python scripts/wps_excel.py formula --file "Sales.xlsx" --sheet "Q1" --cell "C1" --formula "=SUM(A1:B1)"
python scripts/wps_excel.py chart --file "Sales.xlsx" --sheet "Q1" --type bar --data "A1:B10"
python scripts/wps_excel.py sort --file "Sales.xlsx" --sheet "Q1" --sort-json '[{"column":"Price","ascending":false}]'
python scripts/wps_excel.py filter --file "Sales.xlsx" --sheet "Q1" --filter-json '[{"column":"Price","op":">","value":"50"}]' --filter-and
python scripts/wps_excel.py add-sheet --file "Sales.xlsx" --sheet "Q4" --headers "Product,Price" --data '[["X",300]]'
python scripts/wps_excel.py info --file "Sales.xlsx"
python scripts/wps_excel.py engine-info
```

### PPT

```bash
python scripts/wps_ppt.py create --title "Pitch"
python scripts/wps_ppt.py add-slide --file "Pitch.pptx" --title "Intro"
python scripts/wps_ppt.py insert --file "Pitch.pptx" --slide 2 --content "Key points"
python scripts/wps_ppt.py theme --file "Pitch.pptx" --name business_blue
python scripts/wps_ppt.py export --file "Pitch.pptx" --format pdf
python scripts/wps_ppt.py info --file "Pitch.pptx"
python scripts/wps_ppt.py engine-info
```

### 🆕 格式设置（纯Python模式）

```bash
# Word 格式设置
python scripts/wps_word.py format --file "report.docx" --font "微软雅黑" --size 14 --align center --bold --first-indent 0.74

# Excel 添加 Sheet
python scripts/wps_excel.py add-sheet --file "Sales.xlsx" --sheet "Q4" --headers "A,B,C"

# Word 添加表格
python scripts/wps_word.py add-table --file "report.docx" --headers "姓名,年龄,城市" --data '[["张三",25,"北京"],["李四",30,"上海"]]'

# Word 插入图片
python scripts/wps_word.py insert-image --file "report.docx" --image "logo.png" --width 10 --caption "公司LOGO"
```

### 🆕 环境自检

```bash
python scripts/wps_test.py              # 人类可读报告
python scripts/wps_test.py --json       # JSON 格式（程序分析）
```

### 🆕 反馈入口

```bash
python scripts/wps_feedback.py page     # 打开反馈页面（浏览器）
python scripts/wps_feedback.py email    # 打开邮件客户端（自动附带系统信息）
```

---

## 📊 版本兼容矩阵

| Python | WPS Office | LibreOffice | Windows | macOS | Linux | 状态 |
|--------|-----------|-------------|---------|-------|-------|------|
| 3.8+ | 2019+ | - | ✅ | ⚠️ | ❌ | 基础 |
| 3.8+ | 365 | - | ✅ | ✅ | ❌ | 最佳 |
| 3.8+ | - | 7.0+ | ✅ | ✅ | ✅ | 跨平台推荐 |
| 3.8+ | - | - | ✅ | ✅ | ✅ | 纯Python |

> ⚠️ = 部分功能受限，❌ = 对应引擎不可用（如 WPS 在 Linux 上不支持）

---

## ⚠️ 安全须知

**✅ 四道防线保障安全**：
1. **引擎自检**：启动时自动检测可用引擎，崩溃自动重启
2. **路径校验**：`safe_path()` 全面校验，拒绝非法路径和特殊字符
3. **错误中文化**：所有错误 ID 提供详细中文说明和操作步骤
4. **数据零上传**：所有处理在本地完成，不上传任何内容到互联网

**📝 注意事项**：
- 批量操作时，桌面会创建 `WPS_Backup` 文件夹保存副本
- macOS 上 WPS 不支持所有功能
- 纯 Python 模式下格式设置有限，复杂排版建议安装 WPS
- 所有文件操作在本地进行，不会联网
- LibreOffice Headless 模式下不支持实时预览

---

## 📝 版本记录

| 版本 | 日期 | 本次更新 |
|------|------|---------|
| **v2.2.0** | 2026-06-30 | 🏗️ 四引擎智能识别（WPS/MS Office/LibreOffice/纯Python）；🆕 LibreOffice Headless 跨平台兜底；✨ 纯Python格式设置/表格/图片插入；📋 错误ID系统（E001-E015）；📐 能力边界说明；🔧 中文化提示；🔄 智能引擎检测器 wps_engine.py；📝 引擎信息查询命令 |
| v2.1.0 | 2026-06-28 | 🆕 目录生成（TOC）；🆕 环境自检（test）；🆕 反馈入口；📚 错误速查手册（10个FAQ）；🎬 用例库（20个端到端场景）；📊 版本兼容矩阵 |
| v2.0.0 | 2026-06-28 | 🏗️ 三引擎自动切换；🤖 AI助手零学习成本；🛡️ 三道安全防线；📊 多列排序+多条件筛选 |
| v1.0.0 | 2026-06-28 | 初始版本，三大组件 + 格式转换 |
