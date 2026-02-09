"""
Integration Test: Explainability Workflow
追问解释工作流集成测试
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from fastapi.testclient import TestClient
from main import app


def test_explainability_workflow():
    """追问解释工作流测试"""
    print("=" * 60)
    print("追问解释工作流集成测试")
    print("=" * 60)

    client = TestClient(app)

    # 1. 创建测试数据和审查任务
    print("\n1. 准备测试数据")
    print("-" * 60)

    # 创建规则
    rule_id = f"test_explain_{os.urandom(4).hex()}"
    try:
        client.post("/api/rules", json={
            "rule_id": rule_id,
            "name": "追问测试规则",
            "category": "Test",
            "intent": "测试追问功能",
            "type": "requirement",
            "params": {},
            "risk_level": "MEDIUM",
            "retrieval_tags": ["test"],
            "enabled": True,
        })
        print(f"  ✓ 创建规则: {rule_id}")
    except:
        print(f"  ○ 规则可能已存在")

    # 创建文档
    try:
        from config.document_service import get_document_service as get_doc_service
        from config.database import get_database

        get_database()
        doc_service = get_doc_service()

        doc = doc_service.create(
            filename="explain_test.pdf",
            file_type="pdf",
            file_size=12345,
        )
        doc_id = doc["doc_id"]
        print(f"  ✓ 创建文档: {doc_id}")
    except Exception as e:
        print(f"  ○ 使用现有文档或创建失败: {e}")
        docs = client.get("/api/documents").json()
        if docs:
            doc_id = docs[0]["doc_id"]
        else:
            print("  ✗ 没有可用文档")
            return False

    # 创建审查任务
    from execution.executor import get_review_executor as get_executor
    from execution.executor import ReviewTask, ReviewStatus, ReviewResult

    executor = get_executor()

    review_id = f"test_explain_review_{os.urandom(4).hex()}"

    task = ReviewTask(
        review_id=review_id,
        doc_id=doc_id,
        rule_ids=[rule_id],
        status=ReviewStatus.COMPLETED,
    )

    # 添加测试结果
    result = ReviewResult(
        rule_id=rule_id,
        rule_name="追问测试规则",
        status="PASS",
        reason="测试通过原因",
        evidence=[
            {
                "chunk_id": f"{doc_id}_p1_c0",
                "quote": "测试引用文本",
                "page": 1,
                "bbox": {"x1": 0, "y1": 0, "x2": 100, "y2": 20},
                "confidence": 0.9,
            }
        ],
    )

    task.results.append(result)
    executor._tasks[review_id] = task

    print(f"  ✓ 创建审查任务: {review_id}")

    # 2. 发起追问
    print("\n2. 发起追问")
    print("-" * 60)

    response = client.post(
        "/api/explain",
        json={
            "review_id": review_id,
            "result_id": "0",
            "question": "为什么判定为通过？",
        }
    )

    if response.status_code != 200:
        print(f"  ✗ 追问失败: {response.text}")
        return False

    data = response.json()
    session_id = data.get("session_id")
    print(f"  ✓ 追问成功: {session_id}")
    print(f"  回答: {data.get('answer', '')[:100]}...")

    # 3. 继续追问
    print("\n3. 继续追问")
    print("-" * 60)

    response = client.post(
        "/api/explain",
        json={
            "review_id": review_id,
            "result_id": "0",
            "question": "具体在哪一页？",
            "session_id": session_id,
        }
    )

    if response.status_code != 200:
        print(f"  ✗ 追问失败: {response.text}")
        return False

    data = response.json()
    print(f"  ✓ 追问成功")
    print(f"  会话ID一致: {data.get('session_id') == session_id}")

    # 4. 获取对话历史
    print("\n4. 获取对话历史")
    print("-" * 60)

    response = client.get(f"/api/explain/{session_id}/history")

    if response.status_code != 200:
        print(f"  ✗ 获取历史失败: {response.text}")
        return False

    history = response.json()
    messages = history.get("messages", [])
    print(f"  ✓ 获取历史成功: {len(messages)} 条消息")

    for i, msg in enumerate(messages):
        role = msg.get("role")
        content_preview = msg.get("content", "")[:50]
        print(f"    {i+1}. [{role}] {content_preview}...")

    # 验证消息数量（应该是4条：2个用户 + 2个助手）
    if len(messages) >= 4:
        print(f"  ✓ 对话历史完整")
    else:
        print(f"  ⚠️  消息数量不足: {len(messages)}/4")

    # 5. 列出会话
    print("\n5. 列出会话")
    print("-" * 60)

    response = client.get("/api/explain/sessions")

    if response.status_code != 200:
        print(f"  ✗ 列会话失败: {response.text}")
        return False

    sessions = response.json()
    print(f"  ✓ 列会话成功: {len(sessions)} 个会话")

    # 6. 删除会话
    print("\n6. 删除会话")
    print("-" * 60)

    response = client.delete(f"/api/explain/{session_id}")

    if response.status_code != 204:
        print(f"  ✗ 删除会话失败: {response.text}")
        return False

    print(f"  ✓ 会话删除成功")

    # 7. 验证删除
    print("\n7. 验证删除")
    print("-" * 60)

    response = client.get(f"/api/explain/{session_id}/history")

    if response.status_code == 404:
        print(f"  ✓ 会话已删除")
    else:
        print(f"  ✗ 会话仍然存在")
        return False

    print("\n" + "=" * 60)
    print("追问解释工作流测试完成")
    print("=" * 60)
    print("\n✅ 追问解释工作流测试通过！")

    return True


if __name__ == "__main__":
    success = test_explainability_workflow()
    sys.exit(0 if success else 1)
