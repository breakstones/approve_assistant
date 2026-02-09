"""
TrustLens AI - Vector Store
向量存储模块，支持 FAISS 和内存存储
"""
import os
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import hashlib


@dataclass
class VectorDocument:
    """向量文档"""
    chunk_id: str
    doc_id: str
    text: str
    embedding: Optional[List[float]] = None
    page: int = 1
    clause_hint: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "text": self.text,
            "embedding": self.embedding,
            "page": self.page,
            "clause_hint": self.clause_hint,
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    """搜索结果"""
    chunk_id: str
    doc_id: str
    text: str
    page: int
    clause_hint: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "text": self.text,
            "page": self.page,
            "clause_hint": self.clause_hint,
            "score": self.score,
            "metadata": self.metadata,
        }


class InMemoryVectorStore:
    """内存向量存储（用于开发和测试）"""

    def __init__(self):
        self.documents: Dict[str, VectorDocument] = {}
        self.embeddings: List[List[float]] = []
        self.chunk_ids: List[str] = []

    def add_documents(self, docs: List[VectorDocument]) -> int:
        """
        添加文档到存储

        Args:
            docs: 文档列表

        Returns:
            添加的文档数量
        """
        count = 0
        for doc in docs:
            if doc.embedding is None:
                continue

            if doc.chunk_id not in self.documents:
                self.chunk_ids.append(doc.chunk_id)

            self.documents[doc.chunk_id] = doc
            count += 1

        # 重建嵌入列表
        self._rebuild_embeddings()

        return count

    def _rebuild_embeddings(self):
        """重建嵌入列表"""
        self.embeddings = []
        self.chunk_ids = []

        for chunk_id, doc in self.documents.items():
            if doc.embedding is not None:
                self.embeddings.append(doc.embedding)
                self.chunk_ids.append(chunk_id)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        doc_filter: Optional[str] = None,
        clause_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        向量搜索

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            doc_filter: 文档 ID 过滤
            clause_filter: 条款类型过滤

        Returns:
            搜索结果列表
        """
        if not self.embeddings:
            return []

        # 计算相似度
        scores = self._compute_similarity(query_embedding)

        # 创建结果列表
        results = []
        for chunk_id, score in zip(self.chunk_ids, scores):
            doc = self.documents.get(chunk_id)
            if doc is None:
                continue

            # 应用过滤条件
            if doc_filter and doc.doc_id != doc_filter:
                continue
            if clause_filter and doc.clause_hint != clause_filter:
                continue

            results.append(SearchResult(
                chunk_id=doc.chunk_id,
                doc_id=doc.doc_id,
                text=doc.text,
                page=doc.page,
                clause_hint=doc.clause_hint,
                score=score,
                metadata=doc.metadata,
            ))

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    def _compute_similarity(self, query_embedding: List[float]) -> List[float]:
        """
        计算余弦相似度

        Args:
            query_embedding: 查询向量

        Returns:
            相似度分数列表
        """
        import numpy as np

        query = np.array(query_embedding)
        embeddings = np.array(self.embeddings)

        # 余弦相似度
        norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query)
        scores = np.dot(embeddings, query) / (norms + 1e-8)

        return scores.tolist()

    def get_document(self, chunk_id: str) -> Optional[VectorDocument]:
        """
        获取文档

        Args:
            chunk_id: Chunk ID

        Returns:
            向量文档或 None
        """
        return self.documents.get(chunk_id)

    def delete_document(self, chunk_id: str) -> bool:
        """
        删除文档

        Args:
            chunk_id: Chunk ID

        Returns:
            是否删除成功
        """
        if chunk_id in self.documents:
            del self.documents[chunk_id]
            self._rebuild_embeddings()
            return True
        return False

    def delete_by_doc_id(self, doc_id: str) -> int:
        """
        删除指定文档的所有 chunks

        Args:
            doc_id: 文档 ID

        Returns:
            删除的数量
        """
        count = 0
        to_delete = [
            chunk_id for chunk_id, doc in self.documents.items()
            if doc.doc_id == doc_id
        ]

        for chunk_id in to_delete:
            self.delete_document(chunk_id)
            count += 1

        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息

        Returns:
            统计信息字典
        """
        # 统计文档数量
        doc_counts = {}
        clause_counts = {}

        for doc in self.documents.values():
            doc_counts[doc.doc_id] = doc_counts.get(doc.doc_id, 0) + 1
            clause_counts[doc.clause_hint] = clause_counts.get(doc.clause_hint, 0) + 1

        return {
            "total_chunks": len(self.documents),
            "total_documents": len(doc_counts),
            "document_counts": doc_counts,
            "clause_counts": clause_counts,
            "embedding_dimension": len(self.embeddings[0]) if self.embeddings else 0,
        }

    def save(self, path: str):
        """
        保存存储到文件

        Args:
            path: 保存路径
        """
        data = {
            "documents": self.documents,
            "chunk_ids": self.chunk_ids,
        }

        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str):
        """
        从文件加载存储

        Args:
            path: 文件路径
        """
        with open(path, "rb") as f:
            data = pickle.load(f)

        self.documents = data["documents"]
        self.chunk_ids = data["chunk_ids"]
        self._rebuild_embeddings()


