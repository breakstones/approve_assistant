"""
Performance Test
性能测试脚本
"""
import sys
import os
import time
import asyncio
from pathlib import Path

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from main import app


def test_api_performance():
    """API 性能测试"""
    print("=" * 60)
    print("API 性能测试")
    print("=" * 60)

    client = TestClient(app)

    # 测试结果存储
    results = []

    # 1. 根端点
    print("\n1. 根端点")
    print("-" * 60)
    start = time.time()
    response = client.get("/")
    elapsed = time.time() - start
    results.append(("GET /", elapsed, response.status_code == 200))
    print(f"  响应时间: {elapsed*1000:.2f}ms")
    print(f"  状态: {'✓ 通过' if response.status_code == 200 else '✗ 失败'}")

    # 2. 列出规则
    print("\n2. 列出规则")
    print("-" * 60)
    start = time.time()
    response = client.get("/api/rules")
    elapsed = time.time() - start
    results.append(("GET /api/rules", elapsed, response.status_code == 200))
    print(f"  响应时间: {elapsed*1000:.2f}ms")
    print(f"  状态: {'✓ 通过' if response.status_code == 200 else '✗ 失败'}")

    # 3. 列出文档
    print("\n3. 列出文档")
    print("-" * 60)
    start = time.time()
    response = client.get("/api/documents")
    elapsed = time.time() - start
    results.append(("GET /api/documents", elapsed, response.status_code == 200))
    print(f"  响应时间: {elapsed*1000:.2f}ms")
    print(f"  状态: {'✓ 通过' if response.status_code == 200 else '✗ 失败'}")

    # 4. 列出审查任务
    print("\n4. 列出审查任务")
    print("-" * 60)
    start = time.time()
    response = client.get("/api/review")
    elapsed = time.time() - start
    results.append(("GET /api/review", elapsed, response.status_code == 200))
    print(f"  响应时间: {elapsed*1000:.2f}ms")
    print(f"  状态: {'✓ 通过' if response.status_code == 200 else '✗ 失败'}")

    # 5. 列出会话
    print("\n5. 列出会话")
    print("-" * 60)
    start = time.time()
    response = client.get("/api/explain/sessions")
    elapsed = time.time() - start
    results.append(("GET /api/explain/sessions", elapsed, response.status_code == 200))
    print(f"  响应时间: {elapsed*1000:.2f}ms")
    print(f"  状态: {'✓ 通过' if response.status_code == 200 else '✗ 失败'}")

    # 汇总结果
    print("\n" + "=" * 60)
    print("性能测试汇总")
    print("=" * 60)

    for name, elapsed, passed in results:
        status = "✓" if elapsed < 1.0 else "⚠" if elapsed < 3.0 else "✗"
        print(f"  {status} {name}: {elapsed*1000:.2f}ms")

    avg_time = sum(r[1] for r in results) / len(results)
    print(f"\n  平均响应时间: {avg_time*1000:.2f}ms")

    # 性能判断
    all_fast = all(r[1] < 3.0 for r in results)
    if all_fast:
        print("\n✅ 所有 API 响应时间 < 3s，性能达标！")
        return True
    else:
        print("\n⚠️  部分 API 响应时间超过 3s，需要优化")
        return False


def test_concurrent_requests():
    """并发请求测试"""
    print("\n" + "=" * 60)
    print("并发请求测试")
    print("=" * 60)

    client = TestClient(app)
    concurrent = 5

    print(f"\n发起 {concurrent} 个并发请求...")

    import threading
    import queue

    results = queue.Queue()

    def make_request(index):
        start = time.time()
        try:
            response = client.get("/api/rules")
            elapsed = time.time() - start
            results.put((index, elapsed, response.status_code == 200))
        except Exception as e:
            results.put((index, -1, False, str(e)))

    # 创建并启动线程
    threads = []
    start_time = time.time()

    for i in range(concurrent):
        t = threading.Thread(target=make_request, args=(i,))
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join()

    total_time = time.time() - start_time

    # 收集结果
    request_results = []
    while not results.empty():
        request_results.append(results.get())

    request_results.sort(key=lambda x: x[0])

    print("\n请求结果:")
    all_success = True
    for index, elapsed, success, *rest in request_results:
        error_msg = rest[0] if not success and rest else ""
        status = "✓" if success else "✗"
        print(f"  {status} 请求 {index + 1}: {elapsed*1000:.2f}ms {error_msg}")
        if not success:
            all_success = False

    print(f"\n  总耗时: {total_time*1000:.2f}ms")
    print(f"  平均每请求: {total_time/concurrent*1000:.2f}ms")

    if all_success:
        print("\n✅ 并发测试通过，支持 5+ 并发请求！")
        return True
    else:
        print("\n⚠️  部分请求失败")
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("性能测试套件")
    print("=" * 60)

    results = []

    # 运行所有测试
    results.append(("API 性能测试", test_api_performance()))
    results.append(("并发请求测试", test_concurrent_requests()))

    # 输出结果
    print("\n" + "=" * 60)
    print("性能测试结果汇总")
    print("=" * 60)

    all_pass = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_pass = False

    print("\n" + "=" * 60)
    if all_pass:
        print("✅ 所有性能测试通过！")
    else:
        print("⚠️  部分性能测试未通过")
    print("=" * 60)

    return all_pass


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
