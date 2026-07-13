---
name: multi-agent-pro
slug: multi-agent-pro
displayName: 多Agent协作编排引擎
description: 支持多Agent流水线编排（采集→分析→报告），基于DAG调度实现跨技能状态共享、错误重试、断点续传、执行报告生成、HTML甘特图可视化、人工审批节点、历史执行对比、硬件自适应参数和版本更新提醒。AI即编排器，脚本提供基础设施。
version: 3.0.0
category: developer-tools
platforms:
  - windows
  - macos
  - linux
tags:
  - multi-agent
  - orchestration
  - dag
  - pipeline
  - workflow
  - automation
  - visualization
requires_api_key: false
author: WorkBuddy
---

# 多Agent协作编排引擎

> 让 AI 成为编排器，将"单Agent单任务"升级为"多Agent流水线协作"。

> **联系邮箱：** 有更好建议： njskills@agent.qq.com

---

## 快速入门（30秒）

### 速查表

| 你想做什么 | 直接对 AI 说 |
|-----------|-------------|
| 编排一个采集→分析→报告流水线 | "帮我编排一个数据采集到报告生成的流水线" |
| 多个Agent协作完成任务 | "用多Agent协作编排这个任务" |
| 定义并执行DAG流水线 | "帮我定义一个DAG流水线并执行" |
| 查看流水线执行状态 | "查看流水线执行状态" |
| 从断点恢复执行 | "断点续传流水线" |
| 生成执行报告 | "生成流水线执行报告" |
| 可视化甘特图 | "生成流水线甘特图" |
| 查看历史对比 | "对比最近5次执行记录" |

### 三步上手

```
第1步：定义流水线 → AI 生成 pipeline JSON（参考 templates/pipeline_dag_template.json）
第2步：验证并初始化 → python orchestrator.py run pipeline.json
第3步：逐步执行 → python orchestrator.py step state.json（循环直到完成）
```

### 可直接复制的开场白

```
"帮我编排一个竞品分析流水线：采集竞品信息 → 分析优劣势 → 生成报告"
"用多Agent协作编排引擎，把我这个任务拆成三个Agent串行执行"
"定义一个DAG流水线，包含数据采集、数据清洗、数据分析、报告生成四个节点"
"我需要人工审批节点，在关键步骤暂停等用户确认"
```

---

## 依赖

仅需 **Python 3.8+**，零第三方依赖。所有脚本仅使用 Python 标准库。

### 依赖检测

```python
import sys
print(f"Python: {sys.version.split()[0]}")
if sys.version_info < (3, 8):
    print("需要 Python 3.8+，请升级后重试")
else:
    print("环境满足要求，可以正常使用")
```

### 安全声明

| 项目 | 说明 |
|------|------|
| 网络请求 | 仅检查更新时有 GitHub 请求，其他均为本地操作 |
| API Key | 无。不需要任何密钥或认证 |
| 敏感数据 | 状态文件仅存储在本地，不上传任何服务器 |
| 子进程 | 由 AI 编排器管理 spawn 和回收，脚本不创建子进程 |
| 文件写入 | 仅写入 pipeline_state.json 和报告文件到指定路径 |

---

## 能力边界

### 三分类

| 分类 | 说明 | 示例 |
|------|------|------|
| ✅ 擅长 | 多Agent流水线编排、DAG验证、状态管理、错误恢复、执行报告 | "采集→分析→报告"三阶段流水线 |
| ✅ 擅长 | 断点续传、下游影响分析、拓扑排序执行计划 | 失败后从断点恢复执行 |
| ✅ 擅长 | HTML甘特图可视化、人工审批节点、历史执行对比 | DAG执行过程颜色编码时间轴 |
| ✅ 擅长 | 硬件自适应参数推荐、版本更新提醒 | 自动检测CPU/内存推荐并发数 |
| ⚠️ 需素材 | 需要用户提供 DAG 定义（或由AI根据需求生成） | pipeline JSON 文件 |
| ⚠️ 需素材 | 各Agent的具体任务由AI执行，脚本仅管理编排流程 | AI需要自行完成采集/分析/报告等实际任务 |
| ❌ 超范围 | 实时流处理（如Kafka流式消费） | 请使用 Flink/Spark Streaming |
| ❌ 超范围 | 分布式多机调度 | 请使用 Airflow/Prefect |
| ❌ 超范围 | GPU资源调度 | 请使用 Kubernetes/Ray |

---

## 功能模块

---

### 模块 1：DAG 定义与验证

