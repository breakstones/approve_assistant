"""
TrustLens AI - Rule Parser Service
自然语言规则解析服务
"""
import json
import re
from typing import Dict, Any, Optional
from pathlib import Path


class RuleParser:
    """规则解析器"""

    def __init__(self, prompt_path: Optional[str] = None):
        """
        初始化规则解析器

        Args:
            prompt_path: Prompt 模板文件路径
        """
        if prompt_path is None:
            # 从项目根目录的 prompts 文件夹加载
            project_root = Path(__file__).parent.parent.parent
            prompt_path = project_root / "prompts" / "rule_parsing.txt"
        self.prompt_path = Path(prompt_path)
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """加载 Prompt 模板"""
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_prompt(self, user_input: str) -> str:
        """
        获取完整的 Prompt

        Args:
            user_input: 用户输入的自然语言规则

        Returns:
            完整的 Prompt
        """
        return self.prompt_template.replace("{{USER_INPUT}}", user_input.strip())

    def parse_mock(self, user_input: str) -> Dict[str, Any]:
        """
        模拟解析（不调用 LLM，使用规则匹配）

        Args:
            user_input: 用户输入的自然语言规则

        Returns:
            解析后的规则字典
        """
        input_lower = user_input.lower()

        # 规则 1: 付款周期限制
        if "付款周期" in user_input or "付款期限" in user_input:
            match = re.search(r'(\d+)\s*[天日]', user_input)
            if match:
                days = int(match.group(1))
                return {
                    "rule_id": f"payment_cycle_max_{days}",
                    "name": "付款周期限制",
                    "category": "Payment",
                    "intent": user_input,
                    "type": "numeric_constraint",
                    "params": {
                        "field": "payment_cycle",
                        "operator": "<=",
                        "value": days,
                        "unit": "days"
                    },
                    "risk_level": "HIGH" if days <= 30 else "MEDIUM",
                    "retrieval_tags": ["payment", "cycle", "settlement"],
                    "prompt_template_id": "numeric_constraint_v1"
                }

        # 规则 2: 保密条款要求
        if "保密" in user_input and ("必须" in user_input or "应" in user_input or "需" in user_input):
            return {
                "rule_id": "confidentiality_clause_required",
                "name": "保密条款要求",
                "category": "Confidentiality",
                "intent": user_input,
                "type": "requirement",
                "params": {
                    "required_clauses": [
                        {
                            "clause_type": "confidentiality",
                            "min_content_length": 50
                        }
                    ]
                },
                "risk_level": "HIGH",
                "retrieval_tags": ["confidentiality", "secret", "protection"],
                "prompt_template_id": "requirement_v1"
            }

        # 规则 3: 违约金限制
        if "违约金" in user_input or "罚金" in user_input:
            match = re.search(r'(\d+(?:\.\d+)?)\s*[%％]', user_input)
            if match:
                rate = float(match.group(1))
                return {
                    "rule_id": f"penalty_rate_max_{int(rate)}_percent",
                    "name": "违约金上限限制",
                    "category": "Payment",
                    "intent": user_input,
                    "type": "numeric_constraint",
                    "params": {
                        "field": "penalty_rate",
                        "operator": "<=",
                        "value": rate,
                        "unit": "percent"
                    },
                    "risk_level": "HIGH" if rate <= 5 else "MEDIUM",
                    "retrieval_tags": ["payment", "penalty", "breach"],
                    "prompt_template_id": "numeric_constraint_v1"
                }

        # 规则 4: 禁止自动续约
        if "自动续约" in user_input or "自动延期" in user_input:
            if "不得" in user_input or "禁止" in user_input or "不允许" in user_input:
                return {
                    "rule_id": "no_auto_renewal",
                    "name": "禁止自动续约",
                    "category": "Termination",
                    "intent": user_input,
                    "type": "prohibition",
                    "params": {
                        "prohibited_patterns": ["自动续约", "自动延期", "auto-renew", "automatically renew"],
                        "scope": "entire"
                    },
                    "risk_level": "HIGH",
                    "retrieval_tags": ["termination", "renewal", "expiration"],
                    "prompt_template_id": "prohibition_v1"
                }

        # 规则 5: 管辖法律要求
        if "管辖法律" in user_input or "适用法律" in user_input:
            keywords = []
            if "中华人民共和国" in user_input or "中国" in user_input:
                keywords = ["中华人民共和国法律", "适用法律", "管辖法律"]
            else:
                keywords = ["管辖法律", "适用法律", "法律"]
            return {
                "rule_id": "governing_law_specified",
                "name": "管辖法律要求",
                "category": "Governing_Law",
                "intent": user_input,
                "type": "text_contains",
                "params": {
                    "keywords": keywords,
                    "match_mode": "any",
                    "case_sensitive": False
                },
                "risk_level": "CRITICAL",
                "retrieval_tags": ["governing_law", "jurisdiction", "legal"],
                "prompt_template_id": "text_contains_v1"
            }

        # 规则 6: 不可抗力条款要求
        if "不可抗力" in user_input and ("必须" in user_input or "应" in user_input or "需" in user_input):
            return {
                "rule_id": "force_majeure_clause_required",
                "name": "不可抗力条款要求",
                "category": "Force_Majeure",
                "intent": user_input,
                "type": "requirement",
                "params": {
                    "required_clauses": [
                        {
                            "clause_type": "force_majeure",
                            "min_content_length": 50
                        }
                    ]
                },
                "risk_level": "MEDIUM",
                "retrieval_tags": ["force_majeure", "emergency", "exemption"],
                "prompt_template_id": "requirement_v1"
            }

        # 规则 7: 交付周期限制
        if "交付" in user_input and ("天" in user_input or "日" in user_input):
            match = re.search(r'(\d+)\s*[天日]', user_input)
            if match:
                days = int(match.group(1))
                return {
                    "rule_id": f"delivery_within_{days}_days",
                    "name": "交付周期限制",
                    "category": "Delivery",
                    "intent": user_input,
                    "type": "numeric_constraint",
                    "params": {
                        "field": "delivery_days",
                        "operator": "<=",
                        "value": days,
                        "unit": "days"
                    },
                    "risk_level": "MEDIUM",
                    "retrieval_tags": ["delivery", "shipping", "timeline"],
                    "prompt_template_id": "numeric_constraint_v1"
                }

        # 规则 8: 争议仲裁条款要求
        if "仲裁" in user_input and ("必须" in user_input or "应" in user_input or "需" in user_input):
            return {
                "rule_id": "dispute_arbitration_required",
                "name": "争议仲裁条款要求",
                "category": "Dispute_Resolution",
                "intent": user_input,
                "type": "requirement",
                "params": {
                    "required_clauses": [
                        {
                            "clause_type": "arbitration",
                            "min_content_length": 30
                        }
                    ]
                },
                "risk_level": "MEDIUM",
                "retrieval_tags": ["dispute", "arbitration", "resolution"],
                "prompt_template_id": "requirement_v1"
            }

        # 默认返回 text_contains 类型
        # 提取关键词
        words = re.findall(r'[\u4e00-\u9fa5]+', user_input)
        keywords = words[:5] if len(words) > 5 else words

        return {
            "rule_id": f"custom_rule_{hash(user_input) % 10000}",
            "name": "自定义规则",
            "category": "Other",
            "intent": user_input,
            "type": "text_contains",
            "params": {
                "keywords": keywords,
                "match_mode": "any",
                "case_sensitive": False
            },
            "risk_level": "MEDIUM",
            "retrieval_tags": keywords[:3],
            "prompt_template_id": "text_contains_v1"
        }

    def validate(self, rule_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        验证解析结果是否符合 Rule Schema

        Args:
            rule_data: 解析后的规则数据

        Returns:
            (是否有效, 错误信息)
        """
        required_fields = [
            "rule_id", "name", "category", "intent", "type",
            "params", "risk_level", "retrieval_tags", "prompt_template_id"
        ]

        # 检查必需字段
        for field in required_fields:
            if field not in rule_data:
                return False, f"缺少必需字段: {field}"

        # 验证 rule_id 格式
        rule_id = rule_data["rule_id"]
        if not re.match(r'^[a-z][a-z0-9_]*$', rule_id):
            return False, f"rule_id 格式无效: {rule_id}"

        # 验证 type
        valid_types = ["numeric_constraint", "text_contains", "prohibition", "requirement"]
        if rule_data["type"] not in valid_types:
            return False, f"无效的 type: {rule_data['type']}"

        # 验证 risk_level
        valid_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        if rule_data["risk_level"] not in valid_levels:
            return False, f"无效的 risk_level: {rule_data['risk_level']}"

        # 验证 retrieval_tags
        if not isinstance(rule_data["retrieval_tags"], list) or len(rule_data["retrieval_tags"]) == 0:
            return False, "retrieval_tags 必须是非空数组"

        # 根据 type 验证 params
        rule_type = rule_data["type"]
        params = rule_data.get("params", {})

        if rule_type == "numeric_constraint":
            required_params = ["field", "operator", "value"]
            for param in required_params:
                if param not in params:
                    return False, f"numeric_constraint 缺少 params.{param}"

        elif rule_type == "text_contains":
            required_params = ["keywords", "match_mode"]
            for param in required_params:
                if param not in params:
                    return False, f"text_contains 缺少 params.{param}"

        elif rule_type == "prohibition":
            if "prohibited_patterns" not in params:
                return False, "prohibition 缺少 params.prohibited_patterns"

        elif rule_type == "requirement":
            if "required_clauses" not in params:
                return False, "requirement 缺少 params.required_clauses"

        return True, None


def parse_rule_from_text(text: str) -> Dict[str, Any]:
    """
    便捷函数：从自然语言文本解析规则

    Args:
        text: 自然语言规则描述

    Returns:
        解析后的规则字典
    """
    parser = RuleParser()
    return parser.parse_mock(text)
