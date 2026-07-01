#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态持久化管理器 - 多Agent协作编排引擎

功能：pipeline_state.json 的创建、读取、更新、查询 + 断点续传支持
零第三方依赖，仅使用 Python 标准库

★★★ 重要提示 ★★★
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 首次使用需要创建 pipeline.json 文件（定义流水线的 JSON 配置）
   创建后运行：python orchestrator.py run <pipeline.json>
   这会自动生成 pipeline_state.json 状态文件

2. 后续所有操作都基于 pipeline_state.json（不是 pipeline.json！）

3. 文件路径中不要使用中文或特殊字符，建议使用英文路径
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import sys
import os
import time
from datetime import datetime


def get_timestamp():
    """获取当前时间戳（ISO 8601 格式）"""
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def init_state(pipeline, state_path=None):
    """初始化状态文件

    首次运行流水线时使用，将 pipeline 定义的节点转换为可执行的状态文件。
    """
    if state_path is None:
        state_path = pipeline.get('state_store', {}).get('path', './pipeline_state.json')

    # 用 pipeline_name + 时间戳生成唯一 ID
    pipeline_id = pipeline.get('pipeline_name', 'unnamed').replace(' ', '_') + '_' + str(int(time.time()))

    state = {
        "pipeline_id": pipeline_id,
        "pipeline_name": pipeline.get('pipeline_name', 'unnamed'),
        "version": pipeline.get('version', '1.0'),
        "created_at": get_timestamp(),
        "updated_at": get_timestamp(),
        "status": "initialized",  # initialized → running → completed / aborted
        "nodes": {}
    }

    # 将每个 agent 转换为状态节点
    for agent in pipeline.get('agents', []):
        aid = agent.get('id')
        state['nodes'][aid] = {
            "name": agent.get('name', aid),
            "role": agent.get('role', ''),
            "status": "pending",       # pending → running → completed / failed / skipped
            "depends_on": agent.get('depends_on', []),
            "retry_count": 0,
            "max_retry": agent.get('retry', 3),
            "timeout": agent.get('timeout', 60),
            "fallback": agent.get('fallback', 'abort'),
            "inputs": agent.get('inputs', []),
            "outputs": agent.get('outputs', []),
            "output_data": {},
            "error": None,
            "started_at": None,
            "completed_at": None
        }

    save_state(state, state_path)
    print(f"状态文件已初始化：{state_path}")
    print(f"流水线 ID：{pipeline_id}")
    print(f"节点数量：{len(state['nodes'])}")
    return state, state_path


def save_state(state, state_path):
    """保存状态到文件（原子写入，避免写入过程中崩溃导致文件损坏）"""
    state['updated_at'] = get_timestamp()
    tmp_path = state_path + '.tmp'
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        # os.replace 是原子操作，确保不会出现半写文件
        os.replace(tmp_path, state_path)
    except Exception as e:
        print(f"错误：无法写入状态文件 [{state_path}]")
        print(f"  原因：{e}")
        print(f"  建议：检查磁盘空间和文件权限")
        sys.exit(1)


def load_state(state_path):
    """加载状态文件

    如果文件不存在或 JSON 格式损坏，会给出清晰的报错和修复建议。
    """
    if not os.path.exists(state_path):
        print(f"错误：状态文件不存在 [{state_path}]")
        print("  修复步骤：")
        print("  1. 确认路径是否正确（区分大小写）")
        print("  2. 运行以下命令初始化：")
        print("     python orchestrator.py run <pipeline.json>")
        sys.exit(1)
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误：状态文件 JSON 格式不合法 [{state_path}]")
        print(f"  详情：第 {e.lineno} 行 - {e.msg}")
        print(f"  建议：使用 JSON 校验工具检查文件，或重新初始化")
        sys.exit(1)


def complete_node(state_path, node_id, output_json=None):
    """标记节点为已完成

    使用方式：
      python state_store.py complete <state.json> <node_id> '{"key":"value"}'

    output_json 必须是合法 JSON 字符串（建议用单引号包裹）。
    如果 output_json 不是合法 JSON 字符串，会降级为 {"raw_output": "原字符串保存"}。
    """
    state = load_state(state_path)
    if node_id not in state['nodes']:
        print(f"错误：节点 [{node_id}] 不存在")
        print(f"  可用节点：{', '.join(state['nodes'].keys())}")
        print(f"  修复：检查 pipeline.json 中的 id 是否与命令中的 id 一致")
        sys.exit(1)

    node = state['nodes'][node_id]
    node['status'] = 'completed'
    node['completed_at'] = get_timestamp()

    if output_json:
        try:
            output_data = json.loads(output_json)
        except json.JSONDecodeError:
            # 不是合法 JSON → 降级保存原始字符串
            output_data = {"raw_output": output_json}
        node['output_data'] = output_data
    else:
        node['output_data'] = {"result": "completed"}

    all_done = all(n['status'] == 'completed' for n in state['nodes'].values())
    if all_done:
        state['status'] = 'completed'
    else:
        state['status'] = 'running'

    save_state(state, state_path)
    print(f"节点 [{node_id}] 已标记为完成")
    if output_json:
        print(f"  输出数据已保存")
    print(f"  完成时间：{node['completed_at']}")

    if all_done:
        print(f"\n🎉 流水线 [{state['pipeline_name']}] 全部节点已完成！")
        print(f"  查看完整报告：python orchestrator.py report {state_path}")
    return state


