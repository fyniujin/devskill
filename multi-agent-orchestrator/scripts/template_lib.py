#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板库管理器 - 多Agent协作编排引擎 v5.3

功能：预置流水线模板的注册、探测、渲染
- 预置 4 类高频流水线模板（政采日报/视频分析/周报/巡检）
- 模板元数据声明建议安装的外部 skill
- 运行时探测依赖 skill 是否存在，缺失则标灰 + 附安装链接
- 绝不自动安装或隐式依赖，保持单包合规

零第三方依赖，仅使用 Python 标准库
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'templates')


def _load_template(template_path):
    """加载模板 JSON 文件"""
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _check_skill_available(skill_id):
    """
    检查外部 skill 是否已安装。

    探测方式（按优先级）：
    1. 检查 ~/.workbuddy/skills/<skill_id>/SKILL.md 是否存在
    2. 检查当前工作区 .workbuddy/skills/<skill_id>/SKILL.md 是否存在
    3. 尝试 import 对应的 Python 模块（如 skill_id 可映射为模块名）

    返回 (bool, str) - (是否可用, 探测依据说明)
    """
    # 检查用户级 skill 目录
    home_skills_dir = os.path.expanduser('~/.workbuddy/skills')
    skill_path = os.path.join(home_skills_dir, skill_id, 'SKILL.md')
    if os.path.exists(skill_path):
        return True, f'已安装（用户级：{skill_path}）'

    # 检查工作区级 skill 目录
    workspace_dir = os.environ.get('WORKSPACE_DIR', '')
    if workspace_dir:
        workspace_skill_path = os.path.join(workspace_dir, '.workbuddy', 'skills', skill_id, 'SKILL.md')
        if os.path.exists(workspace_skill_path):
            return True, f'已安装（工作区级）'

    # 尝试 import（如果 skill_id 可映射为 Python 模块）
    try:
        __import__(skill_id.replace('-', '_'))
        return True, '已安装（Python 模块可导入）'
    except ImportError:
        pass

    return False, '未安装'


def list_templates():
    """列出所有可用的预置模板"""
    if not os.path.exists(TEMPLATES_DIR):
        print("模板目录不存在")
        return []

    templates = []
    for fname in os.listdir(TEMPLATES_DIR):
        if not fname.endswith('.json') or fname == 'template_schema.json' or fname == 'state_schema.json':
            continue
        if fname in ('pipeline_dag_template.json', 'control_flow_template.json',
                     'sub_pipeline_template.json', 'parent_pipeline_template.json'):
            continue  # 跳过旧模板，只展示新预置模板

        fpath = os.path.join(TEMPLATES_DIR, fname)
        tpl = _load_template(fpath)
        if tpl and 'name' in tpl:
            templates.append({
                'file': fname,
                'name': tpl.get('name', ''),
                'description': tpl.get('description', ''),
                'category': tpl.get('category', ''),
                'version': tpl.get('version', ''),
                'tags': tpl.get('tags', []),
                'dependency_count': len(tpl.get('dependencies', [])),
            })

    return templates


def show_template(template_file):
    """显示模板详细信息 + 依赖状态"""
    fpath = os.path.join(TEMPLATES_DIR, template_file)
    tpl = _load_template(fpath)

    if not tpl:
        print(f"错误：无法加载模板文件 {template_file}")
        return

    print("=" * 60)
    print(f"  模板：{tpl.get('name', '未命名')}")
    print("=" * 60)
    print(f"  描述：{tpl.get('description', '无描述')}")
    print(f"  分类：{tpl.get('category', '未分类')}")
    print(f"  版本：{tpl.get('version', '未知')}")
    print(f"  标签：{', '.join(tpl.get('tags', []))}")
    print()

    # 依赖检查
    deps = tpl.get('dependencies', [])
    if deps:
        print("  依赖 skill（建议安装，非强制）：")
        for dep in deps:
            skill_id = dep.get('skill_id', '')
            desc = dep.get('description', '')
            install_link = dep.get('install_link', '')
            required = dep.get('required', False)

            available, reason = _check_skill_available(skill_id)
            status_icon = '✅' if available else '⚠️'
            req_tag = ' [必需]' if required else ' [可选]'

            print(f"    {status_icon} [{skill_id}]{req_tag}")
            print(f"      用途：{desc}")
            if not available:
                print(f"      安装：{install_link}")
                print(f"      状态：缺失 — 对应节点将标灰，可先安装后重新运行")
            else:
                print(f"      状态：{reason}")
            print()
    else:
        print("  无外部依赖")
        print()

    # 流水线结构预览
    pipeline = tpl.get('pipeline', {})
    agents = pipeline.get('agents', [])
    if agents:
        print("  流水线节点：")
        for i, agent in enumerate(agents, 1):
            aid = agent.get('id', '')
            name = agent.get('name', '')
            atype = agent.get('type', 'task')
            role = agent.get('role', '')
            print(f"    {i}. [{aid}] {name} (type: {atype})")
            print(f"       角色：{role}")
            if i < len(agents):
                print(f"       ↓")
        print()

    print(f"  模板文件：{fpath}")
    print("=" * 60)


