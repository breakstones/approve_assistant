"""
TrustLens AI - Document Service
文档服务，管理文档的 CRUD 操作和状态流转
"""
import os
import shutil
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .document_models import Document, DocumentStatus, FileType, generate_doc_id, Base
from .database import get_database


class DocumentService:
    """文档服务"""

    # 状态转换规则
    VALID_TRANSITIONS = {
        DocumentStatus.UPLOADED: [DocumentStatus.PROCESSING, DocumentStatus.FAILED],
        DocumentStatus.PROCESSING: [DocumentStatus.READY, DocumentStatus.FAILED],
        DocumentStatus.READY: [DocumentStatus.REVIEWING],
        DocumentStatus.REVIEWING: [DocumentStatus.REVIEWED, DocumentStatus.READY],
        DocumentStatus.REVIEWED: [],
        DocumentStatus.FAILED: [DocumentStatus.PROCESSING],
    }

    def __init__(self, upload_dir: str = None, db=None):
        """
        初始化文档服务

        Args:
            upload_dir: 文件上传目录
            db: 数据库连接
        """
        self.upload_dir = upload_dir or os.path.join(os.getcwd(), "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

        self.db = db

    def _get_db(self):
        """获取数据库连接"""
        return self.db or get_database()

    def create(
        self,
        filename: str,
        file_type: str,
        file_size: int,
        file_path: str = None,
        metadata: dict = None,
    ) -> Dict[str, Any]:
        """
        创建新文档记录

        Args:
            filename: 文件名
            file_type: 文件类型
            file_size: 文件大小
            file_path: 文件路径
            metadata: 元数据

        Returns:
            文档字典
        """
        doc_id = generate_doc_id()

        # 如果提供了文件路径，复制到上传目录
        if file_path and os.path.exists(file_path):
            dest_path = os.path.join(self.upload_dir, f"{doc_id}.{file_type}")
            shutil.copy2(file_path, dest_path)
            file_path = dest_path

        doc = Document(
            doc_id=doc_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            status=DocumentStatus.UPLOADED,
            status_message="文档已上传",
            progress=0.0,
            doc_metadata=metadata or {},
        )

        with self._get_db().get_session() as session:
            session.add(doc)
            session.commit()
            session.refresh(doc)
            return doc.to_dict()

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档

        Args:
            doc_id: 文档 ID

        Returns:
            文档字典或 None
        """
        with self._get_db().get_session() as session:
            doc = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()

            if doc:
                return doc.to_dict()
            return None

    def list(
        self,
        status: Optional[DocumentStatus] = None,
        file_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        列出文档

        Args:
            status: 状态过滤
            file_type: 文件类型过滤
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            文档字典列表
        """
        with self._get_db().get_session() as session:
            query = session.query(Document)

            if status:
                query = query.filter(Document.status == status)
            if file_type:
                query = query.filter(Document.file_type == file_type)

            query = query.order_by(Document.created_at.desc())
            query = query.limit(limit).offset(offset)

            docs = query.all()
            return [doc.to_dict() for doc in docs]

    def count(
        self,
        status: Optional[DocumentStatus] = None,
        file_type: Optional[str] = None,
    ) -> int:
        """
        统计文档数量

        Args:
            status: 状态过滤
            file_type: 文件类型过滤

        Returns:
            文档数量
        """
        with self._get_db().get_session() as session:
            query = session.query(Document)

            if status:
                query = query.filter(Document.status == status)
            if file_type:
                query = query.filter(Document.file_type == file_type)

            return query.count()

    def update_status(
        self,
        doc_id: str,
        status: DocumentStatus,
        message: str = None,
        progress: float = None,
    ) -> Optional[Dict[str, Any]]:
        """
        更新文档状态

        Args:
            doc_id: 文档 ID
            status: 新状态
            message: 状态消息
            progress: 进度

        Returns:
            更新后的文档字典或 None
        """
        with self._get_db().get_session() as session:
            doc = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()

            if not doc:
                return None

            # 验证状态转换
            if not self._is_valid_transition(doc.status, status):
                raise ValueError(
                    f"Invalid status transition: {doc.status} -> {status}"
                )

            doc.update_status(status, message, progress)
            session.commit()
            session.refresh(doc)
            return doc.to_dict()

    def update_processing_info(
        self,
        doc_id: str,
        info: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        更新处理信息

        Args:
            doc_id: 文档 ID
            info: 处理信息

        Returns:
            更新后的文档字典或 None
        """
        with self._get_db().get_session() as session:
            doc = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()

            if not doc:
                return None

            doc.update_processing_info(info)
            session.commit()
            session.refresh(doc)
            return doc.to_dict()

    def update_review_info(
        self,
        doc_id: str,
        info: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        更新审查信息

        Args:
            doc_id: 文档 ID
            info: 审查信息

        Returns:
            更新后的文档字典或 None
        """
        with self._get_db().get_session() as session:
            doc = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()

            if not doc:
                return None

            doc.update_review_info(info)
            session.commit()
            session.refresh(doc)
            return doc.to_dict()

    def delete(self, doc_id: str) -> bool:
        """
        删除文档（软删除：标记为删除状态）

        Args:
            doc_id: 文档 ID

        Returns:
            是否删除成功
        """
        with self._get_db().get_session() as session:
            doc = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()

            if not doc:
                return False

            # 删除文件
            if doc.file_path and os.path.exists(doc.file_path):
                try:
                    os.remove(doc.file_path)
                except Exception as e:
                    print(f"Warning: Failed to delete file: {e}")

            session.delete(doc)
            session.commit()
            return True

    def get_file_path(self, doc_id: str) -> Optional[str]:
        """
        获取文档文件路径

        Args:
            doc_id: 文档 ID

        Returns:
            文件路径或 None
        """
        with self._get_db().get_session() as session:
            doc = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()

            if doc and doc.file_path:
                return doc.file_path
            return None

    def _is_valid_transition(
        self,
        from_status: DocumentStatus,
        to_status: DocumentStatus,
    ) -> bool:
        """
        验证状态转换是否有效

        Args:
            from_status: 当前状态
            to_status: 目标状态

        Returns:
            是否有效
        """
        # 允许相同状态的更新（用于更新进度）
        if from_status == to_status:
            return True
        allowed = self.VALID_TRANSITIONS.get(from_status, [])
        return to_status in allowed


# 全局服务实例
_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    """获取文档服务实例"""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
