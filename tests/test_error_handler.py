"""
Test Error Handler
测试错误处理模块
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from utils.error_handler import (
    ErrorCode,
    TrustLensError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    ValidationError,
    DocumentProcessingError,
    ReviewExecutionError,
    RuleValidationError,
    handle_error,
    log_business_event,
    get_error_response,
)


def test_error_codes():
    """测试错误码定义"""
    print("=" * 60)
    print("错误码测试")
    print("=" * 60)

    # 检查各类错误码
    categories = {
        "通用错误": [ErrorCode.UNKNOWN_ERROR, ErrorCode.INVALID_REQUEST],
        "资源错误": [ErrorCode.RESOURCE_NOT_FOUND, ErrorCode.RESOURCE_ALREADY_EXISTS],
        "业务错误": [ErrorCode.RULE_VALIDATION_ERROR, ErrorCode.DOCUMENT_PROCESSING_ERROR],
        "系统错误": [ErrorCode.DATABASE_ERROR, ErrorCode.CACHE_ERROR],
    }

    for category, codes in categories.items():
        print(f"\n{category}:")
        for code in codes:
            print(f"  {code.value}: {code.name}")

    return True


def test_error_creation():
    """测试错误创建"""
    print("\n" + "=" * 60)
    print("错误创建测试")
    print("=" * 60)

    tests_passed = 0
    tests_total = 0

    # 测试 TrustLensError
    tests_total += 1
    try:
        error = TrustLensError("测试错误", ErrorCode.UNKNOWN_ERROR)
        assert error.message == "测试错误"
        assert error.code == ErrorCode.UNKNOWN_ERROR
        error_dict = error.to_dict()
        assert "code" in error_dict
        print("  ✓ TrustLensError 创建成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ TrustLensError 创建失败: {e}")

    # 测试 ResourceNotFoundError
    tests_total += 1
    try:
        error = ResourceNotFoundError("文档", "doc_123")
        assert "文档" in error.message
        assert error.code == ErrorCode.RESOURCE_NOT_FOUND
        assert error.details["resource_type"] == "文档"
        print("  ✓ ResourceNotFoundError 创建成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ ResourceNotFoundError 创建失败: {e}")

    # 测试 ValidationError
    tests_total += 1
    try:
        error = ValidationError("email", "invalid", "格式错误")
        assert "email" in error.message
        assert error.code == ErrorCode.INVALID_PARAMETER
        print("  ✓ ValidationError 创建成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ ValidationError 创建失败: {e}")

    # 测试 DocumentProcessingError
    tests_total += 1
    try:
        error = DocumentProcessingError("doc_123", "parsing", "解析失败")
        assert "doc_123" in error.message
        assert error.code == ErrorCode.DOCUMENT_PROCESSING_ERROR
        print("  ✓ DocumentProcessingError 创建成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ DocumentProcessingError 创建失败: {e}")

    # 测试 ReviewExecutionError
    tests_total += 1
    try:
        error = ReviewExecutionError("review_123", "rule_456", "执行失败")
        assert "review_123" in error.message
        assert error.code == ErrorCode.REVIEW_EXECUTION_ERROR
        print("  ✓ ReviewExecutionError 创建成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ ReviewExecutionError 创建失败: {e}")

    # 测试 RuleValidationError
    tests_total += 1
    try:
        error = RuleValidationError("rule_789", "参数无效")
        assert "rule_789" in error.message
        assert error.code == ErrorCode.RULE_VALIDATION_ERROR
        print("  ✓ RuleValidationError 创建成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ RuleValidationError 创建失败: {e}")

    print(f"\n通过: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("错误处理测试")
    print("=" * 60)

    tests_passed = 0
    tests_total = 0

    # 测试 handle_error
    tests_total += 1
    try:
        # 处理普通异常
        original_error = ValueError("测试错误")
        handled = handle_error(original_error, reraise=False)

        assert isinstance(handled, TrustLensError)
        assert handled.code == ErrorCode.INVALID_PARAMETER
        assert handled.original_error == original_error
        print("  ✓ handle_error 处理 ValueError 成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ handle_error 失败: {e}")

    # 测试错误响应生成
    tests_total += 1
    try:
        error = ResourceNotFoundError("规则", "rule_123")
        response = get_error_response(error)

        assert "code" in response
        assert "message" in response
        assert "timestamp" in response
        assert response["code"] == ErrorCode.RESOURCE_NOT_FOUND.value
        print("  ✓ get_error_response 成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ get_error_response 失败: {e}")

    # 测试业务事件日志
    tests_total += 1
    try:
        log_business_event("DOCUMENT_UPLOADED", "文档上传成功", {"doc_id": "doc_123"})
        print("  ✓ log_business_event 成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ log_business_event 失败: {e}")

    print(f"\n通过: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_error_conversion():
    """测试错误转换"""
    print("\n" + "=" * 60)
    print("错误转换测试")
    print("=" * 60)

    tests_passed = 0
    tests_total = 0

    # 测试 KeyError 转换
    tests_total += 1
    try:
        error = KeyError("missing_key")
        handled = handle_error(error, reraise=False)

        assert handled.code == ErrorCode.RESOURCE_NOT_FOUND
        assert "missing_key" in str(handled.details["missing_key"])
        print("  ✓ KeyError 转换成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ KeyError 转换失败: {e}")

    # 测试 PermissionError 转换
    tests_total += 1
    try:
        error = PermissionError("Access denied")
        handled = handle_error(error, reraise=False)

        assert handled.code == ErrorCode.FORBIDDEN
        print("  ✓ PermissionError 转换成功")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ PermissionError 转换失败: {e}")

    # 测试 reraise
    tests_total += 1
    try:
        error = ValueError("测试重新抛出")
        try:
            handle_error(error, reraise=True)
        except TrustLensError:
            print("  ✓ reraise 参数正常工作")
            tests_passed += 1
    except Exception as e:
        print(f"  ✗ reraise 测试失败: {e}")

    print(f"\n通过: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("错误处理模块测试")
    print("=" * 60)

    results = []

    # 运行所有测试
    results.append(("错误码测试", test_error_codes()))
    results.append(("错误创建测试", test_error_creation()))
    results.append(("错误处理测试", test_error_handling()))
    results.append(("错误转换测试", test_error_conversion()))

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