**功能**：用 JSON 定义多Agent流水线，自动验证结构合法性。

**触发词**：`验证DAG`、`检查流水线`、`DAG验证`

**可运行命令**：

```bash
python scripts/dag_validator.py pipeline.json
```

**DAG 定义格式**：

```json
{
  "pipeline_name": "流水线名称",
  "version": "3.0",
  "agents": [
    {
      "id": "agent_1",
      "name": "Agent名称",
      "role": "Agent职责描述",
      "type": "task",
      "inputs": ["input_param"],
      "outputs": ["output_param"],
      "depends_on": [],
      "retry": 3,
      "timeout": 60,
      "fallback": "skip",
      "default_value": null
    }
  ],
  "state_store": {
    "type": "json",
    "path": "./pipeline_state.json"
  }
}
```

**节点类型说明**：

| type 值 | 说明 |
|---------|------|
| `task` | 普通任务节点（默认），AI 自动执行 |
| `approval` | 人工审批节点，执行到此暂停等待用户确认 |

**验证内容**：
1. Schema 结构完整性（必填字段检查）
2. 循环依赖检测（Kahn 算法）
3. 孤立节点检测
4. 输出拓扑排序执行顺序

---

### 模块 2：拓扑排序与执行计划

**功能**：按依赖关系自动排序节点，展示执行计划。

**触发词**：`执行计划`、`查看拓扑排序`、`流水线执行顺序`

**可运行命令**：

```bash
python scripts/orchestrator.py plan pipeline.json
```

---

### 模块 3：状态持久化与共享

**功能**：每个Agent的输出自动存入JSON状态文件，下游Agent自动读取上游输出。

**触发词**：`初始化状态`、`保存节点输出`、`查看状态`

**可运行命令**：

```bash
python scripts/orchestrator.py run pipeline.json
python scripts/state_store.py complete state.json node_id '{"result":"输出数据"}'
python scripts/state_store.py fail state.json node_id "错误描述"
python scripts/orchestrator.py status state.json
```

---

### 模块 4：错误恢复（三级降级）

**功能**：节点失败时，按"重试→降级→中止"三级策略自动恢复。

**触发词**：`重试节点`、`节点失败了`、`降级处理`、`错误恢复`

**可运行命令**：

```bash
python scripts/error_recovery.py retry state.json node_id "错误信息"
python scripts/error_recovery.py fallback state.json node_id "错误信息"
python scripts/error_recovery.py impact state.json node_id
```

---

### 模块 5：断点续传

**功能**：流水线中断后，从失败节点恢复执行，跳过已完成节点。

**触发词**：`断点续传`、`恢复执行`、`从断点继续`

**可运行命令**：

```bash
python scripts/orchestrator.py status state.json
python scripts/orchestrator.py resume state.json
python scripts/orchestrator.py step state.json
```

---

### 模块 6：执行报告生成

**功能**：自动生成 Markdown 执行报告，包含概览、节点详情、失败分析、建议。

**触发词**：`生成报告`、`执行报告`、`流水线报告`

**可运行命令**：

```bash
python scripts/orchestrator.py report state.json [output.md]
```

---

### 模块 7：HTML 甘特图可视化 🆕

**功能**：生成纯 HTML 甘特图，颜色编码每个节点的执行状态和时间轴。

**触发词**：`甘特图`、`可视化`、`执行过程图`

**可运行命令**：

```bash
python scripts/orchestrator.py gantt state.json [output.html]
```

**颜色编码**：

| 颜色 | 状态 | 说明 |
|------|------|------|
| 🟢 绿色 | 成功 | completed |
| 🔴 红色 | 失败 | failed |
| 🔵 蓝色 | 执行中 | running |
| 🟡 黄色 | 跳过 | skipped |
| ⚪ 灰色 | 待执行 | pending |

**输出路径**默认 `gantt_<pipeline_id>.html`，可用浏览器直接打开。

---

### 模块 8：人工审批节点 🆕

**功能**：在 DAG 中设置 `type: approval` 节点，流水线执行到此暂停，等待用户确认后继续或终止。

**触发词**：`审批节点`、`人工确认`、`暂停`

**使用方法**：在 pipeline.json 中定义：

```json
{
  "id": "reviewer",
  "name": "人工审核",
  "role": "请确认数据是否符合预期",
  "type": "approval",
  "depends_on": ["previous_node"]
}
```

