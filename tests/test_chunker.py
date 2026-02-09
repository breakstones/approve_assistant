"""
Test Document Chunker
测试智能文档切分功能
"""
import sys
import os
from pathlib import Path

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from document.chunker import DocumentChunker, Chunk, chunk_document
from document.pdf_parser import PDFPage, TextBlock, BoundingBox


def create_test_page() -> PDFPage:
    """创建测试页面"""
    # 创建测试文本块
    blocks = [
        TextBlock(
            text="写字楼租赁合同",
            page=1,
            bbox=BoundingBox(x1=50, y1=50, x2=300, y2=70, page_width=595, page_height=842),
            font_size=16,
            is_bold=True,
        ),
        TextBlock(
            text="合同编号：LEASE-2024-001",
            page=1,
            bbox=BoundingBox(x1=50, y1=80, x2=300, y2=100, page_width=595, page_height=842),
        ),
        TextBlock(
            text="第一条 租赁标的",
            page=1,
            bbox=BoundingBox(x1=50, y1=120, x2=200, y2=140, page_width=595, page_height=842),
            font_size=14,
            is_bold=True,
        ),
        TextBlock(
            text="出租方将位于长沙市高新区创新大厦A座15楼的房屋出租给承租方使用。",
            page=1,
            bbox=BoundingBox(x1=50, y1=150, x2=500, y2=170, page_width=595, page_height=842),
        ),
        TextBlock(
            text="第二条 租金及支付方式",
            page=1,
            bbox=BoundingBox(x1=50, y1=190, x2=250, y2=210, page_width=595, page_height=842),
            font_size=14,
            is_bold=True,
        ),
        TextBlock(
            text="每月租金为人民币5000元整。承租方应在每月5日前支付当月租金。",
            page=1,
            bbox=BoundingBox(x1=50, y1=220, x2=500, y2=240, page_width=595, page_height=842),
        ),
        TextBlock(
            text="付款方式为银行转账，开户行：中国银行长沙分行，账号：6217-xxxx-xxxx-xxxx。",
            page=1,
            bbox=BoundingBox(x1=50, y1=250, x2=500, y2=270, page_width=595, page_height=842),
        ),
        TextBlock(
            text="第三条 保密义务",
            page=1,
            bbox=BoundingBox(x1=50, y1=290, x2=200, y2=310, page_width=595, page_height=842),
            font_size=14,
            is_bold=True,
        ),
        TextBlock(
            text="双方应对在合同履行过程中知悉的对方商业秘密承担保密义务。",
            page=1,
            bbox=BoundingBox(x1=50, y1=320, x2=500, y2=340, page_width=595, page_height=842),
        ),
        TextBlock(
            text="未经对方书面同意，不得向任何第三方披露。",
            page=1,
            bbox=BoundingBox(x1=50, y1=350, x2=400, y2=370, page_width=595, page_height=842),
        ),
        TextBlock(
            text="第四条 违约责任",
            page=1,
            bbox=BoundingBox(x1=50, y1=390, x2=200, y2=410, page_width=595, page_height=842),
            font_size=14,
            is_bold=True,
        ),
        TextBlock(
            text="承租方逾期支付租金的，每逾期一日，应按日租金的千分之五支付违约金。",
            page=1,
            bbox=BoundingBox(x1=50, y1=420, x2=500, y2=440, page_width=595, page_height=842),
        ),
        TextBlock(
            text="第五条 争议解决",
            page=1,
            bbox=BoundingBox(x1=50, y1=460, x2=200, y2=480, page_width=595, page_height=842),
            font_size=14,
            is_bold=True,
        ),
        TextBlock(
            text="本合同履行过程中发生的争议，双方应友好协商解决。",
            page=1,
            bbox=BoundingBox(x1=50, y1=490, x2=500, y2=510, page_width=595, page_height=842),
        ),
        TextBlock(
            text="协商不成的，任何一方均可向长沙市人民法院提起诉讼。",
            page=1,
            bbox=BoundingBox(x1=50, y1=520, x2=500, y2=540, page_width=595, page_height=842),
        ),
    ]

    return PDFPage(
        page_number=1,
        width=595,
        height=842,
        text_blocks=blocks,
        raw_text="\n".join([b.text for b in blocks]),
    )


