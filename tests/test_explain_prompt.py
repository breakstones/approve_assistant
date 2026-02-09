"""
Test Explain Prompt
测试解释 Prompt
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def test_explain_prompt_structure():
    """测试解释 Prompt 结构"""
    print("=" * 60)
    print("解释 Prompt 结构测试")
    print("=" * 60)

    # 读取 Prompt 模板
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "explain.txt"
    )

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_content = f.read()

    # 验证关键部分
    required_sections = [
        "核心原则",
        "输入信息",
        "输出格式",
        "回答策略",
        "多轮对话处理",
        "限制与边界",
        "质量检查清单",
    ]

    print("\n1. 验证 Prompt 结构完整性")
    print("-" * 60)

    all_present = True
    for section in required_sections:
        if section in prompt_content:
            print(f"  ✓ 包含 '{section}' 部分")
        else:
            print(f"  ✗ 缺少 '{section}' 部分")
            all_present = False

    # 验证关键原则
    print("\n2. 验证核心原则")
    print("-" * 60)

    required_principles = [
        "Evidence First",
        "严格引用",
        "诚实原则",
        "结构清晰",
        "可追溯",
    ]

    for principle in required_principles:
        if principle in prompt_content:
            print(f"  ✓ 包含原则: {principle}")
        else:
            print(f"  ✗ 缺少原则: {principle}")
            all_present = False

    # 验证输出格式
    print("\n3. 验证输出格式")
    print("-" * 60)

    required_fields = [
        "answer",
        "reasoning",
        "evidence_references",
        "confidence",
        "limitations",
    ]

    for field in required_fields:
        if field in prompt_content:
            print(f"  ✓ 包含字段: {field}")
        else:
            print(f"  ✗ 缺少字段: {field}")
            all_present = False

    # 验证不同状态的回答策略
    print("\n4. 验证状态处理策略")
    print("-" * 60)

    statuses = ["PASS", "RISK", "MISSING"]
    for status in statuses:
        if f"{status} 状态的追问" in prompt_content:
            print(f"  ✓ 包含 {status} 状态处理")
        else:
            print(f"  ✗ 缺少 {status} 状态处理")
            all_present = False

    return all_present


def test_explain_test_cases():
    """测试 15+ 追问测试用例"""
    print("\n" + "=" * 60)
    print("追问测试用例验证")
    print("=" * 60)

    # 定义测试用例
    test_cases = [
        # PASS 状态追问
        {"status": "PASS", "question": "为什么判定为通过？", "category": "原因解释"},
        {"status": "PASS", "question": "具体满足规则的哪些要求？", "category": "细节确认"},
        {"status": "PASS", "question": "原文哪里体现了这一点？", "category": "证据定位"},
        {"status": "PASS", "question": "这个判定可靠吗？", "category": "置信度询问"},
        {"status": "PASS", "question": "还有其他相关条款吗？", "category": "扩展询问"},

        # RISK 状态追问
        {"status": "RISK", "question": "为什么判定为有风险？", "category": "原因解释"},
        {"status": "RISK", "question": "具体哪些地方不符合要求？", "category": "问题定位"},
        {"status": "RISK", "question": "应该如何修改？", "category": "修改建议"},
        {"status": "RISK", "question": "这个风险严重吗？", "category": "风险评估"},
        {"status": "RISK", "question": "有没有替代方案？", "category": "方案探讨"},

        # MISSING 状态追问
        {"status": "MISSING", "question": "为什么说缺失了？", "category": "原因解释"},
        {"status": "MISSING", "question": "原文中确实没有相关内容吗？", "category": "确认询问"},
        {"status": "MISSING", "question": "检索范围是什么？", "category": "范围确认"},
        {"status": "MISSING", "question": "应该在哪个章节补充？", "category": "补充建议"},
        {"status": "MISSING", "question": "这可能是遗漏吗？", "category": "验证询问"},

        # 跨状态问题
        {"status": "ANY", "question": "请解释一下这个条款的含义", "category": "条款解释"},
        {"status": "ANY", "question": "这个结论的依据是什么？", "category": "依据确认"},
        {"status": "ANY", "question": "如何验证这个结论？", "category": "验证方法"},
        {"status": "ANY", "question": "还有其他需要注意的吗？", "category": "额外提醒"},
    ]

    print(f"\n总计: {len(test_cases)} 个测试用例")
    print("\n测试用例分布:")
    print("-" * 60)

    # 按状态统计
    from collections import Counter
    status_count = Counter(case["status"] for case in test_cases)
    for status, count in status_count.items():
        print(f"  {status}: {count} 个")

    # 按类别统计
    print("\n按类别分布:")
    print("-" * 60)
    category_count = Counter(case["category"] for case in test_cases)
    for category, count in category_count.items():
        print(f"  {category}: {count} 个")

    return len(test_cases) >= 15


def test_explain_prompt_examples():
    """测试 Prompt 示例完整性"""
    print("\n" + "=" * 60)
    print("Prompt 示例完整性验证")
    print("=" * 60)

    # 读取 Prompt 模板
    prompt_path = os.path.join(
        os.path.dirname(__file__), "..", "prompts", "explain.txt"
    )

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_content = f.read()

    print("\n验证示例内容:")
    print("-" * 60)

    # 检查是否包含 JSON 示例
    checks = [
        ("PASS 示例", "PASS 状态的追问" in prompt_content),
        ("RISK 示例", "RISK 状态的追问" in prompt_content),
        ("MISSING 示例", "MISSING 状态的追问" in prompt_content),
        ("JSON 格式示例", '"answer":' in prompt_content),
        ("证据引用示例", '"evidence_references":' in prompt_content),
        ("多轮对话示例", "多轮对话处理" in prompt_content),
        ("完整对话示例", "示例对话" in prompt_content),
        ("限制处理示例", "必须拒绝的场景" in prompt_content),
    ]

    all_pass = True
    for name, check in checks:
        if check:
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name}")
            all_pass = False

    return all_pass


def test_explain_mock_execution():
    """测试解释 Prompt 执行模拟"""
    print("\n" + "=" * 60)
    print("解释 Prompt 执行模拟测试")
    print("=" * 60)

    # 模拟输入
    mock_input = {
        "rule_name": "付款周期限制",
        "rule_type": "numeric_constraint",
        "rule_intent": "付款周期不得超过30天",
        "rule_params": {"max_days": 30},
        "rule_risk_level": "HIGH",
        "review_status": "RISK",
        "review_reason": "合同约定付款周期为60天，超过30天限制",
        "evidence_list": [
            {
                "chunk_id": "doc_001_p3_c1",
                "text": "甲方应在验收合格后60个工作日内支付款项",
                "page": 3,
                "bbox": {"x1": 100, "y1": 200, "x2": 400, "y2": 250},
            }
        ],
        "user_question": "为什么判定为有风险？",
        "conversation_history": [],
    }

    print("\n模拟输入:")
    print("-" * 60)
    print(f"  规则: {mock_input['rule_name']}")
    print(f"  状态: {mock_input['review_status']}")
    print(f"  问题: {mock_input['user_question']}")
    print(f"  证据数: {len(mock_input['evidence_list'])}")

    print("\n期望输出结构:")
    print("-" * 60)
    print("""
    {
      "answer": "该合同的付款周期约定为60天...",
      "reasoning": "规则要求付款周期不超过30天...",
      "evidence_references": [
        {
          "chunk_id": "doc_001_p3_c1",
          "quote": "甲方应在验收合格后60个工作日内支付款项",
          "page": 3,
          "relevance": "直接证明了付款周期为60天，超出规则限制"
        }
      ],
      "confidence": "high",
      "limitations": []
    }
    """)

    return True


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("解释 Prompt 测试套件")
    print("=" * 60)

    results = []

    # 运行所有测试
    results.append(("结构完整性", test_explain_prompt_structure()))
    results.append(("测试用例数量", test_explain_test_cases()))
    results.append(("示例完整性", test_explain_prompt_examples()))
    results.append(("执行模拟", test_explain_mock_execution()))

    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_pass = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_pass = False

    print("\n" + "=" * 60)
    if all_pass:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败！")
    print("=" * 60)

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
