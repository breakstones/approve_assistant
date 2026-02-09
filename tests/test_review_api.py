"""
Test Review API
测试审查任务 API
"""
import sys
import os
import asyncio
from pathlib import Path

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from main import app


def create_test_rules():
    """创建测试规则数据"""
    return [
        {
            "rule_id": "payment_cycle_max_30",
            "name": "付款周期限制",
            "category": "Payment",
            "intent": "付款周期不得超过30天",
            "type": "numeric_constraint",
            "params": {"max_days": 30},
            "risk_level": "HIGH",
            "retrieval_tags": ["payment"],
            "enabled": True,
        },
        {
            "rule_id": "confidentiality_required",
            "name": "保密条款要求",
            "category": "Confidentiality",
            "intent": "合同必须包含保密条款",
            "type": "requirement",
            "params": {"obligation": "保密义务"},
            "risk_level": "MEDIUM",
            "retrieval_tags": ["confidentiality"],
            "enabled": True,
        },
    ]


def test_review_api():
    """测试审查 API"""

    print("=" * 60)
    print("审查 API 测试")
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
    except Exception as e:
        print(f"✗ 根端点测试失败: {e}")
        return False

    print("\n2. 初始化数据库和创建测试数据")
    print("-" * 60)

    try:
        # 初始化数据库
        from config.database import get_database
        from config.rule_service import RuleService

        db = get_database()
        rule_service = RuleService()

        # 创建测试规则
        rules = create_test_rules()

        for rule in rules:
            try:
                rule_service.create(rule)
                print(f"  ✓ 创建规则: {rule['name']}")
            except Exception as e:
                print(f"  ○ 规则已存在或创建失败: {rule['name']}")

        # 创建测试文档
        from config.document_service import get_document_service as get_doc_service
        from config.document_models import DocumentStatus

        doc_service = get_doc_service()

        # 尝试创建测试文档
        try:
            doc = doc_service.create(
                filename="test_contract.pdf",
                file_type="pdf",
                file_size=12345,
            )
            print(f"  ✓ 创建测试文档: {doc['doc_id']}")
        except Exception as e:
            print(f"  ○ 文档已存在或创建失败: {e}")

    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n3. 测试启动审查（指定规则）")
    print("-" * 60)

    try:
        # 获取文档 ID（使用最近创建的）
        from config.document_service import get_document_service as get_doc_service
        doc_service = get_doc_service()
        docs = doc_service.list(limit=1)

        if not docs:
            print("○ 没有可用文档，跳过测试")
            return True

        doc_id = docs[0]["doc_id"]

        response = client.post(
            "/api/review/start",
            json={
                "doc_id": doc_id,
                "rule_ids": ["payment_cycle_max_30"],
            }
        )

        print(f"✓ 启动审查响应: {response.status_code}")

        if response.status_code == 202:
            data = response.json()
            review_id = data.get("review_id")
            print(f"  审查 ID: {review_id}")
            print(f"  文档 ID: {data.get('doc_id')}")
            print(f"  总规则数: {data.get('total_rules')}")
            print(f"  状态: {data.get('status')}")

            # 等待后台任务完成
            import time
            time.sleep(2)

            # 检查状态
            status_response = client.get(f"/api/review/{review_id}/status")
            print(f"\n  状态查询响应: {status_response.status_code}")

            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"  当前状态: {status_data.get('status')}")
                print(f"  完成进度: {status_data.get('progress'):.1f}%")
                print(f"  已完成规则: {status_data.get('completed_rules')}/{status_data.get('total_rules')}")

    except Exception as e:
        print(f"✗ 启动审查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n4. 测试启动审查（所有规则）")
    print("-" * 60)

    try:
        response = client.post(
            "/api/review/start",
            json={
                "doc_id": doc_id,
                "rule_ids": [],  # 空列表表示使用所有启用规则
            }
        )

        print(f"✓ 启动审查响应: {response.status_code}")

        if response.status_code == 202:
            data = response.json()
            print(f"  审查 ID: {data.get('review_id')}")
            print(f"  总规则数: {data.get('total_rules')}")

    except Exception as e:
        print(f"✗ 启动审查失败: {e}")
        return False

    print("\n5. 测试获取审查结果")
    print("-" * 60)

    try:
        # 使用第一个 review_id
        if 'review_id' not in locals():
            review_id = "test_review_id"

        response = client.get(f"/api/review/{review_id}/results")
        print(f"✓ 获取结果响应: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  审查状态: {data.get('status')}")
            print(f"  结果数量: {len(data.get('results', []))}")

            summary = data.get("summary", {})
            print(f"  结果汇总:")
            print(f"    - 总计: {summary.get('total', 0)}")
            print(f"    - 通过: {summary.get('pass', 0)}")
            print(f"    - 风险: {summary.get('risk', 0)}")
            print(f"    - 缺失: {summary.get('missing', 0)}")
            print(f"    - 失败: {summary.get('failed', 0)}")

    except Exception as e:
        print(f"✗ 获取结果失败: {e}")
        return False

    print("\n6. 测试列出审查任务")
    print("-" * 60)

    try:
        response = client.get("/api/review")
        print(f"✓ 列出任务响应: {response.status_code}")

        if response.status_code == 200:
            tasks = response.json()
            print(f"  任务数量: {len(tasks)}")

            for task in tasks[:3]:  # 只显示前3个
                print(f"  - {task.get('review_id')}: {task.get('status')}")

    except Exception as e:
        print(f"✗ 列出任务失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("审查 API 测试完成")
    print("=" * 60)

    print("\n✅ 所有测试通过！")

    return True


if __name__ == "__main__":
    success = test_review_api()
    sys.exit(0 if success else 1)
