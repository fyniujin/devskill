#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
编排引擎入口 - 多Agent协作编排引擎

功能：统一入口，整合 DAG 验证、状态管理、执行调度、错误恢复、报告生成
零第三方依赖，仅使用 Python 标准库

★★★ 快速上手（3步）★★★
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
step 1 → 创建 pipeline.json（定义流水线，参考 templates/pipeline_dag_template.json）
step 2 → 运行：python orchestrator.py run <pipeline.json>
step 3 → 循环运行：python orchestrator.py step <state.json> + 执行任务 + complete/fail

详细文档：SKILL.md 第一层「快速入门」
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import sys
import os

# 将脚本目录加入 path 以便导入同级模块
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import dag_validator
import state_store
import error_recovery
import pipeline_reporter


def cmd_validate(args):
    """验证 DAG 结构（Schema + 循环检测 + 孤立节点）"""
    if not args:
        print("错误：缺少[pipeline.json路径]")
        print("用法：python orchestrator.py validate <pipeline.json>")
        print("示例：python orchestrator.py validate templates/pipeline_dag_template.json")
        sys.exit(1)
    dag_validator.validate(args[0])


def cmd_plan(args):
    """查看执行计划（拓扑排序 + 节点详情，不做任何修改）"""
    if not args:
        print("错误：缺少[pipeline.json路径]")
        print("用法：python orchestrator.py plan <pipeline.json>")
        sys.exit(1)

    pipeline = dag_validator.load_pipeline(args[0])

    # 验证
    errors, warnings = dag_validator.validate_schema(pipeline)
    if errors:
        print("DAG 结构验证失败，请先修复以下错误：")
        for e in errors:
            print(f"  [错误] {e}")
        sys.exit(1)

    cycle_errors = dag_validator.detect_cycles(pipeline)
    if cycle_errors:
        print("检测到循环依赖，请先修复：")
        for e in cycle_errors:
            print(f"  [错误] {e}")
        sys.exit(1)

    # 拓扑排序
    order = dag_validator.topological_sort(pipeline)
    agents = {a['id']: a for a in pipeline.get('agents', [])}

    print("=" * 60)
    print(f"  执行计划：{pipeline.get('pipeline_name', '未命名')}")
    print("=" * 60)
    print(f"\n拓扑排序执行顺序（共 {len(order)} 个节点）：\n")

    for i, node_id in enumerate(order, 1):
        agent = agents.get(node_id, {})
        name = agent.get('name', node_id)
        role = agent.get('role', '')
        deps = agent.get('depends_on', [])
        retry = agent.get('retry', 3)
        timeout = agent.get('timeout', 60)
        fallback = agent.get('fallback', 'abort')

        print(f"  Step {i}: [{node_id}] {name}")
        print(f"    角色：{role}")
        print(f"    依赖：{', '.join(deps) if deps else '无（首节点）'}")
        print(f"    超时：{timeout}秒 | 重试：{retry}次 | 降级：{fallback}")
        if i < len(order):
            print(f"    ↓")
        print()

    print("=" * 60)
    print(f"\n确认无误后运行：python orchestrator.py run {args[0]}")


def cmd_run(args):
    """初始化并开始执行（验证 → 初始化状态）★★★ 首次使用必做 ★★★"""
    if not args:
        print("错误：缺少[pipeline.json路径]")
        print("用法：python orchestrator.py run <pipeline.json>")
        print("示例：python orchestrator.py run templates/pipeline_dag_template.json")
        print("")
        print("★★★ 提示 ★★★")
        print("  首次使用请先运行 plan 查看执行计划：")
        print("  python orchestrator.py plan <pipeline.json>")
        sys.exit(1)

    pipeline_path = args[0]
    state_path_arg = args[1] if len(args) > 1 else None

    # 先验证
    print("[1/2] 验证 DAG 结构...")
    pipeline = dag_validator.load_pipeline(pipeline_path)
    errors, warnings = dag_validator.validate_schema(pipeline)
    if errors:
        print("验证失败：")
        for e in errors:
            print(f"  [错误] {e}")
        print("\n修复建议：参考 templates/pipeline_dag_template.json 检查字段")
        sys.exit(1)
    cycle_errors = dag_validator.detect_cycles(pipeline)
    if cycle_errors:
        print("循环依赖检测失败：")
        for e in cycle_errors:
            print(f"  [错误] {e}")
        sys.exit(1)
    print("  ✅ 验证通过")

    # 初始化状态
    print("\n[2/2] 初始化状态文件...")
    state, state_path = state_store.init_state(pipeline, state_path_arg)

    print(f"\n✅ 初始化完成！")
    print(f"\n接下来，循环执行以下步骤：")
    print(f"  1. python orchestrator.py step {state_path}")
    print(f"     → 获取待执行节点，AI 执行任务")
    print(f"  2a. 成功 → python state_store.py complete {state_path} <node_id> '输出JSON'")
    print(f"  2b. 失败 → python error_recovery.py retry {state_path} <node_id> '错误描述'")
    print(f"  3. 重复步骤 1-2，直到流水线完成")
    print(f"\n查看状态：")
    print(f"  python orchestrator.py status {state_path}")


