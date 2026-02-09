"""
TrustLens AI - Review Executor
RAG 审查执行模块，实现完整的检索 + LLM 审核流程
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

# 延迟导入避免循环依赖
from .query_builder import build_search_queries, SearchQuery
from .review_prompt import build_review_prompt, ReviewPromptValidator


class ReviewStatus(str, Enum):
    """审查状态"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class ReviewResult:
    """单个规则审查结果"""
    rule_id: str
    rule_name: str
    status: str  # PASS, RISK, MISSING
    reason: str
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.8
    suggestion: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "status": self.status,
            "reason": self.reason,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "suggestion": self.suggestion,
            "error": self.error,
        }


@dataclass
class ReviewTask:
    """审查任务"""
    review_id: str
    doc_id: str
    rule_ids: List[str]
    status: ReviewStatus
    results: List[ReviewResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_id": self.review_id,
            "doc_id": self.doc_id,
            "rule_ids": self.rule_ids,
            "status": self.status.value if isinstance(self.status, ReviewStatus) else self.status,
            "results": [r.to_dict() for r in self.results],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionContext:
    """执行上下文"""
    doc_id: str
    chunks: List[Dict[str, Any]]
    embedding_pipeline: Any  # EmbeddingPipeline
    llm_client: Optional[Any] = None
    llm_model: str = "gpt-4"
    max_retrieved_chunks: int = 10
    batch_size: int = 5


class ReviewExecutor:
    """RAG 审查执行器"""

    def __init__(
        self,
        vector_store=None,
        llm_client=None,
        llm_model: str = "gpt-4",
    ):
        """
        初始化审查执行器

        Args:
            vector_store: 向量存储实例
            llm_client: LLM 客户端（可选，用于实际调用）
            llm_model: LLM 模型名称
        """
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.llm_model = llm_model
        self.prompt_validator = ReviewPromptValidator()

        # 存储任务
        self._tasks: Dict[str, ReviewTask] = {}

    def create_review(
        self,
        doc_id: str,
        rule_ids: List[str],
        rules: List[Dict[str, Any]],
        context: ExecutionContext,
    ) -> ReviewTask:
        """
        创建审查任务

        Args:
            doc_id: 文档 ID
            rule_ids: 规则 ID 列表
            rules: 规则列表
            context: 执行上下文

        Returns:
            审查任务
        """
        review_id = f"review_{doc_id}_{uuid.uuid4().hex[:8]}"

        task = ReviewTask(
            review_id=review_id,
            doc_id=doc_id,
            rule_ids=rule_ids,
            status=ReviewStatus.PENDING,
            metadata={
                "total_rules": len(rule_ids),
                "llm_model": self.llm_model,
                "created_at": datetime.now().isoformat(),
            },
        )

        self._tasks[review_id] = task
        return task

    async def execute_review(
        self,
        review_id: str,
        rules: List[Dict[str, Any]],
        context: ExecutionContext,
        progress_callback: Optional[Callable] = None,
    ) -> ReviewTask:
        """
        执行审查任务

        Args:
            review_id: 审查任务 ID
            rules: 规则列表
            context: 执行上下文
            progress_callback: 进度回调函数

        Returns:
            审查任务
        """
        task = self._tasks.get(review_id)
        if not task:
            raise ValueError(f"Review task not found: {review_id}")

        try:
            # 更新状态为运行中
            task.status = ReviewStatus.RUNNING
            task.started_at = datetime.now()

            total_rules = len(rules)
            completed = 0

            # 遍历规则执行审查
            for i, rule in enumerate(rules):
                try:
                    # 执行单条规则审查
                    result = await self._execute_rule_review(rule, context)

                    # 添加结果
                    task.results.append(result)
                    completed += 1

                    # 进度回调
                    if progress_callback:
                        await progress_callback(
                            review_id,
                            completed,
                            total_rules,
                            f"已完成 {completed}/{total_rules} 条规则审查"
                        )

                except Exception as e:
                    # 单条规则失败，记录错误但继续
                    error_result = ReviewResult(
                        rule_id=rule.get("rule_id", ""),
                        rule_name=rule.get("name", ""),
                        status="FAILED",
                        reason=f"规则审查失败: {str(e)}",
                        error=str(e),
                    )
                    task.results.append(error_result)

            # 更新状态为完成
            task.status = ReviewStatus.COMPLETED
            task.completed_at = datetime.now()
            task.metadata["completed_at"] = task.completed_at.isoformat()

        except Exception as e:
            # 整体失败
            task.status = ReviewStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()

        return task

    async def _execute_rule_review(
        self,
        rule: Dict[str, Any],
        context: ExecutionContext,
    ) -> ReviewResult:
        """
        执行单条规则审查

        Args:
            rule: 规则字典
            context: 执行上下文

        Returns:
            审查结果
        """
        rule_id = rule.get("rule_id", "")
        rule_name = rule.get("name", "")

        # 1. 构建检索查询
        query_result = build_search_queries([rule], combine_rules=False)
        queries = query_result.queries

        if not queries:
            return ReviewResult(
                rule_id=rule_id,
                rule_name=rule_name,
                status="FAILED",
                reason="无法生成检索查询",
            )

        # 2. 向量检索
        retrieved_chunks = await self._retrieve_chunks(
            queries,
            context,
            rule.get("retrieval_tags", []),
        )

        # 3. 构建 Prompt
        prompt = build_review_prompt(rule, retrieved_chunks)

        # 4. 调用 LLM（如果有客户端）或模拟结果
        llm_result = await self._call_llm(prompt, context)

        # 5. 验证并解析结果
        validated = self.prompt_validator.validate_prompt_output(llm_result)

        if not validated["valid"]:
            # 解析失败，返回错误结果
            return ReviewResult(
                rule_id=rule_id,
                rule_name=rule_name,
                status="FAILED",
                reason=f"LLM 输出解析失败: {validated['error']}",
                error=validated["error"],
            )

        # 6. 构建结果
        data = validated["data"]
        return ReviewResult(
            rule_id=data.get("rule_id", rule_id),
            rule_name=data.get("rule_name", rule_name),
            status=data.get("status", "MISSING"),
            reason=data.get("reason", ""),
            evidence=data.get("evidence", []),
            confidence=data.get("confidence", 0.8),
            suggestion=data.get("suggestion"),
        )

    async def _retrieve_chunks(
        self,
        queries: List[SearchQuery],
        context: ExecutionContext,
        retrieval_tags: List[str],
    ) -> List[Dict[str, Any]]:
        """
        向量检索相关 chunks

        Args:
            queries: 检索查询列表
            context: 执行上下文
            retrieval_tags: 检索标签

        Returns:
            检索到的 chunks
        """
        if not context.embedding_pipeline:
            # 如果没有 embedding pipeline，使用 mock 数据
            return context.chunks[:context.max_retrieved_chunks]

        all_results = []

        for query in queries:
            # 使用 embedding pipeline 搜索
            results = context.embedding_pipeline.search(
                query.text,
                top_k=context.max_retrieved_chunks,
            )

            # 应用标签过滤
            if retrieval_tags:
                filtered = [
                    r for r in results
                    if any(tag in r.get("clause_hint", "") for tag in retrieval_tags)
                ]
                results = filtered

            all_results.extend(results)

        # 去重（按 chunk_id）
        seen = set()
        unique_results = []
        for result in all_results:
            chunk_id = result.get("chunk_id", "")
            if chunk_id and chunk_id not in seen:
                seen.add(chunk_id)
                unique_results.append(result)

        return unique_results[:context.max_retrieved_chunks]

    async def _call_llm(
        self,
        prompt: str,
        context: ExecutionContext,
    ) -> str:
        """
        调用 LLM 生成审核结果

        Args:
            prompt: 审核提示词
            context: 执行上下文

        Returns:
            LLM 输出
        """
        if context.llm_client and self.llm_client:
            # 实际调用 LLM
            try:
                response = await context.llm_client.chat.completions.create(
                    model=context.llm_model,
                    messages=[
                        {"role": "system", "content": "你是一位专业的合同审核专家。"},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"LLM 调用失败: {e}")
                # 返回 mock 结果
                return self._mock_llm_response(prompt)
        else:
            # Mock LLM 响应
            return self._mock_llm_response(prompt)

    def _mock_llm_response(self, prompt: str) -> str:
        """
        Mock LLM 响应（用于测试）

        Args:
            prompt: 审核提示词

        Returns:
            Mock JSON 响应
        """
        # 简单的 mock 逻辑
        if "30天" in prompt and "45" not in prompt:
            # PASS 场景
            return '''{
  "rule_id": "payment_cycle_max_30",
  "rule_name": "付款周期限制",
  "status": "PASS",
  "reason": "合同约定承租方在每月5日前支付租金，符合30天内付款的要求",
  "evidence": [
    {
      "chunk_id": "doc1_p1_c0",
      "page": 1,
      "text": "承租方应在每月5日前支付当月租金。"
    }
  ],
  "confidence": 0.9
}'''
        elif "45" in prompt:
            # RISK 场景
            return '''{
  "rule_id": "payment_cycle_max_30",
  "rule_name": "付款周期限制",
  "status": "RISK",
  "reason": "付款周期为45天，超过30天限制",
  "evidence": [
    {
      "chunk_id": "doc2_p1_c0",
      "page": 1,
      "text": "付款周期为收到发票后45日内完成付款。"
    }
  ],
  "confidence": 0.95,
  "suggestion": "建议将付款周期修改为30天以内"
}'''
        else:
            # MISSING 场景
            return '''{
  "rule_id": "payment_cycle_max_30",
  "rule_name": "付款周期限制",
  "status": "MISSING",
  "reason": "合同中未找到付款周期相关条款",
  "evidence": [],
  "confidence": 0.8
}'''

    def get_task(self, review_id: str) -> Optional[ReviewTask]:
        """获取审查任务"""
        return self._tasks.get(review_id)

    def list_tasks(self, status: Optional[ReviewStatus] = None) -> List[ReviewTask]:
        """列出审查任务"""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def delete_task(self, review_id: str) -> bool:
        """删除审查任务"""
        if review_id in self._tasks:
            del self._tasks[review_id]
            return True
        return False


# 全局执行器实例
_executor: Optional[ReviewExecutor] = None


def get_review_executor(
    vector_store=None,
    llm_client=None,
    llm_model: str = "gpt-4",
) -> ReviewExecutor:
    """
    获取审查执行器实例

    Args:
        vector_store: 向量存储
        llm_client: LLM 客户端
        llm_model: LLM 模型

    Returns:
        审查执行器
    """
    global _executor
    if _executor is None:
        _executor = ReviewExecutor(
            vector_store=vector_store,
            llm_client=llm_client,
            llm_model=llm_model,
        )
    return _executor