def fail_node(state_path, node_id, error_msg):
    """标记节点为失败

    ★★★ 注意 ★★★
    此命令只是"标记"失败。实际的重试或降级逻辑需要运行：
      python error_recovery.py retry <state.json> <node_id> '<错误描述>'

    易错点：
    - error_msg 包含空格时，整个字符串必须用引号包裹
    - error_msg 建议简洁（不超过50字），详细说明可以放在 output_data 中

    使用方式：
      python state_store.py fail <state.json> <node_id> '错误描述'
    """
    state = load_state(state_path)
    if node_id not in state['nodes']:
        print(f"错误：节点 [{node_id}] 不存在")
        print(f"  可用节点：{', '.join(state['nodes'].keys())}")
        sys.exit(1)

    node = state['nodes'][node_id]
    node['status'] = 'failed'
    node['error'] = error_msg
    node['retry_count'] = node.get('retry_count', 0) + 1

    save_state(state, state_path)
    print(f"节点 [{node_id}] 标记为失败")
    print(f"  错误信息：{error_msg}")
    print(f"  已重试次数：{node['retry_count']}/{node['max_retry']}")

    # 给出下一步操作提示
    if node['retry_count'] >= node['max_retry']:
        print(f"\n  已达最大重试次数，下一步：")
        fallback = node.get('fallback', 'abort')
        if fallback == 'skip':
            print(f"  将自动运行降级策略：跳过此节点")
        elif fallback == 'default':
            print(f"  将自动运行降级策略：使用预设默认值")
        else:
            print(f"  将自动运行降级策略：中止流水线")
        print(f"\n  运行触发降级：python error_recovery.py retry {state_path} {node_id} '{error_msg}'")
    else:
        print(f"\n  下一步：修复后重新运行")
        print(f"  重试命令：python error_recovery.py retry {state_path} {node_id} '{error_msg}'")

    return state


def show_status(state_path):
    """显示流水线当前状态

    输出格式说明：
    ✅ = completed（已完成）
    ❌ = failed（失败）
    🔄 = running（执行中）
    ⏳ = pending（等待执行）
    ⏭️ = skipped（已跳过）
    """
    state = load_state(state_path)
    print("=" * 60)
    print(f"  流水线状态：{state['pipeline_name']}")
    print(f"  流水线 ID：{state['pipeline_id']}")
    print(f"  总状态：{state['status']}")
    print(f"  创建时间：{state['created_at']}")
    print(f"  更新时间：{state['updated_at']}")
    print("=" * 60)

    for aid, node in state['nodes'].items():
        status_icon = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌',
            'skipped': '⏭️'
        }.get(node['status'], '?')

        line = f"  {status_icon} [{aid}] {node.get('name', aid)} - {node['status']}"
        if node['status'] == 'failed':
            line += f" (重试 {node['retry_count']}/{node['max_retry']})"
        if node['status'] == 'completed' and node.get('completed_at'):
            line += f" @ {node['completed_at']}"
        print(line)
        if node.get('error'):
            print(f"      错误：{node['error']}")

    completed = sum(1 for n in state['nodes'].values() if n['status'] == 'completed')
    failed = sum(1 for n in state['nodes'].values() if n['status'] == 'failed')
    skipped = sum(1 for n in state['nodes'].values() if n['status'] == 'skipped')
    pending = sum(1 for n in state['nodes'].values() if n['status'] == 'pending')
    print(f"\n  汇总：{completed} 完成 / {pending} 待执行 / {failed} 失败 / {skipped} 跳过 / 共 {len(state['nodes'])} 节点")
    print("=" * 60)