def cmd_step(args):
    """执行下一个待处理节点（从状态文件中获取，自动注入上游输出）"""
    if not args:
        print("错误：缺少[state.json路径]")
        print("用法：python orchestrator.py step <state.json>")
        print("示例：python orchestrator.py step pipeline_state.json")
        sys.exit(1)

    state_path = args[0]
    node_id = state_store.get_next_node(state_path)

    if node_id:
        state = state_store.load_state(state_path)
        node = state['nodes'][node_id]
        print(f"\n{'=' * 60}")
        print(f"  🎯 请 AI 执行此节点的任务")
        print(f"{'=' * 60}")
        print(f"节点 ID：{node_id}")
        print(f"节点名称：{node.get('name', node_id)}")
        print(f"角色描述：{node.get('role', '未指定')}")
        print(f"输入参数：{', '.join(node.get('inputs', []))}")
        print(f"期望输出：{', '.join(node.get('outputs', []))}")

        # 注入上游输出
        deps = node.get('depends_on', [])
        if deps:
            print(f"\n📥 上游输出（已自动注入到 input_data）：")
            for dep in deps:
                dep_data = state['nodes'].get(dep, {}).get('output_data', {})
                preview = json.dumps(dep_data, ensure_ascii=False)[:300]
                print(f"  [{dep}] → {preview}")

        print(f"\n完成后运行：")
        print(f"  ✅ 成功：python state_store.py complete {state_path} {node_id} '{{\"result\":\"你的输出\"}}'")
        print(f"  ❌ 失败：python error_recovery.py retry {state_path} {node_id} '错误描述'")
        print(f"{'=' * 60}")


def cmd_status(args):
    """查看当前流水线状态"""
    if not args:
        print("错误：缺少[state.json路径]")
        print("用法：python orchestrator.py status <state.json>")
        sys.exit(1)
    state_store.show_status(args[0])


def cmd_resume(args):
    """断点续传（重置失败节点为待执行，给予全新重试机会）"""
    if not args:
        print("错误：缺少[state.json路径]")
        print("用法：python orchestrator.py resume <state.json>")
        print("示例：python orchestrator.py resume pipeline_state.json")
        print("")
        print("★★★ 使用场景 ★★★")
        print("  - 节点因网络/超时问题失败后，修复问题")
        print("  - 节点因 AI 客户端崩溃导致 running 状态残留")
        print("  - abort 后重新启动")
        sys.exit(1)
    state_store.resume_pipeline(args[0])


def cmd_report(args):
    """生成 Markdown 执行报告（可在任意阶段运行）"""
    if not args:
        print("错误：缺少[state.json路径]")
        print("用法：python orchestrator.py report <state.json> [output.md]")
        print("示例：python orchestrator.py report pipeline_state.json report.md")
        sys.exit(1)
    output = args[1] if len(args) > 1 else None
    pipeline_reporter.generate_report(args[0], output)


def cmd_impact(args):
    """分析指定节点的下游影响（用于排查故障传导范围）"""
    if len(args) < 2:
        print("错误：参数不足")
        print("用法：python orchestrator.py impact <state.json> <node_id>")
        print("示例：python orchestrator.py impact pipeline_state.json node_a")
        sys.exit(1)
    error_recovery.analyze_downstream_impact(args[0], args[1])


USAGE = """
编排引擎 - 多Agent协作编排引擎
================================

用法：python orchestrator.py <command> [args]

命令列表（按使用频率排序）：
  run <pipeline.json> [state]      ★★★ 首次使用 ★★★ 初始化并开始执行
  step <state.json>                 ★☆☆ 逐步执行（获取下一个待执行节点）
  status <state.json>               ★★☆ 查看流水线状态
  resume <state.json>               ★★☆ 断点续传（重置失败节点）
  report <state.json> [output]      ★★☆ 生成 Markdown 执行报告
  validate <pipeline.json>          ★☆  验证 DAG 结构（不修改任何文件）
  plan <pipeline.json>              ★☆  查看执行计划（拓扑排序，不修改任何文件）
  impact <state.json> <node_id>     ☆☆  分析下游影响

典型工作流：
  1. python orchestrator.py plan pipeline.json         # 查看执行计划
  2. python orchestrator.py run pipeline.json           # 初始化
  3. python orchestrator.py step state.json             # 获取待执行节点
  4. AI 执行任务...
  5. python state_store.py complete state.json node '...'
  6. 重复 3-5，直到流水线完成
  7. python orchestrator.py report state.json           # 生成报告

★★★ 三句话总结 ★★★
  1. run  创建流水线
  2. step 获取下一个节点 → AI 执行 → complete/fail
  3. report 生成报告
"""


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(USAGE)
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        'validate': cmd_validate,
        'plan': cmd_plan,
        'run': cmd_run,
        'step': cmd_step,
        'status': cmd_status,
        'resume': cmd_resume,
        'report': cmd_report,
        'impact': cmd_impact,
    }

    if cmd not in commands:
        print(f"错误：未知命令 [{cmd}]")
        print(USAGE)
        sys.exit(1)

    commands[cmd](args)
