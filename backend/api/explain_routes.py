"""
TrustLens AI - Explainability API Routes
追问与解释 HTTP API
"""
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
import json


# API Router
router = APIRouter(
    prefix="/explain",
    tags=["explainability"],
)


# Request/Response Models
class ExplainRequest(BaseModel):
    """追问请求"""
    review_id: str = Field(..., description="审查任务 ID")
    result_id: str = Field(..., description="审核结果 ID")
    question: str = Field(..., description="用户问题")
    session_id: Optional[str] = Field(None, description="会话 ID（多轮对话时传入）")


class ExplainResponse(BaseModel):
    """解释响应"""
    session_id: str
    message_id: str
    answer: str
    reasoning: str
    evidence_references: List[dict]
    confidence: str
    limitations: List[str]
    timestamp: str


class ConversationMessage(BaseModel):
    """对话消息"""
    message_id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


class ConversationHistory(BaseModel):
    """对话历史响应"""
    session_id: str
    review_id: str
    result_id: str
    messages: List[ConversationMessage]
    created_at: str
    last_updated: str


# 会话存储（内存实现，生产环境应使用数据库）
class SessionManager:
    """会话管理器"""

    def __init__(self):
        # session_id -> session data
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self, review_id: str, result_id: str
    ) -> str:
        """创建新会话"""
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        self._sessions[session_id] = {
            "session_id": session_id,
            "review_id": review_id,
            "result_id": result_id,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        return self._sessions.get(session_id)

    def add_message(
        self, session_id: str, role: str, content: str
    ) -> str:
        """添加消息到会话"""
        session = self._sessions.get(session_id)
        if not session:
            return None

        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        message = {
            "message_id": message_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }

        session["messages"].append(message)
        session["last_updated"] = datetime.now().isoformat()

        return message_id

    def get_messages(
        self, session_id: str
    ) -> List[Dict[str, Any]]:
        """获取会话消息"""
        session = self._sessions.get(session_id)
        if not session:
            return None
        return session["messages"]

    def list_sessions(
        self, review_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """列会话"""
        sessions = list(self._sessions.values())

        if review_id:
            sessions = [s for s in sessions if s["review_id"] == review_id]

        # 按最后更新时间排序
        sessions.sort(
            key=lambda x: x["last_updated"], reverse=True
        )

        return sessions[:limit]


# 全局会话管理器
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    return _session_manager


@router.post("", response_model=ExplainResponse, status_code=status.HTTP_200_OK)
async def create_explanation(request: ExplainRequest):
    """
    发起追问

    - **review_id**: 审查任务 ID
    - **result_id**: 审核结果 ID（指定要追问的具体审核结果）
    - **question**: 用户问题
    - **session_id**: 会话 ID（多轮对话时传入，首次提问可不传）

    返回基于证据的解释回答。
    """
    try:
        # 获取相关服务
        from execution.executor import get_review_executor as get_executor
        from config.rule_service import RuleService

        executor = get_executor()
        rule_service = RuleService()

        # 验证审查任务存在
        task = executor.get_task(request.review_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"审查任务不存在: {request.review_id}"
            )

        # 查找指定的审核结果
        # 当前 ReviewResult 使用索引而非 result_id
        try:
            result_index = int(request.result_id.replace("result_", ""))
            if 0 <= result_index < len(task.results):
                target_result = task.results[result_index]
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"审核结果索引超出范围: {result_index}"
                )
        except (ValueError, AttributeError):
            # 如果 result_id 不是索引格式，尝试通过 rule_id 查找
            target_result = None
            for result in task.results:
                if result.rule_id == request.result_id:
                    target_result = result
                    break

            if not target_result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"审核结果不存在: {request.result_id}"
                )

        # 获取规则信息
        rule = rule_service.get_by_id(target_result.rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"规则不存在: {target_result.rule_id}"
            )

        # 获取或创建会话
        session_manager = get_session_manager()

        if request.session_id:
            session = session_manager.get_session(request.session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"会话不存在: {request.session_id}"
                )
            session_id = request.session_id
        else:
            session_id = session_manager.create_session(
                request.review_id, request.result_id
            )

        # 记录用户问题
        session_manager.add_message(session_id, "user", request.question)

        # 生成解释（Mock实现，生产环境应调用LLM）
        explanation = _generate_explanation(
            rule=rule,
            result=target_result,
            question=request.question,
            history=session_manager.get_messages(session_id)[:-1],  # 排除刚添加的消息
        )

        # 记录助手回复
        session_manager.add_message(
            session_id, "assistant", json.dumps(explanation, ensure_ascii=False)
        )

        return ExplainResponse(
            session_id=session_id,
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            answer=explanation["answer"],
            reasoning=explanation["reasoning"],
            evidence_references=explanation["evidence_references"],
            confidence=explanation["confidence"],
            limitations=explanation["limitations"],
            timestamp=datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成解释失败: {str(e)}"
        )


