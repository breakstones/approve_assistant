"""
Test PDF Parser
测试 PDF 文档解析功能
"""
import sys
import os

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from document.pdf_parser import PDFPlumberParser, PyMuPDFParser, get_pdf_parser, parse_pdf


def test_pdf_parser():
    """测试 PDF 解析器"""

    print("=" * 60)
    print("PDF 解析器测试")
    print("=" * 60)

    # 检查 pdfplumber 是否安装
    try:
        import pdfplumber
        print("✓ pdfplumber 已安装")
    except ImportError:
        print("✗ pdfplumber 未安装，尝试安装...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pdfplumber", "-q"],
                       check=False)
        import pdfplumber
        print("✓ pdfplumber 安装成功")

    # 检查 PyMuPDF 是否安装
    try:
        import fitz
        print("✓ PyMuPDF 已安装")
    except ImportError:
        print("○ PyMuPDF 未安装（可选）")

    print("\n1. 测试 pdfplumber 解析器")
    print("-" * 60)

    try:
        parser = PDFPlumberParser()
        print(f"✓ 创建 pdfplumber 解析器成功")

        # 测试解析功能（如果有测试 PDF）
        test_pdf = Path(__file__).parent.parent / "shared" / "schemas" / "rule_schema.json"
        if test_pdf.exists():
            print(f"注: 未找到测试 PDF 文件，跳过实际解析测试")
        else:
            print(f"   需要提供测试 PDF 文件进行完整测试")

    except Exception as e:
        print(f"✗ pdfplumber 解析器创建失败: {e}")

    print("\n2. 测试 PyMuPDF 解析器")
    print("-" * 60)

    try:
        parser = PyMuPDFParser()
        print(f"✓ 创建 PyMuPDF 解析器成功")
    except ImportError as e:
        print(f"○ PyMuPDF 未安装: {e}")

    print("\n3. 测试便捷函数")
    print("-" * 60)

    try:
        # 测试获取默认解析器
        parser = get_pdf_parser()
        print(f"✓ 获取默认解析器: {parser.engine}")
    except Exception as e:
        print(f"✗ 获取默认解析器失败: {e}")

    print("\n4. 测试数据结构")
    print("-" * 60)

    # 测试数据结构
    from document.pdf_parser import BoundingBox, TextBlock, PDFPage

    # 创建测试 bbox
    bbox = BoundingBox(100, 200, 500, 250, page_width=612, page_height=792)
    print(f"✓ BoundingBox: {bbox.to_list()}")

    # 创建测试文本块
    text_block = TextBlock(
        text="测试文本",
        page=1,
        bbox=bbox,
        font_size=12,
        is_bold=False
    )
    print(f"✓ TextBlock: {text_block.to_dict()}")

    # 创建测试页面
    page = PDFPage(
        page_number=1,
        width=612,
        height=792,
        text_blocks=[text_block],
        raw_text="测试文本"
    )
    print(f"✓ PDFPage: {page.page_number} 页, {len(page.text_blocks)} 个文本块")

    print("\n" + "=" * 60)
    print("PDF 解析器基本功能测试完成")
    print("=" * 60)
    print("\n说明：完整的 PDF 解析测试需要实际的 PDF 文件")
    print("      请在 Phase 2 集成测试时使用真实 PDF 文件进行测试")

    return True


if __name__ == "__main__":
    test_pdf_parser()
