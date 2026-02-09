"""
Error Handler Module
统一错误处理模块
"""
from enum import Enum
from typing import Optional, Any, Dict
from datetime import datetime
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('trustlens.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


# 错误码枚举
class ErrorCode(str, Enum):
    """统一错误码"""
    # 通用错误 (1xxx)
    UNKNOWN_ERROR = "1000"
    INVALID_REQUEST = "1001"
    INVALID_PARAMETER = "1002"
    MISSING_PARAMETER = "1003"
    UNAUTHORIZED = "1004"
    FORBIDDEN = "1005"

    # 资源错误 (2xxx)
    RESOURCE_NOT_FOUND = "2000"
    RESOURCE_ALREADY_EXISTS = "2001"
    RESOURCE_CONFLICT = "2002"
    RESOURCE_LOCKED = "2003"

    # 业务逻辑错误 (3xxx)
    RULE_VALIDATION_ERROR = "3000"
    RULE_PARSE_ERROR = "3001"
    DOCUMENT_PROCESSING_ERROR = "3002"
    REVIEW_EXECUTION_ERROR = "3003"
    EMBEDDING_ERROR = "3004"
    LLM_ERROR = "3005"

    # 系统错误 (5xxx)
    DATABASE_ERROR = "5000"
    CACHE_ERROR = "5001"
    EXTERNAL_SERVICE_ERROR = "5002"


class TrustLensError(Exception):
    """TrustLens AI 基础异常类"""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        self.original_error = original_error
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "code": self.code.value,
            "message": self.message,
            "type": self.__class__.__name__,
        }

        if self.details:
            result["details"] = self.details

        if self.original_error:
            result["original_error"] = str(self.original_error)

        return result

    def log(self, level: str = "ERROR") -> None:
        """记录错误日志"""
        log_func = getattr(logger, level.lower(), logger.error)

        log_func(
            f"[{self.code.value}] {self.message}",
            extra={
                "error_code": self.code.value,
                "error_type": self.__class__.__name__,
                "details": self.details,
            }
        )

        # 记录原始错误的堆栈
        if self.original_error:
            logger.debug(f"Original error traceback:\n{traceback.format_exc()}")


# 具体错误类
class ResourceNotFoundError(TrustLensError):
    """资源不存在错误"""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"{resource_type} '{resource_id}' 不存在"
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_NOT_FOUND,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                **(details or {})
            }
        )


class ResourceAlreadyExistsError(TrustLensError):
    """资源已存在错误"""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"{resource_type} '{resource_id}' 已存在"
        super().__init__(
            message=message,
            code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id,
                **(details or {})
            }
        )


class ValidationError(TrustLensError):
    """验证错误"""

    def __init__(
        self,
        field: str,
        value: Any,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"字段 '{field}' 验证失败: {reason}"
        super().__init__(
            message=message,
            code=ErrorCode.INVALID_PARAMETER,
            details={
                "field": field,
                "value": str(value),
                "reason": reason,
                **(details or {})
            }
        )


class DocumentProcessingError(TrustLensError):
    """文档处理错误"""

    def __init__(
        self,
        document_id: str,
        stage: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"文档 '{document_id}' 在 '{stage}' 阶段处理失败: {reason}"
        super().__init__(
            message=message,
            code=ErrorCode.DOCUMENT_PROCESSING_ERROR,
            details={
                "document_id": document_id,
                "stage": stage,
                "reason": reason,
                **(details or {})
            }
        )


class ReviewExecutionError(TrustLensError):
    """审查执行错误"""

    def __init__(
        self,
        review_id: str,
        rule_id: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"审查 '{review_id}' 的规则 '{rule_id}' 执行失败: {reason}"
        super().__init__(
            message=message,
            code=ErrorCode.REVIEW_EXECUTION_ERROR,
            details={
                "review_id": review_id,
                "rule_id": rule_id,
                "reason": reason,
                **(details or {})
            }
        )


class RuleValidationError(TrustLensError):
    """规则验证错误"""

    def __init__(
        self,
        rule_id: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"规则 '{rule_id}' 验证失败: {reason}"
        super().__init__(
            message=message,
            code=ErrorCode.RULE_VALIDATION_ERROR,
            details={
                "rule_id": rule_id,
                "reason": reason,
                **(details or {})
            }
        )


def handle_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    reraise: bool = False,
) -> TrustLensError:
    """
    统一错误处理

    Args:
        error: 原始异常
        context: 额外上下文信息
        reraise: 是否重新抛出异常

    Returns:
        TrustLensError: 转换后的错误
    """
    # 如果已经是 TrustLensError，直接记录并返回
    if isinstance(error, TrustLensError):
        error.log()
        if reraise:
            raise
        return error

    # 转换其他异常
    error_code = ErrorCode.UNKNOWN_ERROR
    error_message = str(error)
    error_details = {}

    # 根据异常类型确定错误码
    if isinstance(error, ValueError):
        error_code = ErrorCode.INVALID_PARAMETER
        error_details = {"error_type": "ValueError"}
    elif isinstance(error, KeyError):
        error_code = ErrorCode.RESOURCE_NOT_FOUND
        error_details = {"missing_key": str(error)}
    elif isinstance(error, PermissionError):
        error_code = ErrorCode.FORBIDDEN
        error_details = {"error_type": "PermissionError"}

    # 添加上下文
    if context:
        error_details.update(context)

    # 创建 TrustLensError
    trustlens_error = TrustLensError(
        message=error_message,
        code=error_code,
        details=error_details,
        original_error=error,
    )

    trustlens_error.log()

    if reraise:
        raise trustlens_error

    return trustlens_error


def log_api_request(
    method: str,
    path: str,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
):
    """记录 API 请求日志"""
    logger.info(
        f"API Request: {method} {path}",
        extra={
            "method": method,
            "path": path,
            "params": params or {},
            "body_keys": list(body.keys()) if body else [],
        }
    )


def log_api_response(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    response_size: Optional[int] = None,
):
    """记录 API 响应日志"""
    logger.info(
        f"API Response: {method} {path} - {status_code} ({duration_ms:.2f}ms)",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "response_size": response_size,
        }
    )


def log_business_event(
    event_type: str,
    description: str,
    data: Optional[Dict[str, Any]] = None,
):
    """记录业务事件日志"""
    logger.info(
        f"[{event_type}] {description}",
        extra={
            "event_type": event_type,
            "description": description,
            "data": data or {},
        }
    )


def get_error_response(error: TrustLensError) -> Dict[str, Any]:
    """
    生成标准错误响应

    Args:
        error: TrustLensError 实例

    Returns:
        标准错误响应字典
    """
    response = error.to_dict()

    # 添加时间戳
    response["timestamp"] = datetime.now().isoformat()

    return response


# FastAPI 依赖项（用于路由中的错误处理）
async def log_request_context(
    method: str = "GET",
    path: str = "/",
):
    """记录请求上下文（可作为 FastAPI 依赖使用）"""
    log_api_request(method, path)
    return {"method": method, "path": path}
