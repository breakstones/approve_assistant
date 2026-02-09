"""
TrustLens AI - Configuration Models
规则数据模型定义
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, JSON, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum


Base = declarative_base()


class RuleType(str, Enum):
    """规则类型"""
    NUMERIC_CONSTRAINT = "numeric_constraint"
    TEXT_CONTAINS = "text_contains"
    PROHIBITION = "prohibition"
    REQUIREMENT = "requirement"


class RiskLevel(str, Enum):
    """风险等级"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class RuleCategory(str, Enum):
    """规则分类"""
    PAYMENT = "Payment"
    LIABILITY = "Liability"
    CONFIDENTIALITY = "Confidentiality"
    TERMINATION = "Termination"
    INTELLECTUAL_PROPERTY = "Intellectual_Property"
    DISPUTE_RESOLUTION = "Dispute_Resolution"
    FORCE_MAJEURE = "Force_Majeure"
    GOVERNING_LAW = "Governing_Law"
    DELIVERY = "Delivery"
    QUALITY = "Quality"
    WARRANTY = "Warranty"
    INDEMNIFICATION = "Indemnification"
    LIMITATION_OF_LIABILITY = "Limitation_of_Liability"
    AMENDMENT = "Amendment"
    SEVERABILITY = "Severability"
    ENTIRE_AGREEMENT = "Entire_Agreement"
    ASSIGNMENT = "Assignment"
    NOTICES = "Notices"
    OTHER = "Other"


class Rule(Base):
    """
    规则数据模型
    对应 Rule Schema
    """
    __tablename__ = "rules"

    # 主键和必需字段
    rule_id = Column(String(100), primary_key=True, comment="规则唯一标识符")
    name = Column(String(200), nullable=False, comment="规则名称")
    category = Column(String(50), nullable=False, comment="规则分类")
    intent = Column(String(500), nullable=False, comment="规则意图描述")
    type = Column(String(50), nullable=False, comment="规则类型")
    params = Column(JSON, nullable=False, comment="规则参数")
    risk_level = Column(String(20), nullable=False, comment="风险等级")
    retrieval_tags = Column(JSON, nullable=False, comment="检索标签")
    prompt_template_id = Column(String(100), nullable=False, comment="Prompt 模板 ID")

    # 可选字段
    version = Column(Integer, default=1, nullable=False, comment="规则版本号")
    enabled = Column(Boolean, default=True, nullable=False, comment="规则是否启用")
    description = Column(String(1000), comment="规则详细描述")

    # 审计字段
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment="更新时间")
    created_by = Column(String(100), comment="创建人")
    updated_by = Column(String(100), comment="更新人")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "category": self.category,
            "intent": self.intent,
            "type": self.type,
            "params": self.params,
            "risk_level": self.risk_level,
            "retrieval_tags": self.retrieval_tags,
            "prompt_template_id": self.prompt_template_id,
            "version": self.version,
            "enabled": self.enabled,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Rule":
        """从字典创建实例"""
        return cls(
            rule_id=data.get("rule_id"),
            name=data.get("name"),
            category=data.get("category"),
            intent=data.get("intent"),
            type=data.get("type"),
            params=data.get("params", {}),
            risk_level=data.get("risk_level", "MEDIUM"),
            retrieval_tags=data.get("retrieval_tags", []),
            prompt_template_id=data.get("prompt_template_id", "default_v1"),
            version=data.get("version", 1),
            enabled=data.get("enabled", True),
            description=data.get("description"),
        )

    def __repr__(self) -> str:
        return f"<Rule(rule_id={self.rule_id}, name={self.name}, type={self.type})>"
