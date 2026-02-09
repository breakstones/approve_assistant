"""
TrustLens AI - Embedding Pipeline
文本向量化模块，支持 OpenAI Embedding API 和本地模型
"""
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

from .chunker import Chunk
from vector.vector_store import VectorDocument, get_vector_store


# 默认模型配置
DEFAULT_OPENAI_MODEL = "text-embedding-3-small"
DEFAULT_OPENAI_DIMENSION = 1536

# 批处理大小
BATCH_SIZE = 100


class EmbeddingProvider:
    """Embedding 提供者基类"""

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        编码文本为向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        raise NotImplementedError("Subclass must implement encode method")

    @property
    def dimension(self) -> int:
        """获取向量维度"""
        raise NotImplementedError("Subclass must implement dimension property")


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI Embedding 提供者"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_OPENAI_MODEL,
        dimension: Optional[int] = None,
    ):
        """
        初始化 OpenAI Embedding 提供者

        Args:
            api_key: OpenAI API Key（如果不提供，从环境变量读取）
            model: 模型名称
            dimension: 向量维度（仅支持的模型有效）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model

        # 根据模型设置维度
        if dimension is None:
            if model == "text-embedding-3-small":
                dimension = DEFAULT_OPENAI_DIMENSION
            elif model == "text-embedding-3-large":
                dimension = 3072
            elif model == "text-embedding-ada-002":
                dimension = 1536
            else:
                dimension = DEFAULT_OPENAI_DIMENSION

        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        使用 OpenAI API 编码文本

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. "
                "Run: pip install openai"
            )

        if not self.api_key:
            # 如果没有 API Key，返回 mock 向量用于测试
            return self._mock_encode(texts)

        client = OpenAI(api_key=self.api_key)

        all_embeddings = []

        # 批处理
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]

            response = client.embeddings.create(
                input=batch,
                model=self.model,
                encoding_format="float",
            )

            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)

        return all_embeddings

    def _mock_encode(self, texts: List[str]) -> List[List[float]]:
        """
        Mock 编码（用于没有 API Key 时的测试）

        Args:
            texts: 文本列表

        Returns:
            伪随机向量列表
        """
        import hashlib

        embeddings = []
        for text in texts:
            # 使用文本哈希生成伪随机向量
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()

            # 转换为向量
            vector = []
            for i in range(self._dimension):
                byte_idx = i % len(hash_bytes)
                val = hash_bytes[byte_idx] / 255.0
                vector.append(val)

            # 归一化
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = (np.array(vector) / norm).tolist()

            embeddings.append(vector)

        return embeddings


class LocalEmbeddingProvider(EmbeddingProvider):
    """本地 Embedding 提供者（使用 sentence-transformers）"""

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    ):
        """
        初始化本地 Embedding 提供者

        Args:
            model_name: 模型名称
        """
        self.model_name = model_name
        self._model = None
        self._dimension = 384  # MiniLM-L12 的默认维度

    @property
    def dimension(self) -> int:
        return self._dimension

    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )

    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        使用本地模型编码文本

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        self._load_model()

        embeddings = self._model.encode(texts, convert_to_numpy=True)

        # 转换为列表
        return embeddings.tolist()


@dataclass
class EmbeddingResult:
    """Embedding 结果"""
    chunks: List[Chunk]
    vectors: List[VectorDocument]
    total_processed: int
    failed_count: int
    processing_time: float


class EmbeddingPipeline:
    """Embedding 处理流水线"""

    def __init__(
        self,
        provider: Optional[EmbeddingProvider] = None,
        vector_store=None,
    ):
        """
        初始化 Embedding 流水线

        Args:
            provider: Embedding 提供者
            vector_store: 向量存储实例
        """
        self.provider = provider or OpenAIEmbeddingProvider()
        self.vector_store = vector_store or get_vector_store(
            store_type="memory",
            embedding_dimension=self.provider.dimension,
        )

    def process_chunks(
        self,
        chunks: List[Chunk],
        batch_size: int = BATCH_SIZE,
        show_progress: bool = False,
    ) -> EmbeddingResult:
        """
        处理 chunks，生成向量并存储

        Args:
            chunks: Chunk 列表
            batch_size: 批处理大小
            show_progress: 是否显示进度

        Returns:
            Embedding 结果
        """
        import time

        start_time = time.time()
        vectors = []
        failed_count = 0

        # 提取文本
        texts = [chunk.text for chunk in chunks]

        # 批处理编码
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_chunks = chunks[i:i + batch_size]

            if show_progress:
                print(f"Processing batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}")

            try:
                embeddings = self.provider.encode(batch_texts)
                all_embeddings.extend(embeddings)

                # 创建向量文档
                for chunk, embedding in zip(batch_chunks, embeddings):
                    vector_doc = VectorDocument(
                        chunk_id=chunk.chunk_id,
                        doc_id=chunk.doc_id,
                        text=chunk.text,
                        embedding=embedding,
                        page=chunk.page,
                        clause_hint=chunk.clause_hint,
                        metadata=chunk.metadata,
                    )
                    vectors.append(vector_doc)

            except Exception as e:
                print(f"Error processing batch: {e}")
                failed_count += len(batch_texts)
                # 添加空向量
                all_embeddings.extend([[0.0] * self.provider.dimension] * len(batch_texts))

        # 添加到向量存储
        if vectors:
            self.vector_store.add_documents(vectors)

        processing_time = time.time() - start_time

        return EmbeddingResult(
            chunks=chunks,
            vectors=vectors,
            total_processed=len(chunks),
            failed_count=failed_count,
            processing_time=processing_time,
        )

    def search(
        self,
        query: str,
        top_k: int = 10,
        doc_filter: Optional[str] = None,
        clause_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索相似 chunks

        Args:
            query: 查询文本
            top_k: 返回结果数量
            doc_filter: 文档 ID 过滤
            clause_filter: 条款类型过滤

        Returns:
            搜索结果列表
        """
        # 编码查询
        query_embedding = self.provider.encode([query])[0]

        # 搜索
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            doc_filter=doc_filter,
            clause_filter=clause_filter,
        )

        return [result.to_dict() for result in results]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return self.vector_store.get_stats()


def create_embedding_pipeline(
    provider_type: str = "openai",
    store_type: str = "memory",
    **kwargs
) -> EmbeddingPipeline:
    """
    创建 Embedding 流水线

    Args:
        provider_type: 提供者类型（"openai" 或 "local"）
        store_type: 存储类型（"memory" 或 "faiss"）
        **kwargs: 其他参数

    Returns:
        Embedding 流水线实例
    """
    # 创建提供者
    if provider_type == "local":
        provider = LocalEmbeddingProvider(
            model_name=kwargs.get("model_name", "paraphrase-multilingual-MiniLM-L12-v2"),
        )
    else:
        provider = OpenAIEmbeddingProvider(
            api_key=kwargs.get("api_key"),
            model=kwargs.get("model", DEFAULT_OPENAI_MODEL),
            dimension=kwargs.get("dimension"),
        )

    # 创建向量存储
    vector_store = get_vector_store(
        store_type=store_type,
        embedding_dimension=provider.dimension,
    )

    return EmbeddingPipeline(
        provider=provider,
        vector_store=vector_store,
    )
