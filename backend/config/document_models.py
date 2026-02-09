"""
TrustLens AI - Document Database Models
文档数据库模型
"""
from sqlalchemy import Column, String, Integer, DateTime, Float, JSON, Enum as SQLEnum, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime
from enum import Enum
import uuid

Base = declarative_base()


class DocumentStatus(str, Enum):
    """文档状态"""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    REVIEWING = "REVIEWING"
    REVIEWED = "REVIEWED"
    FAILED = "FAILED"


class FileType(str, Enum):
    """文件类型"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"


class Document(Base):
    """文档模型"""
    __tablename__ = "documents"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 唯一标识符
    doc_id = Column(String(100), unique=True, nullable=False, index=True)

    # 文件信息
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500))

    # 状态信息
    status = Column(SQLEnum(DocumentStatus), nullable=False, default=DocumentStatus.UPLOADED)
    status_message = Column(String(500))
    progress = Column(Float, default=0.0)

    # 解析结果
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)

    # 文档元数据（JSON）
    doc_metadata = Column(JSON)

    # 处理信息（JSON）
    processing_info = Column(JSON)

    # 审查信息（JSON）
    review_info = Column(JSON)

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "file_path": self.file_path,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "status_message": self.status_message,
            "progress": self.progress,
            "page_count": self.page_count,
            "chunk_count": self.chunk_count,
            "metadata": self.doc_metadata or {},
            "processing_info": self.processing_info or {},
            "review_info": self.review_info or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        """从字典创建"""
        return cls(
            doc_id=data.get("doc_id", str(uuid.uuid4())),
            filename=data.get("filename", ""),
            file_type=data.get("file_type", ""),
            file_size=data.get("file_size", 0),
            file_path=data.get("file_path"),
            status=DocumentStatus(data.get("status", "UPLOADED")),
            status_message=data.get("status_message"),
            progress=data.get("progress", 0.0),
            page_count=data.get("page_count", 0),
            chunk_count=data.get("chunk_count", 0),
            doc_metadata=data.get("metadata"),
            processing_info=data.get("processing_info"),
            review_info=data.get("review_info"),
        )

    def update_status(
        self,
        status: DocumentStatus,
        message: str = None,
        progress: float = None,
    ):
        """更新状态"""
        self.status = status
        if message:
            self.status_message = message
        if progress is not None:
            self.progress = progress
        self.updated_at = datetime.now()

    def update_processing_info(self, info: dict):
        """更新处理信息"""
        if self.processing_info is None:
            self.processing_info = {}
        self.processing_info.update(info)
        self.updated_at = datetime.now()

    def update_review_info(self, info: dict):
        """更新审查信息"""
        if self.review_info is None:
            self.review_info = {}
        self.review_info.update(info)
        self.updated_at = datetime.now()


def generate_doc_id() -> str:
    """生成文档 ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique = str(uuid.uuid4())[:8]
    return f"doc_{timestamp}_{unique}"
