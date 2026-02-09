"""
Test Explain API
测试追问与解释 API
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from main import app


def test_explain_api():
    """测试解释 API"""

    print("=" * 60)
    print("解释 API 测试")
    print("=" * 60)

    # 创建测试客户端
    client = TestClient(app)

    print("\n1. 测试根端点")
    print("-" * 60)

    try:
        response = client.get("/")
        print(f"✓ 根端点响应: {response.status_code}")
        data = response.json()
        print(f"  可用端点: {data.get('endpoints', {})}")
        assert "/api/explain" in data.get('endpoints', {}).values() or "explain" in str(data.get('endpoints', {}))
        print(f"  ✓ explain 端点已注册")
    except Exception as e:
        print(f"✗ 根端点测试失败: {e}")
        return False

    print("\n2. 初始化测试数据")
    print("-" * 60)

    try:
        from config.database import get_database
        from config.rule_service import RuleService
        from config.document_service import get_document_service as get_doc_service
        from execution.executor import get_review_executor as get_executor

        db = get_database()
        rule_service = RuleService()
        doc_service = get_doc_service()
        executor = get_executor()

        # 创建测试规则
        try:
            rule_service.create({
                "rule_id": "test_explain_rule",
                "name": "测试解释规则",
                "category": "Test",
                "intent": "测试规则意图",
                "type": "requirement",
                "params": {},
                "risk_level": "MEDIUM",
                "retrieval_tags": ["test"],
                "enabled": True,
            })
            print(f"  ✓ 创建测试规则")
        except:
            print(f"  ○ 规则已存在")

        # 获取或创建测试文档
        docs = doc_service.list(limit=1)
        if not docs:
            try:
                doc = doc_service.create(
                    filename="test_explain.pdf",
                    file_type="pdf",
                    file_size=12345,
                )
                print(f"  ✓ 创建测试文档: {doc['doc_id']}")
                doc_id = doc['doc_id']
            except Exception as e:
                print(f"  ○ 创建文档失败: {e}")
                return False
        else:
            doc_id = docs[0]["doc_id"]
            print(f"  ○ 使用现有文档: {doc_id}")

        # 创建测试审查任务
        from execution.executor import ReviewTask, ReviewStatus, ReviewResult
        import uuid

        review_id = f"test_review_explain_{uuid.uuid4().hex[:8]}"

        # 创建测试结果（使用简单的字典结构）
        # result_id 使用索引格式 "0" 表示第一个结果
        result_id = "0"
        test_result = ReviewResult(
            rule_id="test_explain_rule",
            rule_name="测试解释规则",
            status="PASS",
            reason="测试通过原因",
            evidence=[
                {
                    "chunk_id": f"{doc_id}_p1_c0",
                    "quote": "测试引用文本",
                    "page": 1,
                    "bbox": {"x1": 0, "y1": 0, "x2": 100, "y2": 20},
                }
            ],
        )

        task = ReviewTask(
            review_id=review_id,
            doc_id=doc_id,
            rule_ids=["test_explain_rule"],
            status=ReviewStatus.COMPLETED,
            results=[test_result],
        )

        executor._tasks[review_id] = task
        print(f"  ✓ 创建测试审查任务: {review_id}")
        print(f"  ✓ 测试结果 ID: {result_id}")

    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n3. 测试创建解释（首次提问）")
    print("-" * 60)

    try:
        response = client.post(
            "/api/explain",
            json={
                "review_id": review_id,
                "result_id": result_id,  # 使用 result_id 变量
                "question": "为什么判定为通过？",
            }
        )

        print(f"✓ 创建解释响应: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            session_id = data.get("session_id")
            print(f"  会话 ID: {session_id}")
            print(f"  回答: {data.get('answer', '')[:100]}...")
            print(f"  推理: {data.get('reasoning', '')[:100]}...")
            print(f"  证据引用数: {len(data.get('evidence_references', []))}")
            print(f"  置信度: {data.get('confidence')}")
            print(f"  限制: {data.get('limitations')}")
        else:
            print(f"  错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 创建解释失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n4. 测试多轮对话")
    print("-" * 60)

    try:
        response = client.post(
            "/api/explain",
            json={
                "review_id": review_id,
                "result_id": result_id,  # 使用 result_id 变量
                "question": "具体是哪一条？",
                "session_id": session_id,
            }
        )

        print(f"✓ 追问响应: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  会话 ID: {data.get('session_id')} (应与之前相同)")
            print(f"  回答: {data.get('answer', '')[:100]}...")
            assert data.get("session_id") == session_id
            print(f"  ✓ 会话 ID 保持一致")
        else:
            print(f"  错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 追问失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n5. 测试获取对话历史")
    print("-" * 60)

    try:
        response = client.get(f"/api/explain/{session_id}/history")

        print(f"✓ 对话历史响应: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])
            print(f"  会话 ID: {data.get('session_id')}")
            print(f"  消息总数: {len(messages)}")
            for i, msg in enumerate(messages):
                print(f"    {i+1}. [{msg.get('role')}] {msg.get('content', '')[:50]}...")
            assert len(messages) == 4  # 2 user + 2 assistant
            print(f"  ✓ 消息数量正确")
        else:
            print(f"  错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 获取对话历史失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n6. 测试列会话")
    print("-" * 60)

    try:
        response = client.get("/api/explain/sessions")

        print(f"✓ 列会话响应: {response.status_code}")

        if response.status_code == 200:
            sessions = response.json()
            print(f"  会话总数: {len(sessions)}")
            if sessions:
                for s in sessions[:3]:
                    print(f"    - {s.get('session_id')}: {s.get('message_count')} 条消息")
        else:
            print(f"  错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 列会话失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n7. 测试删除会话")
    print("-" * 60)

    try:
        response = client.delete(f"/api/explain/{session_id}")

        print(f"✓ 删除会话响应: {response.status_code}")

        if response.status_code == 204:
            print(f"  ✓ 会话已删除")

            # 验证删除后无法获取历史
            response2 = client.get(f"/api/explain/{session_id}/history")
            if response2.status_code == 404:
                print(f"  ✓ 确认会话已不存在")
            else:
                print(f"  ○ 验证响应: {response2.status_code}")
        else:
            print(f"  错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 删除会话失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("解释 API 测试完成")
    print("=" * 60)

    print("\n✅ 所有测试通过！")

    return True


if __name__ == "__main__":
    success = test_explain_api()
    sys.exit(0 if success else 1)
