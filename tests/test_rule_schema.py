"""
Test Rule Schema Validation
验证规则示例是否符合 JSON Schema
"""
import json
from pathlib import Path


def validate_rule_schema():
    """验证规则 Schema 和示例"""
    # 读取 Schema 定义
    schema_path = Path(__file__).parent.parent / "shared" / "schemas" / "rule_schema.json"
    examples_path = Path(__file__).parent.parent / "shared" / "schemas" / "rule_examples.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    with open(examples_path, "r", encoding="utf-8") as f:
        examples_data = json.load(f)

    examples = examples_data["examples"]

    # 基本结构验证
    print("=" * 60)
    print("Rule Schema 验证")
    print("=" * 60)

    # 验证 Schema 本身是否有效
    assert "$schema" in schema, "Schema 缺少 $schema 字段"
    assert "$id" in schema, "Schema 缺少 $id 字段"
    assert "title" in schema, "Schema 缺少 title 字段"
    assert "type" in schema, "Schema 缺少 type 字段"
    assert "required" in schema, "Schema 缺少 required 字段"
    assert "properties" in schema, "Schema 缺少 properties 字段"
    print("✓ Schema 基本结构有效")

    # 验证所有必需字段
    required_fields = schema["required"]
    expected_fields = [
        "rule_id", "name", "category", "intent", "type", "params",
        "risk_level", "retrieval_tags", "prompt_template_id"
    ]
    assert set(required_fields) == set(expected_fields), f"必需字段不匹配: {set(required_fields)} vs {set(expected_fields)}"
    print(f"✓ 必需字段正确: {expected_fields}")

    # 验证规则类型枚举
    rule_types = schema["properties"]["type"]["enum"]
    expected_types = ["numeric_constraint", "text_contains", "prohibition", "requirement"]
    assert rule_types == expected_types, f"规则类型不匹配: {rule_types} vs {expected_types}"
    print(f"✓ 规则类型正确: {expected_types}")

    # 验证风险等级枚举
    risk_levels = schema["properties"]["risk_level"]["enum"]
    expected_levels = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert risk_levels == expected_levels, f"风险等级不匹配: {risk_levels} vs {expected_levels}"
    print(f"✓ 风险等级正确: {expected_levels}")

    print("\n" + "=" * 60)
    print("示例规则验证")
    print("=" * 60)

    # 验证所有示例规则
    for i, rule in enumerate(examples, 1):
        print(f"\n规则 {i}: {rule['name']} ({rule['rule_id']})")

        # 验证必需字段
        for field in required_fields:
            assert field in rule, f"规则 {rule['rule_id']} 缺少必需字段: {field}"

        # 验证规则类型有效
        assert rule["type"] in rule_types, f"规则 {rule['rule_id']} 类型无效: {rule['type']}"

        # 验证风险等级有效
        assert rule["risk_level"] in risk_levels, f"规则 {rule['rule_id']} 风险等级无效: {rule['risk_level']}"

        # 验证 retrieval_tags 非空
        assert len(rule["retrieval_tags"]) > 0, f"规则 {rule['rule_id']} retrieval_tags 为空"

        # 验证 params 根据 type 匹配
        rule_type = rule["type"]
        if rule_type == "numeric_constraint":
            assert "field" in rule["params"], f"规则 {rule['rule_id']} 缺少 params.field"
            assert "operator" in rule["params"], f"规则 {rule['rule_id']} 缺少 params.operator"
            assert "value" in rule["params"], f"规则 {rule['rule_id']} 缺少 params.value"
            operators = ["<", "<=", "=", ">=", ">", "between"]
            assert rule["params"]["operator"] in operators, f"规则 {rule['rule_id']} operator 无效"

        elif rule_type == "text_contains":
            assert "keywords" in rule["params"], f"规则 {rule['rule_id']} 缺少 params.keywords"
            assert "match_mode" in rule["params"], f"规则 {rule['rule_id']} 缺少 params.match_mode"
            match_modes = ["all", "any", "exact"]
            assert rule["params"]["match_mode"] in match_modes, f"规则 {rule['rule_id']} match_mode 无效"

        elif rule_type == "prohibition":
            assert "prohibited_patterns" in rule["params"], f"规则 {rule['rule_id']} 缺少 params.prohibited_patterns"

        elif rule_type == "requirement":
            assert "required_clauses" in rule["params"], f"规则 {rule['rule_id']} 缺少 params.required_clauses"

        print(f"  ✓ 类型: {rule['type']}, 风险: {rule['risk_level']}")

    # 统计每种类型的规则数量
    print("\n" + "=" * 60)
    print("规则类型统计")
    print("=" * 60)

    type_counts = {}
    for rule in examples:
        rule_type = rule["type"]
        type_counts[rule_type] = type_counts.get(rule_type, 0) + 1

    for rule_type, count in type_counts.items():
        print(f"  {rule_type}: {count} 条")

    print("\n" + "=" * 60)
    print("验证通过！")
    print(f"共验证 {len(examples)} 条规则，全部符合 Schema 定义")
    print("=" * 60)

    return True


if __name__ == "__main__":
    validate_rule_schema()
