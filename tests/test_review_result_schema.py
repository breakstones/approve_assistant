"""
Test Review Result Schema Validation
验证 Review Result 示例是否符合 JSON Schema
"""
import json
from pathlib import Path


def validate_review_result_schema():
    """验证 Review Result Schema 和示例"""
    # 读取 Schema 定义
    schema_path = Path(__file__).parent.parent / "shared" / "schemas" / "review_result_schema.json"
    examples_path = Path(__file__).parent.parent / "shared" / "schemas" / "review_result_examples.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    with open(examples_path, "r", encoding="utf-8") as f:
        examples_data = json.load(f)

    examples = examples_data["examples"]

    print("=" * 60)
    print("Review Result Schema 验证")
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
    expected_fields = ["rule_id", "status", "reason"]
    assert set(required_fields) == set(expected_fields), f"必需字段不匹配"
    print(f"✓ 必需字段正确: {expected_fields}")

    # 验证状态枚举
    status_values = schema["properties"]["status"]["enum"]
    expected_status = ["PASS", "RISK", "MISSING"]
    assert status_values == expected_status, f"状态枚举不匹配: {status_values} vs {expected_status}"
    print(f"✓ 状态枚举正确: {expected_status}")

    print("\n" + "=" * 60)
    print("示例 Review Result 验证")
    print("=" * 60)

    # 统计信息
    status_counts = {"PASS": 0, "RISK": 0, "MISSING": 0}
    evidence_counts = {"empty": 0, "single": 0, "multiple": 0}
    total_confidence = 0
    rules_reviewed = set()

    for i, result in enumerate(examples, 1):
        print(f"\n结果 {i}: {result['rule_id']}")

        # 验证必需字段
        for field in required_fields:
            assert field in result, f"结果 {result['rule_id']} 缺少必需字段: {field}"

        # 验证状态值
        assert result["status"] in status_values, f"结果 {result['rule_id']} 状态无效: {result['status']}"

        # 验证 reason 非空
        assert len(result["reason"]) > 0, f"结果 {result['rule_id']} reason 为空"

        # 验证 evidence
        evidence = result.get("evidence", [])
        assert isinstance(evidence, list), f"结果 {result['rule_id']} evidence 不是数组"

        if len(evidence) == 0:
            evidence_counts["empty"] += 1
        elif len(evidence) == 1:
            evidence_counts["single"] += 1
        else:
            evidence_counts["multiple"] += 1

        # 验证 evidence 中的每个项目
        for ev in evidence:
            assert "chunk_id" in ev, f"结果 {result['rule_id']} evidence 缺少 chunk_id"
            assert "page" in ev, f"结果 {result['rule_id']} evidence 缺少 page"
            assert "text" in ev, f"结果 {result['rule_id']} evidence 缺少 text"
            assert ev["page"] >= 1, f"结果 {result['rule_id']} evidence 页码无效"
            assert len(ev["text"]) > 0, f"结果 {result['rule_id']} evidence text 为空"

        # 验证 confidence（如果存在）
        if "confidence" in result:
            assert 0 <= result["confidence"] <= 1, f"结果 {result['rule_id']} confidence 超出范围"
            total_confidence += result["confidence"]

        # 统计
        status_counts[result["status"]] += 1
        rules_reviewed.add(result["rule_id"])

        print(f"  ✓ 状态: {result['status']}, Evidence: {len(evidence)} 条, 置信度: {result.get('confidence', 0):.2f}")

    print("\n" + "=" * 60)
    print("统计信息")
    print("=" * 60)
    print(f"  总结果数: {len(examples)}")
    print(f"  涉及规则: {len(rules_reviewed)}")
    print(f"  状态分布:")
    for status, count in status_counts.items():
        print(f"    {status}: {count}")
    print(f"  Evidence 分布:")
    for ev_type, count in evidence_counts.items():
        print(f"    {ev_type}: {count}")
    print(f"  平均置信度: {total_confidence / len(examples):.3f}")

    # 验证覆盖三种状态
    assert all(status_counts[s] > 0 for s in expected_status), "必须覆盖 PASS/RISK/MISSING 三种状态"
    print(f"\n✓ 覆盖所有三种状态: PASS/RISK/MISSING")

    # 验证 evidence 数组的不同情况
    assert evidence_counts["empty"] > 0, "必须包含空 evidence 的示例"
    assert evidence_counts["single"] > 0, "必须包含单 evidence 的示例"
    assert evidence_counts["multiple"] > 0, "必须包含多 evidence 的示例"
    print(f"✓ Evidence 数组支持: 空值({evidence_counts['empty']}), 单值({evidence_counts['single']}), 多值({evidence_counts['multiple']})")

    print("\n" + "=" * 60)
    print("验证通过！")
    print("=" * 60)

    return True


if __name__ == "__main__":
    validate_review_result_schema()
