#!/usr/bin/env python3
"""
版本更新检查模块（死规则 11）
- 启动时异步检查 SkillHub/GitHub 最新版本
- 有新版本主动提示
- 24h 不重复检查（可配置）
- 支持关闭（隐私优先）
- 网络异常时静默失败，不打扰用户
"""

import asyncio
import hashlib
import json
import os
import sqlite3
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

import aiohttp
import yaml

# ============================================================
# 元数据
# ============================================================

CURRENT_VERSION = "1.0.0"
SKILL_SLUG = "privacy-search"
UPDATE_CHECK_URL = "https://api.skillhub.cn/api/v1/skills/privacy-search"
GITHUB_UPDATE_URL = "https://api.github.com/repos/your-org/privacy-search/releases/latest"
CACHE_DB_PATH = os.path.expanduser("~/.workbuddy/output/.privacy-search-update.db")


# ============================================================
# 数据结构
# ============================================================

@dataclass
class UpdateInfo:
    """更新信息"""
    current_version: str
    latest_version: str
    changelog: str
    download_url: str
    checked_at: datetime
    has_update: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "changelog": self.changelog,
            "download_url": self.download_url,
            "checked_at": self.checked_at.isoformat(),
            "has_update": self.has_update,
        }


# ============================================================
# 缓存管理（SQLite，支持跨进程）
# ============================================================

class UpdateCache:
    """更新检查缓存（SQLite 持久化）"""

    def __init__(self, db_path: str = CACHE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS update_cache (
                    id INTEGER PRIMARY KEY,
                    slug TEXT UNIQUE,
                    latest_version TEXT,
                    checked_at TEXT,
                    has_update INTEGER,
                    changelog TEXT,
                    download_url TEXT
                )
            """)
            conn.commit()

    def get(self, slug: str) -> Optional[Dict[str, Any]]:
        """获取缓存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM update_cache WHERE slug = ?", (slug,)
            ).fetchone()
            if row:
                return dict(row)
        return None

    def set(self, slug: str, version: str, has_update: bool, changelog: str = "", download_url: str = ""):
        """设置缓存"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO update_cache
                (slug, latest_version, checked_at, has_update, changelog, download_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                slug,
                version,
                datetime.now().isoformat(),
                1 if has_update else 0,
                changelog,
                download_url,
            ))
            conn.commit()

    def is_cache_valid(self, slug: str, cache_hours: int = 24) -> bool:
        """检查缓存是否在有效期内"""
        cache = self.get(slug)
        if not cache:
            return False
        try:
            checked_at = datetime.fromisoformat(cache["checked_at"])
            return (datetime.now() - checked_at) < timedelta(hours=cache_hours)
        except (ValueError, KeyError):
            return False


# ============================================================
# 版本比较
# ============================================================

def parse_version(version_str: str) -> tuple:
    """
    解析版本号为可比较的元组
    支持: "1.0.0", "v1.0.0", "1.0.0-beta.1"
    始终返回3元组 (major, minor, patch)，预发布版本通过额外逻辑处理
    """
    import re
    # 去除 v 前缀
    v = version_str.lower().lstrip("v")
    # 分离主版本和预发布标识
    parts = v.split("-", 1)
    main = parts[0]
    pre = parts[1] if len(parts) > 1 else ""

    try:
        nums = tuple(int(x) for x in main.split("."))
    except ValueError:
        nums = (0, 0, 0)

    # 补齐到3位
    nums = nums + (0,) * (3 - len(nums))
    nums = nums[:3]

    # 预发布版本比正式版本小（通过额外权重）
    # 这里不修改元组长度，而是在 compare_versions 中处理
    return nums


def compare_versions(v1: str, v2: str) -> int:
    """
    比较两个版本号
    返回: -1 (v1 < v2), 0 (相等), 1 (v1 > v2)
    预发布版本（含'-'）小于对应正式版本
    """
    # 检查是否为预发布版本
    v1_pre = "-" in v1.lower()
    v2_pre = "-" in v2.lower()

    p1 = parse_version(v1)
    p2 = parse_version(v2)

    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1
    else:
        # 主版本相同时，预发布 < 正式
        if v1_pre and not v2_pre:
            return -1
        elif not v1_pre and v2_pre:
            return 1
        return 0


# ============================================================
# 更新检查器
# ============================================================

class UpdateChecker:
    """版本更新检查器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        update_cfg = config.get("update_check", {})
        self.enabled = update_cfg.get("enabled", True)
        self.check_on_startup = update_cfg.get("check_on_startup", True)
        self.cache_hours = update_cfg.get("cache_hours", 24)
        self.api_url = update_cfg.get("api_url", UPDATE_CHECK_URL)
        self.github_url = update_cfg.get("github_url", GITHUB_UPDATE_URL)
        self.cache = UpdateCache()

    async def check(self, force: bool = False) -> Optional[UpdateInfo]:
        """
        检查更新
        Args:
            force: 是否强制检查（忽略缓存）
        Returns:
            UpdateInfo（有更新）或 None（无更新/网络异常/已禁用）
        """
        if not self.enabled:
            return None

        # 检查缓存
        if not force and self.cache.is_cache_valid(SKILL_SLUG, self.cache_hours):
            return None  # 缓存期内不检查

        # 尝试 SkillHub API
        update_info = await self._check_skillhub()
        if update_info and update_info.has_update:
            return update_info

        # 备用：GitHub Releases API
        update_info = await self._check_github()
        return update_info

    async def _check_skillhub(self) -> Optional[UpdateInfo]:
        """通过 SkillHub API 检查更新"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.api_url,
                    timeout=aiohttp.ClientTimeout(total=5),
                    headers={"User-Agent": "PrivacySearch-UpdateChecker/1.0"}
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    latest = data.get("version", "")
                    if not latest:
                        return None

                    has_update = compare_versions(latest, CURRENT_VERSION) > 0

                    # 更新缓存
                    self.cache.set(
                        slug=SKILL_SLUG,
                        version=latest,
                        has_update=has_update,
                        changelog=data.get("summary_zh", data.get("summary", "")),
                        download_url=data.get("homepage", "https://skillhub.cn/"),
                    )

                    return UpdateInfo(
                        current_version=CURRENT_VERSION,
                        latest_version=latest,
                        changelog=data.get("summary_zh", data.get("summary", "有新版本可用")),
                        download_url=data.get("homepage", "https://skillhub.cn/"),
                        checked_at=datetime.now(),
                        has_update=has_update,
                    )
        except Exception:
            # 网络异常静默失败
            return None

    async def _check_github(self) -> Optional[UpdateInfo]:
        """通过 GitHub Releases API 检查更新（备用）"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.github_url,
                    timeout=aiohttp.ClientTimeout(total=5),
                    headers={"User-Agent": "PrivacySearch-UpdateChecker/1.0"}
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    latest = data.get("tag_name", "").lstrip("v")
                    if not latest:
                        return None

                    has_update = compare_versions(latest, CURRENT_VERSION) > 0

                    self.cache.set(
                        slug=SKILL_SLUG,
                        version=latest,
                        has_update=has_update,
                        changelog=data.get("body", "有新版本可用"),
                        download_url=data.get("html_url", "https://skillhub.cn/"),
                    )

                    return UpdateInfo(
                        current_version=CURRENT_VERSION,
                        latest_version=latest,
                        changelog=data.get("body", "有新版本可用")[:200],
                        download_url=data.get("html_url", "https://skillhub.cn/"),
                        checked_at=datetime.now(),
                        has_update=has_update,
                    )
        except Exception:
            return None


