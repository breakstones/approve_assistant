"""
Test Rule-aware Query Builder
测试基于规则语义的检索查询生成功能
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from execution.query_builder import (
    RuleAwareQueryBuilder,
    build_search_queries,
    get_filter_tags,
    SearchQuery,
)


def create_test_rules() -> list[dict]:
    """创建测试规则"""
    return [
        {
            "rule_id": "rule_001",
            "name": "付款期限检查",
            "category": "Payment",
            "intent": "承租方应在每月5日前支付当月租金",
            "type": "numeric_constraint",
            "params": {
                "payment_day": "5",
                "payment_type": "租金",
            },
            "risk_level": "HIGH",
            "retrieval_tags": ["payment", "rent", "deadline"],
        },
        {
            "rule_id": "rule_002",
            "name": "保密义务检查",
            "category": "Confidentiality",
            "intent": "双方应对合同履行过程中知悉的商业秘密承担保密义务",
            "type": "requirement",
            "params": {
                "obligation": "保密义务",
                "scope": "合同履行过程中",
            },
            "risk_level": "MEDIUM",
            "retrieval_tags": ["confidentiality", "obligation"],
        },
        {
            "rule_id": "rule_003",
            "name": "禁止转租检查",
            "category": "Assignment",
            "intent": "未经出租方书面同意，承租方不得将房屋转租",
            "type": "prohibition",
            "params": {
                "action": "转租",
                "condition": "未经出租方书面同意",
            },
            "risk_level": "HIGH",
            "retrieval_tags": ["assignment", "prohibition"],
        },
        {
            "rule_id": "rule_004",
            "name": "合同期限检查",
            "category": "Termination",
            "intent": "租赁期限为两年，自2024年1月1日起至2025年12月31日止",
            "type": "numeric_constraint",
            "params": {
                "duration": "两年",
                "start_date": "2024年1月1日",
                "end_date": "2025年12月31日",
            },
            "risk_level": "MEDIUM",
            "retrieval_tags": ["term", "duration"],
        },
    ]


def test_query_builder():
    """测试查询构建器"""

    print("=" * 60)
    print("Rule-aware Query Builder 测试")
    print("=" * 60)

    print("\n1. 测试查询构建器创建")
    print("-" * 60)

    try:
        builder = RuleAwareQueryBuilder(
            max_queries_per_rule=3,
            min_keyword_length=2,
        )
        print(f"✓ 创建查询构建器成功")
        print(f"  - 每规则最大查询数: {builder.max_queries_per_rule}")
        print(f"  - 最小关键词长度: {builder.min_keyword_length}")

    except Exception as e:
        print(f"✗ 创建查询构建器失败: {e}")
        return False

    print("\n2. 测试单条规则查询构建")
    print("-" * 60)

    rules = create_test_rules()
    rule = rules[0]  # 付款期限检查

    try:
        queries = builder._build_queries_for_rule(rule)
        print(f"✓ 为规则 '{rule['name']}' 生成 {len(queries)} 个查询")

        for i, query in enumerate(queries):
            print(f"\n  查询 {i + 1}:")
            print(f"    ID: {query.query_id}")
            print(f"    文本: {query.text}")
            print(f"    关键词: {query.keywords}")
            print(f"    类型: {query.query_type}")
            print(f"    权重: {query.weight}")

    except Exception as e:
        print(f"✗ 单条规则查询构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n3. 测试多规则查询构建")
    print("-" * 60)

    try:
        result = builder.build_queries(rules, combine_rules=True)

        print(f"✓ 查询构建完成")
        print(f"  - 规则数: {result.rules_count}")
        print(f"  - 查询数: {len(result.queries)}")
        print(f"  - 唯一关键词: {result.unique_keywords}")
        print(f"  - 唯一标签: {result.unique_tags}")

    except Exception as e:
        print(f"✗ 多规则查询构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n4. 显示所有生成的查询")
    print("-" * 60)

    try:
        for i, query in enumerate(result.queries):
            print(f"\n查询 {i + 1}:")
            print(f"  ID: {query.query_id}")
            print(f"  文本: {query.text}")
            print(f"  关键词: {query.keywords[:5]}...")  # 只显示前5个
            print(f"  标签: {list(query.tags)}")
            print(f"  规则: {query.rules}")

    except Exception as e:
        print(f"✗ 显示查询失败: {e}")
        return False

    print("\n5. 测试便捷函数")
    print("-" * 60)

    try:
        result = build_search_queries(rules, combine_rules=True)
        print(f"✓ build_search_queries() 返回 {len(result.queries)} 个查询")

    except Exception as e:
        print(f"✗ 便捷函数测试失败: {e}")
        return False

    print("\n6. 测试标签提取")
    print("-" * 60)

    try:
        tags = get_filter_tags(rules)
        print(f"✓ 提取到 {len(tags)} 个唯一标签:")
        print(f"  {', '.join(sorted(tags))}")

    except Exception as e:
        print(f"✗ 标签提取测试失败: {e}")
        return False

    print("\n7. 验证查询质量")
    print("-" * 60)

    try:
        # 验证查询数量
        assert len(result.queries) > 0, "至少应生成一个查询"

        # 验证每个查询都有必需字段
        for query in result.queries:
            assert query.query_id, "查询必须有 ID"
            assert query.text, "查询必须有文本"
            assert isinstance(query.keywords, list), "关键词必须是列表"
            assert isinstance(query.tags, set), "标签必须是集合"
            assert query.rules, "查询必须关联至少一个规则"
            assert 0 <= query.weight <= 1, "权重必须在 0-1 之间"

        print("✓ 所有查询字段验证通过")

        # 验证查询类型分布
        type_counts = {}
        for query in result.queries:
            type_counts[query.query_type] = type_counts.get(query.query_type, 0) + 1

        print(f"✓ 查询类型分布:")
        for query_type, count in type_counts.items():
            print(f"  - {query_type}: {count}")

    except AssertionError as e:
        print(f"✗ 查询质量验证失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 验证过程出错: {e}")
        return False

    print("\n8. 测试不同规则类型")
    print("-" * 60)

    try:
        type_tests = {
            "numeric_constraint": rules[0],
            "requirement": rules[1],
            "prohibition": rules[2],
        }

        for rule_type, rule in type_tests.items():
            queries = builder._build_queries_for_rule(rule)
            print(f"✓ {rule_type}: 生成 {len(queries)} 个查询")

    except Exception as e:
        print(f"✗ 规则类型测试失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("Rule-aware Query Builder 测试完成")
    print("=" * 60)

    print("\n✅ 所有测试通过！")

    return True


if __name__ == "__main__":
    success = test_query_builder()
    sys.exit(0 if success else 1)
