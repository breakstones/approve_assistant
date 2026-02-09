"""TrustLens AI - Document Intelligence Package"""

from .pdf_parser import (
    PDFParser,
    PDFPlumberParser,
    PyMuPDFParser,
    BoundingBox,
    TextBlock,
    PDFPage,
    get_pdf_parser,
    parse_pdf,
)

from .docx_parser import (
    DOCXParser,
    get_docx_parser,
    parse_docx,
)

__all__ = [
    # PDF Parser
    "PDFParser",
    "PDFPlumberParser",
    "PyMuPDFParser",
    "BoundingBox",
    "TextBlock",
    "PDFPage",
    "get_pdf_parser",
    "parse_pdf",
    # DOCX Parser
    "DOCXParser",
    "get_docx_parser",
    "parse_docx",
]