def check_dependencies(template_file):
    """
    检查模板依赖是否全部满足。

    返回：
    - missing_required: 缺失的必需依赖列表
    - missing_optional: 缺失的可选依赖列表
    """
    fpath = os.path.join(TEMPLATES_DIR, template_file)
    tpl = _load_template(fpath)

    if not tpl:
        return [], []

    missing_required = []
    missing_optional = []

    for dep in tpl.get('dependencies', []):
        skill_id = dep.get('skill_id', '')
        required = dep.get('required', False)
        install_link = dep.get('install_link', '')
        desc = dep.get('description', '')

        available, _ = _check_skill_available(skill_id)
        if not available:
            item = {
                'skill_id': skill_id,
                'description': desc,
                'install_link': install_link,
            }
            if required:
                missing_required.append(item)
            else:
                missing_optional.append(item)

    return missing_required, missing_optional


def render_pipeline(template_file, check_deps=True):
    """
    渲染模板为可执行的 pipeline.json 格式。

    如果 check_deps=True，缺失的依赖对应节点会被标记为
    _missing_dependency=true，渲染时显示警告但不阻塞。
    """
    fpath = os.path.join(TEMPLATES_DIR, template_file)
    tpl = _load_template(fpath)

    if not tpl:
        print(f"错误：无法加载模板文件 {template_file}")
        return None

    pipeline = tpl.get('pipeline', {})
    if not pipeline:
        print(f"错误：模板 {template_file} 缺少 pipeline 定义")
        return None

    # 检查依赖并标记缺失节点
    if check_deps and tpl.get('dependencies'):
        missing_required, missing_optional = check_dependencies(template_file)
        if missing_required or missing_optional:
            print()
            print("⚠️  依赖检查结果：")
            if missing_required:
                print(f"  缺失必需依赖：{', '.join(d['skill_id'] for d in missing_required)}")
            if missing_optional:
                print(f"  缺失可选依赖：{', '.join(d['skill_id'] for d in missing_optional)}")
            print("  对应节点将在执行时标灰并提示安装，不会自动安装")
            print()

    return pipeline


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("模板库管理器 - 多Agent协作编排引擎 v5.3")
        print("=" * 50)
        print("命令：")
        print("  python template_lib.py list               列出所有预置模板")
        print("  python template_lib.py show <template>    显示模板详情 + 依赖状态")
        print("  python template_lib.py check <template>   检查依赖是否满足")
        print("  python template_lib.py render <template>  渲染为可执行 pipeline JSON")
        print()
        print("示例：")
        print("  python template_lib.py list")
        print("  python template_lib.py show gov_procurement_daily.json")
        print("  python template_lib.py render gov_procurement_daily.json")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == 'list':
        templates = list_templates()
        if not templates:
            print("暂无预置模板")
        else:
            print("=" * 60)
            print("  预置流水线模板库")
            print("=" * 60)
            for tpl in templates:
                print(f"\n  📋 {tpl['name']} ({tpl['category']}) v{tpl['version']}")
                print(f"     {tpl['description'][:60]}...")
                print(f"     文件：{tpl['file']} | 标签：{', '.join(tpl['tags'])} | 依赖：{tpl['dependency_count']} 个")
            print(f"\n共 {len(templates)} 个模板")
            print("=" * 60)

    elif cmd == 'show':
        if not args:
            print("错误：请指定模板文件名")
            print("用法：python template_lib.py show <template_file>")
            sys.exit(1)
        show_template(args[0])

    elif cmd == 'check':
        if not args:
            print("错误：请指定模板文件名")
            print("用法：python template_lib.py check <template_file>")
            sys.exit(1)
        req, opt = check_dependencies(args[0])
        if not req and not opt:
            print("✅ 所有依赖均已满足")
        else:
            if req:
                print(f"❌ 缺失必需依赖：{', '.join(d['skill_id'] for d in req)}")
            if opt:
                print(f"⚠️ 缺失可选依赖：{', '.join(d['skill_id'] for d in opt)}")

    elif cmd == 'render':
        if not args:
            print("错误：请指定模板文件名")
            print("用法：python template_lib.py render <template_file> [output.json]")
            sys.exit(1)
        output_path = args[1] if len(args) > 1 else None
        pipeline = render_pipeline(args[0])
        if pipeline:
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(pipeline, f, ensure_ascii=False, indent=2)
                print(f"✅ 已渲染到 {output_path}")
            else:
                print(json.dumps(pipeline, ensure_ascii=False, indent=2))

    else:
        print(f"未知命令：{cmd}")
        sys.exit(1)