def get_next_node(state_path):
    """获取下一个待执行的节点（依赖已全部完成）

    ★★★ 注意：此函数会修改状态文件！★★★
    1. 找到的节点会被标记为 running（防止重复执行）
    2. 如果节点超时未响应（AI 崩溃），会自动重置为 pending
    3. 所有修改会立即保存到状态文件

    使用方式：
      python state_store.py next <state.json>
    或（推荐）：
      python orchestrator.py step <state.json>
    """
    state = load_state(state_path)

    # 第一遍：检查是否有 running 超时的节点，防止 AI 崩溃导致流水线卡死
    for aid, node in state['nodes'].items():
        if node['status'] == 'running' and node.get('started_at'):
            try:
                started = datetime.strptime(node['started_at'], '%Y-%m-%dT%H:%M:%S')
                elapsed = (datetime.now() - started).total_seconds()
                timeout = node.get('timeout', 60)
                if elapsed > timeout * 2:
                    print(f"  ⚠️ [自动恢复] 节点 [{aid}] 已 running {elapsed:.0f} 秒，"
                          f"超过超时限制 ({timeout}×2={timeout*2}秒)，自动重置为 pending")
                    node['status'] = 'pending'
                    node['started_at'] = None
                    node['error'] = f"自动重置：超时未响应（{elapsed:.0f}秒）"
                    save_state(state, state_path)
            except (ValueError, TypeError):
                pass

    # 第二遍：找到第一个依赖全部完成的 pending 节点
    for aid, node in state['nodes'].items():
        if node['status'] in ('completed', 'skipped', 'running'):
            continue
        if node['status'] == 'failed' and node['retry_count'] >= node['max_retry']:
            continue

        deps = node.get('depends_on', [])
        all_deps_done = all(
            state['nodes'].get(dep, {}).get('status') in ('completed', 'skipped')
            for dep in deps
        )

        if all_deps_done:
            # 标记为 running，防止被重复获取
            node['status'] = 'running'
            node['started_at'] = get_timestamp()
            save_state(state, state_path)

            # 收集上游输出作为下游输入
            upstream_outputs = {}
            for dep in deps:
                dep_node = state['nodes'].get(dep, {})
                upstream_outputs[dep] = dep_node.get('output_data', {})

            print(f"下一个待执行节点：[{aid}] {node.get('name', aid)}")
            print(f"  角色：{node.get('role', '未指定')}")
            print(f"  依赖：{', '.join(deps) if deps else '无（首节点）'}")
            print(f"  超时：{node['timeout']}秒")
            print(f"  最大重试：{node['max_retry']}次")
            print(f"  降级策略：{node['fallback']}")
            if upstream_outputs:
                print(f"  上游输出已自动注入到 input_data：")
                for dep, data in upstream_outputs.items():
                    preview = json.dumps(data, ensure_ascii=False)[:200]
                    print(f"    [{dep}] → {preview}")
            print(f"\n请执行此节点的任务，完成后运行：")
            print(f"  成功：python state_store.py complete {state_path} {aid} '{{\"result\":\"...\"}}'")
            print(f"  失败：python error_recovery.py retry {state_path} {aid} '错误描述'")
            return aid

    # 处理没有可执行节点的情况
    remaining = {aid: n for aid, n in state['nodes'].items()
                 if n['status'] not in ('completed', 'skipped')}

    if not remaining:
        # 检查是否全部完成
        all_done = all(n['status'] in ('completed', 'skipped')
                       for n in state['nodes'].values())
        if all_done:
            print("🎉 所有节点均已处理完毕！")
        else:
            print("⚠️ 没有可执行的节点，但流水线尚未完成")
            print("  可能原因：部分节点处于 running 状态（可能是残留）")
    else:
        # 有待处理节点但无法执行 → 卡在依赖上
        blocked = [aid for aid, n in remaining.items()
                   if n['status'] == 'pending']
        failed_no_retry = [aid for aid, n in remaining.items()
                           if n['status'] == 'failed' and n['retry_count'] >= n['max_retry']]

        if failed_no_retry:
            print(f"⚠️ 节点 {', '.join(failed_no_retry)} 已达到最大重试次数")
            print(f"  请检查日志，修复问题后运行断点续传：")
            print(f"  python orchestrator.py resume {state_path}")
        elif blocked:
            print(f"⏳ 无法继续执行，{len(blocked)} 个节点被上游阻塞：{', '.join(blocked)}")
            print(f"  请检查上游节点状态")

    return None


