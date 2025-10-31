from fastapi import APIRouter, UploadFile, File, Query, Path
from typing import Optional
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

router = APIRouter()


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