def _generate_explanation(
    rule: dict, result: "ReviewResult", question: str, history: List[dict]
) -> dict:
    """
    生成解释（Mock实现）

    生产环境应该：
    1. 加载 prompts/explain.txt 模板
    2. 构建完整上下文（规则+结果+证据+问题+历史）
    3. 调用 LLM 生成回答
    4. 解析并验证输出
    """
    # Mock: 根据问题关键词生成简单回答
    question_lower = question.lower()

    # 提取证据信息
    evidence_refs = []
    for evidence in result.evidence:
        # evidence 是字典类型
        chunk_id = evidence.get("chunk_id", "")
        quote = evidence.get("quote", "")
        page = evidence.get("page")
        bbox = evidence.get("bbox", {})

        evidence_refs.append({
            "chunk_id": chunk_id,
            "quote": quote,
            "page": page,
            "bbox": bbox,
            "relevance": "直接相关" if page else "参考信息",
        })

    # 根据问题类型生成回答
    # result.status 是字符串，不是枚举
    if "为什么" in question or "为何" in question:
        if result.status == "PASS":
            answer = f"该合同通过了「{rule['name']}」规则的审查。{rule['intent']}"
        elif result.status == "RISK":
            answer = f"该合同在「{rule['name']}」方面存在风险。{result.reason}"
        else:  # MISSING
            answer = f"该合同缺少「{rule['name']}」相关条款。{result.reason}"

        reasoning = f"根据规则要求「{rule['intent']}」检查合同内容。"

    elif "哪里" in question or "哪条" in question or "第几" in question:
        if evidence_refs:
            pages = set(e["page"] for e in evidence_refs if e["page"])
            if pages:
                answer = f"相关条款位于合同第 {', '.join(map(str, sorted(pages)))} 页。"
            else:
                answer = "相关条款的位置信息请参考下方证据引用。"
        else:
            answer = "根据现有证据，未找到明确的相关条款位置。"
        reasoning = "根据证据中的页码信息定位。"

    elif "如何" in question or "怎么" in question or "建议" in question:
        if result.status == "RISK":
            answer = f"建议修改合同以符合规则要求：{rule['intent']}。"
        elif result.status == "MISSING":
            answer = f"建议在合同中补充相关条款：{rule['intent']}。"
        else:
            answer = "合同已符合规则要求，无需修改。"
        reasoning = f"基于规则「{rule['intent']}」给出建议。"

    else:
        # 默认回答
        answer = f"关于「{rule['name']}」，审核结论为{result.status}。{result.reason}"
        reasoning = f"根据规则「{rule['intent']}」进行审核。"

    return {
        "answer": answer,
        "reasoning": reasoning,
        "evidence_references": evidence_refs,
        "confidence": "high" if evidence_refs else "medium",
        "limitations": [] if evidence_refs else ["证据可能不完整"],
    }


@router.get("/{session_id}/history", response_model=ConversationHistory)
async def get_conversation_history(session_id: str):
    """
    获取对话历史

    - **session_id**: 会话 ID
    """
    try:
        session_manager = get_session_manager()
        session = session_manager.get_session(session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"会话不存在: {session_id}"
            )

        messages = [
            ConversationMessage(
                message_id=msg["message_id"],
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"],
            )
            for msg in session["messages"]
        ]

        return ConversationHistory(
            session_id=session["session_id"],
            review_id=session["review_id"],
            result_id=session["result_id"],
            messages=messages,
            created_at=session["created_at"],
            last_updated=session["last_updated"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取对话历史失败: {str(e)}"
        )


@router.get("/sessions", response_model=List[dict])
async def list_explain_sessions(
    review_id: Optional[str] = Query(None, description="按审查任务过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
):
    """
    列出解释会话

    支持按审查任务过滤
    """
    try:
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions(review_id=review_id, limit=limit)

        # 简化返回数据
        return [
            {
                "session_id": s["session_id"],
                "review_id": s["review_id"],
                "result_id": s["result_id"],
                "message_count": len(s["messages"]),
                "created_at": s["created_at"],
                "last_updated": s["last_updated"],
            }
            for s in sessions
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"列会话失败: {str(e)}"
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_explain_session(session_id: str):
    """
    删除解释会话

    - **session_id**: 会话 ID
    """
    try:
        session_manager = get_session_manager()

        if session_id not in session_manager._sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"会话不存在: {session_id}"
            )

        del session_manager._sessions[session_id]
        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除会话失败: {str(e)}"
        )