def test_chunker():
    """测试文档切分器"""

    print("=" * 60)
    print("智能文档切分器测试")
    print("=" * 60)

    print("\n1. 测试切分器创建")
    print("-" * 60)

    try:
        chunker = DocumentChunker(
            min_chunk_size=50,
            max_chunk_size=300,
            target_chunk_size=150,
        )
        print(f"✓ 创建切分器成功")
        print(f"  - 最小 chunk 大小: {chunker.min_chunk_size} tokens")
        print(f"  - 目标 chunk 大小: {chunker.target_chunk_size} tokens")
        print(f"  - 最大 chunk 大小: {chunker.max_chunk_size} tokens")
    except Exception as e:
        print(f"✗ 切分器创建失败: {e}")
        return False

    print("\n2. 测试文档切分")
    print("-" * 60)

    try:
        # 创建测试页面
        test_page = create_test_page()

        # 执行切分
        chunks = chunker.chunk([test_page], doc_id="test_doc")

        print(f"✓ 切分成功，生成 {len(chunks)} 个 chunks")

        # 显示每个 chunk 的信息
        for i, chunk in enumerate(chunks):
            preview = chunk.text[:60] + "..." if len(chunk.text) > 60 else chunk.text
            print(f"\nChunk {i + 1}:")
            print(f"  ID: {chunk.chunk_id}")
            print(f"  页码: {chunk.page}")
            print(f"  条款类型: {chunk.clause_hint}")
            print(f"  Token 数: {chunk.token_count}")
            print(f"  文本: {preview}")

    except Exception as e:
        print(f"✗ 切分失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n3. 验证 Chunk Schema")
    print("-" * 60)

    try:
        # 验证第一个 chunk 的数据结构
        if chunks:
            chunk = chunks[0]

            # 检查必需字段
            required_fields = [
                "chunk_id", "doc_id", "page", "text", "bbox"
            ]
            chunk_dict = chunk.to_dict()

            for field in required_fields:
                if field not in chunk_dict:
                    print(f"✗ 缺少必需字段: {field}")
                    return False

            # 验证 chunk_id 格式
            import re
            pattern = r'^[a-zA-Z0-9_]+_p\d+_c\d+$'
            if not re.match(pattern, chunk.chunk_id):
                print(f"✗ chunk_id 格式错误: {chunk.chunk_id}")
                return False

            # 验证 bbox
            bbox = chunk.bbox
            if not isinstance(bbox, dict):
                print(f"✗ bbox 类型错误: {type(bbox)}")
                return False

            required_bbox_fields = ["x1", "y1", "x2", "y2"]
            for field in required_bbox_fields:
                if field not in bbox:
                    print(f"✗ bbox 缺少字段: {field}")
                    return False

            print("✓ Chunk Schema 验证通过")

    except Exception as e:
        print(f"✗ Schema 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n4. 测试条款类型识别")
    print("-" * 60)

    try:
        # 统计条款类型分布
        clause_types = {}
        for chunk in chunks:
            clause_type = chunk.clause_hint
            clause_types[clause_type] = clause_types.get(clause_type, 0) + 1

        print(f"条款类型分布:")
        for clause_type, count in sorted(clause_types.items()):
            print(f"  - {clause_type}: {count}")

    except Exception as e:
        print(f"✗ 条款类型识别测试失败: {e}")
        return False

    print("\n5. 测试 Token 估算")
    print("-" * 60)

    try:
        # 检查 token 数是否在合理范围内
        for i, chunk in enumerate(chunks):
            if chunk.token_count < chunker.min_chunk_size:
                print(f"⚠ Chunk {i+1} token 数 ({chunk.token_count}) 小于最小值 ({chunker.min_chunk_size})")
            elif chunk.token_count > chunker.max_chunk_size:
                print(f"⚠ Chunk {i+1} token 数 ({chunk.token_count}) 超过最大值 ({chunker.max_chunk_size})")

        print("✓ Token 估算检查完成")

    except Exception as e:
        print(f"✗ Token 估算测试失败: {e}")
        return False

    print("\n6. 测试便捷函数")
    print("-" * 60)

    try:
        # 测试便捷函数
        chunks2 = chunk_document([test_page], doc_id="test_doc2")

        print(f"✓ chunk_document() 返回 {len(chunks2)} 个 chunks")

    except Exception as e:
        print(f"✗ 便捷函数测试失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("智能文档切分器测试完成")
    print("=" * 60)

    print("\n✅ 所有测试通过！")

    return True


if __name__ == "__main__":
    success = test_chunker()
    sys.exit(0 if success else 1)
