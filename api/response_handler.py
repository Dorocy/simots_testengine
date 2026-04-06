from enum import Enum
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from typing import Optional


# 원하는 에러 메세지를 전달하기위해 Enum으로 그룹핑해서 처리
class ErrorCode(str, Enum):
    INVALID_PARAMETER = "invalid_parameter"
    API_NOT_FOUND = "api_not_found"
    MISSING_PARAMETER = "missing_parameter"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    DB_ERROR = "db_error"
    INVALID_FILE_FORMAT = "invalid_file_format"
    INVALID_TEMPLATE = "invalid_template"
    # 아래는 검증부분에서 사전에 처리되면 좋을 에러
    INVALID_QUALIFIER_COMBINATION = "invalid_qualifier_combination"
    INVALID_SUBMODEL_KIND = "invalid_submodel_kind"
    INVALID_JSON_FORMAT = "invalid_json_format"
    TEST_ENGINE_NO_OUTPUT = "test_engine_no_output"
    ALREADY_EXISTS_SCHEMA = "already_exists_schema"
    SCHEMA_NOT_FOUND = "schema_not_found"
    SUBMODEL_NOT_FOUND = "submodel_not_found"
    SEMANTIC_ID_NOT_FOUND = "semantic_id_not_found"
    LLM_NO_USABLE_OUTPUT = "llm_no_usable_output"
    OLLAMA_HTTP_ERROR = "ollama_http_error"
    OLLAMA_CONNECTION_ERROR = "ollama_connection_error"
    OLLAMA_REQUEST_FAILED = "ollama_request_failed"


# 에러코드에 따라 에러메세지도 동일하게 처리되도록 매핑
ERROR_MESSAGES = {
    ErrorCode.INVALID_PARAMETER: "잘못된 파라미터입니다.",
    ErrorCode.API_NOT_FOUND: "API를 찾을 수 없습니다.",
    ErrorCode.MISSING_PARAMETER: "필수 파라미터가 누락되었습니다.",
    ErrorCode.INTERNAL_SERVER_ERROR: "서버 내부 오류가 발생했습니다.",
    ErrorCode.DB_ERROR: "DB 오류가 발생했습니다.",
    ErrorCode.INVALID_FILE_FORMAT: "잘못된 형태의 파일입니다.",
    ErrorCode.INVALID_TEMPLATE: "잘못된 형태의 Template입니다.",
    ErrorCode.INVALID_SUBMODEL_KIND: "submodel의 kind가 'Template'이 아닙니다.",
    ErrorCode.INVALID_QUALIFIER_COMBINATION: "{param}의 Qualifier의 'kind'는 'TemplateQualifier', 'type'은 'SMT_Cardinality'인 요소가 하나 이상 포함되어야 합니다.",
    ErrorCode.TEST_ENGINE_NO_OUTPUT: "test engine으로 부터 결과를 받지 못했습니다.",
    ErrorCode.INVALID_JSON_FORMAT: "json 파싱 오류 발생",
    ErrorCode.ALREADY_EXISTS_SCHEMA: "이미 존재하는 스키마입니다.",
    ErrorCode.SCHEMA_NOT_FOUND: "스키마를 찾을 수 없습니다.",
    ErrorCode.SUBMODEL_NOT_FOUND: "Submodel이 없습니다.",
    ErrorCode.SEMANTIC_ID_NOT_FOUND: "semantic_id가 없습니다.",
    ErrorCode.LLM_NO_USABLE_OUTPUT: "LLM이 사용할 수 있는 수정 결과를 반환하지 않았습니다.",
    ErrorCode.OLLAMA_HTTP_ERROR: "Ollama HTTP 오류가 발생했습니다.",
    ErrorCode.OLLAMA_CONNECTION_ERROR: "Ollama 연결 오류가 발생했습니다.",
    ErrorCode.OLLAMA_REQUEST_FAILED: "Ollama 요청 처리 중 오류가 발생했습니다.",
}


# 예외 처리시 동일한 구조로 가도록 함수 작성
def error_response(
    status_code: int, error_code: ErrorCode,  param: Optional[str] = None, message: Optional[str] = None
):
    template = message if message is not None else ERROR_MESSAGES.get(error_code, "알 수 없는 오류입니다.")
    try:
        resolved_message = template.format(param=param) if message is None else template
    except Exception:
        resolved_message = template

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "API error",
            "error": {
                "code": error_code.value,
                "message": resolved_message
            },
        },
    )


def success_response(status: str, verification_status, verification_message):
    return JSONResponse(
        status_code=200,
        content={
            "status": status,
            "verification": {
                "result": verification_status,
                "message": verification_message,
            },
        },
    )


# FAST api에서 예외 처리하기 위해 만듬.
def setup_exception_handlers(app):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else None
        return error_response(
            status_code=exc.status_code,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=detail,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return error_response(
            status_code=HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.INVALID_PARAMETER,
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return error_response(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
        )

    @app.exception_handler(UnicodeDecodeError)
    async def unicode_exception_handler(request: Request, exc: UnicodeDecodeError):
        return error_response(
            status_code=400,
            error_code=ErrorCode.INVALID_FILE_FORMAT,
        )
