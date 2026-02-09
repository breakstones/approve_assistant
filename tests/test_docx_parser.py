"""
Test DOCX Parser
测试 Word 文档解析功能
"""
import sys
import os
from pathlib import Path

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from document.docx_parser import DOCXParser, get_docx_parser, parse_docx


def test_docx_parser():
    """测试 Word 文档解析器"""

    print("=" * 60)
    print("Word 文档解析器测试")
    print("=" * 60)

    # 检查 python-docx 是否安装
    try:
        from docx import Document
        print("✓ python-docx 已安装")
    except ImportError:
        print("✗ python-docx 未安装，尝试安装...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "python-docx", "-q"],
                       check=False)
        from docx import Document
        print("✓ python-docx 安装成功")

    print("\n1. 测试解析器创建")
    print("-" * 60)

    try:
        parser = DOCXParser()
        print(f"✓ 创建 DOCX 解析器成功，引擎: {parser.engine}")
    except Exception as e:
        print(f"✗ DOCX 解析器创建失败: {e}")
        return False

    print("\n2. 测试真实文档解析")
    print("-" * 60)

    # 查找测试文档
    test_docx = Path(__file__).parent / "contract_files" / "T2栋1506房长沙睿瑞科技租赁合同.docx"

    if not test_docx.exists():
        print(f"○ 测试文档不存在: {test_docx}")
        print("   跳过实际解析测试")
        return True

    print(f"测试文档: {test_docx.name}")

    try:
        # 解析文档
        pages = parser.parse(str(test_docx))

        print(f"✓ 解析成功，共 {len(pages)} 页")

        # 显示第一页信息
        if pages:
            page = pages[0]
            print(f"\n第一页信息:")
            print(f"  页码: {page.page_number}")
            print(f"  尺寸: {page.width:.1f} x {page.height:.1f}")
            print(f"  文本块数量: {len(page.text_blocks)}")

            # 显示前3个文本块
            print(f"\n前3个文本块:")
            for i, block in enumerate(page.text_blocks[:3]):
                preview = block.text[:50] + "..." if len(block.text) > 50 else block.text
                print(f"  [{i+1}] {preview}")

        # 测试元数据提取
        print(f"\n3. 测试元数据提取")
        print("-" * 60)

        metadata = parser.extract_metadata(str(test_docx))
        print(f"✓ 元数据提取成功")
        print(f"  文件名: {metadata['file_name']}")
        print(f"  文件大小: {metadata['file_size']:,} bytes")
        print(f"  估计页数: {metadata['pages']}")
        print(f"  标题: {metadata['title'] or '(无)'}")
        print(f"  作者: {metadata['author'] or '(无)'}")

        # 测试便捷函数
        print(f"\n4. 测试便捷函数")
        print("-" * 60)

        parser2 = get_docx_parser()
        print(f"✓ get_docx_parser() 返回: {parser2.engine}")

        pages2 = parse_docx(str(test_docx))
        print(f"✓ parse_docx() 返回 {len(pages2)} 页")

        # 验证数据结构
        print(f"\n5. 验证数据结构")
        print("-" * 60)

        from document.pdf_parser import BoundingBox, TextBlock, PDFPage

        # 验证页面对象
        assert isinstance(pages, list), "pages 应该是列表"
        if pages:
            assert isinstance(pages[0], PDFPage), "page 应该是 PDFPage 对象"
            assert pages[0].page_number > 0, "页码应该大于0"
            assert pages[0].width > 0, "宽度应该大于0"
            assert pages[0].height > 0, "高度应该大于0"
            assert isinstance(pages[0].text_blocks, list), "text_blocks 应该是列表"

            # 验证文本块对象
            if pages[0].text_blocks:
                block = pages[0].text_blocks[0]
                assert isinstance(block, TextBlock), "block 应该是 TextBlock 对象"
                assert isinstance(block.text, str), "text 应该是字符串"
                assert isinstance(block.bbox, BoundingBox), "bbox 应该是 BoundingBox 对象"
                assert block.bbox.page_width is not None, "bbox 应该有 page_width"
                assert block.bbox.page_height is not None, "bbox 应该有 page_height"

        print("✓ 所有数据结构验证通过")

    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("Word 文档解析器测试完成")
    print("=" * 60)

    return True


if __name__ == "__main__":
    success = test_docx_parser()
    sys.exit(0 if success else 1)
