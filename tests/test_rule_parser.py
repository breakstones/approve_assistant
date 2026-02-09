"""
Test Rule Parser
测试自然语言规则解析服务
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from config.rule_parser import RuleParser, parse_rule_from_text


def test_rule_parser():
    """测试规则解析器"""

    parser = RuleParser()

    print("=" * 60)
    print("规则解析器测试")
    print("=" * 60)

    # 测试用例
    test_cases = [
        # 测试用例 1: 付款周期限制
        {
            "input": "付款周期不得超过 30 天",
            "expected_type": "numeric_constraint",
            "expected_category": "Payment",
        },
        # 测试用例 2: 保密条款要求
        {
            "input": "合同必须包含保密条款",
            "expected_type": "requirement",
            "expected_category": "Confidentiality",
        },
        # 测试用例 3: 违约金限制
        {
            "input": "违约金比例不得超过 5%",
            "expected_type": "numeric_constraint",
            "expected_category": "Payment",
        },
        # 测试用例 4: 禁止自动续约
        {
            "input": "合同不得包含自动续约条款",
            "expected_type": "prohibition",
            "expected_category": "Termination",
        },
        # 测试用例 5: 管辖法律要求
        {
            "input": "合同应适用中华人民共和国法律",
            "expected_type": "text_contains",
            "expected_category": "Governing_Law",
        },
        # 测试用例 6: 不可抗力条款要求
        {
            "input": "合同必须包含不可抗力条款",
            "expected_type": "requirement",
            "expected_category": "Force_Majeure",
        },
        # 测试用例 7: 交付周期限制
        {
            "input": "货物应在合同签订后 30 日内交付",
            "expected_type": "numeric_constraint",
            "expected_category": "Delivery",
        },
        # 测试用例 8: 争议仲裁条款要求
        {
            "input": "合同争议应提交仲裁委员会仲裁",
            "expected_type": "requirement",
            "expected_category": "Dispute_Resolution",
        },
        # 测试用例 9: 多种付款周期表述
        {
            "input": "乙方应在收到发票后 45 日内完成付款",
            "expected_type": "numeric_constraint",
            "expected_category": "Payment",
        },
        # 测试用例 10: 复杂表述
        {
            "input": "若甲方逾期付款，每逾期一日应按应付金额的千分之五支付违约金",
            "expected_type": "numeric_constraint",
            "expected_category": "Payment",
        },
        # 测试用例 11: 质量标准要求
        {
            "input": "产品质量应符合国家标准",
            "expected_type": "text_contains",
            "expected_category": "Quality",
        },
        # 测试用例 12: 禁止转包条款
        {
            "input": "未经甲方书面同意，乙方不得将工程转包给第三方",
            "expected_type": "prohibition",
            "expected_category": "Other",
        },
        # 测试用例 13: 违约责任要求
        {
            "input": "合同应明确约定双方的违约责任",
            "expected_type": "text_contains",
            "expected_category": "Liability",
        },
        # 测试用例 14: 合同期限要求
        {
            "input": "合同有效期为 1 年",
            "expected_type": "numeric_constraint",
            "expected_category": "Termination",
        },
        # 测试用例 15: 知识产权条款要求
        {
            "input": "合同应明确知识产权归属",
            "expected_type": "text_contains",
            "expected_category": "Intellectual_Property",
        },
        # 测试用例 16: 争议解决方式要求
        {
            "input": "发生争议时应先协商解决",
            "expected_type": "requirement",
            "expected_category": "Dispute_Resolution",
        },
        # 测试用例 17: 通知条款要求
        {
            "input": "双方往来的通知应以书面形式作出",
            "expected_type": "text_contains",
            "expected_category": "Notices",
        },
        # 测试用例 18: 不可抗力条款内容
        {
            "input": "不可抗力包括但不限于地震、洪水、战争等不能预见、不能避免并不能克服的客观情况",
            "expected_type": "text_contains",
            "expected_category": "Force_Majeure",
        },
        # 测试用例 19: 保密义务具体要求
        {
            "input": "双方应对合作过程中获知的对方商业秘密承担保密义务，保密期限为合同终止后 3 年",
            "expected_type": "text_contains",
            "expected_category": "Confidentiality",
        },
        # 测试用例 20: 质保期要求
        {
            "input": "产品质量保证期为交付后 12 个月",
            "expected_type": "numeric_constraint",
            "expected_category": "Warranty",
        },
    ]

    print(f"\n总共 {len(test_cases)} 个测试用例\n")

    success_count = 0
    type_match_count = 0
    validation_fail_count = 0

    for i, test_case in enumerate(test_cases, 1):
        input_text = test_case["input"]
        expected_type = test_case.get("expected_type")
        expected_category = test_case.get("expected_category")

        print(f"测试用例 {i}: {input_text[:50]}...")
        print("-" * 60)

        # 解析规则
        result = parser.parse_mock(input_text)

        # 验证结果
        is_valid, error_msg = parser.validate(result)

        print(f"  rule_id: {result['rule_id']}")
        print(f"  name: {result['name']}")
        print(f"  type: {result['type']}", end="")
        if expected_type and result['type'] == expected_type:
            print(" ✓")
            type_match_count += 1
        else:
            print(f" (期望: {expected_type})")
        print(f"  category: {result['category']}", end="")
        if expected_category and result['category'] == expected_category:
            print(" ✓")
        print(f"  risk_level: {result['risk_level']}")
        print(f"  验证: {'通过 ✓' if is_valid else f'失败: {error_msg}'}")

        if is_valid:
            success_count += 1
        else:
            validation_fail_count += 1

        print()

    print("=" * 60)
    print("测试统计")
    print("=" * 60)
    print(f"总测试数: {len(test_cases)}")
    print(f"验证通过: {success_count} ({success_count/len(test_cases)*100:.1f}%)")
    print(f"类型匹配: {type_match_count} ({type_match_count/len(test_cases)*100:.1f}%)")
    print(f"验证失败: {validation_fail_count}")

    # 验证 Prompt 模板加载
    print("\n" + "=" * 60)
    print("Prompt 模板测试")
    print("=" * 60)

    prompt = parser.get_prompt("测试规则")
    print(f"✓ Prompt 模板加载成功")
    print(f"  模板长度: {len(parser.prompt_template)} 字符")
    print(f"  完整 Prompt 长度: {len(prompt)} 字符")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

    # 要求：解析成功率 > 80%
    success_rate = success_count / len(test_cases)
    if success_rate > 0.8:
        print(f"✓ 解析成功率 {success_rate*100:.1f}% > 80%，满足要求")
    else:
        print(f"✗ 解析成功率 {success_rate*100:.1f}% < 80%，不满足要求")

    return success_rate > 0.8


if __name__ == "__main__":
    result = test_rule_parser()
    sys.exit(0 if result else 1)
