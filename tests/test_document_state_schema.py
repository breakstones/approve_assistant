"""
Test Document State Schema Validation
验证 Document State 示例是否符合 JSON Schema
"""
import json
from pathlib import Path


def validate_document_state_schema():
    """验证 Document State Schema 和示例"""
    # 读取 Schema 定义
    schema_path = Path(__file__).parent.parent / "shared" / "schemas" / "document_state_schema.json"
    examples_path = Path(__file__).parent.parent / "shared" / "schemas" / "document_state_examples.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    with open(examples_path, "r", encoding="utf-8") as f:
        examples_data = json.load(f)

    state_transitions = examples_data["state_transitions"]
    examples = examples_data["examples"]

    print("=" * 60)
    print("Document State Schema 验证")
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
    expected_fields = ["doc_id", "filename", "file_type", "status", "created_at"]
    assert set(required_fields) == set(expected_fields), f"必需字段不匹配"
    print(f"✓ 必需字段正确: {expected_fields}")

    # 验证状态枚举
    status_values = schema["properties"]["status"]["enum"]
    expected_status = ["UPLOADED", "PROCESSING", "READY", "REVIEWING", "REVIEWED", "FAILED"]
    assert status_values == expected_status, f"状态枚举不匹配: {status_values} vs {expected_status}"
    print(f"✓ 状态枚举正确: {expected_status}")

    print("\n" + "=" * 60)
    print("状态转换规则验证")
    print("=" * 60)

    # 验证状态定义
    states = state_transitions["states"]
    for state_name, state_info in states.items():
        assert state_name in expected_status, f"未定义的状态: {state_name}"
        assert "allowed_next" in state_info, f"状态 {state_name} 缺少 allowed_next"
        assert "allowed_operations" in state_info, f"状态 {state_name} 缺少 allowed_operations"
        print(f"  ✓ {state_name}: {state_info['description']}")
        print(f"    允许转换: {', '.join(state_info['allowed_next'])}")
        print(f"    允许操作: {', '.join(state_info['allowed_operations'])}")

    # 验证状态转换规则
    print("\n状态转换规则:")
    transition_rules = state_transitions["transition_rules"]
    for rule in transition_rules:
        print(f"  {rule['from']} → {rule['to']}: {rule['condition']}")
        # 验证转换的合法性
        assert rule["from"] in expected_status, f"无效的源状态: {rule['from']}"
        assert rule["to"] in expected_status, f"无效的目标状态: {rule['to']}"
        assert rule["to"] in states[rule["from"]]["allowed_next"], \
            f"非法转换: {rule['from']} → {rule['to']}"

    print("\n" + "=" * 60)
    print("文档示例验证")
    print("=" * 60)

    # 统计状态
    status_counts = {s: 0 for s in expected_status}

    for i, doc in enumerate(examples, 1):
        print(f"\n文档 {i}: {doc['doc_id']}")

        # 验证必需字段
        for field in required_fields:
            assert field in doc, f"文档 {doc['doc_id']} 缺少必需字段: {field}"

        # 验证状态值
        assert doc["status"] in expected_status, f"文档 {doc['doc_id']} 状态无效: {doc['status']}"

        # 验证文件类型
        assert doc["file_type"] in ["pdf", "docx", "doc"], f"文档 {doc['doc_id']} 文件类型无效"

        # 验证进度范围
        if "progress" in doc:
            assert 0 <= doc["progress"] <= 100, f"文档 {doc['doc_id']} progress 超出范围"

        # 验证处理信息（如果有）
        if "processing_info" in doc and doc["processing_info"]:
            if "processing_time_ms" in doc["processing_info"]:
                assert doc["processing_info"]["processing_time_ms"] >= 0, \
                    f"文档 {doc['doc_id']} processing_time_ms 无效"

        # 统计
        status_counts[doc["status"]] += 1

        print(f"  ✓ 状态: {doc['status']}, 文件: {doc['filename']}, 进度: {doc.get('progress', 0)}%")

    print("\n" + "=" * 60)
    print("统计信息")
    print("=" * 60)
    print(f"  总文档数: {len(examples)}")
    print(f"  状态分布:")
    for status, count in status_counts.items():
        print(f"    {status}: {count}")

    # 验证覆盖所有状态
    covered_statuses = [s for s, c in status_counts.items() if c > 0]
    assert len(covered_statuses) >= 4, f"应覆盖至少 4 种状态，实际: {covered_statuses}"
    print(f"\n✓ 覆盖 {len(covered_statuses)} 种状态: {', '.join(covered_statuses)}")

    # 验证包含失败状态示例
    assert status_counts["FAILED"] > 0, "必须包含 FAILED 状态示例"
    print(f"✓ 包含失败状态示例")

    print("\n" + "=" * 60)
    print("验证通过！")
    print("=" * 60)

    return True


if __name__ == "__main__":
    validate_document_state_schema()
