"""TrustLens AI - Vector Store Package"""

from .vector_store import (
    VectorDocument,
    SearchResult,
    InMemoryVectorStore,
    FAISSVectorStore,
    get_vector_store,
)

__all__ = [
    "VectorDocument",
    "SearchResult",
    "InMemoryVectorStore",
    "FAISSVectorStore",
    "get_vector_store",
]
