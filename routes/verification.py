from fastapi import APIRouter, UploadFile, File, Query
from services.verification_service import (
    verification_instance,
    verification_metamodel,
    verification_schema,
    delete_schema,
    schemas_list,
    # find_schema
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


@router.delete("/delete_submodel_schema/")
async def check_and_delete_schema(semanticId: str = Query(..., description="SemanticId of the schema to delete")):
    return await delete_schema(semanticId)

@router.get("/schemas")
async def schema_list():
    return await schemas_list()

# @router.get("/schemas/")
# async def find_schema_with_semantic_id():
#     return await find_schema(semantic_id)

# @router.put("/schemas")
# async def bbb():
#     return await bbbbb