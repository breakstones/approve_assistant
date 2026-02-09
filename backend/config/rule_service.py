"""
TrustLens AI - Configuration Services
规则 CRUD 服务
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import Rule, RuleType, RiskLevel, RuleCategory
from .database import get_database


class RuleService:
    """规则服务类"""

    def __init__(self):
        """初始化规则服务"""
        self.db = get_database()

    def create(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新规则

        Args:
            rule_data: 规则数据字典

        Returns:
            创建的规则字典
        """
        with self.db.get_session() as session:
            # 检查 rule_id 是否已存在
            existing = session.query(Rule).filter(
                Rule.rule_id == rule_data["rule_id"]
            ).first()
            if existing:
                raise ValueError(f"规则 ID '{rule_data['rule_id']}' 已存在")

            # 创建规则
            rule = Rule.from_dict(rule_data)
            session.add(rule)
            session.flush()
            session.refresh(rule)

            # 在会话内转换为字典
            return rule.to_dict()

    def get_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取规则

        Args:
            rule_id: 规则 ID

        Returns:
            规则字典，不存在时返回 None
        """
        with self.db.get_session() as session:
            rule = session.query(Rule).filter(
                and_(Rule.rule_id == rule_id, Rule.enabled == True)
            ).first()
            if rule:
                session.refresh(rule)
                return rule.to_dict()
            return None

    def list(
        self,
        category: Optional[str] = None,
        risk_level: Optional[str] = None,
        type: Optional[str] = None,
        enabled_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        获取规则列表

        Args:
            category: 按分类过滤
            risk_level: 按风险等级过滤
            type: 按类型过滤
            enabled_only: 只返回启用的规则
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            规则字典列表
        """
        with self.db.get_session() as session:
            query = session.query(Rule)

            # 应用过滤条件
            if enabled_only:
                query = query.filter(Rule.enabled == True)

            if category:
                query = query.filter(Rule.category == category)

            if risk_level:
                query = query.filter(Rule.risk_level == risk_level)

            if type:
                query = query.filter(Rule.type == type)

            # 排序和分页
            query = query.order_by(Rule.category, Rule.risk_level, Rule.name)
            query = query.offset(offset).limit(limit)

            rules = query.all()
            # 在会话内转换为字典
            return [rule.to_dict() for rule in rules]

    def update(self, rule_id: str, rule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新规则

        Args:
            rule_id: 规则 ID
            rule_data: 更新的数据

        Returns:
            更新后的规则字典，不存在时返回 None
        """
        with self.db.get_session() as session:
            rule = session.query(Rule).filter(Rule.rule_id == rule_id).first()
            if not rule:
                return None

            # 更新字段
            for key, value in rule_data.items():
                if key != "rule_id" and hasattr(rule, key):
                    setattr(rule, key, value)

            # 自动增加版本号
            rule.version += 1

            session.flush()
            session.refresh(rule)

            return rule.to_dict()

    def delete(self, rule_id: str) -> bool:
        """
        删除规则（软删除，设置 enabled=False）

        Args:
            rule_id: 规则 ID

        Returns:
            是否成功删除
        """
        with self.db.get_session() as session:
            rule = session.query(Rule).filter(Rule.rule_id == rule_id).first()
            if not rule:
                return False

            # 软删除
            rule.enabled = False
            session.flush()

            return True

    def hard_delete(self, rule_id: str) -> bool:
        """
        硬删除规则

        Args:
            rule_id: 规则 ID

        Returns:
            是否成功删除
        """
        with self.db.get_session() as session:
            rule = session.query(Rule).filter(Rule.rule_id == rule_id).first()
            if not rule:
                return False

            session.delete(rule)
            session.flush()

            return True

    def count(
        self,
        category: Optional[str] = None,
        risk_level: Optional[str] = None,
        enabled_only: bool = True,
    ) -> int:
        """
        统计规则数量

        Args:
            category: 按分类过滤
            risk_level: 按风险等级过滤
            enabled_only: 只统计启用的规则

        Returns:
            规则数量
        """
        with self.db.get_session() as session:
            query = session.query(Rule)

            if enabled_only:
                query = query.filter(Rule.enabled == True)

            if category:
                query = query.filter(Rule.category == category)

            if risk_level:
                query = query.filter(Rule.risk_level == risk_level)

            return query.count()

    def get_categories(self) -> List[str]:
        """获取所有规则分类"""
        with self.db.get_session() as session:
            categories = session.query(Rule.category).distinct().all()
            return [c[0] for c in categories if c[0]]

    def get_risk_levels(self) -> List[str]:
        """获取所有风险等级"""
        with self.db.get_session() as session:
            levels = session.query(Rule.risk_level).distinct().all()
            return [l[0] for l in levels if l[0]]

    def bulk_create(self, rules_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量创建规则

        Args:
            rules_data: 规则数据列表

        Returns:
            创建的规则字典列表
        """
        created_rules = []
        for rule_data in rules_data:
            try:
                rule = self.create(rule_data)
                created_rules.append(rule.to_dict())
            except ValueError:
                # 跳过已存在的规则
                pass
        return created_rules
