"""
TrustLens AI - Document Chunker
智能文档切分模块，将文档解析结果转换为符合 Chunk Schema 的切分单元
"""
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

from .pdf_parser import PDFPage, TextBlock, BoundingBox


# 条款类型关键词映射
CLAUSE_KEYWORDS = {
    "payment": ["付款", "支付", "结算", "费用", "金额", "价款", "租金", "payment", "pay"],
    "liability": ["责任", "义务", "承担", "赔偿", "损失", "liability", "responsibility"],
    "confidentiality": ["保密", "机密", "秘密", "泄露", "confidential", "secret"],
    "termination": ["终止", "解除", "到期", "期满", "termination", "end", "expire"],
    "intellectual_property": ["知识产权", "专利", "商标", "著作权", "版权", "intellectual", "property", "patent", "copyright"],
    "dispute_resolution": ["争议", "纠纷", "仲裁", "诉讼", "dispute", "arbitration", "litigation"],
    "force_majeure": ["不可抗力", "天灾", "force", "majeure"],
    "governing_law": ["法律", "管辖", "适用法律", "governing", "law", "jurisdiction"],
    "delivery": ["交付", "运送", "发货", "delivery", "ship"],
    "quality": ["质量", "标准", "规格", "quality", "standard"],
    "warranty": ["质保", "保修", "保证", "warranty", "guarantee"],
    "indemnification": ["补偿", "赔付", "indemnif"],
    "limitation_of_liability": ["责任限制", "免责", "limitation"],
    "amendment": ["修改", "修订", "变更", "amendment", "modify"],
    "severability": ["可分割", "独立性", "severability"],
    "entire_agreement": ["完整协议", "全部协议", "取代", "entire", "agreement"],
    "assignment": ["转让", "让与", "assignment"],
    "notices": ["通知", "告知", "notice"],
}


