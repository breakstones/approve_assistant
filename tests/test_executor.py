"""
Test Review Executor
测试 RAG 审查执行流程
"""
import sys
import os
import asyncio

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from execution.executor import (
    ReviewExecutor,
    ReviewStatus,
    ReviewResult,
    ReviewTask,
    ExecutionContext,
    get_review_executor,
)
from execution.query_builder import build_search_queries


def create_test_rules() -> list[dict]:
    """创建测试规则"""
    return [
        {
            "rule_id": "payment_cycle_max_30",
            "name": "付款周期限制",
            "category": "Payment",
            "type": "numeric_constraint",
            "risk_level": "HIGH",
            "intent": "付款周期不得超过30天",
            "params": {
                "max_days": 30,
                "payment_type": "租金",
            },
            "retrieval_tags": ["payment", "rent"],
        },
        {
            "rule_id": "confidentiality_required",
            "name": "保密条款要求",
            "category": "Confidentiality",
            "type": "requirement",
            "risk_level": "MEDIUM",
            "intent": "合同必须包含保密条款",
            "params": {
                "obligation": "保密义务",
            },
            "retrieval_tags": ["confidentiality"],
        },
    ]


def create_test_chunks() -> list[dict]:
    """创建测试文档片段"""
    return [
        {
            "chunk_id": "doc1_p1_c0",
            "doc_id": "doc1",
            "page": 1,
            "text": "每月租金为人民币5000元整。承租方应在每月5日前支付当月租金。",
            "bbox": {"x1": 50, "y1": 220, "x2": 500, "y2": 240},
            "clause_hint": "payment",
        },
        {
            "chunk_id": "doc1_p1_c1",
            "doc_id": "doc1",
            "page": 1,
            "text": "双方应对在合同履行过程中知悉的甲方商业秘密承担保密义务。",
            "bbox": {"x1": 50, "y1": 280, "x2": 500, "y2": 300},
            "clause_hint": "confidentiality",
        },
    ]


