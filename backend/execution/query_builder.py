"""
TrustLens AI - Rule-aware Query Builder
基于规则语义的检索查询生成模块
"""
import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class SearchQuery:
    """检索查询"""
    query_id: str
    text: str
    keywords: List[str]
    tags: Set[str]
    rules: List[str]  # 关联的规则ID列表
    query_type: str = "semantic"  # semantic, keyword, hybrid
    weight: float = 1.0  # 查询权重

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "text": self.text,
            "keywords": self.keywords,
            "tags": list(self.tags),
            "rules": self.rules,
            "query_type": self.query_type,
            "weight": self.weight,
        }


@dataclass
class QueryBuildResult:
    """查询构建结果"""
    queries: List[SearchQuery]
    rules_count: int
    unique_keywords: int
    unique_tags: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "queries": [q.to_dict() for q in self.queries],
            "rules_count": self.rules_count,
            "unique_keywords": self.unique_keywords,
            "unique_tags": self.unique_tags,
        }


class RuleAwareQueryBuilder:
    """规则感知的查询构建器"""

    # 关键词提取停用词
    STOP_WORDS = {
        "的", "了", "是", "在", "和", "与", "或", "但", "而", "等",
        "应", "需", "要", "可以", "能够", "应该", "必须",
        "this", "that", "the", "a", "an", "and", "or", "but",
        "shall", "should", "must", "may", "can", "will",
    }

    # 规则类型到关键词模板的映射
    RULE_TYPE_TEMPLATES = {
        "numeric_constraint": [
            "{参数名称} {数值}",
            "{参数名称} 不超过 {数值}",
            "{参数名称} 少于 {数值}",
            "{参数名称} 超过 {数值}",
        ],
        "text_contains": [
            "{关键词}",
            "包含 {关键词}",
            "约定 {关键词}",
            "规定 {关键词}",
        ],
        "prohibition": [
            "禁止 {行为}",
            "不得 {行为}",
            "不允许 {行为}",
            "不能 {行为}",
        ],
        "requirement": [
            "{义务}",
            "应当 {义务}",
            "必须 {义务}",
            "有义务 {义务}",
        ],
    }

    def __init__(
        self,
        max_queries_per_rule: int = 3,
        min_keyword_length: int = 2,
        max_query_length: int = 100,
    ):
        """
        初始化查询构建器

        Args:
            max_queries_per_rule: 每条规则生成的最大查询数
            min_keyword_length: 最小关键词长度
            max_query_length: 最大查询长度
        """
        self.max_queries_per_rule = max_queries_per_rule
        self.min_keyword_length = min_keyword_length
        self.max_query_length = max_query_length

    def build_queries(
        self,
        rules: List[Dict[str, Any]],
        combine_rules: bool = True,
    ) -> QueryBuildResult:
        """
        从规则列表构建检索查询

        Args:
            rules: 规则列表
            combine_rules: 是否合并多规则的查询

        Returns:
            查询构建结果
        """
        all_queries = []
        all_keywords = set()
        all_tags = set()

        # 为每条规则生成查询
        for rule in rules:
            rule_queries = self._build_queries_for_rule(rule)
            all_queries.extend(rule_queries)

            # 收集关键词和标签
            for query in rule_queries:
                all_keywords.update(query.keywords)
                all_tags.update(query.tags)

        # 如果需要合并查询
        if combine_rules and len(rules) > 1:
            combined_queries = self._build_combined_queries(rules)
            all_queries.extend(combined_queries)

        return QueryBuildResult(
            queries=all_queries,
            rules_count=len(rules),
            unique_keywords=len(all_keywords),
            unique_tags=len(all_tags),
        )

    def _build_queries_for_rule(
        self,
        rule: Dict[str, Any],
    ) -> List[SearchQuery]:
        """
        为单条规则构建查询

        Args:
            rule: 规则字典

        Returns:
            查询列表
        """
        queries = []

        rule_id = rule.get("rule_id", "")
        rule_type = rule.get("type", "")
        intent = rule.get("intent", "")
        params = rule.get("params", {})
        retrieval_tags = rule.get("retrieval_tags", [])

        # 1. 从 intent 生成查询
        intent_queries = self._build_queries_from_intent(
            rule_id, intent, rule_type, retrieval_tags
        )
        queries.extend(intent_queries)

        # 2. 从 params 生成查询
        param_queries = self._build_queries_from_params(
            rule_id, params, rule_type, retrieval_tags
        )
        queries.extend(param_queries)

        # 3. 使用模板生成查询
        template_queries = self._build_queries_from_templates(
            rule_id, rule_type, params, retrieval_tags
        )
        queries.extend(template_queries)

        # 限制查询数量
        if len(queries) > self.max_queries_per_rule:
            # 按优先级排序：intent > params > templates
            queries = queries[:self.max_queries_per_rule]

        return queries

    def _build_queries_from_intent(
        self,
        rule_id: str,
        intent: str,
        rule_type: str,
        retrieval_tags: List[str],
    ) -> List[SearchQuery]:
        """从 intent 生成查询"""
        if not intent:
            return []

        queries = []
        keywords = self._extract_keywords(intent)

        # 生成自然语言查询
        query_text = intent

        # 如果 intent 太短，可以补充
        if len(intent) < 10:
            if rule_type == "prohibition":
                query_text = f"禁止{intent}"
            elif rule_type == "requirement":
                query_text = f"应当{intent}"

        query = SearchQuery(
            query_id=f"{rule_id}_intent",
            text=query_text[:self.max_query_length],
            keywords=keywords,
            tags=set(retrieval_tags),
            rules=[rule_id],
            query_type="semantic",
            weight=1.0,
        )

        queries.append(query)

        # 生成关键词查询
        if keywords:
            keyword_query = SearchQuery(
                query_id=f"{rule_id}_keywords",
                text=" ".join(keywords[:5]),  # 限制关键词数量
                keywords=keywords,
                tags=set(retrieval_tags),
                rules=[rule_id],
                query_type="keyword",
                weight=0.8,
            )
            queries.append(keyword_query)

        return queries

    def _build_queries_from_params(
        self,
        rule_id: str,
        params: Dict[str, Any],
        rule_type: str,
        retrieval_tags: List[str],
    ) -> List[SearchQuery]:
        """从 params 生成查询"""
        queries = []

        for param_name, param_value in params.items():
            if not param_value:
                continue

            # 跳过非文本参数
            if isinstance(param_value, (int, float)):
                param_value = str(param_value)
            elif not isinstance(param_value, str):
                continue

            # 生成查询
            keywords = self._extract_keywords(param_value)

            query_text = param_value

            # 根据规则类型补充查询文本
            if rule_type == "numeric_constraint":
                if "threshold" in param_name or "limit" in param_name:
                    query_text = f"{param_value}以内"
                elif "min" in param_name or "lower" in param_name:
                    query_text = f"不少于{param_value}"

            query = SearchQuery(
                query_id=f"{rule_id}_param_{param_name}",
                text=query_text[:self.max_query_length],
                keywords=keywords + [param_name],
                tags=set(retrieval_tags),
                rules=[rule_id],
                query_type="keyword",
                weight=0.9,
            )

            queries.append(query)

        return queries

    def _build_queries_from_templates(
        self,
        rule_id: str,
        rule_type: str,
        params: Dict[str, Any],
        retrieval_tags: List[str],
    ) -> List[SearchQuery]:
        """从模板生成查询"""
        queries = []

        templates = self.RULE_TYPE_TEMPLATES.get(rule_type, [])

        for template in templates:
            try:
                # 尝试填充模板
                query_text = template

                # 替换占位符
                for param_name, param_value in params.items():
                    if isinstance(param_value, str):
                        placeholder = f"{{{param_name}}}"
                        if placeholder in template:
                            query_text = query_text.replace(placeholder, param_value)

                # 替换通用占位符
                if "{参数名称}" in query_text and params:
                    first_param = list(params.keys())[0]
                    query_text = query_text.replace("{参数名称}", first_param)

                if "{数值}" in query_text:
                    number_value = next(
                        (str(v) for v in params.values() if isinstance(v, (int, float))),
                        "指定值"
                    )
                    query_text = query_text.replace("{数值}", str(number_value))

                if "{关键词}" in query_text:
                    keyword_value = next(
                        (v for v in params.values() if isinstance(v, str)),
                        "约定内容"
                    )
                    query_text = query_text.replace("{关键词}", keyword_value)

                if "{行为}" in query_text:
                    action_value = next(
                        (v for v in params.values() if isinstance(v, str)),
                        "相关行为"
                    )
                    query_text = query_text.replace("{行为}", action_value)

                if "{义务}" in query_text:
                    obligation_value = next(
                        (v for v in params.values() if isinstance(v, str)),
                        "相关义务"
                    )
                    query_text = query_text.replace("{义务}", obligation_value)

                # 如果模板仍有占位符，跳过
                if "{" in query_text:
                    continue

                keywords = self._extract_keywords(query_text)

                query = SearchQuery(
                    query_id=f"{rule_id}_template_{len(queries)}",
                    text=query_text[:self.max_query_length],
                    keywords=keywords,
                    tags=set(retrieval_tags),
                    rules=[rule_id],
                    query_type="hybrid",
                    weight=0.7,
                )

                queries.append(query)

            except Exception:
                # 模板填充失败，跳过
                continue

        return queries

    def _build_combined_queries(
        self,
        rules: List[Dict[str, Any]],
    ) -> List[SearchQuery]:
        """构建多规则合并查询"""
        if len(rules) < 2:
            return []

        combined_queries = []

        # 收集所有关键词
        all_keywords = []
        all_tags = set()
        rule_ids = []

        for rule in rules:
            rule_ids.append(rule.get("rule_id", ""))
            intent = rule.get("intent", "")
            params = rule.get("params", {})
            retrieval_tags = rule.get("retrieval_tags", [])

            # 从 intent 提取关键词
            if intent:
                all_keywords.extend(self._extract_keywords(intent))

            # 从 params 提取关键词
            for param_value in params.values():
                if isinstance(param_value, str):
                    all_keywords.extend(self._extract_keywords(param_value))

            # 收集标签
            all_tags.update(retrieval_tags)

        # 统计关键词频率
        keyword_freq = Counter(all_keywords)

        # 选择高频关键词
        top_keywords = [kw for kw, _ in keyword_freq.most_common(10)]

        if top_keywords:
            combined_query = SearchQuery(
                query_id=f"combined_{len(rules)}rules",
                text=" ".join(top_keywords),
                keywords=top_keywords,
                tags=all_tags,
                rules=rule_ids,
                query_type="hybrid",
                weight=0.6,
            )
            combined_queries.append(combined_query)

        return combined_queries

    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 输入文本

        Returns:
            关键词列表
        """
        if not text:
            return []

        # 分词（简单按空格和标点分词）
        words = re.findall(r'[\w\u4e00-\u9fff]+', text)

        # 过滤停用词和短词
        keywords = [
            word for word in words
            if len(word) >= self.min_keyword_length
            and word not in self.STOP_WORDS
        ]

        # 去重
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords


def build_search_queries(
    rules: List[Dict[str, Any]],
    combine_rules: bool = True,
    max_queries_per_rule: int = 3,
) -> QueryBuildResult:
    """
    便捷函数：从规则列表构建检索查询

    Args:
        rules: 规则列表
        combine_rules: 是否合并多规则的查询
        max_queries_per_rule: 每条规则生成的最大查询数

    Returns:
        查询构建结果
    """
    builder = RuleAwareQueryBuilder(
        max_queries_per_rule=max_queries_per_rule,
    )
    return builder.build_queries(rules, combine_rules=combine_rules)


def get_filter_tags(rules: List[Dict[str, Any]]) -> Set[str]:
    """
    从规则列表中提取所有检索标签

    Args:
        rules: 规则列表

    Returns:
        标签集合
    """
    tags = set()
    for rule in rules:
        retrieval_tags = rule.get("retrieval_tags", [])
        tags.update(retrieval_tags)
    return tags
