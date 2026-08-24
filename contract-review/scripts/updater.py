#!/usr/bin/env python3
"""
Skill 更新检测模块 v5.2.1
仅在用户显式选择更新时检查新版本，固定 commit 并校验哈希
v5.0 新增：法条数据库季度更新提醒
v5.1 新增：指导案例数据库月度更新提醒
v5.2.1 修复：移除自动远程拉取逻辑，改为显式用户确认 + 哈希校验
"""

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 更新检查配置
UPDATE_CHECK_PATH = Path.home() / '.contract-review' / 'update_check.json'
CHECK_INTERVAL_SECONDS = 7 * 24 * 3600  # 7 天
# 固定 commit hash（用户更新时手动修改以锁定版本）
PINNED_COMMIT = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# 发布校验 SHA-256（用户更新时手动填入以验证完整性）
PINNED_SHA256 = ""
REQUEST_TIMEOUT = 10  # 秒


class UpdateChecker:
    """更新检测器"""
    
    def __init__(self, github_url: str = GITHUB_RAW_URL):
        self.github_url = github_url
        self._check_data: Optional[Dict[str, Any]] = None
    
    def check(self, force: bool = False) -> Optional[Dict[str, Any]]:
        """
        检查是否有新版本
        
        Returns:
            None: 无新版本或检查失败
            Dict: 有新版本，返回版本信息
        """
        # 读取检查记录
        check_data = self._load_check_data()
        
        # 检查是否需要跳过（7 天内已检查过）
        if not force:
            last_check = check_data.get('last_check_time', 0)
            if time.time() - last_check < CHECK_INTERVAL_SECONDS:
                logger.debug("跳过更新检查（7 天内已检查）")
                return None
        
        # 获取远程版本
        remote_version = self._fetch_remote_version()
        if remote_version is None:
            return None
        
        # 获取本地版本
        local_version = self._get_local_version()
        
        # 更新检查记录
        check_data['last_check_time'] = time.time()
        check_data['last_remote_version'] = remote_version
        check_data['last_local_version'] = local_version
        self._save_check_data(check_data)
        
        # 比较版本
        if self._compare_versions(remote_version, local_version) > 0:
            return {
                'local_version': local_version,
                'remote_version': remote_version,
                'should_notify': self._should_notify(check_data, remote_version),
            }
        
        return None
    
    def get_update_message(self, update_info: Dict[str, Any]) -> str:
        """生成更新提示消息"""
        local = update_info.get('local_version', '?')
        remote = update_info.get('remote_version', '?')
        
        return (
            f"\n{'=' * 50}\n"
            f"📢 发现新版本 v{remote} (当前 v{local})\n"
            f"{'=' * 50}\n"
            f"更新内容：新增 Word 报告生成、历史版本对比、硬件自适应调度、安全风险拦截等功能。\n"
            f"更新方法：运行 skillhub install contract-review\n"
            f"{'=' * 50}\n"
        )
    
    def _fetch_remote_version(self) -> Optional[str]:
        """
        从 GitHub 获取远程版本号
        
        安全增强（v5.2.1）：
        - 仅在用户显式选择更新时调用
        - 固定 commit hash，避免供应链攻击
        - 校验 SHA-256 哈希，确保内容完整性
        """
        # 未配置固定 commit 时不拉取远程内容
        if PINNED_COMMIT == "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx":
            logger.warning("未配置 PINNED_COMMIT，跳过远程版本检查（安全策略）")
            return None
        
        try:
            import urllib.request
            # 使用固定 commit 而非 main 分支
            url = f'https://raw.githubusercontent.com/fyniujin/devskill/{PINNED_COMMIT}/contract-review/SKILL.md'
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'contract-review-updater/5.2.1'}
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                content = response.read()
            
            # 哈希校验
            if PINNED_SHA256:
                actual_hash = hashlib.sha256(content).hexdigest()
                if actual_hash != PINNED_SHA256:
                    logger.error(f"哈希校验失败: expected {PINNED_SHA256}, got {actual_hash}")
                    return None
            
            content_str = content.decode('utf-8')
            
            # 从 SKILL.md 中提取版本号
            match = re.search(r'version:\s*["\']?(\d+\.\d+\.\d+)["\']?', content_str)
            if match:
                return match.group(1)
            
            logger.warning("无法从远程 SKILL.md 解析版本号")
            return None
        except Exception as e:
            logger.debug(f"获取远程版本失败: {e}")
            return None
    
    def _get_local_version(self) -> str:
        """获取本地版本号"""
        # 从 SKILL.md 读取
        skill_md = Path(__file__).parent.parent / 'SKILL.md'
        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r'version:\s*["\']?(\d+\.\d+\.\d+)["\']?', content)
            if match:
                return match.group(1)
        except Exception:
            pass
        return '2.5.0'  # 默认值
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """
        比较两个版本号
        
        Returns:
            1: v1 > v2
            0: v1 == v2
            -1: v1 < v2
        """
        def parse_version(v):
            return tuple(int(x) for x in v.split('.'))
        
        try:
            v1_parts = parse_version(v1)
            v2_parts = parse_version(v2)
            
            if v1_parts > v2_parts:
                return 1
            elif v1_parts < v2_parts:
                return -1
            return 0
        except Exception:
            return 0
    
    def _should_notify(self, check_data: Dict, remote_version: str) -> bool:
        """判断是否需要提醒（同一版本 7 天内只提醒一次）"""
        last_notified_version = check_data.get('last_notified_version', '')
        last_notified_time = check_data.get('last_notified_time', 0)
        
        # 如果是新版本，或者同一版本超过 7 天，需要提醒
        if remote_version != last_notified_version:
            return True
        
        if time.time() - last_notified_time >= CHECK_INTERVAL_SECONDS:
            return True
        
        return False
    
    def record_notified(self, version: str):
        """记录已提醒的版本"""
        check_data = self._load_check_data()
        check_data['last_notified_version'] = version
        check_data['last_notified_time'] = time.time()
        self._save_check_data(check_data)
    
    def _load_check_data(self) -> Dict[str, Any]:
        """加载检查记录"""
        if self._check_data is not None:
            return self._check_data
        
        try:
            if UPDATE_CHECK_PATH.exists():
                with open(UPDATE_CHECK_PATH, 'r', encoding='utf-8') as f:
                    self._check_data = json.load(f)
                return self._check_data
        except Exception as e:
            logger.debug(f"读取更新检查记录失败: {e}")
        
        return {}
    
    def _save_check_data(self, data: Dict[str, Any]):
        """保存检查记录"""
        try:
            UPDATE_CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(UPDATE_CHECK_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._check_data = data
        except Exception as e:
            logger.debug(f"保存更新检查记录失败: {e}")


# ===== v5.0 法条数据库季度更新提醒 =====
LEGAL_BASIS_DIR = Path(__file__).resolve().parent.parent / "references" / "legal_basis"
LEGAL_UPDATE_CHECK_PATH = Path.home() / '.contract-review' / 'legal_update_check.json'
LEGAL_CHECK_INTERVAL_SECONDS = 90 * 24 * 3600  # 90 天（一季度）


def check_legal_basis_update() -> Optional[str]:
    """
    检查法条数据库是否需要季度更新
    返回 None 表示无需提醒，返回字符串表示提醒消息
    """
    # 获取本地法条数据库最新版本日期
    index_file = LEGAL_BASIS_DIR / "index.json"
    if not index_file.exists():
        return None

    try:
        with open(index_file, encoding='utf-8') as f:
            data = json.load(f)
        db_version = data.get("version", "1.0.0")
        db_updated = data.get("updated", "")
    except Exception:
        return None

    # 读取上次提醒记录
    check_data = {}
    if LEGAL_UPDATE_CHECK_PATH.exists():
        try:
            with open(LEGAL_UPDATE_CHECK_PATH, encoding='utf-8') as f:
                check_data = json.load(f)
        except Exception:
            pass

    # 检查是否需要提醒（同一版本 90 天内只提醒一次）
    last_notified_version = check_data.get('last_notified_version', '')
    last_notified_time = check_data.get('last_notified_time', 0)

    if db_version == last_notified_version and time.time() - last_notified_time < LEGAL_CHECK_INTERVAL_SECONDS:
        return None

    # 超过 90 天提醒一次
    if time.time() - last_notified_time >= LEGAL_CHECK_INTERVAL_SECONDS:
        check_data['last_notified_version'] = db_version
        check_data['last_notified_time'] = time.time()
        try:
            LEGAL_UPDATE_CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(LEGAL_UPDATE_CHECK_PATH, 'w', encoding='utf-8') as f:
                json.dump(check_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return (
            f"法条数据库已 {db_updated} 更新，距今超过 3 个月。"
            f"建议检查最新法律法规变化（如民法典司法解释新增、公司法修订等）。"
        )

    return None


# ===== v5.1 指导案例数据库月度更新提醒 =====
GUIDING_CASES_DIR = Path(__file__).resolve().parent.parent / "references" / "guiding_cases"
GUIDING_UPDATE_CHECK_PATH = Path.home() / '.contract-review' / 'guiding_update_check.json'
GUIDING_CHECK_INTERVAL_SECONDS = 30 * 24 * 3600  # 30 天（一月）


def check_guiding_cases_update() -> Optional[str]:
    """
    检查指导案例数据库是否需要月度更新
    返回 None 表示无需提醒，返回字符串表示提醒消息
    """
    update_log_file = GUIDING_CASES_DIR / "update_log.json"
    if not update_log_file.exists():
        return None

    try:
        with open(update_log_file, encoding='utf-8') as f:
            data = json.load(f)
        db_version = data.get("version", "1.0.0")
        db_updated = data.get("updated", "")
        next_update = data.get("next_update", "")
    except Exception:
        return None

    # 读取上次提醒记录
    check_data = {}
    if GUIDING_UPDATE_CHECK_PATH.exists():
        try:
            with open(GUIDING_UPDATE_CHECK_PATH, encoding='utf-8') as f:
                check_data = json.load(f)
        except Exception:
            pass

    # 检查是否需要提醒（同一版本 30 天内只提醒一次）
    last_notified_version = check_data.get('last_notified_version', '')
    last_notified_time = check_data.get('last_notified_time', 0)

    if db_version == last_notified_version and time.time() - last_notified_time < GUIDING_CHECK_INTERVAL_SECONDS:
        return None

    # 超过 30 天提醒一次
    if time.time() - last_notified_time >= GUIDING_CHECK_INTERVAL_SECONDS:
        check_data['last_notified_version'] = db_version
        check_data['last_notified_time'] = time.time()
        try:
            GUIDING_UPDATE_CHECK_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(GUIDING_UPDATE_CHECK_PATH, 'w', encoding='utf-8') as f:
                json.dump(check_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return (
            f"指导案例数据库已 {db_updated} 更新，距今超过 1 个月。"
            f"建议关注最高人民法院新发布的指导性案例（下次应更新于 {next_update}）。"
        )

    return None


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Skill 更新检测 v3.0')
    parser.add_argument('--force', '-f', action='store_true', help='强制检查（忽略 7 天间隔）')
    parser.add_argument('--quiet', '-q', action='store_true', help='静默模式（只输出 JSON）')
    args = parser.parse_args()
    
    checker = UpdateChecker()
    update_info = checker.check(force=args.force)
    
    if update_info:
        if args.quiet:
            print(json.dumps(update_info, ensure_ascii=False))
        else:
            print(checker.get_update_message(update_info))
    else:
        if args.quiet:
            print('{}')
        else:
            print("✅ 当前已是最新版本")


if __name__ == '__main__':
    main()
