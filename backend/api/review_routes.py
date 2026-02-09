"""
TrustLens AI - Review API Routes
审查任务 HTTP API
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import asyncio
import uuid


# API Router
router = APIRouter(
    prefix="/review",
    tags=["review"],
)


# Request/Response Models
class ReviewStartRequest(BaseModel):
    """启动审查请求"""
    doc_id: str = Field(..., description="文档 ID")
    rule_ids: Optional[List[str]] = Field(None, description="指定规则ID列表（为空则使用所有启用的规则）")
    rules_filter: Optional[dict] = Field(None, description="规则过滤条件（category, risk_level, type）")


class ReviewStatusResponse(BaseModel):
    """审查状态响应"""
    review_id: str
    doc_id: str
    status: str
    total_rules: int
    completed_rules: int
    progress: float
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]


class ReviewResultResponse(BaseModel):
    """审查结果响应"""
    review_id: str
    doc_id: str
    status: str
    results: List[dict]
    summary: dict
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]


# 服务实例
_review_executor = None
_rule_service = None
_document_service = None


def get_review_executor():
    """获取审查执行器实例"""
    global _review_executor
    if _review_executor is None:
        from execution.executor import get_review_executor as get_executor
        _review_executor = get_executor()
    return _review_executor


def get_rule_service():
    """获取规则服务实例"""
    global _rule_service
    if _rule_service is None:
        from config.rule_service import get_database, RuleService
        get_database()
        _rule_service = RuleService()
    return _rule_service


def get_document_service():
    """获取文档服务实例"""
    global _document_service
    if _document_service is None:
        from config.document_service import get_document_service as get_doc_service
        from config.database import get_database
        get_database()
        _document_service = get_doc_service()
    return _document_service


async def execute_review_background(
    review_id: str,
    doc_id: str,
    rule_ids: List[str],
    rules: List[dict],
):
    """
    后台执行审查任务

    Args:
        review_id: 审查 ID
        doc_id: 文档 ID
        rule_ids: 规则 ID 列表
        rules: 规则列表
    """
    executor = get_review_executor()
    document_service = get_document_service()

    try:
        # 获取文档的 chunks
        doc = document_service.get_by_id(doc_id)
        if not doc:
            raise ValueError(f"文档不存在: {doc_id}")

        # 获取 chunks（从向量存储或数据库）
        # 这里简化处理，实际应该从向量存储获取
        chunks = _get_document_chunks(doc_id)

        # 创建执行上下文
        from execution.executor import ExecutionContext
        from document import create_embedding_pipeline

        context = ExecutionContext(
            doc_id=doc_id,
            chunks=chunks,
            embedding_pipeline=create_embedding_pipeline(),
            llm_client=None,  # 使用 Mock
        )

        # 执行审查
        await executor.execute_review(
            review_id=review_id,
            rules=rules,
            context=context,
            progress_callback=lambda rid, completed, total, msg: None,
        )

    except Exception as e:
        # 记录错误
        executor = get_review_executor()
        task = executor.get_task(review_id)
        if task:
            task.error = str(e)
            task.status = "FAILED"


def _get_document_chunks(doc_id: str) -> List[dict]:
    """获取文档的 chunks（简化版本）"""
    # 这里应该从向量存储或数据库获取
    # 返回 mock 数据
    return [
        {
            "chunk_id": f"{doc_id}_p1_c0",
            "doc_id": doc_id,
            "page": 1,
            "text": "样本文本内容",
            "bbox": {"x1": 0, "y1": 0, "x2": 100, "y2": 20},
            "clause_hint": "payment",
        }
    ]


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_review(
    background_tasks: BackgroundTasks,
    request: ReviewStartRequest,
):
    """
    启动审查任务

    - **doc_id**: 文档 ID（必需）
    - **rule_ids**: 规则 ID 列表（可选，为空则使用所有启用规则）
    - **rules_filter**: 规则过滤条件（可选）
    """
    try:
        # 获取服务
        rule_service = get_rule_service()
        executor = get_review_executor()
        document_service = get_document_service()

        # 验证文档存在
        doc = document_service.get_by_id(request.doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档不存在: {request.doc_id}"
            )

        # 获取规则列表
        if request.rule_ids:
            # 使用指定的规则
            rules = []
            for rule_id in request.rule_ids:
                rule = rule_service.get_by_id(rule_id)
                if rule:
                    rules.append(rule)
        else:
            # 使用所有启用的规则，支持过滤
            rules = rule_service.list(
                enabled_only=True,
                category=request.rules_filter.get("category") if request.rules_filter else None,
                risk_level=request.rules_filter.get("risk_level") if request.rules_filter else None,
                type=request.rules_filter.get("type") if request.rules_filter else None,
            )

        if not rules:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有可用的审查规则"
            )

        rule_ids = [r["rule_id"] for r in rules]

        # 创建审查任务
        from execution.executor import ExecutionContext, ReviewTask, ReviewStatus

        review_id = f"review_{request.doc_id}_{uuid.uuid4().hex[:8]}"

        # 创建初始任务
        task = ReviewTask(
            review_id=review_id,
            doc_id=request.doc_id,
            rule_ids=rule_ids,
            status=ReviewStatus.PENDING,
            metadata={
                "total_rules": len(rule_ids),
                "created_at": datetime.now().isoformat(),
            },
        )

        # 添加到执行器
        executor._tasks[review_id] = task

        # 启动后台任务
        background_tasks.add_task(
            execute_review_background,
            review_id,
            request.doc_id,
            rule_ids,
            rules,
        )

        return {
            "review_id": review_id,
            "doc_id": request.doc_id,
            "total_rules": len(rule_ids),
            "status": "PENDING",
            "message": "审查任务已创建，正在后台执行",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动审查失败: {str(e)}"
        )


@router.get("/{review_id}/status", response_model=ReviewStatusResponse)
async def get_review_status(review_id: str):
    """
    获取审查状态

    - **review_id**: 审查任务 ID
    """
    try:
        executor = get_review_executor()
        task = executor.get_task(review_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"审查任务不存在: {review_id}"
            )

        # 计算进度
        total = task.metadata.get("total_rules", 0)
        completed = len(task.results)
        progress = (completed / total * 100) if total > 0 else 0

        return ReviewStatusResponse(
            review_id=task.review_id,
            doc_id=task.doc_id,
            status=task.status.value if isinstance(task.status, type(task.status)) else task.status,
            total_rules=total,
            completed_rules=completed,
            progress=progress,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            error=task.error,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取审查状态失败: {str(e)}"
        )


@router.get("/{review_id}/results", response_model=ReviewResultResponse)
async def get_review_results(review_id: str):
    """
    获取审查结果

    - **review_id**: 审查任务 ID
    """
    try:
        executor = get_review_executor()
        task = executor.get_task(review_id)

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"审查任务不存在: {review_id}"
            )

        # 统计结果
        results = [r.to_dict() for r in task.results]

        summary = {
            "total": len(results),
            "pass": len([r for r in results if r["status"] == "PASS"]),
            "risk": len([r for r in results if r["status"] == "RISK"]),
            "missing": len([r for r in results if r["status"] == "MISSING"]),
            "failed": len([r for r in results if r["status"] == "FAILED"]),
        }

        return ReviewResultResponse(
            review_id=task.review_id,
            doc_id=task.doc_id,
            status=task.status.value if isinstance(task.status, type(task.status)) else task.status,
            results=results,
            summary=summary,
            started_at=task.started_at.isoformat() if task.started_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            error=task.error,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取审查结果失败: {str(e)}"
        )


@router.get("", response_model=List[dict])
async def list_reviews(
    status: Optional[str] = Query(None, description="按状态过滤"),
    doc_id: Optional[str] = Query(None, description="按文档过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
):
    """
    列出审查任务

    支持按状态、文档过滤
    """
    try:
        executor = get_review_executor()
        tasks = executor.list_tasks()

        # 过滤
        if status:
            from execution.executor import ReviewStatus
            tasks = [t for t in tasks if t.status == ReviewStatus(status)]
        if doc_id:
            tasks = [t for t in tasks if t.doc_id == doc_id]

        # 限制数量
        tasks = tasks[:limit]

        return [t.to_dict() for t in tasks]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列出审查任务失败: {str(e)}"
        )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_review(review_id: str):
    """
    取消/删除审查任务

    - **review_id**: 审查任务 ID
    """
    try:
        executor = get_review_executor()
        success = executor.delete_task(review_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"审查任务不存在: {review_id}"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消审查任务失败: {str(e)}"
        )