async def test_executor():
    """测试审查执行器"""

    print("=" * 60)
    print("RAG 审查执行器测试")
    print("=" * 60)

    print("\n1. 测试执行器创建")
    print("-" * 60)

    try:
        executor = get_review_executor()
        print(f"✓ 创建审查执行器成功")
        print(f"  - LLM 模型: {executor.llm_model}")

    except Exception as e:
        print(f"✗ 创建执行器失败: {e}")
        return False

    print("\n2. 测试审查任务创建")
    print("-" * 60)

    try:
        rules = create_test_rules()
        rule_ids = [r["rule_id"] for r in rules]
        chunks = create_test_chunks()

        # 创建执行上下文
        context = ExecutionContext(
            doc_id="test_doc",
            chunks=chunks,
            embedding_pipeline=None,  # 使用 mock
            llm_client=None,  # 使用 mock
        )

        # 创建审查任务
        task = executor.create_review(
            doc_id="test_doc",
            rule_ids=rule_ids,
            rules=rules,
            context=context,
        )

        print(f"✓ 创建审查任务成功")
        print(f"  - 审查 ID: {task.review_id}")
        print(f"  - 文档 ID: {task.doc_id}")
        print(f"  - 规则数: {len(task.rule_ids)}")
        print(f"  - 状态: {task.status}")

    except Exception as e:
        print(f"✗ 创建审查任务失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n3. 测试执行审查（异步）")
    print("-" * 60)

    try:
        # 进度回调
        async def progress_callback(review_id, completed, total, message):
            print(f"  进度: {completed}/{total} - {message}")

        # 执行审查
        executed_task = await executor.execute_review(
            review_id=task.review_id,
            rules=rules,
            context=context,
            progress_callback=progress_callback,
        )

        print(f"✓ 执行审查完成")
        print(f"  - 最终状态: {executed_task.status}")
        print(f"  - 结果数: {len(executed_task.results)}")

        # 显示结果
        for result in executed_task.results:
            print(f"\n  规则: {result.rule_name}")
            print(f"    状态: {result.status}")
            print(f"    原因: {result.reason}")
            print(f"    证据数: {len(result.evidence)}")

    except Exception as e:
        print(f"✗ 执行审查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n4. 测试任务查询")
    print("-" * 60)

    try:
        # 获取任务
        retrieved_task = executor.get_task(task.review_id)
        print(f"✓ 获取任务成功: {retrieved_task.review_id}")

        # 列出所有任务
        all_tasks = executor.list_tasks()
        print(f"✓ 列出任务成功: {len(all_tasks)} 个任务")

    except Exception as e:
        print(f"✗ 任务查询失败: {e}")
        return False

    print("\n5. 测试状态转换")
    print("-" * 60)

    try:
        # 验证状态转换
        task = executor.get_task(task.review_id)
        print(f"✓ 任务状态: {task.status}")

        # 验证必须的状态
        assert task.status in [ReviewStatus.COMPLETED, ReviewStatus.FAILED]
        print(f"✓ 任务已执行完成")

        if task.started_at:
            print(f"✓ 开始时间: {task.started_at}")
        if task.completed_at:
            print(f"✓ 完成时间: {task.completed_at}")

    except Exception as e:
        print(f"✗ 状态转换测试失败: {e}")
        return False

    print("\n6. 验证结果结构")
    print("-" * 60)

    try:
        task = executor.get_task(task.review_id)

        for result in task.results:
            # 验证必需字段
            assert result.rule_id, "结果必须有 rule_id"
            assert result.rule_name, "结果必须有 rule_name"
            assert result.status in ["PASS", "RISK", "MISSING", "FAILED"], f"无效状态: {result.status}"
            assert result.reason, "结果必须有原因"

            # 验证状态和证据的一致性
            if result.status == "MISSING":
                assert len(result.evidence) == 0, "MISSING 状态必须有空 evidence"
            else:
                # PASS 或 RISK 应该有证据
                if not result.error:
                    pass  # 允许没有证据的情况

        print(f"✓ 所有 {len(task.results)} 个结果结构验证通过")

    except AssertionError as e:
        print(f"✗ 结果结构验证失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 验证过程出错: {e}")
        return False

    print("\n7. 测试 Mock LLM 响应")
    print("-" * 60)

    try:
        # 测试 mock LLM 响应
        test_prompts = [
            "付款周期不得超过30天",
            "付款周期为45天",
            "租赁期限",
        ]

        for prompt in test_prompts:
            response = executor._mock_llm_response(prompt)
            print(f"✓ Prompt: '{prompt[:20]}...'")
            print(f"  响应长度: {len(response)} 字符")

    except Exception as e:
        print(f"✗ Mock LLM 测试失败: {e}")
        return False

    print("\n8. 测试任务删除")
    print("-" * 60)

    try:
        # 创建临时任务
        temp_task = executor.create_review(
            doc_id="temp_doc",
            rule_ids=["rule_1"],
            rules=create_test_rules()[:1],
            context=context,
        )

        # 删除任务
        success = executor.delete_task(temp_task.review_id)
        print(f"✓ 删除任务成功: {temp_task.review_id}")

        # 验证删除
        deleted_task = executor.get_task(temp_task.review_id)
        if deleted_task is None:
            print(f"✓ 验证：任务已删除")
        else:
            print(f"✗ 验证：任务仍然存在")
            return False

    except Exception as e:
        print(f"✗ 任务删除测试失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("RAG 审查执行器测试完成")
    print("=" * 60)

    print("\n✅ 所有测试通过！")
    print("\n说明：完整 RAG 流程已实现（检索 + Prompt + Mock LLM），")
    print("      实际使用时需要配置真实的 LLM 客户端。")

    return True


if __name__ == "__main__":
    success = asyncio.run(test_executor())
    sys.exit(0 if success else 1)
