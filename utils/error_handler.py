from enum import Enum
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from typing import Optional

#원하는 에러 메세지를 전달하기위해 Enum으로 그룹핑해서 처리
class ErrorCode(str, Enum):
    INVALID_PARAMETER = "invalid_parameter"
    API_NOT_FOUND = "api_not_found"
    MISSING_PARAMETER = "missing_parameter"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    INVALID_FILE_FORMAT = "invalid_file_format"
    #아래는 검증부분에서 사전에 처리되면 좋을 에러
    INVALID_QUALIFIER_KIND = "invalid_qualifier_kind"
    INVALID_QUALIFIER_TYPE = "invalid_qualifier_type"
    INVALID_SUBMODEL_KIND = "invalid_submodel_kind"

#에러코드에 따라 에러메세지도 동일하게 처리되도록 매핑
ERROR_MESSAGES = {
    ErrorCode.INVALID_PARAMETER: "잘못된 파라미터입니다.",
    ErrorCode.API_NOT_FOUND: "API를 찾을 수 없습니다.",
    ErrorCode.MISSING_PARAMETER: "필수 파라미터가 누락되었습니다.",
    ErrorCode.INTERNAL_SERVER_ERROR: "서버 내부 오류가 발생했습니다.",
    ErrorCode.INVALID_FILE_FORMAT: "지원하지 않는 파일 형식입니다.",
    ErrorCode.INVALID_QUALIFIER_KIND: "Qualifier의 'kind'는 'TemplateQualifier'여야 합니다.",
    ErrorCode.INVALID_QUALIFIER_TYPE: "Qualifier의 'type'은 'SMT_Cardinality'여야 합니다.",
    ErrorCode.INVALID_SUBMODEL_KIND: "Submodel의 'Kind'는 'Template'여야 합니다."
}

#에러 응답시 동일한 구조로 가도록 함수 작성
def error_response(status_code: int, error_code: ErrorCode, message: Optional[str] = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_code,
            "message": message or ERROR_MESSAGES.get(error_code, "알지 못하는 에러 입니다.")
        }
    )
    

#FAST api에서 예외 처리하기 위해 만듬.
def setup_exception_handlers(app):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"message": "요청 데이터 오류", "details": exc.errors()})

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "서버 오류", "details": str(exc)})

#직접 예외처리 발생하려고 따로 만듬
def raise_400(msg: str):
    raise RequestValidationError([{
        "msg": message or ERROR_MESSAGES.get(error_code),
        "type": str(error_code)
    }])