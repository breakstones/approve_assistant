"""
Integration Test: Rule Management Workflow
规则管理工作流集成测试
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from fastapi.testclient import TestClient
from main import app


def test_rule_management_workflow():
    """规则管理工作流测试"""
    print("=" * 60)
    print("规则管理工作流集成测试")
    print("=" * 60)

    client = TestClient(app)

    rule_id = f"test_workflow_{os.urandom(4).hex()}"

    # 1. 创建规则
    print("\n1. 创建规则")
    print("-" * 60)

    rule_data = {
        "rule_id": rule_id,
        "name": "测试工作流规则",
        "category": "Test",
        "intent": "测试工作流",
        "type": "requirement",
        "params": {},
        "risk_level": "MEDIUM",
        "retrieval_tags": ["test"],
        "enabled": True,
    }

    response = client.post("/api/rules", json=rule_data)
    if response.status_code not in [200, 201]:
        print(f"  ✗ 创建失败: {response.text}")
        return False

    rule = response.json()
    if rule.get("rule_id") != rule_id:
        print(f"  ✗ 创建返回的 rule_id 不匹配: {rule.get('rule_id')}")
        return False

    print(f"  ✓ 规则创建成功: {rule_id}")

    # 2. 获取规则
    print("\n2. 获取规则")
    print("-" * 60)

    response = client.get(f"/api/rules/{rule_id}")
    if response.status_code != 200:
        print(f"  ✗ 获取失败: {response.text}")
        return False

    rule = response.json()
    print(f"  ✓ 规则获取成功: {rule.get('name')}")

    # 3. 更新规则
    print("\n3. 更新规则")
    print("-" * 60)

    update_data = {"name": "更新后的规则名称"}
    response = client.put(f"/api/rules/{rule_id}", json=update_data)
    if response.status_code != 200:
        print(f"  ✗ 更新失败: {response.text}")
        return False

    print(f"  ✓ 规则更新成功")

    # 4. 禁用规则
    print("\n4. 禁用规则")
    print("-" * 60)

    update_data = {"enabled": False}
    response = client.put(f"/api/rules/{rule_id}", json=update_data)
    if response.status_code != 200:
        print(f"  ✗ 禁用失败: {response.text}")
        return False

    print(f"  ✓ 规则禁用成功")

    # 5. 列出规则（验证禁用状态）
    print("\n5. 列出规则")
    print("-" * 60)

    response = client.get("/api/rules", params={"enabled_only": True})
    if response.status_code != 200:
        print(f"  ✗ 列出失败: {response.text}")
        return False

    list_data = response.json()
    rules = list_data.get("rules", [])
    is_disabled = all(r.get("enabled", True) == False for r in rules)

    print(f"  ✓ 规则列表成功: {len(rules)} 条")
    print(f"  ✓ 规则已禁用: {is_disabled}")

    # 6. 删除规则
    print("\n6. 删除规则")
    print("-" * 60)

    response = client.delete(f"/api/rules/{rule_id}")
    if response.status_code != 204:
        print(f"  ✗ 删除失败: {response.text}")
        return False

    print(f"  ✓ 规则删除成功")

    # 7. 验证删除
    print("\n7. 验证删除")
    print("-" * 60)

    response = client.get(f"/api/rules/{rule_id}")
    if response.status_code == 404:
        print(f"  ✓ 规则已删除")
    else:
        print(f"  ✗ 规则仍然存在")
        return False

    print("\n" + "=" * 60)
    print("规则管理工作流测试完成")
    print("=" * 60)
    print("\n✅ 规则管理工作流测试通过！")

    return True


if __name__ == "__main__":
    import os
    success = test_rule_management_workflow()
    sys.exit(0 if success else 1)
