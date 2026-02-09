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

from .chunker import (
    Chunk,
    DocumentChunker,
    chunk_document,
)

from .embedding import (
    EmbeddingProvider,
    OpenAIEmbeddingProvider,
    LocalEmbeddingProvider,
    EmbeddingPipeline,
    EmbeddingResult,
    create_embedding_pipeline,
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
    # Chunker
    "Chunk",
    "DocumentChunker",
    "chunk_document",
    # Embedding
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "LocalEmbeddingProvider",
    "EmbeddingPipeline",
    "EmbeddingResult",
    "create_embedding_pipeline",
]
