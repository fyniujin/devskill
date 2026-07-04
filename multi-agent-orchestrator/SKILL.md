---
name: multi-agent-pro
slug: multi-agent-pro
displayName: 多Agent协作编排引擎
description: 支持多Agent流水线编排（采集→分析→报告），基于DAG调度实现跨技能状态共享、错误重试、断点续传和执行报告生成。AI即编排器，脚本提供基础设施。
version: 2.0.1
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
requires_api_key: false
author: WorkBuddy
---

# 多Agent协作编排引擎

> 让 AI 成为编排器，将"单Agent单任务"升级为"多Agent流水线协作"。

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
| 网络请求 | 无。所有脚本仅读写本地文件 |
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
  "version": "1.0",
  "agents": [
    {
      "id": "agent_1",
      "name": "Agent名称",
      "role": "Agent职责描述",
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

**验证内容**：
1. Schema 结构完整性（必填字段检查）
2. 循环依赖检测（Kahn 算法）
3. 孤立节点检测
4. 输出拓扑排序执行顺序

**输出示例**：

```
[1/3] Schema 验证 ... 通过
[2/3] 循环依赖检测 ... 通过
[3/3] 孤立节点检测 ... 通过

执行顺序（拓扑排序）：collector -> analyzer -> reporter

验证结果：完全通过
```

**常见报错**：

| 报错 | 原因 | 解决 |
|------|------|------|
| 缺少必填字段 [pipeline_name] | JSON 缺少流水线名称 | 添加 pipeline_name 字段 |
| 检测到循环依赖！涉及节点：A, B, C | depends_on 形成环 | 移除环路上某条依赖 |
| 节点 [X] 依赖了不存在的节点 [Y] | depends_on 引用了不存在的 id | 检查 id 拼写或添加缺失节点 |

---

### 模块 2：拓扑排序与执行计划

**功能**：按依赖关系自动排序节点，展示执行计划。

**触发词**：`执行计划`、`查看拓扑排序`、`流水线执行顺序`

**可运行命令**：

```bash
python scripts/orchestrator.py plan pipeline.json
```

**输出示例**：

```
Step 1: [collector] 数据采集Agent
  角色：从指定数据源采集原始数据
  依赖：无（首节点）
  超时：60秒 | 重试：3次 | 降级：skip
  ↓
Step 2: [analyzer] 分析Agent
  角色：对原始数据进行分析和结构化
  依赖：collector
  超时：120秒 | 重试：2次 | 降级：default
  ↓
Step 3: [reporter] 报告生成Agent
  角色：基于分析结果生成最终报告
  依赖：analyzer
  超时：180秒 | 重试：1次 | 降级：abort
```

---

### 模块 3：状态持久化与共享

**功能**：每个Agent的输出自动存入JSON状态文件，下游Agent自动读取上游输出。

**触发词**：`初始化状态`、`保存节点输出`、`查看状态`

**可运行命令**：

```bash
# 初始化状态文件
python scripts/orchestrator.py run pipeline.json

# 标记节点完成（保存输出）
python scripts/state_store.py complete state.json node_id '{"result":"输出数据"}'

# 标记节点失败
python scripts/state_store.py fail state.json node_id "错误描述"

# 查看状态
python scripts/orchestrator.py status state.json
```

**状态文件格式**：

```json
{
  "pipeline_id": "market_research_1751370000",
  "pipeline_name": "市场调研报告生成",
  "status": "running",
  "nodes": {
    "collector": {
      "status": "completed",
      "output_data": {"raw_data": "采集到的数据..."},
      "started_at": "2026-07-01T17:30:00",
      "completed_at": "2026-07-01T17:30:45"
    },
    "analyzer": {
      "status": "pending",
      "depends_on": ["collector"]
    }
  }
}
```

**状态传递机制**：当 `analyzer` 开始执行时，引擎自动注入 `collector` 的 `output_data` 作为输入。

---

### 模块 4：错误恢复（三级降级）

**功能**：节点失败时，按"重试→降级→中止"三级策略自动恢复。

**触发词**：`重试节点`、`节点失败了`、`降级处理`、`错误恢复`

**可运行命令**：

```bash
# Level 1: 重试
python scripts/error_recovery.py retry state.json node_id "错误信息"

# Level 2: 降级（自动根据 fallback 策略执行）
python scripts/error_recovery.py fallback state.json node_id "错误信息"

# 下游影响分析
python scripts/error_recovery.py impact state.json node_id
```

**三级策略说明**：

| 级别 | 策略 | 说明 |
|------|------|------|
| Level 1 | 重试 | 按配置次数重试，间隔指数退避（2s→4s→8s） |
| Level 2 | 降级-skip | 跳过节点，下游收到空输出 |
| Level 2 | 降级-default | 使用预设默认值，下游收到默认值 |
| Level 2 | 降级-abort | 中止流水线，保存状态供断点续传 |
| Level 3 | 中止 | 保存状态 → 生成部分报告 → 等待人工干预 |

---

### 模块 5：断点续传

**功能**：流水线中断后，从失败节点恢复执行，跳过已完成节点。

**触发词**：`断点续传`、`恢复执行`、`从断点继续`

**可运行命令**：

```bash
# 查看当前状态
python scripts/orchestrator.py status state.json

# 断点续传（重置失败节点为待执行）
python scripts/orchestrator.py resume state.json

# 继续执行
python scripts/orchestrator.py step state.json
```

**工作原理**：
1. 读取 `pipeline_state.json`
2. 将 `failed` 且未达最大重试次数的节点重置为 `pending`
3. 已 `completed` 的节点保持不变（跳过）
4. 从第一个 `pending` 节点继续执行

---

### 模块 6：执行报告生成

**功能**：自动生成 Markdown 执行报告，包含概览、节点详情、失败分析、建议。

**触发词**：`生成报告`、`执行报告`、`流水线报告`

**可运行命令**：

```bash
python scripts/orchestrator.py report state.json [output.md]
```

**报告内容**：
- 流水线概览（状态/耗时/节点统计）
- 各节点执行详情（状态/时长/重试次数/输出数据/错误信息）
- 失败节点下游影响分析
- 后续操作建议

**输出路径**：默认 `pipeline_report_[pipeline_id].md`

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

# 生成执行报告
python scripts/orchestrator.py report state.json

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
A: 不需要。所有脚本仅使用 Python 标准库（json/os/sys/time/datetime），开箱即用。

### Q: AI 在编排中扮演什么角色？
A: AI 是编排器。脚本提供基础设施（验证/状态/报告），AI 负责理解用户需求→生成DAG→逐步执行各节点任务→管理错误恢复。详见 `references/examples.md`。

### Q: 如何处理节点间数据传递？
A: 节点完成时将输出保存到 `pipeline_state.json`，下游节点执行时引擎自动注入上游输出。详见 `references/state-sharing-protocol.md`。

### Q: 节点失败后怎么恢复？
A: 三级策略：重试（自动）→ 降级（skip/default/abort）→ 断点续传。详见 `references/error-recovery-patterns.md`。

### Q: 如何查看完整的端到端示例？
A: 参见 `references/examples.md`，包含竞品分析、数据处理（含错误恢复）、断点续传三个完整案例。

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
| `templates/pipeline_dag_template.json` | DAG 定义模板（四阶段流水线示例） |
| `templates/state_schema.json` | 状态文件 JSON Schema 规范 |
| `tests/test_pipeline.json` | 测试用 DAG（三节点，用于自检） |
