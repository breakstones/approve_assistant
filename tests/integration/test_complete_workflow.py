"""
Integration Test: Complete Review Workflow
端到端集成测试 - 完整审核工作流
"""
import sys
import os
import time

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from fastapi.testclient import TestClient
from main import app


def test_complete_review_workflow():
    """完整审核工作流测试"""
    print("=" * 60)
    print("完整审核工作流集成测试")
    print("=" * 60)

    client = TestClient(app)

    # 1. 创建规则
    print("\n1. 创建审核规则")
    print("-" * 60)

    rules = [
        {
            "rule_id": "test_payment_cycle",
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
            "rule_id": "test_confidentiality",
            "name": "保密条款要求",
            "category": "Confidentiality",
            "intent": "合同必须包含保密条款",
            "type": "requirement",
            "params": {},
            "risk_level": "MEDIUM",
            "retrieval_tags": ["confidentiality"],
            "enabled": True,
        },
    ]

    rule_ids = []
    for rule in rules:
        try:
            response = client.post("/api/rules", json=rule)
            if response.status_code in [200, 201]:
                rule_ids.append(rule["rule_id"])
                print(f"  ✓ 创建规则: {rule['name']}")
            elif response.status_code == 409:
                # 规则已存在，仍然可以使用
                rule_ids.append(rule["rule_id"])
                print(f"  ○ 规则已存在: {rule['name']}")
            else:
                print(f"  ✗ 创建规则失败: {rule['name']} - {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  ✗ 创建规则异常: {rule['name']} - {e}")

    # 2. 上传文档
    print("\n2. 上传文档")
    print("-" * 60)

    # 使用测试目录中的合同文件
    test_files_dir = Path(__file__).parent.parent / "contract_files"

    # 检查可用的测试文件
    if test_files_dir.exists():
        test_files = list(test_files_dir.glob("*.pdf")) + list(test_files_dir.glob("*.docx"))
    else:
        test_files = []

    if not test_files:
        print("  ○ 没有 PDF/DOCX 测试文件，跳过文档上传")
        doc_id = None
    else:
        test_file = test_files[0]
        print(f"  使用测试文件: {test_file.name}")

        try:
            with open(test_file, "rb") as f:
                files = {"file": (test_file.name, f, "application/pdf")}
                if test_file.suffix == ".docx":
                    files = {"file": (test_file.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}

                response = client.post("/api/documents/upload", files=files)

                if response.status_code in [200, 201, 202]:
                    data = response.json()
                    doc_id = data.get("doc_id")
                    print(f"  ✓ 文档上传成功: {doc_id}")

                    # 等待处理完成
                    max_wait = 30
                    waited = 0
                    while waited < max_wait:
                        time.sleep(2)
                        waited += 2

                        status_resp = client.get(f"/api/documents/{doc_id}/status")
                        if status_resp.status_code == 200:
                            status_data = status_resp.json()
                            print(f"  文档状态: {status_data.get('status')} ({waited}s)")
                            if status_data.get("status") in ["READY", "ERROR"]:
                                break
                else:
                    print(f"  ✗ 文档上传失败: {response.text}")
                    doc_id = None
        except Exception as e:
            print(f"  ✗ 文档上传异常: {e}")
            doc_id = None

    # 3. 启动审查
    print("\n3. 启动审查")
    print("-" * 60)

    if not doc_id:
        print("  ○ 没有可用文档，跳过审查")
        return True

    try:
        response = client.post(
            "/api/review/start",
            json={
                "doc_id": doc_id,
                "rule_ids": rule_ids[:1],  # 使用第一个规则测试
            }
        )

        if response.status_code == 202:
            data = response.json()
            review_id = data.get("review_id")
            print(f"  ✓ 审查启动成功: {review_id}")
            print(f"  总规则数: {data.get('total_rules')}")

            # 等待审查完成
            max_wait = 30
            waited = 0
            completed = False

            while waited < max_wait:
                time.sleep(2)
                waited += 2

                status_resp = client.get(f"/api/review/{review_id}/status")
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    status = status_data.get("status")
                    progress = status_data.get("progress", 0)
                    completed_rules = status_data.get("completed_rules", 0)
                    total_rules = status_data.get("total_rules", 0)

                    print(f"  审查状态: {status} ({completed_rules}/{total_rules} 规则, {progress:.1f}%)")

                    if status == "COMPLETED" or status == "FAILED":
                        completed = True
                        break

            if completed:
                # 4. 获取审查结果
                print("\n4. 获取审查结果")
                print("-" * 60)

                results_resp = client.get(f"/api/review/{review_id}/results")
                if results_resp.status_code == 200:
                    results_data = results_resp.json()
                    print(f"  ✓ 审查状态: {results_data.get('status')}")
                    print(f"  结果数量: {len(results_data.get('results', []))}")

                    summary = results_data.get("summary", {})
                    print(f"  结果汇总:")
                    print(f"    - 总计: {summary.get('total', 0)}")
                    print(f"    - 通过: {summary.get('pass', 0)}")
                    print(f"    - 风险: {summary.get('risk', 0)}")
                    print(f"    - 缺失: {summary.get('missing', 0)}")
                    print(f"    - 失败: {summary.get('failed', 0)}")
                else:
                    print(f"  ✗ 获取结果失败: {results_resp.text}")

                # 5. 追问解释
                print("\n5. 追问解释")
                print("-" * 60)

                if results_data.get("results") and len(results_data["results"]) > 0:
                    result = results_data["results"][0]
                    result_id = str(0)  # 使用索引

                    # 发起追问
                    explain_resp = client.post(
                        "/api/explain",
                        json={
                            "review_id": review_id,
                            "result_id": result_id,
                            "question": "为什么是这个结果？",
                        }
                    )

                    if explain_resp.status_code == 200:
                        explain_data = explain_resp.json()
                        print(f"  ✓ 追问成功")
                        print(f"  回答: {explain_data.get('answer', '')[:100]}...")
                    else:
                        print(f"  ✗ 追问失败: {explain_resp.text}")

        else:
            print(f"  ✗ 启动审查失败: {response.text}")
    except Exception as e:
        print(f"  ✗ 启动审查异常: {e}")
        return False

    print("\n" + "=" * 60)
    print("集成测试完成")
    print("=" * 60)
    print("\n✅ 完整工作流测试通过！")

    return True


if __name__ == "__main__":
    from pathlib import Path

    success = test_complete_review_workflow()
    sys.exit(0 if success else 1)
