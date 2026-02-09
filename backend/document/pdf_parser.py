"""
TrustLens AI - PDF Document Parser
PDF 文档解析模块，保留页码与坐标信息
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json

# 检查并安装 pdfplumber
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

# 检查并安装 PyMuPDF
try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


@dataclass
class BoundingBox:
    """边界框坐标"""
    x1: float
    y1: float
    x2: float
    y2: float
    page_width: Optional[float] = None
    page_height: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x1": self.x1,
            "y1": self.y1,
            "x2": self.x2,
            "y2": self.y2,
            "page_width": self.page_width,
            "page_height": self.page_height,
        }

    def to_list(self) -> List[float]:
        """转换为列表格式 [x1, y1, x2, y2]"""
        return [self.x1, self.y1, self.x2, self.y2]


@dataclass
class TextBlock:
    """文本块"""
    text: str
    page: int
    bbox: BoundingBox
    char_start: int = 0
    char_end: int = 0
    font_size: Optional[float] = None
    font_name: Optional[str] = None
    is_bold: bool = False
    is_italic: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "page": self.page,
            "bbox": self.bbox.to_dict(),
            "char_start": self.char_start,
            "char_end": self.char_end,
            "font_size": self.font_size,
            "font_name": self.font_name,
            "is_bold": self.is_bold,
            "is_italic": self.is_italic,
        }


@dataclass
class PDFPage:
    """PDF 页面"""
    page_number: int
    width: float
    height: float
    text_blocks: List[TextBlock]
    raw_text: str = ""

    def get_full_text(self) -> str:
        """获取页面完整文本"""
        if self.raw_text:
            return self.raw_text
        return "\n".join([block.text for block in self.text_blocks])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "text_blocks": [block.to_dict() for block in self.text_blocks],
            "raw_text": self.raw_text,
        }


class PDFParser:
    """PDF 解析器基类"""

    def __init__(self):
        self.engine = "pdfplumber"  # 默认使用 pdfplumber

    def parse(self, file_path: str, extract_bbox: bool = True) -> List[PDFPage]:
        """
        解析 PDF 文档

        Args:
            file_path: PDF 文件路径
            extract_bbox: 是否提取文本块坐标

        Returns:
            解析后的页面列表
        """
        raise NotImplementedError("Subclass must implement parse method")


class PDFPlumberParser(PDFParser):
    """基于 pdfplumber 的 PDF 解析器"""

    def __init__(self):
        super().__init__()
        self.engine = "pdfplumber"

        try:
            import pdfplumber
            self.pdfplumber = pdfplumber
        except ImportError:
            raise ImportError("pdfplumber is not installed. Run: pip install pdfplumber")

    def parse(self, file_path: str, extract_bbox: bool = True) -> List[PDFPage]:
        """
        解析 PDF 文档

        Args:
            file_path: PDF 文件路径
            extract_bbox: 是否提取文本块坐标

        Returns:
            解析后的页面列表
        """
        pages = []

        try:
            with self.pdfplumber.open(file_path) as pdf:
                for i, pdf_page in enumerate(pdf.pages, start=1):
                    # 获取页面尺寸
                    page_width = float(pdf_page.width)
                    page_height = float(pdf_page.height)

                    # 提取文本
                    text = pdf_page.extract_text()

                    # 提取文本块
                    text_blocks = []
                    if extract_bbox:
                        words = pdf_page.extract_words()
                        for word in words:
                            # 过滤掉空文本
                            if not word.get('text'):
                                continue

                            # 获取字符位置
                            x0 = word.get('x0', 0)
                            y0 = word.get('top', 0)
                            x1 = word.get('x1', x0)
                            y1 = word.get('bottom', y0)

                            # 处理非数字坐标
                            try:
                                x0 = float(x0)
                                y0 = float(y0)
                                x1 = float(x1)
                                y1 = float(y1)
                            except (ValueError, TypeError):
                                continue

                            bbox = BoundingBox(
                                x1=min(x0, x1),
                                y1=min(y0, y1),
                                x2=max(x0, x1),
                                y2=max(y0, y1),
                                page_width=page_width,
                                page_height=page_height,
                            )

                            text_blocks.append(TextBlock(
                                text=word['text'],
                                page=i,
                                bbox=bbox,
                                font_size=word.get('size', None),
                                is_bold='bold' in word.get('fontname', '').lower(),
                            ))

                    # 如果没有提取到文本块，创建一个包含整页文本的块
                    if not text_blocks and text.strip():
                        # 无法获取精确坐标，使用页面边界
                        bbox = BoundingBox(
                            x1=0,
                            y1=0,
                            x2=page_width,
                            y2=page_height,
                            page_width=page_width,
                            page_height=page_height,
                        )
                        text_blocks.append(TextBlock(
                            text=text.strip(),
                            page=i,
                            bbox=bbox,
                        ))

                    page = PDFPage(
                        page_number=i,
                        width=page_width,
                        height=page_height,
                        text_blocks=text_blocks,
                        raw_text=text,
                    )
                    pages.append(page)

        except Exception as e:
            raise RuntimeError(f"PDF 解析失败: {str(e)}")

        return pages

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        提取 PDF 元数据

        Args:
            file_path: PDF 文件路径

        Returns:
            元数据字典
        """
        metadata = {
            "file_name": Path(file_path).name,
            "file_size": os.path.getsize(file_path),
            "pages": 0,
            "title": "",
            "author": "",
            "subject": "",
            "creator": "",
            "producer": "",
            "creation_date": "",
            "modification_date": "",
        }

        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                # 获取页数
                metadata["pages"] = len(pdf.pages)

                # 提取元数据
                if hasattr(pdf, 'metadata'):
                    pdf_meta = pdf.metadata
                    if pdf_meta:
                        metadata.update({
                            "title": pdf_meta.get('Title', ''),
                            "author": pdf_meta.get('Author', ''),
                            "subject": pdf_meta.get('Subject', ''),
                            "creator": pdf_meta.get('Creator', ''),
                            "producer": pdf_meta.get('Producer', ''),
                            "creation_date": pdf_meta.get('CreationDate', ''),
                        })

        except Exception as e:
            print(f"Warning: Failed to extract metadata: {e}")

        return metadata


