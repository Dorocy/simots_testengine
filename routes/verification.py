from fastapi import APIRouter, UploadFile, File, Query
from services.verification_service import (
    verification_instance,
    verification_metamodel,
    verification_schema,
    delete_schema,
    schemas_list,
    search_schema_by_value,
    search_schema_by_semamtic_id,
    search_schema_by_uploaded_by
)

router = APIRouter()


@router.post("/metamodel")
async def check_metamodel(file: UploadFile = File(...)):
    return await verification_metamodel(file)


@router.post("/schema")
async def check_schema(file: UploadFile = File(...)):
    return await verification_schema(file)


@router.post("/instance")
async def check_instance(file: UploadFile = File(...)):
    return await verification_instance(file)


@router.delete("/delete_schema/")
async def check_and_delete_schema(semanticId: str = Query(..., description="SemanticId of the schema to delete")):
    return await delete_schema(semanticId)


@router.get("/schemas")
async def schema_list():
    return await schemas_list()


@router.get("/schemas/search/semantic_id")
async def search_schema_with_semantic_id(value: str = Query(..., description="semanticId")):
    return await search_schema_by_semamtic_id(value)


@router.get("/schemas/search/uploaded_by")
async def search_schema_with_uploaded_by(value: str = Query(..., description="제조 기업")):
    return await search_schema_by_uploaded_by(value)


@router.get("/schemas/search")
async def search_schema(semanticId: str = Query(..., description="semanticId"), uploadedBy: str = Query(..., description="제조 기업")):
    return await search_schema_by_value(semanticId, uploadedBy)