@dataclass
class Chunk:
    """文档切分单元"""
    chunk_id: str
    doc_id: str
    page: int
    text: str
    bbox: Dict[str, Any]  # 支持数组或对象格式
    clause_hint: str = "unknown"
    char_start: int = 0
    char_end: int = 0
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "doc_id": self.doc_id,
            "page": self.page,
            "text": self.text,
            "bbox": self.bbox,
            "clause_hint": self.clause_hint,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "token_count": self.token_count,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class DocumentChunker:
    """智能文档切分器"""

    def __init__(
        self,
        min_chunk_size: int = 50,
        max_chunk_size: int = 300,
        target_chunk_size: int = 150,
        overlap_sentences: int = 1,
    ):
        """
        初始化切分器

        Args:
            min_chunk_size: 最小 chunk token 数
            max_chunk_size: 最大 chunk token 数
            target_chunk_size: 目标 chunk token 数
            overlap_sentences: 相邻 chunk 重叠的句子数
        """
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.target_chunk_size = target_chunk_size
        self.overlap_sentences = overlap_sentences

    def chunk(
        self,
        pages: List[PDFPage],
        doc_id: str,
    ) -> List[Chunk]:
        """
        将文档页面列表切分为 chunks

        Args:
            pages: PDF 页面列表
            doc_id: 文档 ID

        Returns:
            Chunk 列表
        """
        chunks = []
        global_char_offset = 0
        chunk_index = 0

        for page in pages:
            # 先按段落分组
            paragraphs = self._extract_paragraphs(page)

            # 然后将段落合并为 chunks
            page_chunks, page_char_offset = self._create_chunks_from_paragraphs(
                paragraphs=paragraphs,
                doc_id=doc_id,
                page_number=page.page_number,
                chunk_index=chunk_index,
                global_char_offset=global_char_offset,
            )

            chunks.extend(page_chunks)
            global_char_offset += page_char_offset
            chunk_index += len(page_chunks)

        return chunks

    def _extract_paragraphs(self, page: PDFPage) -> List[Dict[str, Any]]:
        """
        从页面中提取段落

        Args:
            page: PDF 页面

        Returns:
            段落列表，每个段落包含文本、bbox 和元数据
        """
        paragraphs = []

        if not page.text_blocks:
            return paragraphs

        # 按位置排序文本块
        sorted_blocks = sorted(
            page.text_blocks,
            key=lambda b: (b.bbox.y1, b.bbox.x1)
        )

        current_paragraph = {
            "text": "",
            "bboxes": [],
            "metadata": {},
        }

        prev_y = None

        for block in sorted_blocks:
            text = block.text.strip()
            if not text:
                continue

            # 判断是否为新段落（Y 坐标差异较大）
            is_new_paragraph = False
            if prev_y is not None:
                y_diff = abs(block.bbox.y1 - prev_y)
                # 如果 Y 坐标差异超过行高（假设为 20 点），认为是新段落
                if y_diff > 25:
                    is_new_paragraph = True

            if is_new_paragraph and current_paragraph["text"]:
                # 保存当前段落
                paragraphs.append(current_paragraph)
                # 开始新段落
                current_paragraph = {
                    "text": "",
                    "bboxes": [],
                    "metadata": {},
                }

            # 添加到当前段落
            if current_paragraph["text"]:
                current_paragraph["text"] += " "
            current_paragraph["text"] += text
            current_paragraph["bboxes"].append(block.bbox.to_dict())

            # 保存元数据
            if block.font_size:
                current_paragraph["metadata"]["font_size"] = block.font_size
            if block.font_name:
                current_paragraph["metadata"]["font_name"] = block.font_name
            if block.is_bold:
                current_paragraph["metadata"]["is_bold"] = True

            prev_y = block.bbox.y1

        # 添加最后一个段落
        if current_paragraph["text"]:
            paragraphs.append(current_paragraph)

        return paragraphs

    def _create_chunks_from_paragraphs(
        self,
        paragraphs: List[Dict[str, Any]],
        doc_id: str,
        page_number: int,
        chunk_index: int,
        global_char_offset: int,
    ) -> Tuple[List[Chunk], int]:
        """
        从段落列表创建 chunks

        Args:
            paragraphs: 段落列表
            doc_id: 文档 ID
            page_number: 页码
            chunk_index: 起始 chunk 索引
            global_char_offset: 全局字符偏移

        Returns:
            (Chunk 列表, 字符总数)
        """
        chunks = []
        current_chunk = {
            "text": "",
            "bboxes": [],
            "metadata": {},
        }
        char_offset = global_char_offset

        for para in paragraphs:
            para_text = para["text"]
            para_tokens = self._estimate_tokens(para_text)

            # 如果单个段落超过最大大小，需要切分
            if para_tokens > self.max_chunk_size:
                # 先保存当前 chunk
                if current_chunk["text"]:
                    chunks.append(self._create_chunk(
                        doc_id=doc_id,
                        page_number=page_number,
                        chunk_index=len(chunks) + chunk_index,
                        text=current_chunk["text"],
                        bboxes=current_chunk["bboxes"],
                        char_start=char_offset,
                        metadata=current_chunk["metadata"],
                    ))
                    char_offset += len(current_chunk["text"])
                    current_chunk = {"text": "", "bboxes": [], "metadata": {}}

                # 切分长段落
                sub_chunks = self._split_long_paragraph(
                    paragraph=para_text,
                    max_tokens=self.max_chunk_size,
                )
                for sub_chunk_text in sub_chunks:
                    chunks.append(self._create_chunk(
                        doc_id=doc_id,
                        page_number=page_number,
                        chunk_index=len(chunks) + chunk_index,
                        text=sub_chunk_text,
                        bboxes=para["bboxes"],
                        char_start=char_offset,
                        metadata=para["metadata"],
                    ))
                    char_offset += len(sub_chunk_text)
                continue

            # 检查添加此段落后是否会超过目标大小
            current_tokens = self._estimate_tokens(current_chunk["text"])
            new_tokens = current_tokens + para_tokens

            if new_tokens <= self.target_chunk_size:
                # 添加到当前 chunk
                if current_chunk["text"]:
                    current_chunk["text"] += "\n\n"
                current_chunk["text"] += para_text
                current_chunk["bboxes"].extend(para["bboxes"])
                current_chunk["metadata"].update(para["metadata"])
            else:
                # 保存当前 chunk
                if current_chunk["text"]:
                    chunks.append(self._create_chunk(
                        doc_id=doc_id,
                        page_number=page_number,
                        chunk_index=len(chunks) + chunk_index,
                        text=current_chunk["text"],
                        bboxes=current_chunk["bboxes"],
                        char_start=char_offset,
                        metadata=current_chunk["metadata"],
                    ))
                    char_offset += len(current_chunk["text"])

                # 开始新 chunk
                current_chunk = {
                    "text": para_text,
                    "bboxes": para["bboxes"],
                    "metadata": para["metadata"],
                }

        # 添加最后一个 chunk
        if current_chunk["text"]:
            chunks.append(self._create_chunk(
                doc_id=doc_id,
                page_number=page_number,
                chunk_index=len(chunks) + chunk_index,
                text=current_chunk["text"],
                bboxes=current_chunk["bboxes"],
                char_start=char_offset,
                metadata=current_chunk["metadata"],
            ))
            char_offset += len(current_chunk["text"])

        return chunks, char_offset - global_char_offset

    def _split_long_paragraph(
        self,
        paragraph: str,
        max_tokens: int,
    ) -> List[str]:
        """
        切分过长的段落

        Args:
            paragraph: 段落文本
            max_tokens: 最大 token 数

        Returns:
            切分后的文本列表
        """
        # 按句子切分
        sentences = re.split(r'([。！？.!?])', paragraph)
        # 重新组合句子和标点
        sentences = [
            sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else "")
            for i in range(0, len(sentences), 2)
        ]

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if not sentence.strip():
                continue

            test_chunk = current_chunk + sentence
            if self._estimate_tokens(test_chunk) <= max_tokens:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _create_chunk(
        self,
        doc_id: str,
        page_number: int,
        chunk_index: int,
        text: str,
        bboxes: List[Dict[str, Any]],
        char_start: int,
        metadata: Dict[str, Any],
    ) -> Chunk:
        """
        创建 Chunk 对象

        Args:
            doc_id: 文档 ID
            page_number: 页码
            chunk_index: chunk 索引
            text: 文本内容
            bboxes: 边界框列表
            char_start: 起始字符位置
            metadata: 元数据

        Returns:
            Chunk 对象
        """
        chunk_id = f"{doc_id}_p{page_number}_c{chunk_index}"

        # 合并边界框
        merged_bbox = self._merge_bboxes(bboxes) if bboxes else None

        # 识别条款类型
        clause_hint = self._identify_clause_type(text)

        # 估算 token 数
        token_count = self._estimate_tokens(text)

        # 生成创建时间
        created_at = datetime.now().isoformat()

        return Chunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            page=page_number,
            text=text,
            bbox=merged_bbox or {"x1": 0, "y1": 0, "x2": 0, "y2": 0},
            clause_hint=clause_hint,
            char_start=char_start,
            char_end=char_start + len(text),
            token_count=token_count,
            metadata=metadata,
            created_at=created_at,
        )

    def _merge_bboxes(self, bboxes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并多个边界框

        Args:
            bboxes: 边界框列表

        Returns:
            合并后的边界框
        """
        if not bboxes:
            return {"x1": 0, "y1": 0, "x2": 0, "y2": 0}

        x1 = min(b.get("x1", float('inf')) for b in bboxes)
        y1 = min(b.get("y1", float('inf')) for b in bboxes)
        x2 = max(b.get("x2", float('-inf')) for b in bboxes)
        y2 = max(b.get("y2", float('-inf')) for b in bboxes)

        # 获取页面尺寸
        page_width = bboxes[0].get("page_width")
        page_height = bboxes[0].get("page_height")

        result = {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
        }

        if page_width is not None:
            result["page_width"] = page_width
        if page_height is not None:
            result["page_height"] = page_height

        return result

    def _identify_clause_type(self, text: str) -> str:
        """
        识别条款类型

        Args:
            text: 文本内容

        Returns:
            条款类型
        """
        text_lower = text.lower()

        # 计算每种类型的关键词匹配数
        scores = {}
        for clause_type, keywords in CLAUSE_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1
            if score > 0:
                scores[clause_type] = score

        # 返回得分最高的类型
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return "unknown"

    def _estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数

        Args:
            text: 文本内容

        Returns:
            估算的 token 数
        """
        # 简单估算：中文字符 = 1 token，英文单词 = 1 token
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))

        return chinese_chars + english_words


def chunk_document(
    pages: List[PDFPage],
    doc_id: str,
    min_chunk_size: int = 50,
    max_chunk_size: int = 300,
    target_chunk_size: int = 150,
) -> List[Chunk]:
    """
    便捷函数：切分文档

    Args:
        pages: PDF 页面列表
        doc_id: 文档 ID
        min_chunk_size: 最小 chunk token 数
        max_chunk_size: 最大 chunk token 数
        target_chunk_size: 目标 chunk token 数

    Returns:
        Chunk 列表
    """
    chunker = DocumentChunker(
        min_chunk_size=min_chunk_size,
        max_chunk_size=max_chunk_size,
        target_chunk_size=target_chunk_size,
    )
    return chunker.chunk(pages, doc_id)
