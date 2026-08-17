#!/usr/bin/env python3
"""
case_retriever.py v5.1
最高法指导案例检索引擎
功能：指导案例数据库检索、风险点自动匹配案例、案例全文展开、月度更新提醒
v5.1 新增：指导案例数据库（每月增量同步）
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === 路径 ===
GUIDING_CASES_DIR = Path(__file__).resolve().parent.parent / "references" / "guiding_cases"
CASES_FILE = GUIDING_CASES_DIR / "cases.json"
INDEX_FILE = GUIDING_CASES_DIR / "index.json"
UPDATE_LOG_FILE = GUIDING_CASES_DIR / "update_log.json"

# === 风险类型关键词 → 案例标签映射 ===
RISK_TO_CASE_TAGS = {
    "违约": ["违约", "跳单", "失信"],
    "欺诈": ["欺诈", "恶意侵权"],
    "质量": ["质量", "食品安全"],
    "食品安全": ["食品安全"],
    "不正当竞争": ["不正当竞争", "垄断"],
    "知识产权": ["专利侵权", "商标抢注", "源代码"],
    "专利": ["专利侵权"],
    "商标": ["商标抢注"],
    "技术": ["源代码"],
    "保密": ["个人信息", "安全保障"],
    "个人信息": ["个人信息", "安全保障"],
    "数据安全": ["个人信息", "安全保障"],
    "优先受偿": ["优先受偿"],
    "工程": ["工程结算", "工程款优先", "黑白合同"],
    "招投标": ["黑白合同", "招投标"],
    "破产": ["破产重整", "执行不能", "偏颇清偿", "破产撤销"],
    "保险": ["保险代位", "不利解释", "多因一果"],
    "格式条款": ["格式条款", "不利解释"],
    "阴阳合同": ["阴阳合同"],
    "违约方": ["违约方解除", "情势变更"],
    "情势变更": ["情势变更", "违约方解除"],
    "合同无效": ["背俗无效", "公序良俗"],
    "公序良俗": ["公序良俗"],
    "生态环境": ["生态修复"],
    "环境": ["生态修复"],
    "劳动": ["竞业限制", "经济补偿", "违法解除"],
    "竞业": ["竞业限制"],
    "股权": ["优先购买权", "股权转让"],
    "公司": ["法人人格否认", "关联公司", "公司解散", "公司僵局"],
    "股东": ["法人人格否认", "公司僵局"],
    "保理": ["保理", "应收账款"],
    "让与担保": ["流押", "让与担保"],
    "流押": ["流押"],
    "诉讼时效": ["诉讼时效"],
    "举证": ["举证"],
    "担保": ["优先受偿", "让与担保"],
    "连带责任": ["连带责任", "法人人格否认"],
    "物业": ["物业", "安全保障"],
    "房屋": ["房屋买卖", "违约方解除"],
    "消费者": ["欺诈", "食品安全", "惩罚性赔偿"],
    "公益": ["公益赠与"],
    "赠与": ["公益赠与"],
    "执行": ["执行异议", "案外人"],
    "案外人": ["案外人", "执行异议"],
}


class CaseRetriever:
    """指导案例检索引擎 — 本地 JSON 数据库 + 标签/关键词自动匹配"""

    def __init__(self, cases_dir: Optional[Path] = None):
        self.cases_dir = cases_dir or GUIDING_CASES_DIR
        self.cases_file = self.cases_dir / "cases.json"
        self.index_file = self.cases_dir / "index.json"
        self.update_log_file = self.cases_dir / "update_log.json"
        self._cases: List[Dict[str, Any]] = []
        self._index: Dict[str, Any] = {}
        self._update_log: Dict[str, Any] = {}
        self._loaded: bool = False
        self._load_data()

    # ---------- 加载 ----------
    def _load_data(self):
        self._load_cases()
        self._load_index()
        self._load_update_log()

    def _load_cases(self):
        if not self.cases_file.exists():
            logger.warning(f"指导案例文件不存在: {self.cases_file}")
            return
        try:
            with open(self.cases_file, encoding='utf-8') as f:
                data = json.load(f)
            self._cases = data.get("cases", [])
            self._loaded = True
            logger.debug(f"指导案例加载成功，共 {len(self._cases)} 条")
        except Exception as e:
            logger.warning(f"指导案例加载失败: {e}")

    def _load_index(self):
        if not self.index_file.exists():
            return
        try:
            with open(self.index_file, encoding='utf-8') as f:
                self._index = json.load(f)
        except Exception as e:
            logger.warning(f"指导案例索引加载失败: {e}")

    def _load_update_log(self):
        if not self.update_log_file.exists():
            return
        try:
            with open(self.update_log_file, encoding='utf-8') as f:
                self._update_log = json.load(f)
        except Exception as e:
            logger.warning(f"更新日志加载失败: {e}")

    # ---------- 查询 ----------
    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """根据案例 ID 获取完整案例信息"""
        for case in self._cases:
            if case.get("id") == case_id:
                return case
        return None

    def search_by_keywords(self, keywords: List[str], max_results: int = 3) -> List[Dict[str, Any]]:
        """根据关键词搜索相关指导案例"""
        if not self._loaded:
            return []
        results: List[Dict[str, Any]] = []
        for case in self._cases:
            score = self._keyword_score(case, keywords)
            if score > 0:
                case_copy = dict(case)
                case_copy["_score"] = score
                results.append(case_copy)
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)
        return results[:max_results]

    def search_by_tags(self, tags: List[str], max_results: int = 3) -> List[Dict[str, Any]]:
        """根据风险标签搜索相关指导案例"""
        if not self._loaded:
            return []
        results: List[Dict[str, Any]] = []
        for case in self._cases:
            case_tags = case.get("risk_tags", [])
            overlap = set(tags) & set(case_tags)
            if overlap:
                case_copy = dict(case)
                case_copy["_score"] = len(overlap) * 10
                case_copy["_matched_tags"] = list(overlap)
                results.append(case_copy)
        results.sort(key=lambda x: x.get("_score", 0), reverse=True)
        return results[:max_results]

    def search_by_category(self, category: str) -> List[Dict[str, Any]]:
        """按类别搜索指导案例"""
        return [c for c in self._cases if c.get("category") == category]

    def _keyword_score(self, case: Dict[str, Any], keywords: List[str]) -> int:
        """计算案例与关键词的匹配分"""
        score = 0
        text = " ".join([
            case.get("title", ""),
            case.get("summary", ""),
            case.get("holding", ""),
            " ".join(case.get("keywords", [])),
            " ".join(case.get("risk_tags", "")),
        ]).lower()
        for kw in keywords:
            kw_lower = kw.lower()
            # 标题匹配权重最高
            if kw_lower in case.get("title", "").lower():
                score += 10
            # 关键词列表匹配
            for k in case.get("keywords", []):
                if kw_lower in k.lower() or k.lower() in kw_lower:
                    score += 5
            # 风险标签匹配
            for t in case.get("risk_tags", []):
                if kw_lower in t.lower() or t.lower() in kw_lower:
                    score += 8
            # 正文匹配
            if kw_lower in text:
                score += 2
        return score

    # ---------- 自动匹配 ----------
    def match_for_risk(self, risk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为风险点自动匹配相关指导案例"""
        keywords: List[str] = []
        title = str(risk.get("title", "") or "")
        description = str(risk.get("description", "") or "")
        risk_type = str(risk.get("risk_type", "") or "")

        # 风险类型映射
        keywords.extend(self._extract_keywords(risk_type))
        keywords.extend(self._extract_keywords(title))
        keywords.extend(self._extract_keywords(description))

        # 去重
        keywords = list(dict.fromkeys(keywords))

        # 先按标签搜索（精确匹配）
        tag_results = self.search_by_tags(keywords, max_results=2)
        # 再按关键词搜索（模糊匹配）
        kw_results = self.search_by_keywords(keywords, max_results=3)

        # 合并去重
        seen = set()
        combined = []
        for case in tag_results + kw_results:
            cid = case.get("id")
            if cid not in seen:
                seen.add(cid)
                combined.append(case)
        return combined[:3]

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取法律相关关键词"""
        if not text:
            return []
        keywords = []
        for risk_key in RISK_TO_CASE_TAGS:
            if risk_key in text:
                keywords.append(risk_key)
        return keywords

    # ---------- 格式化输出 ----------
    def format_citation(self, case: Dict[str, Any], include_summary: bool = False) -> str:
        """格式化指导案例引用"""
        case_no = case.get("case_no", "")
        title = case.get("title", "")
        holding = case.get("holding", "")

        cite = f"参见{case_no}「{title}」"
        if include_summary and holding:
            cite += f"（核心裁判要旨：{holding}）"
        return cite

    # ---------- 批量富化 ----------
    def enrich_risks(self, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """为风险点列表自动匹配指导案例并写入 guiding_cases 字段"""
        enriched = []
        for risk in risks:
            risk = dict(risk)  # 不修改原对象
            cases = self.match_for_risk(risk)
            if cases:
                citations = []
                for c in cases:
                    cite = self.format_citation(c, include_summary=False)
                    citations.append(cite)
                risk["guiding_cases"] = "；".join(citations)
            enriched.append(risk)
        return enriched

    # ---------- 月度更新提醒 ----------
    def check_update_reminder(self) -> Optional[str]:
        """检查指导案例数据库是否需要更新（月度提醒）"""
        if not self._update_log:
            return None
        next_update = self._update_log.get("next_update")
        if not next_update:
            return None
        try:
            next_date = datetime.strptime(next_update, "%Y-%m-%d")
            days_until = (next_date - datetime.now()).days
            if days_until <= 7 and days_until >= 0:
                return (
                    f"指导案例数据库下次更新日为 {next_update}（{days_until} 天后）。"
                    f"建议关注最高人民法院新发布的指导性案例。"
                )
            elif days_until < 0:
                return (
                    f"指导案例数据库已逾期 {-days_until} 天未更新（应更新于 {next_update}）。"
                    f"建议尽快同步最新指导性案例。"
                )
        except ValueError:
            pass
        return None

    # ---------- 属性 ----------
    @property
    def is_available(self) -> bool:
        return self._loaded and len(self._cases) > 0

    @property
    def total_cases(self) -> int:
        return len(self._cases)

    @property
    def last_updated(self) -> Optional[str]:
        return self._update_log.get("updated")


# ---------- 便捷函数 ----------
_default_retriever: Optional[CaseRetriever] = None


def get_case_retriever() -> CaseRetriever:
    """获取全局单例"""
    global _default_retriever
    if _default_retriever is None:
        _default_retriever = CaseRetriever()
    return _default_retriever


def enrich_risks_with_cases(risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """便捷函数：为风险点列表匹配指导案例"""
    return get_case_retriever().enrich_risks(risks)


def search_cases(keywords: List[str], max_results: int = 3) -> List[Dict[str, Any]]:
    """便捷函数：搜索指导案例"""
    return get_case_retriever().search_by_keywords(keywords, max_results)


if __name__ == "__main__":
    # 简单测试
    retriever = CaseRetriever()
    print(f"指导案例数据库可用: {retriever.is_available}")
    print(f"指导案例总数: {retriever.total_cases}")
    print(f"最近更新: {retriever.last_updated}")

    # 测试搜索
    results = retriever.search_by_keywords(["违约金", "欺诈"], max_results=3)
    print(f"\n搜索'违约金 欺诈'，命中 {len(results)} 条:")
    for r in results:
        print(f"  - {retriever.format_citation(r, include_summary=True)}")

    # 测试富化
    sample_risks = [{
        "risk_id": "TEST-001",
        "risk_type": "欺诈行为",
        "severity": "high",
        "title": "经营者隐瞒产品缺陷构成欺诈",
        "description": "故意隐瞒真实情况或告知虚假情况",
        "suggestion": "建议消费者主张惩罚性赔偿",
        "text_snippet": "欺诈",
        "clause_ref": "第 5 条",
    }]
    enriched = retriever.enrich_risks(sample_risks)
    print("\n富化结果:")
    for risk in enriched:
        print(f"  案例: {risk.get('guiding_cases', '无')}")

    # 月度提醒
    reminder = retriever.check_update_reminder()
    if reminder:
        print(f"\n⚠️ {reminder}")
    else:
        print("\n✅ 指导案例数据库更新及时")