# ============================================================
# 通知显示
# ============================================================

def display_update_notification(update_info: UpdateInfo):
    """在 CLI 中显示更新提示"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  🔔 发现新版本可用                                            ║
╠══════════════════════════════════════════════════════════════╣""")
    print(f"║  当前版本: v{update_info.current_version:<52}║")
    print(f"║  最新版本: v{update_info.latest_version:<52}║")
    print(f"║  更新内容: {update_info.changelog[:50]:<52}║")
    print(f"║  下载地址: {update_info.download_url[:50]:<52}║")
    print("""║                                                              ║
║  更新方式:                                                    ║
║    clawhub install privacy-search --force                     ║
║    或访问 SkillHub 页面手动更新                                ║
╚══════════════════════════════════════════════════════════════╝
""")


def display_no_update():
    """显示已是最新版本"""
    print(f"✅ 已是最新版本 v{CURRENT_VERSION}")


# ============================================================
# CLI 入口
# ============================================================

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """加载配置文件"""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="版本更新检查（死规则 11）")
    parser.add_argument("action", choices=["check", "status", "enable", "disable"], help="操作")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--force", action="store_true", help="强制检查（忽略缓存）")

    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    checker = UpdateChecker(config)

    if args.action == "check":
        update_info = asyncio.run(checker.check(force=args.force))

        if args.json:
            if update_info:
                print(json.dumps(update_info.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(json.dumps({"has_update": False, "version": CURRENT_VERSION}, ensure_ascii=False))
        else:
            if update_info and update_info.has_update:
                display_update_notification(update_info)
            else:
                display_no_update()

    elif args.action == "status":
        cache = checker.cache.get(SKILL_SLUG)
        if args.json:
            output = {
                "current_version": CURRENT_VERSION,
                "latest_version": cache.get("latest_version", "unknown") if cache else "unknown",
                "last_checked": cache.get("checked_at", "never") if cache else "never",
                "has_update": bool(cache.get("has_update", 0)) if cache else False,
                "cache_valid": checker.cache.is_cache_valid(SKILL_SLUG, checker.cache_hours),
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"当前版本: v{CURRENT_VERSION}")
            if cache:
                print(f"最新版本: v{cache.get('latest_version', 'unknown')}")
                print(f"最后更新: {cache.get('checked_at', 'never')}")
                print(f"有更新: {'是' if cache.get('has_update') else '否'}")
            else:
                print("尚未进行过更新检查")

    elif args.action == "enable":
        update_cfg = config.setdefault("update_check", {})
        update_cfg["enabled"] = True
        config_path = args.config or os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print("✅ 已启用版本更新检查")

    elif args.action == "disable":
        update_cfg = config.setdefault("update_check", {})
        update_cfg["enabled"] = False
        config_path = args.config or os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print("✅ 已禁用版本更新检查")


if __name__ == "__main__":
    main()
