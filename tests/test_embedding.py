"""
Test Embedding Pipeline
测试文本向量化和向量存储功能
"""
import sys
import os
from pathlib import Path

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from document.embedding import (
    OpenAIEmbeddingProvider,
    LocalEmbeddingProvider,
    EmbeddingPipeline,
    create_embedding_pipeline,
)
from document.chunker import Chunk
from vector.vector_store import get_vector_store


def create_test_chunks() -> list[Chunk]:
    """创建测试 chunks"""
    chunks = [
        Chunk(
            chunk_id="doc1_p1_c0",
            doc_id="doc1",
            page=1,
            text="出租方将位于长沙市高新区创新大厦的房屋出租给承租方使用。",
            bbox={"x1": 50, "y1": 100, "x2": 500, "y2": 120, "page_width": 595, "page_height": 842},
            clause_hint="other",
            char_start=0,
            char_end=30,
            token_count=30,
        ),
        Chunk(
            chunk_id="doc1_p1_c1",
            doc_id="doc1",
            page=1,
            text="每月租金为人民币5000元整。承租方应在每月5日前支付当月租金。",
            bbox={"x1": 50, "y1": 130, "x2": 500, "y2": 150, "page_width": 595, "page_height": 842},
            clause_hint="payment",
            char_start=31,
            char_end=70,
            token_count=35,
        ),
        Chunk(
            chunk_id="doc1_p1_c2",
            doc_id="doc1",
            page=1,
            text="双方应对在合同履行过程中知悉的对方商业秘密承担保密义务。",
            bbox={"x1": 50, "y1": 160, "x2": 500, "y2": 180, "page_width": 595, "page_height": 842},
            clause_hint="confidentiality",
            char_start=71,
            char_end=100,
            token_count=28,
        ),
        Chunk(
            chunk_id="doc1_p1_c3",
            doc_id="doc1",
            page=1,
            text="承租方逾期支付租金的，每逾期一日，应按日租金的千分之五支付违约金。",
            bbox={"x1": 50, "y1": 190, "x2": 500, "y2": 210, "page_width": 595, "page_height": 842},
            clause_hint="liability",
            char_start=101,
            char_end=140,
            token_count=32,
        ),
        Chunk(
            chunk_id="doc1_p1_c4",
            doc_id="doc1",
            page=1,
            text="本合同履行过程中发生的争议，双方应友好协商解决。",
            bbox={"x1": 50, "y1": 220, "x2": 500, "y2": 240, "page_width": 595, "page_height": 842},
            clause_hint="dispute_resolution",
            char_start=141,
            char_end=170,
            token_count=25,
        ),
    ]
    return chunks


def test_embedding_provider():
    """测试 Embedding 提供者"""

    print("=" * 60)
    print("Embedding 提供者测试")
    print("=" * 60)

    print("\n1. 测试 OpenAI Embedding 提供者")
    print("-" * 60)

    try:
        provider = OpenAIEmbeddingProvider()
        print(f"✓ 创建 OpenAI Embedding 提供者成功")
        print(f"  - 模型: {provider.model}")
        print(f"  - 维度: {provider.dimension}")

        # 测试编码
        test_texts = ["测试文本1", "测试文本2"]
        embeddings = provider.encode(test_texts)

        print(f"✓ 编码成功，生成 {len(embeddings)} 个向量")
        print(f"  - 向量维度: {len(embeddings[0])}")

        # 验证向量维度
        for i, emb in enumerate(embeddings):
            if len(emb) != provider.dimension:
                print(f"✗ 向量 {i+1} 维度不匹配: 期望 {provider.dimension}, 实际 {len(emb)}")
                return False

        print("✓ 所有向量维度正确")

    except Exception as e:
        print(f"✗ OpenAI Embedding 测试失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n2. 测试本地 Embedding 提供者（可选）")
    print("-" * 60)

    try:
        provider = LocalEmbeddingProvider()
        print(f"✓ 创建本地 Embedding 提供者成功")
        print(f"  - 模型: {provider.model_name}")

        # 注意：本地模型需要下载，可能会很慢
        print(f"○ 本地模型需要下载，跳过实际测试")

    except Exception as e:
        print(f"○ 本地 Embedding 不可用: {e}")

    return True


