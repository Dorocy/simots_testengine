import asyncio
import os
from fastapi import APIRouter, UploadFile, File, Query, Path
from typing import Optional, Any, Literal
from pydantic import BaseModel
from api.response_handler import ErrorCode, error_response
from services.verification_service import (
    verification_instance,
    verification,
    verification_schema,
    delete_schema,
    schemas_list,
    search_schema_by_value,
    search_schema_by_semamtic_id,
    search_schema_by_uploaded_by,
    update_schema_put,
    update_schema_patch
)
from services.llm_fix_service import request_llm_fix, request_repair_fix, request_rule_based_fix

router = APIRouter()
FIX_REQUEST_TIMEOUT_SECONDS = float(os.getenv("FIX_REQUEST_TIMEOUT_SECONDS", "120"))


class FixTargetError(BaseModel):
    id: Optional[str] = None
    code: str
    message: str
    location: Optional[str] = None


class LlmFixRequest(BaseModel):
    mode: Literal["single", "batch"] = "single"
    verificationType: Literal["metamodel", "template", "instance"] = "metamodel"
    errors: list[FixTargetError]
    fileName: Optional[str] = None
    context: Optional[dict[str, Any]] = None
    includeUpdatedFile: bool = False

#타고 들어가는 함수와 같이 전달되는 파라미터 체크필요
@router.post("/metamodel")
async def verify_metamodel(file: UploadFile = File(...)):
    return await verification(file, is_template=False)

@router.post("/template")
async def verify_template(file: UploadFile = File(...)):
    return await verification(file, is_template=True)


@router.post("/schema")
async def create_schema(file: UploadFile = File(...)):
    return await verification_schema(file)


@router.post("/instance")
async def verify_instance(file: UploadFile = File(...)):
    return await verification_instance(file)


@router.delete("/schema/delete/{semanticId:path}")
async def check_and_delete_schema(semanticId: str = Path(..., description="SemanticId of the schema to delete")):
    return await delete_schema(semanticId)


@router.get("/schema/search")
async def search_schemas(
    semanticId: Optional[str] = Query(None, description="semanticId"),
    uploadedBy: Optional[str] = Query(None, description="제조 기업")
):
    if semanticId and uploadedBy:
        return await search_schema_by_value(semanticId, uploadedBy)
    elif semanticId:
        return await search_schema_by_semamtic_id(semanticId)
    elif uploadedBy:
        return await search_schema_by_uploaded_by(uploadedBy)
    else:
        return await schemas_list()


@router.put("/schema")
async def put_schema(file: UploadFile = File(...)):
    return await update_schema_put(file)


@router.patch("/schema")
async def patch_schema(file: UploadFile = File(...)):
    return await update_schema_patch(file)



# 하이브리드 수정 API
@router.post("/fix")
async def fix_errors_with_llm(payload: LlmFixRequest):
    try:
        return await asyncio.wait_for(
            request_llm_fix(payload.model_dump()),
            timeout=FIX_REQUEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return {
            "success": False,
            "message": (
                f"Fix request timed out after {FIX_REQUEST_TIMEOUT_SECONDS:.0f}s. "
                "Try fewer errors."
            ),
        }
    except Exception as e:
        return error_response(
            status_code=500,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"/verification/fix failed: {str(e)}",
        )


@router.post("/rule-fix")
async def fix_errors_with_rules(payload: LlmFixRequest):
    try:
        return await asyncio.wait_for(
            request_rule_based_fix(payload.model_dump()),
            timeout=FIX_REQUEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return {
            "success": False,
            "message": (
                f"Rule fix request timed out after {FIX_REQUEST_TIMEOUT_SECONDS:.0f}s. "
                "Try fewer errors."
            ),
        }
    except Exception as e:
        return error_response(
            status_code=500,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"/verification/rule-fix failed: {str(e)}",
        )


@router.post("/llm-repair")
async def repair_errors_with_llm(payload: LlmFixRequest):
    try:
        return await asyncio.wait_for(
            request_repair_fix(payload.model_dump()),
            timeout=FIX_REQUEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        return {
            "success": False,
            "message": (
                f"LLM repair request timed out after {FIX_REQUEST_TIMEOUT_SECONDS:.0f}s. "
                "Try fewer errors."
            ),
        }
    except Exception as e:
        return error_response(
            status_code=500,
            error_code=ErrorCode.INTERNAL_SERVER_ERROR,
            message=f"/verification/llm-repair failed: {str(e)}",
        )


@router.get("/fix")
async def fix_errors_with_llm_get():
    return {
        "message": "Use POST /verification/fix, /verification/rule-fix, or /verification/llm-repair with JSON payload.",
        "method": "POST",
    }
