"""
Test Chunk Schema Validation
验证 Chunk 示例是否符合 JSON Schema
"""
import json
from pathlib import Path


def validate_chunk_schema():
    """验证 Chunk Schema 和示例"""
    # 读取 Schema 定义
    schema_path = Path(__file__).parent.parent / "shared" / "schemas" / "chunk_schema.json"
    examples_path = Path(__file__).parent.parent / "shared" / "schemas" / "chunk_examples.json"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    with open(examples_path, "r", encoding="utf-8") as f:
        examples_data = json.load(f)

    examples = examples_data["examples"]

    print("=" * 60)
    print("Chunk Schema 验证")
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
    expected_fields = ["chunk_id", "doc_id", "page", "text", "bbox"]
    assert set(required_fields) == set(expected_fields), f"必需字段不匹配"
    print(f"✓ 必需字段正确: {expected_fields}")

    # 验证 clause_hint 枚举
    clause_hints = schema["properties"]["clause_hint"]["enum"]
    print(f"✓ 条件提示类型: {len(clause_hints)} 种")

    print("\n" + "=" * 60)
    print("示例 Chunk 验证")
    print("=" * 60)

    # 统计信息
    doc_ids = set()
    pages = set()
    clause_hints_used = set()
    total_tokens = 0

    for i, chunk in enumerate(examples, 1):
        print(f"\nChunk {i}: {chunk['chunk_id']}")

        # 验证必需字段
        for field in required_fields:
            assert field in chunk, f"Chunk {chunk['chunk_id']} 缺少必需字段: {field}"

        # 验证 chunk_id 格式
        import re
        pattern = r"^[a-zA-Z0-9_]+_p\d+_c\d+$"
        assert re.match(pattern, chunk["chunk_id"]), f"Chunk {chunk['chunk_id']} 格式不正确"

        # 验证 doc_id 关联
        assert chunk["doc_id"] in chunk["chunk_id"], f"Chunk {chunk['chunk_id']} doc_id 不匹配"

        # 验证页码
        assert chunk["page"] >= 1, f"Chunk {chunk['chunk_id']} 页码无效"

        # 验证文本长度
        assert len(chunk["text"]) >= 10, f"Chunk {chunk['chunk_id']} 文本过短"

        # 验证 bbox
        bbox = chunk["bbox"]
        if isinstance(bbox, list):
            assert len(bbox) == 4, f"Chunk {chunk['chunk_id']} bbox 数组长度无效"
            assert all(isinstance(v, (int, float)) for v in bbox), f"Chunk {chunk['chunk_id']} bbox 值类型无效"
        elif isinstance(bbox, dict):
            assert "x1" in bbox and "y1" in bbox and "x2" in bbox and "y2" in bbox, \
                f"Chunk {chunk['chunk_id']} bbox 对象缺少必需字段"
            assert bbox["x1"] < bbox["x2"], f"Chunk {chunk['chunk_id']} bbox x1 < x2 不成立"
            assert bbox["y1"] < bbox["y2"], f"Chunk {chunk['chunk_id']} bbox y1 < y2 不成立"

        # 统计
        doc_ids.add(chunk["doc_id"])
        pages.add(chunk["page"])
        if "clause_hint" in chunk:
            clause_hints_used.add(chunk["clause_hint"])
        if "token_count" in chunk:
            total_tokens += chunk["token_count"]

        print(f"  ✓ 文档: {chunk['doc_id']}, 页码: {chunk['page']}, 条款: {chunk.get('clause_hint', 'unknown')}")

    print("\n" + "=" * 60)
    print("统计信息")
    print("=" * 60)
    print(f"  总 Chunk 数: {len(examples)}")
    print(f"  文档数: {len(doc_ids)}")
    print(f"  涉及页数: {len(pages)}")
    print(f"  条款类型: {len(clause_hints_used)}")
    print(f"  总 Token 数: {total_tokens}")
    print(f"  平均 Token 数: {total_tokens / len(examples):.1f}")

    # 验证覆盖至少 3 页
    assert len(pages) >= 3, f"示例应覆盖至少 3 页，实际: {len(pages)} 页"
    print(f"\n✓ 覆盖 {len(pages)} 页（要求 ≥ 3 页）")

    # 验证 chunk 数量
    assert len(examples) >= 10, f"示例应至少 10 个 chunks，实际: {len(examples)}"
    print(f"✓ 共 {len(examples)} 个 chunks（要求 ≥ 10）")

    print("\n" + "=" * 60)
    print("验证通过！")
    print("=" * 60)

    return True


if __name__ == "__main__":
    validate_chunk_schema()