**执行流程**：
1. 引擎遇到审批节点 → 显示节点信息和上游输出
2. 提示用户输入 `Y`（继续）或 `N`（拒绝）
3. Y → 标记 completed，继续下游
4. N → 标记 aborted，中止流水线

---

### 模块 9：历史执行对比 🆕

**功能**：每次执行完成后自动保存摘要，新执行时与最近5次对比，输出"本次比上次慢X%"。

**触发词**：`历史记录`、`执行对比`、`上次对比`

**可运行命令**：

```bash
# 查看历史记录
python scripts/orchestrator.py history state.json

# 对比最近5次执行
python scripts/orchestrator.py compare state.json
```

**对比维度**：
- 耗时对比（"本次比上次慢23%"）
- 成功/失败节点数对比
- 重试次数对比

**存储位置**：`.execution_history.json`（与 state.json 同目录，保留最近10次）

---

### 模块 10：硬件自适应与参数推荐 🆕

**功能**：自动检测用户电脑硬件配置，推荐最优流水线参数，确保不拖累用户电脑。

**触发词**：`硬件检测`、`性能检测`、`参数推荐`

**可运行命令**：

```bash
python scripts/orchestrator.py hardware
```

**检测内容**：
- CPU 核心数（使用 `os.cpu_count()`）
- 内存大小（Windows 使用 `ctypes` + `GlobalMemoryStatusEx`，Linux/macOS 读取 `/proc/meminfo`）
- 性能等级评估（高/中/低）

**推荐参数**：
- 并发节点数（根据 CPU 核数）
- 文件大小限制（根据内存大小）
- 默认超时时间（根据综合性能）

**安全说明**：仅读取系统信息，不上传任何数据，不修改系统配置。

---

### 模块 11：版本更新提醒 🆕

**功能**：启动时自动检查 GitHub 是否有新版本，有更新时提醒用户。

**触发词**：`检查更新`、`有新版本吗`

**可运行命令**：

```bash
python scripts/orchestrator.py check-update
```

**工作原理**：从 GitHub 仓库读取远程 SKILL.md 的 `version` 字段，与本地版本比对。

**安全说明**：仅读取远程文件，不下载、不安装、不收集数据。

---

## 统一入口命令速查

```bash
# 验证 DAG 结构
python scripts/orchestrator.py validate pipeline.json

# 查看执行计划
python scripts/orchestrator.py plan pipeline.json

# 初始化并开始执行
python scripts/orchestrator.py run pipeline.json

# 执行下一个节点
python scripts/orchestrator.py step state.json

# 查看当前状态
python scripts/orchestrator.py status state.json

# 断点续传
python scripts/orchestrator.py resume state.json

# 生成 Markdown 执行报告
python scripts/orchestrator.py report state.json

# 生成 HTML 甘特图
python scripts/orchestrator.py gantt state.json

# 查看执行历史
python scripts/orchestrator.py history state.json

# 对比最近执行
python scripts/orchestrator.py compare state.json

# 硬件检测与参数推荐
python scripts/orchestrator.py hardware

# 检查更新
python scripts/orchestrator.py check-update

# 下游影响分析
python scripts/orchestrator.py impact state.json node_id
```

---

## 反模式（请避免）

| 反模式 | 问题 | 正确做法 |
|--------|------|---------|
| 循环依赖 | A→B→C→A 死锁 | 打破循环，改为 DAG |
| 巨型节点 | 所有逻辑放一个节点 | 按职责拆分为多个节点 |
| 零容错 | retry=0 + fallback=abort | 前端节点高重试+skip，末端节点低重试+abort |

详见 `references/anti-patterns.md`。

---

## 安全风险项

| 风险项 | 等级 | 说明 | 缓解措施 |
|--------|------|------|---------|
| 子进程泄漏 | P1 | AI 编排器 spawn 的子 Agent 未正确回收 | AI 需确保每个子任务完成后回收资源；脚本不创建子进程 |
| 状态文件并发写入 | P2 | 多个编排实例同时写同一个 state.json | 每个流水线使用独立的 state 文件路径 |
| DAG 循环依赖 | P2 | 用户定义了循环依赖的 DAG | `dag_validator.py` 启动前强制检测，发现环即中止 |
| 状态文件过大 | P2 | 节点输出过多导致 state.json 膨胀 | 单节点输出超过 10MB 时写入独立文件，state 中只存路径 |
| 敏感数据泄露 | P1 | Agent 输出中可能包含敏感信息 | FAQ 说明脱敏方法；建议不要处理真实密钥 |

---

## FAQ

