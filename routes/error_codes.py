# routes/error_codes.py
from fastapi import APIRouter
from starlette.status import (
    HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR
)
from utils.response_handler import ErrorCode, ERROR_MESSAGES

router = APIRouter()

@router.get("/error-codes", summary="HTTP 및 커스텀 에러 코드 목록", tags=["Info"])
async def get_error_codes():
    return {
        "http_status_codes": {
            "200": "OK - 요청 성공",
            "400": "Bad Request - 잘못된 요청",
            "404": "Not Found - 요청한 자원을 찾을 수 없음",
            "422": "Unprocessable Entity - 유효성 검사 실패",
            "500": "Internal Server Error - 서버 오류"
        },
        "custom_error_codes": {
            error_code.value: message
            for error_code, message in ERROR_MESSAGES.items()
        }
    }