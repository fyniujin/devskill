#!/usr/bin/env python3
"""
V1.1: 一键安装启动脚本
- 自动创建 venv
- 安装依赖
- 配置 config.yaml
- 启动 SearXNG
- 验证安装
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        timeout=60,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"执行失败: {result.stderr.strip() if result.stderr else result.returncode}")
    return result


def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         隐私搜索 v1.1 - 一键安装启动                        ║
╚══════════════════════════════════════════════════════════════╝
""")

    base_dir = Path(__file__).parent.parent
    scripts_dir = base_dir / "scripts"

    # Step 1: check python
    print("📌 [1/5] 检查 Python 版本...")
    result = run(["python", "--version"], check=False, capture=True)
    if result.returncode != 0:
        print("❌ 未找到 Python，请先安装 Python 3.10+")
        sys.exit(1)
    version_str = result.stdout.strip() or result.stderr.strip()
    print(f"   ✅ {version_str}")

    # Step 2: create venv
    print("\n📌 [2/5] 创建虚拟环境...")
    venv_path = base_dir / ".venv"
    if venv_path.exists():
        print("   ⚠️  .venv 已存在，跳过创建")
    else:
        run([sys.executable, "-m", "venv", str(venv_path)])
        print("   ✅ 虚拟环境已创建")

    # Step 3: install deps
    print("\n📌 [3/5] 安装依赖...")
    pip_path = venv_path / "Scripts" / "pip.exe" if os.name == "nt" else venv_path / "bin" / "pip"
    python_path = venv_path / "Scripts" / "python.exe" if os.name == "nt" else venv_path / "bin" / "python"
    requirements_path = base_dir / "requirements.txt"
    run([str(pip_path), "install", "-q", "-r", str(requirements_path)])
    print("   ✅ 依赖安装完成")

    # Step 4: copy config
    print("\n📌 [4/5] 配置 config.yaml...")
    config_path = base_dir / "config.yaml"
    example_path = base_dir / "references" / "config.yaml.example"
    if config_path.exists():
        print("   ⚠️  config.yaml 已存在，跳过")
    else:
        shutil.copy(str(example_path), str(config_path))
        print("   ✅ config.yaml 已创建")

    # Step 5: verify
    print("\n📌 [5/5] 验证安装...")
    result = run(
        [str(python_path), str(scripts_dir / "search.py"), "--help"],
        check=False, capture=True,
    )
    if result.returncode == 0:
        print("   ✅ search.py 可运行")
    else:
        print(f"   ⚠️  search.py 运行异常: {result.stderr[:200]}")

    result = run(
        [str(python_path), str(scripts_dir / "privacy.py"), "--help"],
        check=False, capture=True,
    )
    if result.returncode == 0:
        print("   ✅ privacy.py 可运行")

    result = run(
        [str(python_path), str(scripts_dir / "update_checker.py"), "--help"],
        check=False, capture=True,
    )
    if result.returncode == 0:
        print("   ✅ update_checker.py 可运行")

    print("""
╔══════════════════════════════════════════════════════════════╗
║  ✅ 安装完成！                                              ║
╠══════════════════════════════════════════════════════════════╣
║  快速使用：                                                 ║
║  1. 启动 SearXNG（可选）：                                  ║
║     python scripts/searxng_manager start --method pip     ║
║  2. 开始搜索：                                              ║
║     python scripts/search.py "关键词"                       ║
║  3. 隐私搜索：                                              ║
║     python scripts/search.py "关键词" --privacy strict     ║
║  4. 查看隐私状态：                                          ║
║     python scripts/privacy report                           ║
║  5. 检查更新：                                              ║
║     python scripts/update_checker check                     ║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 安装失败: {e}")
        print("请手动执行安装步骤，详见 QUICK_START.md")
        sys.exit(1)
