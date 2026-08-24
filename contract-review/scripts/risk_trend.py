#!/usr/bin/env python3
"""
risk_trend.py v5.2
风险趋势对比分析引擎
功能：多合同聚合视图、风险类型频次按月分布、红级条款占比变化、同一对方历史风险复发标记
v5.2 新增：风险趋势对比
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === 路径 ===
DATA_DIR = Path.home() / '.contract-review' / 'trend_data'
REVIEW_HISTORY_FILE = DATA_DIR / 'review_history.json'

# === 严重等级归一化 ===
SEVERITY_LEVELS = {
    'critical': '严重', 'high': '严重', '严重': '严重',
    'medium': '中等', '中等': '中等',
    'low': '低', '一般': '中等', '提示': '低', '低': '低',
}

# 红级（高风险）等级
RED_LEVELS = {'严重', '高', 'critical', 'high'}


class RiskTrendAnalyzer:
    """
    风险趋势分析器
    
    输入：历史审查记录列表
    输出：多维度趋势分析结果
    """

    def __init__(self, history_file: Optional[Path] = None):
        self.history_file = history_file or REVIEW_HISTORY_FILE
        self._history: List[Dict[str, Any]] = []
        self._loaded = False

    # ================================================================
    # 数据加载
    # ================================================================

    def _load_history(self):
        """加载历史审查记录"""
        if self._loaded:
            return
        if not self.history_file.exists():
            self._history = []
            self._loaded = True
            return
        try:
            with open(self.history_file, encoding='utf-8') as f:
                self._history = json.load(f)
            self._loaded = True
        except Exception as e:
            logger.warning(f"加载历史记录失败: {e}")
            self._history = []
            self._loaded = True

    def add_review_record(self, record: Dict[str, Any]):
        """
        添加一条审查记录
        
        Args:
            record: {
                "review_id": "唯一标识",
                "date": "YYYY-MM-DD",
                "contract_type": "合同类型",
                "counterparty": "对方主体",
                "contract_no": "合同编号",
                "risks": [
                    {
                        "risk_type": "风险类型",
                        "severity": "严重/中等/低",
                        "title": "风险标题",
                        ...
                    }
                ]
            }
        """
        self._load_history()
        self._history.append(record)
        self._save_history()

    def _save_history(self):
        """保存历史记录"""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存历史记录失败: {e}")

    # ================================================================
    # 核心分析接口
    # ================================================================

    def analyze(self, months: int = 12, counterparty: Optional[str] = None) -> Dict[str, Any]:
        """
        执行全面风险趋势分析
        
        Args:
            months: 分析时间范围（月）
            counterparty: 筛选特定对方主体（None 为全部）
        
        Returns:
            趋势分析结果
        """
        self._load_history()
        
        # 过滤时间范围
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        filtered = []
        for r in self._history:
            try:
                review_date = datetime.strptime(r.get('date', ''), "%Y-%m-%d")
                if review_date >= cutoff_date:
                    if counterparty is None or counterparty in r.get('counterparty', ''):
                        filtered.append(r)
            except (ValueError, TypeError):
                continue
        
        if not filtered:
            return {
                "status": "no_data",
                "message": f"近 {months} 个月内无审查记录",
                "months": months,
                "total_reviews": 0,
            }
        
        # 执行各维度分析
        result = {
            "status": "ok",
            "months": months,
            "total_reviews": len(filtered),
            "counterparty_filter": counterparty,
            "date_range": {
                "start": filtered[-1].get('date', ''),
                "end": filtered[0].get('date', ''),
            },
            "risk_type_distribution": self._risk_type_distribution(filtered),
            "monthly_trend": self._monthly_trend(filtered, months),
            "red_level_ratio": self._red_level_ratio(filtered),
            "counterparty_risk": self._counterparty_risk(filtered),
            "recurring_risks": self._recurring_risks(filtered),
            "summary": {},
        }
        
        # 生成摘要
        result["summary"] = self._generate_summary(result)
        
        return result

    def _risk_type_distribution(self, records: List[Dict]) -> Dict[str, int]:
        """风险类型频次分布"""
        distribution = defaultdict(int)
        for record in records:
            for risk in record.get('risks', []):
                risk_type = risk.get('risk_type', '未知')
                distribution[risk_type] += 1
        # 按频次降序
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))

    def _monthly_trend(self, records: List[Dict], months: int) -> Dict[str, Dict[str, int]]:
        """
        按月风险趋势
        
        Returns:
            { "YYYY-MM": { "risk_type": count, ... }, ... }
        """
        monthly: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for record in records:
            date_str = record.get('date', '')
            if not date_str:
                continue
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                month_key = dt.strftime("%Y-%m")
                for risk in record.get('risks', []):
                    risk_type = risk.get('risk_type', '未知')
                    monthly[month_key][risk_type] += 1
            except (ValueError, TypeError):
                continue
        
        # 转换为普通 dict
        return {k: dict(v) for k, v in sorted(monthly.items())}

    def _red_level_ratio(self, records: List[Dict]) -> Dict[str, Any]:
        """
        红级（高风险）条款占比分析
        """
        total_risks = 0
        red_risks = 0
        monthly_ratio: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "red": 0})
        
        for record in records:
            date_str = record.get('date', '')
            month_key = date_str[:7] if len(date_str) >= 7 else "未知"
            
            for risk in record.get('risks', []):
                total_risks += 1
                monthly_ratio[month_key]["total"] += 1
                
                severity = risk.get('severity', '')
                level = SEVERITY_LEVELS.get(severity.lower() if isinstance(severity, str) else '', '')
                if level in RED_LEVELS or severity in RED_LEVELS:
                    red_risks += 1
                    monthly_ratio[month_key]["red"] += 1
        
        overall_ratio = round(red_risks / total_risks, 4) if total_risks > 0 else 0
        
        # 计算月度红级占比
        monthly_pct = {}
        for month, data in sorted(monthly_ratio.items()):
            pct = round(data["red"] / data["total"], 4) if data["total"] > 0 else 0
            monthly_pct[month] = {
                "total": data["total"],
                "red": data["red"],
                "ratio": pct,
            }
        
        return {
            "overall_ratio": overall_ratio,
            "total_risks": total_risks,
            "red_risks": red_risks,
            "monthly": monthly_pct,
        }

    def _counterparty_risk(self, records: List[Dict]) -> Dict[str, Dict[str, Any]]:
        """
        按对方主体聚合风险统计
        """
        cp_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "review_count": 0,
            "total_risks": 0,
            "red_risks": 0,
            "risk_types": defaultdict(int),
        })
        
        for record in records:
            cp = record.get('counterparty', '未知主体')
            cp_stats[cp]["review_count"] += 1
            
            for risk in record.get('risks', []):
                cp_stats[cp]["total_risks"] += 1
                risk_type = risk.get('risk_type', '未知')
                cp_stats[cp]["risk_types"][risk_type] += 1
                
                severity = risk.get('severity', '')
                level = SEVERITY_LEVELS.get(severity.lower() if isinstance(severity, str) else '', '')
                if level in RED_LEVELS or severity in RED_LEVELS:
                    cp_stats[cp]["red_risks"] += 1
        
        # 转换格式
        result = {}
        for cp, stats in cp_stats.items():
            result[cp] = {
                "review_count": stats["review_count"],
                "total_risks": stats["total_risks"],
                "red_risks": stats["red_risks"],
                "red_ratio": round(stats["red_risks"] / stats["total_risks"], 4) if stats["total_risks"] > 0 else 0,
                "risk_types": dict(sorted(stats["risk_types"].items(), key=lambda x: x[1], reverse=True)),
            }
        
        return dict(sorted(result.items(), key=lambda x: x[1]["total_risks"], reverse=True))

    def _recurring_risks(self, records: List[Dict]) -> List[Dict[str, Any]]:
        """
        识别同一对方主体的历史风险复发
        
        复发定义：同一对方主体出现 2 次及以上的相同风险类型
        """
        # 按对方主体分组
        cp_risks: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        
        for record in records:
            cp = record.get('counterparty', '未知主体')
            for risk in record.get('risks', []):
                risk_type = risk.get('risk_type', '未知')
                title = risk.get('title', '')
                cp_risks[cp][risk_type].append(title)
        
        recurring = []
        for cp, risks in cp_risks.items():
            for risk_type, titles in risks.items():
                if len(titles) >= 2:
                    recurring.append({
                        "counterparty": cp,
                        "risk_type": risk_type,
                        "occurrences": len(titles),
                        "titles": titles[:5],  # 最多保留 5 个示例
                    })
        
        # 按复发次数降序
        recurring.sort(key=lambda x: x["occurrences"], reverse=True)
        return recurring

    def _generate_summary(self, result: Dict[str, Any]) -> Dict[str, str]:
        """生成文字摘要"""
        summary = {}
        
        total = result["total_reviews"]
        summary["total_reviews"] = f"共分析 {total} 份合同审查记录"
        
        # 红级占比
        red_ratio = result["red_level_ratio"]
        summary["red_level"] = (
            f"红级（高风险）条款占比 {red_ratio['overall_ratio']*100:.1f}%"
            f"（{red_ratio['red_risks']}/{red_ratio['total_risks']}）"
        )
        
        # 最高频风险类型
        dist = result["risk_type_distribution"]
        if dist:
            top_type = list(dist.keys())[0]
            summary["top_risk_type"] = f"最高频风险类型：{top_type}（{dist[top_type]} 次）"
        
        # 复发风险
        recurring = result["recurring_risks"]
        if recurring:
            summary["recurring"] = f"发现 {len(recurring)} 个复发风险（同一对方重复出现）"
        else:
            summary["recurring"] = "未发现复发风险"
        
        return summary

    # ================================================================
    # 输出格式化
    # ================================================================

    def format_report(self, result: Dict[str, Any]) -> str:
        """
        格式化趋势分析报告为可读文本
        """
        if result.get("status") == "no_data":
            return f"⚠️ {result['message']}"
        
        lines = []
        lines.append("=" * 60)
        lines.append("风险趋势对比分析报告")
        lines.append("=" * 60)
        
        # 基本信息
        lines.append(f"\n📊 分析范围：近 {result['months']} 个月")
        lines.append(f"📄 审查合同数：{result['total_reviews']}")
        if result.get("counterparty_filter"):
            lines.append(f"🏢 对方主体筛选：{result['counterparty_filter']}")
        
        # 摘要
        lines.append("\n" + "-" * 40)
        lines.append("【摘要】")
        for key, value in result["summary"].items():
            lines.append(f"  • {value}")
        
        # 红级占比
        red = result["red_level_ratio"]
        lines.append("\n" + "-" * 40)
        lines.append("【红级条款占比】")
        lines.append(f"  总体占比：{red['overall_ratio']*100:.1f}%")
        if red["monthly"]:
            lines.append("  月度变化：")
            for month, data in red["monthly"].items():
                lines.append(f"    {month}: {data['ratio']*100:.1f}% ({data['red']}/{data['total']})")
        
        # 风险类型分布
        dist = result["risk_type_distribution"]
        if dist:
            lines.append("\n" + "-" * 40)
            lines.append("【风险类型分布（Top 10）】")
            for i, (risk_type, count) in enumerate(list(dist.items())[:10]):
                lines.append(f"  {i+1}. {risk_type}: {count} 次")
        
        # 复发风险
        recurring = result["recurring_risks"]
        if recurring:
            lines.append("\n" + "-" * 40)
            lines.append("【复发风险标记】")
            for r in recurring[:10]:
                lines.append(f"  ⚠️ [{r['counterparty']}] {r['risk_type']} — 出现 {r['occurrences']} 次")
        
        # 对方主体风险
        cp_risk = result["counterparty_risk"]
        if cp_risk:
            lines.append("\n" + "-" * 40)
            lines.append("【对方主体风险排名（Top 5）】")
            for i, (cp, stats) in enumerate(list(cp_risk.items())[:5]):
                lines.append(f"  {i+1}. {cp}: {stats['total_risks']} 个风险（红级 {stats['red_risks']} 个）")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    # ================================================================
    # 可视化（可选）
    # ================================================================

    def generate_chart(self, result: Dict[str, Any], output_path: Optional[Path] = None) -> Optional[str]:
        """
        生成趋势图表（需要 matplotlib）
        
        Returns:
            图表文件路径，或 None（无 matplotlib 时）
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # 无 GUI 后端
            import matplotlib.pyplot as plt
            from matplotlib import font_manager
        except ImportError:
            logger.warning("未安装 matplotlib，跳过图表生成")
            return None
        
        if result.get("status") == "no_data":
            return None
        
        # 设置中文字体
        try:
            # 尝试常见中文字体
            for font_name in ['SimHei', 'Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC']:
                try:
                    plt.rcParams['font.sans-serif'] = [font_name]
                    plt.rcParams['axes.unicode_minus'] = False
                    break
                except Exception:
                    continue
        except Exception:
            pass
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('风险趋势对比分析', fontsize=16)
        
        # 1. 月度风险总数趋势
        monthly = result.get("monthly_trend", {})
        if monthly:
            months = list(monthly.keys())
            totals = [sum(v.values()) for v in monthly.values()]
            axes[0, 0].plot(months, totals, marker='o', color='#e74c3c')
            axes[0, 0].set_title('月度风险总数趋势')
            axes[0, 0].set_xlabel('月份')
            axes[0, 0].set_ylabel('风险数')
            axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 红级占比月度变化
        red_monthly = result.get("red_level_ratio", {}).get("monthly", {})
        if red_monthly:
            months = list(red_monthly.keys())
            ratios = [v["ratio"] * 100 for v in red_monthly.values()]
            axes[0, 1].bar(months, ratios, color='#e67e22')
            axes[0, 1].set_title('红级条款占比月度变化（%）')
            axes[0, 1].set_xlabel('月份')
            axes[0, 1].set_ylabel('占比 %')
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. 风险类型分布 Top 10
        dist = result.get("risk_type_distribution", {})
        if dist:
            items = list(dist.items())[:10]
            types = [x[0] for x in items]
            counts = [x[1] for x in items]
            axes[1, 0].barh(types[::-1], counts[::-1], color='#3498db')
            axes[1, 0].set_title('风险类型分布 Top 10')
            axes[1, 0].set_xlabel('出现次数')
        
        # 4. 对方主体风险排名 Top 5
        cp_risk = result.get("counterparty_risk", {})
        if cp_risk:
            items = list(cp_risk.items())[:5]
            cps = [x[0] for x in items]
            red_counts = [x[1]["red_risks"] for x in items]
            total_counts = [x[1]["total_risks"] for x in items]
            x = range(len(cps))
            axes[1, 1].bar(x, total_counts, color='#95a5a6', label='总风险')
            axes[1, 1].bar(x, red_counts, color='#e74c3c', label='红级风险')
            axes[1, 1].set_xticks(x)
            axes[1, 1].set_xticklabels(cps, rotation=45, ha='right')
            axes[1, 1].set_title('对方主体风险排名 Top 5')
            axes[1, 1].legend()
        
        plt.tight_layout()
        
        # 保存
        if output_path is None:
            output_path = DATA_DIR / f"risk_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(output_path)