### Q: 脚本支持哪些操作系统？
A: Windows、macOS、Linux 全部支持。仅使用 Python 标准库，无平台依赖。

### Q: 需要安装第三方库吗？
A: 不需要。所有脚本仅使用 Python 标准库（json/os/sys/time/datetime/platform/ctypes/urllib），开箱即用。

### Q: AI 在编排中扮演什么角色？
A: AI 是编排器。脚本提供基础设施（验证/状态/报告），AI 负责理解用户需求→生成DAG→逐步执行各节点任务→管理错误恢复。详见 `references/examples.md`。

### Q: 如何处理节点间数据传递？
A: 节点完成时将输出保存到 `pipeline_state.json`，下游节点执行时引擎自动注入上游输出。详见 `references/state-sharing-protocol.md`。

### Q: 节点失败后怎么恢复？
A: 三级策略：重试（自动）→ 降级（skip/default/abort）→ 断点续传。详见 `references/error-recovery-patterns.md`。

### Q: 如何查看完整的端到端示例？
A: 参见 `references/examples.md`，包含竞品分析、数据处理（含错误恢复）、断点续传三个完整案例。

### Q: 甘特图怎么打开？
A: 运行 `python orchestrator.py gantt state.json`，生成的 `.html` 文件可直接用浏览器打开。

### Q: 如何设置人工审批节点？
A: 在 pipeline.json 中定义节点时添加 `"type": "approval"`，执行到此节点时会暂停等待用户确认。

### Q: 历史记录占用多少存储？
A: 默认保留最近10次执行摘要，每次摘要约200字节，总计不超过2KB。

### Q: 硬件检测会不会修改我的系统配置？
A: 不会。硬件检测仅读取系统信息（CPU核数、内存大小），不做任何修改。

---

## 深度参考

| 文档 | 内容 |
|------|------|
| `references/dag-scheduling-guide.md` | DAG 调度原理：拓扑排序、执行策略、环检测、孤立节点 |
| `references/state-sharing-protocol.md` | 状态共享协议：数据传递机制、状态转换、最佳实践 |
| `references/error-recovery-patterns.md` | 错误恢复模式库：5种常见场景及恢复决策树 |
| `references/anti-patterns.md` | 反模式说明：3类常见错误 + 改进对比 |
| `references/faq-deep.md` | 深度 FAQ：10题覆盖边缘场景 |
| `references/examples.md` | 完整使用示例：3个端到端案例 |
| `templates/pipeline_dag_template.json` | DAG 定义模板（含人工审批节点示例） |
| `templates/state_schema.json` | 状态文件 JSON Schema 规范 v3.0 |
| `tests/test_pipeline.json` | 测试用 DAG（含审批节点，用于自检） |

---

## 禁止文件类型

本 Skill **不支持**以下文件类型的处理或生成：

| 类别 | 禁止的文件类型 |
|------|---------------|
| Windows 可执行/批处理脚本 | `.bat`、`.cmd`、`.ps1`、`.vbs`、`.exe`、`.dll`、`.lnk`、`.msi` |
| Office 二进制文档 | `.docx`、`.xlsx`、`.pptx`、`.doc`、`.xls`、`.ppt`、`.xlsm`、`.docm`、`.pptm` |
| 二进制镜像/安装包 | `.iso`、`.dmg`、`.zip`、`.rar`、`.7z`、`.tar`、`.gz`、`.apk`、`.jar` |
| 系统缓存/隐藏文件 | `.DS_Store`、`.git`目录、`.env`、`.log`、`.tmp` |
| 其他风险脚本 | `.sh`、`.com`、`.scr`、`.hta`、`.reg` |

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v3.0.0 | 2026-07-13 | 增加：HTML甘特图可视化模块，支持颜色编码的DAG执行时间轴；增加：人工审批节点（type: approval），可在关键步骤暂停等用户确认；增加：历史执行对比功能，自动保存最近10次执行摘要并对比耗时/成功率/重试次数；增加：硬件自适应模块，自动检测CPU/内存并推荐最优流水线参数；增加：版本更新提醒功能，对比GitHub远程版本；增加：禁止文件类型清单；优化：all_done判定逻辑，支持skipped节点视为完成；优化：calc_duration提取为独立函数供历史模块复用 |
| v2.0.1 | 2026-07-08 | 修复：状态文件并发写入potential问题；优化：atomic write安全性 |
| v2.0.0 | 2026-07-01 | 增加：三级错误恢复策略；增加：断点续传功能；增加：执行报告生成；优化：拓扑排序算法 |
