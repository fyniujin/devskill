#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行报告生成器 - 多Agent协作编排引擎 v3.0

功能：根据 pipeline_state.json 生成 Markdown 执行报告 + HTML 甘特图
零第三方依赖，仅使用 Python 标准库

★★★ 安全说明 ★★★
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 报告文件包含节点输出数据，可能含有敏感信息
2. 建议将报告文件存放在安全位置，避免未授权访问
3. 报告中的 output_data 字段会原样输出，注意脱敏
4. 报告文件默认保存在 state.json 同目录下，注意目录权限

★★★ 使用时机 ★★★
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
可在任意阶段运行，生成当前快照报告：
  - 执行中 → 查看进度
  - 完成后 → 查看最终结果
  - 中止后 → 查看部分结果和失败原因

使用方式：
  python pipeline_reporter.py <state.json>
  python pipeline_reporter.py <state.json> report.md
  或（推荐）：
  python orchestrator.py report <state.json>
  python orchestrator.py report <state.json> report.md

报告内容：
  - 流水线概览（状态、耗时、节点统计）
  - 各节点执行详情（状态、时长、重试次数、输出、错误）
  - 失败节点的下游影响分析
  - 后续操作建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import sys
import os
from datetime import datetime


def load_state(state_path):
    """加载状态文件

    如果文件不存在或 JSON 格式损坏，会给出清晰的报错。
    """
    if not os.path.exists(state_path):
        print(f"错误：状态文件不存在 [{state_path}]")
        print("  修复：运行 orchestrator.py run <pipeline.json> 初始化")
        sys.exit(1)
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误：状态文件 JSON 格式不合法 [{state_path}]")
        print(f"  详情：第 {e.lineno} 行 - {e.msg}")
        sys.exit(1)


def parse_time(timestamp_str):
    """解析时间戳，返回可读格式"""
    if not timestamp_str:
        return "-"
    try:
        dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return str(timestamp_str)


def calc_duration(start, end):
    """计算时长，返回人类可读格式

    格式：X时X分X秒 / X分X秒 / X秒
    """
    if not start or not end:
        return "-"
    try:
        s = datetime.strptime(start, '%Y-%m-%dT%H:%M:%S')
        e = datetime.strptime(end, '%Y-%m-%dT%H:%M:%S')
        delta = e - s
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins}分{secs:02d}秒"
        else:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            return f"{hours}时{mins:02d}分"
    except (ValueError, TypeError):
        return "-"