class FAISSVectorStore:
    """基于 FAISS 的向量存储"""

    def __init__(self, embedding_dimension: int = 1536):
        """
        初始化 FAISS 存储

        Args:
            embedding_dimension: 向量维度
        """
        self.embedding_dimension = embedding_dimension
        self.documents: Dict[str, VectorDocument] = {}

        try:
            import faiss
            self.faiss = faiss
            # 创建索引
            self.index = faiss.IndexFlatIP(embedding_dimension)  # 内积索引（用于余弦相似度）
            self.use_faiss = True
        except ImportError:
            self.faiss = None
            self.index = None
            self.use_faiss = False

    def add_documents(self, docs: List[VectorDocument]) -> int:
        """
        添加文档到存储

        Args:
            docs: 文档列表

        Returns:
            添加的文档数量
        """
        import numpy as np

        embeddings = []
        chunk_ids = []

        for doc in docs:
            if doc.embedding is None:
                continue

            self.documents[doc.chunk_id] = doc
            embeddings.append(doc.embedding)
            chunk_ids.append(doc.chunk_id)

        if not embeddings:
            return 0

        embeddings_array = np.array(embeddings, dtype=np.float32)

        # 归一化向量（用于余弦相似度）
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        normalized_embeddings = embeddings_array / (norms + 1e-8)

        if self.use_faiss and self.index:
            self.index.add(normalized_embeddings)
        else:
            # Fallback to in-memory
            pass

        return len(embeddings)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        doc_filter: Optional[str] = None,
        clause_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        向量搜索

        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            doc_filter: 文档 ID 过滤
            clause_filter: 条款类型过滤

        Returns:
            搜索结果列表
        """
        import numpy as np

        if not self.documents:
            return []

        # 归一化查询向量
        query = np.array([query_embedding], dtype=np.float32)
        query_norm = np.linalg.norm(query)
        normalized_query = query / (query_norm + 1e-8)

        if self.use_faiss and self.index and self.index.ntotal > 0:
            # 使用 FAISS 搜索
            scores, indices = self.index.search(normalized_query, min(top_k * 2, self.index.ntotal))

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:
                    continue

                # 由于我们没有直接映射，需要遍历文档
                # 这里简化处理，直接返回所有文档然后过滤
                break

        # Fallback: 计算所有文档的相似度
        results = []
        for doc in self.documents.values():
            if doc.embedding is None:
                continue

            # 应用过滤条件
            if doc_filter and doc.doc_id != doc_filter:
                continue
            if clause_filter and doc.clause_hint != clause_filter:
                continue

            # 计算余弦相似度
            score = self._cosine_similarity(query_embedding, doc.embedding)

            results.append(SearchResult(
                chunk_id=doc.chunk_id,
                doc_id=doc.doc_id,
                text=doc.text,
                page=doc.page,
                clause_hint=doc.clause_hint,
                score=score,
                metadata=doc.metadata,
            ))

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:top_k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        import numpy as np
        a = np.array(a)
        b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))

    def get_document(self, chunk_id: str) -> Optional[VectorDocument]:
        """获取文档"""
        return self.documents.get(chunk_id)

    def delete_document(self, chunk_id: str) -> bool:
        """删除文档"""
        if chunk_id in self.documents:
            del self.documents[chunk_id]
            return True
        return False

    def delete_by_doc_id(self, doc_id: str) -> int:
        """删除指定文档的所有 chunks"""
        count = 0
        to_delete = [
            chunk_id for chunk_id, doc in self.documents.items()
            if doc.doc_id == doc_id
        ]

        for chunk_id in to_delete:
            self.delete_document(chunk_id)
            count += 1

        return count

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        doc_counts = {}
        clause_counts = {}

        for doc in self.documents.values():
            doc_counts[doc.doc_id] = doc_counts.get(doc.doc_id, 0) + 1
            clause_counts[doc.clause_hint] = clause_counts.get(doc.clause_hint, 0) + 1

        return {
            "total_chunks": len(self.documents),
            "total_documents": len(doc_counts),
            "document_counts": doc_counts,
            "clause_counts": clause_counts,
            "embedding_dimension": self.embedding_dimension,
            "use_faiss": self.use_faiss,
        }


def get_vector_store(
    store_type: str = "memory",
    embedding_dimension: int = 1536,
) -> Any:
    """
    获取向量存储实例

    Args:
        store_type: 存储类型（"memory" 或 "faiss"）
        embedding_dimension: 向量维度

    Returns:
        向量存储实例
    """
    if store_type == "faiss":
        return FAISSVectorStore(embedding_dimension=embedding_dimension)
    return InMemoryVectorStore()
