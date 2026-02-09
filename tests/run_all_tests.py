"""
Test Runner
测试运行脚本 - 运行所有测试并生成报告
"""
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


def run_test(test_file: str) -> tuple[bool, str, float]:
    """
    运行单个测试文件

    Returns:
        (success, output, duration)
    """
    start_time = datetime.now()

    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=60,
        )

        duration = (datetime.now() - start_time).total_seconds()
        success = result.returncode == 0

        return success, result.stdout + result.stderr, duration
    except subprocess.TimeoutExpired:
        duration = (datetime.now() - start_time).total_seconds()
        return False, f"测试超时（{duration:.2f}s）", duration
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        return False, f"测试执行失败: {e}", duration


def main():
    """主测试运行器"""
    print("=" * 60)
    print("TrustLens AI - 测试运行器")
    print("=" * 60)

    tests_dir = Path(__file__).parent
    test_files = [
        "test_rule_schema.py",
        "test_chunk_schema.py",
        "test_review_result_schema.py",
        "test_document_state_schema.py",
        "test_rule_service.py",
        "test_rule_parser.py",
        "test_pdf_parser.py",
        "test_docx_parser.py",
        "test_chunker.py",
        "test_embedding.py",
        "test_query_builder.py",
        "test_review_prompt.py",
        "test_executor.py",
        "test_rule_api.py",
        "test_document_api.py",
        "test_review_api.py",
        "test_explain_prompt.py",
        "test_explain_api.py",
        "test_error_handler.py",
        "test_performance.py",
    ]

    all_results = []
    total_duration = 0

    print(f"\n发现 {len(test_files)} 个测试文件")
    print("-" * 60)

    # 运行所有测试
    for i, test_file in enumerate(test_files, 1):
        test_path = tests_dir / test_file

        if not test_path.exists():
            print(f"\n{i}. {test_file}")
            print(f"  ○ 文件不存在，跳过")
            continue

        print(f"\n{i}. {test_file}")
        print("-" * 60)

        success, output, duration = run_test(str(test_path))
        total_duration += duration

        all_results.append({
            "name": test_file,
            "success": success,
            "output": output,
            "duration": duration,
        })

        status = "✓ 通过" if success else "✗ 失败"
        print(f"  状态: {status}")
        print(f"  耗时: {duration:.2f}s")

        # 显示测试输出摘要
        if "✓ 所有测试通过" in output:
            print("  结果: 所有测试通过")
        elif "✅ 所有测试通过" in output:
            print("  结果: 所有测试通过")
        elif "失败" in output or "错误" in output:
            # 显示最后几行输出
            lines = output.split('\n')
            for line in lines[-3:]:
                if line.strip():
                    print(f"  {line}")

    # 生成测试报告
    print("\n" + "=" * 60)
    print("测试汇总")
    print("=" * 60)

    passed = sum(1 for r in all_results if r["success"])
    failed = sum(1 for r in all_results if not r["success"])
    total = len(all_results)

    print(f"\n总测试数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    print(f"总耗时: {total_duration:.2f}s")

    # 失败的测试
    if failed > 0:
        print("\n失败的测试:")
        for result in all_results:
            if not result["success"]:
                print(f"  - {result['name']}")

    # 生成报告文件
    report_path = tests_dir / "test_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("TrustLens AI - 测试报告\n")
        f.write("=" * 60 + "\n")
        f.write(f"生成时间: {datetime.now().isoformat()}\n")
        f.write(f"总测试数: {total}\n")
        f.write(f"通过: {passed}\n")
        f.write(f"失败: {failed}\n")
        f.write(f"通过率: {passed/total*100:.1f}%\n")
        f.write(f"总耗时: {total_duration:.2f}s\n")
        f.write("\n" + "=" * 60 + "\n")
        f.write("详细结果\n")
        f.write("=" * 60 + "\n\n")

        for result in all_results:
            f.write(f"## {result['name']}\n")
            f.write(f"状态: {'✓ 通过' if result['success'] else '✗ 失败'}\n")
            f.write(f"耗时: {result['duration']:.2f}s\n")
            f.write(f"\n输出:\n{result['output']}\n")
            f.write("\n" + "-" * 60 + "\n\n")

    print(f"\n测试报告已保存: {report_path}")

    print("\n" + "=" * 60)
    if failed == 0:
        print("✅ 所有测试通过！")
    else:
        print(f"⚠️  {failed} 个测试失败")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