def generate_report(state_path, output_path=None):
    """生成 Markdown 执行报告

    ★★★ 安全提示 ★★★
    - 报告包含节点输出数据，可能含有敏感信息
    - 默认路径：pipeline_report_<pipeline_id>.md（与 state.json 同目录）
    - 建议将报告存放在受保护的目录中

    参数：
      state_path: pipeline_state.json 路径
      output_path: 输出 Markdown 文件路径（可选）
    """
    state = load_state(state_path)

    pipeline_name = state.get('pipeline_name', '未命名流水线')
    pipeline_id = state.get('pipeline_id', 'unknown')
    overall_status = state.get('status', 'unknown')

    nodes = state.get('nodes', {})

    # 统计各状态节点数量
    total = len(nodes)
    completed = sum(1 for n in nodes.values() if n['status'] == 'completed')
    failed = sum(1 for n in nodes.values() if n['status'] == 'failed')
    skipped = sum(1 for n in nodes.values() if n['status'] == 'skipped')
    pending = sum(1 for n in nodes.values() if n['status'] in ('pending', 'running'))

    total_retries = sum(n.get('retry_count', 0) for n in nodes.values())

    # 计算总耗时（从第一个节点开始到最后一个节点结束）
    times = []
    for n in nodes.values():
        if n.get('started_at') and n.get('completed_at'):
            times.append((n['started_at'], n['completed_at']))
    total_duration = "-"
    if times:
        all_times = [t for pair in times for t in pair]
        total_duration = calc_duration(min(all_times), max(all_times))

    # 状态的中文说明
    status_map = {
        'completed': '✅ 成功完成',
        'aborted': '🛑 已中止',
        'running': '🔄 执行中',
        'failed': '❌ 执行失败',
        'initialized': '⏳ 已初始化（未开始）'
    }
    status_text = status_map.get(overall_status, overall_status)

    # 构建 Markdown 报告
    lines = []
    lines.append(f"# 📊 流水线执行报告：{pipeline_name}")
    lines.append("")
    lines.append(f"> 自动生成时间：{parse_time(state.get('updated_at', datetime.now().strftime('%Y-%m-%dT%H:%M:%S')))}")
    lines.append("")

    # 概览
    lines.append("## 概览")
    lines.append("")
    lines.append("| 项目 | 值 |")
    lines.append("|------|------|")
    lines.append(f"| 流水线名称 | {pipeline_name} |")
    lines.append(f"| 流水线 ID | `{pipeline_id}` |")
    lines.append(f"| 总状态 | **{status_text}** |")
    lines.append(f"| 创建时间 | {parse_time(state.get('created_at'))} |")
    lines.append(f"| 更新时间 | {parse_time(state.get('updated_at'))} |")
    lines.append(f"| 总耗时 | {total_duration} |")
    lines.append(f"| 节点总数 | {total} |")
    lines.append(f"| ✅ 成功 | {completed} |")
    lines.append(f"| ❌ 失败 | {failed} |")
    lines.append(f"| ⏭️ 跳过 | {skipped} |")
    lines.append(f"| ⏳ 待执行 | {pending} |")
    lines.append(f"| 🔁 总重试次数 | {total_retries} |")
    lines.append("")

    # 节点执行详情
    lines.append("## 节点执行详情")
    lines.append("")

    status_icons = {
        'completed': 'PASS',
        'failed': 'FAIL',
        'skipped': 'SKIP',
        'pending': 'WAIT',
        'running': 'RUN '
    }

    for aid, node in nodes.items():
        icon = status_icons.get(node['status'], '?')
        name = node.get('name', aid)
        role = node.get('role', '')

        lines.append(f"### [{aid}] {name}")
        lines.append("")
        lines.append("| 属性 | 值 |")
        lines.append("|------|------|")
        lines.append(f"| 状态 | **{icon}** - {node['status']} |")
        lines.append(f"| 角色 | {role} |")
        deps_str = ', '.join(node.get('depends_on', [])) or '无（首节点）'
        lines.append(f"| 依赖 | {deps_str} |")
        lines.append(f"| 开始时间 | {parse_time(node.get('started_at'))} |")
        lines.append(f"| 完成时间 | {parse_time(node.get('completed_at'))} |")
        lines.append(f"| 执行时长 | {calc_duration(node.get('started_at'), node.get('completed_at'))} |")
        lines.append(f"| 重试次数 | {node.get('retry_count', 0)} / {node.get('max_retry', 3)} |")
        lines.append(f"| 降级策略 | {node.get('fallback', 'abort')} |")
        lines.append(f"| 超时设置 | {node.get('timeout', 60)} 秒 |")
        lines.append("")

        if node.get('error'):
            lines.append("**错误信息：**")
            lines.append("```")
            lines.append(node['error'])
            lines.append("```")
            lines.append("")

        if node.get('output_data') and node['status'] in ('completed', 'skipped'):
            output_str = json.dumps(node['output_data'], ensure_ascii=False, indent=2)
            if len(output_str) > 2000:
                output_str = output_str[:2000] + "\n... (输出过长，已截断)"
            lines.append("**输出数据：**")
            lines.append("```json")
            lines.append(output_str)
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")

    # 失败影响分析
    if failed > 0:
        lines.append("## 失败影响分析")
        lines.append("")
        for aid, node in nodes.items():
            if node['status'] == 'failed':
                affected = []
                for other_id, other_node in nodes.items():
                    if aid in other_node.get('depends_on', []):
                        affected.append(other_id)
                if affected:
                    lines.append(f"- ❌ 节点 **[{aid}]** 失败，直接影响了下游节点：{', '.join(affected)}")
                else:
                    lines.append(f"- ❌ 节点 **[{aid}]** 失败，无直接下游节点受影响（末端节点）")
        lines.append("")

    # 后续操作建议
    lines.append("## 后续操作建议")
    lines.append("")
    if overall_status == 'completed':
        lines.append("- ✅ 流水线已全部成功完成，可查看各节点输出数据获取结果。")
    elif overall_status == 'aborted':
        lines.append("- 🛑 流水线被中止，建议：")
        lines.append("  1. 查看上方失败节点的错误信息")
        lines.append("  2. 修复问题后运行断点续传：`python orchestrator.py resume <state.json> --force`")
        lines.append("  3. 重新执行：`python orchestrator.py step <state.json>`")
    elif overall_status == 'running':
        lines.append("- 🔄 流水线正在执行中，继续运行：`python orchestrator.py step <state.json>`")
    elif overall_status == 'initialized':
        lines.append("- ⏳ 流水线已初始化但未开始，运行：`python orchestrator.py step <state.json>`")
    else:
        lines.append(f"- 当前状态：{overall_status}，运行 `python orchestrator.py status <state.json>` 查看详情")
    lines.append("")

    lines.append("---")
    lines.append(f"*本报告由多Agent协作编排引擎自动生成*")

    report = '\n'.join(lines)

    # 输出报告
    if output_path is None:
        report_filename = f"pipeline_report_{pipeline_id}.md"
        output_path = os.path.join(os.path.dirname(os.path.abspath(state_path)) or '.', report_filename)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 执行报告已生成：{output_path}")
    print(f"  流水线状态：{status_text}")
    print(f"  节点统计：{completed}成功 / {failed}失败 / {skipped}跳过 / {pending}待执行")
    print(f"  总重试：{total_retries} 次")
    print(f"  总耗时：{total_duration}")
    print(f"  ⚠️ 安全提示：报告文件可能包含节点输出数据，请妥善保管")
    return output_path


