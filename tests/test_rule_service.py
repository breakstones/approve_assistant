"""
Test Rule Service
测试规则存储模型与 CRUD 操作
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from config import RuleService, init_db, RuleType, RiskLevel, RuleCategory
import json
from pathlib import Path


def test_rule_service():
    """测试规则服务"""

    # 初始化数据库（使用测试数据库）
    db = init_db("sqlite:///./test_rules.db")

    # 创建规则服务
    service = RuleService()

    print("=" * 60)
    print("规则服务测试")
    print("=" * 60)

    # 加载示例规则
    examples_path = Path(__file__).parent.parent / "shared" / "schemas" / "rule_examples.json"
    with open(examples_path, "r", encoding="utf-8") as f:
        examples_data = json.load(f)

    test_rules = examples_data["examples"]

    print("\n1. 批量创建规则")
    print("-" * 60)

    created_rules = service.bulk_create(test_rules)
    print(f"✓ 创建了 {len(created_rules)} 条规则")

    for rule in created_rules:
        print(f"  - {rule['rule_id']}: {rule['name']}")

    print("\n2. 查询单条规则")
    print("-" * 60)

    rule = service.get_by_id("payment_cycle_max_30")
    assert rule is not None, "规则未找到"
    print(f"✓ 查询成功: {rule['name']}")
    print(f"  类型: {rule['type']}")
    print(f"  风险等级: {rule['risk_level']}")
    print(f"  版本: {rule['version']}")

    print("\n3. 列出所有规则")
    print("-" * 60)

    all_rules = service.list()
    print(f"✓ 共 {len(all_rules)} 条规则")

    print("\n4. 按分类过滤")
    print("-" * 60)

    payment_rules = service.list(category="Payment")
    print(f"✓ Payment 类别: {len(payment_rules)} 条规则")

    print("\n5. 按风险等级过滤")
    print("-" * 60)

    high_risk_rules = service.list(risk_level="HIGH")
    print(f"✓ HIGH 风险等级: {len(high_risk_rules)} 条规则")

    print("\n6. 按类型过滤")
    print("-" * 60)

    numeric_rules = service.list(type="numeric_constraint")
    print(f"✓ numeric_constraint 类型: {len(numeric_rules)} 条规则")

    print("\n7. 统计规则数量")
    print("-" * 60)

    total_count = service.count()
    payment_count = service.count(category="Payment")
    high_risk_count = service.count(risk_level="HIGH")

    print(f"✓ 总数: {total_count}")
    print(f"✓ Payment 类别: {payment_count}")
    print(f"✓ HIGH 风险: {high_risk_count}")

    print("\n8. 获取分类列表")
    print("-" * 60)

    categories = service.get_categories()
    print(f"✓ 分类: {', '.join(categories)}")

    print("\n9. 获取风险等级列表")
    print("-" * 60)

    risk_levels = service.get_risk_levels()
    print(f"✓ 风险等级: {', '.join(risk_levels)}")

    print("\n10. 更新规则")
    print("-" * 60)

    updated_rule = service.update("payment_cycle_max_30", {
        "description": "更新后的描述",
        "risk_level": "CRITICAL"
    })
    assert updated_rule is not None, "规则更新失败"
    assert updated_rule['version'] == 2, "版本号未增加"
    print(f"✓ 更新成功，版本: {updated_rule['version']}")
    print(f"  新风险等级: {updated_rule['risk_level']}")

    print("\n11. 分页查询")
    print("-" * 60)

    page1 = service.list(limit=3, offset=0)
    page2 = service.list(limit=3, offset=3)
    print(f"✓ 第1页 (3条): {[r['rule_id'] for r in page1]}")
    print(f"✓ 第2页 (3条): {[r['rule_id'] for r in page2]}")

    print("\n12. 软删除规则")
    print("-" * 60)

    delete_result = service.delete("payment_cycle_max_30")
    assert delete_result == True, "删除失败"

    # 查询已删除的规则（默认不返回）
    rule_after_delete = service.get_by_id("payment_cycle_max_30")
    assert rule_after_delete is None, "软删除后仍可查询到"

    # 查询包括未启用的规则
    disabled_rules = service.list(enabled_only=False)
    disabled_ids = [r['rule_id'] for r in disabled_rules]
    assert "payment_cycle_max_30" in disabled_ids, "软删除规则未在列表中"

    print("✓ 软删除成功")
    print("  默认查询: 不返回已删除规则")
    print("  查询所有: 包含已删除规则")

    print("\n13. 重新启用规则")
    print("-" * 60)

    # 通过 update 重新启用
    service.update("payment_cycle_max_30", {"enabled": True})
    reactivated = service.get_by_id("payment_cycle_max_30")
    assert reactivated is not None, "重新启用失败"
    print(f"✓ 重新启用成功: {reactivated['name']}")

    print("\n" + "=" * 60)
    print("所有测试通过！")
    print("=" * 60)

    # 关闭数据库连接
    db.disconnect()

    # 清理测试数据库文件
    import os
    try:
        os.remove("./test_rules.db")
        print("测试数据库已清理")
    except:
        pass

    return True


if __name__ == "__main__":
    test_rule_service()