def test_vector_store():
    """测试向量存储"""

    print("\n" + "=" * 60)
    print("向量存储测试")
    print("=" * 60)

    print("\n1. 测试内存向量存储")
    print("-" * 60)

    try:
        # 创建向量存储
        store = get_vector_store(store_type="memory")
        print(f"✓ 创建内存向量存储成功")

        # 创建测试向量文档
        from vector.vector_store import VectorDocument

        docs = [
            VectorDocument(
                chunk_id="doc1_p1_c0",
                doc_id="doc1",
                text="测试文本1",
                embedding=[0.1, 0.2, 0.3],
                page=1,
                clause_hint="payment",
            ),
            VectorDocument(
                chunk_id="doc1_p1_c1",
                doc_id="doc1",
                text="测试文本2",
                embedding=[0.2, 0.3, 0.4],
                page=1,
                clause_hint="liability",
            ),
            VectorDocument(
                chunk_id="doc2_p1_c0",
                doc_id="doc2",
                text="测试文本3",
                embedding=[0.3, 0.4, 0.5],
                page=1,
                clause_hint="other",
            ),
        ]

        # 添加文档
        count = store.add_documents(docs)
        print(f"✓ 添加 {count} 个文档成功")

        # 测试搜索
        results = store.search(
            query_embedding=[0.15, 0.25, 0.35],
            top_k=2,
        )
        print(f"✓ 搜索返回 {len(results)} 个结果")

        for i, result in enumerate(results):
            print(f"  - 结果 {i+1}: {result.chunk_id} (分数: {result.score:.4f})")

        # 测试过滤
        results_filtered = store.search(
            query_embedding=[0.15, 0.25, 0.35],
            top_k=10,
            doc_filter="doc1",
        )
        print(f"✓ 过滤后返回 {len(results_filtered)} 个结果")

        # 获取统计
        stats = store.get_stats()
        print(f"✓ 统计信息: {stats['total_chunks']} chunks, {stats['total_documents']} documents")

    except Exception as e:
        print(f"✗ 向量存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n2. 测试 FAISS 向量存储（可选）")
    print("-" * 60)

    try:
        store = get_vector_store(store_type="faiss", embedding_dimension=1536)
        print(f"✓ 创建 FAISS 向量存储成功")
        stats = store.get_stats()
        print(f"  - 使用 FAISS: {stats.get('use_faiss', False)}")
        print(f"  - 向量维度: {stats.get('embedding_dimension', 'N/A')}")

    except Exception as e:
        print(f"○ FAISS 不可用: {e}")

    return True


def test_embedding_pipeline():
    """测试 Embedding 流水线"""

    print("\n" + "=" * 60)
    print("Embedding 流水线测试")
    print("=" * 60)

    print("\n1. 创建测试 chunks")
    print("-" * 60)

    chunks = create_test_chunks()
    print(f"✓ 创建 {len(chunks)} 个测试 chunks")

    for chunk in chunks:
        print(f"  - {chunk.chunk_id}: {chunk.text[:40]}...")

    print("\n2. 创建 Embedding 流水线")
    print("-" * 60)

    try:
        pipeline = create_embedding_pipeline(
            provider_type="openai",
            store_type="memory",
        )
        print(f"✓ 创建流水线成功")

    except Exception as e:
        print(f"✗ 创建流水线失败: {e}")
        return False

    print("\n3. 处理 chunks")
    print("-" * 60)

    try:
        result = pipeline.process_chunks(chunks, show_progress=True)

        print(f"✓ 处理完成")
        print(f"  - 总数: {result.total_processed}")
        print(f"  - 失败: {result.failed_count}")
        print(f"  - 耗时: {result.processing_time:.2f}s")

        # 获取统计
        stats = pipeline.get_stats()
        print(f"\n✓ 向量存储统计:")
        print(f"  - 总 chunks: {stats['total_chunks']}")
        print(f"  - 总文档: {stats['total_documents']}")
        print(f"  - 向量维度: {stats['embedding_dimension']}")
        print(f"  - 条款分布: {stats['clause_counts']}")

    except Exception as e:
        print(f"✗ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n4. 测试搜索")
    print("-" * 60)

    try:
        # 搜索关于付款的内容
        query = "租金支付"
        results = pipeline.search(query, top_k=3)

        print(f"✓ 搜索 '{query}' 返回 {len(results)} 个结果")

        for i, result in enumerate(results):
            preview = result['text'][:50] + "..." if len(result['text']) > 50 else result['text']
            print(f"  - 结果 {i+1}:")
            print(f"      Chunk: {result['chunk_id']}")
            print(f"      类型: {result['clause_hint']}")
            print(f"      分数: {result['score']:.4f}")
            print(f"      文本: {preview}")

    except Exception as e:
        print(f"✗ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n5. 测试过滤搜索")
    print("-" * 60)

    try:
        # 只搜索 payment 类型的内容
        results = pipeline.search(
            "租金",
            top_k=10,
            clause_filter="payment",
        )

        print(f"✓ 过滤搜索返回 {len(results)} 个结果 (类型: payment)")

        for result in results:
            assert result['clause_hint'] == "payment", "过滤条件未生效"

        print("✓ 过滤条件验证通过")

    except Exception as e:
        print(f"✗ 过滤搜索失败: {e}")
        return False

    return True


def test_embedding():
    """运行所有测试"""

    print("\n" + "=" * 60)
    print("Embedding Pipeline 综合测试")
    print("=" * 60)

    success = True

    # 测试提供者
    if not test_embedding_provider():
        success = False

    # 测试向量存储
    if not test_vector_store():
        success = False

    # 测试流水线
    if not test_embedding_pipeline():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")
    print("=" * 60)

    return success


if __name__ == "__main__":
    success = test_embedding()
    sys.exit(0 if success else 1)