def generate_html_gantt(state_path, output_path=None):
    """生成 HTML 甘特图（零依赖，纯 HTML+CSS）"""
    state = load_state(state_path)

    pipeline_name = state.get('pipeline_name', '未命名流水线')
    pipeline_id = state.get('pipeline_id', 'unknown')
    nodes = state.get('nodes', {})

    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(state_path)) or '.',
            f"gantt_{pipeline_id}.html"
        )

    # 收集时间数据
    start_times = []
    end_times = []
    for n in nodes.values():
        if n.get('started_at'):
            start_times.append(n['started_at'])
        if n.get('completed_at'):
            end_times.append(n['completed_at'])

    if not start_times or not end_times:
        print("⚠️ 没有足够的时间数据生成甘特图（至少需要一个已执行节点）")
        return None

    all_start = min(start_times)
    all_end = max(end_times)

    # 计算总时长（秒）
    try:
        s = datetime.strptime(all_start, '%Y-%m-%dT%H:%M:%S')
        e = datetime.strptime(all_end, '%Y-%m-%dT%H:%M:%S')
        total_seconds = max((e - s).total_seconds(), 1)
    except (ValueError, TypeError):
        total_seconds = 1

    # 颜色映射
    status_colors = {
        'completed': '#22c55e',
        'failed': '#ef4444',
        'skipped': '#eab308',
        'pending': '#9ca3af',
        'running': '#3b82f6',
    }
    status_labels = {
        'completed': '✅ 成功',
        'failed': '❌ 失败',
        'skipped': '⏭️ 跳过',
        'pending': '⏳ 待执行',
        'running': '🔄 执行中',
    }

    # 构建甘特图 HTML 行
    bar_rows = ''
    for aid, node in nodes.items():
        status = node.get('status', 'pending')
        color = status_colors.get(status, '#9ca3af')
        name = node.get('name', aid)
        started = node.get('started_at') or all_start
        completed = node.get('completed_at') or all_end

        try:
            s_dt = datetime.strptime(started, '%Y-%m-%dT%H:%M:%S')
            e_dt = datetime.strptime(completed, '%Y-%m-%dT%H:%M:%S')
            left_pct = max(0, ((s_dt - s).total_seconds() / total_seconds) * 100)
            width_pct = max(2, ((e_dt - s_dt).total_seconds() / total_seconds) * 100)
        except (ValueError, TypeError):
            left_pct = 0
            width_pct = 50

        duration_str = calc_duration(started, completed)
        bar_rows += f'''
      <tr>
        <td class="node-name">{aid}<br><small>{name}</small></td>
        <td class="gantt-cell">
          <div class="gantt-bar" style="left:{left_pct:.1f}%;width:{width_pct:.1f}%;background:{color};" title="{aid}: {duration_str}">
            <span class="bar-label">{duration_str}</span>
          </div>
        </td>
      </tr>'''

    # 生成完整 HTML 文件
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>甘特图 - {pipeline_name}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #1e293b; padding: 2rem; }}
.container {{ max-width: 1200px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.1); padding: 2rem; }}
h1 {{ margin-bottom: .5rem; }}
.subtitle {{ color: #64748b; margin-bottom: 1.5rem; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; }}
.legend-item {{ display: flex; align-items: center; gap: .4rem; font-size: .875rem; }}
.legend-dot {{ width: 14px; height: 14px; border-radius: 3px; }}
table {{ width: 100%; border-collapse: collapse; }}
.node-name {{ width: 180px; padding: .75rem; vertical-align: top; font-weight: 500; border-bottom: 1px solid #e2e8f0; }}
.node-name small {{ color: #64748b; font-weight: 400; }}
.gantt-cell {{ position: relative; height: 36px; border-bottom: 1px solid #e2e8f0; padding: 4px 0; }}
.gantt-bar {{ position: absolute; height: 28px; border-radius: 4px; display: flex; align-items: center; justify-content: center; min-width: 40px; transition: opacity .2s; }}
.gantt-bar:hover {{ opacity: .85; }}
.bar-label {{ font-size: .75rem; color: #fff; font-weight: 600; white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,.3); }}
.footer {{ margin-top: 1.5rem; color: #64748b; font-size: .875rem; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <h1>📊 流水线甘特图</h1>
  <p class="subtitle">{pipeline_name} | 总耗时 {calc_duration(all_start, all_end)}</p>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#22c55e"></div>成功</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div>失败</div>
    <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div>执行中</div>
    <div class="legend-item"><div class="legend-dot" style="background:#eab308"></div>跳过</div>
    <div class="legend-item"><div class="legend-dot" style="background:#9ca3af"></div>待执行</div>
  </div>
  <table>
    <thead>
      <tr style="text-align:left;border-bottom:2px solid #cbd5e1;">
        <th style="padding:.5rem;width:180px;">节点</th>
        <th style="padding:.5rem;">时间轴</th>
      </tr>
    </thead>
    <tbody>
    {bar_rows}
    </tbody>
  </table>
  <p class="footer">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 多Agent协作编排引擎 v3.0</p>
</div>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 甘特图已生成：{output_path}")
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("执行报告生成器 - 多Agent协作编排引擎 v3.0")
        print("=" * 50)
        print("命令：")
        print("  python pipeline_reporter.py report <state.json> [output.md]")
        print("      → 生成 Markdown 执行报告")
        print("  python pipeline_reporter.py gantt <state.json> [output.html]")
        print("      → 生成 HTML 甘特图（颜色编码时间轴）")
        print("")
        print("★★★ 安全提示 ★★★")
        print("  - 报告文件包含节点输出数据，可能含有敏感信息")
        print("  - 建议将报告存放在安全位置，避免未授权访问")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == 'report':
        state_path = args[0]
        output_path = args[1] if len(args) > 1 else None
        generate_report(state_path, output_path)
    elif cmd == 'gantt':
        state_path = args[0]
        output_path = args[1] if len(args) > 1 else None
        generate_html_gantt(state_path, output_path)
    else:
        print(f"未知命令：{cmd}")
        print("可用命令：report / gantt")
        sys.exit(1)
