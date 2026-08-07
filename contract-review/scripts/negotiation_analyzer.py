#!/usr/bin/env python3
"""
negotiation_analyzer.py v5.0
合同谈判辅助引擎
功能：多轮修改差异分析、必争/可让步条款识别、谈判准备文档生成
v5.0 新增：合同谈判辅助
"""

import hashlib
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === 路径 ===
STRATEGY_FILE = Path(__file__).resolve().parent.parent / "references" / "negotiation_strategies.yaml"


class NegotiationAnalyzer:
    """谈判分析引擎 — 多轮版本对比 + 策略建议"""

    def __init__(self, strategy_file: Optional[Path] = None):
        self.strategy_file = strategy_file or STRATEGY_FILE
        self._strategies: List[Dict[str, Any]] = []
        self._load_strategies()

    # ---------- 加载 ----------
    def _load_strategies(self):
        if not self.strategy_file.exists():
            logger.warning(f"谈判策略文件不存在: {self.strategy_file}")
            return
        try:
            import yaml
            with open(self.strategy_file, encoding='utf-8') as f:
                data = yaml.safe_load(f)
            self._strategies = data.get("strategies", [])
            logger.debug(f"谈判策略加载成功，共 {len(self._strategies)} 条")
        except ImportError:
            logger.warning("未安装 pyyaml，无法读取谈判策略")
        except Exception as e:
            logger.warning(f"谈判策略加载失败: {e}")

    # ---------- 多轮差异分析 ----------
    def analyze_versions(
        self,
        versions: List[Dict[str, Any]],
        role: str = "乙方",
    ) -> Dict[str, Any]:
        """
        分析多轮版本差异
        :param versions: 按时间顺序排列的版本列表（从旧到新），每个版本包含 {'content': ..., 'timestamp': ..., 'party': ...}
        :param role: 当前用户角色（甲方/乙方）
        :return: 谈判分析结果
        """
        if len(versions) < 2:
            return {
                "status": "insufficient_data",
                "message": "至少需要两个版本才能分析谈判模式",
                "versions_count": len(versions),
            }

        # 逐对比较
        all_diffs = []
        for i in range(len(versions) - 1):
            diff = self._diff_two(versions[i], versions[i + 1])
            diff["round"] = i + 1
            diff["from_version"] = versions[i].get("timestamp", f"v{i}")
            diff["to_version"] = versions[i + 1].get("timestamp", f"v{i+1}")
            all_diffs.append(diff)

        # 识别必争/可让步条款
        clause_changes = self._track_clause_changes(all_diffs)
        hold_firm = []   # 必争条款
        flexible = []    # 可让步条款

        for clause_id, info in clause_changes.items():
            if info["change_count"] == 0 and info["always_present"]:
                # 从未改变且始终存在 → 对方必争
                hold_firm.append(info)
            elif info["change_count"] >= 2 and info["direction"] == "concession":
                # 多次退让 → 可让步条款
                flexible.append(info)
            elif info["change_count"] >= 2 and info["direction"] == "insist":
                # 多次坚持 → 必争
                hold_firm.append(info)

        # 生成策略建议
        strategy = self._generate_strategy(hold_firm, flexible, role)

        return {
            "status": "ok",
            "versions_count": len(versions),
            "total_rounds": len(all_diffs),
            "hold_firm_clauses": hold_firm,
            "flexible_clauses": flexible,
            "all_clause_changes": clause_changes,
            "strategy": strategy,
            "generated_at": datetime.now().isoformat(),
        }

    def _diff_two(self, v1: Dict[str, Any], v2: Dict[str, Any]) -> Dict[str, Any]:
        """比较两个版本的差异"""
        text1 = v1.get("content", "")
        text2 = v2.get("content", "")

        # 简单行级 diff
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()

        added = []
        removed = []
        modified = []

        # 使用简单的集合差
        set1 = set(lines1)
        set2 = set(lines2)

        for line in lines2:
            if line not in set1 and line.strip():
                added.append(line)
        for line in lines1:
            if line not in set2 and line.strip():
                removed.append(line)

        return {
            "added": added[:20],
            "removed": removed[:20],
            "modified": modified,
            "added_count": len(added),
            "removed_count": len(removed),
            "party": v2.get("party", "unknown"),
        }

    def _track_clause_changes(self, diffs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """追踪每个条款的变化情况"""
        clause_info: Dict[str, Dict[str, Any]] = {}

        for diff in diffs:
            party = diff.get("party", "unknown")
            for line in diff.get("added", []):
                clause_id = self._extract_clause_id(line)
                if clause_id not in clause_info:
                    clause_info[clause_id] = {
                        "clause_id": clause_id,
                        "title": clause_id,
                        "change_count": 0,
                        "always_present": True,
                        "direction": "unknown",
                        "changes": [],
                    }
                clause_info[clause_id]["change_count"] += 1
                clause_info[clause_id]["changes"].append({
                    "type": "added",
                    "content": line[:100],
                    "party": party,
                })

            for line in diff.get("removed", []):
                clause_id = self._extract_clause_id(line)
                if clause_id not in clause_info:
                    clause_info[clause_id] = {
                        "clause_id": clause_id,
                        "title": clause_id,
                        "change_count": 0,
                        "always_present": True,
                        "direction": "unknown",
                        "changes": [],
                    }
                clause_info[clause_id]["change_count"] += 1
                clause_info[clause_id]["changes"].append({
                    "type": "removed",
                    "content": line[:100],
                    "party": party,
                })

        # 判断方向
        for clause_id, info in clause_info.items():
            changes = info["changes"]
            if len(changes) >= 2:
                # 检查是否逐步退让（内容越来越短或条件越来越宽松）
                lengths = [len(c.get("content", "")) for c in changes]
                if all(lengths[i] >= lengths[i+1] for i in range(len(lengths)-1)):
                    info["direction"] = "concession"
                elif all(lengths[i] <= lengths[i+1] for i in range(len(lengths)-1)):
                    info["direction"] = "insist"
                else:
                    info["direction"] = "mixed"

        return clause_info

    def _extract_clause_id(self, line: str) -> str:
        """从行中提取条款标识"""
        # 匹配"第X条"、"第X款"、"X."等格式
        import re
        m = re.search(r'第[一二三四五六七八九十\d]+条', line)
        if m:
            return m.group(0)
        m = re.search(r'^\d+[\.、]', line)
        if m:
            return m.group(0)
        # 返回前 20 字作为标识
        return line[:20].strip() or "未知条款"

    # ---------- 策略生成 ----------
    def _generate_strategy(
        self,
        hold_firm: List[Dict[str, Any]],
        flexible: List[Dict[str, Any]],
        role: str,
    ) -> Dict[str, Any]:
        """生成谈判策略建议"""
        strategy = {
            "role": role,
            "summary": "",
            "hold_firm": [],
            "can_concede": [],
            "suggestions": [],
        }

        # 必争条款建议
        for clause in hold_firm:
            matched = self._match_strategy(clause["title"])
            if matched:
                strategy["hold_firm"].append({
                    "clause": clause["title"],
                    "reason": matched.get("hold_reason", ""),
                    "fallback": matched.get("fallback_options", []),
                })
            else:
                strategy["hold_firm"].append({
                    "clause": clause["title"],
                    "reason": "对方始终坚持，可能涉及核心利益",
                    "fallback": [],
                })

        # 可让步条款建议
        for clause in flexible:
            matched = self._match_strategy(clause["title"])
            if matched:
                strategy["can_concede"].append({
                    "clause": clause["title"],
                    "reason": f"对方已退让 {clause['change_count']} 次",
                    "reasonable_range": matched.get("reasonable_range", ""),
                    "red_line": matched.get("red_line", ""),
                })
            else:
                strategy["can_concede"].append({
                    "clause": clause["title"],
                    "reason": f"对方已退让 {clause['change_count']} 次",
                    "reasonable_range": "",
                    "red_line": "",
                })

        # 综合建议
        if hold_firm:
            strategy["suggestions"].append(
                f"对方有 {len(hold_firm)} 个必争条款，建议不要轻易挑战"
            )
        if flexible:
            strategy["suggestions"].append(
                f"对方有 {len(flexible)} 个可让步条款，可作为谈判筹码"
            )
        strategy["suggestions"].append("让步要交换，不要单方面让步")
        strategy["suggestions"].append("所有口头承诺必须落实到书面")

        strategy["summary"] = (
            f"共分析 {len(hold_firm) + len(flexible)} 个条款，"
            f"其中 {len(hold_firm)} 个对方必争，{len(flexible)} 个可让步"
        )

        return strategy

    def _match_strategy(self, clause_title: str) -> Optional[Dict[str, Any]]:
        """匹配谈判策略"""
        for s in self._strategies:
            if s.get("clause") in clause_title or clause_title in s.get("clause", ""):
                return s
            if s.get("category") in clause_title or clause_title in s.get("category", ""):
                return s
        return None

    # ---------- 谈判文档生成 ----------
    def generate_negotiation_doc(
        self,
        analysis: Dict[str, Any],
        contract_info: Dict[str, Any],
        output_path: Optional[str] = None,
    ) -> str:
        """生成谈判准备文档"""
        strategy = analysis.get("strategy", {})
        lines = []

        # 标题
        title = contract_info.get("title", "合同谈判准备文档")
        lines.append(f"# {title} — 谈判准备文档")
        lines.append(f"\n生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"角色：{strategy.get('role', '未指定')}")
        lines.append("")

        # 摘要
        lines.append("## 谈判摘要")
        lines.append(f"\n{strategy.get('summary', '')}")
        lines.append("")

        # 必争条款
        lines.append("## 必须守住的条款（对方必争）")
        for item in strategy.get("hold_firm", []):
            lines.append(f"\n### {item.get('clause', '')}")
            lines.append(f"- 原因：{item.get('reason', '')}")
            for fb in item.get("fallback", []):
                lines.append(f"- 替代方案：{fb}")
        lines.append("")

        # 可让步条款
        lines.append("## 可以适当让步的条款")
        for item in strategy.get("can_concede", []):
            lines.append(f"\n### {item.get('clause', '')}")
            lines.append(f"- 原因：{item.get('reason', '')}")
            if item.get("reasonable_range"):
                lines.append(f"- 合理范围：{item['reasonable_range']}")
            if item.get("red_line"):
                lines.append(f"- 红线：{item['red_line']}")
        lines.append("")

        # 综合建议
        lines.append("## 综合建议")
        for s in strategy.get("suggestions", []):
            lines.append(f"- {s}")
        lines.append("")

        # 通用提示
        lines.append("## 通用谈判原则")
        lines.append("- 谈判前明确己方的核心利益和底线条款")
        lines.append("- 区分'必须守住'和'可以交换'的条款")
        lines.append("- 不要轻易放弃付款条件，现金流是企业的命脉")
        lines.append("- 知识产权归属是长期战略资产，尽量争取全部或独占")
        lines.append("- 让步要交换，不要单方面让步")
        lines.append("- 所有口头承诺必须落实到书面")
        lines.append("- 重大合同建议律师参与谈判")
        lines.append("")

        content = "\n".join(lines)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"谈判文档已保存: {output_path}")

        return content

    # ---------- 便捷分析 ----------
    def quick_analyze(
        self,
        old_text: str,
        new_text: str,
        role: str = "乙方",
    ) -> Dict[str, Any]:
        """快速分析两个版本的差异"""
        versions = [
            {"content": old_text, "timestamp": "v1", "party": "对方"},
            {"content": new_text, "timestamp": "v2", "party": "我方"},
        ]
        return self.analyze_versions(versions, role)


# ---------- 便捷函数 ----------
_default_analyzer: Optional[NegotiationAnalyzer] = None


def get_analyzer() -> NegotiationAnalyzer:
    """获取全局单例"""
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = NegotiationAnalyzer()
    return _default_analyzer


def analyze_versions(versions: List[Dict[str, Any]], role: str = "乙方") -> Dict[str, Any]:
    """便捷函数：分析多轮版本"""
    return get_analyzer().analyze_versions(versions, role)


def generate_negotiation_doc(
    analysis: Dict[str, Any],
    contract_info: Dict[str, Any],
    output_path: Optional[str] = None,
) -> str:
    """便捷函数：生成谈判文档"""
    return get_analyzer().generate_negotiation_doc(analysis, contract_info, output_path)


if __name__ == "__main__":
    # 简单测试
    analyzer = NegotiationAnalyzer()
    print(f"谈判策略加载: {len(analyzer._strategies)} 条")

    # 测试快速分析
    old = """
第8条 违约金：违约金为合同金额的 50%。
第9条 付款：合同签订后一次性付清。
第10条 知识产权：知识产权归甲方所有。
"""
    new = """
第8条 违约金：违约金为合同金额的 20%。
第9条 付款：合同签订后一次性付清。
第10条 知识产权：知识产权归甲方所有。
"""
    result = analyzer.quick_analyze(old, new, role="乙方")
    print(f"\n分析状态: {result['status']}")
    print(f"必争条款: {len(result['hold_firm_clauses'])}")
    print(f"可让步条款: {len(result['flexible_clauses'])}")
    print(f"策略摘要: {result['strategy']['summary']}")
