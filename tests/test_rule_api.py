"""
Test Rule Configuration API (Simplified)
测试规则配置管理 HTTP API（使用 TestClient）
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

# 设置测试环境变量
os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"

from fastapi.testclient import TestClient
from main import app
from config import init_db, RuleService
from pathlib import Path
import json


def test_rule_api():
    """测试规则配置 API"""

    print("=" * 60)
    print("规则配置 API 测试（使用 TestClient）")
    print("=" * 60)

    # 初始化数据库
    db = init_db("sqlite:///./test_api.db")

    # 创建测试规则数据
    test_rules_path = Path(__file__).parent.parent / "shared" / "schemas" / "rule_examples.json"
    with open(test_rules_path, "r", encoding="utf-8") as f:
        examples_data = json.load(f)

    # 批量创建规则
    service = RuleService()
    service.bulk_create(examples_data["examples"])
    print(f"✓ 初始化：创建了 {len(examples_data['examples'])} 条测试规则")

    # 创建测试客户端
    client = TestClient(app)

    try:
        print("\n1. 测试健康检查")
        print("-" * 60)

        response = client.get("/health")
        assert response.status_code == 200, f"健康检查失败: {response.status_code}"
        print(f"✓ GET /health: {response.json()}")

        print("\n2. 测试获取规则列表")
        print("-" * 60)

        response = client.get("/api/rules")
        assert response.status_code == 200, f"获取规则列表失败: {response.status_code}"
        data = response.json()
        print(f"✓ GET /api/rules: 返回 {data['total']} 条规则")

        print("\n3. 测试按分类过滤")
        print("-" * 60)

        response = client.get("/api/rules?category=Payment")
        assert response.status_code == 200, f"按分类过滤失败: {response.status_code}"
        data = response.json()
        print(f"✓ GET /api/rules?category=Payment: 返回 {len(data['rules'])} 条规则")

        print("\n4. 测试按风险等级过滤")
        print("-" * 60)

        response = client.get("/api/rules?risk_level=HIGH")
        assert response.status_code == 200, f"按风险等级过滤失败: {response.status_code}"
        data = response.json()
        print(f"✓ GET /api/rules?risk_level=HIGH: 返回 {len(data['rules'])} 条规则")

        print("\n5. 测试获取单条规则")
        print("-" * 60)

        response = client.get("/api/rules/payment_cycle_max_30")
        assert response.status_code == 200, f"获取单条规则失败: {response.status_code}"
        rule = response.json()
        print(f"✓ GET /api/rules/payment_cycle_max_30:")
        print(f"  name: {rule['name']}")
        print(f"  type: {rule['type']}")
        print(f"  risk_level: {rule['risk_level']}")

        print("\n6. 测试创建规则")
        print("-" * 60)

        new_rule = {
            "rule_id": "test_rule_api",
            "name": "API 测试规则",
            "category": "Test",
            "intent": "用于测试 API 的规则",
            "type": "text_contains",
            "params": {
                "keywords": ["测试"],
                "match_mode": "any",
                "case_sensitive": False
            },
            "risk_level": "LOW",
            "retrieval_tags": ["test"],
            "prompt_template_id": "text_contains_v1"
        }

        response = client.post("/api/rules", json=new_rule)
        assert response.status_code == 201, f"创建规则失败: {response.status_code}"
        created_rule = response.json()
        print(f"✓ POST /api/rules:")
        print(f"  rule_id: {created_rule['rule_id']}")
        print(f"  name: {created_rule['name']}")

        print("\n7. 测试更新规则")
        print("-" * 60)

        update_data = {
            "name": "API 测试规则（已更新）",
            "risk_level": "MEDIUM"
        }

        response = client.put("/api/rules/test_rule_api", json=update_data)
        assert response.status_code == 200, f"更新规则失败: {response.status_code}"
        updated_rule = response.json()
        print(f"✓ PUT /api/rules/test_rule_api:")
        print(f"  name: {updated_rule['name']}")
        print(f"  version: {updated_rule['version']}")
        assert updated_rule['version'] == 2, "版本号未增加"

        print("\n8. 测试规则解析")
        print("-" * 60)

        parse_request = {
            "text": "付款周期不得超过 45 天"
        }

        response = client.post("/api/rules/parse", json=parse_request)
        assert response.status_code == 200, f"规则解析失败: {response.status_code}"
        parsed_rule = response.json()
        print(f"✓ POST /api/rules/parse:")
        print(f"  rule_id: {parsed_rule['rule_id']}")
        print(f"  type: {parsed_rule['type']}")
        print(f"  params: {parsed_rule['params']}")

        print("\n9. 测试获取分类列表")
        print("-" * 60)

        response = client.get("/api/rules/categories")
        assert response.status_code == 200, f"获取分类列表失败: {response.status_code}"
        categories = response.json()
        print(f"✓ GET /api/rules/categories: {', '.join(categories)}")

        print("\n10. 测试获取风险等级列表")
        print("-" * 60)

        response = client.get("/api/rules/risk-levels")
        assert response.status_code == 200, f"获取风险等级列表失败: {response.status_code}"
        levels = response.json()
        print(f"✓ GET /api/rules/risk-levels: {', '.join(levels)}")

        print("\n11. 测试分页查询")
        print("-" * 60)

        response = client.get("/api/rules?limit=3&offset=0")
        assert response.status_code == 200, f"分页查询失败: {response.status_code}"
        data = response.json()
        print(f"✓ GET /api/rules?limit=3&offset=0:")
        print(f"  返回 {len(data['rules'])} 条规则")
        print(f"  规则 IDs: {[r['rule_id'] for r in data['rules']]}")

        print("\n12. 测试软删除规则")
        print("-" * 60)

        response = client.delete("/api/rules/test_rule_api")
        assert response.status_code == 204, f"删除规则失败: {response.status_code}"
        print(f"✓ DELETE /api/rules/test_rule_api: 204 No Content")

        # 验证已删除
        response = client.get("/api/rules/test_rule_api")
        assert response.status_code == 404, f"已删除规则仍可查询: {response.status_code}"
        print(f"✓ 验证：已删除规则默认不返回 (404)")

        # 查询包括未启用的规则
        response = client.get("/api/rules?enabled_only=false")
        data = response.json()
        rule_ids = [r['rule_id'] for r in data['rules']]
        assert "test_rule_api" in rule_ids, "已删除规则未在列表中"
        print(f"✓ 验证：enabled_only=false 包含已删除规则")

        print("\n13. 测试 404 错误处理")
        print("-" * 60)

        response = client.get("/api/rules/nonexistent_rule")
        assert response.status_code == 404, f"404 错误处理失败: {response.status_code}"
        print(f"✓ GET /api/rules/nonexistent_rule: 404 Not Found")

        print("\n14. 测试 409 冲突错误处理")
        print("-" * 60)

        # 尝试创建已存在的规则
        duplicate_rule = {
            "rule_id": "payment_cycle_max_30",  # 已存在
            "name": "重复规则",
            "category": "Payment",
            "intent": "测试",
            "type": "text_contains",
            "params": {"keywords": ["测试"], "match_mode": "any"},
            "risk_level": "LOW",
            "retrieval_tags": ["test"],
        }

        response = client.post("/api/rules", json=duplicate_rule)
        assert response.status_code == 409, f"409 错误处理失败: {response.status_code}"
        print(f"✓ POST /api/rules (重复): 409 Conflict")

        print("\n15. 测试请求/响应符合 Schema")
        print("-" * 60)

        # 验证返回数据符合 Rule Schema
        response = client.get("/api/rules")
        data = response.json()
        for rule in data['rules']:
            assert "rule_id" in rule
            assert "name" in rule
            assert "type" in rule
            assert "params" in rule
            assert "risk_level" in rule
            assert "retrieval_tags" in rule
            assert "prompt_template_id" in rule
        print(f"✓ 所有返回数据符合 Rule Schema")

        print("\n" + "=" * 60)
        print("所有 API 测试通过！")
        print("=" * 60)

    finally:
        # 关闭数据库连接
        db.disconnect()

        # 清理测试数据库文件
        try:
            os.remove("./test_api.db")
            print("测试数据库已清理")
        except:
            pass

    return True


if __name__ == "__main__":
    test_rule_api()
