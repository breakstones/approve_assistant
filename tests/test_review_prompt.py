"""
Test Review Prompt
测试审核 Prompt 设计与实现
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from execution.review_prompt import (
    ReviewPromptLoader,
    ReviewPromptValidator,
    ReviewContext,
    build_review_prompt,
    load_review_prompt,
)


def create_test_rule() -> dict:
    """创建测试规则"""
    return {
        "rule_id": "payment_cycle_max_30",
        "name": "付款周期限制",
        "category": "Payment",
        "type": "numeric_constraint",
        "risk_level": "HIGH",
        "intent": "付款周期不得超过30天",
        "params": {
            "max_days": 30,
            "payment_type": "租金",
        },
        "retrieval_tags": ["payment", "rent", "deadline"],
    }


def create_test_chunks() -> list[dict]:
    """创建测试文档片段"""
    return [
        {
            "chunk_id": "doc1_p1_c0",
            "doc_id": "doc1",
            "page": 1,
            "text": "每月租金为人民币5000元整。承租方应在每月5日前支付当月租金。",
            "bbox": {"x1": 50, "y1": 220, "x2": 500, "y2": 240, "page_width": 595, "page_height": 842},
            "clause_hint": "payment",
        },
        {
            "chunk_id": "doc1_p1_c1",
            "doc_id": "doc1",
            "page": 1,
            "text": "付款方式为银行转账，开户行：中国银行长沙分行，账号：6217-xxxx-xxxx-xxxx。",
            "bbox": {"x1": 50, "y1": 250, "x2": 500, "y2": 270, "page_width": 595, "page_height": 842},
            "clause_hint": "payment",
        },
        {
            "chunk_id": "doc1_p2_c0",
            "doc_id": "doc1",
            "page": 2,
            "text": "租赁期限为两年，自2024年1月1日起至2025年12月31日止。",
            "bbox": {"x1": 50, "y1": 100, "x2": 500, "y2": 120, "page_width": 595, "page_height": 842},
            "clause_hint": "other",
        },
    ]


def create_risk_chunks() -> list[dict]:
    """创建包含风险的文档片段"""
    return [
        {
            "chunk_id": "doc2_p1_c0",
            "doc_id": "doc2",
            "page": 1,
            "text": "付款周期为收到发票后45日内完成付款。",
            "bbox": {"x1": 50, "y1": 150, "x2": 500, "y2": 170, "page_width": 595, "page_height": 842},
            "clause_hint": "payment",
        },
    ]


def create_missing_chunks() -> list[dict]:
    """创建缺失条款的文档片段"""
    return [
        {
            "chunk_id": "doc3_p1_c0",
            "doc_id": "doc3",
            "page": 1,
            "text": "租赁期限为两年，自2024年1月1日起至2025年12月31日止。",
            "bbox": {"x1": 50, "y1": 100, "x2": 500, "y2": 120, "page_width": 595, "page_height": 842},
            "clause_hint": "other",
        },
    ]


def test_review_prompt():
    """测试审核 Prompt"""

    print("=" * 60)
    print("审核 Prompt 测试")
    print("=" * 60)

    print("\n1. 测试 Prompt 模板加载")
    print("-" * 60)

    try:
        template = load_review_prompt()
        print(f"✓ 加载 Prompt 模板成功")
        print(f"  - 模板长度: {len(template)} 字符")
        print(f"  - 包含占位符: {template.count('{')}")
    except Exception as e:
        print(f"✗ 加载模板失败: {e}")
        return False

    print("\n2. 测试 Prompt 构建（PASS 场景）")
    print("-" * 60)

    try:
        rule = create_test_rule()
        chunks = create_test_chunks()

        prompt = build_review_prompt(rule, chunks)

        print(f"✓ 构建 Prompt 成功")
        print(f"  - 规则ID: {rule['rule_id']}")
        print(f"  - 规则名称: {rule['name']}")
        print(f"  - 候选片段数: {len(chunks)}")
        print(f"  - Prompt 长度: {len(prompt)} 字符")

        # 显示 Prompt 片段
        print(f"\n  Prompt 预览（前500字符）:")
        print(f"  {prompt[:500]}...")

    except Exception as e:
        print(f"✗ 构建 Prompt 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n3. 测试不同场景的 Prompt 构建")
    print("-" * 60)

    scenarios = [
        ("PASS", create_test_rule(), create_test_chunks()),
        ("RISK", create_test_rule(), create_risk_chunks()),
        ("MISSING", create_test_rule(), create_missing_chunks()),
    ]

    for scenario_name, rule, chunks in scenarios:
        try:
            prompt = build_review_prompt(rule, chunks)
            print(f"✓ {scenario_name} 场景: Prompt 长度 {len(prompt)} 字符")
        except Exception as e:
            print(f"✗ {scenario_name} 场景失败: {e}")
            return False

    print("\n4. 测试 ReviewContext")
    print("-" * 60)

    try:
        rule = create_test_rule()
        chunks = create_test_chunks()

        context = ReviewContext(
            rule_id=rule["rule_id"],
            rule_name=rule["name"],
            category=rule["category"],
            rule_type=rule["type"],
            risk_level=rule["risk_level"],
            intent=rule["intent"],
            params=rule["params"],
            chunks=chunks,
        )

        loader = ReviewPromptLoader()
        prompt = loader.build_prompt_from_context(context)

        print(f"✓ 使用 ReviewContext 构建 Prompt 成功")
        print(f"  - Prompt 长度: {len(prompt)} 字符")

    except Exception as e:
        print(f"✗ ReviewContext 测试失败: {e}")
        return False

    print("\n5. 测试输出验证器")
    print("-" * 60)

    validator = ReviewPromptValidator()

    # 测试有效的输出
    valid_outputs = [
        # PASS 输出
        '''{
  "rule_id": "payment_cycle_max_30",
  "rule_name": "付款周期限制",
  "status": "PASS",
  "reason": "合同约定承租方在每月5日前支付租金，符合30天内付款的要求",
  "evidence": [
    {
      "chunk_id": "doc1_p1_c0",
      "page": 1,
      "text": "承租方应在每月5日前支付当月租金。",
      "bbox": {"x1": 50, "y1": 220, "x2": 500, "y2": 240}
    }
  ],
  "confidence": 0.9
}''',
        # RISK 输出
        '''{
  "rule_id": "payment_cycle_max_30",
  "rule_name": "付款周期限制",
  "status": "RISK",
  "reason": "付款周期为45天，超过30天限制",
  "evidence": [
    {
      "chunk_id": "doc2_p1_c0",
      "page": 1,
      "text": "付款周期为收到发票后45日内完成付款。",
      "bbox": {"x1": 50, "y1": 150, "x2": 500, "y2": 170}
    }
  ],
  "confidence": 0.95,
  "suggestion": "建议将付款周期修改为30天以内"
}''',
        # MISSING 输出
        '''{
  "rule_id": "payment_cycle_max_30",
  "rule_name": "付款周期限制",
  "status": "MISSING",
  "reason": "合同中未找到付款周期相关条款",
  "evidence": [],
  "confidence": 0.8
}''',
    ]

    for i, output in enumerate(valid_outputs, 1):
        result = validator.validate_prompt_output(output)
        if result["valid"]:
            print(f"✓ 有效输出 {i}: {result['data']['status']}")
        else:
            print(f"✗ 有效输出 {i} 验证失败: {result['error']}")
            return False

    # 测试无效的输出
    invalid_outputs = [
        '{"rule_id": "test"}',  # 缺少必需字段
        '{"rule_id": "test", "status": "INVALID", "reason": "test"}',  # 无效状态
        'not json',  # 无效 JSON
    ]

    for output in invalid_outputs:
        result = validator.validate_prompt_output(output)
        if not result["valid"]:
            print(f"✓ 正确拒绝无效输出: {result['error'][:50]}...")
        else:
            print(f"✗ 未能拒绝无效输出")
            return False

    print("\n6. 验证 Prompt 约束")
    print("-" * 60)

    # 检查 Prompt 是否包含关键约束
    template = load_review_prompt()

    constraints = [
        ("仅基于提供的原文", "仅基于提供的原文进行审核"),
        ("逐字引用", "必须逐字引用 Evidence"),
        ("状态说明", "状态只能是 PASS、RISK、MISSING 之一"),
        ("MISSING 空数组", "MISSING 状态时，evidence 必须为空数组"),
        ("JSON 输出", "必须输出有效的 JSON"),
    ]

    for name, keyword in constraints:
        if keyword in template:
            print(f"✓ 包含约束: {name}")
        else:
            print(f"✗ 缺少约束: {name}")
            return False

    print("\n" + "=" * 60)
    print("审核 Prompt 测试完成")
    print("=" * 60)

    print("\n✅ 所有测试通过！")
    print("\n说明：Prompt 模板已创建并验证，可以用于 LLM 调用。")
    print("      完整的审核流程将在 TASK-303 中实现。")

    return True


if __name__ == "__main__":
    success = test_review_prompt()
    sys.exit(0 if success else 1)
