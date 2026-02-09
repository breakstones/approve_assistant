"""
TrustLens AI - Rule Configuration API Routes
规则配置管理 HTTP API
"""
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from config import RuleService, get_database
from config.rule_parser import parse_rule_from_text


# API Router
router = APIRouter(
    prefix="/rules",
    tags=["rules"],
)


# Request/Response Models
class RuleCreateRequest(BaseModel):
    """创建规则请求"""
    rule_id: str = Field(..., description="规则唯一标识符")
    name: str = Field(..., description="规则名称")
    category: str = Field(..., description="规则分类")
    intent: str = Field(..., description="规则意图描述")
    type: str = Field(..., description="规则类型")
    params: dict = Field(..., description="规则参数")
    risk_level: str = Field(default="MEDIUM", description="风险等级")
    retrieval_tags: List[str] = Field(default_factory=list, description="检索标签")
    prompt_template_id: str = Field(default="default_v1", description="Prompt 模板 ID")
    description: Optional[str] = Field(None, description="规则详细描述")


class RuleUpdateRequest(BaseModel):
    """更新规则请求"""
    name: Optional[str] = Field(None, description="规则名称")
    category: Optional[str] = Field(None, description="规则分类")
    intent: Optional[str] = Field(None, description="规则意图描述")
    type: Optional[str] = Field(None, description="规则类型")
    params: Optional[dict] = Field(None, description="规则参数")
    risk_level: Optional[str] = Field(None, description="风险等级")
    retrieval_tags: Optional[List[str]] = Field(None, description="检索标签")
    prompt_template_id: Optional[str] = Field(None, description="Prompt 模板 ID")
    description: Optional[str] = Field(None, description="规则详细描述")
    enabled: Optional[bool] = Field(None, description="规则是否启用")


class RuleResponse(BaseModel):
    """规则响应"""
    rule_id: str
    name: str
    category: str
    intent: str
    type: str
    params: dict
    risk_level: str
    retrieval_tags: List[str]
    prompt_template_id: str
    version: int
    enabled: bool
    description: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]


class RuleParseRequest(BaseModel):
    """规则解析请求"""
    text: str = Field(..., description="自然语言规则描述")


class RuleListResponse(BaseModel):
    """规则列表响应"""
    total: int
    rules: List[RuleResponse]
    limit: int
    offset: int


# 服务实例
rule_service: Optional[RuleService] = None


def get_rule_service() -> RuleService:
    """获取规则服务实例"""
    global rule_service
    if rule_service is None:
        # 初始化数据库
        db = get_database()
        rule_service = RuleService()
    return rule_service


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(request: RuleCreateRequest):
    """
    创建新规则

    - **rule_id**: 规则唯一标识符（必需）
    - **name**: 规则名称（必需）
    - **category**: 规则分类（必需）
    - **intent**: 规则意图（必需）
    - **type**: 规则类型（必需）
    - **params**: 规则参数（必需）
    - **risk_level**: 风险等级（默认：MEDIUM）
    - **retrieval_tags**: 检索标签（默认：[]）
    - **prompt_template_id**: Prompt 模板 ID（默认：default_v1）
    """
    service = get_rule_service()

    try:
        # 转换为字典
        rule_data = request.dict(exclude_unset=True)

        # 创建规则
        created_rule = service.create(rule_data)

        return RuleResponse(**created_rule)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建规则失败: {str(e)}"
        )


@router.get("", response_model=RuleListResponse)
async def list_rules(
    category: Optional[str] = Query(None, description="按分类过滤"),
    risk_level: Optional[str] = Query(None, description="按风险等级过滤"),
    type: Optional[str] = Query(None, description="按类型过滤"),
    enabled_only: bool = Query(True, description="只返回启用的规则"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """
    获取规则列表

    支持按分类、风险等级、类型过滤，支持分页
    """
    service = get_rule_service()

    try:
        rules = service.list(
            category=category,
            risk_level=risk_level,
            type=type,
            enabled_only=enabled_only,
            limit=limit,
            offset=offset,
        )

        # 获取总数
        total = service.count(
            category=category,
            risk_level=risk_level,
            enabled_only=enabled_only,
        )

        return RuleListResponse(
            total=total,
            rules=[RuleResponse(**rule) for rule in rules],
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询规则列表失败: {str(e)}"
        )


# 注意：categories 和 risk-levels 路由必须放在 /{rule_id} 之前
# 否则 FastAPI 会把 "categories" 或 "risk-levels" 当作 rule_id 处理


@router.get("/categories", response_model=List[str])
async def get_categories():
    """获取所有规则分类"""
    service = get_rule_service()

    try:
        categories = service.get_categories()
        return categories
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分类失败: {str(e)}"
        )


@router.get("/risk-levels", response_model=List[str])
async def get_risk_levels():
    """获取所有风险等级"""
    service = get_rule_service()

    try:
        levels = service.get_risk_levels()
        return levels
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取风险等级失败: {str(e)}"
        )


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str):
    """
    获取单条规则

    - **rule_id**: 规则唯一标识符
    """
    service = get_rule_service()

    try:
        rule = service.get_by_id(rule_id)

        if rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"规则 '{rule_id}' 不存在"
            )

        return RuleResponse(**rule)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询规则失败: {str(e)}"
        )


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: str, request: RuleUpdateRequest):
    """
    更新规则

    - **rule_id**: 规则唯一标识符
    """
    service = get_rule_service()

    try:
        # 获取更新的字段
        update_data = request.dict(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供要更新的字段"
            )

        # 更新规则
        updated_rule = service.update(rule_id, update_data)

        if updated_rule is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"规则 '{rule_id}' 不存在"
            )

        return RuleResponse(**updated_rule)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新规则失败: {str(e)}"
        )


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: str):
    """
    删除规则（软删除）

    - **rule_id**: 规则唯一标识符
    """
    service = get_rule_service()

    try:
        success = service.delete(rule_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"规则 '{rule_id}' 不存在"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除规则失败: {str(e)}"
        )


@router.post("/parse", response_model=RuleResponse)
async def parse_rule(request: RuleParseRequest):
    """
    从自然语言解析规则

    将自然语言规则描述转换为结构化的规则数据
    """
    try:
        # 解析规则
        parsed_rule = parse_rule_from_text(request.text)

        # 尝试创建规则
        service = get_rule_service()

        try:
            created_rule = service.create(parsed_rule)
            return RuleResponse(**created_rule)
        except ValueError:
            # 规则已存在，仅返回解析结果
            return RuleResponse(**parsed_rule)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"解析规则失败: {str(e)}"
        )