# ================================================================
# 便捷函数
# ================================================================

_default_analyzer: Optional[RiskTrendAnalyzer] = None


def get_analyzer() -> RiskTrendAnalyzer:
    """获取全局单例"""
    global _default_analyzer
    if _default_analyzer is None:
        _default_analyzer = RiskTrendAnalyzer()
    return _default_analyzer


def analyze_trends(months: int = 12, counterparty: Optional[str] = None) -> Dict[str, Any]:
    """便捷函数：分析风险趋势"""
    return get_analyzer().analyze(months, counterparty)


def format_trend_report(result: Dict[str, Any]) -> str:
    """便捷函数：格式化趋势报告"""
    return get_analyzer().format_report(result)


def add_review_record(record: Dict[str, Any]):
    """便捷函数：添加审查记录"""
    get_analyzer().add_review_record(record)


# ================================================================
# 命令行测试
# ================================================================

if __name__ == "__main__":
    analyzer = RiskTrendAnalyzer()
    
    # 添加测试数据
    test_records = [
        {
            "review_id": "R001",
            "date": "2026-01-15",
            "contract_type": "买卖合同",
            "counterparty": "上海某科技有限公司",
            "contract_no": "HT-2026-001",
            "risks": [
                {"risk_type": "违约责任风险", "severity": "严重", "title": "违约金约定过高"},
                {"risk_type": "付款风险", "severity": "中等", "title": "付款节点不明确"},
            ]
        },
        {
            "review_id": "R002",
            "date": "2026-02-20",
            "contract_type": "服务合同",
            "counterparty": "北京某咨询有限公司",
            "contract_no": "HT-2026-002",
            "risks": [
                {"risk_type": "履行风险", "severity": "严重", "title": "服务标准不明确"},
                {"risk_type": "保密风险", "severity": "中等", "title": "保密条款缺失"},
            ]
        },
        {
            "review_id": "R003",
            "date": "2026-03-10",
            "contract_type": "买卖合同",
            "counterparty": "上海某科技有限公司",
            "contract_no": "HT-2026-003",
            "risks": [
                {"risk_type": "违约责任风险", "severity": "严重", "title": "违约责任不对等"},
                {"risk_type": "质量风险", "severity": "中等", "title": "验收标准模糊"},
            ]
        },
    ]
    
    for record in test_records:
        analyzer.add_review_record(record)
    
    # 执行分析
    result = analyzer.analyze(months=6)
    
    # 输出报告
    print(analyzer.format_report(result))
    
    # 尝试生成图表
    chart_path = analyzer.generate_chart(result)
    if chart_path:
        print(f"\n📊 图表已保存: {chart_path}")
    else:
        print("\n⚠️ 未安装 matplotlib，跳过图表生成")
