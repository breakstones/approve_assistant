"""
TrustLens AI - Document API Routes
文档上传与状态管理 HTTP API
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import os
import asyncio
from pathlib import Path


# API Router
router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


# Request/Response Models
class DocumentUploadRequest(BaseModel):
    """文档上传请求（元数据）"""
    filename: str = Field(..., description="文件名")
    file_type: str = Field(..., description="文件类型（pdf/docx/doc）")
    metadata: Optional[dict] = Field(None, description="文档元数据")


class DocumentResponse(BaseModel):
    """文档响应"""
    doc_id: str
    filename: str
    file_type: str
    file_size: int
    file_path: Optional[str]
    status: str
    status_message: Optional[str]
    progress: float
    page_count: int
    chunk_count: int
    metadata: dict
    processing_info: dict
    review_info: dict
    created_at: Optional[str]
    updated_at: Optional[str]


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    total: int
    documents: List[DocumentResponse]
    limit: int
    offset: int


class StatusUpdateRequest(BaseModel):
    """状态更新请求"""
    status: str = Field(..., description="新状态")
    message: Optional[str] = Field(None, description="状态消息")
    progress: Optional[float] = Field(None, description="进度（0-100）")


# 服务实例
document_service: Optional["DocumentService"] = None


def get_document_service_instance() -> "DocumentService":
    """获取文档服务实例"""
    global document_service
    if document_service is None:
        # 延迟导入，避免循环依赖
        from config.database import get_database
        from config.document_service import get_document_service as get_doc_service
        # 初始化数据库
        get_database()
        document_service = get_doc_service()
    return document_service


async def process_document_task(doc_id: str, file_path: str, file_type: str):
    """
    异步处理文档（后台任务）

    Args:
        doc_id: 文档 ID
        file_path: 文件路径
        file_type: 文件类型
    """
    # 延迟导入，避免循环依赖
    from config.document_models import DocumentStatus
    from document import parse_pdf, parse_docx, chunk_document, create_embedding_pipeline

    service = get_document_service_instance()

    try:
        # 更新状态为处理中
        service.update_status(
            doc_id,
            DocumentStatus.PROCESSING,
            message="正在解析文档...",
            progress=10.0,
        )

        # 解析文档
        start_time = datetime.now()
        if file_type == "pdf":
            pages = parse_pdf(file_path)
            parser_used = "pdfplumber"
        else:  # docx or doc
            pages = parse_docx(file_path)
            parser_used = "python-docx"

        page_count = len(pages)

        # 更新进度
        service.update_status(
            doc_id,
            DocumentStatus.PROCESSING,
            message=f"解析完成，共 {page_count} 页，正在切分...",
            progress=50.0,
        )

        # 切分文档
        chunks = chunk_document(pages, doc_id)
        chunk_count = len(chunks)

        # 更新进度
        service.update_status(
            doc_id,
            DocumentStatus.PROCESSING,
            message=f"切分完成，共 {chunk_count} 个 chunks，正在向量化...",
            progress=70.0,
        )

        # 创建 embedding pipeline 并处理
        pipeline = create_embedding_pipeline(
            provider_type="openai",
            store_type="memory",
        )

        result = pipeline.process_chunks(chunks, batch_size=50)

        # 计算处理时间
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # 更新处理信息
        service.update_processing_info(doc_id, {
            "started_at": start_time.isoformat(),
            "completed_at": datetime.now().isoformat(),
            "processing_time_ms": processing_time,
            "parser_used": parser_used,
            "page_count": page_count,
            "chunk_count": chunk_count,
        })

        # 更新为完成状态
        service.update_status(
            doc_id,
            DocumentStatus.READY,
            message="文档处理完成",
            progress=100.0,
        )

        # 更新页数和 chunk 数
        with service._get_db().get_session() as session:
            from config.document_models import Document
            doc = session.query(Document).filter(
                Document.doc_id == doc_id
            ).first()
            if doc:
                doc.page_count = page_count
                doc.chunk_count = chunk_count
                session.commit()

    except Exception as e:
        # 处理失败
        service.update_status(
            doc_id,
            DocumentStatus.FAILED,
            message=f"处理失败: {str(e)}",
            progress=0.0,
        )

        # 记录错误信息
        service.update_processing_info(doc_id, {
            "error_message": str(e),
            "error_type": type(e).__name__,
        })


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="文档文件"),
):
    """
    上传文档

    上传 PDF 或 DOCX 文档，自动启动后台处理流程
    """
    service = get_document_service_instance()

    # 验证文件类型
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower().lstrip(".")

    if ext not in ["pdf", "docx", "doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {ext}。仅支持 PDF、DOCX、DOC"
        )

    try:
        # 读取文件内容
        contents = await file.read()
        file_size = len(contents)

        # 创建文档记录
        doc_dict = service.create(
            filename=filename,
            file_type=ext,
            file_size=file_size,
        )

        # 保存文件
        file_path = doc_dict.get("file_path")
        if file_path:
            with open(file_path, "wb") as f:
                f.write(contents)

        # 启动后台处理任务
        background_tasks.add_task(
            process_document_task,
            doc_dict["doc_id"],
            file_path,
            ext,
        )

        return DocumentResponse(**doc_dict)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传文档失败: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    status_filter: Optional[str] = Query(None, alias="status", description="按状态过滤"),
    file_type: Optional[str] = Query(None, description="按文件类型过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
):
    """
    获取文档列表

    支持按状态、文件类型过滤，支持分页
    """
    from config.document_models import DocumentStatus

    service = get_document_service_instance()

    try:
        # 转换状态
        doc_status = None
        if status_filter:
            try:
                doc_status = DocumentStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的状态值: {status_filter}"
                )

        documents = service.list(
            status=doc_status,
            file_type=file_type,
            limit=limit,
            offset=offset,
        )

        # 获取总数
        total = service.count(
            status=doc_status,
            file_type=file_type,
        )

        return DocumentListResponse(
            total=total,
            documents=[DocumentResponse(**doc) for doc in documents],
            limit=limit,
            offset=offset,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询文档列表失败: {str(e)}"
        )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """
    获取单个文档

    - **doc_id**: 文档唯一标识符
    """
    service = get_document_service_instance()

    try:
        doc = service.get_by_id(doc_id)

        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档 '{doc_id}' 不存在"
            )

        return DocumentResponse(**doc)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询文档失败: {str(e)}"
        )


@router.get("/{doc_id}/status", response_model=DocumentResponse)
async def get_document_status(doc_id: str):
    """
    获取文档状态

    - **doc_id**: 文档唯一标识符
    """
    service = get_document_service_instance()

    try:
        doc = service.get_by_id(doc_id)

        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档 '{doc_id}' 不存在"
            )

        return DocumentResponse(**doc)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询文档状态失败: {str(e)}"
        )


@router.put("/{doc_id}/status", response_model=DocumentResponse)
async def update_document_status(doc_id: str, request: StatusUpdateRequest):
    """
    更新文档状态

    - **doc_id**: 文档唯一标识符
    """
    service = get_document_service_instance()

    try:
        # 转换状态
        try:
            new_status = DocumentStatus(request.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的状态值: {request.status}"
            )

        # 更新状态
        updated_doc = service.update_status(
            doc_id,
            new_status,
            message=request.message,
            progress=request.progress,
        )

        if updated_doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档 '{doc_id}' 不存在"
            )

        return DocumentResponse(**updated_doc)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文档状态失败: {str(e)}"
        )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(doc_id: str):
    """
    删除文档

    - **doc_id**: 文档唯一标识符
    """
    service = get_document_service_instance()

    try:
        success = service.delete(doc_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档 '{doc_id}' 不存在"
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文档失败: {str(e)}"
        )


@router.get("/{doc_id}/download")
async def download_document(doc_id: str):
    """
    下载文档文件

    - **doc_id**: 文档唯一标识符
    """
    service = get_document_service_instance()

    try:
        file_path = service.get_file_path(doc_id)

        if file_path is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文档 '{doc_id}' 不存在"
            )

        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )

        from fastapi.responses import FileResponse
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/octet-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载文档失败: {str(e)}"
        )