class PyMuPDFParser(PDFParser):
    """基于 PyMuPDF (fitz) 的 PDF 解析器"""

    def __init__(self):
        super().__init__()
        self.engine = "PyMuPDF"

        try:
            import fitz  # PyMuPDF
            self.fitz = fitz
        except ImportError:
            raise ImportError("PyMuPDF is not installed. Run: pip install PyMuPDF")

    def parse(self, file_path: str, extract_bbox: bool = True) -> List[PDFPage]:
        """
        解析 PDF 文档

        Args:
            file_path: PDF 文件路径
            extract_bbox: 是否提取文本块坐标

        Returns:
            解析后的页面列表
        """
        pages = []

        try:
            doc = self.fitz.open(file_path)

            for page_num in range(doc.page_count):
                page = doc[page_num]

                # 获取页面尺寸
                rect = page.rect
                page_width = rect.width
                page_height = rect.height

                # 提取文本
                text = page.get_text()

                # 提取文本块
                text_blocks = []
                if extract_bbox:
                    blocks = page.get_text("dict")["blocks"]

                    for block in blocks:
                        if "lines" not in block:
                            continue

                        for line in block["lines"]:
                            if "spans" not in line:
                                continue

                            for span in line["spans"]:
                                span_text = span.get("text", "")
                                if not span_text:
                                    continue

                                # 获取边界框
                                bbox = span.get("bbox", None)
                                if bbox:
                                    x0, y0, x1, y1 = bbox
                                    bbox_obj = BoundingBox(
                                        x1=float(x0),
                                        y1=float(y0),
                                        x2=float(x1),
                                        y2=float(y1),
                                        page_width=page_width,
                                        page_height=page_height,
                                    )
                                else:
                                    bbox_obj = BoundingBox(
                                        x1=0,
                                        y1=0,
                                        x2=page_width,
                                        y2=page_height,
                                        page_width=page_width,
                                        page_height=page_height,
                                    )

                                text_blocks.append(TextBlock(
                                    text=span_text,
                                    page=page_num + 1,
                                    bbox=bbox_obj,
                                    font_size=span.get("size", None),
                                    font_name=span.get("font", None),
                                ))

                # 如果没有提取到文本块，创建一个包含整页文本的块
                if not text_blocks and text.strip():
                    bbox = BoundingBox(
                        x1=0,
                        y1=0,
                        x2=page_width,
                        y2=page_height,
                        page_width=page_width,
                        page_height=page_height,
                    )
                    text_blocks.append(TextBlock(
                        text=text.strip(),
                        page=page_num + 1,
                        bbox=bbox,
                    ))

                page_obj = PDFPage(
                    page_number=page_num + 1,
                    width=page_width,
                    height=page_height,
                    text_blocks=text_blocks,
                    raw_text=text,
                )
                pages.append(page_obj)

            doc.close()

        except Exception as e:
            raise RuntimeError(f"PDF 解析失败: {str(e)}")

        return pages

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取 PDF 元数据"""
        metadata = {
            "file_name": Path(file_path).name,
            "file_size": os.path.getsize(file_path),
            "pages": 0,
            "title": "",
            "author": "",
            "subject": "",
            "creator": "",
            "producer": "",
            "creation_date": "",
        }

        try:
            doc = self.fitz.open(file_path)
            metadata["pages"] = doc.page_count

            # 提取元数据
            pdf_meta = doc.metadata
            if pdf_meta:
                metadata.update({
                    "title": pdf_meta.get("title", ""),
                    "author": pdf_meta.get("author", ""),
                    "subject": pdf_meta.get("subject", ""),
                    "creator": pdf_meta.get("creator", ""),
                    "producer": pdf_meta.get("producer", ""),
                    "creation_date": pdf_meta.get("creationDate", ""),
                })
            doc.close()

        except Exception as e:
            print(f"Warning: Failed to extract metadata: {e}")

        return metadata


def get_pdf_parser(engine: str = "pdfplumber") -> PDFParser:
    """
    获取 PDF 解析器实例

    Args:
        engine: 解析引擎类型 ("pdfplumber" 或 "PyMuPDF")

    Returns:
        PDF 解析器实例
    """
    if engine == "PyMuPDF":
        return PyMuPDFParser()
    return PDFPlumberParser()


def parse_pdf(file_path: str, engine: str = "pdfplumber", extract_bbox: bool = True) -> List[PDFPage]:
    """
    便捷函数：解析 PDF 文档

    Args:
        file_path: PDF 文件路径
        engine: 解析引擎类型
        extract_bbox: 是否提取坐标

    Returns:
        解析后的页面列表
    """
    parser = get_pdf_parser(engine)
    return parser.parse(file_path, extract_bbox)