def resume_pipeline(state_path):
    """断点续传：从失败处恢复执行

    ★★★ 功能说明 ★★★
    1. 将所有 failed 节点重置为 pending
    2. 重置 retry_count 归零（给予全新重试机会）
    3. 清除之前的 error 信息
    4. 不影响已完成的节点

    使用场景：
    - 节点因网络问题失败后，修复网络后恢复
    - 节点因超时失败后，需要重新开始

    使用方式：
      python state_store.py resume <state.json>
    或（推荐）：
      python orchestrator.py resume <state.json>
    """
    state = load_state(state_path)

    print("=" * 60)
    print("  断点续传模式")
    print(f"  流水线：{state['pipeline_name']}")
    print("=" * 60)

    reset_count = 0
    for aid, node in state['nodes'].items():
        if node['status'] == 'failed':
            node['status'] = 'pending'
            node['retry_count'] = 0
            node['error'] = None
            reset_count += 1

    state['status'] = 'running'
    save_state(state, state_path)

    completed = sum(1 for n in state['nodes'].values() if n['status'] == 'completed')
    total = len(state['nodes'])
    print(f"已完成节点：{completed}/{total}")

    if reset_count > 0:
        print(f"重置失败节点：{reset_count} 个（已重置为待执行，重试计数归零）")
        print(f"\n继续执行请运行：python orchestrator.py step {state_path}")
    else:
        print(f"没有需要重置的失败节点")

    print("=" * 60)


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("状态持久化管理器 - 多Agent协作编排引擎")
        print("=" * 50)
        print("命令列表：")
        print("  python state_store.py init <pipeline.json> [state_path]")
        print("      → 首次创建 pipeline.json 时使用，生成状态文件")
        print("")
        print("  python state_store.py complete <state.json> <node_id> '[json]'")
        print("      → 节点成功完成后调用，保存输出数据")
        print("")
        print("  python state_store.py fail <state.json> <node_id> '错误描述'")
        print("      → 节点失败时调用（注意：不会自动重试/降级）")
        print("")
        print("  python state_store.py status <state.json>")
        print("      → 查看流水线当前状态")
        print("")
        print("  python state_store.py next <state.json>")
        print("      → 获取下一个待执行节点（会自动标记为running）")
        print("")
        print("  python state_store.py resume <state.json>")
        print("      → 断点续传（重置所有失败节点为pending）")
        print("")
        print("★★★ 重要：错误处理流程 ★★★")
        print("  1. 执行失败时，先运行 fail 标记失败")
        print("  2. 然后运行 error_recovery.py retry 触发")
        print("     - 重试（未达max_retry）")
        print("     - 或降级（已达max_retry，根据fallback策略）")
        print("  3. abort 策略走 resume 断点续传重新执行")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == 'init':
        if len(sys.argv) < 3:
            print("错误：缺少参数")
            print("用法：python state_store.py init <pipeline.json> [state_path]")
            sys.exit(1)
        pipeline_path = sys.argv[2]
        state_path = sys.argv[3] if len(sys.argv) > 3 else None
        try:
            with open(pipeline_path, 'r', encoding='utf-8') as f:
                pipeline = json.load(f)
            init_state(pipeline, state_path)
        except FileNotFoundError:
            print(f"错误：找不到 pipeline 文件 [{pipeline_path}]")
            print(f"  请确认路径正确，且文件存在")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"错误：pipeline 文件 JSON 格式不合法")
            print(f"  详情：第 {e.lineno} 行 - {e.msg}")
            sys.exit(1)

    elif cmd == 'complete':
        if len(sys.argv) < 4:
            print("错误：参数不足")
            print("用法：python state_store.py complete <state.json> <node_id> '[json]'")
            print("示例：python state_store.py complete state.json node_a '{\"result\":\"hello\"}'")
            sys.exit(1)
        output_json = sys.argv[4] if len(sys.argv) > 4 else None
        complete_node(sys.argv[2], sys.argv[3], output_json)

    elif cmd == 'fail':
        if len(sys.argv) < 4:
            print("错误：参数不足")
            print("用法：python state_store.py fail <state.json> <node_id> '错误描述'")
            print("示例：python state_store.py fail state.json node_a '网络请求超时'")
            print("")
            print("提示：错误描述包含空格时，必须用单引号包裹整个字符串")
            sys.exit(1)
        error_msg = sys.argv[4] if len(sys.argv) > 4 else "未知错误"
        fail_node(sys.argv[2], sys.argv[3], error_msg)

    elif cmd == 'status':
        if len(sys.argv) < 3:
            print("错误：缺少[state.json路径]")
            print("用法：python state_store.py status <state.json>")
            sys.exit(1)
        show_status(sys.argv[2])

    elif cmd == 'next':
        if len(sys.argv) < 3:
            print("错误：缺少[state.json路径]")
            print("用法：python state_store.py next <state.json>")
            sys.exit(1)
        get_next_node(sys.argv[2])

    elif cmd == 'resume':
        if len(sys.argv) < 3:
            print("错误：缺少[state.json路径]")
            print("用法：python state_store.py resume <state.json>")
            sys.exit(1)
        resume_pipeline(sys.argv[2])

    else:
        print(f"错误：未知命令 [{cmd}]")
        print("运行 python state_store.py --help 查看可用命令")
        sys.exit(1)
