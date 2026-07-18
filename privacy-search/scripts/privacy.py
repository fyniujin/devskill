#!/usr/bin/env python3
"""
F3: 隐私模式模块
- normal / strict 两种模式切换
- strict 模式下仅允许 DuckDuckGo + 本地 SearXNG
- 强制 DNT=1、无 Cookie、无 Referrer
- HTTP 头清理与隐私保护
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import yaml

# ============================================================
# 数据结构
# ============================================================

@dataclass
class PrivacyConfig:
    """隐私配置"""
    mode: str = "strict"  # normal | strict
    strict_allowed_engines: List[str] = field(default_factory=lambda: ["duckduckgo", "searxng"])
    dnt: bool = True
    no_cookie: bool = True
    no_referrer: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


@dataclass
class PrivacyReport:
    """隐私保护报告"""
    mode: str
    blocked_engines: List[str]
    http_headers_cleaned: List[str]
    timestamp: datetime
    recommendations: List[str] = field(default_factory=list)


# ============================================================
# 隐私管理器
# ============================================================

class PrivacyManager:
    """隐私模式管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        privacy_cfg = config.get("privacy", {})
        self.privacy_config = PrivacyConfig(
            mode=privacy_cfg.get("default_mode", "normal"),
            strict_allowed_engines=privacy_cfg.get("strict", {}).get("allowed_engines", ["duckduckgo", "searxng"]),
            dnt=privacy_cfg.get("strict", {}).get("dnt", True),
            no_cookie=privacy_cfg.get("strict", {}).get("no_cookie", True),
            no_referrer=privacy_cfg.get("strict", {}).get("no_referrer", True),
            user_agent=privacy_cfg.get("strict", {}).get("user_agent", ""),
        )

    def get_mode(self) -> str:
        """获取当前隐私模式"""
        return self.privacy_config.mode

    def set_mode(self, mode: str) -> bool:
        """
        切换隐私模式
        Args:
            mode: "normal" 或 "strict"
        Returns:
            是否切换成功
        """
        if mode not in ("normal", "strict"):
            print(f"❌ 未知模式: {mode}，可选: normal / strict")
            return False
        self.privacy_config.mode = mode
        print(f"🔒 已切换到 {mode} 模式")
        return True

    def get_allowed_engines(self) -> List[str]:
        """获取当前模式允许的引擎列表"""
        if self.privacy_config.mode == "strict":
            return self.privacy_config.strict_allowed_engines
        # normal 模式返回配置中的所有默认引擎
        return self.config.get("search", {}).get("default_engines", ["baidu", "bing", "duckduckgo", "searxng"])

    def get_blocked_engines(self) -> List[str]:
        """获取当前模式被屏蔽的引擎列表"""
        all_engines = ["baidu", "bing", "sogou", "360", "duckduckgo", "searxng"]
        allowed = set(self.get_allowed_engines())
        return [e for e in all_engines if e not in allowed]

    def build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        构建隐私安全的 HTTP 请求头
        Args:
            extra: 额外的请求头
        Returns:
            清理后的请求头
        """
        headers = {
            "User-Agent": self.privacy_config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        }

        # strict 模式隐私头
        if self.privacy_config.mode == "strict":
            if self.privacy_config.dnt:
                headers["DNT"] = "1"
            if self.privacy_config.no_referrer:
                headers["Referrer-Policy"] = "no-referrer"

        # 合并额外请求头
        if extra:
            headers.update(extra)

        # strict 模式下移除敏感头
        if self.privacy_config.mode == "strict":
            headers.pop("Cookie", None)
            if self.privacy_config.no_referrer:
                headers.pop("Referer", None)

        return headers

    def generate_report(self) -> PrivacyReport:
        """生成隐私保护报告"""
        blocked = self.get_blocked_engines()
        headers_cleaned = ["Cookie", "Referer"] if self.privacy_config.mode == "strict" else []
        recommendations = []

        if self.privacy_config.mode == "strict":
            recommendations = [
                "当前为 strict 模式，仅使用 DuckDuckGo 和本地 SearXNG",
                "已禁用 Cookie 和 Referrer，启用 DNT",
                "注意：strict 模式不隐藏 IP 地址，建议配合 VPN 使用",
                "SearXNG 仅绑定 127.0.0.1，不暴露到外网",
            ]
        else:
            recommendations = [
                "当前为 normal 模式，搜索引擎可能记录您的 IP 和搜索历史",
                "建议切换到 strict 模式以获得更佳隐私保护",
            ]

        return PrivacyReport(
            mode=self.privacy_config.mode,
            blocked_engines=blocked,
            http_headers_cleaned=headers_cleaned,
            timestamp=datetime.now(),
            recommendations=recommendations,
        )

    def check_engine_allowed(self, engine: str) -> bool:
        """检查引擎是否在当前模式下可用"""
        return engine in self.get_allowed_engines()


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

    parser = argparse.ArgumentParser(description="隐私模式管理")
    parser.add_argument("action", choices=["mode", "status", "report"], help="操作")
    parser.add_argument("--set", choices=["normal", "strict"], help="设置模式")
    parser.add_argument("--config", help="配置文件路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)
    manager = PrivacyManager(config)

    if args.action == "mode":
        if args.set:
            success = manager.set_mode(args.set)
            if not success:
                sys.exit(1)
        else:
            mode = manager.get_mode()
            print(f"当前模式: {mode}")
            print(f"可用引擎: {', '.join(manager.get_allowed_engines())}")
            print(f"被屏蔽引擎: {', '.join(manager.get_blocked_engines())}")

    elif args.action == "status":
        if args.json:
            output = {
                "mode": manager.get_mode(),
                "allowed_engines": manager.get_allowed_engines(),
                "blocked_engines": manager.get_blocked_engines(),
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"模式: {manager.get_mode()}")
            print(f"可用引擎: {', '.join(manager.get_allowed_engines())}")
            print(f"被屏蔽引擎: {', '.join(manager.get_blocked_engines())}")

    elif args.action == "report":
        report = manager.generate_report()
        if args.json:
            output = {
                "mode": report.mode,
                "blocked_engines": report.blocked_engines,
                "http_headers_cleaned": report.http_headers_cleaned,
                "timestamp": report.timestamp.isoformat(),
                "recommendations": report.recommendations,
            }
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"\n🔒 隐私保护报告 ({report.timestamp.strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"   模式: {report.mode}")
            print(f"   被屏蔽引擎: {', '.join(report.blocked_engines)}")
            print(f"   清理的 HTTP 头: {', '.join(report.http_headers_cleaned)}")
            print(f"\n   建议:")
            for rec in report.recommendations:
                print(f"   • {rec}")


if __name__ == "__main__":
    import sys
    main()
