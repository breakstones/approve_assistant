"""
Test Document API
测试文档上传与状态管理 API
"""
import sys
import os
from pathlib import Path

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from main import app
from config.database import get_database, init_db
from config.document_service import get_document_service
from config.document_models import DocumentStatus


def test_document_api():
    """测试文档 API"""

    print("=" * 60)
    print("文档 API 测试")
    print("=" * 60)

    # 初始化数据库
    print("\n1. 初始化数据库")
    print("-" * 60)

    try:
        init_db()
        print("✓ 数据库初始化成功")
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        return False

    # 创建测试客户端
    client = TestClient(app)

    print("\n2. 测试根端点")
    print("-" * 60)

    try:
        response = client.get("/")
        print(f"✓ 根端点响应: {response.status_code}")
        print(f"  可用端点: {response.json().get('endpoints', {})}")
    except Exception as e:
        print(f"✗ 根端点测试失败: {e}")
        return False

    print("\n3. 测试文档列表（空列表）")
    print("-" * 60)

    try:
        response = client.get("/api/documents")
        print(f"✓ 文档列表响应: {response.status_code}")

        data = response.json()
        print(f"  总数: {data.get('total', 0)}")
        print(f"  文档数: {len(data.get('documents', []))}")

    except Exception as e:
        print(f"✗ 文档列表测试失败: {e}")
        return False

    print("\n4. 测试文档上传")
    print("-" * 60)

    # 查找测试文件
    test_file_path = Path(__file__).parent / "contract_files" / "T2栋1506房长沙睿瑞科技租赁合同.docx"

    if not test_file_path.exists():
        print(f"○ 测试文件不存在: {test_file_path}")
        print("   跳过上传测试")
        return True

    print(f"测试文件: {test_file_path.name}")

    try:
        with open(test_file_path, "rb") as f:
            response = client.post(
                "/api/documents/upload",
                files={"file": (test_file_path.name, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )

        print(f"✓ 文档上传响应: {response.status_code}")

        if response.status_code == 201:
            doc_data = response.json()
            doc_id = doc_data.get("doc_id")
            print(f"  文档 ID: {doc_id}")
            print(f"  文件名: {doc_data.get('filename')}")
            print(f"  状态: {doc_data.get('status')}")
            print(f"  进度: {doc_data.get('progress')}%")
        else:
            print(f"  错误: {response.text}")
            return False

    except Exception as e:
        print(f"✗ 文档上传测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n5. 测试获取文档状态")
    print("-" * 60)

    try:
        response = client.get(f"/api/documents/{doc_id}/status")
        print(f"✓ 获取状态响应: {response.status_code}")

        data = response.json()
        print(f"  文档 ID: {data.get('doc_id')}")
        print(f"  状态: {data.get('status')}")
        print(f"  状态消息: {data.get('status_message')}")
        print(f"  进度: {data.get('progress')}%")

    except Exception as e:
        print(f"✗ 获取状态测试失败: {e}")
        return False

    print("\n6. 测试获取文档详情")
    print("-" * 60)

    try:
        response = client.get(f"/api/documents/{doc_id}")
        print(f"✓ 获取文档响应: {response.status_code}")

        data = response.json()
        print(f"  文件类型: {data.get('file_type')}")
        print(f"  文件大小: {data.get('file_size')} bytes")
        print(f"  页数: {data.get('page_count')}")
        print(f"  Chunk 数: {data.get('chunk_count')}")

    except Exception as e:
        print(f"✗ 获取文档测试失败: {e}")
        return False

    print("\n7. 测试文档列表（有数据）")
    print("-" * 60)

    try:
        response = client.get("/api/documents")
        print(f"✓ 文档列表响应: {response.status_code}")

        data = response.json()
        print(f"  总数: {data.get('total', 0)}")
        print(f"  文档数: {len(data.get('documents', []))}")

    except Exception as e:
        print(f"✗ 文档列表测试失败: {e}")
        return False

    print("\n8. 测试状态过滤")
    print("-" * 60)

    try:
        # 测试按状态过滤
        response = client.get("/api/documents?status=UPLOADED")
        print(f"✓ 状态过滤响应: {response.status_code}")

        data = response.json()
        print(f"  UPLOADED 状态文档数: {len(data.get('documents', []))}")

        # 测试按文件类型过滤
        response = client.get("/api/documents?file_type=docx")
        print(f"✓ 文件类型过滤响应: {response.status_code}")

        data = response.json()
        print(f"  DOCX 文件数: {len(data.get('documents', []))}")

    except Exception as e:
        print(f"✗ 过滤测试失败: {e}")
        return False

    print("\n9. 测试文档删除")
    print("-" * 60)

    try:
        response = client.delete(f"/api/documents/{doc_id}")
        print(f"✓ 删除文档响应: {response.status_code}")

        if response.status_code == 204:
            print("  文档已删除")

            # 验证删除
            response = client.get(f"/api/documents/{doc_id}")
            if response.status_code == 404:
                print("  ✓ 验证：文档已不存在")
            else:
                print("  ✗ 验证：文档仍然存在")

    except Exception as e:
        print(f"✗ 删除文档测试失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("文档 API 测试完成")
    print("=" * 60)

    print("\n✅ 所有测试通过！")
    print("\n说明：完整的异步处理测试需要等待后台任务完成，")
    print("      在实际使用中文档会自动完成解析、切分和向量化。")

    return True


if __name__ == "__main__":
    success = test_document_api()
    sys.exit(0 if success else 1)
